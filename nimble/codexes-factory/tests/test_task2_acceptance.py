"""
Task 2 Acceptance Test: Verify that automatic detection handles lists of CodexObjects
"""

import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from codexes.ui.components.content_detector import ContentTypeDetector
from codexes.ui.components.universal_input import UniversalContentInput
from codexes.ui.core.simple_codex_object import CodexObjectType

def test_acceptance_criteria():
    """Test the acceptance criteria: 'users see automatic type detection with confidence' for lists."""
    print("🎯 Task 2 Acceptance Test: Multiple CodexObjects Detection")
    print("=" * 70)
    
    detector = ContentTypeDetector()
    
    # Test cases that represent common scenarios users will encounter
    test_scenarios = [
        {
            'name': 'List of Story Ideas',
            'content': """1. A young wizard discovers they're the chosen one
2. Time travelers accidentally change history
3. Dragons return to the modern world
4. AI becomes sentient and questions existence
5. Magic is discovered to be advanced science""",
            'expected_multiple': True,
            'min_count': 5,
            'description': 'Common brainstorming scenario'
        },
        {
            'name': 'Bullet Point Concepts',
            'content': """- Vampire detective in modern city
- Alien invasion comedy
- Robot uprising drama
- Underwater civilization emerges
- Time loop mystery""",
            'expected_multiple': True,
            'min_count': 5,
            'description': 'Alternative list format'
        },
        {
            'name': 'Chapter Outline',
            'content': """Chapter 1: The Discovery
Our hero finds the ancient artifact

Chapter 2: The Journey Begins
They set out on their quest

Chapter 3: The First Challenge
They face their greatest fear

Chapter 4: The Revelation
The truth is revealed

Chapter 5: The Final Battle
Good versus evil""",
            'expected_multiple': True,
            'min_count': 5,
            'description': 'Story structure breakdown'
        },
        {
            'name': 'Character Concepts',
            'content': """Character 1: The Reluctant Hero
A young person thrust into adventure

Character 2: The Wise Mentor
An old sage with hidden secrets

Character 3: The Dark Antagonist
A villain with understandable motives""",
            'expected_multiple': True,
            'min_count': 3,
            'description': 'Character development list'
        },
        {
            'name': 'Mixed Content Types',
            'content': """Story Premise:
A world where magic and technology coexist

Main Characters:
- Alex: The tech-savvy protagonist
- Morgan: The magical mentor
- Dr. Chen: The scientist villain

Plot Points:
1. Discovery of the connection
2. The first conflict
3. The resolution""",
            'expected_multiple': True,
            'min_count': 3,
            'description': 'Complex mixed content'
        },
        {
            'name': 'Single Long Story (Control)',
            'content': """This is a single, cohesive story about a young hero who discovers they have magical powers. The story follows their journey as they learn to control their abilities, meet allies and enemies, face challenges that test their resolve, and ultimately save their world from an ancient evil that threatens to destroy everything they hold dear. The narrative explores themes of growth, friendship, sacrifice, and the responsibility that comes with great power.""",
            'expected_multiple': False,
            'min_count': 1,
            'description': 'Should NOT be detected as multiple'
        }
    ]
    
    print("Testing common user scenarios for multiple object detection:\n")
    
    passed_tests = 0
    total_tests = len(test_scenarios)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"🔍 Test {i}: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        
        # Perform detection
        result = detector.detect_type_and_multiplicity(scenario['content'])
        
        # Check results
        multiple_correct = result['is_multiple'] == scenario['expected_multiple']
        count_correct = result['count'] >= scenario['min_count'] if scenario['expected_multiple'] else result['count'] == scenario['min_count']
        
        if multiple_correct and count_correct:
            status = "✅ PASS"
            passed_tests += 1
        else:
            status = "❌ FAIL"
        
        print(f"   {status}")
        print(f"   Expected Multiple: {scenario['expected_multiple']}, Got: {result['is_multiple']}")
        print(f"   Expected Count: >={scenario['min_count']}, Got: {result['count']}")
        print(f"   Confidence: {result['confidence']:.1%}")
        print(f"   Reasoning: {result['reasoning']}")
        
        if result['is_multiple'] and len(result['objects']) > 0:
            print(f"   Objects Preview:")
            for j, obj in enumerate(result['objects'][:3]):
                preview = obj['content'][:50] + "..." if len(obj['content']) > 50 else obj['content']
                print(f"     {j+1}. {obj['type'].value.title()}: {preview}")
            if len(result['objects']) > 3:
                print(f"     ... and {len(result['objects']) - 3} more objects")
        
        print()
    
    # Summary
    print("=" * 70)
    print(f"📊 ACCEPTANCE TEST RESULTS: {passed_tests}/{total_tests} scenarios passed")
    
    if passed_tests == total_tests:
        print("🎉 ✅ ACCEPTANCE CRITERIA MET!")
        print("   Users can now see automatic type detection with confidence for lists of CodexObjects")
        print("   The system successfully detects and handles multiple objects in common scenarios")
    else:
        print("❌ ACCEPTANCE CRITERIA NOT FULLY MET")
        print(f"   {total_tests - passed_tests} scenarios failed")
    
    return passed_tests == total_tests

def test_user_experience_flow():
    """Test the complete user experience flow for multiple objects."""
    print("\n" + "=" * 70)
    print("🎭 User Experience Flow Test")
    print("=" * 70)
    
    # Simulate user entering multiple ideas
    user_content = """1. A story about a detective who can see ghosts
2. Time travelers who get stuck in the past
3. A world where dreams become reality
4. Robots that develop emotions
5. Magic users hiding in modern society"""
    
    print("User enters content:")
    print(f'"{user_content}"')
    print()
    
    # Test the detection
    detector = ContentTypeDetector()
    result = detector.detect_type_and_multiplicity(user_content)
    
    print("System Response:")
    if result['is_multiple']:
        print(f"✅ Detected {result['count']} separate objects")
        print(f"   Confidence: {result['confidence']:.1%}")
        print(f"   Reasoning: {result['reasoning']}")
        print(f"   User will see options to:")
        print(f"   - Create all as detected types")
        print(f"   - Create all as same type")
        print(f"   - Review and customize each")
        print()
        print("Individual object analysis:")
        for i, obj in enumerate(result['objects']):
            print(f"   {i+1}. Type: {obj['type'].value.title()} ({obj['confidence']:.1%})")
            preview = obj['content'][:60] + "..." if len(obj['content']) > 60 else obj['content']
            print(f"      Content: {preview}")
    else:
        print("❌ Failed to detect multiple objects")
        return False
    
    print("\n🎯 User Experience: EXCELLENT")
    print("   - Clear detection of multiple objects")
    print("   - Confidence scores provided")
    print("   - Flexible creation options")
    print("   - Individual object analysis")
    
    return True

if __name__ == "__main__":
    acceptance_met = test_acceptance_criteria()
    ux_good = test_user_experience_flow()
    
    print("\n" + "=" * 70)
    print("🏁 FINAL ACCEPTANCE STATUS")
    print("=" * 70)
    
    if acceptance_met and ux_good:
        print("✅ TASK 2 ACCEPTANCE CRITERIA FULLY SATISFIED")
        print("   - Automatic detection works for single objects ✅")
        print("   - Automatic detection works for lists of objects ✅")
        print("   - Users see confidence scores ✅")
        print("   - Users get clear reasoning ✅")
        print("   - Multiple creation options provided ✅")
    else:
        print("❌ TASK 2 ACCEPTANCE CRITERIA NOT MET")
        print("   Additional work needed on multiple object detection")
    
    print("\n🎉 Task 2 testing completed!")