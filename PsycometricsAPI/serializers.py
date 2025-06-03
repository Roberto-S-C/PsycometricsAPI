from rest_framework import serializers

class HRSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    age = serializers.IntegerField()
    gender = serializers.CharField(max_length=10)
    company = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, max_length=128)

class CandidateSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    age = serializers.IntegerField()
    gender = serializers.CharField(max_length=10)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    hr_id = serializers.CharField()  # FK reference to HR
    code = serializers.CharField(max_length=50)

class ResultSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    duration = serializers.IntegerField()
    conflicts = serializers.FloatField()
    tolerance = serializers.FloatField()
    savic = serializers.FloatField()
    health = serializers.FloatField()
    test_id = serializers.CharField()      # FK to Test
    hr_id = serializers.CharField()        # FK to HR
    candidate_id = serializers.CharField() # FK to Candidate

class ResponseOptionSerializer(serializers.Serializer):
    option = serializers.CharField()
    value = serializers.IntegerField()

class QuestionSerializer(serializers.Serializer):
    question = serializers.CharField()
    category = serializers.CharField()
    responses = ResponseOptionSerializer(many=True)

class TestSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField()
    description = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField())
    questions = QuestionSerializer(many=True)