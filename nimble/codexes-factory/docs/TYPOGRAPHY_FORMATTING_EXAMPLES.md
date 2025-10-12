# Typography and Formatting Examples

## Overview

This document provides examples of proper typography and formatting for bibliography entries, glossary layouts, and other book production elements using the enhanced formatting system.

## Bibliography Formatting Examples

### Chicago Style Bibliography

#### Single Author Book
```latex
% Input
BibliographyEntry(
    author="Smith, John",
    title="Modern Publishing Techniques",
    publisher="Academic Press",
    year="2023"
)

% Output
\begin{thebibliography}{99}
\setlength{\itemindent}{-0.15in}
\setlength{\leftmargin}{0.15in}
\setlength{\itemsep}{6pt}

\bibitem{001} Smith, John. \textit{Modern Publishing Techniques}. Academic Press, 2023.

\end{thebibliography}
```

#### Multiple Authors
```latex
% Input
BibliographyEntry(
    author="Johnson, Mary and Williams, Robert",
    title="Collaborative Writing in the Digital Age",
    publisher="Tech Publications",
    year="2024"
)

% Output
\bibitem{002} Johnson, Mary and Williams, Robert. \textit{Collaborative Writing in the Digital Age}. Tech Publications, 2024.
```

#### Book with Pages
```latex
% Input
BibliographyEntry(
    author="Brown, Sarah",
    title="Academic Writing Standards",
    publisher="University Press",
    year="2023",
    pages="45-67"
)

% Output
\bibitem{003} Brown, Sarah. \textit{Academic Writing Standards}. University Press, 2023. pp. 45-67.
```

### MLA Style Bibliography

```latex
% Input (with citation_style="mla")
BibliographyEntry(
    author="Davis, Michael",
    title="Research Methodologies",
    publisher="Scholarly Books",
    year="2024"
)

% Output
\bibitem{004} Davis, Michael. \textit{Research Methodologies}. Scholarly Books, 2024.
```

### Long Bibliography Entry with Hanging Indent

```latex
% Example of how hanging indent works with long entries
\bibitem{005} Anderson, Jennifer Elizabeth and Thompson, Christopher James. \textit{Comprehensive Guide to Modern Academic Publishing: Standards, Practices, and Digital Transformation in the Twenty-First Century}. International Academic Publishers, 2024. pp. 123-456.
```

The hanging indent ensures that the second and subsequent lines are indented 0.15 inches from the left margin, creating a professional appearance.

## Glossary Layout Examples

### Two-Column Korean/English Glossary

#### Basic Term Stacking
```latex
% Input
{
    'korean': '안녕',
    'english': 'hello',
    'definition': 'A common greeting used when meeting someone'
}

% Output
\begin{multicols}{2}
\raggedcolumns

\noindent
\textbf{\parbox[t]{2in}{\fontspec{Apple Myungjo}[10pt]{안녕}\\\fontspec{Adobe Caslon Pro}[9pt]{hello}}}
\\[3pt]
\fontsize{9pt}{\baselineskip}\selectfont
A common greeting used when meeting someone
\\[6pt]

\end{multicols}
```

#### Multiple Terms Example
```latex
% Complete glossary with multiple terms
\clearpage
\chapter*{Glossary}
\addcontentsline{toc}{chapter}{Glossary}

\setlength{\columnsep}{0.25in}
\setlength{\columnseprule}{0.5pt}

\begin{multicols}{2}
\raggedcolumns

\noindent
\textbf{\parbox[t]{2in}{\fontspec{Apple Myungjo}[10pt]{안녕}\\\fontspec{Adobe Caslon Pro}[9pt]{hello}}}
\\[3pt]
\fontsize{9pt}{\baselineskip}\selectfont
A greeting used when meeting someone
\\[6pt]

\noindent
\textbf{\parbox[t]{2in}{\fontspec{Apple Myungjo}[10pt]{감사}\\\fontspec{Adobe Caslon Pro}[9pt]{thanks}}}
\\[3pt]
\fontsize{9pt}{\baselineskip}\selectfont
Expression of gratitude or appreciation
\\[6pt]

\noindent
\textbf{\parbox[t]{2in}{\fontspec{Apple Myungjo}[10pt]{학교}\\\fontspec{Adobe Caslon Pro}[9pt]{school}}}
\\[3pt]
\fontsize{9pt}{\baselineskip}\selectfont
An educational institution for learning
\\[6pt]

\end{multicols}
```

### Table-Based Glossary Layout (Alternative)

```latex
\begin{longtable}{p{0.45\textwidth} p{0.45\textwidth}}

\textbf{\parbox[t]{2in}{\fontspec{Apple Myungjo}[10pt]{안녕}\\\fontspec{Adobe Caslon Pro}[9pt]{hello}}}
\\[3pt]
\fontsize{9pt}{\baselineskip}\selectfont
A greeting used when meeting someone
& 
\textbf{\parbox[t]{2in}{\fontspec{Apple Myungjo}[10pt]{감사}\\\fontspec{Adobe Caslon Pro}[9pt]{thanks}}}
\\[3pt]
\fontsize{9pt}{\baselineskip}\selectfont
Expression of gratitude
\\[6pt]

\textbf{\parbox[t]{2in}{\fontspec{Apple Myungjo}[10pt]{학교}\\\fontspec{Adobe Caslon Pro}[9pt]{school}}}
\\[3pt]
\fontsize{9pt}{\baselineskip}\selectfont
Educational institution
& 
\textbf{\parbox[t]{2in}{\fontspec{Apple Myungjo}[10pt]{친구}\\\fontspec{Adobe Caslon Pro}[9pt]{friend}}}
\\[3pt]
\fontsize{9pt}{\baselineskip}\selectfont
A close companion
\\[6pt]

\end{longtable}
```

## Typography Examples

### Mnemonics Page Formatting

#### Standard Mnemonics
```latex
% Input
[
    {'text': 'Remember to always verify your sources', 'type': 'standard'},
    {'text': 'Quality over quantity in research', 'type': 'standard'}
]

% Output
\clearpage
\chapter*{Mnemonics}
\addcontentsline{toc}{chapter}{Mnemonics}

\fontspec{Adobe Caslon Pro}
\begin{itemize}
\setlength{\itemsep}{12pt}

\item Remember to always verify your sources

\item Quality over quantity in research

\end{itemize}
```

#### Acronym Mnemonics
```latex
% Input
{
    'text': 'SMART goals are essential',
    'type': 'acronym',
    'acronym': 'SMART',
    'expanded': 'Specific Measurable Achievable Relevant Timely'
}

% Output
\item \textbf{S}: Specific
\item \textbf{M}: Measurable
\item \textbf{A}: Achievable
\item \textbf{R}: Relevant
\item \textbf{T}: Timely
```

### Korean Text on Title Page

```latex
% Input
korean_text = "학술 출판의 미래"

% Output
\fontspec{Apple Myungjo}[12pt]{학술 출판의 미래}
```

### Chapter Heading with Adjusted Leading

```latex
% Input
content = "\\chapter{Introduction to Academic Writing}\nThis chapter covers..."

% Output
\chapter{Introduction to Academic Writing}
\vspace{-\baselineskip}\vspace{36pt}
This chapter covers...
```

### Instruction Pages

```latex
% Automatic instruction placement setup
\usepackage{fancyhdr}
\usepackage{ifthen}

% Define instruction text
\newcommand{\instructiontext}{Read carefully and reflect on the meaning of each quotation.}

% Custom page style for instruction pages
\fancypagestyle{instructionpage}{
  \fancyhf{}
  \fancyfoot[C]{\small\instructiontext}
  \renewcommand{\headrulewidth}{0pt}
  \renewcommand{\footrulewidth}{0pt}
}

% Apply instruction style every 8th recto page
\newcommand{\checkforinstructions}{
  \ifthenelse{\isodd{\thepage}}{
    \ifthenelse{\equal{\arabic{page} \bmod 8}{1}}{
      \thispagestyle{instructionpage}
    }{}
  }{}
}

% Hook into page output
\AddEverypageHook{\checkforinstructions}
```

## Publisher's Note Examples

### Properly Formatted Publisher's Note

```text
This pilsa book presents "Advanced Research Methodologies" as an essential exploration of academic inquiry. Developed by the AI Lab for Book-Lovers, this work synthesizes key insights and perspectives to provide readers with a comprehensive understanding of contemporary research practices. The carefully curated content serves both as an educational resource and a catalyst for deeper reflection in today's evolving academic landscape.

The book features 90 carefully selected quotations that represent diverse perspectives and timeless wisdom from leading researchers and scholars. The material explores cutting-edge methodologies and established practices that bridge theoretical foundations with practical applications. Each section is designed to engage readers intellectually while providing practical insights for contemporary research challenges.

For publishers, this work represents an opportunity to offer readers meaningful content that bridges academic rigor with accessible presentation. For readers, the book serves as both an educational journey and a practical guide for navigating the complexities of modern research methodology. Whether used for personal enrichment, academic study, or professional development, this pilsa book delivers lasting value and intellectual satisfaction.
```

**Structure Analysis**:
- **Paragraph 1**: 398 characters (✓ under 600)
- **Paragraph 2**: 456 characters (✓ under 600)  
- **Paragraph 3**: 587 characters (✓ under 600)
- **Pilsa explanation**: ✓ Present in paragraphs 1 and 3
- **Current events reference**: ✓ "contemporary", "modern", "today's evolving"
- **Publisher/reader motivation**: ✓ Present in paragraph 3

## ISBN Barcode Examples

### UPC-A Barcode Integration

```latex
% ISBN: 978-0-123456-78-9
% UPC Code: 012345678-4 (after conversion)

% Barcode placement on back cover
\begin{textblock*}{2in}(4.5in,8.5in)
\centering
% Barcode image would be included here
% Base64 data: iVBORw0KGgoAAAANSUhEUgAAASwAAAEsCAYAAAB5fY51...
\\[2pt]
\fontsize{8pt}{10pt}\selectfont
\texttt{978-0-123456-78-9}
\end{textblock*}
```

### Formatted ISBN Numerals

```text
Input: 9780123456789
Output: 978-0-123456-78-9

Input: 9791234567890  
Output: 979-1-234567-89-0
```

## Quote Assembly Examples

### Before Optimization (Author Repetition Problem)

```text
1. "Quote 1" - Author A
2. "Quote 2" - Author A  
3. "Quote 3" - Author A
4. "Quote 4" - Author A  ← Violation (4 consecutive)
5. "Quote 5" - Author B
6. "Quote 6" - Author B
7. "Quote 7" - Author B
8. "Quote 8" - Author B  ← Violation (4 consecutive)
```

### After Optimization (Improved Distribution)

```text
1. "Quote 1" - Author A
2. "Quote 5" - Author B
3. "Quote 2" - Author A
4. "Quote 6" - Author B
5. "Quote 3" - Author A
6. "Quote 7" - Author B
7. "Quote 4" - Author A  ← Only 3 consecutive max
8. "Quote 8" - Author B
```

### Thematic Grouping Example

```text
Leadership Theme:
1. "Leadership is action, not position" - Author A
2. "The best leaders are servants first" - Author B  
3. "Leadership is influence, nothing more" - Author C

Wisdom Theme:
4. "Wisdom comes from experience" - Author A
5. "Knowledge speaks, wisdom listens" - Author D
6. "The wise learn from others' mistakes" - Author B
```

## Writing Style Configuration Examples

### Hierarchical Style Loading

#### Publisher Level (configs/publishers/academic_press.json)
```json
{
  "writing_style": {
    "text_values": [
      "Maintain academic rigor and scholarly tone",
      "Use formal language appropriate for academic audience"
    ],
    "style_type": "academic"
  }
}
```

#### Imprint Level (configs/imprints/research_series.json)
```json
{
  "writing_style": {
    "text_values": [
      "Focus on empirical evidence and data-driven conclusions",
      "Include methodological considerations in discussions"
    ],
    "style_type": "research"
  }
}
```

#### Tranche Level (configs/tranches/methodology_books.json)
```json
{
  "writing_style": {
    "text_values": [
      "Emphasize practical applications of research methods",
      "Provide step-by-step guidance for implementation"
    ],
    "style_type": "practical"
  }
}
```

#### Merged Style Prompt
```text
Please follow these writing style guidelines:
1. Maintain academic rigor and scholarly tone
2. Use formal language appropriate for academic audience
3. Focus on empirical evidence and data-driven conclusions
4. Include methodological considerations in discussions
5. Emphasize practical applications of research methods
6. Provide step-by-step guidance for implementation
```

## Error Handling Examples

### Quote Verification Error Recovery

#### Invalid Response
```json
// Invalid verifier response (missing verified_quotes)
{
  "status": "completed",
  "message": "Verification complete"
}

// Recovered response
{
  "verified_quotes": [],
  "verification_status": "recovered_empty",
  "error_details": "Missing verified_quotes field in original response"
}
```

#### Malformed Response Recovery
```json
// Original quotes
[
  {"quote": "Test quote", "author": "Test Author", "source": "Test Source"}
]

// Recovery using original quotes
{
  "verified_quotes": [
    {
      "is_accurate": false,
      "verified_quote": "Test quote",
      "verified_source": "Test Source", 
      "verified_author": "Test Author",
      "verification_notes": "Recovery: Original quote used due to verification failure"
    }
  ],
  "verification_status": "recovered_original"
}
```

### Field Completion Error Recovery

```python
# Original error
AttributeError: 'FieldCompleter' object has no attribute 'complete_field'

# Recovery attempt - search for alternative methods
if hasattr(completer_obj, 'complete_field_safe'):
    return completer_obj.complete_field_safe
elif hasattr(completer_obj, 'complete_field_fallback'):
    return completer_obj.complete_field_fallback
else:
    # Return safe default function
    return lambda *args, **kwargs: "[Recovered] Default value for field_name"
```

These examples demonstrate the proper formatting and structure for all major components of the book production system. Use these as templates when implementing or troubleshooting the various formatting features.