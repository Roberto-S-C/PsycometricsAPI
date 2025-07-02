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

class ResponseSerializer(serializers.Serializer):
    question_id = serializers.CharField()
    response = serializers.CharField()

class ResultSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    test_id = serializers.CharField()
    candidate_id = serializers.CharField()
    hr_id = serializers.CharField()
    completed_at = serializers.DateTimeField(required=False)
    responses = ResponseSerializer(many=True)

class ResponseOptionSerializer(serializers.Serializer):
    option = serializers.CharField()
    value = serializers.IntegerField()

class QuestionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    question = serializers.CharField()
    options = serializers.ListField(child=serializers.CharField())

class TestSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    questions = QuestionSerializer(many=True)