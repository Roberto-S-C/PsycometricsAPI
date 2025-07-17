from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from bson import ObjectId
from ..db.mongo import hr_collection, candidate_collection, result_collection
from ..serializers import HRSerializer
from ..utils.objectIdConversion import convert_objectid
from rest_framework_simplejwt.authentication import JWTAuthentication
import random
import string


@api_view(["GET", "POST"])
def hr_list(request):
    if request.method == "GET":
        hrs = list(hr_collection.find())
        hrs = [convert_objectid(c) for c in hrs]
        return Response(hrs)

    elif request.method == "POST":
        serializer = HRSerializer(data=request.data)
        if serializer.is_valid():
            hr_collection.insert_one(serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
def hr_detail(request, id):
    try:
        _id = ObjectId(id)
    except:
        return Response({"error": "Invalid HR ID"}, status=status.HTTP_400_BAD_REQUEST)

    hr = hr_collection.find_one({"_id": _id})
    if not hr:
        return Response({"error": "HR not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        hr["id"] = str(hr["_id"])
        del hr["_id"]
        return Response(hr)

    if request.method == "PUT":
        serializer = HRSerializer(data=request.data)
        if serializer.is_valid():
            update_data = serializer.validated_data
            hr_collection.update_one({"_id": _id}, {"$set": update_data})
            return Response({"message": "HR updated"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "DELETE":
        try:
            _id = ObjectId(id)
            hr = hr_collection.find_one({"_id": _id})
            if not hr:
                return Response({"error": "HR not found"}, status=404)
        except:
            return Response({"error": "Invalid ID"}, status=400)

        # Delete related candidates
        candidate_collection.delete_many({"hr": _id})

        # Delete related results
        result_collection.delete_many({"hr": _id})

        # Finally delete the HR
        hr_collection.delete_one({"_id": _id})

        return Response(status=204)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_candidate_code(request):
    try:
        # Extract HR ID from the authenticated user
        hr_id = request.user.user_id
        if not hr_id:
            return Response({"error": "HR ID not found in token"}, status=status.HTTP_401_UNAUTHORIZED)

        # Find HR by user_id
        hr = hr_collection.find_one({"_id": ObjectId(hr_id)})
        if not hr:
            return Response({"error": "HR not found"}, status=status.HTTP_404_NOT_FOUND)

        # Generate unique 6-character code (uppercase letters and digits)
        def generate_code():
            return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Ensure code uniqueness in candidate_collection
        for _ in range(10):  # Try up to 10 times
            code = generate_code()
            if not candidate_collection.find_one({"code": code}):
                break
        else:
            return Response({"error": "Could not generate unique code"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Generate a unique email using the code
        unique_email = f"candidate_{code}@example.com"

        # Create generic candidate
        candidate_doc = {
            "first_name": "Candidate",
            "last_name": "Candidate",
            "age": 0,
            "gender": "",
            "email": unique_email,  # Use the unique email
            "phone": "",
            "hr": hr_id,
            "code": code
        }
        inserted = candidate_collection.insert_one(candidate_doc)
        candidate_doc["id"] = str(inserted.inserted_id)

        return Response({
            "status": "success",
            "candidate": {
                "id": candidate_doc["id"],
                "code": code,
                "email": unique_email  # Return the unique email
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        print(f"Error generating candidate code: {e}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def hr_candidates(request):
    try:
        # Extract HR ID from the authenticated user
        hr_id = request.user.user_id
        if not hr_id:
            return Response({"error": "HR ID not found in token"}, status=status.HTTP_401_UNAUTHORIZED)

        # Convert HR ID to ObjectId
        hr_object_id = ObjectId(hr_id)
    except Exception:
        return Response({"error": "Invalid HR ID in token"}, status=status.HTTP_400_BAD_REQUEST)

    # Fetch all candidates associated with the HR
    candidates = list(candidate_collection.find({"hr": hr_object_id}))
    if not candidates:
        return Response({"message": "No candidates found"}, status=status.HTTP_404_NOT_FOUND)

    # Filter out candidates with emails like "candidate_<code>@example.com"
    filtered_candidates = [
        candidate for candidate in candidates
        if not candidate["email"].startswith("candidate_") or not candidate["email"].endswith("@example.com")
    ]

    # Convert ObjectId fields to strings
    filtered_candidates = [convert_objectid(candidate) for candidate in filtered_candidates]

    return Response(filtered_candidates, status=status.HTTP_200_OK)