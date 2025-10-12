# /Users/fred/xcu_my_apps/nimble/codexes-factory/src/codexes/modules/covers/cover_generator.py
# version 1.3.2
import logging
import json
import random
import re
import shutil
import subprocess
import io
from pathlib import Path
from typing import Optional, Dict, Any

# We will use fitz (PyMuPDF) to convert the final PDF to a PNG
import fitz

# Import the barcode library
from src.codexes.modules.covers.treepoem_barcode_generator import BooklandBarcodeGenerator

logger = logging.getLogger(__name__)

# FIX: Re-introduce the traditional Korean color palette.
# These are CMYK values suitable for print, inspired by traditional Korean art and nature.
KOREAN_COLOR_PALETTE = [
    {'name': 'Mungyeong Cheongja (Celadon Green)', 'c': 0.35, 'm': 0.10, 'y': 0.30, 'k': 0.05},
    {'name': 'Andong Hwangto (Ocher)', 'c': 0.10, 'm': 0.45, 'y': 0.80, 'k': 0.05},
    {'name': 'Goryeo Dancheong (Red Ochre)', 'c': 0.15, 'm': 0.80, 'y': 0.70, 'k': 0.10},
    {'name': 'Naju Jjok (Indigo Blue)', 'c': 0.85, 'm': 0.60, 'y': 0.20, 'k': 0.20},
    {'name': 'Seoul Doldam (Stone Gray)', 'c': 0.20, 'm': 0.15, 'y': 0.25, 'k': 0.45},
    {'name': 'Jeonju Hanji (Paper Beige)', 'c': 0.05, 'm': 0.10, 'y': 0.25, 'k': 0.02},
    {'name': 'Boseong Nokcha (Green Tea)', 'c': 0.40, 'm': 0.20, 'y': 0.80, 'k': 0.10},
]


def substitute_template_variables(text: str, data: Dict[str, Any]) -> str:
    """
    Substitutes template variables like {stream}, {title}, etc. with actual book data.
    
    Args:
        text: Text containing template variables
        data: Book metadata dictionary
        
    Returns:
        Text with all variables substituted
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Define variable mappings with fallback values
    variable_mappings = {
        'stream': data.get('subject', data.get('title', 'this topic')),
        'title': data.get('title', 'Untitled'),
        'description': data.get('description', data.get('storefront_publishers_note_en', 'this important topic')),
        'quotes_per_book': str(data.get('quotes_per_book', '90')),
        'author': data.get('author', 'AI Lab for Book-Lovers'),
        'imprint': data.get('imprint', 'xynapse traces')
    }
    
    # Substitute each variable
    for variable, value in variable_mappings.items():
        if value:  # Only substitute if we have a value
            text = text.replace(f'{{{variable}}}', str(value))
    
    return text


def _escape_latex_preserve_korean(text: Any) -> str:
    """
    Safely escapes special LaTeX characters while preserving korean{} commands.
    
    Args:
        text: Text to escape
        
    Returns:
        LaTeX-safe text with Korean commands preserved
    """
    if not isinstance(text, str):
        text = str(text)
    
    # First, find and temporarily replace \korean{} commands with placeholders
    import uuid
    korean_commands = {}
    korean_pattern = r'\\korean\{[^}]+\}'
    
    matches = re.findall(korean_pattern, text)
    for match in matches:
        # Use a placeholder that won't be affected by LaTeX escaping
        placeholder = f"KOREANPLACEHOLDER{uuid.uuid4().hex.replace('-', '')}KOREANPLACEHOLDER"
        korean_commands[placeholder] = match
        text = text.replace(match, placeholder)
    
    # Now escape the text normally
    text = _escape_latex(text)
    
    # Restore the Korean commands (placeholders won't have been escaped)
    for placeholder, original in korean_commands.items():
        text = text.replace(placeholder, original)
    
    return text


def _escape_latex(text: Any) -> str:
    """Safely escapes special LaTeX characters in a string."""
    if not isinstance(text, str):
        text = str(text)
    # A comprehensive mapping for LaTeX special characters.
    mapping = {
        '&': r'\&', '%': r'\%', '\n': r'\\', '#': r'\#', '_': r'\_',
        '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}', '“': '``', '”': "''", '‘': '`', '’': "'",
        '–': '--', '—': '---',
    }
    return "".join(mapping.get(c, c) for c in text)


def _replace_latex_command(content: str, command: str, value: str) -> str:
    """
    Replaces a LaTeX \\newcommand placeholder using a robust regular expression.
    This version is safer against complex strings with special characters.
    """
    # This pattern finds the entire \\newcommand{...}{...} block.
    pattern = re.compile(r"\\newcommand{\\" + command + r"}\{.*?\}")

    # We construct the full replacement string we want to insert.
    # The `value` should already be escaped for LaTeX before being passed here.
    replacement_string = f"\\newcommand{{\\{command}}}{{{value}}}"

    # Using a lambda for the replacement is the safest way to handle
    # values that might contain backslashes, as it prevents re.sub's
    # special interpretation of them.
    new_content, count = pattern.subn(lambda m: replacement_string, content, count=1)

    if count == 0:
        logger.warning(f"Could not find and replace \\newcommand for '{command}' in template.")
        return content

    return new_content


def create_cover_latex(
        json_path: Path,
        output_dir: Path,
        template_path: Path,
        build_dir: Path,
        replacements: Dict[str, str],
        debug_mode: bool = False,
        data = None,
) -> Optional[Dict[str, Path]]:
    """
    Generates a book cover using a LaTeX/TikZ template, including an ISBN barcode.
    Creates a full-spread PDF, a full-spread PNG, and separate front/back cover PNGs.
    """
    logger.info("--- Starting LaTeX Cover Generation ---")


    # --- 1. Load Data and Define Dimensions ---
    if data is None: # load from file
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load JSON data from {json_path}: {e}", exc_info=True)
            return None

    book_width_in = data.get("book_width_in", 6.0)
    book_height_in = data.get("book_height_in", 9.0)
    spine_width_in = data.get("spine_width_in", 0.5)
    bleed_in = 0.125
    storefront_dpi = 300

    page_width = (book_width_in * 2) + spine_width_in + (bleed_in * 2)
    page_height = book_height_in + (bleed_in * 2)

    # --- Dynamic calculation for cover content centering ---
    front_cover_center_xshift = (spine_width_in / 2) + (book_width_in / 2)
    back_cover_center_xshift = -front_cover_center_xshift

    # --- 2. Generate Bookland EAN Barcode using the dedicated generator ---
    isbn_str = data.get('isbn13')
    barcode_draw_command = ""  # Initialize with empty command as fallback

    # Check for valid ISBN (not None, not 'nan', not empty)
    if isbn_str and str(isbn_str).lower() not in ['nan', 'none', '']:
        try:
            # Instantiate the robust generator, pointing it to the build directory
            barcode_generator = BooklandBarcodeGenerator(output_dir=build_dir)
            # Generate the barcode with the default "90000" price code
            barcode_path = barcode_generator.generate(isbn=str(isbn_str))

            if barcode_path and barcode_path.exists():
                barcode_filename = barcode_path.name
                # Center the barcode on the back cover, 0.5in from the bottom.
                # The width is set to 2 inches, a standard size for covers.
                # Add 0.25" white space margin around all sides of the barcode
                barcode_draw_command = (
                    f"\\node[anchor=south, yshift=0.5in] at ([xshift={back_cover_center_xshift:.4f}in]current page.south) "
                    f"{{ "
                    f"\\begin{{tikzpicture}}[baseline=(current bounding box.center)]"
                    f"\\node[fill=white, inner sep=0.25in] (barcode) {{ \\includegraphics[width=2in]{{{barcode_filename}}} }};"
                    f"\\end{{tikzpicture}} "
                    f"}};"
                )
                logger.info(f"✅ Barcode generated successfully for ISBN: {isbn_str}")
            else:
                # The generator already logs detailed errors, so we just note the failure here.
                logger.warning("Barcode generation failed. See previous errors for details.")

        except Exception as e:
            logger.error(f"An unexpected error occurred during barcode generation for ISBN '{isbn_str}': {e}", exc_info=True)
    else:
        logger.info(f"No valid ISBN provided (got: '{isbn_str}'); skipping barcode generation.")
    # --- 3. Prepare LaTeX Source ---
    if not template_path.exists():
        logger.error(f"Cover template not found at: {template_path}")
        return None

    tex_content = template_path.read_text(encoding='utf-8')

    # FIX: Randomly choose a background color and create the LaTeX definition string.
    chosen_color = random.choice(KOREAN_COLOR_PALETTE)
    logger.info(f"Selected random cover color: {chosen_color['name']}")
    c, m, y, k = chosen_color['c'], chosen_color['m'], chosen_color['y'], chosen_color['k']
    color_def_string = f"\\definecolor{{coverbackground}}{{cmyk}}{{{c:.4f},{m:.4f},{y:.4f},{k:.4f}}}"

    # FIX: Use a specific regex to replace the placeholder color definition line.
    # This is more robust than trying to stuff a command inside another command.
    placeholder_pattern = re.compile(r"^\\definecolor{coverbackground}.*$", re.MULTILINE)
    # FIX: Use a lambda function to prevent re.subn from misinterpreting backslashes in the replacement string.
    tex_content, num_replacements = placeholder_pattern.subn(lambda m: color_def_string, tex_content, count=1)
    if num_replacements == 0:
        logger.error("Failed to find and replace the cover background color placeholder in the template.")
        return None

    # Replace dimensions and text using helper functions for clarity and safety
    tex_content = _replace_latex_command(tex_content, "coverPageWidth", f"{page_width:.4f}in")
    tex_content = _replace_latex_command(tex_content, "coverPageHeight", f"{page_height:.4f}in")
    tex_content = _replace_latex_command(tex_content, "coverFrontCoverXShift", f"{front_cover_center_xshift:.4f}in")
    tex_content = _replace_latex_command(tex_content, "coverTrimHeight", f"{book_height_in:.4f}in")
    tex_content = _replace_latex_command(tex_content, "coverTrimWidth", f"{book_width_in:.4f}in")
    tex_content = _replace_latex_command(tex_content, "coverSpineWidth", f"{spine_width_in:.4f}in")
    tex_content = _replace_latex_command(tex_content, "coverBleedIn", f"{bleed_in:.4f}in")
    tex_content = _replace_latex_command(tex_content, "coverDebugMode", "true" if debug_mode else "false")
    tex_content = _replace_latex_command(tex_content, "coverBackCoverXShift", f"{back_cover_center_xshift:.4f}in")
    
    # Process back cover text with variable substitution and Korean-aware escaping
    back_cover_text = data.get('back_cover_text', '')
    back_cover_text = substitute_template_variables(back_cover_text, data)
    tex_content = _replace_latex_command(tex_content, "coverBackCoverText",
                                         _escape_latex_preserve_korean(back_cover_text))

    tex_content = _replace_latex_command(tex_content, "coverBookTitle", _escape_latex_preserve_korean(data.get('title', 'Untitled')))
    tex_content = _replace_latex_command(tex_content, "coverBookAuthor",
                                         _escape_latex_preserve_korean(data.get('author', 'AI Lab for Book-Lovers')))
    tex_content = _replace_latex_command(tex_content, "coverImprint",
                                         _escape_latex_preserve_korean(data.get('imprint', 'xynapse traces')))
    tex_content = _replace_latex_command(tex_content, "coverDrawBarcode", barcode_draw_command)

    # Apply imprint-specific replacements

    if replacements:
        logger.warning(str(replacements.items()))
        for key, value in replacements.items():
            for item in value:
                # if the value contains Korean characters, we need to escape it first
               if 'r\korean' in item:
                    tex_content = _replace_latex_command(tex_content, key, _escape_latex_preserve_korean(item))
            else:
                    tex_content = _replace_latex_command(tex_content, key, _escape_latex(item))
    # otherwise, pass


    subtitle_chunk = ""
    if subtitle_raw := data.get("subtitle"):
        # Validate and process subtitle for xynapse_traces imprint
        processed_subtitle = subtitle_raw
        imprint = data.get('imprint', '')
        
        if imprint == 'xynapse_traces':
            try:
                from ..metadata.subtitle_validator import SubtitleValidator
                
                subtitle_validator = SubtitleValidator()
                processed_subtitle = subtitle_validator.process_xynapse_subtitle(subtitle_raw, data)
                
                if processed_subtitle != subtitle_raw:
                    logger.warning(f"Cover subtitle replaced: '{subtitle_raw}' -> '{processed_subtitle}'")
                    # Update data for consistency
                    data['subtitle'] = processed_subtitle
                    
            except Exception as e:
                logger.warning(f"Cover subtitle validation failed, using original: {e}")
                processed_subtitle = subtitle_raw
        
        subtitle_escaped = _escape_latex(processed_subtitle)
        subtitle_chunk = f"\\vspace{{1em}}\n{{\\Large\\sffamily\\bfseries\\scshape {subtitle_escaped}\\par}}"
    tex_content = _replace_latex_command(tex_content, "coverBookSubtitleChunk", subtitle_chunk)

    tex_filepath = build_dir / f"{json_path.stem}_cover.tex"
    tex_filepath.write_text(tex_content, encoding='utf-8')

    # --- 4. Compile the LaTeX file to PDF ---
    logger.info(f"Compiling cover TeX file: {tex_filepath}")
    compiler = "lualatex"
    jobname = tex_filepath.stem
    command = [compiler, "-interaction=nonstopmode", "-halt-on-error", f"-jobname={jobname}", tex_filepath.name]
    process = None
    for i in range(2):
        process = subprocess.run(command, cwd=build_dir, capture_output=True, text=True, check=False)
        if process.returncode != 0:
            break

    # --- 5. Verify PDF and Convert to PNGs ---
    compiled_pdf = build_dir / f"{jobname}.pdf"

    if process.returncode != 0 or not compiled_pdf.exists():
        if process.returncode == 0:
            logger.error("PDF file was not created after successful compilation (silent failure).")
        else:
            logger.error(f"LaTeX cover compilation failed with exit code {process.returncode}.")

        log_file = build_dir / f"{jobname}.log"
        if log_file.exists():
            log_tail = log_file.read_text(encoding='utf-8', errors='ignore')[-3000:]
            logger.error(f"--- LaTeX Log Tail for {log_file.name} ---\n{log_tail}")
        else:
            logger.error("No LaTeX log file was found to provide details on the failure.")
        return None

    # Convert to PDF/X-1a using Ghostscript
    pdfx_path = build_dir / f"{json_path.stem}_cover_x1a.pdf"
    gs_command = [
        "gs", "-dCompatibilityLevel=1.4", "-dPDFX", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite",
        "-dPDFSETTINGS=/prepress", f"-sOutputFile={pdfx_path}", str(compiled_pdf)
    ]
    try:
        subprocess.run(gs_command, capture_output=True, text=True, check=True)
        logger.info(f"Ghostscript PDF/X-1a conversion successful for {compiled_pdf.name}")
        compiled_pdf = pdfx_path
    except FileNotFoundError:
        logger.warning("Ghostscript not found. Skipping PDF/X-1a conversion.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Ghostscript PDF/X-1a conversion failed: {e.stderr}")
        logger.warning("Proceeding with non-PDF/X-1a PDF.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during Ghostscript conversion: {e}", exc_info=True)
        logger.warning("Proceeding with non-PDF/X-1a PDF.")

    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = json_path.stem
    final_pdf_path = output_dir / f"{base_name}_cover_spread.pdf"
    shutil.move(str(compiled_pdf), str(final_pdf_path))

    try:
        with fitz.open(final_pdf_path) as doc:
            page = doc.load_page(0)
            # --- Full Spread PNG (for review) ---
            full_spread_png_path = output_dir / f"{base_name}_cover_spread.png"
            page.get_pixmap(dpi=300).save(str(full_spread_png_path))
            logger.info(f"Generated full spread PNG: {full_spread_png_path}")

            # --- Cropped Front and Back Cover PNGs (for storefront) ---
            points_per_inch = 72
            back_rect = fitz.Rect(
                bleed_in * points_per_inch,
                bleed_in * points_per_inch,
                (bleed_in + book_width_in) * points_per_inch,
                (bleed_in + book_height_in) * points_per_inch
            )
            front_rect = fitz.Rect(
                (bleed_in + book_width_in + spine_width_in) * points_per_inch,
                bleed_in * points_per_inch,
                (bleed_in + book_width_in * 2 + spine_width_in) * points_per_inch,
                (bleed_in + book_height_in) * points_per_inch
            )

            front_cover_png_path = output_dir / f"{base_name}_front_cover.png"
            page.get_pixmap(dpi=storefront_dpi, clip=front_rect).save(str(front_cover_png_path))
            logger.info(f"Generated front cover PNG: {front_cover_png_path}")

            back_cover_png_path = output_dir / f"{base_name}_back_cover.png"
            page.get_pixmap(dpi=storefront_dpi, clip=back_rect).save(str(back_cover_png_path))
            logger.info(f"Generated back cover PNG: {back_cover_png_path}")

        logger.info("✅ Cover generation process completed successfully.")
        return {
            "full_spread_pdf": final_pdf_path,
            "full_spread_png": full_spread_png_path,
            "front_cover_png": front_cover_png_path,
            "back_cover_png": back_cover_png_path,
        }

    except Exception as e:
        logger.error(f"Failed to convert cover PDF to PNGs: {e}", exc_info=True)
        return None
