from rest_framework import serializers
from ..models import Aluno

class AlunoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno
        fields = '__all__'

    def validate_responsaveis(self, value):
        invalidos = [u.username for u in value if u.tipo != 'responsavel']
        if invalidos:
            raise serializers.ValidationError(
                'Contas vinculadas precisam ser do tipo responsável: '
                + ', '.join(invalidos)
            )
        return value


class AlunoPedagogicoSerializer(serializers.ModelSerializer):
    """Para professores: apenas o necessário ao trabalho pedagógico em sala (LGPD, art. 6º, III)."""

    class Meta:
        model = Aluno
        fields = [
            'id',
            'nome_completo',
            'foto',
            'turma',
            'data_nascimento',
            'nome_responsavel',
            'telefone_contato',
        ]
        read_only_fields = fields


class AlunoResponsavelSerializer(serializers.ModelSerializer):
    """Para o responsável: os dados do próprio dependente, sem as contas de outros responsáveis."""

    class Meta:
        model = Aluno
        exclude = ['responsaveis']
        read_only_fields = [f.name for f in Aluno._meta.fields]
