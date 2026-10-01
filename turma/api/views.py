from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from core.escopo import turmas_visiveis
from core.permissions import IsGestor, IsGestorOrReadOnly
from disciplina.models import Disciplina
from ..models import Turma, TurmaDisciplina, SERIE_CHOICES, NIVEL_CHOICES, TURMA_LETRA_CHOICES, PERIODO_CHOICES
from .serializers import TurmaDisciplinaSerializer, TurmaSerializer

class TurmaViewSet(viewsets.ModelViewSet):
    """
    Gestão escolar: CRUD completo. Professor: as turmas em que atua.
    Responsável: as turmas dos filhos. Somente leitura para quem não é da gestão.
    """
    serializer_class = TurmaSerializer
    permission_classes = [IsGestorOrReadOnly]

    def get_queryset(self):
        return (
            turmas_visiveis(self.request.user)
            .select_related('professor_responsavel')
            .annotate(total_alunos=Count('aluno', distinct=True))
            .order_by('-ano', 'serie', 'turma_letra')
        )

    @action(detail=False, methods=['get'], url_path='choices')
    def choices(self, request):
        return Response({
            'serie': [{'value': v, 'label': l} for v, l in SERIE_CHOICES],
            'nivel': [{'value': v, 'label': l} for v, l in NIVEL_CHOICES],
            'turma_letra': [{'value': v, 'label': l} for v, l in TURMA_LETRA_CHOICES],
            'periodo': [{'value': v, 'label': l} for v, l in PERIODO_CHOICES],
        })

    @action(detail=True, methods=['post'], url_path='professor-unico', permission_classes=[IsGestor])
    def professor_unico(self, request, pk=None):
        """Turma com professor único: o regente passa a lecionar todas as disciplinas."""
        turma = self.get_object()
        for disciplina in Disciplina.objects.all():
            TurmaDisciplina.objects.update_or_create(
                turma=turma,
                disciplina=disciplina,
                defaults={'professor_id': turma.professor_responsavel_id},
            )
        atribuicoes = turma.atribuicoes.select_related('disciplina', 'professor').order_by('disciplina__nome')
        return Response(TurmaDisciplinaSerializer(atribuicoes, many=True).data, status=status.HTTP_200_OK)


class TurmaDisciplinaViewSet(viewsets.ModelViewSet):
    """Atribuição de professores às disciplinas de cada turma (?turma=<id> filtra)."""
    serializer_class = TurmaDisciplinaSerializer
    permission_classes = [IsGestorOrReadOnly]

    def get_queryset(self):
        queryset = (
            TurmaDisciplina.objects.filter(turma__in=turmas_visiveis(self.request.user))
            .select_related('turma', 'disciplina', 'professor')
            .order_by('disciplina__nome')
        )
        turma = self.request.query_params.get('turma')
        if turma and turma.isdigit():
            queryset = queryset.filter(turma_id=int(turma))
        return queryset
