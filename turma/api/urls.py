from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TurmaDisciplinaViewSet, TurmaViewSet

router = DefaultRouter()
# 'atribuicoes' precisa vir antes de '' para não ser lido como id de turma.
router.register(r'atribuicoes', TurmaDisciplinaViewSet, basename='turma-atribuicoes')
router.register(r'', TurmaViewSet, basename='turma')  # '' = raiz da rota

urlpatterns = [
    path('', include(router.urls)),
]
