# Implementation Plan

- [x] 1. Set up core Streamlit app management infrastructure
  - Create the main StreamlitAppManager class with port management capabilities
  - Implement port allocation logic for range 8501-8510
  - Add basic app lifecycle methods (start, stop, restart, status)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Implement database schema extensions for enhanced habit tracking
  - Create habit_metrics table for quantitative data storage
  - Create behavior_counters table for positive/negative behavior tracking
  - Create streamlit_app_status table for app monitoring
  - Add database migration logic to preserve existing data
  - _Requirements: 7.1, 7.2, 8.1, 9.1_

- [x] 3. Build port management and process monitoring system
  - Implement PortManager class with availability checking
  - Add process health monitoring with PID tracking
  - Create automatic port conflict resolution
  - Implement graceful process termination
  - _Requirements: 1.1, 1.2, 1.3, 2.4_

- [x] 4. Create command-line interface for manual app management
  - Build CLI commands for start, stop, restart, status operations
  - Add JSON output support for programmatic use
  - Implement error handling with appropriate exit codes
  - Create help documentation and usage examples
  - _Requirements: 6.1, 6.2, 6.3, 6.5_

- [x] 5. Implement habit metrics management system
  - Create HabitMetricsManager class for quantitative tracking
  - Add metric definition with data type validation (int, float, string)
  - Implement metric value logging with date/time stamps
  - Create metric history retrieval functions
  - _Requirements: 7.1, 7.2, 7.4, 7.5_

- [x] 6. Build behavior counter system for positive/negative tracking
  - Implement BehaviorCounterManager class
  - Create positive behavior counter creation and increment functions
  - Add negative behavior counter with discrete reporting interface
  - Implement daily summary and trend calculation functions
  - _Requirements: 8.1, 8.2, 8.3, 9.1, 9.2, 9.3_

- [x] 7. Extend habit promotion system with behavior integration
  - Modify existing HabitPromotionSystem to include behavior counters
  - Implement behavior influence scoring for promotion/demotion
  - Add negative behavior streak tracking as separate category
  - Create weighted scoring system combining streaks and behaviors
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 8. Create visualization engine for metrics and trends
  - Implement HabitVisualizationEngine class using Streamlit charts
  - Create line charts for metric trends over time periods
  - Build bar charts for behavior counter analysis
  - Add correlation views for multiple metrics comparison
  - Implement zoom and filter capabilities for detailed analysis
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 9. Implement daily_engine configuration integration
  - Create automatic URL detection and configuration updates
  - Add connectivity verification for running apps
  - Implement dynamic port mapping updates
  - Create URL removal when apps are stopped
  - Add error logging and restart attempts for failed connections
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 10. Build comprehensive logging and monitoring system
  - Implement structured logging for all app operations
  - Add performance metrics tracking (startup time, memory usage)
  - Create error categorization and troubleshooting guides
  - Build log rotation and retention policies
  - Add health check endpoint monitoring
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 11. Create launchctl daemon configuration and management
  - Build LaunchCtlManager class for macOS daemon operations
  - Generate plist files for automatic app management
  - Implement daemon installation and startup procedures
  - Add automatic restart logic with 30-second delay
  - Create configuration reload without manual restart
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 12. Implement multi-app type support and configuration
  - Add support for daily_engine, habit_tracker, and settings_ui apps
  - Create app-specific configuration templates
  - Implement consistent management across different app types
  - Add app discovery and automatic configuration
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 13. Build enhanced habit tracker UI with metrics input
  - Extend existing habit_tracker.py with metrics input forms
  - Add behavior counter increment buttons to UI
  - Create metric value input validation and error handling
  - Implement partial logging support for missing metrics
  - _Requirements: 7.2, 7.4, 8.2, 9.2_

- [x] 14. Create comprehensive visualization dashboard
  - Build main dashboard showing all metrics and trends
  - Add interactive charts with time period selection
  - Implement behavior pattern highlighting and analysis
  - Create exportable reports and trend summaries
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 15. Integrate app management into settings UI
  - Add app management section to existing settings_ui.py
  - Create app configuration forms and status displays
  - Implement start/stop controls within the UI
  - Add daemon configuration management interface
  - _Requirements: 6.2, 6.4, 2.5_

- [ ] 16. Implement programmatic API for external integration
  - Create Python functions for all management operations
  - Add callback hooks for app state changes
  - Implement structured data return formats
  - Create integration examples and documentation
  - _Requirements: 6.2, 6.4_

- [ ] 17. Build comprehensive test suite
  - Create unit tests for all core classes and functions
  - Add integration tests for app lifecycle management
  - Implement database operation tests with rollback
  - Create mock tests for subprocess and daemon operations
  - Add performance tests for visualization generation
  - _Requirements: All requirements validation_

- [ ] 18. Create system integration and final wiring
  - Integrate all components into existing daily_engine.py
  - Add app management controls to main dashboard
  - Implement seamless switching between enhanced features
  - Create migration scripts for existing habit data
  - Add comprehensive error handling and user feedback
  - _Requirements: Integration of all components_