#!/usr/bin/env python3
"""
LaunchCtl Manager for macOS
Manages launchctl daemon configuration for automatic Streamlit app management
"""

import os
import json
import subprocess
import plistlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from streamlit_app_manager import StreamlitAppManager
from logging_monitoring_system import log_app_event, LogLevel, EventType


class LaunchCtlManager:
    """Manages launchctl daemon operations for macOS"""
    
    def __init__(self):
        self.app_manager = StreamlitAppManager()
        self.daemon_dir = Path.home() / "Library" / "LaunchAgents"
        self.daemon_prefix = "com.streamlit.app"
        self.python_path = self._get_python_path()
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Ensure daemon directory exists
        self.daemon_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_python_path(self) -> str:
        """Get the current Python interpreter path"""
        try:
            result = subprocess.run(['which', 'python3'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                # Fallback to system python
                return '/usr/bin/python3'
        except Exception:
            return '/usr/bin/python3'
    
    def create_daemon_plist(self, app_config: Dict) -> str:
        """Create plist configuration for a daemon"""
        app_name = app_config['name']
        app_path = app_config['path']
        port = app_config.get('port', 8501)
        
        # Create daemon identifier
        daemon_id = f"{self.daemon_prefix}.{app_name.lower().replace(' ', '_')}"
        
        # Create the plist structure
        plist_data = {
            'Label': daemon_id,
            'ProgramArguments': [
                self.python_path,
                os.path.join(self.script_dir, 'daemon_wrapper.py'),
                '--app-name', app_name,
                '--app-path', app_path,
                '--port', str(port)
            ],
            'RunAtLoad': True,
            'KeepAlive': {
                'SuccessfulExit': False,  # Restart if exits successfully
                'Crashed': True,          # Restart if crashes
                'NetworkState': True      # Restart when network is available
            },
            'StartInterval': 30,  # Check every 30 seconds
            'StandardOutPath': os.path.join(self.script_dir, 'logs', f'{app_name}_daemon.log'),
            'StandardErrorPath': os.path.join(self.script_dir, 'logs', f'{app_name}_daemon_error.log'),
            'WorkingDirectory': self.script_dir,
            'EnvironmentVariables': {
                'PATH': os.environ.get('PATH', ''),
                'PYTHONPATH': self.script_dir
            },
            'ThrottleInterval': 5,  # Wait 5 seconds between restart attempts
            'ExitTimeOut': 30,      # Give 30 seconds for graceful shutdown
        }
        
        # Add additional configuration if specified
        if 'environment' in app_config:
            plist_data['EnvironmentVariables'].update(app_config['environment'])
        
        return daemon_id, plist_data
    
    def install_daemon(self, app_name: str) -> Dict:
        """Install daemon for an app"""
        try:
            # Get app configuration
            app_config = self.app_manager.config['apps'].get(app_name)
            if not app_config:
                return {
                    'success': False,
                    'error': f'App configuration not found: {app_name}'
                }
            
            if not app_config.get('enabled', True):
                return {
                    'success': False,
                    'error': f'App {app_name} is disabled'
                }
            
            # Create daemon plist
            daemon_id, plist_data = self.create_daemon_plist(app_config)
            plist_path = self.daemon_dir / f"{daemon_id}.plist"
            
            # Write plist file
            with open(plist_path, 'wb') as f:
                plistlib.dump(plist_data, f)
            
            # Set proper permissions
            os.chmod(plist_path, 0o644)
            
            log_app_event(
                LogLevel.INFO,
                EventType.CONFIG_UPDATE,
                app_name,
                f"Daemon plist created at {plist_path}",
                details={'daemon_id': daemon_id, 'plist_path': str(plist_path)}
            )
            
            return {
                'success': True,
                'daemon_id': daemon_id,
                'plist_path': str(plist_path),
                'message': f'Daemon installed for {app_name}'
            }
            
        except Exception as e:
            log_app_event(
                LogLevel.ERROR,
                EventType.ERROR_OCCURRED,
                app_name,
                f"Failed to install daemon: {str(e)}",
                error_info={'error': str(e), 'operation': 'install_daemon'}
            )
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def start_daemon(self, app_name: str) -> Dict:
        """Start daemon for an app"""
        try:
            daemon_id = f"{self.daemon_prefix}.{app_name.lower().replace(' ', '_')}"
            
            # Load the daemon
            result = subprocess.run(
                ['launchctl', 'load', '-w', str(self.daemon_dir / f"{daemon_id}.plist")],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                log_app_event(
                    LogLevel.INFO,
                    EventType.APP_START,
                    app_name,
                    f"Daemon started successfully",
                    details={'daemon_id': daemon_id}
                )
                
                return {
                    'success': True,
                    'daemon_id': daemon_id,
                    'message': f'Daemon started for {app_name}'
                }
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                
                log_app_event(
                    LogLevel.ERROR,
                    EventType.ERROR_OCCURRED,
                    app_name,
                    f"Failed to start daemon: {error_msg}",
                    error_info={'error': error_msg, 'operation': 'start_daemon'}
                )
                
                return {
                    'success': False,
                    'error': error_msg,
                    'daemon_id': daemon_id
                }
                
        except Exception as e:
            log_app_event(
                LogLevel.ERROR,
                EventType.ERROR_OCCURRED,
                app_name,
                f"Exception starting daemon: {str(e)}",
                error_info={'error': str(e), 'operation': 'start_daemon'}
            )
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def stop_daemon(self, app_name: str) -> Dict:
        """Stop daemon for an app"""
        try:
            daemon_id = f"{self.daemon_prefix}.{app_name.lower().replace(' ', '_')}"
            
            # Unload the daemon
            result = subprocess.run(
                ['launchctl', 'unload', '-w', str(self.daemon_dir / f"{daemon_id}.plist")],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                log_app_event(
                    LogLevel.INFO,
                    EventType.APP_STOP,
                    app_name,
                    f"Daemon stopped successfully",
                    details={'daemon_id': daemon_id}
                )
                
                return {
                    'success': True,
                    'daemon_id': daemon_id,
                    'message': f'Daemon stopped for {app_name}'
                }
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                
                # Check if daemon was not loaded (not an error)
                if 'Could not find specified service' in error_msg:
                    return {
                        'success': True,
                        'daemon_id': daemon_id,
                        'message': f'Daemon was not running for {app_name}'
                    }
                
                log_app_event(
                    LogLevel.ERROR,
                    EventType.ERROR_OCCURRED,
                    app_name,
                    f"Failed to stop daemon: {error_msg}",
                    error_info={'error': error_msg, 'operation': 'stop_daemon'}
                )
                
                return {
                    'success': False,
                    'error': error_msg,
                    'daemon_id': daemon_id
                }
                
        except Exception as e:
            log_app_event(
                LogLevel.ERROR,
                EventType.ERROR_OCCURRED,
                app_name,
                f"Exception stopping daemon: {str(e)}",
                error_info={'error': str(e), 'operation': 'stop_daemon'}
            )
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_daemon_status(self, app_name: str) -> Dict:
        """Get status of daemon for an app"""
        try:
            daemon_id = f"{self.daemon_prefix}.{app_name.lower().replace(' ', '_')}"
            
            # List loaded daemons
            result = subprocess.run(
                ['launchctl', 'list'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                
                for line in lines:
                    if daemon_id in line:
                        parts = line.split('\t')
                        if len(parts) >= 3:
                            pid = parts[0].strip()
                            exit_code = parts[1].strip()
                            label = parts[2].strip()
                            
                            status = 'running' if pid != '-' else 'stopped'
                            
                            return {
                                'daemon_id': daemon_id,
                                'status': status,
                                'pid': pid if pid != '-' else None,
                                'exit_code': exit_code if exit_code != '-' else None,
                                'label': label
                            }
                
                # Daemon not found in list
                return {
                    'daemon_id': daemon_id,
                    'status': 'not_loaded',
                    'pid': None,
                    'exit_code': None,
                    'label': daemon_id
                }
            else:
                return {
                    'daemon_id': daemon_id,
                    'status': 'error',
                    'error': result.stderr.strip()
                }
                
        except Exception as e:
            return {
                'daemon_id': daemon_id,
                'status': 'error',
                'error': str(e)
            }
    
    def uninstall_daemon(self, app_name: str) -> Dict:
        """Uninstall daemon for an app"""
        try:
            daemon_id = f"{self.daemon_prefix}.{app_name.lower().replace(' ', '_')}"
            plist_path = self.daemon_dir / f"{daemon_id}.plist"
            
            # Stop daemon first
            stop_result = self.stop_daemon(app_name)
            
            # Remove plist file
            if plist_path.exists():
                plist_path.unlink()
                
                log_app_event(
                    LogLevel.INFO,
                    EventType.CONFIG_UPDATE,
                    app_name,
                    f"Daemon plist removed",
                    details={'daemon_id': daemon_id, 'plist_path': str(plist_path)}
                )
                
                return {
                    'success': True,
                    'daemon_id': daemon_id,
                    'message': f'Daemon uninstalled for {app_name}',
                    'stop_result': stop_result
                }
            else:
                return {
                    'success': True,
                    'daemon_id': daemon_id,
                    'message': f'Daemon plist not found for {app_name}',
                    'stop_result': stop_result
                }
                
        except Exception as e:
            log_app_event(
                LogLevel.ERROR,
                EventType.ERROR_OCCURRED,
                app_name,
                f"Failed to uninstall daemon: {str(e)}",
                error_info={'error': str(e), 'operation': 'uninstall_daemon'}
            )
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_installed_daemons(self) -> List[Dict]:
        """List all installed Streamlit app daemons"""
        daemons = []
        
        try:
            # Find all plist files with our prefix
            for plist_file in self.daemon_dir.glob(f"{self.daemon_prefix}.*.plist"):
                daemon_id = plist_file.stem
                app_name = daemon_id.replace(f"{self.daemon_prefix}.", "").replace("_", " ").title()
                
                # Get status
                status_info = self.get_daemon_status(app_name)
                
                daemons.append({
                    'app_name': app_name,
                    'daemon_id': daemon_id,
                    'plist_path': str(plist_file),
                    'status': status_info.get('status', 'unknown'),
                    'pid': status_info.get('pid'),
                    'exit_code': status_info.get('exit_code')
                })
                
        except Exception as e:
            log_app_event(
                LogLevel.ERROR,
                EventType.ERROR_OCCURRED,
                "system",
                f"Failed to list daemons: {str(e)}",
                error_info={'error': str(e), 'operation': 'list_daemons'}
            )
        
        return daemons
    
    def reload_daemon_config(self, app_name: str) -> Dict:
        """Reload daemon configuration without manual restart"""
        try:
            # Stop daemon
            stop_result = self.stop_daemon(app_name)
            
            # Reinstall with updated config
            install_result = self.install_daemon(app_name)
            
            if install_result['success']:
                # Start daemon
                start_result = self.start_daemon(app_name)
                
                return {
                    'success': start_result['success'],
                    'message': f'Daemon configuration reloaded for {app_name}',
                    'stop_result': stop_result,
                    'install_result': install_result,
                    'start_result': start_result
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to reinstall daemon: {install_result.get("error")}',
                    'stop_result': stop_result,
                    'install_result': install_result
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def install_all_enabled_daemons(self) -> Dict:
        """Install daemons for all enabled apps"""
        results = {}
        success_count = 0
        
        for app_name, app_config in self.app_manager.config['apps'].items():
            if app_config.get('enabled', True) and app_config.get('auto_start', False):
                result = self.install_daemon(app_name)
                results[app_name] = result
                
                if result['success']:
                    success_count += 1
        
        return {
            'success': True,
            'installed_count': success_count,
            'total_apps': len(results),
            'results': results
        }
    
    def start_all_daemons(self) -> Dict:
        """Start all installed daemons"""
        daemons = self.list_installed_daemons()
        results = {}
        success_count = 0
        
        for daemon_info in daemons:
            app_name = daemon_info['app_name']
            result = self.start_daemon(app_name)
            results[app_name] = result
            
            if result['success']:
                success_count += 1
        
        return {
            'success': True,
            'started_count': success_count,
            'total_daemons': len(daemons),
            'results': results
        }
    
    def stop_all_daemons(self) -> Dict:
        """Stop all running daemons"""
        daemons = self.list_installed_daemons()
        results = {}
        success_count = 0
        
        for daemon_info in daemons:
            if daemon_info['status'] == 'running':
                app_name = daemon_info['app_name']
                result = self.stop_daemon(app_name)
                results[app_name] = result
                
                if result['success']:
                    success_count += 1
        
        return {
            'success': True,
            'stopped_count': success_count,
            'total_running': len([d for d in daemons if d['status'] == 'running']),
            'results': results
        }


# Create daemon wrapper script
def create_daemon_wrapper_script():
    """Create the daemon wrapper script"""
    wrapper_script = '''#!/usr/bin/env python3
"""
Daemon Wrapper Script
Wrapper for running Streamlit apps as daemons
"""

import argparse
import sys
import os
import time
import signal
from pathlib import Path

# Add the script directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from streamlit_app_manager import StreamlitAppManager
from logging_monitoring_system import log_app_event, LogLevel, EventType
from daily_engine_integration import daily_engine_integration

class DaemonWrapper:
    def __init__(self, app_name, app_path, port):
        self.app_name = app_name
        self.app_path = app_path
        self.port = port
        self.app_manager = StreamlitAppManager()
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        log_app_event(
            LogLevel.INFO,
            EventType.APP_STOP,
            self.app_name,
            f"Received signal {signum}, shutting down daemon"
        )
        self.running = False
    
    def run(self):
        """Main daemon loop"""
        log_app_event(
            LogLevel.INFO,
            EventType.APP_START,
            self.app_name,
            f"Daemon wrapper starting for {self.app_name}"
        )
        
        while self.running:
            try:
                # Check if app is running
                status = self.app_manager.get_app_status(self.app_name)
                
                if not isinstance(status, dict) or status.get('status') != 'running':
                    # App is not running, start it
                    log_app_event(
                        LogLevel.INFO,
                        EventType.APP_START,
                        self.app_name,
                        f"Starting app on port {self.port}"
                    )
                    
                    start_result = self.app_manager.start_app(self.app_name, self.app_path, self.port)
                    
                    if start_result['success']:
                        log_app_event(
                            LogLevel.INFO,
                            EventType.APP_START,
                            self.app_name,
                            f"App started successfully",
                            details=start_result
                        )
                        
                        # Update daily engine configuration
                        daily_engine_integration.handle_app_startup(self.app_name, self.port)
                    else:
                        log_app_event(
                            LogLevel.ERROR,
                            EventType.ERROR_OCCURRED,
                            self.app_name,
                            f"Failed to start app: {start_result.get('error')}",
                            error_info={'error': start_result.get('error')}
                        )
                
                # Wait before next check
                time.sleep(30)
                
            except Exception as e:
                log_app_event(
                    LogLevel.ERROR,
                    EventType.ERROR_OCCURRED,
                    self.app_name,
                    f"Daemon wrapper error: {str(e)}",
                    error_info={'error': str(e)}
                )
                time.sleep(10)  # Wait before retrying
        
        # Cleanup on shutdown
        try:
            self.app_manager.stop_app(self.app_name)
            daily_engine_integration.handle_app_shutdown(self.app_name)
        except Exception as e:
            log_app_event(
                LogLevel.ERROR,
                EventType.ERROR_OCCURRED,
                self.app_name,
                f"Error during daemon shutdown: {str(e)}",
                error_info={'error': str(e)}
            )

def main():
    parser = argparse.ArgumentParser(description='Streamlit App Daemon Wrapper')
    parser.add_argument('--app-name', required=True, help='Name of the app')
    parser.add_argument('--app-path', required=True, help='Path to the app file')
    parser.add_argument('--port', type=int, required=True, help='Port to run the app on')
    
    args = parser.parse_args()
    
    wrapper = DaemonWrapper(args.app_name, args.app_path, args.port)
    wrapper.run()

if __name__ == "__main__":
    main()
'''
    
    wrapper_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'daemon_wrapper.py')
    with open(wrapper_path, 'w') as f:
        f.write(wrapper_script)
    
    # Make executable
    os.chmod(wrapper_path, 0o755)
    
    return wrapper_path


# Global instance
launchctl_manager = LaunchCtlManager()


# Convenience functions
def install_daemon(app_name: str) -> Dict:
    """Install daemon for an app"""
    return launchctl_manager.install_daemon(app_name)


def start_daemon(app_name: str) -> Dict:
    """Start daemon for an app"""
    return launchctl_manager.start_daemon(app_name)


def stop_daemon(app_name: str) -> Dict:
    """Stop daemon for an app"""
    return launchctl_manager.stop_daemon(app_name)


def get_daemon_status(app_name: str) -> Dict:
    """Get daemon status"""
    return launchctl_manager.get_daemon_status(app_name)


def list_daemons() -> List[Dict]:
    """List all installed daemons"""
    return launchctl_manager.list_installed_daemons()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='LaunchCtl Daemon Manager')
    parser.add_argument('command', choices=['install', 'start', 'stop', 'status', 'uninstall', 'list', 'install-all', 'start-all', 'stop-all'])
    parser.add_argument('--app-name', help='Name of the app')
    
    args = parser.parse_args()
    
    # Create daemon wrapper script
    wrapper_path = create_daemon_wrapper_script()
    print(f"Daemon wrapper created at: {wrapper_path}")
    
    manager = LaunchCtlManager()
    
    if args.command == 'install' and args.app_name:
        result = manager.install_daemon(args.app_name)
        print(f"Install result: {result}")
    
    elif args.command == 'start' and args.app_name:
        result = manager.start_daemon(args.app_name)
        print(f"Start result: {result}")
    
    elif args.command == 'stop' and args.app_name:
        result = manager.stop_daemon(args.app_name)
        print(f"Stop result: {result}")
    
    elif args.command == 'status' and args.app_name:
        result = manager.get_daemon_status(args.app_name)
        print(f"Status: {result}")
    
    elif args.command == 'uninstall' and args.app_name:
        result = manager.uninstall_daemon(args.app_name)
        print(f"Uninstall result: {result}")
    
    elif args.command == 'list':
        daemons = manager.list_installed_daemons()
        print(f"Installed daemons ({len(daemons)}):")
        for daemon in daemons:
            print(f"  - {daemon['app_name']}: {daemon['status']}")
    
    elif args.command == 'install-all':
        result = manager.install_all_enabled_daemons()
        print(f"Install all result: {result}")
    
    elif args.command == 'start-all':
        result = manager.start_all_daemons()
        print(f"Start all result: {result}")
    
    elif args.command == 'stop-all':
        result = manager.stop_all_daemons()
        print(f"Stop all result: {result}")
    
    else:
        parser.print_help()