"""
Answer key generation system for LLM training data.

This module implements answer key generation with verification instructions,
LLM judge evaluation criteria, and scoring rubrics for training data quality
assessment.
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from enum import Enum

from .content_extractor import (
    ExtractedFigure, 
    SFTExample, 
    RLExample, 
    ExtractionResult
)


class DifficultyLevel(Enum):
    """Difficulty levels for training examples."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class EvaluationCriteria(Enum):
    """Evaluation criteria for LLM judge scoring."""
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    CLARITY = "clarity"
    COHERENCE = "coherence"
    TECHNICAL_DEPTH = "technical_depth"
    CITATION_QUALITY = "citation_quality"
    FIGURE_INTEGRATION = "figure_integration"


@dataclass
class ScoringRubric:
    """Scoring rubric for evaluation criteria."""
    criterion: EvaluationCriteria
    weight: float = 1.0
    max_score: int = 5
    description: str = ""
    scoring_guidelines: Dict[int, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default scoring guidelines if not provided."""
        if not self.scoring_guidelines:
            self.scoring_guidelines = {
                5: "Excellent - Exceeds expectations",
                4: "Good - Meets expectations well",
                3: "Satisfactory - Meets basic expectations",
                2: "Needs improvement - Below expectations",
                1: "Poor - Significantly below expectations"
            }


@dataclass
class VerificationInstruction:
    """Verification instruction for training data quality."""
    instruction_id: str
    instruction_text: str
    verification_type: str  # "factual", "logical", "stylistic", "technical"
    expected_outcome: str
    verification_steps: List[str] = field(default_factory=list)
    automated_check: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnswerKey:
    """Complete answer key for a training example."""
    example_id: str
    example_type: str  # "sft" or "rl"
    correct_answer: str
    alternative_answers: List[str] = field(default_factory=list)
    verification_instructions: List[VerificationInstruction] = field(default_factory=list)
    scoring_rubrics: List[ScoringRubric] = field(default_factory=list)
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    expected_response_length: Tuple[int, int] = (100, 500)  # min, max words
    key_concepts: List[str] = field(default_factory=list)
    required_citations: List[str] = field(default_factory=list)
    figure_references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class JudgeEvaluationCriteria:
    """Comprehensive evaluation criteria for LLM judge."""
    criteria_id: str
    name: str
    description: str
    rubrics: List[ScoringRubric] = field(default_factory=list)
    weight_in_total_score: float = 1.0
    evaluation_prompt: str = ""
    examples: Dict[str, str] = field(default_factory=dict)  # score -> example
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnswerKeyResult:
    """Result of answer key generation process."""
    answer_keys: List[AnswerKey] = field(default_factory=list)
    judge_criteria: List[JudgeEvaluationCriteria] = field(default_factory=list)
    generation_summary: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AnswerKeyGenerator:
    """
    Answer key generation system for LLM training data.
    
    Generates comprehensive answer keys with verification instructions,
    scoring rubrics, and LLM judge evaluation criteria for training
    data quality assessment.
    """
    
    def __init__(self, output_dir: str = "answer_keys"):
        """
        Initialize the answer key generator.
        
        Args:
            output_dir: Directory to save generated answer keys
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Default scoring rubrics for different criteria
        self.default_rubrics = self._create_default_rubrics()
        
        # Default verification instruction templates
        self.verification_templates = self._create_verification_templates()
        
        # Judge evaluation criteria templates
        self.judge_criteria_templates = self._create_judge_criteria_templates()
    
    def generate_answer_keys(self, extraction_result: ExtractionResult) -> AnswerKeyResult:
        """
        Generate answer keys for all examples in extraction result.
        
        Args:
            extraction_result: Result from content extraction
            
        Returns:
            AnswerKeyResult with generated answer keys and judge criteria
        """
        answer_keys = []
        
        # Generate answer keys for SFT examples
        for sft_example in extraction_result.sft_examples:
            answer_key = self._generate_sft_answer_key(sft_example, extraction_result.figures)
            answer_keys.append(answer_key)
        
        # Generate answer keys for RL examples
        for rl_example in extraction_result.rl_examples:
            answer_key = self._generate_rl_answer_key(rl_example, extraction_result.figures)
            answer_keys.append(answer_key)
        
        # Generate judge evaluation criteria
        judge_criteria = self._generate_judge_criteria(answer_keys)
        
        # Create generation summary
        generation_summary = {
            "total_answer_keys": len(answer_keys),
            "sft_answer_keys": len(extraction_result.sft_examples),
            "rl_answer_keys": len(extraction_result.rl_examples),
            "judge_criteria_count": len(judge_criteria),
            "generation_date": datetime.now().isoformat()
        }
        
        return AnswerKeyResult(
            answer_keys=answer_keys,
            judge_criteria=judge_criteria,
            generation_summary=generation_summary
        )
    
    def _generate_sft_answer_key(self, sft_example: SFTExample, figures: List[ExtractedFigure]) -> AnswerKey:
        """Generate answer key for SFT example."""
        # Create correct answer based on the analysis passage and conclusion
        correct_answer = self._create_sft_correct_answer(sft_example)
        
        # Generate alternative answers
        alternative_answers = self._generate_alternative_answers(sft_example, "sft")
        
        # Create verification instructions
        verification_instructions = self._create_sft_verification_instructions(sft_example)
        
        # Select appropriate scoring rubrics
        scoring_rubrics = self._select_rubrics_for_sft(sft_example)
        
        # Determine difficulty level
        difficulty_level = self._determine_difficulty_level(sft_example.analysis_passage)
        
        # Extract key concepts
        key_concepts = self._extract_key_concepts(sft_example.analysis_passage)
        
        # Find figure references
        figure_refs = [fig.figure_id for fig in figures if fig.figure_id in sft_example.figures_referenced]
        
        return AnswerKey(
            example_id=sft_example.example_id,
            example_type="sft",
            correct_answer=correct_answer,
            alternative_answers=alternative_answers,
            verification_instructions=verification_instructions,
            scoring_rubrics=scoring_rubrics,
            difficulty_level=difficulty_level,
            expected_response_length=self._estimate_response_length(sft_example.analysis_passage),
            key_concepts=key_concepts,
            figure_references=figure_refs,
            metadata={
                "section_type": sft_example.section_type,
                "quality_score": sft_example.quality_score,
                "original_context": sft_example.context
            }
        )
    
    def _generate_rl_answer_key(self, rl_example: RLExample, figures: List[ExtractedFigure]) -> AnswerKey:
        """Generate answer key for RL example."""
        # Create correct answer based on the case study components
        correct_answer = self._create_rl_correct_answer(rl_example)
        
        # Generate alternative answers
        alternative_answers = self._generate_alternative_answers(rl_example, "rl")
        
        # Create verification instructions
        verification_instructions = self._create_rl_verification_instructions(rl_example)
        
        # Select appropriate scoring rubrics
        scoring_rubrics = self._select_rubrics_for_rl(rl_example)
        
        # Determine difficulty level
        difficulty_level = self._determine_difficulty_level(rl_example.methodology)
        
        # Extract key concepts
        key_concepts = self._extract_key_concepts(
            f"{rl_example.problem_description} {rl_example.methodology}"
        )
        
        # Find figure references
        figure_refs = [fig.figure_id for fig in figures if fig.figure_id in rl_example.figures_referenced]
        
        return AnswerKey(
            example_id=rl_example.example_id,
            example_type="rl",
            correct_answer=correct_answer,
            alternative_answers=alternative_answers,
            verification_instructions=verification_instructions,
            scoring_rubrics=scoring_rubrics,
            difficulty_level=difficulty_level,
            expected_response_length=self._estimate_response_length(rl_example.methodology),
            key_concepts=key_concepts,
            figure_references=figure_refs,
            metadata={
                "case_study_title": rl_example.case_study_title,
                "problem_type": self._classify_problem_type(rl_example.problem_description)
            }
        )
    
    def _create_sft_correct_answer(self, sft_example: SFTExample) -> str:
        """Create correct answer for SFT example."""
        answer_parts = []
        
        if sft_example.context:
            answer_parts.append(f"Context: {sft_example.context.strip()}")
        
        answer_parts.append(f"Analysis: {sft_example.analysis_passage.strip()}")
        
        if sft_example.conclusion:
            answer_parts.append(f"Conclusion: {sft_example.conclusion.strip()}")
        
        return "\n\n".join(answer_parts)
    
    def _create_rl_correct_answer(self, rl_example: RLExample) -> str:
        """Create correct answer for RL example."""
        answer_parts = [
            f"Case Study: {rl_example.case_study_title}",
            f"Problem: {rl_example.problem_description}",
            f"Methodology: {rl_example.methodology}",
            f"Results: {rl_example.results}"
        ]
        
        if rl_example.lessons_learned:
            answer_parts.append(f"Lessons Learned: {rl_example.lessons_learned}")
        
        return "\n\n".join(answer_parts)
    
    def _generate_alternative_answers(self, example: Union[SFTExample, RLExample], example_type: str) -> List[str]:
        """Generate alternative correct answers."""
        alternatives = []
        
        if example_type == "sft" and isinstance(example, SFTExample):
            # Create variations focusing on different aspects
            if example.conclusion:
                alternatives.append(f"Key Finding: {example.conclusion}")
            
            # Create a more concise version
            alternatives.append(f"Summary: {example.analysis_passage[:200]}...")
            
        elif example_type == "rl" and isinstance(example, RLExample):
            # Create variations focusing on different components
            alternatives.append(f"Problem-Solution Pair: {example.problem_description} -> {example.methodology}")
            
            # Create results-focused version
            if example.results:
                alternatives.append(f"Outcome Analysis: {example.results}")
        
        return alternatives
    
    def _create_sft_verification_instructions(self, sft_example: SFTExample) -> List[VerificationInstruction]:
        """Create verification instructions for SFT example."""
        instructions = []
        
        # Factual accuracy verification
        instructions.append(VerificationInstruction(
            instruction_id=f"{sft_example.example_id}_factual",
            instruction_text="Verify that all factual claims in the analysis are supported by evidence or proper reasoning.",
            verification_type="factual",
            expected_outcome="All claims should be verifiable or clearly marked as hypotheses/assumptions.",
            verification_steps=[
                "Identify all factual claims in the analysis",
                "Check if claims are supported by data, citations, or logical reasoning",
                "Flag any unsupported assertions",
                "Verify numerical data and statistics if present"
            ]
        ))
        
        # Logical coherence verification
        instructions.append(VerificationInstruction(
            instruction_id=f"{sft_example.example_id}_logical",
            instruction_text="Verify that the logical flow from context to analysis to conclusion is coherent.",
            verification_type="logical",
            expected_outcome="The reasoning should follow a clear logical progression without contradictions.",
            verification_steps=[
                "Check if the analysis follows from the given context",
                "Verify that conclusions are supported by the analysis",
                "Identify any logical gaps or contradictions",
                "Ensure cause-effect relationships are properly established"
            ]
        ))
        
        # Technical accuracy verification (if applicable)
        if sft_example.section_type in ["methodology", "results"]:
            instructions.append(VerificationInstruction(
                instruction_id=f"{sft_example.example_id}_technical",
                instruction_text="Verify technical accuracy of methods, procedures, or results described.",
                verification_type="technical",
                expected_outcome="Technical content should be accurate and follow established practices.",
                verification_steps=[
                    "Check technical terminology usage",
                    "Verify methodological approaches are sound",
                    "Validate statistical or analytical procedures",
                    "Ensure results interpretation is appropriate"
                ]
            ))
        
        return instructions
    
    def _create_rl_verification_instructions(self, rl_example: RLExample) -> List[VerificationInstruction]:
        """Create verification instructions for RL example."""
        instructions = []
        
        # Problem-solution alignment verification
        instructions.append(VerificationInstruction(
            instruction_id=f"{rl_example.example_id}_alignment",
            instruction_text="Verify that the proposed methodology appropriately addresses the stated problem.",
            verification_type="logical",
            expected_outcome="The methodology should be well-suited to solve the identified problem.",
            verification_steps=[
                "Analyze the problem characteristics and requirements",
                "Evaluate if the methodology addresses key problem aspects",
                "Check for any misalignment between problem and solution",
                "Verify that the approach is feasible for the given context"
            ]
        ))
        
        # Results consistency verification
        instructions.append(VerificationInstruction(
            instruction_id=f"{rl_example.example_id}_consistency",
            instruction_text="Verify that results are consistent with the methodology and problem context.",
            verification_type="factual",
            expected_outcome="Results should logically follow from the applied methodology.",
            verification_steps=[
                "Check if results align with expected outcomes of the methodology",
                "Verify that performance metrics are appropriate",
                "Ensure results are presented in proper context",
                "Validate any comparative claims or improvements"
            ]
        ))
        
        # Lessons learned verification
        if rl_example.lessons_learned:
            instructions.append(VerificationInstruction(
                instruction_id=f"{rl_example.example_id}_lessons",
                instruction_text="Verify that lessons learned are well-supported by the case study experience.",
                verification_type="logical",
                expected_outcome="Lessons should be clearly derived from the case study outcomes.",
                verification_steps=[
                    "Check if lessons are supported by the case study results",
                    "Verify generalizability claims are appropriate",
                    "Ensure lessons are actionable and specific",
                    "Validate that lessons address key learning objectives"
                ]
            ))
        
        return instructions
    
    def _select_rubrics_for_sft(self, sft_example: SFTExample) -> List[ScoringRubric]:
        """Select appropriate scoring rubrics for SFT example."""
        rubrics = [
            self.default_rubrics[EvaluationCriteria.ACCURACY],
            self.default_rubrics[EvaluationCriteria.CLARITY],
            self.default_rubrics[EvaluationCriteria.COHERENCE]
        ]
        
        # Add technical depth for methodology/results sections
        if sft_example.section_type in ["methodology", "results"]:
            rubrics.append(self.default_rubrics[EvaluationCriteria.TECHNICAL_DEPTH])
        
        # Add figure integration if figures are referenced
        if sft_example.figures_referenced:
            rubrics.append(self.default_rubrics[EvaluationCriteria.FIGURE_INTEGRATION])
        
        return rubrics
    
    def _select_rubrics_for_rl(self, rl_example: RLExample) -> List[ScoringRubric]:
        """Select appropriate scoring rubrics for RL example."""
        rubrics = [
            self.default_rubrics[EvaluationCriteria.COMPLETENESS],
            self.default_rubrics[EvaluationCriteria.COHERENCE],
            self.default_rubrics[EvaluationCriteria.TECHNICAL_DEPTH]
        ]
        
        # Add figure integration if figures are referenced
        if rl_example.figures_referenced:
            rubrics.append(self.default_rubrics[EvaluationCriteria.FIGURE_INTEGRATION])
        
        return rubrics
    
    def _determine_difficulty_level(self, content: str) -> DifficultyLevel:
        """Determine difficulty level based on content complexity."""
        content_lower = content.lower()
        
        # Count technical indicators
        technical_terms = len(re.findall(r'\b(?:algorithm|methodology|statistical|analysis|optimization|framework|architecture|implementation)\b', content_lower))
        
        # Count complex sentence structures
        complex_sentences = len(re.findall(r'[;:]', content))
        
        # Estimate based on length and complexity
        word_count = len(content.split())
        
        complexity_score = (technical_terms * 2) + complex_sentences + (word_count / 100)
        
        if complexity_score < 5:
            return DifficultyLevel.BEGINNER
        elif complexity_score < 10:
            return DifficultyLevel.INTERMEDIATE
        elif complexity_score < 20:
            return DifficultyLevel.ADVANCED
        else:
            return DifficultyLevel.EXPERT
    
    def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts from content."""
        # Simple keyword extraction - could be enhanced with NLP
        technical_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Proper nouns/technical terms
            r'\b(?:algorithm|method|approach|technique|framework|model|system)\b',
            r'\b(?:analysis|evaluation|assessment|optimization|classification)\b'
        ]
        
        concepts = set()
        for pattern in technical_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            concepts.update([match.lower() for match in matches])
        
        # Filter out common words
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        concepts = [concept for concept in concepts if concept not in common_words and len(concept) > 2]
        
        return sorted(list(concepts))[:10]  # Return top 10 concepts
    
    def _estimate_response_length(self, content: str) -> Tuple[int, int]:
        """Estimate expected response length based on content."""
        word_count = len(content.split())
        
        # Base estimate on content length with some variation
        min_words = max(50, word_count // 3)
        max_words = max(min_words, min(1000, word_count * 2))
        
        return (min_words, max_words)
    
    def _classify_problem_type(self, problem_description: str) -> str:
        """Classify the type of problem described."""
        problem_lower = problem_description.lower()
        
        if any(term in problem_lower for term in ['classify', 'classification', 'categorization', 'labeling']):
            return "classification"
        elif any(term in problem_lower for term in ['predict', 'prediction', 'forecasting', 'estimation']):
            return "prediction"
        elif any(term in problem_lower for term in ['optimization', 'minimize', 'maximize']):
            return "optimization"
        elif any(term in problem_lower for term in ['detect', 'detection', 'identification', 'recognition']):
            return "detection"
        else:
            return "general"
    
    def _generate_judge_criteria(self, answer_keys: List[AnswerKey]) -> List[JudgeEvaluationCriteria]:
        """Generate comprehensive judge evaluation criteria."""
        criteria_list = []
        
        # Create criteria for each evaluation type
        for criterion_type in EvaluationCriteria:
            # Check if this criterion is used in any answer key
            if any(any(rubric.criterion == criterion_type for rubric in ak.scoring_rubrics) for ak in answer_keys):
                criteria = self.judge_criteria_templates[criterion_type]
                criteria_list.append(criteria)
        
        return criteria_list
    
    def _create_default_rubrics(self) -> Dict[EvaluationCriteria, ScoringRubric]:
        """Create default scoring rubrics for all evaluation criteria."""
        rubrics = {}
        
        rubrics[EvaluationCriteria.ACCURACY] = ScoringRubric(
            criterion=EvaluationCriteria.ACCURACY,
            weight=1.5,
            description="Factual correctness and precision of information",
            scoring_guidelines={
                5: "All facts are accurate, no errors or misconceptions",
                4: "Mostly accurate with minor factual errors",
                3: "Generally accurate with some notable errors",
                2: "Several factual errors that affect credibility",
                1: "Significant factual errors throughout"
            }
        )
        
        rubrics[EvaluationCriteria.COMPLETENESS] = ScoringRubric(
            criterion=EvaluationCriteria.COMPLETENESS,
            weight=1.2,
            description="Thoroughness and coverage of required elements",
            scoring_guidelines={
                5: "Addresses all required elements comprehensively",
                4: "Covers most elements with good detail",
                3: "Addresses basic requirements adequately",
                2: "Missing some important elements",
                1: "Incomplete, missing many required elements"
            }
        )
        
        rubrics[EvaluationCriteria.CLARITY] = ScoringRubric(
            criterion=EvaluationCriteria.CLARITY,
            weight=1.0,
            description="Clear communication and understandability",
            scoring_guidelines={
                5: "Exceptionally clear and easy to understand",
                4: "Clear with good organization and flow",
                3: "Generally clear with minor confusion",
                2: "Somewhat unclear, requires effort to understand",
                1: "Confusing and difficult to follow"
            }
        )
        
        rubrics[EvaluationCriteria.COHERENCE] = ScoringRubric(
            criterion=EvaluationCriteria.COHERENCE,
            weight=1.3,
            description="Logical flow and consistency of arguments",
            scoring_guidelines={
                5: "Perfect logical flow, all arguments connect seamlessly",
                4: "Good logical structure with clear connections",
                3: "Generally coherent with some logical gaps",
                2: "Some logical inconsistencies or unclear connections",
                1: "Poor logical flow, arguments don't connect well"
            }
        )
        
        rubrics[EvaluationCriteria.TECHNICAL_DEPTH] = ScoringRubric(
            criterion=EvaluationCriteria.TECHNICAL_DEPTH,
            weight=1.4,
            description="Appropriate level of technical detail and expertise",
            scoring_guidelines={
                5: "Excellent technical depth, demonstrates expertise",
                4: "Good technical understanding with appropriate detail",
                3: "Adequate technical content for the context",
                2: "Limited technical depth, some gaps in understanding",
                1: "Insufficient technical content or understanding"
            }
        )
        
        rubrics[EvaluationCriteria.CITATION_QUALITY] = ScoringRubric(
            criterion=EvaluationCriteria.CITATION_QUALITY,
            weight=0.8,
            description="Proper use and formatting of citations and references",
            scoring_guidelines={
                5: "Excellent citation practices, all sources properly attributed",
                4: "Good citation practices with minor formatting issues",
                3: "Adequate citations, some formatting inconsistencies",
                2: "Limited citations, some attribution issues",
                1: "Poor citation practices, missing or incorrect attributions"
            }
        )
        
        rubrics[EvaluationCriteria.FIGURE_INTEGRATION] = ScoringRubric(
            criterion=EvaluationCriteria.FIGURE_INTEGRATION,
            weight=1.1,
            description="Effective integration and reference to figures and tables",
            scoring_guidelines={
                5: "Figures perfectly integrated, enhance understanding significantly",
                4: "Good figure integration, clear references and explanations",
                3: "Adequate figure use, basic integration with text",
                2: "Limited figure integration, unclear references",
                1: "Poor figure integration, figures don't support text well"
            }
        )
        
        return rubrics
    
    def _create_verification_templates(self) -> Dict[str, VerificationInstruction]:
        """Create templates for common verification instructions."""
        templates = {}
        
        templates["factual_accuracy"] = VerificationInstruction(
            instruction_id="template_factual",
            instruction_text="Verify all factual claims are accurate and supported by evidence.",
            verification_type="factual",
            expected_outcome="All facts should be verifiable or clearly marked as assumptions.",
            verification_steps=[
                "Identify factual claims",
                "Check supporting evidence",
                "Verify data accuracy",
                "Flag unsupported assertions"
            ]
        )
        
        templates["logical_coherence"] = VerificationInstruction(
            instruction_id="template_logical",
            instruction_text="Verify logical flow and consistency of arguments.",
            verification_type="logical",
            expected_outcome="Arguments should follow logical progression without contradictions.",
            verification_steps=[
                "Check argument structure",
                "Verify logical connections",
                "Identify contradictions",
                "Ensure conclusions follow from premises"
            ]
        )
        
        return templates
    
    def _create_judge_criteria_templates(self) -> Dict[EvaluationCriteria, JudgeEvaluationCriteria]:
        """Create judge evaluation criteria templates."""
        templates = {}
        
        templates[EvaluationCriteria.ACCURACY] = JudgeEvaluationCriteria(
            criteria_id="accuracy_judge",
            name="Factual Accuracy",
            description="Evaluate the factual correctness and precision of the response",
            rubrics=[self.default_rubrics[EvaluationCriteria.ACCURACY]],
            weight_in_total_score=1.5,
            evaluation_prompt="Assess the factual accuracy of the response. Check for errors, misconceptions, and unsupported claims.",
            examples={
                "5": "Response contains only verified facts with proper support",
                "3": "Response is generally accurate with minor factual issues",
                "1": "Response contains significant factual errors"
            }
        )
        
        templates[EvaluationCriteria.COHERENCE] = JudgeEvaluationCriteria(
            criteria_id="coherence_judge",
            name="Logical Coherence",
            description="Evaluate the logical flow and consistency of arguments",
            rubrics=[self.default_rubrics[EvaluationCriteria.COHERENCE]],
            weight_in_total_score=1.3,
            evaluation_prompt="Assess how well the response maintains logical flow and consistency throughout.",
            examples={
                "5": "Perfect logical progression with seamless argument connections",
                "3": "Generally coherent with some minor logical gaps",
                "1": "Poor logical flow with disconnected arguments"
            }
        )
        
        # Add templates for other criteria...
        for criterion in EvaluationCriteria:
            if criterion not in templates:
                templates[criterion] = JudgeEvaluationCriteria(
                    criteria_id=f"{criterion.value}_judge",
                    name=criterion.value.replace('_', ' ').title(),
                    description=f"Evaluate {criterion.value.replace('_', ' ')} of the response",
                    rubrics=[self.default_rubrics[criterion]],
                    weight_in_total_score=1.0,
                    evaluation_prompt=f"Assess the {criterion.value.replace('_', ' ')} of the response."
                )
        
        return templates
    
    def save_answer_keys(self, result: AnswerKeyResult, filename: str = "answer_keys") -> str:
        """
        Save answer key result to files.
        
        Args:
            result: AnswerKeyResult to save
            filename: Base filename for output files
            
        Returns:
            Path to the main output file
        """
        # Save answer keys
        answer_keys_file = self.output_dir / f"{filename}.json"
        answer_keys_data = [
            {
                "example_id": ak.example_id,
                "example_type": ak.example_type,
                "correct_answer": ak.correct_answer,
                "alternative_answers": ak.alternative_answers,
                "verification_instructions": [
                    {
                        "instruction_id": vi.instruction_id,
                        "instruction_text": vi.instruction_text,
                        "verification_type": vi.verification_type,
                        "expected_outcome": vi.expected_outcome,
                        "verification_steps": vi.verification_steps,
                        "automated_check": vi.automated_check,
                        "metadata": vi.metadata
                    }
                    for vi in ak.verification_instructions
                ],
                "scoring_rubrics": [
                    {
                        "criterion": sr.criterion.value,
                        "weight": sr.weight,
                        "max_score": sr.max_score,
                        "description": sr.description,
                        "scoring_guidelines": sr.scoring_guidelines
                    }
                    for sr in ak.scoring_rubrics
                ],
                "difficulty_level": ak.difficulty_level.value,
                "expected_response_length": ak.expected_response_length,
                "key_concepts": ak.key_concepts,
                "required_citations": ak.required_citations,
                "figure_references": ak.figure_references,
                "metadata": ak.metadata,
                "created_at": ak.created_at
            }
            for ak in result.answer_keys
        ]
        
        with open(answer_keys_file, 'w', encoding='utf-8') as f:
            json.dump(answer_keys_data, f, indent=2, ensure_ascii=False)
        
        # Save judge criteria
        judge_criteria_file = self.output_dir / f"{filename}_judge_criteria.json"
        judge_criteria_data = [
            {
                "criteria_id": jc.criteria_id,
                "name": jc.name,
                "description": jc.description,
                "rubrics": [
                    {
                        "criterion": rubric.criterion.value,
                        "weight": rubric.weight,
                        "max_score": rubric.max_score,
                        "description": rubric.description,
                        "scoring_guidelines": rubric.scoring_guidelines
                    }
                    for rubric in jc.rubrics
                ],
                "weight_in_total_score": jc.weight_in_total_score,
                "evaluation_prompt": jc.evaluation_prompt,
                "examples": jc.examples,
                "metadata": jc.metadata
            }
            for jc in result.judge_criteria
        ]
        
        with open(judge_criteria_file, 'w', encoding='utf-8') as f:
            json.dump(judge_criteria_data, f, indent=2, ensure_ascii=False)
        
        # Save generation summary
        summary_file = self.output_dir / f"{filename}_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(result.generation_summary, f, indent=2, ensure_ascii=False)
        
        return str(answer_keys_file)