# LSI Pricing System Fix Requirements

## Introduction

The LSI CSV generation system has critical pricing regressions that must be fixed to ensure proper Lightning Source compatibility. The current system generates incorrect price formats and missing calculated prices.

## Requirements

### Requirement 1: Price Format Standardization

**User Story:** As a Lightning Source user, I want all prices to be decimal numbers without currency symbols, so that the CSV can be properly processed by LSI systems.

#### Acceptance Criteria

1. WHEN generating any price field THEN the system SHALL output decimal numbers with exactly 2 decimal places
2. WHEN generating any price field THEN the system SHALL NOT include currency symbols ($, £, €, etc.)
3. WHEN generating US Suggested List Price THEN the output SHALL be format "19.95" not "$19.95"
4. WHEN generating UK Suggested List Price THEN the output SHALL be format "19.99" not "£19.99"
5. WHEN generating any territorial price THEN the output SHALL be numeric only

### Requirement 2: Calculated Territorial Pricing

**User Story:** As a publisher, I want EU, CA, and AU prices to be automatically calculated from the US base price, so that I have consistent multi-territorial pricing.

#### Acceptance Criteria

1. WHEN US Suggested List Price is provided THEN the system SHALL calculate EU Suggested List Price using current exchange rates
2. WHEN US Suggested List Price is provided THEN the system SHALL calculate CA Suggested List Price using current exchange rates
3. WHEN US Suggested List Price is provided THEN the system SHALL calculate AU Suggested List Price using current exchange rates
4. WHEN calculating territorial prices THEN the system SHALL use cached exchange rates with fallback defaults
5. WHEN territorial prices are calculated THEN they SHALL be formatted as decimal numbers without currency symbols

### Requirement 3: Market Price Consistency

**User Story:** As a Lightning Source user, I want GC and other specialty market prices to equal the US list price when not specifically set, so that pricing is consistent across all markets.

#### Acceptance Criteria

1. WHEN GC Suggested List Price is not specifically configured THEN it SHALL equal the US Suggested List Price
2. WHEN USBR1 Suggested List Price is not configured THEN it SHALL equal the US Suggested List Price
3. WHEN USDE1 Suggested List Price is not configured THEN it SHALL equal the US Suggested List Price
4. WHEN any specialty market price is not configured THEN it SHALL default to the US Suggested List Price
5. WHEN specialty market prices are set THEN they SHALL be formatted as decimal numbers without currency symbols

### Requirement 4: Wholesale Discount Consistency

**User Story:** As a publisher, I want wholesale discounts to be consistently applied across all markets, so that my distribution terms are uniform.

#### Acceptance Criteria

1. WHEN a wholesale discount is configured for US market THEN it SHALL be applied to all other markets unless specifically overridden
2. WHEN no wholesale discount is specified for a market THEN it SHALL use the default wholesale discount percentage
3. WHEN wholesale discounts are output THEN they SHALL be integer percentages without the % symbol
4. WHEN wholesale discount is 40% THEN the output SHALL be "40" not "40%"
5. WHEN wholesale discounts are calculated THEN they SHALL be consistent across all territorial markets

### Requirement 5: Price Field Mapping Optimization

**User Story:** As a system administrator, I want the field mapping system to be optimized with no duplicate or redundant strategies, so that the system is efficient and maintainable.

#### Acceptance Criteria

1. WHEN the system initializes THEN it SHALL register exactly one mapping strategy per LSI field
2. WHEN field mapping strategies are registered THEN there SHALL be no duplicate registrations
3. WHEN the system reports mapping strategies THEN the count SHALL not exceed the number of LSI template fields
4. WHEN pricing strategies are registered THEN they SHALL be consolidated into a single pricing strategy per field
5. WHEN the system processes pricing fields THEN it SHALL use optimized, non-redundant mapping logic