# All Applications Runner - Complete Deployment Guide

**Last Updated:** 2025-10-02
**Author:** Fred Zimmerman
**Purpose:** Deploy the unified app runner on a fresh Debian server

## Overview

The All Applications Runner is a unified Streamlit-based dashboard that manages and provides access to multiple web applications across different organizations (xtuff.ai, Nimble Books LLC, personal sites). It provides:

- Master dashboard at port 8500
- Process management and health monitoring
- Authentication integration
- Apache reverse proxy configuration
- Systemd service management

## Architecture Summary

### Organizations & Apps

**xtuff.ai** (AI Innovation)
- Daily Engine (8509) - dailyengine.xtuff.ai
- Social Xtuff (8501) - social.xtuff.ai
- Text-to-Feed API (59312) - api.xtuff.ai
- Collectiverse (8503) - collectiverse.xtuff.ai
- TrillionsOfPeople.Info (8504) - trillionsofpeople.info
- altDOGE (8505) - altdoge.xtuff.ai

**Nimble Books LLC** (Publishing)
- Codexes Factory (8502) - codexes.nimblebooks.com
- Max Bialystok (8506) - maxb.nimblebooks.com

**Personal**
- Resume & Contact (8508) - fredzannarbor.com

**Master Dashboard**
- Main runner (8500) - xtuff.ai (main domain)

## Prerequisites

### Server Requirements

- Debian 12 or Ubuntu 22.04+
- 4GB RAM minimum (8GB recommended)
- 20GB disk space
- Root or sudo access
- Static IP address with domain names configured

### Required Software

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.12
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa  # Ubuntu
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Install Apache and tools
sudo apt install -y apache2 git curl wget

# Install UV (modern Python package manager) - optional but recommended
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Verify installations
python3.12 --version
apache2 -v
git --version
```

### User Setup

```bash
# Create user 'wfz' if doesn't exist (or use your preferred user)
sudo adduser wfz
sudo usermod -aG sudo wfz

# Switch to user
su - wfz
```

## Step 1: Obtain Source Code

### Option A: Transfer from Local Machine

On your **local machine** (macOS):

```bash
cd /Users/fred/bin/all_applications_runner

# Create deployment package
tar czf app-runner.tar.gz \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='*.pyc' \
  --exclude='.DS_Store' \
  --exclude='.idea' \
  .

# Transfer to server (replace with your server address)
scp app-runner.tar.gz wfz@YOUR_SERVER_IP:/home/wfz/
```

On your **Debian server**:

```bash
cd /home/wfz
mkdir -p all_applications_runner
cd all_applications_runner
tar xzf ../app-runner.tar.gz
rm ../app-runner.tar.gz
```

### Option B: Clone from Git (if repo exists)

```bash
cd /home/wfz
git clone <repository-url> all_applications_runner
cd all_applications_runner
```

## Step 2: Deploy Application Repositories

Each app needs its repository on the server. Adjust paths based on your setup:

```bash
cd /home/wfz

# Clone or transfer each application
# Daily Engine
git clone <daily-engine-repo> personal-time-management

# Agentic Social Server
git clone <social-repo> agentic_social_server

# Collectiverse
git clone <collectiverse-repo> collectiverse

# TrillionsOfPeople
git clone <trillions-repo> trillionsofpeople

# altDOGE
git clone <altdoge-repo> altDOGE

# Codexes Factory
git clone <codexes-repo> codexes-factory

# Resume site
git clone <resume-repo> resume-site
```

## Step 3: Configure apps_config.json

Update the configuration file with correct server paths:

```bash
cd /home/wfz/all_applications_runner

# Backup original
cp apps_config.json apps_config.json.original

# Edit configuration
nano apps_config.json
```

Update all paths from `/Users/fred/my-organizations/...` to `/home/wfz/...`:

```json
{
  "organizations": {
    "xtuff_ai": {
      "name": "xtuff.ai",
      "apps": {
        "personal_time_management": {
          "name": "Daily Engine",
          "port": 8509,
          "path": "/home/wfz/personal-time-management",
          "entry": "daily_engine.py",
          "startup_command": "uv run streamlit run daily_engine.py --server.port=8509",
          "domain_name": "dailyengine.xtuff.ai"
        },
        "agentic_social_server": {
          "name": "Social Xtuff",
          "port": 8501,
          "path": "/home/wfz/agentic_social_server",
          "entry": "app.py",
          "startup_command": "uv run python app.py",
          "domain_name": "social.xtuff.ai"
        }
        // ... etc for all apps
      }
    }
  },
  "global_settings": {
    "auth_service_url": "http://localhost:8502/auth",
    "master_port": 8500,
    "health_check_interval": 120,
    "auto_restart": false,
    "production_domain": "xtuff.ai"
  }
}
```

**Quick path replacement:**

```bash
# Automated path replacement
sed -i 's|/Users/fred/my-organizations/xtuff/agentic_social_server|/home/wfz/agentic_social_server|g' apps_config.json
sed -i 's|/Users/fred/my-organizations/altDOGE|/home/wfz/altDOGE|g' apps_config.json
sed -i 's|/Users/fred/my-organizations/trillionsofpeople|/home/wfz/trillionsofpeople|g' apps_config.json
sed -i 's|/Users/fred/my-organizations/nimble/repos/codexes-factory|/home/wfz/codexes-factory|g' apps_config.json
sed -i 's|/Users/fred/my-organizations/personal-time-management|/home/wfz/personal-time-management|g' apps_config.json
sed -i 's|/Users/fred/my-organizations/personal/resume-site|/home/wfz/resume-site|g' apps_config.json
sed -i 's|/Users/fred/my-organizations/xtuff/collectiverse|/home/wfz/collectiverse|g' apps_config.json
```

## Step 4: Setup Environment Variables

```bash
cd /home/wfz/all_applications_runner

# Create .env file
cat > .env << 'EOF'
# LLM API Keys (if needed)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Stripe (if using payments)
STRIPE_SECRET_KEY=your_stripe_key_here
STRIPE_PUBLISHABLE_KEY=your_stripe_pub_key_here

# Environment
ENVIRONMENT=production

# Logging
LOG_LEVEL=INFO
EOF

# Secure the file
chmod 600 .env
```

## Step 5: Run Deployment Script

The repository includes a deployment script that automates setup:

```bash
cd /home/wfz/all_applications_runner
chmod +x deployment/deploy.sh
./deployment/deploy.sh
```

This script will:
1. ✓ Update apps_config.json paths
2. ✓ Create Python virtual environment
3. ✓ Install dependencies
4. ✓ Create log directory
5. ✓ Install systemd service
6. ✓ Install Apache VirtualHosts
7. ✓ Enable Apache modules
8. ✓ Start the service

### Manual Installation (if script unavailable)

If deployment script is missing, perform these steps manually:

#### Create Virtual Environment

```bash
cd /home/wfz/all_applications_runner
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**requirements.txt contents:**
```
streamlit>=1.28.0
requests>=2.31.0
psutil>=5.9.0
pydantic>=2.0.0
stripe>=6.0.0
python-dotenv>=1.0.0
```

#### Create Systemd Service

```bash
sudo nano /etc/systemd/system/all-apps-runner.service
```

```ini
[Unit]
Description=xtuff.ai All Applications Runner
After=network.target apache2.service

[Service]
Type=simple
User=wfz
Group=wfz
WorkingDirectory=/home/wfz/all_applications_runner
Environment="PATH=/home/wfz/all_applications_runner/.venv/bin"
ExecStart=/home/wfz/all_applications_runner/.venv/bin/streamlit run main.py --server.port=8500 --server.address=127.0.0.1
Restart=always
RestartSec=10
StandardOutput=append:/home/wfz/all_applications_runner/logs/runner.log
StandardError=append:/home/wfz/all_applications_runner/logs/runner-error.log

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable all-apps-runner.service
sudo systemctl start all-apps-runner.service
sudo systemctl status all-apps-runner.service
```

## Step 6: Configure Apache Reverse Proxy

### Enable Required Modules

```bash
sudo a2enmod proxy proxy_http proxy_wstunnel rewrite headers ssl
sudo systemctl restart apache2
```

### Create VirtualHost Configuration

Create main xtuff.ai configuration:

```bash
sudo nano /etc/apache2/sites-available/xtuff-ai-runner.conf
```

```apache
<VirtualHost *:80>
    ServerName xtuff.ai
    ServerAlias www.xtuff.ai

    # Redirect to HTTPS (after SSL setup)
    # RewriteEngine On
    # RewriteCond %{HTTPS} off
    # RewriteRule ^(.*)$ https://%{HTTP_HOST}$1 [R=301,L]

    # Proxy to master dashboard
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8500/
    ProxyPassReverse / http://127.0.0.1:8500/

    # WebSocket support for Streamlit
    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} =websocket [NC]
    RewriteRule /(.*)           ws://127.0.0.1:8500/$1 [P,L]
    RewriteCond %{HTTP:Upgrade} !=websocket [NC]
    RewriteRule /(.*)           http://127.0.0.1:8500/$1 [P,L]

    ErrorLog ${APACHE_LOG_DIR}/xtuff-ai-error.log
    CustomLog ${APACHE_LOG_DIR}/xtuff-ai-access.log combined
</VirtualHost>
```

Create subdomain configurations:

```bash
sudo nano /etc/apache2/sites-available/all-apps-vhosts.conf
```

```apache
# Daily Engine
<VirtualHost *:80>
    ServerName dailyengine.xtuff.ai
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8509/
    ProxyPassReverse / http://127.0.0.1:8509/

    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} =websocket [NC]
    RewriteRule /(.*)           ws://127.0.0.1:8509/$1 [P,L]

    ErrorLog ${APACHE_LOG_DIR}/dailyengine-error.log
    CustomLog ${APACHE_LOG_DIR}/dailyengine-access.log combined
</VirtualHost>

# Social Xtuff
<VirtualHost *:80>
    ServerName social.xtuff.ai
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8501/
    ProxyPassReverse / http://127.0.0.1:8501/

    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} =websocket [NC]
    RewriteRule /(.*)           ws://127.0.0.1:8501/$1 [P,L]

    ErrorLog ${APACHE_LOG_DIR}/social-error.log
    CustomLog ${APACHE_LOG_DIR}/social-access.log combined
</VirtualHost>

# Collectiverse
<VirtualHost *:80>
    ServerName collectiverse.xtuff.ai
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8503/
    ProxyPassReverse / http://127.0.0.1:8503/

    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} =websocket [NC]
    RewriteRule /(.*)           ws://127.0.0.1:8503/$1 [P,L]

    ErrorLog ${APACHE_LOG_DIR}/collectiverse-error.log
    CustomLog ${APACHE_LOG_DIR}/collectiverse-access.log combined
</VirtualHost>

# TrillionsOfPeople.Info
<VirtualHost *:80>
    ServerName trillionsofpeople.info
    ServerAlias www.trillionsofpeople.info
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8504/
    ProxyPassReverse / http://127.0.0.1:8504/

    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} =websocket [NC]
    RewriteRule /(.*)           ws://127.0.0.1:8504/$1 [P,L]

    ErrorLog ${APACHE_LOG_DIR}/trillions-error.log
    CustomLog ${APACHE_LOG_DIR}/trillions-access.log combined
</VirtualHost>

# altDOGE
<VirtualHost *:80>
    ServerName altdoge.xtuff.ai
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8505/
    ProxyPassReverse / http://127.0.0.1:8505/

    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} =websocket [NC]
    RewriteRule /(.*)           ws://127.0.0.1:8505/$1 [P,L]

    ErrorLog ${APACHE_LOG_DIR}/altdoge-error.log
    CustomLog ${APACHE_LOG_DIR}/altdoge-access.log combined
</VirtualHost>

# Codexes Factory
<VirtualHost *:80>
    ServerName codexes.nimblebooks.com
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8502/
    ProxyPassReverse / http://127.0.0.1:8502/

    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} =websocket [NC]
    RewriteRule /(.*)           ws://127.0.0.1:8502/$1 [P,L]

    ErrorLog ${APACHE_LOG_DIR}/codexes-error.log
    CustomLog ${APACHE_LOG_DIR}/codexes-access.log combined
</VirtualHost>

# FredZannarbor.com
<VirtualHost *:80>
    ServerName fredzannarbor.com
    ServerAlias www.fredzannarbor.com
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8508/
    ProxyPassReverse / http://127.0.0.1:8508/

    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} =websocket [NC]
    RewriteRule /(.*)           ws://127.0.0.1:8508/$1 [P,L]

    ErrorLog ${APACHE_LOG_DIR}/resume-error.log
    CustomLog ${APACHE_LOG_DIR}/resume-access.log combined
</VirtualHost>
```

### Enable Sites

```bash
sudo a2ensite xtuff-ai-runner.conf
sudo a2ensite all-apps-vhosts.conf

# Test configuration
sudo apache2ctl configtest

# Reload Apache
sudo systemctl reload apache2
```

## Step 7: DNS Configuration

Update DNS records at your domain registrar:

### A Records (replace YOUR_SERVER_IP with actual IP)

```
xtuff.ai                  → YOUR_SERVER_IP
*.xtuff.ai                → YOUR_SERVER_IP
trillionsofpeople.info    → YOUR_SERVER_IP
www.trillionsofpeople.info → YOUR_SERVER_IP
codexes.nimblebooks.com   → YOUR_SERVER_IP
fredzannarbor.com         → YOUR_SERVER_IP
www.fredzannarbor.com     → YOUR_SERVER_IP
```

Wait 5-60 minutes for DNS propagation. Verify:

```bash
dig xtuff.ai +short
dig dailyengine.xtuff.ai +short
dig trillionsofpeople.info +short
```

## Step 8: SSL Certificate Setup

Install Certbot:

```bash
sudo apt install -y certbot python3-certbot-apache
```

Obtain certificates for each domain:

```bash
# Main xtuff.ai domain
sudo certbot --apache -d xtuff.ai -d www.xtuff.ai

# Subdomains
sudo certbot --apache -d dailyengine.xtuff.ai
sudo certbot --apache -d social.xtuff.ai
sudo certbot --apache -d collectiverse.xtuff.ai
sudo certbot --apache -d altdoge.xtuff.ai

# Other domains
sudo certbot --apache -d trillionsofpeople.info -d www.trillionsofpeople.info
sudo certbot --apache -d codexes.nimblebooks.com
sudo certbot --apache -d fredzannarbor.com -d www.fredzannarbor.com

# Verify auto-renewal
sudo certbot renew --dry-run
```

Certbot automatically updates VirtualHost files to redirect HTTP to HTTPS.

## Step 9: Firewall Configuration

```bash
# Check firewall status
sudo ufw status

# Allow necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# Enable firewall (if not already)
sudo ufw enable

# Verify
sudo ufw status verbose
```

**Important:** Application ports (8500-8509) should NOT be exposed directly. They're accessed only via Apache reverse proxy on 127.0.0.1.

## Step 10: Verification & Testing

### Check Service Status

```bash
# Check app runner service
sudo systemctl status all-apps-runner.service

# View logs
tail -f /home/wfz/all_applications_runner/logs/runner.log
tail -f /home/wfz/all_applications_runner/logs/runner-error.log

# Check systemd logs
sudo journalctl -u all-apps-runner.service -n 100 -f
```

### Check Listening Ports

```bash
# Verify all apps are listening
sudo netstat -tlnp | grep -E '(8500|8501|8502|8503|8504|8505|8508|8509)'

# Expected output: Each port should show LISTEN with python/streamlit process
```

### Test Domains

```bash
# Test HTTP status for each domain
curl -I https://xtuff.ai
curl -I https://dailyengine.xtuff.ai
curl -I https://social.xtuff.ai
curl -I https://collectiverse.xtuff.ai
curl -I https://trillionsofpeople.info
curl -I https://altdoge.xtuff.ai
curl -I https://codexes.nimblebooks.com
curl -I https://fredzannarbor.com

# All should return: HTTP/2 200
```

### Browser Testing

Access each domain in a browser:
- https://xtuff.ai - Should show master dashboard
- https://dailyengine.xtuff.ai - Daily Engine app
- https://social.xtuff.ai - Social Xtuff app
- https://collectiverse.xtuff.ai - Collectiverse
- https://trillionsofpeople.info - TrillionsOfPeople
- https://altdoge.xtuff.ai - altDOGE
- https://codexes.nimblebooks.com - Codexes Factory
- https://fredzannarbor.com - Resume site

## Management & Operations

### Service Control

```bash
# Start
sudo systemctl start all-apps-runner.service

# Stop
sudo systemctl stop all-apps-runner.service

# Restart
sudo systemctl restart all-apps-runner.service

# Status
sudo systemctl status all-apps-runner.service

# Enable on boot
sudo systemctl enable all-apps-runner.service

# Disable on boot
sudo systemctl disable all-apps-runner.service
```

### Log Monitoring

```bash
# Application logs
tail -f /home/wfz/all_applications_runner/logs/runner.log
tail -f /home/wfz/all_applications_runner/logs/runner-error.log

# Systemd logs
sudo journalctl -u all-apps-runner.service -f

# Apache logs
sudo tail -f /var/log/apache2/xtuff-ai-error.log
sudo tail -f /var/log/apache2/xtuff-ai-access.log
```

### Process Management

Using the built-in process manager:

```bash
cd /home/wfz/all_applications_runner
source .venv/bin/activate

# Check status
python3 process_manager.py --action status

# Start all apps
python3 process_manager.py --action start

# Stop all apps
python3 process_manager.py --action stop

# Complete shutdown (prevents auto-restart)
python3 process_manager.py --action shutdown

# Manage specific app
python3 process_manager.py --app xtuff_ai.agentic_social_server --action restart
```

### Updating the Application

```bash
# On local machine - create deployment package
cd /Users/fred/bin/all_applications_runner
tar czf app-runner.tar.gz \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='*.pyc' \
  --exclude='.DS_Store' \
  .

# Transfer to server
scp app-runner.tar.gz wfz@YOUR_SERVER_IP:/home/wfz/

# On server
cd /home/wfz/all_applications_runner
sudo systemctl stop all-apps-runner.service

# Backup current config
cp apps_config.json apps_config.json.backup
cp .env .env.backup

# Extract update
tar xzf ~/app-runner.tar.gz

# Restore config if needed
cp apps_config.json.backup apps_config.json
cp .env.backup .env

# Update dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Restart
sudo systemctl start all-apps-runner.service
```

## Troubleshooting

### Service Won't Start

```bash
# Check detailed logs
sudo journalctl -u all-apps-runner.service -n 100 --no-pager

# Check if port 8500 is in use
sudo netstat -tlnp | grep 8500

# Test manual start
cd /home/wfz/all_applications_runner
source .venv/bin/activate
streamlit run main.py --server.port=8500
```

### Apache Proxy Issues

```bash
# Test configuration
sudo apache2ctl configtest

# Check enabled modules
sudo apache2ctl -M | grep proxy

# View error logs
sudo tail -f /var/log/apache2/error.log

# Reload Apache
sudo systemctl reload apache2
```

### SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Renew certificates
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal

# Test renewal
sudo certbot renew --dry-run
```

### Individual App Won't Start

```bash
# Check app directory exists
ls -la /home/wfz/agentic_social_server

# Verify dependencies in app directory
cd /home/wfz/agentic_social_server
source .venv/bin/activate  # if app has its own venv
pip list

# Check apps_config.json paths
cd /home/wfz/all_applications_runner
cat apps_config.json | grep "path"

# Test starting app manually
cd /home/wfz/agentic_social_server
uv run python app.py  # or appropriate command
```

### Port Conflicts

```bash
# Find what's using a port
sudo lsof -i :8501

# Kill process on port
sudo kill <PID>

# Or use fuser
sudo fuser -k 8501/tcp
```

### DNS Not Resolving

```bash
# Check DNS propagation
dig xtuff.ai +short
nslookup xtuff.ai

# Test from different DNS
dig @8.8.8.8 xtuff.ai +short

# Clear local DNS cache
sudo systemd-resolve --flush-caches
```

## Performance Monitoring

### Resource Usage

```bash
# CPU and memory by user
top -u wfz
htop -u wfz

# Disk usage
df -h
du -sh /home/wfz/all_applications_runner

# Memory
free -h

# Connection count
sudo netstat -an | grep -E '(8500|8501|8502|8503|8504|8505|8508|8509)' | wc -l
```

### System Monitoring

```bash
# Setup monitoring script
cat > /home/wfz/monitor-apps.sh << 'EOF'
#!/bin/bash
echo "=== App Runner Status ==="
sudo systemctl status all-apps-runner.service --no-pager
echo ""
echo "=== Listening Ports ==="
sudo netstat -tlnp | grep -E '(8500|8501|8502|8503|8504|8505|8508|8509)'
echo ""
echo "=== Resource Usage ==="
ps aux | grep -E '(streamlit|python)' | grep -v grep
echo ""
echo "=== Disk Space ==="
df -h /home/wfz
EOF

chmod +x /home/wfz/monitor-apps.sh
./monitor-apps.sh
```

## Backup & Recovery

### Backup Script

```bash
cat > /home/wfz/backup-apps.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/wfz/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup app runner config
cd /home/wfz/all_applications_runner
tar czf $BACKUP_DIR/app-runner-config-$DATE.tar.gz \
  apps_config.json \
  .env \
  deployment/

# Keep only last 7 backups
cd $BACKUP_DIR
ls -t | tail -n +8 | xargs -r rm

echo "Backup completed: app-runner-config-$DATE.tar.gz"
EOF

chmod +x /home/wfz/backup-apps.sh
```

### Setup Automated Backups

```bash
# Add to crontab
crontab -e

# Add line (daily backup at 2 AM):
0 2 * * * /home/wfz/backup-apps.sh
```

### Restore from Backup

```bash
cd /home/wfz/all_applications_runner
sudo systemctl stop all-apps-runner.service

# Restore config
tar xzf /home/wfz/backups/app-runner-config-YYYYMMDD_HHMMSS.tar.gz

sudo systemctl start all-apps-runner.service
```

## Security Considerations

### File Permissions

```bash
# Ensure proper ownership
sudo chown -R wfz:wfz /home/wfz/all_applications_runner

# Secure .env file
chmod 600 /home/wfz/all_applications_runner/.env

# Secure logs
chmod 700 /home/wfz/all_applications_runner/logs
```

### SSH Hardening

```bash
# Disable root login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no

# Use key-based authentication
# Disable password authentication
# Set: PasswordAuthentication no

sudo systemctl restart sshd
```

### Keep System Updated

```bash
# Regular updates
sudo apt update && sudo apt upgrade -y

# Security updates only
sudo apt update && sudo apt upgrade --security -y

# Setup automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Success Checklist

- [ ] All prerequisites installed (Python 3.12, Apache, Git)
- [ ] User 'wfz' created with sudo access
- [ ] All application repositories cloned to /home/wfz/
- [ ] apps_config.json updated with correct paths
- [ ] .env file configured with API keys
- [ ] Virtual environment created and dependencies installed
- [ ] Systemd service installed and enabled
- [ ] Apache VirtualHosts configured
- [ ] Apache modules enabled (proxy, ssl, rewrite)
- [ ] DNS records configured and propagated
- [ ] SSL certificates obtained for all domains
- [ ] Firewall configured (80, 443, 22 allowed)
- [ ] Service running: `systemctl status all-apps-runner.service`
- [ ] All ports listening: `netstat -tlnp | grep 850X`
- [ ] All domains accessible via HTTPS
- [ ] Master dashboard shows all apps
- [ ] Individual apps launch from dashboard
- [ ] Logs being written correctly
- [ ] Backup script configured

## Quick Reference Commands

```bash
# Service management
sudo systemctl {start|stop|restart|status} all-apps-runner.service

# View logs
tail -f /home/wfz/all_applications_runner/logs/runner.log
sudo journalctl -u all-apps-runner.service -f

# Apache
sudo apache2ctl configtest
sudo systemctl reload apache2
sudo tail -f /var/log/apache2/xtuff-ai-error.log

# SSL
sudo certbot certificates
sudo certbot renew

# Monitoring
sudo netstat -tlnp | grep 850
top -u wfz
df -h
```

## Support & Contact

For issues and support:
- Email: fred@fredzannarbor.com
- Documentation: /home/wfz/all_applications_runner/README.md
- Logs: /home/wfz/all_applications_runner/logs/

## Changelog

- 2025-10-02: Initial comprehensive deployment guide created
