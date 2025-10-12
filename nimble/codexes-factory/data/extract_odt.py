#!/usr/bin/env python3
"""Extract text from ODT files for PT Boat book"""

import zipfile
import xml.etree.ElementTree as ET
import sys
import os
from pathlib import Path

def extract_text_from_odt(odt_path):
    """Extract text from an ODT file."""
    try:
        with zipfile.ZipFile(odt_path, 'r') as zf:
            # Read the content.xml file
            content_xml = zf.read('content.xml')

        # Parse XML
        root = ET.fromstring(content_xml)

        # Define namespaces
        namespaces = {
            'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
            'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'
        }

        # Extract all text
        text_parts = []

        # Find all text:p (paragraph) elements
        for elem in root.iter():
            if elem.tag.endswith('}p') or elem.tag.endswith('}h'):
                # Get text from this element and all children
                text = ''.join(elem.itertext())
                if text.strip():
                    text_parts.append(text.strip())

        return '\n\n'.join(text_parts)

    except Exception as e:
        print(f"Error extracting {odt_path}: {e}", file=sys.stderr)
        return None

def main():
    source_dir = Path("/Users/fred/Downloads/Files for New PT book")
    output_dir = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/output/pt_boat_book/extracted_text")

    # List of ODT files to extract
    odt_files = [
        "Title of the new book frank andruss.odt",
        "Forward for new Elco book frank andruss.odt",
        "frank andruss - Preface for new book.odt",
        "chapter one write up new Elco book frank andruss.odt",
        "Chapter One Photo Descriptions frank andruss.odt",
        "Elco's seventy-seven-foot design chapter two frank andruss.odt",
        "chapter twp photo descriptions 2nd one frank andruss.odt",
        "The Workers that made it happen chapter 3 frank andruss.odt",
        "chapter three photo descriptions frank andruss.odt",
        "Elco 80 foot chapter frank andruss.odt",
        "chapter four photo descriptions second time frank andruss.odt",
        "Chapter 5 the Lighter Side of War frank andruss.odt",
        "Chapter five photo discriptions (2) frank andruss.odt",
        "Chater 7 end of an era frank andruss.odt",
        "chapter 7 photo descriptions frank andruss.odt",
        "frank andruss - ackowledgements.odt",
    ]

    for odt_file in odt_files:
        odt_path = source_dir / odt_file
        if not odt_path.exists():
            print(f"Warning: {odt_file} not found")
            continue

        text = extract_text_from_odt(odt_path)
        if text:
            # Create output filename
            output_name = odt_file.replace('.odt', '.txt')
            output_path = output_dir / output_name

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)

            print(f"Extracted: {odt_file} -> {output_name}")
        else:
            print(f"Failed to extract: {odt_file}")

if __name__ == '__main__':
    main()
