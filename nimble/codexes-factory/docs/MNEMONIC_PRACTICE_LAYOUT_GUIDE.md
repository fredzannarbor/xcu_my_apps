# Mnemonic Practice Layout System Guide

## Overview

The Mnemonic Practice Layout System creates alternating verso/recto page pairs where each mnemonic appears on a left-hand page followed by a dot grid practice page on the right-hand page.

## Features

- **Alternating Layout**: Each mnemonic on verso (left) page, practice on recto (right) page
- **Sequential Numbering**: Practice pages numbered as "Mnemonic Practice 1", "Mnemonic Practice 2", etc.
- **Automatic Page Sequencing**: Ensures proper page alignment for printing
- **Flexible Formatting**: Multiple formatting options for different content types
- **Error Handling**: Graceful fallback for malformed content

## LaTeX Commands

### Core Commands

#### `\mnemonicwithpractice{mnemonic_content}{instruction}`
Creates a mnemonic/practice page pair using default formatting.
- `mnemonic_content`: LaTeX content for the mnemonic
- `instruction`: Text to display at bottom of practice page

#### `\mnemonicwithpracticealternate{mnemonic_content}{instruction}`
Alternative version with different formatting for longer content.

#### `\fullpagedotgridwithinstruction{instruction}`
Creates a full-page dot grid with instruction text at bottom.

### Formatting Commands

#### `\formattedquote{content}` (Default)
- Italic text styling
- 16pt font with 24pt line spacing
- 90% text width
- Best for short, impactful mnemonics

#### `\formattedmnemonic{content}` (Alternative)
- Regular text styling
- 14pt font with 20pt line spacing
- 85% text width
- Best for longer, instructional content

## Usage Examples

### Basic Usage
```latex
\mnemonicwithpractice{
  \textbf{Memory Palace Technique}
  
  Visualize walking through a familiar place, associating each room with a concept you need to remember.
}{Mnemonic Practice 1}
```

### Multiple Mnemonics
```latex
\chapter*{Mnemonics}
\addcontentsline{toc}{chapter}{Mnemonics}

\mnemonicwithpractice{
  \textbf{First Mnemonic}
  Content here...
}{Mnemonic Practice 1}

\mnemonicwithpractice{
  \textbf{Second Mnemonic}
  More content...
}{Mnemonic Practice 2}
```

### Alternative Formatting
```latex
\mnemonicwithpracticealternate{
  \textbf{Long Mnemonic Title}
  
  This is a longer mnemonic with multiple sentences and detailed explanations that benefit from the alternative formatting approach.
}{Mnemonic Practice 3}
```

## Data Format

### JSON Input Format
```json
{
  "mnemonics_tex": "\\textbf{First Mnemonic}\nContent for first mnemonic.\n\n\\textbf{Second Mnemonic}\nContent for second mnemonic."
}
```

### LaTeX Content Structure
Each mnemonic should start with `\textbf` at the beginning of a line:
```latex
\textbf{Mnemonic Title}
Mnemonic content and explanation.

\textbf{Another Mnemonic}
More content here.
```

## Processing Flow

1. **Content Detection**: System detects `mnemonics_tex` in book data
2. **Mnemonic Extraction**: Parses individual mnemonics using regex pattern `^\\textbf`
3. **Layout Generation**: Creates alternating verso/recto pairs
4. **Page Sequencing**: Ensures proper page alignment with `\cleartoverso`
5. **LaTeX Generation**: Outputs complete `.tex` file for compilation

## Configuration Options

### Template Selection
Choose between formatting options by modifying the prepress processing:

```python
# Default formatting
instruction = f"Mnemonic Practice {i}"
layout_parts.append(f"\\mnemonicwithpractice{{{mnemonic_content}}}{{{instruction}}}")

# Alternative formatting
layout_parts.append(f"\\mnemonicwithpracticealternate{{{mnemonic_content}}}{{{instruction}}}")
```

### Dot Grid Customization
Modify dot grid appearance by updating the generation parameters:
- Grid spacing: Default 5mm
- Dot opacity: Default 100%
- Grid height: Default 75% of text height

## Error Handling

### Common Issues and Solutions

#### No Mnemonics Generated
**Cause**: Empty or malformed `mnemonics_tex` content
**Solution**: Ensure content starts with `\textbf` at line beginning

#### LaTeX Compilation Errors
**Cause**: Special characters not properly escaped
**Solution**: Use `escape_latex()` function for user content

#### Page Alignment Issues
**Cause**: Odd number of pages or missing `\cleartoverso`
**Solution**: System automatically adds `\cleardoublepage` for proper alignment

### Logging and Debugging

The system provides detailed logging:
```
INFO: Extracted 3 individual mnemonics for practice layout
INFO: Generated 3 mnemonic pairs, expecting 6 content pages
INFO: Successfully wrote mnemonics.tex with 3 mnemonic/practice pairs
```

## Best Practices

### Content Guidelines
1. **Keep mnemonics concise**: Aim for 1-3 sentences per mnemonic
2. **Use clear titles**: Start each mnemonic with `\textbf{Clear Title}`
3. **Avoid special characters**: Or ensure proper LaTeX escaping
4. **Test formatting**: Preview with both formatting options

### Layout Considerations
1. **Page count planning**: Each mnemonic adds 2 pages to the book
2. **Print alignment**: System ensures proper verso/recto sequencing
3. **Dot grid scaling**: Practice pages automatically scale for instruction text

### Performance Tips
1. **Batch processing**: System efficiently processes multiple mnemonics
2. **Error recovery**: Malformed content doesn't break entire processing
3. **Memory usage**: Scales linearly with content size

## Troubleshooting

### Common Problems

#### "No mnemonics found in LaTeX content"
- Check that content starts with `\textbf` at line beginning
- Verify content is not empty or None
- Ensure proper line breaks between mnemonics

#### LaTeX compilation fails
- Check for unescaped special characters (&, %, $, #)
- Verify all commands are properly closed
- Test with minimal content first

#### Page numbering issues
- Ensure `\cleartoverso` is working properly
- Check that dot grid image exists
- Verify page style settings

### Debug Mode
Enable detailed logging by setting log level to DEBUG:
```python
logger.setLevel(logging.DEBUG)
```

## Integration with Existing System

### Backward Compatibility
The system maintains compatibility with existing mnemonic processing:
- Falls back to old markdown-based processing if needed
- Preserves existing data formats
- Maintains current prompt system

### Template Integration
New commands integrate seamlessly with existing templates:
- Uses existing `\formattedquote` command
- Leverages current dot grid system
- Maintains page style consistency

## Future Enhancements

### Planned Features
1. **Dynamic formatting selection** based on content length
2. **Custom styling options** per imprint
3. **Interactive practice elements** in digital versions
4. **Accessibility improvements** for better readability

### Configuration Expansion
Future versions may include:
- Configurable instruction text templates
- Custom dot grid patterns
- Alternative page layouts
- Multi-language support