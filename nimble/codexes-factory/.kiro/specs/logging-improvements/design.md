# Design Document

## Overview

This design implements a comprehensive logging improvement system that filters LiteLLM noise, enhances prompt call visibility, improves readability, and provides detailed token usage statistics. The solution uses Python's logging framework with custom filters, formatters, and handlers.

## Architecture

### Core Components

1. **LiteLLM Filter**: Custom logging filter to suppress verbose LiteLLM messages
2. **Enhanced LLM Caller**: Modified to include prompt names and collect usage from LiteLLM responses
3. **Usage Statistics Collector**: Lightweight collector that aggregates LiteLLM usage data
4. **Logging Configuration Manager**: Centralized logging setup and configuration
5. **Statistics Reporter**: End-of-pipeline reporting component

### Component Interactions

```
Application Code
    ↓
Enhanced LLM Caller (with prompt names)
    ↓
Token Usage Tracker (collects metrics)
    ↓
Logging System (with LiteLLM filter)
    ↓
Statistics Reporter (end-of-run summary)
```

## Components and Interfaces

### 1. LiteLLM Logging Filter

**File**: `src/codexes/core/logging_filters.py`

```python
class LiteLLMFilter(logging.Filter):
    """Filter to suppress verbose LiteLLM logging messages."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out LiteLLM noise while preserving important messages."""
```

**Responsibilities**:
- Filter cost calculation messages
- Filter completion wrapper messages  
- Filter utility messages
- Allow critical LiteLLM errors through
- Provide debug mode override

### 2. Enhanced Prompt Logging

**File**: `src/codexes/core/enhanced_llm_caller.py` (modifications)

```python
def call_model_with_prompt_enhanced(
    model_name: str,
    prompt_config: Dict[str, Any],
    prompt_name: str = None,
    **kwargs
) -> Dict[str, Any]:
    """Enhanced LLM caller with prompt name logging and usage collection."""
```

**Responsibilities**:
- Log prompt names before success messages
- Pass LiteLLM response to usage collector
- Maintain consistent logging format
- Handle prompt name extraction from configs

### 3. Usage Statistics Collector

**File**: `src/codexes/core/usage_statistics_collector.py`

```python
class UsageStatisticsCollector:
    """Collects and aggregates LiteLLM usage statistics."""
    
    def record_llm_response(self, prompt_name: str, response: litellm.ModelResponse)
    def get_statistics(self) -> Dict[str, Any]
    def reset(self)
```

**Responsibilities**:
- Extract usage data from LiteLLM response objects
- Use LiteLLM's built-in cost calculation (litellm.completion_cost)
- Aggregate statistics by model and prompt
- Handle missing usage data gracefully

### 4. Logging Configuration Manager

**File**: `src/codexes/core/logging_config.py`

```python
class LoggingConfigManager:
    """Manages logging configuration and setup."""
    
    def setup_logging(self, config: Dict[str, Any])
    def apply_litellm_filter(self)
    def configure_formatters(self)
```

**Responsibilities**:
- Set up logging handlers and formatters
- Apply LiteLLM filters
- Configure different logging levels
- Handle environment-specific settings

### 5. Statistics Reporter

**File**: `src/codexes/core/statistics_reporter.py`

```python
class StatisticsReporter:
    """Reports token usage and cost statistics."""
    
    def report_pipeline_statistics(self, tracker: TokenUsageTracker)
    def format_cost_summary(self, stats: Dict[str, Any]) -> str
    def log_model_breakdown(self, stats: Dict[str, Any])
```

**Responsibilities**:
- Generate end-of-pipeline reports
- Format statistics for readability
- Log model-specific breakdowns
- Handle missing cost data

## Data Models

### Usage Statistics Record

```python
@dataclass
class UsageRecord:
    model: str
    prompt_name: str
    usage: litellm.Usage  # LiteLLM's usage object
    cost: float
    timestamp: datetime
    response_time: float
```

### Statistics Summary

```python
@dataclass
class UsageStatistics:
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float
    model_breakdown: Dict[str, ModelStats]
    prompt_breakdown: Dict[str, PromptStats]
    duration: float
```

## Error Handling

### LiteLLM Filter Errors
- **Strategy**: Log filter errors at debug level, continue execution
- **Fallback**: If filter fails, allow all messages through temporarily
- **Recovery**: Attempt to reinitialize filter on next log message

### Usage Collection Errors
- **Strategy**: Log collection failures, continue without statistics for that call
- **Fallback**: Provide partial statistics if some data is available
- **Recovery**: Continue collection for subsequent calls

### Cost Calculation Errors
- **Strategy**: Use LiteLLM's built-in error handling for cost calculation
- **Fallback**: Show token counts only if cost calculation fails
- **Recovery**: Continue with usage tracking even if cost calculation fails

## Testing Strategy

### Unit Tests
- **LiteLLM Filter**: Test message filtering with various LiteLLM log patterns
- **Token Tracker**: Test usage recording and statistics calculation
- **Statistics Reporter**: Test report formatting and output
- **Logging Config**: Test configuration application and filter setup

### Integration Tests
- **End-to-End Pipeline**: Test complete logging flow with real LLM calls
- **Multi-Prompt Scenarios**: Test statistics collection across multiple prompts
- **Error Scenarios**: Test behavior when components fail
- **Performance Tests**: Ensure logging doesn't significantly impact performance

### Test Data
- Sample LiteLLM log messages for filter testing
- Mock LLM responses with token usage data
- Various prompt configurations for testing
- Cost calculation test cases with different models

## Implementation Phases

### Phase 1: LiteLLM Filtering
1. Create LiteLLM filter class
2. Identify and catalog LiteLLM message patterns
3. Implement filter logic with debug mode override
4. Apply filter to existing logging configuration

### Phase 2: Enhanced Prompt Logging
1. Modify LLM caller to accept prompt names
2. Update prompt loading to extract/provide prompt names
3. Implement consistent logging format with prompt names
4. Update all LLM call sites to provide prompt names

### Phase 3: Usage Statistics Collection
1. Create usage statistics collector class
2. Integrate collector with LLM caller
3. Use LiteLLM's built-in cost calculation (completion_cost)
4. Add error handling for missing usage data

### Phase 4: Statistics Reporting
1. Create statistics reporter class
2. Implement end-of-pipeline reporting
3. Add model and prompt breakdowns
4. Format reports for readability

### Phase 5: Configuration and Testing
1. Create centralized logging configuration
2. Add environment-specific settings
3. Implement comprehensive test suite
4. Performance optimization and validation