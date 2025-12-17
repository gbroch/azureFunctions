"""
Azure Function to identify high-cost Azure resources and optionally shut them down.

This function:
1. Queries Azure Cost Management API to identify resources with highest costs
2. Provides the ability to stop/deallocate those resources to reduce costs
"""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main entry point for the Cost Manager Azure Function.
    
    Query Parameters:
    - subscription_id: Azure subscription ID to analyze
    - top: Number of top cost resources to return (default: 10)
    - action: 'analyze' (default) or 'shutdown' to stop resources
    - resource_ids: Comma-separated list of resource IDs to shut down (required if action=shutdown)
    
    Returns:
    JSON response with cost analysis and/or shutdown results
    """
    logging.info('Cost Manager function triggered')
    
    try:
        # Parse query parameters
        subscription_id = req.params.get('subscription_id') or os.environ.get('AZURE_SUBSCRIPTION_ID')
        top_n = int(req.params.get('top', '10'))
        action = req.params.get('action', 'analyze')
        resource_ids_param = req.params.get('resource_ids', '')
        
        # Parse request body if present
        try:
            req_body = req.get_json()
            if req_body:
                subscription_id = req_body.get('subscription_id', subscription_id)
                top_n = req_body.get('top', top_n)
                action = req_body.get('action', action)
                resource_ids_param = req_body.get('resource_ids', resource_ids_param)
        except ValueError:
            pass  # No JSON body, continue with query params
        
        if not subscription_id:
            return func.HttpResponse(
                json.dumps({
                    "error": "subscription_id is required. Provide via query parameter or AZURE_SUBSCRIPTION_ID environment variable."
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        # Initialize Azure clients
        credential = DefaultAzureCredential()
        cost_client = CostManagementClient(credential)
        resource_client = ResourceManagementClient(credential, subscription_id)
        compute_client = ComputeManagementClient(credential, subscription_id)
        
        result = {}
        
        if action == 'analyze':
            # Analyze costs and identify top resources
            logging.info(f"Analyzing costs for subscription: {subscription_id}")
            top_resources = get_top_cost_resources(
                cost_client, 
                resource_client,
                subscription_id, 
                top_n
            )
            result = {
                "action": "analyze",
                "subscription_id": subscription_id,
                "top_resources": top_resources,
                "total_resources_analyzed": len(top_resources),
                "message": f"Found {len(top_resources)} resources with cost data"
            }
            
        elif action == 'shutdown':
            # Shutdown specified resources
            if not resource_ids_param:
                return func.HttpResponse(
                    json.dumps({
                        "error": "resource_ids parameter is required for shutdown action"
                    }),
                    status_code=400,
                    mimetype="application/json"
                )
            
            resource_ids = [rid.strip() for rid in resource_ids_param.split(',')]
            logging.info(f"Attempting to shutdown {len(resource_ids)} resources")
            
            shutdown_results = shutdown_resources(
                compute_client,
                resource_client,
                resource_ids
            )
            result = {
                "action": "shutdown",
                "subscription_id": subscription_id,
                "shutdown_results": shutdown_results,
                "total_resources_processed": len(shutdown_results)
            }
        else:
            return func.HttpResponse(
                json.dumps({
                    "error": f"Invalid action: {action}. Must be 'analyze' or 'shutdown'"
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        return func.HttpResponse(
            json.dumps(result, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error in Cost Manager function: {str(e)}", exc_info=True)
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "type": type(e).__name__
            }),
            status_code=500,
            mimetype="application/json"
        )


def get_top_cost_resources(
    cost_client: CostManagementClient,
    resource_client: ResourceManagementClient,
    subscription_id: str,
    top_n: int
) -> List[Dict[str, Any]]:
    """
    Query Azure Cost Management API to identify resources with highest costs.
    
    Args:
        cost_client: Azure Cost Management client
        resource_client: Azure Resource Management client
        subscription_id: Azure subscription ID
        top_n: Number of top resources to return
    
    Returns:
        List of dictionaries containing resource cost information
    """
    from azure.mgmt.costmanagement.models import (
        QueryDefinition,
        QueryTimePeriod,
        QueryDataset,
        QueryAggregation,
        QueryGrouping
    )
    
    # Define time period for cost query (last 30 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Build cost query
    scope = f"/subscriptions/{subscription_id}"
    
    query = QueryDefinition(
        type="ActualCost",
        timeframe="Custom",
        time_period=QueryTimePeriod(
            from_property=start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            to=end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        ),
        dataset=QueryDataset(
            granularity="None",
            aggregation={
                "totalCost": QueryAggregation(name="PreTaxCost", function="Sum")
            },
            grouping=[
                QueryGrouping(type="Dimension", name="ResourceId")
            ]
        )
    )
    
    try:
        # Execute cost query
        logging.info("Executing cost query...")
        query_result = cost_client.query.usage(scope, query)
        
        # Parse results
        resources_with_costs = []
        
        if hasattr(query_result, 'rows') and query_result.rows:
            # Extract cost data from rows
            for row in query_result.rows:
                if len(row) >= 2:
                    cost = row[0]  # Total cost
                    resource_id = row[1]  # Resource ID
                    
                    if resource_id and cost and cost > 0:
                        # Get resource details
                        resource_info = get_resource_details(resource_client, resource_id)
                        
                        resources_with_costs.append({
                            "resource_id": resource_id,
                            "cost": float(cost),
                            "resource_name": resource_info.get("name", "Unknown"),
                            "resource_type": resource_info.get("type", "Unknown"),
                            "location": resource_info.get("location", "Unknown"),
                            "resource_group": resource_info.get("resource_group", "Unknown")
                        })
        
        # Sort by cost (descending) and return top N
        resources_with_costs.sort(key=lambda x: x['cost'], reverse=True)
        return resources_with_costs[:top_n]
        
    except Exception as e:
        logging.warning(f"Error querying costs: {str(e)}")
        # Return empty list if cost query fails
        return []


def get_resource_details(
    resource_client: ResourceManagementClient,
    resource_id: str
) -> Dict[str, str]:
    """
    Get details about a specific Azure resource.
    
    Args:
        resource_client: Azure Resource Management client
        resource_id: Full resource ID
    
    Returns:
        Dictionary with resource details
    """
    try:
        # Parse resource ID
        parts = resource_id.split('/')
        if len(parts) >= 9:
            resource_group = parts[4]
            resource_provider = parts[6]
            resource_type = parts[7]
            resource_name = parts[8]
            
            # Try to get full resource details
            try:
                # Use latest stable API version
                resource = resource_client.resources.get_by_id(
                    resource_id,
                    api_version=os.environ.get('AZURE_RESOURCE_API_VERSION', '2023-07-01')
                )
                return {
                    "name": resource.name,
                    "type": resource.type,
                    "location": resource.location,
                    "resource_group": resource_group
                }
            except Exception:
                # Return basic parsed info if API call fails
                return {
                    "name": resource_name,
                    "type": f"{resource_provider}/{resource_type}",
                    "location": "Unknown",
                    "resource_group": resource_group
                }
    except Exception:
        pass
    
    return {
        "name": "Unknown",
        "type": "Unknown",
        "location": "Unknown",
        "resource_group": "Unknown"
    }


def shutdown_resources(
    compute_client: ComputeManagementClient,
    resource_client: ResourceManagementClient,
    resource_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Shutdown/deallocate specified Azure resources.
    
    Currently supports:
    - Virtual Machines (deallocate)
    
    Args:
        compute_client: Azure Compute Management client
        resource_client: Azure Resource Management client
        resource_ids: List of resource IDs to shutdown
    
    Returns:
        List of dictionaries with shutdown results for each resource
    """
    results = []
    
    for resource_id in resource_ids:
        result = {
            "resource_id": resource_id,
            "status": "unknown",
            "message": ""
        }
        
        try:
            # Parse resource ID to determine type
            parts = resource_id.split('/')
            if len(parts) < 9:
                result["status"] = "error"
                result["message"] = "Invalid resource ID format"
                results.append(result)
                continue
            
            resource_group = parts[4]
            resource_type = parts[7].lower()
            resource_name = parts[8]
            
            # Handle Virtual Machines
            if resource_type == "virtualmachines":
                logging.info(f"Deallocating VM: {resource_name}")
                try:
                    # Deallocate the VM
                    async_vm_deallocate = compute_client.virtual_machines.begin_deallocate(
                        resource_group,
                        resource_name
                    )
                    # Wait for operation to complete (with configurable timeout)
                    timeout = int(os.environ.get('VM_SHUTDOWN_TIMEOUT', '300'))
                    async_vm_deallocate.wait(timeout=timeout)
                    
                    result["status"] = "success"
                    result["message"] = f"VM '{resource_name}' deallocated successfully"
                    result["resource_type"] = "Virtual Machine"
                except Exception as vm_error:
                    result["status"] = "error"
                    result["message"] = f"Failed to deallocate VM: {str(vm_error)}"
                    result["resource_type"] = "Virtual Machine"
            else:
                result["status"] = "unsupported"
                result["message"] = f"Resource type '{resource_type}' shutdown not yet implemented"
                result["resource_type"] = resource_type
        
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Error processing resource: {str(e)}"
        
        results.append(result)
    
    return results
