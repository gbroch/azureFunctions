import logging
import os
import json
import azure.functions as func
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient


# Constants
GLOBAL_ADMIN_ROLE_ID = "62e90394-69f5-4237-9190-012177145e10"
USER_ODATA_TYPE = "#microsoft.graph.user"


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function to remove all users from the Global Administrator role.
    
    This function uses Microsoft Graph API to:
    1. Find the Global Administrator role
    2. Get all members of the role
    3. Remove all users from the role
    
    Required environment variables:
    - AZURE_TENANT_ID: Azure AD tenant ID
    - AZURE_CLIENT_ID: Application (client) ID
    - AZURE_CLIENT_SECRET: Client secret value
    
    Required API permissions:
    - RoleManagement.ReadWrite.Directory
    - Directory.Read.All
    """
    logging.info('RemoveGlobalAdmins function triggered.')
    
    # Get credentials from environment variables
    tenant_id = os.environ.get('AZURE_TENANT_ID')
    client_id = os.environ.get('AZURE_CLIENT_ID')
    client_secret = os.environ.get('AZURE_CLIENT_SECRET')
    
    # Validate environment variables
    if not all([tenant_id, client_id, client_secret]):
        error_msg = "Missing required environment variables: AZURE_TENANT_ID, AZURE_CLIENT_ID, or AZURE_CLIENT_SECRET"
        logging.error(error_msg)
        return func.HttpResponse(
            json.dumps({"error": error_msg}),
            status_code=500,
            mimetype="application/json"
        )
    
    try:
        # Create credential and Graph client
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        scopes = ['https://graph.microsoft.com/.default']
        client = GraphServiceClient(credentials=credential, scopes=scopes)
        
        logging.info(f"Fetching members of Global Administrator role (ID: {GLOBAL_ADMIN_ROLE_ID})")
        
        # Get all members of the Global Administrator role
        role_assignments = await client.directory_roles.by_directory_role_id(
            GLOBAL_ADMIN_ROLE_ID
        ).members.get()
        
        removed_users = []
        errors = []
        
        if role_assignments and role_assignments.value:
            logging.info(f"Found {len(role_assignments.value)} members in Global Administrator role")
            
            # Remove each user from the role
            for member in role_assignments.value:
                try:
                    # Only process user objects (not service principals or groups)
                    if hasattr(member, 'odata_type') and member.odata_type == USER_ODATA_TYPE:
                        user_id = member.id
                        user_principal_name = getattr(member, 'user_principal_name', 'Unknown')
                        
                        logging.info(f"Removing user {user_principal_name} (ID: {user_id}) from Global Administrator role")
                        
                        # Remove the user from the role
                        await client.directory_roles.by_directory_role_id(
                            GLOBAL_ADMIN_ROLE_ID
                        ).members.by_directory_object_id(
                            user_id
                        ).ref.delete()
                        
                        removed_users.append({
                            "id": user_id,
                            "userPrincipalName": user_principal_name
                        })
                        logging.info(f"Successfully removed user {user_principal_name}")
                    else:
                        logging.info(f"Skipping non-user object: {member.id}")
                        
                except Exception as e:
                    error_detail = f"Failed to remove member {member.id}: {str(e)}"
                    logging.error(error_detail)
                    errors.append(error_detail)
        else:
            logging.info("No members found in Global Administrator role")
        
        # Prepare response
        response_data = {
            "status": "completed",
            "removedUsers": removed_users,
            "totalRemoved": len(removed_users),
            "errors": errors if errors else None
        }
        
        logging.info(f"Function completed. Removed {len(removed_users)} users from Global Administrator role")
        
        return func.HttpResponse(
            json.dumps(response_data, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        logging.error(error_msg)
        return func.HttpResponse(
            json.dumps({"error": error_msg}),
            status_code=500,
            mimetype="application/json"
        )
