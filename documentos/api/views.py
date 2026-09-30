from rest_framework import viewsets
from core.permissions import IsGestor
from ..models import Documento # troque "Aluno"
from .serializers import DocumentoSerializer

class DocumentoViewSet(viewsets.ModelViewSet):
    """
    ViewSet base para CRUD completo do modelo.
    """
    queryset = Documento.objects.all().order_by('id')  # ajuste a ordenação se precisar
    serializer_class = DocumentoSerializer
    permission_classes = [IsGestor]
