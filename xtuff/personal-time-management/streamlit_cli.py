#!/usr/bin/env python3
"""
Streamlit App Manager CLI
Command-line interface for managing Streamlit applications
"""

import argparse
import json
import sys
from typing import Dict, Any
from streamlit_app_manager import StreamlitAppManager
from process_monitor import process_monitor, start_monitoring, stop_monitoring, get_monitoring_stats, force_health_check, detect_port_conflicts, resolve_port_conflicts


class StreamlitCLI:
    """Command-line interface for Streamlit app management"""
    
    def __init__(self):
        self.app_manager = StreamlitAppManager()
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser"""
        parser = argparse.ArgumentParser(
            description='Streamlit App Manager - Manage multiple Streamlit applications',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s start daily_engine                    # Start the daily engine app
  %(prog)s start my_app --path ./my_app.py       # Start custom app with path
  %(prog)s start my_app --port 8505              # Start app on specific port
  %(prog)s stop daily_engine                     # Stop the daily engine app
  %(prog)s restart daily_engine                  # Restart the daily engine app
  %(prog)s status                                # Show status of all apps
  %(prog)s status daily_engine                   # Show status of specific app
  %(prog)s health                                # Health check all apps
  %(prog)s health daily_engine                   # Health check specific app
  %(prog)s monitor start                         # Start background monitoring
  %(prog)s monitor stop                          # Stop background monitoring
  %(prog)s monitor stats                         # Show monitoring statistics
  %(prog)s ports check                           # Check for port conflicts
  %(prog)s ports resolve                         # Resolve port conflicts
  %(prog)s list                                  # List all configured apps
  %(prog)s --json status                         # Output in JSON format
            """
        )
        
        parser.add_argument('--json', action='store_true', 
                          help='Output results in JSON format')
        parser.add_argument('--verbose', '-v', action='store_true',
                          help='Verbose output')
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Start command
        start_parser = subparsers.add_parser('start', help='Start a Streamlit app')
        start_parser.add_argument('app_name', help='Name of the app to start')
        start_parser.add_argument('--path', help='Path to the Streamlit app file')
        start_parser.add_argument('--port', type=int, help='Port to run the app on')
        
        # Stop command
        stop_parser = subparsers.add_parser('stop', help='Stop a Streamlit app')
        stop_parser.add_argument('app_name', help='Name of the app to stop')
        
        # Restart command
        restart_parser = subparsers.add_parser('restart', help='Restart a Streamlit app')
        restart_parser.add_argument('app_name', help='Name of the app to restart')
        
        # Status command
        status_parser = subparsers.add_parser('status', help='Show app status')
        status_parser.add_argument('app_name', nargs='?', help='Name of specific app (optional)')
        
        # Health command
        health_parser = subparsers.add_parser('health', help='Perform health check')
        health_parser.add_argument('app_name', nargs='?', help='Name of specific app (optional)')
        
        # Monitor commands
        monitor_parser = subparsers.add_parser('monitor', help='Monitoring operations')
        monitor_subparsers = monitor_parser.add_subparsers(dest='monitor_action', help='Monitor actions')
        
        monitor_subparsers.add_parser('start', help='Start background monitoring')
        monitor_subparsers.add_parser('stop', help='Stop background monitoring')
        monitor_subparsers.add_parser('stats', help='Show monitoring statistics')
        
        # Port commands
        ports_parser = subparsers.add_parser('ports', help='Port management operations')
        ports_subparsers = ports_parser.add_subparsers(dest='ports_action', help='Port actions')
        
        ports_subparsers.add_parser('check', help='Check for port conflicts')
        ports_subparsers.add_parser('resolve', help='Resolve port conflicts')
        ports_subparsers.add_parser('list', help='List port assignments')
        
        # List command
        subparsers.add_parser('list', help='List all configured apps')
        
        return parser
    
    def run(self, args=None):
        """Run the CLI with given arguments"""
        parsed_args = self.parser.parse_args(args)
        
        if not parsed_args.command:
            self.parser.print_help()
            return 1
        
        try:
            result = self._execute_command(parsed_args)
            self._output_result(result, parsed_args.json, parsed_args.verbose)
            
            # Return appropriate exit code
            if isinstance(result, dict):
                if result.get('success') is False:
                    return 1
                elif 'error' in result:
                    return 1
            
            return 0
            
        except Exception as e:
            error_result = {'error': str(e), 'success': False}
            self._output_result(error_result, parsed_args.json, parsed_args.verbose)
            return 1
    
    def _execute_command(self, args) -> Dict[str, Any]:
        """Execute the specified command"""
        if args.command == 'start':
            return self.app_manager.start_app(args.app_name, args.path, args.port)
        
        elif args.command == 'stop':
            return self.app_manager.stop_app(args.app_name)
        
        elif args.command == 'restart':
            return self.app_manager.restart_app(args.app_name)
        
        elif args.command == 'status':
            return self.app_manager.get_app_status(args.app_name)
        
        elif args.command == 'health':
            return force_health_check(args.app_name)
        
        elif args.command == 'monitor':
            return self._handle_monitor_command(args)
        
        elif args.command == 'ports':
            return self._handle_ports_command(args)
        
        elif args.command == 'list':
            return self._list_apps()
        
        else:
            return {'error': f'Unknown command: {args.command}', 'success': False}
    
    def _handle_monitor_command(self, args) -> Dict[str, Any]:
        """Handle monitor subcommands"""
        if args.monitor_action == 'start':
            interval = getattr(args, 'interval', 30)
            start_monitoring(interval)
            return {'success': True, 'message': f'Monitoring started with {interval}s interval'}
        
        elif args.monitor_action == 'stop':
            stop_monitoring()
            return {'success': True, 'message': 'Monitoring stopped'}
        
        elif args.monitor_action == 'stats':
            stats = get_monitoring_stats()
            return {'success': True, 'stats': stats}
        
        else:
            return {'error': 'Monitor action required: start, stop, or stats', 'success': False}
    
    def _handle_ports_command(self, args) -> Dict[str, Any]:
        """Handle ports subcommands"""
        if args.ports_action == 'check':
            conflicts = detect_port_conflicts()
            return {'success': True, 'conflicts': conflicts, 'count': len(conflicts)}
        
        elif args.ports_action == 'resolve':
            result = resolve_port_conflicts()
            return {'success': True, 'resolution': result}
        
        elif args.ports_action == 'list':
            assignments = self.app_manager.port_manager.get_port_assignments()
            available = self.app_manager.port_manager.get_available_ports()
            return {
                'success': True,
                'assignments': assignments,
                'available_ports': available,
                'port_range': self.app_manager.port_manager.port_range
            }
        
        else:
            return {'error': 'Ports action required: check, resolve, or list', 'success': False}
    
    def _list_apps(self) -> Dict[str, Any]:
        """List all configured apps"""
        configured_apps = self.app_manager.config.get('apps', {})
        app_status = self.app_manager.get_app_status()
        
        apps_info = []
        for app_name, config in configured_apps.items():
            status = app_status.get(app_name, {})
            apps_info.append({
                'name': app_name,
                'display_name': config.get('name', app_name),
                'path': config.get('path', 'unknown'),
                'enabled': config.get('enabled', True),
                'auto_start': config.get('auto_start', False),
                'status': status.get('status', 'unknown'),
                'port': status.get('port'),
                'pid': status.get('pid'),
                'restart_count': status.get('restart_count', 0)
            })
        
        return {'success': True, 'apps': apps_info, 'total': len(apps_info)}
    
    def _output_result(self, result: Dict[str, Any], json_output: bool, verbose: bool):
        """Output the result in the specified format"""
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            self._format_human_output(result, verbose)
    
    def _format_human_output(self, result: Dict[str, Any], verbose: bool):
        """Format output for human reading"""
        if 'error' in result:
            print(f"❌ Error: {result['error']}", file=sys.stderr)
            return
        
        if 'message' in result:
            print(f"✅ {result['message']}")
        
        # Handle different result types
        if 'apps' in result:
            self._format_apps_list(result['apps'], verbose)
        
        elif 'stats' in result:
            self._format_monitoring_stats(result['stats'])
        
        elif 'conflicts' in result:
            self._format_port_conflicts(result['conflicts'])
        
        elif 'resolution' in result:
            self._format_port_resolution(result['resolution'])
        
        elif 'assignments' in result:
            self._format_port_assignments(result)
        
        elif 'app_name' in result:
            self._format_single_app_result(result, verbose)
        
        elif isinstance(result, dict) and len(result) > 0:
            # Multiple app status
            if all(isinstance(v, dict) for v in result.values()):
                self._format_multiple_app_status(result, verbose)
            else:
                # Health check results
                self._format_health_results(result)
    
    def _format_apps_list(self, apps: list, verbose: bool):
        """Format apps list output"""
        print(f"\n📱 Configured Apps ({len(apps)} total):")
        print("-" * 80)
        
        for app in apps:
            status_emoji = {
                'running': '🟢',
                'stopped': '🔴',
                'error': '❌',
                'unknown': '⚪'
            }.get(app['status'], '⚪')
            
            enabled_text = "✅" if app['enabled'] else "❌"
            auto_start_text = "🚀" if app['auto_start'] else "🔧"
            
            print(f"{status_emoji} {app['display_name']} ({app['name']})")
            
            if verbose or app['status'] != 'unknown':
                print(f"   Path: {app['path']}")
                print(f"   Status: {app['status']}")
                if app['port']:
                    print(f"   Port: {app['port']}")
                if app['pid']:
                    print(f"   PID: {app['pid']}")
                print(f"   Enabled: {enabled_text}  Auto-start: {auto_start_text}")
                if app['restart_count'] > 0:
                    print(f"   Restarts: {app['restart_count']}")
                print()
    
    def _format_monitoring_stats(self, stats: dict):
        """Format monitoring statistics"""
        print(f"\n📊 Monitoring Statistics:")
        print("-" * 40)
        print(f"Total Apps: {stats['total_apps']}")
        print(f"Running: {stats['running_apps']} 🟢")
        print(f"Stopped: {stats['stopped_apps']} 🔴")
        print(f"Failed: {stats['failed_apps']} ❌")
        print(f"High Restarts: {stats['apps_with_high_restarts']} ⚠️")
        print(f"Monitoring Active: {'Yes' if stats['monitoring_active'] else 'No'}")
    
    def _format_port_conflicts(self, conflicts: list):
        """Format port conflicts output"""
        if not conflicts:
            print("✅ No port conflicts detected")
            return
        
        print(f"\n⚠️  Port Conflicts Detected ({len(conflicts)}):")
        print("-" * 50)
        
        for conflict in conflicts:
            print(f"App: {conflict['app_name']}")
            print(f"Type: {conflict['type']}")
            print(f"Assigned Port: {conflict['assigned_port']}")
            
            if conflict['type'] == 'port_conflict':
                proc = conflict['conflicting_process']
                print(f"Conflicting Process: {proc['name']} (PID: {proc['pid']})")
            elif conflict['type'] == 'port_mismatch':
                print(f"Actual Port: {conflict['actual_port']}")
            print()
    
    def _format_port_resolution(self, resolution: dict):
        """Format port resolution results"""
        print(f"\n🔧 Port Conflict Resolution:")
        print("-" * 40)
        print(f"Conflicts Found: {resolution['conflicts_found']}")
        print(f"Resolved: {len(resolution['resolved'])}")
        print(f"Failed: {len(resolution['failed'])}")
        
        if resolution['resolved']:
            print("\n✅ Successfully Resolved:")
            for item in resolution['resolved']:
                print(f"  {item['app_name']}: {item['old_port']} → {item['new_port']} ({item['action']})")
        
        if resolution['failed']:
            print("\n❌ Failed to Resolve:")
            for item in resolution['failed']:
                print(f"  {item['app_name']}: {item['error']}")
    
    def _format_port_assignments(self, result: dict):
        """Format port assignments"""
        print(f"\n🔌 Port Assignments:")
        print("-" * 30)
        print(f"Port Range: {result['port_range'][0]}-{result['port_range'][1]}")
        print(f"Available Ports: {result['available_ports']}")
        
        if result['assignments']:
            print("\nAssigned Ports:")
            for app_name, port in result['assignments'].items():
                print(f"  {app_name}: {port}")
        else:
            print("\nNo ports currently assigned")
    
    def _format_single_app_result(self, result: dict, verbose: bool):
        """Format single app operation result"""
        if result.get('success'):
            if 'url' in result:
                print(f"🚀 Started {result['app_name']} on port {result['port']}")
                print(f"   URL: {result['url']}")
                print(f"   PID: {result['pid']}")
            else:
                print(f"✅ Operation completed for {result.get('app_name', 'app')}")
        else:
            print(f"❌ Operation failed: {result.get('error', 'Unknown error')}")
    
    def _format_multiple_app_status(self, results: dict, verbose: bool):
        """Format multiple app status results"""
        print(f"\n📱 App Status ({len(results)} apps):")
        print("-" * 60)
        
        for app_name, status in results.items():
            if isinstance(status, dict):
                status_emoji = {
                    'running': '🟢',
                    'stopped': '🔴',
                    'error': '❌'
                }.get(status.get('status'), '⚪')
                
                print(f"{status_emoji} {app_name}: {status.get('status', 'unknown')}")
                
                if verbose or status.get('status') == 'running':
                    if status.get('port'):
                        print(f"   Port: {status['port']}")
                    if status.get('pid'):
                        print(f"   PID: {status['pid']}")
                    if status.get('restart_count', 0) > 0:
                        print(f"   Restarts: {status['restart_count']}")
                    if status.get('error_message'):
                        print(f"   Error: {status['error_message']}")
    
    def _format_health_results(self, results: dict):
        """Format health check results"""
        print(f"\n🏥 Health Check Results:")
        print("-" * 40)
        
        for app_name, health in results.items():
            if isinstance(health, dict):
                health_emoji = "✅" if health.get('healthy') else "❌"
                print(f"{health_emoji} {app_name}: {'Healthy' if health.get('healthy') else 'Unhealthy'}")
                
                if not health.get('healthy'):
                    reason = health.get('reason', 'unknown')
                    print(f"   Reason: {reason}")
                elif 'status_code' in health:
                    print(f"   Status Code: {health['status_code']}")
                    if 'response_time' in health:
                        print(f"   Response Time: {health['response_time']:.2f}s")


def main():
    """Main CLI entry point"""
    cli = StreamlitCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()