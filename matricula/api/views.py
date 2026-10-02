from django.db import transaction
from rest_framework import viewsets
from core.escopo import filtrar_por_aluno, registros_de_alunos_visiveis
from core.permissions import IsGestorOrReadOnly
from ..models import Matricula
from .serializers import MatriculaSerializer


def sincronizar_turma_do_aluno(matricula):
    """Matrícula ativa define a turma atual do aluno (evita ficha e matrícula divergentes)."""
    if matricula.status == 'ativo' and matricula.aluno.turma_id != matricula.turma_id:
        matricula.aluno.turma = matricula.turma
        matricula.aluno.save(update_fields=['turma'])


class MatriculaViewSet(viewsets.ModelViewSet):
    """
    Gestão escolar: CRUD completo. Responsável: somente leitura dos registros
    dos próprios dependentes. Demais papéis: nenhum registro.
    Filtros: ?aluno=, ?turma=, ?ano=, ?status=.
    """
    serializer_class = MatriculaSerializer
    permission_classes = [IsGestorOrReadOnly]

    def get_queryset(self):
        queryset = registros_de_alunos_visiveis(Matricula.objects.all(), self.request.user)
        queryset = filtrar_por_aluno(queryset, self.request)
        params = self.request.query_params
        if params.get('turma', '').isdigit():
            queryset = queryset.filter(turma_id=int(params['turma']))
        if params.get('ano', '').isdigit():
            queryset = queryset.filter(ano_letivo=int(params['ano']))
        if params.get('status') in dict(Matricula.STATUS_CHOICES):
            queryset = queryset.filter(status=params['status'])
        return (
            queryset.select_related('aluno', 'turma')
            .order_by('-ano_letivo', 'aluno__nome_completo', 'id')
        )

    @transaction.atomic
    def perform_create(self, serializer):
        sincronizar_turma_do_aluno(serializer.save())

    @transaction.atomic
    def perform_update(self, serializer):
        sincronizar_turma_do_aluno(serializer.save())
