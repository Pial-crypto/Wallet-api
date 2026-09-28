from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]

    def create(self, validated_data):
        tenant = self.context["tenant"]
        print(tenant, "I am the tenant")

        password = validated_data.pop("password")

        user = User.objects.create_user(
            tenant=tenant,
            password=password,
            **validated_data,
        )
        print(user)

        return user