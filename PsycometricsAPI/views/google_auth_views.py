from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.conf import settings
from ..db.mongo import hr_collection
import requests

@api_view(["POST"])
@permission_classes([AllowAny])
def google_auth(request):
    code = request.data.get('code')
    redirect_uri = request.data.get('redirect_uri')
    
    if not code:
        return Response({
            "status": "error",
            "code": "MISSING_CODE",
            "message": "Google authorization code is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Exchange code for access token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'client_id': settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id'],
        'client_secret': settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['secret'],
        'code': code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    try:
        # Get access token
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_data = token_response.json()
        access_token = token_data['access_token']

        # Get user info using the access token
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        google_response = requests.get(userinfo_url, headers=headers)
        google_response.raise_for_status()
        user_data = google_response.json()
        
    except requests.exceptions.RequestException as e:
        return Response({
            "status": "error",
            "code": "GOOGLE_API_ERROR",
            "message": "Failed to validate Google authentication"
        }, status=status.HTTP_401_UNAUTHORIZED)

    # Get or create user
    try:
        user = User.objects.get(email=user_data['email'])
    except User.DoesNotExist:
        user = User.objects.create(
            username=user_data['email'],
            email=user_data['email'],
            first_name=user_data.get('given_name', ''),
            last_name=user_data.get('family_name', '')
        )

        # Create HR in MongoDB
        hr_doc = {
            "first_name": user_data.get('given_name', ''),
            "last_name": user_data.get('family_name', ''),
            "email": user_data['email'],
            "picture": user_data.get('picture', '')
        }
        inserted_hr = hr_collection.insert_one(hr_doc)
        hr_id = str(inserted_hr.inserted_id)
    else:
        # Get existing HR
        hr = hr_collection.find_one({"email": user_data['email']})
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