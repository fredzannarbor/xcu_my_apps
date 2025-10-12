# Reader Panels Slash Command Guide

## Quick Start

The `/drafts2readerpanels` command automatically evaluates book drafts using comprehensive reader panels powered by Claude Max.

### Basic Usage

```bash
/drafts2readerpanels <file_path>
```

**Example:**
```bash
/drafts2readerpanels data/ideation/development/my_book_outline.json
```

## What It Does

1. **Reads your draft** - Extracts title, target audience, genre, content
2. **Creates 4 reader panels** (270+ total personas by default):
   - Children (100 personas) - Target age group readers
   - Parents (80 personas) - Purchase decision makers
   - Reading Experts (50 personas) - Educators & specialists
   - Purchasing (40 personas) - School administrators & librarians
3. **Launches parallel evaluations** - Each persona evaluates from their unique perspective
4. **Generates comprehensive reports** - Scores, feedback, recommendations, market analysis

## Advanced Options

### Multiple Files
Evaluate several drafts at once:
```bash
/drafts2readerpanels outline1.json outline2.md outline3.txt
```

### Custom Panels
Specify which panels to use:
```bash
/drafts2readerpanels draft.json --panels children,parents,experts
```

### Custom Panel Sizes
Adjust the number of personas:
```bash
/drafts2readerpanels draft.json --panel-sizes children:50,parents:30,experts:20
```

### Custom Age Range
Override the target age:
```bash
/drafts2readerpanels draft.json --age-range 12-14
```

### Custom Output Directory
```bash
/drafts2readerpanels draft.json --output-dir my_evaluations/
```

## What You Get

### Output Files (per draft)
```
data/reader_panels/{book_slug}/
├── evaluation_data.json              # Structured book & persona data
├── children_feedback.jsonl           # 100 child evaluations
├── parents_feedback.jsonl            # 80 parent evaluations
├── experts_feedback.jsonl            # 50 expert evaluations
├── purchasing_feedback.jsonl         # 40 purchasing evaluations
└── COMPLETE_PANEL_SUMMARY.md         # Comprehensive analysis report
```

### Evaluation Scores (per persona)
- **Market Appeal** (0-10): How appealing to their demographic
- **Genre Fit** (0-10): How well it fits genre expectations
- **Audience Alignment** (0-10): Appropriateness for target audience
- **Overall Rating** (0-10): Average of above scores
- **Detailed Feedback**: Persona-specific reactions and analysis
- **Recommendations**: Specific improvements from their perspective
- **Concerns**: Potential issues they identify

### Summary Report Includes
- Executive summary with overall verdict
- Panel-by-panel analysis and breakdown
- Universal strengths across all panels
- Common concerns and recommendations
- Prioritized action plan (Immediate/Short/Long-term)
- Market potential assessment (revenue projections)
- Critical success factors

## Example Workflow

### Step 1: Create your book outline
Save as JSON, Markdown, or text file with:
- Title
- Target audience (age)
- Genre
- Logline/premise
- Chapter outlines or summary

### Step 2: Run the command
```bash
/drafts2readerpanels data/ideation/development/my_outline.json
```

### Step 3: Monitor progress
The command will report:
- Progress every 20-25 evaluations
- Panel completion status
- Interim findings

### Step 4: Review results
Read the summary report:
```bash
cat data/reader_panels/my_book/COMPLETE_PANEL_SUMMARY.md
```

## Panel Personas

### Children Panel (Default: 100)
**Archetypes:**
- Advanced Reader (20) - Above grade level, loves complex stories
- Reluctant Reader (20) - Below grade level, prefers visual/action
- Grade Level Reader (20) - At grade level, likes relatable stories
- Tech-Savvy (20) - Digital native, loves modern/tech stories
- Special Interest (20) - Animals, science, sports enthusiasts

### Parents Panel (Default: 80)
**Archetypes:**
- Concerned Parent (20) - Worried about literacy, seeks solutions
- Tech-Positive Parent (20) - Open to AI/tech in learning
- Traditional Parent (20) - Skeptical of tech, values classics
- Diverse Family Parent (20) - Seeks representation & inclusivity

### Reading Experts Panel (Default: 50)
**Archetypes:**
- Science of Reading Expert (10) - Evidence-based literacy
- Elementary Teacher (10) - Classroom application focus
- Reading Specialist (10) - Intervention & struggling readers
- EdTech Specialist (10) - Technology integration
- Literacy Coach (10) - Professional development & family engagement

### Purchasing Panel (Default: 40)
**Archetypes:**
- Elementary Principal (10) - Student achievement, budget, parent satisfaction
- Curriculum Director (10) - Standards alignment, evidence-based, scalability
- School Librarian (10) - Collection diversity, circulation, engagement
- Special Ed Coordinator (10) - Intervention tools, accommodations, equity

## Tips for Best Results

### 1. Provide Complete Information
Include in your draft:
- Clear target age range
- Specific genre
- Educational objectives (if any)
- Character diversity and representation
- Contemporary hooks or themes

### 2. Use Structured Formats
JSON or Markdown works best:
```json
{
  "title": "Book Title",
  "target_age": "9-10",
  "genre": "Contemporary Fiction",
  "logline": "One sentence pitch",
  "chapters": [...]
}
```

### 3. Review Panel Reports Separately
Each panel provides unique insights:
- **Children**: Entertainment value, engagement, relatability
- **Parents**: Educational value, appropriateness, purchase intent
- **Experts**: Pedagogical soundness, best practices alignment
- **Purchasing**: ROI, implementation, scalability

### 4. Act on Recommendations
The summary prioritizes actions:
- **Immediate** (Weeks 1-4): Critical fixes
- **Short-term** (Months 2-6): Enhancements
- **Long-term** (6-12 months): Strategic positioning

## Comparison to Maya Example

The Maya's Story Reel evaluation created:
- 270 total evaluations
- 7.89/10 overall rating
- $150K-$1.2M market projection
- Detailed action plan with 15+ recommendations
- Files totaling ~600KB of analysis

Your drafts will receive the same comprehensive treatment!

## Technical Details

- **Powered by**: Claude Max (no API costs)
- **Evaluation method**: Agent-based task execution
- **Processing time**: ~5-15 minutes for 270 evaluations
- **Output format**: JSONL (one evaluation per line) + Markdown summaries
- **Persona authenticity**: Each evaluation reflects unique characteristics and priorities

## Support & Customization

Need different panels? The command supports:
- Custom persona definitions
- Industry-specific reviewers (publishers, agents, booksellers)
- International perspectives (non-US markets)
- Specific demographic focuses (neurodivergent readers, ELL students)
- Academic review panels (researchers, curriculum developers)

Just specify in the command or modify the default configuration!

---

**Created:** October 10, 2025
**Version:** 1.0
**Based on:** Maya's Story Reel comprehensive panel evaluation
