from rest_framework import serializers

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id",
            "wallet",
            "transaction_type",
            "amount",
            "transfer_id",
            "idempotency_key",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "wallet",
            "transaction_type",
            "amount",
            "transfer_id",
            "idempotency_key",
            "created_at",
        ]