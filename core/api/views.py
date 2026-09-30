from rest_framework.views import APIView
from rest_framework.response import Response
from core.permissions import IsGestor
from django.utils import timezone

from aluno.models import Aluno
from professor.models import Professor
from turma.models import Turma
from matricula.models import Matricula
from calendario.models import Evento
from documentos.models import Documento
from logs.models import LogAtividade

from .serializers import AlunoSimpleSerializer, EventoSimpleSerializer, LogAtividadeSerializer


class DashboardAPIView(APIView):
    """
    API que fornece os dados agregados para o dashboard principal.
    """
    permission_classes = [IsGestor]

    def get(self, request, format=None):
        hoje = timezone.now()
        ano_atual = hoje.year
        mes_atual = hoje.month

        # Contagens gerais
        total_alunos = Aluno.objects.count()
        total_professores = Professor.objects.count()
        total_turmas = Turma.objects.count()
        total_matriculas_ativas = Matricula.objects.filter(status='ativo').count()

        # Próximos eventos
        proximos_eventos_qs = Evento.objects.filter(
            data_inicio__gte=hoje
        ).order_by('data_inicio')[:5]

        # Últimos alunos cadastrados
        ultimos_alunos_qs = Aluno.objects.all().order_by('-id')[:5]

        # Últimas atividades do sistema
        ultimas_atividades_qs = LogAtividade.objects.all().order_by('-data_hora')[:10]

        # Contadores adicionais
        documentos_mes_atual = Documento.objects.filter(
            data_emissao__year=ano_atual,
            data_emissao__month=mes_atual
        ).count()

        data = {
            'total_alunos': total_alunos,
            'total_professores': total_professores,
            'total_turmas': total_turmas,
            'total_matriculas_ativas': total_matriculas_ativas,
            'documentos_mes_atual': documentos_mes_atual,
            'proximos_eventos': EventoSimpleSerializer(proximos_eventos_qs, many=True).data,
            'ultimos_alunos': AlunoSimpleSerializer(ultimos_alunos_qs, many=True).data,
            'ultimas_atividades': LogAtividadeSerializer(ultimas_atividades_qs, many=True).data,
        }
        return Response(data)

