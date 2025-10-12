#!/bin/bash
# Deployment script for xtuff.ai All Applications Runner
# Run this script on the Debian server as user wfz

set -e  # Exit on error

echo "====================================="
echo "xtuff.ai App Runner Deployment Script"
echo "====================================="

# Variables
APP_DIR="/home/wfz/all_applications_runner"
SERVICE_NAME="all-apps-runner.service"
VHOST_MAIN="xtuff-ai-runner.conf"
VHOST_APPS="all-apps-vhosts.conf"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as wfz
if [ "$USER" != "wfz" ]; then
    echo -e "${RED}Error: This script must be run as user 'wfz'${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Updating apps_config.json paths...${NC}"
# Update paths in apps_config.json
cd $APP_DIR
if [ -f apps_config.json ]; then
    # Backup original
    cp apps_config.json apps_config.json.backup

    # Update paths (macOS -> Debian)
    sed -i 's|/Users/fred/my-organizations/xtuff/agentic_social_server|/home/wfz/agentic_social_server|g' apps_config.json
    sed -i 's|/Users/fred/my-organizations/altDOGE|/home/wfz/altDOGE|g' apps_config.json
    sed -i 's|/Users/fred/my-organizations/trillionsofpeople|/home/wfz/trillionsofpeople|g' apps_config.json
    sed -i 's|/Users/fred/my-organizations/nimble/repos/codexes-factory|/home/wfz/codexes-factory|g' apps_config.json
    sed -i 's|/Users/fred/my-organizations/personal-time-management|/home/wfz/personal-time-management|g' apps_config.json
    sed -i 's|/Users/fred/my-organizations/personal/resume-site|/home/wfz/resume-site|g' apps_config.json
    sed -i 's|/Users/fred/my-organizations/xtuff/collectiverse|/home/wfz/collectiverse|g' apps_config.json

    echo -e "${GREEN}✓ apps_config.json paths updated${NC}"
else
    echo -e "${RED}Error: apps_config.json not found${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 2: Creating Python virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    python3.12 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

echo -e "${YELLOW}Step 3: Installing Python dependencies...${NC}"
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo -e "${YELLOW}Step 4: Creating log directory...${NC}"
mkdir -p logs
echo -e "${GREEN}✓ Log directory created${NC}"

echo -e "${YELLOW}Step 5: Installing systemd service...${NC}"
if [ -f "deployment/$SERVICE_NAME" ]; then
    sudo cp deployment/$SERVICE_NAME /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    echo -e "${GREEN}✓ Systemd service installed and enabled${NC}"
else
    echo -e "${RED}Error: Service file not found at deployment/$SERVICE_NAME${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 6: Installing Apache VirtualHosts...${NC}"
if [ -f "deployment/$VHOST_MAIN" ]; then
    sudo cp deployment/$VHOST_MAIN /etc/apache2/sites-available/
    sudo a2ensite $VHOST_MAIN
    echo -e "${GREEN}✓ Main VirtualHost installed${NC}"
else
    echo -e "${RED}Warning: Main VirtualHost file not found${NC}"
fi

if [ -f "deployment/$VHOST_APPS" ]; then
    sudo cp deployment/$VHOST_APPS /etc/apache2/sites-available/
    sudo a2ensite $VHOST_APPS
    echo -e "${GREEN}✓ Apps VirtualHosts installed${NC}"
else
    echo -e "${RED}Warning: Apps VirtualHost file not found${NC}"
fi

echo -e "${YELLOW}Step 7: Enabling Apache modules...${NC}"
sudo a2enmod proxy proxy_http proxy_wstunnel rewrite headers ssl
echo -e "${GREEN}✓ Apache modules enabled${NC}"

echo -e "${YELLOW}Step 8: Testing Apache configuration...${NC}"
sudo apache2ctl configtest
echo -e "${GREEN}✓ Apache configuration is valid${NC}"

echo -e "${YELLOW}Step 9: Reloading Apache...${NC}"
sudo systemctl reload apache2
echo -e "${GREEN}✓ Apache reloaded${NC}"

echo -e "${YELLOW}Step 10: Starting app runner service...${NC}"
sudo systemctl start $SERVICE_NAME
sleep 3

# Check service status
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${GREEN}✓ App runner service started successfully${NC}"
else
    echo -e "${RED}Error: Service failed to start. Checking logs...${NC}"
    sudo journalctl -u $SERVICE_NAME -n 50
    exit 1
fi

echo ""
echo -e "${GREEN}====================================="
echo "Deployment Complete!"
echo "=====================================${NC}"
echo ""
echo "Service Status:"
sudo systemctl status $SERVICE_NAME --no-pager -l
echo ""
echo "Next Steps:"
echo "1. Update DNS records for all domains to point to this server"
echo "2. Run: sudo certbot --apache -d xtuff.ai -d www.xtuff.ai"
echo "3. Run certbot for each additional domain"
echo "4. Test each domain: https://xtuff.ai, https://dailyengine.xtuff.ai, etc."
echo ""
echo "Useful Commands:"
echo "  View logs:    tail -f $APP_DIR/logs/runner.log"
echo "  Service logs: sudo journalctl -u $SERVICE_NAME -f"
echo "  Restart:      sudo systemctl restart $SERVICE_NAME"
echo "  Stop:         sudo systemctl stop $SERVICE_NAME"
echo ""
