Below is the completed Python script that generates the `scene_configs` dictionary for all 81 scenes in "Code for Change: GroguGirl and the DOGE Audit." I’ve continued from where the previous response left off, ensuring all scenes from Chapter 16 and the Epilogue are included, and maintaining consistency with the provided documents ("Detailed Scene-by-Scene Outline," "GroguGirl Character Profile," "Supporting Characters Profiles," "Thematic Elements Review and Refinement," and "Plot Arc and Key Scenes"). The script defines the full dictionary, which can be integrated into the novel-writing script previously provided.

### Completed Python Script

```python
# Script to generate scene_configs for "Code for Change: GroguGirl and the DOGE Audit"

# Character details from "GroguGirl Character Profile" and "Supporting Characters Profiles"
CHARACTER_DETAILS = {
    "Maya Chen (GroguGirl)": "12-year-old coder, analytical, curious, empathetic, struggles with explaining complex ideas, loves sci-fi and data visualization",
    "Alex Chen": "Maya's 24-year-old brother, data scientist at DOGE team, brilliant but intense, conflicted about work's impact",
    "Dr. Sophia Chen": "45-year-old medical researcher, brilliant, loving but distracted",
    "James Chen": "46-year-old high school science teacher, patient, encouraging",
    "Grandma Chen (Nai Nai)": "75-year-old family elder, wise, observant, tech-savvy",
    "Olivia Kim": "12-year-old, Maya's best friend, outgoing, artistic, curious",
    "Elon Musk": "Leader of DOGE team, charismatic, visionary, demanding but fair",
    "Dr. Leila Patel": "35-year-old Senior Data Ethics Officer, thoughtful, principled, diplomatic",
    "Jackson 'Jack' Williams": "26-year-old UX/UI Designer, creative, empathetic, practical",
    "Zoe Rodriguez": "22-year-old Junior Systems Analyst, enthusiastic, hardworking, sometimes overwhelmed",
    "Tyler Washington": "30-year-old Cybersecurity specialist, cautious, detail-oriented",
    "Director Marcus Thompson": "58-year-old government official, initially skeptical, knowledgeable",
    "Maria Gonzalez": "42-year-old government data clerk, hardworking, concerned about job security"
}

# Thematic progression stages (simplified from "Thematic Elements Review and Refinement")
THEMATIC_STAGES = {
    "Act 1 (Chapters 1-5)": {
        "knowledge": "Maya sees knowledge as personal achievement",
        "prejudice": "Gender bias in tech as others underestimate her",
        "tech": "Technology as a tool for personal expression",
        "family": "Growing distance with Alex, supported by parents",
        "gov": "Government as inefficient bureaucracy"
    },
    "Act 2 (Chapters 6-11)": {
        "knowledge": "Maya recognizes knowledge can serve different purposes",
        "prejudice": "Overcoming age and gender assumptions through competence",
        "tech": "Human costs of tech decisions become apparent",
        "family": "Conflict with Alex deepens then begins reconciliation",
        "gov": "Complexity of government systems understood"
    },
    "Act 3 (Chapters 12-16 + Epilogue)": {
        "knowledge": "Knowledge should be accessible to everyone",
        "prejudice": "Maya proves her worth, breaking barriers",
        "tech": "Technology serves human needs",
        "family": "Reconciliation and mature relationship with Alex",
        "gov": "Vision of collaborative citizen-government relationship"
    }
}

# Educational elements progression (from "Thematic Elements Review and Refinement")
EDUCATIONAL_PROGRESSION = {
    "Act 1": "Basics of data visualization (e.g., turning numbers into graphs), basic government structure",
    "Act 2": "Pattern recognition in datasets, departmental interactions, ethical dilemmas in tech",
    "Act 3": "Complex systems analysis, budgeting/resource allocation, ethical framework development"
}

# Function to determine act for a chapter
def get_act(chapter):
    if chapter.startswith("Chapter") and int(chapter.split()[1].split(":")[0]) <= 5:
        return "Act 1"
    elif chapter.startswith("Chapter") and 6 <= int(chapter.split()[1].split(":")[0]) <= 11:
        return "Act 2"
    else:
        return "Act 3"

# Scene configurations based on "Detailed Scene-by-Scene Outline"
scene_configs = {}

# Chapter 1: Introduction to GroguGirl
scene_configs["Maya's Bedroom Sanctuary"] = {
    "setting": "Maya's bedroom in a Northern Virginia suburb, filled with tech gadgets, astronomy posters, and sci-fi books",
    "characters": "Maya Chen (GroguGirl)",
    "purpose": "Introduce Maya's character, skills, and passion for data visualization",
    "character_details": CHARACTER_DETAILS["Maya Chen (GroguGirl)"],
    "plot_details": "Maya works on a data visualization project about local wildlife patterns using a self-modified coding platform, posts it online as 'GroguGirl,' showing frustration when forum members assume she's older or male.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["Family Dinner Tension"] = {
    "setting": "Chen family dining room",
    "characters": "Maya Chen, Dr. Sophia Chen, James Chen",
    "purpose": "Establish family dynamics and hint at distance with Alex",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Dr. Sophia Chen']}, {CHARACTER_DETAILS['James Chen']}",
    "plot_details": "Maya joins parents for dinner, Alex’s empty chair noticeable; parents discuss work, Maya tries to share her project but they’re distracted; Alex calls to say he can’t make it.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["School Day Challenges"] = {
    "setting": "Middle school science classroom",
    "characters": "Maya Chen, Olivia Kim",
    "purpose": "Show Maya's school life and social position",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Olivia Kim']}",
    "plot_details": "Maya excels in a science assignment, interacts with supportive Olivia; a male classmate dismisses her idea, but she solves it anyway; teacher suggests she work on explaining concepts.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["Late Night Message"] = {
    "setting": "Maya's bedroom at night",
    "characters": "Maya Chen",
    "purpose": "Introduce Alex’s involvement with DOGE",
    "character_details": CHARACTER_DETAILS["Maya Chen (GroguGirl)"],
    "plot_details": "Maya can’t sleep, works on coding; receives a message from Alex with a DOGE team article; researches and realizes Alex might be involved, feeling pride and concern.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["Weekend Rock Climbing"] = {
    "setting": "Indoor climbing gym",
    "characters": "Maya Chen",
    "purpose": "Show Maya’s problem-solving approach and decision to confront Alex",
    "character_details": CHARACTER_DETAILS["Maya Chen (GroguGirl)"],
    "plot_details": "Maya climbs, reflecting on Alex and DOGE; talks with instructor about breaking down problems; decides to ask Alex about his work.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

# Chapter 2: The DOGE Connection
scene_configs["Surprise Visit"] = {
    "setting": "Alex’s messy apartment with takeout containers and screens",
    "characters": "Maya Chen, Alex Chen",
    "purpose": "Reintroduce Alex and hint at his DOGE role",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Maya convinces parents to drive her to Alex’s; finds him exhausted, awkward reunion; he’s evasive but she spots a DOGE badge and confronts him.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["Reluctant Revelation"] = {
    "setting": "Alex’s apartment",
    "characters": "Maya Chen, Alex Chen",
    "purpose": "Reveal Alex’s DOGE role and mission",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Alex admits he’s on the DOGE team, explains using AI to audit government inefficiencies; excited but uneasy under Maya’s probing questions.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["Brother-Sister Bonding"] = {
    "setting": "Alex’s apartment",
    "characters": "Maya Chen, Alex Chen",
    "purpose": "Reestablish their connection",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Alex orders pizza, they talk comfortably; Maya shares her projects, Alex shows pride; they troubleshoot a coding problem together.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["The Late Night Conversation"] = {
    "setting": "Alex’s apartment at night",
    "characters": "Maya Chen, Alex Chen",
    "purpose": "Deepen understanding of DOGE and Maya’s potential",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Alex opens up about DOGE challenges, shows a visualization of redundant systems; Maya suggests an improvement, sparking Alex’s realization.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["The Invitation"] = {
    "setting": "Alex’s apartment, morning",
    "characters": "Maya Chen, Alex Chen",
    "purpose": "Set up Maya’s DOGE visit",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Alex impulsively invites Maya to DOGE headquarters for her school break; she’s thrilled but apprehensive; he calls to arrange clearance.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

# Chapter 3: An Unexpected Opportunity
scene_configs["Family Discussion"] = {
    "setting": "Chen family living room",
    "characters": "Maya Chen, Dr. Sophia Chen, James Chen",
    "purpose": "Show family reaction to the invitation",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Dr. Sophia Chen']}, {CHARACTER_DETAILS['James Chen']}",
    "plot_details": "Maya tells parents about Alex’s invite; mixed reactions—pride and concern; she argues for educational value, reaching a compromise for a limited visit.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["School Research Project"] = {
    "setting": "School library",
    "characters": "Maya Chen, Olivia Kim",
    "purpose": "Show Maya preparing for DOGE",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Olivia Kim']}",
    "plot_details": "Maya researches government structure; talks with librarian and Olivia; a classmate mocks her interest, she defends it with facts.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["Online Forums"] = {
    "setting": "Maya’s bedroom",
    "characters": "Maya Chen",
    "purpose": "Broaden Maya’s perspective on DOGE",
    "character_details": CHARACTER_DETAILS["Maya Chen (GroguGirl)"],
    "plot_details": "Maya browses tech forums about DOGE, finding mixed opinions; sees a government worker’s concern about job cuts, makes a question list.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["Conversation with Dad"] = {
    "setting": "Chen family home",
    "characters": "Maya Chen, James Chen",
    "purpose": "Provide government context",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['James Chen']}",
    "plot_details": "James explains government structure and history; encourages open-mindedness, gives Maya a notebook for observations.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["The Night Before"] = {
    "setting": "Maya’s bedroom",
    "characters": "Maya Chen, Alex Chen (via video call)",
    "purpose": "Build anticipation for DOGE visit",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Maya packs for the visit; Alex confirms details via call, seems stressed; she’s excited and nervous.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

# Chapter 4: First Day at DOGE
scene_configs["Arrival at Headquarters"] = {
    "setting": "Nondescript government building exterior",
    "characters": "Maya Chen, Alex Chen",
    "purpose": "Introduce DOGE environment",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Maya and Alex arrive, go through security; Alex is treated with respect and tension; Maya notes old building vs. new tech.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["The DOGE Workspace"] = {
    "setting": "DOGE team’s dedicated floor",
    "characters": "Maya Chen, Alex Chen, Jackson 'Jack' Williams",
    "purpose": "Show DOGE team dynamics",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}, {CHARACTER_DETAILS['Jackson \'Jack\' Williams']}",
    "plot_details": "Alex shows Maya the open workspace with screens and data; introduces Jack, who connects with her; she notes the intense atmosphere.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["Meeting Zoe"] = {
    "setting": "DOGE workspace",
    "characters": "Maya Chen, Zoe Rodriguez, Jackson 'Jack' Williams",
    "purpose": "Introduce Zoe and tech challenges",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Zoe Rodriguez']}, {CHARACTER_DETAILS['Jackson \'Jack\' Williams']}",
    "plot_details": "Jack introduces Zoe, who shows Maya her workstation; they discuss being young women in tech, Zoe shares a story of her idea being misattributed.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["The Data Center Tour"] = {
    "setting": "DOGE data processing center",
    "characters": "Maya Chen, Alex Chen, Tyler Washington",
    "purpose": "Show scale of DOGE tech",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}, {CHARACTER_DETAILS['Tyler Washington']}",
    "plot_details": "Alex takes Maya to see servers; Tyler gives a security overview; Maya asks a smart question, impressing them.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["The Unexpected Encounter"] = {
    "setting": "DOGE conference room",
    "characters": "Maya Chen, Alex Chen, Elon Musk",
    "purpose": "Introduce Musk and leadership dynamics",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}, {CHARACTER_DETAILS['Elon Musk']}",
    "plot_details": "Maya accidentally enters a meeting, sees Musk arguing with leaders; Alex retrieves her, Musk comments dismissively; she’s intrigued.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

# Chapter 5: Understanding the Mission
scene_configs["Morning Briefing"] = {
    "setting": "DOGE team meeting room",
    "characters": "Maya Chen, Alex Chen, Dr. Leila Patel",
    "purpose": "Show team goals and ethical tension",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}, {CHARACTER_DETAILS['Dr. Leila Patel']}",
    "plot_details": "Maya observes a briefing; leaders report progress, Patel raises ethical concerns about Education Department; Alex explains structure.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["Data Visualization Lab"] = {
    "setting": "DOGE visualization lab",
    "characters": "Maya Chen, Jackson 'Jack' Williams",
    "purpose": "Show Maya contributing",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Jackson \'Jack\' Williams']}",
    "plot_details": "Jack shows Maya his work translating data; she suggests an improvement, he incorporates it; she feels a sense of belonging.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["Lunch with Dr. Patel"] = {
    "setting": "DOGE cafeteria",
    "characters": "Maya Chen, Dr. Leila Patel",
    "purpose": "Introduce ethical considerations",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Dr. Leila Patel']}",
    "plot_details": "Alex leaves Maya with Patel; they discuss ethics and balancing efficiency with impact; Patel shares a past tech mistake.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["The Government Liaison"] = {
    "setting": "DOGE headquarters hallway",
    "characters": "Maya Chen, Director Marcus Thompson",
    "purpose": "Introduce government perspective",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Director Marcus Thompson']}",
    "plot_details": "Maya meets Thompson, who’s dismissive; she asks about department history, surprising him; he shares old charts and a personal story.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

scene_configs["End of Day Reflection"] = {
    "setting": "Car ride from DOGE headquarters",
    "characters": "Maya Chen, Alex Chen",
    "purpose": "Show Maya’s growing concerns",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Maya shares her day’s observations; Alex explains pressure for savings; she worries about rushing, tension builds as he defends the timeline.",
    "knowledge_theme": THEMATIC_STAGES["Act 1"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 1"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 1"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 1"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 1"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 1"]
}

# Chapter 6: Family Tensions
scene_configs["Weekend Family Gathering"] = {
    "setting": "Chen family dining room",
    "characters": "Maya Chen, Alex Chen, Dr. Sophia Chen, James Chen, Grandma Chen",
    "purpose": "Highlight family strain",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}, {CHARACTER_DETAILS['Dr. Sophia Chen']}, {CHARACTER_DETAILS['James Chen']}, {CHARACTER_DETAILS['Grandma Chen (Nai Nai)']}",
    "plot_details": "Family dinner with Grandma; Alex arrives late, exhausted; parents question his work, tense talk about balance.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["Kitchen Conversation"] = {
    "setting": "Chen family kitchen",
    "characters": "Maya Chen, Grandma Chen",
    "purpose": "Provide wisdom and perspective",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Grandma Chen (Nai Nai)']}",
    "plot_details": "Maya and Grandma wash dishes; Grandma shares insights on systems and change, encouraging Maya to find connections.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["Backyard Confrontation"] = {
    "setting": "Chen family backyard",
    "characters": "Maya Chen, Alex Chen",
    "purpose": "Deepen sibling conflict",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Maya confronts Alex about his changes; he reveals pressure from Musk; they argue about ends vs. means, he dismisses her.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["Late Night Research"] = {
    "setting": "Maya’s bedroom",
    "characters": "Maya Chen",
    "purpose": "Show Maya’s initiative",
    "character_details": CHARACTER_DETAILS["Maya Chen (GroguGirl)"],
    "plot_details": "Upset, Maya researches government reforms, finds patterns of failure; creates a visualization of reform outcomes.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["Breakfast Reconciliation"] = {
    "setting": "Chen family kitchen",
    "characters": "Maya Chen, Alex Chen, Grandma Chen",
    "purpose": "Begin reconciliation",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}, {CHARACTER_DETAILS['Grandma Chen (Nai Nai)']}",
    "plot_details": "Awkward breakfast; Grandma facilitates talk; Maya shows research, Alex acknowledges points, invites her back to DOGE.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

# Chapter 7: Making Discoveries
scene_configs["Return to DOGE"] = {
    "setting": "DOGE headquarters",
    "characters": "Maya Chen, Alex Chen, Zoe Rodriguez",
    "purpose": "Show increased tension",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}, {CHARACTER_DETAILS['Zoe Rodriguez']}",
    "plot_details": "Maya returns with Alex, notices tense atmosphere; Alex assigns her to Zoe; she overhears departments resisting audit.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["Data Deep Dive"] = {
    "setting": "DOGE workspace",
    "characters": "Maya Chen, Zoe Rodriguez",
    "purpose": "Show Maya’s analytical skills",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Zoe Rodriguez']}",
    "plot_details": "Zoe shows Maya Transportation data; Maya spots a communication-efficiency pattern Zoe missed, impressing her.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["The Pattern Recognition"] = {
    "setting": "DOGE meeting room",
    "characters": "Maya Chen, Zoe Rodriguez, Dr. Leila Patel",
    "purpose": "Validate Maya’s insight",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Zoe Rodriguez']}, {CHARACTER_DETAILS['Dr. Leila Patel']}",
    "plot_details": "Team discusses Maya’s find; some dismiss it, Patel defends it; Maya gains confidence despite mixed reception.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["Lunch with Jack"] = {
    "setting": "DOGE cafeteria",
    "characters": "Maya Chen, Jackson 'Jack' Williams",
    "purpose": "Strengthen allyship",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Jackson \'Jack\' Williams']}",
    "plot_details": "Jack discusses team politics with Maya, encourages her pattern-finding; shares his credibility journey.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["The Breakthrough"] = {
    "setting": "DOGE visualization lab",
    "characters": "Maya Chen, Alex Chen",
    "purpose": "Highlight Maya’s growing role",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Maya connects datasets, creates a budget-efficiency prototype; Alex sees it, takes her to present to leaders.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

# Chapter 8: A Mistake with Consequences
scene_configs["The Celebration"] = {
    "setting": "DOGE workspace",
    "characters": "Maya Chen, Tyler Washington",
    "purpose": "Show initial success",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Tyler Washington']}",
    "plot_details": "Team celebrates Maya’s insight with pizza; she overhears Tyler discuss accelerating timeline based on her find, feeling uneasy.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["Department Visit Preparation"] = {
    "setting": "DOGE headquarters",
    "characters": "Maya Chen, Dr. Leila Patel",
    "purpose": "Prepare for real-world impact",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Dr. Leila Patel']}",
    "plot_details": "Team preps for Housing visit; Maya’s invited, Patel explains sensitivity; Maya learns of restructuring plans.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["The Department Visit"] = {
    "setting": "Department of Housing and Urban Development",
    "characters": "Maya Chen, Maria Gonzalez",
    "purpose": "Show government workers’ perspective",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Maria Gonzalez']}",
    "plot_details": "Team visits Housing; tense atmosphere; Maria shows Maya operations, revealing data discrepancies.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["The Discovery of Error"] = {
    "setting": "Department of Housing",
    "characters": "Maya Chen, Alex Chen, Maria Gonzalez",
    "purpose": "Reveal DOGE mistake",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}, {CHARACTER_DETAILS['Maria Gonzalez']}",
    "plot_details": "Maya spots a seasonal program error in data; Alex dismisses it, Maria gets emotional about its importance.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["The Human Impact"] = {
    "setting": "Department of Housing",
    "characters": "Maya Chen, Alex Chen, Maria Gonzalez",
    "purpose": "Show consequences of error",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}, {CHARACTER_DETAILS['Maria Gonzalez']}",
    "plot_details": "Maria shows Maya families helped by the program; Maya confronts Alex about cutting it, they argue heatedly.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

# Chapter 9: Taking Initiative
scene_configs["Morning Reflection"] = {
    "setting": "Maya’s bedroom",
    "characters": "Maya Chen, Dr. Sophia Chen, James Chen",
    "purpose": "Process the error",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Dr. Sophia Chen']}, {CHARACTER_DETAILS['James Chen']}",
    "plot_details": "Maya diagrams Maria’s lessons; parents notice her distraction, encourage her to speak up despite resistance.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["Approaching Dr. Patel"] = {
    "setting": "DOGE headquarters",
    "characters": "Maya Chen, Dr. Leila Patel",
    "purpose": "Seek ethical support",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Dr. Leila Patel']}",
    "plot_details": "Maya shares the housing error with Patel; they review data, Patel agrees to raise it with leaders.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["The Dismissal"] = {
    "setting": "DOGE meeting room",
    "characters": "Maya Chen, Alex Chen, Dr. Leila Patel",
    "purpose": "Show team resistance",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}, {CHARACTER_DETAILS['Dr. Leila Patel']}",
    "plot_details": "Maya presents findings; leaders dismiss it as minor, Alex doesn’t support her; she’s devastated.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["Conversation with Director Thompson"] = {
    "setting": "DOGE hallway",
    "characters": "Maya Chen, Director Marcus Thompson",
    "purpose": "Gain unexpected ally",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Director Marcus Thompson']}",
    "plot_details": "Thompson asks about Maya’s distress; she explains, he shares concerns and a past reform failure, suggests looking at data collection.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["The Initiative"] = {
    "setting": "DOGE headquarters late at night",
    "characters": "Maya Chen, Jackson 'Jack' Williams",
    "purpose": "Show Maya taking action",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Jackson \'Jack\' Williams']}",
    "plot_details": "Maya creates a tool to flag human impact; Jack helps, they develop a prototype without approval.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

# Chapter 10: Building Bridges
scene_configs["The Unofficial Project"] = {
    "setting": "DOGE headquarters after hours",
    "characters": "Maya Chen, Jackson 'Jack' Williams, Zoe Rodriguez, Dr. Leila Patel, Director Marcus Thompson",
    "purpose": "Collaborate on solution",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Jackson \'Jack\' Williams']}, {CHARACTER_DETAILS['Zoe Rodriguez']}, {CHARACTER_DETAILS['Dr. Leila Patel']}, {CHARACTER_DETAILS['Director Marcus Thompson']}",
    "plot_details": "Maya leads a group to develop her tool; Patel adds ethics, Thompson secretly provides data.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["Reconnecting with Alex"] = {
    "setting": "Alex’s apartment",
    "characters": "Maya Chen, Alex Chen",
    "purpose": "Begin repairing relationship",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Maya brings Alex takeout; they talk awkwardly, she asks about his motives; they reconnect over shared values.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["Field Research"] = {
    "setting": "Various government departments",
    "characters": "Maya Chen, Jackson 'Jack' Williams",
    "purpose": "Gather real-world data",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Jackson \'Jack\' Williams']}",
    "plot_details": "Maya and Jack visit departments, interview workers; she collects stories, gaining nuance.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["The Pattern Emerges"] = {
    "setting": "DOGE headquarters",
    "characters": "Maya Chen, Jackson 'Jack' Williams",
    "purpose": "Develop transparency idea",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Jackson \'Jack\' Williams']}",
    "plot_details": "Maya finds transparent data improves performance; develops an open data platform concept, Jack refines it.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["The Ally Recruitment"] = {
    "setting": "DOGE headquarters",
    "characters": "Maya Chen, Tyler Washington",
    "purpose": "Build support network",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Tyler Washington']}",
    "plot_details": "Maya convinces Tyler with security benefits of transparency; he joins after initial resistance, shares his story.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

# Chapter 11: The Big Presentation
scene_configs["Preparation Pressure"] = {
    "setting": "DOGE headquarters",
    "characters": "Maya Chen, Jackson 'Jack' Williams, Zoe Rodriguez, Dr. Leila Patel",
    "purpose": "Prepare for presentation",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Jackson \'Jack\' Williams']}, {CHARACTER_DETAILS['Zoe Rodriguez']}, {CHARACTER_DETAILS['Dr. Leila Patel']}",
    "plot_details": "Maya and allies prep their transparency pitch, nervous about discovery; Patel coaches, Jack refines visuals.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["The Discovery"] = {
    "setting": "DOGE headquarters",
    "characters": "Maya Chen, Jackson 'Jack' Williams, Zoe Rodriguez, Dr. Leila Patel",
    "purpose": "Face consequences of secrecy",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Jackson \'Jack\' Williams']}, {CHARACTER_DETAILS['Zoe Rodriguez']}, {CHARACTER_DETAILS['Dr. Leila Patel']}",
    "plot_details": "Leader finds their project; confronts them, Patel defends it; they compromise on a small presentation.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["Small Group Presentation"] = {
    "setting": "DOGE meeting room",
    "characters": "Maya Chen, Alex Chen",
    "purpose": "Test transparency idea",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Maya presents to a small group including Alex, showing platform with housing example; mixed reception.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["Alex's Reaction"] = {
    "setting": "DOGE hallway",
    "characters": "Maya Chen, Alex Chen",
    "purpose": "Strengthen sibling bond",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Alex is impressed but worried; Maya pushes his original motives, he admits feeling lost, agrees to help.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

scene_configs["The Opportunity"] = {
    "setting": "Maya’s bedroom",
    "characters": "Maya Chen, Alex Chen (via call)",
    "purpose": "Set up big presentation",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Alex arranges a leadership briefing with Musk; Maya preps intensely, excited and terrified.",
    "knowledge_theme": THEMATIC_STAGES["Act 2"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 2"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 2"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 2"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 2"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 2"]
}

# Chapter 12: Facing Resistance
scene_configs["The Leadership Briefing"] = {
    "setting": "DOGE leadership meeting room",
    "characters": "Maya Chen, Alex Chen, Elon Musk",
    "purpose": "Introduce high stakes",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}, {CHARACTER_DETAILS['Elon Musk']}",
    "plot_details": "Maya attends a briefing, nervous; observes dynamics, Alex supports her as she waits to present.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

scene_configs["The Presentation"] = {
    "setting": "DOGE leadership meeting room",
    "characters": "Maya Chen, Elon Musk",
    "purpose": "Present transparency platform",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Elon Musk']}",
    "plot_details": "Maya presents well until Musk’s skeptical questions fluster her; mixed reception, Musk noncommittal.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

scene_configs["The Aftermath"] = {
    "setting": "DOGE hallway",
    "characters": "Maya Chen, Alex Chen",
    "purpose": "Process presentation",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Maya’s disappointed, Alex encourages her; team reactions split, she resolves to improve.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

scene_configs["The Opposition"] = {
    "setting": "DOGE headquarters",
    "characters": "Maya Chen, Alex Chen",
    "purpose": "Reveal resistance",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Maya overhears opposition to transparency; confronts Alex, who’s torn between team and her idea.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

scene_configs["The Strategy Session"] = {
    "setting": "DOGE headquarters",
    "characters": "Maya Chen, Dr. Leila Patel, Director Marcus Thompson, Jackson 'Jack' Williams",
    "purpose": "Plan next steps",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Dr. Leila Patel']}, {CHARACTER_DETAILS['Director Marcus Thompson']}, {CHARACTER_DETAILS['Jackson \'Jack\' Williams']}",
    "plot_details": "Maya regroups with allies; Patel and Thompson suggest a pilot, Jack refines it; they plan to prove it with results.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

# Chapter 13: A New Approach
scene_configs["The Pilot Proposal"] = {
    "setting": "DOGE headquarters",
    "characters": "Maya Chen, Alex Chen, Tyler Washington",
    "purpose": "Propose pilot",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}, {CHARACTER_DETAILS['Tyler Washington']}",
    "plot_details": "Maya drafts a Transportation pilot with Alex and Tyler’s help; submits it officially.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

scene_configs["Conversation with Grandma Chen"] = {
    "setting": "Grandparents’ house",
    "characters": "Maya Chen, Grandma Chen",
    "purpose": "Gain perspective",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Grandma Chen (Nai Nai)']}",
    "plot_details": "Maya shares struggles; Grandma tells a story of village change via info sharing, gives her a jade pendant.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

scene_configs["The Unexpected Advocate"] = {
    "setting": "DOGE headquarters",
    "characters": "Maya Chen, Director Marcus Thompson",
    "purpose": "Gain support",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Director Marcus Thompson']}",
    "plot_details": "Thompson advocates for pilot; it’s approved with constraints; Maya’s excited but daunted.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

scene_configs["Building the Pilot"] = {
    "setting": "DOGE headquarters",
    "characters": "Maya Chen, Jackson 'Jack' Williams",
    "purpose": "Develop pilot",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Jackson \'Jack\' Williams']}",
    "plot_details": "Montage of Maya and Jack coding, testing, and collaborating with Transportation staff; confidence grows.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

scene_configs["Reconciliation with Alex"] = {
    "setting": "DOGE headquarters late at night",
    "characters": "Maya Chen, Alex Chen",
    "purpose": "Fully reconcile",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Alex brings dinner, apologizes; shares disillusionment, joins pilot; they work together like old times.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

# Chapter 14: Testing the Solution
scene_configs["Pilot Launch Day"] = {
    "setting": "Transportation Department",
    "characters": "Maya Chen",
    "purpose": "Launch pilot",
    "character_details": CHARACTER_DETAILS["Maya Chen (GroguGirl)"],
    "plot_details": "Ceremony launches pilot; staff are nervous, Maya demos features; glitch resolved, launch succeeds.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

scene_configs["User Feedback"] = {
    "setting": "Transportation Department",
    "characters": "Maya Chen, Maria Gonzalez",
    "purpose": "Assess pilot use",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Maria Gonzalez']}",
    "plot_details": "Maya observes staff using platform, collects feedback; Maria visits, offers user perspective.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

scene_configs["The Unexpected Result"] = {
    "setting": "DOGE headquarters",
    "characters": "Maya Chen",
    "purpose": "Show transparency’s impact",
    "character_details": CHARACTER_DETAILS["Maya Chen (GroguGirl)"],
    "plot_details": "Citizens find a funding discrepancy via platform; media reports it, leaders worry, Maya fears shutdown.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

scene_configs["Crisis Management"] = {
    "setting": "DOGE meeting room",
    "characters": "Maya Chen",
    "purpose": "Defend transparency",
    "character_details": CHARACTER_DETAILS["Maya Chen (GroguGirl)"],
    "plot_details": "Emergency meeting; some want to restrict access, Maya argues it’s working; compromise to monitor.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

scene_configs["The Validation"] = {
    "setting": "DOGE headquarters",
    "characters": "Maya Chen",
    "purpose": "Prove pilot success",
    "character_details": CHARACTER_DETAILS["Maya Chen (GroguGirl)"],
    "plot_details": "Month into pilot, efficiency improves; staff proactive, public engaged; Maya reports, Musk requests briefing.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

# Chapter 15: Presenting to Leadership
scene_configs["Preparation with Allies"] = {
    "setting": "DOGE headquarters",
    "characters": "Maya Chen, Dr. Leila Patel, Jackson 'Jack' Williams, Alex Chen, Director Marcus Thompson",
    "purpose": "Prep for final pitch",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Dr. Leila Patel']}, {CHARACTER_DETAILS['Jackson \'Jack\' Williams']}, {CHARACTER_DETAILS['Alex Chen']}, {CHARACTER_DETAILS['Director Marcus Thompson']}",
    "plot_details": "Team preps presentation; Patel frames ethics, Jack refines visuals, Alex coaches, Thompson advises.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

scene_configs["Pre-Presentation Nerves"] = {
    "setting": "Maya’s bedroom",
    "characters": "Maya Chen, Alex Chen",
    "purpose": "Build tension",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Maya’s nervous; Alex gives a pep talk, she uses Grandma’s pendant for courage, reviews points.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

scene_configs["The Comprehensive Presentation"] = {
    "setting": "DOGE leadership meeting room",
    "characters": "Maya Chen, Elon Musk",
    "purpose": "Pitch to leadership",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Elon Musk']}",
    "plot_details": "Maya presents pilot results confidently with data and testimonials; Musk asks thoughtful questions.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

scene_configs["The Challenge"] = {
    "setting": "DOGE leadership meeting room",
    "characters": "Maya Chen, Elon Musk",
    "purpose": "Face Musk’s skepticism",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Elon Musk']}",
    "plot_details": "Musk questions government adoption, suggests DOGE control; Maya argues for democratic access, tense standoff.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

scene_configs["The Decision"] = {
    "setting": "DOGE leadership meeting room",
    "characters": "Maya Chen, Elon Musk",
    "purpose": "Resolve pilot’s fate",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Elon Musk']}",
    "plot_details": "Musk approves platform with modifications; Maya’s thrilled but concerned about compromises.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

# Chapter 16: The Path Forward
scene_configs["Implementation Planning"] = {
    "setting": "DOGE headquarters",
    "characters": "Maya Chen, Alex Chen",
    "purpose": "Plan platform rollout",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}",
    "plot_details": "Maya’s a special advisor, plans expansion with Alex; navigates bureaucracy, grows confident.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

scene_configs["Family Celebration"] = {
    "setting": "Chen family dining room",
    "characters": "Maya Chen, Alex Chen, Dr. Sophia Chen, James Chen, Grandma Chen",
    "purpose": "Celebrate success and family reconnection",
    "character_details": f"{CHARACTER_DETAILS['Maya Chen (GroguGirl)']}, {CHARACTER_DETAILS['Alex Chen']}, {CHARACTER_DETAILS['Dr. Sophia Chen']}, {CHARACTER_DETAILS['James Chen']}, {CHARACTER_DETAILS['Grandma Chen (Nai Nai)']}",
    "plot_details": "Family celebrates Maya and Alex’s achievements; parents express pride, Alex is relaxed, Grandma teases about the jade pendant.",
    "knowledge_theme": THEMATIC_STAGES["Act 3"]["knowledge"],
    "prejudice_theme": THEMATIC_STAGES["Act 3"]["prejudice"],
    "tech_theme": THEMATIC_STAGES["Act 3"]["tech"],
    "family_theme": THEMATIC_STAGES["Act 3"]["family"],
    "gov_theme": THEMATIC_STAGES["Act 3"]["gov"],
    "educational_elements": EDUCATIONAL_PROGRESSION["Act 3"]
}

scene_configs["School Presentation"] = {
    "setting": "Middle school science classroom",
    "characters": "Maya Chen, Olivia Kim",
    "purpose": "Show Maya’s growth in communication