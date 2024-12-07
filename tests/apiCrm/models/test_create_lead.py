from unittest import TestCase
from unittest.mock import patch, MagicMock
from apiCrm.models.lead import Lead
from apiCrm.dicts.dict_store_ident import dic_store_ident
from apiCrm.dicts.dict_region_ident import dic_region_ident

class TestLeadModel(TestCase):
    def setUp(self):
        """Set up test data"""
        self.lead = Lead()
        # Get first store and its corresponding region
        self.test_store = 'LONDRINA'  # Using a known store
        self.test_region = 'Londrina'  # Using corresponding region name
        
        self.test_data = {
            'name': 'Test User',
            'phone': '5511999999999',
            'email': 'test@example.com',
            'message': 'Test message',
            'store': self.test_store,
            'region': self.test_region
        }
        
    @patch('apiCrm.models.lead.requests.post')
    @patch('apiCrm.models.lead.config')
    def test_successful_lead_creation(self, mock_config, mock_post):
        """Test successful lead creation in CRM"""
        # Mock configuration and response
        mock_config.return_value = 'test_token'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'createLead': {
                    'email': self.test_data['email'],
                    'name': self.test_data['name'],
                    'message': self.test_data['message']
                }
            }
        }
        mock_post.return_value = mock_response
        
        # Call method
        response = self.lead.create_leads_at_crm(
            name=self.test_data['name'],
            phone=self.test_data['phone'],
            email=self.test_data['email'],
            message=self.test_data['message'],
            store=self.test_data['store'],
            region=self.test_data['region']
        )
        
        # Verify response
        self.assertEqual(response, mock_response.json.return_value)
        
        # Verify request
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        self.assertEqual(call_kwargs['headers']['Authorization'], 'Bearer test_token')
        self.assertIn('variables', call_kwargs['json'])
        
        # Verify variables
        variables = call_kwargs['json']['variables']['data']
        self.assertEqual(variables['name'], self.test_data['name'])
        self.assertEqual(variables['email'], self.test_data['email'])
        self.assertEqual(variables['telephone'], self.test_data['phone'])
        self.assertEqual(variables['message'], self.test_data['message'])
        
    @patch('apiCrm.models.lead.requests.post')
    @patch('apiCrm.models.lead.config')
    def test_failed_lead_creation(self, mock_config, mock_post):
        """Test failed lead creation in CRM"""
        # Mock configuration and failed response
        mock_config.return_value = 'test_token'
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'errors': ['Test error']}
        mock_post.return_value = mock_response
        
        # Call method
        response = self.lead.create_leads_at_crm(
            name=self.test_data['name'],
            phone=self.test_data['phone'],
            email=self.test_data['email'],
            message=self.test_data['message'],
            store=self.test_data['store'],
            region=self.test_data['region']
        )
        
        # Verify response contains error
        self.assertEqual(response, mock_response.json.return_value)
        
    def test_phone_number_formatting(self):
        """Test phone number is properly formatted"""
        test_phones = [
            ('5511999999999', '5511999999999'),  # Already formatted
            (5511999999999, '5511999999999'),    # Integer
            ('(55) 11 99999-9999', '5511999999999')  # Formatted string
        ]
        
        for input_phone, expected in test_phones:
            with patch('apiCrm.models.lead.requests.post') as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = {}
                
                self.lead.create_leads_at_crm(
                    name=self.test_data['name'],
                    phone=input_phone,
                    email=self.test_data['email'],
                    message=self.test_data['message'],
                    store=self.test_data['store'],
                    region=self.test_data['region']
                )
                
                # Verify phone format in request
                call_kwargs = mock_post.call_args.kwargs
                self.assertEqual(
                    call_kwargs['json']['variables']['data']['telephone'],
                    expected
                )

if __name__ == '__main__':
    unittest.main()