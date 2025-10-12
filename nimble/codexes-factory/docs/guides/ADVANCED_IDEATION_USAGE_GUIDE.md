# Advanced Ideation System - Usage Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Core Concepts](#core-concepts)
3. [Tournament System](#tournament-system)
4. [Synthetic Reader Panels](#synthetic-reader-panels)
5. [Series Generation](#series-generation)
6. [Element Extraction & Recombination](#element-extraction--recombination)
7. [Batch Processing](#batch-processing)
8. [Continuous Generation](#continuous-generation)
9. [Longform Development](#longform-development)
10. [Analytics & Insights](#analytics--insights)
11. [Collaborative Workflows](#collaborative-workflows)
12. [API Reference](#api-reference)
13. [Best Practices](#best-practices)
14. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites
- Python 3.12+
- Codexes Factory platform installed
- LLM API access (OpenAI, Anthropic, or other supported providers)
- Streamlit for web interface

### Quick Start
1. **Launch the Ideation Dashboard**
   ```bash
   uv run streamlit run src/codexes/pages/ideation_dashboard.py
   ```

2. **Access the Web Interface**
   - Navigate to `http://localhost:8501`
   - Select your desired ideation workflow from the sidebar

3. **Create Your First Concept**
   - Use the "Quick Concept Generator" to create a basic book idea
   - Or import existing concepts from your library

## Core Concepts

### CodexObject
The foundation of all ideation workflows is the `CodexObject` - a standardized representation of book concepts.

```python
from src.codexes.modules.ideation.core.codex_object import CodexObject

# Create a new concept
concept = CodexObject(
    title="The Crystal Prophecy",
    premise="A young mage discovers an ancient prophecy that could save or destroy her world",
    genre="fantasy",
    setting="Medieval fantasy realm with floating crystal cities",
    themes=["coming of age", "power and responsibility", "sacrifice"],
    tone="epic and hopeful",
    target_audience="young adult",
    estimated_length="novel"
)
```

### Key Attributes
- **title**: The book's working title
- **premise**: Core story concept (1-2 sentences)
- **genre**: Primary genre classification
- **setting**: Where and when the story takes place
- **themes**: Central themes and messages
- **tone**: Emotional atmosphere
- **target_audience**: Intended readership
- **estimated_length**: Expected word count category

## Tournament System

### Overview
The Tournament System pits book concepts against each other in elimination-style competitions, using AI judges to determine winners based on configurable criteria.

### Creating a Tournament

#### Via Web Interface
1. Navigate to "Tournament Manager" in the sidebar
2. Click "Create New Tournament"
3. Upload or select concepts (minimum 4, maximum 64)
4. Configure tournament settings:
   - **Tournament Name**: Descriptive name for tracking
   - **Evaluation Criteria**: What judges should focus on
   - **Judge Model**: Which LLM to use for evaluation
   - **Bracket Type**: Single elimination, double elimination, or round-robin

#### Via API
```python
from src.codexes.modules.ideation.tournament.tournament_engine import TournamentEngine

engine = TournamentEngine()

# Create concepts list
concepts = [concept1, concept2, concept3, concept4]  # Your CodexObjects

# Create tournament
tournament = engine.create_tournament(
    concepts=concepts,
    tournament_name="Fantasy Concept Championship",
    evaluation_criteria="originality, market appeal, character development",
    bracket_type="single_elimination"
)

# Execute tournament
results = engine.execute_tournament(tournament.tournament_id)
```

### Understanding Results
Tournament results include:
- **Winner**: The concept that won the tournament
- **Bracket Results**: Detailed match-by-match outcomes
- **Judge Reasoning**: AI explanations for each decision
- **Confidence Scores**: How certain the AI was about each decision
- **Performance Analytics**: Strengths and weaknesses of each concept

### Export Options
- **JSON**: Complete tournament data for analysis
- **CSV**: Tabular results for spreadsheet analysis
- **PDF Report**: Human-readable tournament summary
- **Bracket Visualization**: Visual tournament tree

## Synthetic Reader Panels

### Overview
Synthetic Reader Panels simulate diverse reader demographics to evaluate how different audiences might respond to your concepts.

### Creating Reader Personas

#### Automatic Diverse Panel
```python
from src.codexes.modules.ideation.synthetic_readers.reader_panel import SyntheticReaderPanel

panel = SyntheticReaderPanel()

# Create a diverse panel of 8 readers
readers = panel.create_diverse_panel(panel_size=8)
```

#### Targeted Demographics
```python
# Create readers for specific demographics
target_demographics = {
    "age_group": "young_adult",
    "education_level": "college_graduate",
    "reading_frequency": "avid",
    "preferred_genres": ["fantasy", "romance"]
}

targeted_readers = panel.create_targeted_panel(
    demographics=target_demographics,
    panel_size=5
)
```

### Evaluating Concepts
```python
# Evaluate a concept with your reader panel
evaluation_results = panel.evaluate_concept(
    concept=your_concept,
    reader_panel=readers,
    evaluation_focus="market_appeal"
)

# Results include:
# - overall_appeal: Average appeal score (0.0-1.0)
# - demographic_breakdown: Appeal by reader demographics
# - consensus_patterns: Areas of agreement/disagreement
# - individual_evaluations: Detailed feedback from each reader
# - market_insights: Recommendations for target audience
```

### Reader Panel Analytics
- **Diversity Score**: How well your panel represents different demographics
- **Reliability Tracking**: Consistency of reader evaluations over time
- **Bias Detection**: Identification of systematic preferences
- **Market Segmentation**: Which demographics prefer which concepts

## Series Generation

### Overview
Generate cohesive book series with configurable consistency levels and franchise management capabilities.

### Basic Series Generation
```python
from src.codexes.modules.ideation.series.series_generator import (
    SeriesGenerator, SeriesConfiguration, SeriesType
)

generator = SeriesGenerator()

# Configure series parameters
config = SeriesConfiguration(
    series_type=SeriesType.SEQUENTIAL_SERIES,
    formulaicness_level=0.7,  # 0.0 = completely different, 1.0 = very similar
    target_book_count=5,
    franchise_mode=False
)

# Generate complete series
series_entries = generator.generate_complete_series(
    base_concept=your_concept,
    configuration=config
)
```

### Series Types
- **Sequential Series**: Books follow chronological order (Harry Potter style)
- **Character Series**: Same characters, different adventures (Sherlock Holmes style)
- **World Series**: Same universe, different characters (Marvel style)
- **Standalone Series**: Thematically connected but independent (Black Mirror style)
- **Franchise Series**: Extended universe with multiple sub-series

### Formulaicness Control
The formulaicness level (0.0-1.0) controls consistency:
- **0.0-0.3**: High variation, each book feels unique
- **0.4-0.6**: Moderate consistency, recognizable but fresh
- **0.7-0.9**: High consistency, reliable formula
- **0.9-1.0**: Maximum consistency, very predictable structure

### Series Management
```python
# Get series statistics
stats = generator.get_series_statistics(series_uuid)

# Adjust formulaicness mid-series
updated_series = generator.adjust_formulaicness(series_uuid, new_level=0.5)

# Reboot existing series with new parameters
reboot_config = SeriesConfiguration(formulaicness_level=0.4, target_book_count=3)
rebooted_series = generator.reboot_series(original_series_uuid, reboot_config)
```

## Element Extraction & Recombination

### Overview
Extract story elements from existing concepts and recombine them to create new, unique ideas.

### Extracting Elements
```python
from src.codexes.modules.ideation.elements.element_extractor import ElementExtractor

extractor = ElementExtractor()

# Extract elements from multiple concepts
source_concepts = [concept1, concept2, concept3]
extracted_elements = extractor.extract_elements_from_concepts(source_concepts)

# Elements are categorized as:
# - characters: Protagonist types, antagonists, supporting characters
# - settings: Locations, time periods, world-building elements
# - themes: Central messages, moral questions, emotional cores
# - plot_devices: Story structures, conflicts, resolution methods
# - tone_elements: Mood, atmosphere, narrative voice
```

### Element Selection
```python
from src.codexes.modules.ideation.elements.element_selector import ElementSelector

selector = ElementSelector()

# Select elements for recombination
selected_elements = selector.select_elements_for_recombination(
    available_elements=extracted_elements,
    selection_criteria={
        "diversity_weight": 0.7,  # Prefer diverse combinations
        "compatibility_weight": 0.8,  # Ensure elements work together
        "novelty_weight": 0.6  # Balance familiar and unique elements
    },
    target_element_count=5
)
```

### Recombination
```python
from src.codexes.modules.ideation.elements.recombination_engine import RecombinationEngine

engine = RecombinationEngine()

# Create new concept from selected elements
new_concept = engine.recombine_elements(
    elements=selected_elements,
    recombination_style="creative_fusion",  # or "structured_blend", "thematic_merge"
    target_genre="science fiction"
)
```

### Element Tracking
- **Source Provenance**: Track which concepts contributed which elements
- **Usage Statistics**: See which elements are most popular/successful
- **Compatibility Matrix**: Learn which elements work well together
- **Evolution Tracking**: See how elements change through recombination

## Batch Processing

### Overview
Process large volumes of concepts efficiently with progress tracking and error recovery.

### Basic Batch Processing
```python
from src.codexes.modules.ideation.batch.batch_processor import BatchProcessor

processor = BatchProcessor()

# Define processing function
def enhance_concept(concept):
    # Your enhancement logic here
    concept.premise = f"Enhanced: {concept.premise}"
    return concept

# Process batch
results = processor.process_batch(
    concepts=concept_list,
    processing_function=enhance_concept,
    batch_name="Concept Enhancement Batch",
    batch_size=10,  # Process 10 at a time
    max_retries=3
)
```

### Advanced Batch Operations
```python
# Tournament batch processing
tournament_results = processor.process_tournament_batch(
    concept_groups=grouped_concepts,
    tournament_config=tournament_settings
)

# Reader evaluation batch
evaluation_results = processor.process_reader_evaluation_batch(
    concepts=concepts,
    reader_panels=panels,
    evaluation_criteria="market_appeal"
)

# Series generation batch
series_results = processor.process_series_generation_batch(
    base_concepts=base_concepts,
    series_configs=configurations
)
```

### Monitoring Progress
```python
# Get real-time progress
progress = processor.get_batch_progress(batch_id)
print(f"Progress: {progress['completion_percentage']}%")
print(f"ETA: {progress['estimated_completion_time']}")

# Get detailed statistics
stats = processor.get_batch_statistics(batch_id)
```

## Continuous Generation

### Overview
Automatically generate concepts at regular intervals with monitoring and quality control.

### Setting Up Continuous Generation
```python
from src.codexes.modules.ideation.continuous.continuous_generator import ContinuousGenerationEngine

engine = ContinuousGenerationEngine()

# Configure continuous generation
config = {
    "generation_interval": 3600,  # Generate every hour
    "concepts_per_batch": 10,
    "auto_tournament": True,  # Automatically run tournaments on generated concepts
    "quality_threshold": 0.7,  # Only keep concepts above this score
    "max_storage": 1000  # Maximum concepts to store
}

# Start continuous generation
engine.start_continuous_generation(config)
```

### Monitoring Continuous Generation
```python
# Get real-time status
status = engine.get_generation_status()
print(f"Status: {status['state']}")
print(f"Concepts generated: {status['total_concepts_generated']}")
print(f"Next generation in: {status['time_until_next_generation']}")

# Get performance metrics
metrics = engine.get_performance_metrics()
```

### Quality Control
- **Automatic Filtering**: Remove low-quality concepts based on configurable criteria
- **Duplicate Detection**: Prevent generation of similar concepts
- **Diversity Enforcement**: Ensure variety in genres, themes, and styles
- **Tournament Integration**: Automatically test new concepts against existing ones

## Longform Development

### Overview
Expand promising concepts into detailed outlines, character profiles, and manuscript structures.

### Basic Longform Development
```python
from src.codexes.modules.ideation.longform.longform_developer import LongformDeveloper

developer = LongformDeveloper()

# Develop concept into full outline
detailed_outline = developer.develop_concept_to_outline(
    concept=your_concept,
    development_depth="comprehensive",  # or "basic", "detailed"
    target_length="novel"  # or "novella", "short_story"
)
```

### Character Development
```python
from src.codexes.modules.ideation.longform.character_developer import CharacterDeveloper

char_dev = CharacterDeveloper()

# Generate detailed character profiles
characters = char_dev.develop_characters_from_concept(
    concept=your_concept,
    character_count=5,
    development_focus="psychological_depth"
)

# Create character relationships
relationships = char_dev.generate_character_relationships(characters)

# Develop character arcs
arcs = char_dev.create_character_arcs(
    characters=characters,
    story_structure="three_act"
)
```

### Plot Structure Development
```python
# Generate plot structure
plot_structure = developer.generate_plot_structure(
    concept=your_concept,
    structure_type="hero_journey",  # or "three_act", "seven_point", "custom"
    complexity_level="complex"
)

# Create scene outlines
scenes = developer.generate_scene_outlines(
    plot_structure=plot_structure,
    scene_detail_level="detailed"
)

# Generate chapter breakdown
chapters = developer.create_chapter_breakdown(
    scenes=scenes,
    target_chapter_count=20
)
```

### Export Options
- **Manuscript Template**: Ready-to-write document structure
- **Character Bible**: Comprehensive character reference
- **World Building Guide**: Setting and lore documentation
- **Plot Summary**: Executive summary for pitching
- **Scene Cards**: Individual scene descriptions for planning

## Analytics & Insights

### Overview
Analyze patterns in your concepts and get data-driven recommendations for improvement.

### Pattern Analysis
```python
from src.codexes.modules.ideation.analytics.pattern_analyzer import PatternAnalyzer

analyzer = PatternAnalyzer()

# Analyze successful concepts
patterns = analyzer.analyze_success_patterns(
    concepts=your_concept_library,
    success_metric="tournament_wins"  # or "reader_appeal", "market_score"
)

# Get recommendations
recommendations = analyzer.generate_improvement_recommendations(
    concept=your_concept,
    based_on_patterns=patterns
)
```

### Market Analysis
```python
# Analyze market trends
market_trends = analyzer.analyze_market_trends(
    time_period="last_6_months",
    genre_focus="fantasy"
)

# Get demographic insights
demographic_insights = analyzer.analyze_demographic_preferences(
    concepts=concepts,
    demographic_data=reader_data
)

# Predict market appeal
appeal_prediction = analyzer.predict_market_appeal(
    concept=your_concept,
    target_demographics=["young_adult", "fantasy_readers"]
)
```

### Performance Tracking
```python
# Track concept performance over time
performance_history = analyzer.track_concept_performance(
    concept_id=concept.uuid,
    metrics=["tournament_performance", "reader_scores", "development_progress"]
)

# Compare concepts
comparison = analyzer.compare_concepts(
    concepts=[concept1, concept2, concept3],
    comparison_criteria=["originality", "market_appeal", "development_potential"]
)
```

## Collaborative Workflows

### Overview
Work with teams on ideation projects with real-time collaboration and contribution tracking.

### Creating Collaboration Sessions
```python
from src.codexes.modules.ideation.collaboration.session_manager import CollaborationSessionManager

session_manager = CollaborationSessionManager()

# Create new collaboration session
session = session_manager.create_session(
    session_name="Fantasy Series Brainstorm",
    participants=["user1", "user2", "user3"],
    session_type="concept_development",  # or "tournament", "evaluation"
    duration_hours=2
)
```

### Real-time Collaboration
```python
# Add concept to session
session_manager.add_concept_to_session(
    session_id=session.session_id,
    concept=new_concept,
    contributor="user1"
)

# Add comment/feedback
session_manager.add_comment(
    session_id=session.session_id,
    concept_id=concept.uuid,
    comment="Love the magic system, but the protagonist needs more depth",
    commenter="user2"
)

# Rate concepts collaboratively
session_manager.add_rating(
    session_id=session.session_id,
    concept_id=concept.uuid,
    rating=8.5,
    rater="user3",
    criteria="overall_appeal"
)
```

### Session Analytics
```python
# Get session statistics
stats = session_manager.get_session_statistics(session.session_id)

# Track individual contributions
contributions = session_manager.get_contribution_summary(
    session_id=session.session_id,
    participant="user1"
)

# Analyze team performance
team_performance = session_manager.analyze_team_performance(session.session_id)
```

## API Reference

### Core Classes

#### CodexObject
```python
class CodexObject:
    def __init__(self, title: str, premise: str, genre: str, **kwargs)
    def to_dict(self) -> Dict[str, Any]
    def from_dict(cls, data: Dict[str, Any]) -> 'CodexObject'
    def calculate_similarity(self, other: 'CodexObject') -> float
    def enhance_with_llm(self, enhancement_type: str) -> 'CodexObject'
```

#### TournamentEngine
```python
class TournamentEngine:
    def create_tournament(self, concepts: List[CodexObject], **kwargs) -> Tournament
    def execute_tournament(self, tournament_id: str) -> Dict[str, Any]
    def get_tournament_results(self, tournament_id: str) -> Dict[str, Any]
    def export_tournament_results(self, tournament_id: str, format: str) -> str
```

#### SyntheticReaderPanel
```python
class SyntheticReaderPanel:
    def create_diverse_panel(self, panel_size: int) -> List[ReaderPersona]
    def create_targeted_panel(self, demographics: Dict, panel_size: int) -> List[ReaderPersona]
    def evaluate_concept(self, concept: CodexObject, panel: List[ReaderPersona]) -> Dict[str, Any]
    def get_panel_statistics(self, panel: List[ReaderPersona]) -> Dict[str, Any]
```

### Configuration Options

#### Tournament Configuration
```python
tournament_config = {
    "bracket_type": "single_elimination",  # or "double_elimination", "round_robin"
    "evaluation_criteria": "originality, market_appeal, character_development",
    "judge_model": "gpt-4",
    "confidence_threshold": 0.7,
    "allow_ties": False
}
```

#### Reader Panel Configuration
```python
panel_config = {
    "diversity_requirements": {
        "age_groups": ["young_adult", "adult", "senior"],
        "education_levels": ["high_school", "college", "graduate"],
        "reading_frequencies": ["casual", "regular", "avid"]
    },
    "evaluation_focus": "market_appeal",  # or "literary_merit", "entertainment_value"
    "bias_simulation": True,
    "reliability_tracking": True
}
```

## Best Practices

### Concept Creation
1. **Be Specific**: Detailed premises perform better than vague ones
2. **Include Conflict**: Concepts with clear conflicts are more engaging
3. **Consider Audience**: Tailor concepts to specific target demographics
4. **Balance Familiarity**: Mix familiar elements with unique twists

### Tournament Strategy
1. **Diverse Concepts**: Include variety in your tournament brackets
2. **Clear Criteria**: Specify what judges should evaluate
3. **Multiple Rounds**: Run several tournaments to validate results
4. **Analyze Feedback**: Use judge reasoning to improve concepts

### Reader Panel Optimization
1. **Representative Panels**: Ensure panels match your target audience
2. **Panel Size**: Use 6-12 readers for reliable results
3. **Demographic Balance**: Include diverse perspectives
4. **Regular Updates**: Refresh reader personas periodically

### Series Development
1. **Start Conservative**: Begin with moderate formulaicness (0.5-0.7)
2. **Test Early**: Run tournaments on first few entries
3. **Monitor Consistency**: Track element usage across entries
4. **Plan Ahead**: Outline entire series before generating all entries

### Performance Optimization
1. **Use Caching**: Enable caching for repeated operations
2. **Batch Processing**: Process multiple concepts together
3. **Monitor Resources**: Track LLM usage and costs
4. **Regular Cleanup**: Remove unused concepts and data

## Troubleshooting

### Common Issues

#### "LLM Service Unavailable"
- Check your API keys and configuration
- Verify network connectivity
- Try switching to a different LLM provider
- Check rate limits and quotas

#### "Tournament Creation Failed"
- Ensure you have at least 4 concepts
- Verify all concepts have required fields
- Check that concepts are properly formatted
- Try reducing the number of concepts

#### "Reader Panel Evaluation Timeout"
- Reduce panel size
- Simplify evaluation criteria
- Check LLM service status
- Enable caching to speed up repeated evaluations

#### "Series Generation Inconsistent"
- Adjust formulaicness level
- Check base concept quality
- Verify series configuration
- Review generated elements for conflicts

#### "Batch Processing Stuck"
- Check error logs for specific failures
- Reduce batch size
- Verify processing function works on individual concepts
- Check available system resources

### Performance Issues

#### Slow Tournament Execution
- Enable result caching
- Use faster LLM models for initial rounds
- Reduce evaluation criteria complexity
- Process tournaments during off-peak hours

#### High LLM Costs
- Enable aggressive caching
- Use cheaper models for preliminary evaluations
- Batch similar requests together
- Set cost limits and monitoring

#### Memory Usage High
- Clear unused concepts from memory
- Reduce batch sizes
- Enable automatic cleanup
- Monitor database size

### Getting Help

1. **Check Logs**: Review `logs/ideation/` for detailed error messages
2. **Documentation**: Refer to API documentation for specific functions
3. **Community**: Join the Codexes Factory community forums
4. **Support**: Contact technical support with specific error messages

### Debug Mode
Enable debug mode for detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export IDEATION_DEBUG=true
```

This comprehensive guide covers all major aspects of the Advanced Ideation system. For specific implementation details, refer to the API documentation and code examples in the `examples/` directory.