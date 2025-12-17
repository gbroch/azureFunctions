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
        
        logging.info(f"Fetching Global Administrator role (template ID: {GLOBAL_ADMIN_ROLE_ID})")
        
        # Get all directory roles and find the activated Global Administrator role
        all_roles = await client.directory_roles.get()
        global_admin_role = None
        
        if all_roles and all_roles.value:
            for role in all_roles.value:
                # Check if this is the Global Administrator role using role_template_id
                role_template_id = getattr(role, 'role_template_id', None)
                if role_template_id == GLOBAL_ADMIN_ROLE_ID:
                    global_admin_role = role
                    logging.info(f"Found activated Global Administrator role (ID: {role.id})")
                    break
        
        if not global_admin_role:
            logging.warning("Global Administrator role not found or not activated")
            return func.HttpResponse(
                json.dumps({
                    "status": "completed",
                    "removedUsers": [],
                    "totalRemoved": 0,
                    "errors": ["Global Administrator role not found or not activated"]
                }),
                status_code=200,
                mimetype="application/json"
            )
        
        # Get all members of the Global Administrator role
        role_assignments = await client.directory_roles.by_directory_role_id(
            global_admin_role.id
        ).members.get()
        
        removed_users = []
        errors = []
        
        if role_assignments and role_assignments.value:
            logging.info(f"Found {len(role_assignments.value)} members in Global Administrator role")
            
            # Remove each user from the role
            for member in role_assignments.value:
                try:
                    # Check if this is a user object using additional_data
                    odata_type = None
                    if hasattr(member, 'additional_data') and member.additional_data:
                        odata_type = member.additional_data.get('@odata.type')
                    elif hasattr(member, 'odata_type'):
                        odata_type = member.odata_type
                    
                    # Only process user objects (not service principals or groups)
                    if odata_type == USER_ODATA_TYPE:
                        user_id = member.id
                        
                        # Get display name from member object, or fetch user details if needed
                        user_display_name = getattr(member, 'display_name', None)
                        if not user_display_name:
                            user_display_name = f"User-{user_id}"
                        
                        logging.info(f"Removing user {user_display_name} (ID: {user_id}) from Global Administrator role")
                        
                        # Remove the user from the role using the actual role ID
                        await client.directory_roles.by_directory_role_id(
                            global_admin_role.id
                        ).members.by_directory_object_id(
                            user_id
                        ).ref.delete()
                        
                        removed_users.append({
                            "id": user_id,
                            "displayName": user_display_name
                        })
                        logging.info(f"Successfully removed user {user_display_name}")
                    else:
                        odata_info = odata_type if odata_type else "unknown type"
                        logging.info(f"Skipping non-user object: {member.id} (type: {odata_info})")
                        
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
