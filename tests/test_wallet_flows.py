import uuid
from concurrent.futures import ThreadPoolExecutor

from django.db import close_old_connections, connections
from django.test import TransactionTestCase
from rest_framework.test import APIClient

from ledger.models import Transaction
from tenants.models import Tenant
from users.models import User
from wallets.models import Wallet


class WalletFlowTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.client = APIClient()

        self.tenant_a = Tenant.objects.create(
            name="Tenant A",
            api_key=uuid.uuid4().hex,
        )

        self.tenant_b = Tenant.objects.create(
            name="Tenant B",
            api_key=uuid.uuid4().hex,
        )

        self.user_a1 = User.objects.create_user(
            email="user-a1@example.com",
            password="password123",
            tenant=self.tenant_a,
        )

        self.user_a2 = User.objects.create_user(
            email="user-a2@example.com",
            password="password123",
            tenant=self.tenant_a,
        )

        self.user_b1 = User.objects.create_user(
            email="user-b1@example.com",
            password="password123",
            tenant=self.tenant_b,
        )

        self.wallet_a1 = Wallet.objects.create(
            tenant=self.tenant_a,
            user=self.user_a1,
        )

        self.wallet_a2 = Wallet.objects.create(
            tenant=self.tenant_a,
            user=self.user_a2,
        )

        self.wallet_b1 = Wallet.objects.create(
            tenant=self.tenant_b,
            user=self.user_b1,
        )

        self.user_a3 = User.objects.create_user(
            email="user-a3@example.com",
            password="password123",
            tenant=self.tenant_a,
        )

        self.wallet_a3 = Wallet.objects.create(
            tenant=self.tenant_a,
            user=self.user_a3,
        )

    def tenant_headers(self, tenant):
        return {
            "HTTP_X_TENANT_ID": str(tenant.id),
        }

    def deposit(
        self,
        wallet,
        tenant,
        amount,
        idempotency_key,
    ):
        response = self.client.post(
            f"/api/wallets/{wallet.id}/deposit/",
            {
                "amount": amount,
            },
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
            HTTP_IDEMPOTENCY_KEY=idempotency_key,
        )

        return response

    def get_balance(self, wallet, tenant):
        return self.client.get(
            f"/api/wallets/{wallet.id}/balance/",
            **self.tenant_headers(tenant),
        )

    def test_withdraw_rejects_insufficient_funds(self):
        self.deposit(
            wallet=self.wallet_a1,
            tenant=self.tenant_a,
            amount=500,
            idempotency_key="deposit-insufficient-test",
        )

        response = self.client.post(
            f"/api/wallets/{self.wallet_a1.id}/withdraw/",
            {
                "amount": 600,
            },
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
            HTTP_IDEMPOTENCY_KEY="withdraw-insufficient-test",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "Insufficient funds",
            response.data["detail"],
        )

        balance_response = self.get_balance(
            self.wallet_a1,
            self.tenant_a,
        )

        self.assertEqual(
            balance_response.data["balance"],
            500,
        )

        self.assertFalse(
            Transaction.objects.filter(
                wallet=self.wallet_a1,
                transaction_type=Transaction.TransactionType.WITHDRAW,
            ).exists()
        )

    def test_duplicate_idempotency_key_does_not_double_deposit(self):
        first_response = self.deposit(
            wallet=self.wallet_a1,
            tenant=self.tenant_a,
            amount=1000,
            idempotency_key="duplicate-deposit",
        )

        second_response = self.deposit(
            wallet=self.wallet_a1,
            tenant=self.tenant_a,
            amount=1000,
            idempotency_key="duplicate-deposit",
        )

        self.assertEqual(
            first_response.status_code,
            200,
        )

        self.assertEqual(
            second_response.status_code,
            200,
        )

        self.assertTrue(
            second_response.data.get("idempotent")
        )

        transaction_count = Transaction.objects.filter(
            tenant=self.tenant_a,
            wallet=self.wallet_a1,
            transaction_type=Transaction.TransactionType.DEPOSIT,
        ).count()

        self.assertEqual(
            transaction_count,
            1,
        )

        balance_response = self.get_balance(
            self.wallet_a1,
            self.tenant_a,
        )

        self.assertEqual(
            balance_response.data["balance"],
            1000,
        )

    def test_same_idempotency_key_with_different_request_is_rejected(self):
        first_response = self.deposit(
            wallet=self.wallet_a1,
            tenant=self.tenant_a,
            amount=1000,
            idempotency_key="same-key-different-request",
        )

        self.assertEqual(
            first_response.status_code,
            200,
        )

        second_response = self.deposit(
            wallet=self.wallet_a1,
            tenant=self.tenant_a,
            amount=2000,
            idempotency_key="same-key-different-request",
        )

        self.assertEqual(
            second_response.status_code,
            400,
        )

        self.assertIn(
            "different request",
            second_response.data["detail"],
        )

        balance_response = self.get_balance(
            self.wallet_a1,
            self.tenant_a,
        )

        self.assertEqual(
            balance_response.data["balance"],
            1000,
        )

    def test_cross_tenant_wallet_access_is_blocked(self):
        response = self.get_balance(
            wallet=self.wallet_b1,
            tenant=self.tenant_a,
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_cross_tenant_transfer_is_blocked(self):
        self.deposit(
            wallet=self.wallet_a1,
            tenant=self.tenant_a,
            amount=1000,
            idempotency_key="cross-tenant-deposit",
        )

        response = self.client.post(
            f"/api/wallets/{self.wallet_a1.id}/transfer/",
            {
                "destination_wallet_id": str(
                    self.wallet_b1.id
                ),
                "amount": 500,
            },
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
            HTTP_IDEMPOTENCY_KEY="cross-tenant-transfer",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertFalse(
            Transaction.objects.filter(
                tenant=self.tenant_a,
                transaction_type=Transaction.TransactionType.TRANSFER_OUT,
            ).exists()
        )

    def test_transfer_is_atomic(self):
        self.deposit(
            wallet=self.wallet_a1,
            tenant=self.tenant_a,
            amount=1000,
            idempotency_key="atomic-deposit",
        )

        response = self.client.post(
            f"/api/wallets/{self.wallet_a1.id}/transfer/",
            {
                "destination_wallet_id": str(
                    self.wallet_a2.id
                ),
                "amount": 500,
            },
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant_a.id),
            HTTP_IDEMPOTENCY_KEY="atomic-transfer",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        source_balance = self.get_balance(
            self.wallet_a1,
            self.tenant_a,
        )

        destination_balance = self.get_balance(
            self.wallet_a2,
            self.tenant_a,
        )

        self.assertEqual(
            source_balance.data["balance"],
            500,
        )

        self.assertEqual(
            destination_balance.data["balance"],
            500,
        )

        transfer_entries = Transaction.objects.filter(
            transfer_id=response.data["transfer_id"],
        )

        self.assertEqual(
            transfer_entries.count(),
            2,
        )

    def test_concurrent_transfers_do_not_overspend(self):
        self.deposit(
            wallet=self.wallet_a1,
            tenant=self.tenant_a,
            amount=1000,
            idempotency_key="concurrent-deposit",
        )

        def perform_transfer(destination_wallet_id, key):
            close_old_connections()

            try:
                client = APIClient()

                return client.post(
                    f"/api/wallets/{self.wallet_a1.id}/transfer/",
                    {
                        "destination_wallet_id": str(
                            destination_wallet_id
                        ),
                        "amount": 700,
                    },
                    format="json",
                    HTTP_X_TENANT_ID=str(
                        self.tenant_a.id
                    ),
                    HTTP_IDEMPOTENCY_KEY=key,
                )

            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_one = executor.submit(
                perform_transfer,
                self.wallet_a2.id,
                "concurrent-transfer-1",
            )

            future_two = executor.submit(
                perform_transfer,
                self.wallet_a3.id,
                "concurrent-transfer-2",
            )

            response_one = future_one.result()
            response_two = future_two.result()

        # Close any connections opened by the main test thread.
        connections.close_all()

        statuses = {
            response_one.status_code,
            response_two.status_code,
        }

        self.assertIn(
            200,
            statuses,
        )

        self.assertIn(
            400,
            statuses,
        )

        source_balance = self.get_balance(
            self.wallet_a1,
            self.tenant_a,
        )

        self.assertEqual(
            source_balance.data["balance"],
            300,
        )

        # Close the main test connection before Django
        # attempts to destroy the test database.
        connections.close_all()