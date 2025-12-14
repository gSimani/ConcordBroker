#!/bin/bash
# Automatic Port Configuration for Worktrees
# Updates vite.config.ts in a worktree to use the correct port

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Port mapping (must match worktree-manager.sh)
declare -A PORT_MAP=(
    ["master"]="5191"
    ["feature/ui-consolidation"]="5192"
    ["feature/api-enhancements"]="5193"
    ["feature/database-optimization"]="5194"
    ["feature/agent-development"]="5195"
    ["hotfix/production"]="5196"
    ["experimental/new-features"]="5197"
    ["testing/integration"]="5198"
)

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Get assigned port
ASSIGNED_PORT=${PORT_MAP[$CURRENT_BRANCH]}

if [ -z "$ASSIGNED_PORT" ]; then
    echo -e "${YELLOW}Warning: No port assignment found for branch: $CURRENT_BRANCH${NC}"
    echo -e "${YELLOW}Using default port 5191${NC}"
    ASSIGNED_PORT="5191"
else
    echo -e "${GREEN}Branch: $CURRENT_BRANCH${NC}"
    echo -e "${GREEN}Assigned Port: $ASSIGNED_PORT${NC}"
fi

# Path to vite config
VITE_CONFIG="apps/web/vite.config.ts"

if [ ! -f "$VITE_CONFIG" ]; then
    echo -e "${RED}Error: $VITE_CONFIG not found${NC}"
    echo -e "${YELLOW}Are you in the correct directory?${NC}"
    exit 1
fi

# Backup original config
cp "$VITE_CONFIG" "${VITE_CONFIG}.backup"

# Update port in vite.config.ts
sed -i "s/port: [0-9]\+,/port: $ASSIGNED_PORT,/" "$VITE_CONFIG"

echo -e "${GREEN}✓ Updated vite.config.ts${NC}"
echo -e "${BLUE}Port changed to: $ASSIGNED_PORT${NC}"
echo ""
echo "Verification:"
grep "port:" "$VITE_CONFIG" | head -1
echo ""
echo -e "${YELLOW}Backup saved: ${VITE_CONFIG}.backup${NC}"
echo ""
echo "Next steps:"
echo "  cd apps/web"
echo "  npm run dev"
echo ""
echo "Your server will start on: http://localhost:$ASSIGNED_PORT"
