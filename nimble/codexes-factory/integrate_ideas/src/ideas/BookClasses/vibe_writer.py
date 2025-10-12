import os
import json
import argparse
from src.ideas.BookClasses.Model2BookIdeas import Models2BookIdeas  # Assuming this is in a separate file or same directory
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_codexspec(file_path):
    """Load a codexspec JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data, file_path):
    """Save data to a JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved to {file_path}")


def enhance_codexspec(spec, model):
    """Enhance and extend the codexspec using the model."""
    prompt = f"""
    Review and enhance the following book specification. Extend it by adding more detailed character development, plot twists, and thematic depth while maintaining its original structure and intent. Ensure it remains suitable for 9-12 year-olds, educational, and inspirational. Respond with the enhanced JSON spec only.

    {json.dumps(spec, indent=2)}
    """
    enhanced = model._create_with_ollama(prompt, model.model, model.temperature)
    return enhanced


def create_treatment(spec):
    """Create a treatment from the enhanced spec."""
    prompt = f"""
    Create a narrative treatment based on the following book specification. The treatment should be a 2-3 paragraph summary of the story, focusing on the protagonist’s journey, key conflicts, and resolution, written in a clear, engaging style for young readers aged 9-12.

    {json.dumps(spec, indent=2)}
    """
    treatment_json = model._create_with_ollama(prompt, model.model, model.temperature)
    return treatment_json.get('treatment', treatment_json)  # Assuming response might be a dict or plain text


def create_scene_outline(spec, num_chapters, num_scenes_per_chapter):
    """Create a scene-by-scene outline from the spec."""
    prompt = f"""
    Create a scene-by-scene outline for a {num_chapters}-chapter book with {num_scenes_per_chapter} scenes per chapter based on this specification. Each scene should include a brief description, key characters involved, and the primary action or development. Return a JSON array where each element represents a chapter with its scenes.

    {json.dumps(spec, indent=2)}
    """
    outline = model._create_with_ollama(prompt, model.model, model.temperature)
    return outline


def write_first_draft(outline):
    """Write a first draft from the scene-by-scene outline."""
    prompt = f"""
    Write a first draft of a book based on this scene-by-scene outline. Use a clear, engaging, and educational tone suitable for 9-12 year-olds. Each chapter should flow naturally from the outline, with dialogue, descriptions, and narrative that bring the story to life. Return the full text as a single string.

    {json.dumps(outline, indent=2)}
    """
    draft = model._create_with_ollama(prompt, model.model, model.temperature)
    return draft.get('draft', draft)  # Assuming response might be a dict or plain text


def process_codexspec(file_path, output_dir, model):
    """Process a single codexspec file through all stages."""
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_subdirs = {
        'enhanced': os.path.join(output_dir, 'enhanced_specs'),
        'treatment': os.path.join(output_dir, 'treatments'),
        'outline': os.path.join(output_dir, 'outlines'),
        'draft': os.path.join(output_dir, 'drafts')
    }

    # Create output subdirectories if they don't exist
    for subdir in output_subdirs.values():
        os.makedirs(subdir, exist_ok=True)

    # Load original spec
    spec = load_codexspec(file_path)
    logger.info(f"Processing {base_name}")

    # 1. Enhance the spec
    enhanced_spec = enhance_codexspec(spec, model)
    enhanced_path = os.path.join(output_subdirs['enhanced'], f"{base_name}_enhanced.json")
    save_json(enhanced_spec, enhanced_path)

    # 2. Create treatment
    treatment = create_treatment(enhanced_spec)
    treatment_path = os.path.join(output_subdirs['treatment'], f"{base_name}_treatment.json")
    save_json({'treatment': treatment}, treatment_path)

    # 3. Create scene-by-scene outline
    outline = create_scene_outline(enhanced_spec, spec['num_chapters'], spec['num_scenes_per_chapter'])
    outline_path = os.path.join(output_subdirs['outline'], f"{base_name}_outline.json")
    save_json(outline, outline_path)

    # 4. Write first draft
    draft = write_first_draft(outline)
    draft_path = os.path.join(output_subdirs['draft'], f"{base_name}_draft.txt")
    with open(draft_path, 'w', encoding='utf-8') as f:
        f.write(draft)
    logger.info(f"Saved draft to {draft_path}")


def main():
    global model  # Make model accessible to helper functions
    parser = argparse.ArgumentParser(description="Process codexspec files to generate book drafts.")
    parser.add_argument('--input-dir', required=True, help="Directory containing codexspec JSON files")
    parser.add_argument('--output-dir', required=True, help="Directory to save output files")
    parser.add_argument('--model', default="deepseek-r1:latest", help="Model name for generation")
    parser.add_argument('--temperature', type=float, default=0.7, help="Temperature for generation")
    parser.add_argument('--api-type', default="ollama", help="API type (ollama or openai)")
    parser.add_argument('--ollama-host', default="http://localhost:11434", help="Ollama host URL")

    args = parser.parse_args()

    # Initialize the model
    model = Models2BookIdeas(
        model=args.model,
        temperature=args.temperature,
        api_type=args.api_type,
        ollama_host=args.ollama_host
    )

    # Process all codexspec files in the input directory
    input_dir = args.input_dir
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(input_dir, filename)
            try:
                process_codexspec(file_path, args.output_dir, model)
            except Exception as e:
                logger.error(f"Error processing {filename}: {str(e)}")


if __name__ == "__main__":
    main()