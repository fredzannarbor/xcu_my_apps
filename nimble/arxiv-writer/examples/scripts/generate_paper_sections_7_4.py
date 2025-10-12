#!/usr/bin/env python3
"""
Generate technical documentation and supplemental materials for the ArXiv paper.
This script implements task 7.4 from the arxiv_article_on_imprint_release spec.
"""

import logging
import json
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.codexes.core.enhanced_llm_caller import enhanced_llm_caller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('output/arxiv_paper/logs/section_generation_7_4.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def generate_book_catalog_table():
    """Generate comprehensive table of all books from xynapse_traces catalog."""
    logger.info("Generating comprehensive book catalog table...")
    
    try:
        # Read the xynapse_traces book catalog
        catalog_path = Path("imprints/xynapse_traces/books.csv")
        if not catalog_path.exists():
            logger.warning(f"Book catalog not found at {catalog_path}")
            return None
        
        df = pd.read_csv(catalog_path)
        total_books = len(df)
        
        # Generate table content
        table_content = f"""# Complete Book Catalog Table

**Total Books:** {total_books}
**Imprint:** xynapse_traces
**Generated:** {datetime.now()}

## Statistical Summary

- **Total Books:** {total_books}
- **Average Page Count:** {df['page_count'].mean():.1f} (if available)
- **Price Range:** ${df['price'].min():.2f} - ${df['price'].max():.2f} (if available)

## Complete Book Listing

| # | Title | Author | ISBN | Publication Date | Page Count | Price |
|---|-------|--------|------|------------------|------------|-------|
"""
        
        # Add each book to the table
        for idx, row in df.iterrows():
            table_content += f"| {idx+1} | {row.get('title', 'N/A')} | {row.get('author', 'N/A')} | {row.get('isbn13', 'N/A')} | {row.get('publication_date', 'N/A')} | {row.get('page_count', 'N/A')} | ${row.get('price', 0):.2f} |\n"
        
        # Save to file
        output_file = Path("output/arxiv_paper/content/book_catalog_table.md")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            f.write(table_content)
        
        logger.info(f"Generated book catalog table with {total_books} books")
        return str(output_file)
        
    except Exception as e:
        logger.error(f"Error generating book catalog table: {e}")
        return None


def generate_technical_features_box():
    """Generate technical features box highlighting key algorithmic features."""
    logger.info("Generating technical features box...")
    
    features_prompt = """Generate a comprehensive technical features box highlighting the key algorithmic features of the xynapse_traces imprint.

Create a well-formatted technical specification box that includes:

1. **Core Algorithmic Features:**
   - Multi-level configuration inheritance system
   - AI-assisted metadata generation using multiple LLMs
   - Korean language LaTeX processing
   - Automated LSI CSV generation
   - Template-based document production

2. **AI Integration Features:**
   - LiteLLM abstraction for multi-model support
   - Prompt engineering and response validation
   - Quality scoring and threshold checking
   - Retry mechanisms with exponential backoff

3. **Configuration System Features:**
   - Five-tier hierarchy (Global → Publisher → Imprint → Tranche → Book)
   - Runtime context management
   - Field inheritance and override patterns
   - JSON-based validation schemas

4. **Production Pipeline Features:**
   - End-to-end automation from concept to publication
   - Quality assurance checkpoints
   - Error handling and recovery mechanisms
   - Performance optimization for large catalogs

5. **Technical Specifications:**
   - Python 3.12+ with type hints
   - Pandas for data processing
   - LaTeX/LuaLaTeX for document generation
   - Unicode handling for multilingual support

Format this as a professional technical specification box suitable for academic publication."""
    
    try:
        messages = [
            {"role": "system", "content": "You are a technical documentation specialist creating specification boxes for academic papers."},
            {"role": "user", "content": features_prompt}
        ]
        
        response = enhanced_llm_caller.call_llm_with_retry(
            model="openai/gpt-4o",
            messages=messages,
            max_tokens=2000,
            temperature=0.3
        )
        
        if response and response.get('content'):
            output_file = Path("output/arxiv_paper/content/technical_features_box.md")
            
            with open(output_file, 'w') as f:
                f.write("# Technical Features Box\n\n")
                f.write(f"**Generated:** {datetime.now()}\n\n")
                f.write("---\n\n")
                f.write(response['content'])
            
            logger.info("Generated technical features box")
            return str(output_file)
            
    except Exception as e:
        logger.error(f"Error generating technical features box: {e}")
        return None


def generate_configuration_variables_table():
    """Generate detailed variable tables showing configuration settings by module."""
    logger.info("Generating configuration variables table...")
    
    variables_prompt = """Generate a comprehensive table showing all configuration variables set at each stage by module and line number, grouped by interior, cover, and metadata.

Create detailed tables that document:

1. **Interior Configuration Variables:**
   - Font settings and typography
   - Page layout and margins
   - Chapter and section formatting
   - Korean language processing settings
   - LaTeX template variables

2. **Cover Configuration Variables:**
   - Cover design templates
   - Image processing settings
   - Typography and layout
   - Color schemes and branding
   - Print specifications

3. **Metadata Configuration Variables:**
   - ISBN and publication data
   - Author and title information
   - Category and subject classifications
   - Pricing and distribution settings
   - LSI CSV field mappings

For each variable, include:
- Variable name
- Module location
- Default value
- Override hierarchy level
- Data type and validation rules
- Description and usage

Format as professional technical documentation tables suitable for academic appendix."""
    
    try:
        messages = [
            {"role": "system", "content": "You are a technical documentation expert creating detailed configuration tables for academic papers."},
            {"role": "user", "content": variables_prompt}
        ]
        
        response = enhanced_llm_caller.call_llm_with_retry(
            model="openai/gpt-4o",
            messages=messages,
            max_tokens=3000,
            temperature=0.3
        )
        
        if response and response.get('content'):
            output_file = Path("output/arxiv_paper/content/configuration_variables_table.md")
            
            with open(output_file, 'w') as f:
                f.write("# Configuration Variables Table\n\n")
                f.write(f"**Generated:** {datetime.now()}\n\n")
                f.write("---\n\n")
                f.write(response['content'])
            
            logger.info("Generated configuration variables table")
            return str(output_file)
            
    except Exception as e:
        logger.error(f"Error generating configuration variables table: {e}")
        return None


def generate_contact_information():
    """Generate contact information and resource links."""
    logger.info("Generating contact information and resource links...")
    
    contact_content = f"""# Contact Information and Resources

**Generated:** {datetime.now()}

## Author Contact Information

**Corresponding Author:** Fred Zimmerman  
**Email:** wfz@nimblebooks.com  
**Affiliation:** AI Lab for Book-Lovers, Nimble Books LLC

## Resource Links

### Primary Resources
- **GitHub Repository:** https://github.com/fredzannarbor/codexes-factory
- **Xynapse Traces Imprint Homepage:** https://NimbleBooks.com/xynapse_traces
- **Publisher Website:** https://NimbleBooks.com

### Technical Documentation
- **API Documentation:** Available in repository docs/ directory
- **Configuration Guide:** See configs/README.md in repository
- **Installation Instructions:** See repository README.md

### Data and Code Availability
- **Source Code:** Available under open source license at GitHub repository
- **Configuration Files:** Sample configurations available in configs/examples/
- **Documentation:** Comprehensive guides available in docs/ directory

### Citation Information
```bibtex
@article{{xynapse_traces_2025,
  title={{AI-Assisted Creation of a Publishing Imprint: The xynapse_traces Case Study}},
  author={{Zimmerman, Fred}},
  journal={{arXiv preprint}},
  year={{2025}},
  organization={{AI Lab for Book-Lovers}}
}}
```

### Acknowledgments
This work was supported by the AI Lab for Book-Lovers and Nimble Books LLC. We thank the open source community for the foundational tools and libraries that made this project possible.

### Licensing
- **Code:** MIT License (see repository for details)
- **Documentation:** Creative Commons Attribution 4.0 International License
- **Data:** Available under appropriate data sharing agreements

For questions about implementation, collaboration opportunities, or access to additional data, please contact the corresponding author at wfz@nimblebooks.com.
"""
    
    try:
        output_file = Path("output/arxiv_paper/content/contact_information.md")
        
        with open(output_file, 'w') as f:
            f.write(contact_content)
        
        logger.info("Generated contact information and resource links")
        return str(output_file)
        
    except Exception as e:
        logger.error(f"Error generating contact information: {e}")
        return None


def generate_supplemental_materials():
    """Generate all supplemental materials for Task 7.4."""
    logger.info("Starting generation of supplemental materials for Task 7.4...")
    
    generated_files = []
    
    # Generate book catalog table
    catalog_file = generate_book_catalog_table()
    if catalog_file:
        generated_files.append(catalog_file)
    
    # Generate technical features box
    features_file = generate_technical_features_box()
    if features_file:
        generated_files.append(features_file)
    
    # Generate configuration variables table
    variables_file = generate_configuration_variables_table()
    if variables_file:
        generated_files.append(variables_file)
    
    # Generate contact information
    contact_file = generate_contact_information()
    if contact_file:
        generated_files.append(contact_file)
    
    # Generate summary report
    summary = {
        "task": "7.4 - Complete technical documentation and supplemental materials",
        "materials_generated": [Path(f).name for f in generated_files],
        "total_materials": len(generated_files),
        "output_directory": "output/arxiv_paper/content",
        "generation_timestamp": str(datetime.now()),
        "files_created": generated_files
    }
    
    # Save summary
    summary_file = Path("output/arxiv_paper/content/task_7_4_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    logger.info("Task 7.4 generation complete!")
    logger.info(f"Generated materials: {summary['materials_generated']}")
    
    return summary


if __name__ == "__main__":
    try:
        result = generate_supplemental_materials()
        print(f"\nTask 7.4 completed successfully!")
        print(f"Materials generated: {result['materials_generated']}")
        print(f"Total files: {result['total_materials']}")
        print(f"Output directory: {result['output_directory']}")
        
    except Exception as e:
        logger.error(f"Task 7.4 failed: {e}")
        sys.exit(1)