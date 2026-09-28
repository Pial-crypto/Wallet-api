from django.db import transaction
from django.db.models import Case, F, IntegerField, Sum, Value, When

from .models import Transaction
from wallets.models import Wallet


@transaction.atomic
def create_deposit(
    *,
    wallet_id,
    tenant,
    amount,
    idempotency_key,
):
    wallet = (
        Wallet.objects
        .select_for_update()
        .get(
            id=wallet_id,
            tenant=tenant,
        )
    )

    existing_transaction = (
        Transaction.objects
        .filter(
            tenant=tenant,
            idempotency_key=idempotency_key,
        )
        .first()
    )

    if existing_transaction:
        return existing_transaction, False

    transaction_record = Transaction.objects.create(
        tenant=tenant,
        wallet=wallet,
        transaction_type=Transaction.TransactionType.DEPOSIT,
        amount=amount,
        idempotency_key=idempotency_key,
    )

    return transaction_record, True


def get_wallet_balance(*, wallet_id, tenant):
    balance = (
        Transaction.objects
        .filter(
            wallet_id=wallet_id,
            tenant=tenant,
        )
        .aggregate(
            balance=Sum(
                Case(
                    When(
                        transaction_type__in=[
                            Transaction.TransactionType.DEPOSIT,
                            Transaction.TransactionType.TRANSFER_IN,
                        ],
                        then=F("amount"),
                    ),
                    When(
                        transaction_type__in=[
                            Transaction.TransactionType.WITHDRAW,
                            Transaction.TransactionType.TRANSFER_OUT,
                        ],
                        then=-F("amount"),
                    ),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            )
        )["balance"]
    )

    return balance or 0

@transaction.atomic
def create_withdrawal(
    *,
    wallet_id,
    tenant,
    amount,
    idempotency_key,
):
    wallet = (
        Wallet.objects
        .select_for_update()
        .get(
            id=wallet_id,
            tenant=tenant,
        )
    )

    existing_transaction = (
        Transaction.objects
        .filter(
            tenant=tenant,
            idempotency_key=idempotency_key,
        )
        .first()
    )

    if existing_transaction:
        print("I am existing",existing_transaction)
        return existing_transaction, False

    current_balance = get_wallet_balance(
        wallet_id=wallet.id,
        tenant=tenant,
    )

    if current_balance < amount:
        print("Insufficient bro")
        raise ValueError(
            f"Insufficient funds. "
            f"Available balance: {current_balance}"
        )

    transaction_record = Transaction.objects.create(
        tenant=tenant,
        wallet=wallet,
        transaction_type=Transaction.TransactionType.WITHDRAW,
        amount=amount,
        idempotency_key=idempotency_key,
    )
    print(transaction_record)

    return transaction_record, True