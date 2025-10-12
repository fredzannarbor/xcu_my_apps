# Technology Stack

## Core Framework
- **Streamlit**: Primary web application framework (runs on assigned port)
- **Python 3.12+**: Required Python version
- **Pandas**: Data manipulation and CSV handling

## Key Dependencies
- **OpenAI API**: GPT-3 completions for persona generation
- **PyMuPDF (fitz)**: PDF generation and manipulation
- **Stripe**: Payment processing integration
- **SQLAlchemy**: Database operations
- **spaCy**: Natural language processing
- **NumPy**: Numerical computations
- **Pillow**: Image processing

## Data Processing
- **CSV files**: Primary data storage format in `people_data/` directory
- **JSON**: Configuration and preset storage in `app/presets/`
- **SQLite**: Database storage (see `fakeface/db.sqlite`)

## AI/ML Libraries
- **OpenAI**: Text generation and completions
- **spaCy**: NLP processing
- **NLTK**: Text analysis and summarization
- **Gensim**: Topic modeling and text processing

## Common Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the main Streamlit app
streamlit run trillionsofpeople.py

# Run specific pages
streamlit run pages/Scenarios.py
streamlit run pages/Data_Dictionary.py
```

### Environment Setup
- Requires OpenAI API key in environment variables
- Stripe keys needed for payment processing
- Python 3.12+ with pip package management

### Data Processing
- CSV files in `people_data/` for persona storage
- JSON presets in `app/presets/` for scenario configurations
- Backup files automatically generated in `people_data/backup.csv`