import time
from functools import reduce

import requests
import os
from django.http import JsonResponse
from requests.models import Response
from django.conf import settings

def can_make_request():
    current_time = int(time.time())
    reset_time = int(os.environ.get('HOUSECANARY_RESET_TIME', '0'))
    return current_time >= reset_time

def get_mocked_response():
    with open('property_details/mocked_response.json') as f:
        data = f.read()

    response = Response()
    response.status_code = 200
    response.headers = {}
    response._content = bytes(data, encoding='utf8')

    return response

def deep_get(dictionary, *keys):
    return reduce(lambda d, key: d.get(key) if d else None, keys, dictionary)

def generate_rate_limit_response(time_until_reset):
    response = JsonResponse({'error': 'Too many requests, please try again in {} seconds'.format(time_until_reset)},
                        status=429)

    response['Retry-After'] = time_until_reset
    return response

def parse_response(response):
    # Check for errors from HouseCanary API
    if response.status_code == 429:
        reset_timestamp = response.headers.get('X-RateLimit-Reset')
        if reset_timestamp:
            os.environ['HOUSECANARY_RESET_TIME'] = reset_timestamp
            time_until_reset = int(reset_timestamp) - int(time.time())
            return generate_rate_limit_response(time_until_reset)
        else:
            return JsonResponse({'error': 'Too many requests'}, status=429)
    elif response.status_code != 200:
        return JsonResponse({'error': 'Error retrieving property details'}, status=500)

    data = response.json()
    api_code = deep_get(data, "property/details", "api_code")
    if api_code != 0:
        return JsonResponse({'error': 'No property details found for address.'}, status=404)

    # Determine whether property has property_details system
    sewer_type = deep_get(data, "property/details", "result", "property", "sewer")
    return JsonResponse({'has_septic': str(sewer_type).lower() == 'septic'})

def has_septic_system(request):
    address = request.GET.get('address')
    city = request.GET.get('city')
    state = request.GET.get('state')
    zipcode = request.GET.get('zipcode')

    # Minimum required parameters see https://api-docs.housecanary.com/#levels-and-identifiers
    if not (address and zipcode) and not (address and city and state):
        return JsonResponse({'error': 'Either address and zipcode, or address, city, and state are required'},
                            status=400)

    unit = request.GET.get('unit')

    # Ensure we handle rate limits as good citizens https://api-docs.housecanary.com/#429-rate-limit-hit
    if not can_make_request():
        reset_timestamp = os.environ.get('HOUSECANARY_RESET_TIME')
        time_until_reset = int(reset_timestamp) - int(time.time())
        return generate_rate_limit_response(time_until_reset)

    if settings.MOCK_RESPONSE:
        return parse_response(get_mocked_response())

    # Retrieve property details from HouseCanary API
    housecanary_url = 'https://api.housecanary.com/v2/property/details'
    params = {'address': address, 'city': city, 'state': state, 'unit': unit, 'zipcode': zipcode}
    response = requests.get(housecanary_url, auth=(settings.API_KEY, settings.API_SECRET), params=params)
    return parse_response(response)