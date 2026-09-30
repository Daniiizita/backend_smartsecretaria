from rest_framework.permissions import BasePermission

# Tipos de conta que a secretaria pode criar e gerenciar.
TIPOS_GERENCIADOS_PELO_SECRETARIO = ('professor', 'aluno', 'responsavel')


def is_admin(user):
    """Administrador: superusuário do Django ou usuário com tipo 'admin'."""
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or getattr(user, 'tipo', None) == 'admin')
    )


def is_secretario(user):
    return bool(
        user
        and user.is_authenticated
        and getattr(user, 'tipo', None) == 'secretario'
        and not is_admin(user)
    )


def is_gestor(user):
    """Gestão escolar: administradores e secretários administram a escola."""
    return is_admin(user) or is_secretario(user)


def tipos_de_conta_gerenciaveis(user):
    """Tipos de conta que o usuário pode gerenciar; None significa todos."""
    if is_admin(user):
        return None
    if is_secretario(user):
        return TIPOS_GERENCIADOS_PELO_SECRETARIO
    return ()


class IsAdmin(BasePermission):
    message = 'Apenas administradores podem realizar esta ação.'

    def has_permission(self, request, view):
        return is_admin(request.user)


class CanManageUserAccounts(BasePermission):
    """Admins gerenciam todas as contas; secretários, apenas os tipos permitidos."""

    message = 'Você não tem permissão para gerenciar esta conta.'

    def has_permission(self, request, view):
        return is_admin(request.user) or is_secretario(request.user)

    def has_object_permission(self, request, view, obj):
        tipos = tipos_de_conta_gerenciaveis(request.user)
        if tipos is None:
            return True
        return obj.tipo in tipos and not obj.is_superuser


class ProtectSuperuser(BasePermission):
    """Somente um superusuário pode alterar ou excluir a conta de outro superusuário."""

    message = 'Apenas superusuários podem alterar contas de superusuário.'

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return not obj.is_superuser or request.user.is_superuser


class IsGestor(BasePermission):
    message = 'Apenas a gestão escolar (administração e secretaria) pode acessar.'

    def has_permission(self, request, view):
        return is_gestor(request.user)


class IsGestorOrReadOnly(BasePermission):
    """Leitura para autenticados; escrita somente para a gestão escolar."""

    message = 'Apenas a gestão escolar (administração e secretaria) pode alterar estes dados.'

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return bool(request.user and request.user.is_authenticated)
        return is_gestor(request.user)


def conta_de_demo_protegida(user):
    """No modo demonstração, as contas *_demo são públicas e não podem ser alteradas."""
    from django.conf import settings

    return bool(
        getattr(settings, 'DEMO_MODE', False)
        and user is not None
        and getattr(user, 'username', '').endswith(getattr(settings, 'DEMO_SUFIXO', '_demo'))
    )


class ProtegeContasDeDemo(BasePermission):
    """Impede editar, desativar, trocar a senha ou excluir contas públicas de demonstração."""

    message = 'Contas de demonstração não podem ser alteradas.'

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return not conta_de_demo_protegida(obj)
