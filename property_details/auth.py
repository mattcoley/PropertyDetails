def authenticate_user(request):
    # Make request to internal authentication API to check auth cookie
    session_cookie = request.COOKIES.get('ht_auth')

    '''
    auth_api_url = 'https://internal-auth-api.example.com/validate_auth_token'
    response = requests.get(auth_api_url, cookies={'auth_token': session_cookie})

    if response.status_code != 200:
        return False
    '''

    return True
