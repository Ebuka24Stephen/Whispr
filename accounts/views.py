from django.shortcuts import render
from rest_framework_simplejwt.tokens import  RefreshToken
from rest_framework.views import  APIView 
from rest_framework import status 
from rest_framework.response import Response 
from .models import User 
from .serializers import LoginSerializer, RegisterSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate,login

class RegisterApiView(APIView):
    permission_classes = [AllowAny]
    def post(self,request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)
    
    
class LoginApiView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        login(request, user)
        

        return Response({
            "message": "Login successful",
            "data": {
                "user": {
                    "email": user.email,
                    "username": user.username,
                }
            }
        }, status=status.HTTP_200_OK)
