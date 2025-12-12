#!/bin/bash

###############################################################################
# ConcordBroker Project Cleanup Script
# Purpose: Safely remove files identified in security audit
# Date: 2025-11-07
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Timestamp for backup
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="security_cleanup_backup_${TIMESTAMP}"

###############################################################################
# STEP 0: Pre-flight checks
###############################################################################
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ConcordBroker Cleanup Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ] || [ ! -d "apps" ]; then
    echo -e "${RED}ERROR: Not in ConcordBroker root directory${NC}"
    echo "Please run this script from the project root"
    exit 1
fi

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}ERROR: git is not installed${NC}"
    exit 1
fi

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}ERROR: Not in a git repository${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Pre-flight checks passed${NC}"
echo ""

###############################################################################
# STEP 1: Create backup directory
###############################################################################
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}STEP 1: Creating Backup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

mkdir -p "${BACKUP_DIR}"
echo -e "${GREEN}✓ Created backup directory: ${BACKUP_DIR}${NC}"
echo ""

###############################################################################
# STEP 2: Backup files with credentials (CRITICAL)
###############################################################################
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}STEP 2: Backing Up Credential Files${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

CREDENTIAL_FILES=(
    "apply_security_fixes.py"
    "apply_optimizations.py"
)

for file in "${CREDENTIAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "${BACKUP_DIR}/"
        echo -e "${GREEN}✓ Backed up: $file${NC}"
    else
        echo -e "${YELLOW}⚠ Not found (already deleted?): $file${NC}"
    fi
done
echo ""

###############################################################################
# STEP 3: Backup obsolete files
###############################################################################
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}STEP 3: Backing Up Obsolete Files${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

OBSOLETE_FILES=(
    "apply_all_fixes.py"
    "apply_sunbiz_fixes.py"
    "APPLY_TIMEOUTS_NOW.sql"
    "api.log"
    "api_diagnostic_report_2025-09-09T12-43-29-220Z.json"
    "api_diagnostic_report_2025-09-09T12-47-37-440Z.json"
)

for file in "${OBSOLETE_FILES[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "${BACKUP_DIR}/"
        echo -e "${GREEN}✓ Backed up: $file${NC}"
    else
        echo -e "${YELLOW}⚠ Not found: $file${NC}"
    fi
done
echo ""

###############################################################################
# STEP 4: Check git history for credential exposure
###############################################################################
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}STEP 4: Checking Git History${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

EXPOSED_IN_GIT=false

for file in "${CREDENTIAL_FILES[@]}"; do
    if git log --all --full-history --oneline -- "$file" | head -1 > /dev/null 2>&1; then
        echo -e "${RED}⚠ CRITICAL: $file found in git history${NC}"
        EXPOSED_IN_GIT=true
    else
        echo -e "${GREEN}✓ $file not in git history${NC}"
    fi
done

echo ""

if [ "$EXPOSED_IN_GIT" = true ]; then
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}⚠ CRITICAL: CREDENTIALS EXPOSED IN GIT${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "${YELLOW}You MUST rotate these credentials:${NC}"
    echo "  1. Database password (Supabase)"
    echo "  2. Service role key (Supabase)"
    echo ""
    echo "See PROJECT_AUDIT_REPORT.md for detailed instructions"
    echo ""

    # Create a reminder file
    cat > "${BACKUP_DIR}/ROTATE_CREDENTIALS_CHECKLIST.txt" << 'EOF'
CRITICAL: CREDENTIALS ROTATION CHECKLIST
========================================

⚠️ The following credentials were found in git history and MUST be rotated:

1. DATABASE PASSWORD
   - Go to: https://supabase.com/dashboard
   - Settings → Database → Change password
   - Update in:
     □ .env.mcp
     □ apps/api/.env
     □ apps/web/.env
     □ Railway environment variables
     □ Vercel environment variables

2. SUPABASE SERVICE ROLE KEY
   - Go to: https://supabase.com/dashboard
   - Settings → API → Regenerate service role key
   - Update in:
     □ .env.mcp (SUPABASE_SERVICE_ROLE_KEY)
     □ apps/api/.env (SUPABASE_SERVICE_ROLE_KEY)
     □ Railway environment variables
     □ Vercel environment variables

3. VERIFICATION
   - □ Test local dev: npm run dev
   - □ Test API: curl http://localhost:3005/health
   - □ Test UI: Check properties load
   - □ Test Railway deployment
   - □ Test Vercel deployment

DO NOT SKIP THIS STEP!
Your database and API are currently compromised.

Reference: PROJECT_AUDIT_REPORT.md
EOF

    echo -e "${GREEN}✓ Created checklist: ${BACKUP_DIR}/ROTATE_CREDENTIALS_CHECKLIST.txt${NC}"
    echo ""
fi

###############################################################################
# STEP 5: Delete credential files
###############################################################################
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}STEP 5: Deleting Credential Files${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

for file in "${CREDENTIAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        if git ls-files --error-unmatch "$file" > /dev/null 2>&1; then
            git rm "$file"
            echo -e "${GREEN}✓ Deleted (git rm): $file${NC}"
        else
            rm "$file"
            echo -e "${GREEN}✓ Deleted (rm): $file${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Already deleted: $file${NC}"
    fi
done
echo ""

###############################################################################
# STEP 6: Delete obsolete files
###############################################################################
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}STEP 6: Deleting Obsolete Files${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

for file in "${OBSOLETE_FILES[@]}"; do
    if [ -f "$file" ]; then
        if git ls-files --error-unmatch "$file" > /dev/null 2>&1; then
            git rm "$file"
            echo -e "${GREEN}✓ Deleted (git rm): $file${NC}"
        else
            rm "$file"
            echo -e "${GREEN}✓ Deleted (rm): $file${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Already deleted: $file${NC}"
    fi
done
echo ""

###############################################################################
# STEP 7: Reorganize keeper files
###############################################################################
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}STEP 7: Reorganizing Keeper Files${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Create directories
mkdir -p scripts/database
mkdir -p docs/database
mkdir -p scripts/testing

echo -e "${GREEN}✓ Created directory: scripts/database${NC}"
echo -e "${GREEN}✓ Created directory: docs/database${NC}"
echo -e "${GREEN}✓ Created directory: scripts/testing${NC}"
echo ""

# Move files
MOVE_OPS=(
    "apply_database_optimizations.py|scripts/database/"
    "APPLY_INDEXES_NOW.md|docs/database/"
    "api_endpoint_test.js|scripts/testing/"
)

for op in "${MOVE_OPS[@]}"; do
    IFS='|' read -r source dest <<< "$op"

    if [ -f "$source" ]; then
        if git ls-files --error-unmatch "$source" > /dev/null 2>&1; then
            git mv "$source" "$dest"
            echo -e "${GREEN}✓ Moved (git mv): $source → $dest${NC}"
        else
            mv "$source" "$dest"
            git add "$dest"
            echo -e "${GREEN}✓ Moved (mv): $source → $dest${NC}"
        fi
    else
        if [ -f "${dest}$(basename $source)" ]; then
            echo -e "${YELLOW}⚠ Already moved: $source${NC}"
        else
            echo -e "${YELLOW}⚠ Not found: $source${NC}"
        fi
    fi
done
echo ""

###############################################################################
# STEP 8: Update .gitignore
###############################################################################
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}STEP 8: Updating .gitignore${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Add patterns to .gitignore to prevent future issues
GITIGNORE_ADDITIONS="
# Security: Never commit files with potential credentials
*_fixes.py
*_security*.py
*.log
*diagnostic_report*.json

# Backup directories
security_cleanup_backup_*/
security_backup_*/
"

if [ -f ".gitignore" ]; then
    # Check if patterns already exist
    if ! grep -q "Security: Never commit files with potential credentials" .gitignore; then
        echo "$GITIGNORE_ADDITIONS" >> .gitignore
        git add .gitignore
        echo -e "${GREEN}✓ Updated .gitignore with security patterns${NC}"
    else
        echo -e "${YELLOW}⚠ .gitignore already has security patterns${NC}"
    fi
else
    echo "$GITIGNORE_ADDITIONS" > .gitignore
    git add .gitignore
    echo -e "${GREEN}✓ Created .gitignore with security patterns${NC}"
fi
echo ""

###############################################################################
# STEP 9: Show status and summary
###############################################################################
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}STEP 9: Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Show git status
echo -e "${YELLOW}Git Status:${NC}"
git status --short
echo ""

# Create summary
SUMMARY="${BACKUP_DIR}/CLEANUP_SUMMARY.txt"
cat > "$SUMMARY" << EOF
ConcordBroker Cleanup Summary
========================================
Date: ${TIMESTAMP}
Backup Location: ${BACKUP_DIR}

FILES DELETED (WITH CREDENTIALS):
$(printf '  - %s\n' "${CREDENTIAL_FILES[@]}")

FILES DELETED (OBSOLETE):
$(printf '  - %s\n' "${OBSOLETE_FILES[@]}")

FILES REORGANIZED:
  - apply_database_optimizations.py → scripts/database/
  - APPLY_INDEXES_NOW.md → docs/database/
  - api_endpoint_test.js → scripts/testing/

GIT HISTORY CHECK:
$(if [ "$EXPOSED_IN_GIT" = true ]; then echo "  ⚠️ CREDENTIALS FOUND IN GIT HISTORY"; else echo "  ✓ Credentials not in git history"; fi)

NEXT STEPS:
$(if [ "$EXPOSED_IN_GIT" = true ]; then echo "  1. ⚠️ ROTATE CREDENTIALS IMMEDIATELY (see checklist)"; else echo "  1. ✓ No credential rotation needed"; fi)
  2. Review changes: git status
  3. Commit changes: git commit -m "security: cleanup audit files"
  4. Push to remote: git push origin master

VERIFICATION:
  - All backups are in: ${BACKUP_DIR}
  - Review PROJECT_AUDIT_REPORT.md for details
$(if [ "$EXPOSED_IN_GIT" = true ]; then echo "  - MUST rotate credentials before considering this complete"; fi)

EOF

cat "$SUMMARY"
echo ""

###############################################################################
# STEP 10: Next steps
###############################################################################
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Next Steps${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ "$EXPOSED_IN_GIT" = true ]; then
    echo -e "${RED}⚠️ CRITICAL: ROTATE CREDENTIALS FIRST${NC}"
    echo ""
    echo "See: ${BACKUP_DIR}/ROTATE_CREDENTIALS_CHECKLIST.txt"
    echo ""
    echo -e "${YELLOW}After rotating credentials:${NC}"
else
    echo -e "${GREEN}✓ No credential rotation needed${NC}"
    echo ""
    echo -e "${YELLOW}You can now:${NC}"
fi

echo "  1. Review changes:"
echo -e "     ${YELLOW}git status${NC}"
echo ""
echo "  2. Commit changes:"
echo -e "     ${YELLOW}git commit -m 'security: Remove files with hardcoded credentials and reorganize'${NC}"
echo ""
echo "  3. Push to remote:"
echo -e "     ${YELLOW}git push origin master${NC}"
echo ""
echo "  4. Verify everything works:"
echo -e "     ${YELLOW}npm run dev${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Cleanup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "All files backed up to: ${BACKUP_DIR}"
echo "Full report: PROJECT_AUDIT_REPORT.md"
echo ""

if [ "$EXPOSED_IN_GIT" = true ]; then
    echo -e "${RED}⚠️ DO NOT FORGET TO ROTATE CREDENTIALS!${NC}"
    echo ""
fi

exit 0
