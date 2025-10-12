# Requirements Document

## Introduction

This feature will create a comprehensive Streamlit app management system that ensures all Streamlit applications are running on assigned ports (8501-8510) and properly integrated with the daily_engine system. The system will include both a script for manual management and a launchctl daemon for automatic management on macOS, providing robust monitoring, automatic restart capabilities, and seamless integration with the existing daily_engine infrastructure. The system must avoid triggering any methods that generate unwanted and costly LLM calls.

## Requirements

### Requirement 1

**User Story:** As a developer, I want a script that can start, stop, and monitor all my Streamlit apps on specific ports, so that I can easily manage multiple applications without port conflicts. 

#### Acceptance Criteria

1. WHEN the script is executed THEN the system SHALL check which ports in the range 8501-8510 are available
2. WHEN starting apps THEN the system SHALL assign each Streamlit app to a specific port from the available range
3. WHEN a port is already in use THEN the system SHALL either use the existing process or reassign to the next available port
4. WHEN stopping apps THEN the system SHALL gracefully terminate all managed Streamlit processes
5. WHEN checking status THEN the system SHALL display which apps are running on which ports with their process IDs

### Requirement 2

**User Story:** As a system administrator, I want a launchctl daemon that automatically ensures my Streamlit apps stay running, so that my applications are always available without manual intervention.

#### Acceptance Criteria

1. WHEN the daemon starts THEN the system SHALL automatically launch all configured Streamlit apps on their assigned ports
2. WHEN a Streamlit app crashes THEN the daemon SHALL automatically restart it on the same port within 30 seconds
3. WHEN the system reboots THEN the daemon SHALL automatically start and restore all Streamlit apps
4. WHEN port conflicts occur THEN the daemon SHALL resolve them by reassigning apps to available ports
5. IF a daemon configuration changes THEN the system SHALL reload and apply new settings without manual restart

### Requirement 3

**User Story:** As a daily_engine user, I want the system to automatically detect and configure Streamlit app URLs, so that the daily_engine can properly connect to all running applications.

#### Acceptance Criteria

1. WHEN Streamlit apps are started THEN the system SHALL update the daily_engine configuration with correct port mappings
2. WHEN the daily_engine starts THEN it SHALL verify connectivity to all configured Streamlit apps
3. WHEN a Streamlit app changes ports THEN the system SHALL automatically update the daily_engine configuration
4. WHEN apps are stopped THEN the system SHALL remove their URLs from the daily_engine configuration
5. IF connectivity fails THEN the system SHALL log errors and attempt to restart the affected app

### Requirement 4

**User Story:** As a developer, I want comprehensive logging and monitoring of all Streamlit app operations, so that I can troubleshoot issues and monitor system health.

#### Acceptance Criteria

1. WHEN any app management operation occurs THEN the system SHALL log the action with timestamp and details
2. WHEN apps start or stop THEN the system SHALL record the event with port, PID, and status information
3. WHEN errors occur THEN the system SHALL log detailed error messages with context
4. WHEN requested THEN the system SHALL provide health check reports for all managed apps
5. IF log files exceed size limits THEN the system SHALL rotate logs automatically

### Requirement 5

**User Story:** As a system user, I want the management system to handle different types of Streamlit applications (daily_engine, habit_tracker, settings_ui), so that all my applications are managed consistently.

#### Acceptance Criteria

1. WHEN configuring apps THEN the system SHALL support different app types with specific startup parameters
2. WHEN starting the daily_engine app THEN it SHALL be assigned to port 8501 by default
3. WHEN starting the habit_tracker app THEN it SHALL be assigned to port 8502 by default
4. WHEN starting the settings_ui app THEN it SHALL be assigned to port 8503 by default
5. IF custom apps are added THEN the system SHALL assign them to the next available port in the range

### Requirement 6

**User Story:** As a developer, I want the system to provide both command-line and programmatic interfaces, so that I can integrate app management into other scripts and workflows.

#### Acceptance Criteria

1. WHEN using command line THEN the system SHALL provide start, stop, restart, status, and health-check commands
2. WHEN called programmatically THEN the system SHALL provide Python functions for all management operations
3. WHEN requesting status THEN the system SHALL return structured data (JSON) for programmatic use
4. WHEN integrating with other systems THEN the system SHALL provide callback hooks for app state changes
5. IF errors occur THEN the system SHALL return appropriate exit codes and error messages

### Requirement 7

**User Story:** As a habit tracker user, I want to record quantitative metrics for my habits (like weight, sleep hours), so that I can track measurable progress alongside my habit streaks.

#### Acceptance Criteria

1. WHEN defining a habit THEN the system SHALL allow adding related metrics with data types (e.g., "weight: int", "sleep_hours: float")
2. WHEN logging a habit THEN the system SHALL prompt for associated metric values if configured
3. WHEN viewing habit history THEN the system SHALL display both streak data and metric trends
4. WHEN metrics are recorded THEN the system SHALL validate data types and ranges
5. IF metric data is missing THEN the system SHALL allow partial logging without breaking the habit streak

### Requirement 8

**User Story:** As a behavior tracker user, I want daily counters for positive behaviors, so that I can measure and reinforce good choices throughout the day.

#### Acceptance Criteria

1. WHEN creating a positive behavior counter THEN the system SHALL allow naming and configuring the behavior (e.g., "healthy eating choices")
2. WHEN a positive behavior occurs THEN the system SHALL provide a quick increment (+1) interface
3. WHEN viewing daily summary THEN the system SHALL display total counts for all positive behaviors
4. WHEN reviewing history THEN the system SHALL show daily, weekly, and monthly positive behavior trends
5. IF multiple positive behaviors are tracked THEN the system SHALL support bulk increment operations

### Requirement 9

**User Story:** As a self-monitoring user, I want daily counters for negative behaviors, so that I can acknowledge and track patterns I want to change.

#### Acceptance Criteria

1. WHEN creating a negative behavior counter THEN the system SHALL allow naming and configuring the behavior (e.g., "binge eating episodes")
2. WHEN a negative behavior occurs THEN the system SHALL provide a discrete self-reporting interface
3. WHEN viewing daily summary THEN the system SHALL display negative behavior counts with appropriate context
4. WHEN reviewing patterns THEN the system SHALL identify streaks and frequency of negative behaviors
5. IF negative behaviors are reported THEN the system SHALL maintain privacy and avoid judgmental language

### Requirement 10

**User Story:** As a habit system user, I want behavior counters to influence habit promotion and demotion, so that my overall behavior patterns affect my habit progression.

#### Acceptance Criteria

1. WHEN positive behavior counters exceed thresholds THEN the system SHALL contribute to habit promotion scoring
2. WHEN negative behavior counters exceed thresholds THEN the system SHALL contribute to habit demotion scoring
3. WHEN calculating habit progression THEN the system SHALL weight behavior counters alongside streak data
4. WHEN negative behavior streaks occur THEN the system SHALL create a separate tracking category for consecutive bad behavior days
5. IF behavior patterns improve THEN the system SHALL provide positive reinforcement in habit progression

### Requirement 11

**User Story:** As a data-driven user, I want visualizations of my metric and behavior trends, so that I can understand patterns and make informed decisions about my habits.

#### Acceptance Criteria

1. WHEN viewing metrics THEN the system SHALL provide line charts showing trends over time (daily, weekly, monthly)
2. WHEN viewing behavior counters THEN the system SHALL provide bar charts and trend analysis
3. WHEN comparing multiple metrics THEN the system SHALL support overlay charts and correlation views
4. WHEN analyzing patterns THEN the system SHALL highlight significant changes and trends
5. IF data spans multiple time periods THEN the system SHALL provide zoom and filter capabilities for detailed analysis