from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from aluno.models import Aluno
from ..models import Documento


class DocumentoSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.CharField(source='aluno.nome_completo', read_only=True)
    tipo_label = serializers.CharField(source='get_tipo_display', read_only=True)
    data_emissao = serializers.DateField(default=timezone.localdate)
    # Cabeçalho da folha impressa (configurável por ESCOLA_NOME / ESCOLA_CIDADE).
    escola_nome = serializers.SerializerMethodField()
    escola_cidade = serializers.SerializerMethodField()

    class Meta:
        model = Documento
        fields = [
            'id',
            'aluno',
            'aluno_nome',
            'tipo',
            'tipo_label',
            'data_emissao',
            'conteudo',
            'escola_nome',
            'escola_cidade',
        ]

    def get_escola_nome(self, _documento) -> str:
        return settings.ESCOLA_NOME

    def get_escola_cidade(self, _documento) -> str:
        return settings.ESCOLA_CIDADE

    def validate_conteudo(self, valor):
        if not valor.strip():
            raise serializers.ValidationError('Escreva o conteúdo do documento.')
        return valor.strip()


class PedidoDeModeloSerializer(serializers.Serializer):
    """Entrada de POST /api/documentos/modelo/: para quem e de que tipo é o texto."""

    aluno = serializers.PrimaryKeyRelatedField(queryset=Aluno.objects.all())
    tipo = serializers.ChoiceField(choices=Documento.TIPOS_DOCUMENTO)
    data_emissao = serializers.DateField(required=False)
