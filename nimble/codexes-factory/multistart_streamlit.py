import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

def launch_servers(role, include=None, exclude=None):
    # Correctly locate streamlit_servers.json in the project root
    project_root = Path(__file__).resolve().parent
    config_path = project_root / "streamlit_servers.json"

    with open(config_path, 'r') as f:
        servers = json.load(f)

    # Set PYTHONPATH to include the 'src' directory
    pythonpath = project_root / "src"
    env = os.environ.copy()
    env['PYTHONPATH'] = f"{pythonpath}:{env.get('PYTHONPATH', '')}"

    # Filter servers based on role and command-line flags
    servers_to_launch = []
    for server in servers:
        if include and server['name'] not in include:
            continue
        if exclude and server['name'] in exclude:
            continue
        servers_to_launch.append(server)

    # Launch the filtered servers as subprocesses
    processes = []
    for server in servers_to_launch:
        if 'venv' in server:
            # Construct path to the executable inside the venv
            executable = project_root / server['venv'] / 'bin' / server['command'][0]
            command = [str(executable)] + server['command'][1:]
        else:
            # Use 'uv run' for servers without a specific venv
            command = ['uv', 'run'] + server['command']

        print(f"Launching {server['name']}: {' '.join(command)}")
        proc = subprocess.Popen(command, env=env)
        processes.append(proc)

    # Wait for all server processes to complete
    for proc in processes:
        proc.wait()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Launch Streamlit servers based on user roles.')
    parser.add_argument('--role', required=False, choices=['multi-organizational', 'personal'], help='The user role to determine which servers to launch.')
    parser.add_argument('--include', nargs='+', help='A list of specific servers to launch.')
    parser.add_argument('--exclude', nargs='+', help='A list of specific servers to exclude from launching.')
    args = parser.parse_args()

    launch_servers(args.role, args.include, args.exclude)
