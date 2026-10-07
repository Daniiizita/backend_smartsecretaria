from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from core.escopo import filtrar_por_aluno, registros_de_alunos_visiveis
from core.permissions import IsGestor, IsGestorOrReadOnly
from ..modelos import texto_modelo
from ..models import Documento
from .serializers import DocumentoSerializer, PedidoDeModeloSerializer

class DocumentoViewSet(viewsets.ModelViewSet):
    """
    Gestão escolar: CRUD completo. Responsável: somente leitura dos documentos
    dos próprios dependentes. Demais papéis: nenhum registro.
    Filtros: ?aluno=, ?tipo=, ?ano= (ano de emissão).
    """
    serializer_class = DocumentoSerializer
    permission_classes = [IsGestorOrReadOnly]

    def get_queryset(self):
        queryset = registros_de_alunos_visiveis(Documento.objects.all(), self.request.user)
        queryset = filtrar_por_aluno(queryset, self.request)
        params = self.request.query_params
        if params.get('tipo') in dict(Documento.TIPOS_DOCUMENTO):
            queryset = queryset.filter(tipo=params['tipo'])
        if params.get('ano', '').isdigit():
            queryset = queryset.filter(data_emissao__year=int(params['ano']))
        return queryset.select_related('aluno').order_by('-data_emissao', '-id')

    @action(detail=False, methods=['post'], permission_classes=[IsGestor])
    def modelo(self, request):
        """Texto-modelo preenchido com os dados do aluno (a secretaria revisa antes de salvar)."""
        pedido = PedidoDeModeloSerializer(data=request.data)
        pedido.is_valid(raise_exception=True)
        dados = pedido.validated_data
        return Response({'conteudo': texto_modelo(dados['aluno'], dados['tipo'], dados.get('data_emissao'))})
