import logging
import os
import json
import azure.functions as func
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.reference_create import ReferenceCreate


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function to assign all Entra ID users to a specific group.
    
    This function uses Microsoft Graph API to add all users in the tenant
    to a specified group.
    
    Required environment variables:
    - AZURE_TENANT_ID: Azure AD tenant ID
    - AZURE_CLIENT_ID: Application (client) ID
    - AZURE_CLIENT_SECRET: Client secret value
    
    Required API permissions (Application permissions):
    - User.Read.All: To read all users
    - GroupMember.ReadWrite.All: To add members to groups
    
    Request body:
    {
        "groupId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    }
    """
    logging.info('AssignUsersToGroup function triggered.')
    
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
    
    # Get group ID from request body
    try:
        req_body = req.get_json()
        group_id = req_body.get('groupId')
        
        if not group_id:
            return func.HttpResponse(
                json.dumps({"error": "groupId is required in request body"}),
                status_code=400,
                mimetype="application/json"
            )
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON in request body"}),
            status_code=400,
            mimetype="application/json"
        )
    
    try:
        # Create credential and Graph client
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        # Create Graph client with required scopes
        scopes = ['https://graph.microsoft.com/.default']
        graph_client = GraphServiceClient(credentials=credential, scopes=scopes)
        
        logging.info(f"Fetching all users from Entra ID...")
        
        # Get all users from Entra ID
        users = await graph_client.users.get()
        
        if not users or not users.value:
            logging.warning("No users found in the tenant")
            return func.HttpResponse(
                json.dumps({
                    "status": "success",
                    "message": "No users found in the tenant",
                    "usersProcessed": 0,
                    "usersAdded": 0,
                    "errors": []
                }),
                status_code=200,
                mimetype="application/json"
            )
        
        users_processed = 0
        users_added = 0
        errors = []
        
        logging.info(f"Found {len(users.value)} users. Adding them to group {group_id}...")
        
        # Add each user to the group
        for user in users.value:
            users_processed += 1
            try:
                # Create reference to add user to group
                request_body = ReferenceCreate(
                    odata_id=f"https://graph.microsoft.com/v1.0/directoryObjects/{user.id}"
                )
                
                await graph_client.groups.by_group_id(group_id).members.ref.post(request_body)
                users_added += 1
                logging.info(f"Added user {user.user_principal_name} (ID: {user.id}) to group")
                
            except Exception as user_error:
                error_msg = f"Failed to add user {user.user_principal_name}: {str(user_error)}"
                logging.warning(error_msg)
                
                # Check if user is already a member (this is expected and not a critical error)
                if "already exists" in str(user_error).lower() or "already a member" in str(user_error).lower():
                    logging.info(f"User {user.user_principal_name} is already a member of the group")
                else:
                    errors.append({
                        "userId": user.id,
                        "userPrincipalName": user.user_principal_name,
                        "error": str(user_error)
                    })
        
        logging.info(f"Completed processing. Added {users_added} out of {users_processed} users to group {group_id}")
        
        # Prepare response
        response_data = {
            "status": "success",
            "groupId": group_id,
            "usersProcessed": users_processed,
            "usersAdded": users_added,
            "errors": errors if errors else None
        }
        
        return func.HttpResponse(
            json.dumps(response_data, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        error_msg = f"An error occurred while assigning users to group: {str(e)}"
        logging.error(error_msg)
        return func.HttpResponse(
            json.dumps({"error": error_msg}),
            status_code=500,
            mimetype="application/json"
        )
