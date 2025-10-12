#!/bin/bash
#
# Migration script: Sync xcu_my_apps to remote GCP server
# Usage: ./migrate_to_remote.sh [dry-run|sync]
#

REMOTE_USER="wfzimmerman"
REMOTE_HOST="34.172.181.254"
REMOTE_BASE="/home/wfz"
LOCAL_BASE="/Users/fred/my-apps"
SSH_KEY="$HOME/.ssh/rare-shadow_ed25519"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

MODE="${1:-dry-run}"

if [ "$MODE" = "dry-run" ]; then
    echo -e "${YELLOW}Running in DRY-RUN mode (no changes will be made)${NC}"
    RSYNC_FLAGS="-avzn"
else
    echo -e "${GREEN}Running in SYNC mode (files will be transferred)${NC}"
    RSYNC_FLAGS="-avz"
fi

# Common rsync options
RSYNC_OPTS="--progress --stats --exclude='.DS_Store' --exclude='__pycache__' --exclude='*.pyc' --exclude='.venv' --exclude='node_modules' --exclude='.git' --exclude='*.db' --exclude='logs/*'"

echo -e "\n${GREEN}=== Migration Plan ===${NC}"
echo "Local:  $LOCAL_BASE"
echo "Remote: $REMOTE_USER@$REMOTE_HOST:$REMOTE_BASE"
echo ""

# Function to sync a directory
sync_dir() {
    local_path="$1"
    remote_path="$2"
    description="$3"

    echo -e "\n${YELLOW}Syncing: $description${NC}"
    echo "From: $local_path"
    echo "To:   $REMOTE_USER@$REMOTE_HOST:$remote_path"

    rsync $RSYNC_FLAGS $RSYNC_OPTS \
        -e "ssh -i $SSH_KEY" \
        "$local_path" \
        "$REMOTE_USER@$REMOTE_HOST:$remote_path"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Success${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi
}

# 1. Sync shared components
echo -e "\n${GREEN}=== Step 1: Shared Components ===${NC}"
sync_dir "$LOCAL_BASE/shared/" "$REMOTE_BASE/xcu_my_apps/shared" "Shared authentication and UI components"

# 2. Sync all_applications_runner
echo -e "\n${GREEN}=== Step 2: Applications Runner ===${NC}"
sync_dir "$LOCAL_BASE/all_applications_runner/" "$REMOTE_BASE/xcu_my_apps/all_applications_runner" "Unified application runner"

# 3. Sync xtuff apps
echo -e "\n${GREEN}=== Step 3: Xtuff Applications ===${NC}"
sync_dir "$LOCAL_BASE/xtuff/agentic_social_server/" "$REMOTE_BASE/agentic_social_server" "Agentic Social Server"
sync_dir "$LOCAL_BASE/xtuff/personal-time-management/" "$REMOTE_BASE/personal/" "Daily Engine (Personal Time Management)"
sync_dir "$LOCAL_BASE/xtuff/trillionsofpeople/" "$REMOTE_BASE/trillionsofpeople" "Trillions of People"
sync_dir "$LOCAL_BASE/xtuff/xai_health/" "$REMOTE_BASE/xai_health_coach" "XAI Health Coach"

# 4. Sync nimble apps
echo -e "\n${GREEN}=== Step 4: Nimble Applications ===${NC}"
if [ -d "$LOCAL_BASE/nimble/codexes-factory" ]; then
    sync_dir "$LOCAL_BASE/nimble/codexes-factory/" "$REMOTE_BASE/nimble/codexes-factory" "Codexes Factory"
fi

# 5. Sync configuration files
echo -e "\n${GREEN}=== Step 5: Configuration Files ===${NC}"
sync_dir "$LOCAL_BASE/.env" "$REMOTE_BASE/xcu_my_apps/.env" "Environment variables"
sync_dir "$LOCAL_BASE/pyproject.toml" "$REMOTE_BASE/xcu_my_apps/pyproject.toml" "Python project config"

echo -e "\n${GREEN}=== Migration Complete ===${NC}"
if [ "$MODE" = "dry-run" ]; then
    echo -e "${YELLOW}This was a DRY-RUN. Run './migrate_to_remote.sh sync' to perform actual sync.${NC}"
else
    echo -e "${GREEN}Files have been synced to remote server.${NC}"
    echo -e "\nNext steps:"
    echo "1. SSH to server: ssh -i ~/.ssh/rare-shadow_ed25519 wfzimmerman@34.172.181.254"
    echo "2. Update systemd services if needed"
    echo "3. Test applications"
fi
