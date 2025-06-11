from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from ..db.mongo import hr_collection

@api_view(["POST"])
def signup(request):
    data = request.data

    # Validate email format
    try:
        validate_email(data['email'])
    except ValidationError:
        return Response({"error": "Invalid email address"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=data['email']).exists():
        return Response({"error": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)

    if len(data['password1']) < 8 or len(data['password2']) < 8:
        return Response({"error": "Password must be at least 8 characters long"}, status=status.HTTP_400_BAD_REQUEST)

    if data['password1'] != data['password2']:
        return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

    # Create Django User in SQL DB
    user = User.objects.create(
        username=data['email'],
        email=data['email'],
        password=make_password(data['password1'])
    )

    # Create HR in MongoDB
    hr_doc = {
        "first_name": "",
        "last_name": "",
        "age": "",
        "gender": "",
        "company": "",
        "email": data["email"],
        "phone": "",
        "password": make_password(data["password1"]),
    }

    inserted_hr = hr_collection.insert_one(hr_doc)
    hr = str(inserted_hr.inserted_id)

    # Generate JWT containing MongoDB HR ID
    refresh = RefreshToken.for_user(user)
    refresh["hr"] = hr

    return Response({
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "hr": hr
    }, status=status.HTTP_201_CREATED)

@api_view(["POST"])
def login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    # Authenticate against SQL user
    user = authenticate(username=email, password=password)
    if not user:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

    # Fetch matching HR in MongoDB
    hr = hr_collection.find_one({"email": email})
    if not hr:
        return Response({"error": "HR profile not found in MongoDB"}, status=status.HTTP_404_NOT_FOUND)

    # Create JWT containing the HR's MongoDB _id
    refresh = RefreshToken.for_user(user)
    refresh["hr"] = str(hr["_id"])

    return Response({
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "hr": str(hr["_id"]),
    }, status=status.HTTP_200_OK)
