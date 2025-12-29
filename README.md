# Azure Functions - Remove Global Administrators

An Azure Function written in Python that removes all users from the Global Administrator group using Microsoft Graph API.

## Overview

This Azure Function provides a secure, HTTP-triggered endpoint to remove all users from the Global Administrator role in Azure AD. It uses Microsoft Graph API with application permissions to manage directory roles.

## Prerequisites

- Azure subscription
- Azure AD tenant
- Python 3.8 or higher
- Azure Functions Core Tools (for local development)

## Setup

### 1. Register an Azure AD Application

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Provide a name (e.g., "RemoveGlobalAdminsFunction")
5. Click **Register**

### 2. Configure API Permissions & IAM Roles

Add the following Microsoft Graph **Application permissions** (not delegated):
- `RoleManagement.ReadWrite.Directory` - Required to remove users from roles
- `Directory.Read.All` - Required to read directory role members

After adding permissions, click **Grant admin consent** for your tenant.

Open the subscription you would like to provide access to
Navigate to **Access control (IAM)** > **Role Assignments**
Add the following role assignments to the app registration you created in Step 1
- `Billing Reader` - Required to see the resource utilization cost
- `Resource Policy Contributer` - Required to create the policy to deny new resource creation


### 3. Create a Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Click **New client secret**
3. Add a description and select an expiration period
4. Click **Add**
5. **Important**: Copy the secret value immediately (it won't be shown again)

### 4. Configure Environment Variables

Update the `local.settings.json` file (for local development) or configure Application Settings in Azure:
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
    "AzureWebJobsStorage": "",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_TENANT_ID": "<your-tenant-id>",
    "AZURE_CLIENT_ID": "<your-application-client-id>",
    "AZURE_CLIENT_SECRET": "<your-client-secret>"
  }
}
```

**Note**: Never commit `local.settings.json` with real credentials to source control.

## Installation

### Install Dependencies

```bash
pip install -r requirements.txt
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_SUBSCRIPTION_ID": "your-subscription-id-here",
    "AZURE_RESOURCE_API_VERSION": "2023-07-01",
    "VM_SHUTDOWN_TIMEOUT": "300"
  }
}
```

#### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_RESOURCE_API_VERSION` | `2023-07-01` | API version for Azure Resource Manager queries |
| `VM_SHUTDOWN_TIMEOUT` | `300` | Timeout in seconds for VM shutdown operations |

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

### Local Development

1. Start the function locally:
```bash
func start
```

2. Trigger the function with a POST request:
```bash
curl -X POST http://localhost:7071/api/RemoveGlobalAdmins
```

### Azure Deployment

1. Create a Function App in Azure Portal
2. Deploy using Azure Functions Core Tools:
```bash
func azure functionapp publish <your-function-app-name>
```

3. Configure the required environment variables in Azure Portal under **Configuration** > **Application settings**

### Triggering the Function

The function is triggered via HTTP POST request. Authentication is handled via function key:

```bash
curl -X POST https://<your-function-app>.azurewebsites.net/api/RemoveGlobalAdmins?code=<function-key>
```

### Response Format

Success response:
```json
{
  "status": "completed",
  "removedUsers": [
    {
      "id": "user-id-1",
      "displayName": "User One"
    },
    {
      "id": "user-id-2",
      "displayName": "User Two"
    }
  ],
  "totalRemoved": 2,
  "errors": null
}
```

Error response:
```json
{
  "error": "Error message description"
}
```

## Function Details

### RemoveGlobalAdmins

- **Trigger**: HTTP POST
- **Authentication Level**: Function key required
- **Functionality**: 
  1. Authenticates with Microsoft Graph API using service principal credentials
  2. Retrieves all members of the Global Administrator role (using well-known role ID)
  3. Removes each user from the role
  4. Returns a list of removed users and any errors encountered

### Global Administrator Role ID

The function uses the well-known Global Administrator role template ID: `62e90394-69f5-4237-9190-012177145e10`. This ID is constant across all Azure AD tenants.

## Security Considerations

1. **Credentials**: Store credentials securely using Azure Key Vault or Azure App Configuration
2. **Function Key**: Keep the function key secure - this is the only authentication for the HTTP endpoint
3. **Least Privilege**: The service principal should only have the minimum required permissions
4. **Audit Logging**: Review Azure AD audit logs after running this function
5. **Testing**: Test thoroughly in a non-production environment first
6. **Backup Admins**: Ensure you have alternative admin access (e.g., break-glass account) before running

## Error Handling

The function includes comprehensive error handling:
- Validates environment variables before execution
- Catches and logs individual member removal failures
- Returns detailed error messages in JSON format
- Continues processing remaining users if one fails

## Logging

The function logs detailed information about its execution:
- Function trigger events
- Number of Global Administrator members found
- Each user removal attempt (success/failure)
- Final count of removed users

View logs in:
- Local development: Console output
- Azure: Application Insights or Streaming logs in Azure Portal

## Limitations

- Only removes **user** objects from the role (skips service principals and groups)
- Requires appropriate Microsoft Graph API permissions
- Execution time may vary based on the number of Global Administrators

## Contributing

Feel free to submit issues or pull requests to improve this function.

## License

This project is provided as-is for educational and operational purposes.
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
