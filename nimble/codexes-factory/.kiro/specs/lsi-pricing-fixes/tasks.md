# LSI Pricing System Fix Implementation Tasks

## Task Overview
Fix critical pricing regressions in LSI CSV generation system to ensure Lightning Source compatibility.

## Implementation Tasks

- [x] 1. Create Currency Formatter Utility
  - Create `src/codexes/modules/distribution/currency_formatter.py`
  - Implement `format_decimal_price()` method to remove currency symbols
  - Implement `extract_numeric_value()` method to parse price strings
  - Add comprehensive unit tests for all currency symbol removal
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Create Enhanced Pricing Strategy
  - Create `src/codexes/modules/distribution/enhanced_pricing_strategy.py`
  - Implement unified pricing strategy for all price fields
  - Replace multiple pricing strategies with single optimized strategy
  - Ensure all prices output as decimal numbers without symbols
  - _Requirements: 1.1, 1.2, 5.4, 5.5_

- [ ] 3. Implement Territorial Price Calculator
  - Create `src/codexes/modules/distribution/territorial_price_calculator.py`
  - Implement automatic EU price calculation from US base price
  - Implement automatic CA price calculation from US base price
  - Implement automatic AU price calculation from US base price
  - Add exchange rate caching and fallback mechanisms
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 4. Fix Specialty Market Pricing
  - Update pricing strategy to set GC prices equal to US prices
  - Update pricing strategy to set USBR1 prices equal to US prices
  - Update pricing strategy to set USDE1 prices equal to US prices
  - Ensure all specialty market prices default to US price when not configured
  - Format all specialty market prices as decimal numbers
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 5. Standardize Wholesale Discount Formatting
  - Remove percentage symbols from wholesale discount output
  - Ensure consistent wholesale discount application across all markets
  - Set default wholesale discount to 40 for all markets
  - Format wholesale discounts as integer strings without % symbol
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 6. Optimize Field Mapping Strategy Registration
  - Audit current field mapping registrations to identify duplicates
  - Eliminate duplicate strategy registrations
  - Consolidate pricing strategies into single enhanced strategy
  - Reduce total strategy count from 190 to approximately 119
  - Add validation to prevent duplicate strategy registration
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 7. Update Price Field Mappings
  - Update US Suggested List Price mapping to use enhanced strategy
  - Update UK Suggested List Price mapping to use enhanced strategy
  - Update EU Suggested List Price mapping to use enhanced strategy
  - Update CA Suggested List Price mapping to use enhanced strategy
  - Update AU Suggested List Price mapping to use enhanced strategy
  - Update all specialty market price mappings
  - _Requirements: 1.3, 1.4, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3_

- [ ] 8. Create Comprehensive Pricing Tests
  - Write unit tests for currency formatter
  - Write unit tests for territorial price calculator
  - Write unit tests for enhanced pricing strategy
  - Write integration tests for complete pricing pipeline
  - Write validation tests for LSI compliance
  - _Requirements: All requirements validation_

- [ ] 9. Update Configuration System
  - Update default pricing configuration with proper decimal formats
  - Remove currency symbols from configuration files
  - Add exchange rate configuration for territorial pricing
  - Update wholesale discount configuration format
  - _Requirements: 1.1, 1.2, 2.4, 4.2_

- [ ] 10. Integration and Testing
  - Integrate all pricing components into LSI generator
  - Run comprehensive pipeline tests with pricing fixes
  - Validate CSV output format compliance
  - Verify field coverage improvement
  - Test performance with optimized strategy count
  - _Requirements: All requirements integration_

## Success Criteria

### Pricing Format Compliance
- All price fields output as decimal numbers (e.g., "19.95")
- No currency symbols in any price field
- All wholesale discounts as integers (e.g., "40")

### Territorial Price Coverage
- EU, CA, AU prices automatically calculated and populated
- All specialty market prices equal to US price when not configured
- Consistent wholesale discounts across all markets

### System Optimization
- Field mapping strategy count reduced to ~119 (one per field)
- No duplicate strategy registrations
- Improved field coverage percentage

### LSI Compliance
- CSV passes Lightning Source validation
- All required price fields properly formatted
- No pricing-related validation errors