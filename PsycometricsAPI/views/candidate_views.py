from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
from ..db.mongo import candidate_collection
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
            candidate_collection.insert_one(serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
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

    elif request.method == "PUT":
        serializer = CandidateSerializer(data=request.data)
        if serializer.is_valid():
            candidate_collection.update_one({ "_id": _id }, { "$set": serializer.validated_data })
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == "DELETE":
        candidate_collection.delete_one({ "_id": _id })
        return Response(status=204)
