#!/bin/bash
# Test script for Cost Manager Azure Function
# Usage: ./test_function.sh [local|azure] [subscription_id]

set -e

MODE=${1:-local}
SUBSCRIPTION_ID=${2:-$AZURE_SUBSCRIPTION_ID}

if [ -z "$SUBSCRIPTION_ID" ]; then
    echo "Error: SUBSCRIPTION_ID not provided"
    echo "Usage: ./test_function.sh [local|azure] [subscription_id]"
    echo "Or set AZURE_SUBSCRIPTION_ID environment variable"
    exit 1
fi

if [ "$MODE" == "local" ]; then
    BASE_URL="http://localhost:7071/api/CostManager"
    echo "Testing local function..."
elif [ "$MODE" == "azure" ]; then
    if [ -z "$FUNCTION_APP_NAME" ]; then
        echo "Error: FUNCTION_APP_NAME environment variable not set"
        exit 1
    fi
    if [ -z "$FUNCTION_KEY" ]; then
        echo "Error: FUNCTION_KEY environment variable not set"
        exit 1
    fi
    BASE_URL="https://${FUNCTION_APP_NAME}.azurewebsites.net/api/CostManager?code=${FUNCTION_KEY}"
    echo "Testing Azure function..."
else
    echo "Invalid mode: $MODE. Use 'local' or 'azure'"
    exit 1
fi

echo ""
echo "=== Test 1: Analyze top 5 cost resources ==="
curl -s -X GET "${BASE_URL}&subscription_id=${SUBSCRIPTION_ID}&top=5" | jq .

echo ""
echo "=== Test 2: Analyze top 10 cost resources (POST) ==="
curl -s -X POST "${BASE_URL}" \
    -H "Content-Type: application/json" \
    -d "{
        \"subscription_id\": \"${SUBSCRIPTION_ID}\",
        \"top\": 10,
        \"action\": \"analyze\"
    }" | jq .

echo ""
echo "Tests completed!"
echo ""
echo "To test shutdown functionality, use:"
echo "curl -X POST '${BASE_URL}' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"subscription_id\": \"${SUBSCRIPTION_ID}\", \"action\": \"shutdown\", \"resource_ids\": \"<resource-id>\"}'"
