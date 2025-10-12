#!/usr/bin/env python3
"""
Expand incomplete imprints from data/working/imprints/imprints_in_progress.csv
into fully complete, professional imprint specifications
"""

import csv
import json
import logging
import litellm
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprintExpander:
    def __init__(self):
        self.input_file = "data/working/imprints/imprints_in_progress.csv"
        self.output_file = "data/working/imprints/expanded_complete_imprints.csv"
        self.output_configs_dir = Path("configs/imprints/expanded")
        self.output_configs_dir.mkdir(parents=True, exist_ok=True)

    def load_incomplete_imprints(self):
        """Load the imprints in progress CSV"""
        imprints = []
        with open(self.input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('name'):  # Skip empty rows
                    imprints.append(row)

        logger.info(f"Loaded {len(imprints)} imprints to expand")
        return imprints

    def expand_single_imprint(self, imprint_data):
        """Use LLM to expand and complete a single imprint"""

        # Create context from existing data
        existing_info = []
        for field, value in imprint_data.items():
            if value and value.strip():
                existing_info.append(f"{field}: {value}")

        existing_context = "\n".join(existing_info) if existing_info else "Minimal information provided"

        prompt = f"""You are expanding an incomplete publishing imprint specification into a comprehensive, professional imprint profile.

EXISTING IMPRINT DATA:
{existing_context}

TASK: Complete all missing fields and enhance existing ones to create a professional, market-ready imprint specification.

REQUIREMENTS:
1. Preserve ALL existing information exactly as provided
2. Fill in any missing fields with professional, realistic content
3. Enhance sparse fields with more detailed, compelling descriptions
4. Ensure consistency across all fields
5. Make the imprint commercially viable and distinctive

OUTPUT FORMAT: Return ONLY a valid JSON object with this exact structure:
{{
  "name": "Exact existing name or enhanced if missing",
  "charter": "Complete mission statement",
  "focus": "Detailed publishing focus areas",
  "tagline": "Memorable marketing tagline",
  "target_audience": "Specific target readership",
  "competitive_advantage": "Clear market positioning and advantages",
  "examples": "Specific example titles, authors, or book types that would fit",
  "enhanced_details": {{
    "annual_titles_target": "Realistic annual publishing target",
    "price_range": "Typical book price range for this imprint",
    "distribution_strategy": "How books will reach readers",
    "marketing_approach": "Key marketing and promotion strategies",
    "editorial_philosophy": "Editorial standards and approach",
    "series_potential": "Potential book series or collections",
    "author_profile": "Types of authors this imprint would attract",
    "market_positioning": "Position in the competitive landscape"
  }}
}}

Generate a comprehensive, professional imprint specification that builds on the existing information."""

        try:
            response = litellm.completion(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )

            content = response.choices[0].message.content.strip()

            # Clean response to get JSON
            if not content.startswith('{'):
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end != 0:
                    content = content[start:end]

            expanded_imprint = json.loads(content)
            logger.info(f"✅ Expanded imprint: {expanded_imprint.get('name', 'Unknown')}")
            return expanded_imprint

        except Exception as e:
            logger.error(f"❌ Error expanding imprint {imprint_data.get('name', 'Unknown')}: {e}")
            # Return enhanced version of original data as fallback
            return self.create_fallback_expansion(imprint_data)

    def create_fallback_expansion(self, original_data):
        """Create a basic expansion if LLM fails"""
        return {
            "name": original_data.get('name', 'Unnamed Imprint'),
            "charter": original_data.get('charter', 'Professional publishing excellence'),
            "focus": original_data.get('focus', 'Quality books for discerning readers'),
            "tagline": original_data.get('tagline', 'Excellence in publishing'),
            "target_audience": original_data.get('target_audience', 'General readers'),
            "competitive_advantage": original_data.get('competitive_advantage', 'Quality and curation'),
            "examples": original_data.get('examples', 'Various quality titles'),
            "enhanced_details": {
                "annual_titles_target": "12-24 titles",
                "price_range": "$15-35",
                "distribution_strategy": "Print-on-demand and digital",
                "marketing_approach": "Targeted digital marketing",
                "editorial_philosophy": "Quality over quantity",
                "series_potential": "Open to series development",
                "author_profile": "Established and emerging authors",
                "market_positioning": "Quality-focused imprint"
            }
        }

    def save_expanded_imprints(self, expanded_imprints):
        """Save expanded imprints to CSV and individual config files"""

        # Define CSV fieldnames
        fieldnames = [
            "name", "charter", "focus", "tagline", "target_audience",
            "competitive_advantage", "examples", "annual_titles_target",
            "price_range", "distribution_strategy", "marketing_approach",
            "editorial_philosophy", "series_potential", "author_profile",
            "market_positioning"
        ]

        # Save to CSV
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for imprint in expanded_imprints:
                # Flatten the enhanced_details into main row
                row = {
                    "name": imprint.get("name", ""),
                    "charter": imprint.get("charter", ""),
                    "focus": imprint.get("focus", ""),
                    "tagline": imprint.get("tagline", ""),
                    "target_audience": imprint.get("target_audience", ""),
                    "competitive_advantage": imprint.get("competitive_advantage", ""),
                    "examples": imprint.get("examples", "")
                }

                # Add enhanced details
                enhanced = imprint.get("enhanced_details", {})
                for field in ["annual_titles_target", "price_range", "distribution_strategy",
                             "marketing_approach", "editorial_philosophy", "series_potential",
                             "author_profile", "market_positioning"]:
                    row[field] = enhanced.get(field, "")

                writer.writerow(row)

        # Save individual config files
        for imprint in expanded_imprints:
            safe_name = imprint.get("name", "unnamed").lower().replace(" ", "_").replace("&", "and")
            config_file = self.output_configs_dir / f"{safe_name}.json"

            # Create full config structure
            config = {
                "imprint": imprint.get("name", ""),
                "publisher": "BigFiveReplacement LLC",
                "contact_email": f"contact@{safe_name}.com",
                "imprint_details": imprint,
                "branding": {
                    "tagline": imprint.get("tagline", ""),
                    "brand_colors": {"primary": "#1a237e", "secondary": "#303f9f"},
                    "website": f"https://www.{safe_name}.com"
                },
                "business_metrics": imprint.get("enhanced_details", {}),
                "distribution_settings": {
                    "lightning_source_account": "LSI950000",
                    "distribution_channel": "Global POD + Traditional"
                }
            }

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Saved {len(expanded_imprints)} expanded imprints to {self.output_file}")
        logger.info(f"✅ Created {len(expanded_imprints)} config files in {self.output_configs_dir}")

    def run_expansion(self):
        """Main expansion process"""
        logger.info("🚀 Starting imprint expansion process...")

        # Load incomplete imprints
        incomplete_imprints = self.load_incomplete_imprints()

        # Expand each imprint
        expanded_imprints = []
        for i, imprint in enumerate(incomplete_imprints, 1):
            logger.info(f"📝 Expanding {i}/{len(incomplete_imprints)}: {imprint.get('name', 'Unnamed')}")
            expanded = self.expand_single_imprint(imprint)
            expanded_imprints.append(expanded)

        # Save results
        self.save_expanded_imprints(expanded_imprints)

        # Generate summary
        summary = {
            "total_imprints_expanded": len(expanded_imprints),
            "input_file": self.input_file,
            "output_file": self.output_file,
            "config_directory": str(self.output_configs_dir),
            "expansion_complete": True
        }

        with open("imprint_expansion_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"🎉 Expansion complete! {len(expanded_imprints)} imprints fully developed")
        return summary

def main():
    expander = ImprintExpander()
    summary = expander.run_expansion()

    print(f"\n✅ Imprint Expansion Complete!")
    print(f"📊 Expanded: {summary['total_imprints_expanded']} imprints")
    print(f"📁 Output CSV: {summary['output_file']}")
    print(f"📁 Config files: {summary['config_directory']}")

    return True

if __name__ == "__main__":
    main()