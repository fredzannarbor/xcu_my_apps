"""
Quote Assembly Optimizer - Optimize quote ordering to avoid excessive author repetition
"""

import logging
import random
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QuoteAnalysis:
    """Analysis of quote distribution and author patterns"""
    total_quotes: int
    unique_authors: int
    author_counts: Dict[str, int]
    max_consecutive: int
    consecutive_violations: List[Tuple[int, str, int]]  # (start_index, author, count)
    distribution_score: float  # 0-1, higher is better
    thematic_coherence_score: float  # 0-1, higher is better

class QuoteAssemblyOptimizer:
    """Optimize quote ordering to minimize author repetition while maintaining coherence"""
    
    def __init__(self, max_consecutive_author: int = 3):
        self.max_consecutive = max_consecutive_author
        self.thematic_keywords = self._initialize_thematic_keywords()
        self.optimization_strategies = [
            self._strategy_round_robin,
            self._strategy_weighted_shuffle,
            self._strategy_thematic_grouping,
            self._strategy_author_spacing
        ]
    
    def _initialize_thematic_keywords(self) -> Dict[str, List[str]]:
        """Initialize thematic keyword groups for coherence analysis"""
        return {
            'leadership': ['leader', 'leadership', 'manage', 'guide', 'direct', 'inspire'],
            'wisdom': ['wisdom', 'wise', 'knowledge', 'insight', 'understanding', 'learn'],
            'success': ['success', 'achieve', 'accomplish', 'goal', 'victory', 'triumph'],
            'perseverance': ['persist', 'endure', 'overcome', 'struggle', 'challenge', 'resilience'],
            'creativity': ['create', 'innovate', 'imagine', 'original', 'artistic', 'invention'],
            'relationships': ['friend', 'love', 'family', 'relationship', 'connect', 'community'],
            'growth': ['grow', 'develop', 'improve', 'progress', 'evolve', 'advance'],
            'courage': ['courage', 'brave', 'bold', 'fearless', 'daring', 'heroic']
        }
    
    def optimize_quote_order(self, quotes: List[Dict]) -> List[Dict]:
        """Reorder quotes to minimize author repetition while maintaining coherence"""
        try:
            if not quotes:
                return quotes
            
            logger.info(f"Optimizing order for {len(quotes)} quotes")
            
            # Analyze current distribution
            initial_analysis = self.check_author_distribution(quotes)
            logger.info(f"Initial analysis: {initial_analysis.consecutive_violations} violations")
            
            # If no violations, return original order
            if not initial_analysis.consecutive_violations:
                logger.info("No author repetition violations found, keeping original order")
                return quotes
            
            # Try different optimization strategies
            best_quotes = quotes.copy()
            best_score = initial_analysis.distribution_score
            
            for strategy in self.optimization_strategies:
                try:
                    optimized_quotes = strategy(quotes.copy())
                    analysis = self.check_author_distribution(optimized_quotes)
                    
                    # Calculate combined score (distribution + coherence)
                    combined_score = (analysis.distribution_score * 0.7 + 
                                    analysis.thematic_coherence_score * 0.3)
                    
                    if combined_score > best_score:
                        best_quotes = optimized_quotes
                        best_score = combined_score
                        logger.info(f"Strategy {strategy.__name__} improved score to {combined_score:.3f}")
                
                except Exception as e:
                    logger.warning(f"Strategy {strategy.__name__} failed: {e}")
                    continue
            
            # Final validation
            final_analysis = self.check_author_distribution(best_quotes)
            logger.info(f"Final optimization: {len(final_analysis.consecutive_violations)} violations, "
                       f"score: {final_analysis.distribution_score:.3f}")
            
            return best_quotes
            
        except Exception as e:
            logger.error(f"Error optimizing quote order: {e}")
            return quotes
    
    def _strategy_round_robin(self, quotes: List[Dict]) -> List[Dict]:
        """Round-robin strategy: cycle through authors"""
        try:
            # Group quotes by author
            author_groups = defaultdict(list)
            for quote in quotes:
                author = quote.get('author', 'Unknown')
                author_groups[author].append(quote)
            
            # Create round-robin ordering
            optimized = []
            authors = list(author_groups.keys())
            max_quotes_per_author = max(len(group) for group in author_groups.values())
            
            for round_num in range(max_quotes_per_author):
                for author in authors:
                    if round_num < len(author_groups[author]):
                        optimized.append(author_groups[author][round_num])
            
            return optimized
            
        except Exception as e:
            logger.error(f"Error in round-robin strategy: {e}")
            return quotes
    
    def _strategy_weighted_shuffle(self, quotes: List[Dict]) -> List[Dict]:
        """Weighted shuffle: randomly distribute while avoiding consecutive authors"""
        try:
            optimized = []
            remaining = quotes.copy()
            
            while remaining:
                # Get last author to avoid repetition
                last_author = optimized[-1].get('author', '') if optimized else ''
                
                # Filter out quotes from last author if possible
                available = [q for q in remaining if q.get('author', '') != last_author]
                
                # If no alternatives, use any remaining quote
                if not available:
                    available = remaining
                
                # Randomly select from available quotes
                selected = random.choice(available)
                optimized.append(selected)
                remaining.remove(selected)
            
            return optimized
            
        except Exception as e:
            logger.error(f"Error in weighted shuffle strategy: {e}")
            return quotes
    
    def _strategy_thematic_grouping(self, quotes: List[Dict]) -> List[Dict]:
        """Thematic grouping: group by theme while distributing authors"""
        try:
            # Analyze themes for each quote
            quote_themes = []
            for quote in quotes:
                themes = self._analyze_quote_themes(quote)
                quote_themes.append((quote, themes))
            
            # Group by primary theme
            theme_groups = defaultdict(list)
            for quote, themes in quote_themes:
                primary_theme = themes[0] if themes else 'general'
                theme_groups[primary_theme].append(quote)
            
            # Optimize within each theme group
            optimized = []
            for theme, theme_quotes in theme_groups.items():
                if len(theme_quotes) > 1:
                    # Apply author distribution within theme
                    theme_optimized = self._distribute_authors_in_group(theme_quotes)
                    optimized.extend(theme_optimized)
                else:
                    optimized.extend(theme_quotes)
            
            return optimized
            
        except Exception as e:
            logger.error(f"Error in thematic grouping strategy: {e}")
            return quotes
    
    def _strategy_author_spacing(self, quotes: List[Dict]) -> List[Dict]:
        """Author spacing: ensure minimum distance between same authors"""
        try:
            optimized = []
            remaining = quotes.copy()
            author_last_position = {}
            
            while remaining:
                best_quote = None
                best_score = -1
                
                for quote in remaining:
                    author = quote.get('author', 'Unknown')
                    current_position = len(optimized)
                    
                    # Calculate spacing score
                    if author in author_last_position:
                        distance = current_position - author_last_position[author]
                        spacing_score = min(distance / 3.0, 1.0)  # Prefer distance of 3+
                    else:
                        spacing_score = 1.0  # New author gets highest score
                    
                    if spacing_score > best_score:
                        best_score = spacing_score
                        best_quote = quote
                
                if best_quote:
                    optimized.append(best_quote)
                    remaining.remove(best_quote)
                    author_last_position[best_quote.get('author', 'Unknown')] = len(optimized) - 1
            
            return optimized
            
        except Exception as e:
            logger.error(f"Error in author spacing strategy: {e}")
            return quotes
    
    def _distribute_authors_in_group(self, quotes: List[Dict]) -> List[Dict]:
        """Distribute authors within a group of quotes"""
        try:
            if len(quotes) <= 1:
                return quotes
            
            # Group by author
            author_groups = defaultdict(list)
            for quote in quotes:
                author = quote.get('author', 'Unknown')
                author_groups[author].append(quote)
            
            # If only one author, return as-is
            if len(author_groups) == 1:
                return quotes
            
            # Distribute using round-robin within group
            distributed = []
            authors = list(author_groups.keys())
            max_per_author = max(len(group) for group in author_groups.values())
            
            for round_num in range(max_per_author):
                for author in authors:
                    if round_num < len(author_groups[author]):
                        distributed.append(author_groups[author][round_num])
            
            return distributed
            
        except Exception as e:
            logger.error(f"Error distributing authors in group: {e}")
            return quotes
    
    def _analyze_quote_themes(self, quote: Dict) -> List[str]:
        """Analyze themes in a quote"""
        try:
            quote_text = quote.get('quote', '').lower()
            source = quote.get('source', '').lower()
            combined_text = f"{quote_text} {source}"
            
            themes = []
            for theme, keywords in self.thematic_keywords.items():
                if any(keyword in combined_text for keyword in keywords):
                    themes.append(theme)
            
            return themes if themes else ['general']
            
        except Exception as e:
            logger.error(f"Error analyzing quote themes: {e}")
            return ['general']
    
    def check_author_distribution(self, quotes: List[Dict]) -> QuoteAnalysis:
        """Analyze author distribution in quote sequence"""
        try:
            if not quotes:
                return QuoteAnalysis(0, 0, {}, 0, [], 0.0, 0.0)
            
            # Count authors
            author_counts = Counter(quote.get('author', 'Unknown') for quote in quotes)
            
            # Find consecutive author violations
            consecutive_violations = []
            current_author = None
            current_count = 0
            start_index = 0
            
            for i, quote in enumerate(quotes):
                author = quote.get('author', 'Unknown')
                
                if author == current_author:
                    current_count += 1
                else:
                    # Check if previous sequence was a violation
                    if current_count > self.max_consecutive:
                        consecutive_violations.append((start_index, current_author, current_count))
                    
                    # Start new sequence
                    current_author = author
                    current_count = 1
                    start_index = i
            
            # Check final sequence
            if current_count > self.max_consecutive:
                consecutive_violations.append((start_index, current_author, current_count))
            
            # Calculate distribution score
            max_consecutive = max(current_count, max((v[2] for v in consecutive_violations), default=0))
            distribution_score = max(0.0, 1.0 - (max_consecutive - self.max_consecutive) / len(quotes))
            
            # Calculate thematic coherence score
            coherence_score = self._calculate_thematic_coherence(quotes)
            
            return QuoteAnalysis(
                total_quotes=len(quotes),
                unique_authors=len(author_counts),
                author_counts=dict(author_counts),
                max_consecutive=max_consecutive,
                consecutive_violations=consecutive_violations,
                distribution_score=distribution_score,
                thematic_coherence_score=coherence_score
            )
            
        except Exception as e:
            logger.error(f"Error checking author distribution: {e}")
            return QuoteAnalysis(0, 0, {}, 0, [], 0.0, 0.0)
    
    def _calculate_thematic_coherence(self, quotes: List[Dict]) -> float:
        """Calculate thematic coherence score for quote sequence"""
        try:
            if len(quotes) < 2:
                return 1.0
            
            coherence_scores = []
            
            for i in range(len(quotes) - 1):
                current_themes = set(self._analyze_quote_themes(quotes[i]))
                next_themes = set(self._analyze_quote_themes(quotes[i + 1]))
                
                # Calculate theme overlap
                if current_themes and next_themes:
                    overlap = len(current_themes.intersection(next_themes))
                    total = len(current_themes.union(next_themes))
                    coherence = overlap / total if total > 0 else 0.0
                else:
                    coherence = 0.0
                
                coherence_scores.append(coherence)
            
            return sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating thematic coherence: {e}")
            return 0.0
    
    def reorder_quotes_by_author(self, quotes: List[Dict]) -> List[Dict]:
        """Reorder quotes to improve author variety (legacy method)"""
        return self.optimize_quote_order(quotes)
    
    def validate_author_distribution(self, quotes: List[Dict]) -> bool:
        """Validate that no author appears more than max_consecutive times consecutively"""
        try:
            analysis = self.check_author_distribution(quotes)
            return len(analysis.consecutive_violations) == 0
            
        except Exception as e:
            logger.error(f"Error validating author distribution: {e}")
            return False
    
    def get_optimization_report(self, original_quotes: List[Dict], 
                              optimized_quotes: List[Dict]) -> Dict[str, Any]:
        """Generate optimization report comparing original and optimized quotes"""
        try:
            original_analysis = self.check_author_distribution(original_quotes)
            optimized_analysis = self.check_author_distribution(optimized_quotes)
            
            return {
                'original': {
                    'violations': len(original_analysis.consecutive_violations),
                    'max_consecutive': original_analysis.max_consecutive,
                    'distribution_score': original_analysis.distribution_score,
                    'coherence_score': original_analysis.thematic_coherence_score
                },
                'optimized': {
                    'violations': len(optimized_analysis.consecutive_violations),
                    'max_consecutive': optimized_analysis.max_consecutive,
                    'distribution_score': optimized_analysis.distribution_score,
                    'coherence_score': optimized_analysis.thematic_coherence_score
                },
                'improvement': {
                    'violations_reduced': len(original_analysis.consecutive_violations) - len(optimized_analysis.consecutive_violations),
                    'distribution_improved': optimized_analysis.distribution_score - original_analysis.distribution_score,
                    'coherence_change': optimized_analysis.thematic_coherence_score - original_analysis.thematic_coherence_score
                },
                'summary': {
                    'total_quotes': len(original_quotes),
                    'unique_authors': original_analysis.unique_authors,
                    'max_consecutive_allowed': self.max_consecutive,
                    'optimization_successful': len(optimized_analysis.consecutive_violations) < len(original_analysis.consecutive_violations)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating optimization report: {e}")
            return {'error': str(e)}
    
    def get_author_statistics(self, quotes: List[Dict]) -> Dict[str, Any]:
        """Get detailed author statistics"""
        try:
            analysis = self.check_author_distribution(quotes)
            
            # Calculate author distribution metrics
            author_counts = analysis.author_counts
            total_quotes = analysis.total_quotes
            
            # Find most and least quoted authors
            most_quoted = max(author_counts.items(), key=lambda x: x[1]) if author_counts else ('None', 0)
            least_quoted = min(author_counts.items(), key=lambda x: x[1]) if author_counts else ('None', 0)
            
            # Calculate distribution evenness (Gini coefficient approximation)
            if len(author_counts) > 1:
                sorted_counts = sorted(author_counts.values())
                n = len(sorted_counts)
                cumsum = sum((i + 1) * count for i, count in enumerate(sorted_counts))
                evenness = 1 - (2 * cumsum) / (n * sum(sorted_counts)) + (n + 1) / n
            else:
                evenness = 1.0
            
            return {
                'total_quotes': total_quotes,
                'unique_authors': analysis.unique_authors,
                'author_counts': author_counts,
                'most_quoted': {'author': most_quoted[0], 'count': most_quoted[1]},
                'least_quoted': {'author': least_quoted[0], 'count': least_quoted[1]},
                'average_quotes_per_author': total_quotes / analysis.unique_authors if analysis.unique_authors > 0 else 0,
                'distribution_evenness': evenness,
                'consecutive_violations': analysis.consecutive_violations,
                'max_consecutive_found': analysis.max_consecutive,
                'max_consecutive_allowed': self.max_consecutive,
                'distribution_score': analysis.distribution_score
            }
            
        except Exception as e:
            logger.error(f"Error getting author statistics: {e}")
            return {'error': str(e)}