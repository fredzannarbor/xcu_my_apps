#!/usr/bin/env python3
"""
Generate Imprint Artifacts CLI Tool

Processes ExpandedImprint JSON files to create comprehensive production artifacts
using the ImprintArtifactGenerator.

Usage:
    python tools/generate_imprint_artifacts.py -i expanded_imprint.json -o output_directory
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.codexes.modules.imprint_builder.imprint_expander import ExpandedImprint
    from src.codexes.modules.imprint_builder.artifact_generator import ImprintArtifactGenerator
    from src.codexes.core.llm_integration import CodexesLLMIntegration
except ImportError as e:
    logging.error(f"Failed to import required modules: {e}")
    logging.error(f"Project root: {project_root}")
    logging.error(f"Python path: {sys.path}")
    sys.exit(1)


class LLMCallerWrapper:
    """Wrapper to adapt CodexesLLMIntegration to the expected interface."""
    
    def __init__(self):
        try:
            self.llm_integration = CodexesLLMIntegration()
        except Exception as e:
            logging.warning(f"Failed to initialize LLM integration: {e}, using mock")
            self.llm_integration = None
    
    def call_model_with_prompt(self, **kwargs) -> Dict[str, Any]:
        """Call LLM with prompt and return response."""
        prompt = kwargs.get('prompt', 'No prompt provided')
        temperature = kwargs.get('temperature', 0.7)
        
        if self.llm_integration:
            try:
                response = self.llm_integration.call_llm(prompt, temperature=temperature)
                return {"content": response}
            except Exception as e:
                logging.warning(f"LLM call failed: {e}, using fallback")
        
        # Fallback response
        return {"content": "Generated content placeholder - LLM integration not available"}


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive imprint production artifacts from ExpandedImprint JSON"
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        required=True,
        help="Path to the ExpandedImprint JSON file"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output directory for generated artifacts"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the input JSON without generating artifacts"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output directory"
    )
    
    return parser.parse_args()


def validate_input_file(input_path: Path) -> Dict[str, Any]:
    """Validate the input JSON file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if not input_path.suffix.lower() == '.json':
        raise ValueError(f"Input file must be a JSON file: {input_path}")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Basic structure validation
        required_sections = ['concept', 'branding', 'design_specifications', 
                           'publishing_strategy', 'operational_framework', 
                           'marketing_approach', 'financial_projections']
        
        missing_sections = [section for section in required_sections if section not in data]
        if missing_sections:
            raise ValueError(f"Missing required sections: {missing_sections}")
        
        return data
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")


def prepare_output_directory(output_path: Path, force: bool = False):
    """Prepare the output directory."""
    if output_path.exists():
        if not force:
            response = input(f"Output directory {output_path} already exists. Overwrite? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                print("Operation cancelled.")
                sys.exit(0)
        
        # Remove existing directory
        import shutil
        shutil.rmtree(output_path)
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)


class SafeAttributeWrapper:
    """Wrapper that provides safe attribute access with fallbacks."""
    
    def __init__(self, data):
        self._data = data if data else {}
    
    def __getattr__(self, name):
        if hasattr(self._data, 'get') and callable(getattr(self._data, 'get')):
            return self._data.get(name, '')
        elif hasattr(self._data, name):
            return getattr(self._data, name, '')
        elif isinstance(self._data, dict):
            return self._data.get(name, '')
        else:
            return ''
    
    def get(self, key, default=''):
        return self.__getattr__(key) or default


class ExpandedImprintCompatibilityWrapper:
    """Wrapper to provide compatibility between ExpandedImprint and ImprintArtifactGenerator expectations."""
    
    def __init__(self, expanded_imprint: ExpandedImprint):
        self.original = expanded_imprint
        
        # Map the attributes to what ImprintArtifactGenerator expects
        self.branding = SafeAttributeWrapper(expanded_imprint.branding)
        self.design = SafeAttributeWrapper(expanded_imprint.design_specifications)
        self.publishing = SafeAttributeWrapper(expanded_imprint.publishing_strategy)
        self.production = SafeAttributeWrapper(expanded_imprint.operational_framework)
        self.distribution = SafeAttributeWrapper(getattr(expanded_imprint, 'distribution', expanded_imprint.operational_framework))
        self.marketing = SafeAttributeWrapper(expanded_imprint.marketing_approach)
        self.financial = SafeAttributeWrapper(expanded_imprint.financial_projections)
        self.concept = SafeAttributeWrapper(expanded_imprint.concept)
        
        # Add some common attribute mappings that might be expected
        self._add_attribute_mappings()
    
    def _add_attribute_mappings(self):
        """Add common attribute mappings and fallbacks."""
        # Ensure design has expected attributes
        if not hasattr(self.design, 'trim_sizes') or not self.design.trim_sizes:
            self.design.trim_sizes = ['6x9']
        
        # Ensure publishing has expected attributes
        if not hasattr(self.publishing, 'target_audience'):
            self.publishing.target_audience = getattr(self.publishing, 'target_readership', 'General readers')
        
        # Add automation settings if missing
        if not hasattr(self.production, 'automation_settings'):
            self.production.automation_settings = {'level': 'medium'}
        
        # Add quality standards if missing
        if not hasattr(self.production, 'quality_standards'):
            self.production.quality_standards = {'level': 'high'}
        
        # Add distribution channels if missing
        if not hasattr(self.distribution, 'primary_channels'):
            self.distribution.primary_channels = ['online', 'bookstores']
        
        if not hasattr(self.distribution, 'secondary_channels'):
            self.distribution.secondary_channels = ['libraries']
        
        if not hasattr(self.distribution, 'international_distribution'):
            self.distribution.international_distribution = False
        
        if not hasattr(self.distribution, 'digital_first'):
            self.distribution.digital_first = False


def generate_artifacts(imprint: ExpandedImprint, output_path: Path) -> Dict[str, Any]:
    """Generate all artifacts using ImprintArtifactGenerator."""
    logger = logging.getLogger(__name__)
    
    # Initialize LLM caller
    llm_caller = LLMCallerWrapper()
    
    # Create compatibility wrapper
    wrapped_imprint = ExpandedImprintCompatibilityWrapper(imprint)
    
    # Initialize artifact generator
    generator = ImprintArtifactGenerator(llm_caller)
    
    # Generate all artifacts
    logger.info(f"Generating artifacts for imprint: {imprint.branding.imprint_name}")
    results = generator.generate_all_artifacts(wrapped_imprint, str(output_path))
    
    return results


def print_results_summary(results: Dict[str, Any]):
    """Print a summary of the generation results."""
    print(f"\n{'='*60}")
    print(f"ARTIFACT GENERATION SUMMARY")
    print(f"{'='*60}")
    
    print(f"Imprint: {results.get('imprint_name', 'Unknown')}")
    print(f"Generated at: {results.get('generated_at', 'Unknown')}")
    
    artifacts = results.get('artifacts', {})
    if artifacts:
        print(f"\nGenerated Artifacts:")
        for artifact_type, artifact_info in artifacts.items():
            status = artifact_info.get('status', 'unknown')
            print(f"  • {artifact_type.title()}: {status}")
            
            if status == 'success':
                if 'files_generated' in artifact_info:
                    print(f"    Files: {', '.join(artifact_info['files_generated'])}")
                elif 'output_file' in artifact_info:
                    print(f"    File: {Path(artifact_info['output_file']).name}")
                elif 'output_directory' in artifact_info:
                    print(f"    Directory: {Path(artifact_info['output_directory']).name}")
            elif status == 'error':
                print(f"    Error: {artifact_info.get('error', 'Unknown error')}")
    
    # Validation results
    validation = results.get('validation', {})
    if validation:
        print(f"\nValidation Results:")
        overall_valid = validation.get('overall_valid', False)
        print(f"  Overall Valid: {'✅ Yes' if overall_valid else '❌ No'}")
        
        if not overall_valid:
            issues = validation.get('issues', [])
            if issues:
                print(f"  Issues Found:")
                for issue in issues[:5]:  # Show first 5 issues
                    print(f"    • {issue}")
                if len(issues) > 5:
                    print(f"    ... and {len(issues) - 5} more issues")
    
    # Errors and warnings
    errors = results.get('errors', [])
    warnings = results.get('warnings', [])
    
    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        for error in errors:
            print(f"  • {error}")
    
    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)}):")
        for warning in warnings:
            print(f"  • {warning}")
    
    if not errors and not warnings:
        print(f"\n✅ All artifacts generated successfully!")
    
    print(f"\n{'='*60}")


def main():
    """Main CLI function."""
    args = parse_arguments()
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Validate arguments
    if not args.validate_only and not args.output:
        print("Error: Output directory (-o/--output) is required unless using --validate-only")
        sys.exit(1)
    
    try:
        # Validate input file
        logger.info(f"Validating input file: {args.input}")
        imprint_data = validate_input_file(args.input)
        logger.info("✅ Input file validation passed")
        
        # Create ExpandedImprint object
        logger.info("Loading ExpandedImprint object...")
        expanded_imprint = ExpandedImprint.from_dict(imprint_data)
        logger.info(f"✅ Loaded imprint: {expanded_imprint.branding.imprint_name}")
        
        if args.validate_only:
            print("✅ Input validation completed successfully")
            print(f"Imprint: {expanded_imprint.branding.imprint_name}")
            print(f"Sections: {len(imprint_data)} main sections found")
            return
        
        # Prepare output directory
        logger.info(f"Preparing output directory: {args.output}")
        prepare_output_directory(args.output, args.force)
        
        # Generate artifacts
        logger.info("Starting artifact generation...")
        results = generate_artifacts(expanded_imprint, args.output)
        
        # Save results summary
        results_file = args.output / "generation_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Results saved to: {results_file}")
        
        # Print summary
        print_results_summary(results)
        
        # Exit with appropriate code
        if results.get('errors'):
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == "__main__":
    main()