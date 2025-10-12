#!/usr/bin/env python3
"""
Process Monitor for Streamlit Apps
Advanced process monitoring with health checks and automatic recovery
"""

import psutil
import time
import threading
import signal
import os
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import sqlite3
import requests
from streamlit_app_manager import StreamlitAppManager


class ProcessMonitor:
    """Advanced process monitoring with health checks and recovery"""
    
    def __init__(self, check_interval: int = 30, max_restart_attempts: int = 3):
        self.check_interval = check_interval
        self.max_restart_attempts = max_restart_attempts
        self.monitoring = False
        self.monitor_thread = None
        self.app_manager = StreamlitAppManager()
        self.callbacks = {}
        
    def start_monitoring(self):
        """Start the monitoring thread"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print(f"Process monitoring started with {self.check_interval}s interval")
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("Process monitoring stopped")
    
    def add_callback(self, event_type: str, callback: Callable):
        """Add callback for monitoring events"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
    
    def _trigger_callback(self, event_type: str, data: Dict):
        """Trigger callbacks for an event"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Callback error: {e}")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self._check_all_apps()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"Monitor loop error: {e}")
                time.sleep(5)  # Brief pause before retrying
    
    def _check_all_apps(self):
        """Check all registered apps"""
        apps_status = self.app_manager.get_app_status()
        
        for app_name, status in apps_status.items():
            if isinstance(status, dict):
                self._check_single_app(app_name, status)
    
    def _check_single_app(self, app_name: str, status: Dict):
        """Check a single app's health"""
        try:
            if status.get('status') == 'running':
                pid = status.get('pid')
                port = status.get('port')
                
                # Check if process is still running
                if not self._is_process_running(pid):
                    print(f"Process {pid} for {app_name} is not running")
                    self._handle_app_failure(app_name, "process_not_found")
                    return
                
                # Check resource usage
                resource_info = self._get_process_resources(pid)
                if resource_info:
                    self._check_resource_limits(app_name, resource_info)
                
                # Perform health check
                health_result = self._perform_health_check(app_name, port)
                if not health_result['healthy']:
                    print(f"Health check failed for {app_name}: {health_result.get('reason', 'unknown')}")
                    self._handle_app_failure(app_name, "health_check_failed")
                else:
                    # Update last health check time
                    self.app_manager._update_health_check(app_name)
                    
        except Exception as e:
            print(f"Error checking app {app_name}: {e}")
    
    def _is_process_running(self, pid: int) -> bool:
        """Check if a process is running"""
        if not pid:
            return False
        
        try:
            process = psutil.Process(pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def _get_process_resources(self, pid: int) -> Optional[Dict]:
        """Get process resource usage"""
        try:
            process = psutil.Process(pid)
            return {
                'cpu_percent': process.cpu_percent(),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'memory_percent': process.memory_percent(),
                'num_threads': process.num_threads(),
                'create_time': process.create_time()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    
    def _check_resource_limits(self, app_name: str, resource_info: Dict):
        """Check if app is exceeding resource limits"""
        # Define reasonable limits for Streamlit apps
        cpu_limit = 80.0  # 80% CPU
        memory_limit_mb = 1024  # 1GB RAM
        
        if resource_info['cpu_percent'] > cpu_limit:
            self._trigger_callback('high_cpu', {
                'app_name': app_name,
                'cpu_percent': resource_info['cpu_percent'],
                'limit': cpu_limit
            })
        
        if resource_info['memory_mb'] > memory_limit_mb:
            self._trigger_callback('high_memory', {
                'app_name': app_name,
                'memory_mb': resource_info['memory_mb'],
                'limit': memory_limit_mb
            })
    
    def _perform_health_check(self, app_name: str, port: int) -> Dict:
        """Perform HTTP health check on app"""
        try:
            response = requests.get(
                f'http://localhost:{port}',
                timeout=10,
                headers={'User-Agent': 'StreamlitAppMonitor/1.0'}
            )
            
            healthy = response.status_code == 200
            return {
                'healthy': healthy,
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds()
            }
            
        except requests.exceptions.Timeout:
            return {'healthy': False, 'reason': 'timeout'}
        except requests.exceptions.ConnectionError:
            return {'healthy': False, 'reason': 'connection_refused'}
        except Exception as e:
            return {'healthy': False, 'reason': str(e)}
    
    def _handle_app_failure(self, app_name: str, failure_reason: str):
        """Handle app failure with restart logic"""
        try:
            # Get current restart count
            status = self.app_manager.get_app_status(app_name)
            restart_count = status.get('restart_count', 0)
            
            if restart_count >= self.max_restart_attempts:
                print(f"Max restart attempts reached for {app_name}, marking as failed")
                self._mark_app_failed(app_name, f"Max restarts exceeded: {failure_reason}")
                self._trigger_callback('app_failed', {
                    'app_name': app_name,
                    'reason': failure_reason,
                    'restart_count': restart_count
                })
                return
            
            print(f"Attempting to restart {app_name} (attempt {restart_count + 1}/{self.max_restart_attempts})")
            
            # Trigger callback before restart
            self._trigger_callback('app_restarting', {
                'app_name': app_name,
                'reason': failure_reason,
                'attempt': restart_count + 1
            })
            
            # Wait a bit before restarting
            time.sleep(5)
            
            # Attempt restart
            restart_result = self.app_manager.restart_app(app_name)
            
            if restart_result['success']:
                print(f"Successfully restarted {app_name}")
                self._trigger_callback('app_restarted', {
                    'app_name': app_name,
                    'reason': failure_reason,
                    'attempt': restart_count + 1
                })
            else:
                print(f"Failed to restart {app_name}: {restart_result.get('error')}")
                self._mark_app_failed(app_name, f"Restart failed: {restart_result.get('error')}")
                
        except Exception as e:
            print(f"Error handling failure for {app_name}: {e}")
            self._mark_app_failed(app_name, f"Handler error: {str(e)}")
    
    def _mark_app_failed(self, app_name: str, error_message: str):
        """Mark an app as failed in the database"""
        conn = sqlite3.connect('daily_engine.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE streamlit_app_status 
                SET status = 'error', error_message = ?
                WHERE app_name = ?
            ''', (error_message, app_name))
            
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error marking app as failed: {e}")
        finally:
            conn.close()
    
    def get_monitoring_stats(self) -> Dict:
        """Get monitoring statistics"""
        apps_status = self.app_manager.get_app_status()
        
        stats = {
            'total_apps': len(apps_status),
            'running_apps': 0,
            'stopped_apps': 0,
            'failed_apps': 0,
            'apps_with_high_restarts': 0,
            'monitoring_active': self.monitoring
        }
        
        for app_name, status in apps_status.items():
            if isinstance(status, dict):
                app_status = status.get('status', 'unknown')
                restart_count = status.get('restart_count', 0)
                
                if app_status == 'running':
                    stats['running_apps'] += 1
                elif app_status == 'stopped':
                    stats['stopped_apps'] += 1
                elif app_status == 'error':
                    stats['failed_apps'] += 1
                
                if restart_count > 2:
                    stats['apps_with_high_restarts'] += 1
        
        return stats
    
    def force_health_check(self, app_name: str = None) -> Dict:
        """Force immediate health check"""
        if app_name:
            status = self.app_manager.get_app_status(app_name)
            if isinstance(status, dict) and status.get('status') == 'running':
                port = status.get('port')
                return self._perform_health_check(app_name, port)
            else:
                return {'healthy': False, 'reason': 'app_not_running'}
        else:
            # Check all apps
            results = {}
            apps_status = self.app_manager.get_app_status()
            
            for name, status in apps_status.items():
                if isinstance(status, dict) and status.get('status') == 'running':
                    port = status.get('port')
                    results[name] = self._perform_health_check(name, port)
                else:
                    results[name] = {'healthy': False, 'reason': 'app_not_running'}
            
            return results


class PortConflictResolver:
    """Handles port conflicts and reassignment"""
    
    def __init__(self, app_manager: StreamlitAppManager):
        self.app_manager = app_manager
    
    def detect_conflicts(self) -> List[Dict]:
        """Detect port conflicts"""
        conflicts = []
        port_assignments = self.app_manager.port_manager.get_port_assignments()
        
        for app_name, assigned_port in port_assignments.items():
            # Check if port is actually in use by this app
            status = self.app_manager.get_app_status(app_name)
            
            if isinstance(status, dict) and status.get('status') == 'running':
                pid = status.get('pid')
                
                # Check if the process is actually using the assigned port
                if not self._is_port_used_by_process(assigned_port, pid):
                    conflicts.append({
                        'app_name': app_name,
                        'assigned_port': assigned_port,
                        'actual_port': self._find_process_port(pid),
                        'type': 'port_mismatch'
                    })
            
            # Check if port is used by another process
            if self.app_manager.port_manager.is_port_in_use(assigned_port):
                using_process = self._get_port_process(assigned_port)
                if using_process and using_process.get('pid') != status.get('pid'):
                    conflicts.append({
                        'app_name': app_name,
                        'assigned_port': assigned_port,
                        'conflicting_process': using_process,
                        'type': 'port_conflict'
                    })
        
        return conflicts
    
    def resolve_conflicts(self) -> Dict:
        """Resolve detected port conflicts"""
        conflicts = self.detect_conflicts()
        resolved = []
        failed = []
        
        for conflict in conflicts:
            try:
                if conflict['type'] == 'port_conflict':
                    # Reassign to new port
                    new_port = self.app_manager.port_manager.assign_port(conflict['app_name'])
                    restart_result = self.app_manager.restart_app(conflict['app_name'])
                    
                    if restart_result['success']:
                        resolved.append({
                            'app_name': conflict['app_name'],
                            'old_port': conflict['assigned_port'],
                            'new_port': new_port,
                            'action': 'reassigned'
                        })
                    else:
                        failed.append({
                            'app_name': conflict['app_name'],
                            'error': restart_result.get('error'),
                            'action': 'reassign_failed'
                        })
                
                elif conflict['type'] == 'port_mismatch':
                    # Update database with actual port
                    actual_port = conflict['actual_port']
                    if actual_port:
                        self.app_manager._update_app_status(
                            conflict['app_name'], 
                            actual_port, 
                            'running',
                            self.app_manager.get_app_status(conflict['app_name']).get('pid')
                        )
                        resolved.append({
                            'app_name': conflict['app_name'],
                            'old_port': conflict['assigned_port'],
                            'new_port': actual_port,
                            'action': 'updated_database'
                        })
                
            except Exception as e:
                failed.append({
                    'app_name': conflict['app_name'],
                    'error': str(e),
                    'action': 'resolution_failed'
                })
        
        return {
            'conflicts_found': len(conflicts),
            'resolved': resolved,
            'failed': failed
        }
    
    def _is_port_used_by_process(self, port: int, pid: int) -> bool:
        """Check if a specific process is using a port"""
        try:
            process = psutil.Process(pid)
            connections = process.connections()
            
            for conn in connections:
                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    return True
            return False
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def _find_process_port(self, pid: int) -> Optional[int]:
        """Find what port a process is actually using"""
        try:
            process = psutil.Process(pid)
            connections = process.connections()
            
            for conn in connections:
                if conn.status == psutil.CONN_LISTEN:
                    return conn.laddr.port
            return None
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    
    def _get_port_process(self, port: int) -> Optional[Dict]:
        """Get information about the process using a port"""
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                try:
                    process = psutil.Process(conn.pid)
                    return {
                        'pid': conn.pid,
                        'name': process.name(),
                        'cmdline': ' '.join(process.cmdline()[:3])  # First 3 args
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    return {'pid': conn.pid, 'name': 'unknown', 'cmdline': 'unknown'}
        return None


# Global monitor instance
process_monitor = ProcessMonitor()


# Convenience functions
def start_monitoring(check_interval: int = 30):
    """Start process monitoring"""
    global process_monitor
    process_monitor.check_interval = check_interval
    process_monitor.start_monitoring()


def stop_monitoring():
    """Stop process monitoring"""
    global process_monitor
    process_monitor.stop_monitoring()


def get_monitoring_stats() -> Dict:
    """Get monitoring statistics"""
    global process_monitor
    return process_monitor.get_monitoring_stats()


def force_health_check(app_name: str = None) -> Dict:
    """Force immediate health check"""
    global process_monitor
    return process_monitor.force_health_check(app_name)


def detect_port_conflicts() -> List[Dict]:
    """Detect port conflicts"""
    app_manager = StreamlitAppManager()
    resolver = PortConflictResolver(app_manager)
    return resolver.detect_conflicts()


def resolve_port_conflicts() -> Dict:
    """Resolve port conflicts"""
    app_manager = StreamlitAppManager()
    resolver = PortConflictResolver(app_manager)
    return resolver.resolve_conflicts()


if __name__ == "__main__":
    # Test the process monitor
    print("Testing Process Monitor...")
    
    # Start monitoring
    start_monitoring(check_interval=10)
    
    # Add some test callbacks
    def on_app_restart(data):
        print(f"App restarted: {data}")
    
    def on_high_cpu(data):
        print(f"High CPU usage: {data}")
    
    process_monitor.add_callback('app_restarted', on_app_restart)
    process_monitor.add_callback('high_cpu', on_high_cpu)
    
    # Get stats
    stats = get_monitoring_stats()
    print(f"Monitoring stats: {stats}")
    
    # Check for conflicts
    conflicts = detect_port_conflicts()
    print(f"Port conflicts: {conflicts}")
    
    print("Process monitor test completed")