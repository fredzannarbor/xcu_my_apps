# App Management API Documentation

The App Management API provides a programmatic interface for managing Streamlit applications from other Python scripts. This API wraps the underlying `StreamlitAppManager` functionality with a clean, well-documented interface.

## Installation and Setup

The API is available through the `app_management_api.py` module. No additional installation is required beyond the existing project dependencies.

```python
from app_management_api import AppAPI
```

## Quick Start

```python
from app_management_api import AppAPI

# Initialize the API
api = AppAPI()

# Start an app
result = api.start('daily_engine')
if result.success:
    print(f"App started successfully on {result.url}")
else:
    print(f"Failed to start app: {result.error}")

# Get status of all apps
statuses = api.status()
for app_name, status in statuses.items():
    print(f"{app_name}: {status.status}")

# Stop an app
result = api.stop('daily_engine')
if result.success:
    print("App stopped successfully")
```

## API Reference

### AppAPI Class

The main class for interacting with the app management system.

#### Constructor

```python
AppAPI(config_path: str = "config/streamlit_apps.json")
```

**Parameters:**
- `config_path`: Path to the app configuration file (optional)

#### Methods

##### start(app_name, app_path=None, port=None)

Start a Streamlit application.

**Parameters:**
- `app_name` (str): Name of the app to start
- `app_path` (str, optional): Path to the app file (required for unknown apps)
- `port` (int, optional): Specific port to use

**Returns:** `AppResult` object

**Example:**
```python
# Start a configured app
result = api.start('daily_engine')

# Start an app with custom path
result = api.start('my_app', app_path='path/to/my_app.py')

# Start an app on a specific port
result = api.start('my_app', port=8505)
```

##### stop(app_name)

Stop a Streamlit application.

**Parameters:**
- `app_name` (str): Name of the app to stop

**Returns:** `AppResult` object

**Example:**
```python
result = api.stop('daily_engine')
if result.success:
    print("App stopped successfully")
```

##### restart(app_name)

Restart a Streamlit application.

**Parameters:**
- `app_name` (str): Name of the app to restart

**Returns:** `AppResult` object

**Example:**
```python
result = api.restart('daily_engine')
if result.success:
    print(f"App restarted on {result.url}")
```

##### status(app_name=None)

Get status information for applications.

**Parameters:**
- `app_name` (str, optional): Specific app name. If None, returns all apps.

**Returns:** Dictionary mapping app names to `AppStatus` objects

**Example:**
```python
# Get all app statuses
statuses = api.status()
for name, status in statuses.items():
    print(f"{name}: {status.status}")
    if status.is_running:
        print(f"  Running on port {status.port}")

# Get specific app status
status_dict = api.status('daily_engine')
if 'daily_engine' in status_dict:
    status = status_dict['daily_engine']
    print(f"Status: {status.status}")
```

##### health_check(app_name=None)

Perform health check on applications.

**Parameters:**
- `app_name` (str, optional): Specific app name. If None, checks all running apps.

**Returns:** Dictionary mapping app names to `HealthResult` objects

**Example:**
```python
# Check all apps
health = api.health_check()
for name, result in health.items():
    if result.healthy:
        print(f"{name}: Healthy (status {result.status_code})")
    else:
        print(f"{name}: Unhealthy - {result.reason}")

# Check specific app
health = api.health_check('daily_engine')
```

##### list_apps()

Get list of configured app names.

**Returns:** List of app names

**Example:**
```python
apps = api.list_apps()
print(f"Configured apps: {', '.join(apps)}")
```

##### get_running_apps()

Get list of currently running app names.

**Returns:** List of running app names

**Example:**
```python
running = api.get_running_apps()
print(f"Running apps: {', '.join(running)}")
```

##### get_available_ports()

Get list of available ports in the configured range.

**Returns:** List of available port numbers

**Example:**
```python
ports = api.get_available_ports()
print(f"Available ports: {ports}")
```

##### get_port_assignments()

Get current port assignments for apps.

**Returns:** Dictionary mapping app names to assigned ports

**Example:**
```python
assignments = api.get_port_assignments()
for app, port in assignments.items():
    print(f"{app}: port {port}")
```

##### start_all_enabled()

Start all enabled applications.

**Returns:** Dictionary mapping app names to `AppResult` objects

**Example:**
```python
results = api.start_all_enabled()
for app_name, result in results.items():
    if result.success:
        print(f"Started {app_name} on {result.url}")
    else:
        print(f"Failed to start {app_name}: {result.error}")
```

##### stop_all()

Stop all running applications.

**Returns:** Dictionary mapping app names to `AppResult` objects

**Example:**
```python
results = api.stop_all()
for app_name, result in results.items():
    if result.success:
        print(f"Stopped {app_name}")
```

##### get_app_config(app_name)

Get configuration for a specific app.

**Parameters:**
- `app_name` (str): Name of the app

**Returns:** App configuration dictionary or None if not found

**Example:**
```python
config = api.get_app_config('daily_engine')
if config:
    print(f"Path: {config['path']}")
    print(f"Enabled: {config['enabled']}")
    print(f"Auto-start: {config['auto_start']}")
```

## Data Classes

### AppResult

Result object returned by app operations.

**Attributes:**
- `success` (bool): Whether the operation succeeded
- `app_name` (str): Name of the app
- `message` (str): Success message
- `error` (str): Error message (if failed)
- `port` (int, optional): Port number (for start operations)
- `pid` (int, optional): Process ID (for start operations)
- `url` (str, optional): App URL (for start operations)

**Methods:**
- `__bool__()`: Returns `success` value, allowing use in boolean context

**Example:**
```python
result = api.start('my_app')
if result:  # Uses __bool__ method
    print(f"Success! App running on {result.url}")
else:
    print(f"Failed: {result.error}")
```

### AppStatus

Status information for an application.

**Attributes:**
- `app_name` (str): Name of the app
- `status` (str): Current status ('running', 'stopped', 'not_found', 'unknown')
- `port` (int, optional): Port number
- `pid` (int, optional): Process ID
- `start_time` (str, optional): Start timestamp
- `last_health_check` (str, optional): Last health check timestamp
- `restart_count` (int): Number of restarts
- `error_message` (str, optional): Last error message
- `url` (str, optional): App URL

**Properties:**
- `is_running` (bool): True if app is running
- `is_stopped` (bool): True if app is stopped
- `is_healthy` (bool): True if app is running with recent health check

**Example:**
```python
status = api.status('daily_engine')['daily_engine']
if status.is_running:
    print(f"App is running on {status.url}")
    print(f"Started at: {status.start_time}")
    print(f"Restart count: {status.restart_count}")
```

### HealthResult

Health check result for an application.

**Attributes:**
- `app_name` (str): Name of the app
- `healthy` (bool): Whether the app is healthy
- `reason` (str): Reason if unhealthy
- `status_code` (int, optional): HTTP status code from health check
- `response_time` (float, optional): Response time in seconds

**Example:**
```python
health = api.health_check('daily_engine')['daily_engine']
if health.healthy:
    print(f"App is healthy (HTTP {health.status_code})")
else:
    print(f"App is unhealthy: {health.reason}")
```

## Convenience Functions

For backward compatibility and simple usage, the module also provides standalone functions:

```python
from app_management_api import start_app, stop_app, restart_app, get_app_status, health_check

# These functions return dictionaries in the legacy format
result = start_app('daily_engine')
if result['success']:
    print(f"Started on port {result['port']}")

status = get_app_status('daily_engine')
print(f"Status: {status['status']}")
```

## Error Handling

The API includes comprehensive error handling:

1. **Graceful Failures**: Operations return result objects with success/failure status
2. **Logging**: All operations are logged with appropriate levels
3. **Exception Handling**: Unexpected exceptions are caught and returned as error results
4. **Validation**: Input parameters are validated before operations

**Example:**
```python
result = api.start('nonexistent_app')
if not result.success:
    print(f"Operation failed: {result.error}")
    # Continue with error handling logic
```

## Integration Examples

### Automated Deployment Script

```python
#!/usr/bin/env python3
"""
Automated deployment script using App Management API
"""
from app_management_api import AppAPI
import time

def deploy_apps():
    api = AppAPI()
    
    # Stop all running apps
    print("Stopping all running apps...")
    stop_results = api.stop_all()
    
    # Wait for graceful shutdown
    time.sleep(2)
    
    # Start all enabled apps
    print("Starting all enabled apps...")
    start_results = api.start_all_enabled()
    
    # Report results
    for app_name, result in start_results.items():
        if result.success:
            print(f"✅ {app_name}: {result.url}")
        else:
            print(f"❌ {app_name}: {result.error}")
    
    # Perform health checks
    print("\nPerforming health checks...")
    time.sleep(5)  # Wait for apps to fully start
    
    health_results = api.health_check()
    for app_name, health in health_results.items():
        if health.healthy:
            print(f"✅ {app_name}: Healthy")
        else:
            print(f"❌ {app_name}: {health.reason}")

if __name__ == "__main__":
    deploy_apps()
```

### Monitoring Script

```python
#!/usr/bin/env python3
"""
App monitoring script using App Management API
"""
from app_management_api import AppAPI
import time
import logging

def monitor_apps():
    api = AppAPI()
    
    while True:
        try:
            # Get all app statuses
            statuses = api.status()
            
            # Check each app
            for app_name, status in statuses.items():
                if status.is_running:
                    # Perform health check
                    health = api.health_check(app_name)
                    if app_name in health and not health[app_name].healthy:
                        logging.warning(f"App {app_name} is unhealthy, restarting...")
                        result = api.restart(app_name)
                        if result.success:
                            logging.info(f"Successfully restarted {app_name}")
                        else:
                            logging.error(f"Failed to restart {app_name}: {result.error}")
                
                elif status.status == 'stopped':
                    # Check if app should be auto-started
                    config = api.get_app_config(app_name)
                    if config and config.get('auto_start', False):
                        logging.info(f"Auto-starting {app_name}")
                        result = api.start(app_name)
                        if result.success:
                            logging.info(f"Successfully started {app_name}")
                        else:
                            logging.error(f"Failed to start {app_name}: {result.error}")
            
            # Wait before next check
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("Monitoring stopped")
            break
        except Exception as e:
            logging.exception("Error in monitoring loop")
            time.sleep(60)  # Wait longer on error

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    monitor_apps()
```

### Load Balancer Integration

```python
#!/usr/bin/env python3
"""
Load balancer integration using App Management API
"""
from app_management_api import AppAPI
import json

def update_load_balancer_config():
    api = AppAPI()
    
    # Get running apps
    statuses = api.status()
    running_apps = []
    
    for app_name, status in statuses.items():
        if status.is_running and status.url:
            # Perform health check
            health = api.health_check(app_name)
            if app_name in health and health[app_name].healthy:
                running_apps.append({
                    'name': app_name,
                    'url': status.url,
                    'port': status.port
                })
    
    # Generate load balancer configuration
    lb_config = {
        'upstream_servers': running_apps,
        'health_check_interval': 30,
        'updated_at': time.time()
    }
    
    # Write configuration file
    with open('/etc/nginx/upstream.conf', 'w') as f:
        # Generate nginx upstream configuration
        f.write("upstream streamlit_apps {\n")
        for app in running_apps:
            f.write(f"    server localhost:{app['port']};\n")
        f.write("}\n")
    
    print(f"Updated load balancer config with {len(running_apps)} healthy apps")

if __name__ == "__main__":
    update_load_balancer_config()
```

## Configuration

The API uses the same configuration file as the underlying `StreamlitAppManager`. The default location is `config/streamlit_apps.json`.

**Example configuration:**
```json
{
  "apps": {
    "daily_engine": {
      "name": "Daily Engine",
      "path": "daily_engine.py",
      "port": 8501,
      "enabled": true,
      "auto_start": true,
      "restart_on_failure": true,
      "health_check_url": "/health",
      "environment": {}
    },
    "habit_tracker": {
      "name": "Habit Tracker",
      "path": "habits/habit_tracker.py",
      "port": 8502,
      "enabled": true,
      "auto_start": false,
      "restart_on_failure": true,
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
```

## Best Practices

1. **Error Handling**: Always check the `success` attribute of `AppResult` objects
2. **Logging**: The API logs all operations; configure logging appropriately for your use case
3. **Health Checks**: Use health checks to verify app status before considering operations successful
4. **Graceful Shutdown**: Allow time for apps to shut down gracefully before restarting
5. **Resource Management**: Monitor port usage and clean up stopped apps
6. **Configuration**: Keep app configurations up to date and validate paths exist

## Troubleshooting

### Common Issues

1. **Port Already in Use**: Check `get_available_ports()` and `get_port_assignments()`
2. **App Won't Start**: Verify the app path exists and is executable
3. **Health Check Failures**: Ensure apps respond to HTTP requests on their assigned ports
4. **Permission Errors**: Ensure the process has permission to start/stop applications

### Debugging

Enable debug logging to get detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

api = AppAPI()
result = api.start('my_app')
```

### Getting Help

Check the logs in the `logs/` directory for detailed error information and performance metrics.