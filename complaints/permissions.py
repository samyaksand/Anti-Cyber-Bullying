from rest_framework.permissions import BasePermission


def user_is_admin(user):
    return user.is_authenticated and (
        user.is_staff or getattr(getattr(user, 'profile', None), 'is_admin', False)
    )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return user_is_admin(request.user)


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if user_is_admin(request.user):
            return True
        return obj.reporter_id == request.user.id
