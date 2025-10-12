import argparse
import os
import sys
import json
from datetime import datetime
import logging

# Set up path to import from the application's source directory
# This allows running 'python src/codexes/cli.py' from the project root
# The `pip install -e .` command makes this unnecessary.

from dotenv import load_dotenv

load_dotenv()

# Corrected imports: use absolute paths from 'codexes' package root
from codexes.core.utils import setup_logging
from codexes.core.file_handler import load_document
from codexes.core.prompt_manager import load_and_prepare_prompts
from codexes.core.llm_integration import get_responses_from_multiple_models
from codexes.modules.distribution.lsi_acs_generator import LsiAcsGenerator
from codexes.core.config import MODELS_CHOICE, PROMPT_FILE_NAME


def run_cli_process(args):
    """Encapsulates the core logic for the command-line interface."""
    logging.info(f"Starting CLI process for output type: {args.output_type}")

    # Define project root to resolve relative paths
    # This assumes the CLI is run from the project root directory
    project_root = os.getcwd()

    if not args.output_path:
        input_basename = os.path.splitext(os.path.basename(args.input_file))[0]
        output_dir = os.path.join(project_root, "output")
        os.makedirs(output_dir, exist_ok=True)
        file_extension = "csv" if args.output_type == 'metadata' else "txt"
        args.output_path = os.path.join(output_dir,
                                        f"{input_basename}_{args.output_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_extension}")
        logging.info(f"Output path not specified. Defaulting to: {args.output_path}")

    # The paths from args are now relative to the project root
    input_file_path = os.path.join(project_root, args.input_file)
    prompt_file_path = os.path.join(project_root, args.prompt_file)

    book_content = load_document(input_file_path)
    if not book_content:
        logging.critical(f"Fatal: Could not read content from {input_file_path}. Exiting.")
        sys.exit(1)

    prompt_keys = [key.strip() for key in args.prompt_keys.split(',')]
    prompt_configs = load_and_prepare_prompts(
        prompt_file_path, prompt_keys, book_content
    )
    if not prompt_configs:
        logging.critical("No valid prompts were prepared. Exiting.")
        sys.exit(1)

    # Keep the full prompt configs with keys for proper prompt name tracking
    final_prompt_configs_for_llm = prompt_configs

    models_to_use = [model.strip() for model in args.model.split(',')]
    logging.info(f"Calling model(s) '{', '.join(models_to_use)}' with {len(final_prompt_configs_for_llm)} prompts.")

    responses = get_responses_from_multiple_models(
        prompt_configs=final_prompt_configs_for_llm,
        models=models_to_use,
        response_format_type=args.response_format_type
    )

    try:
        if args.output_type == 'metadata':
            template_path = os.path.join(project_root, 'templates/LSI_ACS_header.csv')
            if not os.path.exists(template_path):
                logging.critical(f"Metadata template not found at {template_path}. Cannot generate CSV.")
                sys.exit(1)
            generator = LsiAcsGenerator(template_path=template_path)
            generator.generate(responses, args.output_path)
        else:
            logging.error(f"Output type '{args.output_type}' is not yet fully implemented.")
    except Exception as e:
        logging.critical(f"Fatal error during output generation: {e}", exc_info=True)
        sys.exit(1)

    logging.info(f"CLI run completed successfully. Output at: {args.output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Codexes: AI-Powered Publishing Assistant (CLI Mode).",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--input-file", required=True,
                        help="Path to the source book relative to project root (e.g., 'input/my_book.pdf').")
    parser.add_argument("--output-type", required=True, choices=['metadata'],
                        help="Type of output to generate. Currently only 'metadata' is implemented.")
    parser.add_argument("--output-path", type=str, help="Full path to save the output file.")
    parser.add_argument("--model", default="gemini/gemini-1.5-pro-latest", choices=MODELS_CHOICE, help="LLM to use.")
    parser.add_argument("--prompt-file", default=f"prompts/{PROMPT_FILE_NAME}",
                        help="Path to the prompt file relative to project root.")
    parser.add_argument("--prompt-keys", required=True, help="Comma-separated list of prompt keys to execute.")
    parser.add_argument("--response-format-type", type=str, choices=['json_object', 'text'], default='json_object',
                        help="Global response format.")
    parser.add_argument('--logging-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set the logging level.')

    args = parser.parse_args()

    setup_logging(args.logging_level)
    run_cli_process(args)


if __name__ == "__main__":
    main()