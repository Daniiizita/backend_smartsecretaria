from rest_framework import viewsets
from rest_framework.response import Response
from core.escopo import professores_visiveis
from core.permissions import IsGestorOrReadOnly, is_gestor
from .serializers import ProfessorBasicoSerializer, ProfessorSerializer

class ProfessorViewSet(viewsets.ModelViewSet):
    """
    Gestão escolar: CRUD completo. Demais papéis: somente leitura dos
    professores que podem ver, com dados básicos (sem documentos pessoais).
    O próprio professor vê o seu cadastro completo no detalhe.
    """
    permission_classes = [IsGestorOrReadOnly]

    def get_queryset(self):
        return professores_visiveis(self.request.user).order_by('id')

    def get_serializer_class(self):
        if is_gestor(getattr(self.request, 'user', None)):
            return ProfessorSerializer
        return ProfessorBasicoSerializer

    def retrieve(self, request, *args, **kwargs):
        professor = self.get_object()
        if professor.usuario_id is not None and professor.usuario_id == request.user.pk:
            serializer = ProfessorSerializer(professor, context=self.get_serializer_context())
        else:
            serializer = self.get_serializer(professor)
        return Response(serializer.data)
