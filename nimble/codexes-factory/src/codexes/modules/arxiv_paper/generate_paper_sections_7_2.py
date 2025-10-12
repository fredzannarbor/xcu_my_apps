#!/usr/bin/env python3
"""
Generate Methodology and Implementation sections for the ArXiv paper.
This script implements task 7.2 from the arxiv_article_on_imprint_release spec.
"""

import logging
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.codexes.modules.arxiv_paper.paper_generator import (
    ArxivPaperGenerator, 
    PaperGenerationConfig,
    create_paper_generation_config,
    PaperSectionGenerator
)
from src.codexes.core.enhanced_llm_caller import enhanced_llm_caller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('output/arxiv_paper/logs/section_generation_7_2.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def generate_sections_7_2():
    """Generate Methodology and Implementation sections (Task 7.2)."""
    logger.info("Starting generation of sections for Task 7.2...")
    
    # Create configuration for paper generation
    config = create_paper_generation_config(
        output_dir="output/arxiv_paper/content",
        models=["openai/gpt-4o"],
        additional_context={
            "task_focus": "7.2 - Methodology and Implementation",
            "required_sections": ["methodology", "implementation"]
        }
    )
    
    # Initialize the paper generator
    generator = ArxivPaperGenerator(config)
    
    # Collect context data
    logger.info("Collecting context data for paper generation...")
    context_data = generator.context_collector.collect_xynapse_traces_data()
    
    # Initialize section generator
    section_generator = PaperSectionGenerator(generator.prompt_templates, context_data)
    
    # Generate the two sections for Task 7.2
    sections_to_generate = ["methodology", "implementation"]
    generated_sections = {}
    
    for section_name in sections_to_generate:
        logger.info(f"Generating section: {section_name}")
        
        try:
            section = section_generator.generate_section(section_name, model="openai/gpt-4o")
            
            if section:
                generated_sections[section_name] = section
                
                # Save section to individual file
                section_file = Path(config.output_directory) / f"{section_name}.md"
                section_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(section_file, 'w') as f:
                    f.write(f"# {section_name.title()}\n\n")
                    f.write(f"**Generated:** {section.generated_at}\n")
                    f.write(f"**Model:** {section.model_used}\n")
                    f.write(f"**Word Count:** {section.word_count}\n")
                    f.write(f"**Validation Status:** {section.validation_status}\n\n")
                    f.write("---\n\n")
                    f.write(section.content)
                    f.write("\n\n---\n\n")
                    f.write("**Generation Metadata:**\n")
                    f.write(f"```json\n{json.dumps(section.metadata, indent=2, default=str)}\n```\n")
                
                logger.info(f"Successfully generated and saved {section_name} ({section.word_count} words)")
                
            else:
                logger.error(f"Failed to generate section: {section_name}")
                
        except Exception as e:
            logger.error(f"Error generating section {section_name}: {e}")
    
    # Generate summary report
    summary = {
        "task": "7.2 - Generate Methodology and Implementation sections",
        "sections_generated": list(generated_sections.keys()),
        "total_sections": len(generated_sections),
        "output_directory": config.output_directory,
        "generation_timestamp": str(generator.context_collector.context_data.get('generation_timestamp', 'N/A')),
        "context_data_summary": {
            "total_books": context_data.get('total_books', 'N/A'),
            "key_technologies": context_data.get('key_technologies', []),
            "technical_innovations": context_data.get('technical_innovations', [])
        }
    }
    
    # Save summary
    summary_file = Path(config.output_directory) / "task_7_2_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    logger.info("Task 7.2 generation complete!")
    logger.info(f"Generated sections: {summary['sections_generated']}")
    logger.info(f"Output directory: {config.output_directory}")
    
    return summary


if __name__ == "__main__":
    try:
        result = generate_sections_7_2()
        print(f"\nTask 7.2 completed successfully!")
        print(f"Sections generated: {result['sections_generated']}")
        print(f"Output directory: {result['output_directory']}")
        
    except Exception as e:
        logger.error(f"Task 7.2 failed: {e}")
        sys.exit(1)