"""
Test script for multiple object detection functionality
"""

import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from codexes.ui.components.content_detector import ContentTypeDetector
from codexes.ui.core.simple_codex_object import CodexObjectType

def test_multiple_object_detection():
    """Test detection of multiple objects in content."""
    detector = ContentTypeDetector()
    
    print("🧪 Testing Multiple Object Detection")
    print("=" * 50)
    
    test_cases = [
        # Numbered list of ideas
        ("1. A story about time travel\n2. Dragons in modern cities\n3. Magic school adventures", True, 3),
        
        # Bullet list of concepts
        ("- Vampire detective story\n- Alien invasion comedy\n- Robot uprising drama", True, 3),
        
        # Titled sections
        ("Story Idea 1:\nA young wizard discovers ancient magic\n\nStory Idea 2:\nSpace pirates find treasure\n\nStory Idea 3:\nUnderwater civilization emerges", True, 3),
        
        # Paragraph-separated concepts
        ("A magical adventure in a fantasy realm with dragons and wizards.\n\nA science fiction story about space exploration and alien contact.\n\nA mystery novel set in Victorian London with supernatural elements.", True, 3),
        
        # Single object (should not be detected as multiple)
        ("This is a single story about a hero who goes on a journey to save the world from an ancient evil.", False, 1),
        
        # Multiple chapters (outline)
        ("Chapter 1: The Beginning\nOur hero starts their journey\n\nChapter 2: The Challenge\nThey face obstacles\n\nChapter 3: The Resolution\nThey succeed", True, 3),
    ]
    
    for i, (content, expected_multiple, expected_count) in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}:")
        print(f"Content: '{content[:60]}...'")
        
        result = detector.detect_type_and_multiplicity(content)
        
        is_multiple = result['is_multiple']
        count = result['count']
        confidence = result['confidence']
        reasoning = result['reasoning']
        
        # Check results
        multiple_correct = is_multiple == expected_multiple
        count_correct = count == expected_count
        
        status_multiple = "✅" if multiple_correct else "❌"
        status_count = "✅" if count_correct else "❌"
        
        print(f"  {status_multiple} Multiple: Expected {expected_multiple}, Got {is_multiple}")
        print(f"  {status_count} Count: Expected {expected_count}, Got {count}")
        print(f"  Confidence: {confidence:.1%}")
        print(f"  Reasoning: {reasoning}")
        
        if is_multiple and 'objects' in result:
            print(f"  Objects detected:")
            for j, obj in enumerate(result['objects'][:3]):  # Show first 3
                preview = obj['content'][:40] + "..." if len(obj['content']) > 40 else obj['content']
                print(f"    {j+1}. {obj['type'].value.title()}: {preview}")
            if len(result['objects']) > 3:
                print(f"    ... and {len(result['objects']) - 3} more")

def test_object_splitting():
    """Test splitting content into individual objects."""
    detector = ContentTypeDetector()
    
    print("\n\n🔧 Testing Object Splitting")
    print("=" * 50)
    
    test_content = """1. A story about a young wizard who discovers they have magical powers
2. A science fiction tale of space exploration and alien contact
3. A mystery novel set in Victorian London with supernatural elements"""
    
    print(f"Original content:\n{test_content}")
    
    # Detect multiplicity
    result = detector.detect_type_and_multiplicity(test_content)
    
    if result['is_multiple']:
        print(f"\n✅ Detected {result['count']} objects")
        print(f"Separator type: {result.get('separator_type', 'Unknown')}")
        
        # Show split objects
        for i, obj in enumerate(result['objects']):
            print(f"\nObject {i+1}:")
            print(f"  Type: {obj['type'].value.title()}")
            print(f"  Confidence: {obj['confidence']:.1%}")
            print(f"  Content: {obj['content']}")
    else:
        print("❌ Failed to detect multiple objects")

def test_edge_cases():
    """Test edge cases for multiple object detection."""
    detector = ContentTypeDetector()
    
    print("\n\n🎯 Testing Edge Cases")
    print("=" * 50)
    
    edge_cases = [
        # Empty content
        ("", False, 0),
        
        # Single numbered item
        ("1. Just one idea", False, 1),
        
        # Mixed separators
        ("1. First idea\n- Second concept\n• Third thought", True, 3),
        
        # False positive prevention
        ("This story has 1. a beginning, 2. a middle, and 3. an end.", False, 1),
        
        # Very short items
        ("1. Magic\n2. Dragons\n3. Adventure", True, 3),
    ]
    
    for i, (content, expected_multiple, expected_count) in enumerate(edge_cases, 1):
        print(f"\n🔍 Edge Case {i}: '{content[:30]}...'")
        
        result = detector.detect_type_and_multiplicity(content)
        
        multiple_correct = result['is_multiple'] == expected_multiple
        count_correct = result['count'] == expected_count
        
        status = "✅" if multiple_correct and count_correct else "❌"
        print(f"  {status} Multiple: {result['is_multiple']}, Count: {result['count']}")
        print(f"  Reasoning: {result['reasoning']}")

if __name__ == "__main__":
    test_multiple_object_detection()
    test_object_splitting()
    test_edge_cases()
    print("\n🎉 Multiple object detection tests completed!")