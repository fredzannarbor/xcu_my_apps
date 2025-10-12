# /Users/fred/xcu_my_apps/nimble/codexes-factory/src/codexes/modules/prepress/pilsa_prepress.py
# version 1.3.3
import logging
import json
import shutil
import uuid
from pathlib import Path
from typing import Dict, Optional

import fitz  # PyMuPDF

# These are assumed to be existing helper modules within your project structure
from .tex_utils import compile_tex_to_pdf, escape_latex
from ..covers.cover_generator import create_cover_latex

logger = logging.getLogger(__name__)


def _create_content_tex_files(data: dict, build_dir: Path, templates_dir: Path):
    """
    Generates all necessary .tex files for the book's interior based on the data.
    This includes creating content for key pages and placeholders for others
    to ensure the main LaTeX template can compile successfully.
    """
    logger.info("Generating all required interior .tex content files.")

    # --- Create title_page.tex (Defines \thetitle for headers) ---
    book_title = escape_latex(data.get('title', 'Untitled Book'))
    book_author = escape_latex(data.get('author', 'Unknown Author'))
    title_page_content = (
        f"\\title{{{book_title}}}\n"
        f"\\author{{{book_author}}}\n"
        f"\\maketitle\n"
    )
    (build_dir / "title_page.tex").write_text(title_page_content, encoding='utf-8')
    logger.info("Created title_page.tex with content to define book title and author.")

    # --- Create publishers_note.tex ---
    publishers_note_content = data.get('storefront_publishers_note_en', '')
    if publishers_note_content:
        latex_content = (
            f"\\chapter*{{Publisher's Note}}\n"
            f"\\vspace*{{2em}}\n\n"
            f"{escape_latex(publishers_note_content)}"
        )
        (build_dir / "publishers_note.tex").write_text(latex_content, encoding='utf-8')
        logger.info("Created publishers_note.tex with content from 'storefront_publishers_note_en'.")
    else:
        (build_dir / "publishers_note.tex").touch()
        logger.warning("No 'storefront_publishers_note_en' found. Created empty publishers_note.tex.")

    # --- Create other required placeholder files ---
    # These files are included unconditionally in the main .tex template.
    required_placeholders = [
        "copyright_page.tex",
        "table_of_contents.tex",
        "transcription_note.tex",
    ]
    for filename in required_placeholders:
        (build_dir / filename).touch()
    logger.info(f"Created {len(required_placeholders)} placeholder .tex files to satisfy template includes.")

    if not data.get('quotes'):
        logger.warning("No 'quotes' found in JSON data; interior will be minimal.")


def process_single_book(
        json_path: Path,
        final_output_dir: Path,
        templates_dir: Path,
        debug_cover: bool = False,
        catalog_only: bool = False,
        leave_build_directories_in_place: bool = False
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
        template_path = templates_dir / 'pilsa_template.tex'
        shutil.copy(template_path, temp_build_dir / 'pilsa_template.tex')

        _create_content_tex_files(data, temp_build_dir, templates_dir)

        main_tex_file = temp_build_dir / "pilsa_template.tex"
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
        cover_results = create_cover_latex(
            json_path=json_path,
            output_dir=final_output_dir / "covers",
            templates_dir=templates_dir,
            build_dir=temp_build_dir,
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
