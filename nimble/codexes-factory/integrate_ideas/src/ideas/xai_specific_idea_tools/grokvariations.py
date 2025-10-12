import json
import os
from openai import OpenAI  # OpenAI-compatible client
import copy

# Configuration
INPUT_JSON_FILE = "//nimble/codexes-libraries/codexes-ideas/src/xai-idea2codex/grogu_girl_specs.json"  # Path to your full CodexSpecs JSON file
OUTPUT_DIR = "output/variations"
N_VARIATIONS = 4  # Number of variations to generate
 # Replace with your OpenAI-compatible API key
MODEL = "grok-2-latest"  # Or another OpenAI-compatible model

base_url = "https://api.x.ai/v1"
client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),  # Replace with your xAI API key or set as environment variable
    base_url="https://api.x.ai/v1"  # Hypothetical xAI endpoint; adjust as needed
)
print(os.getenv("XAI_API_KEY"))
print(base_url)

def load_base_specs(file_path):
    """Load the base CodexSpecs from a JSON file."""
    try:
        with open(file_path, "r") as f:
            base_specs = json.load(f)
        print(f"Loaded base specs from {file_path}")
        return base_specs
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        raise
    except json.JSONDecodeError:
        print(f"Error: File {file_path} contains invalid JSON.")
        raise

def generate_variation(base_specs, variation_num):
    """Generate a single variation using the OpenAI API."""
    # Deep copy the base specs to avoid modifying the original
    new_specs = copy.deepcopy(base_specs)

    # Prompt to generate variations, simplified to handle full JSON
    prompt = f"""
    Take the following book specification and create a significant variation while preserving the core idea: 'A young person joins the DOGE team to improve government operations.' Change the protagonist (age, gender, skills, background), the setting (locations), the cast of characters (new roles or traits), and introduce a unique plot twist. You can and should change the name, gender, background, and personallity of the protagonist each time.   You can and should change the protagonist (age, gender, skills, background), the setting (locations), the cast of characters (new roles or traits), and introduce a unique plot twist. Provide the output as a JSON object with the same structure as the input, but with varied content. Keep it suitable for 9-12 year-olds and educational. Avoid overly complex nested structures for simplicity.

    Base Specs:
    {json.dumps(base_specs, indent=2)}

    Return only the JSON object for the variation.
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a creative writer generating variations for a children's book."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500,  # Increased to handle larger JSON
        temperature=0.9  # Higher temperature for creativity
    )
    print(response)
    # extract the response as text
    response_text = response.choices[0].message.content.strip()
    print(response_text)
    with open("response_text.txt", "a") as file:
        file.write(response_text)

    # Extract and parse the JSON response as JSON

    try:
        variation_json = json.loads(response.choices[0].message.content.strip())
        return variation_json
    except json.JSONDecodeError:
        print(f"Warning: Variation {variation_num} returned invalid JSON. Using empty object.")
        return {}

def create_summary(variation_specs):
    """Create a readable string summary of a variation, simplified for full JSON."""
    try:
        protagonist = variation_specs["protagonist"]["name"]
        age = variation_specs["protagonist"]["age"]
        desc = variation_specs["protagonist"]["description"]
        setting = ", ".join(variation_specs["locations"])
        # Use last plot point as twist (simplified assumption)
        twist = variation_specs["plot_points"][-1] if variation_specs["plot_points"] else "No twist defined"
        return f"{protagonist}, a {age}-year-old, joins the DOGE team. {desc} Set in {setting}. Twist: {twist}"
    except KeyError as e:
        return f"Summary unavailable due to missing field: {e}"

def main():
    # Load the base specs from the JSON file
    base_specs = load_base_specs(INPUT_JSON_FILE)

    # List to store summaries
    summaries = []

    # Generate N variations
    for i in range(N_VARIATIONS):
        print(f"Generating variation {i+1} of {N_VARIATIONS}...")
        variation_specs = generate_variation(base_specs, i+1)

        # Save variation to JSON file
        filename = f"variation_{i+1}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w") as f:
            json.dump(variation_specs, f, indent=2)
        print(f"Saved variation to {filepath}")

        # Generate and store summary
        summary = create_summary(variation_specs)
        summaries.append({"file": filename, "summary": summary})

    # Save summaries to a single JSON file
    summary_filepath = os.path.join(OUTPUT_DIR, "variations_summary.json")
    with open(summary_filepath, "w") as f:
        json.dump(summaries, f, indent=2)
    print(f"Saved summaries to {summary_filepath}")

if __name__ == "__main__":
    main()