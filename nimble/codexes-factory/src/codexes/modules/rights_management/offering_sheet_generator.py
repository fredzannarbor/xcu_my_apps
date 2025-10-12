#!/usr/bin/env python3
"""
Rights Offering Sheet Generator

Creates professional rights offering sheets for imprints and individual works.
Generates PDF documents suitable for rights fairs and publisher outreach.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

# LaTeX and PDF generation
try:
    from codexes.modules.prepress.tex_utils import compile_tex_to_pdf, escape_latex
except ImportError:
    try:
        from src.codexes.modules.prepress.tex_utils import compile_tex_to_pdf, escape_latex
    except ImportError:
        # Fallback functions if tex_utils not available
        def escape_latex(text):
            return str(text).replace('&', '\\&').replace('%', '\\%').replace('$', '\\$').replace('#', '\\#').replace('^', '\\textasciicircum{}').replace('_', '\\_').replace('{', '\\{').replace('}', '\\}').replace('~', '\\textasciitilde{}').replace('\\', '\\textbackslash{}')

        def compile_tex_to_pdf(tex_file, output_dir):
            logger.warning("LaTeX compilation not available - tex_utils not found")
            return None

try:
    from .crud_operations import RightsManager
    from .database import RightsDatabase
except ImportError:
    from crud_operations import RightsManager
    from database import RightsDatabase

logger = logging.getLogger(__name__)


class RightsOfferingSheetGenerator:
    """
    Generates professional rights offering sheets in PDF format.
    """

    def __init__(self, rights_manager: Optional[RightsManager] = None):
        """Initialize with rights manager."""
        self.rights_manager = rights_manager or RightsManager()

    def generate_imprint_offering_sheet(self, imprint_config_path: str, output_dir: str, isbn_filter: Optional[str] = None) -> Optional[str]:
        """
        Generate rights offering sheet for an entire imprint.

        Args:
            imprint_config_path: Path to imprint configuration JSON
            output_dir: Directory for output files
            isbn_filter: Optional comma-separated list of ISBNs to focus on specific titles

        Returns:
            Path to generated PDF file
        """
        try:
            # Load imprint configuration
            with open(imprint_config_path, 'r') as f:
                imprint_config = json.load(f)

            imprint_name = imprint_config.get('imprint', 'Unknown Imprint')

            # Load imprint catalog if available
            # First try the operational imprints directory (using current working dir as project root)
            imprint_slug = imprint_name.lower().replace(" ", "_").replace("-", "_")

            # Try multiple possible locations for the operational directory
            possible_dirs = [
                Path.cwd() / "imprints" / imprint_slug,  # Standard location
                Path(imprint_config_path).resolve().parent.parent.parent / "imprints" / imprint_slug,  # From configs/imprints/
                Path(imprint_config_path).parent  # Config directory itself
            ]

            catalog_works = []
            for operational_dir in possible_dirs:
                if operational_dir.exists():
                    logger.info(f"Trying to load catalog from: {operational_dir}")
                    catalog_works = self._load_imprint_catalog(operational_dir)
                    if catalog_works:
                        logger.info(f"Successfully loaded {len(catalog_works)} works from {operational_dir}")
                        break

            # If no catalog, get works from database by imprint
            if not catalog_works:
                all_works = self.rights_manager.db.get_works()
                catalog_works = [w for w in all_works if w.get('imprint') == imprint_name]

            if not catalog_works:
                logger.warning(f"No works found for imprint {imprint_name}")
                return None

            # Apply ISBN filter if provided
            if isbn_filter:
                filtered_works = self._filter_works_by_isbn(catalog_works, isbn_filter)
                if filtered_works:
                    catalog_works = filtered_works
                    logger.info(f"Filtered to {len(catalog_works)} works based on ISBN filter: {isbn_filter}")
                else:
                    logger.warning(f"No works found matching ISBN filter: {isbn_filter}")
                    return None

            # Generate LaTeX content
            latex_content = self._generate_imprint_latex(imprint_config, catalog_works)

            # Write and compile
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            tex_file = output_path / f"{imprint_name.lower().replace(' ', '_')}_rights_offering.tex"
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)

            # Compile to PDF
            try:
                pdf_file = compile_tex_to_pdf(tex_file, str(output_path))
                if pdf_file:
                    logger.info(f"Generated rights offering sheet PDF: {pdf_file}")
                    return pdf_file
                else:
                    logger.warning("PDF compilation failed, returning LaTeX file")
                    return str(tex_file)
            except Exception as e:
                logger.warning(f"PDF compilation not available ({e}), returning LaTeX file")
                return str(tex_file)

        except Exception as e:
            logger.error(f"Error generating imprint offering sheet: {e}")
            return None

    def generate_work_offering_sheet(self, work_id: int, output_dir: str, **kwargs) -> Optional[str]:
        """
        Generate rights offering sheet for a specific work.

        Args:
            work_id: Database ID of the work
            output_dir: Directory for output files
            **kwargs: Additional offering parameters (asking_price, territories, etc.)

        Returns:
            Path to generated PDF file
        """
        try:
            # Get work details
            work = self.rights_manager.db.get_work_by_id(work_id)
            if not work:
                logger.error(f"Work not found: {work_id}")
                return None

            # Get rights summary
            rights_summary = self.rights_manager.get_work_rights_summary(work_id)
            available_territories = self.rights_manager.get_available_territories_for_work(work_id)

            # Generate LaTeX content
            latex_content = self._generate_work_latex(work, rights_summary, available_territories, kwargs)

            # Write and compile
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            safe_title = work['title'].lower().replace(' ', '_').replace('/', '_')[:50]
            tex_file = output_path / f"{safe_title}_rights_offering.tex"

            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)

            # Compile to PDF
            pdf_file = compile_tex_to_pdf(tex_file, str(output_path))
            if pdf_file:
                logger.info(f"Generated work rights offering sheet: {pdf_file}")
                return pdf_file
            else:
                return str(tex_file)

        except Exception as e:
            logger.error(f"Error generating work offering sheet: {e}")
            return None

    def _filter_works_by_isbn(self, works: List[Dict[str, Any]], isbn_filter: str) -> List[Dict[str, Any]]:
        """
        Filter works by a comma-separated list of ISBNs.

        Args:
            works: List of work dictionaries
            isbn_filter: Comma-separated string of ISBNs

        Returns:
            Filtered list of works matching the ISBNs
        """
        if not isbn_filter or not isbn_filter.strip():
            return works

        # Parse and clean the ISBN list
        target_isbns = set()
        for isbn in isbn_filter.split(','):
            cleaned_isbn = isbn.strip().replace('-', '').replace(' ', '')
            if cleaned_isbn:
                target_isbns.add(cleaned_isbn)

        if not target_isbns:
            logger.warning("No valid ISBNs found in filter")
            return works

        # Filter works by ISBN
        filtered_works = []
        for work in works:
            # Check both isbn and isbn13 fields
            work_isbn = work.get('isbn', '') or work.get('isbn13', '')
            if work_isbn:
                # Clean the work's ISBN for comparison
                cleaned_work_isbn = str(work_isbn).replace('-', '').replace(' ', '')
                if cleaned_work_isbn in target_isbns:
                    filtered_works.append(work)
                    logger.debug(f"Matched ISBN {cleaned_work_isbn} for work: {work.get('title', 'Unknown')}")

        logger.info(f"Filtered {len(works)} works to {len(filtered_works)} works using ISBN filter")
        return filtered_works

    def _load_imprint_catalog(self, imprint_dir: Path) -> List[Dict[str, Any]]:
        """Load works from imprint schedule or catalog files."""
        catalog_works = []

        # Try to load from schedule.csv
        schedule_file = imprint_dir / "schedule.csv"
        if schedule_file.exists():
            try:
                import csv
                with open(schedule_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('title') and row.get('author'):
                            work = {
                                'title': row.get('title', ''),
                                'subtitle': row.get('subtitle', ''),
                                'author_name': row.get('author', ''),
                                'genre': row.get('genre', ''),
                                'page_count': row.get('page_count', ''),
                                'description': row.get('notes', ''),
                                'publication_date': row.get('publication_date', ''),
                                'isbn': row.get('isbn', '')
                            }
                            catalog_works.append(work)
            except Exception as e:
                logger.warning(f"Error loading schedule.csv: {e}")

        # Try other catalog formats
        for catalog_file in ['books.csv', 'catalog.json', 'family.csv']:
            file_path = imprint_dir / catalog_file
            if file_path.exists() and not catalog_works:
                try:
                    if catalog_file.endswith('.csv'):
                        import csv
                        with open(file_path, 'r') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                if row.get('title') and row.get('author'):
                                    catalog_works.append(dict(row))
                    elif catalog_file.endswith('.json'):
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                catalog_works.extend(data)
                            elif isinstance(data, dict) and 'books' in data:
                                catalog_works.extend(data['books'])
                except Exception as e:
                    logger.warning(f"Error loading {catalog_file}: {e}")

        return catalog_works

    def _generate_imprint_latex(self, imprint_config: Dict[str, Any], works: List[Dict[str, Any]]) -> str:
        """Generate LaTeX content for imprint offering sheet."""
        imprint_name = imprint_config.get('imprint', 'Unknown Imprint')
        publisher = imprint_config.get('publisher', 'Unknown Publisher')
        tagline = imprint_config.get('branding', {}).get('tagline', '')
        contact_email = imprint_config.get('contact_email', '')
        website = imprint_config.get('branding', {}).get('website', '')

        focus_areas = imprint_config.get('publishing_focus', {})
        genres = ', '.join(focus_areas.get('primary_genres', []))
        target_audience = focus_areas.get('target_audience', '')
        specialization = focus_areas.get('specialization', '')

        # Escape LaTeX special characters
        imprint_name_safe = escape_latex(imprint_name)
        publisher_safe = escape_latex(publisher)
        tagline_safe = escape_latex(tagline)

        # Extract single featured work for detailed highlight
        featured_work = works[0] if works else {'title': 'Featured Title', 'author_name': 'AI Lab for Book-Lovers'}

        # Get author names safely
        def get_author_name(work):
            return escape_latex(work.get('author_name', work.get('author', 'AI Lab for Book-Lovers')))

        # Get cover image paths safely
        def get_cover_path(work):
            cover_path = work.get('front_cover_image_path', '')
            if cover_path and Path(cover_path).exists():
                return str(Path(cover_path).resolve())
            return None

        featured_author = get_author_name(featured_work)
        featured_title = escape_latex(featured_work.get('title', 'Featured Title'))
        featured_cover = get_cover_path(featured_work)
        featured_pages = featured_work.get('pages', featured_work.get('page_count', '250'))

        latex_template = f"""\\documentclass[11pt]{{article}}
\\usepackage[letterpaper,margin=1in]{{geometry}}
\\usepackage{{fontspec}}
\\usepackage{{xcolor}}
\\usepackage{{titlesec}}
\\usepackage{{fancyhdr}}
\\usepackage{{graphicx}}
\\usepackage{{hyperref}}
\\usepackage{{array}}
\\usepackage{{tabularx}}
\\usepackage{{wrapfig}}
\\usepackage{{longtable}}
\\usepackage{{booktabs}}
\\usepackage{{colortbl}}

% Fonts (Xynapse Traces specified fonts)
\\setmainfont{{Adobe Caslon Pro}}
\\setsansfont{{Neulis Sans}}

% Colors
\\definecolor{{primarycolor}}{{HTML}}{{2C3E50}}
\\definecolor{{secondarycolor}}{{HTML}}{{E74C3C}}

% Header setup (no header on page 1)
\\fancypagestyle{{firstpage}}{{%
    \\fancyhf{{}}
    \\fancyfoot[C]{{\\thepage}}
    \\renewcommand{{\\headrulewidth}}{{0pt}}
}}

\\fancypagestyle{{otherpages}}{{%
    \\fancyhf{{}}
    \\fancyhead[L]{{\\textcolor{{primarycolor}}{{\\textbf{{RIGHTS OFFERING SHEET}}}}}}
    \\fancyhead[R]{{\\textcolor{{secondarycolor}}{{{imprint_name_safe}}}}}
    \\fancyfoot[C]{{\\thepage}}
}}

\\pagestyle{{otherpages}}

\\begin{{document}}

\\thispagestyle{{firstpage}}

% Title section with imprint name prominently displayed
\\begin{{center}}
{{\\Huge \\textcolor{{primarycolor}}{{{imprint_name_safe}}}}}\\\\[0.3cm]
{{\\Large \\textcolor{{secondarycolor}}{{{publisher_safe}}}}}\\\\[0.2cm]
{{\\large \\textit{{{tagline_safe}}}}}\\\\[0.5cm]
{{\\large \\textbf{{INTERNATIONAL RIGHTS CATALOG}}}}\\\\[0.3cm]
{{\\normalsize Generated: {datetime.now().strftime('%B %Y')}}}
\\end{{center}}

\\vspace{{1cm}}

% Section 1: Imprint Overview with Name
\\section{{{imprint_name_safe}: Imprint Overview}}

\\textbf{{Publisher:}} {publisher_safe}\\\\
\\textbf{{Primary Genres:}} {escape_latex(genres)}\\\\
\\textbf{{Target Audience:}} {escape_latex(target_audience)}\\\\
\\textbf{{Specialization:}} {escape_latex(specialization)}\\\\
\\textbf{{Contact:}} {escape_latex(contact_email)}\\\\
\\textbf{{Website:}} {escape_latex(website)}\\\\

\\vspace{{1cm}}

% Section 2: Enhanced Catalog Information
\\section{{Publishing Philosophy \\& Catalog}}

\\subsection{{{imprint_name_safe} Charter}}

{imprint_name_safe} represents a distinctive approach to {escape_latex(specialization.lower())}. In an era where technology and human understanding intersect at unprecedented scales, our imprint bridges the gap between cutting-edge research and accessible knowledge. We situate ourselves within the global movement toward interdisciplinary thinking, where {escape_latex(genres.lower())} converge to address humanity's most pressing questions.

Our editorial philosophy aligns with international trends toward evidence-based discourse and the democratization of complex knowledge. As readers worldwide seek deeper understanding of technological transformation, geopolitical shifts, and philosophical implications of rapid change, {imprint_name_safe} provides authoritative yet accessible perspectives from leading thinkers and emerging voices.

\\subsection{{Catalog Summary}}

\\begin{{center}}
\\begin{{tabular}}{{|l|r|}}
\\hline
\\textbf{{Metric}} & \\textbf{{Value}} \\\\
\\hline
Total Titles & {len(works)} \\\\
Primary Focus Areas & {len(focus_areas.get('primary_genres', []))} \\\\
Target Markets & Academic \\& Professional \\\\
Publication Frequency & Monthly releases \\\\
Average Length & 200-250 pages \\\\
Language Rights Available & All major languages \\\\
\\hline
\\end{{tabular}}
\\end{{center}}

\\subsection{{Featured Title}}

{self._generate_featured_book_description(featured_title, featured_author, featured_cover, featured_pages)}

\\vspace{{0.5cm}}

\\newpage

% Section 3: Rights Information
\\section{{Rights Information}}

\\subsection{{Available Rights}}
\\begin{{itemize}}
\\item Translation rights for all languages
\\item Audio book rights
\\item Digital/ebook rights
\\item Print rights for specific territories
\\item Educational/academic licensing
\\item Rights for usage in LLM training and generation
\\item AI model training and development rights
\\item Machine learning dataset inclusion rights
\\end{{itemize}}

\\subsection{{Terms \\& Conditions}}
\\begin{{itemize}}
\\item Standard royalty rate: 8\\% of net receipts
\\item Advance payments are due on signature
\\item Typical contract term: 7 years with renewal options
\\item Rights revert if out of print for 12 months
\\item Author approval required for major content changes
\\item Minimum advance varies by territory and rights scope
\\item Digital rights may be licensed separately or bundled
\\end{{itemize}}

\\subsection{{Standard Contract}}
Our comprehensive standard contract template is available on request. The contract includes detailed provisions for:
\\begin{{itemize}}
\\item Rights scope and territorial limitations
\\item Royalty calculations and payment schedules
\\item Quality standards and approval processes
\\item Marketing and promotional obligations
\\item Reversion clauses and renewal terms
\\item Dispute resolution mechanisms
\\end{{itemize}}

\\subsection{{Contact Information}}
\\textbf{{Rights Manager:}} {escape_latex(contact_email)}\\\\
\\textbf{{Publisher:}} {publisher_safe}\\\\
\\textbf{{Response Time:}} 2-3 business days\\\\
\\textbf{{Standard Contract:}} Available on request\\\\

\\vspace{{1cm}}
\\begin{{center}}
\\textit{{All inquiries welcome. We look forward to working with international publishers to bring these titles to new markets.}}
\\end{{center}}

\\newpage

% Appendix: Complete Catalog
\\appendix
\\section{{Complete Forthcoming Catalog}}

{self._generate_complete_catalog(works)}

\\end{{document}}"""

        return latex_template

    def _generate_book_cell(self, title: str, author: str, cover_path: str, index: int) -> str:
        """Generate a single book cell for the highlights grid (1x3 format)."""

        # Define different bullet points for variety (fewer points for narrower cells)
        bullet_sets = [
            ["Cutting-edge analysis", "Expert insights", "Global perspective"],
            ["International scope", "Practical applications", "Future-focused"],
            ["Innovative methodology", "Data-driven approach", "Thought leadership"]
        ]

        bullets = bullet_sets[index % len(bullet_sets)]

        # Generate cell content with proper structure for narrow cells
        cell_content = f"\\textbf{{{title}}} \\\\\n"
        cell_content += f"\\textit{{By {author}}} \\\\[0.2cm]\n"

        # Add thumbnail if cover path exists (smaller for 1x3 format)
        if cover_path and cover_path != 'None':
            # Include thumbnail with smaller sizing for narrow columns
            cell_content += f"\\begin{{center}}\n"
            cell_content += f"\\includegraphics[width=0.6in,height=0.9in,keepaspectratio]{{{cover_path}}}\n"
            cell_content += f"\\end{{center}}\n"
            cell_content += f"\\vspace{{0.15cm}}\n"

        # Add bullet points with proper formatting (fewer bullets for space)
        for bullet in bullets:
            cell_content += f"• {bullet} \\\\\n"

        return cell_content.rstrip(' \\\\\n')  # Remove trailing newlines and backslashes

    def _generate_featured_book_description(self, title: str, author: str, cover_path: str, pages: str) -> str:
        """Generate detailed description for single featured book."""

        # Detailed bullet points for featured book
        detailed_bullets = [
            "Cutting-edge analysis from leading researchers in the field",
            "Comprehensive coverage of contemporary issues and future implications",
            "Expert insights from international perspectives and cross-cultural analysis",
            "Data-driven approach with evidence-based methodologies",
            "Practical applications for academic and professional audiences",
            "Thought leadership positioning within global intellectual discourse",
            "Future-focused frameworks addressing emerging challenges"
        ]

        # Build the featured book description
        description = f"\\textbf{{{title}}}\\\\\n"
        description += f"\\textit{{By {author}}} \\\\[0.4cm]\n\n"

        # Add cover image if available (larger size for single book display)
        if cover_path and cover_path != 'None':
            description += f"\\begin{{wrapfigure}}{{r}}{{2.5in}}\n"
            description += f"\\centering\n"
            description += f"\\includegraphics[width=2.0in,height=3.0in,keepaspectratio]{{{cover_path}}}\n"
            description += f"\\end{{wrapfigure}}\n\n"

        description += f"\\textbf{{Pages:}} {pages}\\\\[0.3cm]\n\n"

        # Add detailed bullet points
        description += "\\textbf{Key Features:}\n"
        description += "\\begin{itemize}\n"
        for bullet in detailed_bullets:
            description += f"\\item {bullet}\n"
        description += "\\end{itemize}\n\n"

        return description

    def _generate_complete_catalog(self, works: List[Dict[str, Any]]) -> str:
        """Generate complete catalog listing using longtable with proper formatting."""

        if not works:
            return "\\textit{No titles currently available.}"

        # Sort works by publication date (ascending)
        sorted_works = self._sort_works_by_date(works)

        # Define subtle row shading (light gray with high opacity for readability)
        catalog_content = """% Define subtle row colors for alternating shading
\\definecolor{lightrowgray}{gray}{0.95}

% Longtable for catalog with page breaks
\\begin{longtable}{p{4.2in} c r}
\\caption{Complete Forthcoming Catalog} \\\\
\\toprule
\\textbf{Title} & \\textbf{Publication} & \\textbf{Pages} \\\\
\\midrule
\\endfirsthead

\\multicolumn{3}{c}{\\tablename\\ \\thetable\\ -- \\textit{Continued from previous page}} \\\\
\\toprule
\\textbf{Title} & \\textbf{Publication} & \\textbf{Pages} \\\\
\\midrule
\\endhead

\\midrule
\\multicolumn{3}{r}{\\textit{Continued on next page}} \\\\
\\endfoot

\\bottomrule
\\endlastfoot

"""

        for i, work in enumerate(sorted_works):
            title = escape_latex(work.get('title', 'Untitled'))
            pages = work.get('pages', work.get('page_count', 'TBD'))

            # Format publication date
            pub_date = self._format_publication_date(work.get('publication_date', work.get('scheduled_date', '')))

            # Determine if this should be a shaded row (every other row)
            if i % 2 == 1:  # Odd rows get light shading
                catalog_content += f"\\rowcolor{{lightrowgray}} \\textbf{{{title}}} & {pub_date} & {pages} \\\\\n"
            else:
                catalog_content += f"\\textbf{{{title}}} & {pub_date} & {pages} \\\\\n"

        catalog_content += "\\end{longtable}\n"

        return catalog_content

    def _sort_works_by_date(self, works: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort works by publication date in ascending order."""
        from datetime import datetime

        def parse_date(work):
            # Try to parse different date formats
            date_str = work.get('publication_date', work.get('scheduled_date', ''))
            if not date_str:
                return datetime.max  # Put undated items at the end

            try:
                # Try YYYY-MM-DD format first (e.g., "2025-09-09")
                if '-' in date_str and len(date_str.split('-')) >= 3:
                    parts = date_str.split('-')
                    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                    return datetime(year, month, day)

                # Try M/D/YY format (e.g., "9/2/25")
                elif '/' in date_str and len(date_str.split('/')) == 3:
                    parts = date_str.split('/')
                    month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
                    # Convert 2-digit year to 4-digit
                    if year < 50:
                        year += 2000
                    elif year < 100:
                        year += 1900
                    return datetime(year, month, day)

                # Try other formats as needed
                return datetime.max
            except:
                return datetime.max

        return sorted(works, key=parse_date)

    def _format_publication_date(self, date_str: str) -> str:
        """Format publication date as Month/Year."""
        if not date_str:
            return "TBD"

        try:
            # Handle YYYY-MM-DD format (e.g., "2025-09-09")
            if '-' in date_str and len(date_str.split('-')) >= 3:
                parts = date_str.split('-')
                year, month = int(parts[0]), int(parts[1])

                # Convert month number to name
                month_names = [
                    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
                ]

                if 1 <= month <= 12:
                    return f"{month_names[month]} {year}"

            # Handle M/D/YY format (e.g., "9/2/25")
            elif '/' in date_str and len(date_str.split('/')) == 3:
                parts = date_str.split('/')
                month, day, year = int(parts[0]), int(parts[1]), int(parts[2])

                # Convert 2-digit year to 4-digit
                if year < 50:
                    year += 2000
                elif year < 100:
                    year += 1900

                # Convert month number to name
                month_names = [
                    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
                ]

                if 1 <= month <= 12:
                    return f"{month_names[month]} {year}"

            return date_str  # Return as-is if can't parse
        except:
            return "TBD"

    def _generate_work_latex(self, work: Dict[str, Any], rights_summary: Dict[str, Any],
                           available_territories: List[Dict[str, Any]], offering_params: Dict[str, Any]) -> str:
        """Generate LaTeX content for individual work offering sheet."""

        title = escape_latex(work.get('title', ''))
        subtitle = escape_latex(work.get('subtitle', ''))
        author = escape_latex(work.get('author_name', ''))
        isbn = work.get('isbn', '')
        genre = escape_latex(work.get('genre', ''))
        pages = work.get('page_count', '')
        description = escape_latex(work.get('description', ''))

        # Territories sold
        territories_sold = rights_summary.get('territories_sold', {})
        sold_list = ""
        for territory, details in territories_sold.items():
            sold_list += f"\\item {escape_latex(territory)} - {escape_latex(details['publisher'])}\n"

        # Available territories
        available_list = ""
        for territory in available_territories[:15]:  # Limit display
            available_list += f"\\item {escape_latex(territory['territory_name'])} ({escape_latex(territory.get('primary_language', 'N/A'))})\n"

        asking_price = offering_params.get('asking_price', 'Negotiable')
        minimum_advance = offering_params.get('minimum_advance', 'Negotiable')

        latex_template = f"""\\documentclass[11pt]{{article}}
\\usepackage[letterpaper,margin=1in]{{geometry}}
\\usepackage{{fontspec}}
\\usepackage{{xcolor}}
\\usepackage{{titlesec}}
\\usepackage{{fancyhdr}}

% Fonts (Xynapse Traces specified fonts)
\\setmainfont{{Adobe Caslon Pro}}
\\setsansfont{{Neulis Sans}}

% Colors
\\definecolor{{primarycolor}}{{HTML}}{{2C3E50}}
\\definecolor{{secondarycolor}}{{HTML}}{{E74C3C}}

% Header
\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyhead[L]{{\\textcolor{{primarycolor}}{{\\textbf{{RIGHTS OFFERING}}}}}}
\\fancyhead[R]{{\\textcolor{{secondarycolor}}{{{title}}}}}
\\fancyfoot[C]{{\\thepage}}

\\begin{{document}}

% Title section
\\begin{{center}}
{{\\Huge \\textcolor{{primarycolor}}{{{title}}}}}\\\\[0.3cm]
"""

        if subtitle:
            latex_template += f"{{\\Large \\textcolor{{secondarycolor}}{{{subtitle}}}}}\\\\[0.2cm]\n"

        latex_template += f"""{{\\large by {author}}}\\\\[0.5cm]
{{\\large \\textbf{{INTERNATIONAL RIGHTS OFFERING}}}}\\\\[0.3cm]
{{\\normalsize {datetime.now().strftime('%B %Y')}}}
\\end{{center}}

\\vspace{{1cm}}

% Book details
\\section{{Book Information}}

\\textbf{{Title:}} {title}\\\\
"""

        if subtitle:
            latex_template += f"\\textbf{{Subtitle:}} {subtitle}\\\\\n"

        latex_template += f"""\\textbf{{Author:}} {author}\\\\
\\textbf{{ISBN:}} {isbn}\\\\
\\textbf{{Genre:}} {genre}\\\\
\\textbf{{Pages:}} {pages}\\\\

\\vspace{{0.5cm}}

\\textbf{{Description:}}\\\\
{description}

\\vspace{{1cm}}

% Rights status
\\section{{Rights Status}}

\\subsection{{Territories Already Licensed}}
\\begin{{itemize}}
{sold_list}
\\end{{itemize}}

\\subsection{{Available Territories}}
\\begin{{itemize}}
{available_list}
\\end{{itemize}}

\\vspace{{1cm}}

% Offering terms
\\section{{Offering Terms}}

\\textbf{{Asking Price:}} {asking_price}\\\\
\\textbf{{Minimum Advance:}} {minimum_advance}\\\\
\\textbf{{Royalty Rate:}} 8-12\\% of net receipts\\\\
\\textbf{{Contract Term:}} 7 years with renewal options\\\\
\\textbf{{Delivery:}} Electronic files (PDF/Word)\\\\

\\vspace{{1cm}}

\\section{{Contact Information}}
For licensing inquiries, please contact:\\\\
\\textbf{{Email:}} rights@nimblebooks.com\\\\
\\textbf{{Response Time:}} 2-3 business days\\\\

\\vspace{{1cm}}
\\begin{{center}}
\\textit{{We welcome inquiries from international publishers and look forward to discussing licensing opportunities for this title.}}
\\end{{center}}

\\end{{document}}"""

        return latex_template


def generate_imprint_rights_sheet(imprint_config_path: str, output_dir: str, isbn_filter: Optional[str] = None) -> Optional[str]:
    """Convenience function to generate imprint rights offering sheet."""
    generator = RightsOfferingSheetGenerator()
    return generator.generate_imprint_offering_sheet(imprint_config_path, output_dir, isbn_filter)


def generate_work_rights_sheet(work_id: int, output_dir: str, **kwargs) -> Optional[str]:
    """Convenience function to generate work rights offering sheet."""
    generator = RightsOfferingSheetGenerator()
    return generator.generate_work_offering_sheet(work_id, output_dir, **kwargs)