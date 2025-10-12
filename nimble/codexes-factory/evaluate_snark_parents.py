#!/usr/bin/env python3
"""
Generate 80 diverse parent evaluations of "The Hunting of the Snark" by Lewis Carroll.
Evaluates from 4 archetypes: Literary, Practical, Modern, and Nostalgic parents.
"""

import json
import os
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from codexes.core.llm_integration import CodexesLLMIntegration
except ImportError:
    try:
        from src.codexes.core.llm_integration import CodexesLLMIntegration
    except ImportError:
        print("Error: Could not import CodexesLLMIntegration")
        exit(1)


# Book context for evaluations
BOOK_CONTEXT = """
Title: The Hunting of the Snark: An Agony in Eight Fits
Author: Lewis Carroll (Alice in Wonderland author)
Genre: Classic nonsense poetry / Fantasy
Format: Narrative poem in verse (8 "fits" or sections)
Target Age: 9-12 years old
Publication: 1876

CONTENT SUMMARY:
A Victorian-era nonsense poem about absurd characters (Bellman, Baker, Beaver, Butcher,
Banker, Barrister, etc.) hunting a mythical Snark creature using ridiculous methods.

KEY CHARACTERISTICS:
- Filled with wordplay, invented words ("frumious," "galumphing"), and whimsical logic
- Connected to "Jabberwocky" with similar linguistic playfulness
- Absurdist humor and illogical scenarios
- Mathematical jokes and Victorian cultural references
- Dark ending: the Baker vanishes when the Snark turns out to be a "Boojum"
- Victorian language and outdated cultural references (bathing-machines, railway-shares)
- All male characters with Victorian occupations
- No diverse representation
- Abstract concepts and existential themes

POTENTIAL CONCERNS:
- Victorian language may be difficult for modern children
- Lack of diversity in characters
- Abstract, nonsensical plot with no clear moral
- Dark/unsettling ending (character vanishes)
- May require significant adult explanation

POTENTIAL STRENGTHS:
- Classic literature exposure
- Language creativity and wordplay
- Encourages imagination and appreciation for absurdist humor
- Connection to beloved Alice in Wonderland author
- Poetry format offers rhythmic reading experience
- Unique and memorable linguistic inventions
"""


def create_parent_personas():
    """Create 80 diverse parent personas across 4 archetypes."""

    personas = []

    # LITERARY PARENT personas (20)
    literary_parents = [
        {"name": "Professor Catherine", "details": "PhD in English Literature, homeschools, values canonical texts, teaches kids etymology"},
        {"name": "Librarian Marcus", "details": "Children's librarian, curates reading lists, believes in age-appropriate classics"},
        {"name": "Writer Sophia", "details": "Published author, wants kids exposed to great writing, values linguistic creativity"},
        {"name": "Teacher James", "details": "Middle school English teacher, focuses on poetry analysis, loves wordplay"},
        {"name": "Classics Enthusiast Rachel", "details": "Studied comparative literature, reads to kids nightly, maintains family book club"},
        {"name": "Poet David", "details": "Performance poet, values rhythm and sound in language, wants kids to love poetry"},
        {"name": "Editor Michelle", "details": "Book editor, analytical about children's literature quality, high standards"},
        {"name": "Academic Aisha", "details": "Children's literature researcher, knows developmental reading stages, evidence-based"},
        {"name": "Bookstore Owner Tom", "details": "Independent bookstore owner, knows classics sell, values literary heritage"},
        {"name": "Literary Critic Elena", "details": "Reviews children's books, appreciates Victorian literature, concerned about accessibility"},
        {"name": "Shakespeare Teacher Robert", "details": "High school drama teacher, loves language play, wants early exposure to complex texts"},
        {"name": "Linguist Dr. Patel", "details": "Studies language acquisition, fascinated by portmanteau words, sees educational value"},
        {"name": "Book Club Leader Sarah", "details": "Runs mother-daughter book club, values discussion-worthy texts, classic literature advocate"},
        {"name": "Historian Margaret", "details": "Victorian era specialist, appreciates historical context, worried about dated references"},
        {"name": "Poetry Slam Coach Andre", "details": "Teaches performance poetry, values rhythm and memorization, appreciates Carroll's meter"},
        {"name": "Children's Lit Professor Kim", "details": "University professor, knows canon intimately, debates age-appropriateness of classics"},
        {"name": "Translation Scholar Yuki", "details": "Studies how texts work across languages, appreciates Carroll's linguistic innovation"},
        {"name": "Reading Specialist Dr. Chen", "details": "Specializes in gifted readers, pushes for challenging material, vocabulary builder"},
        {"name": "Storytelling Coach Maria", "details": "Professional storyteller, loves oral tradition, appreciates memorizable verse"},
        {"name": "Literary Magazine Editor Josh", "details": "Publishes children's writing, values exposure to experimental forms, worried about engagement"}
    ]

    # PRACTICAL PARENT personas (20)
    practical_parents = [
        {"name": "Engineer Parent Alison", "details": "STEM-focused, wants clear educational value, prefers books with lessons or information"},
        {"name": "Business Mom Jennifer", "details": "Busy professional, needs engaging books that hold attention, values time efficiency"},
        {"name": "Teacher Dad Mike", "details": "Elementary teacher, knows what kids actually enjoy, concerned about comprehension level"},
        {"name": "Pediatrician Laura", "details": "Focuses on age-appropriate development, worried about confusing content for 9-12 year olds"},
        {"name": "Coach Parent Derek", "details": "Values character building and clear morals, prefers books with life lessons"},
        {"name": "Working Mom Priya", "details": "Limited reading time, wants books kids can read independently without constant explanation"},
        {"name": "School Principal Karen", "details": "Knows curriculum standards, wants books that support literacy development"},
        {"name": "Budget-Conscious Dad Rick", "details": "Considers cost vs. value, wants books kids will actually read multiple times"},
        {"name": "Homeschool Mom Beth", "details": "Needs books that work for multiple ages, wants clear educational outcomes"},
        {"name": "PTA President Lisa", "details": "Involved in school reading programs, knows what books circulate well in libraries"},
        {"name": "Single Parent Jamal", "details": "Time-strapped, needs independently engaging books, values clear comprehension"},
        {"name": "Speech Therapist Nicole", "details": "Concerned about reading level appropriateness, vocabulary accessibility"},
        {"name": "Reading Tutor Stephen", "details": "Works with struggling readers, worried about Victorian language barriers"},
        {"name": "Occupational Therapist Amy", "details": "Considers sensory aspects of reading, attention span concerns"},
        {"name": "Educational Consultant Dan", "details": "Evaluates learning materials professionally, needs measurable educational benefits"},
        {"name": "Accountant Mom Vanessa", "details": "Practical mindset, questions value of nonsense over informational texts"},
        {"name": "School Counselor Troy", "details": "Concerned about emotional impact of dark ending, age-appropriateness of themes"},
        {"name": "Nurse Parent Diane", "details": "Busy schedule, wants books that kids enjoy enough to finish, engagement is key"},
        {"name": "IT Dad Carlos", "details": "Tech-savvy, wonders if Victorian poetry competes with modern entertainment"},
        {"name": "Project Manager Mom Hannah", "details": "Results-oriented, wants clear outcomes from reading choices, questions ROI of classics"}
    ]

    # MODERN PARENT personas (20)
    modern_parents = [
        {"name": "Diversity Advocate Keisha", "details": "Prioritizes diverse representation, concerned about all-male Victorian cast"},
        {"name": "Progressive Dad Sam", "details": "Values contemporary stories with modern values, questions relevance of 1876 text"},
        {"name": "Social Justice Mom Tara", "details": "Wants books that reflect current social awareness, concerned about colonial-era content"},
        {"name": "Millennial Parent Alex", "details": "Prefers contemporary diverse authors, questions why teach Victorian white male poet"},
        {"name": "Inclusive Education Mom Jessica", "details": "Seeks representation for all kids, worried about lack of female or POC characters"},
        {"name": "Gen Z Parent Taylor", "details": "Values authenticity and relevance, skeptical of 'because it's a classic' arguments"},
        {"name": "Feminist Mom Rebecca", "details": "Questions all-male cast, wants strong female characters, concerned about gender representation"},
        {"name": "Urban Parent Malik", "details": "Kids grow up in diverse environment, wants books reflecting modern reality"},
        {"name": "Tech Industry Dad Wei", "details": "Future-focused, questions value of Victorian text for 21st century kids"},
        {"name": "Environmental Activist Mom Grace", "details": "Wants books with contemporary relevant themes, questions colonial-era hunting narrative"},
        {"name": "LGBTQ+ Parent Jordan", "details": "Prioritizes inclusive representation, Victorian heteronormative content concerns"},
        {"name": "Multicultural Family Mom Amara", "details": "Biracial family, wants diverse characters, concerned about Eurocentric classics"},
        {"name": "Contemporary Fiction Advocate Luis", "details": "Believes modern authors better serve today's kids, questions canon's continued relevance"},
        {"name": "Media Literacy Mom Nora", "details": "Wants books teaching critical thinking about modern issues, Victorian text seems dated"},
        {"name": "Anti-Racist Parent Cameron", "details": "Actively decolonizing bookshelf, questions prioritizing Victorian white authors"},
        {"name": "Disability Advocate Dad Peter", "details": "Wants disability representation, concerned about Victorian ableist language"},
        {"name": "Body Positive Mom Zoe", "details": "Concerned about Victorian-era attitudes, wants affirming modern content"},
        {"name": "Global Citizen Parent Fatima", "details": "Wants books featuring diverse cultures, British Victorian text seems limited"},
        {"name": "Social Media Savvy Dad Tyler", "details": "Kids influenced by diverse online content, Victorian classics feel disconnected"},
        {"name": "Progressive School Mom Emma", "details": "Kids attend diverse urban school, wants reading to reflect their world"}
    ]

    # NOSTALGIC PARENT personas (20)
    nostalgic_parents = [
        {"name": "Grandparent Barbara", "details": "Read Carroll to her kids, wants to share with grandchildren, values tradition"},
        {"name": "British Expat Dad Oliver", "details": "Grew up with Carroll, wants to share cultural heritage, nostalgic for British childhood"},
        {"name": "Former Gifted Kid Mom Julia", "details": "Read this at age 10 and felt special, wants same experience for her kids"},
        {"name": "Alice in Wonderland Fan Dad Nathan", "details": "Loves Carroll's work, excited to share whole Carroll universe with kids"},
        {"name": "Baby Boomer Mom Patricia", "details": "Remembers illustrated edition from childhood, wants to recreate that experience"},
        {"name": "Private School Parent Richard", "details": "Received classical education, wants same for children, values traditional canon"},
        {"name": "Anglophile Mom Christine", "details": "Loves British culture, wants kids exposed to British literary tradition"},
        {"name": "Poetry-Loving Dad Vincent", "details": "Memorized passages as a child, wants to share poetry appreciation"},
        {"name": "Former English Major Mom Sandra", "details": "Studied Carroll in college, nostalgic for literary analysis days"},
        {"name": "Homeschool Classics Mom Deborah", "details": "Uses traditional canon, believes classics provide cultural literacy foundation"},
        {"name": "Theater Parent Gary", "details": "Performed in Carroll adaptations, wants kids to know classic texts"},
        {"name": "Tradition-Focused Dad William", "details": "Believes passing down classics is important parenting responsibility"},
        {"name": "Classical Education Mom Heather", "details": "Follows Great Books curriculum, Carroll is part of the canon"},
        {"name": "Prep School Graduate Dad Charles", "details": "Read Carroll at boarding school, sees it as marker of education"},
        {"name": "Book Collector Parent Dorothy", "details": "Has vintage Carroll editions, wants kids to appreciate literary heritage"},
        {"name": "Old-School Mom Frances", "details": "Believes modern kids need challenging classical texts, worried about dumbing down"},
        {"name": "Literature Legacy Dad George", "details": "From family of educators, passing down canonical texts is family tradition"},
        {"name": "Victorian Literature Enthusiast Mom Virginia", "details": "Loves Victorian era, wants kids exposed to that cultural world"},
        {"name": "Former Precocious Reader Dad Howard", "details": "Read advanced books young, wants kids to experience that pride"},
        {"name": "British Heritage Mom Rosemary", "details": "Values British literary tradition, Carroll is essential cultural touchstone"}
    ]

    # Combine all personas
    for persona in literary_parents:
        persona['archetype'] = 'Literary Parent'
        personas.append(persona)

    for persona in practical_parents:
        persona['archetype'] = 'Practical Parent'
        personas.append(persona)

    for persona in modern_parents:
        persona['archetype'] = 'Modern Parent'
        personas.append(persona)

    for persona in nostalgic_parents:
        persona['archetype'] = 'Nostalgic Parent'
        personas.append(persona)

    return personas


def generate_evaluation_prompt(persona):
    """Generate LLM prompt for a specific parent persona evaluation."""

    prompt = f"""You are {persona['name']}, a parent evaluating whether to purchase "The Hunting of the Snark"
by Lewis Carroll for your 9-12 year old child.

YOUR BACKGROUND: {persona['details']}
YOUR ARCHETYPE: {persona['archetype']}

BOOK INFORMATION:
{BOOK_CONTEXT}

As {persona['name']}, provide a detailed evaluation with the following:

1. MARKET APPEAL (0-10): Would you buy this for your 9-12 year old? Rate 0-10.
   Consider your specific values and concerns as {persona['archetype']}.

2. GENRE FIT (0-10): Does this meet your expectations for quality children's literature?
   Rate based on your specific criteria as {persona['name']}.

3. AUDIENCE ALIGNMENT (0-10): Is this appropriate and engaging for modern 9-12 year olds?
   Consider comprehension level, interest, and developmental appropriateness.

4. DETAILED FEEDBACK (150-250 words): As {persona['name']}, explain your perspective.
   - What specifically appeals or doesn't appeal to you?
   - What concerns do you have about your child reading this?
   - How does this fit or not fit your values and priorities?
   - Would your child actually read and enjoy this?

5. RECOMMENDATIONS (50-100 words): What would increase your likelihood of purchasing?
   - What changes or additions would make this more appealing?
   - What supplementary materials would help?
   - Under what conditions might you consider it?

6. CONCERNS (50-100 words): Your top 2-3 specific worries about this book.
   Be honest and specific to your perspective as {persona['name']}.

Respond ONLY with valid JSON in this exact format:
{{
  "persona_name": "{persona['name']}",
  "archetype": "{persona['archetype']}",
  "market_appeal": <number 0-10>,
  "genre_fit": <number 0-10>,
  "audience_alignment": <number 0-10>,
  "detailed_feedback": "<your detailed feedback>",
  "recommendations": "<your recommendations>",
  "concerns": "<your concerns>"
}}

Remember: Stay in character as {persona['name']} with background: {persona['details']}
Be honest, specific, and realistic about how this parent would actually evaluate this book."""

    return prompt


def evaluate_persona(persona, llm_caller, model="gemini/gemini-2.5-flash"):
    """Generate evaluation for a single parent persona."""

    prompt = generate_evaluation_prompt(persona)

    try:
        response = llm_caller.call_llm(
            prompt=prompt,
            model=model,
            temperature=0.7,
            max_tokens=1500
        )

        # Parse JSON response
        response_text = response.strip()

        # Handle markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text.split("```json")[1]
            response_text = response_text.split("```")[0]
        elif response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            response_text = response_text.split("```")[0]

        response_text = response_text.strip()
        evaluation = json.loads(response_text)

        # Add metadata
        evaluation['persona_details'] = persona['details']
        evaluation['timestamp'] = datetime.now().isoformat()
        evaluation['model'] = model

        return evaluation

    except Exception as e:
        print(f"Error evaluating {persona['name']}: {e}")
        return None


def main():
    """Generate all 80 parent evaluations."""

    print("=" * 80)
    print("The Hunting of the Snark - Parent Evaluations")
    print("Generating 80 diverse parent perspectives")
    print("=" * 80)
    print()

    # Initialize LLM caller
    llm_caller = CodexesLLMIntegration()

    # Create output directory
    output_dir = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/data/reader_panels/hunting_of_the_snark")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "parents_feedback.jsonl"

    # Get all personas
    personas = create_parent_personas()
    print(f"Created {len(personas)} parent personas across 4 archetypes")
    print()

    # Track progress
    successful_evaluations = 0
    failed_evaluations = 0

    # Open output file for writing
    with open(output_file, 'w') as f:

        for i, persona in enumerate(personas, 1):
            print(f"[{i}/80] Evaluating: {persona['name']} ({persona['archetype']})")

            evaluation = evaluate_persona(persona, llm_caller)

            if evaluation:
                # Write to JSONL file
                f.write(json.dumps(evaluation) + '\n')
                f.flush()  # Ensure it's written immediately
                successful_evaluations += 1

                # Show scores
                print(f"  ✓ Market Appeal: {evaluation['market_appeal']}/10")
                print(f"    Genre Fit: {evaluation['genre_fit']}/10")
                print(f"    Audience Alignment: {evaluation['audience_alignment']}/10")
            else:
                failed_evaluations += 1
                print(f"  ✗ Failed to generate evaluation")

            print()

            # Progress report every 20 evaluations
            if i % 20 == 0:
                print("=" * 80)
                print(f"PROGRESS REPORT: Completed {i}/80 evaluations")
                print(f"  Successful: {successful_evaluations}")
                print(f"  Failed: {failed_evaluations}")
                print("=" * 80)
                print()

    # Final report
    print("=" * 80)
    print("FINAL REPORT")
    print("=" * 80)
    print(f"Total evaluations attempted: {len(personas)}")
    print(f"Successful: {successful_evaluations}")
    print(f"Failed: {failed_evaluations}")
    print()
    print(f"Output saved to: {output_file}")
    print()

    # Calculate summary statistics
    if successful_evaluations > 0:
        print("Calculating summary statistics...")

        evaluations = []
        with open(output_file, 'r') as f:
            for line in f:
                evaluations.append(json.loads(line))

        # Calculate averages by archetype
        archetypes = {}
        for eval in evaluations:
            archetype = eval['archetype']
            if archetype not in archetypes:
                archetypes[archetype] = {
                    'market_appeal': [],
                    'genre_fit': [],
                    'audience_alignment': []
                }
            archetypes[archetype]['market_appeal'].append(eval['market_appeal'])
            archetypes[archetype]['genre_fit'].append(eval['genre_fit'])
            archetypes[archetype]['audience_alignment'].append(eval['audience_alignment'])

        print("\nAVERAGE SCORES BY ARCHETYPE:")
        print("-" * 80)
        for archetype, scores in archetypes.items():
            avg_market = sum(scores['market_appeal']) / len(scores['market_appeal'])
            avg_genre = sum(scores['genre_fit']) / len(scores['genre_fit'])
            avg_audience = sum(scores['audience_alignment']) / len(scores['audience_alignment'])

            print(f"\n{archetype}:")
            print(f"  Market Appeal: {avg_market:.1f}/10")
            print(f"  Genre Fit: {avg_genre:.1f}/10")
            print(f"  Audience Alignment: {avg_audience:.1f}/10")

        # Overall averages
        all_market = [e['market_appeal'] for e in evaluations]
        all_genre = [e['genre_fit'] for e in evaluations]
        all_audience = [e['audience_alignment'] for e in evaluations]

        print("\nOVERALL AVERAGES:")
        print("-" * 80)
        print(f"Market Appeal: {sum(all_market)/len(all_market):.1f}/10")
        print(f"Genre Fit: {sum(all_genre)/len(all_genre):.1f}/10")
        print(f"Audience Alignment: {sum(all_audience)/len(all_audience):.1f}/10")

    print("\n" + "=" * 80)
    print("Evaluation complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
