from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User

from ledger.models import Transaction
from ledger.services import create_deposit

from .models import Wallet
from .serializers import (
    DepositSerializer,
    WalletSerializer,
)


class WalletCreateView(APIView):
    def post(self, request):
        user_id = request.data.get("user_id")

        if not user_id:
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

        return Response(
            WalletSerializer(wallet).data,
            status=status.HTTP_201_CREATED,
        )


class DepositView(APIView):
    def post(self, request, wallet_id):
        idempotency_key = request.headers.get("Idempotency-Key")

        if not idempotency_key:
            return Response(
                {
                    "detail": "Idempotency-Key header is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]

        try:
            transaction_record, created = create_deposit(
                wallet_id=wallet_id,
                tenant=request.tenant,
                amount=amount,
                idempotency_key=idempotency_key,
            )
        except Wallet.DoesNotExist:
            return Response(
                {"detail": "Wallet not found in this tenant."},
                status=status.HTTP_404_NOT_FOUND,
            )

        response_data = {
            "transaction_id": str(transaction_record.id),
            "wallet_id": str(transaction_record.wallet_id),
            "transaction_type": transaction_record.transaction_type,
            "amount": transaction_record.amount,
            "created_at": transaction_record.created_at,
        }

        if not created:
            response_data["idempotent"] = True

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )