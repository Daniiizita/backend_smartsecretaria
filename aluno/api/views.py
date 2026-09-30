from rest_framework import viewsets
from core.permissions import IsGestorOrReadOnly
from aluno.models import Aluno
from .serializers import AlunoSerializer

class AlunoViewSet(viewsets.ModelViewSet):
    queryset = Aluno.objects.all().order_by('id')
    serializer_class = AlunoSerializer
    permission_classes = [IsGestorOrReadOnly]
