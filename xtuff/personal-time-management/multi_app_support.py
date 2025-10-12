#!/usr/bin/env python3
"""
Multi-App Type Support and Configuration
Handles different types of Streamlit applications with specific configurations
"""

import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from streamlit_app_manager import StreamlitAppManager
from logging_monitoring_system import log_app_event, LogLevel, EventType


class AppTypeManager:
    """Manages different types of Streamlit applications"""
    
    def __init__(self):
        self.app_manager = StreamlitAppManager()
        self.app_types = {
            'daily_engine': DailyEngineAppType(),
            'habit_tracker': HabitTrackerAppType(),
            'settings_ui': SettingsUIAppType(),
            'custom': CustomAppType()
        }
    
    def get_app_type(self, app_name: str) -> str:
        """Determine the type of an app based on its name and configuration"""
        app_config = self.app_manager.config['apps'].get(app_name, {})
        
        # Check if type is explicitly specified
        if 'type' in app_config:
            return app_config['type']
        
        # Infer type from app name
        app_name_lower = app_name.lower()
        
        if 'daily_engine' in app_name_lower or app_name_lower == 'daily_engine':
            return 'daily_engine'
        elif 'habit' in app_name_lower and 'track' in app_name_lower:
            return 'habit_tracker'
        elif 'settings' in app_name_lower or 'config' in app_name_lower:
            return 'settings_ui'
        else:
            return 'custom'
    
    def get_app_type_handler(self, app_name: str) -> 'BaseAppType':
        """Get the appropriate app type handler"""
        app_type = self.get_app_type(app_name)
        return self.app_types.get(app_type, self.app_types['custom'])
    
    def configure_app(self, app_name: str, app_config: Dict) -> Dict:
        """Configure an app based on its type"""
        try:
            handler = self.get_app_type_handler(app_name)
            configured_config = handler.configure_app(app_name, app_config)
            
            log_app_event(
                LogLevel.INFO,
                EventType.CONFIG_UPDATE,
                app_name,
                f"App configured as {self.get_app_type(app_name)} type",
                details={'app_type': self.get_app_type(app_name)}
            )
            
            return {
                'success': True,
                'app_type': self.get_app_type(app_name),
                'configuration': configured_config
            }
            
        except Exception as e:
            log_app_event(
                LogLevel.ERROR,
                EventType.ERROR_OCCURRED,
                app_name,
                f"Failed to configure app: {str(e)}",
                error_info={'error': str(e), 'operation': 'configure_app'}
            )
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def discover_apps(self, search_paths: List[str] = None) -> List[Dict]:
        """Discover Streamlit apps in specified paths"""
        if search_paths is None:
            search_paths = ['.', 'ui', 'habits', 'apps']
        
        discovered_apps = []
        
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
            
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if file.endswith('.py') and self._is_streamlit_app(os.path.join(root, file)):
                        app_info = self._analyze_app_file(os.path.join(root, file))
                        if app_info:
                            discovered_apps.append(app_info)
        
        return discovered_apps
    
    def _is_streamlit_app(self, file_path: str) -> bool:
        """Check if a Python file is a Streamlit app"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for Streamlit imports and usage
            streamlit_indicators = [
                'import streamlit',
                'from streamlit',
                'st.',
                'streamlit.run',
                'st.title',
                'st.write'
            ]
            
            return any(indicator in content for indicator in streamlit_indicators)
            
        except Exception:
            return False
    
    def _analyze_app_file(self, file_path: str) -> Optional[Dict]:
        """Analyze a Streamlit app file to extract information"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract basic information
            app_name = Path(file_path).stem
            app_type = self._infer_app_type_from_content(content, app_name)
            
            # Look for configuration comments or docstrings
            title = self._extract_app_title(content)
            description = self._extract_app_description(content)
            
            return {
                'name': app_name,
                'path': file_path,
                'type': app_type,
                'title': title,
                'description': description,
                'discovered': True
            }
            
        except Exception as e:
            log_app_event(
                LogLevel.WARNING,
                EventType.ERROR_OCCURRED,
                "discovery",
                f"Failed to analyze app file {file_path}: {str(e)}",
                error_info={'error': str(e), 'file_path': file_path}
            )
            return None
    
    def _infer_app_type_from_content(self, content: str, app_name: str) -> str:
        """Infer app type from file content"""
        content_lower = content.lower()
        app_name_lower = app_name.lower()
        
        # Check for specific patterns
        if 'daily_engine' in content_lower or 'daily_engine' in app_name_lower:
            return 'daily_engine'
        elif 'habit' in content_lower and ('track' in content_lower or 'habit' in app_name_lower):
            return 'habit_tracker'
        elif 'settings' in content_lower or 'config' in content_lower:
            return 'settings_ui'
        else:
            return 'custom'
    
    def _extract_app_title(self, content: str) -> Optional[str]:
        """Extract app title from content"""
        import re
        
        # Look for st.title() calls
        title_match = re.search(r'st\.title\(["\']([^"\']+)["\']', content)
        if title_match:
            return title_match.group(1)
        
        # Look for st.set_page_config title
        config_match = re.search(r'page_title=["\']([^"\']+)["\']', content)
        if config_match:
            return config_match.group(1)
        
        return None
    
    def _extract_app_description(self, content: str) -> Optional[str]:
        """Extract app description from docstring or comments"""
        import re
        
        # Look for module docstring
        docstring_match = re.search(r'"""([^"]+)"""', content)
        if docstring_match:
            return docstring_match.group(1).strip()
        
        # Look for st.markdown or st.write with description
        desc_match = re.search(r'st\.(markdown|write)\(["\']([^"\']{20,100})["\']', content)
        if desc_match:
            return desc_match.group(2)
        
        return None
    
    def auto_configure_discovered_apps(self, discovered_apps: List[Dict]) -> Dict:
        """Automatically configure discovered apps"""
        results = {}
        success_count = 0
        
        for app_info in discovered_apps:
            app_name = app_info['name']
            
            # Skip if already configured
            if app_name in self.app_manager.config['apps']:
                results[app_name] = {
                    'success': True,
                    'action': 'already_configured',
                    'message': f'App {app_name} is already configured'
                }
                continue
            
            # Create configuration based on discovered info
            app_config = {
                'name': app_info.get('title', app_name.replace('_', ' ').title()),
                'path': app_info['path'],
                'type': app_info['type'],
                'enabled': True,
                'auto_start': app_info['type'] == 'daily_engine',  # Only auto-start main app
                'restart_on_failure': True,
                'health_check_url': '/health',
                'environment': {}
            }
            
            # Configure with type-specific handler
            config_result = self.configure_app(app_name, app_config)
            
            if config_result['success']:
                # Add to app manager configuration
                self.app_manager.config['apps'][app_name] = config_result['configuration']
                
                # Save configuration
                with open(self.app_manager.config_path, 'w') as f:
                    json.dump(self.app_manager.config, f, indent=2)
                
                success_count += 1
                results[app_name] = {
                    'success': True,
                    'action': 'configured',
                    'app_type': config_result['app_type'],
                    'configuration': config_result['configuration']
                }
            else:
                results[app_name] = {
                    'success': False,
                    'action': 'configuration_failed',
                    'error': config_result['error']
                }
        
        return {
            'success': True,
            'configured_count': success_count,
            'total_discovered': len(discovered_apps),
            'results': results
        }


class BaseAppType:
    """Base class for app type handlers"""
    
    def configure_app(self, app_name: str, app_config: Dict) -> Dict:
        """Configure an app of this type"""
        return app_config
    
    def get_default_port(self) -> int:
        """Get default port for this app type"""
        return 8501
    
    def get_health_check_endpoint(self) -> str:
        """Get health check endpoint for this app type"""
        return '/health'
    
    def get_environment_variables(self) -> Dict[str, str]:
        """Get environment variables for this app type"""
        return {}
    
    def validate_configuration(self, app_config: Dict) -> List[str]:
        """Validate app configuration and return list of issues"""
        issues = []
        
        required_fields = ['name', 'path']
        for field in required_fields:
            if field not in app_config:
                issues.append(f"Missing required field: {field}")
        
        if 'path' in app_config and not os.path.exists(app_config['path']):
            issues.append(f"App file not found: {app_config['path']}")
        
        return issues


class DailyEngineAppType(BaseAppType):
    """Handler for Daily Engine app type"""
    
    def configure_app(self, app_name: str, app_config: Dict) -> Dict:
        config = app_config.copy()
        
        # Set default values for daily engine
        config.setdefault('port', 8501)  # Primary port
        config.setdefault('auto_start', True)
        config.setdefault('restart_on_failure', True)
        config.setdefault('priority', 'high')
        
        # Daily engine specific environment
        config.setdefault('environment', {})
        config['environment'].update({
            'STREAMLIT_SERVER_HEADLESS': 'true',
            'STREAMLIT_SERVER_ENABLE_CORS': 'false',
            'STREAMLIT_BROWSER_GATHER_USAGE_STATS': 'false'
        })
        
        return config
    
    def get_default_port(self) -> int:
        return 8501


class HabitTrackerAppType(BaseAppType):
    """Handler for Habit Tracker app type"""
    
    def configure_app(self, app_name: str, app_config: Dict) -> Dict:
        config = app_config.copy()
        
        # Set default values for habit tracker
        config.setdefault('port', 8502)
        config.setdefault('auto_start', False)  # Start on demand
        config.setdefault('restart_on_failure', True)
        config.setdefault('priority', 'medium')
        
        # Habit tracker specific environment
        config.setdefault('environment', {})
        config['environment'].update({
            'STREAMLIT_SERVER_HEADLESS': 'true',
            'STREAMLIT_THEME_PRIMARY_COLOR': '#2E8B57',  # Sea green for habits
            'STREAMLIT_THEME_BACKGROUND_COLOR': '#F0F8FF'  # Alice blue
        })
        
        return config
    
    def get_default_port(self) -> int:
        return 8502


class SettingsUIAppType(BaseAppType):
    """Handler for Settings UI app type"""
    
    def configure_app(self, app_name: str, app_config: Dict) -> Dict:
        config = app_config.copy()
        
        # Set default values for settings UI
        config.setdefault('port', 8503)
        config.setdefault('auto_start', False)  # Start on demand
        config.setdefault('restart_on_failure', True)
        config.setdefault('priority', 'low')
        
        # Settings UI specific environment
        config.setdefault('environment', {})
        config['environment'].update({
            'STREAMLIT_SERVER_HEADLESS': 'true',
            'STREAMLIT_THEME_PRIMARY_COLOR': '#4B0082',  # Indigo for settings
            'STREAMLIT_THEME_BACKGROUND_COLOR': '#F5F5F5'  # White smoke
        })
        
        return config
    
    def get_default_port(self) -> int:
        return 8503


class CustomAppType(BaseAppType):
    """Handler for custom app types"""
    
    def configure_app(self, app_name: str, app_config: Dict) -> Dict:
        config = app_config.copy()
        
        # Set default values for custom apps
        config.setdefault('port', self._get_next_available_port())
        config.setdefault('auto_start', False)
        config.setdefault('restart_on_failure', True)
        config.setdefault('priority', 'medium')
        
        # Basic environment for custom apps
        config.setdefault('environment', {})
        config['environment'].update({
            'STREAMLIT_SERVER_HEADLESS': 'true'
        })
        
        return config
    
    def _get_next_available_port(self) -> int:
        """Get next available port starting from 8504"""
        from streamlit_app_manager import PortManager
        
        port_manager = PortManager()
        available_ports = port_manager.get_available_ports()
        
        # Start from 8504 for custom apps
        for port in range(8504, 8511):
            if port in available_ports:
                return port
        
        # Fallback to first available port
        return available_ports[0] if available_ports else 8504


# Global instance
app_type_manager = AppTypeManager()


# Convenience functions
def get_app_type(app_name: str) -> str:
    """Get app type"""
    return app_type_manager.get_app_type(app_name)


def configure_app(app_name: str, app_config: Dict) -> Dict:
    """Configure an app"""
    return app_type_manager.configure_app(app_name, app_config)


def discover_apps(search_paths: List[str] = None) -> List[Dict]:
    """Discover Streamlit apps"""
    return app_type_manager.discover_apps(search_paths)


def auto_configure_discovered_apps(discovered_apps: List[Dict] = None) -> Dict:
    """Auto-configure discovered apps"""
    if discovered_apps is None:
        discovered_apps = discover_apps()
    return app_type_manager.auto_configure_discovered_apps(discovered_apps)


def validate_app_configuration(app_name: str) -> List[str]:
    """Validate app configuration"""
    handler = app_type_manager.get_app_type_handler(app_name)
    app_config = app_type_manager.app_manager.config['apps'].get(app_name, {})
    return handler.validate_configuration(app_config)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Multi-App Type Support Manager')
    parser.add_argument('command', choices=['discover', 'configure', 'validate', 'list-types'])
    parser.add_argument('--app-name', help='Name of the app')
    parser.add_argument('--search-paths', nargs='+', help='Paths to search for apps')
    parser.add_argument('--auto-configure', action='store_true', help='Auto-configure discovered apps')
    
    args = parser.parse_args()
    
    manager = AppTypeManager()
    
    if args.command == 'discover':
        discovered = manager.discover_apps(args.search_paths)
        print(f"Discovered {len(discovered)} Streamlit apps:")
        
        for app in discovered:
            print(f"  - {app['name']} ({app['type']}) at {app['path']}")
            if app.get('title'):
                print(f"    Title: {app['title']}")
            if app.get('description'):
                print(f"    Description: {app['description'][:100]}...")
        
        if args.auto_configure:
            result = manager.auto_configure_discovered_apps(discovered)
            print(f"\nAuto-configuration result: {result['configured_count']}/{result['total_discovered']} apps configured")
    
    elif args.command == 'configure' and args.app_name:
        app_config = manager.app_manager.config['apps'].get(args.app_name, {})
        if not app_config:
            print(f"App {args.app_name} not found in configuration")
        else:
            result = manager.configure_app(args.app_name, app_config)
            print(f"Configuration result: {result}")
    
    elif args.command == 'validate' and args.app_name:
        issues = validate_app_configuration(args.app_name)
        if issues:
            print(f"Configuration issues for {args.app_name}:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"Configuration for {args.app_name} is valid")
    
    elif args.command == 'list-types':
        print("Available app types:")
        for app_type, handler in manager.app_types.items():
            default_port = handler.get_default_port()
            print(f"  - {app_type}: Default port {default_port}")
    
    else:
        parser.print_help()