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


def markdown_to_latex(text: str, skip_first_heading_if_matches: str = None) -> str:
    """
    Converts Markdown to LaTeX, handling common markdown syntax.
    Processes in order: headings, bold, italic, blockquotes, lists, paragraphs.

    Args:
        text: Markdown text to convert
        skip_first_heading_if_matches: If provided, skip the first heading if it matches this text
    """
    if not isinstance(text, str):
        text = str(text)

    import re

    lines = text.split('\n')
    result_lines = []
    in_blockquote = False
    in_list = False
    first_heading_seen = False
    consecutive_empty_lines = 0

    for line in lines:
        stripped = line.strip()

        # Handle empty lines with limiting
        if not stripped:
            if in_blockquote:
                result_lines.append('\\end{quotation}')
                in_blockquote = False
                consecutive_empty_lines = 0
            elif in_list:
                result_lines.append('\\end{itemize}')
                in_list = False
                consecutive_empty_lines = 0
            else:
                # Limit consecutive empty lines to 1
                if consecutive_empty_lines < 1:
                    result_lines.append('')
                    consecutive_empty_lines += 1
            continue
        else:
            consecutive_empty_lines = 0

        # Handle markdown headings (# Header)
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if heading_match:
            # Skip first heading if it matches the provided title
            if not first_heading_seen and skip_first_heading_if_matches:
                heading_text_raw = heading_match.group(2)
                if heading_text_raw.strip().lower() == skip_first_heading_if_matches.strip().lower():
                    first_heading_seen = True
                    continue

            first_heading_seen = True

            if in_blockquote:
                result_lines.append('\\end{quotation}')
                in_blockquote = False
            if in_list:
                result_lines.append('\\end{itemize}')
                in_list = False
            level = len(heading_match.group(1))
            heading_text = escape_latex(heading_match.group(2))
            # Convert to subsection for level 2+
            if level == 1:
                result_lines.append(f'\\section*{{{heading_text}}}')
            elif level == 2:
                result_lines.append(f'\\subsection*{{{heading_text}}}')
            else:
                result_lines.append(f'\\subsubsection*{{{heading_text}}}')
            continue

        # Handle blockquotes (> text)
        if stripped.startswith('> '):
            if not in_blockquote:
                if in_list:
                    result_lines.append('\\end{itemize}')
                    in_list = False
                result_lines.append('\\begin{quotation}')
                in_blockquote = True
            quote_text = stripped[2:]
            # Process inline formatting in quote
            quote_text = _process_inline_markdown(quote_text)
            result_lines.append(quote_text)
            continue
        else:
            if in_blockquote:
                result_lines.append('\\end{quotation}')
                in_blockquote = False

        # Handle unordered lists (- item or * item)
        if re.match(r'^[-*]\s+', stripped):
            if not in_list:
                result_lines.append('\\begin{itemize}')
                in_list = True
            item_text = re.sub(r'^[-*]\s+', '', stripped)
            item_text = _process_inline_markdown(item_text)
            result_lines.append(f'    \\item {item_text}')
            continue
        else:
            if in_list:
                result_lines.append('\\end{itemize}')
                in_list = False

        # Regular paragraph text
        processed_line = _process_inline_markdown(stripped)
        result_lines.append(processed_line + '\\\\ ')

    # Close any open environments
    if in_blockquote:
        result_lines.append('\\end{quotation}')
    if in_list:
        result_lines.append('\\end{itemize}')

    return '\n'.join(result_lines)


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