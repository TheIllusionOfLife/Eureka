#!/bin/bash
# Comprehensive dependency verification script
# Prevents CI failures from dependency issues

set -e

echo "🔍 Comprehensive Dependency Check"
echo "=================================="

EXIT_CODE=0

# Function to check Python dependencies
check_python_deps() {
    echo ""
    echo "📦 Python Dependencies"
    echo "----------------------"
    
    local requirements_files=()
    
    # Find all requirements files
    while IFS= read -r -d '' file; do
        requirements_files+=("$file")
    done < <(find . -name "requirements*.txt" -not -path "./venv/*" -not -path "./.venv/*" -not -path "./node_modules/*" -print0)
    
    if [[ ${#requirements_files[@]} -eq 0 ]]; then
        echo "⚠️  No requirements.txt files found"
        return 0
    fi
    
    for req_file in "${requirements_files[@]}"; do
        echo "Checking: $req_file"
        
        # Create temporary environment
        temp_venv=$(mktemp -d)
        python3 -m venv "$temp_venv" >/dev/null 2>&1
        source "$temp_venv/bin/activate"
        
        # Upgrade pip silently
        pip install --upgrade pip >/dev/null 2>&1
        
        # Test installation
        if pip install -r "$req_file" >/dev/null 2>&1; then
            echo "  ✅ $req_file: OK"
        else
            echo "  ❌ $req_file: FAILED"
            echo "    Run: pip install -r $req_file"
            EXIT_CODE=1
        fi
        
        # Cleanup
        deactivate
        rm -rf "$temp_venv"
    done
}

# Function to check npm dependencies
check_npm_deps() {
    echo ""
    echo "📦 npm Dependencies"
    echo "-------------------"
    
    local package_dirs=()
    
    # Find directories with package.json (exclude node_modules subdirectories)
    while IFS= read -r -d '' file; do
        dir=$(dirname "$file")
        # Only include if it's not inside node_modules and not node_modules itself
        if [[ "$dir" != *"/node_modules"* ]]; then
            package_dirs+=("$dir")
        fi
    done < <(find . -name "package.json" -not -path "./node_modules/*" -print0)
    
    if [[ ${#package_dirs[@]} -eq 0 ]]; then
        echo "⚠️  No package.json files found"
        return 0
    fi
    
    for dir in "${package_dirs[@]}"; do
        echo "Checking: $dir/package.json"
        
        cd "$dir"
        
        if [[ ! -f "package-lock.json" ]]; then
            echo "  ⚠️  No package-lock.json found - run 'npm install' first"
            cd - >/dev/null
            continue
        fi
        
        # Check lock file consistency
        if npm ci --dry-run >/dev/null 2>&1; then
            echo "  ✅ Lock file consistent"
        else
            echo "  ❌ Lock file inconsistent with package.json"
            echo "    Run: npm install (to update lock file)"
            EXIT_CODE=1
        fi
        
        # Check for security vulnerabilities
        if npm audit --audit-level=moderate >/dev/null 2>&1; then
            echo "  ✅ No high-severity vulnerabilities"
        else
            echo "  ⚠️  Security vulnerabilities detected"
            echo "    Run: npm audit"
        fi
        
        cd - >/dev/null
    done
}

# Function to check GitHub Actions
check_github_actions() {
    echo ""
    echo "🔧 GitHub Actions"
    echo "-----------------"
    
    if [[ ! -d ".github/workflows" ]]; then
        echo "⚠️  No GitHub workflows found"
        return 0
    fi
    
    local deprecated_actions=(
        "actions/checkout@v3"
        "actions/setup-node@v3" 
        "actions/setup-python@v4"
        "actions/cache@v3"
        "actions/upload-artifact@v3"
    )
    
    local found_deprecated=false
    
    for workflow in .github/workflows/*.yml .github/workflows/*.yaml; do
        if [[ -f "$workflow" ]]; then
            for action in "${deprecated_actions[@]}"; do
                if grep -q "$action" "$workflow"; then
                    echo "  ⚠️  Deprecated action '$action' found in $(basename "$workflow")"
                    found_deprecated=true
                fi
            done
        fi
    done
    
    if [[ "$found_deprecated" == false ]]; then
        echo "  ✅ No deprecated actions found"
    else
        echo "    Consider updating to latest versions"
    fi
}

# Function to check Docker files
check_docker() {
    echo ""
    echo "🐳 Docker Configuration"
    echo "-----------------------"
    
    local docker_files=()
    
    # Find Dockerfiles and docker compose files
    while IFS= read -r -d '' file; do
        docker_files+=("$file")
    done < <(find . -name "Dockerfile*" -o -name "docker-compose*.yml" -o -name "docker-compose*.yaml" -not -path "./node_modules/*" -print0)
    
    if [[ ${#docker_files[@]} -eq 0 ]]; then
        echo "⚠️  No Docker files found"
        return 0
    fi
    
    for file in "${docker_files[@]}"; do
        echo "Checking: $file"
        
        # Basic syntax check for docker-compose files
        if [[ "$file" == *"docker-compose"* ]]; then
            if command -v docker >/dev/null 2>&1; then
                if docker compose -f "$file" config >/dev/null 2>&1; then
                    echo "  ✅ Valid docker compose syntax"
                else
                    echo "  ❌ Invalid docker compose syntax"
                    EXIT_CODE=1
                fi
            else
                echo "  ⚠️  docker not available for validation"
            fi
        fi
    done
}

# Function to check for common CI issues
check_common_issues() {
    echo ""
    echo "🔍 Common CI Issues"
    echo "-------------------"
    
    # Check for hardcoded API keys (basic check)
    if grep -r "api.key.*=" . --include="*.py" --include="*.js" --include="*.ts" --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git >/dev/null 2>&1; then
        echo "  ⚠️  Potential hardcoded API keys found"
        echo "    Review code for sensitive data"
    else
        echo "  ✅ No obvious hardcoded API keys"
    fi
    
    # Check for large files that might cause CI issues
    local large_files
    large_files=$(find . -type f -size +10M -not -path "./node_modules/*" -not -path "./.git/*" -not -path "./venv/*" 2>/dev/null || true)
    
    if [[ -n "$large_files" ]]; then
        echo "  ⚠️  Large files found (>10MB):"
        echo "$large_files" | sed 's/^/    /'
        echo "    Consider using Git LFS or .gitignore"
    else
        echo "  ✅ No problematic large files"
    fi
}

# Run all checks
echo "Starting comprehensive dependency verification..."

check_python_deps
check_npm_deps  
check_github_actions
check_docker
check_common_issues

echo ""
echo "=================================="
if [[ $EXIT_CODE -eq 0 ]]; then
    echo "✅ All dependency checks passed!"
else
    echo "❌ Some issues found - please review above"
fi
echo "=================================="

exit $EXIT_CODE