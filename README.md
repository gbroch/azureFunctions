# Azure Functions - Cost Management & Governance

This repository contains Azure Functions written in Python to help manage Azure costs, enforce governance policies, and manage Azure AD security roles.

## Overview

This project includes four Azure Functions:

1. **CostManager** - Identifies high-cost Azure resources and can shut them down to reduce expenses
2. **CreateBudgetPolicy** - Creates an Azure Policy to deny new resource creation when budget limits are reached
3. **AssignBudgetPolicy** - Assigns the budget policy to a subscription or resource group to enforce it
4. **RemoveGlobalAdmins** - Removes all users from the Global Administrator role in Azure AD

## Prerequisites

- Python 3.8 or higher
- Azure subscription
- Azure AD tenant
- Azure Functions Core Tools (for local development)
- Azure CLI (for authentication and deployment)

## Initial Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Register an Azure AD Application

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Provide a name (e.g., "AzureFunctionsApp")
5. Click **Register**

### 3. Configure API Permissions

Add the following Microsoft Graph **Application permissions** (not delegated):
- `RoleManagement.ReadWrite.Directory` - Required to manage directory roles
- `Directory.Read.All` - Required to read directory information

After adding permissions, click **Grant admin consent** for your tenant.

### 4. Configure IAM Roles

Navigate to your Azure subscription:
1. Go to **Access control (IAM)** > **Role Assignments**
2. Add the following role assignments to the app registration:
   - `Cost Management Reader` - Required to query cost data
   - `Reader` - Required to get resource details
   - `Resource Policy Contributor` - Required to create policy definitions
   - `Virtual Machine Contributor` - Required to stop/deallocate VMs (optional)

### 5. Create a Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Click **New client secret**
3. Add a description and select an expiration period
4. Click **Add**
5. **Important**: Copy the secret value immediately (it won't be shown again)

### 6. Configure Environment Variables

Create a `local.settings.json` file for local development:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_TENANT_ID": "<your-tenant-id>",
    "AZURE_CLIENT_ID": "<your-application-client-id>",
    "AZURE_CLIENT_SECRET": "<your-client-secret>",
    "AZURE_SUBSCRIPTION_ID": "<your-subscription-id>",
    "AZURE_RESOURCE_API_VERSION": "2023-07-01",
    "VM_SHUTDOWN_TIMEOUT": "300"
  }
}
```

**Note**: Never commit `local.settings.json` with real credentials to source control.

### 7. Local Development

Start the function locally:

```bash
func start
```

### 8. Azure Deployment

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

3. Deploy the functions:

```bash
func azure functionapp publish <function-app-name>
```

4. Configure environment variables in Azure Portal under **Configuration** > **Application settings**

---

## Function: CostManager

An HTTP-triggered Azure Function that identifies Azure resources generating the most cost and can shut them down to reduce expenses.

### Features

- **Cost Analysis**: Query Azure Cost Management API to identify top cost-generating resources
- **Resource Details**: Get detailed information about resources including name, type, location, and resource group
- **Automated Shutdown**: Stop/deallocate high-cost resources (currently supports Virtual Machines)
- **Flexible Time Periods**: Analyzes costs over the last 30 days
- **RESTful API**: Easy integration with other systems and workflows

### Supported Resource Types for Shutdown

- Virtual Machines (deallocate/stop)
- Future support planned for: SQL Databases, App Services, and other compute resources

### Required Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_SUBSCRIPTION_ID` | Yes | - | Azure subscription ID to analyze |
| `AZURE_RESOURCE_API_VERSION` | No | `2023-07-01` | API version for Azure Resource Manager queries |
| `VM_SHUTDOWN_TIMEOUT` | No | `300` | Timeout in seconds for VM shutdown operations |

### API Endpoints

### API Endpoints

#### 1. Analyze Costs (Default)

Get a list of resources with the highest costs:

```bash
# Using query parameters (local)
curl "http://localhost:7071/api/CostManager?subscription_id=<subscription-id>&top=10"

# Using POST with JSON body (Azure)
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
curl -X POST "http://localhost:7071/api/CostManager" \
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
| `subscription_id` | Yes* | - | Azure subscription ID to analyze (*Can be set via environment variable) |
| `top` | No | 10 | Number of top cost resources to return |
| `action` | No | analyze | Action to perform: `analyze` or `shutdown` |
| `resource_ids` | Conditional | - | Comma-separated resource IDs (required for `shutdown` action) |

---

## Function: CreateBudgetPolicy

An HTTP-triggered Azure Function that creates an Azure Policy definition to deny new resource creation when budget limits are reached.

### Features

- **Policy Creation**: Automatically creates a custom Azure Policy definition
- **Budget Enforcement**: Denies creation of new resources (except resource groups)
- **Governance**: Helps enforce spending controls at the subscription level
- **REST API**: Simple HTTP POST trigger

### Required Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_SUBSCRIPTION_ID` | Yes | Target subscription ID where the policy will be created |
| `AZURE_TENANT_ID` | Yes | Azure AD tenant ID |
| `AZURE_CLIENT_ID` | Yes | Application (client) ID |
| `AZURE_CLIENT_SECRET` | Yes | Client secret value |

### Usage

Trigger the function to create the policy:

```bash
# Local development
curl -X POST http://localhost:7071/api/CreateBudgetPolicy

# Azure deployment
curl -X POST "https://<function-app-name>.azurewebsites.net/api/CreateBudgetPolicy?code=<function-key>"
```

### Response Format

Success response:

```json
{
  "status": "success",
  "policyName": "Deny-New-Resources-OverBudget",
  "policyId": "/subscriptions/.../providers/Microsoft.Authorization/policyDefinitions/Deny-New-Resources-OverBudget",
  "displayName": "Deny-New-Resources-OverBudget",
  "policyType": "Custom",
  "mode": "All",
  "description": "This will restrict anyone from creating a new resource once the budget is reached."
}
```

Error response:

```json
{
  "error": "An error occurred while creating policy: [error details]"
}
```

### Policy Details

The created policy has the following characteristics:

- **Display Name**: Deny-New-Resources-OverBudget
- **Type**: Custom
- **Mode**: All
- **Effect**: Deny
- **Scope**: Applies to all resource types except resource groups
- **Version**: 1.0.0

### Important Notes

- Use the **AssignBudgetPolicy** function to assign the policy after creation
- Consider using Azure Budgets with Action Groups to trigger these functions automatically when budget thresholds are reached

---

## Function: AssignBudgetPolicy

An HTTP-triggered Azure Function that assigns the Deny-New-Resources-OverBudget policy to a subscription or resource group.

### Features

- **Policy Assignment**: Assigns the custom policy created by CreateBudgetPolicy
- **Flexible Scope**: Can assign to subscription or resource group level
- **Validation**: Verifies the policy definition exists before creating assignment
- **Unique Names**: Generates unique assignment names with UUIDs

### Required Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_SUBSCRIPTION_ID` | Yes | Target subscription ID |
| `AZURE_TENANT_ID` | Yes | Azure AD tenant ID |
| `AZURE_CLIENT_ID` | Yes | Application (client) ID |
| `AZURE_CLIENT_SECRET` | Yes | Client secret value |

### Usage

#### Assign to Subscription (Default)

```bash
# Local development
curl -X POST http://localhost:7071/api/AssignBudgetPolicy

# Azure deployment
curl -X POST "https://<function-app-name>.azurewebsites.net/api/AssignBudgetPolicy?code=<function-key>"
```

#### Assign to Specific Resource Group

```bash
curl -X POST http://localhost:7071/api/AssignBudgetPolicy \
  -H "Content-Type: application/json" \
  -d '{
    "scope": "/subscriptions/<subscription-id>/resourceGroups/<resource-group-name>"
  }'
```

#### Assign Different Policy

```bash
curl -X POST http://localhost:7071/api/AssignBudgetPolicy \
  -H "Content-Type: application/json" \
  -d '{
    "policy_name": "Deny-New-Resources-OverBudget",
    "scope": "/subscriptions/<subscription-id>"
  }'
```

### Request Body Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `policy_name` | No | Deny-New-Resources-OverBudget | Name of the policy definition to assign |
| `scope` | No | /subscriptions/{AZURE_SUBSCRIPTION_ID} | The scope where policy should be assigned |

### Response Format

Success response:

```json
{
  "status": "success",
  "assignmentName": "assign-Deny-New-Resources-OverBudget-a1b2c3d4",
  "assignmentId": "/subscriptions/.../providers/Microsoft.Authorization/policyAssignments/assign-Deny-New-Resources-OverBudget-a1b2c3d4",
  "displayName": "Assignment: Deny-New-Resources-OverBudget",
  "scope": "/subscriptions/12345678-1234-1234-1234-123456789abc",
  "policyDefinitionId": "/subscriptions/.../providers/Microsoft.Authorization/policyDefinitions/Deny-New-Resources-OverBudget",
  "enforcementMode": "Default",
  "description": "Policy assignment to deny new resource creation when budget is exceeded"
}
```

Error response (policy not found):

```json
{
  "error": "Policy definition 'Deny-New-Resources-OverBudget' not found. Please run CreateBudgetPolicy first."
}
```

### Workflow Example

1. Create the policy definition:
   ```bash
   curl -X POST http://localhost:7071/api/CreateBudgetPolicy
   ```

2. Assign the policy to enforce it:
   ```bash
   curl -X POST http://localhost:7071/api/AssignBudgetPolicy
   ```

3. The policy is now active and will deny new resource creation (except resource groups)

### Important Notes

- The policy definition MUST exist before creating an assignment
- Run **CreateBudgetPolicy** first if the policy doesn't exist
- Each assignment gets a unique name with a UUID suffix
- Enforcement mode is set to "Default" (actively enforced)
- You can create multiple assignments at different scopes
- Consider using Azure Budgets with Action Groups to trigger this function automatically when budget thresholds are reached

---

## Function: RemoveGlobalAdmins

An HTTP-triggered Azure Function that removes all users from the Global Administrator role in Azure AD.

### Features

- **Security Automation**: Removes all users from Global Administrator role
- **Microsoft Graph API**: Uses Graph API with application permissions
- **Selective Processing**: Only removes user objects (skips service principals and groups)
- **Detailed Reporting**: Returns list of all removed users and any errors

### Required Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_TENANT_ID` | Yes | Azure AD tenant ID |
| `AZURE_CLIENT_ID` | Yes | Application (client) ID |
| `AZURE_CLIENT_SECRET` | Yes | Client secret value |

### Required Permissions

- `RoleManagement.ReadWrite.Directory` - To remove users from roles
- `Directory.Read.All` - To read directory role members

### Usage

Trigger the function to remove all Global Administrators:

```bash
# Local development
curl -X POST http://localhost:7071/api/RemoveGlobalAdmins

# Azure deployment
curl -X POST "https://<function-app-name>.azurewebsites.net/api/RemoveGlobalAdmins?code=<function-key>"
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
  "error": "Missing required environment variables: AZURE_TENANT_ID, AZURE_CLIENT_ID, or AZURE_CLIENT_SECRET"
}
```

### Security Considerations

⚠️ **CRITICAL WARNINGS**:

1. **Backup Admin Access**: Ensure you have alternative admin access (e.g., break-glass account) before running
2. **Test First**: Always test in a non-production environment
3. **Audit Logs**: Review Azure AD audit logs after execution
4. **Service Accounts**: The function skips service principals and groups (only removes users)

### Global Administrator Role ID

The function uses the well-known Global Administrator role template ID: `62e90394-69f5-4237-9190-012177145e10` (constant across all Azure AD tenants).

---

## Architecture

```
┌─────────────────┐
│   HTTP Request  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Azure Functions                   │
│  ┌───────────────────────────────┐  │
│  │ CostManager                   │  │
│  │  - Cost Analysis              │◄─┼──► Cost Management API
│  │  - Resource Shutdown          │◄─┼──► Compute API
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ CreateBudgetPolicy            │  │
│  │  - Policy Definition Creation │◄─┼──► Policy API
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ RemoveGlobalAdmins            │  │
│  │  - Role Member Removal        │◄─┼──► Microsoft Graph API
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  JSON Response  │
└─────────────────┘
```

---

## Security Best Practices

1. **Credentials Management**:
   - Use Azure Key Vault to store secrets
   - Never commit `local.settings.json` to source control
   - Rotate client secrets regularly

2. **Function Authentication**:
   - Use function-level or admin-level auth keys
   - Restrict network access with Azure Functions private endpoints
   - Enable Application Insights for monitoring

3. **Least Privilege**:
   - Only grant necessary permissions to the service principal
   - Use separate service principals for different functions if needed
   - Regularly audit role assignments

4. **Audit and Monitoring**:
   - Enable Azure Activity Log monitoring
   - Review Azure AD audit logs for security changes
   - Set up alerts for critical operations

---

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify environment variables are set correctly
   - Ensure client secret hasn't expired
   - Check that required API permissions are granted with admin consent

2. **Permission Denied**
   - Verify RBAC roles are assigned correctly
   - Check that service principal has access to the target subscription
   - Ensure API permissions include admin consent

3. **Function Not Found**
   - Verify the function was deployed successfully
   - Check `function.json` exists in each function folder
   - Review deployment logs in Azure Portal

4. **Cost Data Not Available**
   - Cost data may take 24-48 hours to appear for new resources
   - Verify Cost Management Reader role is assigned
   - Ensure the subscription has been active and generating costs

---

## Logging and Monitoring

All functions log detailed information:

- **Trigger Events**: When functions are called
- **Authentication**: Credential validation and API client creation
- **Operations**: Detailed steps and results
- **Errors**: Comprehensive error messages with context

### View Logs

- **Local Development**: Console output
- **Azure**: 
  - Application Insights (recommended)
  - Log Stream in Azure Portal
  - Azure Monitor Logs

---

## Cost Optimization Best Practices

1. **Schedule Regular Analysis**: Run cost analysis daily or weekly to identify trends
2. **Set Budgets**: Use Azure Cost Management budgets with alerts
3. **Automate Dev/Test Shutdown**: Stop dev/test resources outside business hours
4. **Review Before Shutdown**: Always review analysis before shutting down resources
5. **Tag Resources**: Use tags to categorize and exclude critical resources
6. **Policy Enforcement**: Use CreateBudgetPolicy to prevent budget overruns

---

## Future Enhancements

- [ ] Support for additional resource types (SQL Databases, App Services, AKS)
- [ ] Integration with Azure Logic Apps for workflow automation
- [ ] Cost forecasting and trend analysis
- [ ] Slack/Teams notifications for alerts
- [ ] Scheduled automatic shutdowns with exclusion lists
- [ ] Cost anomaly detection
- [ ] Policy assignment automation
- [ ] Budget threshold-based triggers

---

## Contributing

Contributions are welcome! Please ensure your code:
- Follows existing code style and patterns
- Includes appropriate error handling and logging
- Updates relevant documentation
- Has been tested locally before submission

---

## License

MIT License - see LICENSE file for details
