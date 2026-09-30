from rest_framework import viewsets
from core.escopo import registros_de_alunos_visiveis
from core.permissions import IsGestorOrReadOnly
from ..models import Documento # troque "Aluno"
from .serializers import DocumentoSerializer

class DocumentoViewSet(viewsets.ModelViewSet):
    """
    Gestão escolar: CRUD completo. Responsável: somente leitura dos registros
    dos próprios dependentes. Demais papéis: nenhum registro.
    """
    serializer_class = DocumentoSerializer
    permission_classes = [IsGestorOrReadOnly]

    def get_queryset(self):
        return registros_de_alunos_visiveis(
            Documento.objects.all(), self.request.user
        ).order_by('id')
