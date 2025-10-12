"""
Tests for answer key generation functionality.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch

from src.arxiv_writer.core.answer_key_generator import (
    AnswerKeyGenerator,
    AnswerKey,
    AnswerKeyResult,
    VerificationInstruction,
    ScoringRubric,
    JudgeEvaluationCriteria,
    DifficultyLevel,
    EvaluationCriteria
)
from src.arxiv_writer.core.content_extractor import (
    ExtractedFigure,
    SFTExample,
    RLExample,
    ExtractionResult
)


class TestAnswerKeyGenerator:
    """Test cases for AnswerKeyGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = AnswerKeyGenerator(output_dir=self.temp_dir)
        
        # Sample extraction result for testing
        self.sample_figures = [
            ExtractedFigure(
                figure_id="fig_001",
                caption="Test figure showing results",
                file_path="/path/to/fig_001.png",
                figure_type="image"
            )
        ]
        
        self.sample_sft_examples = [
            SFTExample(
                example_id="sft_001",
                context="Previous research has shown limitations in existing approaches.",
                analysis_passage="Our analysis reveals that the proposed method significantly outperforms baseline approaches. The results indicate a 25% improvement in accuracy. We found that the key factor is the novel attention mechanism.",
                conclusion="Therefore, we conclude that this approach is superior for this task.",
                section_type="results",
                quality_score=0.85,
                figures_referenced=["fig_001"]
            )
        ]
        
        self.sample_rl_examples = [
            RLExample(
                example_id="rl_001",
                case_study_title="Case Study: Medical Image Classification",
                problem_description="The problem we address is accurate classification of medical images with limited training data.",
                methodology="Our method uses transfer learning with pre-trained convolutional neural networks.",
                results="The results showed 15% improvement over baseline methods with 95% accuracy.",
                lessons_learned="The key lesson is that pre-training on large datasets is crucial for success.",
                figures_referenced=["fig_001"]
            )
        ]
        
        self.sample_extraction_result = ExtractionResult(
            markdown_content="# Test Content",
            figures=self.sample_figures,
            sft_examples=self.sample_sft_examples,
            rl_examples=self.sample_rl_examples,
            extraction_summary={"test": "data"}
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test AnswerKeyGenerator initialization."""
        assert self.generator.output_dir.exists()
        assert len(self.generator.default_rubrics) > 0
        assert len(self.generator.verification_templates) > 0
        assert len(self.generator.judge_criteria_templates) > 0
    
    def test_generate_answer_keys(self):
        """Test complete answer key generation."""
        result = self.generator.generate_answer_keys(self.sample_extraction_result)
        
        assert isinstance(result, AnswerKeyResult)
        assert len(result.answer_keys) == 2  # 1 SFT + 1 RL
        assert len(result.judge_criteria) > 0
        assert result.generation_summary["total_answer_keys"] == 2
        assert result.generation_summary["sft_answer_keys"] == 1
        assert result.generation_summary["rl_answer_keys"] == 1
    
    def test_generate_sft_answer_key(self):
        """Test SFT answer key generation."""
        sft_example = self.sample_sft_examples[0]
        answer_key = self.generator._generate_sft_answer_key(sft_example, self.sample_figures)
        
        assert isinstance(answer_key, AnswerKey)
        assert answer_key.example_id == "sft_001"
        assert answer_key.example_type == "sft"
        assert len(answer_key.correct_answer) > 0
        assert len(answer_key.verification_instructions) > 0
        assert len(answer_key.scoring_rubrics) > 0
        assert answer_key.difficulty_level in DifficultyLevel
        assert len(answer_key.key_concepts) > 0
        assert "fig_001" in answer_key.figure_references
    
    def test_generate_rl_answer_key(self):
        """Test RL answer key generation."""
        rl_example = self.sample_rl_examples[0]
        answer_key = self.generator._generate_rl_answer_key(rl_example, self.sample_figures)
        
        assert isinstance(answer_key, AnswerKey)
        assert answer_key.example_id == "rl_001"
        assert answer_key.example_type == "rl"
        assert len(answer_key.correct_answer) > 0
        assert "Case Study:" in answer_key.correct_answer
        assert "Problem:" in answer_key.correct_answer
        assert "Methodology:" in answer_key.correct_answer
        assert len(answer_key.verification_instructions) > 0
        assert len(answer_key.scoring_rubrics) > 0
        assert "fig_001" in answer_key.figure_references
    
    def test_create_sft_correct_answer(self):
        """Test SFT correct answer creation."""
        sft_example = self.sample_sft_examples[0]
        answer = self.generator._create_sft_correct_answer(sft_example)
        
        assert "Context:" in answer
        assert "Analysis:" in answer
        assert "Conclusion:" in answer
        assert sft_example.context in answer
        assert sft_example.analysis_passage in answer
        assert sft_example.conclusion in answer
    
    def test_create_rl_correct_answer(self):
        """Test RL correct answer creation."""
        rl_example = self.sample_rl_examples[0]
        answer = self.generator._create_rl_correct_answer(rl_example)
        
        assert "Case Study:" in answer
        assert "Problem:" in answer
        assert "Methodology:" in answer
        assert "Results:" in answer
        assert "Lessons Learned:" in answer
        assert rl_example.case_study_title in answer
        assert rl_example.problem_description in answer
    
    def test_generate_alternative_answers_sft(self):
        """Test alternative answer generation for SFT."""
        sft_example = self.sample_sft_examples[0]
        alternatives = self.generator._generate_alternative_answers(sft_example, "sft")
        
        assert isinstance(alternatives, list)
        assert len(alternatives) > 0
        assert any("Key Finding:" in alt for alt in alternatives)
        assert any("Summary:" in alt for alt in alternatives)
    
    def test_generate_alternative_answers_rl(self):
        """Test alternative answer generation for RL."""
        rl_example = self.sample_rl_examples[0]
        alternatives = self.generator._generate_alternative_answers(rl_example, "rl")
        
        assert isinstance(alternatives, list)
        assert len(alternatives) > 0
        assert any("Problem-Solution Pair:" in alt for alt in alternatives)
        assert any("Outcome Analysis:" in alt for alt in alternatives)
    
    def test_create_sft_verification_instructions(self):
        """Test SFT verification instructions creation."""
        sft_example = self.sample_sft_examples[0]
        instructions = self.generator._create_sft_verification_instructions(sft_example)
        
        assert isinstance(instructions, list)
        assert len(instructions) >= 2  # At least factual and logical
        
        # Check for required instruction types
        instruction_types = [inst.verification_type for inst in instructions]
        assert "factual" in instruction_types
        assert "logical" in instruction_types
        
        # Check for technical instruction for results section
        if sft_example.section_type == "results":
            assert "technical" in instruction_types
        
        # Verify instruction structure
        for instruction in instructions:
            assert instruction.instruction_id.startswith(sft_example.example_id)
            assert len(instruction.instruction_text) > 0
            assert len(instruction.expected_outcome) > 0
            assert len(instruction.verification_steps) > 0
    
    def test_create_rl_verification_instructions(self):
        """Test RL verification instructions creation."""
        rl_example = self.sample_rl_examples[0]
        instructions = self.generator._create_rl_verification_instructions(rl_example)
        
        assert isinstance(instructions, list)
        assert len(instructions) >= 2  # At least alignment and consistency
        
        # Check for required instruction types
        instruction_types = [inst.verification_type for inst in instructions]
        assert "logical" in instruction_types
        assert "factual" in instruction_types
        
        # Check for lessons learned instruction if present
        if rl_example.lessons_learned:
            assert len(instructions) >= 3
        
        # Verify instruction structure
        for instruction in instructions:
            assert instruction.instruction_id.startswith(rl_example.example_id)
            assert len(instruction.instruction_text) > 0
            assert len(instruction.expected_outcome) > 0
            assert len(instruction.verification_steps) > 0
    
    def test_select_rubrics_for_sft(self):
        """Test rubric selection for SFT examples."""
        sft_example = self.sample_sft_examples[0]
        rubrics = self.generator._select_rubrics_for_sft(sft_example)
        
        assert isinstance(rubrics, list)
        assert len(rubrics) > 0
        
        # Check for basic rubrics
        rubric_criteria = [rubric.criterion for rubric in rubrics]
        assert EvaluationCriteria.ACCURACY in rubric_criteria
        assert EvaluationCriteria.CLARITY in rubric_criteria
        assert EvaluationCriteria.COHERENCE in rubric_criteria
        
        # Check for technical depth in results section
        if sft_example.section_type in ["methodology", "results"]:
            assert EvaluationCriteria.TECHNICAL_DEPTH in rubric_criteria
        
        # Check for figure integration if figures referenced
        if sft_example.figures_referenced:
            assert EvaluationCriteria.FIGURE_INTEGRATION in rubric_criteria
    
    def test_select_rubrics_for_rl(self):
        """Test rubric selection for RL examples."""
        rl_example = self.sample_rl_examples[0]
        rubrics = self.generator._select_rubrics_for_rl(rl_example)
        
        assert isinstance(rubrics, list)
        assert len(rubrics) > 0
        
        # Check for basic rubrics
        rubric_criteria = [rubric.criterion for rubric in rubrics]
        assert EvaluationCriteria.COMPLETENESS in rubric_criteria
        assert EvaluationCriteria.COHERENCE in rubric_criteria
        assert EvaluationCriteria.TECHNICAL_DEPTH in rubric_criteria
        
        # Check for figure integration if figures referenced
        if rl_example.figures_referenced:
            assert EvaluationCriteria.FIGURE_INTEGRATION in rubric_criteria
    
    def test_determine_difficulty_level(self):
        """Test difficulty level determination."""
        # Test different complexity levels
        simple_content = "This is a simple analysis."
        complex_content = "The sophisticated algorithm employs advanced statistical methodology for optimization analysis using complex architectural frameworks and implementation techniques."
        
        simple_level = self.generator._determine_difficulty_level(simple_content)
        complex_level = self.generator._determine_difficulty_level(complex_content)
        
        assert simple_level in DifficultyLevel
        assert complex_level in DifficultyLevel
        # Complex content should have higher difficulty
        difficulty_order = [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT]
        assert difficulty_order.index(complex_level) >= difficulty_order.index(simple_level)
    
    def test_extract_key_concepts(self):
        """Test key concept extraction."""
        content = "The machine learning algorithm uses neural network architecture for classification analysis and optimization."
        concepts = self.generator._extract_key_concepts(content)
        
        assert isinstance(concepts, list)
        assert len(concepts) > 0
        assert len(concepts) <= 10  # Should limit to top 10
        
        # Check for expected technical terms
        concepts_lower = [c.lower() for c in concepts]
        assert any("algorithm" in c for c in concepts_lower)
        assert any("analysis" in c for c in concepts_lower)
    
    def test_estimate_response_length(self):
        """Test response length estimation."""
        short_content = "Short analysis."
        long_content = " ".join(["This is a detailed analysis."] * 50)
        
        short_length = self.generator._estimate_response_length(short_content)
        long_length = self.generator._estimate_response_length(long_content)
        
        assert isinstance(short_length, tuple)
        assert isinstance(long_length, tuple)
        assert len(short_length) == 2
        assert len(long_length) == 2
        assert short_length[0] <= short_length[1]  # min <= max
        assert long_length[0] <= long_length[1]
        assert long_length[1] > short_length[1]  # Longer content should have higher max
    
    def test_classify_problem_type(self):
        """Test problem type classification."""
        classification_problem = "The problem is to classify images into categories."
        prediction_problem = "We need to predict future stock prices."
        optimization_problem = "The goal is to minimize the cost function."
        detection_problem = "The task is to detect anomalies in the data."
        general_problem = "This is a general research question."
        
        assert self.generator._classify_problem_type(classification_problem) == "classification"
        assert self.generator._classify_problem_type(prediction_problem) == "prediction"
        assert self.generator._classify_problem_type(optimization_problem) == "optimization"
        assert self.generator._classify_problem_type(detection_problem) == "detection"
        assert self.generator._classify_problem_type(general_problem) == "general"
    
    def test_generate_judge_criteria(self):
        """Test judge criteria generation."""
        # Create answer keys with different rubrics
        answer_keys = [
            AnswerKey(
                example_id="test_001",
                example_type="sft",
                correct_answer="Test answer",
                scoring_rubrics=[
                    self.generator.default_rubrics[EvaluationCriteria.ACCURACY],
                    self.generator.default_rubrics[EvaluationCriteria.CLARITY]
                ]
            )
        ]
        
        judge_criteria = self.generator._generate_judge_criteria(answer_keys)
        
        assert isinstance(judge_criteria, list)
        assert len(judge_criteria) > 0
        
        # Check that criteria match the rubrics used
        criteria_ids = [jc.criteria_id for jc in judge_criteria]
        assert "accuracy_judge" in criteria_ids
    
    def test_save_answer_keys(self):
        """Test saving answer keys to files."""
        result = self.generator.generate_answer_keys(self.sample_extraction_result)
        output_file = self.generator.save_answer_keys(result, "test_output")
        
        # Check that files were created
        assert Path(output_file).exists()
        assert (self.generator.output_dir / "test_output_judge_criteria.json").exists()
        assert (self.generator.output_dir / "test_output_summary.json").exists()
        
        # Verify content can be loaded
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 2  # 1 SFT + 1 RL
            
            # Check structure of first answer key
            first_key = data[0]
            assert "example_id" in first_key
            assert "correct_answer" in first_key
            assert "verification_instructions" in first_key
            assert "scoring_rubrics" in first_key


class TestScoringRubric:
    """Test cases for ScoringRubric dataclass."""
    
    def test_scoring_rubric_creation(self):
        """Test ScoringRubric creation and default guidelines."""
        rubric = ScoringRubric(
            criterion=EvaluationCriteria.ACCURACY,
            weight=1.5,
            description="Test rubric"
        )
        
        assert rubric.criterion == EvaluationCriteria.ACCURACY
        assert rubric.weight == 1.5
        assert rubric.max_score == 5
        assert rubric.description == "Test rubric"
        assert len(rubric.scoring_guidelines) == 5  # Default guidelines
        assert 5 in rubric.scoring_guidelines
        assert 1 in rubric.scoring_guidelines
    
    def test_scoring_rubric_custom_guidelines(self):
        """Test ScoringRubric with custom guidelines."""
        custom_guidelines = {
            3: "Perfect",
            2: "Good", 
            1: "Poor"
        }
        
        rubric = ScoringRubric(
            criterion=EvaluationCriteria.CLARITY,
            max_score=3,
            scoring_guidelines=custom_guidelines
        )
        
        assert rubric.max_score == 3
        assert rubric.scoring_guidelines == custom_guidelines


class TestVerificationInstruction:
    """Test cases for VerificationInstruction dataclass."""
    
    def test_verification_instruction_creation(self):
        """Test VerificationInstruction creation."""
        instruction = VerificationInstruction(
            instruction_id="test_001",
            instruction_text="Test instruction",
            verification_type="factual",
            expected_outcome="Test outcome",
            verification_steps=["Step 1", "Step 2"],
            automated_check=True,
            metadata={"test": "data"}
        )
        
        assert instruction.instruction_id == "test_001"
        assert instruction.instruction_text == "Test instruction"
        assert instruction.verification_type == "factual"
        assert instruction.expected_outcome == "Test outcome"
        assert instruction.verification_steps == ["Step 1", "Step 2"]
        assert instruction.automated_check is True
        assert instruction.metadata["test"] == "data"


class TestAnswerKey:
    """Test cases for AnswerKey dataclass."""
    
    def test_answer_key_creation(self):
        """Test AnswerKey creation with all fields."""
        rubric = ScoringRubric(criterion=EvaluationCriteria.ACCURACY)
        instruction = VerificationInstruction(
            instruction_id="test_001",
            instruction_text="Test",
            verification_type="factual",
            expected_outcome="Test outcome"
        )
        
        answer_key = AnswerKey(
            example_id="test_001",
            example_type="sft",
            correct_answer="Test answer",
            alternative_answers=["Alt 1", "Alt 2"],
            verification_instructions=[instruction],
            scoring_rubrics=[rubric],
            difficulty_level=DifficultyLevel.ADVANCED,
            expected_response_length=(100, 300),
            key_concepts=["concept1", "concept2"],
            required_citations=["ref1"],
            figure_references=["fig_001"],
            metadata={"test": "data"}
        )
        
        assert answer_key.example_id == "test_001"
        assert answer_key.example_type == "sft"
        assert answer_key.correct_answer == "Test answer"
        assert len(answer_key.alternative_answers) == 2
        assert len(answer_key.verification_instructions) == 1
        assert len(answer_key.scoring_rubrics) == 1
        assert answer_key.difficulty_level == DifficultyLevel.ADVANCED
        assert answer_key.expected_response_length == (100, 300)
        assert len(answer_key.key_concepts) == 2
        assert len(answer_key.figure_references) == 1
        assert answer_key.metadata["test"] == "data"
        assert answer_key.created_at  # Should be auto-generated


class TestJudgeEvaluationCriteria:
    """Test cases for JudgeEvaluationCriteria dataclass."""
    
    def test_judge_criteria_creation(self):
        """Test JudgeEvaluationCriteria creation."""
        rubric = ScoringRubric(criterion=EvaluationCriteria.ACCURACY)
        
        criteria = JudgeEvaluationCriteria(
            criteria_id="accuracy_judge",
            name="Accuracy",
            description="Test accuracy",
            rubrics=[rubric],
            weight_in_total_score=1.5,
            evaluation_prompt="Test prompt",
            examples={"5": "Perfect", "1": "Poor"},
            metadata={"test": "data"}
        )
        
        assert criteria.criteria_id == "accuracy_judge"
        assert criteria.name == "Accuracy"
        assert criteria.description == "Test accuracy"
        assert len(criteria.rubrics) == 1
        assert criteria.weight_in_total_score == 1.5
        assert criteria.evaluation_prompt == "Test prompt"
        assert criteria.examples["5"] == "Perfect"
        assert criteria.metadata["test"] == "data"


class TestAnswerKeyResult:
    """Test cases for AnswerKeyResult dataclass."""
    
    def test_answer_key_result_creation(self):
        """Test AnswerKeyResult creation."""
        answer_key = AnswerKey(
            example_id="test_001",
            example_type="sft",
            correct_answer="Test answer"
        )
        
        judge_criteria = JudgeEvaluationCriteria(
            criteria_id="test_judge",
            name="Test",
            description="Test criteria"
        )
        
        result = AnswerKeyResult(
            answer_keys=[answer_key],
            judge_criteria=[judge_criteria],
            generation_summary={"total": 1},
            metadata={"test": "data"}
        )
        
        assert len(result.answer_keys) == 1
        assert len(result.judge_criteria) == 1
        assert result.generation_summary["total"] == 1
        assert result.metadata["test"] == "data"