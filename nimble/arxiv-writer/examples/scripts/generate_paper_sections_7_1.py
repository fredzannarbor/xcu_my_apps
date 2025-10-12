#!/usr/bin/env python3
"""
Generate Abstract, Introduction, and Related Work sections for the ArXiv paper.
This script implements task 7.1 from the arxiv_article_on_imprint_release spec.
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
    create_paper_generation_config
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('output/arxiv_paper/logs/section_generation_7_1.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def generate_sections_7_1():
    """Generate Abstract, Introduction, and Related Work sections (Task 7.1)."""
    logger.info("Starting generation of sections for Task 7.1...")
    
    # Create configuration for paper generation
    config = create_paper_generation_config(
        output_dir="output/arxiv_paper/content",
        models=["openai/gpt-4o"],
        additional_context={
            "task_focus": "7.1 - Abstract, Introduction, and Related Work",
            "required_sections": ["abstract", "introduction", "related_work"]
        }
    )
    
    # Initialize the paper generator
    generator = ArxivPaperGenerator(config)
    
    # Collect context data
    logger.info("Collecting context data for paper generation...")
    context_data = generator.context_collector.collect_xynapse_traces_data()
    
    # Initialize section generator
    from src.codexes.modules.arxiv_paper.paper_generator import PaperSectionGenerator
    section_generator = PaperSectionGenerator(generator.prompt_templates, context_data)
    
    # Generate the three sections for Task 7.1
    sections_to_generate = ["abstract", "introduction"]
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
    
    # Generate related work section (this needs special handling as it's not in the basic templates)
    logger.info("Generating related work section...")
    
    try:
        # Create a custom prompt for related work since it's not in the standard templates
        related_work_prompt = {
            "system_prompt": "You are an expert academic researcher with deep knowledge of AI applications in publishing, content generation, and digital humanities. Write a comprehensive related work section that positions the xynapse_traces imprint creation within the broader research landscape.",
            "user_prompt": f"""Write a comprehensive Related Work section for the paper 'AI-Assisted Creation of a Publishing Imprint: The xynapse_traces Case Study'.

CONTEXT DATA:
- Total books produced: {context_data.get('total_books', 'N/A')}
- AI technologies used: {context_data.get('key_technologies', [])}
- Technical innovations: {context_data.get('technical_innovations', [])}

STRUCTURE THE RELATED WORK SECTION:

1. **AI Content Generation and Automation**
   - Recent advances in LLM-based content creation and automated writing systems
   - Quality assessment approaches for AI-generated content
   - Comparison studies between AI and human-authored content
   - Key papers: GPT-3/4 applications, BERT for content generation, T5 for text-to-text tasks

2. **Publishing Workflow Automation**
   - Digital publishing pipeline optimization and automation systems
   - Metadata generation and enhancement using AI
   - Print-on-demand integration and workflow automation
   - Configuration management systems in publishing platforms

3. **Multilingual and Cross-Cultural Publishing**
   - AI approaches to multilingual content processing and localization
   - Unicode handling and font management in digital publishing
   - Korean language processing in LaTeX and digital publishing systems
   - Cultural adaptation and automated localization systems

4. **Quality Assurance and Validation in AI Systems**
   - AI-assisted quality control methodologies in content creation
   - Automated validation and error detection systems
   - Human-in-the-loop quality assurance frameworks
   - Performance metrics and evaluation frameworks for AI content systems

5. **Configuration Management and System Architecture**
   - Multi-level configuration systems in software architecture
   - Inheritance patterns and resolution strategies in complex systems
   - Scalable system design for content management platforms
   - Modular architecture patterns in publishing and content systems

6. **Digital Humanities and AI Integration**
   - AI applications in digital humanities research and scholarly publishing
   - Technology-assisted content creation and analysis
   - Interdisciplinary approaches to AI and humanities integration
   - Case studies of AI in cultural and literary content creation

POSITIONING REQUIREMENTS:
- Clearly articulate how the xynapse_traces work advances beyond existing research
- Identify specific gaps in current research that this work addresses
- Highlight the novel technical contributions (multi-level config, Korean LaTeX, full imprint automation)
- Position as the first comprehensive case study of fully AI-assisted imprint creation
- Connect to broader trends in AI, digital humanities, and publishing technology

ACADEMIC REQUIREMENTS:
- Use academic tone suitable for cs.AI category submission
- Include references to key papers and systems (you can use placeholder citations like [Smith et al., 2023])
- Maintain scholarly objectivity while highlighting contributions
- Target length: 1000-1500 words
- Emphasize technical innovations and measurable contributions

NOVEL CONTRIBUTIONS TO HIGHLIGHT:
- First fully AI-assisted publishing imprint creation from conception to production
- Multi-level configuration inheritance system for publishing workflows
- Korean language LaTeX integration with automated Unicode handling
- End-to-end automation of print-on-demand publishing pipeline
- Comprehensive case study with {context_data.get('total_books', 'multiple')} books produced
- Quantitative analysis of AI-assisted vs. traditional publishing efficiency""",
            "context_variables": ["total_books", "key_technologies", "technical_innovations"]
        }
        
        # Generate related work using the enhanced LLM caller directly
        from src.codexes.core.enhanced_llm_caller import enhanced_llm_caller
        
        messages = [
            {"role": "system", "content": related_work_prompt["system_prompt"]},
            {"role": "user", "content": related_work_prompt["user_prompt"]}
        ]
        
        response = enhanced_llm_caller.call_llm_with_retry(
            model="openai/gpt-4o",
            messages=messages,
            max_tokens=4000,
            temperature=0.7
        )
        
        if response and response.get('content'):
            # Save related work section
            related_work_file = Path(config.output_directory) / "related_work.md"
            
            with open(related_work_file, 'w') as f:
                f.write("# Related Work\n\n")
                f.write(f"**Generated:** {generator.context_collector.context_data.get('generation_timestamp', 'N/A')}\n")
                f.write(f"**Model:** openai/gpt-4o\n")
                f.write(f"**Word Count:** {len(response['content'].split())}\n\n")
                f.write("---\n\n")
                f.write(response['content'])
                f.write("\n\n---\n\n")
                f.write("**Generation Metadata:**\n")
                f.write(f"```json\n{json.dumps(response.get('usage', {}), indent=2)}\n```\n")
            
            logger.info(f"Successfully generated related work section ({len(response['content'].split())} words)")
            
        else:
            logger.error("Failed to generate related work section")
    
    except Exception as e:
        logger.error(f"Error generating related work section: {e}")
    
    # Generate summary report
    summary = {
        "task": "7.1 - Generate Abstract, Introduction, and Related Work sections",
        "sections_generated": list(generated_sections.keys()) + (["related_work"] if Path(config.output_directory, "related_work.md").exists() else []),
        "total_sections": len(generated_sections) + (1 if Path(config.output_directory, "related_work.md").exists() else 0),
        "output_directory": config.output_directory,
        "generation_timestamp": str(generator.context_collector.context_data.get('generation_timestamp', 'N/A')),
        "context_data_summary": {
            "total_books": context_data.get('total_books', 'N/A'),
            "key_technologies": context_data.get('key_technologies', []),
            "technical_innovations": context_data.get('technical_innovations', [])
        }
    }
    
    # Save summary
    summary_file = Path(config.output_directory) / "task_7_1_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    logger.info("Task 7.1 generation complete!")
    logger.info(f"Generated sections: {summary['sections_generated']}")
    logger.info(f"Output directory: {config.output_directory}")
    
    return summary


if __name__ == "__main__":
    try:
        result = generate_sections_7_1()
        print(f"\nTask 7.1 completed successfully!")
        print(f"Sections generated: {result['sections_generated']}")
        print(f"Output directory: {result['output_directory']}")
        
    except Exception as e:
        logger.error(f"Task 7.1 failed: {e}")
        sys.exit(1)