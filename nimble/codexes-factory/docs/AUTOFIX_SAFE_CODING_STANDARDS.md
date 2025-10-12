# Autofix-Safe Coding Standards for UI Robustness

This document outlines coding standards and patterns that remain stable through autofix operations while maintaining UI robustness against None values and data structure issues.

## Core Principles

### 1. Use Standard Python Idioms
Autofix preserves standard Python patterns. Always use built-in functions and common idioms:

```python
# ✅ GOOD - Autofix preserves this
value = getattr(obj, 'attribute', default_value)
result = (dictionary or {}).get('key', default_value)
items = collection or []

# ❌ AVOID - Custom patterns that autofix might modify
value = safe_attribute_access(obj, 'attribute', default_value)
result = custom_dict_get(dictionary, 'key', default_value)
```

### 2. Clear, Descriptive Comments
Use comments that explain WHY safety patterns are needed, not just WHAT they do:

```python
# ✅ GOOD - Explains purpose, autofix won't remove
# Safe access pattern: handles None objects from session state
value = getattr(obj, 'attribute', default_value)

# Safe iteration: prevents TypeError when collection is None
for item in (collection or []):
    process(item)

# ❌ AVOID - Generic comments that might be removed
# Get attribute safely
value = getattr(obj, 'attribute', default_value)
```

### 3. Consistent Pattern Application
Apply the same patterns consistently throughout the codebase:

```python
# ✅ GOOD - Consistent pattern
publisher = safe_dict_get(config, 'publisher', '')
imprint = safe_dict_get(config, 'imprint', '')
tranche = safe_dict_get(config, 'tranche', '')

# ❌ AVOID - Inconsistent approaches
publisher = config.get('publisher', '') if config else ''
imprint = (config or {}).get('imprint', '')
tranche = config['tranche'] if config and 'tranche' in config else ''
```

## Autofix-Resistant Patterns

### 1. Safe Attribute Access

```python
# ✅ AUTOFIX-SAFE: Uses standard getattr()
value = getattr(obj, 'attribute', default_value)

# ✅ AUTOFIX-SAFE: Standard hasattr() check
if hasattr(obj, 'attribute') and obj.attribute is not None:
    use_value(obj.attribute)
```

### 2. Safe Dictionary Access

```python
# ✅ AUTOFIX-SAFE: Standard dict.get() with None protection
value = (dictionary or {}).get('key', default_value)

# ✅ AUTOFIX-SAFE: Standard 'in' operator with None check
if dictionary and 'key' in dictionary:
    use_value(dictionary['key'])
```

### 3. Safe Collection Operations

```python
# ✅ AUTOFIX-SAFE: Standard 'or' operator for None protection
for item in (collection or []):
    process(item)

# ✅ AUTOFIX-SAFE: Standard len() with None protection
count = len(collection or [])

# ✅ AUTOFIX-SAFE: Standard join() with None protection
result = ', '.join(collection or [])
```

### 4. Safe String Operations

```python
# ✅ AUTOFIX-SAFE: Standard string methods with None protection
text = (text or '').strip()
parts = (text or '').split(',')

# ✅ AUTOFIX-SAFE: Standard format with None handling
message = "Hello {}".format(name or 'Guest')
```

### 5. Safe Numeric Operations

```python
# ✅ AUTOFIX-SAFE: Standard max/min with None protection
maximum = max(numbers or [0])
minimum = min(numbers or [0])
total = sum(numbers or [])
```

## Session State Safety Patterns

### 1. Safe Session State Access

```python
# ✅ AUTOFIX-SAFE: Standard dict.get() pattern
config_state = st.session_state.get('config_ui_state', {})
current_value = config_state.get('current_config', {})

# ✅ AUTOFIX-SAFE: Standard 'in' operator check
if 'config_ui_state' in st.session_state:
    state = st.session_state.config_ui_state
```

### 2. Safe State Initialization

```python
# ✅ AUTOFIX-SAFE: Standard dict initialization
if 'config_ui_state' not in st.session_state:
    st.session_state.config_ui_state = {
        'selected_publisher': '',
        'selected_imprint': '',
        'current_config': {},
        'validation_results': None
    }

# ✅ AUTOFIX-SAFE: Ensure required keys exist
default_values = {
    'selected_publisher': '',
    'selected_imprint': '',
    'current_config': {}
}

for key, default in default_values.items():
    if key not in st.session_state.config_ui_state:
        st.session_state.config_ui_state[key] = default
```

### 3. Safe State Updates

```python
# ✅ AUTOFIX-SAFE: Standard dict.update() with None protection
if st.session_state.config_ui_state is not None:
    st.session_state.config_ui_state.update({
        'selected_publisher': publisher or '',
        'selected_imprint': imprint or ''
    })
```

## Streamlit Widget Safety

### 1. Safe Selectbox Options

```python
# ✅ AUTOFIX-SAFE: Standard list operations
publishers = ['']
try:
    scanned = config_loader.scan_publishers()
    publishers.extend(scanned or [])
except Exception:
    pass  # Graceful degradation with empty list

# ✅ AUTOFIX-SAFE: Safe index calculation
current_selection = config_state.get('selected_publisher', '')
index = publishers.index(current_selection) if current_selection in publishers else 0
```

### 2. Safe Widget Value Access

```python
# ✅ AUTOFIX-SAFE: Standard type conversion with None protection
text_value = str(widget_value) if widget_value is not None else ""
number_value = int(widget_value) if widget_value is not None else 0
list_value = list(widget_value) if widget_value is not None else []
```

### 3. Safe Widget Key Generation

```python
# ✅ AUTOFIX-SAFE: Standard string formatting with None protection
safe_publisher = publisher or 'none'
safe_count = len(items or [])
widget_key = f"selector_{safe_publisher}_{safe_count}"
```

## Error Handling Patterns

### 1. Graceful Degradation

```python
# ✅ AUTOFIX-SAFE: Standard try/except with specific exceptions
try:
    result = risky_operation()
    if result is None:
        result = default_value
except (TypeError, AttributeError, KeyError):
    result = default_value
    # Optional: log the issue for monitoring
```

### 2. Safe Validation

```python
# ✅ AUTOFIX-SAFE: Standard boolean checks
def is_valid_config(config):
    if not config:
        return False
    
    required_keys = ['publisher', 'imprint']
    return all(key in config and config[key] is not None for key in required_keys)
```

### 3. Safe Logging

```python
# ✅ AUTOFIX-SAFE: Standard logging with None protection
def log_none_encounter(context, attribute):
    if hasattr(st, 'logger'):
        st.logger.warning(f"None value in {context} for {attribute}")
```

## Anti-Patterns to Avoid

### 1. Complex Custom Functions
```python
# ❌ AVOID - Autofix might modify complex custom functions
def complex_safe_access(obj, path, default):
    # Complex nested logic that autofix might change
    pass
```

### 2. Decorators for Safety
```python
# ❌ AVOID - Autofix might modify or remove decorators
@safe_access
def get_value(obj, attr):
    return obj.attr
```

### 3. Metaclasses or Dynamic Attributes
```python
# ❌ AVOID - Autofix doesn't handle these well
class SafeAccess(type):
    # Complex metaclass logic
    pass
```

### 4. Lambda Functions for Safety
```python
# ❌ AVOID - Autofix might modify lambda expressions
safe_get = lambda obj, attr, default: getattr(obj, attr, default) if obj else default
```

## Testing Autofix Compatibility

### 1. Before/After Comparison
Always test that safety patterns work the same before and after autofix:

```python
# Test script to verify autofix compatibility
def test_safety_patterns():
    # Test cases for all safety patterns
    assert safe_dict_get(None, 'key', 'default') == 'default'
    assert safe_dict_get({}, 'key', 'default') == 'default'
    assert safe_dict_get({'key': 'value'}, 'key', 'default') == 'value'
```

### 2. Automated Validation
Create tests that run after autofix to ensure patterns still work:

```python
def validate_ui_robustness():
    """Run after autofix to ensure UI patterns still work."""
    # Test None value handling
    # Test iteration safety
    # Test attribute access safety
    pass
```

## Documentation Standards

### 1. Pattern Documentation
Document each safety pattern with its purpose:

```python
"""
Safe access patterns for UI robustness.

These patterns use standard Python idioms that autofix preserves:
- getattr(obj, 'attr', default) for safe attribute access
- (dict or {}).get('key', default) for safe dictionary access  
- (collection or []) for safe iteration
"""
```

### 2. Inline Comments
Use clear, purpose-driven comments:

```python
# Safe access: prevents AttributeError when obj is None
value = getattr(obj, 'attribute', default_value)

# Safe iteration: prevents TypeError when collection is None  
for item in (collection or []):
    process(item)
```

### 3. Change Documentation
Document why safety patterns are needed:

```python
"""
IMPORTANT: This module uses autofix-resistant safety patterns.

These patterns prevent None value errors that occur when:
1. Session state is not properly initialized
2. Configuration loading fails
3. User input validation returns None
4. External API calls return unexpected None values

All patterns use standard Python idioms that autofix preserves.
"""
```

## Monitoring and Maintenance

### 1. Pattern Validation
Regularly validate that safety patterns are working:

```python
def validate_safety_patterns():
    """Validate that all safety patterns are functioning correctly."""
    # Check that None values are handled gracefully
    # Verify that default values are provided
    # Ensure no crashes occur with missing data
```

### 2. Autofix Impact Assessment
After each autofix run, verify:
- All safety patterns still function
- No new None value errors introduced
- UI remains stable with missing data
- Performance impact remains minimal

### 3. Pattern Evolution
Update patterns as needed while maintaining autofix compatibility:
- Use only standard Python idioms
- Test thoroughly before deployment
- Document any changes and their rationale
- Maintain backward compatibility where possible