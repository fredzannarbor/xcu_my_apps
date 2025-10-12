#!/bin/bash
#
# Setup GitHub SSH access on remote server
#

REMOTE_USER="wfzimmerman"
REMOTE_HOST="34.172.181.254"
SSH_KEY="$HOME/.ssh/rare-shadow_ed25519"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Setting up GitHub SSH access on remote server ===${NC}"

echo -e "${YELLOW}Step 1: Checking for existing SSH key on remote...${NC}"
ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" "ls -la ~/.ssh/id_*.pub 2>/dev/null || echo 'No SSH key found'"

echo -e "\n${YELLOW}Step 2: Generating new SSH key on remote (if needed)...${NC}"
ssh -i "$SSH_KEY" "$REMOTE_USER@$REMOTE_HOST" << 'ENDSSH'
if [ ! -f ~/.ssh/id_ed25519 ]; then
    echo "Generating new SSH key..."
    ssh-keygen -t ed25519 -C "wfzimmerman@gmail.com" -f ~/.ssh/id_ed25519 -N ""
    echo "SSH key generated!"
else
    echo "SSH key already exists"
fi

echo ""
echo "===== PUBLIC KEY ====="
cat ~/.ssh/id_ed25519.pub
echo "======================"
echo ""
echo "Add this key to GitHub at: https://github.com/settings/ssh/new"
ENDSSH

echo -e "\n${GREEN}Next steps:${NC}"
echo "1. Copy the public key shown above"
echo "2. Go to: https://github.com/settings/ssh/new"
echo "3. Add the key with title: 'GCP book-publisher-agi'"
echo "4. Test with: ssh -i ~/.ssh/rare-shadow_ed25519 wfzimmerman@34.172.181.254 'ssh -T git@github.com'"
echo "5. Then run: ./deploy_to_remote.sh setup"
