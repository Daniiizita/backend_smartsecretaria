from rest_framework import serializers
from ..models import Turma, TurmaDisciplina


class TurmaSerializer(serializers.ModelSerializer):
    # Campos de leitura para exibição (nome e nível são calculados pelo modelo ao salvar).
    serie_label = serializers.CharField(source='get_serie_display', read_only=True)
    nivel_label = serializers.CharField(source='get_nivel_ensino_sigla_display', read_only=True)
    professor_responsavel_nome = serializers.CharField(
        source='professor_responsavel.nome', read_only=True
    )
    total_alunos = serializers.SerializerMethodField()

    class Meta:
        model = Turma
        fields = [
            'id',
            'nome',
            'serie',
            'serie_label',
            'turma_letra',
            'periodo',
            'ano',
            'nivel_ensino_sigla',
            'nivel_label',
            'horario_aulas',
            'professor_responsavel',
            'professor_responsavel_nome',
            'total_alunos',
        ]
        read_only_fields = ['nome', 'nivel_ensino_sigla']
        # A unicidade é validada em validate(), com mensagem clara (a restrição no banco continua).
        validators = []

    def get_total_alunos(self, turma) -> int:
        anotado = getattr(turma, 'total_alunos', None)
        return anotado if anotado is not None else turma.aluno_set.count()

    def validate(self, attrs):
        ano = attrs.get('ano', getattr(self.instance, 'ano', None))
        serie = attrs.get('serie', getattr(self.instance, 'serie', None))
        letra = attrs.get('turma_letra', getattr(self.instance, 'turma_letra', 'A'))
        if ano is None:
            ano = Turma._meta.get_field('ano').get_default()
        repetidas = Turma.objects.filter(ano=ano, serie=serie, turma_letra=letra)
        if self.instance is not None:
            repetidas = repetidas.exclude(pk=self.instance.pk)
        if repetidas.exists():
            raise serializers.ValidationError(
                {'turma_letra': f'Já existe uma turma {letra} desta série em {ano}.'}
            )
        return attrs


class TurmaDisciplinaSerializer(serializers.ModelSerializer):
    disciplina_nome = serializers.CharField(source='disciplina.nome', read_only=True)
    professor_nome = serializers.CharField(source='professor.nome', read_only=True)

    class Meta:
        model = TurmaDisciplina
        fields = ['id', 'turma', 'disciplina', 'disciplina_nome', 'professor', 'professor_nome']
        validators = []

    def validate(self, attrs):
        turma = attrs.get('turma', getattr(self.instance, 'turma', None))
        disciplina = attrs.get('disciplina', getattr(self.instance, 'disciplina', None))
        repetidas = TurmaDisciplina.objects.filter(turma=turma, disciplina=disciplina)
        if self.instance is not None:
            repetidas = repetidas.exclude(pk=self.instance.pk)
        if repetidas.exists():
            raise serializers.ValidationError(
                {'disciplina': 'Esta disciplina já tem professor nesta turma.'}
            )
        return attrs
