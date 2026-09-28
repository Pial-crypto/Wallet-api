from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "api/tenants/",
        include("tenants.urls"),
    ),

    path(
        "api/users/",
        include("users.urls"),
    ),
    path(
    "api/wallets/",
    include("wallets.urls"),
),
]