from rest_framework import viewsets
from core.permissions import IsAdmin
from ..models import PerfilAcesso, TentativaLogin
from .serializers import PerfilAcessoSerializer, TentativaLoginSerializer

class PerfilAcessoViewSet(viewsets.ModelViewSet):
    """
    Perfis de acesso: configuração do sistema, restrita a administradores.
    """
    queryset = PerfilAcesso.objects.all().order_by('id')
    serializer_class = PerfilAcessoSerializer
    permission_classes = [IsAdmin]

class TentativaLoginViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Registro de tentativas de login: somente leitura, restrito a administradores.
    """
    queryset = TentativaLogin.objects.all().order_by('id')
    serializer_class = TentativaLoginSerializer
    permission_classes = [IsAdmin]
