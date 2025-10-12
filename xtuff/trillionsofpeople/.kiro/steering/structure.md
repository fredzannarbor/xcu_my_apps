# Project Structure

## Root Level
- `trillionsofpeople.py`: Main Streamlit application entry point
- `main.py`: Basic Python entry point (minimal implementation)
- `pyproject.toml`: Python project configuration
- `requirements.txt`: Python dependencies (extensive list)

## Core Application (`app/`)
- `app/ManageUserAPIKeys.py`: API key management utilities
- `app/data/`: Data storage directory
  - `people_data/`: CSV files for persona data
  - `longform_test/`: Test data for longform content generation
- `app/presets/`: JSON configuration files for different scenarios
  - Global Trends 2040 scenarios (RD, AWA, CC, SS, TM)
  - NFT-related presets
  - Story generation templates
- `app/utilities/`: Extensive utility library (100+ modules)
  - Document processing (docx, pdf)
  - AI completions and text processing
  - Data transformation utilities
  - Scribus layout tools

## Pages (`pages/`)
Streamlit multi-page application structure:
- `Scenarios.py`: Scenario-based persona generation
- `Data_Dictionary.py`: Data schema documentation
- `Methods.py`: Methodology documentation
- `Annotated_Bibliography.py`: Research references

## Classes (`classes/`)
- `SyntheticPeople/`: Core persona generation logic
  - `PeopleUtilities.py`: Main persona creation functions
  - `ScenarioUtilities.py`: Scenario-specific utilities
  - `species.py`: Species-related data structures

## Data Directories
- `people_data/`: Primary data storage (CSV format)
- `.snapshots/`: Configuration snapshots
- `fakeface/`: Face generation subproject with Flask app

## Configuration
- `.streamlit/config.toml`: Streamlit server configuration (port 8502)
- `.kiro/`: Kiro IDE configuration and steering rules
- Individual JSON files: Historical figure data (Einstein, Lincoln, etc.)

## Naming Conventions
- Snake_case for Python modules and functions
- PascalCase for class names
- Descriptive filenames indicating functionality
- JSON files named after historical figures for persona data