# Deployment Guide

This guide explains how to deploy the RemoveGlobalAdminRole Azure Function to Azure.

## Prerequisites

1. Azure subscription
2. Azure CLI installed locally
3. Azure Functions Core Tools (optional for local testing)
4. Python 3.9 or later

## Step 1: Create an App Registration

1. Navigate to Azure Portal > Azure Active Directory > App registrations
2. Click "New registration"
3. Provide a name (e.g., "GlobalAdminRoleRemover")
4. Click "Register"
5. Note the **Application (client) ID** and **Directory (tenant) ID**
6. Go to "Certificates & secrets" > "New client secret"
7. Create a secret and **copy the value immediately** (it won't be shown again)

## Step 2: Grant Required Permissions

1. In the app registration, go to "API permissions"
2. Click "Add a permission" > "Microsoft Graph" > "Application permissions"
3. Search for and add: **RoleManagement.ReadWrite.Directory**
4. Click "Grant admin consent" (requires Global Administrator privileges)

## Step 3: Create Azure Function App

Using Azure CLI:

```bash
# Set variables
RESOURCE_GROUP="your-resource-group"
STORAGE_ACCOUNT="yourstorage$(date +%s)"
FUNCTION_APP="your-function-app-name"
LOCATION="eastus"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Create Function App
az functionapp create \
  --resource-group $RESOURCE_GROUP \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name $FUNCTION_APP \
  --storage-account $STORAGE_ACCOUNT \
  --os-type Linux
```

## Step 4: Configure Environment Variables

Set the required environment variables in your Function App:

```bash
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings \
    TENANT_ID="your-tenant-id" \
    CLIENT_ID="your-client-id" \
    CLIENT_SECRET="your-client-secret"
```

## Step 5: Deploy the Function

### Option A: Deploy from local machine

```bash
# Install Azure Functions Core Tools if not already installed
# On Ubuntu/Debian:
# curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
# sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg
# sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-ubuntu-$(lsb_release -cs)-prod $(lsb_release -cs) main" > /etc/apt/sources.list.d/dotnetdev.list'
# sudo apt-get update
# sudo apt-get install azure-functions-core-tools-4

# Deploy
func azure functionapp publish $FUNCTION_APP
```

### Option B: Deploy from Azure CLI

```bash
# Zip the project
cd /path/to/azureFunctions
zip -r function.zip . -x "*.git*" -x "tests/*" -x "__pycache__/*" -x "*.pyc"

# Deploy
az functionapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP \
  --src function.zip
```

### Option C: Deploy from GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Azure Function

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Deploy to Azure Functions
      uses: Azure/functions-action@v1
      with:
        app-name: ${{ secrets.AZURE_FUNCTION_APP_NAME }}
        package: .
        publish-profile: ${{ secrets.AZURE_FUNCTION_APP_PUBLISH_PROFILE }}
```

## Step 6: Get the Function URL and Key

```bash
# Get the function key
FUNCTION_KEY=$(az functionapp keys list \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP \
  --query "functionKeys.default" -o tsv)

# Construct the URL
FUNCTION_URL="https://${FUNCTION_APP}.azurewebsites.net/api/RemoveGlobalAdminRole?code=${FUNCTION_KEY}"

echo "Function URL: $FUNCTION_URL"
```

## Step 7: Test the Function

```bash
# Test the function
curl -X POST "$FUNCTION_URL"
```

## Local Testing

To test locally before deployment:

1. Copy `local.settings.json.template` to `local.settings.json`
2. Fill in your Azure AD credentials
3. Install dependencies: `pip install -r requirements.txt`
4. Run the function: `func start`
5. Test with: `curl -X POST http://localhost:7071/api/RemoveGlobalAdminRole`

## Security Considerations

1. **Never commit `local.settings.json`** - it's already in `.gitignore`
2. Store secrets in Azure Key Vault for production
3. Use managed identities when possible instead of client secrets
4. Regularly rotate client secrets
5. Monitor and audit role assignment changes
6. Use Azure RBAC to restrict who can invoke the function

## Monitoring

View logs in Azure Portal:
1. Navigate to your Function App
2. Go to "Functions" > "RemoveGlobalAdminRole"
3. Click "Monitor" to view invocation logs
4. Set up Application Insights for detailed monitoring

## Troubleshooting

### Authentication Errors
- Verify `TENANT_ID`, `CLIENT_ID`, and `CLIENT_SECRET` are correct
- Ensure admin consent was granted for the API permission

### Permission Errors
- Verify `RoleManagement.ReadWrite.Directory` permission is granted
- Check that admin consent was granted

### Deployment Errors
- Ensure Python runtime version matches (3.9+)
- Check that all files are included in the deployment package
- Verify the resource group and function app exist

### Function Not Found
- Ensure `function.json` exists in the `RemoveGlobalAdminRole` directory
- Check that the deployment completed successfully
