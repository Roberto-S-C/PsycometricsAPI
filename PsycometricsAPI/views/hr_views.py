from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
from ..db.mongo import hr_collection, candidate_collection, result_collection
from ..serializers import HRSerializer
from ..utils.objectIdConversion import convert_objectid


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

    # 2) Handle GET
    if request.method == "GET":
        hr["id"] = str(hr["_id"])
        del hr["_id"]
        return Response(hr)

    # 3) Handle PUT (update HR)
    if request.method == "PUT":
        serializer = HRSerializer(data=request.data)
        if serializer.is_valid():
            update_data = serializer.validated_data
            hr_collection.update_one({"_id": _id}, {"$set": update_data})
            return Response({"message": "HR updated"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 4) Handle DELETE (cascade):
    if request.method == "DELETE":
        # 4a) Find all candidates that belong to this HR
        candidates = list(
            candidate_collection.find(
                {"hr_id": _id}, 
                {"_id": 1}
            )
        )
        candidate_ids = [c["_id"] for c in candidates]

        # 4b) Delete all results whose hr_id == this HR
        result_collection.delete_many({"hr_id": _id})

        # 4c) Delete all results whose candidate_id is in candidate_ids
        if candidate_ids:
            result_collection.delete_many({"candidate_id": {"$in": candidate_ids}})

        # 4d) Delete all candidates whose hr_id == this HR
        candidate_collection.delete_many({"hr_id": _id})

        # 4e) Finally delete the HR document itself
        hr_collection.delete_one({"_id": _id})

        return Response(status=status.HTTP_204_NO_CONTENT)
