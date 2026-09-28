from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User

from rest_framework.pagination import PageNumberPagination

from ledger.models import Transaction
from ledger.serializers import TransactionSerializer
from ledger.services import (
    create_deposit,
    create_transfer,
    create_withdrawal,
    get_wallet_balance,
)
# from wallets.serializers import TransferSerializer

from .models import Wallet
from .serializers import (
    DepositSerializer,
    WalletSerializer,
    WithdrawSerializer,
    TransferSerializer
    
)
class TransferView(APIView):
    def post(self, request, wallet_id):
        idempotency_key = request.headers.get("Idempotency-Key")

        if not idempotency_key:
            return Response(
                {
                    "detail": "Idempotency-Key header is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        destination_wallet_id = serializer.validated_data[
            "destination_wallet_id"
        ]

        amount = serializer.validated_data["amount"]
        print(amount,"amounnt")
        try:
            transaction_record, created = create_transfer(
                source_wallet_id=wallet_id,
                destination_wallet_id=destination_wallet_id,
                tenant=request.tenant,
                amount=amount,
                idempotency_key=idempotency_key,
            )

        except Wallet.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Source or destination wallet "
                        "not found in this tenant."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_data = {
            "transaction_id": str(transaction_record.id),
            "transfer_id": str(
                transaction_record.transfer_id
            ),
            "source_wallet_id": str(
                transaction_record.wallet_id
            ),
            "destination_wallet_id": str(
                destination_wallet_id
            ),
            "transaction_type": (
                transaction_record.transaction_type
            ),
            "amount": transaction_record.amount,
            "created_at": transaction_record.created_at,
        }

        if not created:
            response_data["idempotent"] = True

        return Response(
            response_data,
            status=status.HTTP_200_OK,
        )

    
class TransactionHistoryPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

class WalletTransactionHistoryView(APIView):
    pagination_class = TransactionHistoryPagination

    def get(self, request, wallet_id):
        try:
            wallet = Wallet.objects.get(
                id=wallet_id,
                tenant=request.tenant,
            )
            print("hw wallet", wallet)
        except Wallet.DoesNotExist:
            return Response(
                {
                    "detail": "Wallet not found in this tenant."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        transactions = (
            Transaction.objects
            .filter(
                wallet=wallet,
                tenant=request.tenant,
            )
            .order_by("-created_at")
        )

        paginator = self.pagination_class()
        print(paginator)

        page = paginator.paginate_queryset(
            transactions,
            request,
            view=self,
        )
        print(page)

        serializer = TransactionSerializer(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )


class WalletBalanceView(APIView):
    def get(self, request, wallet_id):
        try:
            wallet = Wallet.objects.get(
                id=wallet_id,
                tenant=request.tenant,
            )
        except Wallet.DoesNotExist:
            return Response(
                {
                    "detail": "Wallet not found in this tenant."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        balance = get_wallet_balance(
            wallet_id=wallet.id,
            tenant=request.tenant,
        )
        print(balance)

        return Response(
            {
                "wallet_id": str(wallet.id),
                "balance": balance,
            },
            status=status.HTTP_200_OK,
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
        print(idempotency_key)

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


class WithdrawView(APIView):
    def post(self, request, wallet_id):
        idempotency_key = request.headers.get("Idempotency-Key")

        if not idempotency_key:
            return Response(
                {
                    "detail": "Idempotency-Key header is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = WithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]

        try:
            transaction_record, created = create_withdrawal(
                wallet_id=wallet_id,
                tenant=request.tenant,
                amount=amount,
                idempotency_key=idempotency_key,
            )

        except Wallet.DoesNotExist:
            return Response(
                {
                    "detail": "Wallet not found in this tenant."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
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