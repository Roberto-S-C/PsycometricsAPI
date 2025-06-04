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

            # Convert string IDs to ObjectId
            test_id = ObjectId(validated.pop("test_id"))
            hr_id = ObjectId(validated.pop("hr_id"))
            candidate_id = ObjectId(validated.pop("candidate_id"))

            result_data = {
                **validated,
                "test_id": test_id,
                "hr_id": hr_id,
                "candidate_id": candidate_id,
            }

            inserted = result_collection.insert_one(result_data)
            new_result = result_collection.find_one({"_id": inserted.inserted_id})

            # Convert ObjectId fields to strings for the response
            new_result["id"] = str(new_result["_id"])
            new_result["test_id"] = str(new_result["test_id"])
            new_result["hr_id"] = str(new_result["hr_id"])
            new_result["candidate_id"] = str(new_result["candidate_id"])
            del new_result["_id"]

            return Response(new_result, status=status.HTTP_201_CREATED)
        
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
