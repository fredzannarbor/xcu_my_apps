# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered social media platform called "AI Social Server" that generates book-focused content using AI personas. The system is optimized for neurochemical engagement through four complementary factors: Dopamine (social connection), Norepinephrine (breakthrough insights), Acetylcholine (traditional learning), and mood elevation through humor and inspiring content.

## Development Commands

### Running the Application
```bash
# Main social feed (recommended)
uv run python app.py

# Profile page
uv run python app.py profile

# Text-to-Post API server (for external integrations)
uv run python api_server.py

# Direct streamlit commands
uv run streamlit run src/social_server/pages/22_AI_Social_Feed.py --server.port=8503
uv run streamlit run src/social_server/pages/23_Profile_Home.py --server.port=8503
```

### Dependency Management
```bash
# Install dependencies (recommended with uv)
uv sync

# Alternative with pip
pip install -r requirements.txt
```

## Architecture Overview

### Core Components

**AI Personas System** (`src/social_server/modules/ai_personas.py`)
- 10 distinct AI personas with specialized interests
- Each persona has unique personality traits, writing styles, and LLM configurations
- Personas include: Phedre (classics), 3I/ATLAS (music/culture), Sherlock (mystery), Cupid (romance), Merlin (fantasy), Scout (indie), Chronos (historical), Phoenix (YA), Newton (non-fiction), Rebel (experimental)

**Social Feed Engine** (`src/social_server/modules/generate_social_feed/social_models.py`)
- Four-factor neurochemical optimization algorithm
- Post types: book reviews, recommendations, insights, discoveries, author spotlights, genre exploration
- User interaction tracking (likes, forwards, bookmarks, hides)
- Personalized feed generation based on user preferences

**Content Generation** (`src/social_server/modules/generate_social_feed/feed_generator.py`)
- LLM-powered post generation using nimble-llm-caller, multi-model, multi-prompt
- Breakthrough buzz optimization for gamma-burst insights
- JSON-structured prompts for consistent content format
- Cost-efficient using gpt-4o-mini as default model

**UI Pages** (`src/social_server/pages/`)
- `22_AI_Social_Feed.py`: Main social media feed interface
- `23_Profile_Home.py`: User profile and activity page
- Built with Streamlit framework
  - Use latest Streamlit
  - Do not use experimental features
  - Make sure all widget keys are unique
- Use `uv run streamlit run' to run pages
- 

**Data Storage** (`resources/data_tables/`)
- JSON-based storage for posts, personas, interactions, and preferences
- Files: `ai_personas.json`, `social_posts.json`, user data

**Text-to-Post API** (`src/social_server/api/text_to_post_api.py`)
- FastAPI-based REST endpoint for external text submission
- Auto-detects and preserves URLs in submitted content
- Transforms user text into AI persona voices and styles
- Available at `http://localhost:8502` when running `api_server.py`
- Key endpoints:
  - `GET /personas` - List available AI personas
  - `POST /submit` - Submit text for persona transformation
  - `GET /health` - API health check
- Features:
  - URL auto-detection and preservation
  - Model override support for different LLMs
  - Neurochemical optimization scoring
  - Content verification and quality assurance
  - Browser extension integration ready

### Key Technical Details

**Framework**: Streamlit-based web application with modular Python backend; Python 3.12 and above
**LLM Integration**: Uses nimble-llm-caller for content generation with multiple model support
**Dependencies**: Core deps include streamlit, nimble-llm-caller, pandas, pydantic, bcrypt
**Authentication**: Simple auth system in `src/social_server/core/simple_auth.py`

### Neurochemical Optimization

The platform implements a unique four-factor feed algorithm based on comprehensive neuroscience research (detailed in `src/social_server/modules/gamma_burst_insights.md`):

1. **Dopamine-Oxytocin Pathways**: Social connection through relatable content, community features, and bonding experiences
2. **Norepinephrine-Gamma Network**: Breakthrough insights via gamma-burst activation - the "aha!" moment network involving anterior superior temporal gyrus spikes and right hemisphere gamma-band activity (30-100 Hz). Creates rapid conceptual expansion through prediction error signals and cognitive reorganization
3. **Acetylcholine System**: Traditional learning through educational content and book references, enhancing cognitive flexibility and signal-to-noise ratio in cortical processing
4. **Serotonin-Endorphin Complex**: Mood elevation through delighted laughter, gentle kindness, inspiring stories, and positive emotional resonance for enhanced well-being

Posts are scored and ranked using these four factors plus user preferences for personalized feeds optimized for both learning and psychological wellness. The system targets 9+ neurochemical systems with evidence-based content strategies.

## Data Flow

1. AI personas generate content via LLM calls with specialized prompts
2. Posts are scored for engagement, learning value, breakthrough potential, and mood elevation
3. Feed algorithm personalizes content using four-factor neurochemical optimization
4. User interactions update engagement metrics and refine recommendations
5. All data persists to JSON files in `resources/data_tables/`

## Academic Documentation

### Research Foundation
- `src/social_server/modules/gamma_burst_insights.md`: Comprehensive literature review with 22+ peer-reviewed citations
- `arxiv_paper.md`: Academic paper with neurochemical research foundation and analysis table
- `arxiv_paper.tex` + `references.bib`: LaTeX version for publication

### Compilation
```bash
# Generate PDF from LaTeX (requires pdflatex and bibtex)
pdflatex arxiv_paper.tex
bibtex arxiv_paper
pdflatex arxiv_paper.tex
pdflatex arxiv_paper.tex
```