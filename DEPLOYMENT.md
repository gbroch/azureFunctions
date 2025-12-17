# Deployment Guide

This guide provides step-by-step instructions for deploying the RemoveGlobalAdmins Azure Function.

## Prerequisites Checklist

Before deployment, ensure you have:

- [ ] Azure subscription with appropriate permissions
- [ ] Azure CLI installed (optional, for command-line deployment)
- [ ] Azure Functions Core Tools installed (for local testing)
- [ ] Python 3.8+ installed locally
- [ ] Admin access to Azure AD tenant

## Step 1: Azure AD Application Setup

### Create App Registration

```bash
# Using Azure CLI (alternative to portal)
az ad app create --display-name "RemoveGlobalAdminsFunction"
```

Or via Azure Portal:
1. Navigate to [Azure Portal](https://portal.azure.com)
2. Go to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Name: `RemoveGlobalAdminsFunction`
5. Click **Register**
6. **Note down** the Application (client) ID and Directory (tenant) ID

### Configure API Permissions

1. In your app registration, select **API permissions**
2. Click **Add a permission** > **Microsoft Graph** > **Application permissions**
3. Add these permissions:
   - `RoleManagement.ReadWrite.Directory`
   - `Directory.Read.All`
4. Click **Grant admin consent for [Your Tenant]**
5. Confirm the consent

### Create Client Secret

1. Select **Certificates & secrets**
2. Click **New client secret**
3. Description: `RemoveGlobalAdminsFunction-Secret`
4. Expiration: Choose based on your security policy (e.g., 6 months)
5. Click **Add**
6. **Copy the secret value immediately** (you won't see it again!)

## Step 2: Create Azure Function App

### Using Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **Create a resource**
3. Search for "Function App"
4. Fill in the details:
   - **Subscription**: Your subscription
   - **Resource Group**: Create new or use existing
   - **Function App name**: Unique name (e.g., `removeadmins-prod`)
   - **Publish**: Code
   - **Runtime stack**: Python
   - **Version**: 3.9, 3.10, or 3.11
   - **Region**: Choose closest to your users
5. Click **Review + Create** > **Create**

### Using Azure CLI

```bash
# Create resource group
az group create --name RemoveAdminsFunctionRG --location eastus

# Create storage account
az storage account create \
  --name removeadminsstorage \
  --resource-group RemoveAdminsFunctionRG \
  --location eastus \
  --sku Standard_LRS

# Create function app
az functionapp create \
  --resource-group RemoveAdminsFunctionRG \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.9 \
  --functions-version 4 \
  --name removeadmins-prod \
  --storage-account removeadminsstorage \
  --os-type Linux
```

## Step 3: Configure Environment Variables

### Using Azure Portal

1. Navigate to your Function App
2. Go to **Configuration** under Settings
3. Click **New application setting** for each:
   - Name: `AZURE_TENANT_ID`, Value: Your tenant ID
   - Name: `AZURE_CLIENT_ID`, Value: Your application client ID
   - Name: `AZURE_CLIENT_SECRET`, Value: Your client secret
4. Click **Save**

### Using Azure CLI

```bash
az functionapp config appsettings set \
  --name removeadmins-prod \
  --resource-group RemoveAdminsFunctionRG \
  --settings \
    AZURE_TENANT_ID="your-tenant-id" \
    AZURE_CLIENT_ID="your-client-id" \
    AZURE_CLIENT_SECRET="your-client-secret"
```

## Step 4: Deploy the Function

### Option A: Deploy using Azure Functions Core Tools

```bash
# Navigate to the project directory
cd /path/to/azureFunctions

# Login to Azure
az login

# Deploy
func azure functionapp publish removeadmins-prod
```

### Option B: Deploy using Azure CLI

```bash
# Create a deployment package
cd /path/to/azureFunctions
zip -r function.zip . -x "*.git*" -x "*__pycache__*" -x "local.settings.json"

# Deploy the package
az functionapp deployment source config-zip \
  --resource-group RemoveAdminsFunctionRG \
  --name removeadmins-prod \
  --src function.zip
```

### Option C: Deploy using VS Code

1. Install the Azure Functions extension
2. Open the project folder in VS Code
3. Click on the Azure icon in the sidebar
4. Sign in to Azure
5. Right-click on your subscription > **Create Function App in Azure**
6. Follow the prompts
7. Right-click on the Function App > **Deploy to Function App**

## Step 5: Test the Function

### Get Function URL and Key

Using Azure Portal:
1. Go to your Function App
2. Click **Functions** > **RemoveGlobalAdmins**
3. Click **Get Function Url**
4. Copy the URL (includes the function key)

Using Azure CLI:
```bash
az functionapp function show \
  --resource-group RemoveAdminsFunctionRG \
  --name removeadmins-prod \
  --function-name RemoveGlobalAdmins

# Get the function key
az functionapp function keys list \
  --resource-group RemoveAdminsFunctionRG \
  --name removeadmins-prod \
  --function-name RemoveGlobalAdmins
```

### Test the Function

```bash
# Using curl
curl -X POST "https://removeadmins-prod.azurewebsites.net/api/RemoveGlobalAdmins?code=YOUR_FUNCTION_KEY"

# Using PowerShell
Invoke-RestMethod -Method Post -Uri "https://removeadmins-prod.azurewebsites.net/api/RemoveGlobalAdmins?code=YOUR_FUNCTION_KEY"
```

### Expected Response

```json
{
  "status": "completed",
  "removedUsers": [
    {
      "id": "user-guid",
      "userPrincipalName": "user@example.com"
    }
  ],
  "totalRemoved": 1,
  "errors": null
}
```

## Step 6: Monitor and Troubleshoot

### View Logs

Using Azure Portal:
1. Go to your Function App
2. Select **Monitor** > **Logs**
3. Or use **Application Insights** if configured

Using Azure CLI:
```bash
az functionapp log tail \
  --resource-group RemoveAdminsFunctionRG \
  --name removeadmins-prod
```

### Common Issues

**Issue**: "Missing required environment variables"
- **Solution**: Verify environment variables are set correctly in Function App Configuration

**Issue**: "Insufficient privileges to complete the operation"
- **Solution**: Ensure API permissions are granted and admin consent is provided

**Issue**: "Function not found"
- **Solution**: Verify deployment was successful and function name matches

**Issue**: Authentication errors
- **Solution**: Verify tenant ID, client ID, and client secret are correct

## Security Best Practices

1. **Rotate Secrets**: Regularly rotate the client secret
2. **Limit Access**: Use Azure RBAC to limit who can invoke the function
3. **Audit Logs**: Regularly review Azure AD audit logs after function execution
4. **Break-Glass Account**: Maintain an emergency admin account that won't be removed
5. **Monitoring**: Set up alerts in Application Insights for function failures
6. **Key Vault**: Consider using Azure Key Vault for storing secrets

## Post-Deployment Verification

1. Check Azure AD audit logs for role member removal events
2. Verify Global Administrator role members in Azure AD portal
3. Test with a non-production tenant first
4. Document the function URL and access procedures

## Rollback Plan

If you need to rollback:
1. Re-add users to Global Administrator role via Azure Portal
2. Use Azure AD Privileged Identity Management for controlled access
3. Review audit logs to identify removed users

## Additional Resources

- [Azure Functions Python Developer Guide](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference-python)
- [Microsoft Graph API Documentation](https://docs.microsoft.com/en-us/graph/overview)
- [Azure AD Role Management](https://docs.microsoft.com/en-us/azure/active-directory/roles/custom-overview)
