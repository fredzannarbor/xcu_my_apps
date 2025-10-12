# LSI Pricing System Fix Design

## Overview

This design addresses critical pricing regressions in the LSI CSV generation system. The current system outputs prices with currency symbols and fails to calculate territorial prices, making the CSV incompatible with Lightning Source requirements.

## Architecture

### Core Components

1. **Enhanced Pricing Strategy**: Unified pricing strategy that handles all price fields
2. **Currency Formatter**: Utility to format prices as decimal numbers without symbols
3. **Territorial Price Calculator**: Service to calculate prices for different markets
4. **Field Mapping Optimizer**: System to eliminate duplicate mapping strategies

## Components and Interfaces

### 1. Enhanced Pricing Strategy

```python
class EnhancedPricingStrategy:
    def __init__(self, exchange_rates: Dict[str, float], default_discount: int = 40):
        self.exchange_rates = exchange_rates
        self.default_discount = default_discount
    
    def map_field(self, field_name: str, metadata: Dict) -> str:
        """Map pricing fields with proper formatting and calculation"""
        
    def format_price(self, amount: float) -> str:
        """Format price as decimal without currency symbols"""
        
    def calculate_territorial_price(self, base_price: float, currency: str) -> float:
        """Calculate price for specific territory"""
```

### 2. Currency Formatter

```python
class CurrencyFormatter:
    @staticmethod
    def format_decimal_price(price_str: str) -> str:
        """Convert price string to decimal format"""
        # Remove currency symbols and format to 2 decimal places
        
    @staticmethod
    def extract_numeric_value(price_str: str) -> float:
        """Extract numeric value from price string"""
```

### 3. Territorial Price Calculator

```python
class TerritorialPriceCalculator:
    def __init__(self, exchange_rates: Dict[str, float]):
        self.exchange_rates = exchange_rates
        
    def calculate_all_territorial_prices(self, us_price: float) -> Dict[str, float]:
        """Calculate prices for all territories"""
        
    def get_exchange_rate(self, currency: str) -> float:
        """Get exchange rate with fallback defaults"""
```

## Data Models

### Price Configuration

```python
@dataclass
class PriceConfiguration:
    us_list_price: float
    wholesale_discount: int = 40
    territorial_rates: Dict[str, float] = field(default_factory=dict)
    specialty_markets: List[str] = field(default_factory=list)
```

### Pricing Result

```python
@dataclass
class PricingResult:
    us_price: str  # "19.95"
    uk_price: str  # "15.99"
    eu_price: str  # "18.50"
    ca_price: str  # "26.95"
    au_price: str  # "29.95"
    specialty_prices: Dict[str, str]  # All equal to US price
    wholesale_discounts: Dict[str, str]  # All "40"
```

## Error Handling

### Price Parsing Errors
- Invalid price formats should default to "0.00"
- Missing exchange rates should use fallback defaults
- Calculation errors should be logged and use safe defaults

### Field Mapping Errors
- Duplicate strategy registration should be prevented
- Unknown price fields should use default pricing strategy
- Missing price data should result in empty string, not error

## Testing Strategy

### Unit Tests
1. **Currency Formatter Tests**
   - Test removal of currency symbols
   - Test decimal formatting
   - Test edge cases (negative prices, zero prices)

2. **Territorial Calculator Tests**
   - Test exchange rate calculations
   - Test fallback mechanisms
   - Test all supported currencies

3. **Enhanced Pricing Strategy Tests**
   - Test all price field mappings
   - Test specialty market pricing
   - Test wholesale discount application

### Integration Tests
1. **Full Pipeline Tests**
   - Test complete CSV generation with proper pricing
   - Test field mapping optimization
   - Test performance with reduced strategy count

### Validation Tests
1. **LSI Compliance Tests**
   - Verify all prices are decimal format
   - Verify no currency symbols in output
   - Verify all required price fields are populated

## Implementation Plan

### Phase 1: Currency Formatting Fix
1. Create CurrencyFormatter utility
2. Update existing pricing strategies to use formatter
3. Test price format compliance

### Phase 2: Territorial Price Calculation
1. Implement TerritorialPriceCalculator
2. Add exchange rate management
3. Calculate EU, CA, AU prices

### Phase 3: Specialty Market Pricing
1. Implement GC and specialty market pricing
2. Ensure all specialty markets equal US price
3. Standardize wholesale discounts

### Phase 4: Field Mapping Optimization
1. Audit current field mapping strategies
2. Eliminate duplicate registrations
3. Consolidate pricing strategies

### Phase 5: Integration and Testing
1. Integrate all components
2. Run comprehensive tests
3. Validate LSI compliance

## Performance Considerations

- **Reduced Strategy Count**: Eliminate duplicate mappings to reduce from 190 to ~119 strategies
- **Cached Exchange Rates**: Use cached rates to avoid repeated API calls
- **Optimized Price Calculation**: Calculate all territorial prices in single pass
- **Memory Efficiency**: Reuse pricing strategy instances across fields

## Monitoring and Logging

- Log all price calculations for audit trail
- Monitor exchange rate usage and cache hits
- Track field mapping strategy registration counts
- Alert on pricing calculation failures