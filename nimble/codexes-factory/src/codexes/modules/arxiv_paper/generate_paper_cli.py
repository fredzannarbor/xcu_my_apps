#!/usr/bin/env python3
"""
ArXiv Paper Generation CLI

Command-line interface for generating academic papers documenting
AI-assisted imprint creation. Provides easy access to the paper
generation system with various configuration options.
"""

import argparse
import logging
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.codexes.modules.arxiv_paper.paper_generator import (
        ArxivPaperGenerator, 
        PaperGenerationConfig,
        create_paper_generation_config,
        generate_arxiv_paper
    )
    from src.codexes.modules.arxiv_paper.paper_validator import (
        validate_paper_file,
        PaperQualityAssessor
    )
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Project root: {project_root}")
    sys.exit(1)

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('arxiv_paper_generation.log')
        ]
    )


def generate_paper_command(args) -> None:
    """Handle the generate paper command."""
    logger.info("Starting ArXiv paper generation...")
    
    # Create configuration
    config = create_paper_generation_config(
        output_dir=args.output_dir,
        models=args.models,
        additional_context={}
    )
    
    # Add any additional context from file
    if args.context_file:
        context_path = Path(args.context_file)
        if context_path.exists():
            with open(context_path, 'r') as f:
                additional_context = json.load(f)
                config.context_data.update(additional_context)
            logger.info(f"Loaded additional context from {args.context_file}")
        else:
            logger.warning(f"Context file not found: {args.context_file}")
    
    # Override configuration settings from command line
    if args.max_retries:
        config.max_retries = args.max_retries
    
    config.validation_enabled = not args.skip_validation
    
    try:
        # Generate the paper
        result = generate_arxiv_paper(config)
        
        # Print summary
        summary = result['generation_summary']
        print(f"\n✅ Paper generation completed!")
        print(f"📊 Sections generated: {summary['successful_sections']}/{summary['total_sections']}")
        print(f"📝 Total word count: {summary['total_word_count']:,} words")
        print(f"📁 Output directory: {args.output_dir}")
        print(f"📄 Complete paper: {result['complete_paper_file']}")
        
        # Show section status
        print(f"\n📋 Section Status:")
        for section_name, section_info in summary['sections'].items():
            status_icon = "✅" if section_info['status'] == 'success' else "❌"
            word_count = section_info.get('word_count', 0)
            print(f"  {status_icon} {section_name.title()}: {word_count:,} words")
        
        # Run validation if requested
        if not args.skip_validation and summary['successful_sections'] > 0:
            print(f"\n🔍 Running quality validation...")
            try:
                report = validate_paper_file(result['complete_paper_file'])
                print(f"📊 Overall Quality Score: {report.overall_score:.2f}/1.0")
                print(f"🎯 ArXiv Ready: {'Yes' if report.arxiv_readiness else 'No'}")
                
                if report.recommendations:
                    print(f"\n💡 Top Recommendations:")
                    for i, rec in enumerate(report.recommendations[:3], 1):
                        print(f"  {i}. {rec}")
                        
            except Exception as e:
                logger.error(f"Validation failed: {e}")
                print(f"⚠️  Validation failed: {e}")
        
        # Save generation metadata
        metadata_file = Path(args.output_dir) / "generation_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump({
                "command_args": vars(args),
                "generation_result": result['generation_summary'],
                "config_used": {
                    "models": config.models,
                    "validation_enabled": config.validation_enabled,
                    "max_retries": config.max_retries
                }
            }, f, indent=2, default=str)
        
        print(f"📋 Generation metadata saved to: {metadata_file}")
        
    except Exception as e:
        logger.error(f"Paper generation failed: {e}")
        print(f"❌ Paper generation failed: {e}")
        sys.exit(1)


def validate_paper_command(args) -> None:
    """Handle the validate paper command."""
    logger.info(f"Validating paper: {args.paper_file}")
    
    try:
        report = validate_paper_file(args.paper_file, args.output_file)
        
        print(f"\n📊 Paper Quality Assessment")
        print(f"=" * 50)
        print(f"📄 Paper: {args.paper_file}")
        print(f"📊 Overall Score: {report.overall_score:.2f}/1.0")
        print(f"🎯 ArXiv Ready: {'Yes' if report.arxiv_readiness else 'No'}")
        
        # Show section scores
        print(f"\n📋 Section Scores:")
        for section, score in report.section_scores.items():
            score_icon = "🟢" if score >= 0.8 else "🟡" if score >= 0.6 else "🔴"
            print(f"  {score_icon} {section.title()}: {score:.2f}")
        
        # Show recommendations
        if report.recommendations:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"  {i}. {rec}")
        
        # Show detailed issues if verbose
        if args.verbose:
            print(f"\n🔍 Detailed Issues:")
            for section, result in report.validation_results.items():
                if result.issues:
                    print(f"  📝 {section.title()}:")
                    for issue in result.issues:
                        print(f"    ❌ {issue}")
                if result.suggestions:
                    print(f"  💭 Suggestions:")
                    for suggestion in result.suggestions:
                        print(f"    💡 {suggestion}")
        
        if args.output_file:
            print(f"📋 Detailed report saved to: {args.output_file}")
            
    except Exception as e:
        logger.error(f"Paper validation failed: {e}")
        print(f"❌ Paper validation failed: {e}")
        sys.exit(1)


def list_sections_command(args) -> None:
    """Handle the list sections command."""
    prompt_file = Path(args.prompt_file)
    
    if not prompt_file.exists():
        print(f"❌ Prompt file not found: {args.prompt_file}")
        sys.exit(1)
    
    try:
        with open(prompt_file, 'r') as f:
            prompts = json.load(f)
        
        sections = prompts.get("paper_sections", {})
        
        print(f"\n📋 Available Paper Sections")
        print(f"=" * 40)
        print(f"📄 Prompt file: {args.prompt_file}")
        print(f"📊 Total sections: {len(sections)}")
        
        for i, (section_name, section_config) in enumerate(sections.items(), 1):
            context_vars = section_config.get("context_variables", [])
            validation = "✅" if "validation_criteria" in section_config else "⚪"
            
            print(f"\n{i}. 📝 {section_name.title()}")
            print(f"   🔧 Context variables: {len(context_vars)}")
            print(f"   ✅ Validation: {validation}")
            
            if args.verbose and context_vars:
                print(f"   📋 Variables: {', '.join(context_vars[:5])}")
                if len(context_vars) > 5:
                    print(f"   ... and {len(context_vars) - 5} more")
                    
    except Exception as e:
        logger.error(f"Error reading prompt file: {e}")
        print(f"❌ Error reading prompt file: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ArXiv Paper Generation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a complete paper with default settings
  python generate_paper_cli.py generate
  
  # Generate with specific models and output directory
  python generate_paper_cli.py generate --models anthropic/claude-3-5-sonnet-20241022 --output-dir ./my_paper
  
  # Validate an existing paper
  python generate_paper_cli.py validate paper.md --output-file validation_report.json
  
  # List available sections
  python generate_paper_cli.py list-sections --verbose
        """
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate paper command
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate a complete ArXiv paper"
    )
    generate_parser.add_argument(
        "--output-dir", "-o",
        default="output/arxiv_paper",
        help="Output directory for generated paper (default: output/arxiv_paper)"
    )
    generate_parser.add_argument(
        "--models", "-m",
        nargs="+",
        default=["anthropic/claude-3-5-sonnet-20241022"],
        help="LLM models to use for generation (default: claude-3-5-sonnet)"
    )
    generate_parser.add_argument(
        "--context-file", "-c",
        help="JSON file with additional context data"
    )
    generate_parser.add_argument(
        "--max-retries",
        type=int,
        help="Maximum retries for failed sections"
    )
    generate_parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip automatic validation after generation"
    )
    generate_parser.set_defaults(func=generate_paper_command)
    
    # Validate paper command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate an existing paper"
    )
    validate_parser.add_argument(
        "paper_file",
        help="Path to the paper file to validate"
    )
    validate_parser.add_argument(
        "--output-file", "-o",
        help="Save detailed validation report to file"
    )
    validate_parser.set_defaults(func=validate_paper_command)
    
    # List sections command
    list_parser = subparsers.add_parser(
        "list-sections",
        help="List available paper sections"
    )
    list_parser.add_argument(
        "--prompt-file", "-p",
        default="prompts/arxiv_paper_prompts.json",
        help="Prompt template file (default: prompts/arxiv_paper_prompts.json)"
    )
    list_parser.set_defaults(func=list_sections_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Execute command
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()