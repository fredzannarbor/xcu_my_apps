"""
Ideation integration for batch operations.
Creates tournaments for multiple imprints.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import time
import uuid

from .models import (
    IdeationBatchResult,
    TournamentRecord,
    TournamentConfig
)
from .config_loader import BatchConfigLoader

# Import imprint and ideation modules
try:
    from codexes.modules.imprints.services.imprint_manager import ImprintManager
    from codexes.modules.imprints.models.publisher_persona import PublisherPersona
    from codexes.modules.ideation.book_idea import BookIdea
    from codexes.modules.ideation.continuous.auto_tournament import AutoTournamentExecutor, TournamentConfiguration
    from codexes.core.llm_caller import call_model_with_prompt
    from codexes.modules.supplementary import load_imprint_supplementary_materials, get_largest_context_model
except ImportError:
    from src.codexes.modules.imprints.services.imprint_manager import ImprintManager
    from src.codexes.modules.imprints.models.publisher_persona import PublisherPersona
    from src.codexes.modules.ideation.book_idea import BookIdea
    from src.codexes.modules.ideation.continuous.auto_tournament import AutoTournamentExecutor, TournamentConfiguration
    from src.codexes.core.llm_caller import call_model_with_prompt
    from src.codexes.modules.supplementary import load_imprint_supplementary_materials, get_largest_context_model

logger = logging.getLogger(__name__)


def create_ideation_tournaments(
    source_paths: List[Path],
    selected_imprints: Optional[List[str]] = None,
    tournament_config: Optional[TournamentConfig] = None,
    integration_mode: str = "full",
    use_supplementary: bool = False
) -> IdeationBatchResult:
    """
    Create ideation tournaments for multiple imprints.

    Process:
    1. Load imprint configs/directories
    2. For each imprint:
       a. Extract publisher persona
       b. Generate N ideas aligned with imprint focus
       c. Create Tournament instance
       d. Run evaluation if mode == "full"
    3. Aggregate results
    4. Export to Ideation Dashboard

    Args:
        source_paths: List of paths to search for imprints
        selected_imprints: Specific imprints to process (None = all)
        tournament_config: Tournament configuration
        integration_mode: "ideas_only", "generate_and_run", or "full"

    Returns:
        IdeationBatchResult with tournament details
    """
    start_time = time.time()
    result = IdeationBatchResult()

    # Use default config if not provided
    if tournament_config is None:
        tournament_config = TournamentConfig()

    # Initialize services
    imprint_manager = ImprintManager()
    imprint_manager.scan_imprints()
    tournament_executor = AutoTournamentExecutor()

    try:
        # Load imprint configurations
        loader = BatchConfigLoader()
        loader.load_configs_from_paths(source_paths)
        configs = loader.get_all_configs()

        # Filter to selected imprints if specified
        if selected_imprints:
            configs = {
                name: config for name, config in configs.items()
                if name in selected_imprints
            }

        logger.info(f"Processing {len(configs)} imprints for ideation tournaments")

        # Process each imprint
        for imprint_name, config in configs.items():
            logger.info(f"Creating tournament for imprint: {imprint_name}")

            try:
                # Generate ideas for this imprint
                ideas = generate_imprint_ideas(
                    imprint_name,
                    config,
                    tournament_config,
                    use_supplementary
                )

                if not ideas:
                    logger.warning(f"No ideas generated for {imprint_name}")
                    result.failed_imprints.append(imprint_name)
                    continue

                # Create tournament if integration_mode requires it
                if integration_mode in ["generate_and_run", "full"]:
                    tournament_result = create_tournament_for_imprint(
                        imprint_name,
                        ideas,
                        tournament_config,
                        tournament_executor
                    )

                    if tournament_result:
                        # Create tournament record
                        record = TournamentRecord(
                            tournament_id=tournament_result.get("tournament_id", str(uuid.uuid4())),
                            imprint_name=imprint_name,
                            ideas_generated=len(ideas),
                            tournament_status="completed" if integration_mode == "full" else "created",
                            winner=tournament_result.get("results", {}).get("winner")
                        )

                        result.add_tournament(record)

                        # Export tournament results if in full mode
                        if integration_mode == "full" and tournament_config.save_results:
                            export_tournament_results(
                                imprint_name,
                                ideas,
                                tournament_result
                            )
                    else:
                        logger.warning(f"Failed to create tournament for {imprint_name}")
                        result.failed_imprints.append(imprint_name)
                else:
                    # Ideas only mode - just record the generation
                    record = TournamentRecord(
                        tournament_id=str(uuid.uuid4()),
                        imprint_name=imprint_name,
                        ideas_generated=len(ideas),
                        tournament_status="ideas_only"
                    )
                    result.add_tournament(record)

                    # Export ideas
                    if tournament_config.save_results:
                        export_ideas_only(imprint_name, ideas)

            except Exception as e:
                logger.error(f"Failed to process imprint {imprint_name}: {e}")
                result.failed_imprints.append(imprint_name)

        # Create dashboard export if any tournaments were created
        if result.tournaments_created:
            export_path = export_to_dashboard(result, tournament_config)
            result.dashboard_export_path = export_path

    except Exception as e:
        logger.error(f"Batch ideation failed: {e}")

    finally:
        result.duration_seconds = time.time() - start_time

    return result


def generate_imprint_ideas(
    imprint_name: str,
    config: Dict[str, Any],
    tournament_config: TournamentConfig,
    use_supplementary: bool = False
) -> List[Dict[str, Any]]:
    """
    Generate book ideas for an imprint.

    Args:
        imprint_name: Name of the imprint
        config: Imprint configuration
        tournament_config: Tournament configuration
        use_supplementary: Whether to include supplementary materials

    Returns:
        List of generated ideas
    """
    # Extract imprint context
    publisher_persona = config.get("publisher_persona", {})
    publishing_focus = config.get("publishing_focus", {})
    wizard_config = config.get("wizard_configuration", {})

    # Load supplementary materials if enabled
    supplementary_content = None
    max_tokens = 8192

    if use_supplementary:
        # Get largest context for this model
        max_context = get_largest_context_model(tournament_config.llm_model)

        # Allocate 30% of context to supplementary materials, rest for response
        supplementary_tokens = int(max_context * 0.3)
        max_tokens = max_context - supplementary_tokens - 2000  # Reserve 2k for prompt

        supplementary_content = load_imprint_supplementary_materials(
            config,
            use_supplementary=True,
            max_tokens=supplementary_tokens
        )

        if supplementary_content:
            logger.info(f"Loaded supplementary materials for {imprint_name} "
                       f"(using {max_context} token context window)")

    # Create prompt for idea generation
    prompt = _create_ideation_prompt(
        imprint_name,
        publisher_persona,
        publishing_focus,
        wizard_config,
        tournament_config.ideas_per_imprint,
        supplementary_content
    )

    try:
        prompt_config = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert book concept generator with deep knowledge of publishing markets and reader preferences."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "params": {
                "temperature": 0.8,
                "max_tokens": max_tokens
            }
        }

        response = call_model_with_prompt(
            model_name=tournament_config.llm_model,
            prompt_config=prompt_config,
            response_format_type="json_object",
            prompt_name=f"generate_ideas_{imprint_name}"
        )

        if response and "parsed_content" in response:
            ideas_data = response["parsed_content"]

            if isinstance(ideas_data, dict) and "ideas" in ideas_data:
                ideas = ideas_data["ideas"]
                logger.info(f"Generated {len(ideas)} ideas for {imprint_name}")
                return ideas
            else:
                logger.warning(f"Unexpected response format: {ideas_data}")
                return []
        else:
            logger.warning("No valid response from LLM")
            return []

    except Exception as e:
        logger.error(f"Failed to generate ideas: {e}")
        return []


def _create_ideation_prompt(
    imprint_name: str,
    publisher_persona: Dict[str, Any],
    publishing_focus: Dict[str, Any],
    wizard_config: Dict[str, Any],
    num_ideas: int,
    supplementary_content: Optional[str] = None
) -> str:
    """Create a prompt for generating book ideas."""
    persona_name = publisher_persona.get("persona_name", "Unknown Publisher")
    persona_bio = publisher_persona.get("persona_bio", "")
    editorial_philosophy = publisher_persona.get("editorial_philosophy", "")
    preferred_topics = publisher_persona.get("preferred_topics", "")

    genres = publishing_focus.get("primary_genres", wizard_config.get("genres", []))
    target_audience = publishing_focus.get("target_audience", "General readers")
    charter = wizard_config.get("charter", "")

    # Build prompt with optional supplementary materials
    prompt_parts = []

    # Add supplementary materials first if available
    if supplementary_content:
        prompt_parts.append(supplementary_content)
        prompt_parts.append("\n" + "=" * 80 + "\n")
        prompt_parts.append("The above materials provide context about the domain and mission of this imprint. "
                           "Use these materials to inform your book concept generation, ensuring ideas align with "
                           "the themes, values, and focus areas described.\n\n")

    prompt_parts.append(f"""Generate {num_ideas} compelling book concepts for the imprint "{imprint_name}".

IMPRINT CONTEXT:
Charter: {charter}
Primary Genres: {", ".join(genres) if isinstance(genres, list) else genres}
Target Audience: {target_audience}

PUBLISHER PERSONA:
Name: {persona_name}
Background: {persona_bio}
Editorial Philosophy: {editorial_philosophy}
Preferred Topics: {preferred_topics}

Please generate {num_ideas} book concepts that would be perfect for this imprint and appeal to the publisher persona.

For each concept, provide:
1. title: A compelling, marketable title
2. logline: A one-sentence hook
3. description: 2-3 paragraph description
4. genre: Primary genre
5. target_audience: Specific audience segment
6. word_count: Estimated word count (typically 50000-100000)
7. market_appeal: Why this would sell well (1-2 sentences)
8. imprint_fit: Why this fits the imprint perfectly (1-2 sentences)
9. persona_appeal_score: How much the publisher would love this (0.0-1.0)

Return a JSON object with this structure:
{{
  "ideas": [
    {{
      "title": "...",
      "logline": "...",
      "description": "...",
      "genre": "...",
      "target_audience": "...",
      "word_count": 75000,
      "market_appeal": "...",
      "imprint_fit": "...",
      "persona_appeal_score": 0.85
    }}
  ]
}}
""")

    return "".join(prompt_parts)


def create_tournament_for_imprint(
    imprint_name: str,
    ideas: List[Dict[str, Any]],
    tournament_config: TournamentConfig,
    tournament_executor: AutoTournamentExecutor
) -> Optional[Dict[str, Any]]:
    """
    Create and optionally run a tournament for imprint ideas.

    Args:
        imprint_name: Name of the imprint
        ideas: List of generated ideas
        tournament_config: Tournament configuration
        tournament_executor: Tournament executor instance

    Returns:
        Tournament results or None if failed
    """
    try:
        # Convert ideas to CodexObject format (simplified)
        from codexes.modules.ideation.core.codex_object import CodexObject

        concepts = []
        for idea in ideas:
            concept = CodexObject(
                title=idea.get("title", "Untitled"),
                content=idea.get("description", ""),
                metadata={
                    "logline": idea.get("logline", ""),
                    "genre": idea.get("genre", ""),
                    "target_audience": idea.get("target_audience", ""),
                    "market_appeal": idea.get("market_appeal", ""),
                    "imprint_fit": idea.get("imprint_fit", ""),
                    "persona_appeal_score": idea.get("persona_appeal_score", 0.5)
                }
            )
            concepts.append(concept)

        # Create session ID for this tournament
        session_id = f"{imprint_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Configure auto tournament
        auto_config = TournamentConfiguration(
            tournament_size=min(len(concepts), tournament_config.ideas_per_imprint),
            evaluation_criteria=", ".join(tournament_config.evaluation_criteria),
            auto_promote_winner=False,
            save_results=tournament_config.save_results
        )

        tournament_executor.configure_auto_tournaments(session_id, auto_config)

        # Execute tournament if auto_run is enabled
        if tournament_config.auto_run:
            tournament_result = tournament_executor.execute_auto_tournament(
                session_id,
                concepts
            )

            if tournament_result:
                logger.info(f"Tournament completed for {imprint_name}")
                return tournament_result
            else:
                logger.warning(f"Tournament execution failed for {imprint_name}")
                return None
        else:
            # Just return tournament configuration
            return {
                "tournament_id": session_id,
                "imprint_name": imprint_name,
                "participant_count": len(concepts),
                "status": "configured"
            }

    except Exception as e:
        logger.error(f"Failed to create tournament: {e}")
        return None


def export_tournament_results(
    imprint_name: str,
    ideas: List[Dict[str, Any]],
    tournament_result: Dict[str, Any]
) -> Optional[Path]:
    """
    Export tournament results to files.

    Args:
        imprint_name: Name of the imprint
        ideas: Generated ideas
        tournament_result: Tournament results

    Returns:
        Path to export directory or None
    """
    try:
        # Create export directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = Path("tournaments") / imprint_name / timestamp
        export_dir.mkdir(parents=True, exist_ok=True)

        # Export ideas
        ideas_file = export_dir / f"{imprint_name}_ideas_{timestamp}.json"
        with open(ideas_file, 'w', encoding='utf-8') as f:
            json.dump({"ideas": ideas, "count": len(ideas)}, f, indent=2)

        # Export tournament results
        tournament_file = export_dir / f"{imprint_name}_tournament_{timestamp}.json"
        with open(tournament_file, 'w', encoding='utf-8') as f:
            json.dump(tournament_result, f, indent=2)

        logger.info(f"Exported tournament results to {export_dir}")
        return export_dir

    except Exception as e:
        logger.error(f"Failed to export tournament results: {e}")
        return None


def export_ideas_only(
    imprint_name: str,
    ideas: List[Dict[str, Any]]
) -> Optional[Path]:
    """
    Export just the generated ideas (no tournament).

    Args:
        imprint_name: Name of the imprint
        ideas: Generated ideas

    Returns:
        Path to export file or None
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = Path("integrate_ideas") / imprint_name
        export_dir.mkdir(parents=True, exist_ok=True)

        ideas_file = export_dir / f"{imprint_name}_ideas_{timestamp}.json"
        with open(ideas_file, 'w', encoding='utf-8') as f:
            json.dump({"ideas": ideas, "count": len(ideas)}, f, indent=2)

        logger.info(f"Exported ideas to {ideas_file}")
        return ideas_file

    except Exception as e:
        logger.error(f"Failed to export ideas: {e}")
        return None


def export_to_dashboard(
    result: IdeationBatchResult,
    tournament_config: TournamentConfig
) -> Optional[Path]:
    """
    Export batch results for Ideation Dashboard integration.

    Args:
        result: Batch ideation result
        tournament_config: Tournament configuration

    Returns:
        Path to dashboard export file or None
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = Path("tournaments") / f"batch_tournaments_{timestamp}.json"
        export_file.parent.mkdir(parents=True, exist_ok=True)

        export_data = {
            "export_timestamp": timestamp,
            "export_datetime": datetime.now().isoformat(),
            "tournament_config": tournament_config.to_dict(),
            "summary": result.to_dict(),
            "tournaments": [t.to_dict() for t in result.tournaments_created]
        }

        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported dashboard data to {export_file}")
        return export_file

    except Exception as e:
        logger.error(f"Failed to export dashboard data: {e}")
        return None
