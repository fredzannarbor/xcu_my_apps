#!/usr/bin/env python3
"""
Complete the missing 8 ideas (49-56) for Not a Miracle Readers
"""

import json
from pathlib import Path

# The 8 missing ideas - ensuring diversity in all dimensions
missing_ideas = [
    {
        "idea_number": 49,
        "title": "Podcast Mysteries",
        "protagonist": {
            "name": "Carlos Rivera",
            "age": 10,
            "background": "Latinx boy from a two-parent immigrant family in rural Texas, struggles with r-controlled vowels",
            "struggle": "Difficulty pronouncing and spelling r-controlled vowels (ar, er, ir, or, ur) due to language transfer from Spanish"
        },
        "contemporary_hook": "True crime and mystery podcast production for kids",
        "literacy_skill": "R-controlled vowels (ar, er, ir, or, ur)",
        "creative_integration": "Carlos creates a mystery podcast series where clues are hidden in r-controlled vowel patterns, helping him master these sounds through recording, editing, and scripting",
        "setting": {
            "primary": "Small town Texas with community radio station",
            "secondary": "Podcast studio in converted barn where sound waves visualize vowel patterns"
        },
        "character_arc": "Carlos avoids reading aloud due to vowel pronunciation struggles, discovers podcast editing allows him to practice privately, creates a hit mystery series using r-controlled vowels as clues, masters the sounds through repetition, and teaches younger students his podcast method",
        "unique_element": "The podcast microphone has a special filter that color-codes r-controlled vowels in the waveform, making invisible sounds visible",
        "pitch": "In rural Texas, 10-year-old Carlos Rivera turns his struggle with r-controlled vowels into podcast gold—when his mystery series uses 'ar', 'er', and 'or' sounds as secret clues, Carlos transforms from hesitant reader to confident broadcaster, proving that the right medium can unlock any literacy challenge."
    },
    {
        "idea_number": 50,
        "title": "Game Mod Genius",
        "protagonist": {
            "name": "Mei Zhang",
            "age": 9,
            "background": "Asian American girl raised by grandparents in suburban California, struggles with syllable division",
            "struggle": "Difficulty breaking words into syllables, making multi-syllabic words overwhelming to decode"
        },
        "contemporary_hook": "Roblox modding and custom game creation",
        "literacy_skill": "Syllable types and division patterns",
        "creative_integration": "Mei's game mods use syllable-based level design where each game world is structured by syllable patterns, teaching her to chunk words naturally",
        "setting": {
            "primary": "California suburban home with grandparents",
            "secondary": "Digital game world where platforms are syllable blocks that combine into words"
        },
        "character_arc": "Mei gets overwhelmed by long words in reading assignments, finds escape in game design, realizes her favorite games use syllable-based patterns, creates educational mods that teach syllable division, masters decoding through gameplay, and shares her mods with struggling readers nationwide",
        "unique_element": "Game characters can only jump the exact number of syllables in a word, making syllable counting a superpower",
        "pitch": "Nine-year-old Mei Zhang levels up her reading by modding Roblox games—when syllables become game mechanics and word-breaking becomes world-building, Mei transforms from overwhelmed decoder to game design guru, teaching thousands of kids that reading is just another game to master."
    },
    {
        "idea_number": 51,
        "title": "Digital Art Diaries",
        "protagonist": {
            "name": "Liam O'Connor",
            "age": 10,
            "background": "White boy from two moms in small town Maine, struggles with reading comprehension visualization",
            "struggle": "Difficulty creating mental images while reading, leading to poor comprehension and recall"
        },
        "contemporary_hook": "Procreate animation and digital illustration",
        "literacy_skill": "Reading comprehension through visualization strategies",
        "creative_integration": "Liam learns to draw scenes from books he reads, discovering that visual note-taking transforms his comprehension from weak to vivid",
        "setting": {
            "primary": "Coastal Maine town with lighthouse library",
            "secondary": "Digital sketchbook where illustrations come alive and interact with text"
        },
        "character_arc": "Liam reads words but retains nothing, feels frustrated and 'dumb', discovers digital art as his processing tool, creates animated book summaries that go viral, masters visualization comprehension, and teaches art-based reading strategies to his class",
        "unique_element": "His digital illustrations literally pull words off the page and transform them into animated scenes that replay the story",
        "pitch": "On the coast of Maine, 10-year-old Liam O'Connor can't picture what he reads—until Procreate turns words into worlds, and his animated book diaries become the ultimate comprehension tool, proving that some readers need to draw what they read to truly understand it."
    },
    {
        "idea_number": 52,
        "title": "Beat Maker's Dictionary",
        "protagonist": {
            "name": "Jasmine Williams",
            "age": 10,
            "background": "African American girl from two-parent middle-class family in suburban New Jersey, struggles with morphology",
            "struggle": "Difficulty understanding prefixes, suffixes, and root words, limiting vocabulary growth"
        },
        "contemporary_hook": "GarageBand music production and beat-making",
        "literacy_skill": "Morphology (prefixes, suffixes, root words)",
        "creative_integration": "Jasmine discovers that music production uses 'base tracks' (roots) with 'effects' (prefixes) and 'outros' (suffixes), mirroring word structure perfectly",
        "setting": {
            "primary": "Suburban New Jersey with community music center",
            "secondary": "Sound wave laboratory where word parts pulse like musical beats"
        },
        "character_arc": "Jasmine memorizes words without understanding their parts, struggles with new vocabulary, connects music production to word building, creates 'morphology beats' that teach word structure, masters vocabulary expansion, and produces an educational music album",
        "unique_element": "Each prefix, suffix, and root word has its own musical signature that combines into word symphonies",
        "pitch": "In suburban New Jersey, 10-year-old Jasmine Williams drops beats and drops knowledge—when prefixes become hooks and suffixes become outros, her morphology music videos teach vocabulary through rhythm, transforming word parts into chart-topping educational anthems."
    },
    {
        "idea_number": 53,
        "title": "Code Breaker's Quest",
        "protagonist": {
            "name": "Aiden Park",
            "age": 9,
            "background": "Asian American (Korean) boy from single mom household in urban Seattle, ADHD affecting reading fluency",
            "struggle": "ADHD makes sustained reading difficult; choppy, word-by-word reading lacks phrasing and expression"
        },
        "contemporary_hook": "Python coding and algorithm challenges",
        "literacy_skill": "Reading fluency (phrasing, expression, rate)",
        "creative_integration": "Aiden learns that code has rhythm and 'chunking' just like fluent reading—debugging requires reading code in meaningful phrases, not letter by letter",
        "setting": {
            "primary": "Urban Seattle apartment and coding bootcamp for kids",
            "secondary": "Virtual coding arena where programs flow like rivers of readable text"
        },
        "character_arc": "Aiden reads robotically, one word at a time, gets exhausted quickly, discovers coding requires 'code fluency' to debug efficiently, practices phrasing through programming, masters reading fluency via code patterns, and creates a fluency training app",
        "unique_element": "His programs only run when the code is 'read' with proper phrasing and expression—choppy reading causes syntax errors",
        "pitch": "In Seattle, 9-year-old Aiden Park debugs more than code—when programming teaches him to read in meaningful chunks instead of isolated words, his ADHD becomes his superpower, and fluency becomes just another algorithm to optimize."
    },
    {
        "idea_number": 54,
        "title": "Stop-Motion Stories",
        "protagonist": {
            "name": "Rosa Martinez",
            "age": 10,
            "background": "Latinx girl from grandmother-raised household in urban New York, English Language Learner struggling with vocabulary",
            "struggle": "Limited English vocabulary as an ELL student, uses context clues poorly"
        },
        "contemporary_hook": "Stop-motion animation and claymation storytelling",
        "literacy_skill": "Vocabulary development through context clues",
        "creative_integration": "Rosa's stop-motion films require her to build scenes that visually demonstrate word meanings, teaching context clue strategies through animation",
        "setting": {
            "primary": "New York City apartment with grandmother",
            "secondary": "Miniature film studio where clay characters act out word definitions"
        },
        "character_arc": "Rosa skips unknown words or guesses wildly, feels vocabulary-limited compared to peers, discovers stop-motion requires context-building for every scene, creates vocabulary animation series, masters context clue strategies, and teaches ELL students through her films",
        "unique_element": "Unknown words appear as blank clay figures that take shape only when Rosa builds the right context around them",
        "pitch": "In New York City, 10-year-old Rosa Martinez shapes more than clay—when stop-motion animation teaches her to build context around unknown words, her vocabulary films become viral ELL resources, proving that language learning is an art form anyone can sculpt."
    },
    {
        "idea_number": 55,
        "title": "Nature Doc Navigator",
        "protagonist": {
            "name": "Skylar Reed",
            "age": 9,
            "background": "White boy from farm family in rural Iowa, late bloomer with phonemic awareness gaps",
            "struggle": "Late reading development with weak phonemic awareness—struggles to manipulate sounds in words"
        },
        "contemporary_hook": "Wildlife photography and nature documentary creation (iPhone cinematography)",
        "literacy_skill": "Phonemic awareness (sound manipulation, blending, segmenting)",
        "creative_integration": "Skylar edits nature videos by 'splicing' sound clips—learning that audio editing mirrors phoneme blending and segmenting",
        "setting": {
            "primary": "Iowa farmland with diverse wildlife",
            "secondary": "Sound editing booth where animal calls break into phonemes that combine into words"
        },
        "character_arc": "Skylar feels 'behind' in reading, avoids phonics practice, finds passion in documenting farm wildlife, realizes documentary narration requires precise sound editing, masters phonemic manipulation through audio work, and creates nature literacy films for rural students",
        "unique_element": "Animal sounds in his documentaries break apart and recombine to teach phoneme manipulation—bird calls become blending practice",
        "pitch": "On an Iowa farm, 9-year-old Skylar Reed discovers that reading is like editing bird songs—when nature documentary creation teaches him to blend and segment sounds, his late-bloomer status becomes early-pioneer innovation, and phonics finally makes sense."
    },
    {
        "idea_number": 56,
        "title": "Recipe Revolution",
        "protagonist": {
            "name": "Zion Jackson",
            "age": 10,
            "background": "African American boy from single dad household in urban Chicago, dyslexia affecting written expression",
            "struggle": "Dyslexia makes organizing thoughts on paper extremely difficult—ideas are clear verbally but jumbled in writing"
        },
        "contemporary_hook": "Cooking content creation and recipe TikTok videos",
        "literacy_skill": "Written expression (organization and planning)",
        "creative_integration": "Zion learns that recipe writing has a clear structure (ingredients, steps, tips) that mirrors essay organization—his cooking videos teach writing through food",
        "setting": {
            "primary": "Chicago apartment kitchen with dad",
            "secondary": "Digital recipe lab where ingredients arrange themselves into organized paragraphs"
        },
        "character_arc": "Zion has great ideas but can't organize them on paper, gets frustrated with writing assignments, discovers recipe structure provides scaffolding, creates viral cooking-writing tutorials, masters essay organization through culinary arts, and teaches writing strategies through his recipe channel",
        "unique_element": "His recipes reorganize themselves into perfect essay structure—introduction (dish overview), body (steps), conclusion (serving suggestions)",
        "pitch": "In Chicago, 10-year-old Zion Jackson serves up more than meals—when TikTok recipes teach him essay structure and cooking shows him how to organize ideas on paper, his dyslexia becomes his unique flavor, and written expression becomes his secret ingredient."
    }
]

def main():
    # Load existing file
    file_path = Path("data/ideation/not_a_miracle_readers/ideas/all_128_ideas.json")
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Add missing ideas at correct positions
    current_ideas = data['ideas']

    # Find insertion point (should be after idea 48)
    insertion_index = None
    for i, idea in enumerate(current_ideas):
        if idea.get('idea_number') == 48:
            insertion_index = i + 1
            break

    if insertion_index is None:
        print("Error: Could not find idea 48")
        return

    # Insert the missing ideas
    for missing_idea in missing_ideas:
        current_ideas.insert(insertion_index, missing_idea)
        insertion_index += 1

    # Update metadata
    data['total_ideas'] = 128
    data['ideas'] = current_ideas

    # Save updated file
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✓ Successfully added 8 missing ideas (49-56)")
    print(f"✓ Updated total_ideas to 128")
    print(f"✓ File saved: {file_path}")

    # Verify
    idea_numbers = sorted([idea.get('idea_number') for idea in data['ideas'] if idea.get('idea_number')])
    print(f"\n✓ Verification: {len(idea_numbers)} ideas with numbers {idea_numbers[0]} to {idea_numbers[-1]}")

    # Check for gaps
    expected = set(range(1, 129))
    actual = set(idea_numbers)
    missing = expected - actual

    if missing:
        print(f"⚠ Still missing: {sorted(missing)}")
    else:
        print("✓ No gaps - all 128 ideas present!")

if __name__ == "__main__":
    main()
