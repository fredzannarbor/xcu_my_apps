# /Users/fred/xcu_my_apps/nimble/codexes-factory/src/codexes/modules/prepress/tex_utils.py
# version 1.2.0
import logging
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def escape_latex(text: str) -> str:
    """
    Escapes special LaTeX characters in a string for safe typesetting.
    The order of replacements is crucial, especially for the backslash.
    """
    if not isinstance(text, str):
        text = str(text)

    # The backslash must be replaced first, otherwise all other replacements will be broken.
    text = text.replace('\\', r'\textbackslash{}')

    # All other special characters
    text = text.replace('&', r'\&')
    text = text.replace('%', r'\%')
    text = text.replace('$', r'\$')
    text = text.replace('#', r'\#')
    text = text.replace('_', r'\_')
    text = text.replace('{', r'\{')
    text = text.replace('}', r'\}')
    text = text.replace('~', r'\textasciitilde{}')
    text = text.replace('^', r'\textasciicircum{}')

    return text


def _process_inline_markdown(text: str) -> str:
    """
    Process inline markdown formatting: **bold**, *italic*, etc.
    """
    import re

    # Escape LaTeX special characters first, but preserve markdown markers temporarily
    text = escape_latex(text)

    # Un-escape the markdown markers we want to process
    text = text.replace('\\textbackslash{}*', '*')
    text = text.replace('\\textbackslash{}\\_', '_')

    # Convert **bold** to \textbf{}
    text = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', text)

    # Convert *italic* or _italic_ to \textit{}
    text = re.sub(r'\*(.+?)\*', r'\\textit{\1}', text)
    text = re.sub(r'_(.+?)_', r'\\textit{\1}', text)

    return text


def validate_and_fix_markdown(text: str, use_llm: bool = True) -> str:
    """
    Validate and fix markdown formatting issues using LLM-based correction.

    This function detects and fixes common formatting issues in LLM-generated markdown:
    - Headings merged with body text (e.g., "### Heading Text body starts here...")
    - Missing blank lines after headings
    - Inconsistent paragraph spacing

    Args:
        text: Markdown text to validate and fix
        use_llm: If True, use LLM to fix formatting. If False, use regex only.

    Returns:
        Corrected markdown text
    """
    if not text or len(text.strip()) < 10:
        return text

    # Quick check: if markdown looks properly formatted, skip LLM call
    import re
    heading_pattern = re.compile(r'^#{1,6}\s+.+$', re.MULTILINE)
    headings = heading_pattern.findall(text)

    # Check if headings have proper spacing (blank line after them)
    needs_fixing = False
    for heading in headings:
        # Find heading in text and check what follows
        idx = text.find(heading)
        if idx >= 0:
            after_heading = text[idx + len(heading):idx + len(heading) + 3]
            # Should be \n\n (blank line), not just \n or immediate text
            if not after_heading.startswith('\n\n'):
                needs_fixing = True
                break

    if not needs_fixing:
        logger.debug("Markdown appears properly formatted, skipping validation")
        return text

    if not use_llm:
        logger.debug("LLM validation disabled, returning original markdown")
        return text

    # Use LLM to fix formatting
    try:
        from codexes.core.llm_integration import call_llm_simple
    except ImportError:
        try:
            from src.codexes.core.llm_integration import call_llm_simple
        except ImportError:
            logger.warning("Cannot import LLM integration, skipping markdown validation")
            return text

    validation_prompt = f"""Fix the markdown formatting in the text below. Ensure:
1. Each heading (###) is on its own line
2. There is exactly ONE blank line after each heading before body text
3. Paragraphs are separated by blank lines
4. Do NOT change the content, only fix formatting

Return ONLY the corrected markdown text, with no explanations or extra commentary.

TEXT TO FIX:
{text}

CORRECTED MARKDOWN:"""

    try:
        # Use a fast, cheap model for this task
        corrected = call_llm_simple(
            prompt=validation_prompt,
            model="gemini/gemini-2.0-flash-exp",
            max_tokens=len(text) + 500,  # Give some buffer
            temperature=0.1  # Low temperature for consistent formatting
        )

        if corrected and len(corrected.strip()) > len(text) * 0.5:
            logger.info(f"✅ LLM corrected markdown formatting ({len(text)} -> {len(corrected)} chars)")
            return corrected
        else:
            logger.warning("LLM correction produced suspiciously short output, using original")
            return text

    except Exception as e:
        logger.warning(f"Markdown validation failed: {e}. Using original text.")
        return text


def markdown_to_latex(text: str, skip_first_heading_if_matches: str = None, validate_markdown: bool = True) -> str:
    """
    Converts Markdown to LaTeX using Pandoc for high-fidelity conversion.

    Args:
        text: Markdown text to convert
        skip_first_heading_if_matches: If provided, skip the first heading if it matches this text
        validate_markdown: If True, validate and fix markdown formatting before conversion

    Returns:
        LaTeX formatted text
    """
    if not isinstance(text, str):
        text = str(text)

    import re
    import tempfile

    # Validate and fix markdown formatting before conversion
    if validate_markdown:
        text = validate_and_fix_markdown(text, use_llm=True)

    # Handle skip_first_heading_if_matches before conversion
    if skip_first_heading_if_matches:
        lines = text.split('\n')
        first_heading_pattern = re.compile(r'^#\s+(.+)$')
        found_first = False
        filtered_lines = []

        for line in lines:
            match = first_heading_pattern.match(line.strip())
            if match and not found_first:
                heading_text = match.group(1).strip()
                if heading_text.lower() == skip_first_heading_if_matches.strip().lower():
                    found_first = True
                    continue  # Skip this heading
            filtered_lines.append(line)

        text = '\n'.join(filtered_lines)

    # Use Pandoc for conversion with optimized settings for book content
    try:
        # Write markdown to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp:
            tmp.write(text)
            tmp_path = tmp.name

        # Run pandoc with options optimized for book typesetting
        result = subprocess.run(
            [
                'pandoc',
                '--from=markdown',
                '--to=latex',
                '--wrap=preserve',           # Preserve line wrapping
                '--no-highlight',            # Disable syntax highlighting
                tmp_path
            ],
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=True
        )

        # Clean up temp file
        Path(tmp_path).unlink()

        latex_output = result.stdout

        # Post-process to ensure proper spacing after headings
        # Pandoc uses \section{}, \subsection{}, etc. - convert to starred versions
        latex_output = re.sub(r'\\(sub)*section\{', r'\\\1section*{', latex_output)
        latex_output = re.sub(r'\\(sub)*subsection\{', r'\\\1subsection*{', latex_output)

        return latex_output

    except subprocess.CalledProcessError as e:
        logger.error(f"Pandoc conversion failed: {e.stderr}")
        # Fallback to simple escape if pandoc fails
        logger.warning("Falling back to simple LaTeX escaping")
        return escape_latex(text)
    except FileNotFoundError:
        logger.error("Pandoc not found. Please install pandoc: brew install pandoc")
        logger.warning("Falling back to simple LaTeX escaping")
        return escape_latex(text)
    except Exception as e:
        logger.error(f"Unexpected error in markdown_to_latex: {e}")
        logger.warning("Falling back to simple LaTeX escaping")
        return escape_latex(text)


def compile_tex_to_pdf(tex_file: Path, build_dir: Path, compiler: str = "lualatex", page_type: str = "interior") -> Optional[Path]:
    """
    Compiles a .tex file to a .pdf, running it twice for TOC/references.
    Accepts different compilers like 'lualatex' or 'xelatex'.
    Creates a log file in the build directory with compilation output.
    
    Parameters:
        tex_file: Path to the .tex file to compile
        build_dir: Directory where compilation will occur
        compiler: LaTeX compiler to use (default: "lualatex")
        page_type: Type of page being created (e.g., "interior", "cover")
    """
    output_stem = tex_file.stem
    command = [
        compiler,
        "-interaction=nonstopmode",
        f"-jobname={output_stem}",
        tex_file.name,
    ]
    
    # Create a log file in the build directory with page type in the name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = build_dir / f"{page_type}_compile_log_{output_stem}_{timestamp}.log"
    
    with open(log_file_path, 'w', encoding='utf-8') as log_file:
        log_file.write(f"LaTeX Compilation Log for {tex_file.name}\n")
        log_file.write(f"Timestamp: {timestamp}\n")
        log_file.write(f"Compiler: {compiler}\n")
        log_file.write(f"Build Directory: {build_dir}\n")
        log_file.write("-" * 80 + "\n\n")
        
        # Run twice to ensure TOC and page references are correct
        for i in range(2):
            log_file.write(f"=== Pass {i + 1}/2 ===\n")
            log_file.write(f"Command: {' '.join(command)}\n\n")
            
            logger.info(f"Running {compiler} pass {i + 1}/2 for '{output_stem}.pdf'...")
            process = subprocess.run(
                command,
                cwd=build_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            # Write stdout and stderr to the log file
            log_file.write("STDOUT:\n")
            log_file.write(process.stdout)
            log_file.write("\nSTDERR:\n")
            log_file.write(process.stderr)
            log_file.write("\n\n")
            
            if process.returncode != 0:
                # Check if PDF was still generated despite non-zero return code
                pdf_path = build_dir / f"{output_stem}.pdf"
                if pdf_path.exists():
                    warning_msg = f"⚠️ LaTeX compilation completed with warnings on pass {i + 1}, but PDF was generated."
                    logger.warning(warning_msg)
                    log_file.write(f"WARNING: {warning_msg}\n")
                    log_file.write(f"Return code: {process.returncode}\n")
                    # Continue to next pass or completion
                else:
                    error_msg = f"❌ LaTeX compilation failed on pass {i + 1}."
                    logger.error(error_msg)
                    logger.error(f"Log output from {compiler}:\n{process.stdout}")
                    log_file.write(f"ERROR: {error_msg}\n")
                    log_file.write(f"See full log at: {build_dir / f'{output_stem}.log'}\n")
                    return None
            
            log_file.write(f"Pass {i + 1} completed successfully.\n\n")
        
        # Check if the PDF was generated
        pdf_path = build_dir / f"{output_stem}.pdf"
        if pdf_path.exists():
            success_msg = f"✅ Successfully generated PDF: {pdf_path}"
            logger.info(success_msg)
            log_file.write(f"SUCCESS: {success_msg}\n")
            
            # Add PDF metadata to the log
            try:
                import fitz  # PyMuPDF
                with fitz.open(pdf_path) as doc:
                    log_file.write(f"PDF Pages: {len(doc)}\n")
                    log_file.write(f"PDF Size: {pdf_path.stat().st_size} bytes\n")
                    metadata = doc.metadata
                    if metadata:
                        log_file.write("PDF Metadata:\n")
                        for key, value in metadata.items():
                            log_file.write(f"  {key}: {value}\n")
            except Exception as e:
                log_file.write(f"Could not extract PDF metadata: {e}\n")
            
            return pdf_path
        else:
            error_msg = f"❌ PDF file not found at {pdf_path} after successful compilation."
            logger.error(error_msg)
            log_file.write(f"ERROR: {error_msg}\n")
            return None