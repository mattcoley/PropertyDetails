import os
import time
from unittest.mock import patch

from django.http import JsonResponse
from django.test import Client, override_settings, TestCase
from requests.models import Response

from . import housecanary_client

client = Client()

class CanMakeRequestTestCase(TestCase):
    def test_can_make_request(self):
        os.environ['HOUSECANARY_RESET_TIME'] = str(int(time.time()) - 60)
        self.assertTrue(housecanary_client.can_make_request())
        del os.environ['HOUSECANARY_RESET_TIME']

    def test_cannot_make_request(self):
        os.environ['HOUSECANARY_RESET_TIME'] = str(int(time.time()) + 60)
        self.assertFalse(housecanary_client.can_make_request())
        del os.environ['HOUSECANARY_RESET_TIME']

class GetMockedResponseTestCase(TestCase):
    def test_get_mocked_response(self):
        response = housecanary_client.get_mocked_response()
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, 200)

class DeepGetTestCase(TestCase):
    def test_deep_get(self):
        data = {
            'property': {
                'features': {
                    'structures': {'sewer': 'Public'}

                }
            }
        }

        self.assertEqual(housecanary_client.deep_get(data, 'property', 'features', 'structures', 'sewer'), 'Public')
        self.assertIsNone(housecanary_client.deep_get(data, 'property', 'features', 'structures', 'random'))

class ParseResponseTestCase(TestCase):
    def test_successful_response(self):
        data = {
            'property': {
                'sewer': 'Septic'
            }
        }
        response = Response()
        response.status_code = 200
        response.json = lambda: {'property/details': {'api_code': 0, 'result': data}}
        json_response = housecanary_client.parse_response(response)
        self.assertIsInstance(json_response, JsonResponse)
        self.assertEqual(json_response.status_code, 200)
        self.assertEqual(json_response.content, JsonResponse({'has_septic': True}).content)

    def test_rate_limited_response(self):
        response = Response()
        response.status_code = 429
        response.headers['X-RateLimit-Reset'] = str(int(time.time()) + 60)
        json_response = housecanary_client.parse_response(response)
        self.assertIsInstance(json_response, JsonResponse)
        self.assertEqual(json_response.status_code, 429)

    def test_error_response(self):
        response = Response()
        response.status_code = 500
        json_response = housecanary_client.parse_response(response)
        self.assertIsInstance(json_response, JsonResponse)
        self.assertEqual(json_response.status_code, 500)

    def test_no_details_response(self):
        data = {'api_code': 123}
        response = Response()
        response.status_code = 200
        response.json = lambda: {'property/details': data}
        json_response = housecanary_client.parse_response(response)
        self.assertIsInstance(json_response, JsonResponse)
        self.assertEqual(json_response.status_code, 404)

@override_settings(MOCK_RESPONSE=False)
class HasSepticSystemTestCase(TestCase):
    def setUp(self):
        if os.environ.get('HOUSECANARY_RESET_TIME'):
            del os.environ['HOUSECANARY_RESET_TIME']

    @patch('requests.get')
    def test_successful_request(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 200
        mock_response.json = lambda: {'property/details': {'api_code': 0, 'result': {'property': {'sewer': 'Septic'}}}}
        mock_get.return_value = mock_response

        response = client.get('/property/details', {'address': '123 Main St', 'zipcode': '12345'})
        self.assertIsInstance(response, JsonResponse)
        print (response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, JsonResponse({'has_septic': True}).content)

    @patch('requests.get')
    def test_rate_limited_request(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 429
        mock_response.headers['X-RateLimit-Reset'] = str(int(time.time()) + 60)
        mock_get.return_value = mock_response

        response = client.get('/property/details', {'address': '123 Main St', 'zipcode': '12345'})
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 429)

    def test_missing_params_request(self):
        response = client.get('/property/details')
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 400)

    @patch('requests.get')
    def test_error_request(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        response = client.get('/property/details', {'address': '123 Main St', 'zipcode': '12345'})
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 500)

    @patch('requests.get')
    def test_no_details_request(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 200
        mock_response.json = lambda: {'property/details': {'api_code': 123}}
        mock_get.return_value = mock_response

        response = client.get('/property/details', {'address': '123 Main St', 'zipcode': '12345'})
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 404)

    @patch('requests.get')
    @override_settings(MOCK_RESPONSE=True)
    def test_mocked_response(self, mock_get):
        mock_response = housecanary_client.get_mocked_response()
        mock_get.return_value = mock_response

        response = client.get('/property/details', {'address': '123 Main St', 'zipcode': '12345'})
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, JsonResponse({'has_septic': True}).content)