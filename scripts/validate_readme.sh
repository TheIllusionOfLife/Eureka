#!/bin/bash
# README.md Validation Script
# Prevents outdated "Known Issues" and stale PR references from being committed

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Validating README.md..."

# Check if README exists
if [ ! -f "README.md" ]; then
    echo -e "${RED}❌ README.md not found${NC}"
    exit 1
fi

# Counter for issues
ISSUES=0
WARNINGS=0

# 1. Check for references to known fixed bugs
echo ""
echo "📋 Checking for references to known fixed bugs..."

# Define known fixed bugs (pattern|description pairs)
# This approach is more maintainable than hardcoded checks
KNOWN_FIXED_BUGS=(
    "Web Interface Enhanced Reasoning Bug|This bug was fixed in PR #161 (August 2025)"
    "Results stuck at 40%|This was a symptom of a bug fixed in PR #161 (August 2025)"
    "Blocker.*Enhanced reasoning bug|This blocker was removed in PR #161 (August 2025)"
)

# Check each known fixed bug pattern
for bug_entry in "${KNOWN_FIXED_BUGS[@]}"; do
    bug_pattern=$(echo "$bug_entry" | cut -d'|' -f1)
    bug_info=$(echo "$bug_entry" | cut -d'|' -f2)

    if grep -qE "$bug_pattern" README.md; then
        echo -e "${RED}❌ FAIL: README references a known fixed issue: '$bug_pattern'${NC}"
        echo -e "${YELLOW}   > $bug_info${NC}"
        ISSUES=$((ISSUES + 1))
    fi
done

# 2. Validate PR references exist
echo ""
echo "🔗 Validating PR references..."

# Extract all PR numbers from README
PR_NUMBERS=$(grep -o "PR #[0-9]\+" README.md | grep -o "[0-9]\+" | sort -u)

for PR in $PR_NUMBERS; do
    # Skip if gh command not available
    if ! command -v gh &> /dev/null; then
        echo -e "${YELLOW}⚠️  WARNING: gh CLI not found, skipping PR validation${NC}"
        WARNINGS=$((WARNINGS + 1))
        break
    fi

    # Check if PR exists
    # Note: Rate limits are unlikely for pre-commit hooks
    if ! gh pr view $PR &> /dev/null; then
        echo -e "${RED}❌ FAIL: PR #$PR referenced but doesn't exist${NC}"
        ISSUES=$((ISSUES + 1))
    fi
done

# 3. Check "Known Issues" section format
echo ""
echo "📝 Checking 'Known Issues' section..."

if grep -q "#### Known Issues / Blockers" README.md; then
    # Extract the Known Issues section (escape the / in section title)
    KNOWN_ISSUES=$(sed -n '/^#### Known Issues \/ Blockers/,/^####/p' README.md)

    # Check if it says "None currently" or lists actual issues
    if echo "$KNOWN_ISSUES" | grep -q "None currently"; then
        echo -e "${GREEN}✅ PASS: Known Issues marked as 'None currently'${NC}"
    else
        # There are issues listed - verify they're recent
        echo -e "${YELLOW}⚠️  WARNING: Known Issues section contains active issues${NC}"
        echo -e "${YELLOW}   Please verify these are still valid and not fixed in recent PRs${NC}"
        WARNINGS=$((WARNINGS + 1))

        # Show the issues
        echo "$KNOWN_ISSUES" | grep -E "^\*\*|^-" || true
    fi
else
    echo -e "${YELLOW}⚠️  WARNING: No 'Known Issues' section found${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# 4. Check for "Incomplete Testing Tasks"
echo ""
echo "🧪 Checking testing task status..."

if grep -q "Incomplete Testing Tasks" README.md; then
    if grep -B 2 -A 10 "Incomplete Testing Tasks" README.md | grep -q "Enhanced reasoning bug prevents full testing"; then
        echo -e "${RED}❌ FAIL: References enhanced reasoning bug as blocker for testing${NC}"
        echo -e "${YELLOW}   Bug was fixed in PR #161${NC}"
        ISSUES=$((ISSUES + 1))
    fi
fi

# 5. Check for outdated timestamps in session handover
echo ""
echo "📅 Checking session handover timestamps..."

if grep -q "### Last Updated:" README.md; then
    LAST_UPDATED=$(grep "### Last Updated:" README.md | head -1)
    echo "   Found: $LAST_UPDATED"

    # Note: Date parsing in bash is complex and brittle
    # For now, just show the timestamp without validation
    # Consider using a Python script if robust date validation is needed
    echo "   ℹ️  Timestamp verification requires manual review"
else
    echo -e "${YELLOW}⚠️  WARNING: No 'Last Updated' timestamp found in session handover${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Summary
echo ""
echo "═══════════════════════════════════════"
if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ README validation PASSED${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  $WARNINGS warning(s) found - please review${NC}"
    fi
    echo "═══════════════════════════════════════"
    exit 0
else
    echo -e "${RED}❌ README validation FAILED${NC}"
    echo -e "${RED}   $ISSUES error(s) found${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}   $WARNINGS warning(s) found${NC}"
    fi
    echo "═══════════════════════════════════════"
    echo ""
    echo "Please fix the issues above before committing."
    echo "See .github/DOCUMENTATION_CHECKLIST.md for guidelines."
    exit 1
fi
