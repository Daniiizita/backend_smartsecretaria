from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from core.escopo import turmas_visiveis
from core.permissions import IsGestorOrReadOnly
from ..models import Turma, TurmaDisciplina, SERIE_CHOICES, NIVEL_CHOICES, TURMA_LETRA_CHOICES, PERIODO_CHOICES
from .serializers import TurmaDisciplinaSerializer, TurmaSerializer

class TurmaViewSet(viewsets.ModelViewSet):
    """
    ViewSet base para CRUD completo do modelo.
    """
    serializer_class = TurmaSerializer
    permission_classes = [IsGestorOrReadOnly]

    def get_queryset(self):
        # Gestão vê todas; professor, as turmas em que atua; responsável, as dos filhos.
        return turmas_visiveis(self.request.user).order_by('id')

    @action(detail=False, methods=['get'], url_path='choices')
    def choices(self, request):
        return Response({
            'serie': [{'value': v, 'label': l} for v, l in SERIE_CHOICES],
            'nivel': [{'value': v, 'label': l} for v, l in NIVEL_CHOICES],
            'turma_letra': [{'value': v, 'label': l} for v, l in TURMA_LETRA_CHOICES],
            'periodo': [{'value': v, 'label': l} for v, l in PERIODO_CHOICES],
        })


class TurmaDisciplinaViewSet(viewsets.ModelViewSet):
    """Atribuição de professores às disciplinas de cada turma."""
    serializer_class = TurmaDisciplinaSerializer
    permission_classes = [IsGestorOrReadOnly]

    def get_queryset(self):
        return (
            TurmaDisciplina.objects.filter(turma__in=turmas_visiveis(self.request.user))
            .select_related('turma', 'disciplina', 'professor')
            .order_by('id')
        )
