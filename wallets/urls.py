from django.urls import path

from .views import (
    DepositView,
    WalletCreateView,
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
]