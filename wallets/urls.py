from django.urls import path

from .views import WalletCreateView


urlpatterns = [
    path(
        "",
        WalletCreateView.as_view(),
        name="wallet-create",
    ),
]