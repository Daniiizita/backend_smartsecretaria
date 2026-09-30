from rest_framework import viewsets
from core.permissions import IsGestorOrReadOnly
from ..models import Professor  # troque "Aluno"
from .serializers import ProfessorSerializer

class ProfessorViewSet(viewsets.ModelViewSet):
    """
    ViewSet base para CRUD completo do modelo.
    """
    queryset = Professor.objects.all().order_by('id')  # ajuste a ordenação se precisar
    serializer_class = ProfessorSerializer
    permission_classes = [IsGestorOrReadOnly]
