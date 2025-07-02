from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
from ..db.mongo import candidate_collection, result_collection
from ..serializers import CandidateSerializer
from ..utils.objectIdConversion import convert_objectid


@api_view(["GET", "POST"])
def candidate_list(request):
    if request.method == "GET":
        candidates = list(candidate_collection.find())
        candidates = [convert_objectid(c) for c in candidates]
        return Response(candidates)

    elif request.method == "POST":
        # serializer = CandidateSerializer(data=request.data)
        # if serializer.is_valid():
        #     validated = serializer.validated_data

        #     validated["hr"] = ObjectId(validated.pop("hr_id"))

        #     result = candidate_collection.insert_one(validated)

        #     response_data = {
        #         "id": str(result.inserted_id),
        #         "first_name": validated["first_name"],
        #         "last_name": validated["last_name"],
        #         "age": validated["age"],
        #         "gender": validated["gender"],
        #         "email": validated["email"],
        #         "phone": validated["phone"],
        #         "hr_id": str(validated["hr"]),
        #         "code": str(validated["code"])
        #     }

        #     return Response(response_data, status=status.HTTP_201_CREATED)

        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # --- New implementation below ---
        data = request.data
        required_fields = ["email", "first_name", "last_name", "age", "gender", "phone"]
        for field in required_fields:
            if field not in data or not data[field]:
                return Response(
                    {"error": f"{field} is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Check if email already exists
        if candidate_collection.find_one({"email": data["email"]}):
            return Response(
                {"error": "A candidate with this email already exists."},
                status=status.HTTP_409_CONFLICT
            )

        # Set hr ObjectId (hardcoded as requested)
        hr_object_id = ObjectId("68634fee4a86e24702186e63")

        candidate_doc = {
            "email": data["email"],
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "age": data["age"],
            "gender": data["gender"],
            "phone": data["phone"],
            "hr": hr_object_id,
        }

        result = candidate_collection.insert_one(candidate_doc)

        response_data = {
            "id": str(result.inserted_id),
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "age": data["age"],
            "gender": data["gender"],
            "email": data["email"],
            "phone": data["phone"],
            "hr_id": str(hr_object_id),
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(["GET", "DELETE", "PUT"])
def candidate_detail(request, id):
    try:
        # Search by code, not by id
        candidate = candidate_collection.find_one({"code": id})
        if not candidate:
            return Response({"error": "Candidate not found"}, status=404)
    except Exception:
        return Response({"error": "Invalid code"}, status=400)

    if request.method == "GET":
        candidate = convert_objectid(candidate)
        return Response(candidate)

    elif request.method == "DELETE":
        _id = candidate["_id"]
        result_collection.delete_many({"candidate": _id})
        candidate_collection.delete_one({"_id": _id})
        return Response(status=status.HTTP_204_NO_CONTENT)

    elif request.method == "PUT":
        data = request.data
        required_fields = ["first_name", "last_name", "age", "gender", "email", "phone"]
        if not all(field in data and data[field] for field in required_fields):
            return Response(
                {"error": "All fields (first_name, last_name, age, gender, email, phone) are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        update_data = {
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "age": data["age"],
            "gender": data["gender"],
            "email": data["email"],
            "phone": data["phone"]
        }
        candidate_collection.update_one({"code": id}, {"$set": update_data})
        candidate = candidate_collection.find_one({"code": id})
        candidate = convert_objectid(candidate)
        return Response(candidate)


@api_view(["POST"])
def verify_candidate_code(request):
    code = request.data.get("code")
    if not code:
        return Response({
            "status": "error",
            "code": "MISSING_CODE",
            "message": "Code is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    candidate = candidate_collection.find_one({"code": code})
    if candidate:
        candidate = convert_objectid(candidate)
        return Response({
            "status": "success",
            "candidate": candidate
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            "status": "error",
            "code": "INVALID_CODE",
            "message": "Code not found"
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
def verify_completed_test(request):
    candidate_id = request.data.get("candidate_id")
    if not candidate_id:
        return Response({
            "status": "error",
            "code": "MISSING_CANDIDATE_ID",
            "message": "Candidate ID is required"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        candidate_obj_id = ObjectId(candidate_id)
    except Exception:
        return Response({
            "status": "error",
            "code": "INVALID_CANDIDATE_ID",
            "message": "Invalid candidate ID"
        }, status=status.HTTP_400_BAD_REQUEST)

    result = result_collection.find_one({"candidate_id": candidate_obj_id})
    if result:
        return Response({
            "status": "exists",
            "message": "Candidate has already submitted a test"
        }, status=status.HTTP_409_CONFLICT)
    else:
        return Response({
            "status": "not_found",
            "message": "No result found for this candidate"
        }, status=status.HTTP_200_OK)