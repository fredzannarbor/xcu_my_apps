import os
from openai import OpenAI
import time
from datetime import datetime

# Set up the xAI API client (OpenAI-compatible)
client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),  # Replace with your xAI API key or set as environment variable
    base_url="https://api.xai.com/v1"  # Hypothetical xAI endpoint; adjust as needed
)

# Initial chapter outlines from previous response
chapter_outlines = {
    1: {"title": "The 51st Dream",
        "summary": "US president unveils Operation Manifest North; troops cross border; Maya Blackwater watches in Winnipeg."},
    2: {"title": "The Corporate Hand",
        "summary": "TerraCore pressures invasion for rare earths; drones map deposits; Lt. Pierce pacifies mining town."},
    3: {"title": "The Red Leaf Pact",
        "summary": "PM meets Indigenous leaders and Mounties; they plan Red Leaf bioweapon; Chief Elena signs on."},
    4: {"title": "Borderline Defiance",
        "summary": "Indigenous guerillas ambush convoys; Mounties sabotage supply lines; Maya reports victories."},
    5: {"title": "The Green Death", "summary": "Red Leaf deployed; US troops fall ill; Pierce sees squad collapse."},
    6: {"title": "The Fractured North",
        "summary": "Canada cheers retreat; bioweapon mutates, kills crops; PM Laurent faces backlash."},
    7: {"title": "TerraCore’s Gambit",
        "summary": "TerraCore deploys mechs for minerals; Elena raids facility, loses brother."},
    8: {"title": "The Last Stand at James Bay",
        "summary": "Final battle; resistance repels TerraCore; Maya broadcasts victory."},
    9: {"title": "The Cost of Sovereignty",
        "summary": "US withdraws; ecological collapse; Pierce sees Canada’s hollow triumph."},
    10: {"title": "Red Leaf Falling",
         "summary": "Government splinters; Maya, Elena, Laurent vow to rebuild; Maya’s final report."}
}


# Function to generate scene outlines for a chapter
def generate_scene_outlines(chapter_num, chapter_info):
    prompt = f"""
    Create a detailed scene-by-scene outline for Chapter {chapter_num}: {chapter_info['title']}.
    - The chapter summary is: {chapter_info['summary']}.
    - The chapter must have exactly 10 scenes.
    - Each scene should be approximately 1000 words when fully written.
    - Provide a brief description (2-3 sentences) for each scene, including the POV character, setting, and key action or development.
    - Ensure the scenes build on the summary and contribute to the overall narrative of 'Red Leaf Rising,' a novel about a US invasion of Canada ending in a Pyrrhic Canadian victory.
    """
    response = client.chat.completions.create(
        model="grok-3",  # Hypothetical xAI model name; adjust as per actual model
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.7
    )
    return response.choices[0].message.content


# Function to generate a single scene's content
def generate_scene_content(chapter_num, scene_num, scene_description):
    prompt = f"""
    Write a 1000-word scene for Chapter {chapter_num}, Scene {scene_num} of 'Red Leaf Rising.'
    - Scene description: {scene_description}
    - The scene must be exactly 1000 words (+/- 50 words).
    - Use vivid descriptions, dialogue, and internal thoughts to advance the plot and develop characters.
    - Maintain consistency with the novel’s tone (gritty, tense, with defiant hope and looming despair) and themes (sovereignty, survival, cultural identity, technology’s cost).
    """
    response = client.chat.completions.create(
        model="grok-3",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,  # Adjust to ensure ~1000 words (assuming ~1.5 tokens per word)
        temperature=0.8
    )
    return response.choices[0].message.content


# Main function to process the book
def create_book():
    book_outline = []
    book_content = []

    # Step 1 & 2: Generate scene outlines for all chapters and assemble full outline
    for chap_num, chap_info in chapter_outlines.items():
        print(f"Generating outline for Chapter {chap_num}...")
        scene_outline = generate_scene_outlines(chap_num, chap_info)
        book_outline.append(f"## Chapter {chap_num}: {chap_info['title']}\n{scene_outline}")
        time.sleep(1)  # Avoid rate limiting

    # Step 3: Generate content for each scene
    for chap_num in range(1, 11):
        chap_title = chapter_outlines[chap_num]['title']
        book_content.append(f"# Chapter {chap_num}: {chap_title}\n")
        for scene_num in range(1, 11):
            print(f"Generating content for Chapter {chap_num}, Scene {scene_num}...")
            # Extract scene description from outline (simplified here; you'd parse the actual outline)
            scene_desc = f"Scene {scene_num} description placeholder for Chapter {chap_num} (from outline)."
            scene_content = generate_scene_content(chap_num, scene_num, scene_desc)
            book_content.append(f"## Scene {scene_num}\n{scene_content}\n")
            time.sleep(1)  # Rate limiting precaution

    # Step 4: Assemble and save as Markdown
    full_book = "# Red Leaf Rising\n\n" + "\n".join(book_outline) + "\n\n" + "\n".join(book_content)
    with open("red_leaf_rising.md", "w", encoding="utf-8") as f:
        f.write(full_book)
    print("Book saved as red_leaf_rising.md")


# Sample execution for one scene (to test)
def sample_scene():
    sample_desc = """
    Chapter 1, Scene 1: POV - Maya Blackwater. Setting - A cramped Winnipeg apartment, evening. 
    Maya watches the US president’s annexation speech on TV, her hands trembling as she records notes for her first resistance broadcast.
    """
    print("Generating sample scene...")
    scene_content = generate_scene_content(1, 1, sample_desc)
    with open("sample_scene.md", "w", encoding="utf-8") as f:
        f.write(f"# Sample Scene: Chapter 1, Scene 1\n\n{scene_content}")
    print("Sample scene saved as sample_scene.md")


if __name__ == "__main__":
    # Uncomment to run full book generation (beware API costs and rate limits!)
    # create_book()

    # Run a sample scene for demonstration
    sample_scene()