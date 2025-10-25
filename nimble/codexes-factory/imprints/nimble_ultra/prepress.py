#!/usr/bin/env python3
"""
Prepress processor for Nimble Ultra Global
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
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

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
IMPRINT_CONFIG = {
    "name": "Nimble Ultra Global",
    "publisher": "Nimble Books LLC",
    "focus": ["History", "Political Science", "Military", "Government"],
    "target_audience": "General Adult, Academic, and Professional",
    "specialized_processing": True
}

class NimbleUltraGlobalProcessor:
    """
    Specialized prepress processor for Nimble Ultra Global.
    Handles content processing specific to this imprint's focus areas.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the processor with imprint-specific settings."""
        self.imprint_config = IMPRINT_CONFIG
        self.template_dir = Path(__file__).parent

        # Initialize Jinja2 environment for template-based LaTeX generation
        templates_path = self.template_dir / "templates"
        self.jinja_env = None
        if templates_path.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(templates_path)),
                autoescape=False,  # LaTeX needs manual escaping
                trim_blocks=True,
                lstrip_blocks=True
            )
            # Add custom filters
            self.jinja_env.filters['escape_latex'] = escape_latex
            self.jinja_env.filters['markdown_to_latex'] = markdown_to_latex
            self.jinja_env.filters['preprocess_markdown'] = self._preprocess_markdown
            self.jinja_env.filters['markdown_to_latex_skip_first'] = self._markdown_to_latex_skip_first
            self.jinja_env.filters['first_value'] = lambda d: list(d.values())[0] if isinstance(d, dict) else str(d)
            logger.info(f"Jinja2 template system initialized from {templates_path}")

    def process_manuscript(self, input_path: str, output_dir: str, metadata: Dict[str, Any]) -> Dict[str, str]:
        """
        Process manuscript for Nimble Ultra Global publication.

        Args:
            input_path: Path to input manuscript
            output_dir: Directory for output files
            metadata: Book metadata dictionary

        Returns:
            Dictionary with paths to generated files
        """
        logger.info(f"Processing manuscript for {self.imprint_config['name']}")

        input_path = Path(input_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {}

        # Check if input is a PDF for direct inclusion
        if input_path.suffix.lower() == '.pdf':
            # Validate PDF page sizes (must be 8.5" x 11" portrait)
            try:
                self._validate_pdf_page_sizes(input_path)
            except ValueError as e:
                logger.error(f"❌ PDF validation failed: {e}")
                raise ValueError(f"PDF validation failed: {e}") from e

            # Copy PDF to build directory for inclusion
            pdf_body_path = output_dir / "pdf_body_source.pdf"
            shutil.copy2(input_path, pdf_body_path)
            logger.info(f"✅ Copied PDF body source to {pdf_body_path}")

            # Generate minimal LaTeX content (front matter + back matter only)
            latex_content = self._generate_latex_with_pdf_body(metadata)
            results["pdf_body_source"] = str(pdf_body_path)
        else:
            # Load and process manuscript content
            content = self._load_manuscript(input_path)
            content = self._apply_imprint_formatting(content)

            # Generate LaTeX content
            latex_content = self._generate_latex(content, metadata)

        # Generate safe filename from title
        title = metadata.get('title', 'untitled')
        safe_filename = self._make_safe_filename(title)

        latex_path = output_dir / f"{safe_filename}.tex"
        with open(latex_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        results["latex"] = str(latex_path)

        # Compile to PDF (uses tex filename stem for output)
        pdf_path = compile_tex_to_pdf(latex_path, output_dir)
        if pdf_path:
            results["pdf"] = pdf_path

        # Save JSON metadata with safe filename (after successful PDF generation)
        json_path = output_dir / f"{safe_filename}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        results["json"] = str(json_path)
        logger.info(f"✅ Saved metadata to {json_path}")

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
        elif input_path.suffix.lower() == '.pdf':
            # PDF files are handled separately for direct inclusion
            raise ValueError(f"PDF files should be handled by PDF inclusion path, not text loading")
        else:
            raise ValueError(f"Unsupported input format: {input_path.suffix}")

    def _make_safe_filename(self, title: str, max_length: int = 100) -> str:
        """
        Create a safe filename from a title.

        Args:
            title: The book title
            max_length: Maximum filename length

        Returns:
            Safe filename string
        """
        import re

        # Remove special characters, keep alphanumeric, spaces, hyphens
        safe = re.sub(r'[^\w\s-]', '', title)
        # Replace spaces with underscores
        safe = re.sub(r'\s+', '_', safe)
        # Collapse multiple underscores
        safe = re.sub(r'_+', '_', safe)
        # Limit length
        safe = safe[:max_length]
        # Remove leading/trailing underscores
        safe = safe.strip('_')
        # Fallback if empty
        if not safe:
            safe = "untitled"
        return safe

    def _validate_pdf_page_sizes(self, pdf_path: Path) -> None:
        """
        Validate that all pages in PDF are 8.5" x 11" portrait.

        Args:
            pdf_path: Path to PDF file to validate

        Raises:
            ValueError: If any page does not match required dimensions
        """
        # Expected dimensions in points (72 points per inch)
        EXPECTED_WIDTH = 8.5 * 72  # 612 points
        EXPECTED_HEIGHT = 11 * 72  # 792 points
        TOLERANCE = 2  # Allow 2 points tolerance for rounding

        logger.info(f"📏 Validating PDF page sizes: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)
            invalid_pages = []
            total_pages = len(doc)

            for page_num in range(total_pages):
                page = doc[page_num]
                rect = page.rect
                width = rect.width
                height = rect.height

                # Check if page is portrait (height > width)
                is_portrait = height > width

                # Check if dimensions match expected size (within tolerance)
                width_match = abs(width - EXPECTED_WIDTH) <= TOLERANCE
                height_match = abs(height - EXPECTED_HEIGHT) <= TOLERANCE

                if not (is_portrait and width_match and height_match):
                    invalid_pages.append({
                        "page": page_num + 1,
                        "width_inches": round(width / 72, 2),
                        "height_inches": round(height / 72, 2),
                        "is_portrait": is_portrait
                    })

            doc.close()

            if invalid_pages:
                error_details = "\n".join([
                    f"  Page {p['page']}: {p['width_inches']}\" x {p['height_inches']}\" "
                    f"({'portrait' if p['is_portrait'] else 'landscape'})"
                    for p in invalid_pages
                ])
                error_msg = (
                    f"PDF contains {len(invalid_pages)} page(s) that are not 8.5\" x 11\" portrait:\n"
                    f"{error_details}\n"
                    f"All pages must be 8.5\" x 11\" portrait orientation."
                )
                raise ValueError(error_msg)

            logger.info(f"✅ All {total_pages} pages are 8.5\" x 11\" portrait")

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Failed to validate PDF: {e}") from e

    def _apply_imprint_formatting(self, content: str) -> str:
        """Apply Nimble Ultra Global-specific formatting rules."""
        # Apply intelligence document formatting
        # Add redacted text styling
        content = re.sub(r'\[REDACTED\]', r'\\textcolor{gray}{[REDACTED]}', content)

        # Format speaker tags for oral history sections
        content = re.sub(r'^([A-Z][A-Z\s]+):', r'\\textbf{\1:}', content, flags=re.MULTILINE)

        # Add annotation markers
        content = re.sub(r'\*\*Note:\*\*', r'\\marginpar{\\textit{Note:}}', content)

        return content

    def _generate_latex(self, content: str, metadata: Dict[str, Any]) -> str:
        """Generate LaTeX document using imprint template."""
        # Load template
        template_path = self.template_dir / "template.tex"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # Convert content to LaTeX
        latex_content = markdown_to_latex(content)

        # Replace template variables
        template_vars = {
            "booktitle": escape_latex(metadata.get("title", "Untitled")),
            "booksubtitle": escape_latex(metadata.get("subtitle", "")),
            "bookauthor": escape_latex(metadata.get("author", "Unknown Author")),
            "bookyear": str(datetime.now().year),
            "bookisbn": metadata.get("isbn", ""),
            "content": latex_content
        }

        for var, value in template_vars.items():
            template = template.replace("\\{" + var + "}", str(value))

        return template

    def _generate_latex_with_pdf_body(self, metadata: Dict[str, Any]) -> str:
        """Generate LaTeX document that includes PDF body and AI-generated content."""
        title = escape_latex(metadata.get("title", "Untitled"))
        author = escape_latex(metadata.get("author", "Unknown Author"))

        # Check if we have pipeline content
        logger.info(f"🔍 DEBUG _generate_latex: metadata keys: {list(metadata.keys())}")
        logger.info(f"🔍 DEBUG _generate_latex: '_pipeline_content' in metadata: {'_pipeline_content' in metadata}")

        pipeline_content = metadata.get("_pipeline_content", {})
        has_pipeline_content = bool(pipeline_content)

        logger.info(f"🔍 DEBUG _generate_latex: pipeline_content keys: {list(pipeline_content.keys()) if pipeline_content else 'None'}")
        logger.info(f"🔍 DEBUG _generate_latex: has_pipeline_content: {has_pipeline_content}")

        if has_pipeline_content:
            logger.info("✅ Including AI-generated content from pipeline in LaTeX document")
            if 'front_matter' in pipeline_content:
                logger.info(f"✅ DEBUG: Front matter sections: {list(pipeline_content['front_matter'].keys())}")
            if 'back_matter' in pipeline_content:
                logger.info(f"✅ DEBUG: Back matter sections: {list(pipeline_content['back_matter'].keys())}")
        else:
            logger.warning("⚠️ DEBUG: NO pipeline_content found - generating minimal LaTeX template")

        # --- Copyright Page Content ---
        # Check for assigned ISBN first, then fallback to other fields
        isbn = metadata.get('assigned_isbn') or metadata.get('isbn13') or metadata.get('isbn')
        if isbn and isbn != "Unknown" and isbn != "TBD":
            # Use ISBNFormatter for proper hyphenation and validation
            try:
                try:
                    from codexes.modules.metadata.isbn_formatter import ISBNFormatter
                except ModuleNotFoundError:
                    from src.codexes.modules.metadata.isbn_formatter import ISBNFormatter

                isbn_formatter = ISBNFormatter()

                # Generate properly formatted ISBN for copyright page
                formatted_isbn = isbn_formatter.generate_copyright_page_isbn(isbn)
                isbn_line = f"{escape_latex(formatted_isbn)}\\\\[2em]"
                logger.info(f"✅ Using formatted ISBN for copyright page: {formatted_isbn}")
            except Exception as e:
                logger.warning(f"ISBN formatting failed, using original: {e}")
                isbn_line = f"ISBN: {escape_latex(isbn)}\\\\[2em]"
                logger.info(f"✅ Using original ISBN for copyright page: {isbn}")
        else:
            isbn_line = ""
            logger.info("No valid ISBN found for copyright page")

        version = escape_latex(f"v1.0-{datetime.now().strftime('%Y%m%d')}")
        copyright_year = datetime.now().year

        # Extract keywords for copyright page
        keywords_section = ""
        if has_pipeline_content:
            front_matter_data = pipeline_content.get("front_matter", {})
            if "bibliographic_key_phrases" in front_matter_data:
                keywords = self._extract_content(front_matter_data["bibliographic_key_phrases"])
                if keywords:
                    keywords_latex = escape_latex(keywords)
                    keywords_section = f"""
\\subsection*{{Subject Headings}}
{keywords_latex}"""
                    logger.info("✅ Including bibliographic keywords on copyright page")

        # Copyright page must always be on page ii (verso after title page i)
        copyright_content = f"""\\clearpage
\\thispagestyle{{empty}}
\\vspace*{{1in}}
\\begin{{center}}
\\large
Nimble Ultra is an imprint of Nimble Books LLC.\\\\
Ann Arbor, Michigan, USA\\\\
http://NimbleBooks.com\\\\
Inquiries: info@nimblebooks.com\\\\[2em]
Copyright \\copyright {copyright_year} by Nimble Books LLC. All rights reserved.\\\\[2em]
{isbn_line}
Version: {version}
\\end{{center}}
{keywords_section}"""

        # --- Table of Contents - must start on odd page (recto) ---
        toc_content = """\\cleardoublepage
\\thispagestyle{{empty}}
\\tableofcontents*
\\cleardoublepage"""

        # --- Build Front Matter Sections ---
        front_matter_sections = ""
        if has_pipeline_content:
            front_matter_data = pipeline_content.get("front_matter", {})

            # Motivation - pass raw parsed_content for template detection
            if "motivation" in front_matter_data:
                raw_content = front_matter_data["motivation"]
                # Extract the actual dict if it's nested in parsed_content
                if isinstance(raw_content, dict) and 'publishers_note' in raw_content:
                    content_to_format = raw_content['publishers_note']
                else:
                    content_to_format = self._extract_content(raw_content)
                if content_to_format:
                    front_matter_sections += self._format_section(
                        "Motivation",
                        content_to_format,
                        use_markdown=True
                    )

            # Historical Context - pass raw for template detection
            if "historical_context" in front_matter_data:
                raw_content = front_matter_data["historical_context"]
                # Extract the actual nested dict if present
                if isinstance(raw_content, dict) and 'historical_context' in raw_content:
                    content_to_format = raw_content['historical_context']
                else:
                    content_to_format = self._extract_content(raw_content)
                if content_to_format:
                    front_matter_sections += self._format_section(
                        "Historical Context",
                        content_to_format,
                        use_markdown=True
                    )

            # Abstracts - markdown string content
            if "abstracts_x4" in front_matter_data:
                abstracts_content = self._extract_content(front_matter_data["abstracts_x4"])
                if abstracts_content:
                    front_matter_sections += self._format_section(
                        "Abstracts",
                        abstracts_content,
                        use_markdown=True
                    )

            # Important Passages - markdown string content
            if "important_passages" in front_matter_data:
                passages_content = self._extract_content(front_matter_data["important_passages"])
                if passages_content:
                    front_matter_sections += self._format_section(
                        "Important Passages",
                        passages_content,
                        use_markdown=True
                    )

        # --- Back Matter Intro Page ---
        back_matter_intro = """\\backmatter
\\chapter*{Back Matter}
\\addcontentsline{toc}{chapter}{Back Matter}

This section contains supplementary materials including indices to help readers navigate the document.

\\section*{Information}

Indexes are generated with reference to the current document's pagination, not the original.

\\cleardoublepage

% Custom footer for back matter with "Back Matter - N" format
\\makeoddfoot{mypagestyle}{}{Back Matter~-~}{\\thepage}
\\makeevenfoot{mypagestyle}{\\thepage}{Back Matter~-~}{}
"""

        # --- Build Back Matter Sections ---
        back_matter_sections = ""
        if has_pipeline_content:
            back_matter_data = pipeline_content.get("back_matter", {})

            # Index of Persons - can be markdown or list - ONLY include if non-empty
            if "index_persons" in back_matter_data:
                raw_content = back_matter_data["index_persons"]
                # Extract the actual content
                if isinstance(raw_content, dict) and 'index_of_persons' in raw_content:
                    persons_content = raw_content['index_of_persons']
                else:
                    persons_content = self._extract_content(raw_content)
                # Only add if content exists and is not empty/whitespace
                if persons_content and str(persons_content).strip():
                    # Check if content is substantive (not just error messages or placeholders)
                    content_str = str(persons_content).strip().lower()
                    if content_str and not content_str.startswith('no ') and not content_str.startswith('none'):
                        back_matter_sections += self._format_section(
                            "Index of Persons",
                            persons_content,
                            use_markdown=True
                        )

            # Index of Places - can be markdown or list of dicts - ONLY include if non-empty
            if "index_places" in back_matter_data:
                raw_content = back_matter_data["index_places"]
                # Extract the actual content (could be list or string)
                if isinstance(raw_content, dict) and 'index_of_places' in raw_content:
                    places_content = raw_content['index_of_places']
                else:
                    places_content = self._extract_content(raw_content)
                # Only add if content exists and is not empty/whitespace
                if places_content and str(places_content).strip():
                    # Check if content is substantive (not just error messages or placeholders)
                    content_str = str(places_content).strip().lower()
                    if content_str and not content_str.startswith('no ') and not content_str.startswith('none'):
                        back_matter_sections += self._format_section(
                            "Index of Places",
                            places_content,
                            use_markdown=True
                        )

            # Mnemonics (special handling for LaTeX) - at end of back matter
            if "mnemonics" in back_matter_data:
                logger.info("🔍 DEBUG: Found mnemonics in back_matter_data, extracting...")
                mnemonics_content = self._extract_mnemonics(back_matter_data["mnemonics"])
                logger.info(f"🔍 DEBUG: Extracted mnemonics content: {len(mnemonics_content)} chars")
                if mnemonics_content:
                    # Mnemonics already contain LaTeX
                    # Just ensure proper spacing around major structural elements
                    import re

                    # Add line breaks only around major structural elements
                    mnemonics_content = re.sub(r'(\\chapter\*\{[^}]+\})\s*', r'\1\n', mnemonics_content)
                    mnemonics_content = re.sub(r'(\\addcontentsline\{[^}]+\}\{[^}]+\}\{[^}]+\})\s*', r'\1\n\n', mnemonics_content)
                    mnemonics_content = re.sub(r'\\begin\{itemize\}', r'\n\\begin{itemize}\n', mnemonics_content)
                    mnemonics_content = re.sub(r'\\end\{itemize\}', r'\n\\end{itemize}\n\n', mnemonics_content)
                    mnemonics_content = re.sub(r'\\item\s+', r'\n    \\item ', mnemonics_content)

                    # Ensure it ends with cleardoublepage
                    if not mnemonics_content.strip().endswith("\\cleardoublepage"):
                        mnemonics_content = mnemonics_content.rstrip() + "\n\n\\cleardoublepage\n"

                    back_matter_sections += f"\n{mnemonics_content}\n"
                    logger.info("✅ DEBUG: Added formatted mnemonics to back_matter_sections")
                else:
                    logger.warning("⚠️  DEBUG: mnemonics_content was empty after extraction")
            else:
                logger.warning("⚠️  DEBUG: 'mnemonics' not found in back_matter_data")

        return f"""\\documentclass[11pt,twoside]{{memoir}}
\\normalsize

% --- Page Geometry ---
\\setstocksize{{9in}}{{6in}}
\\settrimmedsize{{9in}}{{6in}}{{*}}
\\settrims{{0pt}}{{0pt}}

\\setlrmarginsandblock{{1in}}{{1in}}{{*}}
\\setulmarginsandblock{{0.75in}}{{*}}{{1}}

\\setheadfoot{{24pt}}{{24pt}}
\\setlength{{\\headdrop}}{{2pt}}
\\setlength{{\\headsep}}{{12pt}}
\\checkandfixthelayout
\\frenchspacing

% --- Font Setup ---
\\usepackage{{fontspec}}
\\setmainfont{{Adobe Caslon Pro}}
\\setsansfont{{Neulis Sans}}

% --- Packages ---
\\usepackage{{pdfpages}}
\\usepackage{{microtype}}
\\usepackage{{xcolor}}
\\usepackage{{graphicx}}

% --- Page Style Setup ---
\\makepagestyle{{mypagestyle}}
\\makeoddhead{{mypagestyle}}{{}}{{}}{{\\large\\scshape\\sffamily {title}}}
\\makeevenhead{{mypagestyle}}{{\\small\\textit{{{author}}}}}{{}}{{}}
\\makeoddfoot{{mypagestyle}}{{}}{{}}{{\\thepage}}
\\makeevenfoot{{mypagestyle}}{{\\thepage}}{{}}{{}}
\\pagestyle{{mypagestyle}}

\\begin{{document}}

% --- Title page (i) - unnumbered ---
\\thispagestyle{{empty}}
\\begin{{titlingpage}}
\\begin{{center}}
\\vspace*{{\\fill}}
{{\\Huge\\bfseries {title}}}\\\\[1cm]
{{\\Large {author}}}\\\\[2cm]
\\vspace*{{\\fill}}
\\end{{center}}
\\end{{titlingpage}}

% --- Copyright page (ii - verso) - unnumbered ---
{copyright_content}

% --- Table of Contents (iii - recto) - unnumbered ---
{toc_content}

% --- Start roman numerals at page v (recto) for front matter ---
\\pagenumbering{{roman}}
\\setcounter{{page}}{{5}}
\\pagestyle{{mypagestyle}}

{front_matter_sections}

% --- Main matter - switch to arabic numerals with BODY:N format ---
\\mainmatter
\\pagenumbering{{arabic}}
\\setcounter{{page}}{{1}}

% Custom footer for body with "BODY:N" format
\\makeoddfoot{{mypagestyle}}{{}}{{BODY:}}{{\\thepage}}
\\makeevenfoot{{mypagestyle}}{{\\thepage}}{{BODY:}}{{}}

\\IfFileExists{{pdf_body_source.pdf}}{{%
  \\includepdf[pages=-,pagecommand={{}}]{{pdf_body_source.pdf}}
}}{{%
  \\chapter{{Content}}
  \\textit{{No PDF content found. The original PDF should be included here.}}
}}

% --- Back matter with custom numbering ---
{back_matter_intro}

{back_matter_sections}

\\end{{document}}
"""

    def _extract_content(self, section_data: Dict[str, Any]) -> str:
        """
        Extract content from a pipeline section, handling JSON and errors gracefully.

        Args:
            section_data: Section data from pipeline (either parsed_content dict directly,
                         or a dict with 'content' key)

        Returns:
            Extracted content string, or empty string if extraction fails
        """
        if not section_data:
            return ""

        # Handle case where section_data is the parsed_content dict directly
        # (which has keys like 'keywords', 'publishers_note', 'historical_context', etc.)
        if "content" not in section_data:
            # Check if it's a dict with error
            if isinstance(section_data, dict) and "error" in section_data:
                logger.warning(f"Skipping section with error: {section_data.get('error', 'Unknown error')}")
                return ""

            # Try common content keys used in parsed_content responses
            content_keys_to_try = [
                "keywords", "publishers_note", "historical_context", "abstracts_x4",
                "important_passages", "index_of_persons", "index_of_places",
                "passages", "persons", "places", "text", "content", "motivation", "context"
            ]
            for key in content_keys_to_try:
                if key in section_data:
                    return str(section_data[key])

            # If no specific key found, return the whole dict as string (will be ugly but visible)
            logger.warning(f"No recognized content key in section_data, available keys: {list(section_data.keys())}")
            return str(section_data)

        # Original logic: section_data has a 'content' key
        content = section_data["content"]

        # Handle dict content directly
        if isinstance(content, dict):
            if "error" in content:
                logger.warning(f"Skipping section with error: {content.get('error', 'Unknown error')}")
                return ""
            # Try common content keys
            for key in ["keywords", "text", "content", "motivation", "context", "passages", "persons", "places"]:
                if key in content:
                    return str(content[key])
            # If no specific key found, return the whole dict as string (will be ugly but visible)
            logger.warning(f"No recognized content key in dict, available keys: {list(content.keys())}")
            return str(content)

        # Check for errors in string content
        if isinstance(content, str):
            try:
                content_json = json.loads(content)
                if isinstance(content_json, dict) and "error" in content_json:
                    logger.warning(f"Skipping section with error: {content_json.get('error', 'Unknown error')}")
                    return ""
                # If it's a dict with specific content keys, extract them
                if isinstance(content_json, dict):
                    # Try common content keys
                    for key in ["keywords", "text", "content", "motivation", "context", "passages", "persons", "places"]:
                        if key in content_json:
                            return str(content_json[key])
                    # If no specific key found, return the whole JSON as string
                    logger.warning(f"No recognized content key in parsed JSON, available keys: {list(content_json.keys())}")
                    return str(content_json)
            except json.JSONDecodeError:
                # Not JSON, return as-is
                pass

        return str(content)

    def _extract_mnemonics(self, section_data: Dict[str, Any]) -> str:
        """
        Extract mnemonics content, which is already in LaTeX format.

        Args:
            section_data: Section data from pipeline (either parsed_content dict directly,
                         or a dict with 'content' key)

        Returns:
            LaTeX content string, or empty string if extraction fails
        """
        if not section_data:
            return ""

        # Handle case where section_data is the parsed_content dict directly
        if "content" not in section_data:
            # Check for errors
            if isinstance(section_data, dict):
                if "error" in section_data:
                    logger.warning(f"Skipping mnemonics with error: {section_data.get('error', 'Unknown error')}")
                    return ""
                # Extract mnemonics_tex field directly from parsed_content
                if "mnemonics_tex" in section_data:
                    tex_content = section_data["mnemonics_tex"]
                    # Remove leading comment that might interfere with LaTeX compilation
                    # The LLM might generate: "% Comment text \\chapter*{Mnemonics}..."
                    # We need to remove just the "% Comment text " part
                    tex_content = tex_content.strip()
                    if tex_content.startswith('%'):
                        # Find the first backslash (start of LaTeX command) after the %
                        idx = tex_content.find('\\')
                        if idx > 0:
                            tex_content = tex_content[idx:]
                    return tex_content
                # If doesn't have mnemonics_tex, it's an error
                logger.warning(f"Mnemonics section_data missing 'mnemonics_tex' field: {list(section_data.keys())}")
                return ""
            return ""

        # Original logic: section_data has a 'content' key
        content = section_data["content"]

        # Check for errors
        if isinstance(content, dict):
            if "error" in content:
                logger.warning(f"Skipping mnemonics with error: {content.get('error', 'Unknown error')}")
                return ""
            # Extract mnemonics_tex field
            if "mnemonics_tex" in content:
                tex_content = content["mnemonics_tex"]
                # Remove leading comment
                tex_content = tex_content.strip()
                if tex_content.startswith('%'):
                    idx = tex_content.find('\\')
                    if idx > 0:
                        tex_content = tex_content[idx:]
                return tex_content
            # If content is a dict but doesn't have mnemonics_tex, it's an error
            logger.warning(f"Mnemonics content is a dict but missing 'mnemonics_tex' field: {list(content.keys())}")
            return ""

        if isinstance(content, str):
            try:
                content_json = json.loads(content)
                if isinstance(content_json, dict):
                    if "error" in content_json:
                        logger.warning(f"Skipping mnemonics with error: {content_json.get('error', 'Unknown error')}")
                        return ""
                    # Extract mnemonics_tex field
                    if "mnemonics_tex" in content_json:
                        tex_content = content_json["mnemonics_tex"]
                        # Remove leading comment
                        tex_content = tex_content.strip()
                        if tex_content.startswith('%'):
                            idx = tex_content.find('\\')
                            if idx > 0:
                                tex_content = tex_content[idx:]
                        return tex_content
            except json.JSONDecodeError:
                # Not JSON, return as-is (might already be LaTeX)
                pass

        return str(content)

    def _preprocess_markdown(self, content: str) -> str:
        """
        Preprocess markdown to fix common LLM-generated formatting issues.

        Args:
            content: Markdown content

        Returns:
            Preprocessed markdown
        """
        import re

        # Fix LLM responses that smash headings and body text together on one line
        # Pattern: ### Heading Text (capital letter starting new sentence)
        # Solution: Insert \n\n before headings and after headings

        # First, ensure headings are on their own lines (add newlines before ###)
        content = re.sub(r'([^\n])(#{1,6}\s+)', r'\1\n\n\2', content)

        # Second, split heading text from body text
        # Look for: "### Heading Words" followed by sentence-starting words
        # Common sentence starters: This, The, With, In, etc.
        content = re.sub(
            r'(#{1,6}\s+[^\n]+?)\s+((?:This|The|With|In|A|An|By|For|After|During|Following|Before|It)\s)',
            r'\1\n\n\2',
            content
        )

        # Fix missing spaces after bold/italic markers followed by capital letter
        # E.g., "**Context**This document" -> "**Context** This document"
        content = re.sub(r'\*\*([A-Z])', r'** \1', content)
        content = re.sub(r'\*([A-Z])', r'* \1', content)

        # Fix missing spaces after sections/headings followed by capital letter
        # E.g., "SituationThis document" -> "Situation This document"
        content = re.sub(r'([a-z])([A-Z][a-z]+\s[A-Z])', r'\1 \2', content)

        # Insert newline before ## (but not before escaped \##)
        content = re.sub(r'(?<!\\)(\s+)(#{2,})\s+', r'\n\n\2 ', content)

        # Insert newline before lists if inline
        content = re.sub(r'(\S)(\s+)([-*])\s+', r'\1\n\n\3 ', content)

        # Convert markdown blockquotes (>) to proper format for pandoc
        # Ensure blockquotes have proper newlines
        lines = content.split('\n')
        processed_lines = []
        in_blockquote = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('>'):
                if not in_blockquote:
                    # Add blank line before blockquote if not already there
                    if processed_lines and processed_lines[-1].strip():
                        processed_lines.append('')
                    in_blockquote = True
                processed_lines.append(line)
            else:
                if in_blockquote and stripped:
                    # Add blank line after blockquote
                    processed_lines.append('')
                    in_blockquote = False
                processed_lines.append(line)

        return '\n'.join(processed_lines)

    def _markdown_to_latex_skip_first(self, content: str, title: str) -> str:
        """
        Convert markdown to LaTeX, optionally skipping first heading if it matches title.

        Args:
            content: Markdown content
            title: Section title to match against first heading

        Returns:
            LaTeX content
        """
        return markdown_to_latex(content, skip_first_heading_if_matches=title)

    def _detect_content_type(self, content: Any) -> str:
        """
        Detect the type of content structure for template selection.

        Args:
            content: Content to analyze

        Returns:
            Content type identifier: 'dict_with_title', 'nested_dict', 'list', 'markdown', 'latex', or 'unknown'
        """
        if not content:
            return 'unknown'

        if isinstance(content, dict):
            # Check for title/content structure
            if 'title' in content and 'content' in content:
                return 'dict_with_title'
            # Check for nested dict (multiple keys with dict values)
            if len(content) > 1 and any(isinstance(v, dict) for v in content.values()):
                return 'nested_dict'
            # Single-key dict is likely markdown content
            return 'markdown'
        elif isinstance(content, list):
            return 'list'
        elif isinstance(content, str):
            # Try to detect if it's LaTeX or markdown
            if content.strip().startswith('\\chapter') or content.strip().startswith('\\section'):
                return 'latex'
            return 'markdown'

        return 'unknown'

    def _render_with_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render content using a Jinja2 template.

        Args:
            template_name: Name of the template file (e.g., 'section_markdown.tex.j2')
            context: Template context variables

        Returns:
            Rendered LaTeX content, or empty string if template not found
        """
        if not self.jinja_env:
            logger.warning("Jinja2 environment not initialized, cannot use templates")
            return ""

        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            logger.warning(f"Template not found: {template_name}")
            return ""
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}", exc_info=True)
            return ""

    def _format_section(self, title: str, content: Any, use_markdown: bool = True) -> str:
        """
        Format a section with title and content for LaTeX inclusion.
        Uses Jinja2 templates if available, falls back to legacy method.

        Args:
            title: Section title
            content: Section content (can be str, dict, or list)
            use_markdown: If True, convert markdown to LaTeX

        Returns:
            Formatted LaTeX section
        """
        # Check if content is empty
        if not content:
            return ""
        if isinstance(content, str) and not content.strip():
            return ""

        # Try template-based rendering first
        if self.jinja_env:
            content_type = self._detect_content_type(content)
            logger.info(f"Formatting section '{title}' with detected type: {content_type}")

            # Select appropriate template based on content type
            template_name = None
            context = {'title': title, 'content': content}

            if content_type == 'dict_with_title':
                # Content is a dict with title and content keys
                template_name = 'section_with_title.tex.j2'
                if isinstance(content, dict):
                    context['title'] = content.get('title', title)
                    context['content'] = content.get('content', '')
            elif content_type == 'nested_dict':
                # Complex nested structure
                template_name = 'nested_dict.tex.j2'
            elif content_type == 'list':
                # List of items (e.g., indices)
                template_name = 'index_list.tex.j2'
                context['items'] = content
            elif content_type == 'latex':
                # Pre-formatted LaTeX
                template_name = 'section_latex.tex.j2'
            elif content_type == 'markdown':
                # Plain markdown string
                template_name = 'section_markdown.tex.j2'
                # Extract actual markdown if it's wrapped in a dict
                if isinstance(content, dict):
                    # Try common keys
                    for key in ['text', 'content', 'markdown']:
                        if key in content:
                            context['content'] = content[key]
                            break
                    else:
                        # Use first value if no recognized key
                        context['content'] = list(content.values())[0] if content else ''

            if template_name:
                rendered = self._render_with_template(template_name, context)
                if rendered:
                    logger.info(f"Successfully rendered section '{title}' using template {template_name}")
                    return rendered
                else:
                    logger.warning(f"Template rendering failed for '{title}', falling back to legacy method")

        # Legacy fallback method
        escaped_title = escape_latex(title)

        # Convert content to string if needed
        if not isinstance(content, str):
            content = str(content)

        # Convert content if needed
        if use_markdown:
            # Preprocess markdown
            content = self._preprocess_markdown(content)
            # Skip first heading if it matches the chapter title
            latex_content = markdown_to_latex(content, skip_first_heading_if_matches=title)
        else:
            latex_content = content

        # Ensure chapter starts on recto (odd) page
        # Don't add cleardoublepage at end to avoid creating extra blank pages
        return f"""\\cleardoublepage
\\chapter*{{{escaped_title}}}
\\addcontentsline{{toc}}{{chapter}}{{{escaped_title}}}

{latex_content}
"""

    def _generate_cover(self, metadata: Dict[str, Any], output_dir: Path) -> Optional[str]:
        """Generate cover using imprint template."""
        try:
            cover_template = self.template_dir / "cover_template.tex"
            if cover_template.exists():
                return create_cover_latex(metadata, str(cover_template), str(output_dir))
        except Exception as e:
            logger.warning(f"Cover generation failed: {e}")
        return None

def main():
    """CLI interface for the prepress processor."""
    import argparse

    parser = argparse.ArgumentParser(description="Process manuscript for Nimble Ultra Global")
    parser.add_argument("input", help="Input manuscript file")
    parser.add_argument("output", help="Output directory")
    parser.add_argument("--metadata", help="JSON file with book metadata")

    args = parser.parse_args()

    # Load metadata
    metadata = {}
    if args.metadata and Path(args.metadata).exists():
        with open(args.metadata, 'r') as f:
            metadata = json.load(f)

    # Process manuscript
    processor = NimbleUltraGlobalProcessor()
    results = processor.process_manuscript(args.input, args.output, metadata)

    print("Processing complete:")
    for file_type, path in results.items():
        print(f"  {file_type}: {path}")

def process_single_book(
        json_path: Path,
        final_output_dir: Path,
        templates_dir: Path,
        debug_cover: bool = False,
        catalog_only: bool = False,
        leave_build_directories_in_place: bool = False,
        config: Dict[str, Any] = None
) -> Optional[Dict]:
    """
    Orchestrates the full prepress process for a single book in Nimble Ultra imprint.
    Handles both regular manuscript processing and PDF body source inclusion.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Processing book: {data.get('title', 'Unknown')}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Could not read or parse JSON file at {json_path}: {e}")
        return None

    # Initialize processor
    processor = NimbleUltraGlobalProcessor()

    # Check if there's a body_source in the data
    body_source = data.get('body_source')

    # Expand ~ in path if present
    if body_source:
        body_source = Path(body_source).expanduser()

    if body_source and Path(body_source).exists():
        logger.info(f"📄 Processing with body source: {body_source}")

        # Transform LLM responses into _pipeline_content structure for prepress
        logger.info(f"🔍 DEBUG: Checking for responses in data. Keys in data: {list(data.keys())}")
        logger.info(f"🔍 DEBUG: 'responses' in data: {'responses' in data}")

        if 'responses' in data:
            try:
                logger.info("🔍 DEBUG: Starting _pipeline_content transformation")
                # Build _pipeline_content from responses
                pipeline_content = {"front_matter": {}, "back_matter": {}}

                # Find the response list (may be under model name key)
                responses_data = data['responses']
                logger.info(f"🔍 DEBUG: responses_data type: {type(responses_data)}")

                if isinstance(responses_data, dict):
                    # Get the first model's responses
                    model_key = list(responses_data.keys())[0]
                    responses_list = responses_data[model_key]
                    logger.info(f"🔍 DEBUG: Found model key: {model_key}, responses count: {len(responses_list)}")
                else:
                    responses_list = responses_data
                    logger.info(f"🔍 DEBUG: Direct responses list, count: {len(responses_list)}")

                # Map prompt keys to front/back matter sections with name transformations
                front_matter_mappings = {
                    'bibliographic_key_phrases': 'bibliographic_key_phrases',
                    'gemini_get_basic_info_from_public_domain': 'basic_info',
                    'motivation': 'motivation',
                    'place_in_historical_context': 'historical_context',
                    'abstracts_x4': 'abstracts_x4',
                    'most_important_passages_with_reasoning': 'important_passages'
                }

                back_matter_mappings = {
                    'index_of_persons': 'index_persons',
                    'index_of_places': 'index_places',
                    'mnemonics_prompt': 'mnemonics'
                }

                # Organize responses into front/back matter
                for i, response in enumerate(responses_list):
                    prompt_key = response.get('prompt_key', '')
                    parsed_content = response.get('parsed_content', {})
                    logger.info(f"🔍 DEBUG: Response {i+1}: prompt_key={prompt_key}, has parsed_content={bool(parsed_content)}")

                    if prompt_key in front_matter_mappings:
                        # Map to expected key name for template
                        mapped_key = front_matter_mappings[prompt_key]
                        pipeline_content['front_matter'][mapped_key] = parsed_content
                        logger.info(f"✅ DEBUG: Added to front_matter[{mapped_key}]")
                    elif prompt_key in back_matter_mappings:
                        # Map to expected key name for template
                        mapped_key = back_matter_mappings[prompt_key]
                        pipeline_content['back_matter'][mapped_key] = parsed_content
                        logger.info(f"✅ DEBUG: Added to back_matter[{mapped_key}]")
                    else:
                        logger.warning(f"⚠️ DEBUG: prompt_key '{prompt_key}' not mapped")

                # Add to data
                data['_pipeline_content'] = pipeline_content
                logger.info(f"✅ Built _pipeline_content with {len(pipeline_content['front_matter'])} front matter and {len(pipeline_content['back_matter'])} back matter sections")
                logger.info(f"🔍 DEBUG: Front matter keys: {list(pipeline_content['front_matter'].keys())}")
                logger.info(f"🔍 DEBUG: Back matter keys: {list(pipeline_content['back_matter'].keys())}")

            except Exception as e:
                logger.error(f"❌ DEBUG: Exception building _pipeline_content: {e}", exc_info=True)

        # Use the processor's process_manuscript method which handles PDFs
        try:
            results = processor.process_manuscript(
                input_path=str(body_source),
                output_dir=str(final_output_dir),
                metadata=data
            )

            # Return results in the expected format for the pipeline
            return {
                "status": "success",
                "pdf_path": results.get("pdf"),
                "cover_path": results.get("cover"),
                "page_count": data.get("pages", 100),  # Default or from metadata
                "processed_file": str(json_path),
                "output_dir": str(final_output_dir)
            }

        except Exception as e:
            logger.error(f"❌ Error processing body source {body_source}: {e}")
            return None
    else:
        logger.info("📝 No body source found, using default content generation")
        # For now, return basic success - this could be expanded for content generation
        return {
            "status": "success",
            "processed_file": str(json_path),
            "output_dir": str(final_output_dir),
            "page_count": data.get("pages", 100)
        }


if __name__ == "__main__":
    main()
