from rest_framework import serializers
from ..models import Turma, TurmaDisciplina

class TurmaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Turma
        fields = '__all__'  # ou liste explicitamente os campos


class TurmaDisciplinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TurmaDisciplina
        fields = ['id', 'turma', 'disciplina', 'professor']
