from rest_framework.permissions import BasePermission


def is_admin(user):
    """Administrador: superusuário do Django ou usuário com tipo 'admin'."""
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or getattr(user, 'tipo', None) == 'admin')
    )


class IsAdmin(BasePermission):
    message = 'Apenas administradores podem realizar esta ação.'

    def has_permission(self, request, view):
        return is_admin(request.user)


class ProtectSuperuser(BasePermission):
    """Somente um superusuário pode alterar ou excluir a conta de outro superusuário."""

    message = 'Apenas superusuários podem alterar contas de superusuário.'

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return not obj.is_superuser or request.user.is_superuser
