"""
Test script to verify content detection functionality
"""

import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from codexes.ui.components.content_detector import ContentTypeDetector, RuleBasedClassifier
from codexes.ui.core.simple_codex_object import CodexObjectType

def test_rule_based_classifier():
    """Test the rule-based classifier with various content types."""
    classifier = RuleBasedClassifier()
    
    test_cases = [
        # Ideas
        ("A story about time travel", CodexObjectType.IDEA),
        ("Dragons in modern New York", CodexObjectType.IDEA),
        
        # Loglines
        ("When a young wizard discovers he's the chosen one, he must save the world from an ancient evil.", CodexObjectType.LOGLINE),
        
        # Outlines
        ("Chapter 1: The Discovery\nChapter 2: The Journey\nChapter 3: The Resolution", CodexObjectType.OUTLINE),
        ("1. Introduction\n2. Rising Action\n3. Climax\n4. Resolution", CodexObjectType.OUTLINE),
        
        # Synopsis
        ("The story follows a young protagonist who discovers they have magical powers. The character must learn to control these abilities while facing an antagonist who threatens their world. The narrative explores themes of growth, responsibility, and the battle between good and evil.", CodexObjectType.SYNOPSIS),
        
        # Manuscript/Draft
        ('"Hello," she said, looking out the window. The rain was falling steadily now, creating rivulets down the glass. She had been waiting for this moment for years, and now that it was here, she felt surprisingly calm. The door opened behind her, and she turned to see him standing there, just as she had imagined he would be.', CodexObjectType.DRAFT),
    ]
    
    print("🧪 Testing Rule-Based Classifier:")
    for content, expected_type in test_cases:
        result = classifier.classify(content)
        detected_type = result['type']
        confidence = result['confidence']
        reasoning = result['reasoning']
        
        status = "✅" if detected_type == expected_type else "❌"
        print(f"{status} Content: '{content[:50]}...'")
        print(f"   Expected: {expected_type.value}, Got: {detected_type.value} ({confidence:.1%})")
        print(f"   Reasoning: {reasoning}")
        print()

def test_content_detector():
    """Test the main content detector."""
    detector = ContentTypeDetector()
    
    test_content = "Chapter 1: The Beginning\nOur hero starts their journey in a small village.\n\nChapter 2: The Challenge\nThey face their first major obstacle."
    
    print("🔍 Testing Content Detector:")
    
    # Test rule-based detection
    detected_type, confidence, reasoning = detector.detect_type(test_content, use_llm=False)
    print(f"Rule-based: {detected_type.value} ({confidence:.1%})")
    print(f"Reasoning: {reasoning}")
    print()
    
    # Test LLM detection (mock)
    detected_type, confidence, reasoning = detector.detect_type(test_content, use_llm=True)
    print(f"LLM-based: {detected_type.value} ({confidence:.1%})")
    print(f"Reasoning: {reasoning}")
    print()
    
    # Test detailed analysis
    details = detector.get_detection_details(test_content, use_llm=True)
    print("Detailed Analysis:")
    print(f"- Word count: {details['word_count']}")
    print(f"- Line count: {details['line_count']}")
    print(f"- Rule-based type: {details['rule_based']['type'].value}")
    print(f"- LLM-based type: {details['llm_based']['type'].value}")

if __name__ == "__main__":
    test_rule_based_classifier()
    print("=" * 60)
    test_content_detector()
    print("\n🎉 Content detection tests completed!")