from django.shortcuts import render
from rest_framework_simplejwt.tokens import  RefreshToken
from rest_framework.views import  APIView 
from rest_framework import status 
from rest_framework.response import Response 
from .models import User 
from .serializers import LoginSerializer, RegisterSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate,login


from rest_framework.authtoken.models import Token

class LoginApiView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        # ✅ create or get token
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            "message": "Login successful",
            "token": token.key,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
            }
        }, status=status.HTTP_200_OK)
    

class RegisterApiView(APIView):
    permission_classes = [AllowAny]
    def post(self,request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)
    
    

