# Twenty Years of Algorithmic Publishing



## The Answer Set Problem (2001)

In 2001, while working with LexisNexis data, I realized something was fundamentally wrong with how we delivered search results. Users received flat answer sets—endless lists of documents they had to manually sift through. Why couldn't we generate a *report* instead, something formatted like an e-book that synthesized and organized the information into a coherent narrative?

This was the era of proprietary e-reader formats like Microsoft's LIT, years before the Kindle would democratize digital reading. The idea was ahead of its time, blocked by multiple obstacles: LexisNexis focused on high-value business users who expected traditional answer sets; customers didn't know to ask for alternatives; usage licenses assumed answer-set delivery, not incorporation into fixed electronic products; and critically, we lacked any generative text capability. Document creation was limited to assembly, hierarchy, and term extraction.


## Experimenting with Format: The Nimble Books Years (2006)

Five years later, I decided to test these ideas myself. I launched Nimble Books in 2006 and immediately began experimenting with book formats. I was obsessed with questions most publishers considered settled: What's the optimal page length? How should annotations work? What if we varied structure based on content type?

[**NOTE TO AUTHOR: Please add 2-3 specific book titles from this period and what made them experimental. For example: "[Title] featured unconventional 50-page chapters..." or "[Title] used marginal annotations inspired by Talmudic commentary..." Review https://amzn.to/46XJMjD for examples.**]

These early experiments pushed boundaries in small but meaningful ways—books with unconventional pagination, innovative annotation systems, hybrid formats that blended reference and narrative. Each book was a hypothesis about what a book could be, freed from conventions that governed traditional publishing. The experiments were modest, constrained by the technology of the time, but they established a pattern: publishing as experimental practice, format as variable to be optimized, books as products of intentional design choices rather than inherited convention.

Readers didn't always know what to make of these experiments, but they proved that format was a variable worth exploring.

---

## Building PageKicker: Publishing as Code (2010s)

The next leap required me to become a programmer. I taught myself to code and built PageKicker, a publishing platform constructed primarily in bash—a testament to both the possibilities and limitations of the era.

PageKicker represented something fundamentally new: algorithmic book creation at scale. The system could search permissioned content (initially Wikipedia), fetch and analyze articles, and assemble complete books with a single command. Users could specify seed keywords, customize covers, choose fonts, and control how extensively the system expanded topics into pages. The entire process—from content discovery through formatting to final output—could be executed with a single shell script:

```bash
bin/builder.sh --seedsviacli "Fancy Bear; Kaspersky" \
               --booktitle "Cybersecurity Demo Book" \
               --covercolor "red"
```

Simon Dudley correctly understood what PageKicker represented: an evolution away from the answer set toward synthesized, structured documents. This was algorithmic curation and assembly, creating coherent books from distributed knowledge sources. We'd moved from passive search results to active document creation.

---

## The Generative Breakthrough: GPT-3 and the Longform Vision (2019-2020)

[**NOTE TO AUTHOR: Please verify exact dates. GPT-2 was released February 2019, GPT-3 was released June 2020. Adjust timeline accordingly.**]

Everything changed when OpenAI released GPT-2 in early 2019, followed by GPT-3 in mid-2020. Suddenly, genuine text generation became possible. I immediately wrote a longform prospectus envisioning the future of AI-assisted book creation, imagining:

- Authors and AI "Muses" collaborating iteratively on book proposals and chapter outlines
- Section-by-section generation with human oversight and editing
- AI learning from author preferences to recommend structural changes ("you seem to really like my how-to sections—do you want to add more of them?")
- Eventually, reader feedback shaping both human and AI authorship

The technical constraints were obvious at the time. GPT-3's 2048-token limit made longform generation impossible without clever workarounds. But I argued this was solvable through sampling strategies that leveraged document structure: executive summaries, tables of contents, act structures in plays, character-defining passages in fiction.

Four years later, we have models with 128K+ token contexts. The technical barriers I outlined have largely fallen.

Since 2021, I've published experiments under the banner "AI Lab for Book-Lovers," testing these capabilities in practice—human-AI collaboration producing real books that real people read.

[**NOTE TO AUTHOR: Please add 1-2 specific examples from AI Lab for Book-Lovers. What was the first experiment? Most successful? Most surprising outcome? Reference https://amzn.to/42dydSQ**]

Comparing my 2020 vision with today's reality: the technical progression has been faster than I expected, but the creative partnership between human and AI remains more complex and nuanced than I initially imagined. The AI doesn't just execute—it surprises, suggests, and occasionally transforms the work in unexpected ways. I've seen AI Muses suggest metaphors I'd never have considered, identify structural inconsistencies I'd missed, and occasionally generate passages that were genuinely better than my own attempts.

But even as these early visions materialized, my thinking has continued to evolve.

---

## The Expanding Vision: What Comes Next



### Armies of Synthetic Readers

Imagine thousands of AI readers iterating through variations of a book—different titles, opening hooks, narrative structures—providing feedback that helps optimize for engagement and satisfaction. Not simple A/B testing, but evolutionary optimization at scale, where the "fitness function" is genuine reader experience rather than just clicks or time-on-page.

### Agentic Books

Inspired by recent arXiv papers on agentic research papers, I'm exploring books as living systems that can answer questions, update themselves with new information, and adapt to reader needs. Not static frozen artifacts, but dynamic entities that grow and change.

### Pop-up Chatbot Micro-communities

What if Discord servers or Reddit threads could spawn books? Conversations coalesce into collaborative narratives, with an AI synthesizing emergent stories and community members as co-authors. The question isn't "how do we get people to read books?" but "how do we turn the conversations people are already having into books?"

### Young Readers as the Frontier

I'm particularly focused on what engages kids who've grown up with AI. The 9-year-old who dismissively says "That's AI!" when they detect generated content. The 10-year-old who resents being "parentsplained" via ChatGPT.

These kids are the ultimate test of whether we've transcended the answer set. They've grown up with AI-generated content everywhere—they're not impressed by synthesis alone. They need synthesis that adds genuine value, not just assembly that adds convenience. Understanding what authenticity means to them is critical to the future of algorithmic publishing.

---

## The Through-Line: Beyond the Answer Set

From 2001 to 2025, the through-line has been consistent: *information should be synthesized into coherent artifacts, not delivered as raw search results*. The answer set was never the destination—it was always a limitation we should transcend.

What's changed is the scale of what's possible. We've moved from static document assembly to dynamic text generation to collaborative human-AI authorship to, soon, books that can think and adapt.

The question isn't whether algorithmic publishing will transform books—it already has. The question is: **Will we use these capabilities to create genuine value for readers, or just manufacture content at scale?**

The answer will determine whether algorithmic publishing fulfills its promise or becomes just another way to spam the world with words.

I've spent twenty years believing the former is possible. The tools finally exist to prove it. I'm still experimenting, still learning, still believing.

If you're working on similar problems, I'd love to hear from you.

---

*Fred Zimmerman founded Nimble Books in 2006 and has been experimenting with algorithmic and AI-assisted publishing ever since. His work spans traditional publishing, software development, and AI-augmented authorship.*

[**Resources: GitHub repo for PageKicker: https://github.com/fredzannarbor/pagekicker-community/ | AI Lab for Book-Lovers on Amazon: https://amzn.to/42dydSQ | Nimble Books: https://amzn.to/46XJMjD**]