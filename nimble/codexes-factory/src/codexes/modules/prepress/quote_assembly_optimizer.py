"""
Quote assembly optimizer to prevent excessive author repetition.
"""

from typing import Dict, List, Any, Optional
import logging
from collections import Counter

logger = logging.getLogger(__name__)


class QuoteAssemblyOptimizer:
    """Optimize quote ordering to avoid excessive author repetition"""
    
    def __init__(self, max_consecutive_author: int = 3):
        self.max_consecutive = max_consecutive_author
    
    def optimize_quote_order(self, quotes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reorder quotes to minimize author repetition while maintaining coherence"""
        try:
            if len(quotes) <= self.max_consecutive:
                return quotes
            
            # First, check if optimization is needed
            if self.validate_author_distribution(quotes):
                return quotes
            
            # Reorder quotes to improve distribution
            optimized_quotes = self.reorder_quotes_by_author(quotes)
            
            # Validate the result
            if self.validate_author_distribution(optimized_quotes):
                logger.info("Quote order optimization successful")
                return optimized_quotes
            else:
                logger.warning("Quote optimization did not fully resolve author repetition")
                return optimized_quotes  # Return best attempt
                
        except Exception as e:
            logger.error(f"Error optimizing quote order: {e}")
            return quotes  # Return original on error
    
    def check_author_distribution(self, quotes: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze author distribution in quote sequence"""
        try:
            author_stats = {
                'total_authors': 0,
                'max_consecutive': 0,
                'violations': 0,
                'author_counts': {}
            }
            
            if not quotes:
                return author_stats
            
            # Count authors
            authors = [quote.get('author', 'Unknown') for quote in quotes]
            author_counts = Counter(authors)
            author_stats['author_counts'] = dict(author_counts)
            author_stats['total_authors'] = len(author_counts)
            
            # Check for consecutive repetitions
            current_author = None
            consecutive_count = 0
            max_consecutive = 0
            violations = 0
            
            for quote in quotes:
                author = quote.get('author', 'Unknown')
                
                if author == current_author:
                    consecutive_count += 1
                else:
                    if consecutive_count > max_consecutive:
                        max_consecutive = consecutive_count
                    if consecutive_count > self.max_consecutive:
                        violations += 1
                    
                    current_author = author
                    consecutive_count = 1
            
            # Check final sequence
            if consecutive_count > max_consecutive:
                max_consecutive = consecutive_count
            if consecutive_count > self.max_consecutive:
                violations += 1
            
            author_stats['max_consecutive'] = max_consecutive
            author_stats['violations'] = violations
            
            return author_stats
            
        except Exception as e:
            logger.error(f"Error checking author distribution: {e}")
            return {}
    
    def reorder_quotes_by_author(self, quotes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reorder quotes to improve author variety"""
        try:
            if len(quotes) <= 1:
                return quotes
            
            # Group quotes by author
            author_groups = {}
            for quote in quotes:
                author = quote.get('author', 'Unknown')
                if author not in author_groups:
                    author_groups[author] = []
                author_groups[author].append(quote)
            
            # If only one author, can't optimize
            if len(author_groups) == 1:
                return quotes
            
            # Distribute quotes to minimize consecutive repetition
            optimized_quotes = []
            author_queues = {author: quotes_list.copy() for author, quotes_list in author_groups.items()}
            
            last_author = None
            consecutive_count = 0
            
            while any(author_queues.values()):
                # Find best next author
                next_author = self._select_next_author(
                    author_queues, last_author, consecutive_count
                )
                
                if next_author and author_queues[next_author]:
                    # Add quote from selected author
                    quote = author_queues[next_author].pop(0)
                    optimized_quotes.append(quote)
                    
                    # Update tracking
                    if next_author == last_author:
                        consecutive_count += 1
                    else:
                        consecutive_count = 1
                    last_author = next_author
                else:
                    # Fallback: take from any available author
                    for author, queue in author_queues.items():
                        if queue:
                            quote = queue.pop(0)
                            optimized_quotes.append(quote)
                            last_author = author
                            consecutive_count = 1 if author != last_author else consecutive_count + 1
                            break
            
            return optimized_quotes
            
        except Exception as e:
            logger.error(f"Error reordering quotes by author: {e}")
            return quotes
    
    def _select_next_author(self, author_queues: Dict[str, List], last_author: Optional[str], consecutive_count: int) -> Optional[str]:
        """Select the best next author to minimize repetition"""
        try:
            available_authors = [author for author, queue in author_queues.items() if queue]
            
            if not available_authors:
                return None
            
            # If we haven't exceeded the limit, same author is okay
            if last_author and consecutive_count < self.max_consecutive and last_author in available_authors:
                # But prefer different author if available
                other_authors = [a for a in available_authors if a != last_author]
                if other_authors:
                    # Select author with most remaining quotes
                    return max(other_authors, key=lambda a: len(author_queues[a]))
                else:
                    return last_author
            
            # Must choose different author
            if last_author:
                different_authors = [a for a in available_authors if a != last_author]
                if different_authors:
                    # Select author with most remaining quotes
                    return max(different_authors, key=lambda a: len(author_queues[a]))
            
            # Fallback: select any available author
            return max(available_authors, key=lambda a: len(author_queues[a]))
            
        except Exception as e:
            logger.error(f"Error selecting next author: {e}")
            return available_authors[0] if available_authors else None
    
    def validate_author_distribution(self, quotes: List[Dict[str, Any]]) -> bool:
        """Validate that no author appears more than 3 times consecutively"""
        try:
            if not quotes:
                return True
            
            current_author = None
            consecutive_count = 0
            
            for quote in quotes:
                author = quote.get('author', 'Unknown')
                
                if author == current_author:
                    consecutive_count += 1
                    if consecutive_count > self.max_consecutive:
                        return False
                else:
                    current_author = author
                    consecutive_count = 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating author distribution: {e}")
            return False
    
    def get_optimization_report(self, original_quotes: List[Dict[str, Any]], optimized_quotes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate report comparing original and optimized quote distributions"""
        try:
            original_stats = self.check_author_distribution(original_quotes)
            optimized_stats = self.check_author_distribution(optimized_quotes)
            
            return {
                'original': original_stats,
                'optimized': optimized_stats,
                'improvement': {
                    'max_consecutive_reduced': original_stats.get('max_consecutive', 0) - optimized_stats.get('max_consecutive', 0),
                    'violations_reduced': original_stats.get('violations', 0) - optimized_stats.get('violations', 0),
                    'optimization_successful': optimized_stats.get('violations', 0) == 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating optimization report: {e}")
            return {}