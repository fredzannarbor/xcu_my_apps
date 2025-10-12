# Requirements Document

## Introduction

Fix the Streamlit form error caused by using `st.button()` inside an `st.form()` in the Book Pipeline page. The error occurs because the ConfigurationUI component has a "Load Config" button inside the form, which violates Streamlit's form constraints.

## Requirements

### Requirement 1

**User Story:** As a user, I want the configuration to load automatically when I select publisher/imprint/tranche options, so that I don't need to manually click a load button.

#### Acceptance Criteria

1. WHEN I select a publisher, imprint, or tranche THEN the system SHALL automatically load and merge the configurations
2. WHEN configurations are loaded automatically THEN the system SHALL update the session state with the merged configuration
3. WHEN configuration loading fails THEN the system SHALL display an error message to the user
4. WHEN no configurations are selected THEN the system SHALL use default values

### Requirement 2

**User Story:** As a user, I want to be able to change my configuration selections if I realize I picked the wrong ones, so that I can correct my choices without errors.

#### Acceptance Criteria

1. WHEN I change any configuration selection THEN the system SHALL immediately reload the configuration
2. WHEN I change from a valid configuration to an invalid one THEN the system SHALL show validation warnings
3. WHEN I change configurations THEN the system SHALL preserve any manual parameter overrides where possible
4. WHEN configuration changes occur THEN the system SHALL provide visual feedback about the loading process

### Requirement 3

**User Story:** As a developer, I want the form to comply with Streamlit's constraints, so that the application runs without errors.

#### Acceptance Criteria

1. WHEN the form is rendered THEN it SHALL NOT contain any `st.button()` calls
2. WHEN the form is rendered THEN it SHALL only use `st.form_submit_button()` for form submission
3. WHEN the configuration selector is used THEN it SHALL work both inside and outside of forms
4. WHEN the UI components are loaded THEN they SHALL not cause Streamlit API exceptions

### Requirement 4

**User Story:** As a user, I want clear visual feedback about configuration loading status, so that I understand what's happening when I make selections.

#### Acceptance Criteria

1. WHEN configurations are being loaded THEN the system SHALL show a loading indicator
2. WHEN configuration loading completes successfully THEN the system SHALL show a success message
3. WHEN configuration inheritance is active THEN the system SHALL display the inheritance chain
4. WHEN validation occurs THEN the system SHALL show validation status in real-time