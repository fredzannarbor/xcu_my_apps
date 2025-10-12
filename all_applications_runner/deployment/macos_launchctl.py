#!/usr/bin/env python3
"""
macOS LaunchControl Deployment for Unified App Runner

Creates and manages launchctl plists for automatic startup of the app runner system.
"""

import json
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class MacOSDeployment:
    """Manages macOS deployment using launchctl."""

    def __init__(self, config_path: str = "../apps_config.json"):
        self.config_path = Path(__file__).parent / config_path
        self.config = self._load_config()
        self.launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
        self.app_runner_dir = Path(__file__).parent.parent.resolve()

    def _load_config(self):
        """Load the application configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration: {e}")
            raise

    def create_plist_content(self, service_name: str, description: str,
                           working_directory: str, program_arguments: list,
                           environment_variables: dict = None) -> str:
        """Create a launchctl plist XML content."""

        # Create the root element
        root = ET.Element("plist")
        root.set("version", "1.0")

        # Create the dict element
        dict_elem = ET.SubElement(root, "dict")

        # Add Label
        ET.SubElement(dict_elem, "key").text = "Label"
        ET.SubElement(dict_elem, "string").text = service_name

        # Add Description
        ET.SubElement(dict_elem, "key").text = "Description"
        ET.SubElement(dict_elem, "string").text = description

        # Add ProgramArguments
        ET.SubElement(dict_elem, "key").text = "ProgramArguments"
        array_elem = ET.SubElement(dict_elem, "array")
        for arg in program_arguments:
            ET.SubElement(array_elem, "string").text = str(arg)

        # Add WorkingDirectory
        ET.SubElement(dict_elem, "key").text = "WorkingDirectory"
        ET.SubElement(dict_elem, "string").text = working_directory

        # Add RunAtLoad
        ET.SubElement(dict_elem, "key").text = "RunAtLoad"
        ET.SubElement(dict_elem, "true")

        # Add KeepAlive
        ET.SubElement(dict_elem, "key").text = "KeepAlive"
        ET.SubElement(dict_elem, "true")

        # Add Environment Variables if provided
        if environment_variables:
            ET.SubElement(dict_elem, "key").text = "EnvironmentVariables"
            env_dict = ET.SubElement(dict_elem, "dict")
            for key, value in environment_variables.items():
                ET.SubElement(env_dict, "key").text = key
                ET.SubElement(env_dict, "string").text = str(value)

        # Add StandardOutPath and StandardErrorPath
        log_dir = Path.home() / "Library" / "Logs" / "FredApps"
        log_dir.mkdir(parents=True, exist_ok=True)

        ET.SubElement(dict_elem, "key").text = "StandardOutPath"
        ET.SubElement(dict_elem, "string").text = str(log_dir / f"{service_name}.out.log")

        ET.SubElement(dict_elem, "key").text = "StandardErrorPath"
        ET.SubElement(dict_elem, "string").text = str(log_dir / f"{service_name}.err.log")

        # Format the XML
        ET.indent(root, space="  ", level=0)
        return ET.tostring(root, encoding='unicode', xml_declaration=True)

    def create_master_runner_plist(self) -> Path:
        """Create the plist for the master app runner."""
        service_name = "com.fredzannarbor.apprunner.master"
        description = "Fred's Unified App Runner Master Controller"

        # Determine Python executable
        python_exec = self._get_python_executable()

        program_arguments = [
            python_exec,
            "-c",
            "import streamlit.web.cli as stcli; import sys; sys.argv = ['streamlit', 'run', 'main.py', '--server.port=8500', '--server.address=0.0.0.0']; stcli.main()"
        ]

        environment_variables = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": str(self.app_runner_dir),
        }

        plist_content = self.create_plist_content(
            service_name=service_name,
            description=description,
            working_directory=str(self.app_runner_dir),
            program_arguments=program_arguments,
            environment_variables=environment_variables
        )

        plist_path = self.launch_agents_dir / f"{service_name}.plist"

        with open(plist_path, 'w') as f:
            f.write(plist_content)

        logger.info(f"Created master runner plist: {plist_path}")
        return plist_path

    def create_process_manager_plist(self) -> Path:
        """Create the plist for the process manager."""
        service_name = "com.fredzannarbor.apprunner.manager"
        description = "Fred's App Runner Process Manager"

        python_exec = self._get_python_executable()

        program_arguments = [
            python_exec,
            "process_manager.py",
            "--action", "start"
        ]

        environment_variables = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": str(self.app_runner_dir),
        }

        plist_content = self.create_plist_content(
            service_name=service_name,
            description=description,
            working_directory=str(self.app_runner_dir),
            program_arguments=program_arguments,
            environment_variables=environment_variables
        )

        plist_path = self.launch_agents_dir / f"{service_name}.plist"

        with open(plist_path, 'w') as f:
            f.write(plist_content)

        logger.info(f"Created process manager plist: {plist_path}")
        return plist_path

    def _get_python_executable(self) -> str:
        """Get the appropriate Python executable."""
        # Try to find Python in virtual environment first
        venv_python = self.app_runner_dir / ".venv" / "bin" / "python"
        if venv_python.exists():
            return str(venv_python)

        # Fall back to system Python
        try:
            result = subprocess.run(["which", "python3"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except subprocess.SubprocessError:
            pass

        # Default fallback
        return "/usr/bin/python3"

    def install_services(self):
        """Install all launchctl services."""
        # Ensure launch agents directory exists
        self.launch_agents_dir.mkdir(parents=True, exist_ok=True)

        # Create plists
        master_plist = self.create_master_runner_plist()
        manager_plist = self.create_process_manager_plist()

        # Load services
        services = [
            ("com.fredzannarbor.apprunner.master", master_plist),
            ("com.fredzannarbor.apprunner.manager", manager_plist)
        ]

        for service_name, plist_path in services:
            try:
                # Unload if already loaded
                subprocess.run(
                    ["launchctl", "unload", str(plist_path)],
                    capture_output=True
                )

                # Load the service
                result = subprocess.run(
                    ["launchctl", "load", str(plist_path)],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    logger.info(f"Successfully loaded service: {service_name}")
                else:
                    logger.error(f"Failed to load service {service_name}: {result.stderr}")

            except subprocess.SubprocessError as e:
                logger.error(f"Error managing service {service_name}: {e}")

    def uninstall_services(self):
        """Uninstall all launchctl services."""
        service_names = [
            "com.fredzannarbor.apprunner.master",
            "com.fredzannarbor.apprunner.manager"
        ]

        for service_name in service_names:
            plist_path = self.launch_agents_dir / f"{service_name}.plist"

            try:
                # Unload the service
                result = subprocess.run(
                    ["launchctl", "unload", str(plist_path)],
                    capture_output=True,
                    text=True
                )

                # Remove the plist file
                if plist_path.exists():
                    plist_path.unlink()
                    logger.info(f"Removed plist: {plist_path}")

                logger.info(f"Successfully unloaded service: {service_name}")

            except subprocess.SubprocessError as e:
                logger.error(f"Error unloading service {service_name}: {e}")

    def get_service_status(self) -> dict:
        """Get the status of all managed services."""
        service_names = [
            "com.fredzannarbor.apprunner.master",
            "com.fredzannarbor.apprunner.manager"
        ]

        status = {}

        for service_name in service_names:
            try:
                result = subprocess.run(
                    ["launchctl", "list", service_name],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    # Parse the output to get PID and status
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 3:
                        # Format: PID\tStatus\tLabel
                        parts = lines[-1].split('\t')
                        if len(parts) >= 3:
                            pid = parts[0] if parts[0] != '-' else None
                            exit_status = parts[1] if parts[1] != '-' else None

                            status[service_name] = {
                                "loaded": True,
                                "pid": pid,
                                "exit_status": exit_status,
                                "running": pid is not None and pid != '-'
                            }
                        else:
                            status[service_name] = {"loaded": True, "running": False}
                    else:
                        status[service_name] = {"loaded": True, "running": False}
                else:
                    status[service_name] = {"loaded": False, "running": False}

            except subprocess.SubprocessError as e:
                logger.error(f"Error checking status of {service_name}: {e}")
                status[service_name] = {"loaded": False, "running": False, "error": str(e)}

        return status

    def create_install_script(self) -> Path:
        """Create a shell script for easy installation."""
        script_content = f"""#!/bin/bash
# Installation script for Fred's Unified App Runner
# Generated automatically - do not edit manually

set -e

echo "Installing Fred's Unified App Runner..."

# Check if we're in the right directory
if [ ! -f "apps_config.json" ]; then
    echo "Error: Must run from app runner directory"
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
if command -v uv &> /dev/null; then
    uv sync
elif [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "Warning: No requirements.txt found"
fi

# Create log directory
mkdir -p "$HOME/Library/Logs/FredApps"

# Install launchctl services
echo "Installing launchctl services..."
python3 deployment/macos_launchctl.py install

echo "Installation complete!"
echo ""
echo "Services installed:"
echo "  - Master App Runner (port 8500)"
echo "  - Process Manager"
echo ""
echo "Check status with: python3 deployment/macos_launchctl.py status"
echo "View logs in: $HOME/Library/Logs/FredApps/"
echo ""
echo "Access the app runner at: http://localhost:8500"
"""

        script_path = self.app_runner_dir / "install.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)

        # Make executable
        script_path.chmod(0o755)

        logger.info(f"Created install script: {script_path}")
        return script_path

    def create_uninstall_script(self) -> Path:
        """Create a shell script for easy uninstallation."""
        script_content = f"""#!/bin/bash
# Uninstallation script for Fred's Unified App Runner
# Generated automatically - do not edit manually

set -e

echo "Uninstalling Fred's Unified App Runner..."

# Uninstall launchctl services
echo "Removing launchctl services..."
python3 deployment/macos_launchctl.py uninstall

echo "Uninstallation complete!"
echo ""
echo "Note: Configuration files and logs have been preserved."
echo "To remove completely, delete:"
echo "  - $HOME/Library/Logs/FredApps/"
echo "  - {self.app_runner_dir}"
"""

        script_path = self.app_runner_dir / "uninstall.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)

        # Make executable
        script_path.chmod(0o755)

        logger.info(f"Created uninstall script: {script_path}")
        return script_path

def main():
    """Main CLI for macOS deployment management."""
    import argparse

    parser = argparse.ArgumentParser(description="macOS LaunchControl Deployment Manager")
    parser.add_argument("action", choices=["install", "uninstall", "status", "scripts"],
                       help="Action to perform")

    args = parser.parse_args()

    deployment = MacOSDeployment()

    if args.action == "install":
        print("Installing launchctl services...")
        deployment.install_services()
        print("Installation complete!")

    elif args.action == "uninstall":
        print("Uninstalling launchctl services...")
        deployment.uninstall_services()
        print("Uninstallation complete!")

    elif args.action == "status":
        print("Service Status:")
        status = deployment.get_service_status()
        for service, info in status.items():
            print(f"  {service}:")
            for key, value in info.items():
                print(f"    {key}: {value}")
            print()

    elif args.action == "scripts":
        print("Creating installation scripts...")
        install_script = deployment.create_install_script()
        uninstall_script = deployment.create_uninstall_script()
        print(f"Created: {install_script}")
        print(f"Created: {uninstall_script}")

if __name__ == "__main__":
    main()