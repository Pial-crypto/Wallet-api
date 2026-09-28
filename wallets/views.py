from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User

from .models import Wallet
from .serializers import WalletSerializer


class WalletCreateView(APIView):
    def post(self, request):
        user_id = request.data.get("user_id")
        print(user_id ,"Found user id")

        if not user_id:
            print("No user id")
            return Response(
                {"detail": "user_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(
                id=user_id,
                tenant=request.tenant,
            )
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found in this tenant."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if hasattr(user, "wallet"):
            return Response(
                {"detail": "User already has a wallet."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        wallet = Wallet.objects.create(
            tenant=request.tenant,
            user=user,
        )
        print(wallet,"wallet")

        return Response(
            WalletSerializer(wallet).data,
            status=status.HTTP_201_CREATED,
        )