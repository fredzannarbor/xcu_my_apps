#!/usr/bin/env python3
"""
Enhanced example showing Publisher Persona and Continuous Ideation features
for the xynapse_traces imprint.
"""

from src.codexes.modules.imprints.services.imprint_manager import ImprintManager
from src.codexes.modules.imprints.models.publisher_persona import PublisherPersona
import json

def main():
    print("=== Enhanced Xynapse Traces with Publisher Persona & Continuous Ideation ===")
    
    # 1. Load the imprint
    manager = ImprintManager()
    xynapse = manager.get_imprint("Xynapse Traces")
    
    if not xynapse:
        print("❌ xynapse_traces imprint not found!")
        return
    
    print(f"✅ Loaded: {xynapse.name}")
    
    # 2. Create and set a Publisher Persona
    print("\n=== Creating Publisher Persona ===")
    
    # Create Max Bialystok persona as an example
    max_persona = PublisherPersona.create_max_bialystok_persona()
    
    # Set the persona for the imprint
    success = manager.set_publisher_persona("Xynapse Traces", max_persona)
    if success:
        print(f"✅ Set publisher persona: {max_persona.name}")
        print(f"   Bio: {max_persona.bio}")
        print(f"   Risk Tolerance: {max_persona.risk_tolerance.value}")
        print(f"   Decision Style: {max_persona.decision_style.value}")
        print(f"   Key Vulnerability: {max_persona.vulnerability_factors[0].name}")
    
    # 3. Show persona-driven content evaluation
    print("\n=== Persona-Driven Content Evaluation ===")
    
    # Test content proposal
    sample_content = {
        "title": "The Contrarian's Guide to AI Ethics",
        "genre": "Technology",
        "target_audience": "Academic and Professional",
        "controversy_level": 0.8,
        "market_trend_alignment": 0.3,  # Against trends (good for contrarian)
        "estimated_cost": 75000
    }
    
    evaluation = max_persona.evaluate_acquisition_decision(sample_content)
    
    print(f"Content Evaluation for '{sample_content['title']}':")
    print(f"   Overall Score: {evaluation['overall_score']:.2f}")
    print(f"   Recommendation: {evaluation['recommendation']}")
    
    if evaluation["excitement_factors"]:
        print("   Excitement Factors:")
        for factor in evaluation["excitement_factors"]:
            print(f"     ✨ {factor}")
    
    if evaluation["concerns"]:
        print("   Concerns:")
        for concern in evaluation["concerns"]:
            print(f"     ⚠️ {concern}")
    
    if evaluation["vulnerability_warnings"]:
        print("   Vulnerability Warnings:")
        for warning in evaluation["vulnerability_warnings"]:
            print(f"     🚨 {warning}")
    
    # 4. Generate persona-driven concepts
    print("\n=== Persona-Driven Concept Generation ===")
    
    concept_requests = manager.generate_persona_concepts("Xynapse Traces", num_concepts=3)
    
    print(f"Generated {len(concept_requests)} persona-driven concept requests:")
    for i, request in enumerate(concept_requests, 1):
        print(f"\n   Request {i}:")
        print(f"   Type: {request.get('generation_type', 'unknown')}")
        print(f"   Timestamp: {request.get('timestamp', 'unknown')}")
        if 'special_instructions' in request:
            print(f"   Special Instructions:")
            for instruction in request['special_instructions']:
                print(f"     • {instruction}")
    
    # 5. Analyze catalog opportunities
    print("\n=== Catalog Gap Analysis ===")
    
    # Load existing books
    existing_books = manager._load_imprint_books(xynapse)
    print(f"Analyzing {len(existing_books)} existing books...")
    
    gap_analysis = manager.analyze_catalog_opportunities("Xynapse Traces", existing_books)
    
    if gap_analysis:
        print(f"Gap analysis completed for {gap_analysis['imprint_name']}")
        print(f"Books analyzed: {gap_analysis.get('books_analyzed', 0)}")
        print(f"Analysis type: {gap_analysis.get('analysis_type', 'unknown')}")
    
    # 6. Get ideation opportunities based on persona
    print("\n=== Current Ideation Opportunities ===")
    
    opportunities = manager.ideation_service.get_imprint_ideation_opportunities(xynapse)
    
    print(f"Found {len(opportunities.get('opportunities', []))} opportunities:")
    for opp in opportunities.get('opportunities', [])[:5]:  # Show first 5
        print(f"   • {opp['type']}: {opp['description']}")
        print(f"     Action: {opp['action']}")
    
    # 7. Show continuous ideation setup
    print("\n=== Continuous Ideation Configuration ===")
    
    # Configure continuous ideation prompts
    ideation_config = manager.ideation_service.configure_imprint_ideation_prompts(xynapse)
    
    print("Continuous ideation configured with:")
    print(f"   Enabled: {ideation_config['continuous_ideation']['enabled']}")
    print(f"   Generation frequency: {ideation_config['continuous_ideation']['generation_frequency_hours']} hours")
    print(f"   Concepts per generation: {ideation_config['continuous_ideation']['concepts_per_generation']}")
    
    if 'persona_generation' in ideation_config:
        print(f"   Publisher persona: {ideation_config['persona_generation']['persona_name']}")
        print(f"   Risk tolerance: {ideation_config['persona_generation']['risk_tolerance']}")
    
    # 8. Start continuous ideation (optional)
    print("\n=== Starting Continuous Ideation (Demo) ===")
    
    # Demo configuration for faster testing
    demo_config = {
        "generation_interval": 300,  # 5 minutes for demo
        "concepts_per_batch": 2,
        "quality_threshold": 0.6
    }
    
    print(f"Demo: Starting continuous ideation with {demo_config['generation_interval']}s intervals...")
    print("(In production, this would run continuously in the background)")
    
    # Show what the session would look like
    session_id = f"demo_session_xynapse_{int(datetime.now().timestamp())}"
    print(f"Session ID would be: {session_id}")
    print("Session would continuously generate concepts based on:")
    print("   • Publisher persona preferences")
    print("   • Imprint content constraints")
    print("   • Market gap analysis")
    print("   • Competitive positioning")
    
    print("\n🎉 Enhanced Xynapse Traces with Publisher Persona & Continuous Ideation is ready!")
    
    # 9. Show practical usage examples
    print("\n=== Practical Usage Examples ===")
    print("""
# Set a publisher persona
from src.codexes.modules.imprints.models.publisher_persona import PublisherPersona
persona = PublisherPersona.create_max_bialystok_persona()
manager.set_publisher_persona("Xynapse Traces", persona)

# Start continuous ideation
session_id = manager.start_continuous_ideation("Xynapse Traces")

# Get generated concepts
concepts = manager.get_recent_concepts("Xynapse Traces", limit=5)

# Evaluate content against persona preferences
evaluation = persona.evaluate_acquisition_decision(content_proposal)

# Generate persona-specific content brief
brief = persona.generate_content_brief("book")

# Stop ideation when needed
manager.stop_continuous_ideation( XC"Xynapse Traces")
""")


if __name__ == "__main__":
    from datetime import datetime
    main()