from rest_framework import viewsets
from core.escopo import alunos_visiveis
from core.permissions import IsGestorOrReadOnly, is_gestor
from .serializers import AlunoPedagogicoSerializer, AlunoResponsavelSerializer, AlunoSerializer

class AlunoViewSet(viewsets.ModelViewSet):
    """
    Gestão escolar: CRUD completo. Professor: alunos das suas turmas, só com
    os dados pedagógicos. Responsável: os próprios dependentes. Somente leitura
    para quem não é da gestão.
    """
    permission_classes = [IsGestorOrReadOnly]

    def get_queryset(self):
        queryset = alunos_visiveis(self.request.user).order_by('nome_completo', 'id')
        turma = self.request.query_params.get('turma')  # ?turma=<id>: alunos de uma turma
        if turma and turma.isdigit():
            queryset = queryset.filter(turma_id=int(turma))
        return queryset

    def get_serializer_class(self):
        user = getattr(self.request, 'user', None)
        if is_gestor(user):
            return AlunoSerializer
        if getattr(user, 'tipo', None) == 'responsavel':
            return AlunoResponsavelSerializer
        return AlunoPedagogicoSerializer
