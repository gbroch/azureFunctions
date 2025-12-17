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

### 2. Configure API Permissions

Add the following Microsoft Graph **Application permissions** (not delegated):
- `RoleManagement.ReadWrite.Directory` - Required to remove users from roles
- `Directory.Read.All` - Required to read directory role members

After adding permissions, click **Grant admin consent** for your tenant.

### 3. Create a Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Click **New client secret**
3. Add a description and select an expiration period
4. Click **Add**
5. **Important**: Copy the secret value immediately (it won't be shown again)

### 4. Configure Environment Variables

Update the `local.settings.json` file (for local development) or configure Application Settings in Azure:

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
      "userPrincipalName": "user1@example.com"
    },
    {
      "id": "user-id-2",
      "userPrincipalName": "user2@example.com"
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