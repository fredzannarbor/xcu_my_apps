#!/usr/bin/env python3
"""
One-shot imprint generator for Codexes Factory.
Creates complete imprint configuration in a single LLM call using frontier models.
"""

import argparse
import json
import os
import sys
import csv
import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(project_root))

# Import CodexTypes with fallback pattern
try:
    from codexes.modules.core.codex_types import get_codex_type_by_name, list_all_codex_types, CodexType
except ModuleNotFoundError:
    from src.codexes.modules.core.codex_types import get_codex_type_by_name, list_all_codex_types, CodexType

# Import Font Manager with fallback pattern
try:
    from codexes.modules.core.font_manager import GoogleFontsManager
except ModuleNotFoundError:
    from src.codexes.modules.core.font_manager import GoogleFontsManager

try:
    from codexes.core.llm_caller import call_model_with_prompt
except ModuleNotFoundError:
    from src.codexes.core.llm_caller import call_model_with_prompt

# Set up logging
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def load_prompts_config() -> Dict[str, Any]:
    """Load prompts configuration from JSON file."""
    prompts_path = project_root / "prompts" / "imprint_generation_prompts.json"

    # Alternative path if standard doesn't work
    if not prompts_path.exists():
        prompts_path = Path.cwd() / "prompts" / "imprint_generation_prompts.json"

    if not prompts_path.exists():
        raise FileNotFoundError(f"Prompts config not found: {prompts_path}")

    with open(prompts_path, 'r') as f:
        return json.load(f)


def load_template_and_exemplar() -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Load the imprint template and xynapse_traces exemplar."""
    template_path = project_root / "configs" / "imprints" / "imprint_template.json"
    exemplar_path = project_root / "configs" / "imprints" / "xynapse_traces.json"

    # Alternative path if standard doesn't work (for when script is run from subdirectory)
    if not template_path.exists():
        # Try relative to current working directory
        template_path = Path.cwd() / "configs" / "imprints" / "imprint_template.json"
        exemplar_path = Path.cwd() / "configs" / "imprints" / "xynapse_traces.json"

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    if not exemplar_path.exists():
        raise FileNotFoundError(f"Exemplar not found: {exemplar_path}")

    with open(template_path, 'r') as f:
        template = json.load(f)

    with open(exemplar_path, 'r') as f:
        exemplar = json.load(f)

    return template, exemplar


def create_oneshot_prompt(
    template: Dict[str, Any],
    exemplar: Dict[str, Any],
    imprint_description: str,
    partial_config: Optional[Dict[str, Any]] = None
) -> str:
    """Create the one-shot prompt for imprint generation using external prompts config."""

    # Load prompts from external JSON config
    try:
        prompts_config = load_prompts_config()
        generation_prompt_config = prompts_config["prompts"]["imprint_generation"]

        # Get the user prompt template from JSON
        user_prompt_template = generation_prompt_config["user_prompt_template"]

        # Prepare template variables
        template_json = json.dumps(template, indent=2)
        exemplar_json = json.dumps(exemplar, indent=2)
        partial_config_section = ""

        if partial_config:
            partial_config_section = f"## PARTIAL CONFIGURATION PROVIDED:\n{json.dumps(partial_config, indent=2)}\n\n"

        # Replace placeholders using string replacement to avoid issues with nested braces
        prompt = user_prompt_template.replace("{template_json}", template_json)
        prompt = prompt.replace("{exemplar_json}", exemplar_json)
        prompt = prompt.replace("{imprint_description}", imprint_description)
        prompt = prompt.replace("{partial_config_section}", partial_config_section)

        return prompt

    except Exception as e:
        logger.error(f"Failed to load prompts config, using fallback: {e}")
        # Fallback to inline prompt if loading fails
        prompt = f"""You are an expert publishing consultant tasked with creating a complete imprint configuration for a new publishing brand. Your job is to generate a comprehensive, internally consistent JSON configuration that defines all aspects of this imprint's operations.

## INPUT SPECIFICATION
You will be provided with:
1. A template structure showing all possible fields
2. An exemplar of a completed, successful imprint configuration (Xynapse Traces)
3. A description of the new imprint to create
4. Any partial configuration data already provided

## OUTPUT REQUIREMENTS
Generate a complete JSON configuration that:
- Follows the exact structure of the template
- Uses the exemplar as a guide for consistency and completeness
- Is internally coherent (all fields support the same brand identity)
- Includes realistic, professional values for all fields
- Maintains publishing industry standards and best practices

## TEMPLATE STRUCTURE
```json
{json.dumps(template, indent=2)}
```

## EXEMPLAR CONFIGURATION (Xynapse Traces - Technology/Science Focus)
```json
{json.dumps(exemplar, indent=2)}
```

## NEW IMPRINT TO CREATE
{imprint_description}

{'## PARTIAL CONFIGURATION PROVIDED:' if partial_config else ''}
{json.dumps(partial_config, indent=2) if partial_config else ''}

## OUTPUT FORMAT
Return ONLY the complete JSON configuration, properly formatted and valid. Do not include any explanatory text before or after the JSON."""

        return prompt


def generate_imprint_config(
    prompt: str,
    model: str = "gemini/gemini-2.5-pro",
    temperature: float = 0.3
) -> Dict[str, Any]:
    """Generate the imprint configuration using LLM."""

    logger.info(f"Generating imprint configuration with model: {model}")

    try:
        prompt_config = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": 65536
        }

        response = call_model_with_prompt(
            model_name=model,
            prompt_config=prompt_config,
            response_format_type="text"
        )

        # Parse JSON response
        logger.debug(f"Response keys: {list(response.keys())}")

        # Handle both string and dict responses
        if 'parsed_content' in response:
            content = response['parsed_content']
        else:
            content = response.get('raw_content', '')

        # Convert to string if it's a dict (happens when response_format_type is "json_object")
        if isinstance(content, dict):
            config_json = json.dumps(content, indent=2)
        elif isinstance(content, str):
            config_json = content.strip()
        else:
            config_json = str(content).strip()

        logger.debug(f"Raw config JSON length: {len(config_json)}")
        logger.debug(f"Content type: {type(content)}")

        # Remove any markdown code blocks if present
        if config_json.startswith('```json'):
            config_json = config_json[7:-3]
        elif config_json.startswith('```'):
            config_json = config_json[3:-3]

        config = json.loads(config_json)

        # Add generation metadata
        config["_generation_info"] = {
            "generated_by": "oneshot_imprint_generator",
            "generated_at": datetime.now().isoformat(),
            "model_used": model,
            "temperature": temperature,
            "version": "1.0"
        }

        return config

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.debug(f"Raw response: {config_json}")
        raise
    except Exception as e:
        logger.error(f"Failed to generate imprint configuration: {e}")
        raise


def extract_prompts_config_for_pipeline(oneshot_config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract prompts configuration from oneshot imprint config for book pipeline compatibility."""
    from datetime import datetime

    # Standard prompt keys that the book pipeline expects
    standard_prompt_keys = [
        "gemini_get_basic_info",
        "bibliographic_key_phrases",
        "storefront_get_en_metadata",
        "imprint_quotes_prompt",
        "mnemonics_prompt",
        "bibliography_prompt",
        "back_cover_text"
    ]

    # Keys that should be re-prompted (processed multiple times)
    standard_reprompt_keys = [
        "mnemonics_prompt"
    ]

    # Extract imprint basic info
    imprint_name = oneshot_config.get("imprint", "Unknown Imprint")
    imprint_intro = oneshot_config.get("branding", {}).get("mission_statement",
                                      f"{imprint_name} publishes high-quality books.")

    # Extract specialization from publisher persona and branding
    publisher_persona = oneshot_config.get("publisher_persona", {})
    branding = oneshot_config.get("branding", {})
    publishing_focus = oneshot_config.get("publishing_focus", {})

    specialization = branding.get("unique_selling_proposition",
                     publisher_persona.get("preferred_topics",
                     ", ".join(publishing_focus.get("primary_genres", ["Literature"]))))

    # Create the prompts.json structure expected by book pipeline
    prompts_config = {
        "imprint_name": imprint_name.lower().replace(" ", "_"),
        "imprint_intro": imprint_intro,
        "prompt_keys": standard_prompt_keys.copy(),
        "reprompt_keys": standard_reprompt_keys.copy(),
        "_metadata": {
            "imprint": imprint_name,
            "generated_at": datetime.now().isoformat(),
            "specialization": specialization,
            "extracted_from_oneshot": True
        }
    }

    # Extract content generation configuration if available
    content_generation = oneshot_config.get("content_generation", {})
    if content_generation:
        # Add content generation sections to prompts config
        for section_name, section_config in content_generation.items():
            prompts_config[section_name] = section_config

    # Extract editorial review configuration if available
    editorial_review = oneshot_config.get("editorial_review", {})
    if editorial_review:
        for section_name, section_config in editorial_review.items():
            prompts_config[section_name] = section_config

    # Extract production support configuration if available
    production_support = oneshot_config.get("production_support", {})
    if production_support:
        for section_name, section_config in production_support.items():
            prompts_config[section_name] = section_config

    return prompts_config


def save_imprint_config(config: Dict[str, Any], output_path: Path) -> None:
    """Save the imprint configuration to file and download Google Fonts."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    logger.info(f"Imprint configuration saved to: {output_path}")

    # Create the prompts.json file for book pipeline compatibility
    try:
        prompts_config = extract_prompts_config_for_pipeline(config)

        # Determine imprint directory path
        imprint_name = prompts_config.get("imprint_name", config.get("imprint", "unknown")).lower().replace(" ", "_")
        imprint_dir = output_path.parent.parent / "imprints" / imprint_name
        imprint_dir.mkdir(parents=True, exist_ok=True)

        prompts_path = imprint_dir / "prompts.json"
        with open(prompts_path, 'w', encoding='utf-8') as f:
            json.dump(prompts_config, f, indent=2, ensure_ascii=False)

        logger.info(f"Prompts configuration saved to: {prompts_path}")

    except Exception as e:
        logger.warning(f"Failed to create prompts.json: {e}")

    # Download Google Fonts if any are specified
    try:
        font_manager = GoogleFontsManager()
        font_results = font_manager.download_fonts_from_config(config)

        if font_results:
            success_count = sum(1 for success in font_results.values() if success)
            total_count = len(font_results)
            logger.info(f"Google Fonts download: {success_count}/{total_count} successful")

            # Log individual font results
            for font_name, success in font_results.items():
                status = "✅" if success else "❌"
                logger.info(f"  {status} {font_name}")
        else:
            logger.info("No Google Fonts to download")

    except Exception as e:
        logger.warning(f"Failed to download Google Fonts: {e}")


def load_partial_config(partial_path: Optional[str]) -> Optional[Dict[str, Any]]:
    """Load partial configuration if provided."""
    if not partial_path:
        return None

    partial_path = Path(partial_path)
    if not partial_path.exists():
        raise FileNotFoundError(f"Partial config file not found: {partial_path}")

    with open(partial_path, 'r') as f:
        return json.load(f)


def detect_required_codextypes_llm(charter: str, focus: str, competitive_advantage: str, examples: str, model: str = "gemini/gemini-2.5-flash") -> Dict[str, Any]:
    """Use LLM to analyze imprint requirements and suggest CodexTypes for innovative interior design.

    Returns:
        Dict containing:
        - requires_specialized_design: bool
        - recommended_codextypes: List[str] (type keys)
        - recommended_codex_type_instances: List[CodexType] (actual class instances)
        - design_parameters: Dict[str, str]
        - reasoning: str
    """

    # Load prompts from JSON config
    try:
        prompts_config = load_prompts_config()
        codextype_prompt_config = prompts_config["prompts"]["codextype_analysis"]
    except Exception as e:
        logger.error(f"Failed to load prompts config: {e}")
        # Fallback to inline prompt with CodexType instance
        standard_type = get_codex_type_by_name('standard')
        fallback_instances = [standard_type] if standard_type else []

        return {
            "requires_specialized_design": False,
            "recommended_codextypes": ["standard"],
            "recommended_codex_type_instances": fallback_instances,
            "design_parameters": {
                "primary_considerations": "Standard book layout",
                "interior_layout_notes": "Traditional chapter-based format",
                "typesetting_requirements": "Standard typography",
                "functional_elements": "None required",
                "reader_interaction_model": "Linear reading"
            },
            "reasoning": "Fallback due to prompts config error"
        }

    # Combine all text fields for analysis
    combined_description = f"""
Charter: {charter}
Focus: {focus}
Competitive Advantage: {competitive_advantage}
Examples: {examples}
    """.strip()

    # Build prompt from JSON config
    codextype_analysis_prompt = f"{codextype_prompt_config['system_prompt']}\n\n{codextype_prompt_config['user_prompt_template'].format(combined_description=combined_description)}"

    try:
        prompt_config = {
            "messages": [{"role": "user", "content": codextype_analysis_prompt}],
            "temperature": codextype_prompt_config.get("temperature", 0.4),
            "max_tokens": codextype_prompt_config.get("max_tokens", 65536)
        }

        logger.info("Analyzing CodexType requirements with LLM...")
        response = call_model_with_prompt(
            model_name=model,
            prompt_config=prompt_config,
            response_format_type="text"
        )

        # Parse JSON response
        if 'parsed_content' in response:
            content = response['parsed_content']
        else:
            content = response.get('raw_content', '')

        # Convert to string if it's a dict
        if isinstance(content, dict):
            content_json = json.dumps(content, indent=2)
        else:
            content_json = str(content).strip()

        # Remove any markdown code blocks if present
        if content_json.startswith('```json'):
            content_json = content_json[7:-3]
        elif content_json.startswith('```'):
            content_json = content_json[3:-3]

        analysis_result = json.loads(content_json)

        # Convert string type names to CodexType instances
        recommended_types = analysis_result.get('recommended_codextypes', ['standard'])
        codex_type_instances = []

        for type_name in recommended_types:
            codex_type = get_codex_type_by_name(type_name)
            if codex_type:
                codex_type_instances.append(codex_type)
            else:
                logger.warning(f"Unknown CodexType: {type_name}, using StandardBook as fallback")
                fallback_type = get_codex_type_by_name('standard')
                if fallback_type:
                    codex_type_instances.append(fallback_type)

        # Add CodexType instances to the result
        analysis_result['recommended_codex_type_instances'] = codex_type_instances

        logger.info(f"LLM CodexType Analysis completed:")
        logger.info(f"  Specialized design needed: {analysis_result.get('requires_specialized_design', False)}")
        logger.info(f"  Recommended types: {recommended_types}")
        logger.info(f"  CodexType instances: {[ct.name for ct in codex_type_instances]}")

        return analysis_result

    except Exception as e:
        logger.error(f"Failed to analyze CodexTypes with LLM: {e}")
        # Fallback to standard with CodexType instance
        standard_type = get_codex_type_by_name('standard')
        fallback_instances = [standard_type] if standard_type else []

        return {
            "requires_specialized_design": False,
            "recommended_codextypes": ["standard"],
            "recommended_codex_type_instances": fallback_instances,
            "design_parameters": {
                "primary_considerations": "Standard book layout",
                "interior_layout_notes": "Traditional chapter-based format",
                "typesetting_requirements": "Standard typography",
                "functional_elements": "None required",
                "reader_interaction_model": "Linear reading"
            },
            "reasoning": "Fallback due to analysis error"
        }


def load_csv_imprints(csv_path: str) -> List[Dict[str, str]]:
    """Load imprint data from CSV file."""
    imprints = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('name'):  # Skip empty rows
                imprints.append(row)

    logger.info(f"Loaded {len(imprints)} imprints from CSV: {csv_path}")
    return imprints


def load_json_directory(directory_path: str) -> List[Dict[str, Any]]:
    """Load partial imprint configs from JSON files in directory."""
    directory = Path(directory_path)
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    imprints = []
    json_files = list(directory.glob("*.json"))

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['_source_file'] = str(json_file)
                imprints.append(data)
        except Exception as e:
            logger.warning(f"Failed to load {json_file}: {e}")

    logger.info(f"Loaded {len(imprints)} imprints from directory: {directory_path}")
    return imprints


def csv_row_to_description(row: Dict[str, str]) -> str:
    """Convert CSV row to description string for oneshot processing."""
    parts = []

    if row.get('name'):
        parts.append(f"Imprint Name: {row['name']}")
    if row.get('charter'):
        parts.append(f"Charter: {row['charter']}")
    if row.get('focus'):
        parts.append(f"Focus: {row['focus']}")
    if row.get('tagline'):
        parts.append(f"Tagline: {row['tagline']}")
    if row.get('target_audience'):
        parts.append(f"Target Audience: {row['target_audience']}")
    if row.get('competitive_advantage'):
        parts.append(f"Competitive Advantage: {row['competitive_advantage']}")
    if row.get('examples'):
        parts.append(f"Examples: {row['examples']}")

    return ". ".join(parts)


def process_batch_imprints(input_source: str, output_dir: str, model: str, temperature: float) -> Dict[str, Any]:
    """Process multiple imprints from CSV or JSON directory."""

    input_path = Path(input_source)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load template and exemplar
    template, exemplar = load_template_and_exemplar()

    # Determine input type and load data
    if input_path.is_file() and input_path.suffix.lower() == '.csv':
        logger.info(f"Processing CSV file: {input_source}")
        csv_rows = load_csv_imprints(input_source)
        imprints_data = [{'csv_row': row, 'type': 'csv'} for row in csv_rows]
    elif input_path.is_dir():
        logger.info(f"Processing JSON directory: {input_source}")
        json_configs = load_json_directory(input_source)
        imprints_data = [{'json_config': config, 'type': 'json'} for config in json_configs]
    else:
        raise ValueError(f"Input must be a CSV file or directory containing JSON files: {input_source}")

    results = {
        'total_processed': 0,
        'successful': 0,
        'failed': 0,
        'results': [],
        'output_directory': str(output_path)
    }

    for i, imprint_data in enumerate(imprints_data):
        try:
            logger.info(f"Processing {i+1}/{len(imprints_data)}...")

            # Extract description and metadata
            if imprint_data['type'] == 'csv':
                row = imprint_data['csv_row']
                description = csv_row_to_description(row)
                imprint_name = row.get('name', f'imprint_{i+1}')

                # Analyze CodexTypes with LLM for CSV data
                codextype_analysis = detect_required_codextypes_llm(
                    row.get('charter', ''),
                    row.get('focus', ''),
                    row.get('competitive_advantage', ''),
                    row.get('examples', ''),
                    model
                )

            else:  # JSON
                config = imprint_data['json_config']
                # Convert JSON config back to description format
                description = json.dumps(config, indent=2)
                imprint_name = config.get('title', config.get('name', f'imprint_{i+1}'))

                # Analyze CodexTypes with LLM for JSON data
                content = config.get('content', '')
                codextype_analysis = detect_required_codextypes_llm(
                    content, content, content, content, model
                )

            # Create serializable version of codextype_analysis for JSON
            serializable_analysis = {
                key: value for key, value in codextype_analysis.items()
                if key != 'recommended_codex_type_instances'
            }

            # Create enhanced description with codetype information
            enhanced_description = f"{description}\n\nCodexType Analysis: {json.dumps(serializable_analysis, indent=2)}"

            # Generate configuration
            prompt = create_oneshot_prompt(template, exemplar, enhanced_description, None)
            config = generate_imprint_config(prompt, model, temperature)

            # Add LLM-analyzed codextypes to config
            if 'codextypes' in config:
                config['codextypes']['enabled_types'] = codextype_analysis.get('recommended_codextypes', ['standard'])
                config['codextypes']['llm_analysis'] = serializable_analysis

            # Save configuration
            safe_name = imprint_name.lower().replace(" ", "_").replace("&", "and").replace("/", "_")
            output_file = output_path / f"{safe_name}.json"
            save_imprint_config(config, output_file)

            results['successful'] += 1
            results['results'].append({
                'name': imprint_name,
                'output_file': str(output_file),
                'codextypes': codextype_analysis.get('recommended_codextypes', ['standard']),
                'design_parameters': codextype_analysis.get('design_parameters', {}),
                'success': True
            })

            logger.info(f"✅ Generated: {imprint_name} → {output_file}")

        except Exception as e:
            logger.error(f"❌ Failed to process imprint {i+1}: {e}")
            results['failed'] += 1
            results['results'].append({
                'name': imprint_name if 'imprint_name' in locals() else f'imprint_{i+1}',
                'error': str(e),
                'success': False
            })

        finally:
            results['total_processed'] += 1

    # Save batch summary
    summary_file = output_path / "batch_processing_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Batch processing complete. Summary saved to: {summary_file}")
    return results


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Generate complete imprint configuration in one shot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single imprint from description
  python generate_oneshot_imprint.py "Tech publisher focused on AI and robotics"

  # Batch process CSV file
  python generate_oneshot_imprint.py --batch data/imprints_in_progress.csv --output-dir configs/expanded_imprints/

  # Batch process JSON directory
  python generate_oneshot_imprint.py --batch data/json_configs/ --output-dir configs/expanded_imprints/
        """
    )

    # Single mode arguments
    parser.add_argument(
        "description",
        nargs="?",
        help="Description of the new imprint to create (required for single mode)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (single mode only, default: configs/imprints/{imprint_name}.json)",
        default=None
    )
    parser.add_argument(
        "--partial-config", "-p",
        help="Path to partial configuration JSON file (single mode only)",
        default=None
    )

    # Batch mode arguments
    parser.add_argument(
        "--batch", "-b",
        help="Batch mode: process CSV file or JSON directory",
        default=None
    )
    parser.add_argument(
        "--output-dir", "-d",
        help="Output directory for batch mode (default: configs/expanded_imprints/)",
        default="configs/expanded_imprints/"
    )

    # Common arguments
    parser.add_argument(
        "--model", "-m",
        help="LLM model to use",
        default="gemini/gemini-2.5-flash"
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        help="Temperature for generation (0.0-1.0)",
        default=0.3
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview the prompt without generating (single mode only)"
    )

    args = parser.parse_args()

    try:
        # Determine mode
        if args.batch:
            # Batch processing mode
            logger.info(f"🚀 Starting batch processing: {args.batch}")
            results = process_batch_imprints(args.batch, args.output_dir, args.model, args.temperature)

            # Print summary
            print(f"\n🎉 Batch Processing Complete!")
            print(f"📊 Total: {results['total_processed']}")
            print(f"✅ Successful: {results['successful']}")
            print(f"❌ Failed: {results['failed']}")
            print(f"📁 Output directory: {results['output_directory']}")

            if results['successful'] > 0:
                print(f"\n🏢 Successfully generated imprints:")
                for result in results['results']:
                    if result['success']:
                        codextypes = result.get('codextypes', ['standard'])
                        design_params = result.get('design_parameters', {})
                        specialized = "Specialized" if len(codextypes) > 1 else "Standard"
                        print(f"  • {result['name']} ({specialized} Design: {', '.join(codextypes)})")
                        if design_params.get('primary_considerations'):
                            print(f"    └─ Focus: {design_params['primary_considerations']}")

            if results['failed'] > 0:
                print(f"\n❌ Failed imprints:")
                for result in results['results']:
                    if not result['success']:
                        print(f"  • {result['name']}: {result.get('error', 'Unknown error')}")

        else:
            # Single processing mode
            if not args.description:
                parser.error("Description is required for single mode (use --batch for batch processing)")

            # Load template and exemplar
            logger.info("Loading template and exemplar...")
            template, exemplar = load_template_and_exemplar()

            # Load partial config if provided
            partial_config = load_partial_config(args.partial_config)
            if partial_config:
                logger.info(f"Loaded partial configuration from: {args.partial_config}")

            # Analyze CodexTypes with LLM from description
            codextype_analysis = detect_required_codextypes_llm(
                args.description, args.description, args.description, args.description, args.model
            )

            # Create enhanced description with codetype information
            enhanced_description = f"{args.description}\n\nCodexType Analysis: {json.dumps(codextype_analysis, indent=2)}"

            # Create prompt
            prompt = create_oneshot_prompt(template, exemplar, enhanced_description, partial_config)

            if args.preview:
                print("PROMPT PREVIEW:")
                print("=" * 80)
                print(prompt)
                print("=" * 80)
                return

            # Generate configuration
            logger.info("Generating imprint configuration...")
            config = generate_imprint_config(prompt, args.model, args.temperature)

            # Add LLM-analyzed codextypes to config
            if 'codextypes' in config:
                config['codextypes']['enabled_types'] = codextype_analysis.get('recommended_codextypes', ['standard'])
                config['codextypes']['llm_analysis'] = serializable_analysis

            # Determine output path
            if args.output:
                output_path = Path(args.output)
            else:
                imprint_name = config.get("imprint", "new_imprint").lower().replace(" ", "_")
                output_path = project_root / "configs" / "imprints" / f"{imprint_name}.json"
                # Fallback to current working directory if project root configs don't exist
                if not output_path.parent.exists():
                    output_path = Path.cwd() / "configs" / "imprints" / f"{imprint_name}.json"

            # Save configuration
            save_imprint_config(config, output_path)

            # Success summary
            print(f"\n✅ Successfully generated imprint configuration!")
            print(f"📁 Saved to: {output_path}")
            print(f"🏢 Imprint: {config.get('imprint', 'Unknown')}")
            print(f"🎯 Focus: {', '.join(config.get('publishing_focus', {}).get('primary_genres', []))}")
            print(f"🔧 CodexTypes: {', '.join(codextype_analysis.get('recommended_codextypes', ['standard']))}")
            print(f"📐 Design Analysis: {codextype_analysis.get('requires_specialized_design', False)}")
            print(f"🤖 Model: {args.model}")

    except Exception as e:
        logger.error(f"Failed to generate imprint: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()