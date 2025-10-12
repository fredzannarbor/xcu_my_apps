# xcu_my_apps Development & Deployment Workflow

## Quick Start: Local Development

### 1. Test Locally on Port 8500

```bash
# Start any app locally for testing
cd /Users/fred/xcu_my_apps

# Example: Run all_applications_runner locally
uv run streamlit run all_applications_runner/main.py --server.port=8500 --server.address=127.0.0.1

# Example: Run codexes-factory locally
cd nimble/codexes-factory
uv run streamlit run src/codexes/codexes-factory-home-ui.py --server.port=8500

# Example: Run trillionsofpeople locally
cd xtuff/trillionsofpeople
uv run streamlit run src/trillions_of_people/web/app.py --server.port=8500
```

### 2. Make Changes & Test

- Edit code in your preferred editor
- Streamlit will auto-reload on file changes
- Test features at `http://localhost:8500`
- Check logs in terminal

### 3. Push to GitHub (Production Branch)

```bash
# After testing, commit your changes
git add .
git commit -m "feat: description of your changes"

# Push to lean-production branch (our clean production branch)
git push origin lean-production
```

### 4. Deploy to GCP Production Server

```bash
# Sync code to production server
./deploy_to_remote.sh

# SSH into production to restart services
ssh -i ~/.ssh/rare-shadow_ed25519 wfzimmerman@34.172.181.254

# On production server, restart specific service:
sudo systemctl restart codexes-factory.service
sudo systemctl restart trillionsofpeople.service
# etc.

# Or restart all services:
sudo systemctl restart 'app-*.service'
```

## Production Setup: Systemd Services

### Current Production Services (GCP Debian Server)

| Service | Port | Status | Command |
|---------|------|--------|---------|
| all_applications_runner | 8500 | ✅ | `systemctl status app-runner-master.service` |
| codexes-factory | 8502 | ✅ | `systemctl status codexes-factory.service` |
| trillionsofpeople | 8507 | ❓ | `systemctl status app-xtuff_ai-trillionsofpeople.service` |
| agentic_social_server | 8501 | ❓ | `systemctl status agentic_social_server.service` |
| xai_health_coach | 8506 | ❓ | `systemctl status xai_health_coach.service` |

### Service Management Commands

```bash
# Check service status
sudo systemctl status <service-name>

# Start/stop/restart service
sudo systemctl start <service-name>
sudo systemctl stop <service-name>
sudo systemctl restart <service-name>

# Enable service to start on boot
sudo systemctl enable <service-name>

# View service logs
sudo journalctl -u <service-name> -f

# View all app services
systemctl list-units 'app-*.service'
```

### Service File Locations

- **Local (for editing):** `/Users/fred/xcu_my_apps/systemd_services/`
- **Production:** `/etc/systemd/system/` (deployed via deploy_to_remote.sh)

## Multi-Agent Architecture

### Current Agent Structure

```
xcu_my_apps/
├── all_applications_runner/     # Master launcher (port 8500)
│   ├── main.py                  # Unified app launcher
│   └── apps_config.json         # App registry
│
├── nimble/
│   └── codexes-factory/         # AI publishing (port 8502)
│       └── src/codexes/
│
└── xtuff/
    ├── agentic_social_server/   # Social AI (port 8501)
    ├── personal-time-management/ # Daily Engine (port 8509)
    ├── trillionsofpeople/       # Persona generator (port 8507)
    └── xai_health/              # Health coach (port 8506)
```

### Running Multiple Agents Simultaneously

#### Option 1: Via Systemd (Production)
```bash
# All agents run independently as systemd services
# Each agent has its own port, logs, and process

# Start all agents:
sudo systemctl start app-runner-master.service
sudo systemctl start codexes-factory.service
sudo systemctl start agentic_social_server.service
sudo systemctl start trillionsofpeople.service
sudo systemctl start xai_health_coach.service
```

#### Option 2: Via Process Manager (Local Development)
```bash
# Use tmux or screen to run multiple agents locally

# Terminal 1: Master launcher
uv run streamlit run all_applications_runner/main.py --server.port=8500

# Terminal 2: Codexes Factory
cd nimble/codexes-factory && uv run streamlit run src/codexes/codexes-factory-home-ui.py --server.port=8502

# Terminal 3: Trillions of People
cd xtuff/trillionsofpeople && uv run streamlit run src/trillions_of_people/web/app.py --server.port=8507

# Terminal 4: Health Coach
cd xtuff/xai_health && uv run streamlit run src/xai_health/app.py --server.port=8506
```

#### Option 3: Using all_applications_runner

The `all_applications_runner` is designed to launch and manage multiple Streamlit apps:

```bash
# Edit apps_config.json to define which apps to run
vim all_applications_runner/apps_config.json

# Run the master launcher
cd all_applications_runner
uv run streamlit run main.py --server.port=8500

# It will provide links to all configured apps
```

## Agent Communication Patterns

### Shared Components

All agents can use shared infrastructure:

- **`shared/auth/`** - Unified authentication (SSO, Stripe)
- **`shared/ui/`** - Common UI components and sidebar
- **`shared/utils/`** - Shared utilities and helpers

### Example: Connecting Agents

```python
# In codexes-factory, call trillionsofpeople persona generator
import requests

response = requests.post(
    "http://localhost:8507/api/generate_persona",
    json={"country": "France", "year": 1789}
)
personas = response.json()
```

### Shared Database Access

```python
# All agents can access shared SQLite databases
from shared.utils.db import get_connection

conn = get_connection("/home/wfz/shared_data/app_data.db")
# Query shared data across agents
```

## Development Best Practices

### 1. Branch Strategy

- `lean-production` - Clean production-ready code (NO secrets, NO archives)
- `develop` - Integration branch for feature development
- `feature/*` - Individual feature branches

### 2. Secret Management

**Local Development:**
- Use `.env` files in each app directory
- Copy `.env.example` to `.env` and add your keys

**Production:**
- Secrets loaded via `EnvironmentFile` in systemd service files
- Each service references its own `.env` file:
  ```ini
  [Service]
  EnvironmentFile=-/home/wfz/codexes-factory/.env
  ```

### 3. Testing Before Deploy

```bash
# 1. Test locally
uv run streamlit run app.py --server.port=8500

# 2. Run tests (if available)
uv run pytest tests/

# 3. Check for secrets
git diff | grep -i "api_key\|secret\|password"

# 4. Commit and push
git commit -m "feat: ..."
git push origin lean-production

# 5. Deploy to production
./deploy_to_remote.sh
```

### 4. Monitoring Production

```bash
# SSH to production
ssh -i ~/.ssh/rare-shadow_ed25519 wfzimmerman@34.172.181.254

# Check all app services
systemctl list-units 'app-*.service' --all

# Monitor logs in real-time
sudo journalctl -u codexes-factory.service -f

# Check GCP load balancer health
curl -I http://xtuff.ai/health
```

## Common Workflows

### Add a New Feature to Codexes Factory

```bash
# 1. Start local development
cd /Users/fred/xcu_my_apps/nimble/codexes-factory
uv run streamlit run src/codexes/codexes-factory-home-ui.py --server.port=8500

# 2. Make changes, test locally

# 3. Commit changes
git add src/codexes/
git commit -m "feat(codexes): add new feature"

# 4. Push to GitHub
git push origin lean-production

# 5. Deploy to production
cd /Users/fred/xcu_my_apps
./deploy_to_remote.sh

# 6. Restart service on production
ssh wfzimmerman@34.172.181.254 'sudo systemctl restart codexes-factory.service'
```

### Debug Production Issue

```bash
# 1. Check service status
ssh wfzimmerman@34.172.181.254 'sudo systemctl status codexes-factory.service'

# 2. View recent logs
ssh wfzimmerman@34.172.181.254 'sudo journalctl -u codexes-factory.service -n 100'

# 3. Check application logs
ssh wfzimmerman@34.172.181.254 'tail -50 /home/wfz/codexes-factory/logs/codexes.log'

# 4. Restart service if needed
ssh wfzimmerman@34.172.181.254 'sudo systemctl restart codexes-factory.service'
```

### Add a New Agent/Application

```bash
# 1. Create app directory structure
mkdir -p xtuff/my_new_app/src/my_new_app

# 2. Create Streamlit app
# Edit xtuff/my_new_app/src/my_new_app/app.py

# 3. Create systemd service file
# Edit systemd_services/my-new-app.service

# 4. Register in all_applications_runner
# Edit all_applications_runner/apps_config.json

# 5. Test locally
cd xtuff/my_new_app
uv run streamlit run src/my_new_app/app.py --server.port=8510

# 6. Deploy
git add xtuff/my_new_app systemd_services/my-new-app.service
git commit -m "feat: add my_new_app"
git push origin lean-production
./deploy_to_remote.sh

# 7. Enable on production
ssh wfzimmerman@34.172.181.254 << 'EOF'
  sudo cp /home/wfz/xcu_my_apps/systemd_services/my-new-app.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable my-new-app.service
  sudo systemctl start my-new-app.service
EOF
```

## Useful Commands Reference

```bash
# Local Development
uv run streamlit run app.py --server.port=8500       # Run Streamlit app
uv run pytest tests/                                 # Run tests
uv sync                                              # Sync dependencies

# Git Operations
git status                                           # Check status
git add .                                            # Stage changes
git commit -m "feat: description"                    # Commit
git push origin lean-production                      # Push to production branch

# Deployment
./deploy_to_remote.sh                                # Deploy to GCP
ssh -i ~/.ssh/rare-shadow_ed25519 wfzimmerman@34.172.181.254  # SSH to production

# Systemd (on production server)
sudo systemctl status <service>                      # Check status
sudo systemctl restart <service>                     # Restart
sudo journalctl -u <service> -f                      # View logs
sudo systemctl list-units 'app-*.service'            # List all app services
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :8500

# Kill process
kill -9 <PID>
```

### Service Won't Start
```bash
# Check service status
sudo systemctl status <service>

# View detailed logs
sudo journalctl -u <service> -n 100 --no-pager

# Check service file syntax
sudo systemd-analyze verify /etc/systemd/system/<service>.service
```

### Push Rejected (Secrets Detected)
```bash
# Find and remove secrets
git diff | grep -i "api_key\|secret"

# Amend commit
git add .
git commit --amend --no-edit

# Force push (if needed)
git push origin lean-production --force
```

## Next Steps

1. ✅ Push lean-production branch to GitHub (in progress)
2. ⏳ Test all services on production server
3. ⏳ Configure GCP load balancer health checks
4. ⏳ Set up automated deployment pipeline (GitHub Actions)
5. ⏳ Add monitoring and alerting (Prometheus/Grafana)
