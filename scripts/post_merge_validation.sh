#!/bin/bash
# Post-merge validation script
# Run this after merging a PR to ensure system stability

set -euo pipefail

echo "🔍 Post-Merge Validation"
echo "======================"

# Create timestamp for reports
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="validation_reports"
mkdir -p "$REPORT_DIR"
REPORT_FILE="$REPORT_DIR/validation_${TIMESTAMP}.md"

# Initialize report
cat > "$REPORT_FILE" << EOF
# Post-Merge Validation Report
Generated: $(date)

## Summary
EOF

# Function to log to both console and report
log() {
    echo "$1"
    echo "$1" >> "$REPORT_FILE"
}

# Function to run and log tests
run_validation() {
    local name=$1
    local command=$2
    
    log ""
    log "### $name"
    log "\`\`\`bash"
    log "$ $command"
    log "\`\`\`"
    
    if eval "$command" >> "$REPORT_FILE" 2>&1; then
        log "✅ **Status**: Passed"
        return 0
    else
        log "❌ **Status**: Failed"
        return 1
    fi
}

# 1. Create validation branch
log "## Creating validation branch"
BRANCH_NAME="validation/${TIMESTAMP}"
git checkout -b "$BRANCH_NAME" || true

# 2. Mock mode tests
log "## Mock Mode Tests"
export MADSPARK_MODE=mock
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/src"

run_validation "CLI Mock Mode" "python3 -m madspark.cli.cli 'sustainable energy' 'budget constraints'"
run_validation "Core Tests" "pytest tests/test_agents.py tests/test_coordinator.py -v"

# 3. Docker deployment test
log "## Docker Deployment"
if command -v docker > /dev/null 2>&1; then
    run_validation "Docker Compose Config" "docker compose -f web/docker-compose.yml config"
    
    log "### Starting containers..."
    docker compose up -d >> "$REPORT_FILE" 2>&1
    sleep 10
    
    run_validation "Container Status" "docker compose ps"
    run_validation "API Health Check" "curl -s http://localhost:8000/api/health | jq"
    
    log "### Stopping containers..."
    docker compose down >> "$REPORT_FILE" 2>&1
else
    log "⚠️  Docker not available, skipping deployment test"
fi

# 4. Coverage check
log "## Test Coverage"
if command -v coverage > /dev/null 2>&1; then
    run_validation "Coverage Report" "coverage run -m pytest tests/ && coverage report"
else
    run_validation "Basic Test Run" "pytest tests/ -v --tb=short"
fi

# 5. Performance benchmark
log "## Performance Check"
cat > "temp_perf_test.py" << 'EOF'
import time
import asyncio
from madspark.core.async_coordinator import AsyncCoordinator

async def benchmark():
    coordinator = AsyncCoordinator()
    start = time.time()
    
    # Run a simple workflow
    result = await coordinator.run_workflow(
        theme="test",
        constraints="test",
        num_top_candidates=1
    )
    
    elapsed = time.time() - start
    print(f"Execution time: {elapsed:.2f}s")
    print(f"Results: {len(result)} ideas generated")
    
    # Basic performance assertion
    assert elapsed < 30, f"Performance regression: took {elapsed}s (max: 30s)"

if __name__ == "__main__":
    asyncio.run(benchmark())
EOF

run_validation "Performance Benchmark" "python temp_perf_test.py"
rm -f temp_perf_test.py

# 6. Generate summary
log ""
log "## Final Summary"
log "Validation completed at $(date)"

# Count failures in report
FAILURES=$(grep -c "❌" "$REPORT_FILE" || true)
PASSES=$(grep -c "✅" "$REPORT_FILE" || true)

log ""
log "- **Passed**: $PASSES checks"
log "- **Failed**: $FAILURES checks"

if [ "$FAILURES" -eq 0 ]; then
    log ""
    log "🎉 **Result**: All validations passed!"
    echo "✅ Validation successful! Report saved to: $REPORT_FILE"
    exit 0
else
    log ""
    log "⚠️  **Result**: Some validations failed. Please investigate."
    echo "❌ Validation failed with $FAILURES issues. Report saved to: $REPORT_FILE"
    exit 1
fi