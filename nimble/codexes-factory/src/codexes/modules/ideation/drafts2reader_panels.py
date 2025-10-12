#!/usr/bin/env python3
"""
Drafts2HighVolumeReaderPanels - Production-ready reader panel evaluation system

Features:
- Multi-file/directory input support
- Configurable panel definitions (Children, YA, Parents, Experts, etc.)
- Configurable prompts from JSON files
- Parallel execution with nimble-llm-caller
- CLI and Streamlit UI interfaces
- Optimized for speed and efficiency
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

try:
    from codexes.core.llm_integration import LLMCaller
    from codexes.modules.ideation.synthetic_reader import SyntheticReaderPersona, ReaderFeedback
except ModuleNotFoundError:
    from src.codexes.core.llm_integration import LLMCaller
    from src.codexes.modules.ideation.synthetic_reader import SyntheticReaderPersona, ReaderFeedback


logger = logging.getLogger(__name__)


@dataclass
class PanelDefinition:
    """Definition of a reader panel with personas and configuration."""
    name: str
    description: str
    target_count: int
    archetypes: List[Dict[str, Any]]
    age_range: Optional[str] = None
    evaluation_focus: Optional[str] = None


@dataclass
class EvaluationConfig:
    """Configuration for evaluation execution."""
    model: str = "claude-sonnet-4-5-20250219"
    temperature: float = 0.7
    max_workers: int = 10
    batch_size: int = 10
    save_incremental: bool = True
    progress_interval: int = 20


class Drafts2HighVolumeReaderPanels:
    """
    High-volume reader panel evaluation system with configurable panels,
    prompts, and parallel execution.

    Usage:
        evaluator = Drafts2HighVolumeReaderPanels()
        evaluator.load_prompts('prompts/reader_panel_prompts.json')
        evaluator.add_panel(PanelDefinition(...))
        results = evaluator.evaluate_drafts(['draft1.json', 'draft2.md'])
    """

    def __init__(
        self,
        output_dir: Path = None,
        config: EvaluationConfig = None,
        llm_caller: LLMCaller = None
    ):
        """
        Initialize the reader panel evaluation system.

        Args:
            output_dir: Base directory for saving results
            config: Evaluation configuration
            llm_caller: Optional custom LLM caller instance
        """
        self.output_dir = output_dir or Path('data/reader_panels')
        self.config = config or EvaluationConfig()
        self.llm_caller = llm_caller or LLMCaller()

        self.panels: List[PanelDefinition] = []
        self.prompts: Dict[str, str] = {}
        self.draft_parsers: Dict[str, Callable] = {}

        # Register default draft parsers
        self._register_default_parsers()

        logger.info(f"Initialized Drafts2HighVolumeReaderPanels with output_dir: {self.output_dir}")

    def _register_default_parsers(self):
        """Register default parsers for common file formats."""
        self.draft_parsers['.json'] = self._parse_json_draft
        self.draft_parsers['.md'] = self._parse_markdown_draft
        self.draft_parsers['.txt'] = self._parse_text_draft

    def load_prompts(self, prompt_file: Path) -> None:
        """
        Load evaluation prompts from JSON file.

        Expected format:
        {
            "system_prompt": "...",
            "evaluation_prompt": "...",
            "panel_specific": {
                "children": "...",
                "parents": "...",
                ...
            }
        }
        """
        with open(prompt_file) as f:
            self.prompts = json.load(f)
        logger.info(f"Loaded {len(self.prompts)} prompt templates from {prompt_file}")

    def add_panel(self, panel: PanelDefinition) -> None:
        """Add a reader panel definition."""
        self.panels.append(panel)
        logger.info(f"Added panel: {panel.name} ({panel.target_count} personas)")

    def load_panel_definitions(self, panel_file: Path) -> None:
        """
        Load panel definitions from JSON file.

        Expected format:
        {
            "panels": [
                {
                    "name": "children_9_10",
                    "description": "9-10 year old readers",
                    "target_count": 100,
                    "archetypes": [...]
                },
                ...
            ]
        }
        """
        with open(panel_file) as f:
            data = json.load(f)

        for panel_data in data.get('panels', []):
            panel = PanelDefinition(**panel_data)
            self.add_panel(panel)

        logger.info(f"Loaded {len(self.panels)} panel definitions from {panel_file}")

    def create_default_panels(self) -> None:
        """Create default panel definitions (Children, YA, Parents, Experts, Purchasing)."""
        # Children Panel (9-10)
        self.add_panel(PanelDefinition(
            name="children_9_10",
            description="9-10 year old readers",
            target_count=100,
            age_range="9-10",
            archetypes=[
                {
                    'name': 'Advanced Reader',
                    'count': 20,
                    'characteristics': {
                        'reading_level': 'above grade level',
                        'interests': ['complex stories', 'wordplay', 'mysteries'],
                        'personality': ['curious', 'confident', 'analytical']
                    }
                },
                {
                    'name': 'Reluctant Reader',
                    'count': 20,
                    'characteristics': {
                        'reading_level': 'below grade level',
                        'interests': ['action', 'visuals', 'gaming'],
                        'personality': ['frustrated', 'visual learner', 'prefers short']
                    }
                },
                {
                    'name': 'Grade Level Reader',
                    'count': 20,
                    'characteristics': {
                        'reading_level': 'at grade level',
                        'interests': ['relatable stories', 'friendship', 'school'],
                        'personality': ['social', 'empathetic', 'likes series']
                    }
                },
                {
                    'name': 'Fantasy Lover',
                    'count': 20,
                    'characteristics': {
                        'reading_level': 'at/above grade level',
                        'interests': ['magic', 'creatures', 'quests'],
                        'personality': ['imaginative', 'loves world-building', 'detail-oriented']
                    }
                },
                {
                    'name': 'Contemporary Fan',
                    'count': 20,
                    'characteristics': {
                        'reading_level': 'at grade level',
                        'interests': ['realistic fiction', 'humor', 'modern life'],
                        'personality': ['relatable', 'funny', 'culturally aware']
                    }
                }
            ]
        ))

        # Young Adult Panel (12-17)
        self.add_panel(PanelDefinition(
            name="young_adult",
            description="12-17 year old readers",
            target_count=80,
            age_range="12-17",
            archetypes=[
                {
                    'name': 'Romance Reader',
                    'count': 20,
                    'characteristics': {
                        'reading_level': 'at/above grade level',
                        'interests': ['romance', 'relationships', 'drama'],
                        'personality': ['emotional', 'shipping', 'character-focused']
                    }
                },
                {
                    'name': 'Fantasy Epic Fan',
                    'count': 20,
                    'characteristics': {
                        'reading_level': 'advanced',
                        'interests': ['epic fantasy', 'series', 'complex plots'],
                        'personality': ['dedicated', 'analytical', 'theory-crafting']
                    }
                },
                {
                    'name': 'Contemporary YA Reader',
                    'count': 20,
                    'characteristics': {
                        'reading_level': 'at grade level',
                        'interests': ['realistic issues', 'identity', 'social justice'],
                        'personality': ['socially conscious', 'authentic', 'diverse']
                    }
                },
                {
                    'name': 'Thriller/Mystery Fan',
                    'count': 20,
                    'characteristics': {
                        'reading_level': 'advanced',
                        'interests': ['suspense', 'plot twists', 'crime'],
                        'personality': ['analytical', 'detail-oriented', 'fast-paced']
                    }
                }
            ]
        ))

        # Parents Panel
        self.add_panel(PanelDefinition(
            name="parents",
            description="Parent purchasers and decision makers",
            target_count=80,
            archetypes=[
                {
                    'name': 'Literary Parent',
                    'count': 20,
                    'characteristics': {
                        'priorities': ['classics', 'language development', 'cultural literacy'],
                        'concerns': ['quality', 'educational value', 'timelessness']
                    }
                },
                {
                    'name': 'Practical Parent',
                    'count': 20,
                    'characteristics': {
                        'priorities': ['engagement', 'age-appropriate', 'value'],
                        'concerns': ['will they read it', 'price', 'appropriateness']
                    }
                },
                {
                    'name': 'Modern Parent',
                    'count': 20,
                    'characteristics': {
                        'priorities': ['diversity', 'contemporary', 'representation'],
                        'concerns': ['inclusivity', 'relevance', 'social awareness']
                    }
                },
                {
                    'name': 'Nostalgic Parent',
                    'count': 20,
                    'characteristics': {
                        'priorities': ['sharing favorites', 'family bonding', 'tradition'],
                        'concerns': ['passing on love of reading', 'shared experience']
                    }
                }
            ]
        ))

        # Reading Experts Panel
        self.add_panel(PanelDefinition(
            name="reading_experts",
            description="Educators and literacy specialists",
            target_count=50,
            archetypes=[
                {
                    'name': 'Elementary Teacher',
                    'count': 10,
                    'characteristics': {
                        'expertise': ['classroom management', 'engagement', 'differentiation'],
                        'priorities': ['student interest', 'curriculum fit', 'practical use']
                    }
                },
                {
                    'name': 'Reading Specialist',
                    'count': 10,
                    'characteristics': {
                        'expertise': ['intervention', 'struggling readers', 'assessment'],
                        'priorities': ['accessibility', 'scaffolding', 'confidence building']
                    }
                },
                {
                    'name': 'Literature Professor',
                    'count': 10,
                    'characteristics': {
                        'expertise': ['literary analysis', 'canon', 'cultural significance'],
                        'priorities': ['quality', 'merit', 'historical importance']
                    }
                },
                {
                    'name': 'Librarian',
                    'count': 10,
                    'characteristics': {
                        'expertise': ['collection development', 'readers advisory', 'trends'],
                        'priorities': ['circulation', 'diverse collection', 'student demand']
                    }
                },
                {
                    'name': 'EdTech Specialist',
                    'count': 10,
                    'characteristics': {
                        'expertise': ['technology integration', 'digital literacy', 'innovation'],
                        'priorities': ['modern learning', 'engagement', 'accessibility']
                    }
                }
            ]
        ))

        # Purchasing Decision Makers Panel
        self.add_panel(PanelDefinition(
            name="purchasing",
            description="School and institutional buyers",
            target_count=40,
            archetypes=[
                {
                    'name': 'School Librarian',
                    'count': 10,
                    'characteristics': {
                        'role': 'library collection',
                        'priorities': ['budget', 'circulation potential', 'diverse needs'],
                        'concerns': ['ROI', 'space', 'maintenance']
                    }
                },
                {
                    'name': 'Curriculum Director',
                    'count': 10,
                    'characteristics': {
                        'role': 'district curriculum',
                        'priorities': ['standards alignment', 'evidence-based', 'scalability'],
                        'concerns': ['district-wide fit', 'teacher support', 'assessment']
                    }
                },
                {
                    'name': 'Principal',
                    'count': 10,
                    'characteristics': {
                        'role': 'school leadership',
                        'priorities': ['student achievement', 'parent satisfaction', 'budget'],
                        'concerns': ['practical implementation', 'staff buy-in', 'outcomes']
                    }
                },
                {
                    'name': 'Special Ed Coordinator',
                    'count': 10,
                    'characteristics': {
                        'role': 'special education',
                        'priorities': ['accessibility', 'accommodations', 'struggling readers'],
                        'concerns': ['equity', 'differentiation', 'support needs']
                    }
                }
            ]
        ))

        logger.info(f"Created {len(self.panels)} default panels")

    def _parse_json_draft(self, file_path: Path) -> Dict[str, Any]:
        """Parse JSON draft file."""
        with open(file_path) as f:
            return json.load(f)

    def _parse_markdown_draft(self, file_path: Path) -> Dict[str, Any]:
        """Parse Markdown draft file."""
        with open(file_path) as f:
            content = f.read()

        # Extract title (first # heading)
        lines = content.split('\n')
        title = "Untitled"
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break

        return {
            'title': title,
            'content': content,
            'format': 'markdown',
            'file_path': str(file_path)
        }

    def _parse_text_draft(self, file_path: Path) -> Dict[str, Any]:
        """Parse plain text draft file."""
        with open(file_path) as f:
            content = f.read()

        # Try to extract title from first line
        lines = content.split('\n')
        title = lines[0].strip() if lines else file_path.stem

        return {
            'title': title,
            'content': content,
            'format': 'text',
            'file_path': str(file_path)
        }

    def load_draft(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a draft file."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Draft file not found: {file_path}")

        suffix = file_path.suffix.lower()
        parser = self.draft_parsers.get(suffix)

        if not parser:
            raise ValueError(f"No parser registered for file type: {suffix}")

        draft_data = parser(file_path)
        draft_data['_source_file'] = str(file_path)
        draft_data['_parsed_at'] = datetime.now().isoformat()

        logger.info(f"Loaded draft: {draft_data.get('title', file_path.name)}")
        return draft_data

    def load_drafts_from_directory(
        self,
        directory: Path,
        recursive: bool = True,
        extensions: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Load all draft files from a directory.

        Args:
            directory: Directory to scan
            recursive: Walk subdirectories
            extensions: File extensions to include (e.g., ['.json', '.md'])

        Returns:
            List of parsed draft data
        """
        directory = Path(directory)
        extensions = extensions or ['.json', '.md', '.txt']

        drafts = []
        pattern = '**/*' if recursive else '*'

        for ext in extensions:
            for file_path in directory.glob(f"{pattern}{ext}"):
                if file_path.is_file():
                    try:
                        draft = self.load_draft(file_path)
                        drafts.append(draft)
                    except Exception as e:
                        logger.error(f"Failed to load {file_path}: {e}")

        logger.info(f"Loaded {len(drafts)} drafts from {directory}")
        return drafts

    def create_personas_for_panel(self, panel: PanelDefinition) -> List[SyntheticReaderPersona]:
        """Create synthetic reader personas for a panel."""
        personas = []

        for archetype in panel.archetypes:
            count = archetype.get('count', 10)
            base_name = archetype['name']
            characteristics = archetype.get('characteristics', {})

            # Add panel-level metadata
            if panel.age_range:
                characteristics['age_range'] = panel.age_range

            for i in range(count):
                persona_name = f"{base_name} #{i+1}"
                persona = SyntheticReaderPersona(persona_name, characteristics)
                personas.append(persona)

        logger.info(f"Created {len(personas)} personas for panel: {panel.name}")
        return personas

    def _evaluate_persona(
        self,
        persona: SyntheticReaderPersona,
        draft_data: Dict[str, Any],
        panel_name: str,
        prompt_template: str
    ) -> Optional[ReaderFeedback]:
        """Evaluate a single persona against a draft."""
        try:
            # Build evaluation prompt
            prompt = prompt_template.format(
                persona_name=persona.name,
                persona_characteristics=json.dumps(persona.characteristics, indent=2),
                draft_title=draft_data.get('title', 'Untitled'),
                draft_content=str(draft_data.get('description', draft_data.get('content', '')))[:2000],
                **draft_data
            )

            # Call LLM
            response = self.llm_caller.call_llm(
                prompt=prompt,
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=2000
            )

            # Parse response (expecting JSON)
            try:
                eval_data = json.loads(response)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    eval_data = json.loads(json_match.group())
                else:
                    logger.error(f"Failed to parse JSON from response for {persona.name}")
                    return None

            # Create ReaderFeedback object
            feedback = ReaderFeedback(
                reader_persona=persona.name,
                idea_id=draft_data.get('idea_id', draft_data.get('title', 'unknown')),
                market_appeal_score=eval_data.get('market_appeal', 5.0),
                genre_fit_score=eval_data.get('genre_fit', 5.0),
                audience_alignment_score=eval_data.get('audience_alignment', 5.0),
                detailed_feedback=eval_data.get('detailed_feedback', ''),
                recommendations=eval_data.get('recommendations', []),
                concerns=eval_data.get('concerns', []),
                overall_rating=(
                    eval_data.get('market_appeal', 5.0) +
                    eval_data.get('genre_fit', 5.0) +
                    eval_data.get('audience_alignment', 5.0)
                ) / 3.0
            )

            return feedback

        except Exception as e:
            logger.error(f"Error evaluating {persona.name}: {e}")
            return None

    def evaluate_panel(
        self,
        panel: PanelDefinition,
        draft_data: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> List[ReaderFeedback]:
        """
        Evaluate a draft with a complete panel in parallel.

        Args:
            panel: Panel definition
            draft_data: Parsed draft data
            progress_callback: Optional callback for progress updates

        Returns:
            List of ReaderFeedback objects
        """
        logger.info(f"Starting evaluation for panel: {panel.name}")
        start_time = time.time()

        # Create personas
        personas = self.create_personas_for_panel(panel)

        # Get prompt template
        prompt_template = self.prompts.get('panel_specific', {}).get(
            panel.name,
            self.prompts.get('evaluation_prompt', '')
        )

        if not prompt_template:
            logger.error(f"No prompt template found for panel: {panel.name}")
            return []

        # Parallel evaluation
        all_feedback = []
        batch_size = self.config.batch_size

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = []

            for persona in personas:
                future = executor.submit(
                    self._evaluate_persona,
                    persona,
                    draft_data,
                    panel.name,
                    prompt_template
                )
                futures.append((future, persona))

            # Collect results
            completed = 0
            for future, persona in futures:
                try:
                    feedback = future.result(timeout=120)  # 2 minute timeout per persona
                    if feedback:
                        all_feedback.append(feedback)
                        completed += 1

                        # Progress callback
                        if progress_callback and completed % self.config.progress_interval == 0:
                            progress_callback(panel.name, completed, len(personas))

                        # Incremental save
                        if self.config.save_incremental and completed % 10 == 0:
                            self._save_incremental(panel.name, draft_data, all_feedback)

                except Exception as e:
                    logger.error(f"Failed to get result for {persona.name}: {e}")

        elapsed = time.time() - start_time
        rate = len(all_feedback) / elapsed * 60 if elapsed > 0 else 0

        logger.info(
            f"Panel {panel.name} complete: {len(all_feedback)}/{len(personas)} "
            f"in {elapsed:.1f}s ({rate:.1f} reviews/min)"
        )

        return all_feedback

    def _save_incremental(
        self,
        panel_name: str,
        draft_data: Dict[str, Any],
        feedback: List[ReaderFeedback]
    ):
        """Save incremental results."""
        draft_slug = self._create_draft_slug(draft_data)
        output_path = self.output_dir / draft_slug / f"{panel_name}_feedback.jsonl"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            for fb in feedback:
                f.write(json.dumps(asdict(fb)) + '\n')

    def _create_draft_slug(self, draft_data: Dict[str, Any]) -> str:
        """Create URL-safe slug for draft."""
        title = draft_data.get('title', 'untitled')
        slug = title.lower().replace(' ', '_').replace("'", '')
        slug = ''.join(c for c in slug if c.isalnum() or c == '_')
        return slug[:50]  # Limit length

    def save_results(
        self,
        panel_name: str,
        draft_data: Dict[str, Any],
        feedback: List[ReaderFeedback]
    ) -> Path:
        """Save panel evaluation results."""
        draft_slug = self._create_draft_slug(draft_data)
        output_path = self.output_dir / draft_slug / f"{panel_name}_feedback.jsonl"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Calculate statistics
        if feedback:
            stats = {
                'avg_market_appeal': sum(f.market_appeal_score for f in feedback) / len(feedback),
                'avg_genre_fit': sum(f.genre_fit_score for f in feedback) / len(feedback),
                'avg_audience_alignment': sum(f.audience_alignment_score for f in feedback) / len(feedback),
                'avg_overall_rating': sum(f.overall_rating for f in feedback) / len(feedback)
            }
        else:
            stats = {}

        # Save JSONL
        with open(output_path, 'w') as f:
            for fb in feedback:
                f.write(json.dumps(asdict(fb)) + '\n')

        # Save summary
        summary_path = output_path.parent / f"{panel_name}_summary.json"
        with open(summary_path, 'w') as f:
            json.dump({
                'panel_name': panel_name,
                'draft_title': draft_data.get('title', 'Untitled'),
                'timestamp': datetime.now().isoformat(),
                'total_reviews': len(feedback),
                'statistics': stats
            }, f, indent=2)

        logger.info(f"Saved {len(feedback)} reviews to {output_path}")
        return output_path

    def evaluate_drafts(
        self,
        draft_paths: List[Path],
        panels: Optional[List[str]] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Dict[str, List[ReaderFeedback]]]:
        """
        Evaluate multiple drafts with configured panels.

        Args:
            draft_paths: List of draft file paths
            panels: Optional list of panel names to use (uses all if None)
            progress_callback: Optional progress callback

        Returns:
            Dict mapping draft_slug -> panel_name -> feedback list
        """
        results = {}

        # Filter panels
        panels_to_use = self.panels
        if panels:
            panels_to_use = [p for p in self.panels if p.name in panels]

        logger.info(f"Evaluating {len(draft_paths)} drafts with {len(panels_to_use)} panels")

        for draft_path in draft_paths:
            try:
                # Load draft
                draft_data = self.load_draft(draft_path)
                draft_slug = self._create_draft_slug(draft_data)

                results[draft_slug] = {}

                # Evaluate with each panel
                for panel in panels_to_use:
                    feedback = self.evaluate_panel(panel, draft_data, progress_callback)
                    results[draft_slug][panel.name] = feedback

                    # Save results
                    self.save_results(panel.name, draft_data, feedback)

            except Exception as e:
                logger.error(f"Failed to evaluate {draft_path}: {e}")

        return results

    def generate_summary_report(
        self,
        draft_slug: str,
        results: Dict[str, List[ReaderFeedback]]
    ) -> Path:
        """Generate comprehensive summary report for a draft."""
        output_path = self.output_dir / draft_slug / "COMPLETE_PANEL_SUMMARY.md"

        # Aggregate statistics
        all_feedback = []
        panel_stats = {}

        for panel_name, feedback in results.items():
            all_feedback.extend(feedback)
            if feedback:
                panel_stats[panel_name] = {
                    'count': len(feedback),
                    'avg_overall': sum(f.overall_rating for f in feedback) / len(feedback),
                    'avg_market': sum(f.market_appeal_score for f in feedback) / len(feedback),
                    'avg_genre': sum(f.genre_fit_score for f in feedback) / len(feedback),
                    'avg_audience': sum(f.audience_alignment_score for f in feedback) / len(feedback)
                }

        # Generate report
        with open(output_path, 'w') as f:
            f.write(f"# Reader Panel Evaluation Summary\n\n")
            f.write(f"**Draft:** {draft_slug}\n")
            f.write(f"**Evaluation Date:** {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"**Total Reviews:** {len(all_feedback)}\n\n")

            f.write("## Panel Results\n\n")
            f.write("| Panel | Reviews | Overall | Market | Genre | Audience |\n")
            f.write("|-------|---------|---------|--------|-------|----------|\n")

            for panel_name, stats in panel_stats.items():
                f.write(
                    f"| {panel_name} | {stats['count']} | "
                    f"{stats['avg_overall']:.2f} | {stats['avg_market']:.2f} | "
                    f"{stats['avg_genre']:.2f} | {stats['avg_audience']:.2f} |\n"
                )

            # Overall statistics
            if all_feedback:
                overall_avg = sum(f.overall_rating for f in all_feedback) / len(all_feedback)
                f.write(f"\n**Overall Average Rating:** {overall_avg:.2f}/10\n\n")

            # Common themes (simple analysis)
            all_concerns = []
            all_recommendations = []
            for fb in all_feedback:
                all_concerns.extend(fb.concerns)
                all_recommendations.extend(fb.recommendations)

            if all_concerns:
                f.write("\n## Common Concerns\n\n")
                # Count unique concerns
                from collections import Counter
                concern_counts = Counter(all_concerns)
                for concern, count in concern_counts.most_common(10):
                    f.write(f"- {concern} ({count} mentions)\n")

            if all_recommendations:
                f.write("\n## Top Recommendations\n\n")
                rec_counts = Counter(all_recommendations)
                for rec, count in rec_counts.most_common(10):
                    f.write(f"- {rec} ({count} mentions)\n")

        logger.info(f"Generated summary report: {output_path}")
        return output_path


def main():
    """CLI entry point for Drafts2HighVolumeReaderPanels."""
    import argparse

    parser = argparse.ArgumentParser(description="High-volume reader panel evaluation system")
    parser.add_argument('drafts', nargs='+', help="Draft file paths or directories")
    parser.add_argument('--panels', nargs='+', help="Panel names to use")
    parser.add_argument('--panel-config', type=Path, help="Panel definitions JSON file")
    parser.add_argument('--prompts', type=Path, help="Prompts JSON file")
    parser.add_argument('--output-dir', type=Path, default='data/reader_panels', help="Output directory")
    parser.add_argument('--model', default='claude-sonnet-4-5-20250219', help="LLM model to use")
    parser.add_argument('--workers', type=int, default=10, help="Parallel workers")
    parser.add_argument('--recursive', action='store_true', help="Recursively scan directories")

    args = parser.parse_args()

    # Initialize
    config = EvaluationConfig(
        model=args.model,
        max_workers=args.workers
    )

    evaluator = Drafts2HighVolumeReaderPanels(
        output_dir=args.output_dir,
        config=config
    )

    # Load configurations
    if args.prompts:
        evaluator.load_prompts(args.prompts)

    if args.panel_config:
        evaluator.load_panel_definitions(args.panel_config)
    else:
        evaluator.create_default_panels()

    # Load drafts
    all_drafts = []
    for path_str in args.drafts:
        path = Path(path_str)
        if path.is_dir():
            drafts = evaluator.load_drafts_from_directory(path, recursive=args.recursive)
            all_drafts.extend([d['_source_file'] for d in drafts])
        else:
            all_drafts.append(path)

    # Progress callback
    def progress(panel_name, completed, total):
        print(f"{panel_name}: {completed}/{total} ({completed/total*100:.1f}%)")

    # Evaluate
    print(f"Evaluating {len(all_drafts)} drafts with {len(evaluator.panels)} panels...")
    results = evaluator.evaluate_drafts(all_drafts, panels=args.panels, progress_callback=progress)

    # Generate reports
    for draft_slug, panel_results in results.items():
        evaluator.generate_summary_report(draft_slug, panel_results)

    print(f"✓ Evaluation complete. Results saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
