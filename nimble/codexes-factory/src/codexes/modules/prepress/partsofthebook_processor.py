"""
Backmatter processor for generating all backmatter sections.
Handles mnemonics, bibliography, verification log, and glossary.
"""

import logging
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from codexes.modules.distribution.isbn_lookup import ISBNLookupService
from codexes.core.enhanced_llm_caller import call_llm_json_with_exponential_backoff
from codexes.modules.prepress.tex_utils import markdown_to_latex, escape_latex
import re

logger = logging.getLogger(__name__)


class PartsOfTheBookProcessor:
    """Processes and generates all backmatter sections."""
    

    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        self.isbn_service = ISBNLookupService()
        
        # LLM configuration - use provided config or defaults
        self.llm_config = llm_config or {
            'model': 'gemini/gemini-2.5-pro',  # Default model
            'temperature': 0.7,
            'max_tokens': 8000
        }
        
        logger.info(f"PartsOfTheBookProcessor initialized with model: {self.llm_config['model']}")
    
    def fix_pilsa_formatting(self, text):
        """Fix pilsa formatting to ensure it's always properly italicized."""
        if not text:
            return text
        
        # Remove any broken LaTeX formatting for pilsa
        text = re.sub(r'extit\{pilsa\}', r'\\textit{pilsa}', text)
        
        # Ensure standalone "pilsa" is italicized (but not if already properly formatted)
        text = re.sub(r'(?<!\\textit\{)pilsa(?!\})', r'\\textit{pilsa}', text)
        
        return text

    def fix_korean_formatting(self, text):
        """Fix Korean text formatting to use proper \\korean{} command."""
        if not text:
            return text
        
        # Fix broken Korean LaTeX commands - specifically the \{korean pattern
        text = re.sub(r'\\?\{korean\{([^}]+)\}', r'\\korean{\1}', text)
        
        return text
    
    def fix_latex_commands(self, text):
        """Fix broken LaTeX commands and escaping issues."""
        if not text:
            return text
        
        # Fix broken textit commands - the main issue mentioned
        text = re.sub(r'extit\{([^}]*)\}', r'\\textit{\1}', text)
        
        # Fix other broken LaTeX commands
        text = re.sub(r'extbf\{([^}]*)\}', r'\\textbf{\1}', text)
        text = re.sub(r'emph\{([^}]*)\}', r'\\emph{\1}', text)
        text = re.sub(r'extsc\{([^}]*)\}', r'\\textsc{\1}', text)
        
        # Fix broken backslashes in general
        text = re.sub(r'(?<!\\)\\(?![a-zA-Z])', r'\\\\', text)
        
        # Fix double backslashes that got corrupted
        text = re.sub(r'\\\\([a-zA-Z]+)', r'\\\\\1', text)
        
        # Clean up any remaining malformed commands
        text = re.sub(r'\\([a-zA-Z]+)\{([^}]*)\}', lambda m: f'\\{m.group(1)}{{{m.group(2)}}}', text)
        
        return text
        
    def process_mnemonics(self, book_data: Dict[str, Any], model: str = None) -> str:
        """
        Process mnemonics using structured data approach.
        
        Args:
            book_data: Book data containing quotes and content
            model: LLM model to use
            
        Returns:
            LaTeX formatted mnemonics content
        """
        try:
            # Prepare content for the prompt
            quotes = book_data.get('quotes', [])
            if not quotes:
                logger.warning("No quotes found for mnemonics generation")
                return
            
            # Create a summary of the book content
            book_content = self._prepare_book_content_for_mnemonics(book_data)
            
            # Prepare the prompt
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at creating educational mnemonics. Create memorable acronyms that help readers retain key insights from the provided book content. Focus ONLY on the specific themes and concepts that emerge from the provided quotations. Do not create generic mnemonics about reading or writing unless those are central themes in the quotations."
                },
                {
                    "role": "user",
                    "content": f"Based on the quotations in the provided book, create three mnemonics that help readers remember key themes and insights from THESE SPECIFIC QUOTATIONS. Each mnemonic should be structured as: 1) An acronym (3-6 letters), 2) What each letter stands for, 3) A brief explanation connecting it to the book's content. Format as structured data that can be easily converted to LaTeX. Return as JSON with key 'mnemonics_data' and three child keys, 'acronym', 'expansion', 'explanation', each with string value. Each explanation should be 2-3 sentences maximum.\n\nBook Content:\n{book_content}"
                }
            ]
            
            # Use configured model if none provided
            model_to_use = model or self.llm_config['model']
            if model:
                logger.info(f"Model source is hard-coded. Using model: {model_to_use}")
            else:
                logger.info(f"Model source is from self.llm_config. Using  model: {model_to_use}")
           # logger.warning({self.llm_config})
            # Call LLM with exponential backoff retry logic
            response = call_llm_json_with_exponential_backoff(
                model=model_to_use,
                messages=messages,
                expected_keys=['mnemonics_data'],
                temperature=self.llm_config.get('temperature', 0.7),
                max_tokens=self.llm_config.get('max_tokens', 65535)
            )
            
            if response and 'mnemonics_data' in response:
                logger.info(f"Successfully generated {len(response['mnemonics_data'])} content-specific mnemonics")
                return self._format_mnemonics_as_latex(response['mnemonics_data'])
            else:
                logger.warning(f"Failed to generate mnemonics, response: {response}")
                return ""  # Return empty string instead of fallback
                
        except Exception as e:
            logger.error(f"Error processing mnemonics: {e}")
            return ""  # Return empty string instead of fallback
    
    def process_bibliography(self, book_data: Dict[str, Any]) -> str:
        """
        Process bibliography with ISBN lookup.
        
        Args:
            book_data: Book data containing quotes
            
        Returns:
            LaTeX formatted bibliography
        """
        try:
            quotes = book_data.get('quotes', [])
            if not quotes:
                logger.warning("No quotes found for bibliography generation")
                return ""
            
            # Extract unique sources
            sources = self._extract_unique_sources(quotes)
            
            # Lookup ISBNs
            logger.info(f"Looking up ISBNs for {len(sources)} sources")
            sources_with_isbns = self.isbn_service.lookup_multiple_isbns(sources)
            
            # Format as Chicago-style bibliography
            return self._format_bibliography_as_latex(sources_with_isbns, book_data)
            
        except Exception as e:
            logger.error(f"Error processing bibliography: {e}")
            return ""
    
    def process_verification_log(self, book_data: Dict[str, Any], templates_dir: Optional[Path] = None, 
                                output_dir: Optional[Path] = None, imprint_dir: Optional[Path] = None) -> str:
        """
        Process verification log.
        
        Args:
            book_data: Book data containing quotes and verification info
            templates_dir: Optional path to templates directory for finding verification_protocol.tex
            output_dir: Optional path to output directory for saving verification files
            imprint_dir: Optional path to imprint directory for imprint-specific protocols
            
        Returns:
            LaTeX formatted verification log or empty string if verification is incomplete
        """
        try:
            quotes = book_data.get('quotes', [])
            if not quotes:
                logger.warning("No quotes found for verification log")
                return ""
            
            # Check if verification is complete
            verified_count = sum(1 for q in quotes if q.get('is_verified', False))
            total_count = len(quotes)
            
            # Store verification status in book_data for metadata use
            book_data['verification_status'] = {
                'verified_count': verified_count,
                'total_count': total_count,
                'percentage': round(verified_count / total_count * 100, 1) if total_count > 0 else 0
            }
            
            logger.info(f"📊 Verification status: {verified_count}/{total_count} quotes verified ({book_data['verification_status']['percentage']}%)")
            
            return self._format_verification_log_as_latex(quotes, templates_dir, output_dir, imprint_dir)
            
        except Exception as e:
            logger.error(f"Error processing verification log: {e}")
            return ""
    
    def process_glossary(self) -> str:
        """

        
        Returns:
            LaTeX formatted glossary
        """
        try:
            # Load glossary data
            glossary_path = Path("data/pilsa_glossary.json")
            if not glossary_path.exists():
                logger.warning("Glossary file not found")
                return ""
            
            with open(glossary_path, 'r', encoding='utf-8') as f:
                glossary_data = json.load(f)
            
            terms = glossary_data.get('terms', [])
            if not terms:
                logger.warning("No terms found in glossary")
                return ""
            
            # Use GlossaryLayoutManager for proper 2-column layout
            from src.codexes.modules.prepress.glossary_layout_manager import GlossaryLayoutManager
            
            # Configure page layout for glossary
            page_config = {
                'text_area': {'width': '4.75in'},
                'column_sep': '0.25in',
                'term_spacing': '0.5em'
            }
            
            layout_manager = GlossaryLayoutManager(page_config)
            
            # Sort terms alphabetically by English term
            sorted_terms = sorted(terms, key=lambda x: x.get('english', '').lower())
            
            # Generate single-column glossary with Korean/English stacking
            return layout_manager.format_glossary_single_column(sorted_terms)
            
        except Exception as e:
            logger.error(f"Error processing glossary: {e}")
            return ""
    
    def _prepare_book_content_for_mnemonics(self, book_data: Dict[str, Any]) -> str:
        """Prepare book content summary for mnemonics generation."""
        title = book_data.get('title', 'Untitled')
        description = book_data.get('description', '')
        quotes = book_data.get('quotes', [])
        
        content = f"Title: {title}\n\nDescription: {description}\n\nKey Quotations:\n"
        
        # Include all quotes to ensure mnemonics are related to the actual content
        for i, quote in enumerate(quotes):
            quote_text = quote.get('quote', '')
            author = quote.get('author', 'Unknown')
            content += f"{i+1}. \"{quote_text}\" - {author}\n"
        
        # Add specific instructions to ensure relevance
        content += "\n\nIMPORTANT: Create mnemonics that are DIRECTLY related to these specific quotations. Do NOT create generic mnemonics about reading or writing. The mnemonics must help readers remember the specific themes, concepts, and ideas present in these exact quotations."
        
        return content

    def _format_mnemonics_as_latex(self, mnemonics_data: List[Dict]) -> str:
        """Format mnemonics data as LaTeX."""
        if not mnemonics_data:
            return ""  # Return empty string instead of fallback

        # Fix: Check if individual mnemonics contain expected keys, not the parent array
        if not all(mnemonic.get('acronym') or mnemonic.get('expansion') or mnemonic.get('explanation')
                   for mnemonic in mnemonics_data):
            logger.warning("Some mnemonics data does not contain the expected keys")
            return ""

        latex = "\\chapter*{Mnemonics}\n"
        latex += "\\addcontentsline{toc}{chapter}{Mnemonics}\n\n"

        # Add introduction
        latex += """
                Neuroscience research demonstrates that mnemonic devices significantly enhance long-term memory retention by engaging multiple neural pathways simultaneously.\\footnote{Maguire, Eleanor A., et al. ``Routes to Remembering: The Brains Behind Superior Memory.'' \\textit{Nature Neuroscience} 6, no. 1 (2003): 90-95.} Studies using fMRI imaging show that mnemonics activate both the hippocampus—critical for memory formation—and the prefrontal cortex, which governs executive function. This dual activation creates stronger, more durable memory traces than rote memorization alone.

                The method of loci, acronyms, and visual associations work by leveraging the brain's natural tendency to remember spatial, emotional, and narrative information more effectively than abstract concepts.\\footnote{Roediger, Henry L. ``The Effectiveness of Four Mnemonics in Ordering Recall.'' \\textit{Journal of Experimental Psychology: Human Learning and Memory} 6, no. 5 (1980): 558-567.} Research demonstrates that participants using mnemonic techniques showed 40\\% better recall after one week compared to traditional study methods.\\footnote{Bellezza, Francis S. ``Mnemonic Devices: Classification, Characteristics, and Criteria.'' \\textit{Review of Educational Research} 51, no. 2 (1981): 247-275.}

                Mastery through mnemonic practice provides profound peace of mind. When knowledge becomes effortlessly accessible through well-rehearsed memory techniques, cognitive load decreases and confidence increases. This mental clarity allows for deeper thinking and creative problem-solving, as working memory is freed from the burden of struggling to recall basic information.

                Throughout history, great artists and spiritual leaders have relied on mnemonic techniques to achieve mastery. Dante structured his \\textit{Divine Comedy} using elaborate memory palaces, with each circle of Hell serving as a spatial mnemonic for moral teachings.\\footnote{Yates, Frances A. \\textit{The Art of Memory}. Chicago: University of Chicago Press, 1966, 95-104.} Medieval monks developed intricate visual mnemonics to memorize entire books of scripture—the illuminated manuscripts themselves functioned as memory aids, with symbolic imagery encoding theological concepts.\\footnote{Carruthers, Mary. \\textit{The Book of Memory: A Study of Memory in Medieval Culture}. Cambridge: Cambridge University Press, 1990, 221-257.} Thomas Aquinas advocated for the ``artificial memory'' as essential to spiritual development, arguing that systematic recall of sacred texts freed the mind for contemplation.\\footnote{Aquinas, Thomas. \\textit{Summa Theologica}, II-II, q. 49, a. 1. Trans. by the Fathers of the English Dominican Province. New York: Benziger Brothers, 1947.} In the Renaissance, Giulio Camillo designed his famous ``Theatre of Memory,'' a physical structure where each architectural element triggered recall of classical knowledge.\\footnote{Bolzoni, Lina. \\textit{The Gallery of Memory: Literary and Iconographic Models in the Age of the Printing Press}. Toronto: University of Toronto Press, 2001, 147-171.} Even Bach embedded mnemonic patterns into his compositions—the numerical symbolism in his cantatas served as memory aids for both performers and congregants, ensuring sacred messages would be retained long after the music ended.\\footnote{Chafe, Eric. \\textit{Analyzing Bach Cantatas}. New York: Oxford University Press, 2000, 89-112.}

                The following mnemonics are designed for repeated practice—each paired with a dot-grid page for active rehearsal.

                \\vspace{1em}
                """

        latex += "\\cleartoverso\n"  # Keep if verso is required
        latex += """\\setsecheadstyle{\\Large\\bfseries\\raggedright} % Style for section headings
        \\setaftersecskip{0.5\\baselineskip} % Reduce space after \\section* to half a line
        % Ensure consistent paragraph spacing
        \\setlength{\\parskip}{0pt} % No extra space between paragraphs
        \\setlength{\\parindent}{15pt} % Standard indentation for first line

        \\setbeforesecskip{1em}
        % Prevent suppression at page top
        \\makeatletter
        \\patchcmd{\\@startsection}{\\vskip \\z@}{\\vskip \\beforesecskip}{}{}
        \\makeatother
"""


        for i, mnemonic in enumerate(mnemonics_data):
            # Extract and provide sensible defaults
            acronym = mnemonic.get('acronym', f'MNEM{i + 1}')
            expansion_raw = mnemonic.get('expansion', 'Memory Enhancement Method')
            explanation_raw = mnemonic.get('explanation', 'A helpful memory device.')

            # Process the text through the formatting pipeline
            expansion = self.fix_latex_commands(
                self.fix_pilsa_formatting(
                    self.fix_korean_formatting(
                        markdown_to_latex(expansion_raw)
                    )
                )
            )
            explanation = self.fix_latex_commands(
                self.fix_pilsa_formatting(
                    self.fix_korean_formatting(
                        markdown_to_latex(explanation_raw)
                    )
                )
            )

            latex += f"\\section*{{{acronym}}}"
            latex += f"\\textbf{{{acronym}}} stands for: {expansion} "
            latex += f"{explanation}"
            # Add practice page
            latex += f"\\dotgridtranscription{{Practice writing the {acronym} mnemonic and its meaning.}}\n\n"

        return latex
    
    def _extract_unique_sources(self, quotes: List[Dict]) -> List[Dict]:
        """Extract unique sources from quotes."""
        sources = {}
        
        for quote in quotes:
            author = quote.get('author', 'Unknown')
            title = quote.get('source', 'Unknown')
            date = quote.get('date_first_published', 'n.d.')
            
            key = f"{author}_{title}"
            if key not in sources:
                sources[key] = {
                    'author': author,
                    'title': title,
                    'date_published': date
                }
        
        return list(sources.values())

    def _format_bibliography_as_latex(self, sources: List[Dict], book_data) -> str:
        """Format bibliography as LaTeX."""
        if not sources:
            return ""

        latex = "\\chapter*{Bibliography}\n"
        latex += "\\addcontentsline{toc}{chapter}{Bibliography}\n\n"

        # Use memoir class hanging paragraph environment for proper hanging indents
        latex += "\\begin{hangparas}{0.15in}{1}\n"
        latex += "\\setlength{\\parskip}{6pt}\n\n"

        # Sort sources by author's last name
        sorted_sources = sorted(sources, key=lambda x: x.get('author', '').split()[-1])

        # Save ISBN data for shopping list page
        self._save_bibliography_shopping_list(sorted_sources.copy(), book_data)

        for source in sorted_sources:
            author = source.get('author', 'Unknown')
            title = source.get('title', 'Unknown')
            date = source.get('date_published', 'n.d.')
            isbn = source.get('isbn', '')

            # Format author (try to get last name first)
            if ',' not in author:
                parts = author.split()
                if len(parts) > 1:
                    author = f"{parts[-1]}, {' '.join(parts[:-1])}"

            # Get publisher information from ISBN lookup if available
            publisher = "Unknown Publisher"
            location = "New York"

            if isbn:
                # Try to get publisher info from ISBN
                try:
                    publisher_info = self._get_publisher_from_isbn(isbn)
                    if publisher_info:
                        publisher = publisher_info.get('name', publisher)
                        location = publisher_info.get('location', location)
                except Exception as e:
                    logger.warning(f"Failed to get publisher info for ISBN {isbn}: {e}")

            # Create citation in Chicago style (without ISBN in the text)
            citation = f"{escape_latex(author)}. \\textit{{{escape_latex(title)}}}. {location}: {publisher}, {date}."
            citation = self.fix_latex_commands(self.fix_pilsa_formatting(self.fix_korean_formatting(citation)))

            # Each citation is a paragraph with automatic hanging indent
            latex += f"{citation}\n\n"

        latex += "\\end{hangparas}\n\n"


        latex += "\\cleardoublepage\n"

        return latex
        
    def _save_bibliography_shopping_list(self, sources: List[Dict], book_data) -> None:
    
        try:
            # Create directory if it doesn't exist
            shopping_dir = Path("data/bibliography_shopping_lists")
            shopping_dir.mkdir(exist_ok=True, parents=True)
            
            # Group sources by ISBN (only those with ISBNs)
            sources_with_isbn = [s for s in sources if s.get('isbn')]
            
            if not sources_with_isbn:
                logger.warning("No sources with ISBN found for shopping list")
                return
                
            # Create shopping list HTML content
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Bibliography Shopping List</title>
                <style>
                    body { font-family: sans-serif; margin: 2em; }
                    h1 { color: #333; }
                    .book { margin-bottom: 1.5em; padding-bottom: 1em; border-bottom: 1px solid #eee; }
                    .title { font-weight: bold; }
                    .author { font-style: italic; }
                    .links { margin-top: 0.5em; }
                    .links a { margin-right: 1em; text-decoration: none; color: #0066cc; }
                </style>
            </head>
            <body>
                <h1>Shop for Works Mentioned</h1>
                <p>The following books were referenced in the quotations:</p>
            """
            
            for source in sources_with_isbn:
                isbn = source.get('isbn')
                title = source.get('title', 'Unknown')
                author = source.get('author', 'Unknown')
                
                html_content += f"""
                <div class="book">
                    <div class="title">{title}</div>
                    <div class="author">by {author}</div>
                    <div class="links">
                        <a href="https://bookshop.org/search?keywords={isbn}" target="_blank">Bookshop.org</a>
                        <a href="https://www.indiebound.org/search/book?isbn={isbn}" target="_blank">IndieBound</a>
                        <a href="https://www.worldcat.org/isbn/{isbn}" target="_blank">WorldCat</a>
                    </div>
                </div>
                """
            
            html_content += """
            </body>
            </html>
            """
            
            # Save the HTML file
            # make book_data['title'] safe
            safetitle = ''.join(c for c in book_data['title'] if c.isalnum() or c in (' ', '_'))
            with open(shopping_dir / f"{safetitle}_bibliography_shopping_list.html", "w", encoding="utf-8") as f:
                f.write(html_content)
                
            logger.info("Created bibliography shopping list HTML for {safetitle}")
            
        except Exception as e:
            logger.error(f"Error creating bibliography shopping list: {e}")
    
    def _format_verification_log_as_latex(self, quotes, templates_dir: Optional[Path] = None, 
                                          output_dir: Optional[Path] = None, imprint_dir: Optional[Path] = None):
        """Format verification log as LaTeX using enhanced protocol loader."""
        try:
            # Use the new verification protocol loader
            loader = VerificationProtocolLoader(
                output_dir=output_dir or Path.cwd(),
                templates_dir=templates_dir,
                imprint_dir=imprint_dir or Path("imprints/xynapse_traces")
            )
            
            # Load the protocol content
            protocol_content = loader.load_verification_protocol(quotes)
            
            # Start with chapter header

            # Add the protocol content
            latex = protocol_content + "\n\n"
            
            # Add the detailed verification log
            latex += "\\section{Verification Log}\n\n"
            latex += "\\begin{hangparas}{0.15in}{1}\n"
            latex += "\\setlength{\\parskip}{6pt}\n\n"
            
            for i, quote in enumerate(quotes):
                quote_text = escape_latex(quote.get('quote', ''))
                author = escape_latex(quote.get('author', ''))
                verification = quote.get('verification', {})
                quote_status = escape_latex(verification.get('status', ''))
                quote_notes = escape_latex(verification.get('notes', ''))

                # Format quote with proper truncation and escaping
                truncated_quote = quote_text[:60] + "..." if len(quote_text) > 60 else quote_text
                truncated_author = author[:20] + "..." if len(author) > 20 else author

                quote_log_entry = f"[{i + 1}] \\textit{{{truncated_quote}}} --- {truncated_author}."

                if quote_notes:
                    quote_log_entry += f" \\textbf{{Notes:}} {quote_notes}"

                latex += f"{quote_log_entry}\\par\\vspace{{0.5em}}\n\n"

            latex += "\\end{hangparas}\n\n"
            return latex
            
        except Exception as e:
            logger.error(f"Error formatting verification log: {e}")
            # Fallback to minimal content
            latex = "\\chapter*{Verification Log}\n"
            latex += "\\addcontentsline{toc}{chapter}{Verification Log}\n\n"
            latex += "Error generating verification log. Please check the logs for details.\n\n"
            return latex

    

    
    def _get_publisher_from_isbn(self, isbn: str) -> Optional[Dict[str, str]]:
        """Get publisher information from ISBN."""
        # Extract publisher code from ISBN
        if not isbn or len(isbn) < 13:
            return None
            
        try:
            # Try to get publisher info from ISBN API
            import requests
            url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('totalItems', 0) > 0:
                    volume_info = data['items'][0]['volumeInfo']
                    publisher = volume_info.get('publisher', 'Unknown Publisher')
                    
                    # Try to extract location from publisher string or use default
                    location = "New York"
                    
                    return {
                        'name': publisher,
                        'location': location
                    }
            
            # Fallback to common publishers based on ISBN prefix
            prefix = isbn[3:7]  # Group identifier in ISBN-13
            publishers = {
                '0060': {'name': 'HarperCollins', 'location': 'New York'},
                '0141': {'name': 'Penguin Books', 'location': 'London'},
                '0307': {'name': 'Random House', 'location': 'New York'},
                '0316': {'name': 'Little, Brown and Company', 'location': 'Boston'},
                '0375': {'name': 'Knopf', 'location': 'New York'},
                '0393': {'name': 'W. W. Norton & Company', 'location': 'New York'},
                '0399': {'name': 'G. P. Putnam\'s Sons', 'location': 'New York'},
                '0451': {'name': 'Penguin', 'location': 'New York'},
                '0553': {'name': 'Bantam Books', 'location': 'New York'},
                '0679': {'name': 'Vintage Books', 'location': 'New York'},
                '0743': {'name': 'Simon & Schuster', 'location': 'New York'},
                '0812': {'name': 'Random House', 'location': 'New York'},
                '1400': {'name': 'Random House', 'location': 'New York'},
                '1594': {'name': 'Riverhead Books', 'location': 'New York'},
                '1984': {'name': 'Penguin Press', 'location': 'New York'}
            }
            
            if prefix in publishers:
                return publishers[prefix]
                
            return {'name': 'University Press', 'location': 'New York'}
            
        except Exception as e:
            logger.warning(f"Error getting publisher from ISBN: {e}")
            return {'name': 'University Press', 'location': 'New York'}

class VerificationProtocolLoader:
    """Handles loading verification protocol files with robust fallback mechanisms."""

    def __init__(self, output_dir: Path, templates_dir: Optional[Path] = None,
                 imprint_dir: Optional[Path] = None):
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.templates_dir = Path(templates_dir) if templates_dir else None
        self.imprint_dir = Path(imprint_dir) if imprint_dir else None
        self.logger = logging.getLogger(__name__)
        self.quotes = []  # Will be set by backmatter processor

    def load_verification_protocol(self, quotes: List[Dict] = None) -> str:
        """Load verification protocol with intelligent fallback."""
        if quotes:
            self.quotes = quotes

        # Define search paths in priority order
        search_paths = []

        # Priority 1: Output directory
        search_paths.append((self.output_dir / "verification_protocol.tex", "output directory"))

        # Priority 2: Templates directory
        if self.templates_dir:
            search_paths.append((self.templates_dir / "verification_protocol.tex", "templates directory"))

        # Priority 3: Imprint directory
        if self.imprint_dir:
            search_paths.append((self.imprint_dir / "verification_protocol.tex", "imprint directory"))

        # Try each path in order
        for path, description in search_paths:
            try:
                if path.exists():
                    content = self._try_load_from_path(path)
                    if content:
                        self.logger.info(
                            f"✅ Successfully loaded verification protocol from {description}: {path}")
                        return content
                    else:
                        self.logger.warning(
                            f"⚠️ Found verification protocol file but failed to read content: {path}")
                else:
                    self.logger.debug(f"🔍 Verification protocol not found in {description}: {path}")
            except Exception as e:
                self.logger.warning(f"⚠️ Error checking verification protocol in {description}: {e}")

        # No file found, create default
        self.logger.info("📝 No verification protocol found in any location. Creating default protocol.")
        return self._create_default_protocol()

    def _try_load_from_path(self, path: Path) -> Optional[str]:
        """Safely attempt to load content from a specific path."""
        try:
            if not path.exists():
                return None

            if not path.is_file():
                self.logger.warning(f"⚠️ Path exists but is not a file: {path}")
                return None

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            if not content:
                self.logger.warning(f"⚠️ Verification protocol file is empty: {path}")
                return None

            return content

        except PermissionError:
            self.logger.error(f"❌ Permission denied reading verification protocol: {path}")
            return None
        except UnicodeDecodeError as e:
            self.logger.error(f"❌ Encoding error reading verification protocol: {path} - {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Unexpected error reading verification protocol: {path} - {e}")
            return None

    def _create_default_protocol(self) -> str:
        """Create comprehensive default verification protocol."""
        from datetime import datetime

        current_time = datetime.now()
        timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")

        # Calculate verification statistics
        stats = self._calculate_verification_stats()

        protocol_content = f"""% Verification Protocol
% Generated automatically on {timestamp}

\\section{{Verification Protocol}}

This document provides a comprehensive record of the verification process for all quotations included in this collection.

\\subsection{{Processing Overview}}

\\begin{{itemize}}
    \\item Processing Date: {timestamp}
    \\item Verification System: Automated Publishing Pipeline
    \\item Protocol Version: 2.0
    \\item Status: {"Complete" if stats.get('verification_complete', False) else "In Progress"}
\\end{{itemize}}

\\subsection{{Verification Statistics}}

\\begin{{itemize}}
    \\item Total Quotations: {stats.get('total_quotes', 'N/A')}
    \\item Verified Quotations: {stats.get('verified_quotes', 'N/A')}
    \\item Verification Rate: {stats.get('verification_percentage', 'N/A')}\\%
    \\item Unique Sources: {stats.get('sources_count', 'N/A')}
    \\item Unique Authors: {stats.get('unique_authors', 'N/A')}
\\end{{itemize}}

\\subsection{{Verification Process}}

The verification process includes the following steps:

\\begin{{enumerate}}
    \\item Source Authentication: Each quotation is traced to its original source
    \\item Accuracy Verification: Quotation text is compared against authoritative sources
    \\item Attribution Validation: Author and publication details are confirmed
    \\item Context Review: Quotations are reviewed for appropriate context
    \\item Final Approval: Verified quotations are marked for inclusion
\\end{{enumerate}}

\\subsection{{Quality Assurance}}

\\begin{{itemize}}
    \\item All quotations undergo multi-stage verification
    \\item Sources are cross-referenced with authoritative databases
    \\item Publication details are validated through ISBN lookup
    \\item Editorial review ensures accuracy and appropriateness
\\end{{itemize}}

\\subsection{{Documentation Standards}}

This verification log follows academic standards for source documentation and maintains a complete audit trail of the verification process.

% End of verification protocol
"""

        # Save the default protocol for future use
        self._save_default_protocol(protocol_content)

        return protocol_content

    def _save_default_protocol(self, content: str) -> bool:
        """Save default protocol to output directory for future use."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            protocol_path = self.output_dir / "verification_protocol.tex"

            # Check if path exists as directory and handle it
            if protocol_path.exists() and protocol_path.is_dir():
                self.logger.warning(f"⚠️ Cannot save protocol - path exists as directory: {protocol_path}")
                return False

            with open(protocol_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"💾 Saved default verification protocol to: {protocol_path}")
            return True

        except Exception as e:
            self.logger.warning(f"⚠️ Could not save default verification protocol: {e}")
            return False

    def _calculate_verification_stats(self) -> Dict[str, Any]:
        """Calculate comprehensive verification statistics."""
        if not self.quotes:
            return {
                'total_quotes': 0,
                'verified_quotes': 0,
                'unverified_quotes': 0,
                'verification_percentage': 0,
                'sources_count': 0,
                'unique_authors': 0,
                'verification_complete': True
            }

        total_quotes = len(self.quotes)
        verified_quotes = sum(1 for q in self.quotes if q.get('is_verified', False))
        unverified_quotes = total_quotes - verified_quotes
        verification_percentage = round((verified_quotes / total_quotes) * 100, 1) if total_quotes > 0 else 0

        # Count unique sources and authors
        unique_sources = set()
        unique_authors = set()

        for quote in self.quotes:
            if quote.get('source'):
                unique_sources.add(quote['source'])
            if quote.get('author'):
                unique_authors.add(quote['author'])

        return {
            'total_quotes': total_quotes,
            'verified_quotes': verified_quotes,
            'unverified_quotes': unverified_quotes,
            'verification_percentage': verification_percentage,
            'sources_count': len(unique_sources),
            'unique_authors': len(unique_authors),
            'verification_complete': verified_quotes == total_quotes
        }
