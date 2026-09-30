from rest_framework import viewsets
from core.permissions import IsAdmin
from ..models import LogAtividade
from .serializers import LogSerializer

class LogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Trilha de auditoria: somente administradores consultam, e ninguém altera pela API.
    """
    queryset = LogAtividade.objects.all().order_by('id')
    serializer_class = LogSerializer
    permission_classes = [IsAdmin]
