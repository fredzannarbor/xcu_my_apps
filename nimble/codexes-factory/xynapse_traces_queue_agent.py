#!/usr/bin/env python3
"""
Xynapse Traces Queue-Based Agent

Two modes:
1. QUEUE mode (runs via cron): Selects tasks and adds to queue
2. EXECUTE mode (interactive): Processes queued tasks using Claude Code

Usage:
  ./xynapse_traces_queue_agent.py queue    # Add task to queue (cron)
  ./xynapse_traces_queue_agent.py execute  # Show queue for Claude to execute
  ./xynapse_traces_queue_agent.py status   # Check queue status
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
import random
import pandas as pd

class XynapseTracesQueueAgent:
    """Queue-based agent for Xynapse Traces imprint."""

    def __init__(self):
        self.base_dir = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory")
        self.imprint_dir = self.base_dir / "imprints" / "xynapse_traces"
        self.queue_dir = self.imprint_dir / "agent_queue"
        self.output_dir = self.imprint_dir / "agent_outputs"

        self.queue_file = self.queue_dir / "task_queue.json"
        self.log_file = self.output_dir / "agent_log.json"
        self.catalog_file = self.imprint_dir / "books.csv"

        # Ensure directories exist
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load queue and history
        self.queue = self.load_queue()
        self.history = self.load_history()

        # Define all 16 tasks
        self.tasks = {
            # Bracket 1: Content Creation (External-Facing)
            1: {
                "name": "Generate social media post about catalog book",
                "category": "content_creation",
                "frequency": "high",
                "output_dir": "social_media",
                "prompt_template": self.get_social_media_prompt
            },
            2: {
                "name": "Write short blog post on pilsa/transcriptive meditation",
                "category": "content_creation",
                "frequency": "medium",
                "output_dir": "blog_posts",
                "prompt_template": self.get_blog_post_prompt
            },
            3: {
                "name": "Create book spotlight feature for newsletter",
                "category": "content_creation",
                "frequency": "medium",
                "output_dir": "newsletters",
                "prompt_template": self.get_book_spotlight_prompt
            },
            4: {
                "name": "Draft themed reading list from catalog",
                "category": "content_creation",
                "frequency": "low",
                "output_dir": "reading_lists",
                "prompt_template": self.get_reading_list_prompt
            },

            # Bracket 2: Catalog Development
            5: {
                "name": "Write back cover copy for book needing it",
                "category": "catalog_development",
                "frequency": "medium",
                "output_dir": "back_cover_copy",
                "prompt_template": self.get_back_cover_prompt
            },
            6: {
                "name": "Generate metadata improvements for book",
                "category": "catalog_development",
                "frequency": "high",
                "output_dir": "metadata",
                "prompt_template": self.get_metadata_prompt
            },
            7: {
                "name": "Create publisher's note for book",
                "category": "catalog_development",
                "frequency": "medium",
                "output_dir": "publishers_notes",
                "prompt_template": self.get_publishers_note_prompt
            },
            8: {
                "name": "Research and draft author bio enhancement",
                "category": "catalog_development",
                "frequency": "low",
                "output_dir": "author_bios",
                "prompt_template": self.get_author_bio_prompt
            },

            # Bracket 3: Marketing & Discovery
            9: {
                "name": "Generate Amazon A+ content module",
                "category": "marketing",
                "frequency": "medium",
                "output_dir": "amazon_content",
                "prompt_template": self.get_amazon_aplus_prompt
            },
            10: {
                "name": "Create book comparison chart",
                "category": "marketing",
                "frequency": "low",
                "output_dir": "comparisons",
                "prompt_template": self.get_comparison_chart_prompt
            },
            11: {
                "name": "Draft retailer pitch for specific book",
                "category": "marketing",
                "frequency": "low",
                "output_dir": "retailer_pitches",
                "prompt_template": self.get_retailer_pitch_prompt
            },
            12: {
                "name": "Generate reader testimonial request template",
                "category": "marketing",
                "frequency": "low",
                "output_dir": "templates",
                "prompt_template": self.get_testimonial_request_prompt
            },

            # Bracket 4: Strategic Development
            13: {
                "name": "Identify potential new book topics from trends",
                "category": "strategic",
                "frequency": "low",
                "output_dir": "strategic",
                "prompt_template": self.get_new_topics_prompt
            },
            14: {
                "name": "Create educational content about imprint mission",
                "category": "strategic",
                "frequency": "medium",
                "output_dir": "mission",
                "prompt_template": self.get_mission_content_prompt
            },
            15: {
                "name": "Generate partnership/collaboration opportunity brief",
                "category": "strategic",
                "frequency": "low",
                "output_dir": "partnerships",
                "prompt_template": self.get_partnership_brief_prompt
            },
            16: {
                "name": "Develop seasonal catalog promotion concept",
                "category": "strategic",
                "frequency": "low",
                "output_dir": "promotions",
                "prompt_template": self.get_seasonal_promotion_prompt
            }
        }

    def load_queue(self):
        """Load task queue."""
        if self.queue_file.exists():
            with open(self.queue_file, 'r') as f:
                return json.load(f)
        return []

    def save_queue(self):
        """Save task queue."""
        with open(self.queue_file, 'w') as f:
            json.dump(self.queue, f, indent=2)

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
        """Get tasks executed/queued in last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        recent = []

        # Check execution history
        for entry in self.history:
            task_date = datetime.fromisoformat(entry['timestamp'])
            if task_date > cutoff:
                recent.append(entry['task_id'])

        # Check queue
        for entry in self.queue:
            if entry.get('status') != 'completed':
                task_date = datetime.fromisoformat(entry['queued_at'])
                if task_date > cutoff:
                    recent.append(entry['task_id'])

        return recent

    def select_task(self):
        """Intelligently select which task to queue today."""
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

    def get_random_books(self, n=5):
        """Get N random books from catalog."""
        catalog = self.load_catalog()
        if len(catalog) > 0:
            sample_size = min(n, len(catalog))
            books = catalog.sample(n=sample_size)
            return [row.to_dict() for _, row in books.iterrows()]
        return []

    # ========== PROMPT TEMPLATES ==========

    def get_social_media_prompt(self, context):
        """Generate social media post prompt."""
        book = context.get('book')
        isbn = book.get('isbn13', 'UNKNOWN')
        pub_date = book.get('publication_date', '')
        return f"""Create a concise, engaging social media post (280 chars max) for:

Book: {book.get('title', 'Unknown')}
Subtitle: {book.get('subtitle', '')}
Author: {book.get('author', 'AI Lab for Book-Lovers')}
Description: {book.get('back_cover_text', '')[:200]}
ISBN: {isbn}
Publication Date: {pub_date}

Imprint: xynapse traces (pilsa/transcriptive meditation practice)
Tone: Thoughtful, inviting, intellectually curious
Include: Relevant hashtags

IMPORTANT INSTRUCTIONS:
1. Whenever you mention "pilsa", include the Korean term 필사 in parentheses immediately after.
2. Check publication date vs today's date (2025-10-13):
   - If book IS PUBLISHED (pub date <= today): Add a separate short comment with link: /Bookstore?isbn={isbn}
   - If book NOT YET PUBLISHED (pub date > today): Mention "Coming {pub_date}" instead of link

Output: Save to file named 'social_post_YYYYMMDD.txt' with today's date"""

    def get_blog_post_prompt(self, context):
        """Generate blog post prompt."""
        return """Write a 300-500 word blog post about pilsa (필사), the Korean practice of copying literary passages.

Focus: How this ancient practice relates to modern knowledge work, mindfulness, and deep reading.
Tone: Educational but accessible, reflective
Audience: Book lovers, knowledge workers, mindfulness practitioners

Connect to xynapse traces imprint mission of pairing readers with frontier knowledge.

IMPORTANT: Whenever you mention "pilsa", include the Korean term 필사 in parentheses immediately after.

Output: Save as markdown file 'blog_pilsa_YYYYMMDD.md' with today's date"""

    def get_book_spotlight_prompt(self, context):
        """Generate newsletter spotlight prompt."""
        book = context.get('book')
        pub_date = book.get('publication_date', '')
        return f"""Create a newsletter book spotlight feature (200-300 words) for:

Title: {book.get('title')}
Subtitle: {book.get('subtitle', '')}
Author: {book.get('author')}
Description: {book.get('back_cover_text', '')[:300]}
Publication Date: {pub_date}

Include:
- Why this book matters now
- Key insights or themes
- Who should read it
- Connection to pilsa/transcriptive meditation practice

Tone: Engaging, intellectually curious, inviting

IMPORTANT INSTRUCTIONS:
1. Whenever you mention "pilsa", include the Korean term 필사 in parentheses immediately after.
2. Check publication date vs today (2025-10-13):
   - If published: Available now
   - If upcoming: "Coming on {pub_date}"

Output: Save as 'spotlight_YYYYMMDD_ISBN.md' with today's date and book ISBN"""

    def get_reading_list_prompt(self, context):
        """Generate reading list prompt."""
        books = context.get('books', [])
        book_list = "\n".join([f"- {b['title']}: {b.get('subtitle', '')}" for b in books])

        return f"""Create a themed reading list from these xynapse traces books:

{book_list}

Task: Identify the unifying theme and create a compelling reading list description (200 words).
Include: Theme title, why these books work together, reading order suggestion.
Tone: Curatorial, insightful

IMPORTANT: Whenever you mention "pilsa", include the Korean term 필사 in parentheses immediately after.

Output: Save as 'reading_list_YYYYMMDD.md' with today's date and book list appended"""

    def get_back_cover_prompt(self, context):
        """Generate back cover copy prompt."""
        book = context.get('book')
        return f"""Write compelling back cover copy (150-200 words) for:

Title: {book.get('title')}
Subtitle: {book.get('subtitle', '')}
Author: {book.get('author')}
Context: Part of xynapse traces imprint (pilsa-inspired transcriptive meditation practice)

Create copy that:
- Opens with hook
- Explains what reader will gain
- Positions within pilsa tradition
- Ends with compelling reason to read

Tone: Thoughtful, inviting, intellectually ambitious

IMPORTANT: Whenever you mention "pilsa", include the Korean term 필사 in parentheses immediately after.

Output: Save as 'back_cover_ISBN_YYYYMMDD.txt' with ISBN and today's date"""

    def get_metadata_prompt(self, context):
        """Generate metadata improvement prompt."""
        book = context.get('book')
        return f"""Suggest metadata improvements for:

Title: {book.get('title')}
Current subtitle: {book.get('subtitle', '[none]')}
Current description: {book.get('back_cover_text', '[none]')[:200]}

Provide:
1. Improved subtitle (if needed)
2. 5 BISAC categories
3. 10 keywords for discoverability
4. Short description (50 words) for online retailers

Format as structured text.

IMPORTANT: Whenever you mention "pilsa", include the Korean term 필사 in parentheses immediately after.

Output: Save as 'metadata_ISBN_YYYYMMDD.txt' with ISBN and today's date"""

    def get_publishers_note_prompt(self, context):
        """Generate publisher's note prompt."""
        book = context.get('book')
        return f"""Write a publisher's note (100-150 words) for:

Title: {book.get('title')}
Subtitle: {book.get('subtitle', '')}
Context: xynapse traces imprint, pilsa-inspired practice

Explain:
- Why we published this book
- How it fits xynapse traces mission
- What makes it special
- How to approach reading it

Tone: Personal, curatorial, inviting

IMPORTANT: Whenever you mention "pilsa", include the Korean term 필사 in parentheses immediately after.

Output: Save as 'publishers_note_ISBN_YYYYMMDD.txt' with ISBN and today's date"""

    def get_author_bio_prompt(self, context):
        """Generate author bio prompt."""
        author = context.get('author', 'AI Lab for Book-Lovers')
        return f"""Create an author bio (100 words) for:

Author: {author}
Context: {author} writes for xynapse traces, an experimental imprint exploring AI-human collaboration in book creation

Create bio that:
- Establishes credibility
- Connects to pilsa tradition
- Explains approach to knowledge synthesis
- Invites reader connection

Tone: Thoughtful, innovative, accessible

IMPORTANT: Whenever you mention "pilsa", include the Korean term 필사 in parentheses immediately after.

Output: Save as 'author_bio_AUTHORNAME_YYYYMMDD.txt' with author name and today's date"""

    def get_amazon_aplus_prompt(self, context):
        """Generate Amazon A+ content prompt."""
        book = context.get('book')
        pub_date = book.get('publication_date', '')
        return f"""Create Amazon A+ Enhanced Content module for:

Title: {book.get('title')}
Description: {book.get('back_cover_text', '')[:300]}
Publication Date: {pub_date}

Provide:
1. Module headline (15 words max)
2. Feature 1: What you'll learn (50 words)
3. Feature 2: Who this is for (50 words)
4. Feature 3: Why it matters now (50 words)

Format for copy-paste into Amazon.

IMPORTANT INSTRUCTIONS:
1. Whenever you mention "pilsa", include the Korean term 필사 in parentheses immediately after.
2. If book is not yet published (pub date > today 2025-10-13), mention availability date.

Output: Save as 'amazon_aplus_ISBN_YYYYMMDD.txt' with ISBN and today's date"""

    def get_comparison_chart_prompt(self, context):
        """Generate comparison chart prompt."""
        book = context.get('book')
        pub_date = book.get('publication_date', '')
        return f"""Create a comparison chart showing how this book differs from similar books:

Our Book: {book.get('title')}
Description: {book.get('back_cover_text', '')[:200]}
Publication Date: {pub_date}

Create markdown table comparing:
- Our book vs. traditional books on similar topics
- Key differentiators (3-4)
- Unique xynapse traces approach

Make compelling case for our book.

IMPORTANT INSTRUCTIONS:
1. Whenever you mention "pilsa", include the Korean term 필사 in parentheses immediately after.
2. If book not yet published (pub date > today 2025-10-13), note as "Forthcoming {pub_date}".

Output: Save as 'comparison_ISBN_YYYYMMDD.md' with ISBN and today's date"""

    def get_retailer_pitch_prompt(self, context):
        """Generate retailer pitch prompt."""
        book = context.get('book')
        pub_date = book.get('publication_date', '')
        return f"""Write a pitch to independent bookstores (200 words) for:

Title: {book.get('title')}
Publisher: Nimble Books / xynapse traces
Description: {book.get('back_cover_text', '')[:300]}
Publication Date: {pub_date}

Include:
- Why this fits their customers
- Unique selling points
- Display/merchandising suggestions
- Conversation starters for handselling

Tone: Professional, enthusiastic, practical

IMPORTANT INSTRUCTIONS:
1. Whenever you mention "pilsa", include the Korean term 필사 in parentheses immediately after.
2. Check publication status vs today (2025-10-13):
   - If published: Focus on "available now"
   - If upcoming: Frame as "advance notice" and include release date

Output: Save as 'retailer_pitch_ISBN_YYYYMMDD.txt' with ISBN and today's date"""

    def get_testimonial_request_prompt(self, context):
        """Generate testimonial request prompt."""
        return """Create an email template for requesting reader testimonials for xynapse traces books.

Include:
- Warm greeting
- Why we value their feedback
- Specific prompts for testimonial (3-4 questions)
- Permission to use quote
- Thank you

Tone: Personal, grateful, non-pushy
Length: 150 words

IMPORTANT: Whenever you mention "pilsa", include the Korean term 필사 in parentheses immediately after.

Output: Save as 'testimonial_request_YYYYMMDD.txt' with today's date"""

    def get_new_topics_prompt(self, context):
        """Generate new topics prompt."""
        return """Identify 5 potential book topics for xynapse traces imprint.

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

Format as structured list.

IMPORTANT: Whenever you mention "pilsa", include the Korean term 필사 in parentheses immediately after.

Output: Save as 'new_topics_YYYYMMDD.md' with today's date"""

    def get_mission_content_prompt(self, context):
        """Generate mission content prompt."""
        return """Write educational content (300 words) explaining xynapse traces imprint mission.

Cover:
- What is pilsa (필사) and why it matters
- How xynapse traces adapts this for modern readers
- The role of AI-human collaboration
- What makes our books different
- How to engage with transcriptive meditation practice

Audience: Potential readers, press, partners
Tone: Educational, inspiring, clear

IMPORTANT: Whenever you mention "pilsa", include the Korean term 필사 in parentheses immediately after.

Output: Save as 'mission_content_YYYYMMDD.md' with today's date"""

    def get_partnership_brief_prompt(self, context):
        """Generate partnership brief prompt."""
        return """Draft a partnership opportunity brief (250 words) for xynapse traces.

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

Tone: Professional, collaborative, open

IMPORTANT: Whenever you mention "pilsa", include the Korean term 필사 in parentheses immediately after.

Output: Save as 'partnership_brief_YYYYMMDD.md' with today's date"""

    def get_seasonal_promotion_prompt(self, context):
        """Generate seasonal promotion prompt."""
        season = context.get('season', 'Current')
        books = context.get('books', [])
        return f"""Create a {season} catalog promotion concept for xynapse traces.

Books available (with publication dates):
{chr(10).join([f"- {b.get('title')}: {b.get('publication_date', 'TBD')}" for b in books])}

Include:
- Seasonal theme/angle
- 3-5 featured books to highlight
- Promotion message (100 words)
- Social media angle
- Email subject line

Connect season to reading/learning/contemplation themes.
Tone: Seasonal, inviting, thoughtful

IMPORTANT INSTRUCTIONS:
1. Whenever you mention "pilsa", include the Korean term 필사 in parentheses immediately after.
2. For each book, check publication date vs today (2025-10-13):
   - Published books: "Available now"
   - Upcoming books: "Coming {pub_date}"

Output: Save as 'seasonal_promo_SEASON_YYYYMMDD.md' with season and today's date"""

    # ========== QUEUE OPERATIONS ==========

    def queue_task(self):
        """Select a task and add to queue (runs daily via cron)."""
        print(f"\n{'='*60}")
        print(f"Xynapse Traces Agent - QUEUE MODE")
        print(f"Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        # Select task
        task_id, task_info = self.select_task()

        # Prepare context
        context = {}
        if 'book' in task_info['prompt_template'].__code__.co_varnames:
            context['book'] = self.get_random_book()
        if 'books' in task_info['prompt_template'].__code__.co_varnames:
            context['books'] = self.get_random_books(5)
        if 'season' in task_info['prompt_template'].__code__.co_varnames:
            month = datetime.now().month
            if month in [12, 1, 2]:
                season = "Winter"
            elif month in [3, 4, 5]:
                season = "Spring"
            elif month in [6, 7, 8]:
                season = "Summer"
            else:
                season = "Fall"
            context['season'] = season
        if 'author' in task_info['prompt_template'].__code__.co_varnames:
            book = self.get_random_book()
            context['author'] = book.get('author') if book else 'AI Lab for Book-Lovers'

        # Generate prompt
        prompt = task_info['prompt_template'](context)

        # Add to queue
        queue_entry = {
            'queue_id': f"q{len(self.queue) + 1:04d}",
            'task_id': task_id,
            'task_name': task_info['name'],
            'category': task_info['category'],
            'output_dir': task_info['output_dir'],
            'prompt': prompt,
            'context': {k: str(v)[:200] for k, v in context.items()},  # Truncate for storage
            'queued_at': datetime.now().isoformat(),
            'status': 'pending'
        }

        self.queue.append(queue_entry)
        self.save_queue()

        print(f"✅ Queued task #{task_id}: {task_info['name']}")
        print(f"   Category: {task_info['category']}")
        print(f"   Queue ID: {queue_entry['queue_id']}")
        print(f"   Total queued: {len([q for q in self.queue if q['status'] == 'pending'])}")
        print(f"\n{'='*60}\n")

    def show_queue_status(self):
        """Show current queue status."""
        pending = [q for q in self.queue if q['status'] == 'pending']
        completed = [q for q in self.queue if q['status'] == 'completed']

        print(f"\n{'='*60}")
        print(f"Xynapse Traces Agent - QUEUE STATUS")
        print(f"{'='*60}\n")
        print(f"📋 Pending tasks: {len(pending)}")
        print(f"✅ Completed tasks: {len(completed)}")
        print(f"\n")

        if pending:
            print("Pending Tasks:")
            print("-" * 60)
            for task in pending:
                print(f"  [{task['queue_id']}] {task['task_name']}")
                print(f"      Queued: {task['queued_at'][:10]}")
                print(f"      Category: {task['category']}")
                print()

        print(f"{'='*60}\n")

    def export_for_claude(self):
        """Export pending tasks for Claude Code execution."""
        pending = [q for q in self.queue if q['status'] == 'pending']

        if not pending:
            print("\n✅ No pending tasks in queue!\n")
            return

        export = {
            'tasks': pending,
            'output_base': str(self.output_dir),
            'exported_at': datetime.now().isoformat()
        }

        export_file = self.queue_dir / "claude_execution_batch.json"
        with open(export_file, 'w') as f:
            json.dump(export, f, indent=2)

        print(f"\n{'='*60}")
        print(f"Xynapse Traces Agent - READY FOR EXECUTION")
        print(f"{'='*60}\n")
        print(f"📦 Exported {len(pending)} tasks for Claude Code")
        print(f"📁 Export file: {export_file}")
        print(f"\n")
        print("Next steps:")
        print("1. In Claude Code, say: 'execute xynapse queue'")
        print("2. I'll process all pending tasks using Claude Max")
        print("3. All outputs will be saved automatically")
        print(f"\n{'='*60}\n")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python xynapse_traces_queue_agent.py queue    # Add task to queue (daily cron)")
        print("  python xynapse_traces_queue_agent.py execute  # Prepare for Claude execution")
        print("  python xynapse_traces_queue_agent.py status   # Show queue status")
        sys.exit(1)

    mode = sys.argv[1].lower()
    agent = XynapseTracesQueueAgent()

    if mode == 'queue':
        agent.queue_task()
    elif mode == 'execute':
        agent.export_for_claude()
    elif mode == 'status':
        agent.show_queue_status()
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
