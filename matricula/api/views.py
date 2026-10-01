from rest_framework import viewsets
from core.escopo import filtrar_por_aluno, registros_de_alunos_visiveis
from core.permissions import IsGestorOrReadOnly
from ..models import Matricula  # troque "Aluno"
from .serializers import MatriculaSerializer

class MatriculaViewSet(viewsets.ModelViewSet):
    """
    Gestão escolar: CRUD completo. Responsável: somente leitura dos registros
    dos próprios dependentes. Demais papéis: nenhum registro.
    """
    serializer_class = MatriculaSerializer
    permission_classes = [IsGestorOrReadOnly]

    def get_queryset(self):
        queryset = registros_de_alunos_visiveis(Matricula.objects.all(), self.request.user)
        return filtrar_por_aluno(queryset, self.request).order_by('-ano_letivo', '-data_matricula', 'id')
