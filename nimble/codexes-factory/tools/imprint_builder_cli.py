import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# --- Start: Path setup for imports ---
# Get the absolute path of the directory containing the current script.
script_dir = Path(__file__).resolve().parent
# Assume the project root is one level up from the 'tools' directory.
# This makes 'src' and 'unified_editor.py' importable directly if they are in the project root.
project_root = script_dir.parent

# Add the project root to sys.path if it's not already there.
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
# --- End: Path setup for imports ---

# Now, import modules relative to the project root or direct modules in project root
try:
    # This import assumes 'src' is directly under the project_root
    from src.codexes.modules.imprint_builder.imprint_expander import ExpandedImprint
except ImportError as e:
    logging.error(f"Failed to import ExpandedImprint: {e}. Please ensure the 'src' directory exists directly under your project root ({project_root}), and that all directories from 'src' down to 'imprint_builder' contain an empty file named '__init__.py'.")
    sys.exit(1)

# Attempt to import the real LLMCaller. If it fails, a mock will be used.
try:
    from src.codexes.core.llm_integration import CodexesLLMIntegration
    # Create a wrapper to match expected interface
    class LLMCaller:
        def __init__(self):
            self.llm_integration = CodexesLLMIntegration()
        
        def call_model_with_prompt(self, **kwargs) -> Dict[str, Any]:
            prompt = kwargs.get('prompt', 'No prompt provided')
            try:
                response = self.llm_integration.call_llm(prompt)
                return {"content": response}
            except Exception as e:
                logging.warning(f"LLM call failed: {e}, using fallback")
                return {"content": "1. Consider refining your target audience within the publishing strategy for more focused marketing efforts.\n2. Explore alternative revenue streams beyond traditional book sales, like merchandise or events.\n3. Standardize your internal communication protocols to improve operational efficiency."}
except ImportError:
    # Define a mock LLMCaller if the real one cannot be imported
    class LLMCaller:
        def call_model_with_prompt(self, **kwargs) -> Dict[str, Any]:
            prompt = kwargs.get('prompt', 'No prompt provided')
            logging.info(f"Mock LLM called with prompt: {prompt[:100]}...")
            # Simulate a response structure expected by ImprintEditor's _get_ai_suggestions
            return {"content": "1. Consider refining your target audience within the publishing strategy for more focused marketing efforts.\n2. Explore alternative revenue streams beyond traditional book sales, like merchandise or events.\n3. Standardize your internal communication protocols to improve operational efficiency."}
    logging.warning("Could not import CodexesLLMIntegration. A mock LLMCaller will be used.")


# Import ImprintEditor from the imprint_builder module
try:
    from src.codexes.modules.imprint_builder.unified_editor import ImprintEditor
except ImportError as e:
    logging.error(f"Failed to import ImprintEditor: {e}. Please ensure the imprint_builder module is properly set up.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Process ExpandedImprint JSON and generate artifacts using ImprintEditor."
    )
    # The -i flag is already implemented as requested
    parser.add_argument(
        "-i", "--input_json_path",
        type=str,
        required=True, # Made required since it's a primary input
        help="Path to the input ExpandedImprint JSON file (expected output from expand_imprint_cli)."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./imprint_artifacts",
        help="Directory to save generated artifacts (e.g., session, preview, suggestions)."
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    input_path = Path(args.input_json_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        logging.error(f"Error: Input file not found at {input_path}")
        return

    try:
        with open(input_path, 'r') as f:
            imprint_data = json.load(f)

        expanded_imprint = ExpandedImprint.from_dict(imprint_data)
        logging.info("ExpandedImprint loaded successfully from input JSON.")

        # Initialize LLMCaller (either real or mock based on import success)
        llm_caller = LLMCaller()
        editor = ImprintEditor(llm_caller=llm_caller)
        logging.info("ImprintEditor initialized.")

        # Create an editing session
        session = editor.create_editing_session(expanded_imprint)
        logging.info(f"Editing session '{session.session_id}' created.")

        # Save the editing session state
        session_file_path = output_dir / f"{session.session_id}_session.json"
        editor.save_session(session, str(session_file_path))
        logging.info(f"Editing session state saved to {session_file_path}")

        # Get and save preview data
        preview_data = editor.get_preview_data(session)
        preview_file_path = output_dir / f"{session.session_id}_preview.json"
        with open(preview_file_path, 'w') as f:
            json.dump(preview_data, f, indent=2)
        logging.info(f"Preview data saved to {preview_file_path}")

        # Get and save AI-powered suggestions
        suggestions = editor.suggest_improvements(session)
        suggestions_file_path = output_dir / f"{session.session_id}_suggestions.json"
        with open(suggestions_file_path, 'w') as f:
            json.dump(suggestions, f, indent=2)
        logging.info(f"Suggestions saved to {suggestions_file_path}")

        logging.info("All specified artifacts generated successfully.")

    except json.JSONDecodeError:
        logging.error(f"Error: Invalid JSON format in {input_path}. Please ensure it's a valid JSON output from expand_imprint_cli.")
    except Exception as e:
        logging.error(f"An unexpected error occurred during artifact generation: {e}", exc_info=True)


if __name__ == "__main__":
    main()