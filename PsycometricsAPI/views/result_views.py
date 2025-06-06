from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
from ..serializers import ResultSerializer
from ..db.mongo import result_collection
from ..utils.objectIdConversion import convert_objectid

@api_view(["GET", "POST"])
def result_list(request):
    if request.method == "GET":
        results = list(result_collection.find())
        results = [convert_objectid(r) for r in results]
        return Response(results)

    elif request.method == "POST":
        serializer = ResultSerializer(data=request.data)
        if serializer.is_valid():
            validated = serializer.validated_data

            validated["test"] = ObjectId(validated.pop("test_id"))
            validated["hr"] = ObjectId(validated.pop("hr_id"))
            validated["candidate"] = ObjectId(validated.pop("candidate_id"))

            inserted = result_collection.insert_one(validated)
            validated["id"] = str(inserted.inserted_id)

            response_data = {
                "id": validated["id"],
                "duration": validated["duration"],
                "conflicts": validated["conflicts"],
                "tolerance": validated["tolerance"],
                "savic": validated["savic"],
                "health": validated["health"],
                "test": str(validated["test"]),
                "hr": str(validated["hr"]),
                "candidate": str(validated["candidate"]),
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET", "DELETE"])
def result_detail(request, id):
    try:
        _id = ObjectId(id)
        result = result_collection.find_one({"_id": _id})
        if not result:
            return Response({"error": "Result not found"}, status=404)
    except:
        return Response({"error": "Invalid ID"}, status=400)

    if request.method == "GET":
        return Response(convert_objectid(result))

    elif request.method == "DELETE":
        result_collection.delete_one({"_id": _id})
        return Response(status=status.HTTP_204_NO_CONTENT)
