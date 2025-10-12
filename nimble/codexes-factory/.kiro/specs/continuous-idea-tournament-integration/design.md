# Design Document

## Overview

This design integrates the ContinuousIdeaGenerator and Tournament system with synthetic reader feedback into the codexes-factory platform. The system creates a continuous pipeline from idea generation through competitive evaluation to production-ready book concepts, with synthetic reader feedback informing the entire publishing strategy.

## Architecture

### Current System Analysis

The integrate_ideas directory contains:
- **ContinuousIdeaGenerator**: Generates batches of book ideas using LLM models with configurable intervals
- **Tournament**: Manages competitive evaluation of ideas using bracket-style tournaments with LLM judges
- **Idea**: Core data structure for representing book concepts
- **Models2BookIdeas**: Interface for LLM-based idea generation

### Integration Strategy

The system will be integrated into codexes-factory through:
1. **Module Integration**: Move core classes into `src/codexes/modules/ideation/`
2. **UI Integration**: Enhance the existing Ideation page with tournament and reader feedback interfaces
3. **Pipeline Integration**: Connect winning ideas to the book production pipeline
4. **Feedback Loop**: Use synthetic reader insights to improve generation and editing processes

## Components and Interfaces

### 1. Continuous Idea Generation System

```python
class IntegratedIdeaGenerator:
    """
    Enhanced version of ContinuousIdeaGenerator integrated with codexes-factory.
    Manages 24/7 idea generation with imprint-specific customization.
    """
    
    def __init__(self, imprint_config: Dict, llm_caller: LLMCaller):
        self.imprint_config = imprint_config
        self.llm_caller = llm_caller
        self.tournament_manager = TournamentManager()
        self.synthetic_reader_panel = SyntheticReaderPanel()
    
    def generate_imprint_aligned_ideas(self, imprint_name: str) -> List[BookIdea]:
        # Generate ideas aligned with specific imprint themes and requirements
        # Use imprint-specific prompts and constraints
        # Apply imprint branding and target audience considerations
        pass
    
    def start_continuous_generation(self, schedule_config: Dict):
        # Start 24/7 generation with configurable intervals
        # Monitor system health and performance
        # Handle graceful shutdown and recovery
        pass
```

### 2. Tournament Management System

```python
class TournamentManager:
    """
    Manages tournament creation, execution, and result processing.
    Integrates with the existing Tournament class but adds codexes-factory specific features.
    """
    
    def __init__(self, llm_caller: LLMCaller):
        self.llm_caller = llm_caller
        self.active_tournaments = {}
        self.tournament_history = []
    
    def create_tournament(self, ideas: List[BookIdea], tournament_config: Dict) -> Tournament:
        # Create tournament with codexes-factory LLM integration
        # Apply imprint-specific judging criteria
        # Configure tournament size and bracket structure
        pass
    
    def process_tournament_results(self, tournament: Tournament) -> TournamentResults:
        # Process results and identify winners
        # Generate detailed analysis and reasoning
        # Prepare winners for synthetic reader evaluation
        pass
    
    def promote_winners_to_pipeline(self, winners: List[BookIdea], imprint: str):
        # Convert winning ideas to book metadata format
        # Add to appropriate imprint schedules
        # Trigger book pipeline integration
        pass
```

### 3. Synthetic Reader Integration

```python
class SyntheticReaderPanel:
    """
    Manages synthetic reader evaluation of tournament winners.
    Provides multi-perspective feedback on market appeal and audience fit.
    """
    
    def __init__(self, llm_caller: LLMCaller):
        self.llm_caller = llm_caller
        self.reader_personas = self.load_reader_personas()
        self.feedback_synthesizer = FeedbackSynthesizer()
    
    def evaluate_ideas(self, ideas: List[BookIdea]) -> List[ReaderFeedback]:
        # Evaluate ideas from multiple synthetic reader perspectives
        # Generate feedback on market appeal, genre fit, audience targeting
        # Provide recommendations for improvement or rejection
        pass
    
    def synthesize_feedback(self, feedback_list: List[ReaderFeedback]) -> SynthesizedInsights:
        # Analyze patterns across reader feedback
        # Generate actionable insights for ideation, editing, and imprints
        # Identify trends and opportunities
        pass
```

### 4. Pipeline Integration Bridge

```python
class IdeationPipelineBridge:
    """
    Bridges the ideation system with the existing book production pipeline.
    Handles format conversion and schedule integration.
    """
    
    def __init__(self, schedule_manager: ScheduleManager):
        self.schedule_manager = schedule_manager
        self.metadata_converter = MetadataConverter()
    
    def convert_idea_to_metadata(self, idea: BookIdea, imprint: str) -> CodexMetadata:
        # Convert BookIdea to CodexMetadata format
        # Apply imprint-specific defaults and branding
        # Ensure compatibility with existing pipeline
        pass
    
    def add_to_schedule(self, metadata: CodexMetadata, imprint: str, priority: int):
        # Add winning ideas to imprint schedules
        # Respect existing scheduling constraints
        # Handle conflicts and priorities
        pass
```

### 5. Enhanced Ideation UI

```python
class IdeationDashboard:
    """
    Streamlit-based dashboard for monitoring and controlling the ideation system.
    Replaces the basic Ideation page with comprehensive functionality.
    """
    
    def render_dashboard(self):
        # Real-time status of idea generation and tournaments
        # Controls for starting/stopping continuous generation
        # Tournament results visualization
        # Synthetic reader feedback display
        # Manual promotion and rejection controls
        pass
    
    def render_tournament_viewer(self, tournament: Tournament):
        # Interactive tournament bracket visualization
        # Match details and LLM reasoning
        # Winner progression tracking
        pass
    
    def render_reader_feedback(self, feedback: List[ReaderFeedback]):
        # Synthetic reader evaluation results
        # Feedback synthesis and insights
        # Trend analysis and recommendations
        pass
```

## Data Models

### Enhanced Book Idea

```python
@dataclass
class BookIdea:
    """Enhanced version of the Idea class with codexes-factory integration."""
    title: str
    logline: str
    description: str = ""
    genre: str = ""
    target_audience: str = ""
    imprint_alignment: float = 0.0
    tournament_performance: Dict[str, Any] = field(default_factory=dict)
    reader_feedback: List[ReaderFeedback] = field(default_factory=list)
    generation_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "generated"  # generated, tournament, reader_review, approved, rejected
```

### Tournament Results

```python
@dataclass
class TournamentResults:
    """Comprehensive tournament results with analysis."""
    tournament_id: str
    winner: BookIdea
    finalists: List[BookIdea]
    all_participants: List[BookIdea]
    match_history: List[Dict[str, Any]]
    performance_analysis: Dict[str, Any]
    completion_time: datetime
    imprint: str
```

### Synthetic Reader Feedback

```python
@dataclass
class ReaderFeedback:
    """Feedback from a synthetic reader persona."""
    reader_persona: str
    idea_id: str
    market_appeal_score: float
    genre_fit_score: float
    audience_alignment_score: float
    detailed_feedback: str
    recommendations: List[str]
    concerns: List[str]
    overall_rating: float
```

### Synthesized Insights

```python
@dataclass
class SynthesizedInsights:
    """Aggregated insights from multiple reader feedback."""
    idea_id: str
    overall_consensus: str
    market_potential: float
    recommended_improvements: List[str]
    target_audience_refinement: str
    genre_recommendations: List[str]
    imprint_suggestions: List[str]
    editing_priorities: List[str]
```

## Error Handling

### Generation Failures
- Retry with different prompts or models
- Log failures with full context
- Continue operation with reduced batch sizes
- Alert administrators for persistent failures

### Tournament Failures
- Handle insufficient participants with bye rounds
- Retry failed matches with different evaluation criteria
- Preserve partial results and allow manual completion
- Fallback to random selection if LLM evaluation fails

### Reader Feedback Failures
- Continue with available reader feedback if some fail
- Use fallback evaluation criteria
- Log missing perspectives for later retry
- Provide warnings about incomplete feedback

### Pipeline Integration Failures
- Queue ideas for manual review
- Preserve all data for later processing
- Alert users to integration issues
- Provide manual promotion interfaces

## Testing Strategy

### Unit Tests
- Test idea generation with various prompts and models
- Validate tournament bracket creation and match processing
- Test synthetic reader feedback generation and synthesis
- Verify pipeline integration and metadata conversion

### Integration Tests
- Test complete flow from generation to pipeline integration
- Verify UI responsiveness and real-time updates
- Test error handling and recovery scenarios
- Validate data persistence and retrieval

### Performance Tests
- Test 24/7 continuous operation under load
- Measure tournament processing times with various sizes
- Test synthetic reader evaluation scalability
- Validate system resource usage and optimization

## Implementation Plan

### Phase 1: Core Integration
1. Move Tournament and ContinuousIdeaGenerator classes to codexes-factory
2. Integrate with existing LLM caller infrastructure
3. Create basic pipeline bridge for metadata conversion
4. Implement enhanced Ideation UI with tournament viewing

### Phase 2: Synthetic Reader Integration
1. Design and implement synthetic reader persona system
2. Create reader feedback evaluation and synthesis
3. Integrate feedback into ideation and editing workflows
4. Add reader feedback visualization to UI

### Phase 3: Advanced Features
1. Implement imprint-specific idea generation
2. Add advanced tournament configurations and judging criteria
3. Create comprehensive monitoring and alerting
4. Implement feedback-driven prompt optimization

### Phase 4: Production Optimization
1. Optimize for 24/7 continuous operation
2. Implement advanced error recovery and resilience
3. Add comprehensive analytics and reporting
4. Create administrative tools for system management

## Integration Points

### Existing Codexes-Factory Systems
- **LLM Caller**: Use existing `src/codexes/core/llm_caller.py` for all LLM interactions
- **Schedule Management**: Integrate with existing book scheduling system
- **Imprint Configuration**: Use existing imprint configuration system
- **Metadata Models**: Convert to existing `CodexMetadata` format
- **UI Framework**: Extend existing Streamlit page structure

### External Dependencies
- **Ollama/OpenAI**: LLM model access for idea generation and evaluation
- **NLTK**: Text processing for idea analysis
- **Pandas**: Data manipulation for tournament results and feedback
- **Threading**: Background processing for continuous operation

## Monitoring and Observability

### Key Metrics
- Ideas generated per hour/day
- Tournament completion rates and times
- Synthetic reader feedback quality scores
- Pipeline integration success rates
- System uptime and error rates

### Logging Strategy
- Structured logging with JSON format
- Separate log levels for different components
- Performance metrics logging
- Error tracking with full context
- User action logging for audit trails

### Alerting
- System health degradation alerts
- Continuous generation failure alerts
- Tournament processing delays
- Pipeline integration failures
- Resource usage threshold alerts