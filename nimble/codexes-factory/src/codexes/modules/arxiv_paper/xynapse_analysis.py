"""
Xynapse Traces Book Catalog Analysis Tools

This module provides comprehensive analysis tools for the xynapse_traces imprint
book catalog, including statistical analysis, data visualization, and metrics
collection for the arXiv paper.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, List, Tuple, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XynapseTracesAnalyzer:
    """Comprehensive analysis tool for xynapse_traces book catalog."""
    
    def __init__(self, csv_path: str = "imprints/xynapse_traces/books.csv"):
        """Initialize analyzer with book catalog data."""
        self.csv_path = Path(csv_path)
        self.df = None
        self.analysis_results = {}
        self.load_data()
    
    def load_data(self) -> None:
        """Load and preprocess the book catalog data."""
        try:
            self.df = pd.read_csv(self.csv_path)
            logger.info(f"Loaded {len(self.df)} books from {self.csv_path}")
            
            # Clean and preprocess data
            self._preprocess_data()
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def _preprocess_data(self) -> None:
        """Clean and preprocess the loaded data."""
        # Convert publication_date to datetime
        self.df['publication_date'] = pd.to_datetime(self.df['publication_date'], format='%m/%d/%y')
        
        # Convert price to numeric, handling any string formatting
        self.df['price'] = pd.to_numeric(self.df['price'], errors='coerce')
        
        # Convert page_count to numeric
        self.df['page_count'] = pd.to_numeric(self.df['page_count'], errors='coerce')
        
        # Extract month and year for temporal analysis
        self.df['publication_month'] = self.df['publication_date'].dt.month
        self.df['publication_year'] = self.df['publication_date'].dt.year
        
        # Calculate title length for analysis
        self.df['title_length'] = self.df['title'].str.len()
        
        logger.info("Data preprocessing completed")
    
    def generate_basic_statistics(self) -> Dict:
        """Generate basic statistical overview of the catalog."""
        stats = {
            'total_books': len(self.df),
            'date_range': {
                'earliest': self.df['publication_date'].min().strftime('%Y-%m-%d'),
                'latest': self.df['publication_date'].max().strftime('%Y-%m-%d'),
                'span_days': (self.df['publication_date'].max() - self.df['publication_date'].min()).days
            },
            'page_count_stats': {
                'mean': float(self.df['page_count'].mean()),
                'median': float(self.df['page_count'].median()),
                'std': float(self.df['page_count'].std()),
                'min': int(self.df['page_count'].min()),
                'max': int(self.df['page_count'].max())
            },
            'pricing_stats': {
                'mean': float(self.df['price'].mean()),
                'median': float(self.df['price'].median()),
                'std': float(self.df['price'].std()),
                'min': float(self.df['price'].min()),
                'max': float(self.df['price'].max()),
                'unique_prices': len(self.df['price'].unique())
            },
            'title_analysis': {
                'avg_title_length': float(self.df['title_length'].mean()),
                'longest_title': self.df.loc[self.df['title_length'].idxmax(), 'title'],
                'shortest_title': self.df.loc[self.df['title_length'].idxmin(), 'title']
            }
        }
        
        self.analysis_results['basic_statistics'] = stats
        return stats
    
    def analyze_publication_timeline(self) -> Dict:
        """Analyze publication timeline and scheduling patterns."""
        # Group by month for timeline analysis
        monthly_counts = self.df.groupby(['publication_year', 'publication_month']).size()
        
        # Calculate publication frequency
        date_counts = self.df['publication_date'].value_counts().sort_index()
        
        # Convert tuple keys to strings for JSON serialization
        monthly_dist = {}
        for (year, month), count in monthly_counts.items():
            monthly_dist[f"{year}-{month:02d}"] = int(count)
        
        # Convert datetime keys to strings
        books_per_date = {}
        for date, count in date_counts.items():
            books_per_date[date.strftime('%Y-%m-%d')] = int(count)
        
        timeline_analysis = {
            'monthly_distribution': monthly_dist,
            'books_per_date': books_per_date,
            'publication_frequency': {
                'dates_with_releases': len(date_counts),
                'max_books_per_date': int(date_counts.max()),
                'avg_books_per_release_date': float(date_counts.mean())
            },
            'temporal_patterns': {
                'most_active_month': int(self.df['publication_month'].mode().iloc[0]),
                'publication_spread_weeks': len(self.df['publication_date'].dt.isocalendar().week.unique())
            }
        }
        
        self.analysis_results['timeline_analysis'] = timeline_analysis
        return timeline_analysis
    
    def analyze_content_patterns(self) -> Dict:
        """Analyze content patterns and themes."""
        # Analyze title patterns
        title_words = ' '.join(self.df['title'].fillna('')).lower().split()
        word_freq = pd.Series(title_words).value_counts().head(20)
        
        # Look for common themes in titles
        versus_books = self.df[self.df['title'].str.contains('versus', case=False, na=False)]
        colon_books = self.df[self.df['title'].str.contains(':', na=False)]
        
        content_analysis = {
            'title_patterns': {
                'books_with_versus': len(versus_books),
                'books_with_colons': len(colon_books),
                'common_title_words': word_freq.head(10).to_dict()
            },
            'author_analysis': {
                'unique_authors': len(self.df['author'].unique()),
                'author_distribution': self.df['author'].value_counts().to_dict()
            },
            'series_analysis': {
                'books_with_series': len(self.df[self.df['series_name'].notna()]),
                'unique_series': len(self.df['series_name'].dropna().unique()) if self.df['series_name'].notna().any() else 0
            }
        }
        
        self.analysis_results['content_analysis'] = content_analysis
        return content_analysis
    
    def generate_production_metrics(self) -> Dict:
        """Generate production-related metrics for the paper."""
        # Calculate production efficiency metrics
        total_pages = self.df['page_count'].sum()
        avg_production_time = self._estimate_production_time()
        
        production_metrics = {
            'volume_metrics': {
                'total_pages_produced': int(total_pages),
                'avg_pages_per_book': float(self.df['page_count'].mean()),
                'page_count_consistency': float(self.df['page_count'].std())
            },
            'standardization_metrics': {
                'price_standardization': len(self.df['price'].unique()) == 1,
                'page_count_standardization': len(self.df['page_count'].unique()) == 1,
                'format_consistency': self._analyze_format_consistency()
            },
            'estimated_metrics': {
                'estimated_production_days': avg_production_time,
                'books_per_week': len(self.df) / (avg_production_time / 7) if avg_production_time > 0 else 0
            }
        }
        
        self.analysis_results['production_metrics'] = production_metrics
        return production_metrics
    
    def _estimate_production_time(self) -> float:
        """Estimate total production time based on date range."""
        if len(self.df) > 1:
            date_range = (self.df['publication_date'].max() - self.df['publication_date'].min()).days
            return float(date_range)
        return 0.0
    
    def _analyze_format_consistency(self) -> Dict:
        """Analyze consistency in book formatting and structure."""
        return {
            'consistent_page_count': len(self.df['page_count'].unique()) <= 2,  # Allow for minor variations
            'consistent_pricing': len(self.df['price'].unique()) <= 2,
            'consistent_imprint': len(self.df['imprint'].unique()) == 1
        }
    
    def create_visualizations(self, output_dir: str = "output/arxiv_paper/visualizations") -> Dict[str, str]:
        """Create data visualizations for the paper."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        plt.style.use('seaborn-v0_8')
        visualization_files = {}
        
        # 1. Publication Timeline
        fig, ax = plt.subplots(figsize=(12, 6))
        publication_counts = self.df['publication_date'].value_counts().sort_index()
        publication_counts.plot(kind='bar', ax=ax)
        ax.set_title('Xynapse Traces Publication Timeline')
        ax.set_xlabel('Publication Date')
        ax.set_ylabel('Number of Books')
        plt.xticks(rotation=45)
        plt.tight_layout()
        timeline_file = output_path / 'publication_timeline.png'
        plt.savefig(timeline_file, dpi=300, bbox_inches='tight')
        plt.close()
        visualization_files['timeline'] = str(timeline_file)
        
        # 2. Price and Page Count Distribution
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Price distribution
        self.df['price'].hist(bins=10, ax=ax1)
        ax1.set_title('Price Distribution')
        ax1.set_xlabel('Price ($)')
        ax1.set_ylabel('Frequency')
        
        # Page count distribution
        self.df['page_count'].hist(bins=10, ax=ax2)
        ax2.set_title('Page Count Distribution')
        ax2.set_xlabel('Page Count')
        ax2.set_ylabel('Frequency')
        
        plt.tight_layout()
        distribution_file = output_path / 'price_page_distribution.png'
        plt.savefig(distribution_file, dpi=300, bbox_inches='tight')
        plt.close()
        visualization_files['distributions'] = str(distribution_file)
        
        # 3. Title Length Analysis
        fig, ax = plt.subplots(figsize=(10, 6))
        self.df['title_length'].hist(bins=15, ax=ax, alpha=0.7)
        ax.axvline(self.df['title_length'].mean(), color='red', linestyle='--', 
                  label=f'Mean: {self.df["title_length"].mean():.1f}')
        ax.set_title('Title Length Distribution')
        ax.set_xlabel('Title Length (characters)')
        ax.set_ylabel('Frequency')
        ax.legend()
        plt.tight_layout()
        title_length_file = output_path / 'title_length_distribution.png'
        plt.savefig(title_length_file, dpi=300, bbox_inches='tight')
        plt.close()
        visualization_files['title_length'] = str(title_length_file)
        
        logger.info(f"Created {len(visualization_files)} visualizations in {output_path}")
        return visualization_files
    
    def generate_comprehensive_report(self) -> Dict:
        """Generate a comprehensive analysis report."""
        logger.info("Generating comprehensive analysis report...")
        
        # Run all analyses
        basic_stats = self.generate_basic_statistics()
        timeline_analysis = self.analyze_publication_timeline()
        content_analysis = self.analyze_content_patterns()
        production_metrics = self.generate_production_metrics()
        
        # Create visualizations
        visualizations = self.create_visualizations()
        
        # Compile comprehensive report
        report = {
            'metadata': {
                'analysis_date': datetime.now().isoformat(),
                'catalog_file': str(self.csv_path),
                'total_books_analyzed': len(self.df)
            },
            'basic_statistics': basic_stats,
            'timeline_analysis': timeline_analysis,
            'content_analysis': content_analysis,
            'production_metrics': production_metrics,
            'visualizations': visualizations,
            'key_insights': self._generate_key_insights()
        }
        
        self.analysis_results = report
        return report
    
    def _generate_key_insights(self) -> List[str]:
        """Generate key insights from the analysis."""
        insights = []
        
        # Publication consistency
        if len(self.df['price'].unique()) == 1:
            insights.append(f"Consistent pricing strategy: all books priced at ${self.df['price'].iloc[0]}")
        
        if len(self.df['page_count'].unique()) == 1:
            insights.append(f"Standardized format: all books have {self.df['page_count'].iloc[0]} pages")
        
        # Timeline insights
        date_range = (self.df['publication_date'].max() - self.df['publication_date'].min()).days
        if date_range > 0:
            books_per_week = len(self.df) / (date_range / 7)
            insights.append(f"Production rate: approximately {books_per_week:.1f} books per week")
        
        # Content insights
        versus_count = len(self.df[self.df['title'].str.contains('versus', case=False, na=False)])
        if versus_count > len(self.df) * 0.5:
            insights.append(f"Thematic consistency: {versus_count} books ({versus_count/len(self.df)*100:.1f}%) use 'versus' format")
        
        return insights
    
    def save_report(self, output_file: str = "output/arxiv_paper/xynapse_analysis_report.json") -> None:
        """Save the analysis report to a JSON file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.analysis_results, f, indent=2, default=str)
        
        logger.info(f"Analysis report saved to {output_path}")
    
    def get_paper_ready_metrics(self) -> Dict:
        """Get metrics formatted for inclusion in the academic paper."""
        if not self.analysis_results:
            self.generate_comprehensive_report()
        
        paper_metrics = {
            'catalog_overview': {
                'total_books': self.analysis_results['basic_statistics']['total_books'],
                'publication_period': f"{self.analysis_results['basic_statistics']['date_range']['earliest']} to {self.analysis_results['basic_statistics']['date_range']['latest']}",
                'production_span_days': self.analysis_results['basic_statistics']['date_range']['span_days']
            },
            'standardization_evidence': {
                'uniform_pricing': f"${self.analysis_results['basic_statistics']['pricing_stats']['mean']:.2f}",
                'consistent_page_count': f"{self.analysis_results['basic_statistics']['page_count_stats']['mean']:.0f} pages",
                'format_consistency': self.analysis_results['production_metrics']['standardization_metrics']
            },
            'production_efficiency': {
                'total_pages_produced': self.analysis_results['production_metrics']['volume_metrics']['total_pages_produced'],
                'estimated_production_rate': f"{self.analysis_results['production_metrics']['estimated_metrics']['books_per_week']:.1f} books/week"
            },
            'thematic_analysis': {
                'versus_format_usage': f"{self.analysis_results['content_analysis']['title_patterns']['books_with_versus']} books",
                'title_structure_consistency': f"{self.analysis_results['content_analysis']['title_patterns']['books_with_colons']} books with structured titles"
            }
        }
        
        return paper_metrics


def main():
    """Main function to run the analysis."""
    analyzer = XynapseTracesAnalyzer()
    
    # Generate comprehensive report
    report = analyzer.generate_comprehensive_report()
    
    # Save report
    analyzer.save_report()
    
    # Print key metrics for paper
    paper_metrics = analyzer.get_paper_ready_metrics()
    print("\n=== XYNAPSE TRACES ANALYSIS SUMMARY ===")
    print(f"Total Books: {paper_metrics['catalog_overview']['total_books']}")
    print(f"Publication Period: {paper_metrics['catalog_overview']['publication_period']}")
    print(f"Uniform Pricing: {paper_metrics['standardization_evidence']['uniform_pricing']}")
    print(f"Standard Page Count: {paper_metrics['standardization_evidence']['consistent_page_count']}")
    print(f"Total Pages Produced: {paper_metrics['production_efficiency']['total_pages_produced']:,}")
    
    return report


if __name__ == "__main__":
    main()