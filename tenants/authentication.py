from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import Tenant


class TenantAuthentication(BaseAuthentication):
    """
    Authenticate requests using either:

    X-Tenant-ID: <tenant_uuid>

    OR

    X-API-Key: <tenant_api_key>
    """

    def authenticate(self, request):
        tenant_id = request.headers.get("X-Tenant-ID")
        api_key = request.headers.get("X-API-Key")

        if not tenant_id and not api_key:
            raise AuthenticationFailed(
                "X-Tenant-ID or X-API-Key header is required."
            )

        tenant = None

        if api_key:
            try:
                tenant = Tenant.objects.get(api_key=api_key)
            except Tenant.DoesNotExist:
                raise AuthenticationFailed("Invalid API key.")

        elif tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
            except (Tenant.DoesNotExist, ValueError):
                raise AuthenticationFailed("Invalid tenant.")

        request.tenant = tenant

        return (None, tenant)