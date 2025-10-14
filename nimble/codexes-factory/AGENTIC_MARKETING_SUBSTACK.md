# Building a $0 AI Marketing Agent That Does One Thing Every Day

## The Problem: Marketing Is a Marathon, Not a Sprint

If you're an indie publisher, you know the drill. You've got books to publish, catalogs to maintain, and a million other things competing for attention. Marketing falls to the bottom of the list—not because it's unimportant, but because it's never urgent *today*.

The paradox: Marketing only works with consistency. One brilliant social post doesn't move the needle. One amazing newsletter doesn't build an audience. But *daily* presence? That compounds.

So how do you maintain daily marketing output when you're drowning in everything else?

## The Solution: An AI Agent That Shows Up Every Day

I built a queue-based AI marketing agent for my publishing imprints that does exactly one marketing task per day. Not zero. Not ten. One.

Here's the key insight: **The agent doesn't execute the tasks**. It just *queues* them. Execution happens in batches using Claude Code's "Claude Max" mode—which is free, unlimited, and produces excellent output.

This architecture solves two problems:
1. **Cost**: Task selection is deterministic (no API costs). Execution uses free Claude Max.
2. **Quality**: Claude Max is the best model. Every output is high-quality, publication-ready content.

## How It Works

### The Daily Cycle

Every morning at 9 AM, a cron job runs for each publishing imprint:

```bash
python3 imprint_queue_agent.py queue xynapse_traces
```

The agent:
1. **Analyzes recent history** - What tasks were done in the last 7 days?
2. **Calculates weights** - High-frequency tasks get priority, recently-done tasks get demoted
3. **Selects intelligently** - Weighted random selection ensures variety while respecting priorities
4. **Queues the task** - Stores the complete prompt with all context (book data, seasonal info, etc.)

No LLM calls. No API costs. Just smart task queueing.

### The Execution Cycle

When I'm ready (usually once a week), I tell Claude Code:

> "Execute the xynapse_traces queue"

Claude Max processes all pending tasks in one batch, generating:
- Social media posts with bookstore links
- Back cover copy
- Newsletter spotlights
- Seasonal promotions
- And 12 other task types

Each task gets saved to the appropriate output directory with proper filenames and metadata.

Total cost: **$0** (using Claude Max via Claude Code)

## The 16 Marketing Tasks

The agent knows how to do 16 different marketing tasks across 4 categories:

### Content Creation (External-Facing)
1. Generate social media post about catalog book
2. Write blog post on imprint mission/practice
3. Create book spotlight for newsletter
4. Draft themed reading list from catalog

### Catalog Development
5. Write back cover copy
6. Generate metadata improvements
7. Create publisher's note
8. Draft author bio enhancement

### Marketing & Discovery
9. Generate Amazon A+ content
10. Create book comparison chart
11. Draft retailer pitch
12. Generate testimonial request template

### Strategic Development
13. Identify potential new book topics
14. Create educational content about imprint mission
15. Generate partnership/collaboration brief
16. Develop seasonal catalog promotion

Tasks are weighted by frequency:
- **High frequency** (runs often): Social media, metadata improvements
- **Medium frequency** (runs regularly): Back cover copy, spotlights, blog posts
- **Low frequency** (runs occasionally): Reading lists, partnership briefs, strategic planning

## Real Examples

Here's what the agent generated for my Xynapse Traces imprint (which focuses on pilsa (필사), the Korean practice of transcriptive meditation):

### Social Media Post (274 characters)
```
AI agents are now discovering drugs, proteins, and materials faster
than humans can validate them. Should we slow down to ensure safety,
or accelerate before others do? Our latest pilsa (필사) meditation
explores this razor's edge. 🧬⚡

#AIScience #ResearchEthics #PilsaPractice #XynapseTraces

See more: /Bookstore?isbn=9781608883691
```

### Seasonal Promotion (Fall 2025)
```markdown
# Fall Catalog Promotion: Harvest Season for the Mind

## Seasonal Theme
As leaves change and days shorten, fall invites natural contemplation.
Our catalog mirrors this seasonal rhythm—books selected for longer
evenings and deeper thinking.

## Featured Fall Reads
1. **AI-Driven Science: Speed versus Safety** - Perfect for crisp October nights
2. **Family Support: Data vs. Intuition** - As families gather for holidays...
3. **Advanced Propulsion: Fast vs. Safe** - When winter approaches...
4. **Quantum Computing: Revolution or Disruption?** - Nature demonstrates transformation...
5. **Climate Science: Urgency vs. Precision** - Fall's changing landscape echoes...

## Promotion Message
This fall, xynapse traces invites you to practice pilsa (필사) with
frontier knowledge. Just as autumn asks us to slow down and observe,
our transcriptive meditation approach pairs you with ideas demanding
careful attention...
```

### Back Cover Copy (194 words)
```
When raising children or caring for aging parents, should you trust
the data or your gut? This question sits at the heart of modern family
life, where algorithmic recommendations compete with ancestral wisdom.

Through the lens of pilsa (필사)—the Korean practice of mindful copying
and contemplation—this book invites you to hold both perspectives
simultaneously. Not to choose between spreadsheets and instinct, but to
develop the cognitive flexibility to know when each matters most...
```

Every piece includes:
- The Korean term 필사 whenever pilsa is mentioned
- Publication date awareness (published books get bookstore links, upcoming books show release dates)
- Imprint-specific voice and positioning
- Proper formatting and structure

## The Architecture: Why It Works

### Separation of Concerns
**Queueing** (automated, free) is separate from **execution** (manual, free but requiring attention).

This matters because:
- Queuing can run automatically without supervision
- Execution happens when you have time to review
- No risk of auto-publishing bad content
- Full control over quality while maintaining consistency

### Publication Date Intelligence
The agent knows which books are published vs. upcoming:
- **Published books**: Get direct bookstore links for discoverability
- **Upcoming books**: Show as "Coming [date]" to build anticipation

### Weighted Randomness
Pure random selection would produce feast-or-famine patterns. The agent uses weighted randomness:
- High-frequency tasks: 3x weight
- Medium-frequency tasks: 2x weight
- Low-frequency tasks: 1x weight
- Recently-done tasks: -0.3 weight per occurrence

This creates natural variety while ensuring important tasks get done regularly.

### Imprint Awareness
The same agent runs for multiple imprints, each with its own:
- Catalog (books.csv)
- Configuration (agent_config.json)
- Queue directory
- Output directory
- Voice and positioning

For Xynapse Traces, it knows about pilsa (필사) and frontier knowledge.
For other imprints, it adapts to their unique characteristics.

## Setting It Up

### 1. Install the Agent

```bash
git clone https://github.com/your-repo/imprint-queue-agent
cd imprint-queue-agent
chmod +x imprint_queue_agent.py
```

### 2. Configure Your Imprint

Create `imprints/your_imprint/agent_config.json`:

```json
{
  "name": "your_imprint",
  "display_name": "Your Imprint Name",
  "tagline": "Your imprint's tagline",
  "special_practice": "your special term (optional)",
  "enabled": true
}
```

### 3. Add Your Catalog

Create `imprints/your_imprint/books.csv` with columns:
- id, title, subtitle, author
- isbn13, publication_date
- back_cover_text
- series_name, series_number, page_count

### 4. Set Up Daily Cron

```bash
./setup_imprint_agents_cron.sh
```

This adds a cron job that runs daily at 9 AM for each enabled imprint.

### 5. Execute Queued Tasks

When ready, use Claude Code:

```
Execute the [your_imprint] queue
```

Claude Max processes all pending tasks using its full capabilities—for free.

## The Results

After one week of running this for Xynapse Traces:
- **7 marketing assets created** (one per day)
- **Zero API costs** (using Claude Max for execution)
- **Consistent output quality** (every piece is publication-ready)
- **Strategic variety** (social posts, back cover copy, seasonal promotions, etc.)
- **Zero maintenance** (it just runs)

The compound effect is remarkable. Seven tasks seems small, but that's:
- 30 tasks per month
- 365 tasks per year

For an indie publisher doing everything manually? That's transformative.

## Why This Matters

**Most indie publishers aren't doing zero marketing**. They're doing *inconsistent* marketing. A burst of activity when launching a book. Radio silence for months. Another burst. More silence.

The algorithm (and your audience) rewards consistency over intensity.

This agent solves the consistency problem by:
1. **Removing decision fatigue** - No "what should I post today?"
2. **Eliminating execution friction** - Tasks are pre-queued with full context
3. **Ensuring strategic variety** - Weighted selection prevents repetition
4. **Maintaining quality** - Claude Max produces excellent output
5. **Costing nothing** - Free to run, free to execute

## Adapting It For Your Needs

The 16 tasks I built are specific to book publishing, but the architecture works for any domain:

**E-commerce?** Queue product descriptions, comparison charts, seasonal promotions, customer testimonial requests.

**SaaS?** Queue feature announcements, use case spotlights, integration guides, customer success stories.

**Consulting?** Queue blog posts, case studies, newsletter content, LinkedIn thought leadership.

The key is identifying your "marketing atoms"—the discrete tasks that compound over time—and letting the agent queue them strategically.

## The Code

The complete agent is open source: [link to repo]

Key files:
- `imprint_queue_agent.py` - Main agent (870 lines)
- `setup_imprint_agents_cron.sh` - Cron setup script
- `imprints/*/agent_config.json` - Per-imprint configuration

The agent is designed to be:
- **Self-contained** - No external dependencies beyond Python stdlib + pandas
- **Auditable** - All prompts are visible, no black boxes
- **Extensible** - Add new tasks by implementing prompt templates
- **Multi-tenant** - One agent serves all your imprints

## Lessons Learned

### What Worked
- **Separation of queueing and execution** - Keeps costs at zero while maintaining quality control
- **Weighted randomness** - Produces natural variety without feast-or-famine patterns
- **Publication date awareness** - Differentiates published vs. upcoming books automatically
- **Imprint-specific configuration** - Same agent adapts to different voices and positioning
- **16 tasks across 4 categories** - Enough variety to feel comprehensive, not overwhelming

### What I'd Do Differently

**Add task dependencies**: Some tasks should only run after others (e.g., don't generate retailer pitches for books without back cover copy yet).

**Smart catalog sampling**: Currently random. Could prioritize books without recent marketing or upcoming releases.

**Output validation**: Agent could check if output files meet quality criteria before marking tasks complete.

**Multi-day campaigns**: Some tasks (like book launches) need coordinated multi-day campaigns, not just one-off tasks.

**Feedback loop**: Track which marketing assets perform best and weight future task selection accordingly.

## The Bigger Picture: Agentic Marketing

This isn't just about task automation. It's about **strategic delegation**.

Traditional marketing automation (Mailchimp, Buffer, etc.) handles *distribution*. You still have to create the content.

LLM-based tools (ChatGPT, Claude, etc.) handle *generation*. You still have to decide what to create and when.

This agent handles **strategic task selection**. It knows:
- What tasks exist
- When each should run
- How to balance variety and priority
- What context each needs

You review and publish. The agent handles the strategy.

That's the future of indie marketing: AI agents that understand your strategy and execute it consistently, while you maintain editorial control.

## Try It Yourself

If you're an indie publisher (or any small business doing content marketing), this architecture can work for you:

1. **Clone the repo** and adapt the 16 tasks to your domain
2. **Set up daily queueing** for your business
3. **Execute batches weekly** using Claude Code
4. **Iterate on task types** based on what performs

The beauty is you can start small—just 3-4 task types—and expand as you see results.

Marketing consistency beats marketing intensity every time. This agent ensures you show up every day, even when you can't.

---

**About the Author**: Fred Zimmerman runs Nimble Books LLC and the Xynapse Traces imprint, exploring the intersection of AI-human collaboration in book publishing. He's been experimenting with agentic workflows since GPT-3.

**Try the agent**: [link to GitHub repo]
**See it in action**: Browse [Xynapse Traces catalog](http://localhost:8502/Bookstore?imprint=xynapse_traces)

---

*If you found this useful, please share it with other indie publishers. The code is open source—adapt it, extend it, and share your own task types.*
