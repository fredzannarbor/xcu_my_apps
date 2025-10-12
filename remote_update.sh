#!/bin/bash
#
# Remote Update Script - Lives on GCP server
# Quick script to update all xCU applications via git pull
#
# Usage: ./remote_update.sh [app_name|all]
#

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

BASE_DIR="$HOME"

# App configuration: "dir|branch|service_name"
APPS=(
    "xcu_my_apps|main|"
    "all_applications_runner|unified-app-runner|all-apps-runner"
    "personal|main|daily-engine"
    "agentic_social_server|main|agentic-social"
    "trillionsofpeople|main|trillions"
)

update_app() {
    local dir="$1"
    local branch="$2"
    local service="$3"

    if [ ! -d "$BASE_DIR/$dir" ]; then
        echo -e "${RED}✗ Directory not found: $dir${NC}"
        return 1
    fi

    echo -e "${YELLOW}Updating: $dir${NC}"

    cd "$BASE_DIR/$dir"

    # Stash any local changes
    if ! git diff-index --quiet HEAD --; then
        echo -e "${YELLOW}  Stashing local changes...${NC}"
        git stash save "Auto-stash before update $(date +%Y%m%d_%H%M%S)"
    fi

    # Fetch and pull
    git fetch origin
    git checkout "$branch"
    git pull origin "$branch"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✓ Updated${NC}"

        # Show latest commit
        echo -e "${GREEN}  Latest: $(git log -1 --oneline)${NC}"

        # Restart service if specified
        if [ -n "$service" ]; then
            echo -e "${YELLOW}  Restarting service: $service${NC}"
            sudo systemctl restart "$service" 2>/dev/null && \
                echo -e "${GREEN}  ✓ Service restarted${NC}" || \
                echo -e "${YELLOW}  ⚠ Could not restart service (may need sudo)${NC}"
        fi

        return 0
    else
        echo -e "${RED}  ✗ Update failed${NC}"
        return 1
    fi
}

show_status() {
    local dir="$1"

    if [ ! -d "$BASE_DIR/$dir" ]; then
        echo -e "${RED}✗ Not found: $dir${NC}"
        return
    fi

    cd "$BASE_DIR/$dir"
    echo -e "${YELLOW}$dir${NC}"
    git status -sb
    git log -1 --oneline
    echo ""
}

TARGET="${1:-all}"

case "$TARGET" in
    all)
        echo -e "${GREEN}=== Updating All Applications ===${NC}"
        for app in "${APPS[@]}"; do
            IFS='|' read -r dir branch service <<< "$app"
            update_app "$dir" "$branch" "$service"
            echo ""
        done
        ;;

    status)
        echo -e "${GREEN}=== Application Status ===${NC}"
        for app in "${APPS[@]}"; do
            IFS='|' read -r dir branch service <<< "$app"
            show_status "$dir"
        done
        ;;

    xcu|xcu_my_apps)
        update_app "xcu_my_apps" "main" ""
        ;;

    runner|all_applications_runner)
        update_app "all_applications_runner" "unified-app-runner" "all-apps-runner"
        ;;

    daily|personal)
        update_app "personal" "main" "daily-engine"
        ;;

    social|agentic_social_server)
        update_app "agentic_social_server" "main" "agentic-social"
        ;;

    trillions|trillionsofpeople)
        update_app "trillionsofpeople" "main" "trillions"
        ;;

    *)
        echo "Usage: $0 [all|status|APP_NAME]"
        echo ""
        echo "Available apps:"
        echo "  xcu                    - Main xCU container"
        echo "  runner                 - All Applications Runner"
        echo "  daily                  - Daily Engine"
        echo "  social                 - Agentic Social Server"
        echo "  trillions              - Trillions of People"
        echo ""
        echo "  all                    - Update all apps"
        echo "  status                 - Show status of all apps"
        exit 1
        ;;
esac

echo -e "${GREEN}=== Done ===${NC}"
