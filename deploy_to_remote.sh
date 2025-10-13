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
    # Main xCU apps container - clean production branch (no archives, no secrets)
    "/Users/fred/xcu_my_apps|git@github.com:fredzannarbor/xcu_my_apps.git|xcu_my_apps|clean-production"

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

        # Copy app-specific .env files
        echo "Copying codexes-factory .env..."
        scp -i "$SSH_KEY" /Users/fred/xcu_my_apps/nimble/codexes-factory/.env "$REMOTE_USER@$REMOTE_HOST:$REMOTE_BASE/xcu_my_apps/nimble/codexes-factory/.env" 2>/dev/null || echo "  (no .env found, skipping)"

        echo -e "${GREEN}✓ .env files copied${NC}"
        ;;

    restart)
        echo -e "${GREEN}=== Restarting Services ===${NC}"
        SERVICE="${2:-all}"

        if [ "$SERVICE" = "all" ]; then
            echo "Restarting all app services..."
            remote_ssh "sudo systemctl restart 'app-*.service' codexes-factory.service trillionsofpeople.service xai_health_coach.service agentic_social_server.service 2>/dev/null || echo 'Some services may not exist'"
        else
            echo "Restarting $SERVICE..."
            remote_ssh "sudo systemctl restart $SERVICE"
        fi

        echo -e "${GREEN}✓ Services restarted${NC}"
        ;;

    deploy)
        echo -e "${GREEN}=== Full Deployment Pipeline ===${NC}"
        echo ""

        # 1. Update code
        echo -e "${BLUE}Step 1: Updating repositories...${NC}"
        for repo_config in "${REPOS[@]}"; do
            IFS='|' read -r local_path github_repo remote_path branch <<< "$repo_config"
            update_repo "$remote_path" "$branch"
        done
        echo ""

        # 2. Copy .env files
        echo -e "${BLUE}Step 2: Copying .env files...${NC}"
        scp -i "$SSH_KEY" /Users/fred/xcu_my_apps/.env "$REMOTE_USER@$REMOTE_HOST:$REMOTE_BASE/xcu_my_apps/.env" 2>/dev/null || echo "  (skipped)"
        echo ""

        # 3. Restart services
        echo -e "${BLUE}Step 3: Restarting services...${NC}"
        remote_ssh "sudo systemctl restart codexes-factory.service trillionsofpeople.service 2>/dev/null || echo 'Some services may not exist'"
        echo ""

        # 4. Check status
        echo -e "${BLUE}Step 4: Checking service status...${NC}"
        remote_ssh "systemctl status codexes-factory.service --no-pager -l | head -10"
        echo ""

        echo -e "${GREEN}=== Deployment Complete ===${NC}"
        echo ""
        echo "Services available at:"
        echo "  - Codexes Factory: http://xtuff.ai:8502"
        echo "  - All Apps Runner: http://xtuff.ai:8500"
        echo "  - Trillions: http://xtuff.ai:8507"
        ;;

    test)
        echo -e "${GREEN}=== Testing Production Services ===${NC}"
        echo ""

        SERVICES=("codexes-factory.service" "trillionsofpeople.service" "xai_health_coach.service" "agentic_social_server.service" "app-runner-master.service")

        for service in "${SERVICES[@]}"; do
            echo -e "${YELLOW}Testing: $service${NC}"
            remote_ssh "systemctl is-active $service 2>/dev/null && echo '  ✓ Running' || echo '  ✗ Not running'"
            remote_ssh "systemctl status $service --no-pager -l 2>/dev/null | head -5"
            echo ""
        done

        echo -e "${BLUE}Checking ports:${NC}"
        remote_ssh "ss -tlnp 2>/dev/null | grep -E ':(8500|8501|8502|8506|8507)' || echo 'No ports listening'"
        ;;

    ssh)
        echo -e "${BLUE}Opening SSH connection to remote server...${NC}"
        ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST"
        ;;

    *)
        echo "Usage: $0 [setup|update|status|copy-env|restart|deploy|test|ssh]"
        echo ""
        echo "Commands:"
        echo "  setup          - Initial clone of all repositories (clean-production branch)"
        echo "  update         - Pull latest changes for all repos"
        echo "  status         - Check git status of all repos"
        echo "  copy-env       - Copy .env files to remote"
        echo "  restart [name] - Restart services (all or specific service)"
        echo "  deploy         - Full deployment pipeline (update + restart + test)"
        echo "  test           - Test all production services"
        echo "  ssh            - Open SSH session to remote server"
        echo ""
        echo "Examples:"
        echo "  $0 deploy                              # Full deployment"
        echo "  $0 restart codexes-factory.service     # Restart single service"
        echo "  $0 test                                # Check all services"
        exit 1
        ;;
esac
