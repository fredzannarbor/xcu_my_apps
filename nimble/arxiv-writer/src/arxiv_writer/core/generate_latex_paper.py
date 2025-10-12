#!/usr/bin/env python3
"""
Generate LaTeX Paper CLI

Command-line interface for generating complete LaTeX papers from
markdown content sections with proper formatting and compilation.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from latex_formatter import (
    LaTeXFormattingConfig, 
    ArxivLaTeXGenerator,
    create_latex_config
)
from paper_assembler import (
    AssemblyConfig,
    PaperMetadata,
    ArxivPaperAssembler,
    create_assembly_config,
    create_paper_metadata
)
from citation_manager import (
    CitationManager,
    create_citation_manager
)

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create log directory relative to project root
    project_root = Path(__file__).parent.parent.parent.parent
    log_dir = project_root / 'output' / 'arxiv_paper' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'latex_generation.log'
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(str(log_file))
        ]
    )


def generate_latex_only(args) -> Dict[str, Any]:
    """Generate LaTeX files only (no PDF compilation)."""
    logger.info("Generating LaTeX files only...")
    
    # Create configuration
    config = create_latex_config(
        template_dir=args.template_dir,
        output_dir=args.output_dir
    )
    
    # Create generator
    generator = ArxivLaTeXGenerator(config)
    
    # Generate LaTeX files
    result = generator.generate_latex_paper(
        content_dir=args.content_dir,
        bibliography_file=args.bibliography_file
    )
    
    logger.info(f"Generated {len(result['latex_files'])} LaTeX files")
    return result


def generate_latex_and_pdf(args) -> Dict[str, Any]:
    """Generate LaTeX files and compile to PDF."""
    logger.info("Generating LaTeX files and compiling to PDF...")
    
    # Create assembly configuration
    config = create_assembly_config(
        content_dir=args.content_dir,
        output_dir=args.output_dir,
        template_dir=args.template_dir,
        bibliography_file=args.bibliography_file,
        include_supplemental=args.include_supplemental,
        generate_bookmarks=args.generate_bookmarks,
        optimize_pdf=args.optimize_pdf
    )
    
    # Create paper metadata
    metadata = create_paper_metadata(
        title=args.title,
        authors=args.authors.split(',') if args.authors else None,
        contact_email=args.contact_email,
        affiliation=args.affiliation
    )
    
    # Create assembler and generate paper
    assembler = ArxivPaperAssembler(config)
    result = assembler.assemble_and_compile_paper(metadata)
    
    return result


def generate_bibliography(args) -> Dict[str, Any]:
    """Generate bibliography file from citations."""
    logger.info("Generating bibliography...")
    
    # Create citation manager
    manager = create_citation_manager(args.input_bibliography)
    
    # Generate BibTeX file
    output_bib = Path(args.output_dir) / "references.bib"
    manager.generate_bibtex_file(str(output_bib))
    
    return {
        'bibliography_file': str(output_bib),
        'citations_count': len(manager.citations)
    }


def validate_references(args) -> Dict[str, Any]:
    """Validate references and citations in LaTeX files."""
    logger.info("Validating references and citations...")
    
    # Load LaTeX files
    latex_dir = Path(args.latex_dir)
    latex_files = {}
    
    for tex_file in latex_dir.glob("*.tex"):
        try:
            content = tex_file.read_text(encoding='utf-8')
            latex_files[tex_file.name] = content
        except Exception as e:
            logger.error(f"Error reading {tex_file}: {e}")
    
    # Create citation manager
    manager = create_citation_manager(args.bibliography_file)
    
    # Process references
    validation_result = manager.process_document_references(latex_files)
    
    # Print validation summary
    print("\n=== Reference Validation Summary ===")
    print(f"Total LaTeX files processed: {len(latex_files)}")
    print(f"Total cross-references: {validation_result['cross_references']['summary']['total_references']}")
    print(f"Valid citations: {len(validation_result['citations']['valid_citations'])}")
    print(f"Invalid citations: {len(validation_result['citations']['invalid_citations'])}")
    print(f"Unused citations: {len(validation_result['citations']['unused_citations'])}")
    
    if validation_result['citations']['invalid_citations']:
        print(f"\nInvalid citations: {validation_result['citations']['invalid_citations']}")
    
    if validation_result['cross_references']['validation']['invalid_references']:
        print(f"Invalid cross-references: {validation_result['cross_references']['validation']['invalid_references']}")
    
    return validation_result


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate LaTeX papers from markdown content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate LaTeX files only
  python generate_latex_paper.py latex --content-dir output/arxiv_paper/content
  
  # Generate LaTeX and compile to PDF
  python generate_latex_paper.py pdf --content-dir output/arxiv_paper/content
  
  # Generate bibliography
  python generate_latex_paper.py bibliography --output-dir output/arxiv_paper/bibliography
  
  # Validate references
  python generate_latex_paper.py validate --latex-dir output/arxiv_paper/latex
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add verbose flag to all subcommands
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # LaTeX generation command
    latex_parser = subparsers.add_parser('latex', help='Generate LaTeX files only', parents=[parent_parser])
    latex_parser.add_argument(
        '--content-dir',
        default='output/arxiv_paper/content',
        help='Directory containing markdown content files'
    )
    latex_parser.add_argument(
        '--output-dir',
        default='output/arxiv_paper/latex',
        help='Output directory for LaTeX files'
    )
    latex_parser.add_argument(
        '--template-dir',
        default='output/arxiv_paper/templates',
        help='Directory for LaTeX templates'
    )
    latex_parser.add_argument(
        '--bibliography-file',
        default='output/arxiv_paper/bibliography/references.bib',
        help='Bibliography file path'
    )
    
    # PDF generation command
    pdf_parser = subparsers.add_parser('pdf', help='Generate LaTeX and compile to PDF', parents=[parent_parser])
    pdf_parser.add_argument(
        '--content-dir',
        default='output/arxiv_paper/content',
        help='Directory containing markdown content files'
    )
    pdf_parser.add_argument(
        '--output-dir',
        default='output/arxiv_paper/latex',
        help='Output directory for LaTeX and PDF files'
    )
    pdf_parser.add_argument(
        '--template-dir',
        default='output/arxiv_paper/templates',
        help='Directory for LaTeX templates'
    )
    pdf_parser.add_argument(
        '--bibliography-file',
        default='output/arxiv_paper/bibliography/references.bib',
        help='Bibliography file path'
    )
    pdf_parser.add_argument(
        '--title',
        default='AI-Assisted Creation of a Publishing Imprint: The xynapse_traces Case Study',
        help='Paper title'
    )
    pdf_parser.add_argument(
        '--authors',
        default='AI Lab for Book-Lovers',
        help='Comma-separated list of authors'
    )
    pdf_parser.add_argument(
        '--contact-email',
        default='wfz@nimblebooks.com',
        help='Contact email address'
    )
    pdf_parser.add_argument(
        '--affiliation',
        default='Nimble Books LLC',
        help='Author affiliation'
    )
    pdf_parser.add_argument(
        '--include-supplemental',
        action='store_true',
        default=True,
        help='Include supplemental materials'
    )
    pdf_parser.add_argument(
        '--generate-bookmarks',
        action='store_true',
        default=True,
        help='Generate PDF bookmarks'
    )
    pdf_parser.add_argument(
        '--optimize-pdf',
        action='store_true',
        default=True,
        help='Optimize PDF for arXiv submission'
    )
    
    # Bibliography generation command
    bib_parser = subparsers.add_parser('bibliography', help='Generate bibliography file', parents=[parent_parser])
    bib_parser.add_argument(
        '--output-dir',
        default='output/arxiv_paper/bibliography',
        help='Output directory for bibliography file'
    )
    bib_parser.add_argument(
        '--input-bibliography',
        help='Input bibliography JSON file (optional)'
    )
    
    # Validation command
    validate_parser = subparsers.add_parser('validate', help='Validate references and citations', parents=[parent_parser])
    validate_parser.add_argument(
        '--latex-dir',
        default='output/arxiv_paper/latex',
        help='Directory containing LaTeX files'
    )
    validate_parser.add_argument(
        '--bibliography-file',
        default='output/arxiv_paper/bibliography/references.bib',
        help='Bibliography file path'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Set up logging
    setup_logging(args.verbose)
    
    try:
        # Ensure output directories exist
        Path('output/arxiv_paper/logs').mkdir(parents=True, exist_ok=True)
        
        if args.command == 'latex':
            result = generate_latex_only(args)
            print(f"✓ Generated LaTeX files in: {result['output_directory']}")
            print(f"  Main file: {result['main_file']}")
            print(f"  Sections: {', '.join(result['sections_processed'])}")
        
        elif args.command == 'pdf':
            result = generate_latex_and_pdf(args)
            if result['success']:
                print(f"✓ Successfully generated PDF: {result['final_pdf']}")
                print(f"  Word count: {result['assembly']['word_count']}")
                print(f"  Sections: {', '.join(result['assembly']['sections_included'])}")
            else:
                print(f"✗ Failed to generate PDF: {result.get('error', 'Unknown error')}")
                return 1
        
        elif args.command == 'bibliography':
            result = generate_bibliography(args)
            print(f"✓ Generated bibliography: {result['bibliography_file']}")
            print(f"  Citations: {result['citations_count']}")
        
        elif args.command == 'validate':
            result = validate_references(args)
            # Validation summary is printed by the function
            
            # Return error code if validation issues found
            if (result['citations']['invalid_citations'] or 
                result['cross_references']['validation']['invalid_references']):
                return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())