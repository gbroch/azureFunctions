import logging
import os
import json
from datetime import datetime
import azure.functions as func
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import PolicyClient


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function to create a custom Azure Policy definition.
    
    This function uses Azure Management API to create a policy that denies
    new resource creation (useful for budget enforcement).
    
    Required environment variables:
    - AZURE_TENANT_ID: Azure AD tenant ID
    - AZURE_CLIENT_ID: Application (client) ID
    - AZURE_CLIENT_SECRET: Client secret value
    - AZURE_SUBSCRIPTION_ID: Target subscription ID
    
    Required API permissions:
    - Resource Policy Contributor or Owner role on the subscription
    """
    logging.info('CreateBudgetPolicy function triggered.')
    
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
        # Create credential and Policy client
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        policy_client = PolicyClient(credential, subscription_id)
        
        # Define the policy name
        policy_name = "Deny-New-Resources-OverBudget"
        
        logging.info(f"Creating policy definition: {policy_name}")
        
        # Define the policy definition
        policy_definition = {
            "properties": {
                "displayName": "Deny-New-Resources-OverBudget",
                "policyType": "Custom",
                "mode": "All",
                "description": "This will restrict anyone from creating a new resource once the budget is reached.",
                "metadata": {
                    "category": "Budget",
                    "createdBy": "",
                    "createdOn": datetime.utcnow().isoformat() + "Z",
                    "updatedBy": None,
                    "updatedOn": None
                },
                "policyRule": {
                    "if": {
                        "field": "type",
                        "notEquals": "Microsoft.Resources/subscriptions/resourceGroups"
                    },
                    "then": {
                        "effect": "deny"
                    }
                }
            }
        }
        
        # Create the policy definition
        result = policy_client.policy_definitions.create_or_update(
            policy_definition_name=policy_name,
            parameters=policy_definition
        )
        
        logging.info(f"Successfully created policy definition: {policy_name}")
        
        # Prepare response
        response_data = {
            "status": "success",
            "policyName": policy_name,
            "policyId": result.id,
            "displayName": result.display_name,
            "policyType": result.policy_type,
            "mode": result.mode,
            "description": result.description
        }
        
        return func.HttpResponse(
            json.dumps(response_data, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        error_msg = f"An error occurred while creating policy: {str(e)}"
        logging.error(error_msg)
        return func.HttpResponse(
            json.dumps({"error": error_msg}),
            status_code=500,
            mimetype="application/json"
        )
