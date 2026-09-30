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
