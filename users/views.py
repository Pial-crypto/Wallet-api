from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserCreateSerializer, UserSerializer


class UserCreateView(APIView):
    def post(self, request):
        serializer = UserCreateSerializer(
            data=request.data,
            context={
                "tenant": request.tenant,
            },
        )

        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )