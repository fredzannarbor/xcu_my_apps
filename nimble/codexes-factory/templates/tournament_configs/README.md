# Tournament Configuration Templates

This directory contains tournament templates for the Codexes Factory publishing system. These templates enable publishers and imprints to run competitive evaluation tournaments for various publishing decisions.

## Available Templates

### 1. Idea Generation Tournament (`idea_generation.json`)

**Purpose**: Generate and evaluate new book or imprint concepts through competitive tournament.

**Use Cases**:
- Creating new imprints (e.g., finding the best concept from 16-32 ideas)
- Developing book series concepts
- Brainstorming product lines
- Community-driven ideation

**Key Features**:
- Supports user-contributed, AI-generated, and hybrid ideas
- Configurable tournament sizes (8, 16, 32, 64 participants)
- Public voting + AI evaluation
- Optional Thaumette review for B5K imprints
- Winner can auto-create imprint or book project

**Based On**: Proven model from Nimitz Volume 9 tournament (16 ideas → 1 winner)

---

### 2. Manuscript Evaluation Tournament (`manuscript_evaluation.json`)

**Purpose**: Select best manuscripts from submission queue through rigorous competitive evaluation.

**Use Cases**:
- Quarterly manuscript selection from slush pile
- Evaluating multiple competing manuscripts for limited publication slots
- Author discovery programs
- Backlist revival selection

**Key Features**:
- Expert panel evaluation (editors, subject experts, production)
- Anti-slop detection (rejecting AI-generated content)
- Thaumette final review
- Literary quality prioritized over metrics
- Detailed comparative analysis
- Author feedback for all participants

**Anti-Slop Measures**: Multiple filters to detect and reject low-quality AI-generated content. Thaumette's core belief: "Books are not content. Readers are not users."

---

### 3. Cover Design Tournament (`cover_design.json`)

**Purpose**: Select winning cover design through multi-stakeholder evaluation.

**Use Cases**:
- Choosing final cover from multiple design concepts
- Testing market appeal before publication
- Engaging author + public + experts in selection
- A/B testing cover variations

**Key Features**:
- Multi-stakeholder voting (marketing, design expert, author, public)
- AI design generation support (Midjourney, DALL-E, Stable Diffusion)
- Thumbnail readability testing
- Genre appropriateness analysis
- Technical quality validation
- Public voting with demographic collection

**Stakeholder Weights**:
- Marketing Team: 30%
- Design Expert: 25%
- Author: 20%
- Public Voting: 15%
- AI Analysis: 10%

---

## Tournament System Integration

### Publisher-Level Tournaments

Big Five Killer LLC (Thaumette) can run tournaments across all 575 imprints:
- "Find 12 best imprint concepts from 32 ideas"
- "Evaluate manuscripts from 20 different imprints"
- "Cross-imprint cover design competition"

### Imprint-Level Tournaments

Individual imprints (e.g., Warships & Navies, Xynapse Traces) can run focused tournaments:
- "Select next book for our Spring catalog"
- "Choose between 8 cover designs"
- "Evaluate 16 manuscript submissions"

### Connection to Imprint Personas

Each imprint has an AI persona connected to Thaumette. Tournament configurations can leverage these personas:
- **Jellicoe** (Warships & Navies): Values primary sources, technical accuracy
- **Seon** (Xynapse Traces): Contemplative, rigorous, bridges tradition and science
- **Zero** (Nimble Ultra): Analytical, politically neutral, transparency-focused

Tournament evaluation criteria adapt to persona values.

---

## How to Use

### 1. Load Tournament Template

```python
import json
with open('templates/tournament_configs/idea_generation.json') as f:
    tournament_config = json.load(f)
```

### 2. Customize for Your Entity

```python
tournament_config['tournament_config']['name_template'] = "Warships & Navies Q1 2026 Ideas"
tournament_config['entity_name'] = "Warships & Navies"
tournament_config['entity_type'] = "imprint"
tournament_config['parent_publisher'] = "Big Five Killer LLC"
```

### 3. Run Tournament

Use the Streamlit UI at `src/codexes/pages/21_Imprint_Ideas_Tournament.py` or programmatically:

```python
from codexes.modules.ideation.tournament.tournament_engine import TournamentEngine

engine = TournamentEngine(config=tournament_config)
engine.setup()
engine.collect_ideas(user_ideas=user_submissions, ai_count=16)
engine.run_tournament()
winner = engine.get_winner()
```

---

## Template Structure

All templates follow this structure:

```json
{
  "_template_info": { },
  "tournament_config": { },
  "evaluation_criteria": { },
  "ai_evaluation_prompts": { },
  "workflow": { },
  "output_templates": { },
  "integration_points": { }
}
```

### Key Sections

**`_template_info`**: Metadata about the template

**`tournament_config`**: Basic setup (size, duration, voting rules)

**`evaluation_criteria`**: What you're evaluating and how (weights, scoring methods)

**`ai_evaluation_prompts`**: Prompts for LLM-assisted evaluation
- Structured to work with `nimble-llm-caller`
- Return JSON for programmatic processing
- Include comparative evaluation prompts

**`workflow`**: Phased approach with tasks and timelines

**`output_templates`**: Reports, notifications, and deliverables

**`integration_points`**: How winners connect to other systems (imprint creation, book pipeline, etc.)

---

## AI Assistance

### Models Used

All templates default to `gemini/gemini-2.5-flash` for:
- Speed and cost-effectiveness
- Good JSON adherence
- Strong analytical capabilities

Can be overridden per prompt or per tournament.

### Prompt Engineering

Prompts are designed to:
1. Return structured JSON
2. Provide detailed rationale (not just scores)
3. Identify strengths AND weaknesses
4. Suggest improvements
5. Consider market positioning

### Anti-Slop Philosophy

Thaumette's core belief permeates all tournament templates:

> "Books are not content. Readers are not users."

AI evaluation always includes:
- Authenticity checks
- Voice analysis (human vs. AI-generated)
- Literary merit over engagement metrics
- Cultural value assessment

---

## Thaumette Review Integration

For Big Five Killer imprints, tournaments can request Thaumette's final review:

```json
{
  "require_thaumette_review": true
}
```

Thaumette's review focuses on:
- L-Space positioning (does this fill a gap Big Five ignore?)
- Literary merit vs. slop
- Strategic fit with B5K's 575-imprint vision
- Long-term catalog value
- Anti-conglomerate positioning

---

## Examples from Production

### Nimitz Volume 9 Tournament

Generated 16 book concepts for "Not A Miracle Readers" imprint:
- Started with uploaded CSV of partial ideas
- AI enhanced incomplete concepts
- 16-idea single elimination tournament
- Winner: "The Manatee's Mystery"
- Result: Published as part of series

Configuration used: `idea_generation.json` (predecessor to current template)

---

## Customization Guide

### Adding New Criteria

```json
{
  "evaluation_criteria": {
    "default_criteria": [
      "Your New Criterion"
    ],
    "weights": {
      "Your New Criterion": 0.10
    }
  }
}
```

### Custom AI Prompts

```json
{
  "ai_evaluation_prompts": {
    "your_custom_analysis": {
      "system_prompt": "You are an expert...",
      "user_prompt_template": "Analyze {variable}...",
      "variables": ["variable"]
    }
  }
}
```

### Publisher-Specific Configuration

Big Five Killer tournaments automatically:
- Include Thaumette review
- Apply anti-slop measures
- Consider L-Space positioning
- Evaluate gap-filling strategy

Individual imprint tournaments inherit parent publisher's:
- Quality standards
- Anti-slop philosophy
- Brand values
- But maintain editorial autonomy

---

## Tournament Best Practices

1. **Right-Size Your Tournament**
   - 8 ideas: Quick decision
   - 16 ideas: Standard model
   - 32 ideas: Comprehensive evaluation
   - 64 ideas: Major strategic decision

2. **Balance AI and Human Input**
   - AI excels at: Pattern recognition, comparative analysis, first-pass evaluation
   - Humans excel at: Nuance, cultural context, authentic voice detection

3. **Involve Stakeholders Early**
   - Authors for manuscript/cover tournaments
   - Marketing for cover designs
   - Community for idea generation

4. **Document Rationale**
   - Every advancement should have written justification
   - Losing concepts should get constructive feedback
   - Winner report should explain "why"

5. **Use Tournaments Strategically**
   - Not for every decision
   - Best for: High-stakes choices, multiple viable options, stakeholder buy-in needed
   - Avoid: Urgent decisions, clear frontrunner, token participation

---

## Future Enhancements

Planned template additions:
- `series_development.json` - Multi-book series planning
- `anthology_selection.json` - Selecting stories for anthologies
- `translation_prioritization.json` - Which books to translate
- `backlist_revival.json` - Which out-of-print titles to revive
- `author_discovery.json` - Finding new talent

Integration improvements:
- Direct Streamlit UI integration per template
- Automated email notifications
- Real-time voting dashboards
- Tournament bracket visualizations
- Historical tournament analytics

---

## Questions & Support

- **Technical Issues**: See `src/codexes/pages/21_Imprint_Ideas_Tournament.py`
- **Tournament Strategy**: Contact publisher or imprint lead
- **Thaumette Review**: For B5K imprints, automatically triggered
- **Custom Templates**: Extend existing templates or create new ones

---

**Version**: 1.0
**Last Updated**: 2025-10-29
**Maintained By**: Big Five Killer LLC / Codexes Factory Team
