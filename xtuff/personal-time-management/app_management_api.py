#!/usr/bin/env python3
"""
App Management API
Programmatic interface for managing Streamlit applications

This module provides a clean, documented API for managing Streamlit applications
that can be called from other Python scripts. It wraps the StreamlitAppManager
functionality with additional convenience methods and error handling.

Example Usage:
    from app_management_api import AppAPI
    
    # Initialize the API
    api = AppAPI()
    
    # Start an app
    result = api.start('daily_engine')
    if result.success:
        print(f"App started on port {result.port}")
    
    # Get status of all apps
    status = api.status()
    for app_name, app_status in status.items():
        print(f"{app_name}: {app_status.status}")
    
    # Stop an app
    api.stop('daily_engine')
"""

from typing import Dict, List, Optional, Any, NamedTuple
from dataclasses import dataclass
from streamlit_app_manager import StreamlitAppManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AppResult:
    """Result object for app operations"""
    success: bool
    app_name: str
    message: str = ""
    error: str = ""
    port: Optional[int] = None
    pid: Optional[int] = None
    url: Optional[str] = None
    
    def __bool__(self):
        """Allow using result in boolean context"""
        return self.success


@dataclass
class AppStatus:
    """Status information for an app"""
    app_name: str
    status: str  # 'running', 'stopped', 'not_found', 'unknown'
    port: Optional[int] = None
    pid: Optional[int] = None
    start_time: Optional[str] = None
    last_health_check: Optional[str] = None
    restart_count: int = 0
    error_message: Optional[str] = None
    url: Optional[str] = None
    
    @property
    def is_running(self) -> bool:
        """Check if app is currently running"""
        return self.status == 'running'
    
    @property
    def is_stopped(self) -> bool:
        """Check if app is stopped"""
        return self.status == 'stopped'
    
    @property
    def is_healthy(self) -> bool:
        """Check if app appears healthy (running with recent health check)"""
        return self.is_running and self.last_health_check is not None


@dataclass
class HealthResult:
    """Health check result for an app"""
    app_name: str
    healthy: bool
    reason: str = ""
    status_code: Optional[int] = None
    response_time: Optional[float] = None


class AppAPI:
    """
    Main API class for managing Streamlit applications
    
    This class provides a high-level interface for managing Streamlit apps
    with proper error handling, logging, and result objects.
    """
    
    def __init__(self, config_path: str = "config/streamlit_apps.json"):
        """
        Initialize the App Management API
        
        Args:
            config_path: Path to the app configuration file
        """
        self.manager = StreamlitAppManager(config_path)
        logger.info("App Management API initialized")
    
    def start(self, app_name: str, app_path: str = None, port: int = None) -> AppResult:
        """
        Start a Streamlit application
        
        Args:
            app_name: Name of the app to start
            app_path: Optional path to the app file (required for unknown apps)
            port: Optional specific port to use
            
        Returns:
            AppResult object with operation details
            
        Example:
            result = api.start('daily_engine')
            if result.success:
                print(f"Started on {result.url}")
            else:
                print(f"Failed: {result.error}")
        """
        logger.info(f"Starting app: {app_name}")
        
        try:
            result = self.manager.start_app(app_name, app_path, port)
            
            if result['success']:
                logger.info(f"Successfully started {app_name} on port {result['port']}")
                return AppResult(
                    success=True,
                    app_name=app_name,
                    message=f"App {app_name} started successfully",
                    port=result['port'],
                    pid=result['pid'],
                    url=result['url']
                )
            else:
                logger.error(f"Failed to start {app_name}: {result['error']}")
                return AppResult(
                    success=False,
                    app_name=app_name,
                    error=result['error']
                )
                
        except Exception as e:
            logger.exception(f"Exception starting {app_name}")
            error_msg = str(e)
            if "not found" in error_msg.lower() or "no such file" in error_msg.lower():
                error_msg = f"App path not found: {app_path or 'unknown path'}"
            return AppResult(
                success=False,
                app_name=app_name,
                error=f"Unexpected error: {error_msg}"
            )
    
    def stop(self, app_name: str) -> AppResult:
        """
        Stop a Streamlit application
        
        Args:
            app_name: Name of the app to stop
            
        Returns:
            AppResult object with operation details
            
        Example:
            result = api.stop('daily_engine')
            if result.success:
                print("App stopped successfully")
        """
        logger.info(f"Stopping app: {app_name}")
        
        try:
            result = self.manager.stop_app(app_name)
            
            if result['success']:
                logger.info(f"Successfully stopped {app_name}")
                return AppResult(
                    success=True,
                    app_name=app_name,
                    message=result['message']
                )
            else:
                logger.error(f"Failed to stop {app_name}: {result['error']}")
                return AppResult(
                    success=False,
                    app_name=app_name,
                    error=result['error']
                )
                
        except Exception as e:
            logger.exception(f"Exception stopping {app_name}")
            return AppResult(
                success=False,
                app_name=app_name,
                error=f"Unexpected error: {str(e)}"
            )
    
    def restart(self, app_name: str) -> AppResult:
        """
        Restart a Streamlit application
        
        Args:
            app_name: Name of the app to restart
            
        Returns:
            AppResult object with operation details
            
        Example:
            result = api.restart('daily_engine')
            if result.success:
                print(f"App restarted on {result.url}")
        """
        logger.info(f"Restarting app: {app_name}")
        
        try:
            result = self.manager.restart_app(app_name)
            
            if result['success']:
                logger.info(f"Successfully restarted {app_name}")
                return AppResult(
                    success=True,
                    app_name=app_name,
                    message=f"App {app_name} restarted successfully",
                    port=result.get('port'),
                    pid=result.get('pid'),
                    url=result.get('url')
                )
            else:
                logger.error(f"Failed to restart {app_name}: {result['error']}")
                return AppResult(
                    success=False,
                    app_name=app_name,
                    error=result['error']
                )
                
        except Exception as e:
            logger.exception(f"Exception restarting {app_name}")
            return AppResult(
                success=False,
                app_name=app_name,
                error=f"Unexpected error: {str(e)}"
            )
    
    def status(self, app_name: str = None) -> Dict[str, AppStatus]:
        """
        Get status of applications
        
        Args:
            app_name: Optional specific app name. If None, returns all apps.
            
        Returns:
            Dictionary mapping app names to AppStatus objects
            
        Example:
            # Get all app statuses
            statuses = api.status()
            for name, status in statuses.items():
                print(f"{name}: {status.status}")
            
            # Get specific app status
            status = api.status('daily_engine')
            if 'daily_engine' in status:
                app_status = status['daily_engine']
                print(f"Running: {app_status.is_running}")
        """
        try:
            result = self.manager.get_app_status(app_name)
            
            if app_name:
                # Single app status
                if 'error' in result:
                    logger.error(f"Error getting status for {app_name}: {result['error']}")
                    return {}
                
                status = AppStatus(
                    app_name=result.get('app_name', app_name),
                    status=result.get('status', 'unknown'),
                    port=result.get('port'),
                    pid=result.get('pid'),
                    start_time=result.get('start_time'),
                    last_health_check=result.get('last_health_check'),
                    restart_count=result.get('restart_count', 0),
                    error_message=result.get('error_message'),
                    url=f"http://localhost:{result['port']}" if result.get('port') else None
                )
                return {app_name: status}
            else:
                # All app statuses
                if 'error' in result:
                    logger.error(f"Error getting all app statuses: {result['error']}")
                    return {}
                
                statuses = {}
                for name, app_data in result.items():
                    if isinstance(app_data, dict):
                        statuses[name] = AppStatus(
                            app_name=name,
                            status=app_data.get('status', 'unknown'),
                            port=app_data.get('port'),
                            pid=app_data.get('pid'),
                            start_time=app_data.get('start_time'),
                            last_health_check=app_data.get('last_health_check'),
                            restart_count=app_data.get('restart_count', 0),
                            error_message=app_data.get('error_message'),
                            url=f"http://localhost:{app_data['port']}" if app_data.get('port') else None
                        )
                
                return statuses
                
        except Exception as e:
            logger.exception(f"Exception getting status for {app_name or 'all apps'}")
            return {}
    
    def health_check(self, app_name: str = None) -> Dict[str, HealthResult]:
        """
        Perform health check on applications
        
        Args:
            app_name: Optional specific app name. If None, checks all running apps.
            
        Returns:
            Dictionary mapping app names to HealthResult objects
            
        Example:
            # Check all apps
            health = api.health_check()
            for name, result in health.items():
                if result.healthy:
                    print(f"{name}: Healthy")
                else:
                    print(f"{name}: Unhealthy - {result.reason}")
        """
        try:
            result = self.manager.health_check(app_name)
            
            if 'error' in result:
                logger.error(f"Health check error: {result['error']}")
                return {}
            
            health_results = {}
            
            if app_name:
                # Single app health check
                health_results[app_name] = HealthResult(
                    app_name=app_name,
                    healthy=result.get('healthy', False),
                    reason=result.get('reason', ''),
                    status_code=result.get('status_code')
                )
            else:
                # Multiple app health check
                for name, health_data in result.items():
                    if isinstance(health_data, dict):
                        health_results[name] = HealthResult(
                            app_name=name,
                            healthy=health_data.get('healthy', False),
                            reason=health_data.get('reason', ''),
                            status_code=health_data.get('status_code')
                        )
            
            return health_results
            
        except Exception as e:
            logger.exception(f"Exception during health check for {app_name or 'all apps'}")
            return {}
    
    def list_apps(self) -> List[str]:
        """
        Get list of configured app names
        
        Returns:
            List of app names that are configured
            
        Example:
            apps = api.list_apps()
            print(f"Configured apps: {', '.join(apps)}")
        """
        try:
            return list(self.manager.config['apps'].keys())
        except Exception as e:
            logger.exception("Exception listing apps")
            return []
    
    def get_running_apps(self) -> List[str]:
        """
        Get list of currently running app names
        
        Returns:
            List of app names that are currently running
            
        Example:
            running = api.get_running_apps()
            print(f"Running apps: {', '.join(running)}")
        """
        try:
            statuses = self.status()
            return [name for name, status in statuses.items() if status.is_running]
        except Exception as e:
            logger.exception("Exception getting running apps")
            return []
    
    def get_available_ports(self) -> List[int]:
        """
        Get list of available ports in the configured range
        
        Returns:
            List of available port numbers
            
        Example:
            ports = api.get_available_ports()
            print(f"Available ports: {ports}")
        """
        try:
            return self.manager.port_manager.get_available_ports()
        except Exception as e:
            logger.exception("Exception getting available ports")
            return []
    
    def get_port_assignments(self) -> Dict[str, int]:
        """
        Get current port assignments for apps
        
        Returns:
            Dictionary mapping app names to assigned ports
            
        Example:
            assignments = api.get_port_assignments()
            for app, port in assignments.items():
                print(f"{app}: port {port}")
        """
        try:
            return self.manager.port_manager.get_port_assignments()
        except Exception as e:
            logger.exception("Exception getting port assignments")
            return {}
    
    def start_all_enabled(self) -> Dict[str, AppResult]:
        """
        Start all enabled applications
        
        Returns:
            Dictionary mapping app names to AppResult objects
            
        Example:
            results = api.start_all_enabled()
            for app_name, result in results.items():
                if result.success:
                    print(f"Started {app_name}")
                else:
                    print(f"Failed to start {app_name}: {result.error}")
        """
        results = {}
        
        try:
            for app_name, app_config in self.manager.config['apps'].items():
                if app_config.get('enabled', True):
                    logger.info(f"Starting enabled app: {app_name}")
                    results[app_name] = self.start(app_name)
                else:
                    logger.info(f"Skipping disabled app: {app_name}")
                    results[app_name] = AppResult(
                        success=False,
                        app_name=app_name,
                        error="App is disabled"
                    )
        except Exception as e:
            logger.exception("Exception starting all enabled apps")
        
        return results
    
    def stop_all(self) -> Dict[str, AppResult]:
        """
        Stop all running applications
        
        Returns:
            Dictionary mapping app names to AppResult objects
            
        Example:
            results = api.stop_all()
            for app_name, result in results.items():
                if result.success:
                    print(f"Stopped {app_name}")
        """
        results = {}
        
        try:
            running_apps = self.get_running_apps()
            for app_name in running_apps:
                logger.info(f"Stopping running app: {app_name}")
                results[app_name] = self.stop(app_name)
        except Exception as e:
            logger.exception("Exception stopping all apps")
        
        return results
    
    def get_app_config(self, app_name: str) -> Optional[Dict]:
        """
        Get configuration for a specific app
        
        Args:
            app_name: Name of the app
            
        Returns:
            App configuration dictionary or None if not found
            
        Example:
            config = api.get_app_config('daily_engine')
            if config:
                print(f"Path: {config['path']}")
                print(f"Enabled: {config['enabled']}")
        """
        try:
            return self.manager.config['apps'].get(app_name)
        except Exception as e:
            logger.exception(f"Exception getting config for {app_name}")
            return None


# Convenience functions for backward compatibility and simple usage
def start_app(app_name: str, app_path: str = None, port: int = None) -> Dict:
    """
    Start a Streamlit app (convenience function)
    
    Args:
        app_name: Name of the app to start
        app_path: Optional path to the app file
        port: Optional specific port to use
        
    Returns:
        Dictionary with operation result (legacy format)
    """
    api = AppAPI()
    result = api.start(app_name, app_path, port)
    
    return {
        'success': result.success,
        'app_name': result.app_name,
        'port': result.port,
        'pid': result.pid,
        'url': result.url,
        'error': result.error,
        'message': result.message
    }


def stop_app(app_name: str) -> Dict:
    """
    Stop a Streamlit app (convenience function)
    
    Args:
        app_name: Name of the app to stop
        
    Returns:
        Dictionary with operation result (legacy format)
    """
    api = AppAPI()
    result = api.stop(app_name)
    
    return {
        'success': result.success,
        'app_name': result.app_name,
        'message': result.message,
        'error': result.error
    }


def restart_app(app_name: str) -> Dict:
    """
    Restart a Streamlit app (convenience function)
    
    Args:
        app_name: Name of the app to restart
        
    Returns:
        Dictionary with operation result (legacy format)
    """
    api = AppAPI()
    result = api.restart(app_name)
    
    return {
        'success': result.success,
        'app_name': result.app_name,
        'port': result.port,
        'pid': result.pid,
        'url': result.url,
        'error': result.error,
        'message': result.message
    }


def get_app_status(app_name: str = None) -> Dict:
    """
    Get app status (convenience function)
    
    Args:
        app_name: Optional specific app name
        
    Returns:
        Dictionary with status information (legacy format)
    """
    api = AppAPI()
    statuses = api.status(app_name)
    
    if app_name and app_name in statuses:
        status = statuses[app_name]
        return {
            'app_name': status.app_name,
            'status': status.status,
            'port': status.port,
            'pid': status.pid,
            'start_time': status.start_time,
            'last_health_check': status.last_health_check,
            'restart_count': status.restart_count,
            'error_message': status.error_message
        }
    elif not app_name:
        # Convert to legacy format
        legacy_format = {}
        for name, status in statuses.items():
            legacy_format[name] = {
                'status': status.status,
                'port': status.port,
                'pid': status.pid,
                'start_time': status.start_time,
                'last_health_check': status.last_health_check,
                'restart_count': status.restart_count,
                'error_message': status.error_message
            }
        return legacy_format
    else:
        return {'app_name': app_name, 'status': 'not_found'}


def health_check(app_name: str = None) -> Dict:
    """
    Perform health check (convenience function)
    
    Args:
        app_name: Optional specific app name
        
    Returns:
        Dictionary with health check results (legacy format)
    """
    api = AppAPI()
    health_results = api.health_check(app_name)
    
    if app_name and app_name in health_results:
        result = health_results[app_name]
        return {
            'app_name': result.app_name,
            'healthy': result.healthy,
            'reason': result.reason,
            'status_code': result.status_code
        }
    elif not app_name:
        # Convert to legacy format
        legacy_format = {}
        for name, result in health_results.items():
            legacy_format[name] = {
                'healthy': result.healthy,
                'reason': result.reason,
                'status_code': result.status_code
            }
        return legacy_format
    else:
        return {'app_name': app_name, 'healthy': False, 'reason': 'not_found'}


if __name__ == "__main__":
    # Example usage and testing
    print("App Management API - Example Usage")
    print("=" * 50)
    
    # Initialize API
    api = AppAPI()
    
    # List configured apps
    apps = api.list_apps()
    print(f"Configured apps: {', '.join(apps)}")
    
    # Get current status
    statuses = api.status()
    print("\nCurrent Status:")
    for name, status in statuses.items():
        print(f"  {name}: {status.status}" + (f" (port {status.port})" if status.port else ""))
    
    # Get running apps
    running = api.get_running_apps()
    print(f"\nRunning apps: {', '.join(running) if running else 'None'}")
    
    # Get available ports
    ports = api.get_available_ports()
    print(f"Available ports: {ports}")