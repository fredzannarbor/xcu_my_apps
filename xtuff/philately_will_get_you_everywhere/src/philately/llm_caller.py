import os
import json
import logging
import sys
import base64
import re
from uuid import uuid4
from pathlib import Path
import cv2
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import argparse
from typing import Dict, Any, List, Tuple

# --- Configuration & Logging ---
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Suppress noisy logs from underlying libraries
for lib in ["openai", "httpx", "httpcore"]:
    logging.getLogger(lib).setLevel(logging.WARNING)

# --- Constants ---
COLLECTION_ORIGIN_STORY = """
This collection was begun by William Zimmerman II, a senior government official in the New Deal era.
"""


class PhilatelyProcessor:
    """
    Orchestrates the entire philatelic analysis pipeline, from image
    processing to clustering and summary generation.
    """

    def __init__(self, image_dir: Path, output_dir: Path):
        self.image_dir = image_dir
        self.output_dir = output_dir
        self.master_csv_path = self.output_dir / "master_inventory.csv"
        self.cropped_dir = self.output_dir / "cropped_entities"
        self.thumbnail_dir = self.output_dir / "thumbnails"
        self.raw_responses_dir = self.output_dir / "raw_api_responses"
        self.final_json_path = self.output_dir / "stamp_inventory.json"

        # Create necessary directories
        for d in [self.output_dir, self.cropped_dir, self.thumbnail_dir, self.raw_responses_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Initialize API Client
        self.client = self._initialize_client()

    def _initialize_client(self) -> OpenAI | None:
        """Initializes the OpenAI-compatible client for xAI."""
        if xai_api_key := os.getenv("XAI_API_KEY"):
            try:
                client = OpenAI(api_key=xai_api_key, base_url="https://api.x.ai/v1")
                logger.info("xAI client initialized successfully.")
                return client
            except Exception as e:
                logger.error(f"Failed to initialize xAI client: {e}")
        else:
            logger.error("XAI_API_KEY not found. Client will not be initialized.")
        return None

    def _preprocess_image(self, image_path: Path) -> str | None:
        """Preprocesses an image and returns a base64 encoded string."""
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                logger.warning(f"Failed to read image: {image_path}")
                return None
            _, buffer = cv2.imencode(".jpg", img)
            return base64.b64encode(buffer.tobytes()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error preprocessing {image_path}: {e}")
            return None

    def _create_thumbnail_and_crop(self, img_path: Path, bbox: dict, stamp_id: str) -> Tuple[str | None, str | None]:
        """Creates a thumbnail and a cropped image from a bounding box."""
        try:
            img = cv2.imread(str(img_path))
            if img is None:
                logger.warning(f"Failed to read image for cropping: {img_path}")
                return None, None

            # Create thumbnail
            thumbnail = cv2.resize(img, (100, 100), interpolation=cv2.INTER_AREA)
            thumbnail_path = self.thumbnail_dir / f"{stamp_id}_thumbnail.jpg"
            cv2.imwrite(str(thumbnail_path), thumbnail)

            # Create cropped image
            x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
            h_img, w_img = img.shape[:2]
            x, y = max(0, x), max(0, y)
            w, h = min(w, w_img - x), min(h, h_img - y)
            if w <= 0 or h <= 0:
                logger.warning(f"Invalid bounding box for {img_path}: {bbox}")
                return str(thumbnail_path.relative_to(self.output_dir)), None

            cropped = img[y:y + h, x:x + w]
            cropped_path = self.cropped_dir / f"{stamp_id}_cropped.jpg"
            cv2.imwrite(str(cropped_path), cropped)

            return str(thumbnail_path.relative_to(self.output_dir)), str(cropped_path.relative_to(self.output_dir))
        except Exception as e:
            logger.error(f"Error creating thumbnail/crop for {img_path}: {e}")
            return None, None

    def _call_vision_model(self, image_base64: str, model: str) -> List[Dict[str, Any]] | None:
        """Analyzes an image using a specified vision model."""
        prompt = """Your response MUST be a valid JSON array.
Identify and describe each distinct stamp or philatelic item on this page.
Note that some stamps are mounted in albums whose pages contain black and white drawings of stamps. The actual stamps are mounted on top of the drawings. Be careful to only include mounted stamps. Exclude drawings-only.
For each item, provide: common_name, country_of_origin, estimated_year_of_issue, face_value, condition, description, bounding_box (x, y, width, height as integers), and a confidence score (1-7 Likert scale, 7 is most confident).
The final item in the array should be a "Collection Overview" object with a description summarizing the page.
Do not wrap your response in markdown. Return only the raw JSON array.
"""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a philately expert. Respond with a valid JSON array."},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]}
                ],
                max_tokens=4096
            )
            raw_content = response.choices[0].message.content
            # Basic cleaning to extract JSON from potential markdown wrappers
            cleaned_content = re.search(r'\[.*\]', raw_content, re.DOTALL)
            if not cleaned_content:
                logger.warning("Could not find a JSON array in the model's response.")
                return None
            return json.loads(cleaned_content.group(0))
        except Exception as e:
            logger.error(f"Analysis with model {model} failed: {e}")
            return None

    # MODIFICATION: Updated method signature to accept model names
    def run_image_analysis_phase(self, confidence_threshold: int, max_images: int | None = None, low_cost_model: str = "grok-2-vision-1212", high_cost_model: str = "gemini-1.5-pro-latest"):
        """
        Runs the two-pass image analysis:
        1. Analyze all images with a low-cost model.
        2. Re-analyze images with low-confidence results using a high-cost model.
        """
        logger.info("--- Starting Image Analysis Phase ---")
        if not self.client:
            logger.error("Client not initialized. Aborting analysis phase.")
            return

        all_stamps = []

        image_patterns = ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]
        image_files = []
        for pattern in image_patterns:
            image_files.extend(self.image_dir.rglob(pattern))

        image_files = sorted(list(set(image_files)))

        if not image_files:
            logger.warning(f"No image files found in the specified directory: {self.image_dir}")
            logger.warning(
                "Please ensure the 'stamps' directory contains subdirectories with images (.jpg, .jpeg, .png).")
            return

        if max_images:
            logger.info(f"Limiting processing to the first {max_images} of {len(image_files)} found images.")
            image_files = image_files[:max_images]

        for img_path in image_files:
            album_name = img_path.parent.name
            logger.info(f"Processing image: {img_path.relative_to(self.image_dir)}")

            image_base64 = self._preprocess_image(img_path)
            if not image_base64:
                continue

            # MODIFICATION: Use the provided low_cost_model parameter
            logger.info(f"  Pass 1: Analyzing with low-cost model ({low_cost_model})...")
            analysis = self._call_vision_model(image_base64, low_cost_model)
            if not analysis:
                continue

            # Check confidence and decide on Pass 2
            needs_reanalysis = any(
                item.get("confidence", 0) < confidence_threshold and "bounding_box" in item
                for item in analysis
            )

            if needs_reanalysis:
                # MODIFICATION: Use the provided high_cost_model parameter
                logger.info(f"  Low confidence detected. Pass 2: Re-analyzing with high-cost model ({high_cost_model})...")
                analysis = self._call_vision_model(image_base64, high_cost_model)
                if not analysis:
                    continue

            # Process final analysis results
            for item in analysis:
                if "bounding_box" not in item:
                    continue

                stamp_id = str(uuid4())
                thumb_path, crop_path = self._create_thumbnail_and_crop(img_path, item["bounding_box"], stamp_id)

                stamp_record = {
                    "stamp_id": stamp_id,
                    "album": album_name,
                    "page_filename": img_path.name,
                    "common_name": item.get("common_name", "Unknown"),
                    "nationality": item.get("country_of_origin", "Unknown"),
                    "year": item.get("estimated_year_of_issue", "Unknown"),
                    "face_value": item.get("face_value", "Unknown"),
                    "condition": item.get("condition", "Unknown"),
                    "initial_description": item.get("description", ""),
                    "confidence": item.get("confidence", 0),
                    "thumbnail_path": thumb_path,
                    "cropped_image_path": crop_path,
                    "deacquired": False
                }
                all_stamps.append(stamp_record)

        if not all_stamps:
            logger.warning("Image analysis phase complete, but no stamps were identified. Skipping CSV creation.")
            return

        df = pd.DataFrame(all_stamps)
        df.to_csv(self.master_csv_path, index=False)
        logger.info(f"Image analysis phase complete. Saved {len(df)} initial records to {self.master_csv_path}")

    def run_philatelic_enrichment_phase(self):
        """
        Enriches the master inventory with detailed philatelic analysis,
        including value, collectibility, and expert remarks.
        """
        logger.info("--- Starting Philatelic Enrichment Phase ---")
        if not self.master_csv_path.exists():
            logger.warning(
                "Master inventory CSV not found. Skipping enrichment phase. Please run image analysis first.")
            return

        try:
            df = pd.read_csv(self.master_csv_path)
            if df.empty:
                logger.info("Master inventory is empty. Nothing to enrich. Skipping phase.")
                return
        except pd.errors.EmptyDataError:
            logger.warning("Master inventory CSV is empty. Skipping enrichment phase.")
            return

        enriched_records = []

        for _, row in df.iterrows():
            logger.info(f"Enriching stamp: {row['common_name']} ({row['stamp_id']})")
            prompt = f"""You are a world-class philatelic expert. Given the following initial data for a postage stamp, provide a detailed analysis.
Initial Data:
- Name: {row['common_name']}
- Country: {row['nationality']}
- Year: {row['year']}
- Description: {row['initial_description']}

Your task is to return a JSON object with the following fields:
- "estimated_value_low": An integer representing the low-end market value in USD.
- "estimated_value_high": An integer representing the high-end market value in USD.
- "detailed_description": An expanded description including historical context, design elements, and printing details.
- "collectibility_notes": Remarks on rarity, demand, and what makes this stamp interesting to collectors.
- "philatelic_remarks": Expert commentary on the stamp's significance in the broader context of philately.

Return only the raw JSON object, without any markdown or wrappers.
"""
            try:
                response = self.client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": "You are a philately expert. Respond with a valid JSON object."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2048,
                    temperature=0.5
                )
                enrichment_data = json.loads(response.choices[0].message.content)

                updated_row = row.to_dict()
                updated_row.update(enrichment_data)
                enriched_records.append(updated_row)

            except Exception as e:
                logger.error(f"Failed to enrich stamp {row['stamp_id']}: {e}")
                enriched_records.append(row.to_dict())

        enriched_df = pd.DataFrame(enriched_records)
        enriched_df.to_csv(self.master_csv_path, index=False)
        logger.info(f"Philatelic enrichment phase complete. Updated master inventory at {self.master_csv_path}")

    def run_clustering_and_summary_phase(self):
        """
        Performs clustering, generates statistics and summaries, and saves the final collection data.
        """
        logger.info("--- Starting Clustering and Summary Phase ---")
        if not self.master_csv_path.exists():
            logger.warning(
                "Master inventory CSV not found. Skipping summary phase. Please run analysis and enrichment first.")
            return

        try:
            df = pd.read_csv(self.master_csv_path)
            if df.empty:
                logger.info("Master inventory is empty. Nothing to summarize. Skipping phase.")
                return
        except pd.errors.EmptyDataError:
            logger.warning("Master inventory CSV is empty. Skipping summary phase.")
            return

        df_active = df[df['deacquired'] != True].copy()

        summaries = {}

        # Top-down: by Album
        logger.info("Generating top-down summaries by Album...")
        for album_name, group in df_active.groupby("album"):
            summaries[f"album_{album_name}"] = self._generate_cluster_summary(album_name, group)

        # Bottom-up: by Country
        logger.info("Generating bottom-up summaries by Country...")
        for country, group in df_active.groupby("nationality"):
            if country == "Unknown": continue
            summaries[f"country_{country}"] = self._generate_cluster_summary(country, group)

        # --- Final Collection-Wide Analysis ---
        logger.info("Generating final collection-wide analysis...")
        collection_stats = self._calculate_collection_stats(df_active)
        summaries["collection_wide"] = self._generate_cluster_summary("Entire Collection", df_active)

        # --- Save Final Output ---
        final_data = {
            "collection_origin_story": COLLECTION_ORIGIN_STORY,
            "collection_statistics": collection_stats,
            "philatelic_summaries": summaries,
            "master_inventory": df.to_dict(orient='records')
        }

        with self.final_json_path.open("w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=4)

        logger.info(f"Clustering and summary phase complete. Saved final data to {self.final_json_path}")

    def _calculate_collection_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates high-level statistics for a given DataFrame of stamps."""
        all_years_raw = [s for s in df['year'].dropna() if s != "Unknown"]
        all_years_clean = []
        for y in all_years_raw:
            match = re.search(r'\b(1[7-9]\d{2}|20\d{2})\b', str(y))
            if match:
                all_years_clean.append(int(match.group(0)))

        total_low = df['estimated_value_low'].sum() if 'estimated_value_low' in df.columns else 0
        total_high = df['estimated_value_high'].sum() if 'estimated_value_high' in df.columns else 0

        return {
            "item_count": len(df),
            "album_count": df['album'].nunique(),
            "countries_represented": df['nationality'].nunique(),
            "year_range": f"{min(all_years_clean)} - {max(all_years_clean)}" if all_years_clean else "N/A",
            "total_value_low": total_low,
            "total_value_high": total_high,
            "condition_distribution": df['condition'].value_counts().to_dict()
        }

    def _generate_cluster_summary(self, cluster_name: str, cluster_df: pd.DataFrame) -> Dict[str, Any]:
        """Generates statistics and a narrative summary for a given cluster of stamps."""
        logger.info(f"  Summarizing cluster: {cluster_name}")

        stats = self._calculate_collection_stats(cluster_df)

        stamps_json_str = cluster_df.to_json(orient='records', indent=2)
        prompt = f"""You are a world-class philatelic expert.
Analyze the following collection of stamps, which represents the '{cluster_name}' cluster.
Provide a concise yet comprehensive summary for a knowledgeable colleague. Focus on:
- Scope and Theme: The range, diversity, and central focus of this cluster.
- Highlights: Notable items, valuable stamps, or particularly interesting features.
- Gaps: Any obvious missing areas or weaknesses.
- Overall Impression: Your final perspective or advice on this specific cluster.

Respond with plain text only. No introductions or salutations.

Stamp Data:
{stamps_json_str}
"""
        try:
            response = self.client.chat.completions.create(
                model="grok-3",
                messages=[
                    {"role": "system", "content": "You are a philately expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1024
            )
            narrative = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Could not generate narrative for cluster {cluster_name}: {e}")
            narrative = "Narrative summary could not be generated."

        return {"statistics": stats, "narrative_summary": narrative}


def main():
    """Main function to run the philately processing pipeline."""
    parser = argparse.ArgumentParser(description='Philately Processor v3.0')
    parser.add_argument('--image-dir', type=str, default="stamps",
                        help='Directory containing stamp images organized in album folders.')
    parser.add_argument('--output-dir', type=str, default="output", help='Directory to save all outputs.')
    parser.add_argument('--confidence-threshold', type=int, default=5,
                        help='Confidence score (1-7) below which to trigger re-analysis with a high-cost model.')
    parser.add_argument('--max-images', type=int, default=None,
                        help='Limit the number of images to process for testing purposes.')

    # MODIFICATION: Add arguments for model selection
    parser.add_argument('--low-cost-model', type=str, default="grok-2-vision-1212",
                        help='The vision model to use for the initial, low-cost pass.')
    parser.add_argument('--high-cost-model', type=str, default="gemini-1.5-pro-latest",
                        help='The vision model to use for the high-confidence re-analysis pass.')

    # Phase control
    parser.add_argument('--run-analysis', action='store_true', help='Run only the image analysis phase.')
    parser.add_argument('--run-enrichment', action='store_true', help='Run only the philatelic enrichment phase.')
    parser.add_argument('--run-summaries', action='store_true', help='Run only the clustering and summary phase.')

    args = parser.parse_args()

    processor = PhilatelyProcessor(image_dir=Path(args.image_dir), output_dir=Path(args.output_dir))

    run_all = not (args.run_analysis or args.run_enrichment or args.run_summaries)

    if run_all or args.run_analysis:
        # MODIFICATION: Pass the model names to the analysis phase
        processor.run_image_analysis_phase(
            args.confidence_threshold,
            max_images=args.max_images,
            low_cost_model=args.low_cost_model,
            high_cost_model=args.high_cost_model
        )

    if run_all or args.run_enrichment:
        processor.run_philatelic_enrichment_phase()

    if run_all or args.run_summaries:
        processor.run_clustering_and_summary_phase()

    logger.info("Philately processing finished.")


if __name__ == "__main__":
    main()