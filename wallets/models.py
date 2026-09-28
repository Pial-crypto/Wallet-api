from django.db import models

# Create your models here.

from django.db import models
import uuid


class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="wallets",
    )

    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="wallet",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wallet {self.id}"
