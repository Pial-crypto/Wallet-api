from django.urls import path

from .views import (
    DepositView,
    WalletBalanceView,
    WalletCreateView,
    WalletTransactionHistoryView,
    WithdrawView,
)


urlpatterns = [
    path(
        "",
        WalletCreateView.as_view(),
        name="wallet-create",
    ),

    path(
        "<uuid:wallet_id>/deposit/",
        DepositView.as_view(),
        name="wallet-deposit",
    ),

    path(
        "<uuid:wallet_id>/withdraw/",
        WithdrawView.as_view(),
        name="wallet-withdraw",
    ),

    path(
        "<uuid:wallet_id>/balance/",
        WalletBalanceView.as_view(),
        name="wallet-balance",
    ),

    path(
        "<uuid:wallet_id>/transactions/",
        WalletTransactionHistoryView.as_view(),
        name="wallet-transactions",
    ),
]