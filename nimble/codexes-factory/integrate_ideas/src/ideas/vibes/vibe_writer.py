import os
import json
import argparse
import traceback

from .Model2BookIdeas import Models2BookIdeas
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_codexspec(file_path):
    """Load a codexspec JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data, file_path, log_message=None):
    """Save data to a JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    if log_message:
        logger.info(log_message)


def _get_create_method(model):
    """Helper function to get the appropriate creation method based on API type."""
    if model.api_type == "ollama":
        return model._create_with_ollama
    elif model.api_type == "openai":
        return model._create_with_openai_style_client
    else:
        logger.debug(f"Encountered unsupported API type: {model.api_type}")
        raise ValueError(f"Unsupported API type: {model.api_type}")


def enhance_codexspec(spec, model, optional_context=None):
    """Enhance and extend the codexspec using the model."""
    optional_context = optional_context or ""
    prompt = f"""
    Review and enhance the following book specification. Extend it by adding more detailed character development, plot twists, and thematic depth while maintaining its original structure and intent. Ensure it remains suitable for 9-12 year-olds, educational, and inspirational. Return a JSON array. Use the same keys where possible. If new keys are appropriate, you may introduce them.

    {json.dumps(spec, indent=2)}

    Additional context: {optional_context}
    """
    create_method = _get_create_method(model)
    enhanced_codex_spec = create_method(prompt, model.model, model.temperature)
    return enhanced_codex_spec


def create_treatment(spec, model, optional_context=None):
    """Create a treatment from the enhanced spec."""
    optional_context = optional_context or ""
    prompt = f"""
    Create a narrative treatment based on the following book specification. The treatment should be a 5-6 paragraph summary of the story, focusing on the protagonist's journey, key conflicts, and resolution, written in a clear, engaging style for young readers aged 9-12. Return as a JSON array.

    {json.dumps(spec, indent=2)}

    Additional context: {optional_context}
    """
    create_method = _get_create_method(model)
    treatment_json = create_method(prompt, model.model, model.temperature)
    logger.debug(treatment_json)
    logger.debug(type(treatment_json))
    return treatment_json.get('treatment', treatment_json)


def create_scene_outline(spec, num_chapters, num_scenes_per_chapter, model):
    """Create a scene-by-scene outline from the spec."""
    prompt = f"""
    Create a scene-by-scene outline for a {num_chapters}-chapter book with {num_scenes_per_chapter} scenes per chapter based on this specification. Each scene should include a brief description, key characters involved, and the primary action or development. Return a JSON array where each element represents a chapter with its scenes.

    {json.dumps(spec, indent=2)}
    """
    create_method = _get_create_method(model)
    outline = create_method(prompt, model.model, model.temperature)
    return outline


def write_first_draft(outline, model):
    """Write a first draft from the scene-by-scene outline."""
    prompt = f"""
    Write a first draft of a book based on this scene-by-scene outline. Use a clear, engaging, and educational tone suitable for 9-12 year-olds. Each chapter should flow naturally from the outline, with dialogue, descriptions, and narrative that bring the story to life.  Return a JSON array where each element represents a chapter with its text as markdown string.
    
    {json.dumps(outline, indent=2)}
    """
    create_method = _get_create_method(model)
    draft = create_method(prompt, model.model, model.temperature)
    return draft


def process_codexspec(file_path, output_dir, model):
    """Process a single codexspec file through all stages."""
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    safe_base_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in base_name)

    # Create folder for this spec under run_id/safe_base_name
    title_output_dir = os.path.join(output_dir, safe_base_name)
    os.makedirs(title_output_dir, exist_ok=True)
    logger.info(f"Created output directory: {title_output_dir}")


    # Load original spec
    spec = load_codexspec(file_path)
    logger.info(f"Loaded original spec from {base_name}")

    # 1. Enhance the spec
    enhanced_spec = enhance_codexspec(spec, model)
    enhanced_path = os.path.join(title_output_dir, f"{base_name}_enhanced.json")
    save_json(enhanced_spec, enhanced_path)
    logger.info(f"Enhanced spec and saved it to {enhanced_path}")

    # 2. Create treatment
    treatment = create_treatment(enhanced_spec, model)
    treatment_path = os.path.join(title_output_dir, f"{base_name}_treatment.json")
    save_json({'treatment': treatment}, treatment_path)
    logger.info(f"Analyzed enhanced spec and saved treatment to {treatment_path}")

    # 3. Create scene-by-scene outline
    outline = create_scene_outline(enhanced_spec, spec['num_chapters'], spec['num_scenes_per_chapter'], model)
    outline_path = os.path.join(title_output_dir, f"{base_name}_outline.json")
    save_json(outline, outline_path)
    logger.info(f"Saved outline to {outline_path}")

    # 4. Write first draft
    draft = write_first_draft(outline, model)
    draft_path = os.path.join(title_output_dir, f"{base_name}_draft.json")
    save_json(draft, draft_path)
    logger.info(f"Saved json draft to {draft_path}")

    # Write Markdown draft
    markdown_content = '\n\n'.join(
        [f"{chapter['text']}" for chapter in draft['chapters']]
    )
    markdown_path = os.path.join(title_output_dir, f"{base_name}_draft.md")
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    logger.info(f"Saved Markdown draft to {markdown_path}")


def main():
    parser = argparse.ArgumentParser(description="Process codexspec files to generate book drafts.")
    parser.add_argument('--input-dir', required=True, help="Directory containing codexspec JSON files")
    parser.add_argument('--output-dir', required=True, help="Directory to save output files")
    parser.add_argument('--model', default="deepseek-r1:latest", help="Model name for generation")
    parser.add_argument('--temperature', type=float, default=0.7, help="Temperature for generation")
    parser.add_argument('--api-type', default="ollama", help="API type (ollama or openai)")
    parser.add_argument('--ollama-host', default="http://localhost:11434", help="Ollama host URL")
    parser.add_argument('--debug', action='store_true', help="Enable debug logging")
    parser.add_argument('--base-url', default="https://api.x.ai/v1", help="Base URL for API requests")
    parser.add_argument('--api-key-host-name', default="XAI_API_KEY", help="Hostname of the API key for model initialization")

    parser.add_argument('--number-to-process', "-np", type=int, help="Number of files to process before stopping", default=1)
    parser.add_argument('--start-stage', choices=['enhance', 'treatment', 'outline', 'draft'], default='enhance',
                        help="Specify the stage to start processing from (enhance, treatment, outline, or draft)")
    
    args = parser.parse_args()

    # Adjust logging level based on --debug flag
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Initialize the model
    model = Models2BookIdeas(
        model=args.model,
        temperature=args.temperature,
        api_type=args.api_type,
        ollama_host=args.ollama_host,
        base_url=args.base_url,
        api_key_host_name=args.api_key_host_name
    )
    logger.info(f"{args.model} initialized")

    # Process all codexspec files in the input directory
    input_dir = args.input_dir
    # create an 8-digit uniqid to hold this run's results
    import uuid
    run_id = uuid.uuid4().hex[:8]
    output_dir = os.path.join(args.output_dir, run_id)
    os.makedirs(output_dir, exist_ok=True)

    processed_count = 0
    for filename in os.listdir(input_dir):
        if args.number_to_process is not None and processed_count >= args.number_to_process:
            logger.info("Reached the specified limit of files to process. Stopping.")
            break

        logger.info(f"Processing {filename} in {output_dir}")

        if filename.endswith('.json'):
            file_path = os.path.join(input_dir, filename)
            try:
                process_codexspec(file_path, output_dir, model)
                processed_count += 1
            except Exception as e:
                logger.error(f"{traceback.format_exc()}")
                logger.error(f"Error processing {filename}: {str(e)}")


if __name__ == "__main__":
    main()
