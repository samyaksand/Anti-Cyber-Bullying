from .models import AuditLog

AUDITED_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method in AUDITED_METHODS and request.path.startswith(('/api/', '/admin-console/')):
            try:
                AuditLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    path=request.path[:300],
                    method=request.method,
                    status_code=response.status_code,
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
            except Exception:
                pass
        return response
