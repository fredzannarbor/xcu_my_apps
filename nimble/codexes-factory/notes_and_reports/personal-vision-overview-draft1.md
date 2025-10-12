# From Nexis to Now: Twenty Years of Algorithmic Publishing

## A Personal Journey from Answer Sets to AI-Assisted Books

In 2001, I had an epiphany while working with LexisNexis data. Why were we delivering search results as flat answer sets—endless lists of documents that users had to sift through themselves? What if we could generate a *report* instead, something formatted like an e-book that synthesized and organized the information into a coherent narrative?

This was the era of proprietary e-reader formats like Microsoft's LIT, years before the Kindle would revolutionize digital reading. The idea was ahead of its time, constrained by multiple obstacles: LexisNexis was focused on high-value business users who expected traditional answer sets; customers didn't know to ask for alternatives; usage licenses assumed answer-set delivery, not incorporation into fixed electronic products; and critically, we lacked any generative text capability—document creation was limited to assembly, hierarchy, and term extraction.

Today, twenty years later, the answer set has evolved into a mirror maze of advertisements, still fundamentally unchanged. But the vision of algorithmically generated reports? That's finally becoming reality.

## Experimenting with Format: The Nimble Books Years

In 2006, I launched Nimble Books and immediately began experimenting with book formats. I was obsessed with questions that most publishers considered settled: What's the optimal page length? How should annotations work? What if we varied structure based on content type?

These early experiments produced titles that pushed boundaries in small but meaningful ways—books with unconventional pagination, innovative annotation systems, hybrid formats that blended reference and narrative. Each book was a hypothesis about what a book could be, freed from the conventions that governed traditional publishing. The experiments were modest, constrained by the technology of the time, but they established a pattern: publishing as an experimental practice, format as a variable to be optimized, books as products of intentional design choices rather than inherited convention.

## Building PageKicker: Publishing as Code

The next leap came when I taught myself to program and built PageKicker, a publishing platform written entirely in bash. PageKicker represented something fundamentally new: algorithmic book creation at scale.

The system could search permissioned content (initially Wikipedia), fetch and analyze articles, and assemble complete books with a single command. Users could specify seed keywords, customize covers, choose fonts, and control how extensively the system expanded topics into pages. The entire process—from content discovery through formatting to final output—could be executed with a single shell script.

```bash
bin/builder.sh --seedsviacli "Fancy Bear; Kaspersky" \
               --booktitle "Cybersecurity Demo Book" \
               --covercolor "red"
```

Simon Dudley correctly understood what PageKicker represented: an evolution away from the answer set toward synthesized, structured documents. This was algorithmic curation and assembly, creating coherent books from distributed knowledge sources. While we still lacked true generative capability, we'd moved from passive search results to active document creation.

## The GPT-2 Moment: Generative Text Arrives

Everything changed in December 2019 when OpenAI released GPT-2, followed by GPT-3 in 2020. Suddenly, genuine text generation became possible. I immediately wrote a longform prospectus envisioning the future of AI-assisted book creation.

In that prospectus, I imagined:

- Authors and AI "Muses" collaborating iteratively on book proposals and chapter outlines
- Section-by-section generation with human oversight and editing
- AI learning from author preferences to recommend structural changes
- Eventually, reader feedback shaping both human and AI authorship

The technical constraints were obvious—GPT-3's 2048-token limit made longform generation impossible, requiring quadratically scaling self-attention resources. But I argued this was solvable through sampling strategies that leveraged document structure: executive summaries, tables of contents, act structures in plays, character-defining passages in fiction.

Four years later, we have models with 2MB+ token contexts. The technical barriers I outlined have largely fallen. Since 2021, I've published experiments under the banner "AI Lab for Book-Lovers," testing these capabilities in practice—human-AI collaboration producing real books that real people read.

Comparing my 2020 vision with today's reality: the technical progression has been faster than I expected, but the creative partnership between human and AI remains more complex and nuanced than I initially imagined. The AI doesn't just execute—it surprises, suggests, and occasionally transforms the work in unexpected ways.

## The Expanding Vision: Synthetic Readers and Agentic Books

Today, my vision has expanded far beyond those early ideas. I'm now thinking about:

**Armies of synthetic readers** iterating through thousands of variations, homing in on the most satisfying titles through reinforcement learning. Not A/B testing, but evolutionary optimization at scale.

**Agentic books**—inspired by recent arXiv papers on agentic research papers—that can answer questions, update themselves with new information, and adapt to reader needs. Books as living systems rather than frozen artifacts.

**Pop-up chatbot micro-communities** where conversations coalesce into collaborative narratives, eventually becoming books. Imagine Discord servers or Reddit threads where an AI synthesizes emergent stories, with community members as co-authors.

**Young readers as the frontier.** I'm particularly focused on what engages kids who've grown up with AI:
- The 9-year-old who dismissively says "That's AI!" when they detect generated content
- The 10-year-old who resents being "parentsplained" via ChatGPT
- Understanding what authenticity means to a generation where AI is ambient

These kids aren't impressed by AI-generated content—they're critics, native to a world where synthesis and generation are everywhere. What will make books matter to them? What can algorithmic publishing offer that feels genuine, not manufactured?

## The Through-Line

From 2001 to 2025, the through-line has been consistent: *information should be synthesized into coherent artifacts, not delivered as raw search results*. The answer set was never the destination—it was always a limitation we should transcend.

What's changed is the scale of what's possible. We've moved from static document assembly to dynamic text generation to collaborative human-AI authorship to, soon, books that can think and adapt.

The question isn't whether algorithmic publishing will transform books—it already has. The question is: will we use these capabilities to create genuine value for readers, or just manufacture content at scale?

I've spent twenty years believing the former is possible. The tools finally exist to prove it.

---

*Fred Zimmerman founded Nimble Books in 2006 and has been experimenting with algorithmic and AI-assisted publishing ever since. His work spans traditional publishing, software development, and AI-augmented authorship.*