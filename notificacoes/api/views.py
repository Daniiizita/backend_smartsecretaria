from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from ..models import Notificacao
from .serializers import NotificacaoSerializer

class NotificacaoViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Cada usuário vê apenas as próprias notificações e só pode marcá-las como lidas.
    As notificações são geradas pelo sistema, não criadas pela API.
    """
    serializer_class = NotificacaoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notificacao.objects.filter(usuario=self.request.user).order_by('-criada_em')
