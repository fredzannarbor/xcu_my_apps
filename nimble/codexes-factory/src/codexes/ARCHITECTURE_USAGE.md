# Codexes Factory - Object-Oriented Architecture Usage Guide

This document demonstrates how to use the new Rich Domain Model and Repository Pattern architecture.

## Architecture Overview

The codebase follows a clean architecture pattern with three main layers:

1. **Domain Layer** (`domain/models/`) - Rich domain models with business logic
2. **Infrastructure Layer** (`infrastructure/repositories/`) - Persistence and data access
3. **Application Layer** (`application/services/`) - Orchestration and use cases

## Quick Start Examples

### 1. Creating an Imprint

```python
from pathlib import Path
from src.codexes.domain.models import BrandingSpecification, PublishingFocus
from src.codexes.infrastructure.repositories import ImprintRepository
from src.codexes.application.services import ImprintCreationService

# Set up repository and service
base_path = Path("/path/to/codexes/configs")
repository = ImprintRepository(base_path)
service = ImprintCreationService(repository)

# Create branding specification
branding = BrandingSpecification(
    display_name="Stellar Press",
    tagline="Books that reach for the stars",
    mission_statement="Publishing visionary science fiction",
    brand_values=["Innovation", "Imagination", "Quality"],
    primary_color="#0066CC",
    secondary_color="#FF6600",
    font_family="Inter"
)

# Create publishing focus
focus = PublishingFocus(
    primary_genres=["Science Fiction", "Space Opera"],
    target_audience="Adult sci-fi enthusiasts",
    price_point="$14.99-$24.99",
    books_per_year=12
)

# Create the imprint
imprint = service.create_from_wizard(
    name="Stellar Press",
    publisher="Codexes Publishing",
    charter="We publish bold science fiction that explores humanity's future among the stars.",
    branding=branding,
    publishing_focus=focus,
    auto_activate=True
)

print(f"Created imprint: {imprint}")
```

### 2. Adding a Publisher Persona

```python
from src.codexes.domain.models import PublisherPersona, RiskTolerance, DecisionStyle

# Create a publisher persona
persona = PublisherPersona(
    name="Dr. Stella Nova",
    bio="Former NASA scientist turned publisher with a passion for hard science fiction",
    risk_tolerance=RiskTolerance.AGGRESSIVE,
    decision_style=DecisionStyle.DATA_DRIVEN,
    preferred_topics=["Space Exploration", "Physics", "AI"],
    target_demographics=["Scientists", "Engineers", "Educators"],
    vulnerabilities=["May overlook softer sci-fi", "Prefers technical accuracy over narrative"]
)

# Attach to imprint
imprint.set_persona(persona)
repository.save(imprint)

# Evaluate a book concept
decision = persona.evaluate_book_concept(
    "A novel about AI achieving consciousness on a generation ship",
    context={"genre": "Science Fiction", "technical_accuracy": "high"}
)
print(f"Decision: {decision.decision} (confidence: {decision.confidence})")
```

### 3. Running a Tournament

```python
from pathlib import Path
from src.codexes.domain.models import ImprintIdea
from src.codexes.infrastructure.repositories import TournamentRepository
from src.codexes.application.services import TournamentService, ImprintCreationService

# Set up services
tournament_repo = TournamentRepository(Path("/path/to/tournaments"))
imprint_repo = ImprintRepository(Path("/path/to/imprints"))
imprint_service = ImprintCreationService(imprint_repo)
tournament_service = TournamentService(tournament_repo, imprint_service)

# Create a tournament
tournament = tournament_service.create_tournament(
    name="Spring 2025 Imprint Competition",
    size=8,
    criteria="Innovation, Market Potential, Editorial Uniqueness",
    allow_public_voting=True
)

# Add user ideas
idea1 = tournament_service.add_user_idea(
    tournament=tournament,
    name="Quantum Fiction Press",
    charter="Publishing mind-bending quantum physics fiction",
    focus="Hard sci-fi with quantum mechanics themes"
)

# Generate AI ideas to fill remaining slots
ai_ideas = tournament_service.generate_ai_ideas(
    tournament=tournament,
    count=7,
    context={"theme": "science fiction", "innovation": "high"}
)

# Start the tournament
tournament_service.start_tournament(tournament)

# Simulate voting
current_round = tournament.get_current_round()
for matchup in current_round.matchups:
    # Vote for idea 1 in each matchup (simplified example)
    tournament_service.record_vote(tournament, matchup.id, matchup.idea1_id)

# After tournament completes, create imprint from winner
if tournament.status.value == 'completed':
    winning_imprint = tournament_service.create_imprint_from_winner(
        tournament=tournament,
        publisher="Codexes Publishing",
        branding_config={
            'primary_color': '#FF6600',
            'secondary_color': '#0066CC'
        }
    )
    print(f"Created winning imprint: {winning_imprint}")
```

### 4. Querying Imprints

```python
# Get all active imprints
active_imprints = service.get_all_active()
for imprint in active_imprints:
    print(f"{imprint.display_name} - {imprint.branding.tagline}")

# Get specific imprint by slug
stellar_press = service.get_by_slug("stellar_press")
if stellar_press:
    print(f"Found: {stellar_press}")
    print(f"Valid: {stellar_press.is_valid()}")
    print(f"Active: {stellar_press.is_active}")
```

## Key Design Patterns

### Rich Domain Models

Domain models contain business logic and validation:

```python
# Imprint validates itself
imprint.is_valid()  # Returns True/False

# Imprint manages its own lifecycle
imprint.activate()  # Changes status if valid

# Branding knows how to validate itself
branding.is_complete()  # Checks all required fields

# Branding provides CSS variables
css_vars = branding.get_css_variables()
```

### Repository Pattern

Repositories abstract persistence:

```python
# Repository handles all I/O
repository.save(imprint)
repository.get_by_slug("stellar_press")
repository.get_all()
repository.delete("old_imprint")

# Domain models don't know about persistence
# They just focus on business logic
```

### Service Layer

Services orchestrate complex operations:

```python
# Service coordinates between domain and infrastructure
service.create_from_wizard(...)  # Complex creation workflow
service.activate("imprint_slug")  # Multi-step activation

# Tournament service manages tournament lifecycle
tournament_service.record_vote(...)  # Handles voting logic
tournament_service.create_imprint_from_winner(...)  # Converts winner to imprint
```

## File Locations

- **Domain Models**: `/src/codexes/domain/models/`
  - `imprint.py` - Imprint, BrandingSpecification, PublishingFocus
  - `publisher_persona.py` - PublisherPersona, EditorialDecision
  - `tournament.py` - Tournament, ImprintIdea, Matchup, TournamentRound

- **Repositories**: `/src/codexes/infrastructure/repositories/`
  - `imprint_repository.py` - ImprintRepository
  - `tournament_repository.py` - TournamentRepository

- **Services**: `/src/codexes/application/services/`
  - `imprint_creation_service.py` - ImprintCreationService
  - `tournament_service.py` - TournamentService

## Benefits

1. **Separation of Concerns** - Business logic separated from persistence
2. **Testability** - Easy to mock repositories for testing
3. **Maintainability** - Changes to persistence don't affect domain logic
4. **Type Safety** - Full type hints throughout
5. **Extensibility** - Easy to add new features following the pattern

## Migration Path

To migrate existing code:

1. Use services instead of direct file I/O
2. Replace dictionary-based configs with domain models
3. Use repositories instead of manual JSON handling
4. Let domain models handle validation and business rules
