from functools import wraps
from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    """Admin role required"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               hasattr(request.user, 'profile') and request.user.profile.role == 'admin'


class IsEditorOrAdmin(BasePermission):
    """Editor or Admin role required"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               hasattr(request.user, 'profile') and \
               request.user.profile.role in ['admin', 'editor']


class IsDocumentOwnerOrCollaborator(BasePermission):
    """Check if user is owner or collaborator of document"""
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user in obj.collaborators.all()


def require_role(*roles):
    """Decorator for WebSocket consumers to check user roles"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if not self.user.is_authenticated:
                return
            if not hasattr(self.user, 'profile'):
                return
            if self.user.profile.role not in roles:
                return
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator
