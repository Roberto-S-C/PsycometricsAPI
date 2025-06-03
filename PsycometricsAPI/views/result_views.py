from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
from ..db.mongo import result_collection
from ..serializers import ResultSerializer
from ..utils.objectIdConversion import convert_objectid


@api_view(["GET", "POST"])
def result_list(request):
    if request.method == "GET":
        results = list(result_collection.find())
        results = [convert_objectid(c) for c in results]
        return Response(results)

    elif request.method == "POST":
        serializer = ResultSerializer(data=request.data)
        if serializer.is_valid():
            # Convert string IDs to ObjectId
            validated = serializer.validated_data
            validated["test"] = ObjectId(validated["test"])
            validated["hr"] = ObjectId(validated["hr"])
            validated["candidate"] = ObjectId(validated["candidate"])

            result_collection.insert_one(validated)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
def result_detail(request, id):
    try:
        _id = ObjectId(id)
        result = result_collection.find_one({"_id": _id})
        if not result:
            return Response({"error": "Result not found"}, status=404)
    except:
        return Response({"error": "Invalid ID"}, status=400)

    if request.method == "GET":
        result = convert_objectid(result)
        return Response(result)

    elif request.method == "PUT":
        serializer = ResultSerializer(data=request.data)
        if serializer.is_valid():
            updated = serializer.validated_data
            updated["test"] = ObjectId(updated["test"])
            updated["hr"] = ObjectId(updated["hr"])
            updated["candidate"] = ObjectId(updated["candidate"])

            result_collection.update_one({"_id": _id}, {"$set": updated})
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == "DELETE":
        result_collection.delete_one({"_id": _id})
        return Response(status=204)
