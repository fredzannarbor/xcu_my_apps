# /Users/fred/xcu_my_apps/nimble/codexes-factory/src/codexes/modules/prepress/pilsa_prepress.py
# version 1.3.3
import logging
import json
import re
import shutil
import uuid
import textwrap
from datetime import datetime

from pathlib import Path
from typing import Dict, Optional, Any  # Add Any here


from typing import Dict, Optional, Any

import fitz  # PyMuPDF

# These are assumed to be existing helper modules within your project structure
from codexes.modules.prepress.tex_utils import compile_tex_to_pdf, escape_latex, markdown_to_latex
from codexes.modules.covers.cover_generator import create_cover_latex
from codexes.modules.prepress.partsofthebook_processor import PartsOfTheBookProcessor
from codexes.modules.distribution.quote_processor import QuoteProcessor
#from codexes.modules.prepress.markdown_utils import markdown_to_latex

logger = logging.getLogger(__name__)

def flatten_nested_quotes(text):
    # Convert any quotation marks within quotes to simple quotes
    text = text.replace('"', "'")  # Convert double quotes to single
    text = text.replace('"', "'")  # Convert smart quotes
    text = text.replace('"', "'")
    return text

def fix_pilsa_formatting(text):
    """Fix pilsa formatting to ensure it's always properly italicized."""
    if not text:
        return text
    
    # Fix various broken LaTeX formatting patterns for pilsa
    # Handle the most common pattern: \textbackslash{}textit{\textit{pilsa}}
    text = re.sub(r'\\textbackslash\{\}textit\{\\textit\{pilsa\}\}', r'\\textit{pilsa}', text)
    
    # Handle other escaped patterns
    text = re.sub(r'\\textbackslash\{\}textit\\?\{\\textit\{pilsa\}\\?\}', r'\\textit{pilsa}', text)
    text = re.sub(r'\\textbackslash\{\}textit\\?\{pilsa\\?\}', r'\\textit{pilsa}', text)
    text = re.sub(r'\\textbackslash\\{\\}', r'\\', text)
    # Fix nested textit patterns
    text = re.sub(r'\\textit\{\\textit\{pilsa\}\}', r'\\textit{pilsa}', text)
    
    # Fix the specific pattern we're seeing: any whitespace + extit{\textit{pilsa}}
    text = re.sub(r'\s*extit\{\\textit\{pilsa\}\}', r'\\textit{pilsa}', text)
    
    # Fix the tab + extit pattern we're actually seeing
    text = re.sub(r'(\s)\textit\{\\textit\{pilsa\}\}', r'\1\\textit{pilsa}', text)
    
    # Fix simple extit patterns
    text = re.sub(r'extit\{pilsa\}', r'\\textit{pilsa}', text)
    
    # Clean up any leftover \t characters that might be artifacts
    text = re.sub(r'\\t\\textit\{pilsa\}', r'\\textit{pilsa}', text)
    
    # Ensure standalone "pilsa" is italicized (but not if already properly formatted)
    text = re.sub(r'(?<!\\textit\{)pilsa(?!\})', r'\\textit{pilsa}', text)
    
    return text

def fix_korean_formatting(text):
    """Fix Korean text formatting to use proper \\korean{} command."""
    if not text:
        return text
    
    # Fix broken Korean LaTeX commands - specifically the \{korean pattern
    text = re.sub(r'\\?\{korean\{([^}]+)\}', r'\\korean{\1}', text)
    
    return text

def fix_latex_commands(text):
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

def escape_latex_preserve_commands(text):
    """
    Escape LaTeX special characters while preserving common LaTeX commands.
    This function protects \\textit{}, \\korean{}, and other common commands
    from being escaped.
    """
    if not text:
        return text
    
    # First, temporarily replace LaTeX commands with placeholders
    import uuid
    placeholders = {}
    
    # Common LaTeX commands to preserve
    latex_commands = [
        r'\\textit\{[^}]+\}',
        r'\\korean\{[^}]+\}',
        r'\\textbf\{[^}]+\}',
        r'\\emph\{[^}]+\}',
        r'\\textsc\{[^}]+\}',
    ]
    
    for pattern in latex_commands:
        matches = re.findall(pattern, text)
        for match in matches:
            placeholder = f"LATEX_PLACEHOLDER_{uuid.uuid4().hex}"
            placeholders[placeholder] = match
            text = text.replace(match, placeholder)
    
    # Now escape the remaining text
    text = escape_latex(text)
    
    # Restore the LaTeX commands
    for placeholder, original in placeholders.items():
        text = text.replace(placeholder, original)
    
    return text

def generate_logo_font_definition(logo_font_config):
    """Generate LaTeX font definition based on imprint configuration."""
    if not logo_font_config:
        # Default fallback - Use Zapfino as the primary logo font
        return """% Default logo font - Zapfino
\\newfontfamily\\logofont{Zapfino}"""

    if isinstance(logo_font_config, str):
        # Use system font family name approach
        return f"""% Logo font from system: {logo_font_config}
\\newfontfamily\\logofont{{{logo_font_config}}}"""
    
    family_name = logo_font_config.get('family_name', '')
    file_path = logo_font_config.get('file_path', '')
    fallback_family = logo_font_config.get('fallback_family', 'Zapfino')
    
    if file_path:
        # Use file path approach
        font_filename = Path(file_path).name
        return f"""% Logo font from file: {font_filename}
\\newfontfamily\\logofont{{{font_filename}}}"""
    elif family_name:
        # Use system font family name approach
        return f"""% Logo font from system: {family_name}
\\newfontfamily\\logofont{{{family_name}}}"""
    else:
        # No configuration, use Zapfino as default (consistent with top-level default)
        return """% Default logo font - Zapfino
\\newfontfamily\\logofont{Zapfino}"""

def extract_individual_mnemonics(mnemonics_tex):
    """
    Extract individual mnemonic entries from LaTeX content.
    Assumes each mnemonic starts with \textbf at line beginning.
    
    Important: This function preserves the raw LaTeX commands in the extracted mnemonics,
    as they are intended to be interpreted as LaTeX, not escaped as text.
    """
    if not mnemonics_tex or not isinstance(mnemonics_tex, str):
        logger.warning("No mnemonics content provided or content is not a string")
        return []
    
    try:
        # Split on line-beginning \textbf commands
        pattern = r'^\\textbf'
        parts = re.split(pattern, mnemonics_tex, flags=re.MULTILINE)
        
        mnemonics = []
        for i, part in enumerate(parts[1:], 1):  # Skip first empty part
            if part.strip():  # Only process non-empty parts
                # Reconstruct the mnemonic with its \textbf command
                # Do NOT escape the LaTeX commands here - they should be preserved as-is
                mnemonic_content = f"\\textbf{part.strip()}"
                mnemonics.append(mnemonic_content)
                logger.debug(f"Extracted mnemonic {i}: {mnemonic_content[:50]}...")
        
        logger.info(f"Successfully extracted {len(mnemonics)} mnemonics from LaTeX content")
        return mnemonics
        
    except Exception as e:
        logger.error(f"Error extracting mnemonics from LaTeX content: {e}")
        # Return empty list to allow processing to continue
        return []


def _create_content_tex_files(data: Dict[str, Any], build_dir: Path, templates_dir: Path, config: Dict[str, Any] = None):
    """
    Generates all necessary .tex files inside a specific build directory using the templates found in the specified imprint directory.    """
    logger.info("Generating .tex content files...")
    
    # Extract LLM configuration for use in content generation
    llm_config = config.get('llm_config', {}) if config else {}

    # --- Define Custom Commands ---
    # This new command is more robust. It uses a `makebox` for the image
    # and an overlaid `parbox` for the text. This correctly centers everything
    # and ensures LaTeX always sees the page as having content.

    # Replace the existing full_page_grid_command_def with this simplified version:
    full_page_grid_command_def = r"""
    \providecommand{\fullpagedotgrid}[1]{%
        \newpage
        \vfill
        \begin{center}
            \includegraphics[height=0.85\textheight,keepaspectratio]{dotgrid.png}%
        \end{center}
        \vfill
    }
    """

    # Add the transcription note system here:
    transcription_note_system = r"""
    % Counter for tracking transcription note cycle
    \newcounter{transcriptioncycle}
    \setcounter{transcriptioncycle}{0}

    % Array of transcription notes
    \newcommand{\gettranscriptionnote}[1]{%
        \ifcase#1\relax
            Consider the meaning of the words as you write.\or
            Breathe deeply before you begin the next line.\or
            Notice the rhythm and flow of the sentence.\or
            Focus on the shape of each letter.\or
            Reflect on one new idea this passage sparked.\or
            Consider the meaning of the words as you write.% Cycle back
        \fi
    }

    % System to add transcription notes to every 8th recto page
    \AddToShipoutPictureFG*{%
        \ifinmainmatter
            \checkoddpage
            \ifoddpage
                \stepcounter{mainmatterrecto}%
                \ifnum\value{mainmatterrecto}=8\relax
                    \put(\LenToUnit{0.5\paperwidth}, \LenToUnit{1in + 0.5in}){%
                        \makebox[0pt][c]{%
                            \parbox{\textwidth}{%
                                \centering
                                {\itshape \gettranscriptionnote{\value{transcriptioncycle}}}%
                            }%
                        }%
                    }%
                    \stepcounter{transcriptioncycle}%
                    \ifnum\value{transcriptioncycle}>4\relax
                        \setcounter{transcriptioncycle}{0}%
                    \fi
                    \setcounter{mainmatterrecto}{0}% Reset recto counter
                \fi
            \fi
        \fi
    }
    """

    # --- Title Page (i) ---
    title = escape_latex(data.get('title', 'Untitled'))
    raw_subtitle = data.get('subtitle')

    # Generate the subtitle chunk in Python only if a subtitle exists.
    # This avoids broken \ifx conditionals in LaTeX.
    subtitle_tex_chunk = ""
    if raw_subtitle:
        escaped_subtitle = escape_latex(raw_subtitle)
        subtitle_tex_chunk = f"""
        \\vspace{{1em}}
        {{\\sffamily\\large {escaped_subtitle}\\par}}"""

    author = escape_latex(data.get('author', 'AI Lab for Book-Lovers'))
    imprint = escape_latex(data.get('imprint', 'xynapse traces'))
    pilsa_line1 = "필사"
    pilsa_line2 = "[\\textit{pilsa}] - transcriptive meditation"

    title_page_content = textwrap.dedent(f"""
        \\title{{{title}}} %%% Defines \\thetitle for headers on even pages.
        \\thispagestyle{{empty}}
        \\begin{{center}}
        \\vspace*{{1.5in}}
        {{\\sffamily\\Huge\\bfseries {title}\\par}}{subtitle_tex_chunk}
        \\vfill
        {{\\fontsize{{120}}{{144}}\\selectfont\\sffamily\\bfseries\\korean{{{pilsa_line1}}}\\par}}
        \\vspace{{0.5em}}
        {{\\sffamily\\large {pilsa_line2}\\par}}
        \\vfill
        {{\\sffamily\\Large\\bfseries {author}\\par}}
        \\vfill
        {{\\logofont\\large {imprint}\\par}}
        \\end{{center}}
    """)
    (build_dir / "title_page.tex").write_text(title_page_content, encoding='utf-8')

    # --- Copyright Page (ii) ---
    # Check for assigned ISBN first, then fallback to original
    isbn = data.get('assigned_isbn') or data.get('isbn13')
    if isbn and isbn != "Unknown" and isbn != "TBD":
        isbn_line = f"ISBN: {escape_latex(isbn)}\\\\[2em]"
        logger.info(f"Using ISBN for copyright page: {isbn}")
    else:
        isbn_line = ""
        logger.info("No valid ISBN found for copyright page")
    version = escape_latex(f"v1.0-{datetime.now().strftime('%Y%m%d')}")
    copyright_year = datetime.now().year

    copyright_content = textwrap.dedent(f"""
        \\newpage
        \\thispagestyle{{empty}}
        \\vspace*{{1in}}
        \\begin{{center}}
        \\large
        {imprint} is an imprint of Nimble Books LLC.\\\\
        Ann Arbor, Michigan, USA \\\\
        http://NimbleBooks.com \\\\
        Inquiries: xynapse@nimblebooks.com \\\\[2em]
        Copyright \\copyright {copyright_year} by Nimble Books LLC. All rights reserved.\\\\[2em]
        {isbn_line}
        Version: {version}
        \\end{{center}}
        \\cleardoublepage
    """)
    (build_dir / "copyright_page.tex").write_text(copyright_content, encoding='utf-8')

    # --- Table of Contents (iii, iv) ---
    toc_content = "\\pagestyle{empty}\n\\tableofcontents*\\cleardoublepage\n"
    (build_dir / "table_of_contents.tex").write_text(toc_content, encoding='utf-8')

    # --- Publisher's Note (v, vi) ---
    # 100% LLM generated content, no boilerplate
    raw_note = data.get('storefront_publishers_note_en', '')
    formatted_note = fix_latex_commands(fix_pilsa_formatting(fix_korean_formatting(escape_latex(raw_note.replace('\n', '\n\n')))))

    publisher_note_content = textwrap.dedent(f"""
        \\pagestyle{{empty}}
        \\chapter*{{Publisher's Note}}
        \\addcontentsline{{toc}}{{chapter}}{{Publisher's Note}}
        {formatted_note}
        \\cleardoublepage
    """)
    (build_dir / "publishers_note.tex").write_text(publisher_note_content, encoding='utf-8')

    # --- Foreword ---
    try:
        from codexes.core.enhanced_llm_caller import call_llm_json_with_exponential_backoff
        
        messages = [
            {
                "role": "system",
                "content": "You are a scholarly writer with expertise in Korean cultural practices and mindfulness traditions."
            },
            {
                "role": "user", 
                "content": "Write a scholarly foreword (300-400 words) about pilsa, the Korean tradition of mindful transcription. CRITICAL FORMATTING: Use proper LaTeX commands - write 'pilsa' in plain text (not *pilsa*), use no markdown syntax, no asterisks for emphasis. For Korean terms, write them in Korean characters followed by romanization in parentheses. Cover: origins in Korean scholarly practices, role in Buddhist and Confucian education, decline during modernization, revival in digital age, connection to modern reader experience. Return clean text with no markdown formatting as JSON with key 'foreword'."
            }
        ]
        
        # Use tranche hierarchy: tranche > imprint > default
        model_to_use = 'gemini/gemini-2.5-pro'  # Default for xynapse traces
        if config:
            # Check tranche config first, then imprint, then use default
            model_to_use = config.get('model', config.get('llm_config', {}).get('model', 'gemini/gemini-2.5-pro'))
        logger.info(f"Generating foreword with model: {model_to_use}")
        
        response = call_llm_json_with_exponential_backoff(
            model=model_to_use,
            messages=messages,
            expected_keys=['foreword'],
            temperature=llm_config.get('temperature', 0.7) if llm_config else 0.7,
            max_tokens=llm_config.get('max_tokens', 2000) if llm_config else 2000
        )
        
        if response and 'foreword' in response:
            foreword_text = fix_latex_commands(fix_pilsa_formatting(fix_korean_formatting(escape_latex(response['foreword']))))
            foreword_content = textwrap.dedent(f"""
                \\pagestyle{{empty}}
                \\chapter*{{Foreword}}
                \\addcontentsline{{toc}}{{chapter}}{{Foreword}}
                {foreword_text}
                \\cleardoublepage
            """)
            (build_dir / "foreword.tex").write_text(foreword_content, encoding='utf-8')
            logger.info("Successfully generated foreword")
        else:
            logger.warning("Failed to generate foreword")
    except Exception as e:
        logger.error(f"Error generating foreword: {e}")

    # --- Transcription Note ---
    transcription_note = fix_latex_commands(fix_pilsa_formatting(fix_korean_formatting(escape_latex(data.get('custom_transcription_note',
                                               "The following pages contain curated quotes and passages for your transcription practice. "
                                               "Engage with them slowly, allowing the act of writing to deepen your understanding."
                                               )))))

    transcription_note_content = textwrap.dedent(f"""
        \\pagestyle{{mypagestyle}}
        \\chapter*{{Quotations for Transcription}}
        \\addcontentsline{{toc}}{{chapter}}{{Quotations for Transcription}}
        {transcription_note}
        
        \\clearpage  % Force a page break after the transcription note
    """)
    (build_dir / "transcription_note.tex").write_text(transcription_note_content, encoding='utf-8')

    # --- Quotations and Transcription Pages ---
    quotes_data = data.get('quotes', [])
    quotes_content_parts = [full_page_grid_command_def]  # Add command definition

    transcription_instructions = [
        "Focus on the shape of each letter.",
        "Consider the meaning of the words as you write.",
        "Notice the rhythm and flow of the sentence.",
        "Reflect on one new idea this passage sparked.",
        "Breathe deeply before you begin the next line."
    ]

    for i, quote_data_item in enumerate(quotes_data, 1):
        quote = escape_latex(quote_data_item.get("quote", ""))
        author = escape_latex(quote_data_item.get('author', 'Unknown Author'))
        source = escape_latex(quote_data_item.get('source', 'Unknown Source'))
        date_pub = escape_latex(quote_data_item.get('date_first_published', 'N.D.'))
        editor_note = escape_latex(quote_data_item.get('editor_note', ''))
        citation_text = f"{author}, \\textit{{{source}}} ({date_pub})"

        # CORRECTED LOGIC: Append footnote directly to the quote text
        # This ensures the footnote marker appears at the end of the quote.
        quote_with_footnote = quote
        if editor_note:
            quote_with_footnote += f"\\footnote{{{editor_note} --Ed.}}"

        # Create the verso page with the quote
        # Create the verso page with the quote
        verso_page = textwrap.dedent(f"""
            % --- Quote {i} (Verso) ---
            \\vspace*{{1.25in}} % Approx 2in from top of page (0.75in margin + 1.25in)
            \\begin{{center}}
                {{\\formattedquote{{{quote_with_footnote}}}}}
                \\par\\vspace*{{4ex}} % Robust vertical spacing
                \\hspace*{{0.3in}}\\begin{{minipage}}{{\\textwidth - 0.3in}}
                    \\raggedleft{{\\small {citation_text}}}
                \\end{{minipage}}
            \\end{{center}}
        """)

        quotes_content_parts.append(verso_page)

        # Create the recto page with the dot grid
        recto_page = f"\\fullpagedotgrid{{}}"
        quotes_content_parts.append(recto_page)

    # No need for \cleardoublepage here as it creates extra blank pages
    # The mnemonics section will handle its own page positioning with \cleartoverso

    (build_dir / "quotations.tex").write_text("\n".join(quotes_content_parts), encoding='utf-8')

    # --- End Matter ---
    # Initialize backmatter processor with LLM configuration using tranche hierarchy
    backmatter_llm_config = {'model': 'gemini/gemini-2.5-pro'}  # Default for xynapse traces
    if config:
        # Use tranche hierarchy for LLM configuration
        backmatter_llm_config['model'] = config.get('model', config.get('llm_config', {}).get('model', 'gemini/gemini-2.5-pro'))
        backmatter_llm_config['temperature'] = config.get('llm_config', {}).get('temperature', 0.7)
        backmatter_llm_config['max_tokens'] = config.get('llm_config', {}).get('max_tokens', 2000)
    
    backmatter_processor = PartsOfTheBookProcessor(llm_config=backmatter_llm_config)
    
    # --- Mnemonics ---
    # Use enhanced mnemonics processing
    try:
        mnemonics_content = backmatter_processor.process_mnemonics(data)
        if mnemonics_content and mnemonics_content.strip():
            (build_dir / "mnemonics.tex").write_text(mnemonics_content, encoding='utf-8')
            logger.info("Successfully generated content-specific mnemonics using enhanced processor")
        else:
            logger.warning("No mnemonics content generated - skipping mnemonics.tex creation")
    except Exception as e:
        logger.error(f"Error generating mnemonics: {e}")
        # Fallback to old method
        mnemonics_tex = data.get('mnemonics_tex', '')
        raw_mnemonics = data.get('mnemonics', '')
        
        if mnemonics_tex and isinstance(mnemonics_tex, str):
            # Create mnemonics directory in build folder
            mnemonics_dir = build_dir / "mnemonics"
            mnemonics_dir.mkdir(exist_ok=True)
            
            # Save the LaTeX content directly to a .tex file in the mnemonics directory
            # Important: Do NOT escape the mnemonics_tex content here, as it already contains LaTeX commands
            # that should be preserved and interpreted as LaTeX, not as plain text.
            mnemonics_file_path = mnemonics_dir / "mnemonics_content.tex"
            mnemonics_file_path.write_text(mnemonics_tex, encoding='utf-8')
            logger.info(f"Saved mnemonics LaTeX content to: {mnemonics_file_path}")
        
            # Extract individual mnemonics for alternating layout
            individual_mnemonics = extract_individual_mnemonics(mnemonics_tex)
            mnemonics_count = len(individual_mnemonics)
            
            if mnemonics_count == 0:
                logger.warning("No mnemonics found in LaTeX content - skipping mnemonic section")
                return
                
            logger.info(f"Extracted {mnemonics_count} individual mnemonics for practice layout")
        
            # Create the main mnemonics.tex file with alternating verso/recto layout
            mnemonics_parts = [full_page_grid_command_def]  # Add command definition
            # Start the mnemonics section without extra page breaks
            mnemonics_parts.append("% Mnemonics section")
            mnemonics_parts.append("\\chapter*{Mnemonics}")
            mnemonics_parts.append("\\addcontentsline{toc}{chapter}{Mnemonics}")
        
            # Add scientific introduction to mnemonics
            mnemonic_intro = """
Neuroscience research demonstrates that mnemonic devices significantly enhance long-term memory retention by engaging multiple neural pathways simultaneously.\\footnote{Maguire, Eleanor A., et al. ``Routes to Remembering: The Brains Behind Superior Memory.'' \\textit{Nature Neuroscience} 6, no. 1 (2003): 90-95.} Studies using fMRI imaging show that mnemonics activate both the hippocampus—critical for memory formation—and the prefrontal cortex, which governs executive function. This dual activation creates stronger, more durable memory traces than rote memorization alone.

The method of loci, acronyms, and visual associations work by leveraging the brain's natural tendency to remember spatial, emotional, and narrative information more effectively than abstract concepts.\\footnote{Roediger, Henry L. ``The Effectiveness of Four Mnemonics in Ordering Recall.'' \\textit{Journal of Experimental Psychology: Human Learning and Memory} 6, no. 5 (1980): 558-567.} Research demonstrates that participants using mnemonic techniques showed 40\\% better recall after one week compared to traditional study methods.\\footnote{Bellezza, Francis S. ``Mnemonic Devices: Classification, Characteristics, and Criteria.'' \\textit{Review of Educational Research} 51, no. 2 (1981): 247-275.}

Mastery through mnemonic practice provides profound peace of mind. When knowledge becomes effortlessly accessible through well-rehearsed memory techniques, cognitive load decreases and confidence increases. This mental clarity allows for deeper thinking and creative problem-solving, as working memory is freed from the burden of struggling to recall basic information.

Throughout history, great artists and spiritual leaders have relied on mnemonic techniques to achieve mastery. Dante structured his \\textit{Divine Comedy} using elaborate memory palaces, with each circle of Hell serving as a spatial mnemonic for moral teachings.\\footnote{Yates, Frances A. \\textit{The Art of Memory}. Chicago: University of Chicago Press, 1966, 95-104.} Medieval monks developed intricate visual mnemonics to memorize entire books of scripture—the illuminated manuscripts themselves functioned as memory aids, with symbolic imagery encoding theological concepts.\\footnote{Carruthers, Mary. \\textit{The Book of Memory: A Study of Memory in Medieval Culture}. Cambridge: Cambridge University Press, 1990, 221-257.} Thomas Aquinas advocated for the ``artificial memory'' as essential to spiritual development, arguing that systematic recall of sacred texts freed the mind for contemplation.\\footnote{Aquinas, Thomas. \\textit{Summa Theologica}, II-II, q. 49, a. 1. Trans. by the Fathers of the English Dominican Province. New York: Benziger Brothers, 1947.} In the Renaissance, Giulio Camillo designed his famous ``Theatre of Memory,'' a physical structure where each architectural element triggered recall of classical knowledge.\\footnote{Bolzoni, Lina. \\textit{The Gallery of Memory: Literary and Iconographic Models in the Age of the Printing Press}. Toronto: University of Toronto Press, 2001, 147-171.} Even Bach embedded mnemonic patterns into his compositions—the numerical symbolism in his cantatas served as memory aids for both performers and congregants, ensuring sacred messages would be retained long after the music ended.\\footnote{Chafe, Eric. \\textit{Analyzing Bach Cantatas}. New York: Oxford University Press, 2000, 89-112.}

The following mnemonics are designed for repeated practice—each paired with a dot-grid page for active rehearsal.

\\vspace{1em}
"""
            mnemonics_parts.append(mnemonic_intro)
        
            # Add "My learning goals" dot grid page after introduction
            mnemonics_parts.append("\\fullpagedotgridwithinstruction{My learning goals}")
            
            # Ensure all ampersands in mnemonics are properly escaped
            for i, mnemonic in enumerate(individual_mnemonics):
                individual_mnemonics[i] = mnemonic.replace("&", "\\&")
            
            mnemonics_parts.append(full_page_grid_command_def)  # Add command definition
        
        # Generate alternating mnemonic/practice page pairs
        try:
            for i, mnemonic_content in enumerate(individual_mnemonics, 1):
                # Important: Do NOT escape the mnemonic_content here, as it already contains LaTeX commands
                # that should be preserved. Only escape the instruction text.
                instruction = escape_latex(f"Mnemonic Practice {i}")
                mnemonics_parts.append(f"\\mnemonicwithpractice{{{mnemonic_content}}}{{{instruction}}}")
                logger.debug(f"Generated mnemonic/practice pair {i}")
            
            mnemonics_parts.append("\\cleardoublepage")
            mnemonics_content = "\n".join(mnemonics_parts)
            
            # Validate page sequencing - should have even number of content pages
            expected_pages = mnemonics_count * 2  # Each mnemonic creates 2 pages
            logger.info(f"Generated {mnemonics_count} mnemonic pairs, expecting {expected_pages} content pages")
            
            (build_dir / "mnemonics.tex").write_text(mnemonics_content, encoding='utf-8')
            logger.info(f"Successfully wrote mnemonics.tex with {mnemonics_count} mnemonic/practice pairs")
            
        except Exception as e:
            logger.error(f"Error generating mnemonic layout: {e}")
            # Create fallback minimal content
            fallback_content = "\\chapter*{Mnemonics}\n\\addcontentsline{toc}{chapter}{Mnemonics}\n% Error generating mnemonic content\n"
            (build_dir / "mnemonics.tex").write_text(fallback_content, encoding='utf-8')
            logger.warning("Created fallback mnemonics.tex due to processing error")
        
        # Check if we have raw mnemonics data instead
        if raw_mnemonics and isinstance(raw_mnemonics, str):
            # Fallback to old markdown-based processing for backward compatibility
            # Start the mnemonics section without extra page breaks
            mnemonics_parts = []  # No page break command
            mnemonics_parts.append('\\chapter*{Mnemonics}')
            mnemonics_parts.append('\\addcontentsline{toc}{chapter}{Mnemonics}')
            mnemonics_parts.append(full_page_grid_command_def)  # Add command definition

            lines = raw_mnemonics.strip().split('\n')
            latex_lines = []
            bullet_count = 0
            in_itemize = False

            for line in lines:
                stripped_line = line.strip()
                if stripped_line.startswith(('* ', '- ')):
                    if not in_itemize:
                        latex_lines.append('\\begin{itemize}')
                        in_itemize = True
                    item_text = markdown_to_latex(stripped_line[2:])
                    latex_lines.append(f'  \\item {item_text}')
                    bullet_count += 1
                else:
                    if in_itemize:
                        latex_lines.append('\\end{itemize}')
                        in_itemize = False
                    latex_lines.append(markdown_to_latex(line))

            if in_itemize:
                latex_lines.append('\\end{itemize}')

            mnemonics_parts.append('\n\n'.join(latex_lines))

            # Add dot grid pages after the mnemonics content
            if mnemonics_count > 0:
                logger.info(f"Adding {mnemonics_count} dot grid pages for mnemonics practice.")
                mnemonics_parts.append("\\cleardoublepage")
                for i in range(mnemonics_count):
                    instruction = escape_latex(f"Mnemonic Practice {i + 1}")
                    mnemonics_parts.append(f"\\fullpagedotgrid{{{instruction}}}")

            mnemonics_parts.append("\\cleardoublepage")

            mnemonics_content = "\n".join(mnemonics_parts)
            (build_dir / "mnemonics.tex").write_text(mnemonics_content, encoding='utf-8')

    # --- Enhanced Bibliography ---
    try:
        bibliography_content = backmatter_processor.process_bibliography(data)
        if bibliography_content and bibliography_content.strip():
            # Add QR code placeholder
            qr_code_placeholder = "NimbleBooks.com"
            bibliography_content += f"""
\\vfill
\\begin{{center}}
For more information and to purchase this book, please visit our website:
\\par\\vspace{{1em}}
{qr_code_placeholder}
\\end{{center}}
\\cleardoublepage
"""
            (build_dir / "bibliography.tex").write_text(bibliography_content, encoding='utf-8')
            logger.info("Successfully generated enhanced bibliography with ISBN lookup")
        else:
            logger.warning("No bibliography content generated - skipping bibliography.tex creation")
    except Exception as e:
        logger.error(f"Error generating enhanced bibliography: {e}")
        # Fallback to old method
        raw_bibliography = data.get('bibliography', '')
        if raw_bibliography and isinstance(raw_bibliography, str):
            # Convert simple line breaks to LaTeX line breaks
            escaped_lines = [escape_latex(line) for line in raw_bibliography.strip().split('\n')]
            bibliography = '\\\\\n'.join(escaped_lines)

            qr_code_placeholder = "NimbleBooks.com"
            bibliography_content = textwrap.dedent(f"""
                \\chapter*{{Bibliography}}
                \\addcontentsline{{toc}}{{chapter}}{{Bibliography}}
                {bibliography}
                \\vfill
                \\begin{{center}}
                For more information and to purchase this book, please visit our website:
                \\par\\vspace{{1em}}
                {qr_code_placeholder}
                \\end{{center}}
                \\cleardoublepage
            """)
            (build_dir / "bibliography.tex").write_text(bibliography_content, encoding='utf-8')
    
    # --- Verification Log ---
    try:
        verification_log_content = backmatter_processor.process_verification_log(data)
        if verification_log_content and verification_log_content.strip():
            (build_dir / "verification_log.tex").write_text(verification_log_content, encoding='utf-8')
            logger.info("Successfully generated verification log")
        else:
            logger.warning("No verification log content generated - skipping verification_log.tex creation")
    except Exception as e:
        logger.error(f"Error generating verification log: {e}")
    
    # --- Pilsa Glossary ---
    try:
        glossary_content = backmatter_processor.process_glossary()
        if glossary_content:
            (build_dir / "glossary.tex").write_text(glossary_content, encoding='utf-8')
            logger.info("Successfully generated pilsa glossary")
    except Exception as e:
        logger.error(f"Error generating glossary: {e}")

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
    Orchestrates the full prepress process for a single book.
    In catalog-only mode, it uses an assumed page count for cover generation.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Could not read or parse JSON file at {json_path}: {e}")
        return None

    # FIX: Ensure a shortuuid exists, creating one if it's missing.
    if not data.get('shortuuid'):
        new_id = uuid.uuid4().hex[:12]
        data['shortuuid'] = new_id
        logger.warning(f"JSON file {json_path.name} was missing a 'shortuuid'. "
                       f"Generated a new one: {new_id}")

    assumed_page_count = data.get('page_count', 0) if catalog_only else 0
    safe_basename = json_path.stem
    build_dir_parent = final_output_dir.parent / ".build"
    build_dir_parent.mkdir(exist_ok=True)
    temp_build_dir = build_dir_parent / f"{safe_basename}_{uuid.uuid4().hex[:8]}"
    temp_build_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created temporary build directory: {temp_build_dir}")

    try:
        # --- Interior Generation ---
        logger.info("--- Starting Interior Generation ---")
        # Load imprint configuration to get logo font
        raw_imprint = data.get('imprint', 'xynapse_traces')
        
        # Map imprint names to configuration files
        imprint_mapping = {
            'xynapse traces': 'xynapse_traces',
            'xynapse_traces': 'xynapse_traces',
            'earthscan from routledge': 'xynapse_traces',  # Fallback for LLM-generated names
            'routledge': 'xynapse_traces',  # Fallback for LLM-generated names
        }
        
        imprint_name = imprint_mapping.get(raw_imprint.lower(), raw_imprint.lower().replace(' ', '_'))
        imprint_config_path = Path(f"configs/imprints/{imprint_name}.json")
        logger.info(f"Mapped imprint '{raw_imprint}' to config file: {imprint_config_path}")
        
        try:
            if imprint_config_path.exists():
                with open(imprint_config_path, 'r', encoding='utf-8') as f:
                    imprint_config = json.load(f)
                    # Get logo font from imprint configuration
                    logo_font_config = imprint_config.get('branding', {}).get('logo_font', {})
                    logger.info(f"Loaded logo font config from imprint configuration: {logo_font_config}")
            else:
                logger.warning(f"Imprint configuration not found at {imprint_config_path}")
                logo_font_config = {}
        except Exception as e:
            logger.error(f"Error loading imprint configuration: {e}")
            logo_font_config = {}
        
        # Generate logo font definition based on imprint configuration
        logo_font_definition = generate_logo_font_definition(logo_font_config)
        logger.info(f"Generated logo font definition: {logo_font_definition}")
        
        # Copy and customize template with font configuration
        template_path = templates_dir / 'template.tex'
        template_content = template_path.read_text(encoding='utf-8')
        
        # Apply font configuration from config
        if config:
            fonts_config = config.get('fonts', {})
            font_substitutions = {
                'korean_font': fonts_config.get('korean', 'Apple Myungjo'),
                'body_font': fonts_config.get('body', 'Adobe Caslon Pro'),
                'heading_font': fonts_config.get('heading', 'Adobe Caslon Pro'),
                'quotations_font': fonts_config.get('quotations', 'Adobe Caslon Pro'),
                'mnemonics_font': fonts_config.get('mnemonics', 'Adobe Caslon Pro')
            }
            
            # Apply font substitutions
            for font_var, font_name in font_substitutions.items():
                template_content = template_content.replace(f'{{{font_var}}}', font_name)
                
            logger.info(f"Applied font configuration: {font_substitutions}")
        else:
            # Apply default fonts if no config provided
            default_fonts = {
                'korean_font': 'Apple Myungjo',
                'body_font': 'Adobe Caslon Pro',
                'heading_font': 'Adobe Caslon Pro',
                'quotations_font': 'Adobe Caslon Pro',
                'mnemonics_font': 'Adobe Caslon Pro'
            }
            
            for font_var, font_name in default_fonts.items():
                template_content = template_content.replace(f'{{{font_var}}}', font_name)
                
            logger.info("Applied default font configuration")
        
        # Check if the template has a placeholder or a hardcoded font definition
        if '{LOGO_FONT_DEFINITION}' in template_content:
            # Replace placeholder with actual font definition
            template_content = template_content.replace('{LOGO_FONT_DEFINITION}', logo_font_definition)
            logger.info("Replaced logo font definition placeholder in template")
        else:
            # Instead of using regex, we'll use string manipulation to replace the font definition
            # Split the template into lines
            lines = template_content.split('\n')
            
            # Check if the logo font definition section exists
            logo_font_section_exists = False
            for i, line in enumerate(lines):
                if '% --- Logo Font Definition ---' in line:
                    logo_font_section_exists = True
                    # Found the section header, now look for the font definition line
                    for j in range(i+1, min(i+10, len(lines))):  # Look at the next few lines
                        if r'\newfontfamily\logofont' in lines[j]:
                            # Found the font definition line, replace it
                            lines[j] = logo_font_definition.split('\n')[-1]  # Get the last line of the font definition
                            logger.info(f"Replaced hardcoded logo font definition in template: {lines[j]}")
                            break
                    break
            
            # If the logo font section doesn't exist, add it after the font setup section
            if not logo_font_section_exists:
                for i, line in enumerate(lines):
                    if '% --- Font Setup ---' in line:
                        # Find the end of the font setup section
                        for j in range(i+1, min(i+20, len(lines))):
                            if lines[j].strip() and lines[j].startswith('%') and '---' in lines[j]:
                                # Found the next section, insert before it
                                lines.insert(j, '')
                                lines.insert(j, logo_font_definition)
                                lines.insert(j, '% --- Logo Font Definition ---')
                                logger.info(f"Added logo font definition section to template")
                                break
                        break
            
            # Check if \logofont is already defined in the template
            logofont_already_defined = False
            for line in lines:
                if '\\newfontfamily\\logofont' in line:
                    logofont_already_defined = True
                    logger.info(f"Found existing logofont definition: {line.strip()}")
                    break
            
            # Make sure the logo font definition is added if it doesn't exist
            if not logo_font_section_exists and not logofont_already_defined:
                # Add the logo font definition right after the font setup section
                font_setup_index = -1
                for i, line in enumerate(lines):
                    if '% --- Font Setup ---' in line:
                        font_setup_index = i
                        break
                
                if font_setup_index >= 0:
                    # Find where the font setup section ends
                    for j in range(font_setup_index + 1, len(lines)):
                        if lines[j].strip() and lines[j].startswith('%') and '---' in lines[j]:
                            # Insert the logo font definition before the next section
                            lines.insert(j, '')
                            lines.insert(j, '\\newfontfamily\\logofont{Berkshire Swash}')
                            lines.insert(j, '% --- Logo Font Definition ---')
                            logger.info(f"Added logo font definition section to template at line {j}")
                            break
                        elif j == len(lines) - 1:
                            # If we reached the end, add it after the last font setup line
                            lines.insert(font_setup_index + 4, '')
                            lines.insert(font_setup_index + 4, '\\newfontfamily\\logofont{Berkshire Swash}')
                            lines.insert(font_setup_index + 4, '% --- Logo Font Definition ---')
                            logger.info(f"Added logo font definition section to template at end of font setup")
                            break
            
            # Now update the header definition to use \logofont
            for i, line in enumerate(lines):
                # Look for the odd header definition
                if r'\makeoddhead{mypagestyle}' in line:
                    # Check if it's using the old format
                    if r'\large\scshape\sffamily\headerstrut' in line:
                        # Replace with the new format using \logofont
                        lines[i] = r'\makeoddhead{mypagestyle}{}{}{\logofont\small\headerstrut xynapse traces}'
                        logger.info(f"Updated header to use logofont: {lines[i]}")
                    break
                
                # Also look for the imprint header command
                elif r'\newcommand{\imprintheader}' in line:
                    # Make sure it's using \logofont
                    if not r'\logofont' in line:
                        lines[i] = r'\newcommand{\imprintheader}{\logofont\small\headerstrut xynapse traces}'
                        logger.info(f"Updated imprint header command to use logofont: {lines[i]}")
                    break
            
            # Rejoin the lines
            template_content = '\n'.join(lines)
        
        # Write customized template to build directory
        (temp_build_dir / 'template.tex').write_text(template_content, encoding='utf-8')
        template_image = templates_dir / 'dotgrid.png'
        shutil.copy(template_image, temp_build_dir / 'dotgrid.png')
        
        if logo_font_config and 'file_path' in logo_font_config:
            #logger.info(f"Found logo font configuration: {logo_font_config}")
            font_file_path = logo_font_config['file_path']
            font_filename = Path(font_file_path).name
            
            # First check if the font exists at the specified path
            font_path = Path(font_file_path)
            if font_path.exists() and font_path.is_file():
                # Copy the font to the build directory
                shutil.copy(font_path, temp_build_dir / font_filename)
                logger.info(f"Copied logo font from specified path: {font_file_path}")
            else:
                # Try to find the font in the templates directory
                template_font = templates_dir / font_filename
                if template_font.exists() and template_font.is_file():
                    shutil.copy(template_font, temp_build_dir / font_filename)
                    logger.info(f"Copied logo font: {font_filename}")
                else:
                    logger.warning(f"Logo font file not found: {template_font}")
        else:
            logger.info("No logo font configuration found, using system fonts")

        _create_content_tex_files(data, temp_build_dir, templates_dir, config)

        main_tex_file = temp_build_dir / "template.tex"
        interim_pdf_path = compile_tex_to_pdf(main_tex_file, temp_build_dir, compiler="lualatex")
        if not interim_pdf_path:
            raise RuntimeError("Interior PDF compilation failed.")

        # --- Page Count Determination ---
        with fitz.open(interim_pdf_path) as doc:
            actual_page_count = len(doc)

        if catalog_only:
            final_page_count = assumed_page_count
            logger.info(f"Catalog-only mode: Using assumed page count ({final_page_count}) for cover generation.")
        else:
            final_page_count = actual_page_count
            logger.info(f"Using actual page count ({final_page_count}) for cover generation.")

        data['page_count'] = final_page_count

        # --- Cover Generation ---
        logger.info("--- Starting Cover Generation ---")
        cover_template_path = templates_dir / 'cover_template.tex'
        cover_replacements = None
        cover_results = create_cover_latex(
            json_path=json_path,
            output_dir=final_output_dir / "covers",
            template_path=cover_template_path,
            build_dir=temp_build_dir,
            replacements=cover_replacements,
            debug_mode=debug_cover
        )

        # --- Update JSON with Cover Paths ---
        if not cover_results:
            logger.warning("Cover generation failed, proceeding without cover files.")
            data['front_cover_image_path'] = ''
            data['full_spread_pdf_path'] = ''
        else:
            # Convert Path objects to strings to prevent JSON serialization errors.
            front_cover_path = cover_results.get('front_cover_png')
            full_spread_path = cover_results.get('full_spread_pdf')
            data['front_cover_image_path'] = str(front_cover_path) if front_cover_path else ''
            data['full_spread_pdf_path'] = str(full_spread_path) if full_spread_path else ''

        # Save all updates (page count and cover paths) back to the JSON file.
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Updated JSON file at {json_path} with final page count and cover paths.")

        # --- Finalize Artifacts ---
        interior_dir = final_output_dir / "interior"
        interior_dir.mkdir(parents=True, exist_ok=True)
        final_interior_path = interior_dir / f"{safe_basename}_interior.pdf"
        shutil.move(interim_pdf_path, final_interior_path)
        logger.info(f"✅ Final interior PDF saved to: {final_interior_path}")

        return {
            "pdf_path": str(final_interior_path),
            "page_count": final_page_count,
            "cover_paths": cover_results or {}
        }

    except Exception as e:
        logger.error(f"❌ An error occurred during prepress for {safe_basename}: {e}", exc_info=True)
        return None
    finally:
        if temp_build_dir.exists():
            if not leave_build_directories_in_place:
                shutil.rmtree(temp_build_dir)
                logger.info(f"Cleaned up temporary directory: {temp_build_dir}")
            else:
                logger.info(f"Build directory left in place as requested: {temp_build_dir}")
