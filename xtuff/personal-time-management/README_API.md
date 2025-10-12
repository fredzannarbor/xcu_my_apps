# App Management API

A programmatic interface for managing Streamlit applications from other Python scripts.

## Quick Start

```python
from app_management_api import AppAPI

# Initialize the API
api = AppAPI()

# Start an app
result = api.start('daily_engine')
if result.success:
    print(f"App started on {result.url}")

# Get status of all apps
statuses = api.status()
for app_name, status in statuses.items():
    print(f"{app_name}: {status.status}")

# Stop an app
api.stop('daily_engine')
```

## Features

- **Start/Stop/Restart** Streamlit applications programmatically
- **Health Checks** to verify app status
- **Port Management** with automatic assignment
- **Batch Operations** to manage multiple apps
- **Comprehensive Error Handling** with detailed result objects
- **Configuration Management** for app settings
- **Monitoring Support** for automated health checks

## Files

- `app_management_api.py` - Main API module
- `docs/app_management_api.md` - Complete documentation
- `examples/app_management_examples.py` - Usage examples
- `tests/test_app_management_api.py` - Test suite

## Usage Examples

### Basic Operations
```python
api = AppAPI()

# List configured apps
apps = api.list_apps()

# Start all enabled apps
results = api.start_all_enabled()

# Perform health checks
health = api.health_check()
```

### Monitoring Script
```python
def monitor_apps():
    api = AppAPI()
    
    statuses = api.status()
    for app_name, status in statuses.items():
        if status.is_running:
            health = api.health_check(app_name)
            if not health[app_name].healthy:
                print(f"Restarting unhealthy app: {app_name}")
                api.restart(app_name)
```

### Error Handling
```python
result = api.start('my_app')
if result.success:
    print(f"Started successfully on {result.url}")
else:
    print(f"Failed to start: {result.error}")
```

## Documentation

See `docs/app_management_api.md` for complete API documentation including:
- Detailed method descriptions
- Data class specifications
- Integration examples
- Best practices
- Troubleshooting guide

## Testing

Run the test suite:
```bash
python tests/test_app_management_api.py
```

## Examples

Run the examples:
```bash
python examples/app_management_examples.py
```