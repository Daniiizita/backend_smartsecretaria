from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permissions import IsAdmin, ProtectSuperuser
from ..models import CustomUser
from .serializers import CustomUserSerializer, TrocarSenhaSerializer

class CustomUserViewSet(viewsets.ModelViewSet):
    """
    Gestão de usuários: restrita a administradores.
    Qualquer usuário autenticado consulta (sem editar) o próprio perfil em /me/.
    """
    queryset = CustomUser.objects.all().order_by('id')
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated, IsAdmin, ProtectSuperuser]

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
