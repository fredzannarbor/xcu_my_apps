#!/usr/bin/env python3
"""
Xynapse Traces Daily Agent

Runs once per day, selects one task from 16 options, and executes it.
Intelligently chooses based on:
- Recent activity (avoid repeating same tasks)
- Strategic priorities
- Content needs
- Catalog status
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
import random
import pandas as pd

# Add to path for imports
sys.path.insert(0, '/Users/fred/xcu_my_apps')

try:
    from nimble_llm_caller import LLMCaller
    HAS_LLM = True
except ImportError:
    HAS_LLM = False
    print("Warning: nimble-llm-caller not available, using mock mode")


class XynapseTracesAgent:
    """Daily autonomous agent for Xynapse Traces imprint."""

    def __init__(self):
        self.base_dir = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory")
        self.imprint_dir = self.base_dir / "imprints" / "xynapse_traces"
        self.output_dir = self.imprint_dir / "agent_outputs"
        self.log_file = self.output_dir / "agent_log.json"
        self.catalog_file = self.imprint_dir / "books.csv"

        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load history
        self.history = self.load_history()

        # Initialize LLM if available
        self.llm = LLMCaller(model="gpt-4o-mini") if HAS_LLM else None

        # Define all 16 tasks
        self.tasks = {
            # Bracket 1: Content Creation (External-Facing)
            1: {
                "name": "Generate social media post about catalog book",
                "category": "content_creation",
                "frequency": "high",  # Can do often
                "function": self.task_social_media_post
            },
            2: {
                "name": "Write short blog post on pilsa/transcriptive meditation",
                "category": "content_creation",
                "frequency": "medium",
                "function": self.task_blog_post
            },
            3: {
                "name": "Create book spotlight feature for newsletter",
                "category": "content_creation",
                "frequency": "medium",
                "function": self.task_book_spotlight
            },
            4: {
                "name": "Draft themed reading list from catalog",
                "category": "content_creation",
                "frequency": "low",
                "function": self.task_reading_list
            },

            # Bracket 2: Catalog Development
            5: {
                "name": "Write back cover copy for book needing it",
                "category": "catalog_development",
                "frequency": "medium",
                "function": self.task_back_cover_copy
            },
            6: {
                "name": "Generate metadata improvements for book",
                "category": "catalog_development",
                "frequency": "high",
                "function": self.task_metadata_improvement
            },
            7: {
                "name": "Create publisher's note for book",
                "category": "catalog_development",
                "frequency": "medium",
                "function": self.task_publishers_note
            },
            8: {
                "name": "Research and draft author bio enhancement",
                "category": "catalog_development",
                "frequency": "low",
                "function": self.task_author_bio
            },

            # Bracket 3: Marketing & Discovery
            9: {
                "name": "Generate Amazon A+ content module",
                "category": "marketing",
                "frequency": "medium",
                "function": self.task_amazon_aplus
            },
            10: {
                "name": "Create book comparison chart",
                "category": "marketing",
                "frequency": "low",
                "function": self.task_comparison_chart
            },
            11: {
                "name": "Draft retailer pitch for specific book",
                "category": "marketing",
                "frequency": "low",
                "function": self.task_retailer_pitch
            },
            12: {
                "name": "Generate reader testimonial request template",
                "category": "marketing",
                "frequency": "low",
                "function": self.task_testimonial_request
            },

            # Bracket 4: Strategic Development
            13: {
                "name": "Identify potential new book topics from trends",
                "category": "strategic",
                "frequency": "low",
                "function": self.task_new_topics
            },
            14: {
                "name": "Create educational content about imprint mission",
                "category": "strategic",
                "frequency": "medium",
                "function": self.task_mission_content
            },
            15: {
                "name": "Generate partnership/collaboration opportunity brief",
                "category": "strategic",
                "frequency": "low",
                "function": self.task_partnership_brief
            },
            16: {
                "name": "Develop seasonal catalog promotion concept",
                "category": "strategic",
                "frequency": "low",
                "function": self.task_seasonal_promotion
            }
        }

    def load_history(self):
        """Load task execution history."""
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                return json.load(f)
        return []

    def save_history(self):
        """Save task execution history."""
        with open(self.log_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def get_recent_tasks(self, days=7):
        """Get tasks executed in last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        recent = []
        for entry in self.history:
            task_date = datetime.fromisoformat(entry['timestamp'])
            if task_date > cutoff:
                recent.append(entry['task_id'])
        return recent

    def select_task(self):
        """Intelligently select which task to run today."""
        recent_tasks = self.get_recent_tasks(days=7)

        # Calculate weights for each task
        weights = []
        task_ids = []

        for task_id, task_info in self.tasks.items():
            # Base weight by frequency
            frequency_weight = {
                'high': 3.0,
                'medium': 2.0,
                'low': 1.0
            }[task_info['frequency']]

            # Reduce weight if done recently
            recent_penalty = recent_tasks.count(task_id) * 0.3

            # Calculate final weight
            final_weight = max(0.1, frequency_weight - recent_penalty)

            weights.append(final_weight)
            task_ids.append(task_id)

        # Select task based on weights
        selected_id = random.choices(task_ids, weights=weights)[0]
        return selected_id, self.tasks[selected_id]

    def load_catalog(self):
        """Load the xynapse traces catalog."""
        if self.catalog_file.exists():
            return pd.read_csv(self.catalog_file)
        return pd.DataFrame()

    def get_random_book(self):
        """Get a random book from catalog."""
        catalog = self.load_catalog()
        if len(catalog) > 0:
            book = catalog.sample(n=1).iloc[0]
            return book.to_dict()
        return None

    def call_llm(self, prompt, max_tokens=1000):
        """Call LLM with prompt."""
        if not self.llm:
            return f"[Mock LLM Response: Would generate content for: {prompt[:100]}...]"

        response = self.llm.call(prompt, max_tokens=max_tokens)
        return response.get('content', '')

    # ========== TASK IMPLEMENTATIONS ==========

    def task_social_media_post(self):
        """Generate social media post about a catalog book."""
        book = self.get_random_book()
        if not book:
            return "No books in catalog"

        prompt = f"""Create a concise, engaging social media post (280 chars max) for:

Book: {book.get('title', 'Unknown')}
Subtitle: {book.get('subtitle', '')}
Author: {book.get('author', 'AI Lab for Book-Lovers')}
Description: {book.get('back_cover_text', '')[:200]}

Imprint: xynapse traces (pilsa/transcriptive meditation practice)
Tone: Thoughtful, inviting, intellectually curious
Include: Relevant hashtags"""

        content = self.call_llm(prompt)

        filename = f"social_post_{datetime.now().strftime('%Y%m%d')}.txt"
        output_path = self.output_dir / "social_media" / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(f"Book: {book.get('title')}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write(content)

        return f"Created social media post for '{book.get('title')}'"

    def task_blog_post(self):
        """Write short blog post on pilsa/transcriptive meditation."""
        prompt = """Write a 300-500 word blog post about pilsa (필사), the Korean practice of copying literary passages.

Focus: How this ancient practice relates to modern knowledge work, mindfulness, and deep reading.
Tone: Educational but accessible, reflective
Audience: Book lovers, knowledge workers, mindfulness practitioners

Connect to xynapse traces imprint mission of pairing readers with frontier knowledge."""

        content = self.call_llm(prompt, max_tokens=800)

        filename = f"blog_pilsa_{datetime.now().strftime('%Y%m%d')}.md"
        output_path = self.output_dir / "blog_posts" / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(f"# Pilsa: Ancient Practice for Modern Minds\n\n")
            f.write(f"*Generated: {datetime.now().strftime('%B %d, %Y')}*\n\n")
            f.write(content)

        return "Created blog post on pilsa practice"

    def task_book_spotlight(self):
        """Create book spotlight feature for newsletter."""
        book = self.get_random_book()
        if not book:
            return "No books in catalog"

        prompt = f"""Create a newsletter book spotlight feature (200-300 words) for:

Title: {book.get('title')}
Subtitle: {book.get('subtitle', '')}
Author: {book.get('author')}
Description: {book.get('back_cover_text', '')[:300]}

Include:
- Why this book matters now
- Key insights or themes
- Who should read it
- Connection to pilsa/transcriptive meditation practice

Tone: Engaging, intellectually curious, inviting"""

        content = self.call_llm(prompt, max_tokens=600)

        filename = f"spotlight_{datetime.now().strftime('%Y%m%d')}_{book.get('isbn13', 'unknown')}.md"
        output_path = self.output_dir / "newsletters" / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(f"# Book Spotlight: {book.get('title')}\n\n")
            f.write(content)

        return f"Created newsletter spotlight for '{book.get('title')}'"

    def task_reading_list(self):
        """Draft themed reading list from catalog."""
        catalog = self.load_catalog()
        if len(catalog) < 3:
            return "Not enough books for reading list"

        # Sample 3-5 books
        sample_size = min(5, len(catalog))
        books = catalog.sample(n=sample_size)

        book_list = "\n".join([
            f"- {row['title']}: {row.get('subtitle', '')}"
            for _, row in books.iterrows()
        ])

        prompt = f"""Create a themed reading list from these xynapse traces books:

{book_list}

Task: Identify the unifying theme and create a compelling reading list description (200 words).
Include: Theme title, why these books work together, reading order suggestion.
Tone: Curatorial, insightful"""

        content = self.call_llm(prompt, max_tokens=500)

        filename = f"reading_list_{datetime.now().strftime('%Y%m%d')}.md"
        output_path = self.output_dir / "reading_lists" / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(f"# Curated Reading List\n\n")
            f.write(f"*Generated: {datetime.now().strftime('%B %d, %Y')}*\n\n")
            f.write(content)
            f.write("\n\n## Books in this list:\n\n")
            for _, row in books.iterrows():
                f.write(f"- **{row['title']}** by {row['author']}\n")

        return f"Created themed reading list with {sample_size} books"

    def task_back_cover_copy(self):
        """Write back cover copy for book."""
        book = self.get_random_book()
        if not book or book.get('back_cover_text'):
            return "No suitable book found (needs empty back cover)"

        prompt = f"""Write compelling back cover copy (150-200 words) for:

Title: {book.get('title')}
Subtitle: {book.get('subtitle', '')}
Author: {book.get('author')}
Context: Part of xynapse traces imprint (pilsa-inspired transcriptive meditation practice)

Create copy that:
- Opens with hook
- Explains what reader will gain
- Positions within pilsa tradition
- Ends with compelling reason to read

Tone: Thoughtful, inviting, intellectually ambitious"""

        content = self.call_llm(prompt, max_tokens=400)

        filename = f"back_cover_{book.get('isbn13', 'unknown')}_{datetime.now().strftime('%Y%m%d')}.txt"
        output_path = self.output_dir / "back_cover_copy" / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(f"Book: {book.get('title')}\n")
            f.write(f"ISBN: {book.get('isbn13')}\n\n")
            f.write(content)

        return f"Created back cover copy for '{book.get('title')}'"

    def task_metadata_improvement(self):
        """Generate metadata improvements."""
        book = self.get_random_book()
        if not book:
            return "No books in catalog"

        prompt = f"""Suggest metadata improvements for:

Title: {book.get('title')}
Current subtitle: {book.get('subtitle', '[none]')}
Current description: {book.get('back_cover_text', '[none]')[:200]}

Provide:
1. Improved subtitle (if needed)
2. 5 BISAC categories
3. 10 keywords for discoverability
4. Short description (50 words) for online retailers

Format as structured JSON."""

        content = self.call_llm(prompt, max_tokens=600)

        filename = f"metadata_{book.get('isbn13', 'unknown')}_{datetime.now().strftime('%Y%m%d')}.txt"
        output_path = self.output_dir / "metadata" / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(f"Book: {book.get('title')}\n")
            f.write(f"ISBN: {book.get('isbn13')}\n\n")
            f.write(content)

        return f"Generated metadata improvements for '{book.get('title')}'"

    def task_publishers_note(self):
        """Create publisher's note."""
        book = self.get_random_book()
        if not book:
            return "No books in catalog"

        prompt = f"""Write a publisher's note (100-150 words) for:

Title: {book.get('title')}
Subtitle: {book.get('subtitle', '')}
Context: xynapse traces imprint, pilsa-inspired practice

Explain:
- Why we published this book
- How it fits xynapse traces mission
- What makes it special
- How to approach reading it

Tone: Personal, curatorial, inviting"""

        content = self.call_llm(prompt, max_tokens=400)

        filename = f"publishers_note_{book.get('isbn13', 'unknown')}_{datetime.now().strftime('%Y%m%d')}.txt"
        output_path = self.output_dir / "publishers_notes" / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(f"Publisher's Note: {book.get('title')}\n\n")
            f.write(content)

        return f"Created publisher's note for '{book.get('title')}'"

    def task_author_bio(self):
        """Research and draft author bio enhancement."""
        book = self.get_random_book()
        if not book:
            return "No books in catalog"

        author = book.get('author', 'AI Lab for Book-Lovers')

        prompt = f"""Create an author bio (100 words) for:

Author: {author}
Context: {author} writes for xynapse traces, an experimental imprint exploring AI-human collaboration in book creation

Create bio that:
- Establishes credibility
- Connects to pilsa tradition
- Explains approach to knowledge synthesis
- Invites reader connection

Tone: Thoughtful, innovative, accessible"""

        content = self.call_llm(prompt, max_tokens=300)

        filename = f"author_bio_{author.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt"
        output_path = self.output_dir / "author_bios" / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(f"Author: {author}\n\n")
            f.write(content)

        return f"Created author bio for {author}"

    def task_amazon_aplus(self):
        """Generate Amazon A+ content module."""
        book = self.get_random_book()
        if not book:
            return "No books in catalog"

        prompt = f"""Create Amazon A+ Enhanced Content module for:

Title: {book.get('title')}
Description: {book.get('back_cover_text', '')[:300]}

Provide:
1. Module headline (15 words max)
2. Feature 1: What you'll learn (50 words)
3. Feature 2: Who this is for (50 words)
4. Feature 3: Why it matters now (50 words)

Format for copy-paste into Amazon."""

        content = self.call_llm(prompt, max_tokens=500)

        filename = f"amazon_aplus_{book.get('isbn13', 'unknown')}_{datetime.now().strftime('%Y%m%d')}.txt"
        output_path = self.output_dir / "amazon_content" / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(f"Amazon A+ Content: {book.get('title')}\n\n")
            f.write(content)

        return f"Created Amazon A+ content for '{book.get('title')}'"

    def task_comparison_chart(self):
        """Create book comparison chart."""
        book = self.get_random_book()
        if not book:
            return "No books in catalog"

        prompt = f"""Create a comparison chart showing how this book differs from similar books:

Our Book: {book.get('title')}
Description: {book.get('back_cover_text', '')[:200]}

Create markdown table comparing:
- Our book vs. traditional books on similar topics
- Key differentiators (3-4)
- Unique xynapse traces approach

Make compelling case for our book."""

        content = self.call_llm(prompt, max_tokens=500)

        filename = f"comparison_{book.get('isbn13', 'unknown')}_{datetime.now().strftime('%Y%m%d')}.md"
        output_path = self.output_dir / "comparisons" / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(f"# Book Comparison: {book.get('title')}\n\n")
            f.write(content)

        return f"Created comparison chart for '{book.get('title')}'"

    def task_retailer_pitch(self):
        """Draft retailer pitch."""
        book = self.get_random_book()
        if not book:
            return "No books in catalog"

        prompt = f"""Write a pitch to independent bookstores (200 words) for:

Title: {book.get('title')}
Publisher: Nimble Books / xynapse traces
Description: {book.get('back_cover_text', '')[:300]}

Include:
- Why this fits their customers
- Unique selling points
- Display/merchandising suggestions
- Conversation starters for handselling

Tone: Professional, enthusiastic, practical"""

        content = self.call_llm(prompt, max_tokens=500)

        filename = f"retailer_pitch_{book.get('isbn13', 'unknown')}_{datetime.now().strftime('%Y%m%d')}.txt"
        output_path = self.output_dir / "retailer_pitches" / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(f"Retailer Pitch: {book.get('title')}\n\n")
            f.write(content)

        return f"Created retailer pitch for '{book.get('title')}'"

    def task_testimonial_request(self):
        """Generate reader testimonial request template."""
        prompt = """Create an email template for requesting reader testimonials for xynapse traces books.

Include:
- Warm greeting
- Why we value their feedback
- Specific prompts for testimonial (3-4 questions)
- Permission to use quote
- Thank you

Tone: Personal, grateful, non-pushy
Length: 150 words"""

        content = self.call_llm(prompt, max_tokens=400)

        filename = f"testimonial_request_{datetime.now().strftime('%Y%m%d')}.txt"
        output_path = self.output_dir / "templates" / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            f.write("# Reader Testimonial Request Template\n\n")
            f.write(content)

        return "Created testimonial request template"

    def task_new_topics(self):
        """Identify potential new book topics."""
        prompt = """Identify 5 potential book topics for xynapse traces imprint.

Consider:
- Current trends in science, technology, philosophy
- Topics benefiting from pilsa/transcriptive meditation approach
- Frontier knowledge areas
- Gaps in current catalog

For each topic provide:
- Working title
- Why it fits xynapse traces
- Potential audience
- Unique angle

Format as structured list."""

        content = self.call_llm(prompt, max_tokens=800)

        filename = f"new_topics_{datetime.now().strftime('%Y%m%d')}.md"
        output_path = self.output_dir / "strategic" / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            f.write("# Potential New Book Topics for Xynapse Traces\n\n")
            f.write(f"*Generated: {datetime.now().strftime('%B %d, %Y')}*\n\n")
            f.write(content)

        return "Identified 5 potential new book topics"

    def task_mission_content(self):
        """Create educational content about imprint mission."""
        prompt = """Write educational content (300 words) explaining xynapse traces imprint mission.

Cover:
- What is pilsa (필사) and why it matters
- How xynapse traces adapts this for modern readers
- The role of AI-human collaboration
- What makes our books different
- How to engage with transcriptive meditation practice

Audience: Potential readers, press, partners
Tone: Educational, inspiring, clear"""

        content = self.call_llm(prompt, max_tokens=600)

        filename = f"mission_content_{datetime.now().strftime('%Y%m%d')}.md"
        output_path = self.output_dir / "mission" / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            f.write("# About Xynapse Traces\n\n")
            f.write(content)

        return "Created educational content about imprint mission"

    def task_partnership_brief(self):
        """Generate partnership/collaboration opportunity brief."""
        prompt = """Draft a partnership opportunity brief (250 words) for xynapse traces.

Potential partners:
- Universities (continuing education)
- Mindfulness/meditation apps
- Book clubs
- Knowledge worker communities

Include:
- What we offer
- What we're looking for
- Sample collaboration ideas
- Next steps for interested partners

Tone: Professional, collaborative, open"""

        content = self.call_llm(prompt, max_tokens=600)

        filename = f"partnership_brief_{datetime.now().strftime('%Y%m%d')}.md"
        output_path = self.output_dir / "partnerships" / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            f.write("# Partnership Opportunities: Xynapse Traces\n\n")
            f.write(content)

        return "Created partnership opportunity brief"

    def task_seasonal_promotion(self):
        """Develop seasonal catalog promotion concept."""
        # Determine current season
        month = datetime.now().month
        if month in [12, 1, 2]:
            season = "Winter"
        elif month in [3, 4, 5]:
            season = "Spring"
        elif month in [6, 7, 8]:
            season = "Summer"
        else:
            season = "Fall"

        prompt = f"""Create a {season} catalog promotion concept for xynapse traces.

Include:
- Seasonal theme/angle
- 3-5 featured books to highlight
- Promotion message (100 words)
- Social media angle
- Email subject line

Connect season to reading/learning/contemplation themes.
Tone: Seasonal, inviting, thoughtful"""

        content = self.call_llm(prompt, max_tokens=600)

        filename = f"seasonal_promo_{season.lower()}_{datetime.now().strftime('%Y%m%d')}.md"
        output_path = self.output_dir / "promotions" / filename
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(f"# {season} Catalog Promotion\n\n")
            f.write(content)

        return f"Created {season} catalog promotion concept"

    def run(self):
        """Main execution method - runs once per day."""
        print(f"\n{'='*60}")
        print(f"Xynapse Traces Daily Agent")
        print(f"Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        # Select task
        task_id, task_info = self.select_task()
        print(f"Selected task #{task_id}: {task_info['name']}")
        print(f"Category: {task_info['category']}")
        print(f"Frequency: {task_info['frequency']}\n")

        # Execute task
        try:
            result = task_info['function']()
            print(f"\n✅ Success: {result}")

            # Log execution
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'task_id': task_id,
                'task_name': task_info['name'],
                'category': task_info['category'],
                'result': result,
                'success': True
            }

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'task_id': task_id,
                'task_name': task_info['name'],
                'category': task_info['category'],
                'error': str(e),
                'success': False
            }

        # Save to history
        self.history.append(log_entry)
        self.save_history()

        print(f"\nOutput directory: {self.output_dir}")
        print(f"Log file: {self.log_file}")
        print(f"\n{'='*60}\n")


if __name__ == "__main__":
    agent = XynapseTracesAgent()
    agent.run()
