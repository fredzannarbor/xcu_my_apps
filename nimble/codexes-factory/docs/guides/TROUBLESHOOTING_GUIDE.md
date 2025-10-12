# Book Production Fixes Troubleshooting Guide

## Overview

This guide provides detailed troubleshooting information for the enhanced error handling system and common issues that may arise with the book production fixes.

## Enhanced Error Handling System

### Error Types and Recovery

#### Quote Verification Errors

**Error**: `Verifier model did not return a valid 'verified_quotes' list`

**Symptoms**:
- Quote verification process fails
- Pipeline stops at verification stage
- Empty or malformed verification responses

**Recovery Strategies**:
1. **Missing Field Recovery**: Adds empty verified_quotes field
2. **Invalid Format Recovery**: Uses original quotes with failed status
3. **Empty Response Recovery**: Assumes quotes are accurate
4. **Final Fallback**: Returns safe empty structure

**Manual Resolution**:
```python
# Check verifier model response format
response = verifier_response.get('content', {})
if 'verified_quotes' not in response:
    # Use enhanced error handler
    recovered = error_handler.handle_quote_verification_error(response, context)
```

#### Field Completion Errors

**Error**: `'FieldCompleter' object has no attribute 'complete_field'`

**Symptoms**:
- Field completion fails with AttributeError
- Missing method errors in LLM field completion
- Pipeline continues with incomplete metadata

**Recovery Strategies**:
1. **Alternative Method Search**: Looks for complete_field_safe, complete_field_fallback
2. **Safe Default Function**: Returns function that provides default values
3. **Timeout Recovery**: Handles timeout scenarios gracefully

**Manual Resolution**:
```python
# Add fallback methods to field completer
class EnhancedFieldCompleter:
    def complete_field_safe(self, *args, **kwargs):
        return "Safe default value"
    
    def complete_field_fallback(self, *args, **kwargs):
        return "Fallback value"
```

#### Validation Errors

**Error**: `Validation reported 0 fields checked`

**Symptoms**:
- Validation shows no fields processed
- Empty validation results
- Missing field mappings

**Diagnostic Information**:
- Check if input data was provided
- Verify field mappings are configured
- Review validation errors for blocking issues

**Manual Resolution**:
```python
# Debug validation process
validation_result = validator.validate(metadata)
if validation_result.get('fields_checked', 0) == 0:
    # Check diagnostic information
    diagnostic = error_handler._diagnose_zero_fields_validation(validation_result)
    print(f"Diagnostic: {diagnostic}")
```

## Component-Specific Issues

### Bibliography Formatter

#### Issue: Hanging Indent Not Applied

**Symptoms**:
- Bibliography entries appear without hanging indent
- Inconsistent formatting across entries

**Solution**:
```latex
% Ensure memoir class is loaded
\documentclass{memoir}

% Check hanging indent setting
\setlength{\itemindent}{-0.15in}
\setlength{\leftmargin}{0.15in}
```

**Code Check**:
```python
# Verify formatter configuration
formatter = BibliographyFormatter({'hanging_indent': '0.15in'})
result = formatter.generate_latex_bibliography(entries)
assert '0.15in' in result
```

#### Issue: Citation Style Not Applied

**Symptoms**:
- Citations don't follow Chicago/MLA style
- Inconsistent author name formatting

**Solution**:
```python
# Set citation style explicitly
formatter = BibliographyFormatter({'citation_style': 'chicago'})

# Verify entry formatting
entry = BibliographyEntry(
    author="Smith, John",  # Use "Last, First" format
    title="Book Title",
    publisher="Publisher",
    year="2023"
)
```

### ISBN Lookup Cache

#### Issue: Cache Not Persisting

**Symptoms**:
- Same ISBNs looked up repeatedly
- Cache file not created or updated

**Solution**:
```python
# Check cache file permissions
cache_file = Path("data/isbn_cache.json")
cache_file.parent.mkdir(parents=True, exist_ok=True)

# Verify cache is saving
cache = ISBNLookupCache(str(cache_file))
cache.cache_isbn_data("9780123456789", test_data)
assert cache_file.exists()
```

#### Issue: Document Processing Not Tracked

**Symptoms**:
- Documents scanned multiple times
- Processed documents list not maintained

**Solution**:
```python
# Ensure document ID is consistent
doc_id = "unique_document_identifier"
isbns = cache.scan_document_for_isbns(doc_id, content)

# Verify tracking
assert cache.is_document_processed(doc_id)
```

### Accurate Reporting System

#### Issue: Statistics Don't Match Reality

**Symptoms**:
- Report shows 0 quotes when quotes exist
- Prompt success rates incorrect
- Missing statistics in reports

**Solution**:
```python
# Ensure tracking calls are made
reporting_system.track_prompt_execution(
    prompt_name="actual_prompt_name",
    success=True,  # Use actual success status
    details={
        'execution_time': actual_time,
        'model_name': actual_model,
        'response_length': len(response)
    }
)

# Verify tracking
report = reporting_system.generate_accurate_report()
assert report['summary']['successful_prompts'] > 0
```

#### Issue: Session Statistics Empty

**Symptoms**:
- Session statistics show no data
- Current session not tracked properly

**Solution**:
```python
# Check session ID generation
session_id = reporting_system.current_session_id
print(f"Current session: {session_id}")

# Verify data is being tracked for current session
stats = reporting_system.get_session_statistics()
print(f"Session stats: {stats}")
```

### Typography Manager

#### Issue: Fonts Not Loading

**Symptoms**:
- Korean text displays incorrectly
- Adobe Caslon not applied to mnemonics

**Solution**:
```latex
% Ensure fontspec is loaded
\usepackage{fontspec}

% Check font availability
\setmainfont{Adobe Caslon Pro}
\newfontfamily\koreanfont{Apple Myungjo}
```

**Code Check**:
```python
# Verify font configuration
typography = TypographyManager({
    'fonts': {
        'adobe_caslon': 'Adobe Caslon Pro',
        'apple_myungjo': 'Apple Myungjo'
    }
})

# Test Korean formatting
result = typography.format_title_page_korean("안녕하세요")
assert "Apple Myungjo" in result
```

#### Issue: Chapter Heading Leading Not Adjusted

**Symptoms**:
- Chapter headings have too much space underneath
- Leading not reduced to 36 points

**Solution**:
```python
# Check leading adjustment
content = "\\chapter{Test Chapter}\nContent here"
adjusted = typography.adjust_chapter_heading_leading(content)
assert "36pt" in adjusted or "vspace" in adjusted
```

### Glossary Layout Manager

#### Issue: Terms Not Stacking Properly

**Symptoms**:
- Korean and English terms appear side by side
- Terms not vertically stacked in cells

**Solution**:
```python
# Verify stacking function
glossary = GlossaryLayoutManager()
stacked = glossary.stack_korean_english_terms("안녕", "hello")

# Should contain both fonts and vertical stacking
assert "Apple Myungjo" in stacked
assert "Adobe Caslon" in stacked
assert "parbox" in stacked or "\\\\" in stacked
```

#### Issue: Column Distribution Uneven

**Symptoms**:
- One column much longer than the other
- Terms not distributed evenly

**Solution**:
```python
# Check distribution algorithm
terms = [{'english': f'term{i}'} for i in range(10)]
left, right = glossary.distribute_terms_across_columns(terms)

# Should be roughly equal
assert abs(len(left) - len(right)) <= 1
```

### Publisher's Note Generator

#### Issue: Validation Failing

**Symptoms**:
- Generated notes fail validation
- Paragraphs too long or too short
- Missing required content

**Solution**:
```python
# Check paragraph lengths
generator = PublishersNoteGenerator()
note = generator.generate_publishers_note(book_data)

paragraphs = [p.strip() for p in note.split('\n\n') if p.strip()]
assert len(paragraphs) == 3
for p in paragraphs:
    assert len(p) <= 600
    assert len(p) >= 50

# Check required content
assert 'pilsa' in note.lower()
```

#### Issue: Current Events References Missing

**Symptoms**:
- Validation fails due to missing current events
- No contemporary keywords found

**Solution**:
```python
# Verify current events keywords
current_keywords = ['contemporary', 'modern', 'current', 'today', 'recent']
note_lower = note.lower()
has_current = any(keyword in note_lower for keyword in current_keywords)
assert has_current
```

### Writing Style Manager

#### Issue: Hierarchical Loading Not Working

**Symptoms**:
- Style configurations not merged properly
- Higher precedence configs not overriding lower ones

**Solution**:
```python
# Check configuration file locations
style_manager = WritingStyleManager()

# Verify file paths
base_paths = {
    'tranche': 'configs/tranches',
    'imprint': 'configs/imprints', 
    'publisher': 'configs/publishers'
}

# Test loading
style_config = style_manager.load_writing_style(
    tranche="test_tranche",
    imprint="test_imprint"
)
```

#### Issue: Configuration Validation Errors

**Symptoms**:
- Invalid configuration files
- Missing required fields

**Solution**:
```json
{
  "writing_style": {
    "text_values": ["Required field - list of strings"],
    "style_type": "Required field - string"
  }
}
```

### Quote Assembly Optimizer

#### Issue: Author Repetition Not Reduced

**Symptoms**:
- Still finding consecutive author violations
- Optimization strategies not working

**Solution**:
```python
# Check max consecutive setting
optimizer = QuoteAssemblyOptimizer(max_consecutive_author=3)

# Verify optimization
original_analysis = optimizer.check_author_distribution(quotes)
optimized_quotes = optimizer.optimize_quote_order(quotes)
optimized_analysis = optimizer.check_author_distribution(optimized_quotes)

# Should have fewer violations
assert len(optimized_analysis.consecutive_violations) <= len(original_analysis.consecutive_violations)
```

#### Issue: Thematic Coherence Lost

**Symptoms**:
- Related quotes separated too much
- Thematic flow disrupted

**Solution**:
```python
# Use thematic grouping strategy
optimizer._strategy_thematic_grouping(quotes)

# Check coherence score
analysis = optimizer.check_author_distribution(optimized_quotes)
assert analysis.thematic_coherence_score > 0.3
```

### ISBN Barcode Generator

#### Issue: Barcode Generation Fails

**Symptoms**:
- No barcode image generated
- Library import errors

**Solution**:
```bash
# Install required libraries
pip install python-barcode[images]
# or
pip install reportlab
```

```python
# Check library availability
generator = ISBNBarcodeGenerator()
assert generator.barcode_library is not None
```

#### Issue: ISBN to UPC Conversion Problems

**Symptoms**:
- Invalid UPC codes generated
- Wrong number of digits

**Solution**:
```python
# Verify ISBN format
isbn13 = "9780123456789"
normalized = generator._normalize_isbn13(isbn13)
assert normalized is not None
assert len(normalized) == 13

# Check UPC conversion
upc = generator._isbn13_to_upc(normalized)
assert upc is not None
assert len(upc) >= 10  # May be 10 or 12 digits depending on implementation
```

## Diagnostic Tools

### Error Log Analysis

```python
# Analyze error patterns
from codexes.modules.distribution.enhanced_error_handler import EnhancedErrorHandler

error_handler = EnhancedErrorHandler(logger)
stats = error_handler.get_error_statistics()

print(f"Total errors: {stats['total_errors']}")
print(f"Recovery rate: {stats['recovery_rate']:.2%}")
print(f"Error types: {stats['error_types']}")
```

### Performance Monitoring

```python
# Monitor system performance
from codexes.modules.distribution.accurate_reporting_system import AccurateReportingSystem

reporting = AccurateReportingSystem()
report = reporting.generate_accurate_report()

# Check key metrics
summary = report['summary']
print(f"Prompt success rate: {summary['prompt_success_rate']:.2%}")
print(f"Quote retrieval rate: {summary['quote_retrieval_rate']:.2%}")
```

### Configuration Validation

```python
# Validate all configurations
from codexes.modules.distribution.writing_style_manager import WritingStyleManager

style_manager = WritingStyleManager()
available_configs = style_manager.list_available_configs()

for level, configs in available_configs.items():
    for config_name in configs:
        # Validate each configuration
        validation = style_manager.validate_style_config(f"configs/{level}/{config_name}.json")
        if not validation['is_valid']:
            print(f"Invalid config: {level}/{config_name} - {validation['errors']}")
```

## Prevention Strategies

### Regular Maintenance

1. **Cache Cleanup**: Run ISBN cache cleanup weekly
2. **Error Log Review**: Monitor error logs daily
3. **Configuration Validation**: Validate configs before deployment
4. **Performance Monitoring**: Track key metrics continuously

### Testing Procedures

1. **Pre-deployment Testing**: Run full test suite before releases
2. **Integration Testing**: Test component interactions
3. **Error Scenario Testing**: Verify error handling works
4. **Performance Testing**: Test with large datasets

### Monitoring Setup

1. **Error Alerts**: Set up alerts for high error rates
2. **Performance Metrics**: Monitor success rates and processing times
3. **Cache Health**: Monitor cache hit rates and cleanup
4. **Configuration Changes**: Track configuration modifications

This troubleshooting guide should help identify and resolve common issues with the book production fixes. For additional support, consult the main documentation and test files for specific implementation details.