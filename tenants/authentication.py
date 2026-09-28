from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import Tenant


class TenantAuthentication(BaseAuthentication):
    """
    Resolves the current tenant from the X-Tenant-ID header.
    """

    def authenticate(self, request):
        tenant_id = request.headers.get("X-Tenant-ID")

        if not tenant_id:
            raise AuthenticationFailed(
                "X-Tenant-ID header is required."
            )

        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            raise AuthenticationFailed(
                "Invalid tenant."
            )

        request.tenant = tenant

        # We are authenticating the tenant, not a Django user.
        return (None, tenant)