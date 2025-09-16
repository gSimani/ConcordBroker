#!/bin/bash
# Environment Security Check Script
# Validates that sensitive environment files are properly secured

echo "🔒 ConcordBroker Environment Security Check"
echo "==========================================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check function
check_file() {
    local file=$1
    local status=$2
    
    if [ -f "$file" ]; then
        # Check if file is in git
        if git ls-files --error-unmatch "$file" 2>/dev/null; then
            echo -e "${RED}❌ CRITICAL: $file is tracked in git!${NC}"
            echo "   Run: git rm --cached $file"
            return 1
        else
            # Check file permissions
            if [ "$status" == "sensitive" ]; then
                perms=$(stat -c %a "$file" 2>/dev/null || stat -f %A "$file" 2>/dev/null)
                if [ "$perms" != "600" ] && [ "$perms" != "400" ]; then
                    echo -e "${YELLOW}⚠️  WARNING: $file has loose permissions ($perms)${NC}"
                    echo "   Run: chmod 600 $file"
                else
                    echo -e "${GREEN}✅ $file is secure${NC}"
                fi
            else
                echo -e "${GREEN}✅ $file exists (example/template)${NC}"
            fi
        fi
    else
        if [ "$status" == "required" ]; then
            echo -e "${YELLOW}⚠️  $file does not exist (may be needed for deployment)${NC}"
        fi
    fi
}

echo ""
echo "Checking sensitive environment files..."
echo "---------------------------------------"

# Check root level env files
check_file ".env" "sensitive"
check_file ".env.production" "sensitive"
check_file ".env.railway" "sensitive"
check_file ".env.supabase" "sensitive"
check_file ".env.local" "sensitive"

echo ""
echo "Checking app-specific env files..."
echo "-----------------------------------"

# Check app env files
check_file "apps/api/.env" "sensitive"
check_file "apps/api/.env.supabase" "sensitive"
check_file "apps/web/.env" "sensitive"
check_file "apps/web/.env.production" "sensitive"

echo ""
echo "Checking example/template files..."
echo "----------------------------------"

# Check example files (should be safe)
check_file ".env.example" "template"
check_file "apps/web/.env.example" "template"

echo ""
echo "Checking .gitignore configuration..."
echo "------------------------------------"

# Check if .gitignore properly excludes env files
if grep -q "^\.env$" .gitignore && grep -q "^\*\.env$" .gitignore; then
    echo -e "${GREEN}✅ .gitignore properly configured for .env files${NC}"
else
    echo -e "${RED}❌ .gitignore may not properly exclude .env files${NC}"
fi

echo ""
echo "Checking for exposed secrets in code..."
echo "---------------------------------------"

# Common patterns for exposed secrets
patterns=(
    "RAILWAY_TOKEN.*=.*['\"]2cfa9487"
    "SUPABASE_SERVICE_ROLE_KEY.*=.*['\"]eyJ"
    "JWT_SECRET.*=.*['\"]your-secret"
    "TWILIO_AUTH_TOKEN.*=.*['\"][a-f0-9]{32}"
    "SENDGRID_API_KEY.*=.*['\"]SG\."
    "OPENAI_API_KEY.*=.*['\"]sk-"
    "ANTHROPIC_API_KEY.*=.*['\"]sk-"
)

found_secrets=0
for pattern in "${patterns[@]}"; do
    if git grep -E "$pattern" -- ':!*.example*' ':!*.template*' ':!*.md' 2>/dev/null; then
        echo -e "${RED}❌ Potential secret found matching: $pattern${NC}"
        found_secrets=$((found_secrets + 1))
    fi
done

if [ $found_secrets -eq 0 ]; then
    echo -e "${GREEN}✅ No exposed secrets found in code${NC}"
fi

echo ""
echo "Security Recommendations:"
echo "------------------------"
echo "1. Never commit .env files with real credentials"
echo "2. Use Railway/Vercel dashboards for production secrets"
echo "3. Rotate all API keys regularly"
echo "4. Use different credentials for each environment"
echo "5. Enable 2FA on all service accounts"
echo ""

# Final status
if [ $found_secrets -eq 0 ]; then
    echo -e "${GREEN}✅ Environment security check passed!${NC}"
else
    echo -e "${RED}❌ Security issues found - please fix immediately!${NC}"
    exit 1
fi