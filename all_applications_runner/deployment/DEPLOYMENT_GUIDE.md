# xtuff.ai All Applications Runner - Deployment Guide

## Prerequisites

### On Your Local Machine
1. Ensure all changes are committed
2. Test the application locally at http://localhost:8500
3. Verify all apps in apps_config.json have correct settings

### On Debian Server (book-publisher-agi)
- Python 3.12 installed
- Apache2 installed and running
- User: wfz with sudo privileges
- All individual app directories exist in /home/wfz/

## Step-by-Step Deployment

### 1. Prepare Local Files

```bash
# From ~/bin/all_applications_runner/
cd ~/bin/all_applications_runner

# Create deployment package (excluding unnecessary files)
tar czf app-runner.tar.gz \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='*.pyc' \
  --exclude='.DS_Store' \
  .
```

### 2. Transfer to Server

```bash
# Copy deployment package
scp app-runner.tar.gz wfzimmerman@book-publisher-agi:/home/wfz/

# SSH into server
ssh wfzimmerman@book-publisher-agi
```

### 3. Extract and Setup on Server

```bash
# On server as wfz
cd /home/wfz

# Create directory
mkdir -p all_applications_runner
cd all_applications_runner

# Extract files
tar xzf ~/app-runner.tar.gz
rm ~/app-runner.tar.gz

# Make deploy script executable
chmod +x deployment/deploy.sh
```

### 4. Update Apps Config for Server Paths

The deploy.sh script will automatically update paths, but verify:

```bash
# Check that all paths point to /home/wfz/ instead of /Users/fred/
grep -n "Users/fred" apps_config.json

# If any found, manually update or run:
nano apps_config.json
```

Required path mappings:
- Daily Engine: `/home/wfz/personal-time-management` (create if missing)
- Social Xtuff: `/home/wfz/agentic_social_server`
- Collectiverse: `/home/wfz/collectiverse` (create if missing)
- TrillionsOfPeople: `/home/wfz/trillionsofpeople`
- altDOGE: `/home/wfz/altDOGE`
- Codexes Factory: `/home/wfz/codexes-factory`
- Resume: `/home/wfz/resume-site` (create if missing)

### 5. Run Deployment Script

```bash
cd /home/wfz/all_applications_runner
./deployment/deploy.sh
```

This script will:
- Update apps_config.json paths
- Create Python virtual environment
- Install dependencies
- Install systemd service
- Configure Apache VirtualHosts
- Start the service

### 6. DNS Configuration

Update DNS records (via your domain registrar):

**A Records:**
- `xtuff.ai` → Your server IP
- `*.xtuff.ai` → Your server IP (wildcard for subdomains)
- `trillionsofpeople.info` → Your server IP
- `www.trillionsofpeople.info` → Your server IP
- `codexes.nimblebooks.com` → Your server IP
- `fredzannarbor.com` → Your server IP
- `www.fredzannarbor.com` → Your server IP

Wait for DNS propagation (5-60 minutes typically).

### 7. SSL Certificate Installation

```bash
# Install certbot if not already installed
sudo apt update
sudo apt install -y certbot python3-certbot-apache

# Get certificates for all domains
sudo certbot --apache -d xtuff.ai -d www.xtuff.ai
sudo certbot --apache -d dailyengine.xtuff.ai
sudo certbot --apache -d social.xtuff.ai
sudo certbot --apache -d collectiverse.xtuff.ai
sudo certbot --apache -d trillionsofpeople.info -d www.trillionsofpeople.info
sudo certbot --apache -d altdoge.xtuff.ai
sudo certbot --apache -d codexes.nimblebooks.com
sudo certbot --apache -d fredzannarbor.com -d www.fredzannarbor.com

# Verify auto-renewal is configured
sudo certbot renew --dry-run
```

### 8. Verification

Test each domain:

```bash
# From any machine
curl -I https://xtuff.ai
curl -I https://dailyengine.xtuff.ai
curl -I https://social.xtuff.ai
curl -I https://collectiverse.xtuff.ai
curl -I https://trillionsofpeople.info
curl -I https://altdoge.xtuff.ai
curl -I https://codexes.nimblebooks.com
curl -I https://fredzannarbor.com
```

Expected: HTTP 200 status codes

### 9. Monitor and Troubleshoot

```bash
# Check service status
sudo systemctl status all-apps-runner.service

# View application logs
tail -f /home/wfz/all_applications_runner/logs/runner.log
tail -f /home/wfz/all_applications_runner/logs/runner-error.log

# View systemd logs
sudo journalctl -u all-apps-runner.service -f

# Check Apache logs
sudo tail -f /var/log/apache2/xtuff-ai-error.log
sudo tail -f /var/log/apache2/xtuff-ai-access.log

# Check if ports are listening
sudo netstat -tlnp | grep -E '(8500|8501|8502|8503|8504|8505|8508|8509)'
```

## Managing the Service

```bash
# Start
sudo systemctl start all-apps-runner.service

# Stop
sudo systemctl stop all-apps-runner.service

# Restart
sudo systemctl restart all-apps-runner.service

# View status
sudo systemctl status all-apps-runner.service

# Enable on boot (already done by deploy.sh)
sudo systemctl enable all-apps-runner.service

# Disable on boot
sudo systemctl disable all-apps-runner.service
```

## Updating the Application

```bash
# On local machine - create new deployment package
cd ~/bin/all_applications_runner
tar czf app-runner.tar.gz \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='*.pyc' \
  --exclude='.DS_Store' \
  .

# Copy to server
scp app-runner.tar.gz wfzimmerman@book-publisher-agi:/home/wfz/

# On server
cd /home/wfz/all_applications_runner
sudo systemctl stop all-apps-runner.service

# Backup current version
cp apps_config.json apps_config.json.backup
cp .env .env.backup

# Extract new version
tar xzf ~/app-runner.tar.gz

# Restore config files if needed
cp apps_config.json.backup apps_config.json
cp .env.backup .env

# Update dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl start all-apps-runner.service
```

## Firewall Configuration

```bash
# If using ufw
sudo ufw status

# Ensure these are allowed:
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 22/tcp    # SSH

# Application ports should NOT be exposed directly
# They're accessed only via Apache reverse proxy on 127.0.0.1
```

## Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u all-apps-runner.service -n 100

# Check if port 8500 is already in use
sudo netstat -tlnp | grep 8500

# Test streamlit manually
cd /home/wfz/all_applications_runner
source .venv/bin/activate
streamlit run main.py --server.port=8500
```

### Apache issues
```bash
# Test config
sudo apache2ctl configtest

# Check if modules are enabled
sudo apache2ctl -M | grep proxy

# Reload Apache
sudo systemctl reload apache2
```

### SSL certificate issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificates manually
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal
```

### App-specific issues
```bash
# Check if individual apps' directories exist
ls -la /home/wfz/agentic_social_server
ls -la /home/wfz/codexes-factory
# etc.

# Verify apps_config.json paths
cat apps_config.json | grep "path"

# Test process manager
cd /home/wfz/all_applications_runner
source .venv/bin/activate
python3 -c "from process_manager import ProcessManager; pm = ProcessManager(); pm.initialize_processes(); print(pm.get_status())"
```

## Performance Monitoring

```bash
# Check resource usage
top -u wfz
htop -u wfz

# Check disk usage
df -h
du -sh /home/wfz/all_applications_runner

# Check memory usage
free -h

# Monitor connections
sudo netstat -an | grep -E '(8500|8501|8502|8503|8504|8505|8508|8509)' | wc -l
```

## Backup Strategy

```bash
# Backup script (add to cron)
#!/bin/bash
BACKUP_DIR="/home/wfz/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

cd /home/wfz/all_applications_runner
tar czf $BACKUP_DIR/app-runner-$DATE.tar.gz \
  --exclude='.venv' \
  --exclude='logs/*.log' \
  .

# Keep only last 7 backups
cd $BACKUP_DIR
ls -t | tail -n +8 | xargs -r rm
```

## Success Criteria

- [ ] All 8 domains accessible via HTTPS
- [ ] Main app runner (xtuff.ai) shows app dashboard
- [ ] Each individual app launches from dashboard
- [ ] SSL certificates valid and auto-renewing
- [ ] Service starts automatically on boot
- [ ] Logs being written correctly
- [ ] Health checks running (check every 120 seconds)
- [ ] No errors in Apache logs
- [ ] No errors in systemd logs
