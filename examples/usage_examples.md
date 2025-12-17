# Usage Examples

This document provides practical examples for using the Cost Manager Azure Function.

## Prerequisites

- Azure subscription with active resources
- Function deployed to Azure or running locally
- Appropriate RBAC permissions configured

## Example 1: Get Top 10 Cost Resources

Find the 10 resources with the highest costs in the last 30 days:

```bash
curl -X GET "https://your-function-app.azurewebsites.net/api/CostManager?code=YOUR_FUNCTION_KEY" \
  -G \
  --data-urlencode "subscription_id=12345678-1234-1234-1234-123456789abc" \
  --data-urlencode "top=10"
```

**Response:**
```json
{
  "action": "analyze",
  "subscription_id": "12345678-1234-1234-1234-123456789abc",
  "top_resources": [
    {
      "resource_id": "/subscriptions/12345678.../virtualMachines/expensive-vm",
      "cost": 2450.50,
      "resource_name": "expensive-vm",
      "resource_type": "Microsoft.Compute/virtualMachines",
      "location": "eastus",
      "resource_group": "production-rg"
    }
  ],
  "total_resources_analyzed": 10,
  "message": "Found 10 resources with cost data"
}
```

## Example 2: Analyze Specific Number of Resources

Get top 20 cost resources:

```bash
curl -X POST "https://your-function-app.azurewebsites.net/api/CostManager?code=YOUR_FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "subscription_id": "12345678-1234-1234-1234-123456789abc",
    "top": 20,
    "action": "analyze"
  }'
```

## Example 3: Shutdown a Single VM

Deallocate a specific virtual machine to save costs:

```bash
curl -X POST "https://your-function-app.azurewebsites.net/api/CostManager?code=YOUR_FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "subscription_id": "12345678-1234-1234-1234-123456789abc",
    "action": "shutdown",
    "resource_ids": "/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/dev-rg/providers/Microsoft.Compute/virtualMachines/dev-vm-01"
  }'
```

**Response:**
```json
{
  "action": "shutdown",
  "subscription_id": "12345678-1234-1234-1234-123456789abc",
  "shutdown_results": [
    {
      "resource_id": "/subscriptions/.../virtualMachines/dev-vm-01",
      "status": "success",
      "message": "VM 'dev-vm-01' deallocated successfully",
      "resource_type": "Virtual Machine"
    }
  ],
  "total_resources_processed": 1
}
```

## Example 4: Shutdown Multiple VMs

Deallocate multiple virtual machines at once:

```bash
curl -X POST "https://your-function-app.azurewebsites.net/api/CostManager?code=YOUR_FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "subscription_id": "12345678-1234-1234-1234-123456789abc",
    "action": "shutdown",
    "resource_ids": "/subscriptions/12345678.../virtualMachines/vm1,/subscriptions/12345678.../virtualMachines/vm2,/subscriptions/12345678.../virtualMachines/vm3"
  }'
```

## Example 5: Using with Azure Logic Apps

Create a scheduled workflow to identify high-cost resources daily:

1. Create a Logic App with a Recurrence trigger (daily at 9 AM)
2. Add an HTTP action:
   - Method: POST
   - URI: `https://your-function-app.azurewebsites.net/api/CostManager?code=YOUR_FUNCTION_KEY`
   - Headers: `Content-Type: application/json`
   - Body:
     ```json
     {
       "subscription_id": "@parameters('subscriptionId')",
       "top": 15,
       "action": "analyze"
     }
     ```
3. Add a condition to check if total cost > threshold
4. Send email notification with top resources

## Example 6: PowerShell Script Integration

Create a scheduled task to analyze costs and shutdown dev resources after hours:

```powershell
# analyze-and-shutdown.ps1
$functionUrl = "https://your-function-app.azurewebsites.net/api/CostManager"
$functionKey = "YOUR_FUNCTION_KEY"
$subscriptionId = "12345678-1234-1234-1234-123456789abc"

# Get top cost resources
$analyzeBody = @{
    subscription_id = $subscriptionId
    top = 10
    action = "analyze"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "$functionUrl`?code=$functionKey" `
    -Method Post `
    -ContentType "application/json" `
    -Body $analyzeBody

Write-Host "Top 10 cost resources:"
$response.top_resources | Format-Table

# Shutdown dev VMs (example - customize as needed)
$devVMs = $response.top_resources | Where-Object { 
    $_.resource_group -like "*dev*" -and 
    $_.resource_type -eq "Microsoft.Compute/virtualMachines" 
}

if ($devVMs.Count -gt 0) {
    $resourceIds = ($devVMs.resource_id -join ",")
    
    $shutdownBody = @{
        subscription_id = $subscriptionId
        action = "shutdown"
        resource_ids = $resourceIds
    } | ConvertTo-Json
    
    $shutdownResponse = Invoke-RestMethod -Uri "$functionUrl`?code=$functionKey" `
        -Method Post `
        -ContentType "application/json" `
        -Body $shutdownBody
    
    Write-Host "Shutdown results:"
    $shutdownResponse.shutdown_results | Format-Table
}
```

## Example 7: Python Script for Cost Monitoring

Monitor costs and send alerts:

```python
import requests
import json
from datetime import datetime

FUNCTION_URL = "https://your-function-app.azurewebsites.net/api/CostManager"
FUNCTION_KEY = "YOUR_FUNCTION_KEY"
SUBSCRIPTION_ID = "12345678-1234-1234-1234-123456789abc"
COST_THRESHOLD = 1000.0  # Alert if any resource costs more than $1000

def analyze_costs():
    """Analyze costs and return high-cost resources"""
    payload = {
        "subscription_id": SUBSCRIPTION_ID,
        "top": 20,
        "action": "analyze"
    }
    
    response = requests.post(
        f"{FUNCTION_URL}?code={FUNCTION_KEY}",
        json=payload
    )
    
    return response.json()

def main():
    print(f"Analyzing costs at {datetime.now()}")
    
    result = analyze_costs()
    
    # Check for high-cost resources
    high_cost_resources = [
        r for r in result.get('top_resources', [])
        if r['cost'] > COST_THRESHOLD
    ]
    
    if high_cost_resources:
        print(f"\n⚠️  WARNING: {len(high_cost_resources)} resources exceed ${COST_THRESHOLD}")
        for resource in high_cost_resources:
            print(f"  - {resource['resource_name']}: ${resource['cost']:.2f}")
            print(f"    Type: {resource['resource_type']}")
            print(f"    Location: {resource['location']}")
    else:
        print("✓ All resources are within cost thresholds")
    
    # Print summary
    total_cost = sum(r['cost'] for r in result.get('top_resources', []))
    print(f"\nTotal cost for top {len(result.get('top_resources', []))} resources: ${total_cost:.2f}")

if __name__ == "__main__":
    main()
```

## Example 8: Bash Script for Automated Cleanup

Schedule a cron job to automatically shutdown non-production VMs:

```bash
#!/bin/bash
# cleanup-nonprod-vms.sh

FUNCTION_URL="https://your-function-app.azurewebsites.net/api/CostManager"
FUNCTION_KEY="YOUR_FUNCTION_KEY"
SUBSCRIPTION_ID="12345678-1234-1234-1234-123456789abc"

# Get top cost resources
RESPONSE=$(curl -s -X POST "${FUNCTION_URL}?code=${FUNCTION_KEY}" \
    -H "Content-Type: application/json" \
    -d "{
        \"subscription_id\": \"${SUBSCRIPTION_ID}\",
        \"top\": 50,
        \"action\": \"analyze\"
    }")

# Extract VM resource IDs from dev/test resource groups
DEV_VMS=$(echo $RESPONSE | jq -r '.top_resources[] | 
    select(.resource_type == "Microsoft.Compute/virtualMachines" and 
           (.resource_group | contains("dev") or contains("test"))) | 
    .resource_id' | paste -sd "," -)

if [ -n "$DEV_VMS" ]; then
    echo "Shutting down dev/test VMs..."
    curl -s -X POST "${FUNCTION_URL}?code=${FUNCTION_KEY}" \
        -H "Content-Type: application/json" \
        -d "{
            \"subscription_id\": \"${SUBSCRIPTION_ID}\",
            \"action\": \"shutdown\",
            \"resource_ids\": \"${DEV_VMS}\"
        }" | jq .
else
    echo "No dev/test VMs found to shutdown"
fi
```

Add to crontab to run every weekday at 6 PM:
```
0 18 * * 1-5 /path/to/cleanup-nonprod-vms.sh >> /var/log/azure-cleanup.log 2>&1
```

## Example 9: Error Handling

Handle common error scenarios:

```python
import requests

def call_cost_manager(action, **kwargs):
    """Wrapper with error handling"""
    try:
        response = requests.post(
            f"{FUNCTION_URL}?code={FUNCTION_KEY}",
            json={"action": action, **kwargs},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print("Request timed out. The operation may still be processing.")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        if response.status_code == 400:
            print("Bad request. Check your parameters.")
        elif response.status_code == 401:
            print("Authentication failed. Check your function key.")
        elif response.status_code == 500:
            print("Server error. Check function logs.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    return None

# Usage
result = call_cost_manager("analyze", subscription_id=SUBSCRIPTION_ID, top=10)
if result:
    print(result)
```

## Tips for Production Use

1. **Use Environment Variables**: Store function keys and subscription IDs securely
2. **Implement Retry Logic**: Network calls can fail; implement exponential backoff
3. **Log All Operations**: Keep audit trail of all shutdown operations
4. **Test First**: Always test with non-critical resources first
5. **Set Up Alerts**: Configure alerts for failed function executions
6. **Use Tags**: Tag resources to exclude critical ones from automation
7. **Schedule Wisely**: Run analysis during off-peak hours to minimize API throttling
