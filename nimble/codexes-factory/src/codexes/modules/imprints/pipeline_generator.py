#!/usr/bin/env python3
"""
Imprint Pipeline Generator Module

Creates complete operational pipeline tools for a publishing imprint based on
its configuration file. Generates all necessary templates, processors, prompts,
and schedules to operate the imprint.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import shutil
import logging
from string import Template

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.append(str(project_root))

try:
    from codexes.core.llm_caller import call_model_with_prompt
    from codexes.modules.rights_management import generate_imprint_rights_sheet
except ModuleNotFoundError:
    from src.codexes.core.llm_caller import call_model_with_prompt
    try:
        from src.codexes.modules.rights_management import generate_imprint_rights_sheet
    except ImportError:
        generate_imprint_rights_sheet = None

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ImprintPipelineGenerator:
    """
    Generates complete pipeline tools for an imprint based on its configuration.
    """

    def __init__(self, config_path: str):
        """Initialize with imprint configuration file."""
        self.config_path = Path(config_path)
        self.config = self._load_and_validate_config()
        self.imprint_name = self.config.get("imprint", "unknown_imprint")
        self.imprint_dir = self._get_imprint_directory()

        # Ensure imprint directory exists
        self.imprint_dir.mkdir(parents=True, exist_ok=True)

    def _load_and_validate_config(self) -> Dict[str, Any]:
        """Load and validate the imprint configuration."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = json.load(f)

        # Validate and cure defects
        config = self._cure_config_defects(config)
        return config

    def _cure_config_defects(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration and fix any defects."""
        logger.info("Validating and curing configuration defects...")

        # Ensure required fields exist
        required_fields = {
            "imprint": "New Imprint",
            "publisher": "Nimble Books LLC",
            "contact_email": "info@nimblebooks.com"
        }

        for field, default in required_fields.items():
            if not config.get(field):
                config[field] = default
                logger.warning(f"Added missing required field '{field}': {default}")

        # Ensure branding section exists
        if "branding" not in config:
            config["branding"] = {}

        branding_defaults = {
            "brand_colors": {"primary": "#2C3E50", "secondary": "#E74C3C"},
            "tagline": f"Excellence in {config['imprint']} Publishing",
            "website": "nimblebooks.com"
        }

        for field, default in branding_defaults.items():
            if field not in config["branding"]:
                config["branding"][field] = default
                logger.warning(f"Added missing branding field '{field}'")

        # Ensure publishing focus exists
        if "publishing_focus" not in config:
            config["publishing_focus"] = {
                "primary_genres": ["Non-Fiction"],
                "target_audience": "General Adult",
                "specialization": "General Publishing",
                "languages": ["eng"]
            }

        # Ensure fonts section exists
        if "fonts" not in config:
            config["fonts"] = {
                "body": "Adobe Caslon Pro",
                "heading": "Adobe Caslon Pro",
                "korean": "Apple Myungjo",
                "quotations": "Adobe Caslon Pro",
                "mnemonics": "Adobe Caslon Pro"
            }

        # Ensure publisher persona exists (for prompts)
        if "publisher_persona" not in config:
            config["publisher_persona"] = {
                "persona_name": f"{config['imprint']} Editorial Team",
                "persona_bio": f"Professional editorial team focused on {', '.join(config['publishing_focus']['primary_genres'])} publishing",
                "risk_tolerance": "Moderate",
                "decision_style": "Collaborative",
                "preferred_topics": "\n".join(config['publishing_focus']['primary_genres']),
                "target_demographics": config['publishing_focus']['target_audience'],
                "vulnerabilities": "Ensuring content quality and market fit"
            }

        # Ensure wizard configuration exists
        if "wizard_configuration" not in config:
            config["wizard_configuration"] = {
                "name": config["imprint"],
                "charter": f"Publishing excellent {', '.join(config['publishing_focus']['primary_genres'])} content",
                "imprint_type": config['publishing_focus']['primary_genres'][0],
                "genres": config['publishing_focus']['primary_genres'],
                "book_format": "6x9 Paperback",
                "price_point": 24.99,
                "page_count": 200,
                "catalog_size": 12,
                "enable_ideation": True
            }

        logger.info("Configuration validation and curing completed")
        return config

    def _get_imprint_directory(self) -> Path:
        """Get the directory path for this imprint."""
        imprint_slug = self.imprint_name.lower().replace(" ", "_").replace("-", "_")
        return project_root / "imprints" / imprint_slug

    def generate_complete_pipeline(self) -> Dict[str, str]:
        """Generate all pipeline components for the imprint."""
        logger.info(f"Generating complete pipeline for imprint: {self.imprint_name}")

        results = {}

        # Create all pipeline components
        results["cover_template"] = self.generate_cover_template()
        results["interior_template"] = self.generate_interior_template()
        results["prepress_processor"] = self.generate_prepress_processor()
        results["prompts"] = self.generate_custom_prompts()
        results["schedule"] = self.generate_initial_schedule()

        # Generate rights offering sheet if enabled
        try:
            rights_sheet = self.generate_rights_offering_sheet()
            if rights_sheet:
                results["rights_offering_sheet"] = rights_sheet
        except Exception as e:
            logger.warning(f"Could not generate rights offering sheet: {e}")

        # Save updated config to imprint directory
        config_path = self.imprint_dir / f"{self.imprint_name.lower().replace(' ', '_')}.json"
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        results["config"] = str(config_path)

        logger.info(f"Pipeline generation complete for {self.imprint_name}")
        return results

    def generate_cover_template(self) -> str:
        """Generate customized cover template."""
        logger.info("Generating cover template...")

        # Load base template
        base_template_path = project_root / "templates" / "cover_template.tex"
        if not base_template_path.exists():
            base_template_path = project_root / "imprints" / "default" / "cover_template.tex"

        if base_template_path.exists():
            with open(base_template_path, 'r') as f:
                template_content = f.read()
        else:
            template_content = self._generate_base_cover_template()

        # Customize template based on config
        template_content = self._customize_cover_template(template_content)

        # Save to imprint directory
        output_path = self.imprint_dir / "cover_template.tex"
        with open(output_path, 'w') as f:
            f.write(template_content)

        logger.info(f"Cover template saved to: {output_path}")
        return str(output_path)

    def _generate_base_cover_template(self) -> str:
        """Generate a base cover template if none exists."""
        return '''% Cover template for {imprint_name}
\\documentclass[12pt]{{article}}

% Required packages
\\usepackage{{fontspec}}
\\usepackage{{geometry}}
\\usepackage{{xcolor}}
\\usepackage{{graphicx}}
\\usepackage{{tikz}}
\\usepackage{{ifthen}}

% Font setup
\\newfontfamily\\bodyfont{{{body_font}}}
\\newfontfamily\\headingfont{{{heading_font}}}

% Color definitions
\\definecolor{{primarycolor}}{{HTML}}{{{primary_color}}}
\\definecolor{{secondarycolor}}{{HTML}}{{{secondary_color}}}

% Page setup
\\geometry{{paperwidth=6.125in, paperheight=9.25in, margin=0in}}
\\pagestyle{{empty}}

\\begin{{document}}

% Cover content goes here
\\begin{{tikzpicture}}[remember picture,overlay]
    \\fill[primarycolor] (current page.south west) rectangle (current page.north east);

    % Title
    \\node[text=white, font=\\Huge\\headingfont, text width=5in, align=center]
        at ([yshift=-2in]current page.north) {{\\booktitle}};

    % Author
    \\node[text=white, font=\\Large\\bodyfont, text width=5in, align=center]
        at ([yshift=-4in]current page.north) {{\\bookauthor}};

    % Imprint logo/name
    \\node[text=secondarycolor, font=\\large\\bodyfont]
        at ([yshift=0.5in]current page.south) {{{imprint_name}}};
\\end{{tikzpicture}}

\\end{{document}}
'''.format(
            imprint_name=self.imprint_name,
            body_font=self.config.get("fonts", {}).get("body", "Adobe Caslon Pro"),
            heading_font=self.config.get("fonts", {}).get("heading", "Adobe Caslon Pro"),
            primary_color=self.config.get("branding", {}).get("brand_colors", {}).get("primary", "2C3E50").lstrip("#"),
            secondary_color=self.config.get("branding", {}).get("brand_colors", {}).get("secondary", "E74C3C").lstrip("#")
        )

    def _customize_cover_template(self, template_content: str) -> str:
        """Customize cover template based on imprint configuration."""
        # Replace font references
        fonts = self.config.get("fonts", {})
        for font_type, font_name in fonts.items():
            template_content = template_content.replace(f"{{{font_type}_font}}", font_name)

        # Replace color references
        colors = self.config.get("branding", {}).get("brand_colors", {})
        for color_type, color_value in colors.items():
            clean_color = color_value.lstrip("#")
            template_content = template_content.replace(f"{{{color_type}_color}}", clean_color)

        # Add imprint-specific customizations
        template_content = template_content.replace("{imprint_name}", self.imprint_name)

        return template_content

    def generate_interior_template(self) -> str:
        """Generate customized interior template."""
        logger.info("Generating interior template...")

        # Load base template
        base_template_path = project_root / "templates" / "template.tex"
        if not base_template_path.exists():
            base_template_path = project_root / "imprints" / "default" / "template.tex"

        if base_template_path.exists():
            with open(base_template_path, 'r') as f:
                template_content = f.read()
        else:
            template_content = self._generate_base_interior_template()

        # Customize template
        template_content = self._customize_interior_template(template_content)

        # Save to imprint directory
        output_path = self.imprint_dir / "template.tex"
        with open(output_path, 'w') as f:
            f.write(template_content)

        logger.info(f"Interior template saved to: {output_path}")
        return str(output_path)

    def _generate_base_interior_template(self) -> str:
        """Generate a base interior template if none exists."""
        return '''% Interior template for {imprint_name}
\\documentclass[12pt,twoside]{{book}}

% Required packages
\\usepackage{{fontspec}}
\\usepackage{{geometry}}
\\usepackage{{fancyhdr}}
\\usepackage{{titlesec}}
\\usepackage{{tocloft}}

% Font setup
\\setmainfont{{{body_font}}}
\\newfontfamily\\headingfont{{{heading_font}}}
\\newfontfamily\\quotefont{{{quote_font}}}

% Page geometry
\\geometry{{
    paperwidth=6in,
    paperheight=9in,
    inner=0.75in,
    outer=0.5in,
    top=0.75in,
    bottom=0.75in
}}

% Headers and footers
\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyhead[LE]{{\\thepage}}
\\fancyhead[RO]{{\\thepage}}
\\fancyhead[RE]{{\\small\\bookauthor}}
\\fancyhead[LO]{{\\small\\booktitle}}

% Chapter formatting
\\titleformat{{\\chapter}}
    {{\\headingfont\\huge\\bfseries}}
    {{\\thechapter}}
    {{1em}}
    {{}}

\\begin{{document}}

% Title page
\\begin{{titlepage}}
\\centering
\\vspace*{{2in}}
{{\\Huge\\headingfont \\booktitle}}\\\\[1cm]
{{\\Large\\headingfont \\booksubtitle}}\\\\[2cm]
{{\\large \\bookauthor}}\\\\[3cm]
\\vfill
{{\\large {imprint_name}}}
\\end{{titlepage}}

% Copyright page
\\newpage
\\thispagestyle{{empty}}
\\vspace*{{\\fill}}
\\noindent
Copyright © \\bookyear\\ \\bookauthor\\\\[0.5cm]
All rights reserved.\\\\[0.5cm]
Published by {imprint_name}\\\\
{publisher}\\\\[0.5cm]
ISBN: \\bookisbn

\\tableofcontents

% Main content starts here
% Chapters will be inserted by the prepress processor

\\end{{document}}
'''.format(
            imprint_name=self.imprint_name,
            publisher=self.config.get("publisher", "Nimble Books LLC"),
            body_font=self.config.get("fonts", {}).get("body", "Adobe Caslon Pro"),
            heading_font=self.config.get("fonts", {}).get("heading", "Adobe Caslon Pro"),
            quote_font=self.config.get("fonts", {}).get("quotations", "Adobe Caslon Pro")
        )

    def _customize_interior_template(self, template_content: str) -> str:
        """Customize interior template based on imprint configuration."""
        # Replace font references
        fonts = self.config.get("fonts", {})
        for font_type, font_name in fonts.items():
            template_content = template_content.replace(f"{{{font_type}_font}}", font_name)

        # Replace imprint-specific information
        template_content = template_content.replace("{imprint_name}", self.imprint_name)
        template_content = template_content.replace("{publisher}", self.config.get("publisher", "Nimble Books LLC"))

        return template_content

    def generate_prepress_processor(self) -> str:
        """Generate customized prepress processor."""
        logger.info("Generating prepress processor...")

        # Create prepress processor based on imprint configuration
        processor_content = self._generate_prepress_content()

        # Save to imprint directory
        output_path = self.imprint_dir / "prepress.py"
        with open(output_path, 'w') as f:
            f.write(processor_content)

        logger.info(f"Prepress processor saved to: {output_path}")
        return str(output_path)

    def _generate_prepress_content(self) -> str:
        """Generate the prepress processor content."""

        # Get values for template substitution
        values = {
            'imprint_name': self.imprint_name,
            'publisher': self.config.get("publisher", "Nimble Books LLC"),
            'class_name': self.imprint_name.replace(" ", "").replace("-", ""),
            'focus_areas': json.dumps(self.config.get("publishing_focus", {}).get("primary_genres", [])),
            'target_audience': self.config.get("publishing_focus", {}).get("target_audience", "General Adult"),
            'specialized_processing': json.dumps(self._get_specialized_processing_rules()),
            'formatting_rules': self._generate_formatting_rules()
        }

        template_str = '''#!/usr/bin/env python3
"""
Prepress processor for {imprint_name}
Customized content processor for this imprint's specific needs.
"""

import logging
import json
import re
import shutil
import uuid
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

import fitz  # PyMuPDF

# Import base prepress utilities
try:
    from codexes.modules.prepress.tex_utils import compile_tex_to_pdf, escape_latex, markdown_to_latex
    from codexes.modules.covers.cover_generator import create_cover_latex
    from codexes.modules.prepress.partsofthebook_processor import PartsOfTheBookProcessor
    from codexes.modules.distribution.quote_processor import QuoteProcessor
except ModuleNotFoundError:
    from src.codexes.modules.prepress.tex_utils import compile_tex_to_pdf, escape_latex, markdown_to_latex
    from src.codexes.modules.covers.cover_generator import create_cover_latex
    from src.codexes.modules.prepress.partsofthebook_processor import PartsOfTheBookProcessor
    from src.codexes.modules.distribution.quote_processor import QuoteProcessor

logger = logging.getLogger(__name__)

# Imprint-specific configuration
IMPRINT_CONFIG = {{
    "name": "{imprint_name}",
    "publisher": "{publisher}",
    "focus": {focus_areas},
    "target_audience": "{target_audience}",
    "specialized_processing": {specialized_processing}
}}

class {class_name}Processor:
    """
    Specialized prepress processor for {imprint_name}.
    Handles content processing specific to this imprint's focus areas.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the processor with imprint-specific settings."""
        self.imprint_config = IMPRINT_CONFIG
        self.template_dir = Path(__file__).parent

    def process_manuscript(self, input_path: str, output_dir: str, metadata: Dict[str, Any]) -> Dict[str, str]:
        """
        Process manuscript for {imprint_name} publication.

        Args:
            input_path: Path to input manuscript
            output_dir: Directory for output files
            metadata: Book metadata dictionary

        Returns:
            Dictionary with paths to generated files
        """
        logger.info(f"Processing manuscript for {{self.imprint_config['name']}}")

        input_path = Path(input_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {{}}

        # Load and process manuscript content
        content = self._load_manuscript(input_path)
        content = self._apply_imprint_formatting(content)

        # Generate LaTeX content
        latex_content = self._generate_latex(content, metadata)
        latex_path = output_dir / "manuscript.tex"
        with open(latex_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        results["latex"] = str(latex_path)

        # Compile to PDF
        pdf_path = compile_tex_to_pdf(str(latex_path), str(output_dir))
        if pdf_path:
            results["pdf"] = pdf_path

        # Generate cover
        cover_path = self._generate_cover(metadata, output_dir)
        if cover_path:
            results["cover"] = cover_path

        return results

    def _load_manuscript(self, input_path: Path) -> str:
        """Load manuscript content from various formats."""
        if input_path.suffix.lower() == '.md':
            with open(input_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif input_path.suffix.lower() == '.txt':
            with open(input_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported input format: {{input_path.suffix}}")

    def _apply_imprint_formatting(self, content: str) -> str:
        """Apply {imprint_name}-specific formatting rules."""{formatting_rules}

        return content

    def _generate_latex(self, content: str, metadata: Dict[str, Any]) -> str:
        """Generate LaTeX document using imprint template."""
        # Load template
        template_path = self.template_dir / "template.tex"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {{template_path}}")

        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # Convert content to LaTeX
        latex_content = markdown_to_latex(content)

        # Replace template variables
        template_vars = {{
            "booktitle": escape_latex(metadata.get("title", "Untitled")),
            "booksubtitle": escape_latex(metadata.get("subtitle", "")),
            "bookauthor": escape_latex(metadata.get("author", "Unknown Author")),
            "bookyear": str(datetime.now().year),
            "bookisbn": metadata.get("isbn", ""),
            "content": latex_content
        }}

        for var, value in template_vars.items():
            template = template.replace("\\\\{" + var + "}", str(value))

        return template

    def _generate_cover(self, metadata: Dict[str, Any], output_dir: Path) -> Optional[str]:
        """Generate cover using imprint template."""
        try:
            cover_template = self.template_dir / "cover_template.tex"
            if cover_template.exists():
                return create_cover_latex(metadata, str(cover_template), str(output_dir))
        except Exception as e:
            logger.warning(f"Cover generation failed: {{e}}")
        return None

def main():
    """CLI interface for the prepress processor."""
    import argparse

    parser = argparse.ArgumentParser(description="Process manuscript for {imprint_name}")
    parser.add_argument("input", help="Input manuscript file")
    parser.add_argument("output", help="Output directory")
    parser.add_argument("--metadata", help="JSON file with book metadata")

    args = parser.parse_args()

    # Load metadata
    metadata = {{}}
    if args.metadata and Path(args.metadata).exists():
        with open(args.metadata, 'r') as f:
            metadata = json.load(f)

    # Process manuscript
    processor = {class_name}Processor()
    results = processor.process_manuscript(args.input, args.output, metadata)

    print("Processing complete:")
    for file_type, path in results.items():
        print(f"  {{file_type}}: {{path}}")

if __name__ == "__main__":
    main()
'''

        # Use Template for safe substitution
        template = Template(template_str)
        return template.safe_substitute(values)

    def _get_specialized_processing_rules(self) -> Dict[str, Any]:
        """Generate specialized processing rules based on imprint focus."""
        genres = self.config.get("publishing_focus", {}).get("primary_genres", [])

        rules = {}

        if "Science" in genres or "Technology" in genres:
            rules["equations"] = True
            rules["citations"] = "academic"
            rules["figures"] = "technical"

        if "Philosophy" in genres:
            rules["quotations"] = "enhanced"
            rules["footnotes"] = "extensive"

        if "Fiction" in genres:
            rules["dialogue"] = "formatted"
            rules["chapters"] = "numbered"

        return rules

    def _generate_formatting_rules(self) -> str:
        """Generate formatting rules code based on imprint focus."""
        genres = self.config.get("publishing_focus", {}).get("primary_genres", [])

        rules = []

        if "Science" in genres or "Technology" in genres:
            rules.append('''
        # Scientific formatting
        content = re.sub(r'\\b(\\d+\\.\\d+)\\b', r'\\\\num{\\1}', content)  # Format numbers
        content = re.sub(r'\\b(Figure|Table)\\s+(\\d+)', r'\\\\autoref{fig:\\2}', content)  # Reference formatting''')

        if "Philosophy" in genres:
            rules.append('''
        # Philosophy formatting
        content = re.sub(r'"([^"]+)"', r'\\\\enquote{\\1}', content)  # Proper quotations
        content = re.sub(r'\\b(cf\\.|i\\.e\\.|e\\.g\\.)\\b', r'\\\\textit{\\1}', content)  # Latin abbreviations''')

        if "Fiction" in genres:
            rules.append('''
        # Fiction formatting
        content = re.sub(r'^"([^"]+)"$', r'\\\\begin{quote}\\1\\\\end{quote}', content, flags=re.MULTILINE)  # Dialogue blocks''')

        if not rules:
            rules.append('''
        # General formatting
        content = re.sub(r'--', r'---', content)  # Em dashes
        content = re.sub(r'\\.\\.\\.', r'\\\\ldots', content)  # Ellipses''')

        return "\n".join(rules)

    def generate_custom_prompts(self) -> str:
        """Generate customized prompts for the imprint."""
        logger.info("Generating custom prompts...")

        # Generate prompts based on imprint configuration
        prompts = self._create_imprint_prompts()

        # Save to imprint directory
        output_path = self.imprint_dir / "prompts.json"
        with open(output_path, 'w') as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)

        logger.info(f"Custom prompts saved to: {output_path}")
        return str(output_path)

    def _create_imprint_prompts(self) -> Dict[str, Any]:
        """Create imprint-specific prompts based on configuration."""
        persona = self.config.get("publisher_persona", {})
        focus = self.config.get("publishing_focus", {})
        branding = self.config.get("branding", {})

        return {
            "_metadata": {
                "imprint": self.imprint_name,
                "generated_at": datetime.now().isoformat(),
                "specialization": focus.get("specialization", "General Publishing")
            },
            "content_generation": {
                "book_description": {
                    "system_prompt": f"You are an expert {self.imprint_name} editor with deep knowledge of {', '.join(focus.get('primary_genres', []))} publishing. Create compelling book descriptions that align with our editorial standards and target audience: {focus.get('target_audience', 'General Adult')}.",
                    "user_prompt_template": "Create a professional book description for a {genre} book titled '{title}' by {author}. The book should appeal to our core readership and reflect our imprint's commitment to {tagline}. Include compelling hooks and clear value proposition.",
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                "chapter_outline": {
                    "system_prompt": f"You are a {self.imprint_name} editorial consultant specializing in {', '.join(focus.get('primary_genres', []))} content. Create detailed chapter outlines that meet our publishing standards and editorial philosophy: {persona.get('persona_bio', 'Professional editorial excellence')}.",
                    "user_prompt_template": "Create a comprehensive chapter outline for a {page_count} page {genre} book titled '{title}'. Each chapter should be substantial, well-structured, and contribute to the overall narrative arc. Target audience: {target_audience}.",
                    "max_tokens": 1500,
                    "temperature": 0.6
                },
                "marketing_copy": {
                    "system_prompt": f"You are a {self.imprint_name} marketing specialist who understands our brand voice and target demographic. Create marketing content that reflects our tagline: '{branding.get('tagline', 'Excellence in Publishing')}' and resonates with {focus.get('target_audience', 'our readers')}.",
                    "user_prompt_template": "Create marketing copy for '{title}' by {author}. Include: back cover blurb, social media posts, and promotional taglines. Emphasize what makes this book special for our {genre} readership.",
                    "max_tokens": 800,
                    "temperature": 0.8
                }
            },
            "editorial_review": {
                "content_assessment": {
                    "system_prompt": f"You are the {persona.get('persona_name', 'Editorial Director')} of {self.imprint_name}. Your approach is {persona.get('decision_style', 'Collaborative')} and your risk tolerance is {persona.get('risk_tolerance', 'Moderate')}. Evaluate content based on our editorial standards and market positioning.",
                    "user_prompt_template": "Review this {content_type} for publication consideration. Assess: 1) Alignment with our {genre} focus, 2) Market potential for {target_audience}, 3) Editorial quality, 4) Brand fit. Provide specific recommendations.",
                    "max_tokens": 1000,
                    "temperature": 0.4
                },
                "sensitivity_review": {
                    "system_prompt": f"You are conducting a sensitivity review for {self.imprint_name}. Consider our target demographics: {persona.get('target_demographics', 'General readers')} and our editorial vulnerabilities: {persona.get('vulnerabilities', 'Market fit concerns')}.",
                    "user_prompt_template": "Conduct a sensitivity review of this content. Identify potential issues for our readership, suggest modifications if needed, and assess overall appropriateness for {imprint_name} publication.",
                    "max_tokens": 800,
                    "temperature": 0.3
                }
            },
            "production_support": {
                "title_suggestions": {
                    "system_prompt": f"You are a {self.imprint_name} title consultant with expertise in {', '.join(focus.get('primary_genres', []))} markets. Create titles that will perform well with our target audience and reflect our brand positioning.",
                    "user_prompt_template": "Suggest 10 compelling titles for a {genre} book about {topic}. Consider SEO, shelf appeal, and brand consistency with {imprint_name}. Include subtitle options for the top 3 choices.",
                    "max_tokens": 600,
                    "temperature": 0.9
                },
                "cover_concepts": {
                    "system_prompt": f"You are a {self.imprint_name} cover design consultant familiar with {', '.join(focus.get('primary_genres', []))} market expectations and our brand colors: {branding.get('brand_colors', {}).get('primary', 'brand appropriate')} palette.",
                    "user_prompt_template": "Describe 3 cover concepts for '{title}' by {author}. Consider genre conventions, target audience appeal, and brand consistency. Include color schemes, imagery, and typography recommendations.",
                    "max_tokens": 700,
                    "temperature": 0.8
                }
            }
        }

    def generate_initial_schedule(self) -> str:
        """Generate initial publication schedule."""
        logger.info("Generating initial publication schedule...")

        # Create initial schedule based on catalog size
        schedule_data = self._create_publication_schedule()

        # Save to imprint directory
        output_path = self.imprint_dir / "schedule.csv"
        self._save_schedule_csv(schedule_data, output_path)

        logger.info(f"Initial schedule saved to: {output_path}")
        return str(output_path)

    def _create_publication_schedule(self) -> List[Dict[str, Any]]:
        """Create initial publication schedule based on imprint configuration."""
        wizard_config = self.config.get("wizard_configuration", {})
        catalog_size = wizard_config.get("catalog_size", 12)
        genres = self.config.get("publishing_focus", {}).get("primary_genres", ["Non-Fiction"])

        schedule = []
        start_date = datetime.now()

        for i in range(catalog_size):
            # Stagger publication dates every 3-4 weeks
            pub_date = start_date + timedelta(weeks=3*i + (i//4)*1)

            # Cycle through genres
            genre = genres[i % len(genres)]

            book_entry = {
                "book_id": f"BK{i+1:03d}",
                "title": f"{genre} Book {i+1}",
                "subtitle": f"An Exploration in {genre}",
                "author": f"Author {i+1}",
                "genre": genre,
                "target_audience": self.config.get("publishing_focus", {}).get("target_audience", "General Adult"),
                "page_count": wizard_config.get("page_count", 200),
                "price": wizard_config.get("price_point", 24.99),
                "format": wizard_config.get("book_format", "6x9 Paperback"),
                "publication_date": pub_date.strftime("%Y-%m-%d"),
                "status": "planned",
                "imprint": self.imprint_name,
                "notes": f"Initial catalog book focusing on {genre.lower()} content"
            }

            schedule.append(book_entry)

        return schedule

    def _save_schedule_csv(self, schedule_data: List[Dict[str, Any]], output_path: Path):
        """Save schedule data as CSV file."""
        import csv

        if not schedule_data:
            return

        fieldnames = schedule_data[0].keys()

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(schedule_data)

    def generate_rights_offering_sheet(self) -> Optional[str]:
        """Generate rights offering sheet for the imprint."""
        if generate_imprint_rights_sheet is None:
            logger.warning("Rights management module not available, skipping offering sheet generation")
            return None

        logger.info("Generating rights offering sheet...")

        try:
            # Save current config to temp file for rights sheet generation
            config_path = self.imprint_dir / f"{self.imprint_name.lower().replace(' ', '_')}.json"
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            # Create output directory for rights materials
            rights_output_dir = self.imprint_dir / "rights_materials"
            rights_output_dir.mkdir(exist_ok=True)

            # Generate offering sheet
            result = generate_imprint_rights_sheet(
                imprint_config_path=str(config_path),
                output_dir=str(rights_output_dir)
            )

            if result:
                logger.info(f"Rights offering sheet generated: {result}")
                return result
            else:
                logger.warning("Rights offering sheet generation returned no result")
                return None

        except Exception as e:
            logger.error(f"Error generating rights offering sheet: {e}")
            return None


def main():
    """CLI interface for the imprint pipeline generator."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate complete imprint pipeline")
    parser.add_argument("config", help="Path to imprint configuration JSON file")
    parser.add_argument("--output-dir", help="Override output directory")

    args = parser.parse_args()

    try:
        # Generate pipeline
        generator = ImprintPipelineGenerator(args.config)
        results = generator.generate_complete_pipeline()

        print(f"✅ Pipeline generated successfully for: {generator.imprint_name}")
        print(f"📁 Output directory: {generator.imprint_dir}")
        print("\n📋 Generated files:")
        for component, path in results.items():
            print(f"  {component}: {path}")

        print(f"\n🚀 Your imprint is ready for operation!")
        print(f"   Templates: {generator.imprint_dir}")
        print(f"   Processor: {generator.imprint_dir}/prepress.py")
        print(f"   Prompts: {generator.imprint_dir}/prompts.json")
        print(f"   Schedule: {generator.imprint_dir}/schedule.csv")

    except Exception as e:
        print(f"❌ Error generating pipeline: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()