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
def microsoft_auth(request):
    print("Received data:", request.data)
    code = request.data.get('code')
    redirect_uri = request.data.get('redirect_uri')
    
    if not code:
        return Response({
            "status": "error",
            "code": "MISSING_CODE",
            "message": "Microsoft authorization code is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Exchange code for access token
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    token_data = {
        'client_id': settings.MICROSOFT_AUTH_CLIENT_ID,
        'code': code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
        'scope': 'User.Read'
    }
    # Remove client_secret for public clients

    try:
        # Get access token
        print("Token request data:", token_data)  # Debug logging
        token_response = requests.post(token_url, data=token_data)
        print("Token response status:", token_response.status_code)  # Debug logging
        print("Token response:", token_response.text)  # Debug logging
        
        token_response.raise_for_status()
        token_data = token_response.json()
        access_token = token_data['access_token']

        # Get user info using the access token
        graph_url = "https://graph.microsoft.com/v1.0/me"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        ms_response = requests.get(graph_url, headers=headers)
        ms_response.raise_for_status()
        user_data = ms_response.json()
        
    except requests.exceptions.RequestException as e:
        print("Microsoft API error:", str(e))  # Debug logging
        print("Error response:", e.response.text if hasattr(e, 'response') else 'No response text')
        return Response({
            "status": "error",
            "code": "MICROSOFT_API_ERROR",
            "message": "Failed to validate Microsoft authentication. Please check client ID and secret."
        }, status=status.HTTP_401_UNAUTHORIZED)

    # Get or create user
    try:
        user = User.objects.get(email=user_data['mail'])
    except User.DoesNotExist:
        user = User.objects.create(
            username=user_data['mail'],
            email=user_data['mail'],
            first_name=user_data.get('givenName', ''),
            last_name=user_data.get('surname', '')
        )

        # Create HR in MongoDB
        hr_doc = {
            "first_name": user_data.get('givenName', ''),
            "last_name": user_data.get('surname', ''),
            "email": user_data['mail'],
            "company": user_data.get('companyName', ''),
        }
        inserted_hr = hr_collection.insert_one(hr_doc)
        hr_id = str(inserted_hr.inserted_id)
    else:
        # Get existing HR
        hr = hr_collection.find_one({"email": user_data['mail']})
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