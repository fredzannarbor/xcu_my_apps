#!/usr/bin/env python3
"""
Streamlit App Manager
Core infrastructure for managing multiple Streamlit applications on dedicated ports
"""

import subprocess
import psutil
import json
import os
import time
import signal
from typing import Dict, List, Optional, Any
from datetime import datetime
import sqlite3


class PortManager:
    """Manages port allocation and availability for Streamlit apps"""
    
    def __init__(self, port_range=(8501, 8510)):
        self.port_range = port_range
        self.port_assignments = {}
        self._load_assignments()
    
    def _load_assignments(self):
        """Load existing port assignments from database"""
        try:
            conn = sqlite3.connect('daily_engine.db')
            cursor = conn.cursor()
            cursor.execute('SELECT app_name, port FROM streamlit_app_status WHERE status = "running"')
            assignments = cursor.fetchall()
            self.port_assignments = {app_name: port for app_name, port in assignments}
            conn.close()
        except sqlite3.Error:
            self.port_assignments = {}
    
    def is_port_in_use(self, port: int) -> bool:
        """Check if a port is currently in use"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    return True
            return False
        except (psutil.AccessDenied, PermissionError):
            # Fallback: try to bind to the port to check if it's available
            import socket
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.bind(('localhost', port))
                    return False  # Port is available
            except OSError:
                return True  # Port is in use
    
    def get_available_ports(self) -> List[int]:
        """Get list of available ports in the range"""
        available = []
        for port in range(self.port_range[0], self.port_range[1] + 1):
            if not self.is_port_in_use(port):
                available.append(port)
        return available
    
    def assign_port(self, app_name: str) -> int:
        """Assign an available port to an app"""
        if app_name in self.port_assignments:
            port = self.port_assignments[app_name]
            if not self.is_port_in_use(port):
                return port
        
        available_ports = self.get_available_ports()
        if not available_ports:
            raise RuntimeError("No available ports in range")
        
        port = available_ports[0]
        self.port_assignments[app_name] = port
        return port
    
    def release_port(self, app_name: str) -> None:
        """Release a port assignment"""
        if app_name in self.port_assignments:
            del self.port_assignments[app_name]
    
    def get_port_assignments(self) -> Dict[str, int]:
        """Get current port assignments"""
        return self.port_assignments.copy()


class StreamlitAppManager:
    """Main class for managing Streamlit applications"""
    
    def __init__(self, config_path="config/streamlit_apps.json"):
        self.config_path = config_path
        self.port_manager = PortManager()
        self.config = self._load_config()
        self._init_database()
    
    def _load_config(self) -> Dict:
        """Load app configuration from file"""
        default_config = {
            "apps": {
                "daily_engine": {
                    "name": "Daily Engine",
                    "path": "daily_engine.py",
                    "port": 8501,
                    "enabled": True,
                    "auto_start": True,
                    "restart_on_failure": True,
                    "health_check_url": "/health",
                    "environment": {}
                },
                "habit_tracker": {
                    "name": "Habit Tracker",
                    "path": "habits/habit_tracker.py",
                    "port": 8502,
                    "enabled": True,
                    "auto_start": False,
                    "restart_on_failure": True,
                    "health_check_url": "/health",
                    "environment": {}
                },
                "settings_ui": {
                    "name": "Settings UI",
                    "path": "ui/settings_ui.py",
                    "port": 8503,
                    "enabled": True,
                    "auto_start": False,
                    "restart_on_failure": True,
                    "health_check_url": "/health",
                    "environment": {}
                }
            },
            "daemon_config": {
                "check_interval": 30,
                "restart_delay": 5,
                "max_restart_attempts": 3,
                "log_level": "INFO"
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults
                for key in default_config:
                    if key not in loaded_config:
                        loaded_config[key] = default_config[key]
                return loaded_config
            except Exception as e:
                print(f"Error loading config: {e}, using defaults")
                return default_config
        else:
            # Create config directory and file
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def _init_database(self):
        """Initialize database table for app status tracking"""
        conn = sqlite3.connect('daily_engine.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS streamlit_app_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT NOT NULL UNIQUE,
                port INTEGER NOT NULL,
                status TEXT NOT NULL,
                pid INTEGER,
                start_time TEXT,
                last_health_check TEXT,
                restart_count INTEGER DEFAULT 0,
                error_message TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def start_app(self, app_name: str, app_path: str = None, port: int = None) -> Dict:
        """Start a Streamlit application"""
        try:
            # Get app config
            if app_name in self.config['apps']:
                app_config = self.config['apps'][app_name]
                if not app_config.get('enabled', True):
                    return {'success': False, 'error': f'App {app_name} is disabled'}
                
                app_path = app_path or app_config['path']
                port = port or self.port_manager.assign_port(app_name)
            else:
                if not app_path:
                    return {'success': False, 'error': 'app_path required for unknown apps'}
                port = port or self.port_manager.assign_port(app_name)
            
            # Check if app is already running
            status = self.get_app_status(app_name)
            if status.get('status') == 'running':
                return {'success': False, 'error': f'App {app_name} is already running on port {status.get("port")}'}
            
            # Check if path exists
            if not os.path.exists(app_path):
                return {'success': False, 'error': f'App path not found: {app_path}'}
            
            # Start the Streamlit process
            cmd = ['streamlit', 'run', app_path, '--server.port', str(port), '--server.headless', 'true']
            
            # Add environment variables if specified
            env = os.environ.copy()
            if app_name in self.config['apps']:
                env.update(self.config['apps'][app_name].get('environment', {}))
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=os.path.dirname(os.path.abspath(app_path)) if os.path.dirname(app_path) else '.'
            )
            
            # Wait a moment to check if process started successfully
            time.sleep(2)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                return {
                    'success': False, 
                    'error': f'Process failed to start: {stderr.decode()}'
                }
            
            # Update database
            self._update_app_status(app_name, port, 'running', process.pid)
            
            return {
                'success': True,
                'app_name': app_name,
                'port': port,
                'pid': process.pid,
                'url': f'http://localhost:{port}'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_app(self, app_name: str) -> Dict:
        """Stop a Streamlit application"""
        try:
            status = self.get_app_status(app_name)
            if status.get('status') != 'running':
                return {'success': False, 'error': f'App {app_name} is not running'}
            
            pid = status.get('pid')
            if pid:
                try:
                    # Try graceful shutdown first
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(2)
                    
                    # Check if process is still running
                    try:
                        os.kill(pid, 0)  # Check if process exists
                        # Force kill if still running
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass  # Process already terminated
                        
                except ProcessLookupError:
                    pass  # Process already terminated
            
            # Release port and update database
            self.port_manager.release_port(app_name)
            self._update_app_status(app_name, status.get('port'), 'stopped', None)
            
            return {
                'success': True,
                'app_name': app_name,
                'message': f'App {app_name} stopped successfully'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def restart_app(self, app_name: str) -> Dict:
        """Restart a Streamlit application"""
        try:
            # Stop the app first
            stop_result = self.stop_app(app_name)
            if not stop_result['success'] and 'not running' not in stop_result.get('error', ''):
                return stop_result
            
            # Wait a moment before restarting
            time.sleep(1)
            
            # Start the app
            if app_name in self.config['apps']:
                app_config = self.config['apps'][app_name]
                start_result = self.start_app(app_name, app_config['path'])
            else:
                return {'success': False, 'error': f'Unknown app {app_name}, cannot restart without path'}
            
            if start_result['success']:
                # Increment restart count
                self._increment_restart_count(app_name)
            
            return start_result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_app_status(self, app_name: str = None) -> Dict:
        """Get status of one or all applications"""
        try:
            conn = sqlite3.connect('daily_engine.db')
            cursor = conn.cursor()
            
            if app_name:
                cursor.execute('''
                    SELECT app_name, port, status, pid, start_time, last_health_check, restart_count, error_message
                    FROM streamlit_app_status WHERE app_name = ?
                ''', (app_name,))
                result = cursor.fetchone()
                
                if result:
                    status_data = {
                        'app_name': result[0],
                        'port': result[1],
                        'status': result[2],
                        'pid': result[3],
                        'start_time': result[4],
                        'last_health_check': result[5],
                        'restart_count': result[6],
                        'error_message': result[7]
                    }
                    
                    # Verify process is actually running
                    if status_data['status'] == 'running' and status_data['pid']:
                        try:
                            os.kill(status_data['pid'], 0)
                        except ProcessLookupError:
                            # Process not running, update status
                            self._update_app_status(app_name, status_data['port'], 'stopped', None)
                            status_data['status'] = 'stopped'
                            status_data['pid'] = None
                    
                    conn.close()
                    return status_data
                else:
                    conn.close()
                    return {'app_name': app_name, 'status': 'not_found'}
            else:
                # Get all apps
                cursor.execute('''
                    SELECT app_name, port, status, pid, start_time, last_health_check, restart_count, error_message
                    FROM streamlit_app_status
                ''')
                results = cursor.fetchall()
                
                apps_status = {}
                for result in results:
                    status_data = {
                        'port': result[1],
                        'status': result[2],
                        'pid': result[3],
                        'start_time': result[4],
                        'last_health_check': result[5],
                        'restart_count': result[6],
                        'error_message': result[7]
                    }
                    
                    # Verify process is actually running
                    if status_data['status'] == 'running' and status_data['pid']:
                        try:
                            os.kill(status_data['pid'], 0)
                        except ProcessLookupError:
                            self._update_app_status(result[0], status_data['port'], 'stopped', None)
                            status_data['status'] = 'stopped'
                            status_data['pid'] = None
                    
                    apps_status[result[0]] = status_data
                
                conn.close()
                return apps_status
                
        except Exception as e:
            return {'error': str(e)}
    
    def health_check(self, app_name: str = None) -> Dict:
        """Perform health check on applications"""
        import requests
        
        try:
            if app_name:
                status = self.get_app_status(app_name)
                if status.get('status') != 'running':
                    return {'app_name': app_name, 'healthy': False, 'reason': 'not_running'}
                
                port = status.get('port')
                try:
                    response = requests.get(f'http://localhost:{port}', timeout=5)
                    healthy = response.status_code == 200
                    self._update_health_check(app_name)
                    return {'app_name': app_name, 'healthy': healthy, 'status_code': response.status_code}
                except requests.RequestException as e:
                    return {'app_name': app_name, 'healthy': False, 'reason': str(e)}
            else:
                # Check all running apps
                all_status = self.get_app_status()
                health_results = {}
                
                for name, app_status in all_status.items():
                    if isinstance(app_status, dict) and app_status.get('status') == 'running':
                        port = app_status.get('port')
                        try:
                            response = requests.get(f'http://localhost:{port}', timeout=5)
                            healthy = response.status_code == 200
                            self._update_health_check(name)
                            health_results[name] = {'healthy': healthy, 'status_code': response.status_code}
                        except requests.RequestException as e:
                            health_results[name] = {'healthy': False, 'reason': str(e)}
                    else:
                        health_results[name] = {'healthy': False, 'reason': 'not_running'}
                
                return health_results
                
        except Exception as e:
            return {'error': str(e)}
    
    def _update_app_status(self, app_name: str, port: int, status: str, pid: int = None, error_message: str = None):
        """Update app status in database"""
        conn = sqlite3.connect('daily_engine.db')
        cursor = conn.cursor()
        
        current_time = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO streamlit_app_status 
            (app_name, port, status, pid, start_time, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (app_name, port, status, pid, current_time if status == 'running' else None, error_message))
        
        conn.commit()
        conn.close()
    
    def _update_health_check(self, app_name: str):
        """Update last health check timestamp"""
        conn = sqlite3.connect('daily_engine.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE streamlit_app_status 
            SET last_health_check = ?
            WHERE app_name = ?
        ''', (datetime.now().isoformat(), app_name))
        
        conn.commit()
        conn.close()
    
    def _increment_restart_count(self, app_name: str):
        """Increment restart count for an app"""
        conn = sqlite3.connect('daily_engine.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE streamlit_app_status 
            SET restart_count = restart_count + 1
            WHERE app_name = ?
        ''', (app_name,))
        
        conn.commit()
        conn.close()


# Convenience functions for external use
def start_app(app_name: str, app_path: str = None, port: int = None) -> Dict:
    """Start a Streamlit app"""
    manager = StreamlitAppManager()
    return manager.start_app(app_name, app_path, port)


def stop_app(app_name: str) -> Dict:
    """Stop a Streamlit app"""
    manager = StreamlitAppManager()
    return manager.stop_app(app_name)


def restart_app(app_name: str) -> Dict:
    """Restart a Streamlit app"""
    manager = StreamlitAppManager()
    return manager.restart_app(app_name)


def get_app_status(app_name: str = None) -> Dict:
    """Get app status"""
    manager = StreamlitAppManager()
    return manager.get_app_status(app_name)


def health_check(app_name: str = None) -> Dict:
    """Perform health check"""
    manager = StreamlitAppManager()
    return manager.health_check(app_name)


if __name__ == "__main__":
    # Simple test
    manager = StreamlitAppManager()
    print("Streamlit App Manager initialized")
    print("Available ports:", manager.port_manager.get_available_ports())
    print("Current status:", manager.get_app_status())