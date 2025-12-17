"""
Azure Function to remove the Global Administrator directory role assignment.
This function deletes the entire Global Administrator role assignment from Azure AD
using Microsoft Graph API.

Required Permissions: RoleManagement.ReadWrite.Directory
"""

import logging
import os
import json
import azure.functions as func
import msal
import requests


# Global Administrator role template ID (constant across all Azure AD tenants)
GLOBAL_ADMIN_ROLE_TEMPLATE_ID = "62e90394-69f5-4237-9190-012177145e10"


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main Azure Function entry point to remove Global Administrator role assignment.
    
    Args:
        req: HTTP request object
        
    Returns:
        HTTP response indicating success or failure
    """
    logging.info('RemoveGlobalAdminRole function triggered.')
    
    try:
        # Get authentication credentials from environment variables
        tenant_id = os.environ.get('TENANT_ID')
        client_id = os.environ.get('CLIENT_ID')
        client_secret = os.environ.get('CLIENT_SECRET')
        
        # Validate environment variables
        if not all([tenant_id, client_id, client_secret]):
            error_msg = "Missing required environment variables: TENANT_ID, CLIENT_ID, or CLIENT_SECRET"
            logging.error(error_msg)
            return func.HttpResponse(
                json.dumps({"error": error_msg}),
                status_code=500,
                mimetype="application/json"
            )
        
        logging.debug(f"Authenticating with tenant: {tenant_id}")
        
        # Acquire access token
        access_token = await get_access_token(tenant_id, client_id, client_secret)
        
        if not access_token:
            error_msg = "Failed to acquire access token"
            logging.error(error_msg)
            return func.HttpResponse(
                json.dumps({"error": error_msg}),
                status_code=500,
                mimetype="application/json"
            )
        
        logging.info("Successfully acquired access token")
        
        # Get the Global Administrator role definition
        role_definition = await get_role_definition(access_token, GLOBAL_ADMIN_ROLE_TEMPLATE_ID)
        
        if not role_definition:
            error_msg = "Global Administrator role definition not found"
            logging.error(error_msg)
            return func.HttpResponse(
                json.dumps({"error": error_msg, "details": "The Global Administrator role may not exist in this tenant"}),
                status_code=404,
                mimetype="application/json"
            )
        
        role_id = role_definition.get('id')
        logging.info(f"Found Global Administrator role with ID: {role_id}")
        logging.debug(f"Role definition: {json.dumps(role_definition)}")
        
        # Delete the Global Administrator role assignment
        deletion_result = await delete_role_assignment(access_token, role_id)
        
        if deletion_result['success']:
            success_msg = f"Successfully removed Global Administrator role assignment. {deletion_result['message']}"
            logging.info(success_msg)
            return func.HttpResponse(
                json.dumps({
                    "message": success_msg,
                    "role_id": role_id,
                    "details": deletion_result
                }),
                status_code=200,
                mimetype="application/json"
            )
        else:
            error_msg = f"Failed to remove Global Administrator role assignment: {deletion_result['message']}"
            logging.error(error_msg)
            return func.HttpResponse(
                json.dumps({
                    "error": error_msg,
                    "role_id": role_id,
                    "details": deletion_result
                }),
                status_code=500,
                mimetype="application/json"
            )
            
    except Exception as e:
        error_msg = f"Unexpected error in RemoveGlobalAdminRole function: {str(e)}"
        logging.exception(error_msg)
        return func.HttpResponse(
            json.dumps({"error": error_msg}),
            status_code=500,
            mimetype="application/json"
        )


async def get_access_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    """
    Acquire access token for Microsoft Graph API using client credentials flow.
    
    Args:
        tenant_id: Azure AD tenant ID
        client_id: Application (client) ID
        client_secret: Client secret
        
    Returns:
        Access token string or None if authentication fails
    """
    try:
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        scope = ["https://graph.microsoft.com/.default"]
        
        logging.debug(f"Acquiring token from authority: {authority}")
        
        app = msal.ConfidentialClientApplication(
            client_id,
            authority=authority,
            client_credential=client_secret
        )
        
        result = app.acquire_token_for_client(scopes=scope)
        
        if "access_token" in result:
            logging.debug("Access token acquired successfully")
            return result["access_token"]
        else:
            error_details = result.get("error_description", result.get("error", "Unknown error"))
            logging.error(f"Failed to acquire token: {error_details}")
            return None
            
    except Exception as e:
        logging.exception(f"Exception during token acquisition: {str(e)}")
        return None


async def get_role_definition(access_token: str, role_template_id: str) -> dict:
    """
    Get the role definition for Global Administrator role.
    
    Args:
        access_token: Microsoft Graph API access token
        role_template_id: Role template ID for Global Administrator
        
    Returns:
        Role definition dictionary or None if not found
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Query role definitions filtered by template ID
        url = f"https://graph.microsoft.com/v1.0/roleManagement/directory/roleDefinitions?$filter=roleTemplateId eq '{role_template_id}'"
        
        logging.debug(f"Fetching role definition from: {url}")
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            roles = data.get('value', [])
            
            if roles:
                role = roles[0]
                logging.info(f"Found role definition: {role.get('displayName', 'Unknown')}")
                return role
            else:
                logging.warning(f"No role found with template ID: {role_template_id}")
                return None
        else:
            logging.error(f"Failed to fetch role definition. Status: {response.status_code}, Response: {response.text}")
            return None
            
    except Exception as e:
        logging.exception(f"Exception while fetching role definition: {str(e)}")
        return None


async def delete_role_assignment(access_token: str, role_id: str) -> dict:
    """
    Delete all role assignments for the Global Administrator role.
    This removes the entire role assignment, not just individual users.
    
    Args:
        access_token: Microsoft Graph API access token
        role_id: Role definition ID
        
    Returns:
        Dictionary with 'success' boolean and 'message' string
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Get all role assignments for this role
        assignments_url = f"https://graph.microsoft.com/v1.0/roleManagement/directory/roleAssignments?$filter=roleDefinitionId eq '{role_id}'"
        
        logging.debug(f"Fetching role assignments from: {assignments_url}")
        
        response = requests.get(assignments_url, headers=headers)
        
        if response.status_code != 200:
            error_msg = f"Failed to fetch role assignments. Status: {response.status_code}, Response: {response.text}"
            logging.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "assignments_deleted": 0
            }
        
        data = response.json()
        assignments = data.get('value', [])
        
        if not assignments:
            logging.info("No role assignments found for Global Administrator role")
            return {
                "success": True,
                "message": "No role assignments to delete",
                "assignments_deleted": 0
            }
        
        logging.info(f"Found {len(assignments)} role assignment(s) to delete")
        
        # Delete each role assignment
        deleted_count = 0
        failed_deletions = []
        
        for assignment in assignments:
            assignment_id = assignment.get('id')
            principal_id = assignment.get('principalId')
            
            logging.debug(f"Deleting role assignment ID: {assignment_id} for principal: {principal_id}")
            
            delete_url = f"https://graph.microsoft.com/v1.0/roleManagement/directory/roleAssignments/{assignment_id}"
            delete_response = requests.delete(delete_url, headers=headers)
            
            if delete_response.status_code == 204:
                logging.info(f"Successfully deleted role assignment: {assignment_id}")
                deleted_count += 1
            else:
                error_detail = f"Assignment {assignment_id}: Status {delete_response.status_code}, Response: {delete_response.text}"
                logging.error(f"Failed to delete role assignment. {error_detail}")
                failed_deletions.append(error_detail)
        
        # Determine overall success
        if deleted_count == len(assignments):
            return {
                "success": True,
                "message": f"All {deleted_count} role assignment(s) deleted successfully",
                "assignments_deleted": deleted_count,
                "total_assignments": len(assignments)
            }
        elif deleted_count > 0:
            return {
                "success": False,
                "message": f"Partially deleted {deleted_count} of {len(assignments)} assignment(s)",
                "assignments_deleted": deleted_count,
                "total_assignments": len(assignments),
                "failures": failed_deletions
            }
        else:
            return {
                "success": False,
                "message": "Failed to delete any role assignments",
                "assignments_deleted": 0,
                "total_assignments": len(assignments),
                "failures": failed_deletions
            }
            
    except Exception as e:
        error_msg = f"Exception while deleting role assignments: {str(e)}"
        logging.exception(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "assignments_deleted": 0
        }
