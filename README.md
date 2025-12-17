# Azure Functions - Global Administrator Role Management

This repository contains Azure Functions for managing Azure Active Directory roles using Microsoft Graph API.

## RemoveGlobalAdminRole Function

An Azure Function that removes the Global Administrator directory role assignment from Azure AD. This function deletes the entire role assignment rather than removing individual users.

### Features

- Identifies the Global Administrator role using its template ID
- Removes all role assignments for the Global Administrator role
- Comprehensive error handling for missing roles, authentication failures, and deletion errors
- Detailed logging at debug and info levels
- Asynchronous Python implementation
- Uses Microsoft Graph API with proper authentication

### Required Permissions

The service principal/app registration used by this function must have the following Microsoft Graph API permission:
- `RoleManagement.ReadWrite.Directory` (Application permission)

### Environment Variables

The following environment variables must be configured:

- `TENANT_ID` - Your Azure AD tenant ID
- `CLIENT_ID` - Application (client) ID of your app registration
- `CLIENT_SECRET` - Client secret for authentication

### Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `local.settings.json` file for local development:
   ```json
   {
     "IsEncrypted": false,
     "Values": {
       "AzureWebJobsStorage": "UseDevelopmentStorage=true",
       "FUNCTIONS_WORKER_RUNTIME": "python",
       "TENANT_ID": "your-tenant-id",
       "CLIENT_ID": "your-client-id",
       "CLIENT_SECRET": "your-client-secret"
     }
   }
   ```

3. Configure the same environment variables in your Azure Function App settings when deploying to Azure.

### Usage

The function is triggered via HTTP POST request:

```bash
curl -X POST https://your-function-app.azurewebsites.net/api/RemoveGlobalAdminRole?code=your-function-key
```

### Response Format

Success response (HTTP 200):
```json
{
  "message": "Successfully removed Global Administrator role assignment. All 2 role assignment(s) deleted successfully",
  "role_id": "role-definition-id",
  "details": {
    "success": true,
    "message": "All 2 role assignment(s) deleted successfully",
    "assignments_deleted": 2,
    "total_assignments": 2
  }
}
```

Error response (HTTP 404/500):
```json
{
  "error": "Error message",
  "details": "Additional error details"
}
```

### Implementation Details

The function performs the following steps:

1. **Authentication**: Acquires an access token using MSAL with client credentials flow
2. **Role Identification**: Queries Microsoft Graph API to find the Global Administrator role definition using its well-known template ID (`62e90394-69f5-4237-9190-012177145e10`)
3. **Role Assignment Retrieval**: Fetches all role assignments associated with the Global Administrator role
4. **Deletion**: Iterates through all role assignments and deletes them individually
5. **Result Reporting**: Returns detailed information about the deletion operation, including success/failure counts

### Error Handling

The function handles various error scenarios:
- Missing or invalid environment variables
- Authentication failures
- Role not found
- No assignments to delete
- Partial deletion failures
- Network or API errors

All errors are logged with appropriate detail levels and returned in structured JSON responses.

### Logging

The function provides comprehensive logging:
- `INFO` level: Major operations and results
- `DEBUG` level: Detailed information including API URLs and response data
- `ERROR` level: Failures and exceptions
- `EXCEPTION` level: Full stack traces for unexpected errors