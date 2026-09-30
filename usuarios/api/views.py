from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permissions import (
    CanManageUserAccounts,
    ProtectSuperuser,
    tipos_de_conta_gerenciaveis,
)
from ..models import CustomUser
from .serializers import CustomUserSerializer, TrocarSenhaSerializer

class CustomUserViewSet(viewsets.ModelViewSet):
    """
    Gestão de contas: administradores gerenciam todas; secretários, apenas
    professor, aluno e responsável.
    Qualquer usuário autenticado consulta (sem editar) o próprio perfil em /me/.
    """
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated, CanManageUserAccounts, ProtectSuperuser]

    def get_queryset(self):
        queryset = CustomUser.objects.all().order_by('id')
        tipos = tipos_de_conta_gerenciaveis(self.request.user)
        if tipos is not None:
            # Contas fora do alcance do usuário nem aparecem (respondem 404).
            queryset = queryset.filter(tipo__in=tipos, is_superuser=False)
        return queryset

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        return Response(self.get_serializer(request.user).data)

    @action(
        detail=False,
        methods=['post'],
        url_path='me/senha',
        permission_classes=[IsAuthenticated],
        serializer_class=TrocarSenhaSerializer,
    )
    def trocar_senha(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
