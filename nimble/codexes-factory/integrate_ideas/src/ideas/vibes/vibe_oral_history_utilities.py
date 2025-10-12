import json
import logging
import os
from pathlib import Path
import pymupdf as fitz
from typing import Dict, List, Any

# Set up logging (use the same logger configuration as the main script)
logger = logging.getLogger(__name__)


def load_json_file(file_path):
    """Load and return JSON file content."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        raise


def save_json_file(content: Dict, output_path: str):
    """Save a dictionary as a JSON file."""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved JSON to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save JSON file: {e}")
        raise


def save_markdown_file(content, output_path):
    """Save the Markdown content to a file."""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Markdown draft saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save Markdown file: {e}")
        raise


def read_text_file(file_path: str) -> str:
    """Read content from a plain text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read text file {file_path}: {e}")
        return ""


def read_pdf_file(file_path: str) -> str:
    """Read content from a PDF file using PyMuPDF."""
    try:
        content = ""
        doc = fitz.open(file_path)
        for page in doc:
            content += page.get_text() + "\n"
        doc.close()
        return content
    except Exception as e:
        logger.error(f"Failed to read PDF file {file_path}: {e}")
        return ""


def read_stipulated_facts(file_paths: List[str]) -> List[Dict[str, str]]:
    """Read stipulated facts from a list of file paths (PDF, JSON, or text)."""
    facts = []
    for path in file_paths:
        file_path = Path(path)
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            continue

        file_suffix = file_path.suffix.lower()
        content = ""
        source_type = file_suffix[1:] if file_suffix else "unknown"  # Remove leading dot

        if file_suffix == '.pdf':
            content = read_pdf_file(str(file_path))
        elif file_suffix == '.json':
            try:
                json_data = load_json_file(str(file_path))
                content = json.dumps(json_data, indent=2)  # Convert to string for inclusion in prompts
            except Exception as e:
                logger.error(f"Failed to parse JSON file {file_path}: {e}")
                content = ""
        elif file_suffix in ['.txt', '']:
            content = read_text_file(str(file_path))
        else:
            logger.warning(f"Unsupported file type for {file_path}; skipping.")
            continue

        if content:
            facts.append({
                "source": str(file_path),
                "type": source_type,
                "content": content
            })
        else:
            logger.warning(f"No content extracted from {file_path}")

    logger.info(f"Loaded {len(facts)} stipulated facts files.")
    return facts