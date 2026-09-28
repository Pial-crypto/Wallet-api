from rest_framework import serializers

from .models import Wallet


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = [
            "id",
            "user",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]


class DepositSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)


class WithdrawSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)

class TransferSerializer(serializers.Serializer):
    destination_wallet_id = serializers.UUIDField()
    amount = serializers.IntegerField(min_value=1)