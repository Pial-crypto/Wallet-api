from django.shortcuts import render

# Create your views here.
import secrets

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Tenant
from .serializers import TenantSerializer


class TenantCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        name = request.data.get("name")

        if not name:
            return Response(
                {"detail": "Tenant name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tenant = Tenant.objects.create(
            name=name,
            api_key=secrets.token_urlsafe(32),
        )

        serializer = TenantSerializer(tenant)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )