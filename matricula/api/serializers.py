from django.utils import timezone
from rest_framework import serializers
from ..models import Matricula


class MatriculaSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.CharField(source='aluno.nome_completo', read_only=True)
    turma_nome = serializers.CharField(source='turma.nome', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    data_matricula = serializers.DateField(default=timezone.localdate)

    class Meta:
        model = Matricula
        fields = [
            'id',
            'aluno',
            'aluno_nome',
            'turma',
            'turma_nome',
            'ano_letivo',
            'data_matricula',
            'status',
            'status_label',
        ]
        # A unicidade é validada em validate(), com mensagem clara (a restrição no banco continua).
        validators = []

    def validate(self, attrs):
        get = lambda campo: attrs.get(campo, getattr(self.instance, campo, None))
        aluno, turma, ano, status = get('aluno'), get('turma'), get('ano_letivo'), get('status')

        if turma is not None and ano is not None and turma.ano != ano:
            raise serializers.ValidationError(
                {'turma': f'A turma escolhida é do ano letivo {turma.ano}, não de {ano}.'}
            )

        if status in Matricula.STATUS_VIGENTES:
            vigentes = Matricula.objects.filter(
                aluno=aluno, ano_letivo=ano, status__in=Matricula.STATUS_VIGENTES
            )
            if self.instance is not None:
                vigentes = vigentes.exclude(pk=self.instance.pk)
            if vigentes.exists():
                raise serializers.ValidationError(
                    {'aluno': f'Este aluno já tem uma matrícula ativa ou pendente em {ano}.'}
                )
        return attrs
