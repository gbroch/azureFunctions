import logging
import os
import json
import uuid
from datetime import datetime
import azure.functions as func
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import PolicyClient


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function to assign the Deny-New-Resources-OverBudget policy to a subscription or resource group.
    
    This function uses Azure Management API to create a policy assignment that enforces
    the custom policy created by CreateBudgetPolicy function.
    
    Required environment variables:
    - AZURE_TENANT_ID: Azure AD tenant ID
    - AZURE_CLIENT_ID: Application (client) ID
    - AZURE_CLIENT_SECRET: Client secret value
    - AZURE_SUBSCRIPTION_ID: Target subscription ID
    
    Optional request body parameters:
    - scope: The scope where the policy should be assigned (defaults to subscription)
              Format: /subscriptions/{subscriptionId} or 
                     /subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}
    - policy_name: Name of the policy definition to assign (defaults to "Deny-New-Resources-OverBudget")
    
    Required API permissions:
    - Resource Policy Contributor or Owner role on the subscription
    """
    logging.info('AssignBudgetPolicy function triggered.')
    
    # Get credentials from environment variables
    tenant_id = os.environ.get('AZURE_TENANT_ID')
    client_id = os.environ.get('AZURE_CLIENT_ID')
    client_secret = os.environ.get('AZURE_CLIENT_SECRET')
    subscription_id = os.environ.get('AZURE_SUBSCRIPTION_ID')
    
    # Validate environment variables
    if not all([tenant_id, client_id, client_secret, subscription_id]):
        error_msg = "Missing required environment variables: AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, or AZURE_SUBSCRIPTION_ID"
        logging.error(error_msg)
        return func.HttpResponse(
            json.dumps({"error": error_msg}),
            status_code=500,
            mimetype="application/json"
        )
    
    try:
        # Parse request body for optional parameters
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = {}
        
        # Get policy name from request or use default
        policy_name = req_body.get('policy_name', 'Deny-New-Resources-OverBudget')
        
        # Get scope from request or default to subscription level
        default_scope = f"/subscriptions/{subscription_id}"
        scope = req_body.get('scope', default_scope)
        
        # Validate scope format
        if not scope.startswith('/subscriptions/'):
            error_msg = f"Invalid scope format. Must start with /subscriptions/. Received: {scope}"
            logging.error(error_msg)
            return func.HttpResponse(
                json.dumps({"error": error_msg}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Create credential and Policy client
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        policy_client = PolicyClient(credential, subscription_id)
        
        # Check if the policy definition exists
        logging.info(f"Checking if policy definition '{policy_name}' exists")
        try:
            policy_definition = policy_client.policy_definitions.get(policy_name)
            policy_definition_id = policy_definition.id
            logging.info(f"Found policy definition: {policy_definition_id}")
        except Exception as e:
            error_msg = f"Policy definition '{policy_name}' not found. Please run CreateBudgetPolicy first. Error: {str(e)}"
            logging.error(error_msg)
            return func.HttpResponse(
                json.dumps({"error": error_msg}),
                status_code=404,
                mimetype="application/json"
            )
        
        # Generate unique assignment name
        assignment_name = f"assign-{policy_name}-{uuid.uuid4().hex[:8]}"
        
        logging.info(f"Creating policy assignment '{assignment_name}' at scope '{scope}'")
        
        # Define the policy assignment
        policy_assignment = {
            "properties": {
                "displayName": f"Assignment: {policy_name}",
                "description": "Policy assignment to deny new resource creation when budget is exceeded",
                "policyDefinitionId": policy_definition_id,
                "enforcementMode": "Default",
                "metadata": {
                    "assignedBy": client_id,
                    "assignedOn": datetime.utcnow().isoformat() + "Z"
                }
            }
        }
        
        # Create the policy assignment
        result = policy_client.policy_assignments.create(
            scope=scope,
            policy_assignment_name=assignment_name,
            parameters=policy_assignment
        )
        
        logging.info(f"Successfully created policy assignment: {assignment_name}")
        
        # Prepare response
        response_data = {
            "status": "success",
            "assignmentName": assignment_name,
            "assignmentId": result.id,
            "displayName": result.display_name,
            "scope": result.scope,
            "policyDefinitionId": result.policy_definition_id,
            "enforcementMode": result.enforcement_mode,
            "description": result.description
        }
        
        return func.HttpResponse(
            json.dumps(response_data, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        error_msg = f"An error occurred while creating policy assignment: {str(e)}"
        logging.error(error_msg)
        return func.HttpResponse(
            json.dumps({"error": error_msg}),
            status_code=500,
            mimetype="application/json"
        )
