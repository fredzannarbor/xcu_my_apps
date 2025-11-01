#!/usr/bin/env python3
"""
Generate annotations for submarine patrol reports using vision models.

This script uses the ORIGINAL PAGE IMAGES (not just OCR text) to generate
rich, contextual annotations that preserve visual information lost in OCR.

Annotations generated:
1. Patrol report metadata (submarine, hull, dates, COs, areas)
2. Bibliographic keywords
3. Publisher's note
4. Historical context essay
5. Abstracts (TLDR, executive, academic, general reader)
6. Enemy encounter analysis (tactical breakdowns)
7. Glossary of naval terms
8. Context boxes (technical/historical sidebars)
9. Most important passages
10. Indices (persons, places, ships)
11. Tactical map locations
"""

import json
import base64
from pathlib import Path
from datetime import datetime
import time
import litellm
from dotenv import load_dotenv
import fitz  # PyMuPDF
import argparse
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

# Configure litellm
litellm.telemetry = False
litellm.drop_params = True

class AnnotationGenerator:
    """Generate vision-based annotations for submarine patrol reports."""

    def __init__(
        self,
        prompts_file="imprints/warships_and_navies/prompts/submarine_patrol_logs_prompts.json",
        ocr_dir="ocr_output",
        input_dir="input_files_by_imprint/warships_and_navies/submarine_patrol_reports",
        output_dir="annotations_output",
        model="gemini/gemini-2.5-flash"
    ):
        self.prompts_file = Path(prompts_file)
        self.ocr_dir = Path(ocr_dir)
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.model = model

        # Load prompts
        with open(self.prompts_file) as f:
            self.prompts = json.load(f)

        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Stats
        self.stats = {
            "annotations_generated": 0,
            "total_cost": 0.0,
            "total_tokens": 0,
            "start_time": datetime.now().isoformat()
        }

    def load_ocr_text(self, submarine_name: str) -> Dict[int, str]:
        """Load OCR'd text for a submarine, indexed by page number."""
        ocr_file = self.ocr_dir / submarine_name / f"{submarine_name}_ocr.jsonl"

        if not ocr_file.exists():
            raise FileNotFoundError(f"OCR file not found: {ocr_file}")

        ocr_data = {}
        with open(ocr_file) as f:
            for line in f:
                page_data = json.loads(line)
                if page_data["success"]:
                    ocr_data[page_data["page_number"]] = page_data["ocr_text"]

        return ocr_data

    def extract_pdf_page_as_image(self, pdf_path: Path, page_num: int, dpi: int = 300) -> bytes:
        """Extract a single page from PDF as high-quality image."""
        doc = fitz.open(pdf_path)
        page = doc[page_num]

        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        img_bytes = pix.tobytes("png")
        doc.close()

        return img_bytes

    def call_vision_model(
        self,
        prompt_text: str,
        image_bytes: Optional[bytes] = None,
        context_text: Optional[str] = None,
        temperature: float = 0.5,
        max_tokens: int = 4096
    ) -> Dict:
        """
        Call vision model with image and/or text context.

        Args:
            prompt_text: The prompt/question to ask
            image_bytes: Optional image to analyze
            context_text: Optional text context (e.g., OCR'd book content)
            temperature: Sampling temperature
            max_tokens: Max completion tokens
        """

        # Add text prompt (replace {book_content} placeholder with context)
        if context_text:
            prompt_text = prompt_text.replace("{book_content}", context_text)

        messages = []

        # Construct message content based on whether we have an image
        if image_bytes:
            # Multimodal: image + text
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            content_parts = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_b64}"
                    }
                },
                {
                    "type": "text",
                    "text": prompt_text
                }
            ]
            messages.append({
                "role": "user",
                "content": content_parts
            })
        else:
            # Text-only: just use string content (not list)
            messages.append({
                "role": "user",
                "content": prompt_text
            })

        # Call model
        try:
            response = litellm.completion(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            # Track cost
            cost = 0
            if hasattr(response, 'usage') and response.usage:
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens

                # Gemini 2.5 Flash pricing
                if "gemini" in self.model.lower():
                    cost = (prompt_tokens * 0.075 / 1_000_000) + (completion_tokens * 0.30 / 1_000_000)

                self.stats["total_tokens"] += response.usage.total_tokens
                self.stats["total_cost"] += cost

            # Check if content exists
            content = response.choices[0].message.content if response.choices else None

            if content is None:
                return {
                    "success": False,
                    "error": "API returned None content",
                    "content": None,
                    "tokens": 0,
                    "cost": 0
                }

            return {
                "success": True,
                "content": content,
                "tokens": response.usage.total_tokens if hasattr(response, 'usage') else 0,
                "cost": cost
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": "",
                "tokens": 0,
                "cost": 0
            }

    def generate_metadata(self, submarine_name: str, pdf_path: Path, ocr_data: Dict) -> Dict:
        """Generate patrol report metadata using vision model on sample pages."""
        print(f"\n{'='*80}")
        print(f"Generating: Patrol Report Metadata")
        print(f"{'='*80}")

        # Use first 20 pages for metadata extraction
        sample_pages = list(ocr_data.keys())[:20]
        combined_text = "\n\n=== PAGE BREAK ===\n\n".join([ocr_data[p] for p in sample_pages])

        # Get prompt
        prompt_config = self.prompts["get_patrol_report_metadata"]
        prompt_text = prompt_config["messages"][1]["content"]

        # Call model with combined text
        result = self.call_vision_model(
            prompt_text=prompt_text,
            context_text=combined_text,
            temperature=prompt_config["params"]["temperature"],
            max_tokens=prompt_config["params"]["max_tokens"]
        )

        if result["success"] and result.get("content"):
            print(f"✅ Metadata generated | Tokens: {result['tokens']} | Cost: ${result['cost']:.4f}")
            self.stats["annotations_generated"] += 1
            try:
                return json.loads(result["content"])
            except (json.JSONDecodeError, TypeError) as e:
                print(f"⚠️  JSON parse error: {e}")
                return {}
        else:
            error_msg = result.get('error', 'No content returned')
            print(f"❌ Failed: {error_msg}")
            return {}

    def generate_document_level_annotation(
        self,
        annotation_name: str,
        prompt_key: str,
        ocr_data: Dict,
        pdf_path: Optional[Path] = None,
        use_vision: bool = True
    ) -> str:
        """
        Generate a document-level annotation (applies to entire book).

        Args:
            annotation_name: Display name (e.g., "Publisher's Note")
            prompt_key: Key in prompts.json
            ocr_data: OCR'd text by page
            pdf_path: Path to PDF (if using vision)
            use_vision: Whether to include sample page images
        """
        print(f"\n{'='*80}")
        print(f"Generating: {annotation_name}")
        print(f"{'='*80}")

        # Get prompt configuration
        prompt_config = self.prompts[prompt_key]

        # Combine OCR text (sample pages for efficiency)
        # For document-level annotations, use strategic sampling:
        # - First 10 pages (cover, intro, summary)
        # - Middle 10 pages (representative combat)
        # - Last 10 pages (conclusion, results)
        page_nums = sorted(ocr_data.keys())
        sample_indices = (
            page_nums[:10] +
            page_nums[len(page_nums)//2 - 5:len(page_nums)//2 + 5] +
            page_nums[-10:]
        )

        combined_text = "\n\n=== PAGE BREAK ===\n\n".join([ocr_data[p] for p in sample_indices[:30]])  # Max 30 pages

        # Extract prompt text
        if isinstance(prompt_config["messages"], list):
            # Find user message
            prompt_text = next(m["content"] for m in prompt_config["messages"] if m["role"] == "user")
        else:
            prompt_text = prompt_config["messages"]["content"]

        # Optionally add vision context with sample page images
        image_bytes = None
        if use_vision and pdf_path and len(sample_indices) > 10:
            # Use one representative middle page image
            rep_page = sample_indices[len(sample_indices) // 2]
            image_bytes = self.extract_pdf_page_as_image(pdf_path, rep_page)

        # Call model
        result = self.call_vision_model(
            prompt_text=prompt_text,
            image_bytes=image_bytes,
            context_text=combined_text,
            temperature=prompt_config["params"].get("temperature", 0.5),
            max_tokens=prompt_config["params"].get("max_tokens", 4096)
        )

        if result["success"] and result.get("content"):
            print(f"✅ {annotation_name} generated | Tokens: {result['tokens']} | Cost: ${result['cost']:.4f}")
            self.stats["annotations_generated"] += 1
            return result["content"]
        else:
            error_msg = result.get('error', 'No content returned')
            print(f"❌ Failed: {error_msg}")
            return ""

    def generate_page_level_annotations(
        self,
        annotation_name: str,
        prompt_key: str,
        pdf_path: Path,
        ocr_data: Dict,
        sample_pages: int = 50
    ) -> List[Dict]:
        """
        Generate page-level annotations using vision model on individual pages.

        Used for:
        - Enemy encounter analysis (needs to see tactical diagrams)
        - Context boxes (needs to see layout and emphasis)
        - Tactical map locations (needs to read charts)

        Args:
            annotation_name: Display name
            prompt_key: Key in prompts.json
            pdf_path: Path to PDF
            ocr_data: OCR'd text
            sample_pages: Analyze this many pages (for cost control)
        """
        print(f"\n{'='*80}")
        print(f"Generating: {annotation_name} (Page-Level Analysis)")
        print(f"{'='*80}")

        prompt_config = self.prompts[prompt_key]
        prompt_text = prompt_config["messages"][1]["content"]

        results = []

        # Sample pages intelligently:
        # - Skip cover pages (first 5)
        # - Sample evenly from operational pages
        page_nums = sorted([p for p in ocr_data.keys() if p >= 5])
        sample_interval = max(1, len(page_nums) // sample_pages)
        sampled_pages = page_nums[::sample_interval][:sample_pages]

        print(f"Analyzing {len(sampled_pages)} pages (sampled from {len(page_nums)} operational pages)")

        for i, page_num in enumerate(sampled_pages):
            # Extract page image
            image_bytes = self.extract_pdf_page_as_image(pdf_path, page_num)

            # Get OCR context
            page_ocr = ocr_data[page_num]

            # Call vision model
            result = self.call_vision_model(
                prompt_text=prompt_text,
                image_bytes=image_bytes,
                context_text=page_ocr,
                temperature=prompt_config["params"].get("temperature", 0.5),
                max_tokens=prompt_config["params"].get("max_tokens", 4096)
            )

            if result["success"] and result.get("content"):
                try:
                    # Parse JSON response
                    page_result = json.loads(result["content"])
                    page_result["page_number"] = page_num
                    results.append(page_result)

                    status = "✅" if page_result else "⚠️ "
                    print(f"{status} Page {page_num+1} | Tokens: {result['tokens']} | Cost: ${result['cost']:.4f}")

                except (json.JSONDecodeError, TypeError) as e:
                    print(f"⚠️  Page {page_num+1} | JSON parse error: {e}")
                    results.append({
                        "page_number": page_num,
                        "error": f"JSON parse failed: {e}",
                        "raw_content": result.get("content", "")
                    })

            else:
                error_msg = result.get('error', 'Unknown error or no content')
                print(f"❌ Page {page_num+1} | Error: {error_msg}")

            # Rate limiting
            time.sleep(0.1)

            # Progress update every 10 pages
            if (i + 1) % 10 == 0:
                print(f"   Progress: {i+1}/{len(sampled_pages)} pages | Total cost: ${self.stats['total_cost']:.2f}")

        print(f"✅ {annotation_name} complete | {len(results)} pages analyzed")
        self.stats["annotations_generated"] += 1

        return results

    def generate_all_annotations(self, submarine_name: str) -> Dict:
        """Generate all annotations for a submarine's patrol reports."""

        print(f"\n{'='*80}")
        print(f"ANNOTATION GENERATION: {submarine_name}")
        print(f"{'='*80}")

        # Load OCR data
        print(f"\nLoading OCR data...")
        ocr_data = self.load_ocr_text(submarine_name)
        print(f"Loaded {len(ocr_data)} pages of OCR'd text")

        # Find PDF file
        submarine_dir = self.input_dir / submarine_name
        pdf_files = list(submarine_dir.glob("*.pdf"))
        if not pdf_files:
            raise FileNotFoundError(f"No PDF found in {submarine_dir}")
        pdf_path = pdf_files[0]

        # Create output directory
        output_sub_dir = self.output_dir / submarine_name
        output_sub_dir.mkdir(exist_ok=True, parents=True)

        annotations = {
            "submarine_name": submarine_name,
            "pdf_file": pdf_path.name,
            "total_pages": len(ocr_data),
            "generation_date": datetime.now().isoformat()
        }

        # 1. Metadata (submarine info, patrol numbers, dates, COs)
        annotations["metadata"] = self.generate_metadata(submarine_name, pdf_path, ocr_data)

        # 2. Bibliographic keywords
        annotations["keywords"] = self.generate_document_level_annotation(
            "Bibliographic Keywords",
            "bibliographic_key_phrases",
            ocr_data,
            pdf_path,
            use_vision=False
        )

        # 3. Publisher's Note
        annotations["publishers_note"] = self.generate_document_level_annotation(
            "Publisher's Note",
            "publishers_note",
            ocr_data,
            pdf_path,
            use_vision=True
        )

        # 4. Historical Context
        annotations["historical_context"] = self.generate_document_level_annotation(
            "Historical Context Essay",
            "place_in_historical_context",
            ocr_data,
            pdf_path,
            use_vision=True
        )

        # 5. Abstracts (4 types)
        annotations["abstracts"] = self.generate_document_level_annotation(
            "Abstracts (TLDR, Executive, Academic, General)",
            "abstracts_x4",
            ocr_data,
            pdf_path,
            use_vision=False
        )

        # 6. Most Important Passages
        annotations["important_passages"] = self.generate_document_level_annotation(
            "Most Important Passages",
            "most_important_passages_with_reasoning",
            ocr_data,
            pdf_path,
            use_vision=True
        )

        # 7. Glossary of Naval Terms
        annotations["glossary"] = self.generate_document_level_annotation(
            "Glossary of Naval Terms",
            "glossary_naval_terms",
            ocr_data,
            pdf_path,
            use_vision=False
        )

        # 8. Enemy Encounter Analysis (page-level, vision-intensive)
        annotations["enemy_encounters"] = self.generate_page_level_annotations(
            "Enemy Encounter Analysis",
            "enemy_encounter_analysis",
            pdf_path,
            ocr_data,
            sample_pages=30  # Analyze 30 representative pages
        )

        # 9. Context Boxes (page-level)
        annotations["context_boxes"] = self.generate_page_level_annotations(
            "Context Boxes",
            "context_boxes",
            pdf_path,
            ocr_data,
            sample_pages=30
        )

        # 10. Tactical Map Locations (page-level, needs to read charts)
        annotations["map_locations"] = self.generate_page_level_annotations(
            "Tactical Map Locations",
            "tactical_map_locations",
            pdf_path,
            ocr_data,
            sample_pages=40  # More pages for geographic coverage
        )

        # 11. Index of Persons
        annotations["index_persons"] = self.generate_document_level_annotation(
            "Index of Persons",
            "index_of_persons",
            ocr_data,
            pdf_path,
            use_vision=False
        )

        # 12. Index of Places
        annotations["index_places"] = self.generate_document_level_annotation(
            "Index of Places",
            "index_of_places",
            ocr_data,
            pdf_path,
            use_vision=False
        )

        # 13. Index of Ships
        annotations["index_ships"] = self.generate_document_level_annotation(
            "Index of Ships (Enemy Vessels)",
            "index_of_ships",
            ocr_data,
            pdf_path,
            use_vision=True  # Needs to see silhouette charts
        )

        # Save complete annotations
        output_file = output_sub_dir / f"{submarine_name}_annotations.json"
        with open(output_file, 'w') as f:
            json.dump(annotations, f, indent=2)

        print(f"\n{'='*80}")
        print(f"✅ ALL ANNOTATIONS GENERATED")
        print(f"{'='*80}")
        print(f"Annotations: {self.stats['annotations_generated']}")
        print(f"Total tokens: {self.stats['total_tokens']:,}")
        print(f"Total cost: ${self.stats['total_cost']:.2f}")
        print(f"Saved to: {output_file}")

        return annotations

def main():
    parser = argparse.ArgumentParser(
        description="Generate annotations for submarine patrol reports using vision models"
    )
    parser.add_argument(
        "--submarine",
        required=True,
        help="Submarine to process (e.g., SS-306_TANG)"
    )
    parser.add_argument(
        "--model",
        default="gemini/gemini-2.5-flash",
        help="Vision model to use (default: gemini/gemini-2.5-flash)"
    )
    parser.add_argument(
        "--prompts",
        default="imprints/warships_and_navies/prompts/submarine_patrol_logs_prompts.json",
        help="Path to prompts file"
    )

    args = parser.parse_args()

    generator = AnnotationGenerator(
        prompts_file=args.prompts,
        model=args.model
    )

    annotations = generator.generate_all_annotations(args.submarine)

    print("\n" + "="*80)
    print("ANNOTATION GENERATION COMPLETE!")
    print(f"Total cost: ${generator.stats['total_cost']:.2f}")
    print("="*80)

if __name__ == "__main__":
    main()
