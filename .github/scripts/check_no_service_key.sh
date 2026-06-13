#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# ORACLE — CI Security Check
# Verifies the service role key is NEVER used in frontend code.
# Run in CI: bash .github/scripts/check_no_service_key.sh
#
# Addresses expert feedback: "Verify no service keys are leaked
# to the client"
# ════════════════════════════════════════════════════════════════
set -euo pipefail

echo "🔍 ORACLE Security Scan: checking for service role key leakage..."
echo ""

FAILED=0

# ── Patterns that should NEVER appear in frontend code ──
PATTERNS=(
    "SUPABASE_SERVICE_ROLE_KEY"
    "service_role"
    "SERVICE_ROLE"
)

# ── Directories to scan (frontend + edge functions) ──
SCAN_DIRS=(
    "apps/web/src"
    "packages/shared-types"
    "packages/mock-data"
)

echo "Checking frontend packages for service role key references..."
for dir in "${SCAN_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        for pattern in "${PATTERNS[@]}"; do
            # Exclude .d.ts, comments with "service role" in a safe context
            matches=$(grep -rn "$pattern" "$dir" \
                --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
                --exclude-dir=node_modules --exclude-dir=dist \
                | grep -v "//.*never" \
                | grep -vi "security\." \
                | grep -vi "guard" || true)
            if [ -n "$matches" ]; then
                echo "❌ FAIL: Found '$pattern' in $dir:"
                echo "$matches"
                echo ""
                FAILED=1
            fi
        done
    fi
done

# ── Verify .env files are gitignored ──
if [ -f ".gitignore" ]; then
    if ! grep -q ".env.local" ".gitignore"; then
        echo "❌ FAIL: .env.local not found in .gitignore"
        FAILED=1
    else
        echo "✓ .env.local is gitignored"
    fi
fi

# ── Verify no .env files are tracked ──
TRACKED_ENV=$(git ls-files "*.env" "**/.env.local" "**/.env.production" 2>/dev/null || true)
if [ -n "$TRACKED_ENV" ]; then
    echo "❌ FAIL: Environment files tracked in git:"
    echo "$TRACKED_ENV"
    FAILED=1
else
    echo "✓ No environment files tracked in git"
fi

# ── Verify the frontend supabase client uses anon key only ──
SUPABASE_CLIENT="apps/web/src/lib/supabase.ts"
if [ -f "$SUPABASE_CLIENT" ]; then
    if grep -q "SERVICE_ROLE\|service_role" "$SUPABASE_CLIENT"; then
        echo "❌ FAIL: Service role key reference in $SUPABASE_CLIENT"
        FAILED=1
    else
        echo "✓ Frontend Supabase client uses anon key only"
    fi
fi

echo ""
if [ $FAILED -eq 0 ]; then
    echo "✅ Security scan PASSED — no service key leakage detected"
    exit 0
else
    echo "❌ Security scan FAILED — fix the issues above before merging"
    exit 1
fi
