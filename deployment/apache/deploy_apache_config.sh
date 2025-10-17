#!/bin/bash
# Deploy Apache configurations to production server

set -e

REMOTE_USER="wfzimmerman"
REMOTE_HOST="34.172.181.254"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Deploying Apache configurations to production..."

# Copy configs to production /tmp
echo "📤 Uploading configuration files..."
scp "$SCRIPT_DIR/all-apps-vhosts.conf" "$REMOTE_USER@$REMOTE_HOST:/tmp/"
scp "$SCRIPT_DIR/all-apps-ssl-vhosts.conf" "$REMOTE_USER@$REMOTE_HOST:/tmp/"

# Deploy configs on production
echo "📝 Installing configurations on production..."
ssh "$REMOTE_USER@$REMOTE_HOST" << 'ENDSSH'
    # Copy configs to Apache sites-available
    sudo cp /tmp/all-apps-vhosts.conf /etc/apache2/sites-available/
    sudo cp /tmp/all-apps-ssl-vhosts.conf /etc/apache2/sites-available/

    # Enable sites if not already enabled
    sudo a2ensite all-apps-vhosts.conf 2>/dev/null || true
    sudo a2ensite all-apps-ssl-vhosts.conf 2>/dev/null || true

    # Test configuration
    echo "🔍 Testing Apache configuration..."
    sudo apache2ctl configtest

    # Reload Apache
    echo "🔄 Reloading Apache..."
    sudo systemctl reload apache2

    echo "✅ Apache configuration deployed successfully!"

    # Show status
    echo ""
    echo "📊 Apache status:"
    sudo systemctl status apache2 --no-pager | head -5
ENDSSH

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔗 Test your sites:"
echo "   https://xtuff.ai"
echo "   https://social.xtuff.ai"
echo "   https://codexes.xtuff.ai"
echo "   https://trillions.xtuff.ai"
echo "   https://daily.xtuff.ai"
echo "   https://resume.xtuff.ai"
