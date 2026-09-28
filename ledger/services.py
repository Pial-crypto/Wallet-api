import uuid

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
        return existing_transaction, False

    current_balance = get_wallet_balance(
        wallet_id=wallet.id,
        tenant=tenant,
    )

    if current_balance < amount:
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

    return transaction_record, True


@transaction.atomic
def create_transfer(
    *,
    source_wallet_id,
    destination_wallet_id,
    tenant,
    amount,
    idempotency_key,
):
    if source_wallet_id == destination_wallet_id:
        raise ValueError(
            "Source and destination wallets must be different."
        )

    # Check idempotency before doing the financial operation.
    existing_transaction = (
        Transaction.objects
        .filter(
            tenant=tenant,
            idempotency_key=idempotency_key,
            transaction_type=Transaction.TransactionType.TRANSFER_OUT,
        )
        .first()
    )

    if existing_transaction:
        return existing_transaction, False

    # Always lock wallets in deterministic ID order.
    # This helps prevent deadlocks when two transfers happen
    # in opposite directions concurrently.
    wallet_ids = sorted(
        [
            source_wallet_id,
            destination_wallet_id,
        ],
        key=str,
    )

    locked_wallets = list(
        Wallet.objects
        .select_for_update()
        .filter(
            id__in=wallet_ids,
            tenant=tenant,
        )
        .order_by("id")
    )

    if len(locked_wallets) != 2:
        raise Wallet.DoesNotExist

    wallets_by_id = {
        wallet.id: wallet
        for wallet in locked_wallets
    }

    source_wallet = wallets_by_id[source_wallet_id]
    destination_wallet = wallets_by_id[destination_wallet_id]

    current_balance = get_wallet_balance(
        wallet_id=source_wallet.id,
        tenant=tenant,
    )

    if current_balance < amount:
        raise ValueError(
            f"Insufficient funds. "
            f"Available balance: {current_balance}"
        )

    transfer_id = uuid.uuid4()

    transfer_out = Transaction.objects.create(
        tenant=tenant,
        wallet=source_wallet,
        transaction_type=Transaction.TransactionType.TRANSFER_OUT,
        amount=amount,
        transfer_id=transfer_id,
        idempotency_key=idempotency_key,
    )

    Transaction.objects.create(
        tenant=tenant,
        wallet=destination_wallet,
        transaction_type=Transaction.TransactionType.TRANSFER_IN,
        amount=amount,
        transfer_id=transfer_id,
    )

    return transfer_out, True