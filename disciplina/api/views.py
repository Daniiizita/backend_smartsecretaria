from rest_framework import viewsets
from core.permissions import IsGestorOrReadOnly
from disciplina.models import Disciplina
from .serializers import DisciplinaSerializer

class DisciplinaViewSet(viewsets.ModelViewSet):
    queryset = Disciplina.objects.all().order_by('id')
    serializer_class = DisciplinaSerializer
    permission_classes = [IsGestorOrReadOnly]