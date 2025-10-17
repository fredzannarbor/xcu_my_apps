"""
Substack Post Generator for xynapse_traces books
Generates HTML-formatted posts for individual books and collections
"""

import csv
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BookData:
    """Represents a book's data extracted from LSI CSV"""
    title: str
    isbn: str
    annotation: str
    pub_date: str
    keywords: str
    short_description: str
    price: str
    pages: str
    series_name: str
    series_number: str
    
    @property
    def clean_annotation(self) -> str:
        """Return annotation with HTML tags cleaned for display"""
        # Remove HTML tags but preserve line breaks
        clean = re.sub(r'<[^>]+>', '', self.annotation)
        # Convert multiple spaces to single spaces
        clean = re.sub(r'\s+', ' ', clean)
        # Split into paragraphs and rejoin with proper spacing
        paragraphs = [p.strip() for p in clean.split('\n\n') if p.strip()]
        return '\n\n'.join(paragraphs)
    
    @property
    def topic_theme(self) -> str:
        """Extract the core theme from the title"""
        if ':' in self.title:
            return self.title.split(':')[0].strip()
        return self.title


class SubstackPostGenerator:
    """Generate HTML posts for Substack from xynapse_traces book data"""
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.books: List[BookData] = []
        self._load_books()
    
    def _load_books(self):
        """Load book data from CSV file (supports both LSI and storefront formats)"""
        with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Check if this is LSI format or storefront format
                title_key = 'Title' if 'Title' in row else 'title'
                if not row.get(title_key, '').strip():
                    continue
                    
                # Map columns based on format
                if 'Title' in row:  # LSI format
                    book = BookData(
                        title=row.get('Title', '').strip(),
                        isbn=row.get('ISBN or SKU', '').strip(),
                        annotation=row.get('Annotation / Summary', '').strip(),
                        pub_date=row.get('Pub Date', '').strip(),
                        keywords=row.get('Keywords', '').strip(),
                        short_description=row.get('Short Description', '').strip(),
                        price=row.get('US Suggested List Price', '').strip(),
                        pages=row.get('Pages', '').strip(),
                        series_name=row.get('Series Name', '').strip(),
                        series_number=row.get('# in Series', '').strip()
                    )
                else:  # Storefront format
                    # Extract keywords from publisher's note if available
                    pub_note = row.get('storefront_publishers_note_en', '')
                    keywords = ''
                    if 'Key themes for contemplation:' in pub_note:
                        keywords_part = pub_note.split('Key themes for contemplation:')[1].strip()
                        keywords = keywords_part.split('.')[0] if '.' in keywords_part else keywords_part
                    
                    book = BookData(
                        title=row.get('title', '').strip(),
                        isbn=str(row.get('isbn13', '')).strip(),
                        annotation=row.get('back_cover_text', '').strip(),
                        pub_date=row.get('publication_date', '').strip(),
                        keywords=keywords,
                        short_description=row.get('back_cover_text', '').strip(),
                        price='24.95',  # Default price for xynapse_traces
                        pages=str(row.get('page_count', '')).strip(),
                        series_name=row.get('series_name', '').strip(),
                        series_number=str(row.get('series_number', '')).strip()
                    )
                
                self.books.append(book)
    
    def generate_individual_post(self, book: BookData) -> str:
        """Generate HTML post for a single book"""
        
        # Generate Amazon buy link
        amazon_link = self._create_amazon_link(book.isbn)
        
        template = f"""<h1>New Release: <em>{book.title}</em></h1>

<p><strong>A {book.series_name} book for contemplative minds seeking deeper understanding</strong></p>

<div style="background-color: #f8f9fa; padding: 20px; margin: 20px 0; border-left: 4px solid #007acc;">
<p><strong>📖 {book.title}</strong><br>
📅 Publication Date: {self._format_date(book.pub_date)}<br>
📄 {book.pages} pages<br>
💰 ${book.price}<br>
🛒 <a href="{amazon_link}" target="_blank">Buy on Amazon</a><br>
📚 {book.series_name} Series #{book.series_number}</p>
</div>

<h2>About This Book</h2>

{self._format_annotation_as_html(book.clean_annotation)}

<h2>The Transcriptive Meditation Experience</h2>

<p>Like all books in the <em>{book.series_name}</em> series, <em>{book.title}</em> is designed for active engagement through hand transcription. Each volume includes:</p>

<ul>
<li><strong>Curated Quotations</strong> — Essential passages selected for copying and contemplation</li>
<li><strong>Key Concepts</strong> — Framework ideas that illuminate the topic's complexity</li>
<li><strong>Mnemonics</strong> — Memory tools to help retain insights</li>
<li><strong>Verified Sources</strong> — Complete bibliography for further exploration</li>
</ul>

<h2>Why {book.topic_theme}?</h2>

<p>This essential exploration addresses one of the most pressing questions of our time. Through careful transcription and contemplation, readers develop nuanced understanding of the tension between {self._extract_dichotomy(book.title)} that goes beyond simple polarization.</p>

<p>The practice of transcriptive meditation allows you to engage deeply with expert perspectives, philosophical frameworks, and cutting-edge research. Each carefully selected quotation becomes a gateway to deeper understanding and personal reflection.</p>

<h2>Perfect For Readers Who...</h2>

<ul>
<li>Seek deeper engagement with complex contemporary issues</li>
<li>Value contemplative learning practices</li>
<li>Want to move beyond surface-level debates</li>
<li>Appreciate the intersection of mindfulness and intellectual growth</li>
<li>Enjoy exploring multiple perspectives on challenging topics</li>
</ul>

<h2>The xynapse traces Approach</h2>

<p>Our AI Lab for Book-Lovers has curated this collection from the frontiers of human knowledge, presenting balanced perspectives on {book.topic_theme}. By engaging with these ideas through transcriptive meditation, readers develop both understanding and mindfulness.</p>

<blockquote>
<p><em>"The practice of transcription transforms passive consumption into active learning, fostering both clarity and contemplation."</em></p>
</blockquote>

<h2>Keywords & Themes</h2>

<p><strong>Explore:</strong> {book.keywords}</p>

<hr>

<p><strong>📚 Available now through major book retailers, Ingram, and direct from NimbleBooks.com</strong><br>
<strong>🔗 ISBN:</strong> {book.isbn}<br>
<strong>🏷️ Series:</strong> {book.series_name}</p>

<p><em>xynapse traces is an imprint of Nimble Books LLC, pioneering AI-assisted publishing for thoughtful readers.</em></p>
"""
        
        return template
    
    def generate_collection_post(self, books: List[BookData], title: str = "New Releases") -> str:
        """Generate HTML post for a collection of books"""
        
        book_list = ""
        for book in books:
            book_list += f"""
<div style="border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 5px;">
<h3>{book.title}</h3>
<p><strong>Pages:</strong> {book.pages} | <strong>Price:</strong> ${book.price} | <strong>ISBN:</strong> {book.isbn}</p>
<p>{book.short_description}</p>
</div>"""
        
        template = f"""<h1>{title}</h1>

<p><strong>Fresh perspectives for contemplative minds</strong></p>

<p>We're excited to share the latest additions to our <em>xynapse traces</em> catalog. Each book offers carefully curated insights on the critical questions of our time, designed for engagement through transcriptive meditation.</p>

{book_list}

<h2>The Transcriptive Meditation Practice</h2>

<p>Each book in the collection includes:</p>
<ul>
<li>Curated quotations for hand transcription</li>
<li>Key concepts and frameworks</li>
<li>Mnemonics for retention</li>
<li>Complete bibliographies for further study</li>
</ul>

<p><em>All titles available through major book retailers, Ingram, and NimbleBooks.com.</em></p>"""
        
        return template
    
    def _create_amazon_link(self, isbn13: str) -> str:
        """Create Amazon buy link from ISBN-13, always using ISBN-10 format"""
        try:
            # Convert ISBN-13 to ISBN-10 for Amazon link (required)
            isbn10 = self._isbn13_to_isbn10(isbn13)
            if isbn10:
                return f"https://www.amazon.com/dp/{isbn10}?tag=internetbookinfo-20"
            else:
                # Log warning but still return a link (though it may not work correctly)
                print(f"Warning: Could not convert ISBN-13 to ISBN-10: {isbn13}")
                return f"https://www.amazon.com/dp/{isbn13}?tag=internetbookinfo-20"
        except Exception as e:
            # Log error but still return a link
            print(f"Error creating Amazon link for {isbn13}: {e}")
            return f"https://www.amazon.com/dp/{isbn13}?tag=internetbookinfo-20"
    
    def _isbn13_to_isbn10(self, isbn13: str) -> Optional[str]:
        """Convert ISBN-13 to ISBN-10"""
        try:
            # Remove any hyphens and ensure it's a string
            isbn_str = str(isbn13).replace('-', '').strip()
            
            # Must be 13 digits and start with 978
            if len(isbn_str) != 13 or not isbn_str.startswith('978'):
                return None
            
            # Take digits 3-12 (removing 978 prefix and check digit)
            isbn10_base = isbn_str[3:12]
            
            # Calculate ISBN-10 check digit
            check_sum = 0
            for i, digit in enumerate(isbn10_base):
                check_sum += int(digit) * (10 - i)
            
            check_digit = (11 - (check_sum % 11)) % 11
            check_digit_str = 'X' if check_digit == 10 else str(check_digit)
            
            return isbn10_base + check_digit_str
        except (ValueError, IndexError):
            return None

    def _format_date(self, date_str: str) -> str:
        """Format publication date for display"""
        if not date_str:
            return "Coming Soon"
        
        try:
            # Handle MM/DD/YY format
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    month, day, year = parts
                    # Assume 20xx for 2-digit years
                    if len(year) == 2:
                        year = f"20{year}"
                    date_obj = datetime(int(year), int(month), int(day))
                    return date_obj.strftime("%B %d, %Y")
        except (ValueError, IndexError):
            pass
        
        return date_str
    
    def _format_annotation_as_html(self, annotation: str) -> str:
        """Convert annotation to HTML paragraphs"""
        paragraphs = [p.strip() for p in annotation.split('\n\n') if p.strip()]
        html_paragraphs = [f"<p>{p}</p>" for p in paragraphs]
        return '\n\n'.join(html_paragraphs)
    
    def _extract_dichotomy(self, title: str) -> str:
        """Extract the vs/versus dichotomy from title"""
        if ':' in title and ('vs.' in title.lower() or 'versus' in title.lower()):
            after_colon = title.split(':', 1)[1].strip()
            # Replace vs./versus with "and" for better flow
            dichotomy = re.sub(r'\s+(vs\.?|versus)\s+', ' and ', after_colon, flags=re.IGNORECASE)
            return dichotomy.lower()
        return "competing perspectives"
    
    def get_book_by_title(self, title: str) -> Optional[BookData]:
        """Find book by exact title match"""
        for book in self.books:
            if book.title == title:
                return book
        return None
    
    def get_books_by_keyword(self, keyword: str) -> List[BookData]:
        """Find books containing keyword in title, keywords, or description"""
        keyword_lower = keyword.lower()
        matching_books = []
        
        for book in self.books:
            if (keyword_lower in book.title.lower() or 
                keyword_lower in book.keywords.lower() or 
                keyword_lower in book.short_description.lower()):
                matching_books.append(book)
        
        return matching_books
    
    def save_post(self, html_content: str, filename: str, output_dir: str = "marketing/posts"):
        """Save HTML content to file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        file_path = output_path / f"{filename}.html"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return file_path


def main():
    """Example usage"""
    # Initialize generator with CSV file
    generator = SubstackPostGenerator("ftp2lsi/csv/xynapse_traces_tranche1_processed.csv")
    
    # Generate post for first book
    if generator.books:
        first_book = generator.books[0]
        post_html = generator.generate_individual_post(first_book)
        
        # Save to file
        safe_filename = re.sub(r'[^\w\s-]', '', first_book.title).replace(' ', '_').lower()
        generator.save_post(post_html, f"book_{safe_filename}")
        
        print(f"Generated post for: {first_book.title}")
        print(f"Saved as: book_{safe_filename}.html")


if __name__ == "__main__":
    main()