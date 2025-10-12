import os
from openai import OpenAI  # Assuming xAI API uses the same client library structure
import time

# Initialize the xAI API client (replace with actual xAI endpoint if different)
client = OpenAI(
    api_key=os.getenv("XAI_API_KEY", "your-xai-api-key-here"),  # Replace with your xAI API key
    base_url="https://api.xai.com/v1"  # Hypothetical xAI API base URL; adjust as needed
)

# Word count target per scene (approximation based on 40,000 words total across 81 scenes)
TARGET_WORDS_PER_SCENE = 40000 // 81  # ~493 words per scene

# Chapter and scene structure based on the Detailed Scene-by-Scene Outline
CHAPTERS = {
    "Chapter 1: Introduction to GroguGirl": [
        {"name": "Maya's Bedroom Sanctuary", "words": 500},
        {"name": "Family Dinner Tension", "words": 500},
        {"name": "School Day Challenges", "words": 500},
        {"name": "Late Night Message", "words": 500},
        {"name": "Weekend Rock Climbing", "words": 500},
    ],
    "Chapter 2: The DOGE Connection": [
        {"name": "Surprise Visit", "words": 500},
        {"name": "Reluctant Revelation", "words": 500},
        {"name": "Brother-Sister Bonding", "words": 500},
        {"name": "The Late Night Conversation", "words": 500},
        {"name": "The Invitation", "words": 500},
    ],
    "Chapter 3: An Unexpected Opportunity": [
        {"name": "Family Discussion", "words": 500},
        {"name": "School Research Project", "words": 500},
        {"name": "Online Forums", "words": 500},
        {"name": "Conversation with Dad", "words": 500},
        {"name": "The Night Before", "words": 500},
    ],
    "Chapter 4: First Day at DOGE": [
        {"name": "Arrival at Headquarters", "words": 500},
        {"name": "The DOGE Workspace", "words": 500},
        {"name": "Meeting Zoe", "words": 500},
        {"name": "The Data Center Tour", "words": 500},
        {"name": "The Unexpected Encounter", "words": 500},
    ],
    "Chapter 5: Understanding the Mission": [
        {"name": "Morning Briefing", "words": 500},
        {"name": "Data Visualization Lab", "words": 500},
        {"name": "Lunch with Dr. Patel", "words": 500},
        {"name": "The Government Liaison", "words": 500},
        {"name": "End of Day Reflection", "words": 500},
    ],
    "Chapter 6: Family Tensions": [
        {"name": "Weekend Family Gathering", "words": 500},
        {"name": "Kitchen Conversation", "words": 500},
        {"name": "Backyard Confrontation", "words": 500},
        {"name": "Late Night Research", "words": 500},
        {"name": "Breakfast Reconciliation", "words": 500},
    ],
    "Chapter 7: Making Discoveries": [
        {"name": "Return to DOGE", "words": 500},
        {"name": "Data Deep Dive", "words": 500},
        {"name": "The Pattern Recognition", "words": 500},
        {"name": "Lunch with Jack", "words": 500},
        {"name": "The Breakthrough", "words": 500},
    ],
    "Chapter 8: A Mistake with Consequences": [
        {"name": "The Celebration", "words": 500},
        {"name": "Department Visit Preparation", "words": 500},
        {"name": "The Department Visit", "words": 500},
        {"name": "The Discovery of Error", "words": 500},
        {"name": "The Human Impact", "words": 500},
    ],
    "Chapter 9: Taking Initiative": [
        {"name": "Morning Reflection", "words": 500},
        {"name": "Approaching Dr. Patel", "words": 500},
        {"name": "The Dismissal", "words": 500},
        {"name": "Conversation with Director Thompson", "words": 500},
        {"name": "The Initiative", "words": 500},
    ],
    "Chapter 10: Building Bridges": [
        {"name": "The Unofficial Project", "words": 500},
        {"name": "Reconnecting with Alex", "words": 500},
        {"name": "Field Research", "words": 500},
        {"name": "The Pattern Emerges", "words": 500},
        {"name": "The Ally Recruitment", "words": 500},
    ],
    "Chapter 11: The Big Presentation": [
        {"name": "Preparation Pressure", "words": 500},
        {"name": "The Discovery", "words": 500},
        {"name": "Small Group Presentation", "words": 500},
        {"name": "Alex's Reaction", "words": 500},
        {"name": "The Opportunity", "words": 500},
    ],
    "Chapter 12: Facing Resistance": [
        {"name": "The Leadership Briefing", "words": 500},
        {"name": "The Presentation", "words": 500},
        {"name": "The Aftermath", "words": 500},
        {"name": "The Opposition", "words": 500},
        {"name": "The Strategy Session", "words": 500},
    ],
    "Chapter 13: A New Approach": [
        {"name": "The Pilot Proposal", "words": 500},
        {"name": "Conversation with Grandma Chen", "words": 500},
        {"name": "The Unexpected Advocate", "words": 500},
        {"name": "Building the Pilot", "words": 500},
        {"name": "Reconciliation with Alex", "words": 500},
    ],
    "Chapter 14: Testing the Solution": [
        {"name": "Pilot Launch Day", "words": 500},
        {"name": "User Feedback", "words": 500},
        {"name": "The Unexpected Result", "words": 500},
        {"name": "Crisis Management", "words": 500},
        {"name": "The Validation", "words": 500},
    ],
    "Chapter 15: Presenting to Leadership": [
        {"name": "Preparation with Allies", "words": 500},
        {"name": "Pre-Presentation Nerves", "words": 500},
        {"name": "The Comprehensive Presentation", "words": 500},
        {"name": "The Challenge", "words": 500},
        {"name": "The Decision", "words": 500},
    ],
    "Chapter 16: The Path Forward": [
        {"name": "Implementation Planning", "words": 500},
        {"name": "Family Celebration", "words": 500},
        {"name": "School Presentation", "words": 500},
        {"name": "The Future Discussion", "words": 500},
        {"name": "The New Beginning", "words": 500},
    ],
    "Epilogue": [
        {"name": "One Year Later", "words": 500},
        {"name": "Looking Forward", "words": 500},
    ]
}

# Prompt templates for each scene (customized per scene below)
BASE_PROMPT = """
You are Grok 3, an AI assistant created by xAI, tasked with writing a scene for a middle school novel titled "Code for Change: GroguGirl and the DOGE Audit." The scene should be approximately {word_count} words long, written in a third-person narrative style suitable for 9-12-year-olds. Incorporate the following details:

**Scene Context**: 
- Chapter: {chapter}
- Scene: {scene_name}
- Setting: {setting}
- Characters Involved: {characters}
- Purpose: {purpose}

**Character Details**:
- Maya Chen (GroguGirl): 12-year-old coder, analytical, curious, empathetic, struggles with explaining complex ideas, loves sci-fi and data visualization.
- Alex Chen: Maya's 24-year-old brother, data scientist at DOGE team, brilliant but intense, conflicted about work's impact.
- Other characters as specified: {character_details}

**Plot Details**:
- {plot_details}

**Thematic Elements**:
- Knowledge and Empowerment: {knowledge_theme}
- Breaking Down Prejudice Barriers: {prejudice_theme}
- Technology and Humanity: {tech_theme}
- Family Relationships: {family_theme}
- Government and Citizenship: {gov_theme}

**Educational Elements**:
- {educational_elements}

**Tone**: Inspirational, educational, respectful of all perspectives, with moments of tension and growth.

Write the scene with vivid descriptions, realistic dialogue, and a focus on Maya's emotional journey. Ensure technical concepts are explained simply for young readers. Do not include these instructions in the output.
"""


# Function to generate a scene using the xAI API
def generate_scene(chapter, scene_info):
    scene_name = scene_info["name"]
    word_count = scene_info["words"]

    # Customize prompt based on scene specifics (example mappings below; expand for all scenes)
    scene_configs = {
        "Maya's Bedroom Sanctuary": {
            "setting": "Maya's bedroom in a Northern Virginia suburb, filled with tech gadgets, astronomy posters, and sci-fi books",
            "characters": "Maya Chen (GroguGirl)",
            "purpose": "Introduce Maya's character, skills, and passion for data visualization",
            "character_details": "Only Maya is present",
            "plot_details": "Maya works on a data visualization project about local wildlife patterns using a self-modified coding platform, posts it online as 'GroguGirl,' showing her frustration when forum members assume she's older or male.",
            "knowledge_theme": "Maya sees knowledge as personal achievement",
            "prejudice_theme": "Gender bias in tech as forum assumes she's male",
            "tech_theme": "Technology as a tool for personal expression",
            "family_theme": "Not prominent, but hints at her family support through her environment",
            "gov_theme": "Not yet introduced",
            "educational_elements": "Basics of data visualization (e.g., turning numbers into graphs)"
        },
        "Family Dinner Tension": {
            "setting": "Chen family dining room",
            "characters": "Maya Chen, Dr. Sophia Chen (mother), James Chen (father)",
            "purpose": "Establish family dynamics and hint at distance with Alex",
            "character_details": "Sophia: medical researcher, distracted; James: science teacher, encouraging",
            "plot_details": "Maya tries to share her visualization project, but her parents are distracted; Alex’s empty chair and a phone call from him highlight his absence.",
            "knowledge_theme": "Maya wants to share knowledge but struggles to be heard",
            "prejudice_theme": "Not prominent here",
            "tech_theme": "Technology as Maya's personal outlet",
            "family_theme": "Growing distance with Alex, busy but loving parents",
            "gov_theme": "Not introduced",
            "educational_elements": "Importance of communication in science"
        },
        # Add configurations for all other scenes here (example for brevity)
    }

    # Default config if scene not explicitly defined (expand this dictionary fully in practice)
    config = scene_configs.get(scene_name, {
        "setting": "Generic setting",
        "characters": "Maya Chen",
        "purpose": "Advance the plot",
        "character_details": "Generic details",
        "plot_details": "Generic plot advancement",
        "knowledge_theme": "Generic knowledge development",
        "prejudice_theme": "Generic prejudice challenge",
        "tech_theme": "Generic tech use",
        "family_theme": "Generic family interaction",
        "gov_theme": "Generic government context",
        "educational_elements": "Generic educational content"
    })

    prompt = BASE_PROMPT.format(
        word_count=word_count,
        chapter=chapter,
        scene_name=scene_name,
        setting=config["setting"],
        characters=config["characters"],
        purpose=config["purpose"],
        character_details=config["character_details"],
        plot_details=config["plot_details"],
        knowledge_theme=config["knowledge_theme"],
        prejudice_theme=config["prejudice_theme"],
        tech_theme=config["tech_theme"],
        family_theme=config["family_theme"],
        gov_theme=config["gov_theme"],
        educational_elements=config["educational_elements"]
    )

    try:
        response = client.chat.completions.create(
            model="grok-3",  # Hypothetical model name; replace with actual xAI model
            messages=[
                {"role": "system", "content": "You are a creative writer assisting with a novel draft."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=word_count * 2,  # Rough estimate: 2 tokens per word
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating scene {scene_name}: {e}")
        return f"Error: Scene {scene_name} could not be generated."


# Main function to write the draft
def write_novel_draft():
    with open("Code_for_Change_Draft.md", "w", encoding="utf-8") as f:
        f.write("# Code for Change: GroguGirl and the DOGE Audit\n\n")
        total_words = 0

        for chapter, scenes in CHAPTERS.items():
            f.write(f"## {chapter}\n\n")
            print(f"Generating {chapter}...")

            for scene in scenes:
                f.write(f"### {scene['name']}\n\n")
                scene_text = generate_scene(chapter, scene)
                f.write(f"{scene_text}\n\n")
                word_count = len(scene_text.split())
                total_words += word_count
                print(f"Generated {scene['name']} ({word_count} words)")
                time.sleep(1)  # Rate limiting to avoid overwhelming API

            f.write("\n")

        f.write(f"\nTotal Word Count: {total_words}\n")
        print(f"Draft completed. Total words: {total_words}")


if __name__ == "__main__":
    write_novel_draft()