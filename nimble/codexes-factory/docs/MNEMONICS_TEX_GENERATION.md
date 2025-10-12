# Mnemonics LaTeX Generation

## Overview

The mnemonics section has been updated to generate LaTeX (.tex) files that are saved directly to a `mnemonics` directory in the build folder. This provides better organization and allows for more sophisticated LaTeX formatting.

## Changes Made

### 1. Updated Prompts

**Files Modified:**
- `prompts/prompts.json`
- `imprints/xynapse_traces/prompts.json`

**Changes:**
- Modified `mnemonics_prompt` to return LaTeX code directly instead of Markdown
- Changed the JSON key from `mnemonics` to `mnemonics_tex`
- Added detailed LaTeX formatting examples in the prompt
- Added `returns_tex` tag to indicate LaTeX output

### 2. Updated Prepress Processing

**File Modified:**
- `imprints/xynapse_traces/prepress.py`

**Changes:**
- Added support for new `mnemonics_tex` field
- Creates a `mnemonics` directory in the build folder
- Saves LaTeX content to `mnemonics/mnemonics_content.tex`
- Maintains backward compatibility with old `mnemonics` field
- Automatically counts `\item` entries to generate appropriate practice pages

### 3. Updated Data Structure

**File Modified:**
- `src/codexes/modules/builders/llm_get_book_data.py`

**Changes:**
- Added `mnemonics_tex` field to the initial book JSON structure
- Maintains existing `mnemonics` field for backward compatibility

## Usage

### New Workflow

1. **LLM Generation**: The `mnemonics_prompt` now generates complete LaTeX code
2. **Data Storage**: LaTeX content is stored in the `mnemonics_tex` field in the book JSON
3. **File Generation**: During prepress, the LaTeX is saved to `build_dir/mnemonics/mnemonics_content.tex`
4. **Integration**: The main `mnemonics.tex` file includes the generated content and adds practice pages

### Directory Structure

```
build_dir/
├── mnemonics/
│   └── mnemonics_content.tex  # Generated LaTeX content
├── mnemonics.tex              # Main file that includes content + practice pages
├── title_page.tex
├── copyright_page.tex
└── ... (other generated files)
```

### LaTeX Output Format

The generated LaTeX includes:
- Chapter heading with TOC entry
- Formatted mnemonics with bold letters
- Itemized lists for concepts
- Proper spacing and formatting
- Multiple mnemonic types (acronyms, phrases, etc.)

### Example Generated Content

```latex
% Mnemonics for Key Concepts
\cleartoverso
\chapter*{Mnemonics}
\addcontentsline{toc}{chapter}{Mnemonics}

\textbf{R}emember \textbf{E}very \textbf{A}rgument \textbf{D}aily

\vspace{1em}

The key concepts are:

\begin{itemize}
    \item Reading comprehension
    \item Engagement with ideas
    \item Active learning
    \item Daily practice
\end{itemize}
```

## Backward Compatibility

The system maintains backward compatibility:
- If `mnemonics_tex` is present, it takes precedence
- If only `mnemonics` (old Markdown format) is present, it's processed as before
- Both fields can coexist during transition period

## Benefits

1. **Better Organization**: LaTeX files are saved in a dedicated directory
2. **Improved Formatting**: Direct LaTeX generation allows for sophisticated formatting
3. **Easier Debugging**: Separate files make it easier to debug LaTeX issues
4. **Flexibility**: LaTeX content can be easily modified or extended
5. **Maintainability**: Clear separation between generated content and processing logic

## Testing

The implementation has been tested with:
- LaTeX content generation and file saving
- Directory creation
- Practice page generation based on item count
- Integration with existing prepress pipeline

All tests pass successfully, confirming the functionality works as expected.