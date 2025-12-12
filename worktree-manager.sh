#!/bin/bash
# Git Worktree Manager for ConcordBroker
# Manages multiple development streams with port isolation

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base directory (parent of main repo)
BASE_DIR="C:/Users/gsima/Documents/MyProject"
MAIN_REPO="$BASE_DIR/ConcordBroker"

# Worktree configurations with assigned ports
# Format: BRANCH_NAME:PORT:DESCRIPTION
declare -A WORKTREE_CONFIGS=(
    ["master"]="5191:Main development (current)"
    ["feature/ui-consolidation"]="5192:UI consolidation and improvements"
    ["feature/api-enhancements"]="5193:Backend API development"
    ["feature/database-optimization"]="5194:Database and query optimization"
    ["feature/agent-development"]="5195:AI agent development"
    ["hotfix/production"]="5196:Production hotfixes"
    ["experimental/new-features"]="5197:Experimental features"
    ["testing/integration"]="5198:Integration testing"
)

# Display usage information
usage() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Git Worktree Manager for ConcordBroker${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  list          - List all worktrees and their status"
    echo "  create BRANCH - Create new worktree for branch"
    echo "  remove BRANCH - Remove worktree for branch"
    echo "  ports         - Show port assignments"
    echo "  status        - Show detailed status of all worktrees"
    echo "  clean         - Clean up deleted worktrees"
    echo "  config BRANCH - Show configuration for a worktree"
    echo ""
    echo "Examples:"
    echo "  $0 list"
    echo "  $0 create feature/ui-consolidation"
    echo "  $0 remove experimental/new-features"
    echo "  $0 ports"
    echo ""
}

# List all worktrees
list_worktrees() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Active Git Worktrees${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    cd "$MAIN_REPO"
    git worktree list

    echo ""
    echo -e "${YELLOW}Tip: Use '$0 status' for detailed information${NC}"
}

# Show port assignments
show_ports() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Port Assignments for Worktrees${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    printf "%-35s %-10s %s\n" "BRANCH" "PORT" "DESCRIPTION"
    echo "────────────────────────────────────────────────────────────────────────────"

    for branch in "${!WORKTREE_CONFIGS[@]}"; do
        IFS=':' read -r port desc <<< "${WORKTREE_CONFIGS[$branch]}"
        printf "%-35s %-10s %s\n" "$branch" "$port" "$desc"
    done

    echo ""
    echo -e "${YELLOW}Note: Each worktree should run on its assigned port to avoid conflicts${NC}"
}

# Create new worktree
create_worktree() {
    local branch="$1"

    if [ -z "$branch" ]; then
        echo -e "${RED}Error: Branch name required${NC}"
        echo "Usage: $0 create BRANCH_NAME"
        exit 1
    fi

    # Generate worktree directory name
    local worktree_name="ConcordBroker-${branch//\//-}"
    local worktree_path="$BASE_DIR/$worktree_name"

    # Check if worktree already exists
    if [ -d "$worktree_path" ]; then
        echo -e "${YELLOW}Worktree already exists at: $worktree_path${NC}"
        exit 0
    fi

    echo -e "${BLUE}Creating worktree for branch: ${GREEN}$branch${NC}"
    echo -e "Location: ${YELLOW}$worktree_path${NC}"

    cd "$MAIN_REPO"

    # Check if branch exists locally
    if git show-ref --verify --quiet "refs/heads/$branch"; then
        # Branch exists locally
        git worktree add "$worktree_path" "$branch"
    elif git show-ref --verify --quiet "refs/remotes/origin/$branch"; then
        # Branch exists on remote
        git worktree add "$worktree_path" -b "$branch" "origin/$branch"
    else
        # Create new branch
        echo -e "${YELLOW}Branch doesn't exist. Creating new branch...${NC}"
        git worktree add "$worktree_path" -b "$branch"
    fi

    # Get assigned port
    if [ -n "${WORKTREE_CONFIGS[$branch]}" ]; then
        IFS=':' read -r port desc <<< "${WORKTREE_CONFIGS[$branch]}"
        echo ""
        echo -e "${GREEN}✓ Worktree created successfully!${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "Branch:      ${GREEN}$branch${NC}"
        echo -e "Path:        ${YELLOW}$worktree_path${NC}"
        echo -e "Assigned Port: ${GREEN}$port${NC}"
        echo -e "Description: $desc"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo "Next steps:"
        echo "1. cd $worktree_path"
        echo "2. Update apps/web/vite.config.ts to use port $port"
        echo "3. npm install (if needed)"
        echo "4. npm run dev"
    else
        echo ""
        echo -e "${GREEN}✓ Worktree created successfully!${NC}"
        echo -e "Path: ${YELLOW}$worktree_path${NC}"
        echo ""
        echo -e "${YELLOW}Note: No port assignment configured for this branch${NC}"
        echo "Consider adding it to WORKTREE_CONFIGS in this script"
    fi
}

# Remove worktree
remove_worktree() {
    local branch="$1"

    if [ -z "$branch" ]; then
        echo -e "${RED}Error: Branch name required${NC}"
        echo "Usage: $0 remove BRANCH_NAME"
        exit 1
    fi

    local worktree_name="ConcordBroker-${branch//\//-}"
    local worktree_path="$BASE_DIR/$worktree_name"

    if [ ! -d "$worktree_path" ]; then
        echo -e "${YELLOW}Worktree not found at: $worktree_path${NC}"
        exit 1
    fi

    echo -e "${YELLOW}Removing worktree: $worktree_path${NC}"

    cd "$MAIN_REPO"
    git worktree remove "$worktree_path"

    echo -e "${GREEN}✓ Worktree removed successfully${NC}"
}

# Show detailed status
show_status() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Worktree Status Report${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    cd "$MAIN_REPO"

    # Get worktree list
    while IFS= read -r line; do
        if [[ $line =~ ^(.+)[[:space:]]+([a-f0-9]+)[[:space:]]+\[(.+)\] ]]; then
            local path="${BASH_REMATCH[1]}"
            local commit="${BASH_REMATCH[2]}"
            local branch="${BASH_REMATCH[3]}"

            echo -e "${GREEN}Branch: $branch${NC}"
            echo -e "Path:   $path"
            echo -e "Commit: $commit"

            # Show port assignment if configured
            if [ -n "${WORKTREE_CONFIGS[$branch]}" ]; then
                IFS=':' read -r port desc <<< "${WORKTREE_CONFIGS[$branch]}"
                echo -e "Port:   ${YELLOW}$port${NC}"
                echo -e "Desc:   $desc"
            fi

            # Check if there are uncommitted changes
            if [ -d "$path/.git" ] || [ -f "$path/.git" ]; then
                cd "$path"
                if ! git diff-index --quiet HEAD --; then
                    echo -e "${YELLOW}⚠ Uncommitted changes${NC}"
                fi
                cd "$MAIN_REPO"
            fi

            echo ""
        fi
    done < <(git worktree list)
}

# Clean up deleted worktrees
clean_worktrees() {
    echo -e "${BLUE}Cleaning up worktrees...${NC}"
    cd "$MAIN_REPO"
    git worktree prune
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

# Show configuration for a specific worktree
show_config() {
    local branch="$1"

    if [ -z "$branch" ]; then
        echo -e "${RED}Error: Branch name required${NC}"
        echo "Usage: $0 config BRANCH_NAME"
        exit 1
    fi

    if [ -n "${WORKTREE_CONFIGS[$branch]}" ]; then
        IFS=':' read -r port desc <<< "${WORKTREE_CONFIGS[$branch]}"

        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}Configuration for: $branch${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "Port:        ${GREEN}$port${NC}"
        echo -e "Description: $desc"
        echo -e "Path:        $BASE_DIR/ConcordBroker-${branch//\//-}"
        echo ""
        echo "Vite config snippet:"
        echo "  server: {"
        echo "    port: $port,"
        echo "    proxy: { ... }"
        echo "  }"
    else
        echo -e "${YELLOW}No configuration found for: $branch${NC}"
        echo "Available configurations:"
        for b in "${!WORKTREE_CONFIGS[@]}"; do
            echo "  - $b"
        done
    fi
}

# Main command handler
case "${1:-}" in
    list)
        list_worktrees
        ;;
    create)
        create_worktree "$2"
        ;;
    remove)
        remove_worktree "$2"
        ;;
    ports)
        show_ports
        ;;
    status)
        show_status
        ;;
    clean)
        clean_worktrees
        ;;
    config)
        show_config "$2"
        ;;
    *)
        usage
        exit 1
        ;;
esac
