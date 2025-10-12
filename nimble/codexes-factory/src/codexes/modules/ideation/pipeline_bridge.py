"""
Pipeline integration bridge for connecting ideation system to book production pipeline.
Handles format conversion and schedule integration.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from .book_idea import BookIdea
from ..metadata.metadata_models import CodexMetadata
from ..distribution.schedule_isbn_manager import ScheduleISBNManager

logger = logging.getLogger(__name__)


class IdeationPipelineBridge:
    """Bridges the ideation system with the existing book production pipeline."""
    
    def __init__(self, schedule_manager: Optional[ScheduleISBNManager] = None):
        self.schedule_manager = schedule_manager
        self.metadata_converter = MetadataConverter()
        self.logger = logging.getLogger(self.__class__.__name__)

    def convert_idea_to_metadata(self, idea: BookIdea, imprint: str, 
                               additional_metadata: Optional[Dict[str, Any]] = None) -> CodexMetadata:
        """Convert BookIdea to CodexMetadata format for pipeline integration."""
        return self.metadata_converter.convert_idea_to_metadata(idea, imprint, additional_metadata)

    def add_to_schedule(self, metadata: CodexMetadata, imprint: str, 
                       priority: int = 5, schedule_file: Optional[str] = None):
        """Add winning ideas to imprint schedules."""
        try:
            # Create schedule entry
            schedule_entry = {
                'title': metadata.title,
                'author': metadata.author,
                'json_file': f"ideas/{imprint}/{metadata.uuid}.json",
                'priority': priority,
                'status': 'approved_from_tournament',
                'added_at': datetime.now().isoformat(),
                'imprint': imprint
            }
            
            # Save metadata as JSON file
            self._save_metadata_json(metadata, imprint)
            
            # Add to schedule
            if self.schedule_manager:
                self.schedule_manager.add_book_to_schedule(schedule_entry, imprint)
            else:
                self._add_to_csv_schedule(schedule_entry, imprint, schedule_file)
            
            self.logger.info(f"Added idea '{metadata.title}' to {imprint} schedule")
            
        except Exception as e:
            self.logger.error(f"Error adding idea to schedule: {e}")
            raise

    def _save_metadata_json(self, metadata: CodexMetadata, imprint: str):
        """Save metadata as JSON file for pipeline processing."""
        output_dir = Path(f"data/ideas/{imprint}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        json_file = output_dir / f"{metadata.uuid}.json"
        
        # Convert metadata to dictionary
        metadata_dict = {
            'title': metadata.title,
            'subtitle': metadata.subtitle,
            'author': metadata.author,
            'publisher': metadata.publisher,
            'imprint': metadata.imprint,
            'publication_date': metadata.publication_date,
            'language': metadata.language,
            'format': metadata.format,
            'country_of_origin': metadata.country_of_origin,
            'audience': metadata.audience,
            'summary_short': metadata.summary_short,
            'summary_long': metadata.summary_long,
            'annotation_summary': metadata.annotation_summary,
            'genre': getattr(metadata, 'genre', ''),
            'target_audience': getattr(metadata, 'target_audience', ''),
            'uuid': metadata.uuid,
            'created_from_idea': True,
            'idea_metadata': getattr(metadata, 'idea_metadata', {})
        }
        
        with open(json_file, 'w') as f:
            json.dump(metadata_dict, f, indent=2)

    def _add_to_csv_schedule(self, schedule_entry: Dict[str, Any], imprint: str, 
                           schedule_file: Optional[str] = None):
        """Add entry to CSV schedule file."""
        import pandas as pd
        
        if not schedule_file:
            schedule_file = f"imprints/{imprint}/schedule.csv"
        
        schedule_path = Path(schedule_file)
        schedule_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create DataFrame from entry
        df_new = pd.DataFrame([schedule_entry])
        
        # Append to existing file or create new
        if schedule_path.exists():
            df_existing = pd.read_csv(schedule_path)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new
        
        df_combined.to_csv(schedule_path, index=False)

    def promote_tournament_winners(self, tournament_results: Dict[str, Any], 
                                 imprint: str, auto_promote: bool = True) -> List[CodexMetadata]:
        """Promote tournament winners to production pipeline."""
        promoted_ideas = []
        
        try:
            winner = tournament_results.get('winner')
            finalists = tournament_results.get('finalists', [])
            
            if winner and auto_promote:
                # Convert winner to metadata
                metadata = self.convert_idea_to_metadata(winner, imprint)
                metadata.idea_metadata = {
                    'tournament_winner': True,
                    'tournament_id': tournament_results.get('tournament_id'),
                    'promotion_date': datetime.now().isoformat()
                }
                
                # Add to schedule with high priority
                self.add_to_schedule(metadata, imprint, priority=1)
                promoted_ideas.append(metadata)
                
                self.logger.info(f"Promoted tournament winner: {winner.title}")
            
            # Optionally promote finalists with lower priority
            for finalist in finalists[:2]:  # Top 2 finalists
                if finalist != winner:  # Don't duplicate winner
                    metadata = self.convert_idea_to_metadata(finalist, imprint)
                    metadata.idea_metadata = {
                        'tournament_finalist': True,
                        'tournament_id': tournament_results.get('tournament_id'),
                        'promotion_date': datetime.now().isoformat()
                    }
                    
                    # Add to schedule with medium priority
                    self.add_to_schedule(metadata, imprint, priority=3)
                    promoted_ideas.append(metadata)
                    
                    self.logger.info(f"Promoted tournament finalist: {finalist.title}")
            
        except Exception as e:
            self.logger.error(f"Error promoting tournament winners: {e}")
            raise
        
        return promoted_ideas

    def batch_promote_ideas(self, ideas: List[BookIdea], imprint: str, 
                          criteria: Optional[Dict[str, Any]] = None) -> List[CodexMetadata]:
        """Batch promote multiple ideas based on criteria."""
        promoted = []
        criteria = criteria or {}
        
        min_rating = criteria.get('min_overall_rating', 6.0)
        max_promotions = criteria.get('max_promotions', 10)
        
        # Filter and sort ideas
        eligible_ideas = []
        for idea in ideas:
            # Check if idea has reader feedback
            if hasattr(idea, 'reader_feedback') and idea.reader_feedback:
                avg_rating = sum(fb.get('overall_rating', 0) for fb in idea.reader_feedback) / len(idea.reader_feedback)
                if avg_rating >= min_rating:
                    eligible_ideas.append((idea, avg_rating))
        
        # Sort by rating (highest first)
        eligible_ideas.sort(key=lambda x: x[1], reverse=True)
        
        # Promote top ideas
        for idea, rating in eligible_ideas[:max_promotions]:
            try:
                metadata = self.convert_idea_to_metadata(idea, imprint)
                metadata.idea_metadata = {
                    'batch_promoted': True,
                    'reader_rating': rating,
                    'promotion_date': datetime.now().isoformat()
                }
                
                # Priority based on rating
                priority = 1 if rating >= 8.0 else 2 if rating >= 7.0 else 3
                self.add_to_schedule(metadata, imprint, priority=priority)
                promoted.append(metadata)
                
            except Exception as e:
                self.logger.error(f"Error promoting idea {idea.title}: {e}")
                continue
        
        self.logger.info(f"Batch promoted {len(promoted)} ideas to {imprint}")
        return promoted


class MetadataConverter:
    """Converts BookIdea objects to CodexMetadata format."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def convert_idea_to_metadata(self, idea: BookIdea, imprint: str, 
                               additional_metadata: Optional[Dict[str, Any]] = None) -> CodexMetadata:
        """Convert BookIdea to CodexMetadata with imprint-specific defaults."""
        
        # Load imprint configuration for defaults
        imprint_defaults = self._load_imprint_defaults(imprint)
        additional = additional_metadata or {}
        
        # Create CodexMetadata object
        metadata = CodexMetadata(
            title=idea.title,
            subtitle="",  # Can be enhanced later
            author=additional.get('author', 'AI Lab for Book-Lovers'),
            publisher=imprint_defaults.get('publisher', 'Nimble Books LLC'),
            imprint=imprint_defaults.get('imprint', imprint),
            publication_date=additional.get('publication_date', ''),
            language=imprint_defaults.get('language', 'English'),
            format=imprint_defaults.get('format', 'Paperback'),
            country_of_origin=imprint_defaults.get('country_of_origin', 'US'),
            audience=imprint_defaults.get('audience', 'General Adult'),
            summary_short=idea.logline,
            summary_long=idea.description or self._expand_logline(idea.logline),
            annotation_summary=self._create_annotation(idea)
        )
        
        # Add idea-specific metadata
        metadata.idea_metadata = {
            'original_idea_id': idea.generation_metadata.get('idea_id', ''),
            'generation_metadata': idea.generation_metadata,
            'tournament_performance': idea.tournament_performance,
            'reader_feedback': idea.reader_feedback,
            'imprint_alignment': idea.imprint_alignment,
            'converted_at': datetime.now().isoformat()
        }
        
        # Set genre and target audience if available
        if hasattr(metadata, 'genre'):
            metadata.genre = idea.genre
        if hasattr(metadata, 'target_audience'):
            metadata.target_audience = idea.target_audience
        
        return metadata

    def _load_imprint_defaults(self, imprint: str) -> Dict[str, Any]:
        """Load imprint-specific defaults."""
        try:
            config_path = Path(f"configs/imprints/{imprint}.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                return {
                    'publisher': config.get('publisher', 'Nimble Books LLC'),
                    'imprint': config.get('imprint', imprint),
                    'language': config.get('default_book_settings', {}).get('language_code', 'eng'),
                    'format': config.get('default_book_settings', {}).get('binding_type', 'paperback'),
                    'country_of_origin': config.get('default_book_settings', {}).get('country_of_origin', 'US'),
                    'audience': config.get('default_book_settings', {}).get('audience', 'General Adult')
                }
        except Exception as e:
            self.logger.warning(f"Could not load imprint defaults for {imprint}: {e}")
        
        # Return basic defaults
        return {
            'publisher': 'Nimble Books LLC',
            'imprint': imprint,
            'language': 'English',
            'format': 'Paperback',
            'country_of_origin': 'US',
            'audience': 'General Adult'
        }

    def _expand_logline(self, logline: str) -> str:
        """Expand a logline into a longer description."""
        if len(logline) > 200:
            return logline
        
        # Simple expansion - in practice, this could use LLM
        expanded = f"{logline} This compelling narrative explores themes of human nature, relationships, and personal growth. "
        expanded += "Through engaging characters and thoughtful storytelling, readers will discover new perspectives and insights. "
        expanded += "A must-read for anyone interested in contemporary literature and meaningful storytelling."
        
        return expanded

    def _create_annotation(self, idea: BookIdea) -> str:
        """Create an annotation summary for the idea."""
        annotation = f"<p><strong>{idea.title}</strong></p>\n"
        annotation += f"<p>{idea.logline}</p>\n"
        
        if idea.description:
            annotation += f"<p>{idea.description}</p>\n"
        
        if idea.genre:
            annotation += f"<p><em>Genre: {idea.genre}</em></p>\n"
        
        if idea.target_audience:
            annotation += f"<p><em>Target Audience: {idea.target_audience}</em></p>\n"
        
        return annotation


class ScheduleIntegrationManager:
    """Manages integration with various schedule formats and systems."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def integrate_with_existing_schedule(self, new_ideas: List[CodexMetadata], 
                                       imprint: str, schedule_path: str) -> Dict[str, Any]:
        """Integrate new ideas with existing schedule, handling conflicts."""
        try:
            import pandas as pd
            
            # Load existing schedule
            if Path(schedule_path).exists():
                existing_df = pd.read_csv(schedule_path)
            else:
                existing_df = pd.DataFrame()
            
            # Convert new ideas to schedule format
            new_entries = []
            for metadata in new_ideas:
                entry = {
                    'title': metadata.title,
                    'author': metadata.author,
                    'json_file': f"ideas/{imprint}/{metadata.uuid}.json",
                    'priority': getattr(metadata, 'priority', 5),
                    'status': 'approved_from_ideas',
                    'added_at': datetime.now().isoformat(),
                    'imprint': imprint
                }
                new_entries.append(entry)
            
            new_df = pd.DataFrame(new_entries)
            
            # Check for conflicts (duplicate titles)
            conflicts = []
            if not existing_df.empty:
                existing_titles = set(existing_df['title'].str.lower())
                for entry in new_entries:
                    if entry['title'].lower() in existing_titles:
                        conflicts.append(entry['title'])
            
            # Combine schedules
            if not existing_df.empty:
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                combined_df = new_df
            
            # Sort by priority and date
            combined_df = combined_df.sort_values(['priority', 'added_at'])
            
            # Save updated schedule
            combined_df.to_csv(schedule_path, index=False)
            
            return {
                'success': True,
                'added_count': len(new_entries),
                'conflicts': conflicts,
                'total_schedule_size': len(combined_df)
            }
            
        except Exception as e:
            self.logger.error(f"Error integrating with schedule: {e}")
            return {
                'success': False,
                'error': str(e),
                'added_count': 0
            }

    def resolve_schedule_conflicts(self, conflicts: List[str], resolution_strategy: str = 'rename') -> Dict[str, str]:
        """Resolve scheduling conflicts using specified strategy."""
        resolutions = {}
        
        for title in conflicts:
            if resolution_strategy == 'rename':
                new_title = f"{title} (Idea Variant)"
                resolutions[title] = new_title
            elif resolution_strategy == 'skip':
                resolutions[title] = 'SKIPPED'
            elif resolution_strategy == 'replace':
                resolutions[title] = 'REPLACED'
            else:
                resolutions[title] = 'MANUAL_REVIEW_REQUIRED'
        
        return resolutions