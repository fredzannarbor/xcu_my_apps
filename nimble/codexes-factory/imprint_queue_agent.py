#!/usr/bin/env python3
"""
Generalized Imprint Queue-Based Agent

Supports multiple imprints with configurable marketing tasks.

Two modes:
1. QUEUE mode (runs via cron): Selects tasks and adds to queue
2. EXECUTE mode (interactive): Processes queued tasks using Claude Code

Usage:
  ./imprint_queue_agent.py queue <imprint_name>    # Add task to queue (cron)
  ./imprint_queue_agent.py execute <imprint_name>  # Show queue for Claude to execute
  ./imprint_queue_agent.py status <imprint_name>   # Check queue status
  ./imprint_queue_agent.py list                    # List all imprints
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
import random
import pandas as pd

class ImprintQueueAgent:
    """Queue-based agent for any imprint."""

    def __init__(self, imprint_name):
        self.base_dir = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory")
        self.imprint_name = imprint_name
        self.imprint_dir = self.base_dir / "imprints" / imprint_name

        # Validate imprint exists
        if not self.imprint_dir.exists():
            raise ValueError(f"Imprint '{imprint_name}' not found at {self.imprint_dir}")

        self.queue_dir = self.imprint_dir / "agent_queue"
        self.output_dir = self.imprint_dir / "agent_outputs"
        self.catalog_file = self.imprint_dir / "books.csv"

        # Load imprint config
        self.config = self.load_imprint_config()

        # Ensure directories exist
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.queue_file = self.queue_dir / "task_queue.json"
        self.log_file = self.output_dir / "agent_log.json"

        # Load queue and history
        self.queue = self.load_queue()
        self.history = self.load_history()

        # Define all 16 tasks (same for all imprints)
        self.tasks = self.define_tasks()

    def load_imprint_config(self):
        """Load imprint-specific configuration."""
        config_file = self.imprint_dir / "agent_config.json"

        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)

        # Default config
        return {
            "name": self.imprint_name,
            "display_name": self.imprint_name.replace('_', ' ').title(),
            "tagline": "Quality books for curious minds",
            "special_practice": None,  # e.g., "pilsa (필사)" for xynapse_traces
            "enabled": True
        }

    def define_tasks(self):
        """Define all 16 marketing tasks."""
        return {
            # Bracket 1: Content Creation (External-Facing)
            1: {
                "name": "Generate social media post about catalog book",
                "category": "content_creation",
                "frequency": "high",
                "output_dir": "social_media",
                "prompt_template": self.get_social_media_prompt
            },
            2: {
                "name": "Write short blog post on imprint mission/practice",
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
        """Load the imprint catalog."""
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

    def get_imprint_context(self):
        """Get imprint-specific context for prompts."""
        practice_info = ""
        if self.config.get('special_practice'):
            practice_info = f" ({self.config['special_practice']})"

        return {
            'name': self.config['display_name'],
            'tagline': self.config['tagline'],
            'practice': practice_info
        }

    # ========== PROMPT TEMPLATES ==========

    def get_social_media_prompt(self, context):
        """Generate social media post prompt."""
        book = context.get('book')
        isbn = book.get('isbn13', 'UNKNOWN')
        pub_date = book.get('publication_date', '')
        imprint = self.get_imprint_context()

        special_instruction = ""
        if self.config.get('special_practice'):
            term = self.config['special_practice'].split('(')[0].strip()
            korean = self.config['special_practice'].split('(')[1].replace(')', '').strip()
            special_instruction = f"\n1. Whenever you mention \"{term}\", include the Korean term {korean} in parentheses immediately after."

        return f"""Create a concise, engaging social media post (280 chars max) for:

Book: {book.get('title', 'Unknown')}
Subtitle: {book.get('subtitle', '')}
Author: {book.get('author', 'AI Lab for Book-Lovers')}
Description: {book.get('back_cover_text', '')[:200]}
ISBN: {isbn}
Publication Date: {pub_date}

Imprint: {imprint['name']}{imprint['practice']}
Tone: Thoughtful, inviting, intellectually curious
Include: Relevant hashtags

IMPORTANT INSTRUCTIONS:{special_instruction}
{"2" if special_instruction else "1"}. Check publication date vs today's date (2025-10-13):
   - If book IS PUBLISHED (pub date <= today): Add a separate short comment with link: /Bookstore?isbn={isbn}
   - If book NOT YET PUBLISHED (pub date > today): Mention "Coming {{pub_date}}" instead of link

Output: Save to file named 'social_post_YYYYMMDD.txt' with today's date"""

    def get_blog_post_prompt(self, context):
        """Generate blog post prompt."""
        imprint = self.get_imprint_context()

        practice_focus = self.config.get('special_practice', 'our unique approach to publishing')
        special_instruction = ""
        if self.config.get('special_practice'):
            term = self.config['special_practice'].split('(')[0].strip()
            korean = self.config['special_practice'].split('(')[1].replace(')', '').strip()
            special_instruction = f"\n\nIMPORTANT: Whenever you mention \"{term}\", include the Korean term {korean} in parentheses immediately after."

        return f"""Write a 300-500 word blog post about {practice_focus}.

Focus: How this practice relates to modern knowledge work, mindfulness, and deep reading.
Tone: Educational but accessible, reflective
Audience: Book lovers, knowledge workers, mindfulness practitioners

Connect to {imprint['name']} imprint mission of pairing readers with meaningful knowledge.{special_instruction}

Output: Save as markdown file 'blog_YYYYMMDD.md' with today's date"""

    def get_book_spotlight_prompt(self, context):
        """Generate newsletter spotlight prompt."""
        book = context.get('book')
        pub_date = book.get('publication_date', '')
        imprint = self.get_imprint_context()

        special_instruction = ""
        if self.config.get('special_practice'):
            term = self.config['special_practice'].split('(')[0].strip()
            korean = self.config['special_practice'].split('(')[1].replace(')', '').strip()
            special_instruction = f"\n1. Whenever you mention \"{term}\", include the Korean term {korean} in parentheses immediately after."

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
- Connection to {imprint['name']}{imprint['practice']}

Tone: Engaging, intellectually curious, inviting

IMPORTANT INSTRUCTIONS:{special_instruction}
{"2" if special_instruction else "1"}. Check publication date vs today (2025-10-13):
   - If published: Available now
   - If upcoming: "Coming on {{pub_date}}"

Output: Save as 'spotlight_YYYYMMDD_ISBN.md' with today's date and book ISBN"""

    def get_reading_list_prompt(self, context):
        """Generate reading list prompt."""
        books = context.get('books', [])
        book_list = "\n".join([f"- {b['title']}: {b.get('subtitle', '')}" for b in books])
        imprint = self.get_imprint_context()

        special_instruction = ""
        if self.config.get('special_practice'):
            term = self.config['special_practice'].split('(')[0].strip()
            korean = self.config['special_practice'].split('(')[1].replace(')', '').strip()
            special_instruction = f"\n\nIMPORTANT: Whenever you mention \"{term}\", include the Korean term {korean} in parentheses immediately after."

        return f"""Create a themed reading list from these {imprint['name']} books:

{book_list}

Task: Identify the unifying theme and create a compelling reading list description (200 words).
Include: Theme title, why these books work together, reading order suggestion.
Tone: Curatorial, insightful{special_instruction}

Output: Save as 'reading_list_YYYYMMDD.md' with today's date and book list appended"""

    def get_back_cover_prompt(self, context):
        """Generate back cover copy prompt."""
        book = context.get('book')
        imprint = self.get_imprint_context()

        special_instruction = ""
        if self.config.get('special_practice'):
            term = self.config['special_practice'].split('(')[0].strip()
            korean = self.config['special_practice'].split('(')[1].replace(')', '').strip()
            special_instruction = f"\n\nIMPORTANT: Whenever you mention \"{term}\", include the Korean term {korean} in parentheses immediately after."

        return f"""Write compelling back cover copy (150-200 words) for:

Title: {book.get('title')}
Subtitle: {book.get('subtitle', '')}
Author: {book.get('author')}
Context: Part of {imprint['name']} imprint{imprint['practice']}

Create copy that:
- Opens with hook
- Explains what reader will gain
- Positions within imprint tradition
- Ends with compelling reason to read

Tone: Thoughtful, inviting, intellectually ambitious{special_instruction}

Output: Save as 'back_cover_ISBN_YYYYMMDD.txt' with ISBN and today's date"""

    def get_metadata_prompt(self, context):
        """Generate metadata improvement prompt."""
        book = context.get('book')
        imprint = self.get_imprint_context()

        special_instruction = ""
        if self.config.get('special_practice'):
            term = self.config['special_practice'].split('(')[0].strip()
            korean = self.config['special_practice'].split('(')[1].replace(')', '').strip()
            special_instruction = f"\n\nIMPORTANT: Whenever you mention \"{term}\", include the Korean term {korean} in parentheses immediately after."

        return f"""Suggest metadata improvements for:

Title: {book.get('title')}
Current subtitle: {book.get('subtitle', '[none]')}
Current description: {book.get('back_cover_text', '[none]')[:200]}
Imprint: {imprint['name']}

Provide:
1. Improved subtitle (if needed)
2. 5 BISAC categories
3. 10 keywords for discoverability
4. Short description (50 words) for online retailers

Format as structured text.{special_instruction}

Output: Save as 'metadata_ISBN_YYYYMMDD.txt' with ISBN and today's date"""

    def get_publishers_note_prompt(self, context):
        """Generate publisher's note prompt."""
        book = context.get('book')
        imprint = self.get_imprint_context()

        special_instruction = ""
        if self.config.get('special_practice'):
            term = self.config['special_practice'].split('(')[0].strip()
            korean = self.config['special_practice'].split('(')[1].replace(')', '').strip()
            special_instruction = f"\n\nIMPORTANT: Whenever you mention \"{term}\", include the Korean term {korean} in parentheses immediately after."

        return f"""Write a publisher's note (100-150 words) for:

Title: {book.get('title')}
Subtitle: {book.get('subtitle', '')}
Context: {imprint['name']} imprint{imprint['practice']}

Explain:
- Why we published this book
- How it fits {imprint['name']} mission
- What makes it special
- How to approach reading it

Tone: Personal, curatorial, inviting{special_instruction}

Output: Save as 'publishers_note_ISBN_YYYYMMDD.txt' with ISBN and today's date"""

    def get_author_bio_prompt(self, context):
        """Generate author bio prompt."""
        author = context.get('author', 'AI Lab for Book-Lovers')
        imprint = self.get_imprint_context()

        special_instruction = ""
        if self.config.get('special_practice'):
            term = self.config['special_practice'].split('(')[0].strip()
            korean = self.config['special_practice'].split('(')[1].replace(')', '').strip()
            special_instruction = f"\n\nIMPORTANT: Whenever you mention \"{term}\", include the Korean term {korean} in parentheses immediately after."

        return f"""Create an author bio (100 words) for:

Author: {author}
Context: {author} writes for {imprint['name']}, exploring AI-human collaboration in book creation

Create bio that:
- Establishes credibility
- Connects to imprint tradition{imprint['practice']}
- Explains approach to knowledge synthesis
- Invites reader connection

Tone: Thoughtful, innovative, accessible{special_instruction}

Output: Save as 'author_bio_AUTHORNAME_YYYYMMDD.txt' with author name and today's date"""

    def get_amazon_aplus_prompt(self, context):
        """Generate Amazon A+ content prompt."""
        book = context.get('book')
        pub_date = book.get('publication_date', '')

        special_instruction = ""
        if self.config.get('special_practice'):
            term = self.config['special_practice'].split('(')[0].strip()
            korean = self.config['special_practice'].split('(')[1].replace(')', '').strip()
            special_instruction = f"\n1. Whenever you mention \"{term}\", include the Korean term {korean} in parentheses immediately after."

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

IMPORTANT INSTRUCTIONS:{special_instruction}
{"2" if special_instruction else "1"}. If book is not yet published (pub date > today 2025-10-13), mention availability date.

Output: Save as 'amazon_aplus_ISBN_YYYYMMDD.txt' with ISBN and today's date"""

    def get_comparison_chart_prompt(self, context):
        """Generate comparison chart prompt."""
        book = context.get('book')
        pub_date = book.get('publication_date', '')
        imprint = self.get_imprint_context()

        special_instruction = ""
        if self.config.get('special_practice'):
            term = self.config['special_practice'].split('(')[0].strip()
            korean = self.config['special_practice'].split('(')[1].replace(')', '').strip()
            special_instruction = f"\n1. Whenever you mention \"{term}\", include the Korean term {korean} in parentheses immediately after."

        return f"""Create a comparison chart showing how this book differs from similar books:

Our Book: {book.get('title')}
Description: {book.get('back_cover_text', '')[:200]}
Publication Date: {pub_date}

Create markdown table comparing:
- Our book vs. traditional books on similar topics
- Key differentiators (3-4)
- Unique {imprint['name']} approach

Make compelling case for our book.

IMPORTANT INSTRUCTIONS:{special_instruction}
{"2" if special_instruction else "1"}. If book not yet published (pub date > today 2025-10-13), note as "Forthcoming {{pub_date}}".

Output: Save as 'comparison_ISBN_YYYYMMDD.md' with ISBN and today's date"""

    def get_retailer_pitch_prompt(self, context):
        """Generate retailer pitch prompt."""
        book = context.get('book')
        pub_date = book.get('publication_date', '')
        imprint = self.get_imprint_context()

        special_instruction = ""
        if self.config.get('special_practice'):
            term = self.config['special_practice'].split('(')[0].strip()
            korean = self.config['special_practice'].split('(')[1].replace(')', '').strip()
            special_instruction = f"\n1. Whenever you mention \"{term}\", include the Korean term {korean} in parentheses immediately after."

        return f"""Write a pitch to independent bookstores (200 words) for:

Title: {book.get('title')}
Publisher: Nimble Books / {imprint['name']}
Description: {book.get('back_cover_text', '')[:300]}
Publication Date: {pub_date}

Include:
- Why this fits their customers
- Unique selling points
- Display/merchandising suggestions
- Conversation starters for handselling

Tone: Professional, enthusiastic, practical

IMPORTANT INSTRUCTIONS:{special_instruction}
{"2" if special_instruction else "1"}. Check publication status vs today (2025-10-13):
   - If published: Focus on "available now"
   - If upcoming: Frame as "advance notice" and include release date

Output: Save as 'retailer_pitch_ISBN_YYYYMMDD.txt' with ISBN and today's date"""

    def get_testimonial_request_prompt(self, context):
        """Generate testimonial request prompt."""
        imprint = self.get_imprint_context()

        special_instruction = ""
        if self.config.get('special_practice'):
            term = self.config['special_practice'].split('(')[0].strip()
            korean = self.config['special_practice'].split('(')[1].replace(')', '').strip()
            special_instruction = f"\n\nIMPORTANT: Whenever you mention \"{term}\", include the Korean term {korean} in parentheses immediately after."

        return f"""Create an email template for requesting reader testimonials for {imprint['name']} books.

Include:
- Warm greeting
- Why we value their feedback
- Specific prompts for testimonial (3-4 questions)
- Permission to use quote
- Thank you

Tone: Personal, grateful, non-pushy
Length: 150 words{special_instruction}

Output: Save as 'testimonial_request_YYYYMMDD.txt' with today's date"""

    def get_new_topics_prompt(self, context):
        """Generate new topics prompt."""
        imprint = self.get_imprint_context()

        special_instruction = ""
        if self.config.get('special_practice'):
            term = self.config['special_practice'].split('(')[0].strip()
            korean = self.config['special_practice'].split('(')[1].replace(')', '').strip()
            special_instruction = f"\n\nIMPORTANT: Whenever you mention \"{term}\", include the Korean term {korean} in parentheses immediately after."

        return f"""Identify 5 potential book topics for {imprint['name']} imprint.

Consider:
- Current trends in science, technology, philosophy
- Topics benefiting from {imprint['name']}'s approach{imprint['practice']}
- Frontier knowledge areas
- Gaps in current catalog

For each topic provide:
- Working title
- Why it fits {imprint['name']}
- Potential audience
- Unique angle

Format as structured list.{special_instruction}

Output: Save as 'new_topics_YYYYMMDD.md' with today's date"""

    def get_mission_content_prompt(self, context):
        """Generate mission content prompt."""
        imprint = self.get_imprint_context()

        practice_text = self.config.get('special_practice', 'our unique approach')
        special_instruction = ""
        if self.config.get('special_practice'):
            term = self.config['special_practice'].split('(')[0].strip()
            korean = self.config['special_practice'].split('(')[1].replace(')', '').strip()
            special_instruction = f"\n\nIMPORTANT: Whenever you mention \"{term}\", include the Korean term {korean} in parentheses immediately after."

        return f"""Write educational content (300 words) explaining {imprint['name']} imprint mission.

Cover:
- What is {practice_text} and why it matters
- How {imprint['name']} adapts this for modern readers
- The role of AI-human collaboration
- What makes our books different
- How readers can engage with this practice

Audience: Potential readers, press, partners
Tone: Educational, inspiring, clear{special_instruction}

Output: Save as 'mission_content_YYYYMMDD.md' with today's date"""

    def get_partnership_brief_prompt(self, context):
        """Generate partnership brief prompt."""
        imprint = self.get_imprint_context()

        special_instruction = ""
        if self.config.get('special_practice'):
            term = self.config['special_practice'].split('(')[0].strip()
            korean = self.config['special_practice'].split('(')[1].replace(')', '').strip()
            special_instruction = f"\n\nIMPORTANT: Whenever you mention \"{term}\", include the Korean term {korean} in parentheses immediately after."

        return f"""Draft a partnership opportunity brief (250 words) for {imprint['name']}.

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

Tone: Professional, collaborative, open{special_instruction}

Output: Save as 'partnership_brief_YYYYMMDD.md' with today's date"""

    def get_seasonal_promotion_prompt(self, context):
        """Generate seasonal promotion prompt."""
        season = context.get('season', 'Current')
        books = context.get('books', [])
        imprint = self.get_imprint_context()

        special_instruction = ""
        if self.config.get('special_practice'):
            term = self.config['special_practice'].split('(')[0].strip()
            korean = self.config['special_practice'].split('(')[1].replace(')', '').strip()
            special_instruction = f"\n1. Whenever you mention \"{term}\", include the Korean term {korean} in parentheses immediately after."

        return f"""Create a {season} catalog promotion concept for {imprint['name']}.

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

IMPORTANT INSTRUCTIONS:{special_instruction}
{"2" if special_instruction else "1"}. For each book, check publication date vs today (2025-10-13):
   - Published books: "Available now"
   - Upcoming books: "Coming {{pub_date}}"

Output: Save as 'seasonal_promo_SEASON_YYYYMMDD.md' with season and today's date"""

    # ========== QUEUE OPERATIONS ==========

    def queue_task(self):
        """Select a task and add to queue (runs daily via cron)."""
        print(f"\n{'='*60}")
        print(f"{self.config['display_name']} Agent - QUEUE MODE")
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
            'context': {k: str(v)[:200] for k, v in context.items()},
            'queued_at': datetime.now().isoformat(),
            'status': 'pending',
            'imprint': self.imprint_name
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
        print(f"{self.config['display_name']} Agent - QUEUE STATUS")
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
            print(f"\n✅ No pending tasks in queue for {self.config['display_name']}!\n")
            return

        export = {
            'tasks': pending,
            'output_base': str(self.output_dir),
            'imprint': self.imprint_name,
            'exported_at': datetime.now().isoformat()
        }

        export_file = self.queue_dir / "claude_execution_batch.json"
        with open(export_file, 'w') as f:
            json.dump(export, f, indent=2)

        print(f"\n{'='*60}")
        print(f"{self.config['display_name']} Agent - READY FOR EXECUTION")
        print(f"{'='*60}\n")
        print(f"📦 Exported {len(pending)} tasks for Claude Code")
        print(f"📁 Export file: {export_file}")
        print(f"\n")
        print("Next steps:")
        print(f"1. In Claude Code, say: 'execute {self.imprint_name} queue'")
        print("2. I'll process all pending tasks using Claude Max")
        print("3. All outputs will be saved automatically")
        print(f"\n{'='*60}\n")


def list_imprints():
    """List all available imprints."""
    base_dir = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/imprints")

    print(f"\n{'='*60}")
    print("Available Imprints")
    print(f"{'='*60}\n")

    for imprint_dir in sorted(base_dir.iterdir()):
        if imprint_dir.is_dir() and not imprint_dir.name.startswith('.'):
            catalog = imprint_dir / "books.csv"
            config = imprint_dir / "agent_config.json"

            # Count books
            book_count = 0
            if catalog.exists():
                try:
                    df = pd.read_csv(catalog)
                    book_count = len(df)
                except:
                    pass

            # Load config
            enabled = True
            display_name = imprint_dir.name.replace('_', ' ').title()
            if config.exists():
                try:
                    with open(config, 'r') as f:
                        cfg = json.load(f)
                        enabled = cfg.get('enabled', True)
                        display_name = cfg.get('display_name', display_name)
                except:
                    pass

            status = "✓ ENABLED" if enabled else "✗ DISABLED"
            books = f"({book_count} books)" if book_count > 0 else "(no catalog)"

            print(f"  {status:12} {imprint_dir.name:30} {display_name:30} {books}")

    print(f"\n{'='*60}\n")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python imprint_queue_agent.py list                           # List all imprints")
        print("  python imprint_queue_agent.py queue <imprint>                # Add task to queue (daily cron)")
        print("  python imprint_queue_agent.py execute <imprint>              # Prepare for Claude execution")
        print("  python imprint_queue_agent.py status <imprint>               # Show queue status")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == 'list':
        list_imprints()
        return

    if len(sys.argv) < 3:
        print(f"Error: Imprint name required for '{mode}' command")
        print("Run 'python imprint_queue_agent.py list' to see available imprints")
        sys.exit(1)

    imprint_name = sys.argv[2]

    try:
        agent = ImprintQueueAgent(imprint_name)
    except ValueError as e:
        print(f"Error: {e}")
        print("Run 'python imprint_queue_agent.py list' to see available imprints")
        sys.exit(1)

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
