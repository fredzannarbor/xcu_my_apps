#!/usr/bin/env python3
"""
Daily Engine Integration
Handles automatic URL detection, configuration updates, and connectivity verification
"""

import json
import os
import requests
import time
from typing import Dict, List, Optional
from datetime import datetime
from streamlit_app_manager import StreamlitAppManager
from config.settings import config


class DailyEngineIntegration:
    """Manages integration between Streamlit apps and daily_engine configuration"""
    
    def __init__(self):
        self.app_manager = StreamlitAppManager()
        self.config_backup_path = 'config/daily_engine_urls_backup.json'
        self.connectivity_timeout = 10
        self.max_retry_attempts = 3
        self.retry_delay = 2
    
    def update_daily_engine_config(self) -> Dict:
        """Update daily_engine configuration with current app URLs"""
        try:
            # Get current app status
            apps_status = self.app_manager.get_app_status()
            
            # Build URL mappings for running apps
            url_mappings = {}
            connectivity_results = {}
            
            for app_name, status in apps_status.items():
                if isinstance(status, dict) and status.get('status') == 'running':
                    port = status.get('port')
                    if port:
                        url = f'http://localhost:{port}'
                        url_mappings[app_name] = url
                        
                        # Verify connectivity
                        connectivity_results[app_name] = self._verify_connectivity(url, app_name)
            
            # Update configuration
            update_result = self._update_config_with_urls(url_mappings)
            
            # Create backup of current configuration
            self._backup_current_config(url_mappings)
            
            return {
                'success': True,
                'updated_apps': len(url_mappings),
                'url_mappings': url_mappings,
                'connectivity_results': connectivity_results,
                'config_update_result': update_result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _verify_connectivity(self, url: str, app_name: str) -> Dict:
        """Verify connectivity to a Streamlit app"""
        for attempt in range(self.max_retry_attempts):
            try:
                response = requests.get(
                    url,
                    timeout=self.connectivity_timeout,
                    headers={'User-Agent': 'DailyEngineIntegration/1.0'}
                )
                
                if response.status_code == 200:
                    return {
                        'connected': True,
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'attempt': attempt + 1
                    }
                else:
                    if attempt == self.max_retry_attempts - 1:
                        return {
                            'connected': False,
                            'status_code': response.status_code,
                            'error': f'HTTP {response.status_code}',
                            'attempts': attempt + 1
                        }
                    
            except requests.exceptions.ConnectionError:
                if attempt == self.max_retry_attempts - 1:
                    return {
                        'connected': False,
                        'error': 'Connection refused',
                        'attempts': attempt + 1
                    }
                    
            except requests.exceptions.Timeout:
                if attempt == self.max_retry_attempts - 1:
                    return {
                        'connected': False,
                        'error': 'Connection timeout',
                        'attempts': attempt + 1
                    }
                    
            except Exception as e:
                if attempt == self.max_retry_attempts - 1:
                    return {
                        'connected': False,
                        'error': str(e),
                        'attempts': attempt + 1
                    }
            
            # Wait before retry
            if attempt < self.max_retry_attempts - 1:
                time.sleep(self.retry_delay)
        
        return {
            'connected': False,
            'error': 'Max retry attempts exceeded',
            'attempts': self.max_retry_attempts
        }
    
    def _update_config_with_urls(self, url_mappings: Dict[str, str]) -> Dict:
        """Update the configuration system with new URLs"""
        try:
            # Get current streamlit apps configuration
            current_streamlit_config = config.get('streamlit_apps', {})
            
            # Update with new URLs
            updated_config = current_streamlit_config.copy()
            
            for app_name, url in url_mappings.items():
                if app_name not in updated_config:
                    updated_config[app_name] = {}
                
                updated_config[app_name].update({
                    'url': url,
                    'status': 'running',
                    'last_updated': datetime.now().isoformat()
                })
            
            # Remove URLs for stopped apps
            apps_status = self.app_manager.get_app_status()
            for app_name in list(updated_config.keys()):
                if app_name in apps_status:
                    status = apps_status[app_name]
                    if isinstance(status, dict) and status.get('status') != 'running':
                        if 'url' in updated_config[app_name]:
                            del updated_config[app_name]['url']
                        updated_config[app_name]['status'] = status.get('status', 'stopped')
                        updated_config[app_name]['last_updated'] = datetime.now().isoformat()
            
            # Save updated configuration
            config.set('streamlit_apps', updated_config)
            
            return {
                'success': True,
                'updated_apps': len(url_mappings),
                'removed_urls': len([app for app, cfg in updated_config.items() if 'url' not in cfg]),
                'config_path': config.config_file
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _backup_current_config(self, url_mappings: Dict[str, str]):
        """Create backup of current configuration"""
        try:
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'url_mappings': url_mappings,
                'config_snapshot': config.get('streamlit_apps', {})
            }
            
            # Ensure backup directory exists
            os.makedirs(os.path.dirname(self.config_backup_path), exist_ok=True)
            
            with open(self.config_backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not create config backup: {e}")
    
    def verify_all_app_connectivity(self) -> Dict:
        """Verify connectivity to all configured Streamlit apps"""
        streamlit_config = config.get('streamlit_apps', {})
        results = {}
        
        for app_name, app_config in streamlit_config.items():
            if 'url' in app_config:
                url = app_config['url']
                results[app_name] = self._verify_connectivity(url, app_name)
            else:
                results[app_name] = {
                    'connected': False,
                    'error': 'No URL configured',
                    'attempts': 0
                }
        
        # Summary statistics
        connected_count = sum(1 for result in results.values() if result.get('connected', False))
        total_count = len(results)
        
        return {
            'results': results,
            'summary': {
                'total_apps': total_count,
                'connected_apps': connected_count,
                'failed_apps': total_count - connected_count,
                'success_rate': (connected_count / total_count * 100) if total_count > 0 else 0
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def handle_app_startup(self, app_name: str, port: int) -> Dict:
        """Handle configuration updates when an app starts"""
        try:
            url = f'http://localhost:{port}'
            
            # Wait a moment for app to fully start
            time.sleep(3)
            
            # Verify connectivity
            connectivity = self._verify_connectivity(url, app_name)
            
            if connectivity['connected']:
                # Update configuration
                url_mappings = {app_name: url}
                config_result = self._update_config_with_urls(url_mappings)
                
                return {
                    'success': True,
                    'app_name': app_name,
                    'url': url,
                    'connectivity': connectivity,
                    'config_updated': config_result['success']
                }
            else:
                return {
                    'success': False,
                    'app_name': app_name,
                    'url': url,
                    'error': 'Failed connectivity verification',
                    'connectivity': connectivity
                }
                
        except Exception as e:
            return {
                'success': False,
                'app_name': app_name,
                'error': str(e)
            }
    
    def handle_app_shutdown(self, app_name: str) -> Dict:
        """Handle configuration updates when an app stops"""
        try:
            # Get current config
            streamlit_config = config.get('streamlit_apps', {})
            
            if app_name in streamlit_config:
                # Remove URL and update status
                if 'url' in streamlit_config[app_name]:
                    del streamlit_config[app_name]['url']
                
                streamlit_config[app_name]['status'] = 'stopped'
                streamlit_config[app_name]['last_updated'] = datetime.now().isoformat()
                
                # Save updated configuration
                config.set('streamlit_apps', streamlit_config)
                
                return {
                    'success': True,
                    'app_name': app_name,
                    'action': 'removed_url_and_updated_status'
                }
            else:
                return {
                    'success': True,
                    'app_name': app_name,
                    'action': 'app_not_in_config'
                }
                
        except Exception as e:
            return {
                'success': False,
                'app_name': app_name,
                'error': str(e)
            }
    
    def get_app_urls(self) -> Dict[str, str]:
        """Get current app URL mappings"""
        streamlit_config = config.get('streamlit_apps', {})
        urls = {}
        
        for app_name, app_config in streamlit_config.items():
            if 'url' in app_config:
                urls[app_name] = app_config['url']
        
        return urls
    
    def restart_failed_apps(self) -> Dict:
        """Restart apps that failed connectivity checks"""
        connectivity_results = self.verify_all_app_connectivity()
        failed_apps = []
        restart_results = {}
        
        for app_name, result in connectivity_results['results'].items():
            if not result.get('connected', False):
                failed_apps.append(app_name)
        
        if not failed_apps:
            return {
                'success': True,
                'message': 'No failed apps to restart',
                'failed_apps': [],
                'restart_results': {}
            }
        
        # Attempt to restart failed apps
        for app_name in failed_apps:
            try:
                restart_result = self.app_manager.restart_app(app_name)
                restart_results[app_name] = restart_result
                
                if restart_result['success']:
                    # Update configuration for successfully restarted app
                    port = restart_result.get('port')
                    if port:
                        self.handle_app_startup(app_name, port)
                        
            except Exception as e:
                restart_results[app_name] = {
                    'success': False,
                    'error': str(e)
                }
        
        successful_restarts = [app for app, result in restart_results.items() 
                             if result.get('success', False)]
        
        return {
            'success': True,
            'failed_apps': failed_apps,
            'restart_results': restart_results,
            'successful_restarts': successful_restarts,
            'restart_count': len(successful_restarts)
        }
    
    def generate_integration_report(self) -> str:
        """Generate comprehensive integration status report"""
        # Get current status
        connectivity_results = self.verify_all_app_connectivity()
        url_mappings = self.get_app_urls()
        apps_status = self.app_manager.get_app_status()
        
        report = f"""
# 🔗 Daily Engine Integration Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Connectivity Summary
- **Total Apps**: {connectivity_results['summary']['total_apps']}
- **Connected Apps**: {connectivity_results['summary']['connected_apps']}
- **Failed Apps**: {connectivity_results['summary']['failed_apps']}
- **Success Rate**: {connectivity_results['summary']['success_rate']:.1f}%

## 🌐 Current URL Mappings
"""
        
        if url_mappings:
            for app_name, url in url_mappings.items():
                connectivity = connectivity_results['results'].get(app_name, {})
                status_emoji = "✅" if connectivity.get('connected') else "❌"
                response_time = connectivity.get('response_time', 0)
                
                report += f"- {status_emoji} **{app_name}**: {url}"
                if connectivity.get('connected'):
                    report += f" ({response_time:.2f}s)\n"
                else:
                    error = connectivity.get('error', 'Unknown error')
                    report += f" - Error: {error}\n"
        else:
            report += "- No apps currently configured with URLs\n"
        
        report += """
## 📱 App Status Details
"""
        
        for app_name, status in apps_status.items():
            if isinstance(status, dict):
                status_emoji = {
                    'running': '🟢',
                    'stopped': '🔴',
                    'error': '❌'
                }.get(status.get('status'), '⚪')
                
                report += f"- {status_emoji} **{app_name}**: {status.get('status', 'unknown')}"
                
                if status.get('port'):
                    report += f" (Port: {status['port']})"
                
                if status.get('restart_count', 0) > 0:
                    report += f" - Restarts: {status['restart_count']}"
                
                report += "\n"
        
        # Add recommendations
        failed_apps = [app for app, result in connectivity_results['results'].items() 
                      if not result.get('connected', False)]
        
        if failed_apps:
            report += f"""
## ⚠️ Recommendations
- **Failed Apps**: {', '.join(failed_apps)}
- **Action**: Run connectivity verification and restart failed apps
- **Command**: `python daily_engine_integration.py --restart-failed`
"""
        else:
            report += """
## ✅ System Status
- All configured apps are running and accessible
- No immediate action required
- Regular monitoring recommended
"""
        
        report += f"""
## 🔧 Configuration Details
- **Config File**: {config.config_file}
- **Backup File**: {self.config_backup_path}
- **Connectivity Timeout**: {self.connectivity_timeout}s
- **Max Retry Attempts**: {self.max_retry_attempts}
- **Retry Delay**: {self.retry_delay}s

---
*This report is automatically generated by the Daily Engine Integration system*
"""
        
        return report


# Global integration instance
daily_engine_integration = DailyEngineIntegration()


# Convenience functions
def update_daily_engine_config() -> Dict:
    """Update daily_engine configuration with current app URLs"""
    return daily_engine_integration.update_daily_engine_config()


def verify_app_connectivity(app_name: str = None) -> Dict:
    """Verify connectivity to apps"""
    if app_name:
        streamlit_config = config.get('streamlit_apps', {})
        if app_name in streamlit_config and 'url' in streamlit_config[app_name]:
            url = streamlit_config[app_name]['url']
            return {app_name: daily_engine_integration._verify_connectivity(url, app_name)}
        else:
            return {app_name: {'connected': False, 'error': 'App not configured or no URL'}}
    else:
        return daily_engine_integration.verify_all_app_connectivity()


def restart_failed_apps() -> Dict:
    """Restart apps that failed connectivity checks"""
    return daily_engine_integration.restart_failed_apps()


def get_integration_report() -> str:
    """Get integration status report"""
    return daily_engine_integration.generate_integration_report()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Daily Engine Integration Management')
    parser.add_argument('--update-config', action='store_true', help='Update configuration with current URLs')
    parser.add_argument('--verify-connectivity', action='store_true', help='Verify connectivity to all apps')
    parser.add_argument('--restart-failed', action='store_true', help='Restart failed apps')
    parser.add_argument('--report', action='store_true', help='Generate integration report')
    
    args = parser.parse_args()
    
    integration = DailyEngineIntegration()
    
    if args.update_config:
        result = integration.update_daily_engine_config()
        print(f"Configuration update: {'Success' if result['success'] else 'Failed'}")
        if result['success']:
            print(f"Updated {result['updated_apps']} apps")
        else:
            print(f"Error: {result['error']}")
    
    elif args.verify_connectivity:
        result = integration.verify_all_app_connectivity()
        print(f"Connectivity check: {result['summary']['connected_apps']}/{result['summary']['total_apps']} apps connected")
        for app_name, conn_result in result['results'].items():
            status = "✅" if conn_result.get('connected') else "❌"
            print(f"  {status} {app_name}")
    
    elif args.restart_failed:
        result = integration.restart_failed_apps()
        print(f"Restart operation: {result['restart_count']} apps restarted")
        for app_name, restart_result in result['restart_results'].items():
            status = "✅" if restart_result.get('success') else "❌"
            print(f"  {status} {app_name}")
    
    elif args.report:
        report = integration.generate_integration_report()
        print(report)
    
    else:
        # Default: show current status
        result = integration.verify_all_app_connectivity()
        print("Daily Engine Integration Status:")
        print(f"Connected: {result['summary']['connected_apps']}/{result['summary']['total_apps']} apps")
        print(f"Success Rate: {result['summary']['success_rate']:.1f}%")