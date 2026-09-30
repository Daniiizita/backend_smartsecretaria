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
