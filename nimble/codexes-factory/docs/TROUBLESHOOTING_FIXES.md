# Troubleshooting Guide for Final Fixes

This guide provides solutions for common issues encountered with the final fixes implementation.

## ISBN Formatter Issues

### Problem: ISBN validation fails for valid ISBNs

**Symptoms**:
- Valid ISBNs are rejected
- Error message: "Invalid ISBN-13 check digit"
- Formatting returns original ISBN unchanged

**Causes**:
1. Incorrect check digit calculation
2. Invalid ISBN test data
3. Whitespace or formatting issues

**Solutions**:

1. **Verify ISBN check digit**:
```python
def calculate_isbn13_check_digit(isbn12):
    """Calculate the check digit for ISBN-13"""
    total = 0
    for i, digit in enumerate(isbn12):
        weight = 1 if i % 2 == 0 else 3
        total += int(digit) * weight
    return (10 - (total % 10)) % 10

# Example: 978013468599 -> check digit should be 1
isbn12 = "978013468599"
check_digit = calculate_isbn13_check_digit(isbn12)
valid_isbn = isbn12 + str(check_digit)  # 9780134685991
```

2. **Clean input data**:
```python
# Remove hyphens and spaces
clean_isbn = isbn.replace('-', '').replace(' ', '').strip()
```

3. **Use valid test ISBNs**:
```python
# Valid test ISBNs with correct check digits
valid_isbns = [
    "9780134685991",  # Valid
    "9791020304056",  # Valid 979 prefix
    "9780321125217"   # Valid alternative
]
```

### Problem: Hyphenation not working correctly

**Symptoms**:
- ISBNs returned without hyphens
- Incorrect hyphen placement
- Basic hyphenation used instead of rules

**Solutions**:

1. **Check hyphenation rules coverage**:
```python
# Verify ISBN prefix and group are supported
isbn = "9780134685991"
prefix = isbn[:3]  # Should be 978 or 979
group = isbn[3:4]  # Should be in hyphenation rules

if prefix in formatter.hyphenation_rules:
    if group in formatter.hyphenation_rules[prefix]:
        print("Rules available")
    else:
        print("Group not in rules, will use basic hyphenation")
```

2. **Add missing hyphenation rules**:
```python
# Extend hyphenation rules for new ISBN ranges
formatter.hyphenation_rules['978']['2'] = [
    (1, [(0, 19999)]),
    (2, [(200000, 699999)]),
    # Add more ranges as needed
]
```

## Barcode Generator Issues

### Problem: Barcode positioning outside cover bounds

**Symptoms**:
- Barcode positioned at negative coordinates
- Barcode extends beyond cover edges
- Safety space validation fails

**Solutions**:

1. **Verify cover dimensions**:
```python
# Ensure cover dimensions are reasonable
cover_specs = {
    "width": 6.0,   # Should be > 4.0 inches minimum
    "height": 9.0   # Should be > 6.0 inches minimum
}

# Check if dimensions can accommodate barcode
min_width = generator.barcode_size.width + 2 * generator.min_safety_spaces.left
min_height = generator.barcode_size.height + 2 * generator.min_safety_spaces.bottom

if cover_specs["width"] < min_width or cover_specs["height"] < min_height:
    print("Cover too small for barcode with safety margins")
```

2. **Adjust positioning calculation**:
```python
# Custom positioning for small covers
def calculate_safe_position(cover_dimensions, barcode_size, safety_spaces):
    width, height = cover_dimensions
    
    # Calculate maximum safe position
    max_x = width - barcode_size.width - safety_spaces.right
    max_y = height - barcode_size.height - safety_spaces.top
    
    # Use smaller offsets for small covers
    x_offset = min(0.5, max_x * 0.1)
    y_offset = min(0.25, max_y * 0.1)
    
    x = max(safety_spaces.left, max_x - x_offset)
    y = max(safety_spaces.bottom, y_offset)
    
    return Position(x=x, y=y)
```

### Problem: Barcode generation library not available

**Symptoms**:
- ImportError for barcode library
- Placeholder barcode generated
- Warning about missing python-barcode

**Solutions**:

1. **Install barcode library**:
```bash
uv add python-barcode[images]
# or
pip install python-barcode[images] pillow
```

2. **Verify installation**:
```python
try:
    from barcode import Code128
    from barcode.writer import ImageWriter
    print("Barcode library available")
except ImportError as e:
    print(f"Barcode library not available: {e}")
```

## Dotgrid Layout Issues

### Problem: Template modification fails

**Symptoms**:
- Template file not found
- Permission denied errors
- LaTeX compilation errors after modification

**Solutions**:

1. **Check file permissions**:
```python
from pathlib import Path

template_path = Path("imprints/xynapse_traces/template.tex")

# Check existence and permissions
if not template_path.exists():
    print(f"Template not found: {template_path}")
elif not template_path.is_file():
    print(f"Path is not a file: {template_path}")
elif not os.access(template_path, os.W_OK):
    print(f"No write permission: {template_path}")
else:
    print("Template accessible")
```

2. **Create backup before modification**:
```python
import shutil
from datetime import datetime

def backup_template(template_path):
    backup_path = template_path.with_suffix(
        f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tex"
    )
    shutil.copy2(template_path, backup_path)
    return backup_path
```

3. **Validate LaTeX syntax**:
```python
def validate_latex_syntax(content):
    """Basic LaTeX syntax validation"""
    issues = []
    
    # Check for balanced braces
    brace_count = content.count('{') - content.count('}')
    if brace_count != 0:
        issues.append(f"Unbalanced braces: {brace_count}")
    
    # Check for required commands
    required_commands = ['\\begin{document}', '\\end{document}']
    for cmd in required_commands:
        if cmd not in content:
            issues.append(f"Missing command: {cmd}")
    
    return issues
```

### Problem: Spacing validation fails

**Symptoms**:
- Header spacing less than 0.5 inches
- Dotgrid position too high or low
- Page boundary violations

**Solutions**:

1. **Adjust page specifications**:
```python
# For tight layouts, reduce header/footer heights
page_specs = PageSpecs(
    width=5.5,
    height=8.5,
    header_height=0.5,    # Reduced from 0.75
    footer_height=0.3,    # Reduced from 0.5
    margin_top=0.75,      # Reduced from 1.0
    margin_bottom=0.75    # Reduced from 1.0
)
```

2. **Calculate available space**:
```python
def calculate_available_space(page_specs, min_spacing=0.5):
    """Calculate space available for dotgrid"""
    total_reserved = (
        page_specs.margin_top + 
        page_specs.margin_bottom +
        page_specs.header_height + 
        page_specs.footer_height +
        2 * min_spacing  # Top and bottom spacing
    )
    
    available = page_specs.height - total_reserved
    return max(0, available)
```

## Subtitle Validator Issues

### Problem: LLM calls fail or timeout

**Symptoms**:
- Connection timeout errors
- Empty LLM responses
- API key or authentication errors

**Solutions**:

1. **Configure retry logic**:
```python
import time
from functools import wraps

def retry_llm_call(max_attempts=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise e
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
            return None
        return wrapper
    return decorator

@retry_llm_call(max_attempts=3, delay=1)
def call_llm_with_retry(llm_caller, request):
    return llm_caller.call_llm(request)
```

2. **Implement fallback strategies**:
```python
def generate_subtitle_with_fallback(original, char_limit):
    """Generate subtitle with multiple fallback strategies"""
    
    # Strategy 1: Try LLM
    try:
        llm_result = call_llm_for_subtitle(original)
        if llm_result and len(llm_result) <= char_limit:
            return llm_result
    except Exception as e:
        logger.warning(f"LLM failed: {e}")
    
    # Strategy 2: Intelligent truncation
    words = original.split()
    if len(words) > 3:
        # Keep first 2 and last 1 words
        key_words = words[:2] + words[-1:]
        result = ' '.join(key_words)
        if len(result) <= char_limit:
            return result
    
    # Strategy 3: Simple truncation
    if len(original) > char_limit:
        return original[:char_limit-3] + "..."
    
    return original
```

### Problem: Generated subtitles still too long

**Symptoms**:
- LLM returns subtitles exceeding character limit
- Validation fails after generation
- Truncation produces poor results

**Solutions**:

1. **Improve LLM prompt**:
```python
def create_strict_prompt(original, title, subject, char_limit):
    return f"""
Create a subtitle for this book that is EXACTLY {char_limit} characters or fewer.

STRICT REQUIREMENTS:
- Maximum {char_limit} characters (count carefully)
- Must be shorter than the original
- Keep the core meaning
- Academic/educational tone

Book: {title}
Subject: {subject}
Original: {original}

Count your characters carefully. Your response must be {char_limit} characters or less.

New subtitle (max {char_limit} chars):"""
```

2. **Post-process LLM responses**:
```python
def clean_and_validate_response(response, char_limit):
    """Clean and validate LLM response"""
    if not response:
        return None
    
    # Clean response
    cleaned = response.strip().strip('"\'').strip()
    
    # Remove common LLM artifacts
    artifacts = ["New subtitle:", "Subtitle:", "Response:"]
    for artifact in artifacts:
        if cleaned.startswith(artifact):
            cleaned = cleaned[len(artifact):].strip()
    
    # Validate length
    if len(cleaned) <= char_limit:
        return cleaned
    
    # Try to truncate at word boundary
    words = cleaned.split()
    result = ""
    for word in words:
        if len(result + " " + word) <= char_limit:
            result += (" " if result else "") + word
        else:
            break
    
    return result if result else cleaned[:char_limit]
```

## Spine Width Calculator Issues

### Problem: SpineWidthLookup.xlsx file not found

**Symptoms**:
- FileNotFoundError for lookup file
- Fallback spine width always used
- Warning about missing lookup data

**Solutions**:

1. **Check file location and permissions**:
```python
from pathlib import Path

lookup_path = Path("resources/SpineWidthLookup.xlsx")

if not lookup_path.exists():
    print(f"File not found: {lookup_path}")
    print(f"Current directory: {Path.cwd()}")
    print(f"Looking for: {lookup_path.absolute()}")
    
    # Try alternative locations
    alternatives = [
        "SpineWidthLookup.xlsx",
        "resources/SpineWidthLookup.xls",
        "../resources/SpineWidthLookup.xlsx"
    ]
    
    for alt in alternatives:
        if Path(alt).exists():
            print(f"Found alternative: {alt}")
```

2. **Create minimal lookup file**:
```python
import pandas as pd

def create_minimal_lookup_file(output_path):
    """Create a minimal spine width lookup file"""
    
    # Standard perfect 70 data
    pages = list(range(50, 501, 50))  # 50, 100, 150, ..., 500
    spine_widths = [p * 0.0025 for p in pages]  # Approximate calculation
    
    df = pd.DataFrame({
        'Pages': pages,
        'SpineWidth': spine_widths
    })
    
    # Create Excel file with sheet
    with pd.ExcelWriter(output_path) as writer:
        df.to_excel(writer, sheet_name='Standard perfect 70', index=False)
    
    print(f"Created minimal lookup file: {output_path}")

# Usage
create_minimal_lookup_file("resources/SpineWidthLookup.xlsx")
```

### Problem: Unrealistic spine width calculations

**Symptoms**:
- Spine widths too thick or thin for page count
- Validation warnings about unusual values
- Cover generation issues

**Solutions**:

1. **Verify lookup data**:
```python
def validate_lookup_data(file_path):
    """Validate spine width lookup data"""
    try:
        sheets = pd.read_excel(file_path, sheet_name=None)
        
        for sheet_name, df in sheets.items():
            print(f"\nSheet: {sheet_name}")
            print(f"Rows: {len(df)}")
            print(f"Page range: {df['Pages'].min()} - {df['Pages'].max()}")
            print(f"Spine range: {df['SpineWidth'].min():.4f} - {df['SpineWidth'].max():.4f}")
            
            # Check for reasonable ratios
            df['ratio'] = df['SpineWidth'] / df['Pages']
            print(f"Thickness ratio range: {df['ratio'].min():.6f} - {df['ratio'].max():.6f}")
            
            # Flag unusual values
            unusual = df[
                (df['ratio'] < 0.001) | (df['ratio'] > 0.01)
            ]
            if not unusual.empty:
                print(f"Unusual ratios found: {len(unusual)} entries")
                
    except Exception as e:
        print(f"Error validating lookup data: {e}")
```

2. **Implement sanity checks**:
```python
def sanity_check_spine_width(spine_width, page_count):
    """Perform sanity checks on calculated spine width"""
    
    # Expected range based on typical paper
    min_expected = page_count * 0.0015  # Thin paper
    max_expected = page_count * 0.006   # Thick paper
    
    issues = []
    
    if spine_width < min_expected:
        issues.append(f"Spine too thin: {spine_width:.4f} < {min_expected:.4f}")
    
    if spine_width > max_expected:
        issues.append(f"Spine too thick: {spine_width:.4f} > {max_expected:.4f}")
    
    # Check for extremely thin spines
    if spine_width < 0.0625:  # Less than 1/16 inch
        issues.append("Spine may be too thin for binding")
    
    # Check for extremely thick spines
    if spine_width > 1.5:  # More than 1.5 inches
        issues.append("Spine unusually thick, verify page count")
    
    return issues
```

## Validation System Issues

### Problem: Validation system not loading

**Symptoms**:
- ImportError for ValidationSystem
- Components falling back to basic validation
- Missing validation results

**Solutions**:

1. **Check import paths**:
```python
try:
    from codexes.modules.fixes.validation_system import ValidationSystem
    print("ValidationSystem imported successfully")
except ImportError as e:
    print(f"Import error: {e}")
    
    # Check if file exists
    from pathlib import Path
    validation_file = Path("src/codexes/modules/fixes/validation_system.py")
    if validation_file.exists():
        print("Validation file exists, check Python path")
    else:
        print("Validation file missing")
```

2. **Initialize with error handling**:
```python
class ComponentWithValidation:
    def __init__(self):
        try:
            from codexes.modules.fixes.validation_system import ValidationSystem
            self.validator = ValidationSystem()
            self.has_validator = True
        except ImportError:
            logger.warning("ValidationSystem not available, using basic validation")
            self.validator = None
            self.has_validator = False
    
    def validate_input(self, data):
        if self.has_validator:
            return self.validator.validate_isbn_input(data)
        else:
            return self._basic_validation(data)
```

## General Debugging Tips

### Enable Debug Logging

```python
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

# Component-specific loggers
loggers = [
    'codexes.modules.metadata.isbn_formatter',
    'codexes.modules.distribution.isbn_barcode_generator',
    'codexes.modules.prepress.dotgrid_layout_manager',
    'codexes.modules.metadata.subtitle_validator',
    'codexes.modules.covers.spine_width_calculator',
    'codexes.modules.fixes.validation_system'
]

for logger_name in loggers:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
```

### Test Individual Components

```python
def test_component_isolation():
    """Test each component in isolation"""
    
    # Test ISBN formatter
    try:
        from codexes.modules.metadata.isbn_formatter import ISBNFormatter
        formatter = ISBNFormatter()
        result = formatter.validate_isbn_format("9780134685991")
        print(f"ISBN formatter: {'OK' if result else 'FAIL'}")
    except Exception as e:
        print(f"ISBN formatter error: {e}")
    
    # Test other components similarly...
```

### Verify Configuration Loading

```python
def verify_configurations():
    """Verify all configuration files load correctly"""
    
    config_files = [
        "configs/llm_prompt_config.json",
        "configs/spine_width_config.json",
        "configs/validation_config.json",
        "configs/imprints/xynapse_traces.json"
    ]
    
    for config_file in config_files:
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f"✓ {config_file}: OK")
        except FileNotFoundError:
            print(f"✗ {config_file}: File not found")
        except json.JSONDecodeError as e:
            print(f"✗ {config_file}: JSON error - {e}")
        except Exception as e:
            print(f"✗ {config_file}: Error - {e}")
```

## Getting Help

If issues persist:

1. **Check the logs** for detailed error messages
2. **Run the test suite** to identify specific failures
3. **Verify configuration files** are properly formatted
4. **Test with minimal examples** to isolate issues
5. **Check file permissions** and paths
6. **Ensure dependencies** are installed correctly
7. **Review the main documentation** for usage examples

For persistent issues, enable debug logging and examine the detailed output to identify the root cause.