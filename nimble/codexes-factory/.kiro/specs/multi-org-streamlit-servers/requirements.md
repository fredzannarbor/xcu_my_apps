# Requirements Document

## Introduction

The current Codexes Factory system operates with a single Streamlit server instance. This enhancement will add support for multi-organizational and personal Streamlit server management, allowing users to access multiple independent Streamlit servers based on their role. The system will support launching and managing multiple servers through a unified interface while maintaining security and access control.

## Requirements

### Requirement 1

**User Story:** As a multi-organizational user, I want to see links to independent Streamlit servers operated by other organizations that are under my control, so that I can access different organizational instances from a single interface.

#### Acceptance Criteria

1. WHEN I have a multi-organizational role THEN the system SHALL display links to configured organizational servers in the sidebar navigation
2. WHEN I click on an organizational server link THEN the system SHALL open the server in a new tab/window
3. WHEN organizational servers are configured THEN the system SHALL validate server accessibility before displaying links
4. IF an organizational server is unavailable THEN the system SHALL display an appropriate status indicator
5. WHEN organizational servers are launched THEN they SHALL run as independent processes with their own configurations

### Requirement 2

**User Story:** As a personal role user, I want to see links to Streamlit servers that I operate personally, so that I can manage my own server instances alongside the main system.

#### Acceptance Criteria

1. WHEN I have a personal role THEN the system SHALL display links to my configured personal servers in the sidebar navigation
2. WHEN I configure personal servers THEN the system SHALL store the configuration securely associated with my user account
3. WHEN personal servers are launched THEN they SHALL run with user-specific configurations and permissions
4. IF I don't have personal servers configured THEN the system SHALL provide guidance on how to set them up
5. WHEN personal servers are managed THEN they SHALL not interfere with organizational or main system operations

### Requirement 3

**User Story:** As a system administrator, I want a unified utility to launch and manage multiple Streamlit servers, so that I can replace the current single-server startup process with a multi-server management system.

#### Acceptance Criteria

1. WHEN I run multistart_streamlit.py THEN the system SHALL launch all configured and enabled servers using the correct virtual environment for each.
2. WHEN each server is launched THEN the system SHALL check if the hard-assigned port is available and find the next available port if needed
3. WHEN production servers are running THEN they SHALL have predictable port numbers that do not conflict with others
2. WHEN servers are launched THEN each SHALL run as an independent subprocess with its own configuration
3. WHEN I specify CLI flags THEN the system SHALL allow me to control which servers are launched
4. IF a server fails to start THEN the system SHALL log the error and continue launching other servers
5. WHEN all servers are running THEN the system SHALL provide status information and management capabilities

### Requirement 4

**User Story:** As a system administrator, I want JSON configuration files to define server settings, so that I can easily manage and version control server configurations.

#### Acceptance Criteria

1. WHEN server configurations are defined THEN they SHALL be stored in structured JSON files
2. WHEN configurations are loaded THEN the system SHALL validate the JSON structure and required fields
3. WHEN configurations change THEN the system SHALL support hot-reloading without full system restart
4. IF configuration files are invalid THEN the system SHALL provide clear error messages and fallback behavior
5. WHEN configurations are managed THEN they SHALL support environment-specific overrides

### Requirement 5

**User Story:** As a user, I want to see server links organized in the sidebar navigation, so that I can easily access different server instances based on my role and permissions.

#### Acceptance Criteria

1. WHEN I access the main UI THEN the sidebar SHALL display server links organized by type (organizational, personal)
2. WHEN server links are displayed THEN they SHALL show server status, name, and description
3. WHEN I have multiple roles THEN the system SHALL display all applicable server links
4. IF servers are offline THEN the links SHALL be visually distinguished from online servers
5. WHEN the sidebar is rendered THEN it SHALL maintain performance even with many configured servers

### Requirement 6

**User Story:** As a system administrator, I want CLI flags to control server launch behavior, so that I can selectively start servers for different environments and use cases.

#### Acceptance Criteria

1. WHEN I use --list-servers flag THEN the system SHALL display all configured servers with their status
2. WHEN I use --allow-servers flag THEN the system SHALL only launch specified servers
3. WHEN I use --disallow-servers flag THEN the system SHALL launch all servers except those specified
4. IF I specify conflicting flags THEN the system SHALL report clear error messages
5. WHEN CLI flags are processed THEN the system SHALL validate server names against configuration

### Requirement 7

**User Story:** As a security-conscious administrator, I want role-based access control for server visibility, so that users only see servers appropriate for their access level.

#### Acceptance Criteria

1. WHEN user roles are evaluated THEN the system SHALL only display servers matching the user's permissions
2. WHEN server configurations are loaded THEN they SHALL include role-based access restrictions
3. WHEN unauthorized access is attempted THEN the system SHALL log the attempt and deny access
4. IF user roles change THEN the visible servers SHALL update accordingly without requiring logout
5. WHEN access control is enforced THEN it SHALL not impact system performance significantly