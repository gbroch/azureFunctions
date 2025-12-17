"""
Unit tests for RemoveGlobalAdminRole Azure Function
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import sys
import os

# Add parent directory to path to import the function
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import RemoveGlobalAdminRole.__init__ as remove_global_admin


class TestRemoveGlobalAdminRole(unittest.IsolatedAsyncioTestCase):
    """Test cases for Global Administrator role removal function"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_req = MagicMock()
        self.test_tenant_id = "test-tenant-id"
        self.test_client_id = "test-client-id"
        self.test_client_secret = "test-client-secret"
        self.test_access_token = "test-access-token"
        self.test_role_id = "test-role-id"

    @patch.dict(os.environ, {
        'TENANT_ID': 'test-tenant-id',
        'CLIENT_ID': 'test-client-id',
        'CLIENT_SECRET': 'test-client-secret'
    })
    @patch('RemoveGlobalAdminRole.__init__.get_access_token')
    @patch('RemoveGlobalAdminRole.__init__.get_role_definition')
    @patch('RemoveGlobalAdminRole.__init__.delete_role_assignment')
    async def test_successful_role_removal(self, mock_delete, mock_get_role, mock_get_token):
        """Test successful removal of Global Administrator role assignment"""
        # Setup mocks
        mock_get_token.return_value = self.test_access_token
        mock_get_role.return_value = {'id': self.test_role_id, 'displayName': 'Global Administrator'}
        mock_delete.return_value = {
            'success': True,
            'message': 'All 2 role assignment(s) deleted successfully',
            'assignments_deleted': 2,
            'total_assignments': 2
        }

        # Execute function
        response = await remove_global_admin.main(self.mock_req)

        # Assertions
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.get_body())
        self.assertIn('message', response_data)
        self.assertIn('Successfully removed', response_data['message'])
        self.assertEqual(response_data['role_id'], self.test_role_id)

    @patch.dict(os.environ, {})
    async def test_missing_environment_variables(self):
        """Test error handling when environment variables are missing"""
        response = await remove_global_admin.main(self.mock_req)

        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.get_body())
        self.assertIn('error', response_data)
        self.assertIn('Missing required environment variables', response_data['error'])

    @patch.dict(os.environ, {
        'TENANT_ID': 'test-tenant-id',
        'CLIENT_ID': 'test-client-id',
        'CLIENT_SECRET': 'test-client-secret'
    })
    @patch('RemoveGlobalAdminRole.__init__.get_access_token')
    async def test_authentication_failure(self, mock_get_token):
        """Test error handling when authentication fails"""
        mock_get_token.return_value = None

        response = await remove_global_admin.main(self.mock_req)

        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.get_body())
        self.assertIn('error', response_data)
        self.assertIn('Failed to acquire access token', response_data['error'])

    @patch.dict(os.environ, {
        'TENANT_ID': 'test-tenant-id',
        'CLIENT_ID': 'test-client-id',
        'CLIENT_SECRET': 'test-client-secret'
    })
    @patch('RemoveGlobalAdminRole.__init__.get_access_token')
    @patch('RemoveGlobalAdminRole.__init__.get_role_definition')
    async def test_role_not_found(self, mock_get_role, mock_get_token):
        """Test error handling when Global Administrator role is not found"""
        mock_get_token.return_value = self.test_access_token
        mock_get_role.return_value = None

        response = await remove_global_admin.main(self.mock_req)

        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.get_body())
        self.assertIn('error', response_data)
        self.assertIn('role definition not found', response_data['error'])

    @patch.dict(os.environ, {
        'TENANT_ID': 'test-tenant-id',
        'CLIENT_ID': 'test-client-id',
        'CLIENT_SECRET': 'test-client-secret'
    })
    @patch('RemoveGlobalAdminRole.__init__.get_access_token')
    @patch('RemoveGlobalAdminRole.__init__.get_role_definition')
    @patch('RemoveGlobalAdminRole.__init__.delete_role_assignment')
    async def test_no_assignments_to_delete(self, mock_delete, mock_get_role, mock_get_token):
        """Test handling when there are no role assignments to delete"""
        mock_get_token.return_value = self.test_access_token
        mock_get_role.return_value = {'id': self.test_role_id, 'displayName': 'Global Administrator'}
        mock_delete.return_value = {
            'success': True,
            'message': 'No role assignments to delete',
            'assignments_deleted': 0
        }

        response = await remove_global_admin.main(self.mock_req)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.get_body())
        self.assertIn('message', response_data)

    @patch.dict(os.environ, {
        'TENANT_ID': 'test-tenant-id',
        'CLIENT_ID': 'test-client-id',
        'CLIENT_SECRET': 'test-client-secret'
    })
    @patch('RemoveGlobalAdminRole.__init__.get_access_token')
    @patch('RemoveGlobalAdminRole.__init__.get_role_definition')
    @patch('RemoveGlobalAdminRole.__init__.delete_role_assignment')
    async def test_partial_deletion_failure(self, mock_delete, mock_get_role, mock_get_token):
        """Test handling when some role assignments fail to delete"""
        mock_get_token.return_value = self.test_access_token
        mock_get_role.return_value = {'id': self.test_role_id, 'displayName': 'Global Administrator'}
        mock_delete.return_value = {
            'success': False,
            'message': 'Partially deleted 1 of 2 assignment(s)',
            'assignments_deleted': 1,
            'total_assignments': 2,
            'failures': ['Assignment xyz: Status 403']
        }

        response = await remove_global_admin.main(self.mock_req)

        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.get_body())
        self.assertIn('error', response_data)

    async def test_get_access_token_with_msal(self):
        """Test access token acquisition"""
        with patch('RemoveGlobalAdminRole.__init__.msal.ConfidentialClientApplication') as mock_msal:
            mock_app = MagicMock()
            mock_app.acquire_token_for_client.return_value = {'access_token': 'test-token'}
            mock_msal.return_value = mock_app

            token = await remove_global_admin.get_access_token(
                self.test_tenant_id,
                self.test_client_id,
                self.test_client_secret
            )

            self.assertEqual(token, 'test-token')
            mock_app.acquire_token_for_client.assert_called_once()

    async def test_get_role_definition_success(self):
        """Test successful role definition retrieval"""
        with patch('RemoveGlobalAdminRole.__init__.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'value': [{'id': 'role-123', 'displayName': 'Global Administrator'}]
            }
            mock_get.return_value = mock_response

            role = await remove_global_admin.get_role_definition(
                self.test_access_token,
                remove_global_admin.GLOBAL_ADMIN_ROLE_TEMPLATE_ID
            )

            self.assertIsNotNone(role)
            self.assertEqual(role['id'], 'role-123')

    async def test_delete_role_assignment_success(self):
        """Test successful deletion of role assignments"""
        with patch('RemoveGlobalAdminRole.__init__.requests.get') as mock_get, \
             patch('RemoveGlobalAdminRole.__init__.requests.delete') as mock_delete:
            
            # Mock GET response for fetching assignments
            mock_get_response = MagicMock()
            mock_get_response.status_code = 200
            mock_get_response.json.return_value = {
                'value': [
                    {'id': 'assignment-1', 'principalId': 'user-1'},
                    {'id': 'assignment-2', 'principalId': 'user-2'}
                ]
            }
            mock_get.return_value = mock_get_response

            # Mock DELETE responses
            mock_delete_response = MagicMock()
            mock_delete_response.status_code = 204
            mock_delete.return_value = mock_delete_response

            result = await remove_global_admin.delete_role_assignment(
                self.test_access_token,
                self.test_role_id
            )

            self.assertTrue(result['success'])
            self.assertEqual(result['assignments_deleted'], 2)
            self.assertEqual(mock_delete.call_count, 2)


if __name__ == '__main__':
    unittest.main()