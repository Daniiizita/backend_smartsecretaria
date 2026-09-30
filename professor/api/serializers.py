from rest_framework import serializers
from ..models import Professor  # troque "Aluno" pelo modelo do app

class ProfessorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Professor
        fields = '__all__'  # ou liste explicitamente os campos

    def validate_usuario(self, value):
        if value is not None and value.tipo != 'professor':
            raise serializers.ValidationError(
                'A conta vinculada precisa ser do tipo professor.'
            )
        return value


class ProfessorBasicoSerializer(serializers.ModelSerializer):
    """Dados básicos para colegas e responsáveis: sem documentos nem contatos pessoais.

    A foto foi liberada pela proprietária do projeto para identificação na escola.
    """

    class Meta:
        model = Professor
        fields = ['id', 'nome', 'disciplinas', 'foto']
        read_only_fields = fields
