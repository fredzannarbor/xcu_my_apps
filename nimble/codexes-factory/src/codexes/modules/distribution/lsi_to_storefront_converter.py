"""
LSI to Storefront Catalog Converter
Converts LSI CSV format to storefront catalog format for xynapse_traces imprint
"""

import csv
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)

# Mapping from LSI CSV columns to storefront catalog columns
LSI_TO_STOREFRONT_MAPPING = {
    'ISBN or SKU': 'isbn13',
    'Title': 'title', 
    'Publisher': None,  # Will use 'AI Lab for Book-Lovers' as author
    'Imprint': 'imprint',
    'Pages': 'page_count',
    'Pub Date': 'publication_date',
    'Annotation / Summary': 'back_cover_text',
    'Series Name': 'series_name',
    '# in Series': 'series_number',
    'Keywords': None,  # Will be used in storefront_publishers_note_en
}

# Required columns for storefront catalog
STOREFRONT_COLUMNS = [
    'id', 'title', 'subtitle', 'author', 'isbn13', 'series_name',
    'series_number', 'page_count', 'publication_date', 'imprint',
    'back_cover_text', 'storefront_publishers_note_en',
    'front_cover_image_path', 'full_spread_pdf_path', 'interior_pdf_path'
]


class LsiToStorefrontConverter:
    """Convert LSI CSV format to storefront catalog format"""
    
    def __init__(self, default_author: str = "AI Lab for Book-Lovers"):
        self.default_author = default_author
        self.logger = logging.getLogger(__name__)
    
    def convert_lsi_to_storefront(self, lsi_csv_path: str, output_path: str) -> bool:
        """
        Convert LSI CSV to storefront catalog format
        
        Args:
            lsi_csv_path: Path to the LSI CSV file
            output_path: Path for the output storefront catalog CSV
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            # Read LSI CSV with UTF-8-SIG encoding to handle BOM
            lsi_df = pd.read_csv(lsi_csv_path, encoding='utf-8-sig')
            
            self.logger.info(f"Loaded LSI CSV with {len(lsi_df)} books")
            
            # Convert each row
            storefront_rows = []
            for _, row in lsi_df.iterrows():
                storefront_row = self._convert_single_book(row)
                if storefront_row:
                    storefront_rows.append(storefront_row)
            
            # Create DataFrame with storefront format
            storefront_df = pd.DataFrame(storefront_rows, columns=STOREFRONT_COLUMNS)
            
            # Ensure output directory exists
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to CSV
            storefront_df.to_csv(output_path, index=False)
            
            self.logger.info(f"Successfully converted {len(storefront_rows)} books to storefront format")
            self.logger.info(f"Saved to: {output_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error converting LSI to storefront format: {e}")
            return False
    
    def _convert_single_book(self, lsi_row: pd.Series) -> Optional[Dict]:
        """Convert a single LSI row to storefront format"""
        try:
            # Generate unique ID
            book_id = str(uuid.uuid4()).replace('-', '')[:12]
            
            # Extract and clean title
            title = str(lsi_row.get('Title', '')).strip()
            if not title:
                return None
            
            # Extract and format ISBN
            isbn_raw = lsi_row.get('ISBN or SKU', '')
            if pd.isna(isbn_raw):
                isbn = ''
            else:
                isbn = str(isbn_raw).strip()
                # Handle scientific notation or float format
                if 'E+' in isbn or 'e+' in isbn or '.' in isbn:
                    isbn = self._convert_scientific_isbn(isbn)
                # Remove .0 if present
                if isbn.endswith('.0'):
                    isbn = isbn[:-2]
            
            # Clean annotation HTML
            annotation = str(lsi_row.get('Annotation / Summary', ''))
            back_cover_text = self._extract_back_cover_text(annotation)
            
            # Format publication date
            pub_date = self._format_publication_date(lsi_row.get('Pub Date', ''))
            
            # Create safe filename from title
            safe_title = self._create_safe_filename(title)
            
            # Build paths (these would be generated during prepress)
            front_cover_path = f"output/xynapse_traces_build/covers/{safe_title}_front_cover.png"
            full_spread_path = f"output/xynapse_traces_build/covers/{safe_title}_cover_spread.pdf"
            interior_path = f"output/xynapse_traces_build/interiors/{safe_title}_interior.pdf"
            
            # Create publisher's note
            keywords = str(lsi_row.get('Keywords', ''))
            publishers_note = self._create_publishers_note(title, keywords)
            
            return {
                'id': book_id,
                'title': title,
                'subtitle': '',  # xynapse_traces doesn't use subtitles
                'author': self.default_author,
                'isbn13': isbn,
                'series_name': str(lsi_row.get('Series Name', '')).strip(),
                'series_number': str(lsi_row.get('# in Series', '')).strip(),
                'page_count': str(lsi_row.get('Pages', '')).strip(),
                'publication_date': pub_date,
                'imprint': str(lsi_row.get('Imprint', '')).strip(),
                'back_cover_text': back_cover_text,
                'storefront_publishers_note_en': publishers_note,
                'front_cover_image_path': front_cover_path,
                'full_spread_pdf_path': full_spread_path,
                'interior_pdf_path': interior_path
            }
            
        except Exception as e:
            self.logger.error(f"Error converting book '{lsi_row.get('Title', 'Unknown')}': {e}")
            return None
    
    def _convert_scientific_isbn(self, isbn_str: str) -> str:
        """Convert scientific notation ISBN to standard format"""
        try:
            # Handle scientific notation like 9.78161E+12
            if 'E+' in isbn_str or 'e+' in isbn_str:
                # Convert to float first, then format without decimal
                isbn_float = float(isbn_str)
                # Format as integer string without scientific notation
                return f"{isbn_float:.0f}"
            else:
                # Try to convert normally
                isbn_float = float(isbn_str)
                return f"{isbn_float:.0f}"
        except (ValueError, OverflowError):
            return isbn_str
    
    def _extract_back_cover_text(self, annotation: str) -> str:
        """Extract back cover text from LSI annotation, removing HTML tags"""
        if not annotation:
            return ""
        
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', annotation)
        
        # Convert HTML entities
        clean_text = clean_text.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        
        # Clean up whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # Extract first paragraph for back cover (usually the hook)
        paragraphs = [p.strip() for p in clean_text.split('\n\n') if p.strip()]
        if paragraphs:
            # Use first paragraph, but ensure it's complete
            first_para = paragraphs[0]
            if len(first_para) > 600:
                # Find a good breaking point at sentence boundaries
                sentences = first_para.split('. ')
                truncated_sentences = []
                current_length = 0
                
                for sentence in sentences:
                    # Add sentence if it doesn't make text too long
                    test_length = current_length + len(sentence) + 2  # +2 for '. '
                    if test_length <= 500 and truncated_sentences:
                        break
                    elif not truncated_sentences:  # Always include at least first sentence
                        truncated_sentences.append(sentence)
                        current_length = len(sentence)
                    else:
                        truncated_sentences.append(sentence)
                        current_length = test_length
                
                # Join sentences and ensure proper ending
                result = '. '.join(truncated_sentences)
                if not result.endswith('.'):
                    result += '.'
                return result
            return first_para
        
        return clean_text[:500] + "..." if len(clean_text) > 500 else clean_text
    
    def _format_publication_date(self, pub_date: str) -> str:
        """Format publication date to YYYY-MM-DD format"""
        if not pub_date or pub_date.strip() == '':
            return ''
        
        try:
            # Handle MM/DD/YY format
            if '/' in pub_date:
                parts = pub_date.strip().split('/')
                if len(parts) == 3:
                    month, day, year = parts
                    # Convert 2-digit year to 4-digit
                    if len(year) == 2:
                        year = f"20{year}"
                    
                    # Create date object to validate and format
                    date_obj = datetime(int(year), int(month), int(day))
                    return date_obj.strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            pass
        
        return pub_date
    
    def _create_safe_filename(self, title: str) -> str:
        """Create safe filename from book title"""
        # Remove special characters and replace spaces with underscores
        safe_name = re.sub(r'[^\w\s-]', '', title)
        safe_name = re.sub(r'\s+', '_', safe_name)
        return safe_name
    
    def _create_publishers_note(self, title: str, keywords: str) -> str:
        """Create publisher's note for storefront"""
        
        base_note = """Welcome. The path to our shared future is etched with profound questions that demand deep contemplation. At xynapse traces, our core mission is to explore the frontiers of human knowledge through the transformative practice of 필사 pilsa, or transcriptive meditation.

The slow, deliberate transfer of thought from eye to hand to page is a powerful algorithm for understanding. As you physically inscribe these carefully curated insights, you are not just copying text. You are slowing down the information stream, allowing complex concepts to resonate and integrate within your own cognitive architecture. In an age defined by rapid consumption and surface-level engagement, this meditative act is a radical form of focus.

We invite you to take up your pen and begin this journey of discovery."""
        
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(';') if k.strip()][:5]  # Limit to 5 keywords
            if keyword_list:
                keyword_text = f"\n\nKey themes for contemplation: {', '.join(keyword_list)}."
                base_note += keyword_text
        
        return base_note


def main():
    """CLI interface for the converter"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert LSI CSV to storefront catalog format")
    parser.add_argument("input_csv", help="Path to input LSI CSV file")
    parser.add_argument("output_csv", help="Path to output storefront catalog CSV file")
    parser.add_argument("--author", default="AI Lab for Book-Lovers", help="Default author name")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    converter = LsiToStorefrontConverter(args.author)
    success = converter.convert_lsi_to_storefront(args.input_csv, args.output_csv)
    
    if success:
        print(f"✅ Successfully converted {args.input_csv} to {args.output_csv}")
    else:
        print(f"❌ Failed to convert {args.input_csv}")
        exit(1)


if __name__ == "__main__":
    main()