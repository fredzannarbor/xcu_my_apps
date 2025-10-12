#!/usr/bin/env python3
"""
Test script to generate 5 posts using a working model (Grok-3)
"""

import sys
from pathlib import Path

# Add the project root to Python path for proper imports
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.social_server.modules.generate_social_feed.feed_generator import FeedGenerator

def main():
    print("🚀 Starting post generation test...")
    print("📝 Generating 5 posts with Grok-3-latest")

    # Create feed generator with Grok-3 override (since Gemini seems to have issues)
    feed_generator = FeedGenerator(model_override="xai/grok-3-latest")

    try:
        # Generate 5 posts
        posts = feed_generator.generate_daily_feed(num_posts=5)

        print(f"\n✅ Successfully generated {len(posts)} posts!")

        # Display each post
        for i, post in enumerate(posts, 1):
            print(f"\n{'='*60}")
            print(f"📝 POST {i}")
            print(f"{'='*60}")
            print(f"🎭 Persona: {post.persona_id}")
            print(f"📚 Type: {post.post_type.value}")
            print(f"📝 Content:")
            print(post.content[:200] + "..." if len(post.content) > 200 else post.content)
            print(f"\n🏷️ Hashtags: {', '.join(post.hashtags[:3])}")
            print(f"📊 Scores:")
            print(f"  • Learning: {post.learning_score:.2f}")
            print(f"  • Engagement: {post.engagement_score:.2f}")
            print(f"  • Breakthrough: {post.breakthrough_potential:.2f}")
            print(f"  • Mood: {post.mood_elevation_score:.2f}")

        print(f"\n🎉 All {len(posts)} posts generated successfully!")

        # Now try Gemini with one post to debug
        print(f"\n{'='*60}")
        print("🧪 DEBUG: Testing Gemini 2.5 Pro with single post...")
        print(f"{'='*60}")

        gemini_generator = FeedGenerator(model_override="gemini/gemini-2.5-pro")
        try:
            gemini_posts = gemini_generator.generate_daily_feed(num_posts=1)
            if gemini_posts:
                print("✅ Gemini generated content successfully!")
                print(f"Content: {gemini_posts[0].content[:100]}...")
            else:
                print("❌ Gemini returned empty results")
        except Exception as e:
            print(f"❌ Gemini error: {e}")

    except Exception as e:
        print(f"❌ Error generating posts: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()