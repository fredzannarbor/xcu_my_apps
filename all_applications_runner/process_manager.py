#!/usr/bin/env python3
"""
Process Manager for Unified Streamlit App Runner

Handles launching, monitoring, and health checking of multiple Streamlit applications.
"""

import json
import logging
import os
import signal
import subprocess
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class AppProcess:
    """Represents a managed application process."""
    org_id: str
    app_id: str
    name: str
    port: int
    path: str
    entry: str
    startup_command: str
    auth_level: str
    status: str
    description: str
    health_endpoint: str
    environment: Dict[str, str] = field(default_factory=dict)
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None
    last_health_check: Optional[datetime] = None
    last_restart_time: Optional[datetime] = None
    health_status: str = "unknown"
    restart_count: int = 0
    max_restarts: int = 5

class ProcessManager:
    """Manages multiple Streamlit application processes."""

    def __init__(self, config_path: str = "apps_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.processes: Dict[str, AppProcess] = {}
        self._running = False
        self._health_check_thread = None

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_path} not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise

    def _create_app_process(self, org_id: str, app_id: str, app_config: Dict[str, Any]) -> AppProcess:
        """Create an AppProcess instance from configuration."""
        return AppProcess(
            org_id=org_id,
            app_id=app_id,
            name=app_config.get("name", app_id),
            port=app_config["port"],
            path=app_config["path"],
            entry=app_config["entry"],
            startup_command=app_config["startup_command"],
            auth_level=app_config.get("auth_level", "public"),
            status=app_config.get("status", "development"),
            description=app_config.get("description", ""),
            health_endpoint=app_config.get("health_endpoint", "/"),
            environment=app_config.get("environment", {})
        )

    def initialize_processes(self):
        """Initialize all application processes from configuration."""
        self.processes.clear()

        for org_id, org_config in self.config["organizations"].items():
            org_name = org_config.get("name", org_id)
            logger.info(f"Processing organization: {org_name}")

            for app_id, app_config in org_config.get("apps", {}).items():
                process_key = f"{org_id}.{app_id}"
                app_process = self._create_app_process(org_id, app_id, app_config)
                self.processes[process_key] = app_process
                logger.info(f"Initialized process config for {app_process.name}")

    def start_process(self, process_key: str) -> bool:
        """Start a specific application process."""
        if process_key not in self.processes:
            logger.error(f"Process {process_key} not found")
            return False

        app = self.processes[process_key]

        # Check if already running
        if app.process and app.process.poll() is None:
            logger.info(f"{app.name} is already running on port {app.port}")
            return True

        # Check if port is available
        if self._is_port_in_use(app.port):
            logger.warning(f"Port {app.port} is already in use for {app.name}")
            return False

        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(app.environment)

            # Change to app directory
            app_path = Path(app.path)
            if not app_path.exists():
                logger.error(f"App path does not exist: {app.path}")
                return False

            # Start the process
            logger.info(f"Starting {app.name} on port {app.port}...")
            app.process = subprocess.Popen(
                app.startup_command.split(),
                cwd=app.path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )

            app.pid = app.process.pid
            logger.info(f"Started {app.name} with PID {app.pid}")

            # Wait a moment for startup
            time.sleep(2)

            # Check if process is still running
            if app.process.poll() is None:
                logger.info(f"{app.name} started successfully")
                return True
            else:
                stderr = app.process.stderr.read().decode() if app.process.stderr else "No error output"
                logger.error(f"Failed to start {app.name}: {stderr}")
                return False

        except Exception as e:
            logger.error(f"Error starting {app.name}: {e}")
            return False

    def stop_process(self, process_key: str) -> bool:
        """Stop a specific application process."""
        if process_key not in self.processes:
            logger.error(f"Process {process_key} not found")
            return False

        app = self.processes[process_key]

        if not app.process or app.process.poll() is not None:
            logger.info(f"{app.name} is not running")
            return True

        try:
            # Try graceful shutdown first
            logger.info(f"Stopping {app.name} (PID {app.pid})...")

            # Send SIGTERM to process group
            os.killpg(os.getpgid(app.pid), signal.SIGTERM)

            # Wait up to 10 seconds for graceful shutdown
            for _ in range(10):
                if app.process.poll() is not None:
                    logger.info(f"{app.name} stopped gracefully")
                    app.process = None
                    app.pid = None
                    return True
                time.sleep(1)

            # Force kill if still running
            logger.warning(f"Force killing {app.name}")
            os.killpg(os.getpgid(app.pid), signal.SIGKILL)
            app.process = None
            app.pid = None

            return True

        except Exception as e:
            logger.error(f"Error stopping {app.name}: {e}")
            return False

    def restart_process(self, process_key: str) -> bool:
        """Restart a specific application process."""
        app = self.processes.get(process_key)
        if not app:
            return False

        if app.restart_count >= app.max_restarts:
            logger.error(f"Maximum restart attempts reached for {app.name}")
            return False

        logger.info(f"Restarting {app.name}...")
        app.restart_count += 1

        self.stop_process(process_key)
        time.sleep(2)
        success = self.start_process(process_key)

        if success:
            app.last_restart_time = datetime.now()
            logger.info(f"Successfully restarted {app.name} at {app.last_restart_time}")

        return success

    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is currently in use."""
        try:
            connections = psutil.net_connections()
            for conn in connections:
                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    return True
            return False
        except Exception:
            # Fallback method
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) == 0

    def check_health(self, process_key: str) -> bool:
        """Check health of a specific application."""
        app = self.processes.get(process_key)
        if not app:
            return False

        # Check if process is running (either managed process or external process on port)
        is_process_running = (app.process and app.process.poll() is None) or self._is_port_in_use(app.port)
        if not is_process_running:
            app.health_status = "stopped"
            return False

        # Check HTTP endpoint
        try:
            url = f"http://localhost:{app.port}{app.health_endpoint}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                app.health_status = "healthy"
                app.last_health_check = datetime.now()
                return True
            else:
                app.health_status = f"unhealthy (HTTP {response.status_code})"
                return False

        except requests.exceptions.RequestException as e:
            app.health_status = f"unreachable ({str(e)[:50]})"
            return False

    def health_check_loop(self):
        """Continuous health checking loop."""
        interval = self.config["global_settings"].get("health_check_interval", 30)
        auto_restart = self.config["global_settings"].get("auto_restart", True)

        logger.info(f"Starting health check loop (interval: {interval}s, auto_restart: {auto_restart})")

        while self._running:
            for process_key in self.processes:
                if not self.check_health(process_key):
                    app = self.processes[process_key]
                    logger.warning(f"Health check failed for {app.name}: {app.health_status}")

                    if auto_restart and app.health_status == "stopped":
                        logger.info(f"Auto-restarting {app.name}")
                        self.restart_process(process_key)

            time.sleep(interval)

    def start_all(self):
        """Start all configured applications."""
        logger.info("Starting all applications...")
        success_count = 0

        for process_key in self.processes:
            if self.start_process(process_key):
                success_count += 1

        logger.info(f"Started {success_count}/{len(self.processes)} applications")

        # Start health checking
        self._running = True
        self._health_check_thread = threading.Thread(target=self.health_check_loop, daemon=True)
        self._health_check_thread.start()

    def stop_all(self):
        """Stop all running applications."""
        logger.info("Stopping all applications...")
        self._running = False

        if self._health_check_thread:
            self._health_check_thread.join(timeout=5)

        for process_key in self.processes:
            self.stop_process(process_key)

        logger.info("All applications stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get status of all applications."""
        status = {
            "timestamp": datetime.now().isoformat(),
            "organizations": {},
            "summary": {
                "total": len(self.processes),
                "running": 0,
                "healthy": 0,
                "stopped": 0
            }
        }

        # Group by organization
        for process_key, app in self.processes.items():
            org_id, app_id = process_key.split('.', 1)

            if org_id not in status["organizations"]:
                org_config = self.config["organizations"][org_id]
                status["organizations"][org_id] = {
                    "name": org_config.get("name", org_id),
                    "description": org_config.get("description", ""),
                    "apps": {}
                }

            # Check current status - either managed process or external process on port
            is_running = (app.process and app.process.poll() is None) or self._is_port_in_use(app.port)
            self.check_health(process_key)

            app_status = {
                "name": app.name,
                "port": app.port,
                "status": app.status,
                "auth_level": app.auth_level,
                "description": app.description,
                "running": is_running,
                "health_status": app.health_status,
                "last_health_check": app.last_health_check.isoformat() if app.last_health_check else None,
                "last_restart_time": app.last_restart_time.isoformat() if app.last_restart_time else None,
                "restart_count": app.restart_count,
                "pid": app.pid
            }

            status["organizations"][org_id]["apps"][app_id] = app_status

            # Update summary
            if is_running:
                status["summary"]["running"] += 1
                if app.health_status == "healthy":
                    status["summary"]["healthy"] += 1
            else:
                status["summary"]["stopped"] += 1

        return status

def main():
    """Main entry point for process manager."""
    import argparse

    parser = argparse.ArgumentParser(description="Unified Streamlit App Process Manager")
    parser.add_argument("--config", default="apps_config.json", help="Configuration file path")
    parser.add_argument("--action", choices=["start", "stop", "restart", "status"], default="start",
                       help="Action to perform")
    parser.add_argument("--app", help="Specific app to target (format: org_id.app_id)")

    args = parser.parse_args()

    try:
        manager = ProcessManager(args.config)
        manager.initialize_processes()

        if args.action == "start":
            if args.app:
                success = manager.start_process(args.app)
                print(f"Started {args.app}: {success}")
            else:
                manager.start_all()
                print("Started all applications. Press Ctrl+C to stop.")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    manager.stop_all()

        elif args.action == "stop":
            if args.app:
                success = manager.stop_process(args.app)
                print(f"Stopped {args.app}: {success}")
            else:
                manager.stop_all()

        elif args.action == "restart":
            if args.app:
                success = manager.restart_process(args.app)
                print(f"Restarted {args.app}: {success}")
            else:
                manager.stop_all()
                time.sleep(2)
                manager.start_all()

        elif args.action == "status":
            status = manager.get_status()
            print(json.dumps(status, indent=2))

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())