# BISAC Category Generator - User Guide

## Overview

The BISAC Category Generator is an AI-powered system that automatically creates industry-standard book categories for your publications. This intelligent tool helps publishers, editors, and book production staff efficiently categorize books according to Book Industry Standards and Communications (BISAC) guidelines, improving discoverability and sales potential.

## What is BISAC Categorization?

### BISAC Standards Explained

BISAC (Book Industry Standards and Communications) is the standardized system used by publishers, booksellers, and libraries to categorize books. Each BISAC category consists of:

- **A code**: Like "BUS001000" (unique identifier)
- **A description**: Like "BUSINESS & ECONOMICS / Accounting / General" (human-readable category)
- **Hierarchical structure**: Categories are organized from general to specific topics

### Why BISAC Categories Matter

**For Discoverability:**
- Online bookstores use BISAC categories to organize inventory
- Readers browse by category to find relevant books
- Search algorithms consider category alignment for recommendations

**For Sales Success:**
- Proper categorization increases visibility in relevant genre sections
- Helps books appear in targeted marketing campaigns
- Enables accurate competitive analysis and pricing

**For Distribution:**
- Wholesalers and distributors rely on BISAC codes for inventory management
- Libraries use categories for acquisition and cataloging decisions
- Retail chains organize shelf space based on category data

### How AI-Powered Categorization Helps

The system analyzes your book's content (title, subtitle, description, keywords) to suggest the most relevant BISAC categories, saving time and ensuring accuracy while leveraging industry expertise.

## Getting Started

### Basic Workflow Integration

The BISAC Category Generator works seamlessly within the Book Pipeline interface:

1. **Book Metadata Input**: Enter your book's title, subtitle, description, and keywords
2. **Automatic Analysis**: The AI analyzes content to identify relevant themes and topics
3. **Category Generation**: System produces up to 3 relevant BISAC categories
4. **Review and Approval**: Review suggested categories and approve or modify as needed
5. **Distribution Integration**: Approved categories automatically populate distribution files

### Configuration Requirements

**Minimum Required Information:**
- Book title
- Book description or summary
- Target audience (optional but recommended)

**Enhanced Accuracy Inputs:**
- Detailed subtitle
- Comprehensive book description
- Relevant keywords
- Genre information
- Target market details

## Step-by-Step Usage Guide

### 1. Using Automatic Categorization

**Through the Book Pipeline Interface:**

1. **Start New Book Project**: Create or open your book project in the system
2. **Enter Book Details**: Fill in the metadata form with your book information
3. **Enable Auto-Categorization**: Ensure "Auto-generate BISAC categories" is enabled
4. **Run Pipeline**: Execute the book pipeline process
5. **Review Results**: Check the generated categories in the distribution section

**What the System Analyzes:**
- Title and subtitle content for subject matter clues
- Book description for theme identification
- Keywords for topic classification
- Existing metadata for context

### 2. Setting Preferred Categories in Configurations

**Imprint-Level Category Preferences:**

Configure your imprint to prefer certain category types:

```json
"metadata_defaults": {
  "bisac_category_preferences": [
    "COM000000",  // Computers/Technology
    "SCI000000",  // Science
    "PHI000000"   // Philosophy
  ]
}
```

**Tranche-Level Category Overrides:**

For specific book collections, set required categories:

```json
"required_bisac_subject": "SELF-HELP / Journaling"
```

This ensures all books in the tranche receive this primary category.

### 3. Reviewing and Approving Generated Suggestions

**Category Review Process:**

1. **Examine Primary Category**: Check if the first category accurately represents the book's main theme
2. **Evaluate Secondary Categories**: Ensure additional categories expand market reach appropriately
3. **Verify Category Hierarchy**: Confirm categories progress from general to specific appropriately
4. **Check Diversity Score**: Look for categories spanning different top-level subjects when appropriate

**Approval Indicators:**
- ✅ **High Confidence Score** (0.8-1.0): Strong match between content and category
- ✅ **Valid Category Names**: All suggestions match official BISAC standards
- ✅ **Good Diversity Score** (0.7+): Categories span multiple subject areas when relevant

**Review Questions to Ask:**
- Does the primary category accurately capture the book's main subject?
- Will readers looking for this type of book find it in these categories?
- Do the categories align with comparable successful books in your market?
- Are there any surprising or inappropriate category suggestions?

### 4. Handling Edge Cases and Errors

**Common Scenarios and Solutions:**

**Multi-Genre Books:**
- *Issue*: Book spans multiple distinct subjects (e.g., historical business biography)
- *Solution*: System automatically provides diverse categories from different top-level subjects
- *Manual Override*: Use tranche configuration to specify preferred primary category

**Niche or Specialized Topics:**
- *Issue*: Very specific subject matter not well-covered by standard categories
- *Solution*: System falls back to broader, related categories with manual refinement option
- *Best Practice*: Review suggested broader categories and select the most specific applicable option

**Validation Errors:**
- *Issue*: Generated category doesn't exist in BISAC database
- *Solution*: System automatically suggests closest valid alternative
- *Action Required*: Review suggested alternatives and select most appropriate

**Empty or Generic Results:**
- *Issue*: System cannot determine appropriate categories from available information
- *Solution*: System provides safe fallback categories (General, Business & Economics, Reference)
- *Improvement Strategy*: Enhance book description with more specific topic keywords

## Best Practices

### Optimizing Category Selections

**For Fiction:**
- Include genre-specific categories (Fiction / Mystery, Fiction / Romance)
- Consider setting categories (Fiction / Historical / World War II)
- Add demographic categories when relevant (Fiction / African American & Black)

**For Non-Fiction:**
- Start with broad subject area (Science, Business & Economics)
- Add specific subtopics (Science / Physics / Quantum Theory)
- Include practical application categories (Self-Help, Reference)

**for Academic/Professional:**
- Use precise subject classifications (Education / Higher Education)
- Include methodology categories (Research / Statistical Methods)
- Add audience-specific categories (Professional Development)

### Working with Different Book Types

**Business Books:**
- Primary: BUSINESS & ECONOMICS / [Specific Area]
- Secondary: BUSINESS & ECONOMICS / Leadership (if applicable)
- Tertiary: SELF-HELP / Personal Growth / Success (if motivational)

**Technology Books:**
- Primary: COMPUTERS / [Specific Technology Area]
- Secondary: SCIENCE / General (if theoretical)
- Tertiary: BUSINESS & ECONOMICS / Industries / Technology (if business-focused)

**Self-Help Books:**
- Primary: SELF-HELP / [Specific Topic]
- Secondary: PSYCHOLOGY / [Relevant Area] (if psychology-based)
- Tertiary: HEALTH & FITNESS / [Area] (if health-related)

### Quality Assurance Workflows

**Pre-Publication Checklist:**
1. ✅ All generated categories validated against current BISAC standards
2. ✅ Primary category aligns with book's main subject matter
3. ✅ Secondary categories enhance discoverability without diluting focus
4. ✅ Categories match competitive titles in the same market
5. ✅ No inappropriate or misleading category assignments

**Regular Review Process:**
- **Monthly**: Review category performance metrics for published books
- **Quarterly**: Update imprint category preferences based on market trends
- **Annually**: Validate category assignments against updated BISAC standards

### Common Pitfalls to Avoid

**Over-Categorization:**
- *Problem*: Using all three category slots when only one or two are truly relevant
- *Solution*: Use only categories that genuinely apply to avoid diluting book's focus

**Generic Category Reliance:**
- *Problem*: Defaulting to "General" categories when specific options exist
- *Solution*: Invest time in detailed book descriptions to enable more specific categorization

**Trend Chasing:**
- *Problem*: Choosing popular categories that don't match book content
- *Solution*: Prioritize accuracy over perceived marketability

**Inconsistent Imprint Categorization:**
- *Problem*: Books in same imprint receiving wildly different category types
- *Solution*: Establish clear category preferences at imprint level

## Troubleshooting

### Common Issues and Solutions

**"No LLM completer available for BISAC category generation"**
- *Cause*: AI service is not properly configured
- *Solution*: Contact system administrator to verify LLM integration
- *Workaround*: Manually specify categories in tranche configuration

**"Category name not found in BISAC database"**
- *Cause*: Generated category uses outdated or incorrect naming
- *Solution*: System automatically suggests valid alternatives
- *Action*: Review and select from suggested valid categories

**"Low diversity score warning"**
- *Cause*: All categories come from same top-level subject area
- *Assessment*: Determine if this is appropriate for your book's narrow focus
- *Resolution*: Either accept focused categorization or manually add diverse category

**"Fallback categories used"**
- *Cause*: AI could not generate confident category suggestions
- *Investigation*: Review book description for clarity and specificity
- *Improvement*: Add more detailed keywords and subject matter information

### Understanding Error Messages

**Validation Messages:**
- `"Valid BISAC category name"` - ✅ Category approved
- `"Category name not in database but may be valid"` - ⚠️ Manual verification recommended
- `"Invalid BISAC format"` - ❌ Category code format incorrect
- `"BISAC code not found in current standards"` - ❌ Code doesn't exist in database

**Generation Messages:**
- `"Tranche override used"` - ℹ️ Category from tranche configuration applied
- `"LLM generated categories"` - ℹ️ AI successfully created suggestions
- `"Using fallback categories"` - ⚠️ Default categories applied due to generation failure

### When to Use Manual Overrides

**Appropriate Override Scenarios:**
- Publisher has specific category requirements for marketing campaigns
- Book series requires consistent categorization across all volumes
- Market research indicates alternative category performs better
- Legal or compliance requirements mandate specific categorization

**Override Configuration:**
```json
"required_bisac_subject": "EDUCATION / Teaching Methods & Materials / Science & Technology"
```

**Override Best Practices:**
- Validate manual categories against BISAC database
- Document override reasoning for future reference
- Review override effectiveness through sales data
- Update overrides based on market performance

## Advanced Features

### Diversity Optimization Settings

The system automatically optimizes category diversity to maximize discoverability:

**Diversity Score Calculation:**
- Perfect diversity (1.0): Each category from different top-level subject
- Good diversity (0.7+): Most categories from different subjects
- Poor diversity (0.3-): All categories from same subject area

**Automatic Optimization:**
- System reorders categories to prioritize diverse subjects
- Prevents redundant categorization within same subject area
- Balances specificity with broad market appeal

### Custom Validation Rules

**Imprint-Specific Rules:**
Configure validation requirements for your imprint:

```json
"validation_rules": {
  "required_top_level_subjects": ["BUS", "COM"],
  "prohibited_subjects": ["JUV"],
  "minimum_specificity_level": 2
}
```

**Quality Standards:**
- Minimum confidence thresholds for auto-approval
- Required manual review for certain category types
- Consistency checks across book series

### Integration with Other Metadata Fields

**Cross-Field Validation:**
- Age range consistency with category selection
- Language code alignment with subject matter
- Geographic market compatibility

**Automated Metadata Enhancement:**
- Keywords derived from category selections
- Subject headings generated from BISAC categories
- Thema subject codes mapped from BISAC classifications

**Marketing Integration:**
- Category-based pricing recommendations
- Target audience refinement based on category analysis
- Competitive positioning insights from category selection

---

## Support and Resources

For technical support, configuration assistance, or advanced feature requests, contact your system administrator or refer to the developer documentation for implementation details.

The BISAC Category Generator is designed to streamline your publishing workflow while maintaining the highest standards of industry categorization accuracy. By leveraging AI assistance with human oversight, you can ensure your books reach their intended audiences effectively.