#!/bin/bash
#
# Deploy systemd services to remote server
#

REMOTE_USER="wfzimmerman"
REMOTE_HOST="34.172.181.254"
SSH_KEY="$HOME/.ssh/rare-shadow_ed25519"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Deploying Systemd Services ===${NC}"

# Services to deploy
SERVICES=(
    "all-apps-runner"
    "daily-engine"
    "agentic-social"
    "trillions"
    "codexes-factory"
    "resume"
    "collectiverse"
    "altdoge"
    "max-bialystok"
)

# Copy service files to remote
echo -e "\n${YELLOW}Step 1: Copying service files...${NC}"
for service in "${SERVICES[@]}"; do
    echo "  Copying $service.service..."
    scp -i "$SSH_KEY" \
        systemd_services/$service.service \
        "$REMOTE_USER@$REMOTE_HOST:/tmp/$service.service"
done

# Install services
echo -e "\n${YELLOW}Step 2: Installing services...${NC}"
ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" << 'ENDSSH'
for service in all-apps-runner daily-engine agentic-social trillions codexes-factory resume collectiverse altdoge max-bialystok; do
    echo "  Installing $service.service..."
    sudo mv /tmp/$service.service /etc/systemd/system/$service.service
    sudo chmod 644 /etc/systemd/system/$service.service
done

# Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable services
echo "Enabling services..."
for service in all-apps-runner daily-engine agentic-social trillions codexes-factory resume collectiverse altdoge max-bialystok; do
    sudo systemctl enable $service.service
    echo "  ✓ $service enabled"
done
ENDSSH

# Create log directories
echo -e "\n${YELLOW}Step 3: Creating log directories...${NC}"
ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" << 'ENDSSH'
for dir in xcu_my_apps/all_applications_runner xcu_my_apps/personal xcu_my_apps/xtuff/agentic_social_server xcu_my_apps/xtuff/trillionsofpeople xcu_my_apps/nimble/codexes-factory xcu_my_apps/xtuff/resume-site xcu_my_apps/xtuff/collectiverse xcu_my_apps/xtuff/altDOGE; do
    mkdir -p ~/${dir}/logs
    echo "  ✓ Created ~/${dir}/logs"
done
ENDSSH

# Handle start/stop/status commands
case "${1:-install}" in
    start)
        echo -e "\n${YELLOW}Starting services...${NC}"
        for service in "${SERVICES[@]}"; do
            ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" "sudo systemctl start $service.service"
            echo "  ✓ Started $service"
        done
        ;;
    stop)
        echo -e "\n${YELLOW}Stopping services...${NC}"
        for service in "${SERVICES[@]}"; do
            ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" "sudo systemctl stop $service.service"
            echo "  ✓ Stopped $service"
        done
        ;;
    restart)
        echo -e "\n${YELLOW}Restarting services...${NC}"
        for service in "${SERVICES[@]}"; do
            ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" "sudo systemctl restart $service.service"
            echo "  ✓ Restarted $service"
        done
        ;;
    status)
        echo -e "\n${GREEN}Service Status:${NC}"
        ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" << 'ENDSSH'
for service in all-apps-runner daily-engine agentic-social trillions codexes-factory resume collectiverse altdoge max-bialystok; do
    echo ""
    echo "=== $service ==="
    sudo systemctl status $service.service --no-pager | head -10
done
ENDSSH
        ;;
    install)
        echo -e "\n${GREEN}=== Services Installed ===${NC}"
        echo ""
        echo "Next steps:"
        echo "  ./deploy_services.sh start    - Start all services"
        echo "  ./deploy_services.sh status   - Check service status"
        echo "  ./deploy_services.sh restart  - Restart all services"
        echo "  ./deploy_services.sh stop     - Stop all services"
        ;;
esac
