"""
Storefront metadata manager with accurate author information from tranche config.
"""

from typing import Dict, List, Any, Optional
import logging
import json
import os

logger = logging.getLogger(__name__)


class StorefrontMetadataManager:
    """Manage storefront metadata with accurate author information from tranche config"""
    
    def __init__(self, config_loader=None):
        self.config_loader = config_loader
    
    def extract_author_from_tranche(self, tranche_name: str) -> Dict[str, str]:
        """Extract Contributor One name from tranche configuration"""
        try:
            # Load tranche configuration
            tranche_config_path = f"configs/tranches/{tranche_name}.json"
            
            if not os.path.exists(tranche_config_path):
                logger.error(f"Tranche config not found: {tranche_config_path}")
                return {'error': 'Tranche configuration not found'}
            
            with open(tranche_config_path, 'r', encoding='utf-8') as f:
                tranche_config = json.load(f)
            
            # Extract author information
            contributor_one = tranche_config.get('contributor_one', '')
            
            if not contributor_one:
                logger.warning(f"No contributor_one found in tranche config: {tranche_name}")
                return {'error': 'No author information in tranche config'}
            
            return {
                'contributor_one_name': contributor_one,
                'storefront_author_en': contributor_one,
                'storefront_author_ko': tranche_config.get('contributor_one_ko', contributor_one),
                'source': 'tranche_config'
            }
            
        except Exception as e:
            logger.error(f"Error extracting author from tranche {tranche_name}: {e}")
            return {'error': f'Failed to extract author: {e}'}
    
    def generate_storefront_metadata(self, book_metadata: Dict[str, Any], tranche_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete storefront metadata with accurate author information"""
        try:
            # Extract author from tranche config
            author_info = self.extract_author_from_tranche(tranche_config.get('name', ''))
            
            if 'error' in author_info:
                # Fallback to tranche config directly
                contributor_one = tranche_config.get('contributor_one', 'Unknown Author')
                author_info = {
                    'contributor_one_name': contributor_one,
                    'storefront_author_en': contributor_one,
                    'storefront_author_ko': tranche_config.get('contributor_one_ko', contributor_one),
                    'source': 'tranche_config_direct'
                }
            
            # Generate complete storefront metadata
            storefront_metadata = {
                # Basic book information
                'title': book_metadata.get('title', 'Untitled'),
                'title_ko': book_metadata.get('title_ko', ''),
                'subtitle': book_metadata.get('subtitle', ''),
                'subtitle_ko': book_metadata.get('subtitle_ko', ''),
                
                # Author information from tranche config
                'storefront_author_en': author_info['storefront_author_en'],
                'storefront_author_ko': author_info['storefront_author_ko'],
                'contributor_one_name': author_info['contributor_one_name'],
                'author_source': author_info['source'],
                
                # Publishing information
                'publisher': tranche_config.get('publisher', 'Unknown Publisher'),
                'imprint': tranche_config.get('imprint', 'Unknown Imprint'),
                'language': tranche_config.get('language', 'en'),
                
                # Book details
                'description': book_metadata.get('description', ''),
                'description_ko': book_metadata.get('description_ko', ''),
                'isbn': book_metadata.get('isbn', ''),
                'price': book_metadata.get('price', '0.00'),
                'currency': book_metadata.get('currency', 'USD'),
                'page_count': book_metadata.get('page_count', '0'),
                'publication_date': book_metadata.get('publication_date', ''),
                
                # Categories and tags
                'categories': book_metadata.get('categories', []),
                'tags': book_metadata.get('tags', []),
                'bisac_categories': book_metadata.get('bisac_categories', []),
                
                # Storefront specific
                'availability': 'available',
                'format': 'paperback',
                'metadata_consistency_validated': False
            }
            
            # Validate consistency
            storefront_metadata['metadata_consistency_validated'] = self.validate_author_consistency(
                {'contributor_one': author_info['contributor_one_name']},
                storefront_metadata
            )
            
            return storefront_metadata
            
        except Exception as e:
            logger.error(f"Error generating storefront metadata: {e}")
            return self._generate_fallback_metadata(book_metadata, tranche_config)
    
    def validate_author_consistency(self, lsi_data: Dict[str, Any], storefront_data: Dict[str, Any]) -> bool:
        """Validate author consistency between LSI CSV and storefront data"""
        try:
            lsi_author = lsi_data.get('contributor_one', '').strip()
            storefront_author_en = storefront_data.get('storefront_author_en', '').strip()
            contributor_one_name = storefront_data.get('contributor_one_name', '').strip()
            
            # Check if all author fields match
            authors_match = (
                lsi_author == storefront_author_en == contributor_one_name
                and lsi_author != ''
            )
            
            if not authors_match:
                logger.warning(f"Author inconsistency detected:")
                logger.warning(f"  LSI: '{lsi_author}'")
                logger.warning(f"  Storefront EN: '{storefront_author_en}'")
                logger.warning(f"  Contributor One: '{contributor_one_name}'")
            
            return authors_match
            
        except Exception as e:
            logger.error(f"Error validating author consistency: {e}")
            return False
    
    def prevent_author_interpolation(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure author names are not interpolated by the model"""
        try:
            # Check for common interpolated author patterns
            interpolated_patterns = [
                r'Dr\.\s+\w+\s+\w+',  # Dr. First Last
                r'\w+\s+\w+,\s+Ph\.D\.',  # First Last, Ph.D.
                r'Professor\s+\w+',  # Professor Name
                r'\w+\s+\w+\s+\(Author\)',  # Name (Author)
            ]
            
            import re
            
            for field in ['storefront_author_en', 'storefront_author_ko', 'contributor_one_name']:
                if field in metadata:
                    author_name = metadata[field]
                    
                    # Check if author name matches interpolated patterns
                    for pattern in interpolated_patterns:
                        if re.match(pattern, author_name):
                            logger.warning(f"Possible interpolated author detected: {author_name}")
                            metadata[f'{field}_interpolation_warning'] = True
                            break
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error preventing author interpolation: {e}")
            return metadata
    
    def _generate_fallback_metadata(self, book_metadata: Dict[str, Any], tranche_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback metadata when main generation fails"""
        try:
            return {
                'title': book_metadata.get('title', 'Untitled'),
                'storefront_author_en': 'Unknown Author',
                'storefront_author_ko': '알 수 없는 저자',
                'contributor_one_name': 'Unknown Author',
                'author_source': 'fallback',
                'publisher': tranche_config.get('publisher', 'Unknown Publisher'),
                'imprint': tranche_config.get('imprint', 'Unknown Imprint'),
                'language': tranche_config.get('language', 'en'),
                'description': book_metadata.get('description', 'No description available'),
                'price': '0.00',
                'currency': 'USD',
                'availability': 'available',
                'metadata_consistency_validated': False,
                'generation_error': True
            }
        except Exception as e:
            logger.error(f"Error generating fallback metadata: {e}")
            return {'error': 'Complete metadata generation failure'}
    
    def update_existing_storefront_data(self, existing_data: Dict[str, Any], tranche_name: str) -> Dict[str, Any]:
        """Update existing storefront data with correct author information"""
        try:
            # Extract correct author from tranche
            author_info = self.extract_author_from_tranche(tranche_name)
            
            if 'error' not in author_info:
                # Update author fields
                existing_data.update({
                    'storefront_author_en': author_info['storefront_author_en'],
                    'storefront_author_ko': author_info['storefront_author_ko'],
                    'contributor_one_name': author_info['contributor_one_name'],
                    'author_source': author_info['source'],
                    'author_updated': True
                })
                
                logger.info(f"Updated storefront author information from tranche: {tranche_name}")
            
            return existing_data
            
        except Exception as e:
            logger.error(f"Error updating existing storefront data: {e}")
            return existing_data