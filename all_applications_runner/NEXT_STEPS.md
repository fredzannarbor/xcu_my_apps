# All Applications Runner - Next Deployment Steps

**Date:** 2025-10-03
**Status:** Setup Complete - Ready for Apache Installation and Service Activation

## ✅ Completed Steps

1. **Prerequisites Verified**
   - Python 3.12.2 installed
   - Git 2.30.2 installed
   - UV package manager installed
   - User `wfzimmerman` has sudo access

2. **Application Files**
   - All files transferred to `/home/wfz/bin/all_applications_runner/`
   - Main files: main.py, process_manager.py, apps_config.json

3. **Configuration Updated**
   - `apps_config.json` paths updated for server directories
   - Backup created: `apps_config.json.backup.20251003_HHMMSS`
   - `.env` file backed up: `.env.backup.20251003_HHMMSS`
   - Production domain set to: `xtuff.ai`

4. **Virtual Environment**
   - Created at `/home/wfz/bin/all_applications_runner/.venv`
   - All dependencies installed (44 packages)

5. **Service Files Prepared**
   - Systemd service: `deployment/all-apps-runner.service` (updated paths)
   - Apache configs ready: `deployment/xtuff-ai-runner.conf` and `deployment/all-apps-vhosts.conf`

6. **Logs Directory**
   - Created at `/home/wfz/bin/all_applications_runner/logs/`

## 🔧 Required Next Steps

### Step 1: Install Apache2

```bash
sudo apt update
sudo apt install -y apache2
sudo systemctl enable apache2
sudo systemctl start apache2
apache2 -v  # Verify installation
```

### Step 2: Enable Apache Modules

```bash
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod proxy_wstunnel
sudo a2enmod rewrite
sudo a2enmod headers
sudo a2enmod ssl
sudo systemctl restart apache2
```

Verify modules:
```bash
sudo apache2ctl -M | grep -E '(proxy|rewrite|headers|ssl)'
```

### Step 3: Install Systemd Service

```bash
sudo cp /home/wfz/bin/all_applications_runner/deployment/all-apps-runner.service \
  /etc/systemd/system/all-apps-runner.service

sudo systemctl daemon-reload
sudo systemctl enable all-apps-runner.service
```

**⚠️ DO NOT START YET** - Start after Apache is configured

### Step 4: Install Apache VirtualHosts

```bash
# Main xtuff.ai domain
sudo cp /home/wfz/bin/all_applications_runner/deployment/xtuff-ai-runner.conf \
  /etc/apache2/sites-available/xtuff-ai-runner.conf

# Individual app subdomains
sudo cp /home/wfz/bin/all_applications_runner/deployment/all-apps-vhosts.conf \
  /etc/apache2/sites-available/all-apps-vhosts.conf

# Test configuration
sudo apache2ctl configtest
```

Expected output: `Syntax OK`

### Step 5: Enable Sites

```bash
sudo a2ensite xtuff-ai-runner.conf
sudo a2ensite all-apps-vhosts.conf
sudo systemctl reload apache2
```

### Step 6: Configure Firewall

```bash
# Check current status
sudo ufw status

# Allow necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# Enable firewall (if not already enabled)
sudo ufw enable

# Verify
sudo ufw status verbose
```

### Step 7: Start the Application Runner Service

```bash
sudo systemctl start all-apps-runner.service
sudo systemctl status all-apps-runner.service
```

Check logs:
```bash
tail -f /home/wfz/bin/all_applications_runner/logs/runner.log
tail -f /home/wfz/bin/all_applications_runner/logs/runner-error.log
```

### Step 8: Verify Application is Running

```bash
# Check if port 8500 is listening
sudo netstat -tlnp | grep 8500

# Test locally
curl -I http://127.0.0.1:8500
```

Expected: HTTP response headers

### Step 9: DNS Configuration

Update DNS records at your domain registrar to point to this server's IP:

**A Records needed:**
```
xtuff.ai                  → YOUR_SERVER_IP
*.xtuff.ai                → YOUR_SERVER_IP
trillionsofpeople.info    → YOUR_SERVER_IP
www.trillionsofpeople.info → YOUR_SERVER_IP
codexes.nimblebooks.com   → YOUR_SERVER_IP
fredzannarbor.com         → YOUR_SERVER_IP
www.fredzannarbor.com     → YOUR_SERVER_IP
```

Verify DNS propagation:
```bash
dig xtuff.ai +short
dig dailyengine.xtuff.ai +short
```

Wait 5-60 minutes for DNS propagation.

### Step 10: SSL Certificates with Let's Encrypt

**After DNS is propagated**, install SSL certificates:

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-apache

# Obtain certificates for main domain
sudo certbot --apache -d xtuff.ai -d www.xtuff.ai

# Obtain certificates for subdomains
sudo certbot --apache -d dailyengine.xtuff.ai
sudo certbot --apache -d social.xtuff.ai
sudo certbot --apache -d collectiverse.xtuff.ai
sudo certbot --apache -d altdoge.xtuff.ai

# Other domains
sudo certbot --apache -d trillionsofpeople.info -d www.trillionsofpeople.info
sudo certbot --apache -d codexes.nimblebooks.com
sudo certbot --apache -d fredzannarbor.com -d www.fredzannarbor.com

# Test auto-renewal
sudo certbot renew --dry-run
```

## 📋 App Directories Status

The following app directories exist in `/home/wfz/`:

- ✅ `agentic_social_server/` - Social Xtuff (port 8501)
- ✅ `altDOGE/` - altDOGE (port 8505)
- ✅ `codexes-factory/` - Codexes Factory (port 8502)
- ✅ `trillionsofpeople/` - TrillionsOfPeople (port 8504)

**Missing/Need to verify:**
- ❓ `personal-time-management/` - Daily Engine (port 8509)
- ❓ `collectiverse/` - Collectiverse (port 8503)
- ❓ `resume-site/` - Resume site (port 8508)

Check if these need to be cloned/transferred:
```bash
ls -d /home/wfz/{personal-time-management,collectiverse,resume-site} 2>/dev/null || echo "Missing directories"
```

## 🔍 Testing & Verification

After all steps complete, test each domain:

```bash
# Test HTTP status
curl -I https://xtuff.ai
curl -I https://dailyengine.xtuff.ai
curl -I https://social.xtuff.ai
curl -I https://collectiverse.xtuff.ai
curl -I https://trillionsofpeople.info
curl -I https://altdoge.xtuff.ai
curl -I https://codexes.nimblebooks.com
curl -I https://fredzannarbor.com
```

All should return: `HTTP/2 200`

## 🛠️ Useful Commands

### Service Management
```bash
# Check service status
sudo systemctl status all-apps-runner.service

# Restart service
sudo systemctl restart all-apps-runner.service

# View logs
sudo journalctl -u all-apps-runner.service -f
```

### Apache Management
```bash
# Test config
sudo apache2ctl configtest

# Reload Apache
sudo systemctl reload apache2

# View error logs
sudo tail -f /var/log/apache2/xtuff-ai-error.log
```

### Monitoring
```bash
# Check all app ports
sudo netstat -tlnp | grep -E '(8500|8501|8502|8503|8504|8505|8508|8509)'

# Resource usage
top -u wfz
htop -u wfz

# Disk space
df -h
du -sh /home/wfz/bin/all_applications_runner
```

## 🚨 Important Notes

1. **Apache must be installed first** before starting the systemd service
2. **DNS must be configured** before requesting SSL certificates
3. **App ports (8500-8509) should NOT be exposed** - only Apache (80, 443) should be accessible
4. **Verify all app directories exist** before starting services
5. **Check logs immediately** after starting services for any errors

## 📞 Troubleshooting

If service fails to start:
```bash
# Check detailed logs
sudo journalctl -u all-apps-runner.service -n 100 --no-pager

# Check if port is in use
sudo netstat -tlnp | grep 8500

# Test manual start
cd /home/wfz/bin/all_applications_runner
source .venv/bin/activate
streamlit run main.py --server.port=8500
```

If Apache has issues:
```bash
# Check syntax
sudo apache2ctl configtest

# Check enabled modules
sudo apache2ctl -M

# View error logs
sudo tail -100 /var/log/apache2/error.log
```

## 📚 Reference Files

- Deployment guide: `/home/wfz/bin/all_applications_runner/all_applications_runner_deployment.md`
- Systemd service: `/home/wfz/bin/all_applications_runner/deployment/all-apps-runner.service`
- Apache main config: `/home/wfz/bin/all_applications_runner/deployment/xtuff-ai-runner.conf`
- Apache vhosts: `/home/wfz/bin/all_applications_runner/deployment/all-apps-vhosts.conf`
- App config: `/home/wfz/bin/all_applications_runner/apps_config.json`

---

**Ready to proceed?** Start with Step 1: Install Apache2
