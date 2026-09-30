from rest_framework import viewsets
from core.permissions import IsGestorOrReadOnly
from ..models import Evento  # troque "Aluno"
from .serializers import CalendarioSerializer

class CalendarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet base para CRUD completo do modelo.
    """
    queryset = Evento.objects.all().order_by('id')  # ajuste a ordenação se precisar
    serializer_class = CalendarioSerializer
    permission_classes = [IsGestorOrReadOnly]
