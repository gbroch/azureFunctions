# Architecture Overview

## RemoveGlobalAdminRole Azure Function

### High-Level Flow

```
HTTP POST Request
      ↓
Azure Function (RemoveGlobalAdminRole)
      ↓
Validate Environment Variables
      ↓
Authenticate with Azure AD (MSAL)
      ↓
Get Access Token
      ↓
Query Microsoft Graph API
      ↓
Get Global Administrator Role Definition
      ↓
Fetch All Role Assignments for Global Admin Role
      ↓
Delete Each Role Assignment
      ↓
Return Success/Failure Response
```

### Component Breakdown

#### 1. Entry Point: `main(req: func.HttpRequest)`
- **Purpose**: HTTP-triggered entry point for the Azure Function
- **Responsibilities**:
  - Validate environment variables (TENANT_ID, CLIENT_ID, CLIENT_SECRET)
  - Orchestrate the authentication and deletion workflow
  - Handle errors and format responses
  - Log all operations

#### 2. Authentication: `get_access_token()`
- **Purpose**: Acquire OAuth2 access token for Microsoft Graph API
- **Method**: Client Credentials Flow using MSAL
- **Authority**: `https://login.microsoftonline.com/{tenant_id}`
- **Scope**: `https://graph.microsoft.com/.default`
- **Returns**: Access token or None on failure

#### 3. Role Identification: `get_role_definition()`
- **Purpose**: Find the Global Administrator role definition
- **API Endpoint**: `GET /roleManagement/directory/roleDefinitions`
- **Filter**: `roleTemplateId eq '62e90394-69f5-4237-9190-012177145e10'`
- **Returns**: Role definition object with role ID, or None if not found

#### 4. Role Assignment Deletion: `delete_role_assignment()`
- **Purpose**: Remove all role assignments for Global Administrator role
- **Steps**:
  1. Fetch all assignments: `GET /roleManagement/directory/roleAssignments?$filter=roleDefinitionId eq '{role_id}'`
  2. Iterate through assignments
  3. Delete each: `DELETE /roleManagement/directory/roleAssignments/{assignment_id}`
- **Returns**: Dictionary with success status, message, and deletion counts

### API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/roleManagement/directory/roleDefinitions` | GET | Find Global Admin role by template ID |
| `/roleManagement/directory/roleAssignments` | GET | List all assignments for the role |
| `/roleManagement/directory/roleAssignments/{id}` | DELETE | Delete individual assignment |

### Required Permissions

- **RoleManagement.ReadWrite.Directory** (Application permission)
  - Required for reading role definitions
  - Required for listing role assignments
  - Required for deleting role assignments

### Error Handling Strategy

The function handles multiple error scenarios:

1. **Missing Environment Variables**: Returns 500 with descriptive error
2. **Authentication Failure**: Returns 500 with token acquisition error
3. **Role Not Found**: Returns 404 indicating Global Admin role doesn't exist
4. **No Assignments**: Returns 200 with message "No role assignments to delete"
5. **Partial Deletion Failure**: Returns 500 with details on which deletions failed
6. **Complete Deletion Failure**: Returns 500 with all failure details
7. **Unexpected Exceptions**: Returns 500 with exception message

### Logging Levels

- **DEBUG**: Detailed information including:
  - API URLs
  - Authentication authority
  - Role definition details
  - Assignment IDs being deleted
  
- **INFO**: Major operations:
  - Function triggered
  - Token acquired
  - Role found with ID
  - Number of assignments found
  - Successful deletions
  - Final result

- **ERROR**: Failures:
  - Missing environment variables
  - Token acquisition failures
  - API call failures
  - Deletion failures

- **EXCEPTION**: Full stack traces for unexpected errors

### Response Format

#### Success Response (HTTP 200)
```json
{
  "message": "Successfully removed Global Administrator role assignment. All 2 role assignment(s) deleted successfully",
  "role_id": "62e90394-69f5-4237-9190-012177145e10",
  "details": {
    "success": true,
    "message": "All 2 role assignment(s) deleted successfully",
    "assignments_deleted": 2,
    "total_assignments": 2
  }
}
```

#### Error Response (HTTP 404/500)
```json
{
  "error": "Error message",
  "role_id": "role-id-if-available",
  "details": {
    "success": false,
    "message": "Detailed error message",
    "assignments_deleted": 0,
    "total_assignments": 2,
    "failures": ["List of specific failures"]
  }
}
```

### Security Considerations

1. **Authentication**: Uses OAuth2 client credentials flow - no user credentials stored
2. **Secrets Management**: All sensitive data in environment variables
3. **Least Privilege**: Only requires RoleManagement.ReadWrite.Directory permission
4. **Audit Trail**: All operations are logged for audit purposes
5. **No Data Exposure**: Responses don't include sensitive user information

### Scalability & Performance

- **Asynchronous**: All functions are async for better performance
- **Stateless**: Function is stateless and can scale horizontally
- **Connection Pooling**: Reuses HTTP connections via requests library
- **Minimal Dependencies**: Only 3 dependencies (azure-functions, msal, requests)
- **Cold Start**: Optimized for Azure Functions consumption plan

### Testing Strategy

The function includes comprehensive unit tests covering:
- ✅ Successful role removal
- ✅ Missing environment variables
- ✅ Authentication failure
- ✅ Role not found
- ✅ No assignments to delete
- ✅ Partial deletion failure
- ✅ Token acquisition
- ✅ Role definition retrieval
- ✅ Role assignment deletion

All tests use mocking to avoid real API calls and ensure consistent test results.
