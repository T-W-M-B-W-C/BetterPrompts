#!/bin/bash
# Generate combined coverage report across all services

set -e

COVERAGE_DIR="${COVERAGE_DIR:-/app/coverage}"
RESULTS_DIR="${RESULTS_DIR:-/app/test-results}"
COVERAGE_THRESHOLD="${COVERAGE_THRESHOLD:-80}"

echo "📊 Generating Combined Coverage Report"
echo "====================================="

# Create report directory
mkdir -p "$RESULTS_DIR/coverage-report"

# Function to extract coverage percentage
get_coverage() {
    local file=$1
    local type=$2
    
    case $type in
        "go")
            if [ -f "$file" ]; then
                go tool cover -func="$file" | tail -1 | awk '{print $3}' | sed 's/%//'
            else
                echo "0"
            fi
            ;;
        "xml")
            if [ -f "$file" ]; then
                grep -oP 'line-rate="\K[^"]+' "$file" | head -1 | awk '{print $1 * 100}'
            else
                echo "0"
            fi
            ;;
        "json")
            if [ -f "$file" ]; then
                jq -r '.total.lines.pct // 0' "$file" 2>/dev/null || echo "0"
            else
                echo "0"
            fi
            ;;
    esac
}

# Collect coverage data
declare -A COVERAGE_DATA

# Go services
COVERAGE_DATA["api-gateway"]=$(get_coverage "$COVERAGE_DIR/api-gateway.coverage" "go")
COVERAGE_DATA["technique-selector"]=$(get_coverage "$COVERAGE_DIR/technique-selector.coverage" "go")

# Python services
COVERAGE_DATA["intent-classifier"]=$(get_coverage "$COVERAGE_DIR/intent-classifier.xml" "xml")
COVERAGE_DATA["prompt-generator"]=$(get_coverage "$COVERAGE_DIR/prompt-generator.xml" "xml")

# Frontend
if [ -f "$COVERAGE_DIR/frontend/coverage-summary.json" ]; then
    COVERAGE_DATA["frontend"]=$(get_coverage "$COVERAGE_DIR/frontend/coverage-summary.json" "json")
else
    COVERAGE_DATA["frontend"]="0"
fi

# ML Pipeline
COVERAGE_DATA["ml-pipeline"]=$(get_coverage "$COVERAGE_DIR/ml-pipeline.xml" "xml")

# Calculate total coverage
TOTAL_COVERAGE=0
SERVICE_COUNT=0

for service in "${!COVERAGE_DATA[@]}"; do
    coverage="${COVERAGE_DATA[$service]}"
    if [ "$coverage" != "0" ]; then
        TOTAL_COVERAGE=$(echo "$TOTAL_COVERAGE + $coverage" | bc)
        SERVICE_COUNT=$((SERVICE_COUNT + 1))
    fi
done

if [ $SERVICE_COUNT -gt 0 ]; then
    AVERAGE_COVERAGE=$(echo "scale=2; $TOTAL_COVERAGE / $SERVICE_COUNT" | bc)
else
    AVERAGE_COVERAGE=0
fi

# Generate HTML report
cat > "$RESULTS_DIR/coverage-report/index.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>BetterPrompts Test Coverage Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .good { color: green; font-weight: bold; }
        .warning { color: orange; font-weight: bold; }
        .bad { color: red; font-weight: bold; }
        .summary { background-color: #e7f3ff; padding: 15px; margin: 20px 0; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>📊 BetterPrompts Test Coverage Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Overall Coverage:</strong> <span class="$([ ${AVERAGE_COVERAGE%.*} -ge $COVERAGE_THRESHOLD ] && echo "good" || echo "bad")">${AVERAGE_COVERAGE}%</span></p>
        <p><strong>Coverage Threshold:</strong> ${COVERAGE_THRESHOLD}%</p>
        <p><strong>Generated:</strong> $(date)</p>
    </div>
    
    <h2>Service Coverage</h2>
    <table>
        <tr>
            <th>Service</th>
            <th>Coverage</th>
            <th>Status</th>
        </tr>
EOF

# Add service rows
for service in "${!COVERAGE_DATA[@]}"; do
    coverage="${COVERAGE_DATA[$service]}"
    coverage_int=${coverage%.*}
    
    if [ "$coverage_int" -ge "$COVERAGE_THRESHOLD" ]; then
        status="✅ Pass"
        class="good"
    elif [ "$coverage_int" -ge $((COVERAGE_THRESHOLD - 10)) ]; then
        status="⚠️ Warning"
        class="warning"
    else
        status="❌ Fail"
        class="bad"
    fi
    
    echo "        <tr>" >> "$RESULTS_DIR/coverage-report/index.html"
    echo "            <td>$service</td>" >> "$RESULTS_DIR/coverage-report/index.html"
    echo "            <td class=\"$class\">${coverage}%</td>" >> "$RESULTS_DIR/coverage-report/index.html"
    echo "            <td>$status</td>" >> "$RESULTS_DIR/coverage-report/index.html"
    echo "        </tr>" >> "$RESULTS_DIR/coverage-report/index.html"
done

cat >> "$RESULTS_DIR/coverage-report/index.html" << EOF
    </table>
    
    <h2>Detailed Reports</h2>
    <ul>
        <li><a href="../api-gateway-results.txt">API Gateway Test Results</a></li>
        <li><a href="../intent-classifier-results.xml">Intent Classifier Test Results</a></li>
        <li><a href="../technique-selector-results.txt">Technique Selector Test Results</a></li>
        <li><a href="../prompt-generator-results.xml">Prompt Generator Test Results</a></li>
        <li><a href="../frontend/lcov-report/index.html">Frontend Coverage Details</a></li>
    </ul>
</body>
</html>
EOF

# Print summary to console
echo ""
echo "Service Coverage Summary:"
echo "========================"
printf "%-20s %10s\n" "Service" "Coverage"
echo "------------------------"

for service in "${!COVERAGE_DATA[@]}"; do
    coverage="${COVERAGE_DATA[$service]}"
    printf "%-20s %9s%%\n" "$service" "$coverage"
done

echo "------------------------"
printf "%-20s %9s%%\n" "TOTAL" "$AVERAGE_COVERAGE"
echo ""

# Check if coverage meets threshold
if [ ${AVERAGE_COVERAGE%.*} -ge $COVERAGE_THRESHOLD ]; then
    echo "✅ Coverage threshold met! ($AVERAGE_COVERAGE% >= $COVERAGE_THRESHOLD%)"
    exit 0
else
    echo "❌ Coverage below threshold! ($AVERAGE_COVERAGE% < $COVERAGE_THRESHOLD%)"
    exit 1
fi