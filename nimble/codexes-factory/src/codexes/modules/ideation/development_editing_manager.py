"""
Development Editing Manager for Ideation System.

Manages bidirectional workflow from manuscript to outline and forward development,
with integrated synthetic reader feedback loop for iterative improvement.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field

try:
    from codexes.modules.ideation.core.codex_object import CodexObject, CodexObjectType, DevelopmentStage
    from codexes.modules.ideation.synthetic_reader import (
        SyntheticReaderPanel, ReaderFeedback, SynthesizedInsights
    )
    from codexes.modules.ideation.feedback_optimizer import FeedbackAnalyzer
    from codexes.core.llm_integration import LLMCaller
except ImportError:
    from src.codexes.modules.ideation.core.codex_object import CodexObject, CodexObjectType, DevelopmentStage
    from src.codexes.modules.ideation.synthetic_reader import (
        SyntheticReaderPanel, ReaderFeedback, SynthesizedInsights
    )
    from src.codexes.modules.ideation.feedback_optimizer import FeedbackAnalyzer
    from src.codexes.core.llm_integration import LLMCaller

logger = logging.getLogger(__name__)


@dataclass
class DevelopmentAction:
    """Represents a development action on a CodexObject."""
    action_type: str  # "expand", "condense", "revise", "evaluate"
    source_stage: str
    target_stage: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    feedback_used: List[str] = field(default_factory=list)
    model_used: str = ""
    success: bool = False
    notes: str = ""


class StageTransitionEngine:
    """Handles transitions between development stages."""

    # Define valid stage transitions
    STAGE_PROGRESSION = {
        CodexObjectType.IDEA: CodexObjectType.LOGLINE,
        CodexObjectType.LOGLINE: CodexObjectType.SUMMARY,
        CodexObjectType.SUMMARY: CodexObjectType.SYNOPSIS,
        CodexObjectType.SYNOPSIS: CodexObjectType.OUTLINE,
        CodexObjectType.OUTLINE: CodexObjectType.DETAILED_OUTLINE,
        CodexObjectType.DETAILED_OUTLINE: CodexObjectType.DRAFT,
        CodexObjectType.DRAFT: CodexObjectType.MANUSCRIPT,
    }

    # Define reverse transitions (condensing)
    STAGE_REGRESSION = {
        CodexObjectType.MANUSCRIPT: CodexObjectType.DETAILED_OUTLINE,
        CodexObjectType.DRAFT: CodexObjectType.OUTLINE,
        CodexObjectType.DETAILED_OUTLINE: CodexObjectType.SYNOPSIS,
        CodexObjectType.OUTLINE: CodexObjectType.SUMMARY,
        CodexObjectType.SYNOPSIS: CodexObjectType.LOGLINE,
        CodexObjectType.SUMMARY: CodexObjectType.IDEA,
        CodexObjectType.LOGLINE: CodexObjectType.IDEA,
    }

    def __init__(self, llm_caller: LLMCaller):
        self.llm_caller = llm_caller
        self.logger = logging.getLogger(self.__class__.__name__)

    def expand_to_next_stage(self, codex_object: CodexObject,
                            model: str = "gemini/gemini-2.0-flash-exp",
                            feedback_context: Optional[str] = None) -> Optional[CodexObject]:
        """Expand a CodexObject to the next development stage."""
        current_type = codex_object.object_type

        if current_type not in self.STAGE_PROGRESSION:
            self.logger.warning(f"No next stage defined for {current_type.value}")
            return None

        next_type = self.STAGE_PROGRESSION[current_type]

        # Generate expansion prompt
        prompt = self._create_expansion_prompt(codex_object, next_type, feedback_context)

        try:
            # Call LLM to expand
            response = self.llm_caller.call_llm(
                prompt=prompt,
                model=model,
                temperature=0.7,
                max_tokens=4000
            )

            if response:
                # Create new CodexObject with expanded content
                new_object = codex_object.transform_to_type(
                    next_type,
                    transformation_details={
                        "method": "llm_expansion",
                        "model": model,
                        "feedback_incorporated": bool(feedback_context)
                    }
                )

                new_object.content = response
                new_object.word_count = len(response.split())
                new_object.development_stage = DevelopmentStage.DEVELOPMENT

                return new_object

        except Exception as e:
            self.logger.error(f"Error expanding to {next_type.value}: {e}")

        return None

    def condense_to_previous_stage(self, codex_object: CodexObject,
                                   model: str = "gemini/gemini-2.0-flash-exp") -> Optional[CodexObject]:
        """Condense a CodexObject to the previous development stage."""
        current_type = codex_object.object_type

        if current_type not in self.STAGE_REGRESSION:
            self.logger.warning(f"No previous stage defined for {current_type.value}")
            return None

        previous_type = self.STAGE_REGRESSION[current_type]

        # Generate condensation prompt
        prompt = self._create_condensation_prompt(codex_object, previous_type)

        try:
            # Call LLM to condense
            response = self.llm_caller.call_llm(
                prompt=prompt,
                model=model,
                temperature=0.5,
                max_tokens=2000
            )

            if response:
                # Create new CodexObject with condensed content
                new_object = codex_object.transform_to_type(
                    previous_type,
                    transformation_details={
                        "method": "llm_condensation",
                        "model": model
                    }
                )

                new_object.content = response
                new_object.word_count = len(response.split())

                return new_object

        except Exception as e:
            self.logger.error(f"Error condensing to {previous_type.value}: {e}")

        return None

    def _create_expansion_prompt(self, codex_object: CodexObject,
                                 target_type: CodexObjectType,
                                 feedback_context: Optional[str] = None) -> str:
        """Create a prompt for expanding content to the next stage."""
        prompt = f"""You are a professional story development assistant. Your task is to expand the following {codex_object.object_type.value} into a detailed {target_type.value}.

Current Content:
Title: {codex_object.title}
{codex_object.content}

"""

        if codex_object.genre:
            prompt += f"Genre: {codex_object.genre}\n"

        if codex_object.target_audience:
            prompt += f"Target Audience: {codex_object.target_audience}\n"

        if feedback_context:
            prompt += f"\nReader Feedback to Incorporate:\n{feedback_context}\n"

        # Add stage-specific guidance
        stage_guidance = {
            CodexObjectType.LOGLINE: "Create a compelling one-sentence logline that captures the core conflict and stakes.",
            CodexObjectType.SUMMARY: "Expand into a 2-3 paragraph summary covering the main characters, conflict, and resolution arc.",
            CodexObjectType.SYNOPSIS: "Develop a comprehensive synopsis (500-800 words) detailing the full story arc, key plot points, and character development.",
            CodexObjectType.OUTLINE: "Create a structured outline with major acts, chapters or sections, and key scenes. Include character arcs and plot progression.",
            CodexObjectType.DETAILED_OUTLINE: "Expand into a detailed scene-by-scene outline. Each scene should include: setting, characters present, action/dialogue summary, and emotional/plot progression.",
            CodexObjectType.DRAFT: "Begin drafting the first chapters or sections based on the outline. Include dialogue, description, and narrative flow.",
            CodexObjectType.MANUSCRIPT: "Continue developing the full manuscript with polished prose, dialogue, and narrative structure."
        }

        guidance = stage_guidance.get(target_type, "Develop the content appropriately for this stage.")
        prompt += f"\nTask: {guidance}\n\nProvide only the expanded content, without meta-commentary."

        return prompt

    def _create_condensation_prompt(self, codex_object: CodexObject,
                                   target_type: CodexObjectType) -> str:
        """Create a prompt for condensing content to a previous stage."""
        prompt = f"""You are a professional story development assistant. Your task is to condense the following {codex_object.object_type.value} into a concise {target_type.value}.

Current Content:
Title: {codex_object.title}
{codex_object.content}

"""

        # Add stage-specific guidance for condensation
        stage_guidance = {
            CodexObjectType.IDEA: "Distill to the core idea or concept in 1-2 sentences.",
            CodexObjectType.LOGLINE: "Condense to a single compelling sentence capturing the essence.",
            CodexObjectType.SUMMARY: "Create a brief 2-3 paragraph summary of the main story elements.",
            CodexObjectType.SYNOPSIS: "Condense to a focused synopsis highlighting the key plot points.",
            CodexObjectType.OUTLINE: "Create a high-level outline of major story beats and structure.",
            CodexObjectType.DETAILED_OUTLINE: "Simplify to a scene outline without excessive detail."
        }

        guidance = stage_guidance.get(target_type, "Condense the content appropriately for this stage.")
        prompt += f"\nTask: {guidance}\n\nProvide only the condensed content, without meta-commentary."

        return prompt


class DevelopmentEditingManager:
    """
    Manages the development editing workflow with bidirectional stage progression
    and integrated synthetic reader feedback.
    """

    def __init__(self, llm_caller: LLMCaller, storage_path: str = "data/ideation/development"):
        self.llm_caller = llm_caller
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.transition_engine = StageTransitionEngine(llm_caller)
        self.synthetic_reader_panel = SyntheticReaderPanel(llm_caller)
        self.feedback_analyzer = FeedbackAnalyzer()

        self.logger = logging.getLogger(self.__class__.__name__)

        # Track development history
        self.development_history: List[DevelopmentAction] = []

    def load_codex_object(self, file_path: str) -> Optional[CodexObject]:
        """Load a CodexObject from file."""
        try:
            return CodexObject.load_from_file(file_path)
        except Exception as e:
            self.logger.error(f"Error loading CodexObject: {e}")
            return None

    def save_codex_object(self, codex_object: CodexObject,
                         custom_filename: Optional[str] = None) -> str:
        """Save a CodexObject to file."""
        try:
            if custom_filename:
                file_path = self.storage_path / custom_filename
            else:
                # Generate filename from title and type
                safe_title = "".join(c for c in codex_object.title if c.isalnum() or c in (' ', '-', '_'))
                safe_title = safe_title.replace(' ', '_')[:50]
                filename = f"{safe_title}_{codex_object.object_type.value}_{codex_object.shortuuid}.json"
                file_path = self.storage_path / filename

            codex_object.save_to_file(str(file_path))
            return str(file_path)

        except Exception as e:
            self.logger.error(f"Error saving CodexObject: {e}")
            return ""

    def progress_forward(self, codex_object: CodexObject,
                        model: str = "gemini/gemini-2.0-flash-exp",
                        incorporate_feedback: bool = False,
                        feedback_ids: Optional[List[str]] = None) -> Optional[CodexObject]:
        """
        Progress a CodexObject to the next development stage.

        Args:
            codex_object: The CodexObject to develop
            model: LLM model to use for development
            incorporate_feedback: Whether to incorporate reader feedback
            feedback_ids: Specific feedback IDs to incorporate

        Returns:
            New CodexObject at next stage, or None if failed
        """
        feedback_context = None

        if incorporate_feedback and codex_object.reader_feedback:
            feedback_context = self._compile_feedback_context(
                codex_object.reader_feedback,
                feedback_ids
            )

        new_object = self.transition_engine.expand_to_next_stage(
            codex_object,
            model=model,
            feedback_context=feedback_context
        )

        if new_object:
            # Record the action
            action = DevelopmentAction(
                action_type="expand",
                source_stage=codex_object.object_type.value,
                target_stage=new_object.object_type.value,
                model_used=model,
                feedback_used=feedback_ids or [],
                success=True,
                notes=f"Expanded from {codex_object.object_type.value} to {new_object.object_type.value}"
            )
            self.development_history.append(action)

            # Save the new object
            self.save_codex_object(new_object)

        return new_object

    def progress_backward(self, codex_object: CodexObject,
                         model: str = "gemini/gemini-2.0-flash-exp") -> Optional[CodexObject]:
        """
        Regress a CodexObject to the previous development stage.

        Args:
            codex_object: The CodexObject to condense
            model: LLM model to use

        Returns:
            New CodexObject at previous stage, or None if failed
        """
        new_object = self.transition_engine.condense_to_previous_stage(
            codex_object,
            model=model
        )

        if new_object:
            # Record the action
            action = DevelopmentAction(
                action_type="condense",
                source_stage=codex_object.object_type.value,
                target_stage=new_object.object_type.value,
                model_used=model,
                success=True,
                notes=f"Condensed from {codex_object.object_type.value} to {new_object.object_type.value}"
            )
            self.development_history.append(action)

            # Save the new object
            self.save_codex_object(new_object)

        return new_object

    def request_synthetic_feedback(self, codex_object: CodexObject,
                                  selected_personas: Optional[List[str]] = None,
                                  feedback_types: Optional[List[str]] = None,
                                  model: str = "gemini/gemini-2.5-flash") -> List[ReaderFeedback]:
        """
        Request synthetic reader feedback on a CodexObject.

        Args:
            codex_object: The CodexObject to evaluate
            selected_personas: List of persona names to use (None = all)
            feedback_types: Types of feedback to request (future enhancement)
            model: LLM model to use for evaluation

        Returns:
            List of ReaderFeedback objects
        """
        try:
            # Convert CodexObject to BookIdea format for compatibility
            from codexes.modules.ideation.book_idea import BookIdea

            book_idea = BookIdea(
                title=codex_object.title,
                logline=codex_object.logline or codex_object.content[:200],
                description=codex_object.description or codex_object.content,
                genre=codex_object.genre,
                target_audience=codex_object.target_audience,
                generation_metadata={"idea_id": codex_object.uuid}
            )

            # Get feedback from synthetic readers with specified model
            feedback_list = self.synthetic_reader_panel.evaluate_ideas(
                [book_idea],
                selected_personas=selected_personas,
                model=model
            )

            # Add feedback to CodexObject
            for feedback in feedback_list:
                codex_object.add_reader_feedback(feedback.to_dict())

            # Save updated object
            self.save_codex_object(codex_object)

            return feedback_list

        except Exception as e:
            self.logger.error(f"Error requesting synthetic feedback: {e}")
            return []

    def evaluate_feedback(self, feedback_list: List[ReaderFeedback]) -> Dict[str, SynthesizedInsights]:
        """
        Evaluate and synthesize reader feedback.

        Args:
            feedback_list: List of feedback to synthesize

        Returns:
            Dictionary of synthesized insights by idea_id
        """
        return self.synthetic_reader_panel.synthesize_feedback(feedback_list)

    def apply_feedback_revisions(self, codex_object: CodexObject,
                                feedback_insights: SynthesizedInsights,
                                model: str = "gemini/gemini-2.0-flash-exp") -> Optional[CodexObject]:
        """
        Apply feedback-driven revisions to a CodexObject at the same stage.

        Args:
            codex_object: The CodexObject to revise
            feedback_insights: Synthesized insights to incorporate
            model: LLM model to use

        Returns:
            Revised CodexObject, or None if failed
        """
        try:
            # Create revision prompt
            revision_prompt = f"""You are a professional editor. Revise the following {codex_object.object_type.value} based on reader feedback.

Current Content:
Title: {codex_object.title}
{codex_object.content}

Reader Feedback Summary:
- Overall Consensus: {feedback_insights.overall_consensus}
- Market Potential: {feedback_insights.market_potential}/10

Recommended Improvements:
{chr(10).join(f"- {imp}" for imp in feedback_insights.recommended_improvements[:5])}

Editing Priorities:
{chr(10).join(f"- {pri}" for pri in feedback_insights.editing_priorities[:5])}

Task: Revise the content to address the feedback while maintaining the same format and stage ({codex_object.object_type.value}).
Focus on the recommended improvements and editing priorities.

Provide only the revised content, without meta-commentary.
"""

            # Call LLM for revision
            response = self.llm_caller.call_llm(
                prompt=revision_prompt,
                model=model,
                temperature=0.6,
                max_tokens=4000
            )

            if response:
                # Update the existing object with revisions
                codex_object.update_content(
                    response,
                    update_type="feedback_revision"
                )

                # Record the action
                action = DevelopmentAction(
                    action_type="revise",
                    source_stage=codex_object.object_type.value,
                    target_stage=codex_object.object_type.value,
                    model_used=model,
                    success=True,
                    notes="Applied feedback-driven revisions"
                )
                self.development_history.append(action)

                # Save updated object
                self.save_codex_object(codex_object)

                return codex_object

        except Exception as e:
            self.logger.error(f"Error applying feedback revisions: {e}")

        return None

    def _compile_feedback_context(self, feedback_list: List[Dict[str, Any]],
                                  feedback_ids: Optional[List[str]] = None) -> str:
        """Compile feedback into a context string for LLM."""
        context_parts = []

        for fb in feedback_list:
            if feedback_ids and fb.get('feedback_id') not in feedback_ids:
                continue

            persona = fb.get('reader_persona', 'Unknown')
            detailed = fb.get('detailed_feedback', '')
            recommendations = fb.get('recommendations', [])

            context_parts.append(f"Reader {persona}:")
            if detailed:
                context_parts.append(f"  {detailed}")
            if recommendations:
                context_parts.append("  Suggestions:")
                for rec in recommendations[:3]:
                    context_parts.append(f"    - {rec}")

        return "\n".join(context_parts)

    def get_development_history(self) -> List[DevelopmentAction]:
        """Get the development action history."""
        return self.development_history

    def list_available_objects(self, object_type: Optional[CodexObjectType] = None) -> List[Dict[str, str]]:
        """
        List available CodexObjects in storage.

        Args:
            object_type: Filter by specific type (None = all types)

        Returns:
            List of dicts with file info
        """
        objects = []

        try:
            for file_path in self.storage_path.glob("*.json"):
                try:
                    obj = CodexObject.load_from_file(str(file_path))

                    if object_type is None or obj.object_type == object_type:
                        objects.append({
                            "file_path": str(file_path),
                            "title": obj.title,
                            "type": obj.object_type.value,
                            "stage": obj.development_stage.value,
                            "word_count": obj.word_count,
                            "last_modified": obj.last_modified,
                            "uuid": obj.uuid
                        })
                except Exception as e:
                    self.logger.warning(f"Error loading {file_path}: {e}")
                    continue

            # Sort by last modified
            objects.sort(key=lambda x: x['last_modified'], reverse=True)

        except Exception as e:
            self.logger.error(f"Error listing objects: {e}")

        return objects
