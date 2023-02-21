from django.http import JsonResponse

from . import auth
from . import housecanary_client


def property_details(request):
    # Check user authentication before making request
    if not auth.authenticate_user(request):
        return JsonResponse({'error': 'User authentication failed'}, status=401)

    return housecanary_client.has_septic_system(request)
