import os
import json
import logging
import sys
import base64
import re
import textwrap
from uuid import uuid4
from pathlib import Path
import cv2
import pandas as pd
# The direct OpenAI client is no longer needed
from dotenv import load_dotenv
import argparse
from typing import Dict, Any, List, Tuple, Union

# New import for the model router
import litellm

# --- Configuration & Logging ---
load_dotenv()

# Logging is now configured in main() based on the --debug flag
logger = logging.getLogger(__name__)

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
        self.public_image_dir = image_dir
        self.public_output_dir = output_dir
        self.private_data_dir = Path('private_data')
        self.use_private_data = self.private_data_dir.exists()

        if self.use_private_data:
            logger.info("Private data directory found. Using private data.")
            self.image_dir = self.private_data_dir / 'stamps'
            self.output_dir = self.private_data_dir / 'output'
        else:
            logger.info("Private data directory not found. Using public data.")
            self.image_dir = self.public_image_dir
            self.output_dir = self.public_output_dir

        self.master_csv_path = self.output_dir / "master_inventory.csv"
        self.cropped_dir = self.output_dir / "cropped_entities"
        self.thumbnail_dir = self.output_dir / "thumbnails"
        self.raw_responses_dir = self.output_dir / "raw_api_responses"
        self.final_json_path = self.output_dir / "stamp_inventory.json"
        self.high_value_reports_dir = self.output_dir / "high_value_reports"
        self.high_value_summary_path = self.output_dir / "high_value_summary.csv"
        # MODIFICATION: Added path for the new false positive report
        self.false_positive_report_path = self.output_dir / "false_positive_check_report.csv"

        # Create necessary directories
        for d in [self.output_dir, self.cropped_dir, self.thumbnail_dir, self.raw_responses_dir,
                  self.high_value_reports_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # The API client is now managed by litellm, which reads keys from .env
        # We can add a check here to ensure at least one key is available.
        if not (os.getenv("XAI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
            logger.error("No API keys (e.g., XAI_API_KEY, GOOGLE_API_KEY) found in environment. LLM calls will fail.")

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

    def _create_thumbnail_and_crop(self, img_path: Path, bbox: Union[Dict, List], stamp_id: str) -> Tuple[
        str | None, str | None]:
        """
        Creates a thumbnail and a cropped image from a bounding box.
        Handles both dictionary and list formats for the bounding box.
        """
        try:
            img = cv2.imread(str(img_path))
            if img is None:
                logger.warning(f"Failed to read image for cropping: {img_path}")
                return None, None

            # Handle both dict and list formats for bbox
            if isinstance(bbox, dict):
                x, y, w, h = bbox.get('x', 0), bbox.get('y', 0), bbox.get('width', 0), bbox.get('height', 0)
            elif isinstance(bbox, list) and len(bbox) == 4:
                x, y, w, h = bbox[0], bbox[1], bbox[2], bbox[3]
            else:
                logger.error(f"Unsupported bounding box format for {img_path}: {bbox}")
                return None, None

            # Create thumbnail
            thumbnail = cv2.resize(img, (100, 100), interpolation=cv2.INTER_AREA)
            thumbnail_path = self.thumbnail_dir / f"{stamp_id}_thumbnail.jpg"
            cv2.imwrite(str(thumbnail_path), thumbnail)

            # Create cropped image
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

    def _log_vision_request(self, model: str, messages: list, context: str):
        """Logs the request payload for a vision model call, redacting image data."""
        if logger.isEnabledFor(logging.DEBUG):
            # Create a deep copy for logging to avoid modifying the original payload
            log_messages = json.loads(json.dumps(messages))

            # Find and redact image data
            for msg in log_messages:
                if msg.get("role") == "user" and isinstance(msg.get("content"), list):
                    for content_part in msg["content"]:
                        if content_part.get("type") == "image_url" and "image_url" in content_part:
                            url = content_part["image_url"].get("url", "")
                            if "base64," in url:
                                # Estimate original size from base64 string
                                image_b64_len = len(url.split("base64,")[1])
                                # Base64 is ~4/3 size of original bytes
                                image_kb = (image_b64_len * 3 / 4) / 1024
                                image_log_msg = "apparently proper image" if image_kb > 50 else f"image data ({image_kb:.1f}KB)"
                                content_part["image_url"]["url"] = f"<redacted: {image_log_msg}>"

            logger.debug(
                f"Calling vision model '{model}' for {context}. Payload:\n{json.dumps(log_messages, indent=2)}")

    def _get_request_hash(self, model: str, messages: list) -> str:
        """Creates a SHA256 hash of the model and messages to use as a cache key."""
        import hashlib
        m = hashlib.sha256()
        m.update(model.encode())
        m.update(json.dumps(messages, sort_keys=True).encode())
        return m.hexdigest()

    def _call_vision_model(self, image_base64: str, model: str) -> List[Dict[str, Any]] | None:
        """Analyzes an image using a specified vision model via litellm."""
        prompt = """Your response MUST be a valid JSON array of objects.
Identify and describe each distinct stamp or philatelic item on this page.
Note that some stamps are mounted in albums whose pages contain black and white drawings of stamps. The actual stamps are mounted on top of the drawings. Be careful to only include mounted stamps. Mounted stamps are in color, have perforated images, and are above the plane of the album page.

For each item, provide a JSON object with the following schema:
{
  "common_name": "string",
  "country_of_origin": "string",
  "estimated_year_of_issue": "string",
  "face_value": "string",
  "condition": "string",
  "description": "string",
  "bounding_box": {"x": <integer>, "y": <integer>, "width": <integer>, "height": <integer>},
  "confidence": <integer from 1 to 7>
}

The final item in the array should be a "Collection Overview" object with a description summarizing the page.
Do not wrap your response in markdown. Return only the raw JSON array.
"""
        messages = [
            {"role": "system", "content": "You are a philately expert. Respond with a valid JSON array."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]}
        ]

        request_hash = self._get_request_hash(model, messages)
        cache_path = self.raw_responses_dir / f"{request_hash}.json"

        if cache_path.exists():
            logger.info(f"Found cached response for vision model {model}.")
            with cache_path.open("r", encoding="utf-8") as f:
                return json.load(f)

        # MODIFICATION: Use the new centralized logging function.
        self._log_vision_request(model, messages, "image analysis")

        try:
            response = litellm.completion(
                model=model,
                messages=messages,
                max_tokens=4096
            )
            raw_content = response.choices[0].message.content

            logger.debug(
                f"Raw analysis response from model '{model}':\n---RESPONSE START---\n{raw_content}\n---RESPONSE END---")

            if not raw_content:
                logger.warning(f"Model {model} returned empty content. Cannot parse JSON.")
                return None

            cleaned_content = re.search(r'\[.*\]', raw_content, re.DOTALL)
            if not cleaned_content:
                logger.warning(f"Could not find a JSON array in the model's response for model {model}.")
                return None
            
            result = json.loads(cleaned_content.group(0))
            with cache_path.open("w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)

            return result
        except Exception as e:
            logger.error(f"Analysis with model {model} failed: {e}")
            return None

    def run_image_analysis_phase(self, confidence_threshold: int, max_images: int | None = None,
                                 low_cost_model: str = "gemini/gemini-1.5-flash-latest",
                                 high_cost_model: str = "gemini/gemini-1.5-pro-latest"):
        """
        Runs the two-pass image analysis using specified models, skipping already processed, high-confidence images.
        """
        logger.info("--- Starting Image Analysis Phase ---")

        # Load existing inventory if it exists to avoid re-processing.
        existing_stamps_df = pd.DataFrame()
        if self.master_csv_path.exists():
            try:
                existing_stamps_df = pd.read_csv(self.master_csv_path)
                if not existing_stamps_df.empty:
                    logger.info(f"Loaded {len(existing_stamps_df)} records from existing master inventory.")
            except pd.errors.EmptyDataError:
                logger.warning("Existing master inventory is empty.")
            except Exception as e:
                logger.error(f"Could not read existing master inventory: {e}")

        processed_pages = {}
        if not existing_stamps_df.empty:
            processed_pages = {name: group.to_dict('records') for name, group in
                               existing_stamps_df.groupby('page_filename')}

        all_stamps_in_run = []
        pages_in_this_run = set()

        image_patterns = ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]
        image_files = []
        for pattern in image_patterns:
            image_files.extend(self.image_dir.rglob(pattern))

        image_files = sorted(list(set(image_files)))

        if not image_files:
            logger.warning(f"No image files found in the specified directory: {self.image_dir}")
            return

        if max_images:
            logger.info(f"Limiting processing to the first {max_images} of {len(image_files)} found images.")
            image_files = image_files[:max_images]

        for img_path in image_files:
            album_name = img_path.parent.name
            page_filename = img_path.name
            pages_in_this_run.add(page_filename)

            # Check if the page is already processed and meets the confidence threshold.
            if page_filename in processed_pages:
                stamps_on_page = processed_pages[page_filename]
                # Ensure all stamps on the page have a confidence score.
                all_confident = all(
                    'confidence' in stamp and stamp.get('confidence', 0) >= confidence_threshold
                    for stamp in stamps_on_page if stamp.get('common_name') != 'Collection Overview'
                )
                if all_confident and any(s.get('common_name') != 'Collection Overview' for s in stamps_on_page):
                    logger.info(f"Skipping already analyzed page with sufficient confidence: {page_filename}")
                    all_stamps_in_run.extend(stamps_on_page)
                    continue
                else:
                    logger.info(f"Re-analyzing page with low-confidence or missing stamps: {page_filename}")
            else:
                logger.info(f"Processing new image: {page_filename}")

            image_base64 = self._preprocess_image(img_path)
            if not image_base64:
                continue

            logger.info(f"  Pass 1: Analyzing with low-cost model ({low_cost_model})...")
            analysis = self._call_vision_model(image_base64, low_cost_model)
            if not analysis:
                continue

            needs_reanalysis = any(
                item.get("confidence", 0) < confidence_threshold and "bounding_box" in item
                for item in analysis
            )

            if needs_reanalysis:
                logger.info(
                    f"  Low confidence detected. Pass 2: Re-analyzing with high-cost model ({high_cost_model})...")
                analysis = self._call_vision_model(image_base64, high_cost_model)
                if not analysis:
                    continue

            for item in analysis:
                if "bounding_box" not in item and item.get("common_name") != "Collection Overview":
                    continue

                stamp_id = str(uuid4())
                thumb_path, crop_path = None, None
                if "bounding_box" in item:
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
                all_stamps_in_run.append(stamp_record)

        # Combine results: take the new/updated records from this run, plus old records from pages not processed.
        final_inventory_records = all_stamps_in_run
        if not existing_stamps_df.empty:
            unprocessed_df = existing_stamps_df[~existing_stamps_df['page_filename'].isin(pages_in_this_run)]
            if not unprocessed_df.empty:
                final_inventory_records.extend(unprocessed_df.to_dict('records'))
                logger.info(f"Preserving {len(unprocessed_df)} records from pages not included in this run.")

        if not final_inventory_records:
            logger.warning(
                "Image analysis phase complete, but no stamps were identified or kept. No CSV will be written.")
            return

        df = pd.DataFrame(final_inventory_records)
        df.to_csv(self.master_csv_path, index=False)
        logger.info(f"Image analysis phase complete. Saved {len(df)} total records to {self.master_csv_path}")

    def run_philatelic_enrichment_phase(self, narrative_model: str):
        """
        Enriches the master inventory with detailed philatelic analysis.
        """
        logger.info("--- Starting Philatelic Enrichment Phase ---")
        if not self.master_csv_path.exists():
            logger.warning("Master inventory CSV not found. Skipping enrichment phase.")
            return

        try:
            df = pd.read_csv(self.master_csv_path)
            if df.empty:
                logger.info("Master inventory is empty. Nothing to enrich.")
                return
        except pd.errors.EmptyDataError:
            logger.warning("Master inventory CSV is empty. Skipping enrichment phase.")
            return

        enriched_records = []
        enrichment_cols = [
            "estimated_value_low", "estimated_value_high", "detailed_description",
            "collectibility_notes", "philatelic_remarks"
        ]
        has_enrichment_cols = all(col in df.columns for col in enrichment_cols)

        for _, row in df.iterrows():
            # Skip non-stamp records like 'Collection Overview'
            if row['common_name'] == 'Collection Overview':
                enriched_records.append(row.to_dict())  # Append the original row without enrichment
                continue

            # Check if the stamp is already satisfactorily enriched
            if has_enrichment_cols:
                is_enriched = (
                        pd.notna(row.get("estimated_value_low")) and
                        pd.notna(row.get("detailed_description")) and row.get("detailed_description", "") != ""
                )
                if is_enriched:
                    logger.info(f"Skipping already enriched stamp: {row['common_name']} ({row['stamp_id']})")
                    enriched_records.append(row.to_dict())
                    continue

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
- "detailed_description": An expanded description including historical context, design elements, printing details, and observed condition.
- "collectibility_notes": Remarks on rarity, demand, and what makes this stamp interesting to collectors.
- "philatelic_remarks": Expert commentary on the stamp's significance in the broader context of philately.

Return only the raw JSON object, without any markdown or wrappers. The response must be complete and fit entirely within the context window.
"""
            messages = [
                {"role": "system", "content": "You are a philately expert. Respond with a valid JSON object."},
                {"role": "user", "content": prompt}
            ]

            request_hash = self._get_request_hash(narrative_model, messages)
            cache_path = self.raw_responses_dir / f"{request_hash}.json"

            if cache_path.exists():
                logger.info(f"Found cached response for enrichment of stamp {row['stamp_id']}.")
                with cache_path.open("r", encoding="utf-8") as f:
                    enrichment_data = json.load(f)
                
                updated_row = row.to_dict()
                updated_row.update(enrichment_data)
                enriched_records.append(updated_row)
                continue

            raw_content = None
            try:
                # Using litellm to call the text model and enforce JSON output
                response = litellm.completion(
                    model=narrative_model,
                    messages=messages,
                    max_tokens=4096,
                    temperature=0.5,
                    response_format={"type": "json_object"}
                )
                raw_content = response.choices[0].message.content
                if not raw_content:
                    raise json.JSONDecodeError("Model returned empty content", "", 0)

                enrichment_data = json.loads(raw_content)

                with cache_path.open("w", encoding="utf-8") as f:
                    json.dump(enrichment_data, f, indent=2)

                updated_row = row.to_dict()
                updated_row.update(enrichment_data)
                enriched_records.append(updated_row)

            except json.JSONDecodeError as e:
                logger.error(f"Failed to enrich stamp {row['stamp_id']} due to JSON decoding error: {e}")
                if raw_content:
                    logger.error(f"  -> Raw content that failed to parse: {raw_content}")
                enriched_records.append(row.to_dict())
            except Exception as e:
                logger.error(f"Failed to enrich stamp {row['stamp_id']} with a general error: {e}")
                enriched_records.append(row.to_dict())

        enriched_df = pd.DataFrame(enriched_records)
        enriched_df.to_csv(self.master_csv_path, index=False)
        logger.info(f"Philatelic enrichment phase complete. Updated master inventory at {self.master_csv_path}")

    def run_clustering_and_summary_phase(self, narrative_model: str, collection_summary_model: str,
                                         collection_only: bool = False):
        """
        Performs clustering, generates statistics and summaries, and saves the final collection data.
        If collection_only is True, it will only generate the final collection-wide summary.
        """
        logger.info("--- Starting Clustering and Summary Phase ---")
        if collection_only:
            logger.info("Running in collection-summary-only mode.")

        if not self.master_csv_path.exists():
            logger.warning("Master inventory CSV not found. Skipping summary phase.")
            return

        try:
            df = pd.read_csv(self.master_csv_path)
            if df.empty:
                logger.info("Master inventory is empty. Nothing to summarize.")
                return
        except pd.errors.EmptyDataError:
            logger.warning("Master inventory CSV is empty. Skipping summary phase.")
            return

        df_active = df[df['deacquired'] != True].copy()
        
        final_data = {}
        if self.final_json_path.exists():
            with self.final_json_path.open("r", encoding="utf-8") as f:
                final_data = json.load(f)
        
        summaries = final_data.get("philatelic_summaries", {})

        if not collection_only:
            # Top-down: by Album
            logger.info("Generating top-down summaries by Album...")
            for album_name, group in df_active.groupby("album"):
                if f"album_{album_name}" not in summaries:
                    summaries[f"album_{album_name}"] = self._generate_cluster_summary(album_name, group, narrative_model)

            # Bottom-up: by Country
            logger.info("Generating bottom-up summaries by Country...")
            for country, group in df_active.groupby("nationality"):
                if country == "Unknown" or pd.isna(country): continue
                if f"country_{country}" not in summaries:
                    summaries[f"country_{country}"] = self._generate_cluster_summary(country, group, narrative_model)

        # --- Final Collection-Wide Analysis ---
        logger.info("Generating final collection-wide analysis...")
        # Filter out overview rows before calculating final stats
        final_stats_df = df_active[df_active['common_name'] != 'Collection Overview']
        collection_stats = self._calculate_collection_stats(final_stats_df)
        # Use the dedicated high-context model for the entire collection summary
        summaries["collection_wide"] = self._generate_cluster_summary("Entire Collection", final_stats_df,
                                                                      collection_summary_model)

        # --- Save Final Output ---
        final_data["collection_origin_story"] = COLLECTION_ORIGIN_STORY
        final_data["collection_statistics"] = collection_stats
        final_data["philatelic_summaries"] = summaries
        final_data["master_inventory"] = df.to_dict(orient='records')

        with self.final_json_path.open("w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=4)

        logger.info(f"Clustering and summary phase complete. Saved final data to {self.final_json_path}")

    def _calculate_collection_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates high-level statistics for a given DataFrame of stamps."""
        # Filter out any remaining overview rows just in case
        df_stamps_only = df[df['common_name'] != 'Collection Overview'].copy()

        if df_stamps_only.empty:
            return {
                "item_count": 0, "album_count": 0, "countries_represented": 0,
                "year_range": "N/A", "total_value_low": 0, "total_value_high": 0,
                "condition_distribution": {}
            }

        all_years_raw = [s for s in df_stamps_only['year'].dropna() if s != "Unknown"]
        all_years_clean = []
        for y in all_years_raw:
            match = re.search(r'\b(1[7-9]\d{2}|20\d{2})\b', str(y))
            if match:
                all_years_clean.append(int(match.group(0)))

        total_low = df_stamps_only[
            'estimated_value_low'].sum() if 'estimated_value_low' in df_stamps_only.columns else 0
        total_high = df_stamps_only[
            'estimated_value_high'].sum() if 'estimated_value_high' in df_stamps_only.columns else 0

        return {
            "item_count": len(df_stamps_only),
            "album_count": df_stamps_only['album'].nunique(),
            "countries_represented": df_stamps_only['nationality'].nunique(),
            "year_range": f"{min(all_years_clean)} - {max(all_years_clean)}" if all_years_clean else "N/A",
            "total_value_low": total_low,
            "total_value_high": total_high,
            "condition_distribution": df_stamps_only['condition'].value_counts().to_dict()
        }

    def _generate_cluster_summary(self, cluster_name: str, cluster_df: pd.DataFrame, narrative_model: str) -> Dict[
        str, Any]:
        """Generates statistics and a narrative summary for a given cluster of stamps."""
        logger.info(f"  Summarizing cluster: {cluster_name} using model {narrative_model}")

        # Ensure we only summarize actual stamps, not overview rows
        cluster_stamps_df = cluster_df[cluster_df['common_name'] != 'Collection Overview'].copy()

        if cluster_stamps_df.empty:
            return {"statistics": self._calculate_collection_stats(cluster_stamps_df),
                    "narrative_summary": "No stamps to summarize for this cluster."}

        stats = self._calculate_collection_stats(cluster_stamps_df)
        stamps_json_str = cluster_stamps_df.to_json(orient='records', indent=2)
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
        # Increased token limit for summary generation
        max_tokens_for_call = 8192
        logger.debug(
            f"Generating summary for '{cluster_name}'. Input data size: ~{len(stamps_json_str)} chars. Max output tokens: {max_tokens_for_call}.")

        messages = [
            {"role": "system", "content": "You are a philately expert."},
            {"role": "user", "content": prompt}
        ]

        request_hash = self._get_request_hash(narrative_model, messages)
        cache_path = self.raw_responses_dir / f"{request_hash}.json"

        if cache_path.exists():
            logger.info(f"Found cached response for cluster summary '{cluster_name}'.")
            with cache_path.open("r", encoding="utf-8") as f:
                narrative = json.load(f)
            return {"statistics": stats, "narrative_summary": narrative}

        try:
            response = litellm.completion(
                model=narrative_model,
                messages=messages,
                max_tokens=max_tokens_for_call
            )
            # Safely access the message content
            raw_narrative = response.choices[0].message.content
            if raw_narrative:
                narrative = raw_narrative.strip()
                with cache_path.open("w", encoding="utf-8") as f:
                    json.dump(narrative, f, indent=2)
            else:
                # Add enhanced warning for 'length' finish reason
                finish_reason = response.choices[0].finish_reason
                logger.warning(
                    f"Model returned empty content for cluster {cluster_name}. Finish reason: {finish_reason}")
                if finish_reason == 'length':
                    logger.warning(
                        f"  -> This 'length' finish reason indicates the model stopped because it reached the `max_tokens` limit ({max_tokens_for_call}). "
                        f"The input data size was ~{len(stamps_json_str)} characters. The output was likely truncated, resulting in an empty message."
                    )
                narrative = "Narrative summary could not be generated due to an empty model response."
        except Exception as e:
            logger.error(f"Could not generate narrative for cluster {cluster_name}: {e}")
            narrative = "Narrative summary could not be generated."

        return {"statistics": stats, "narrative_summary": narrative}

    def run_high_value_report_phase(self, value_threshold: int = 1000):
        """
        Identifies stamps above a certain value, generates a summary CSV,
        and creates individual markdown reports for inspection.
        """
        logger.info("--- Starting High-Value Stamp Report Phase ---")
        if not self.master_csv_path.exists():
            logger.warning("Master inventory CSV not found. Skipping high-value report phase.")
            return

        try:
            df = pd.read_csv(self.master_csv_path)
            if df.empty:
                logger.info("Master inventory is empty. Nothing to report.")
                return
        except pd.errors.EmptyDataError:
            logger.warning("Master inventory CSV is empty. Skipping high-value report phase.")
            return

        if 'estimated_value_high' not in df.columns:
            logger.warning(
                "Column 'estimated_value_high' not found. Cannot generate high-value report. Please run enrichment phase first.")
            return

        # Ensure value column is numeric, coercing errors and dropping NaNs
        df['estimated_value_high'] = pd.to_numeric(df['estimated_value_high'], errors='coerce')
        df.dropna(subset=['estimated_value_high'], inplace=True)

        high_value_df = df[df['estimated_value_high'] > value_threshold].copy()

        if high_value_df.empty:
            logger.info(f"No stamps found with a high estimated value greater than ${value_threshold}.")
            return

        # --- 1. Generate Summary Table (CSV) ---
        logger.info(
            f"Found {len(high_value_df)} stamps with high value > ${value_threshold}. Generating summary table...")
        summary_columns = [
            'stamp_id',
            'common_name',
            'estimated_value_high',
            'detailed_description',
            'philatelic_remarks',
            'collectibility_notes',
            'page_filename',
            'cropped_image_path'
        ]
        # Ensure all columns exist in the dataframe, fill with NA if not
        for col in summary_columns:
            if col not in high_value_df.columns:
                high_value_df[col] = pd.NA

        summary_df = high_value_df[summary_columns]
        summary_df.to_csv(self.high_value_summary_path, index=False)
        logger.info(f"High-value summary table saved to: {self.high_value_summary_path}")

        # --- 2. Generate Individual Markdown Reports ---
        logger.info("Generating individual Markdown reports for each high-value stamp...")

        for _, row in high_value_df.iterrows():
            report_name = f"high_value_report_{row['stamp_id']}.md"
            report_path = self.high_value_reports_dir / report_name

            # Make sure paths in the report are relative to the output directory for portability
            cropped_path_str = str(row.get('cropped_image_path', 'N/A'))

            # Use a Markdown table for key info
            report_content = textwrap.dedent(f"""
            # High-Value Stamp Report: {row.get('common_name', 'N/A')}

            **Estimated Value (High):** `${int(row.get('estimated_value_high', 0))}`

            !Cropped Image

            ---

            ## Key Information

            | Attribute              | Value                                      |
            | :--------------------- | :----------------------------------------- |
            | **Stamp ID**           | `{row.get('stamp_id', 'N/A')}`             |
            | **Album**              | {row.get('album', 'N/A')}                  |
            | **Original Page File** | {row.get('page_filename', 'N/A')}          |
            | **Cropped Image Path** | `{cropped_path_str}`                       |

            ---

            ## Philatelic Analysis

            ### Detailed Description
            {row.get('detailed_description', 'No detailed description available.')}

            ### Collectibility Notes
            {row.get('collectibility_notes', 'No collectibility notes available.')}

            ### Philatelic Remarks
            {row.get('philatelic_remarks', 'No philatelic remarks available.')}
            """)

            try:
                report_path.write_text(report_content.strip(), encoding='utf-8')
                logger.info(f"  -> Saved report: {report_path}")
            except Exception as e:
                logger.error(f"Failed to write report for stamp {row['stamp_id']}: {e}")

        logger.info(f"High-value report phase complete. Individual reports saved in {self.high_value_reports_dir}")

    def _verify_is_real_stamp(self, image_base64: str, model: str) -> Tuple[bool, str]:
        """
        Uses a vision model to verify if an image is a real, mounted stamp or a printed illustration.
        """
        # MODIFICATION: Prompt now requests a JSON array.
        prompt = """You are a philatelic verification expert. Your task is to determine if the provided image is of a real, physical, mounted postage stamp or if it is a flat, printed illustration on an album page.

Characteristics of a REAL, MOUNTED STAMP:
- It is in color.
- It has perforated or cut edges.
- It appears to be physically placed on top of the page, possibly showing some 3D depth, shadow, or texture.

Characteristics of a PRINTED ILLUSTRATION:
- It is typically black and white.
- The edges are printed lines, not perforations.
- It is flat and part of the page itself.

Based on these criteria, analyze the image and return a JSON array with your verdict. Your response MUST be a valid JSON array containing exactly two elements:
1. A boolean value: `true` if it is a real stamp, `false` otherwise.
2. A string containing a brief explanation for your decision.

Example format: `[true, "This appears to be a genuine, mounted stamp with clear perforations and color."]`

Return only the raw JSON array.
"""
        messages = [
            # MODIFICATION: System message updated to reflect new response format.
            {"role": "system",
             "content": "You are a philatelic verification expert. Respond with a valid JSON array of two elements: a boolean and a string."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]}
        ]

        request_hash = self._get_request_hash(model, messages)
        cache_path = self.raw_responses_dir / f"{request_hash}.json"

        if cache_path.exists():
            logger.info(f"Found cached response for stamp verification.")
            with cache_path.open("r", encoding="utf-8") as f:
                result = json.load(f)
                return result[0], result[1]

        # MODIFICATION: Use the new centralized logging function.
        self._log_vision_request(model, messages, "stamp verification")

        try:
            response = litellm.completion(
                model=model,
                messages=messages,
                max_tokens=4096          )
            raw_content = response.choices[0].message.content

            logger.debug(
                f"Raw verification response from model '{model}':\n---RESPONSE START---\n{raw_content}\n---RESPONSE END---")

            if not raw_content:
                logger.warning(f"Model {model} returned empty content during verification. Assuming stamp is real.")
                return True, "Verification failed due to empty model response."

            cleaned_content_match = re.search(r'\[.*\]', raw_content, re.DOTALL)
            if not cleaned_content_match:
                logger.error(
                    f"Could not find a JSON array in verification response from model {model}. Raw response: {raw_content}")
                return True, "Verification failed due to invalid response format."

            result = json.loads(cleaned_content_match.group(0))

            if isinstance(result, list) and len(result) == 2 and isinstance(result[0], bool) and isinstance(result[1],
                                                                                                            str):
                is_real = result[0]
                reason = result[1]
                with cache_path.open("w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                return is_real, reason
            else:
                logger.error(
                    f"Verification response from model {model} was not a two-element array [boolean, string]. Got: {result}")
                return True, "Verification failed due to unexpected data structure."

        except Exception as e:
            logger.error(f"Failed to verify stamp image with model {model}: {e}")
            # Default to assuming it's real to avoid incorrectly marking valid stamps
            return True, "Verification process failed."

    def run_false_positive_check_phase(self, high_cost_model: str, value_threshold: int = 1000,
                                       check_limit: int = 5):
        """
        Re-examines high-value stamps to identify and mark false positives (e.g., album illustrations),
        and incorporates the verification results into the master inventory and a summary report.
        """
        logger.info("--- Starting False Positive Check Phase for High-Value Stamps ---")
        if not self.master_csv_path.exists():
            logger.warning("Master inventory CSV not found. Skipping false positive check.")
            return

        try:
            df = pd.read_csv(self.master_csv_path)
            if df.empty:
                logger.info("Master inventory is empty. Nothing to check.")
                return
        except pd.errors.EmptyDataError:
            logger.warning("Master inventory CSV is empty. Skipping phase.")
            return

        if 'estimated_value_high' not in df.columns:
            logger.warning(
                "Column 'estimated_value_high' not found. Cannot run check. Please run enrichment phase first.")
            return

        # MODIFICATION: Ensure new columns exist for verification data, initialize with pd.NA
        if 'is_verified_real' not in df.columns:
            df['is_verified_real'] = pd.NA
        if 'verification_reason' not in df.columns:
            df['verification_reason'] = pd.NA
        # Convert to a nullable boolean type to handle items that haven't been checked
        df['is_verified_real'] = df['is_verified_real'].astype('boolean')

        # Ensure value column is numeric before sorting
        df['estimated_value_high'] = pd.to_numeric(df['estimated_value_high'], errors='coerce')

        # Filter for stamps to check: high value, not deacquired, and has a valid value
        stamps_to_check_df = df[
            (df['estimated_value_high'] > value_threshold) &
            (df['deacquired'] != True)
            ].copy()

        if stamps_to_check_df.empty:
            logger.info(f"No active stamps found with a value > ${value_threshold} to check.")
            return

        # Sort by value to check the most valuable items first
        stamps_to_check_df.sort_values(by='estimated_value_high', ascending=False, inplace=True)

        # Apply the check limit
        if check_limit > 0:
            logger.info(
                f"Found {len(stamps_to_check_df)} eligible high-value stamps. Limiting check to the top {check_limit}.")
            stamps_to_check_df = stamps_to_check_df.head(check_limit)
        else:
            logger.info(f"Found {len(stamps_to_check_df)} eligible high-value stamps. Checking all of them.")

        # List to store data for the summary report
        report_records = []

        for _, row in stamps_to_check_df.iterrows():
            stamp_id = row['stamp_id']
            cropped_image_path_str = row.get('cropped_image_path')

            if not cropped_image_path_str or pd.isna(cropped_image_path_str):
                logger.warning(f"Skipping stamp {stamp_id} as it has no cropped image path.")
                continue

            cropped_image_path = self.output_dir / cropped_image_path_str
            if not cropped_image_path.exists():
                logger.debug(f"Cropped image not found for stamp {stamp_id} at {cropped_image_path}")
                continue

            logger.debug(f"Found cropped image for verification: {cropped_image_path}")
            logger.info(f"  Verifying stamp: {row['common_name']} (ID: {stamp_id})")

            image_base64 = self._preprocess_image(cropped_image_path)
            if not image_base64:
                continue

            is_real, reason = self._verify_is_real_stamp(image_base64, high_cost_model)

            # Find the index in the main dataframe to update it
            stamp_index = df.index[df['stamp_id'] == stamp_id].tolist()
            if not stamp_index:
                continue
            idx = stamp_index[0]

            # MODIFICATION: Store verification results in the master inventory
            df.loc[idx, 'is_verified_real'] = is_real
            df.loc[idx, 'verification_reason'] = reason

            # Prepare a record for the summary report
            report_record = {
                'stamp_id': stamp_id,
                'common_name': row['common_name'],
                'estimated_value_high': row['estimated_value_high'],
                'page_filename': row['page_filename'],
                'is_verified_real': is_real,
                'cropped_image_path': cropped_image_path_str,
                'verification_reason': reason,
                'action_taken': 'None'
            }

            if not is_real:
                logger.warning(f"    -> FALSE POSITIVE DETECTED for stamp {stamp_id}. Reason: {reason}")
                df.loc[idx, 'deacquired'] = True

                remarks = df.loc[idx, 'philatelic_remarks']
                new_remark = f"[False Positive Check]: Marked as illustration. Reason: {reason}"
                if pd.notna(remarks) and isinstance(remarks, str):
                    df.loc[idx, 'philatelic_remarks'] = f"{remarks}\n\n{new_remark}"
                else:
                    df.loc[idx, 'philatelic_remarks'] = new_remark
                report_record['action_taken'] = 'Marked as deacquired (illustration)'
            else:
                logger.info(f"    -> VERIFIED as a real stamp. Reason: {reason}")
                report_record['action_taken'] = 'Verified as real'

            report_records.append(report_record)

        # Save the updated master inventory
        logger.info("Saving updated master inventory with verification results...")
        df.to_csv(self.master_csv_path, index=False)

        # Save the summary report
        if report_records:
            report_df = pd.DataFrame(report_records)
            report_df.to_csv(self.false_positive_report_path, index=False)
            logger.info(f"False positive check summary report saved to: {self.false_positive_report_path}")
        else:
            logger.info("No stamps were checked, so no summary report was generated.")

        logger.info("False positive check phase complete.")

    def run_substack_export_phase(self, num_items: int = 10):
        """
        Generates a CSV file with the top N items formatted for use in a Substack post.
        """
        logger.info("--- Starting Substack Export Phase ---")
        substack_export_path = self.output_dir / "substack_export.csv"

        if not self.master_csv_path.exists():
            logger.error("Master inventory CSV not found. Please run analysis and enrichment phases first.")
            return

        try:
            df = pd.read_csv(self.master_csv_path)
            if df.empty:
                logger.warning("Master inventory is empty. Nothing to export.")
                return
        except pd.errors.EmptyDataError:
            logger.warning("Master inventory CSV is empty. Nothing to export.")
            return

        # Check for necessary columns from enrichment phase
        required_cols = ['estimated_value_high', 'detailed_description', 'collectibility_notes',
                         'philatelic_remarks', 'common_name', 'nationality', 'year', 'cropped_image_path']
        if not all(col in df.columns for col in required_cols):
            logger.error(
                "Master inventory is missing required columns from the enrichment phase. Cannot generate Substack export.")
            return

        # Filter out non-stamps and deacquired items
        df_stamps = df[(df['common_name'] != 'Collection Overview') & (df['deacquired'] != True)].copy()

        # Sort by value to get the most "interesting" items
        df_stamps['estimated_value_high'] = pd.to_numeric(df_stamps['estimated_value_high'], errors='coerce')
        df_stamps.dropna(subset=['estimated_value_high'], inplace=True)
        df_sorted = df_stamps.sort_values(by='estimated_value_high', ascending=False)

        # Limit the number of items
        if num_items > 0:
            df_selected = df_sorted.head(num_items)
            logger.info(f"Selected the top {len(df_selected)} stamps by value for the export.")
        else:
            df_selected = df_sorted
            logger.info(f"Selected all {len(df_selected)} stamps for the export.")

        # Create the Substack-formatted content
        export_data = []
        for _, row in df_selected.iterrows():
            title = row.get('common_name', 'Untitled Stamp')

            subtitle_parts = []
            if pd.notna(row.get('nationality')) and row.get('nationality') != 'Unknown':
                subtitle_parts.append(row['nationality'])
            if pd.notna(row.get('year')) and row.get('year') != 'Unknown':
                subtitle_parts.append(str(row['year']))
            subtitle = " | ".join(subtitle_parts)

            body_parts = [
                f"### Description\n{row.get('detailed_description', 'N/A')}\n",
                f"### Collectibility\n{row.get('collectibility_notes', 'N/A')}\n",
                f"### Philatelic Remarks\n{row.get('philatelic_remarks', 'N/A')}\n",
                f"**Estimated Value (High):** ${int(row.get('estimated_value_high', 0))}"
            ]
            body = "\n---\n\n".join(body_parts)

            # Create tags from nationality and year
            tags = []
            if pd.notna(row.get('nationality')) and row.get('nationality') != 'Unknown':
                tags.append(row['nationality'])
            if pd.notna(row.get('year')) and row.get('year') != 'Unknown':
                year_match = re.search(r'\d{4}', str(row['year']))
                if year_match:
                    tags.append(year_match.group(0))
            tags_str = ", ".join(tags)

            export_data.append({
                'post_title': title,
                'post_subtitle': subtitle,
                'body_markdown': body,
                'local_image_path': row.get('cropped_image_path', ''),
                'tags': tags_str,
                'value_usd': int(row.get('estimated_value_high', 0))
            })

        if not export_data:
            logger.warning("No data to export for Substack.")
            return

        export_df = pd.DataFrame(export_data)
        export_df.to_csv(substack_export_path, index=False, encoding='utf-8')

        logger.info(f"Successfully created Substack export file with {len(export_df)} items at: {substack_export_path}")


    def run_valuation_phase(self, narrative_model: str, chunk_size: int = 1000):
        """Generate a comprehensive valuation of the stamp collection."""
        logger.info("--- Starting Collection Valuation Phase ---")
        if not self.master_csv_path.exists():
            logger.error(f"Master inventory CSV not found at: {self.master_csv_path}")
            return

        try:
            df = pd.read_csv(self.master_csv_path)
            if df.empty:
                logger.warning("Master inventory is empty. Nothing to value.")
                return
        except pd.errors.EmptyDataError:
            logger.warning("Master inventory is empty. Nothing to value.")
            return

        valuation_reports = []
        for i in range(0, len(df), chunk_size):
            chunk_df = df[i:i + chunk_size]
            stamps_json = chunk_df.to_json(orient='records')
            
            system_prompt = """
You            You are a world-class philatelic appraiser with expertise in stamp collection valuation.
            Your task is to provide a detailed and professional valuation report for a stamp collection based on the provided data.
            Structure your response strictly as a formal appraisal with the following sections:
            1. Executive Summary & Collection Analysis:
               Provide a brief overview of the collection, analyzing its overall character, primary strengths (e.g., key high-value items, condition, thematic depth), and weaknesses (e.g., large amounts of common material, condition issues).
            2. Detailed Valuation Scenarios:
               Provide estimated values for the collection in three scenarios:
               a. Value to a Dealer (Wholesale Price):
                  - Definition: Explain this as an immediate cash offer a dealer would make for the collection as a single lot.
                  - Methodology: Describe how a dealer's offer is calculated, considering profit margin, time to sort/sell, and differentiation between key items and bulk material.
                  - Estimate: Provide a final estimated wholesale value range.
               b. Value at Auction (Fair Market Value):
                  - Definition: Explain this as the estimated total price if sold at a specialized philatelic auction, representing fair market value.
                  - Methodology: Outline a lotting strategy to maximize returns (e.g., key items individually, thematic lots for mid-range, box lots for common stamps).
                  - Estimate: Provide a final estimated auction value range (hammer price), noting seller’s commissions are deducted.
               c. Value for Insurance Purposes (Retail Replacement Value):
                  - Definition: Explain this as the highest valuation, representing the full cost to replace the collection by purchasing items from retail dealers.
                  - Methodology: Describe calculation as the cost to make the owner whole in case of total loss, not a resale value.
                  - Estimate: Provide a final high-end range for an insurance policy.
            Use the data provided, especially estimated_value and condition columns, as the primary basis for calculations and analysis.
            """
            user_prompt = f"Based on the provided data from master_stamp_inventory.csv, perform a comprehensive valuation of this chunk of the stamp collection:\n\n{stamps_json}"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            request_hash = self._get_request_hash(narrative_model, messages)
            cache_path = self.raw_responses_dir / f"{request_hash}.txt"

            if cache_path.exists():
                logger.info(f"Found cached response for collection valuation chunk {i // chunk_size + 1}.")
                valuation_report = cache_path.read_text(encoding="utf-8")
            else:
                logger.info(f"Sending valuation request to LLM for chunk {i // chunk_size + 1}...")
                try:
                    response = litellm.completion(
                        model=narrative_model,
                        messages=messages,
                        max_tokens=4096
                    )
                    valuation_report = response.choices[0].message.content.strip()
                    with cache_path.open("w", encoding="utf-8") as f:
                        f.write(valuation_report)
                    logger.info(f"Successfully received and cached valuation report for chunk {i // chunk_size + 1}.")
                except Exception as e:
                    logger.exception(f"Error during collection valuation generation for chunk {i // chunk_size + 1}: {e}")
                    continue
            
            valuation_reports.append(valuation_report)

        print("\n===== Value Estimates =====\n")
        for report in valuation_reports:
            print(report)
            print("\n---\n")
        logger.info("Collection valuation phase complete.")

    def generate_catalog_pdf(self, value_threshold=100):
        """Generate catalog in PDF format using LaTeX for precise formatting, with high-value reports in front matter."""
        logger.info("--- Starting PDF Catalog Generation Phase ---")
        if not self.master_csv_path.exists():
            logger.error(f"Master inventory CSV not found at: {self.master_csv_path}")
            return

        try:
            df = pd.read_csv(self.master_csv_path)
            if df.empty:
                logger.warning("Master inventory is empty. Nothing to catalog.")
                return
        except pd.errors.EmptyDataError:
            logger.warning("Master inventory is empty. Nothing to catalog.")
            return
        
        # Generate high-value reports for front matter
        self.run_high_value_report_phase(value_threshold=value_threshold)

        # LaTeX document setup
        latex_content = r"""
    \documentclass[letterpaper]{article}
    \usepackage{geometry}
    \geometry{margin=1in}
    \usepackage{graphicx}
    \usepackage{tikz}
    \usepackage[utf8]{inputenc}
    \usepackage{truncate}
    \usepackage{xcolor}
    \setlength{\parindent}{0pt}
    \setlength{\parskip}{2pt}
    \pagestyle{empty}
    \begin{document}
    """

        # Add front matter for high-value reports
        latex_content += r"\section*{High-Value Stamp Reports}"
        
        high_value_reports = {}
        if self.high_value_reports_dir.exists():
            for report_file in self.high_value_reports_dir.glob("*.md"):
                stamp_name = report_file.stem.replace("high_value_report_", "").replace("_", " ")
                high_value_reports[stamp_name] = report_file.read_text(encoding="utf-8")

        if high_value_reports:
            for stamp_name, report in high_value_reports.items():
                latex_report = markdown_to_latex(report)
                latex_content += f"\\subsection*{{{stamp_name}}}\n{latex_report}\n\\newpage\n"
        else:
            latex_content += f"\\textit{{No high-value reports available.}}\n\\newpage\n"

        # Adjusted calculations for box height
        PAGE_SIZE = (612, 792)  # A4 in points (1/72 inch)
        MARGIN = 72  # 1 inch in points
        page_height_in = (PAGE_SIZE[1] - 2 * MARGIN) * 0.0139
        box_height = page_height_in / 2 - 0.2
        image_height = box_height * 0.55
        text_width = 6.2

        # Main catalog content
        for page_idx in range(0, len(df), 2):
            latex_content += r"\newpage" if page_idx > 0 else ""
            for i, idx in enumerate(range(page_idx, min(page_idx + 2, len(df)))):
                row = df.iloc[idx]
                img_path = ""
                albumval = row.get('album', '')
                pagefileval = row['page_filename']
                if row.get('page_filename'):
                    img_path = str(Path("stamps", row.get('album', '')).joinpath(row['page_filename'])).replace('\\', '/')
                    if not Path(img_path).exists():
                        img_path = ""
                        logger.warning(f"Image not found. albumval: {albumval}, pagefileval: {pagefileval}")

                # Metadata with LaTeX-safe escaping
                metadata_lines = (
                    f"Name: {str(row['common_name']).replace('&', r'\\&').replace('%', r'\\%').replace('#', r'\\#')}",
                    f"Country: {str(row['nationality']).replace('&', r'\\&').replace('%', r'\\%').replace('#', r'\\#')}",
                    f"Year: {str(row['year'])}",
                    f"Value: {str(row['face_value']).replace('&', r'\\&').replace('%', r'\\%').replace('#', r'\\#')}",
                    f"Condition: {str(row['condition']).replace('&', r'\\&').replace('%', r'\\%').replace('#', r'\\#')}",
                    f"Est. Value: {str(row.get('estimated_value_high', 'N/A')).replace('&', r'\\&').replace('%', r'\\%').replace('#', r'\\#')}",
                    f"Desc: {str(row.get('detailed_description', 'N/A')).replace('&', r'\\&').replace('%', r'\\%').replace('#', r'\\#')}"
                )
                metadata_text = r"\\\\".join(metadata_lines)

                # Define box with tikz
                y_pos = (box_height + 0.2) * (1 if i == 1 else 0)
                image_latex = r"\color{gray} [No Image Available]" if not img_path else f"\\includegraphics[width=5.5in, height={image_height}in, keepaspectratio]{{{img_path}}}"
                latex_content += f"""
            \\begin{{tikzpicture}}[remember picture, overlay]
                \\node[draw, rectangle, minimum width=6.5in, minimum height={box_height}in, 
                      xshift=0.5in, yshift=-{y_pos}in, anchor=north west] at (current page.north west) (box{i}) {{}};
            \\end{{tikzpicture}}
            \\vspace*{{{y_pos + 0.05}in}}
            \\begin{{minipage}}{{6.5in}}
                \\centering
                {image_latex}
                \\vspace{{0.05in}}
                \\begin{{minipage}}{{{text_width}in}}
                    \\small
                    {metadata_text}
                \\end{{minipage}}
            \\end{{minipage}}
            \\vspace*{{{box_height - 0.05 if i == 0 else 0.1}in}}
            """

        latex_content += r"""
    \end{document}
    """

        # Write LaTeX file
        tex_path = self.output_dir / "philately_catalog.tex"
        pdf_path = self.output_dir / "philately_catalog.pdf"
        with tex_path.open("w", encoding="utf-8") as f:
            f.write(latex_content)

        # Compile LaTeX to PDF
        try:
            import subprocess
            result = subprocess.run(["pdflatex", "-output-directory", str(self.output_dir), str(tex_path)],
                                    check=True, capture_output=True, text=True)
            logger.info(f"Saved PDF catalog to {pdf_path}")
            logger.debug(f"LaTeX compilation output: {result.stdout}")
            return pdf_path if pdf_path.exists() else None
        except subprocess.CalledProcessError as e:
            logger.error(f"Error compiling LaTeX to PDF: {e.stderr}")
            return None
        except FileNotFoundError:
            logger.error("pdflatex not found. Please install TeX Live or MiKTeX.")
            return None

    def generate_high_value_pdf(self, value_threshold=1000):
        """Generate a PDF catalog of high-value stamps only."""
        logger.info("--- Starting High-Value PDF Catalog Generation Phase ---")
        if not self.master_csv_path.exists():
            logger.error(f"Master inventory CSV not found at: {self.master_csv_path}")
            return

        try:
            df = pd.read_csv(self.master_csv_path)
            if df.empty:
                logger.warning("Master inventory is empty. Nothing to catalog.")
                return
        except pd.errors.EmptyDataError:
            logger.warning("Master inventory is empty. Nothing to catalog.")
            return

        # Filter for high-value stamps
        df['estimated_value_high'] = pd.to_numeric(df['estimated_value_high'], errors='coerce')
        df.dropna(subset=['estimated_value_high'], inplace=True)
        high_value_df = df[df['estimated_value_high'] > value_threshold].copy()

        if high_value_df.empty:
            logger.info(f"No stamps found with a high estimated value greater than ${value_threshold}.")
            return
            
        # Generate high-value reports for front matter
        self.run_high_value_report_phase(value_threshold=value_threshold)

        # LaTeX document setup
        latex_content = r"""
    \documentclass[letterpaper]{article}
    \usepackage{geometry}
    \geometry{margin=1in}
    \usepackage{graphicx}
    \usepackage{tikz}
    \usepackage[utf8]{inputenc}
    \usepackage{truncate}
    \usepackage{xcolor}
    \setlength{\parindent}{0pt}
    \setlength{\parskip}{2pt}
    \pagestyle{empty}
    \begin{document}
    """

        # Add front matter for high-value reports
        latex_content += r"\section*{High-Value Stamp Reports}"
        
        high_value_reports = {}
        if self.high_value_reports_dir.exists():
            for report_file in self.high_value_reports_dir.glob("*.md"):
                stamp_name = report_file.stem.replace("high_value_report_", "").replace("_", " ")
                high_value_reports[stamp_name] = report_file.read_text(encoding="utf-8")

        if high_value_reports:
            for stamp_name, report in high_value_reports.items():
                latex_report = markdown_to_latex(report)
                latex_content += f"\\subsection*{{{stamp_name}}}\n{latex_report}\n\\newpage\n"
        else:
            latex_content += f"\\textit{{No high-value reports available.}}\n\\newpage\n"

        # Adjusted calculations for box height
        PAGE_SIZE = (612, 792)  # A4 in points (1/72 inch)
        MARGIN = 72  # 1 inch in points
        page_height_in = (PAGE_SIZE[1] - 2 * MARGIN) * 0.0139
        box_height = page_height_in / 2 - 0.2
        image_height = box_height * 0.55
        text_width = 6.2

        # Main catalog content
        for page_idx in range(0, len(high_value_df), 2):
            latex_content += r"\newpage" if page_idx > 0 else ""
            for i, idx in enumerate(range(page_idx, min(page_idx + 2, len(high_value_df)))):
                row = high_value_df.iloc[idx]
                img_path = ""
                albumval = row.get('album', '')
                pagefileval = row['page_filename']
                if row.get('page_filename'):
                    img_path = str(Path("stamps", row.get('album', '')).joinpath(row['page_filename'])).replace('\\', '/')
                    if not Path(img_path).exists():
                        img_path = ""
                        logger.warning(f"Image not found. albumval: {albumval}, pagefileval: {pagefileval}")

                # Metadata with LaTeX-safe escaping
                metadata_lines = (
                    f"Name: {str(row['common_name']).replace('&', r'\\&').replace('%', r'\\%').replace('#', r'\\#')}",
                    f"Country: {str(row['nationality']).replace('&', r'\\&').replace('%', r'\\%').replace('#', r'\\#')}",
                    f"Year: {str(row['year'])}",
                    f"Value: {str(row['face_value']).replace('&', r'\\&').replace('%', r'\\%').replace('#', r'\\#')}",
                    f"Condition: {str(row['condition']).replace('&', r'\\&').replace('%', r'\\%').replace('#', r'\\#')}",
                    f"Est. Value: {str(row.get('estimated_value_high', 'N/A')).replace('&', r'\\&').replace('%', r'\\%').replace('#', r'\\#')}",
                    f"Desc: {str(row.get('detailed_description', 'N/A')).replace('&', r'\\&').replace('%', r'\\%').replace('#', r'\\#')}"
                )
                metadata_text = r"\\".join(metadata_lines)

                # Define box with tikz
                y_pos = (box_height + 0.2) * (1 if i == 1 else 0)
                image_latex = r"\color{gray} [No Image Available]" if not img_path else f"\\includegraphics[width=5.5in, height={image_height}in, keepaspectratio]{{{img_path}}}"
                latex_content += f"""
            \\begin{{tikzpicture}}[remember picture, overlay]
                \\node[draw, rectangle, minimum width=6.5in, minimum height={box_height}in, 
                      xshift=0.5in, yshift=-{y_pos}in, anchor=north west] at (current page.north west) (box{i}) {{}};
            \\end{{tikzpicture}}
            \\vspace*{{{y_pos + 0.05}in}}
            \\begin{{minipage}}{{6.5in}}
                \\centering
                {image_latex}
                \\vspace{{0.05in}}
                \\begin{{minipage}}{{{text_width}in}}
                    \\small
                    {metadata_text}
                \\end{{minipage}}
            \\end{{minipage}}
            \\vspace*{{{box_height - 0.05 if i == 0 else 0.1}in}}
            """

        latex_content += r"""
    \end{document}
    """

        # Write LaTeX file
        tex_path = self.output_dir / "high_value_catalog.tex"
        pdf_path = self.output_dir / "high_value_catalog.pdf"
        with tex_path.open("w", encoding="utf-8") as f:
            f.write(latex_content)

        # Compile LaTeX to PDF
        try:
            import subprocess
            result = subprocess.run(["pdflatex", "-output-directory", str(self.output_dir), str(tex_path)],
                                    check=True, capture_output=True, text=True)
            logger.info(f"Saved PDF catalog to {pdf_path}")
            logger.debug(f"LaTeX compilation output: {result.stdout}")
            return pdf_path if pdf_path.exists() else None
        except subprocess.CalledProcessError as e:
            logger.error(f"Error compiling LaTeX to PDF: {e.stderr}")
            return None
        except FileNotFoundError:
            logger.error("pdflatex not found. Please install TeX Live or MiKTeX.")
            return None

    def generate_summary_pdf(self, top_n_items: int = 25, top_n_images: int = 5):
        """
        Generates a concise, 10-page summary PDF of the collection.
        """
        logger.info("--- Starting Collection Summary PDF Generation ---")
        summary_pdf_path = self.output_dir / "collection_summary.pdf"
        summary_tex_path = self.output_dir / "collection_summary.tex"

        if not self.master_csv_path.exists():
            logger.error(f"Master inventory CSV not found at: {self.master_csv_path}")
            return

        try:
            df = pd.read_csv(self.master_csv_path)
            if df.empty:
                logger.warning("Master inventory is empty. Cannot generate summary PDF.")
                return
        except pd.errors.EmptyDataError:
            logger.warning("Master inventory is empty. Cannot generate summary PDF.")
            return

        # Filter out non-stamps and deacquired items
        df_active = df[(df['common_name'] != 'Collection Overview') & (df['deacquired'] != True)].copy()

        # Sort by value to get top items
        if 'estimated_value_high' in df_active.columns:
            df_active['estimated_value_high'] = pd.to_numeric(df_active['estimated_value_high'], errors='coerce')
            df_sorted = df_active.sort_values(by='estimated_value_high', ascending=False).dropna(
                subset=['estimated_value_high'])
        else:
            logger.warning("'estimated_value_high' column not found. Cannot sort by value.")
            df_sorted = df_active

        top_items = df_sorted.head(top_n_items)
        top_images = df_sorted.head(top_n_images)

        # --- Start LaTeX Document ---
        latex_content = r"""
\documentclass[10pt, letterpaper]{article}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\geometry{a4paper, margin=1in}
\usepackage{graphicx}
\usepackage{longtable}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{fancyhdr}
\usepackage{lastpage}

\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,
    urlcolor=cyan,
}

\pagestyle{fancy}
\fancyhf{}
\rhead{Collection Summary}
\lhead{Philately Will Get You Everywhere}
\cfoot{Page \thepage\ of \pageref{LastPage}}

\begin{document}

\title{Philatelic Collection Summary}
\author{Generated by Philately Processor}
\date{\today}
\maketitle

\section*{Collection Overview}
"""
        # --- Collection Summary ---
        if self.final_json_path.exists():
            with self.final_json_path.open("r", encoding="utf-8") as f:
                final_data = json.load(f)
            summary_text = final_data.get("philatelic_summaries", {}).get("collection_wide", {}).get(
                "narrative_summary", "No summary available.")
            latex_content += markdown_to_latex(summary_text)
        else:
            latex_content += "Collection summary data not found. Please run the summary phase first.\n"

        latex_content += r"\newpage"

        # --- Top 25 Items Table ---
        latex_content += r"""
\section*{Top 25 High-Value Items}
\begin{longtable}{|p{8cm}|c|p{4cm}|}
\hline
\textbf{Common Name} & \textbf{Est. Value (High)} & \textbf{Verification Status} \\
\hline
\endfirsthead
\hline
\textbf{Common Name} & \textbf{Est. Value (High)} & \textbf{Verification Status} \\
\hline
\endhead
"""
        for _, row in top_items.iterrows():
            name = str(row.get('common_name', 'N/A')).replace('&', r'\&').replace('%', r'\%').replace('#', r'\#')
            value = f"${int(row.get('estimated_value_high', 0))}"
            verified = str(row.get('is_verified_real', 'Not Checked'))
            latex_content += f"""{name} & {value} & {verified} \\
"""

        latex_content += r"""
\hline
\end{longtable}
"""

        # --- Top 5 Images ---
        if not top_images.empty:
            latex_content += r"""
\newpage
\section*{Images of Top 5 Items}
"""
            for _, row in top_images.iterrows():
                name = str(row.get('common_name', 'N/A')).replace('&', r'\&').replace('%', r'\%').replace('#', r'\#')
                img_path_str = row.get('cropped_image_path')
                if img_path_str and pd.notna(img_path_str):
                    full_img_path = self.output_dir / img_path_str
                    if full_img_path.exists():
                        latex_content += f"\\subsection*{{{name}}}\n"
                        latex_content += f"\\includegraphics[width=0.8\\textwidth,height=0.4\\textheight,keepaspectratio]{{{full_img_path}}}\n"
                        latex_content += "\\vspace{1cm}\n"
                    else:
                        latex_content += f"\\subsection*{{{name}}}\n"
                        latex_content += f"Image not found at: {str(full_img_path).replace('_', r'\\_')}\n"
                else:
                    latex_content += f"\\subsection*{{{name}}}\n"
                    latex_content += "No image available.\n"

        # --- End Document ---
        latex_content += r"\end{document}"

        # --- Write and Compile ---
        with summary_tex_path.open("w", encoding="utf-8") as f:
            f.write(latex_content)

        logger.info(f"Generated LaTeX summary at {summary_tex_path}")

        try:
            import subprocess
            result = subprocess.run(
                ["pdflatex", "-output-directory", str(self.output_dir), "-interaction=nonstopmode",
                 str(summary_tex_path)],
                check=True, capture_output=True, text=True
            )
            # Run again for page numbers
            subprocess.run(
                ["pdflatex", "-output-directory", str(self.output_dir), "-interaction=nonstopmode",
                 str(summary_tex_path)],
                check=True, capture_output=True, text=True
            )
            logger.info(f"Successfully generated summary PDF: {summary_pdf_path}")
            logger.debug(f"LaTeX compilation output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error compiling LaTeX to PDF: {e.stderr}")
            logger.error(f"LaTeX content written to {summary_tex_path} for debugging.")
        except FileNotFoundError:
            logger.error("pdflatex not found. Please install a TeX distribution (like TeX Live or MiKTeX).")


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
    parser.add_argument('--high-value-threshold', type=int, default=1000,
                        help='USD threshold to consider a stamp as high-value for reporting.')

    # MODIFICATION: Add debug flag
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug-level logging for verbose output.')

    # Arguments for model selection
    parser.add_argument('--low-cost-model', type=str, default="gemini/gemini-1.5-flash-latest",
                        help='The vision model to use for the initial, low-cost pass.')
    parser.add_argument('--high-cost-model', type=str, default="gemini/gemini-1.5-pro-latest",
                        help='The vision model to use for the high-confidence re-analysis pass.')
    parser.add_argument('--narrative-model', type=str, default="gemini/gemini-1.5-pro-latest",
                        help='The text model to use for enrichment and summaries.')
    parser.add_argument('--collection-summary-model', type=str, default="gemini/gemini-1.5-pro-latest",
                        help='The high-context model to use for the final collection-wide summary.')

    # Phase control
    parser.add_argument('--run-analysis', action='store_true', help='Run only the image analysis phase.')
    parser.add_argument('--run-enrichment', action='store_true', help='Run only the philatelic enrichment phase.')
    parser.add_argument('--run-summaries', action='store_true', help='Run the full clustering and summary phase.')
    parser.add_argument('--run-high-value-report', action='store_true',
                        help='Run only the high-value stamp report generation phase.')
    parser.add_argument('--run-collection-summary-only', action='store_true',
                        help='Run only the final collection-wide summary generation.')
    parser.add_argument('--run-false-positive-check', action='store_true',
                        help='Run a re-examination of high-value stamps to find false positives.')
    # NEW: Substack export phase
    parser.add_argument('--run-substack-export', action='store_true',
                        help='Generate a CSV export formatted for Substack posts.')
    parser.add_argument('--substack-items', type=int, default=10,
                        help='Number of top items to include in the Substack export (0 for all).')
    parser.add_argument('--run-valuation', action='store_true', help='Generate a collection valuation report.')
    parser.add_argument('--run-pdf-catalog', action='store_true', help='Generate a PDF catalog.')
    parser.add_argument('--run-high-value-pdf', action='store_true', help='Generate a PDF catalog of high-value stamps only.')
    parser.add_argument('--run-summary-pdf', action='store_true', help='Generate a summary PDF of the collection.')

    # MODIFICATION: Add the false positive check limit argument
    parser.add_argument('--false-positive-check-limit', type=int, default=5,
                        help='Limit the number of high-value stamps to check for false positives (0 for all).')

    args = parser.parse_args()

    # MODIFICATION: Configure logging based on the flag
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    # Re-suppress noisy logs from underlying libraries after basicConfig
    for lib in ["openai", "httpx", "httpcore", "litellm"]:
        logging.getLogger(lib).setLevel(logging.WARNING)

    processor = PhilatelyProcessor(image_dir=Path(args.image_dir), output_dir=Path(args.output_dir))

    run_all = not (
            args.run_analysis or args.run_enrichment or args.run_summaries or args.run_high_value_report or args.run_collection_summary_only or args.run_false_positive_check or args.run_substack_export or args.run_valuation or args.run_pdf_catalog)

    if run_all or args.run_analysis:
        processor.run_image_analysis_phase(
            args.confidence_threshold,
            max_images=args.max_images,
            low_cost_model=args.low_cost_model,
            high_cost_model=args.high_cost_model
        )

    if run_all or args.run_enrichment:
        processor.run_philatelic_enrichment_phase(narrative_model=args.narrative_model)

    if run_all or args.run_summaries:
        processor.run_clustering_and_summary_phase(
            narrative_model=args.narrative_model,
            collection_summary_model=args.collection_summary_model,
            collection_only=False  # Run full summaries
        )
    elif args.run_collection_summary_only:
        processor.run_clustering_and_summary_phase(
            narrative_model=args.narrative_model,
            collection_summary_model=args.collection_summary_model,
            collection_only=True  # Run only collection summary
        )

    if run_all or args.run_high_value_report:
        processor.run_high_value_report_phase(value_threshold=args.high_value_threshold)

    if run_all or args.run_false_positive_check:
        processor.run_false_positive_check_phase(
            high_cost_model=args.high_cost_model,
            value_threshold=args.high_value_threshold,
            check_limit=args.false_positive_check_limit
        )

    if run_all or args.run_substack_export:
        processor.run_substack_export_phase(num_items=args.substack_items)

    if run_all or args.run_valuation:
        processor.run_valuation_phase(narrative_model=args.narrative_model, chunk_size=1000)

    if run_all or args.run_pdf_catalog:
        processor.generate_catalog_pdf()

    if run_all or args.run_high_value_pdf:
        processor.generate_high_value_pdf()

    if run_all or args.run_summary_pdf:
        processor.generate_summary_pdf()

    logger.info("Philately processing finished.")


def markdown_to_latex(text):
    """Convert Markdown content to LaTeX-compatible text (basic conversion)."""
    text = text.replace('# ', r'\section{').replace('#', r'\subsection{')
    text = text.replace('**', r'\textbf{').replace('*', r'\textit{')
    text = text.replace(' - ', r' \item ')
    text = text.replace('\n- ', r' \item ')
    text = text.replace('\n', r'\\')
    text = text.replace('&', r'\&').replace('%', r'\%').replace('#', r'\#')
    return text


if __name__ == "__main__":
    main()
