#!/bin/bash
#
# Git-based deployment script for xCU apps to GCP remote server
# This script clones repos on the remote server for git-based updates
#
# Usage: ./deploy_to_remote.sh [setup|update|status]
#

REMOTE_USER="wfzimmerman"
REMOTE_HOST="34.172.181.254"
REMOTE_BASE="/home/wfzimmerman"
SSH_KEY="$HOME/.ssh/rare-shadow_ed25519"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

MODE="${1:-setup}"

# SSH command wrapper
remote_ssh() {
    ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" "$@"
}

# Repository configuration
# Format: "local_path|github_repo|remote_path|branch"
REPOS=(
    # Main xCU apps container - this contains everything
    "/Users/fred/my-apps|git@github.com:fredzannarbor/xcu_my_apps.git|xcu_my_apps|gemin"

    # Resume site - separate standalone app
    # Note: Add resume-site repo if/when it exists
)

setup_repo() {
    local github_repo="$1"
    local remote_path="$2"
    local branch="$3"
    local repo_name=$(basename "$remote_path")

    echo -e "${YELLOW}Setting up: $repo_name${NC}"

    # Check if directory already exists
    if remote_ssh "test -d $REMOTE_BASE/$remote_path"; then
        echo -e "${BLUE}  Directory exists, checking if it's a git repo...${NC}"
        if remote_ssh "cd $REMOTE_BASE/$remote_path && git rev-parse --git-dir > /dev/null 2>&1"; then
            echo -e "${GREEN}  ✓ Already a git repo, fetching updates...${NC}"
            remote_ssh "cd $REMOTE_BASE/$remote_path && git fetch origin && git status"
        else
            echo -e "${RED}  ✗ Directory exists but is not a git repo!${NC}"
            echo -e "${YELLOW}  Renaming to ${remote_path}.backup${NC}"
            remote_ssh "mv $REMOTE_BASE/$remote_path $REMOTE_BASE/${remote_path}.backup"
            echo -e "${GREEN}  Cloning fresh copy...${NC}"
            remote_ssh "cd $REMOTE_BASE && git clone -b $branch $github_repo $remote_path"
        fi
    else
        echo -e "${GREEN}  Cloning repository...${NC}"
        remote_ssh "cd $REMOTE_BASE && git clone -b $branch $github_repo $remote_path"
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✓ Success${NC}"
        return 0
    else
        echo -e "${RED}  ✗ Failed${NC}"
        return 1
    fi
}

update_repo() {
    local remote_path="$1"
    local branch="$2"
    local repo_name=$(basename "$remote_path")

    echo -e "${YELLOW}Updating: $repo_name${NC}"

    remote_ssh "cd $REMOTE_BASE/$remote_path && git fetch origin && git checkout $branch && git pull origin $branch"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✓ Updated to latest${NC}"
        return 0
    else
        echo -e "${RED}  ✗ Update failed${NC}"
        return 1
    fi
}

check_status() {
    local remote_path="$1"
    local repo_name=$(basename "$remote_path")

    echo -e "${BLUE}Status: $repo_name${NC}"

    remote_ssh "cd $REMOTE_BASE/$remote_path && git status -sb && echo '---' && git log -1 --oneline"
    echo ""
}

case "$MODE" in
    setup)
        echo -e "${GREEN}=== Git-Based Deployment: Initial Setup ===${NC}"
        echo "Remote: $REMOTE_USER@$REMOTE_HOST:$REMOTE_BASE"
        echo ""

        for repo_config in "${REPOS[@]}"; do
            IFS='|' read -r local_path github_repo remote_path branch <<< "$repo_config"
            setup_repo "$github_repo" "$remote_path" "$branch"
            echo ""
        done

        echo -e "${GREEN}=== Setup Complete ===${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Copy .env files: ./deploy_to_remote.sh copy-env"
        echo "2. Update apps: ./deploy_to_remote.sh update"
        echo "3. Check status: ./deploy_to_remote.sh status"
        ;;

    update)
        echo -e "${GREEN}=== Updating All Repositories ===${NC}"

        for repo_config in "${REPOS[@]}"; do
            IFS='|' read -r local_path github_repo remote_path branch <<< "$repo_config"
            update_repo "$remote_path" "$branch"
            echo ""
        done

        echo -e "${GREEN}=== Update Complete ===${NC}"
        ;;

    status)
        echo -e "${GREEN}=== Repository Status ===${NC}"

        for repo_config in "${REPOS[@]}"; do
            IFS='|' read -r local_path github_repo remote_path branch <<< "$repo_config"
            check_status "$remote_path"
        done
        ;;

    copy-env)
        echo -e "${GREEN}=== Copying .env files ===${NC}"

        # Copy main .env
        echo "Copying main .env to xcu_my_apps..."
        scp -i "$SSH_KEY" /Users/fred/xcu_my_apps/.env "$REMOTE_USER@$REMOTE_HOST:$REMOTE_BASE/xcu_my_apps/.env"

        # You can add more .env files here as needed
        echo -e "${GREEN}✓ .env files copied${NC}"
        ;;

    ssh)
        echo -e "${BLUE}Opening SSH connection to remote server...${NC}"
        ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST"
        ;;

    *)
        echo "Usage: $0 [setup|update|status|copy-env|ssh]"
        echo ""
        echo "Commands:"
        echo "  setup     - Initial clone of all repositories"
        echo "  update    - Pull latest changes for all repos"
        echo "  status    - Check git status of all repos"
        echo "  copy-env  - Copy .env files to remote"
        echo "  ssh       - Open SSH session to remote server"
        exit 1
        ;;
esac
