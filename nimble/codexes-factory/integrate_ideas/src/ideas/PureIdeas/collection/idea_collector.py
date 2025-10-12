# src/ideas/collection/idea_collector.py
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

from typing import Iterable




from src.ideas.PureIdeas.Idea import Idea, IdeaSet



@dataclass
class IdeaSource:
    source_type: str  # 'human', 'llm', 'trend'
    source_name: str
    timestamp: datetime = datetime.now()
    metadata: Dict = None


class IdeaCollector:
    def __init__(self, output_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.output_dir = output_dir or Path("collected_ideas")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def add_human_idea(self, idea_text: str, source_name: str = "human") -> Idea:
        """Add a single human-generated idea"""
        try:
            idea = Idea(idea_text)
            self._store_idea(idea, IdeaSource("human", source_name))
            return idea
        except ValueError as e:
            self.logger.error(f"Failed to create idea: {e}")
            raise

    def add_llm_idea(self,
                     idea_text: str,
                     model_name: str,
                     prompt_used: Optional[str] = None) -> Idea:
        """Add a single LLM-generated idea"""
        try:
            idea = Idea(idea_text)
            source = IdeaSource(
                "llm",
                model_name,
                metadata={"prompt": prompt_used} if prompt_used else None
            )
            self._store_idea(idea, source)
            return idea
        except ValueError as e:
            self.logger.error(f"Failed to create LLM idea: {e}")
            raise

    def add_trend_based_idea(self,
                             idea_text: str,
                             trend_source: str,
                             trend_data: Dict) -> Idea:
        """Add a single trend-based idea"""
        try:
            idea = Idea(idea_text)
            source = IdeaSource(
                "trend",
                trend_source,
                metadata=trend_data
            )
            self._store_idea(idea, source)
            return idea
        except ValueError as e:
            self.logger.error(f"Failed to create trend-based idea: {e}")
            raise

    def _store_idea(self, idea: Idea, source: IdeaSource):
        """Store idea with its metadata"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"idea_{source.source_type}_{timestamp}.json"

        data = {
            "idea": idea.description_of_idea,
            "source_type": source.source_type,
            "source_name": source.source_name,
            "timestamp": source.timestamp.isoformat(),
            "metadata": source.metadata
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def collect_to_idea_set(self,
                            source_types: Optional[List[str]] = None) -> IdeaSet:
        """Collect all stored ideas into an IdeaSet"""
        idea_set = IdeaSet()

        for file in self.output_dir.glob("idea_*.json"):
                with open(file, 'r') as f:
                    data = json.load(f)

                if source_types and data["source_type"] not in source_types:
                    continue

                idea = Idea(data["idea"])
                idea_set.add_idea(idea)

                return idea_set
