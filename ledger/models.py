from django.db import models

# Create your models here.
from django.db import models
import uuid


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        DEPOSIT = "DEPOSIT", "Deposit"
        WITHDRAW = "WITHDRAW", "Withdraw"
        TRANSFER_IN = "TRANSFER_IN", "Transfer In"
        TRANSFER_OUT = "TRANSFER_OUT", "Transfer Out"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="transactions",
    )

    wallet = models.ForeignKey(
        "wallets.Wallet",
        on_delete=models.PROTECT,
        related_name="transactions",
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
    )


    amount = models.PositiveBigIntegerField()
    print("amount")

    transfer_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
    )

    print(transfer_id)


    idempotency_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    print(idempotency_key)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "idempotency_key"],
                name="unique_idempotency_key_per_tenant",
            )
        ]

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"