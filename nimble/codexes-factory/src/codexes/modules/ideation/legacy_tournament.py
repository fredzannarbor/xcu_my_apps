"""
Tournament system for competitive evaluation of book ideas.
Enhanced version of the original Tournament class with codexes-factory integration.
"""

import csv
import datetime
import logging
import math
import random
import json
import uuid
from typing import List, Dict, Any, Set, TextIO, Union, Optional
from pathlib import Path

import pandas as pd

from .book_idea import BookIdea
from ...core.llm_integration import LLMCaller

logger = logging.getLogger(__name__)


class Tournament:
    """
    Enhanced tournament system for arranging, managing, and simulating competition
    between book ideas using codexes-factory infrastructure.
    """
    
    def __init__(self, ideas: Union[Set[Dict[str, Any]], List[BookIdea]], 
                 llm_caller: LLMCaller, model: str = "ollama/deepseek-r1:latest", temperature: float = 0.7):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.llm_caller = llm_caller
        self.model = model
        self.temperature = temperature
        
        # Convert input ideas to BookIdea objects
        self.original_ideas = self._normalize_ideas(ideas)
        self.seeded_ideas = self.assign_random_seeds_to_ideas(self.original_ideas)
        self.total_matches = self._next_power_of_two(len(self.original_ideas)) - 1
        self.rounds = []
        self.total_ideas = len(self.original_ideas)
        self.total_teams = len(self.seeded_ideas)
        self.tournament_id = str(uuid.uuid4())[:8]

    def _normalize_ideas(self, ideas: Union[Set[Dict[str, Any]], List[BookIdea]]) -> List[BookIdea]:
        """Convert various input formats to BookIdea objects."""
        normalized = []
        
        if isinstance(ideas, set):
            ideas = list(ideas)
            
        for idea in ideas:
            if isinstance(idea, BookIdea):
                normalized.append(idea)
            elif isinstance(idea, dict):
                # Convert dict to BookIdea
                book_idea = BookIdea(
                    title=idea.get("title", "Untitled"),
                    logline=idea.get("logline", "No logline provided"),
                    description=idea.get("description", ""),
                    genre=idea.get("genre", ""),
                    target_audience=idea.get("target_audience", "")
                )
                normalized.append(book_idea)
            elif hasattr(idea, 'title') and hasattr(idea, 'logline'):
                # Convert object with title/logline attributes
                book_idea = BookIdea(
                    title=getattr(idea, 'title', 'Untitled'),
                    logline=getattr(idea, 'logline', 'No logline provided')
                )
                normalized.append(book_idea)
            elif isinstance(idea, str):
                # Convert string to BookIdea
                book_idea = BookIdea(
                    title=idea,
                    logline="No logline provided"
                )
                normalized.append(book_idea)
            else:
                raise TypeError(f"Unexpected type for idea: {type(idea)}")
                
        return normalized

    @staticmethod
    def assign_random_seeds_to_ideas(original_ideas: List[BookIdea]) -> List[BookIdea]:
        """Assign random seeds to ideas for tournament bracketing."""
        seeded = []
        seeds = list(range(1, len(original_ideas) + 1))
        random.shuffle(seeds)
        
        for index, idea in enumerate(original_ideas):
            # Create a copy to avoid modifying original
            seeded_idea = BookIdea(
                title=idea.title,
                logline=idea.logline,
                description=idea.description,
                genre=idea.genre,
                target_audience=idea.target_audience,
                seed=seeds[index]
            )
            # Copy other attributes
            seeded_idea.imprint_alignment = idea.imprint_alignment
            seeded_idea.tournament_performance = idea.tournament_performance.copy()
            seeded_idea.reader_feedback = idea.reader_feedback.copy()
            seeded_idea.generation_metadata = idea.generation_metadata.copy()
            seeded_idea.created_at = idea.created_at
            seeded_idea.status = idea.status
            
            seeded.append(seeded_idea)
            
        return seeded

    @staticmethod
    def _next_power_of_two(x):
        """Calculate the next power of two for tournament bracketing."""
        return 1 if x == 0 else 2 ** (x - 1).bit_length()

    def _add_byes(self):
        """Add bye entries to reach power of two participants."""
        actual_count = len(self.seeded_ideas)
        next_power_two = self._next_power_of_two(actual_count)
        byes_needed = next_power_two - actual_count

        for _ in range(byes_needed):
            bye_idea = BookIdea(
                title="BYE",
                logline="Automatic advancement due to insufficient teams.",
                seed=float('inf')
            )
            self.seeded_ideas.append(bye_idea)

    def create_brackets(self):
        """Create and execute tournament brackets."""
        # Ensure we have a power of two
        self._add_byes()
        current_round = self.seeded_ideas

        round_number = 1
        while len(current_round) > 1:
            matches = []
            winners = []
            
            for i in range(0, len(current_round), 2):
                idea_a = current_round[i]
                idea_b = current_round[i + 1]
                
                # Skip match if 'BYE'
                if idea_a.title == "BYE":
                    winner = idea_b
                    raw_response = "BYE - No grading needed"
                elif idea_b.title == "BYE":
                    winner = idea_a
                    raw_response = "BYE - No grading needed"
                else:
                    winner, raw_response = self.determine_winner_with_prompt(idea_a, idea_b)

                match_data = {
                    "idea_a": idea_a,
                    "idea_b": idea_b,
                    "winner": winner,
                    "raw_grading_response": raw_response,
                    "round_number": round_number
                }
                matches.append(match_data)
                winners.append(winner)

            self.rounds.append({
                "round_number": round_number,
                "matches": matches,
                "winners": winners
            })

            current_round = winners
            round_number += 1

    def determine_winner_with_prompt(self, idea_a: BookIdea, idea_b: BookIdea):
        """
        Determine the winner between two ideas using LLM evaluation.
        Returns tuple of (winning idea, raw grading response)
        """
        prompt = f"""
        You are an expert book editor and publisher with extensive knowledge of today's book market.
        You understand what makes books successful across all genres and audiences.
        
        Compare these two book ideas and determine which one is more likely to succeed commercially:
        
        Idea A:
        Title: {idea_a.title}
        Logline: {idea_a.logline}
        {f"Genre: {idea_a.genre}" if idea_a.genre else ""}
        {f"Target Audience: {idea_a.target_audience}" if idea_a.target_audience else ""}
        
        Idea B:
        Title: {idea_b.title}
        Logline: {idea_b.logline}
        {f"Genre: {idea_b.genre}" if idea_b.genre else ""}
        {f"Target Audience: {idea_b.target_audience}" if idea_b.target_audience else ""}
        
        Consider factors like:
        - Market appeal and commercial viability
        - Uniqueness and originality
        - Target audience size and engagement
        - Genre trends and competition
        - Execution potential
        
        Respond with ONLY the letter of the winning idea: A or B
        No additional text, explanation, or formatting.
        """

        try:
            response = self.llm_caller.call_llm(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature
            )

            if response and len(response) > 0:
                raw_grading_response = response.strip()
                
                # Remove thinking tags if present
                if "<think>" in raw_grading_response and "</think>" in raw_grading_response:
                    raw_grading_response = (raw_grading_response.split("<think>")[0] + 
                                          raw_grading_response.split("</think>")[1]).strip()

                # Check if response is a single character
                if len(raw_grading_response) == 1:
                    winner_letter = raw_grading_response.upper()
                    if winner_letter == "A":
                        return idea_a, response['content']
                    elif winner_letter == "B":
                        return idea_b, response['content']

                # If response is unexpected, fall back to random choice
                self.logger.warning(f"Unexpected LLM response: {raw_grading_response}, using random choice")
                return random.choice([idea_a, idea_b]), response['content']

        except Exception as e:
            self.logger.error(f"Error in LLM evaluation: {e}")
            
        # Fallback to random choice
        return random.choice([idea_a, idea_b]), "Error: LLM evaluation failed, random selection used"

    def get_friendly_round_name(self, round_number: int, total_teams: int) -> str:
        """Generate friendly names for tournament rounds."""
        def next_power_of_two(n):
            return 2 ** math.ceil(math.log2(n))

        current_size = next_power_of_two(total_teams)
        is_playin = total_teams != current_size
        
        if is_playin and round_number == 1:
            return "Play-in"
        
        if is_playin:
            round_number -= 1

        teams_in_round = current_size // (2 ** (round_number - 1))

        round_names = {
            2: "Championship",
            4: "Final Four", 
            8: "Elite Eight",
            16: "Sweet Sixteen",
            32: "Round of 32",
            64: "Round of 64",
            128: "Round of 128",
            256: "Round of 256"
        }

        return round_names.get(teams_in_round, f"Round of {teams_in_round}")

    def generate_summary(self) -> str:
        """Generate a textual summary of tournament results."""
        if not self.rounds:
            return "No rounds have been played yet."

        summary = []
        for round_data in self.rounds:
            round_name = self.get_friendly_round_name(round_data["round_number"], self.total_ideas)
            summary.append(f"**{round_name}**")
            summary.append("=" * len(round_name))

            for idx, match in enumerate(round_data["matches"], start=1):
                idea_a = match["idea_a"].title
                idea_b = match["idea_b"].title
                winner = match["winner"].title
                summary.append(f"Match {idx}: {idea_a} vs {idea_b} -> Winner: {winner}")

            summary.append("\n")

        return "\n".join(summary)

    def save_summary_as_json(self, file_path: str):
        """Save tournament summary as JSON."""
        summary = self.generate_summary()
        
        data = {
            "tournament_id": self.tournament_id,
            "total_teams": self.total_teams,
            "rounds": self._serialize_rounds(),
            "summary": summary,
            "completed_at": datetime.datetime.now().isoformat()
        }

        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

    def save_match_data_as_json(self, file_path: str):
        """Save detailed match data as JSON."""
        match_data = []
        
        for round_data in self.rounds:
            for match in round_data["matches"]:
                match_entry = {
                    "tournament_id": self.tournament_id,
                    "round_number": match["round_number"],
                    "idea_a": self._serialize_idea(match["idea_a"]),
                    "idea_b": self._serialize_idea(match["idea_b"]),
                    "winner": self._serialize_idea(match["winner"]),
                    "raw_grading_response": match["raw_grading_response"]
                }
                match_data.append(match_entry)

        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as json_file:
            json.dump(match_data, json_file, indent=4)

    def _serialize_rounds(self) -> List[Dict[str, Any]]:
        """Serialize rounds data for JSON storage."""
        serialized_rounds = []
        
        for round_data in self.rounds:
            serialized_matches = []
            for match in round_data["matches"]:
                serialized_match = {
                    "idea_a": self._serialize_idea(match["idea_a"]),
                    "idea_b": self._serialize_idea(match["idea_b"]),
                    "winner": self._serialize_idea(match["winner"]),
                    "raw_grading_response": match["raw_grading_response"],
                    "round_number": match["round_number"]
                }
                serialized_matches.append(serialized_match)
            
            serialized_round = {
                "round_number": round_data["round_number"],
                "matches": serialized_matches,
                "winners": [self._serialize_idea(winner) for winner in round_data["winners"]]
            }
            serialized_rounds.append(serialized_round)
            
        return serialized_rounds

    def _serialize_idea(self, idea: BookIdea) -> Dict[str, Any]:
        """Serialize a BookIdea for JSON storage."""
        return {
            "title": idea.title,
            "logline": idea.logline,
            "description": idea.description,
            "genre": idea.genre,
            "target_audience": idea.target_audience,
            "seed": idea.seed,
            "status": idea.status
        }

    def get_winner(self) -> Optional[BookIdea]:
        """Get the tournament winner."""
        if not self.rounds:
            return None
        
        final_round = self.rounds[-1]
        if final_round["winners"]:
            return final_round["winners"][0]
        
        return None

    def get_finalists(self) -> List[BookIdea]:
        """Get the final two competitors."""
        if len(self.rounds) < 2:
            return []
        
        semifinal_round = self.rounds[-2]
        return semifinal_round["winners"] if semifinal_round["winners"] else []


class ShowTournamentResults:
    """Display and manage tournament results with enhanced functionality."""
    
    def __init__(self, rounds: List[Dict[str, Any]], number_of_ideas: int):
        self.rounds = rounds
        self.number_of_ideas = number_of_ideas

    def generate_readable_results(self) -> str:
        """Generate human-readable tournament results."""
        readable_summary = []
        readable_summary.append(f"Tournament Results Summary\n{'=' * 30}")
        readable_summary.append(f"Total Ideas: {self.number_of_ideas}")

        for round_result in self.rounds:
            round_name = self._get_friendly_round_name(round_result['round_number'])
            readable_summary.append(f"\n{round_name}\n{'-' * len(round_name)}")
            
            for match in round_result.get('matches', []):
                idea_a = match['idea_a']
                idea_b = match['idea_b']
                winner = match.get('winner')
                
                title1 = idea_a['title'] if isinstance(idea_a, dict) else idea_a.title
                title2 = idea_b['title'] if isinstance(idea_b, dict) else idea_b.title
                seed1 = idea_a.get('seed', '?') if isinstance(idea_a, dict) else getattr(idea_a, 'seed', '?')
                seed2 = idea_b.get('seed', '?') if isinstance(idea_b, dict) else getattr(idea_b, 'seed', '?')

                if winner:
                    winner_title = winner['title'] if isinstance(winner, dict) else winner.title
                    if title1 == winner_title:
                        seed1 = f"W/{seed1}"
                    elif title2 == winner_title:
                        seed2 = f"W/{seed2}"

                readable_summary.append(f"{title1} ({seed1}) v. {title2} ({seed2})")

        # Add champion
        if self.rounds and self.rounds[-1].get('winners'):
            final_winner = self.rounds[-1]['winners'][0]
            winner_title = final_winner['title'] if isinstance(final_winner, dict) else final_winner.title
            readable_summary.append(f"\nChampion: {winner_title}")

        return '\n'.join(readable_summary)

    def _get_friendly_round_name(self, round_number: int) -> str:
        """Get friendly name for a round."""
        # Simplified version - can be enhanced
        round_names = {1: "First Round", 2: "Semifinals", 3: "Finals"}
        return round_names.get(round_number, f"Round {round_number}")

    def save_results_to_csv(self, filename: str):
        """Save tournament results to CSV format."""
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['round_number', 'title1', 'title2', 'seed1', 'seed2', 'winner']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for round_result in self.rounds:
                round_num = round_result.get('round_number')
                
                for match in round_result.get('matches', []):
                    idea_a = match.get('idea_a', {})
                    idea_b = match.get('idea_b', {})
                    winner = match.get('winner', {})
                    
                    title1 = idea_a['title'] if isinstance(idea_a, dict) else getattr(idea_a, 'title', '')
                    title2 = idea_b['title'] if isinstance(idea_b, dict) else getattr(idea_b, 'title', '')
                    seed1 = idea_a.get('seed', '') if isinstance(idea_a, dict) else getattr(idea_a, 'seed', '')
                    seed2 = idea_b.get('seed', '') if isinstance(idea_b, dict) else getattr(idea_b, 'seed', '')
                    winner_title = winner['title'] if isinstance(winner, dict) else getattr(winner, 'title', '')

                    writer.writerow({
                        'round_number': round_num,
                        'title1': title1,
                        'title2': title2,
                        'seed1': seed1,
                        'seed2': seed2,
                        'winner': winner_title
                    })


class TournamentManager:
    """Enhanced tournament management with codexes-factory integration."""
    
    def __init__(self, llm_caller: LLMCaller):
        self.llm_caller = llm_caller
        self.active_tournaments: Dict[str, Tournament] = {}
        self.tournament_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_tournament(self, ideas: List[BookIdea], 
                         tournament_config: Optional[Dict[str, Any]] = None) -> Tournament:
        """Create a new tournament with the given ideas."""
        if len(ideas) < 2:
            raise ValueError("Tournament requires at least 2 ideas")
        
        config = tournament_config or {}
        model = config.get('model', 'ollama/deepseek-r1:latest')
        temperature = config.get('temperature', 0.7)
        
        tournament = Tournament(
            ideas=ideas,
            llm_caller=self.llm_caller,
            model=model,
            temperature=temperature
        )
        
        self.active_tournaments[tournament.tournament_id] = tournament
        self.logger.info(f"Created tournament {tournament.tournament_id} with {len(ideas)} ideas")
        
        return tournament

    def run_tournament(self, tournament: Tournament) -> Dict[str, Any]:
        """Execute a tournament and return results."""
        try:
            self.logger.info(f"Running tournament {tournament.tournament_id}")
            tournament.create_brackets()
            
            results = {
                'tournament_id': tournament.tournament_id,
                'winner': tournament.get_winner(),
                'finalists': tournament.get_finalists(),
                'total_participants': tournament.total_ideas,
                'total_matches': len([match for round_data in tournament.rounds for match in round_data['matches']]),
                'completed_at': datetime.datetime.now().isoformat()
            }
            
            # Move to history
            self.tournament_history.append(results)
            if tournament.tournament_id in self.active_tournaments:
                del self.active_tournaments[tournament.tournament_id]
            
            self.logger.info(f"Tournament {tournament.tournament_id} completed. Winner: {results['winner'].title if results['winner'] else 'None'}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error running tournament {tournament.tournament_id}: {e}")
            raise

    def get_tournament_results(self, tournament_id: str) -> Optional[Dict[str, Any]]:
        """Get results for a specific tournament."""
        for result in self.tournament_history:
            if result['tournament_id'] == tournament_id:
                return result
        return None

    def get_active_tournaments(self) -> Dict[str, Tournament]:
        """Get all currently active tournaments."""
        return self.active_tournaments.copy()

    def get_tournament_history(self) -> List[Dict[str, Any]]:
        """Get history of completed tournaments."""
        return self.tournament_history.copy()