"""
Advanced tournament features including multiple formats and custom judging criteria.
"""

import logging
import random
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from .book_idea import BookIdea
from .legacy_tournament import Tournament, TournamentManager
from ...core.llm_integration import LLMCaller

logger = logging.getLogger(__name__)


class TournamentFormat(Enum):
    """Tournament format types."""
    SINGLE_ELIMINATION = "single_elimination"
    DOUBLE_ELIMINATION = "double_elimination"
    ROUND_ROBIN = "round_robin"
    SWISS_SYSTEM = "swiss_system"


@dataclass
class JudgingCriteria:
    """Custom judging criteria for tournaments."""
    name: str
    description: str
    weight: float = 1.0
    prompt_template: str = ""
    scoring_range: tuple = (0, 10)


@dataclass
class AdvancedTournamentConfig:
    """Configuration for advanced tournaments."""
    format: TournamentFormat = TournamentFormat.SINGLE_ELIMINATION
    judging_criteria: List[JudgingCriteria] = field(default_factory=list)
    seeding_strategy: str = "random"  # random, rating_based, manual
    imprint_specific: bool = False
    imprint_name: Optional[str] = None
    model: str = "mistral"
    temperature: float = 0.7
    max_rounds: Optional[int] = None
    tiebreaker_method: str = "random"  # random, criteria_weighted, head_to_head


class AdvancedTournament(Tournament):
    """Enhanced tournament with advanced features."""
    
    def __init__(self, ideas: List[BookIdea], llm_caller: LLMCaller, 
                 config: AdvancedTournamentConfig):
        # Initialize base tournament
        super().__init__(ideas, llm_caller, config.model, config.temperature)
        
        self.config = config
        self.format = config.format
        self.judging_criteria = config.judging_criteria or self._get_default_criteria()
        self.seeding_strategy = config.seeding_strategy
        
        # Advanced tournament state
        self.standings = {}
        self.detailed_scores = {}
        self.round_results = []
        
        # Apply seeding strategy
        self._apply_seeding_strategy()

    def _get_default_criteria(self) -> List[JudgingCriteria]:
        """Get default judging criteria."""
        return [
            JudgingCriteria(
                name="Market Appeal",
                description="Commercial viability and market potential",
                weight=1.0,
                prompt_template="Rate the market appeal of this book idea on a scale of 1-10"
            ),
            JudgingCriteria(
                name="Originality",
                description="Uniqueness and creative innovation",
                weight=0.8,
                prompt_template="Rate the originality and uniqueness of this book idea on a scale of 1-10"
            ),
            JudgingCriteria(
                name="Execution Potential",
                description="How well the idea could be executed as a book",
                weight=0.9,
                prompt_template="Rate how well this idea could be executed as a book on a scale of 1-10"
            )
        ]

    def _apply_seeding_strategy(self):
        """Apply the configured seeding strategy."""
        if self.seeding_strategy == "rating_based":
            self._apply_rating_based_seeding()
        elif self.seeding_strategy == "manual":
            self._apply_manual_seeding()
        else:
            # Default random seeding already applied in parent class
            pass

    def _apply_rating_based_seeding(self):
        """Apply rating-based seeding using reader feedback or quality metrics."""
        # Sort ideas by quality metrics if available
        def get_idea_rating(idea: BookIdea) -> float:
            if hasattr(idea, 'reader_feedback') and idea.reader_feedback:
                ratings = [fb.get('overall_rating', 5.0) for fb in idea.reader_feedback]
                return sum(ratings) / len(ratings)
            return idea.imprint_alignment or 5.0
        
        # Sort by rating (highest first) and assign seeds
        sorted_ideas = sorted(self.seeded_ideas, key=get_idea_rating, reverse=True)
        
        for i, idea in enumerate(sorted_ideas):
            idea.seed = i + 1

    def _apply_manual_seeding(self):
        """Apply manual seeding (placeholder for UI integration)."""
        # This would be implemented with UI input
        # For now, use random seeding
        pass  
  def create_brackets(self):
        """Create brackets based on tournament format."""
        if self.format == TournamentFormat.SINGLE_ELIMINATION:
            self._create_single_elimination_brackets()
        elif self.format == TournamentFormat.DOUBLE_ELIMINATION:
            self._create_double_elimination_brackets()
        elif self.format == TournamentFormat.ROUND_ROBIN:
            self._create_round_robin_brackets()
        elif self.format == TournamentFormat.SWISS_SYSTEM:
            self._create_swiss_system_brackets()

    def _create_single_elimination_brackets(self):
        """Create single elimination tournament brackets."""
        # Use parent class implementation
        super().create_brackets()

    def _create_double_elimination_brackets(self):
        """Create double elimination tournament brackets."""
        # Implement double elimination logic
        self._add_byes()
        
        winners_bracket = self.seeded_ideas.copy()
        losers_bracket = []
        
        round_number = 1
        
        while len(winners_bracket) > 1 or len(losers_bracket) > 0:
            matches = []
            
            # Winners bracket matches
            if len(winners_bracket) > 1:
                winners_matches, winners_winners, winners_losers = self._run_bracket_round(
                    winners_bracket, round_number, "Winners"
                )
                matches.extend(winners_matches)
                winners_bracket = winners_winners
                losers_bracket.extend(winners_losers)
            
            # Losers bracket matches
            if len(losers_bracket) > 1:
                losers_matches, losers_winners, _ = self._run_bracket_round(
                    losers_bracket, round_number, "Losers"
                )
                matches.extend(losers_matches)
                losers_bracket = losers_winners
            
            if matches:
                self.rounds.append({
                    "round_number": round_number,
                    "matches": matches,
                    "winners": winners_bracket + losers_bracket
                })
            
            round_number += 1
            
            # Final match between winners bracket champion and losers bracket champion
            if len(winners_bracket) == 1 and len(losers_bracket) == 1:
                final_match = self._create_match(winners_bracket[0], losers_bracket[0], round_number)
                self.rounds.append({
                    "round_number": round_number,
                    "matches": [final_match],
                    "winners": [final_match["winner"]]
                })
                break

    def _create_round_robin_brackets(self):
        """Create round robin tournament brackets."""
        participants = self.seeded_ideas.copy()
        
        # Remove byes for round robin
        participants = [idea for idea in participants if idea.title != "BYE"]
        
        round_number = 1
        
        # Generate all possible pairings
        for i in range(len(participants)):
            for j in range(i + 1, len(participants)):
                idea_a = participants[i]
                idea_b = participants[j]
                
                match = self._create_match(idea_a, idea_b, round_number)
                
                self.rounds.append({
                    "round_number": round_number,
                    "matches": [match],
                    "winners": [match["winner"]]
                })
                
                round_number += 1
        
        # Calculate final standings
        self._calculate_round_robin_standings()

    def _create_swiss_system_brackets(self):
        """Create Swiss system tournament brackets."""
        participants = [idea for idea in self.seeded_ideas if idea.title != "BYE"]
        max_rounds = self.config.max_rounds or min(8, len(participants) - 1)
        
        # Initialize standings
        for idea in participants:
            self.standings[idea.title] = {
                'wins': 0,
                'losses': 0,
                'opponents': [],
                'idea': idea
            }
        
        for round_num in range(1, max_rounds + 1):
            # Pair participants based on current standings
            pairings = self._create_swiss_pairings(participants, round_num)
            
            matches = []
            round_winners = []
            
            for idea_a, idea_b in pairings:
                match = self._create_match(idea_a, idea_b, round_num)
                matches.append(match)
                round_winners.append(match["winner"])
                
                # Update standings
                winner = match["winner"]
                loser = idea_a if winner == idea_b else idea_b
                
                self.standings[winner.title]['wins'] += 1
                self.standings[loser.title]['losses'] += 1
                self.standings[winner.title]['opponents'].append(loser.title)
                self.standings[loser.title]['opponents'].append(winner.title)
            
            self.rounds.append({
                "round_number": round_num,
                "matches": matches,
                "winners": round_winners
            })

    def _run_bracket_round(self, bracket: List[BookIdea], round_number: int, 
                          bracket_name: str) -> tuple:
        """Run a single round for a bracket."""
        matches = []
        winners = []
        losers = []
        
        for i in range(0, len(bracket), 2):
            if i + 1 < len(bracket):
                idea_a = bracket[i]
                idea_b = bracket[i + 1]
                
                match = self._create_match(idea_a, idea_b, round_number)
                match["bracket"] = bracket_name
                
                matches.append(match)
                winners.append(match["winner"])
                
                loser = idea_a if match["winner"] == idea_b else idea_b
                losers.append(loser)
            else:
                # Bye
                winners.append(bracket[i])
        
        return matches, winners, losers

    def _create_match(self, idea_a: BookIdea, idea_b: BookIdea, round_number: int) -> Dict[str, Any]:
        """Create a single match with advanced judging."""
        if idea_a.title == "BYE":
            winner = idea_b
            raw_response = "BYE - No judging needed"
            detailed_scores = {}
        elif idea_b.title == "BYE":
            winner = idea_a
            raw_response = "BYE - No judging needed"
            detailed_scores = {}
        else:
            winner, raw_response, detailed_scores = self._judge_match_with_criteria(idea_a, idea_b)
        
        match = {
            "idea_a": idea_a,
            "idea_b": idea_b,
            "winner": winner,
            "raw_grading_response": raw_response,
            "detailed_scores": detailed_scores,
            "round_number": round_number
        }
        
        return match

    def _judge_match_with_criteria(self, idea_a: BookIdea, idea_b: BookIdea) -> tuple:
        """Judge a match using custom criteria."""
        detailed_scores = {
            'idea_a': {},
            'idea_b': {},
            'criteria_weights': {}
        }
        
        total_score_a = 0.0
        total_score_b = 0.0
        total_weight = 0.0
        
        for criteria in self.judging_criteria:
            try:
                score_a, score_b = self._evaluate_ideas_by_criteria(idea_a, idea_b, criteria)
                
                detailed_scores['idea_a'][criteria.name] = score_a
                detailed_scores['idea_b'][criteria.name] = score_b
                detailed_scores['criteria_weights'][criteria.name] = criteria.weight
                
                total_score_a += score_a * criteria.weight
                total_score_b += score_b * criteria.weight
                total_weight += criteria.weight
                
            except Exception as e:
                logger.error(f"Error evaluating criteria {criteria.name}: {e}")
                # Use default scores
                detailed_scores['idea_a'][criteria.name] = 5.0
                detailed_scores['idea_b'][criteria.name] = 5.0
                detailed_scores['criteria_weights'][criteria.name] = criteria.weight
                
                total_score_a += 5.0 * criteria.weight
                total_score_b += 5.0 * criteria.weight
                total_weight += criteria.weight
        
        # Calculate final scores
        final_score_a = total_score_a / total_weight if total_weight > 0 else 5.0
        final_score_b = total_score_b / total_weight if total_weight > 0 else 5.0
        
        detailed_scores['final_scores'] = {
            'idea_a': final_score_a,
            'idea_b': final_score_b
        }
        
        # Determine winner
        if abs(final_score_a - final_score_b) < 0.1:  # Very close scores
            winner = self._apply_tiebreaker(idea_a, idea_b, detailed_scores)
        else:
            winner = idea_a if final_score_a > final_score_b else idea_b
        
        # Create response summary
        response_summary = f"Detailed judging completed. Final scores: {idea_a.title}: {final_score_a:.2f}, {idea_b.title}: {final_score_b:.2f}"
        
        return winner, response_summary, detailed_scores

    def _evaluate_ideas_by_criteria(self, idea_a: BookIdea, idea_b: BookIdea, 
                                   criteria: JudgingCriteria) -> tuple:
        """Evaluate two ideas based on specific criteria."""
        prompt = f"""
        You are an expert book editor evaluating ideas based on {criteria.name}.
        
        {criteria.description}
        
        Idea A:
        Title: {idea_a.title}
        Logline: {idea_a.logline}
        {f"Description: {idea_a.description}" if idea_a.description else ""}
        
        Idea B:
        Title: {idea_b.title}
        Logline: {idea_b.logline}
        {f"Description: {idea_b.description}" if idea_b.description else ""}
        
        Rate each idea on {criteria.name} using a scale of {criteria.scoring_range[0]}-{criteria.scoring_range[1]}.
        
        Respond in this exact format:
        Idea A: [score]
        Idea B: [score]
        
        No additional text or explanation.
        """
        
        try:
            response = self.llm_caller.call_llm(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature
            )
            
            if response and response.get('content'):
                return self._parse_criteria_scores(response['content'], criteria.scoring_range)
            
        except Exception as e:
            logger.error(f"Error in criteria evaluation: {e}")
        
        # Fallback to random scores within range
        min_score, max_score = criteria.scoring_range
        score_a = random.uniform(min_score, max_score)
        score_b = random.uniform(min_score, max_score)
        
        return score_a, score_b

    def _parse_criteria_scores(self, content: str, scoring_range: tuple) -> tuple:
        """Parse scores from LLM response."""
        lines = content.strip().split('\n')
        score_a = scoring_range[0] + (scoring_range[1] - scoring_range[0]) / 2  # Default to middle
        score_b = scoring_range[0] + (scoring_range[1] - scoring_range[0]) / 2
        
        for line in lines:
            line = line.strip()
            if line.startswith('Idea A:'):
                try:
                    score_a = float(line.split(':')[1].strip())
                except:
                    pass
            elif line.startswith('Idea B:'):
                try:
                    score_b = float(line.split(':')[1].strip())
                except:
                    pass
        
        # Clamp scores to valid range
        min_score, max_score = scoring_range
        score_a = max(min_score, min(max_score, score_a))
        score_b = max(min_score, min(max_score, score_b))
        
        return score_a, score_b

    def _apply_tiebreaker(self, idea_a: BookIdea, idea_b: BookIdea, 
                         detailed_scores: Dict[str, Any]) -> BookIdea:
        """Apply tiebreaker method for very close matches."""
        if self.config.tiebreaker_method == "criteria_weighted":
            # Use highest weighted criteria as tiebreaker
            max_weight = 0
            tiebreaker_winner = idea_a
            
            for criteria_name, weight in detailed_scores['criteria_weights'].items():
                if weight > max_weight:
                    max_weight = weight
                    score_a = detailed_scores['idea_a'][criteria_name]
                    score_b = detailed_scores['idea_b'][criteria_name]
                    tiebreaker_winner = idea_a if score_a > score_b else idea_b
            
            return tiebreaker_winner
        
        else:  # Random tiebreaker
            return random.choice([idea_a, idea_b])

    def _create_swiss_pairings(self, participants: List[BookIdea], round_num: int) -> List[tuple]:
        """Create pairings for Swiss system tournament."""
        # Sort by current standings (wins, then by rating if available)
        def sort_key(idea):
            standing = self.standings[idea.title]
            wins = standing['wins']
            # Use reader feedback rating as secondary sort if available
            rating = 0.0
            if hasattr(idea, 'reader_feedback') and idea.reader_feedback:
                ratings = [fb.get('overall_rating', 5.0) for fb in idea.reader_feedback]
                rating = sum(ratings) / len(ratings)
            return (-wins, -rating)  # Negative for descending order
        
        sorted_participants = sorted(participants, key=sort_key)
        
        pairings = []
        used = set()
        
        for i, idea_a in enumerate(sorted_participants):
            if idea_a.title in used:
                continue
            
            # Find best opponent who hasn't played against idea_a
            for j in range(i + 1, len(sorted_participants)):
                idea_b = sorted_participants[j]
                
                if (idea_b.title not in used and 
                    idea_b.title not in self.standings[idea_a.title]['opponents']):
                    
                    pairings.append((idea_a, idea_b))
                    used.add(idea_a.title)
                    used.add(idea_b.title)
                    break
            else:
                # If no valid opponent found, pair with next available
                for j in range(i + 1, len(sorted_participants)):
                    idea_b = sorted_participants[j]
                    if idea_b.title not in used:
                        pairings.append((idea_a, idea_b))
                        used.add(idea_a.title)
                        used.add(idea_b.title)
                        break
        
        return pairings

    def _calculate_round_robin_standings(self):
        """Calculate final standings for round robin tournament."""
        standings = {}
        
        # Initialize standings
        for idea in self.seeded_ideas:
            if idea.title != "BYE":
                standings[idea.title] = {
                    'wins': 0,
                    'losses': 0,
                    'points': 0,
                    'idea': idea
                }
        
        # Count wins and losses
        for round_data in self.rounds:
            for match in round_data['matches']:
                winner = match['winner']
                loser = match['idea_a'] if winner == match['idea_b'] else match['idea_b']
                
                if winner.title in standings:
                    standings[winner.title]['wins'] += 1
                    standings[winner.title]['points'] += 3  # 3 points for win
                
                if loser.title in standings:
                    standings[loser.title]['losses'] += 1
        
        # Sort by points, then by wins
        self.standings = dict(sorted(
            standings.items(),
            key=lambda x: (x[1]['points'], x[1]['wins']),
            reverse=True
        ))

    def get_tournament_analytics(self) -> Dict[str, Any]:
        """Get detailed tournament analytics."""
        analytics = {
            'format': self.format.value,
            'total_participants': self.total_ideas,
            'total_rounds': len(self.rounds),
            'judging_criteria': [
                {
                    'name': criteria.name,
                    'weight': criteria.weight,
                    'description': criteria.description
                }
                for criteria in self.judging_criteria
            ],
            'seeding_strategy': self.seeding_strategy,
            'detailed_match_analysis': self._analyze_matches(),
            'performance_by_criteria': self._analyze_criteria_performance(),
            'standings': self.standings if hasattr(self, 'standings') else {}
        }
        
        return analytics

    def _analyze_matches(self) -> Dict[str, Any]:
        """Analyze match results for insights."""
        total_matches = sum(len(round_data['matches']) for round_data in self.rounds)
        close_matches = 0
        blowout_matches = 0
        
        criteria_impact = {criteria.name: [] for criteria in self.judging_criteria}
        
        for round_data in self.rounds:
            for match in round_data['matches']:
                detailed_scores = match.get('detailed_scores', {})
                
                if 'final_scores' in detailed_scores:
                    score_a = detailed_scores['final_scores']['idea_a']
                    score_b = detailed_scores['final_scores']['idea_b']
                    score_diff = abs(score_a - score_b)
                    
                    if score_diff < 0.5:
                        close_matches += 1
                    elif score_diff > 2.0:
                        blowout_matches += 1
                    
                    # Analyze criteria impact
                    for criteria_name in criteria_impact.keys():
                        if criteria_name in detailed_scores.get('idea_a', {}):
                            criteria_score_a = detailed_scores['idea_a'][criteria_name]
                            criteria_score_b = detailed_scores['idea_b'][criteria_name]
                            criteria_impact[criteria_name].append(abs(criteria_score_a - criteria_score_b))
        
        return {
            'total_matches': total_matches,
            'close_matches': close_matches,
            'blowout_matches': blowout_matches,
            'close_match_percentage': (close_matches / total_matches * 100) if total_matches > 0 else 0,
            'criteria_discrimination': {
                name: {
                    'average_difference': sum(diffs) / len(diffs) if diffs else 0,
                    'max_difference': max(diffs) if diffs else 0
                }
                for name, diffs in criteria_impact.items()
            }
        }

    def _analyze_criteria_performance(self) -> Dict[str, Any]:
        """Analyze how different criteria performed in the tournament."""
        criteria_stats = {}
        
        for criteria in self.judging_criteria:
            scores = []
            
            for round_data in self.rounds:
                for match in round_data['matches']:
                    detailed_scores = match.get('detailed_scores', {})
                    
                    if criteria.name in detailed_scores.get('idea_a', {}):
                        scores.append(detailed_scores['idea_a'][criteria.name])
                    if criteria.name in detailed_scores.get('idea_b', {}):
                        scores.append(detailed_scores['idea_b'][criteria.name])
            
            if scores:
                criteria_stats[criteria.name] = {
                    'average_score': sum(scores) / len(scores),
                    'min_score': min(scores),
                    'max_score': max(scores),
                    'score_range': max(scores) - min(scores),
                    'weight': criteria.weight
                }
        
        return criteria_stats


class AdvancedTournamentManager(TournamentManager):
    """Enhanced tournament manager with advanced features."""
    
    def __init__(self, llm_caller: LLMCaller):
        super().__init__(llm_caller)
        self.tournament_templates = {}
        self.imprint_configurations = {}

    def create_advanced_tournament(self, ideas: List[BookIdea], 
                                 config: AdvancedTournamentConfig) -> AdvancedTournament:
        """Create an advanced tournament with custom configuration."""
        if len(ideas) < 2:
            raise ValueError("Tournament requires at least 2 ideas")
        
        tournament = AdvancedTournament(ideas, self.llm_caller, config)
        self.active_tournaments[tournament.tournament_id] = tournament
        
        self.logger.info(f"Created advanced tournament {tournament.tournament_id} "
                        f"with format {config.format.value}")
        
        return tournament

    def create_imprint_specific_tournament(self, ideas: List[BookIdea], 
                                         imprint_name: str) -> AdvancedTournament:
        """Create a tournament with imprint-specific judging criteria."""
        config = self._get_imprint_tournament_config(imprint_name)
        config.imprint_specific = True
        config.imprint_name = imprint_name
        
        return self.create_advanced_tournament(ideas, config)

    def _get_imprint_tournament_config(self, imprint_name: str) -> AdvancedTournamentConfig:
        """Get tournament configuration for a specific imprint."""
        # Load imprint-specific criteria if available
        if imprint_name in self.imprint_configurations:
            return self.imprint_configurations[imprint_name]
        
        # Create default configuration with imprint-specific criteria
        criteria = self._create_imprint_criteria(imprint_name)
        
        config = AdvancedTournamentConfig(
            format=TournamentFormat.SINGLE_ELIMINATION,
            judging_criteria=criteria,
            seeding_strategy="rating_based",
            model="mistral",
            temperature=0.7
        )
        
        self.imprint_configurations[imprint_name] = config
        return config

    def _create_imprint_criteria(self, imprint_name: str) -> List[JudgingCriteria]:
        """Create judging criteria specific to an imprint."""
        # This would be customized based on imprint focus
        # For now, return enhanced default criteria
        
        base_criteria = [
            JudgingCriteria(
                name="Market Appeal",
                description=f"Commercial viability for {imprint_name} audience",
                weight=1.0
            ),
            JudgingCriteria(
                name="Brand Alignment",
                description=f"How well the idea fits {imprint_name} brand",
                weight=1.2
            ),
            JudgingCriteria(
                name="Execution Potential",
                description="Feasibility of successful book development",
                weight=0.9
            )
        ]
        
        # Add imprint-specific criteria based on focus
        if "science" in imprint_name.lower() or "tech" in imprint_name.lower():
            base_criteria.append(JudgingCriteria(
                name="Technical Accuracy",
                description="Scientific or technical credibility",
                weight=0.8
            ))
        
        if "literary" in imprint_name.lower():
            base_criteria.append(JudgingCriteria(
                name="Literary Merit",
                description="Artistic and literary quality",
                weight=1.1
            ))
        
        return base_criteria

    def save_tournament_template(self, name: str, config: AdvancedTournamentConfig):
        """Save a tournament configuration as a reusable template."""
        self.tournament_templates[name] = config
        self.logger.info(f"Saved tournament template: {name}")

    def load_tournament_template(self, name: str) -> Optional[AdvancedTournamentConfig]:
        """Load a saved tournament template."""
        return self.tournament_templates.get(name)

    def get_tournament_analytics(self, tournament_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a specific tournament."""
        if tournament_id in self.active_tournaments:
            tournament = self.active_tournaments[tournament_id]
            if isinstance(tournament, AdvancedTournament):
                return tournament.get_tournament_analytics()
        
        return None