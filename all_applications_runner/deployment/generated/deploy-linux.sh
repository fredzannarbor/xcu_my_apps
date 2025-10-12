#!/bin/bash
# Deployment script for Fred's Unified App Runner
# Run as root or with sudo

set -e

echo "Deploying Fred's Unified App Runner..."

# Variables
APP_USER="www-data"
APP_DIR="/home/wfz/app-runner"
APACHE_SITES_DIR="/etc/apache2/sites-available"
SYSTEMD_DIR="/etc/systemd/system"

# Create app directory if it doesn't exist
if [ ! -d "$APP_DIR" ]; then
    echo "Creating app directory: $APP_DIR"
    mkdir -p "$APP_DIR"
    chown $APP_USER:$APP_USER "$APP_DIR"
fi

# Install Python dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv apache2

# Enable required Apache modules
echo "Enabling Apache modules..."
a2enmod proxy
a2enmod proxy_http
a2enmod headers
a2enmod rewrite
a2enmod ssl

# Copy application files
echo "Copying application files..."
# Note: Assumes files are already in $APP_DIR via git pull

# Install Python dependencies
cd "$APP_DIR"
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
fi

# Install systemd services
echo "Installing systemd services..."
python3 deployment/apache_config.py generate-systemd

# Copy Apache configuration
echo "Installing Apache configuration..."
python3 deployment/apache_config.py generate-apache > "$APACHE_SITES_DIR/app-runner.conf"

# Enable the site
a2ensite app-runner
a2dissite 000-default  # Optional: disable default site

# Reload Apache
systemctl reload apache2

# Start and enable services
echo "Starting services..."
systemctl daemon-reload
systemctl enable app-runner-master.service
systemctl enable app-runner-manager.service
systemctl start app-runner-master.service
systemctl start app-runner-manager.service

echo "Deployment complete!"
echo ""
echo "Services status:"
systemctl status app-runner-master.service --no-pager
systemctl status app-runner-manager.service --no-pager

echo ""
echo "Access the application at: http://your-domain.com"
echo "Configure DNS to point to this server"