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
        serializer = CandidateSerializer(data=request.data)
        if serializer.is_valid():
            validated = serializer.validated_data

            validated["hr"] = ObjectId(validated.pop("hr_id"))

            result = candidate_collection.insert_one(validated)

            response_data = {
                "id": str(result.inserted_id),
                "first_name": validated["first_name"],
                "last_name": validated["last_name"],
                "age": validated["age"],
                "gender": validated["gender"],
                "email": validated["email"],
                "phone": validated["phone"],
                "hr_id": str(validated["hr"]),
                "code": str(validated["code"])
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(["GET", "DELETE"])
def candidate_detail(request, id):
    try:
        _id = ObjectId(id)
        candidate = candidate_collection.find_one({ "_id": _id })
        if not candidate:
            return Response({"error": "Candidate not found"}, status=404)
    except:
        return Response({"error": "Invalid ID"}, status=400)

    if request.method == "GET":
        candidate = convert_objectid(candidate)
        return Response(candidate)

    elif request.method == "DELETE":
        result_collection.delete_many({"candidate": _id})

        candidate_collection.delete_one({"_id": _id})

        return Response(status=status.HTTP_204_NO_CONTENT)