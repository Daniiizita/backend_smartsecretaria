from rest_framework import serializers
from ..models import Notificacao

class NotificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacao
        fields = ['id', 'tipo', 'titulo', 'mensagem', 'link', 'lida', 'criada_em']
        # Pela API, o destinatário só pode marcar a notificação como lida.
        read_only_fields = ['tipo', 'titulo', 'mensagem', 'link', 'criada_em']
