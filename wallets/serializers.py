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