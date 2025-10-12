# Mnemonic Practice Layout Troubleshooting Guide

## Common Issues and Solutions

### 1. No Mnemonics Generated

#### Symptoms
- `mnemonics.tex` file is not created
- Log message: "No mnemonics found in LaTeX content"
- Empty mnemonic section in final PDF

#### Causes and Solutions

**Empty or Missing Content**
```json
// Problem
{
  "mnemonics_tex": ""
}

// Solution
{
  "mnemonics_tex": "\\textbf{Valid Mnemonic}\nContent here."
}
```

**Incorrect Format**
```latex
% Problem - \textbf not at line beginning
Some text \textbf{Mnemonic Title}
Content here.

% Solution - \textbf at line start
\textbf{Mnemonic Title}
Content here.
```

**Missing Line Breaks**
```latex
% Problem - no separation between mnemonics
\textbf{First}\textbf{Second}

% Solution - proper separation
\textbf{First}
Content for first.

\textbf{Second}
Content for second.
```

### 2. LaTeX Compilation Errors

#### Symptoms
- PDF generation fails
- LaTeX error messages in logs
- Incomplete or corrupted output

#### Common LaTeX Errors

**Unescaped Special Characters**
```latex
% Problem
\textbf{Using & and % symbols}

% Solution
\textbf{Using \& and \% symbols}
```

**Unclosed Commands**
```latex
% Problem
\textbf{Missing closing brace

% Solution
\textbf{Proper closing brace}
```

**Missing Required Packages**
```latex
% Add to template if missing
\usepackage{graphicx}  % For dot grid images
\usepackage{calc}      % For calculations
```

### 3. Page Layout Issues

#### Symptoms
- Mnemonics not on verso pages
- Practice pages misaligned
- Incorrect page numbering

#### Solutions

**Page Alignment Problems**
```latex
% Ensure proper sequencing
\cleartoverso  % Forces verso start
\mnemonicwithpractice{content}{instruction}
\cleardoublepage  % Ensures even page count
```

**Missing Dot Grid**
```bash
# Check if dot grid file exists
ls build_directory/dotgrid.png

# Regenerate if missing
python src/codexes/modules/prepress/generate_dot_grid.py
```

### 4. Content Processing Errors

#### Symptoms
- Partial mnemonic extraction
- Incorrect mnemonic count
- Missing practice pages

#### Debugging Steps

**Check Regex Pattern**
```python
import re
pattern = r'^\\textbf'
matches = re.findall(pattern, content, re.MULTILINE)
print(f"Found {len(matches)} mnemonics")
```

**Validate Content Structure**
```python
def debug_mnemonic_content(content):
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('\\textbf'):
            print(f"Line {i}: {line[:50]}...")
```

### 5. Instruction Text Issues

#### Symptoms
- Missing instruction text on practice pages
- Incorrect numbering
- Formatting problems

#### Solutions

**Check Instruction Generation**
```python
# Verify instruction format
for i in range(1, mnemonic_count + 1):
    instruction = f"Mnemonic Practice {i}"
    print(f"Generated: {instruction}")
```

**Validate LaTeX Command**
```latex
% Test instruction placement
\fullpagedotgridwithinstruction{Test Instruction}
```

## Diagnostic Tools

### 1. Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

### 2. Content Validation Script

```python
def validate_mnemonic_content(content):
    """Validate mnemonic content structure."""
    if not content:
        return False, "Empty content"
    
    pattern = r'^\\textbf'
    matches = re.findall(pattern, content, re.MULTILINE)
    
    if not matches:
        return False, "No \\textbf commands at line beginning"
    
    return True, f"Found {len(matches)} valid mnemonics"

# Usage
is_valid, message = validate_mnemonic_content(mnemonics_tex)
print(f"Validation: {message}")
```

### 3. LaTeX Test Compilation

```bash
# Create minimal test file
cat > test_mnemonic.tex << 'EOF'
\documentclass{article}
\usepackage{graphicx}

% Include mnemonic commands here
\input{mnemonic_commands.tex}

\begin{document}
\mnemonicwithpractice{Test content}{Test Practice 1}
\end{document}
EOF

# Test compilation
pdflatex test_mnemonic.tex
```

## Error Messages Reference

### Processing Errors

| Error Message | Cause | Solution |
|---------------|-------|----------|
| "No mnemonics content provided" | Empty `mnemonics_tex` | Add valid content |
| "Error extracting mnemonics" | Regex processing failed | Check content format |
| "No mnemonics found in LaTeX content" | No `\textbf` at line start | Fix content structure |
| "Error generating mnemonic layout" | LaTeX generation failed | Check for special characters |

### LaTeX Compilation Errors

| Error Message | Cause | Solution |
|---------------|-------|----------|
| "Undefined control sequence" | Missing command definition | Add command to template |
| "File not found: dotgrid.png" | Missing dot grid image | Generate dot grid file |
| "Missing \begin{document}" | Template structure issue | Check template integrity |

## Performance Issues

### Large Content Processing

**Symptoms**
- Slow processing with many mnemonics
- Memory usage spikes
- Timeout errors

**Solutions**
```python
# Process in batches for large content
def process_mnemonics_in_batches(mnemonics, batch_size=10):
    for i in range(0, len(mnemonics), batch_size):
        batch = mnemonics[i:i+batch_size]
        process_batch(batch)
```

### LaTeX Compilation Performance

**Optimization Tips**
- Use `lualatex` for better Unicode support
- Enable `--interaction=nonstopmode` for automated processing
- Cache compiled templates when possible

## Recovery Procedures

### 1. Fallback Content Generation

```python
def create_fallback_mnemonics():
    """Create minimal fallback content."""
    return """
    \\chapter*{Mnemonics}
    \\addcontentsline{toc}{chapter}{Mnemonics}
    
    Content processing encountered an error. 
    Please check the source data and try again.
    """
```

### 2. Partial Recovery

```python
def recover_partial_mnemonics(failed_content):
    """Attempt to recover what we can."""
    # Extract any valid \textbf commands
    valid_parts = []
    for line in failed_content.split('\n'):
        if line.strip().startswith('\\textbf'):
            valid_parts.append(line)
    
    return '\n'.join(valid_parts) if valid_parts else None
```

## Prevention Best Practices

### 1. Content Validation

- Always validate input before processing
- Use consistent formatting in source data
- Test with sample content before full processing

### 2. Error Handling

- Implement comprehensive try-catch blocks
- Provide meaningful error messages
- Create fallback options for critical failures

### 3. Testing Strategy

- Unit test individual components
- Integration test full pipeline
- Visual verification of output PDFs

### 4. Monitoring

- Log all processing steps
- Track success/failure rates
- Monitor performance metrics

## Getting Help

### Log Analysis

When reporting issues, include:
1. Complete error messages
2. Input data sample
3. Processing logs
4. System environment details

### Debug Information Collection

```python
def collect_debug_info():
    """Collect system information for debugging."""
    import sys, platform
    
    info = {
        'python_version': sys.version,
        'platform': platform.platform(),
        'latex_available': shutil.which('pdflatex') is not None,
        'content_length': len(mnemonics_tex) if mnemonics_tex else 0
    }
    
    return info
```

### Support Resources

- Check existing documentation first
- Review test cases for examples
- Examine log files for detailed error information
- Test with minimal content to isolate issues