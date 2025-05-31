# Create your views here.
from django.shortcuts import render
from rest_framework import viewsets
from .models import HR, Test, Candidate, Result
from .serializers import HRSerializer, TestSerializer, CandidateSerializer, ResultSerializer

from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import User

from rest_framework.permissions import AllowAny

#Vistas usando render 

# Vistas para la API REST
class HRViewSet(viewsets.ModelViewSet):
    queryset = HR.objects.all()
    serializer_class = HRSerializer

class TestViewSet(viewsets.ModelViewSet):
    queryset = Test.objects.all()
    serializer_class = TestSerializer

class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer

class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer

class HRRegisterView(APIView):
    def post(self, request):
        data = request.data
        required_fields = ['first_name', 'last_name', 'email', 'password', 'company']
        
        if not all(field in data for field in required_fields):
            return Response({'error': 'Faltan campos obligatorios'}, status=400)
        
        if HR.objects.filter(email=data['email']).exists():
            return Response({'error': 'El email ya está registrado'}, status=400)
        
        hr_user = HR.objects.create(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password=make_password(data['password']),
            company=data['company'],
            age=data.get('age', 0),
            gender=data.get('gender', 'Otro')
        )
        
        return Response({
            'id': hr_user.id,
            'email': hr_user.email,
            'company': hr_user.company
        }, status=201)

class HRLoginView(APIView):
    def post(self, request):
        correo = request.data.get('email')
        password = request.data.get('password')
        
        try:
            hr_user = HR.objects.get(email=correo)
            if check_password(password, hr_user.password):
                refresh = RefreshToken.for_user(hr_user)
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'hr_id': hr_user.id,
                    'company': hr_user.company
                })
            return Response({'error': 'Contraseña incorrecta'}, status=401)
        except HR.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=404)

class CandidateCreateView(APIView):
    permission_classes = [AllowAny] #Más adelante cambiar a "IsAuthenticated"
    
    def post(self, request):
        hr_user = request.user  # Obtiene el HR autenticado
        data = request.data
        
        candidate = Candidate.objects.create(
            first_name=data['first_name'],
            last_name=data['last_name'],
            age=data['age'],
            email=data['email'],
            phone=data['phone'],
            hr=hr_user,
            code=f"CAND-{Candidate.objects.count() + 1}"
        )
        
        return Response({
            'id': candidate.id,
            'code': candidate.code,
           'full_name': f"{candidate.first_name} {candidate.last_name}"
        }, status=201)

class CandidateListView(APIView):
    permission_classes = [AllowAny] #Más adelante cambiar a "IsAuthenticated"

    def get(self, request):
        candidates = Candidate.objects.filter(hr=request.user)
        data = [{
            'id': cand.id,
            'full_name': f"{cand.first_name} {cand.last_name}",
            'email': cand.email,
            'code': cand.code
        } for cand in candidates]
        
        return Response(data)
    
class CandidateDeleteView(APIView):
    permission_classes =  [AllowAny] #Más adelante cambiar a "IsAuthenticated"

    def delete(self, request, candidate_id):
        try:
            candidate = Candidate.objects.get(id=candidate_id, hr=request.user)
            candidate.delete()
            return Response({'message': 'Candidato eliminado'}, status=200)
        except Candidate.DoesNotExist:
            return Response({'error': 'Candidato no encontrado'}, status=404)
        
class CandidateLoginView(APIView):
    def post(self, request):
        code = request.data.get('code')
        
        if not code:
            return Response({'error': 'El código es requerido'}, status=400)
        
        try:
            candidate = Candidate.objects.get(code=code)
            
            # Crear o actualizar usuario temporal para JWT
            user, created = User.objects.get_or_create(
                username=f"candidate_{candidate.id}",
                defaults={
                    'password': make_password(str(candidate.id)),
                    'is_active': True
                }
            )
            
            token = AccessToken.for_user(user)
            return Response({
                'access': str(token),
                'candidate_id': candidate.id,
                'full_name': f"{candidate.first_name} {candidate.last_name}",
                'email': candidate.email
            })
            
        except Candidate.DoesNotExist:
            return Response({'error': 'Código inválido'}, status=404)