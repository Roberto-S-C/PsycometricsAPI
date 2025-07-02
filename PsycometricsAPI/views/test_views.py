from rest_framework.decorators import api_view
from rest_framework.response import Response
from bson import ObjectId
from ..db.mongo import test_collection, candidate_collection
from ..utils.objectIdConversion import convert_objectid 

@api_view(["GET", "POST"])
def test_list(request):
    if request.method == "GET":
        candidate_id = request.query_params.get("candidate_id")
        if not candidate_id:
            return Response({"error": "Candidate ID is required"}, status=400)
        try:
            candidate = candidate_collection.find_one({"_id": ObjectId(candidate_id)})
        except Exception:
            return Response({"error": "Invalid candidate ID"}, status=400)
        if not candidate:
            return Response({"error": "Invalid candidate ID"}, status=404)

        # Check if candidate has already submitted a result
        from ..db.mongo import result_collection
        existing_result = result_collection.find_one({"candidate_id": ObjectId(candidate_id)})
        if existing_result:
            return Response({"error": "Candidate has already submitted a test"}, status=409)

        test = test_collection.find_one()
        if not test:
            return Response({"error": "No test found"}, status=404)
        test = convert_objectid(test)
        return Response(test)

    elif request.method == "POST":
        data = request.data
        result = test_collection.insert_one(data)
        return Response({"inserted_id": str(result.inserted_id)})

@api_view(["GET", "PUT", "DELETE"])
def test_detail(request, id):
    try:
        _id = ObjectId(id)
        test = test_collection.find_one({"_id": _id})
        if not test:
            return Response({"error": "Test not found"}, status=404)
    except:
        return Response({"error": "Invalid ID"}, status=400)

    if request.method == "GET":
        test = convert_objectid(test)
        return Response(test)

    elif request.method == "PUT":
        data = request.data
        test_collection.update_one({"_id": _id}, {"$set": data})
        return Response({"message": "Test updated"})

    elif request.method == "DELETE":
        test_collection.delete_one({"_id": _id})
        return Response({"message": "Test deleted"})
