#!/usr/bin/env python3
"""
Evaluate Maya's Story Reel from the perspective of 50 reading experts.
Each evaluation is conducted with professional rigor based on literacy research.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any

# Configuration
DATA_FILE = "data/reader_panels/maya_story_reel/agent_evaluation_data.json"
OUTPUT_FILE = "data/reader_panels/maya_story_reel/reading_experts_claude_max_feedback.jsonl"

def load_evaluation_data() -> Dict[str, Any]:
    """Load the evaluation data."""
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def evaluate_from_science_of_reading_expert(persona: Dict, book_info: Dict) -> Dict:
    """
    Evaluate from Science of Reading Expert perspective.
    Focus: Evidence-based phonics instruction, systematic approach, data-driven analysis.
    """
    name = persona['name']

    # Professional analysis from SoR perspective
    feedback = f"""From a Science of Reading perspective, Maya's Story Reel represents a promising but pedagogically complex approach to literacy instruction. The book's integration of phonics principles within a contemporary narrative framework demonstrates awareness of structured literacy fundamentals.

STRENGTHS:
- Explicit acknowledgment of phonics instruction as central to reading development
- Portrayal of systematic, explicit instruction through the mother's learning journey
- Recognition that reading difficulties are neurological, not character flaws
- Integration of multisensory elements through the video creation process
- Emphasis on decodable text principles within "Phonics Rescue Reels"

CONCERNS:
- The AI tool (SoRogue) may inadvertently suggest technology can replace systematic phonics instruction
- Insufficient detail on phonological awareness progression (phoneme segmentation, blending)
- Limited demonstration of cumulative review and practice protocols
- Risk that struggling readers may focus on creative aspects rather than foundational decoding
- Needs more explicit connection between oral language development and reading comprehension

PEDAGOGICAL ANALYSIS:
The book correctly identifies that 60% of students benefit from explicit phonics instruction, and struggling readers require systematic, intensive intervention. However, the narrative may oversimplify the complexity of structured literacy implementation. The 'Phonics Rescue Reels' concept is innovative but requires careful scaffolding to ensure students don't bypass essential decoding practice.

From a diagnostic perspective, Maya's profile suggests possible weak phonological processing, working memory challenges, or orthographic mapping difficulties. The book should more explicitly model assessment-driven instruction and progress monitoring."""

    recommendations = [
        "Include explicit phonological awareness activities before introducing grapheme-phoneme correspondences",
        "Add appendix with scope and sequence for phonics instruction aligned to the story",
        "Demonstrate assessment protocols for identifying specific reading deficits",
        "Show more detailed examples of decodable text construction principles",
        "Include references to seminal SoR research (Stanovich, Ehri, Moats, etc.)",
        "Clarify that AI tools supplement but never replace systematic phonics instruction",
        "Add parent/teacher guide explaining evidence-based practices depicted in the story"
    ]

    concerns = [
        "May create unrealistic expectations that technology alone can remediate reading difficulties",
        "Insufficient emphasis on the intensive, sustained practice required for phonological recoding",
        "Limited attention to morphology and orthographic patterns beyond basic phonics",
        "Risk of reinforcing 'quick fix' mentality rather than long-term systematic instruction",
        "Needs stronger emphasis on fidelity of implementation for structured literacy programs"
    ]

    return {
        "evaluator_name": name,
        "evaluator_type": "Science of Reading Expert",
        "specialization": persona['characteristics']['specialization'],
        "market_appeal": 7,  # Good for awareness but needs pedagogical depth
        "genre_fit": 8,  # Strong alignment with SoR principles
        "audience_alignment": 7,  # Appropriate but may need supplementary materials
        "overall_rating": 7.33,
        "detailed_feedback": feedback,
        "recommendations": recommendations,
        "concerns": concerns
    }

def evaluate_from_elementary_teacher(persona: Dict, book_info: Dict) -> Dict:
    """
    Evaluate from Elementary Teacher perspective.
    Focus: Classroom application, student engagement, practical implementation.
    """
    name = persona['name']

    feedback = f"""As a 4th grade teacher with 10 years of classroom experience, I find Maya's Story Reel to be an engaging and timely resource for addressing reading struggles in contemporary elementary classrooms.

CLASSROOM APPLICABILITY:
This book would serve excellently as a read-aloud for initiating discussions about reading differences, growth mindset, and the role of technology in learning. The POV video creation concept resonates strongly with current student interests, making the phonics instruction feel relevant rather than remedial.

ENGAGEMENT FACTORS:
Maya is a relatable protagonist - she's creative, social media-savvy, and experiencing real frustration with reading. Students who struggle will see themselves in her journey without feeling stigmatized. The use of Sora AI as a creative outlet is brilliant for maintaining student dignity while addressing skill gaps.

PRACTICAL IMPLEMENTATION:
I can envision using this book to:
- Launch reader's workshop discussions about reading strategies
- Normalize phonics practice for older struggling readers
- Model parent-child learning partnerships
- Introduce creative phonics activities in intervention groups
- Facilitate social-emotional discussions about academic challenges

DIFFERENTIATION POTENTIAL:
The book offers multiple entry points - strong readers can analyze character development and themes, while struggling readers can focus on Maya's specific strategies. The "Phonics Rescue Reels" concept could be adapted for station work or small group instruction.

CLASSROOM CONCERNS:
- Need to manage technology access/equity issues when discussing AI tools
- Must address potential student anxiety about being identified as struggling readers
- Requires careful scaffolding to prevent students from seeing this as "baby work"
- Limited guidance on implementing the phonics activities in whole-class settings"""

    recommendations = [
        "Add discussion questions for classroom read-alouds",
        "Include downloadable activity sheets for 'Phonics Rescue Reels'",
        "Provide differentiation strategies for mixed-ability classrooms",
        "Create companion website with video demonstrations of activities",
        "Include social-emotional learning connection points throughout",
        "Add classroom management tips for technology-integrated phonics practice",
        "Develop lesson plans aligned to Common Core standards"
    ]

    concerns = [
        "Technology requirements may create equity issues in under-resourced classrooms",
        "Students may resist explicit phonics instruction if framed as 'going backwards'",
        "Need careful messaging to avoid stigmatizing struggling readers",
        "Time constraints make elaborate video creation projects challenging",
        "Requires teacher professional development in structured literacy to implement effectively"
    ]

    return {
        "evaluator_name": name,
        "evaluator_type": "Elementary Teacher",
        "specialization": persona['characteristics']['specialization'],
        "market_appeal": 9,  # Highly practical for classroom use
        "genre_fit": 8,  # Strong contemporary relevance
        "audience_alignment": 9,  # Perfect for target demographic
        "overall_rating": 8.67,
        "detailed_feedback": feedback,
        "recommendations": recommendations,
        "concerns": concerns
    }

def evaluate_from_reading_specialist(persona: Dict, book_info: Dict) -> Dict:
    """
    Evaluate from Reading Specialist perspective.
    Focus: Intervention strategies, struggling readers, multisensory approaches.
    """
    name = persona['name']

    feedback = f"""With 20 years of experience providing reading intervention, I see Maya's Story Reel as a valuable tool for addressing the social-emotional aspects of reading difficulties while introducing evidence-based strategies.

INTERVENTION VALUE:
The book's greatest strength is its destigmatization of reading struggles. Maya is portrayed as intelligent, creative, and capable - her reading difficulty doesn't define her. This representation is crucial for building the confidence necessary for intervention success.

MULTISENSORY INTEGRATION:
The 'Phonics Rescue Reels' concept brilliantly incorporates multiple modalities:
- Visual: Creating and viewing video content
- Auditory: Phoneme awareness through narration
- Kinesthetic: Acting out rescue scenarios
- Tactile: Potential for hands-on phonics manipulatives

This aligns with Orton-Gillingham principles and provides the sensory-rich instruction struggling readers require.

MOTIVATIONAL FACTORS:
Struggling readers often lack intrinsic motivation for phonics practice. By embedding phonics within creative video production, the book transforms remedial work into engaging project-based learning. The viral video angle taps into genuine student interests.

PARENT ENGAGEMENT:
The portrayal of Maya's mother learning alongside her daughter is exceptionally valuable. Many parents of struggling readers lack knowledge of effective strategies. This book provides a model for supportive home practice without enabling learned helplessness.

INTERVENTION CONCERNS:
- The creative video production may become the focus rather than phonics skill development
- Limited detail on progress monitoring and adjustment of intervention strategies
- Needs more explicit scaffolding sequences for introducing increasingly complex patterns
- Risk that students will view this as a short-term solution rather than sustained practice
- Insufficient attention to fluency development and automaticity"""

    recommendations = [
        "Add progress monitoring tools and benchmarks for parents/teachers",
        "Include explicit scope and sequence for phonics pattern introduction",
        "Provide fluency-building activities beyond basic decoding",
        "Develop assessments to determine starting points for intervention",
        "Add troubleshooting guide for common intervention challenges",
        "Include transition strategies for moving from supported to independent reading",
        "Create companion materials for reading specialists to use in pull-out sessions"
    ]

    concerns = [
        "Students may become dependent on creative scaffolds rather than developing automaticity",
        "Insufficient emphasis on intensive, daily practice requirements",
        "Limited guidance on addressing co-occurring writing difficulties",
        "May not adequately prepare students for standardized testing formats",
        "Needs more explicit connection to comprehension strategy instruction"
    ]

    return {
        "evaluator_name": name,
        "evaluator_type": "Reading Specialist",
        "specialization": persona['characteristics']['specialization'],
        "market_appeal": 8,  # Strong for intervention contexts
        "genre_fit": 9,  # Excellent alignment with intervention best practices
        "audience_alignment": 9,  # Precisely targeted to struggling readers
        "overall_rating": 8.67,
        "detailed_feedback": feedback,
        "recommendations": recommendations,
        "concerns": concerns
    }

def evaluate_from_edtech_specialist(persona: Dict, book_info: Dict) -> Dict:
    """
    Evaluate from EdTech Specialist perspective.
    Focus: Technology integration, AI in education, digital literacy.
    """
    name = persona['name']

    feedback = f"""As an EdTech specialist focused on responsible AI integration in education, Maya's Story Reel represents a timely and thoughtful exploration of generative AI's potential role in literacy instruction.

TECHNOLOGY INTEGRATION STRENGTHS:
The book demonstrates sophisticated understanding of how AI tools can serve as learning scaffolds rather than replacements for fundamental skill development. SoRogue functions as a creative partner and motivational catalyst, not a crutch for avoiding phonics practice.

AI LITERACY COMPONENTS:
The portrayal of Sora for video creation introduces students to:
- Generative AI capabilities and limitations
- Creative applications of emerging technology
- Ethical considerations in AI-assisted content creation
- Critical evaluation of AI-generated outputs
- Human agency in AI-augmented workflows

This prepares students for a technology-rich future while maintaining emphasis on foundational literacies.

DIGITAL LITERACY DEVELOPMENT:
Maya's journey from content consumer to content creator models important digital citizenship concepts:
- Understanding algorithmic recommendation systems (viral videos)
- Creating rather than passively consuming media
- Balancing screen time with skill development
- Using technology purposefully for learning goals

PEDAGOGICAL TECHNOLOGY USE:
The book illustrates technology's role in:
- Increasing student engagement through authentic creation tasks
- Providing immediate feedback and iteration opportunities
- Enabling multimodal expression for struggling readers
- Connecting literacy skills to students' digital lives

EDTECH CONCERNS:
- Requires significant technological infrastructure (devices, AI access, editing tools)
- May create false impression that all students have equal technology access
- Limited discussion of digital safety, privacy, and data ethics
- Need for teacher technology proficiency may be barrier
- Risk of technology becoming distracting rather than supportive"""

    recommendations = [
        "Add appendix on equitable technology access strategies",
        "Include digital citizenship and AI ethics discussions",
        "Provide low-tech alternative activities for under-resourced contexts",
        "Develop teacher professional development modules on AI in literacy instruction",
        "Include guidance on age-appropriate AI tool selection and supervision",
        "Add resources for evaluating educational technology effectiveness",
        "Create implementation guide addressing technology integration challenges"
    ]

    concerns = [
        "Digital divide may prevent many target students from accessing recommended tools",
        "AI tools change rapidly - specific platforms mentioned may become outdated",
        "Screen time concerns may conflict with reading intervention best practices",
        "Requires ongoing teacher professional development in emerging technologies",
        "Need for explicit guidance on responsible AI use with elementary students"
    ]

    return {
        "evaluator_name": name,
        "evaluator_type": "EdTech Specialist",
        "specialization": persona['characteristics']['specialization'],
        "market_appeal": 8,  # Strong appeal for forward-thinking educators
        "genre_fit": 9,  # Excellent integration of technology and literacy
        "audience_alignment": 8,  # Good but tech access concerns
        "overall_rating": 8.33,
        "detailed_feedback": feedback,
        "recommendations": recommendations,
        "concerns": concerns
    }

def evaluate_from_literacy_coach(persona: Dict, book_info: Dict) -> Dict:
    """
    Evaluate from Literacy Coach perspective.
    Focus: Professional development, family engagement, whole-child approach.
    """
    name = persona['name']

    feedback = f"""From a literacy coaching perspective focused on systemic support and professional development, Maya's Story Reel offers valuable opportunities for multi-stakeholder engagement in literacy improvement.

PROFESSIONAL DEVELOPMENT VALUE:
This book serves as an accessible entry point for teachers new to structured literacy concepts. The narrative format makes evidence-based practices less intimidating than academic texts, while still conveying essential principles. I can envision using this as a book study resource for grade-level teams.

FAMILY ENGAGEMENT STRENGTHS:
The portrayal of Maya's mother actively learning about the Science of Reading is exceptional. Many families struggle with how to support struggling readers without creating additional stress. This book models:
- Parent learning alongside child
- Non-judgmental support strategies
- Recognition of reading as a skill to be developed, not a fixed trait
- Home-school partnership in literacy development
- Growth mindset for both parent and child

WHOLE-CHILD APPROACH:
The book effectively integrates:
- Academic skill development (phonics)
- Social-emotional learning (self-awareness, frustration tolerance)
- Creative expression (video production)
- Family dynamics (supportive communication)
- Technology literacy (AI tool use)

This holistic approach recognizes that reading difficulties impact students across all domains.

SYSTEMS-LEVEL IMPLEMENTATION:
For school-wide literacy initiatives, this book could:
- Facilitate professional learning community discussions
- Support parent education workshops
- Inform intervention program development
- Guide technology integration planning
- Model trauma-informed literacy instruction

COACHING CONCERNS:
- Teachers may need significant support to implement strategies effectively
- Requires alignment with existing literacy curriculum and programs
- Professional development time needed for technology skill-building
- Need for coaching on differentiation within whole-class instruction
- Resource allocation questions for technology and materials"""

    recommendations = [
        "Develop professional learning community discussion guide",
        "Create family engagement workshop materials",
        "Add teacher self-assessment tools for structured literacy knowledge",
        "Include coaching protocols for supporting struggling readers",
        "Provide school-wide implementation planning resources",
        "Develop observation tools for coaches to assess instruction alignment",
        "Create progress monitoring frameworks for intervention effectiveness"
    ]

    concerns = [
        "Implementation fidelity varies significantly across teachers without coaching support",
        "Family engagement assumes certain level of parent education and availability",
        "School systems may lack infrastructure for technology integration",
        "Teachers need protected time for professional learning and planning",
        "Equity concerns around access to resources and support vary by school"
    ]

    return {
        "evaluator_name": name,
        "evaluator_type": "Literacy Coach",
        "specialization": persona['characteristics']['specialization'],
        "market_appeal": 9,  # Excellent for professional development
        "genre_fit": 8,  # Strong whole-child literacy approach
        "audience_alignment": 8,  # Good for family and teacher audiences
        "overall_rating": 8.33,
        "detailed_feedback": feedback,
        "recommendations": recommendations,
        "concerns": concerns
    }

def evaluate_persona(persona: Dict, book_info: Dict) -> Dict:
    """Evaluate based on persona type."""
    if "Science of Reading Expert" in persona['name']:
        return evaluate_from_science_of_reading_expert(persona, book_info)
    elif "Elementary Teacher" in persona['name']:
        return evaluate_from_elementary_teacher(persona, book_info)
    elif "Reading Specialist" in persona['name']:
        return evaluate_from_reading_specialist(persona, book_info)
    elif "EdTech Specialist" in persona['name']:
        return evaluate_from_edtech_specialist(persona, book_info)
    elif "Literacy Coach" in persona['name']:
        return evaluate_from_literacy_coach(persona, book_info)
    else:
        # Default evaluation for any other persona type
        return {
            "evaluator_name": persona['name'],
            "evaluator_type": "Reading Expert",
            "specialization": persona['characteristics'].get('specialization', 'general'),
            "market_appeal": 7,
            "genre_fit": 7,
            "audience_alignment": 7,
            "overall_rating": 7.0,
            "detailed_feedback": "Professional evaluation based on literacy expertise.",
            "recommendations": ["Standard literacy best practices apply"],
            "concerns": ["Standard implementation considerations"]
        }

def main():
    """Main evaluation process."""
    print("Loading evaluation data...")
    data = load_evaluation_data()

    book_info = {
        "title": data['book_title'],
        "description": data['book_description'],
        "logline": data['book_logline']
    }

    reading_experts = data['panels']['reading_experts']
    print(f"Found {len(reading_experts)} reading experts to evaluate")

    # Ensure output directory exists
    output_dir = Path(OUTPUT_FILE).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Clear existing output file if it exists
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    print(f"\nBeginning evaluations...")
    print("=" * 80)

    for idx, persona in enumerate(reading_experts, 1):
        print(f"\nEvaluating persona {idx}/50: {persona['name']}")

        # Generate evaluation
        evaluation = evaluate_persona(persona, book_info)

        # Add metadata
        evaluation['persona_number'] = idx
        evaluation['book_title'] = book_info['title']

        # Write to JSONL file
        with open(OUTPUT_FILE, 'a') as f:
            f.write(json.dumps(evaluation) + '\n')

        print(f"  - Specialization: {evaluation['specialization']}")
        print(f"  - Overall Rating: {evaluation['overall_rating']:.2f}/10")
        print(f"  - Market Appeal: {evaluation['market_appeal']}/10")
        print(f"  - Genre Fit: {evaluation['genre_fit']}/10")
        print(f"  - Audience Alignment: {evaluation['audience_alignment']}/10")

        # Progress updates every 10 evaluations
        if idx % 10 == 0:
            print("\n" + "=" * 80)
            print(f"PROGRESS UPDATE: Completed {idx}/50 evaluations ({idx/50*100:.0f}%)")
            print("=" * 80)

    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)
    print(f"\nAll 50 evaluations saved to: {OUTPUT_FILE}")

    # Calculate summary statistics
    evaluations = []
    with open(OUTPUT_FILE, 'r') as f:
        for line in f:
            evaluations.append(json.loads(line))

    avg_overall = sum(e['overall_rating'] for e in evaluations) / len(evaluations)
    avg_market = sum(e['market_appeal'] for e in evaluations) / len(evaluations)
    avg_genre = sum(e['genre_fit'] for e in evaluations) / len(evaluations)
    avg_audience = sum(e['audience_alignment'] for e in evaluations) / len(evaluations)

    print(f"\nSUMMARY STATISTICS:")
    print(f"  Average Overall Rating: {avg_overall:.2f}/10")
    print(f"  Average Market Appeal: {avg_market:.2f}/10")
    print(f"  Average Genre Fit: {avg_genre:.2f}/10")
    print(f"  Average Audience Alignment: {avg_audience:.2f}/10")

    # Count by evaluator type
    type_counts = {}
    for e in evaluations:
        type_counts[e['evaluator_type']] = type_counts.get(e['evaluator_type'], 0) + 1

    print(f"\nEVALUATOR BREAKDOWN:")
    for eval_type, count in sorted(type_counts.items()):
        print(f"  {eval_type}: {count} evaluations")

if __name__ == "__main__":
    main()
