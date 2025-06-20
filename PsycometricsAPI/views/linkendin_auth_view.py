from django.shortcuts import redirect
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.conf import settings
from ..db.mongo import hr_collection
import requests

@api_view(["POST"])
@permission_classes([AllowAny])
def linkedin_auth(request):
    code = request.data.get('code')
    redirect_uri = request.data.get('redirect_uri')
    
    if not code:
        return Response({
            "status": "error",
            "code": "MISSING_CODE",
            "message": "LinkedIn authorization code is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Exchange code for access token
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': settings.LINKEDIN_CLIENT_ID,
        'client_secret': settings.LINKEDIN_CLIENT_SECRET,
    }

    try:
        token_response = requests.post(token_url, data=token_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        token_response.raise_for_status()
        token_json = token_response.json()
        access_token = token_json['access_token']

        # Get user info from LinkedIn
        profile_url = "https://api.linkedin.com/v2/me"
        email_url = "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))"
        headers = {'Authorization': f'Bearer {access_token}'}

        profile_response = requests.get(profile_url, headers=headers)
        profile_response.raise_for_status()
        profile_data = profile_response.json()

        email_response = requests.get(email_url, headers=headers)
        email_response.raise_for_status()
        email_data = email_response.json()
        email = email_data['elements'][0]['handle~']['emailAddress']

    except requests.exceptions.RequestException:
        return Response({
            "status": "error",
            "code": "LINKEDIN_API_ERROR",
            "message": "Failed to validate LinkedIn authentication"
        }, status=status.HTTP_401_UNAUTHORIZED)

    # Get or create user
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = User.objects.create(
            username=email,
            email=email,
            first_name=profile_data.get('localizedFirstName', ''),
            last_name=profile_data.get('localizedLastName', '')
        )
        hr_doc = {
            "first_name": profile_data.get('localizedFirstName', ''),
            "last_name": profile_data.get('localizedLastName', ''),
            "email": email,
        }
        inserted_hr = hr_collection.insert_one(hr_doc)
        hr_id = str(inserted_hr.inserted_id)
    else:
        hr = hr_collection.find_one({"email": email})
        hr_id = str(hr["_id"]) if hr else None

    # Generate JWT
    refresh = RefreshToken.for_user(user)
    refresh["hr"] = hr_id

    return Response({
        "status": "success",
        "data": {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "hr": hr_id
        }
    }, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([AllowAny])
def linkedin_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state')
    redirect_uri = settings.SOCIALACCOUNT_PROVIDERS['linkedin_oauth2']['APP'].get('redirect_uri')

    if not code or not state:
        return HttpResponse("Missing code or state.", status=400)

    # Exchange code for access token
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': settings.LINKEDIN_CLIENT_ID,
        'client_secret': settings.LINKEDIN_CLIENT_SECRET,
    }

    try:
        token_response = requests.post(token_url, data=token_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        token_response.raise_for_status()
        token_json = token_response.json()
        access_token = token_json['access_token']

        # Get user info from LinkedIn
        profile_url = "https://api.linkedin.com/v2/me"
        email_url = "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))"
        headers = {'Authorization': f'Bearer {access_token}'}

        profile_response = requests.get(profile_url, headers=headers)
        profile_response.raise_for_status()
        profile_data = profile_response.json()

        email_response = requests.get(email_url, headers=headers)
        email_response.raise_for_status()
        email_data = email_response.json()
        email = email_data['elements'][0]['handle~']['emailAddress']

        # Get or create user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = User.objects.create(
                username=email,
                email=email,
                first_name=profile_data.get('localizedFirstName', ''),
                last_name=profile_data.get('localizedLastName', '')
            )
            hr_doc = {
                "first_name": profile_data.get('localizedFirstName', ''),
                "last_name": profile_data.get('localizedLastName', ''),
                "email": email,
            }
            inserted_hr = hr_collection.insert_one(hr_doc)
            hr_id = str(inserted_hr.inserted_id)
        else:
            hr = hr_collection.find_one({"email": email})
            hr_id = str(hr["_id"]) if hr else None

        # Generate JWT
        refresh = RefreshToken.for_user(user)
        refresh["hr"] = hr_id

        # Redirect to your app using a custom scheme, passing tokens and state
        app_redirect = f"myapp://linkedin-auth?access={str(refresh.access_token)}&refresh={str(refresh)}&hr={hr_id}&state={state}"
        return redirect(app_redirect)

    except Exception as e:
        return HttpResponse(f"LinkedIn authentication failed: {str(e)}", status=400)