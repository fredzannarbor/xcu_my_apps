#!/usr/bin/env python3
"""
Demo of Publisher Persona functionality for imprints.
Shows how personas can drive content decisions and ideation.
"""

from src.codexes.modules.imprints.models.publisher_persona import PublisherPersona, RiskTolerance, DecisionStyle
import json

def main():
    print("=== Publisher Persona Demo ===")
    
    # 1. Create Max Bialystok persona
    print("Creating Max Bialystok persona...")
    max_persona = PublisherPersona.create_max_bialystok_persona()
    
    print(f"✅ Created: {max_persona.name}")
    print(f"   Bio: {max_persona.bio}")
    print(f"   Risk Tolerance: {max_persona.risk_tolerance.value}")
    print(f"   Decision Style: {max_persona.decision_style.value}")
    
    # 2. Show personality traits
    print(f"\n=== Personality Traits ===")
    for trait in max_persona.personality_traits:
        print(f"• {trait.name}: {trait.strength:.2f} - {trait.description}")
    
    # 3. Show market preferences and vulnerabilities
    print(f"\n=== Market Preferences ===")
    for pref in max_persona.market_preferences:
        print(f"• {pref.segment_name}: {pref.preference_strength:.2f}")
        print(f"  {pref.description}")
        if pref.demographic_details.get("vulnerability_factor"):
            print(f"  🚨 CRITICAL: This is a vulnerability factor!")
    
    print(f"\n=== Vulnerabilities ===")
    for vuln in max_persona.vulnerability_factors:
        print(f"🚨 {vuln.name} (severity: {vuln.severity:.2f})")
        print(f"   {vuln.description}")
    
    # 4. Test content evaluation
    print(f"\n=== Content Evaluation Examples ===")
    
    # Test different content proposals
    test_contents = [
        {
            "title": "The Contrarian's Guide to Climate Change",
            "controversy_level": 0.9,
            "market_trend_alignment": 0.2,
            "target_audience": "lonely older female readers, intellectuals",
            "estimated_cost": 150000,
            "genre": "political commentary"
        },
        {
            "title": "Safe Investing for Seniors",
            "controversy_level": 0.1,
            "market_trend_alignment": 0.8,
            "target_audience": "older adults, financial advisors", 
            "estimated_cost": 50000,
            "genre": "financial advice"
        },
        {
            "title": "Lonely Women and the Books That Save Them",
            "controversy_level": 0.6,
            "market_trend_alignment": 0.4,
            "target_audience": "lonely older female readers, literary fiction enthusiasts",
            "estimated_cost": 80000,
            "genre": "literary memoir"
        }
    ]
    
    for i, content in enumerate(test_contents, 1):
        print(f"\n--- Content Proposal {i}: {content['title']} ---")
        evaluation = max_persona.evaluate_acquisition_decision(content)
        
        print(f"Overall Score: {evaluation['overall_score']:.2f}")
        print(f"Recommendation: {evaluation['recommendation']}")
        
        if evaluation.get("excitement_factors"):
            print("Excitement Factors:")
            for factor in evaluation["excitement_factors"]:
                print(f"  ✨ {factor}")
        
        if evaluation.get("concerns"):
            print("Concerns:")
            for concern in evaluation["concerns"]:
                print(f"  ⚠️ {concern}")
                
        if evaluation.get("vulnerability_warnings"):
            print("Vulnerability Warnings:")
            for warning in evaluation["vulnerability_warnings"]:
                print(f"  🚨 {warning}")
    
    # 5. Generate content brief
    print(f"\n=== Generated Content Brief ===")
    content_brief = max_persona.generate_content_brief("book")
    
    print("Content Brief for Max Bialystok:")
    print(f"Risk Profile: {content_brief['risk_profile']}")
    print(f"Budget: {content_brief['budget_considerations']}")
    print(f"Timeline: {content_brief['timeline_preferences']}")
    
    if content_brief["preferred_themes"]:
        print("Preferred Themes:")
        for theme in content_brief["preferred_themes"]:
            print(f"  • {theme['theme']} (priority: {theme['priority']})")
    
    if content_brief["target_markets"]:
        print("Target Markets:")
        for market in content_brief["target_markets"]:
            print(f"  • {market['segment']}: {market['description']}")
    
    # 6. Show serialization
    print(f"\n=== Persona Serialization ===")
    persona_dict = max_persona.to_dict()
    print(f"Serialized persona has {len(persona_dict)} fields")
    print("Key fields:")
    for key in ["name", "risk_tolerance", "decision_style", "career_highlights"]:
        if key in persona_dict:
            value = persona_dict[key]
            if isinstance(value, list):
                print(f"  {key}: {len(value)} items")
            else:
                print(f"  {key}: {value}")
    
    print(f"\n🎉 Publisher Persona system is working perfectly!")
    print(f"\n📝 This persona can now be attached to any imprint to:")
    print("   • Guide content acquisition decisions")
    print("   • Drive automated ideation processes") 
    print("   • Ensure content aligns with publisher vision")
    print("   • Identify potential risks and opportunities")

if __name__ == "__main__":
    main()