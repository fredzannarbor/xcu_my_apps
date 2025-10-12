"""
Tournament results management and export functionality.
Handles storage, retrieval, and export of tournament results in various formats.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import uuid

from ..core.codex_object import CodexObject
from ..storage.database_manager import IdeationDatabase
from ..storage.file_manager import IdeationFileManager
from .tournament_engine import Tournament, TournamentMatch

logger = logging.getLogger(__name__)


class TournamentResultsManager:
    """
    Manages tournament results storage, retrieval, and export.
    Implements Requirements 1.5 and 1.6 for results storage and export.
    """
    
    def __init__(self, database: IdeationDatabase, file_manager: IdeationFileManager):
        """
        Initialize results manager.
        
        Args:
            database: Database interface for storing results
            file_manager: File manager for exporting results
        """
        self.database = database
        self.file_manager = file_manager
        logger.info("TournamentResultsManager initialized")
    
    def save_tournament_results(self, tournament: Tournament, 
                               participants: List[CodexObject]) -> bool:
        """
        Save comprehensive tournament results.
        
        Args:
            tournament: Completed tournament
            participants: List of participant CodexObjects
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not tournament.is_completed:
                logger.warning(f"Tournament {tournament.uuid} is not completed")
                return False
            
            # Create comprehensive results data
            results_data = self._compile_comprehensive_results(tournament, participants)
            
            # Save to database
            tournament_data = {
                "uuid": tournament.uuid,
                "name": tournament.name,
                "tournament_type": tournament.tournament_type.value,
                "status": tournament.status.value,
                "config": tournament.config,
                "results": results_data,
                "created_timestamp": tournament.created_timestamp,
                "started_timestamp": tournament.started_timestamp,
                "completed_timestamp": tournament.completed_timestamp,
                "participant_count": tournament.participant_count,
                "round_count": tournament.round_count
            }
            
            success = self.database.save_tournament(tournament_data)
            
            if success:
                # Also save to file system for backup
                self.file_manager.file_manager.save_tournament_data(tournament.uuid, tournament_data)
                logger.info(f"Tournament results saved: {tournament.uuid}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving tournament results: {e}")
            return False
    
    def load_tournament_results(self, tournament_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Load tournament results by UUID.
        
        Args:
            tournament_uuid: Tournament UUID
            
        Returns:
            Tournament results data or None if not found
        """
        try:
            tournament_data = self.database.load_tournament(tournament_uuid)
            
            if not tournament_data:
                logger.warning(f"Tournament not found: {tournament_uuid}")
                return None
            
            # Enhance results with additional computed data
            enhanced_results = self._enhance_results_data(tournament_data)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error loading tournament results: {e}")
            return None
    
    def export_results_json(self, tournament_uuid: str, 
                           include_detailed_scores: bool = True) -> Optional[str]:
        """
        Export tournament results to JSON format.
        
        Args:
            tournament_uuid: Tournament UUID
            include_detailed_scores: Whether to include detailed match scores
            
        Returns:
            Path to exported JSON file or None if failed
        """
        try:
            results_data = self.load_tournament_results(tournament_uuid)
            
            if not results_data:
                return None
            
            # Prepare export data
            export_data = self._prepare_json_export(results_data, include_detailed_scores)
            
            # Export to file
            filename = f"tournament_results_{tournament_uuid[:8]}.json"
            export_path = self.file_manager.file_manager.export_to_json(
                export_data, filename, "tournaments"
            )
            
            logger.info(f"Tournament results exported to JSON: {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"Error exporting tournament results to JSON: {e}")
            return None
    
    def export_results_csv(self, tournament_uuid: str) -> Optional[str]:
        """
        Export tournament results to CSV format.
        
        Args:
            tournament_uuid: Tournament UUID
            
        Returns:
            Path to exported CSV file or None if failed
        """
        try:
            results_data = self.load_tournament_results(tournament_uuid)
            
            if not results_data:
                return None
            
            # Prepare CSV data
            csv_data = self._prepare_csv_export(results_data)
            
            # Export to file
            filename = f"tournament_results_{tournament_uuid[:8]}.csv"
            export_path = self.file_manager.file_manager.export_to_csv(
                csv_data, filename, "tournaments"
            )
            
            logger.info(f"Tournament results exported to CSV: {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"Error exporting tournament results to CSV: {e}")
            return None
    
    def generate_bracket_summary(self, tournament_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Generate readable bracket summary with round names.
        Implements Requirement 1.6 for bracket summary.
        
        Args:
            tournament_uuid: Tournament UUID
            
        Returns:
            Bracket summary data or None if failed
        """
        try:
            results_data = self.load_tournament_results(tournament_uuid)
            
            if not results_data:
                return None
            
            # Extract bracket information
            bracket_summary = {
                "tournament_uuid": tournament_uuid,
                "tournament_name": results_data.get("name", "Unknown Tournament"),
                "tournament_type": results_data.get("tournament_type", "unknown"),
                "participant_count": results_data.get("participant_count", 0),
                "round_count": results_data.get("round_count", 0),
                "rounds": {},
                "round_names": {},
                "winner": results_data.get("results", {}).get("winner_uuid"),
                "completed_at": results_data.get("completed_timestamp")
            }
            
            # Generate round names
            round_count = bracket_summary["round_count"]
            participant_count = bracket_summary["participant_count"]
            round_names = self._generate_round_names(round_count, participant_count)
            bracket_summary["round_names"] = round_names
            
            # Extract match results by round
            match_results = results_data.get("results", {}).get("match_results", [])
            
            for match in match_results:
                round_num = match.get("round", 0)
                round_name = round_names.get(round_num, f"Round {round_num}")
                
                if round_name not in bracket_summary["rounds"]:
                    bracket_summary["rounds"][round_name] = []
                
                match_summary = {
                    "match_number": match.get("match", 0),
                    "participants": match.get("participants", []),
                    "winner": match.get("winner"),
                    "evaluation_summary": self._summarize_match_evaluation(match.get("evaluation", {}))
                }
                
                bracket_summary["rounds"][round_name].append(match_summary)
            
            return bracket_summary
            
        except Exception as e:
            logger.error(f"Error generating bracket summary: {e}")
            return None
    
    def get_tournament_statistics(self, tournament_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive tournament statistics.
        
        Args:
            tournament_uuid: Tournament UUID
            
        Returns:
            Tournament statistics or None if failed
        """
        try:
            results_data = self.load_tournament_results(tournament_uuid)
            
            if not results_data:
                return None
            
            results = results_data.get("results", {})
            match_results = results.get("match_results", [])
            rankings = results.get("rankings", [])
            
            # Calculate statistics
            stats = {
                "tournament_info": {
                    "uuid": tournament_uuid,
                    "name": results_data.get("name"),
                    "type": results_data.get("tournament_type"),
                    "participant_count": results_data.get("participant_count", 0),
                    "round_count": results_data.get("round_count", 0),
                    "total_matches": len(match_results),
                    "duration": results.get("tournament_duration")
                },
                "match_statistics": self._calculate_match_statistics(match_results),
                "participant_statistics": self._calculate_participant_statistics(rankings),
                "evaluation_statistics": self._calculate_evaluation_statistics(match_results)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating tournament statistics: {e}")
            return None
    
    def compare_tournaments(self, tournament_uuids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple tournaments.
        
        Args:
            tournament_uuids: List of tournament UUIDs to compare
            
        Returns:
            Comparison data
        """
        try:
            comparisons = {
                "tournaments": [],
                "comparison_metrics": {},
                "summary": {}
            }
            
            tournament_data = []
            
            # Load all tournaments
            for uuid in tournament_uuids:
                results = self.load_tournament_results(uuid)
                if results:
                    tournament_data.append(results)
                    comparisons["tournaments"].append({
                        "uuid": uuid,
                        "name": results.get("name"),
                        "type": results.get("tournament_type"),
                        "participant_count": results.get("participant_count", 0),
                        "completed_at": results.get("completed_timestamp")
                    })
            
            if not tournament_data:
                return {"error": "No valid tournaments found"}
            
            # Calculate comparison metrics
            comparisons["comparison_metrics"] = {
                "average_participant_count": sum(t.get("participant_count", 0) for t in tournament_data) / len(tournament_data),
                "tournament_types": list(set(t.get("tournament_type") for t in tournament_data)),
                "total_tournaments": len(tournament_data),
                "date_range": {
                    "earliest": min(t.get("created_timestamp", "") for t in tournament_data if t.get("created_timestamp")),
                    "latest": max(t.get("completed_timestamp", "") for t in tournament_data if t.get("completed_timestamp"))
                }
            }
            
            return comparisons
            
        except Exception as e:
            logger.error(f"Error comparing tournaments: {e}")
            return {"error": str(e)}
    
    def _compile_comprehensive_results(self, tournament: Tournament, 
                                     participants: List[CodexObject]) -> Dict[str, Any]:
        """Compile comprehensive results data."""
        participant_lookup = {obj.uuid: obj for obj in participants}
        
        # Compile match results
        match_results = []
        for match in tournament.matches:
            if match.is_completed and match.evaluation:
                match_result = {
                    "round": match.round_number,
                    "match": match.match_number,
                    "participants": [match.object1_uuid, match.object2_uuid],
                    "participant_titles": [
                        participant_lookup.get(match.object1_uuid, {}).title if participant_lookup.get(match.object1_uuid) else "Unknown",
                        participant_lookup.get(match.object2_uuid, {}).title if participant_lookup.get(match.object2_uuid) else "Unknown"
                    ],
                    "winner": match.winner_uuid,
                    "winner_title": participant_lookup.get(match.winner_uuid, {}).title if participant_lookup.get(match.winner_uuid) else "Unknown",
                    "evaluation": match.evaluation.to_dict() if hasattr(match.evaluation, 'to_dict') else str(match.evaluation),
                    "completed_at": match.completed_timestamp
                }
                match_results.append(match_result)
        
        # Generate rankings
        rankings = self._generate_detailed_rankings(tournament, participant_lookup)
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(tournament, participants)
        
        return {
            "winner_uuid": tournament.get_winner(),
            "winner_title": participant_lookup.get(tournament.get_winner(), {}).title if tournament.get_winner() and participant_lookup.get(tournament.get_winner()) else "Unknown",
            "match_results": match_results,
            "rankings": rankings,
            "performance_metrics": performance_metrics,
            "tournament_duration": tournament.results.get("tournament_duration"),
            "total_matches": len(match_results),
            "completed_matches": len([m for m in tournament.matches if m.is_completed])
        }
    
    def _enhance_results_data(self, tournament_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance results data with additional computed information."""
        enhanced = tournament_data.copy()
        
        # Add computed fields
        results = enhanced.get("results", {})
        
        # Calculate success rates, average scores, etc.
        match_results = results.get("match_results", [])
        if match_results:
            # Calculate average evaluation scores
            total_scores = {}
            score_counts = {}
            
            for match in match_results:
                evaluation = match.get("evaluation", {})
                scores = evaluation.get("scores", {})
                
                for participant_uuid, participant_scores in scores.items():
                    if participant_uuid not in total_scores:
                        total_scores[participant_uuid] = {}
                        score_counts[participant_uuid] = {}
                    
                    for criterion, score in participant_scores.items():
                        if criterion != "total":
                            if criterion not in total_scores[participant_uuid]:
                                total_scores[participant_uuid][criterion] = 0
                                score_counts[participant_uuid][criterion] = 0
                            total_scores[participant_uuid][criterion] += score
                            score_counts[participant_uuid][criterion] += 1
            
            # Calculate averages
            average_scores = {}
            for participant_uuid in total_scores:
                average_scores[participant_uuid] = {}
                for criterion in total_scores[participant_uuid]:
                    if score_counts[participant_uuid][criterion] > 0:
                        average_scores[participant_uuid][criterion] = (
                            total_scores[participant_uuid][criterion] / 
                            score_counts[participant_uuid][criterion]
                        )
            
            enhanced["results"]["average_scores"] = average_scores
        
        return enhanced
    
    def _prepare_json_export(self, results_data: Dict[str, Any], 
                           include_detailed_scores: bool) -> Dict[str, Any]:
        """Prepare data for JSON export."""
        export_data = {
            "tournament_info": {
                "uuid": results_data.get("uuid"),
                "name": results_data.get("name"),
                "type": results_data.get("tournament_type"),
                "status": results_data.get("status"),
                "participant_count": results_data.get("participant_count"),
                "round_count": results_data.get("round_count"),
                "created_at": results_data.get("created_timestamp"),
                "started_at": results_data.get("started_timestamp"),
                "completed_at": results_data.get("completed_timestamp")
            },
            "results": {
                "winner": results_data.get("results", {}).get("winner_uuid"),
                "winner_title": results_data.get("results", {}).get("winner_title"),
                "rankings": results_data.get("results", {}).get("rankings", []),
                "match_results": []
            },
            "export_info": {
                "exported_at": datetime.now().isoformat(),
                "include_detailed_scores": include_detailed_scores
            }
        }
        
        # Add match results
        match_results = results_data.get("results", {}).get("match_results", [])
        for match in match_results:
            match_export = {
                "round": match.get("round"),
                "match": match.get("match"),
                "participants": match.get("participant_titles", match.get("participants", [])),
                "winner": match.get("winner_title", match.get("winner")),
                "completed_at": match.get("completed_at")
            }
            
            if include_detailed_scores:
                match_export["evaluation"] = match.get("evaluation", {})
            
            export_data["results"]["match_results"].append(match_export)
        
        return export_data
    
    def _prepare_csv_export(self, results_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare data for CSV export."""
        csv_data = []
        
        # Tournament info row
        csv_data.append({
            "Type": "Tournament Info",
            "Name": results_data.get("name", ""),
            "Tournament Type": results_data.get("tournament_type", ""),
            "Participants": results_data.get("participant_count", 0),
            "Rounds": results_data.get("round_count", 0),
            "Winner": results_data.get("results", {}).get("winner_title", ""),
            "Completed": results_data.get("completed_timestamp", "")
        })
        
        # Match results
        match_results = results_data.get("results", {}).get("match_results", [])
        for match in match_results:
            evaluation = match.get("evaluation", {})
            
            csv_data.append({
                "Type": "Match Result",
                "Round": match.get("round", ""),
                "Match": match.get("match", ""),
                "Participant 1": match.get("participant_titles", ["", ""])[0] if len(match.get("participant_titles", [])) > 0 else "",
                "Participant 2": match.get("participant_titles", ["", ""])[1] if len(match.get("participant_titles", [])) > 1 else "",
                "Winner": match.get("winner_title", ""),
                "Reasoning": evaluation.get("reasoning", ""),
                "Completed": match.get("completed_at", "")
            })
        
        # Rankings
        rankings = results_data.get("results", {}).get("rankings", [])
        for ranking in rankings:
            csv_data.append({
                "Type": "Ranking",
                "Rank": ranking.get("rank", ""),
                "Participant": ranking.get("uuid", ""),
                "Wins": ranking.get("wins", 0),
                "Losses": ranking.get("losses", 0),
                "Rounds Reached": ranking.get("rounds_reached", 0)
            })
        
        return csv_data
    
    def _generate_round_names(self, round_count: int, participant_count: int) -> Dict[int, str]:
        """Generate appropriate round names."""
        if round_count <= 1:
            return {1: "Final"}
        elif round_count == 2:
            return {1: "Semifinal", 2: "Final"}
        elif round_count == 3:
            return {1: "Quarterfinal", 2: "Semifinal", 3: "Final"}
        elif round_count == 4:
            return {1: "Round of 16", 2: "Quarterfinal", 3: "Semifinal", 4: "Final"}
        elif round_count == 5:
            return {1: "Round of 32", 2: "Round of 16", 3: "Quarterfinal", 4: "Semifinal", 5: "Final"}
        else:
            names = {}
            for i in range(1, round_count + 1):
                if i == round_count:
                    names[i] = "Final"
                elif i == round_count - 1:
                    names[i] = "Semifinal"
                elif i == round_count - 2:
                    names[i] = "Quarterfinal"
                else:
                    names[i] = f"Round {i}"
            return names
    
    def _summarize_match_evaluation(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize match evaluation for bracket display."""
        if not evaluation:
            return {}
        
        return {
            "reasoning_summary": evaluation.get("reasoning", "")[:100] + "..." if len(evaluation.get("reasoning", "")) > 100 else evaluation.get("reasoning", ""),
            "confidence": evaluation.get("confidence_score", 0),
            "evaluation_quality": evaluation.get("metadata", {}).get("evaluation_quality", "unknown")
        }
    
    def _generate_detailed_rankings(self, tournament: Tournament, 
                                  participant_lookup: Dict[str, CodexObject]) -> List[Dict[str, Any]]:
        """Generate detailed participant rankings."""
        rankings = []
        
        # Calculate performance for each participant
        for uuid in tournament.participant_uuids:
            participant = participant_lookup.get(uuid)
            
            wins = 0
            losses = 0
            rounds_reached = 0
            total_score = 0
            match_count = 0
            
            # Analyze matches
            for match in tournament.matches:
                if match.object1_uuid == uuid or match.object2_uuid == uuid:
                    if match.is_completed:
                        match_count += 1
                        rounds_reached = max(rounds_reached, match.round_number)
                        
                        if match.winner_uuid == uuid:
                            wins += 1
                        else:
                            losses += 1
                        
                        # Add scores if available
                        if match.evaluation and match.evaluation.scores:
                            participant_scores = match.evaluation.scores.get(uuid, {})
                            total_score += participant_scores.get("total", 0)
            
            ranking = {
                "uuid": uuid,
                "title": participant.title if participant else "Unknown",
                "object_type": participant.object_type.value if participant else "unknown",
                "wins": wins,
                "losses": losses,
                "rounds_reached": rounds_reached,
                "average_score": total_score / match_count if match_count > 0 else 0,
                "match_count": match_count
            }
            
            rankings.append(ranking)
        
        # Sort by performance
        rankings.sort(key=lambda x: (x["rounds_reached"], x["wins"], x["average_score"]), reverse=True)
        
        # Add rank positions
        for i, ranking in enumerate(rankings, 1):
            ranking["rank"] = i
        
        return rankings
    
    def _calculate_performance_metrics(self, tournament: Tournament, 
                                     participants: List[CodexObject]) -> Dict[str, Any]:
        """Calculate overall tournament performance metrics."""
        metrics = {
            "completion_rate": len(tournament.get_completed_matches()) / len(tournament.matches) if tournament.matches else 0,
            "average_match_duration": "N/A",  # Would need match timing data
            "evaluation_quality_distribution": {},
            "score_distributions": {}
        }
        
        # Analyze evaluation quality
        quality_counts = {}
        for match in tournament.get_completed_matches():
            if match.evaluation and hasattr(match.evaluation, 'metadata'):
                quality = match.evaluation.metadata.get("evaluation_quality", "unknown")
                quality_counts[quality] = quality_counts.get(quality, 0) + 1
        
        metrics["evaluation_quality_distribution"] = quality_counts
        
        return metrics
    
    def _calculate_match_statistics(self, match_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate match-level statistics."""
        if not match_results:
            return {}
        
        total_matches = len(match_results)
        
        # Count matches by round
        round_counts = {}
        for match in match_results:
            round_num = match.get("round", 0)
            round_counts[round_num] = round_counts.get(round_num, 0) + 1
        
        return {
            "total_matches": total_matches,
            "matches_by_round": round_counts,
            "average_matches_per_round": total_matches / len(round_counts) if round_counts else 0
        }
    
    def _calculate_participant_statistics(self, rankings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate participant-level statistics."""
        if not rankings:
            return {}
        
        total_participants = len(rankings)
        total_wins = sum(r.get("wins", 0) for r in rankings)
        total_losses = sum(r.get("losses", 0) for r in rankings)
        
        return {
            "total_participants": total_participants,
            "total_wins": total_wins,
            "total_losses": total_losses,
            "average_wins_per_participant": total_wins / total_participants if total_participants else 0,
            "average_losses_per_participant": total_losses / total_participants if total_participants else 0
        }
    
    def _calculate_evaluation_statistics(self, match_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate evaluation-level statistics."""
        if not match_results:
            return {}
        
        evaluations_with_scores = 0
        total_confidence = 0
        confidence_count = 0
        
        for match in match_results:
            evaluation = match.get("evaluation", {})
            if evaluation.get("scores"):
                evaluations_with_scores += 1
            
            confidence = evaluation.get("confidence_score")
            if confidence is not None:
                total_confidence += confidence
                confidence_count += 1
        
        return {
            "evaluations_with_scores": evaluations_with_scores,
            "evaluation_score_rate": evaluations_with_scores / len(match_results) if match_results else 0,
            "average_confidence": total_confidence / confidence_count if confidence_count else 0
        }