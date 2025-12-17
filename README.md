# Azure Functions - Cost Management

This repository contains Azure Functions written in Python to help manage and optimize Azure costs by identifying high-cost resources and providing automated shutdown capabilities.

## Functions

### CostManager

An HTTP-triggered Azure Function that identifies the Azure resources generating the most cost and can shut them down to reduce expenses.

#### Features

- **Cost Analysis**: Query Azure Cost Management API to identify top cost-generating resources
- **Resource Details**: Get detailed information about resources including name, type, location, and resource group
- **Automated Shutdown**: Stop/deallocate high-cost resources (currently supports Virtual Machines)
- **Flexible Time Periods**: Analyzes costs over the last 30 days
- **RESTful API**: Easy integration with other systems and workflows

#### Supported Resource Types for Shutdown

- Virtual Machines (deallocate/stop)
- Future support planned for: SQL Databases, App Services, and other compute resources

## Prerequisites

- Python 3.8 or later
- Azure subscription
- Azure Functions Core Tools (optional, for local development)
- Azure CLI (for authentication and deployment)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Authentication

The function uses `DefaultAzureCredential` which supports multiple authentication methods:

- **Managed Identity** (recommended for production)
- **Azure CLI** (for local development): Run `az login`
- **Environment Variables**: Set `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, and `AZURE_CLIENT_SECRET`

### 3. Configure Environment Variables

Create a `local.settings.json` file (for local development):

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_SUBSCRIPTION_ID": "your-subscription-id-here"
  }
}
```

### 4. Grant Required Permissions

The function requires the following Azure RBAC roles:

- **Cost Management Reader**: To query cost data
- **Reader**: To get resource details
- **Virtual Machine Contributor**: To stop/deallocate VMs (only if using shutdown feature)

Assign these roles to the Managed Identity or Service Principal used by the function:

```bash
# Example: Assign roles to a managed identity
az role assignment create --assignee <managed-identity-principal-id> \
  --role "Cost Management Reader" \
  --scope /subscriptions/<subscription-id>

az role assignment create --assignee <managed-identity-principal-id> \
  --role "Reader" \
  --scope /subscriptions/<subscription-id>

az role assignment create --assignee <managed-identity-principal-id> \
  --role "Virtual Machine Contributor" \
  --scope /subscriptions/<subscription-id>
```

## Usage

### API Endpoints

#### 1. Analyze Costs (Default)

Get a list of resources with the highest costs:

```bash
# Using query parameters
curl "https://<function-app-name>.azurewebsites.net/api/CostManager?code=<function-key>&subscription_id=<subscription-id>&top=10"

# Using POST with JSON body
curl -X POST "https://<function-app-name>.azurewebsites.net/api/CostManager?code=<function-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "subscription_id": "<subscription-id>",
    "top": 10,
    "action": "analyze"
  }'
```

**Response:**

```json
{
  "action": "analyze",
  "subscription_id": "12345678-1234-1234-1234-123456789abc",
  "top_resources": [
    {
      "resource_id": "/subscriptions/.../resourceGroups/rg1/providers/Microsoft.Compute/virtualMachines/vm1",
      "cost": 1250.75,
      "resource_name": "vm1",
      "resource_type": "Microsoft.Compute/virtualMachines",
      "location": "eastus",
      "resource_group": "rg1"
    }
  ],
  "total_resources_analyzed": 10,
  "message": "Found 10 resources with cost data"
}
```

#### 2. Shutdown Resources

Stop specific resources to reduce costs:

```bash
curl -X POST "https://<function-app-name>.azurewebsites.net/api/CostManager?code=<function-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "subscription_id": "<subscription-id>",
    "action": "shutdown",
    "resource_ids": "/subscriptions/.../virtualMachines/vm1,/subscriptions/.../virtualMachines/vm2"
  }'
```

**Response:**

```json
{
  "action": "shutdown",
  "subscription_id": "12345678-1234-1234-1234-123456789abc",
  "shutdown_results": [
    {
      "resource_id": "/subscriptions/.../virtualMachines/vm1",
      "status": "success",
      "message": "VM 'vm1' deallocated successfully",
      "resource_type": "Virtual Machine"
    }
  ],
  "total_resources_processed": 1
}
```

### Query Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `subscription_id` | Yes* | - | Azure subscription ID to analyze. *Can be set via `AZURE_SUBSCRIPTION_ID` environment variable |
| `top` | No | 10 | Number of top cost resources to return |
| `action` | No | analyze | Action to perform: `analyze` or `shutdown` |
| `resource_ids` | Conditional | - | Comma-separated resource IDs (required for `shutdown` action) |

## Local Development

### Run Locally

1. Install Azure Functions Core Tools
2. Start the function:

```bash
func start
```

3. Test the endpoint:

```bash
curl "http://localhost:7071/api/CostManager?subscription_id=<your-subscription-id>&top=5"
```

## Deployment

### Deploy to Azure

1. Create a Function App:

```bash
az functionapp create \
  --resource-group <resource-group> \
  --consumption-plan-location <location> \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name <function-app-name> \
  --storage-account <storage-account>
```

2. Enable Managed Identity:

```bash
az functionapp identity assign \
  --name <function-app-name> \
  --resource-group <resource-group>
```

3. Deploy the function:

```bash
func azure functionapp publish <function-app-name>
```

4. Set environment variables:

```bash
az functionapp config appsettings set \
  --name <function-app-name> \
  --resource-group <resource-group> \
  --settings AZURE_SUBSCRIPTION_ID=<subscription-id>
```

## Architecture

```
┌─────────────────┐
│   HTTP Request  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│   CostManager Function      │
│  ┌──────────────────────┐   │
│  │ 1. Parse Request     │   │
│  └──────────────────────┘   │
│  ┌──────────────────────┐   │
│  │ 2. Authenticate      │   │
│  │    (DefaultAzure     │   │
│  │     Credential)      │   │
│  └──────────────────────┘   │
│  ┌──────────────────────┐   │
│  │ 3. Query Costs       │◄──┼──► Cost Management API
│  └──────────────────────┘   │
│  ┌──────────────────────┐   │
│  │ 4. Get Resource Info │◄──┼──► Resource Manager API
│  └──────────────────────┘   │
│  ┌──────────────────────┐   │
│  │ 5. Shutdown (opt)    │◄──┼──► Compute API
│  └──────────────────────┘   │
└─────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  JSON Response  │
└─────────────────┘
```

## Security Considerations

- **Authentication**: Function uses function-level authentication (auth level set to "function")
- **Least Privilege**: Only grant necessary permissions to the Managed Identity
- **Audit Logs**: All resource shutdowns are logged and can be audited
- **Manual Approval**: Consider implementing manual approval workflow before shutting down critical resources
- **Testing**: Always test on non-production resources first

## Cost Optimization Best Practices

1. **Schedule Regular Analysis**: Run cost analysis daily or weekly to identify trends
2. **Set Budgets**: Use Azure Cost Management budgets to get alerts
3. **Automate Dev/Test Shutdown**: Automatically stop dev/test resources outside business hours
4. **Review Before Shutdown**: Always review the cost analysis before shutting down resources
5. **Tag Resources**: Use tags to categorize resources and exclude critical ones from automation

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Ensure you're logged in via `az login` for local development
   - Verify Managed Identity is enabled for the Function App
   - Check that required RBAC roles are assigned

2. **No Cost Data Returned**
   - Verify the subscription has cost data (may take 24-48 hours for new resources)
   - Check that Cost Management Reader role is assigned
   - Ensure the time period has activity

3. **Shutdown Failed**
   - Verify the resource type is supported (currently only VMs)
   - Check that Virtual Machine Contributor role is assigned
   - Ensure the resource exists and is in a state that can be stopped

## Future Enhancements

- [ ] Support for additional resource types (SQL Databases, App Services, AKS clusters)
- [ ] Integration with Azure Logic Apps for workflow automation
- [ ] Cost forecasting and trend analysis
- [ ] Slack/Teams notifications for high-cost alerts
- [ ] Scheduled automatic shutdowns with exclusion lists
- [ ] Cost anomaly detection

## Contributing

Contributions are welcome! Please ensure your code follows the existing style and includes appropriate error handling and logging.

## License

MIT License - see LICENSE file for details