"""
Marketing Manager for Stage 5 pipeline integration
Coordinates marketing material generation across different formats
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime

from .substack_post_generator import SubstackPostGenerator

logger = logging.getLogger(__name__)


class MarketingManager:
    """Manages marketing material generation for books"""
    
    def __init__(self, output_dir: str = "marketing/generated"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Track generated materials
        self.generated_materials: Dict[str, List[str]] = {}
    
    def generate_marketing_materials(self, catalog_path: str, imprint: str, 
                                   formats: List[str]) -> Dict[str, any]:
        """
        Generate marketing materials for all books in a catalog
        
        Args:
            catalog_path: Path to book catalog CSV
            imprint: Imprint name  
            formats: List of formats to generate (substack, press_release, social_media)
            
        Returns:
            Dictionary with generation results
        """
        results = {
            'imprint': imprint,
            'total_books': 0,
            'generated_materials': {},
            'errors': [],
            'output_directory': str(self.output_dir / imprint)
        }
        
        try:
            # Create imprint-specific directory
            imprint_dir = self.output_dir / imprint
            imprint_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate materials by format
            for format_type in formats:
                format_results = self._generate_format(catalog_path, imprint, format_type, imprint_dir)
                results['generated_materials'][format_type] = format_results
                
                if format_results.get('success', False):
                    self.logger.info(f"✅ Generated {format_type} materials for {imprint}")
                else:
                    self.logger.error(f"❌ Failed to generate {format_type} materials for {imprint}")
                    results['errors'].append(f"{format_type}: {format_results.get('error', 'Unknown error')}")
            
            # Count total books processed
            if results['generated_materials']:
                first_format = list(results['generated_materials'].values())[0]
                results['total_books'] = first_format.get('book_count', 0)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error generating marketing materials: {e}")
            results['errors'].append(f"General error: {str(e)}")
            return results
    
    def _generate_format(self, catalog_path: str, imprint: str, format_type: str, 
                        output_dir: Path) -> Dict[str, any]:
        """Generate marketing materials for a specific format"""
        
        if format_type == 'substack':
            return self._generate_substack_posts(catalog_path, imprint, output_dir)
        elif format_type == 'press_release':
            return self._generate_press_releases(catalog_path, imprint, output_dir)
        elif format_type == 'social_media':
            return self._generate_social_media_posts(catalog_path, imprint, output_dir)
        else:
            return {
                'success': False,
                'error': f"Unknown format type: {format_type}"
            }
    
    def _generate_substack_posts(self, catalog_path: str, imprint: str, 
                               output_dir: Path) -> Dict[str, any]:
        """Generate Substack posts for all books"""
        try:
            substack_dir = output_dir / 'substack_posts'
            substack_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize generator
            generator = SubstackPostGenerator(catalog_path)
            
            if not generator.books:
                return {
                    'success': False,
                    'error': 'No books found in catalog',
                    'book_count': 0
                }
            
            # Generate posts for all books
            generated_count = 0
            failed_books = []
            
            for book in generator.books:
                try:
                    # Generate individual post
                    post_html = generator.generate_individual_post(book)
                    
                    # Create safe filename
                    import re
                    safe_filename = re.sub(r'[^\w\s-]', '', book.title).replace(' ', '_').lower()
                    
                    # Save post
                    file_path = substack_dir / f'{safe_filename}.html'
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(post_html)
                    
                    generated_count += 1
                    
                except Exception as e:
                    failed_books.append(f"{book.title}: {str(e)}")
            
            # Create index file
            self._create_substack_index(generator.books, substack_dir)
            
            return {
                'success': True,
                'book_count': len(generator.books),
                'generated_count': generated_count,
                'failed_count': len(failed_books),
                'failed_books': failed_books,
                'output_directory': str(substack_dir)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'book_count': 0
            }
    
    def _generate_press_releases(self, catalog_path: str, imprint: str, 
                               output_dir: Path) -> Dict[str, any]:
        """Generate press releases (placeholder for future implementation)"""
        try:
            press_dir = output_dir / 'press_releases'
            press_dir.mkdir(parents=True, exist_ok=True)
            
            # Load catalog to count books
            import pandas as pd
            df = pd.read_csv(catalog_path)
            
            # Create imprint announcement press release
            press_release_content = self._create_imprint_press_release(imprint, len(df))
            
            # Save press release
            press_file = press_dir / f'{imprint}_launch_announcement.txt'
            with open(press_file, 'w', encoding='utf-8') as f:
                f.write(press_release_content)
            
            return {
                'success': True,
                'book_count': len(df),
                'generated_count': 1,
                'output_directory': str(press_dir)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'book_count': 0
            }
    
    def _generate_social_media_posts(self, catalog_path: str, imprint: str, 
                                   output_dir: Path) -> Dict[str, any]:
        """Generate social media posts (placeholder for future implementation)"""
        try:
            social_dir = output_dir / 'social_media'
            social_dir.mkdir(parents=True, exist_ok=True)
            
            # Load catalog
            import pandas as pd
            df = pd.read_csv(catalog_path)
            
            # Generate basic social media templates
            templates = {
                'twitter_launch.txt': f"🚀 Excited to announce our new {imprint} imprint! {len(df)} books exploring the frontiers of human knowledge through transcriptive meditation. #Publishing #AI #Meditation",
                'linkedin_post.txt': f"We're proud to introduce {imprint}, our latest publishing imprint featuring {len(df)} thought-provoking titles designed for contemplative minds. Each book offers a unique approach to learning through the Korean practice of 필사 (pilsa) - transcriptive meditation.",
                'facebook_announcement.txt': f"📚 Big news! We're launching {imprint}, a new imprint focused on transcriptive meditation books. Discover {len(df)} titles that transform reading into a contemplative practice, helping you engage deeply with the most pressing questions of our time."
            }
            
            for filename, content in templates.items():
                file_path = social_dir / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return {
                'success': True,
                'book_count': len(df),
                'generated_count': len(templates),
                'output_directory': str(social_dir)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'book_count': 0
            }
    
    def _create_substack_index(self, books, output_dir: Path):
        """Create HTML index file for Substack posts"""
        index_content = f"""<h1>Substack Posts - Ready to Publish</h1>
<p><strong>Total Posts:</strong> {len(books)}</p>
<p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

<h2>All Posts</h2>
<ul>
"""
        
        for book in books:
            import re
            safe_filename = re.sub(r'[^\w\s-]', '', book.title).replace(' ', '_').lower()
            index_content += f'<li><a href="{safe_filename}.html">{book.title}</a></li>\n'
        
        index_content += '</ul>'
        
        with open(output_dir / 'index.html', 'w', encoding='utf-8') as f:
            f.write(index_content)
    
    def _create_imprint_press_release(self, imprint: str, book_count: int) -> str:
        """Create press release for imprint launch"""
        
        current_date = datetime.now().strftime('%B %d, %Y')
        
        return f"""FOR IMMEDIATE RELEASE

Nimble Books LLC Launches {imprint.title()} Imprint: Revolutionary Publishing for the AI Age

New imprint combines ancient Korean meditation practice with cutting-edge knowledge

{current_date} - Nimble Books LLC today announced the launch of {imprint}, a groundbreaking new imprint that reimagines how readers engage with complex ideas in our rapidly evolving technological landscape.

The {imprint} imprint introduces {book_count} inaugural titles that merge the traditional Korean practice of 필사 (pilsa) - transcriptive meditation - with contemporary explorations of artificial intelligence, space exploration, ethics, and human enhancement. Each book is designed not just for reading, but for active contemplation through hand transcription.

"In an age of information overload and surface-level consumption, we're returning to one of humanity's most powerful learning tools: the deliberate act of writing," said the publishing team at Nimble Books LLC. "By combining this ancient practice with cutting-edge content, we're creating a new category of contemplative literature."

Key features of the {imprint} series include:

• Carefully curated quotations from leading thinkers and researchers
• Transcription-optimized format with dedicated writing spaces  
• Balanced exploration of contemporary debates and dichotomies
• Integration of mindfulness practices with intellectual engagement
• Professional fact-checking and academic-level bibliographies

The inaugural collection explores critical questions such as "AI Governance: Freedom vs. Constraint," "Advanced Propulsion: Fast vs. Safe," and "Brain Plasticity: Growth vs. Limits." Each title presents multiple perspectives on these defining challenges, encouraging readers to develop nuanced understanding through contemplative practice.

"We're not just publishing books; we're creating tools for contemplative learning," the team noted. "In a time when many seek quick answers to complex questions, {imprint} offers a different path: slow, deliberate engagement with the ideas that will shape our future."

The {imprint} titles are available through major book retailers and Lightning Source distribution network worldwide.

About Nimble Books LLC
Nimble Books LLC is a pioneering AI-assisted publishing company focused on innovative approaches to knowledge dissemination. The company specializes in creating thoughtful, research-based publications that bridge technology and human understanding.

Contact:
Nimble Books LLC
Email: info@nimblebooks.com
Web: www.nimblebooks.com

###

<END OF PRESS RELEASE>
"""
    
    def generate_campaign_summary(self, results: Dict[str, any]) -> str:
        """Generate summary report of marketing campaign generation"""
        
        summary = f"""
# Marketing Campaign Generation Summary

**Imprint:** {results['imprint']}
**Total Books:** {results['total_books']}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Output Directory:** {results['output_directory']}

## Materials Generated:
"""
        
        for format_type, format_results in results['generated_materials'].items():
            status = "✅" if format_results.get('success', False) else "❌"
            summary += f"- **{format_type.title()}:** {status} "
            
            if format_results.get('success', False):
                count = format_results.get('generated_count', 0)
                summary += f"({count} items generated)\n"
            else:
                error = format_results.get('error', 'Unknown error')
                summary += f"(Failed: {error})\n"
        
        if results.get('errors'):
            summary += f"\n## Errors:\n"
            for error in results['errors']:
                summary += f"- {error}\n"
        
        return summary