from django.db import transaction

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
    print(wallet,"hey wallet")
   
    existing_transaction = (
        Transaction.objects
        .filter(
            tenant=tenant,
            idempotency_key=idempotency_key,
        )
        .first()
    )

    if existing_transaction:
        print("transaction existing",existing_transaction)
        return existing_transaction, False

   
    transaction_record = Transaction.objects.create(
        tenant=tenant,
        wallet=wallet,
        transaction_type=Transaction.TransactionType.DEPOSIT,
        amount=amount,
        idempotency_key=idempotency_key,
    )
    print(transaction_record)

    return transaction_record, True