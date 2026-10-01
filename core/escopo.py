"""Quais registros cada papel pode enxergar (recorte por linha).

Os recortes por campo ficam nos serializers de cada app. A gestão escolar
(admin e secretário) enxerga tudo; os demais papéis só o que precisam.
"""
from core.permissions import is_gestor


def professor_do_usuario(user):
    """Cadastro de professor vinculado à conta, ou None."""
    if getattr(user, 'tipo', None) != 'professor':
        return None
    return getattr(user, 'professor', None)


def turmas_visiveis(user):
    from turma.models import Turma

    if is_gestor(user):
        return Turma.objects.all()
    professor = professor_do_usuario(user)
    if professor is not None:
        return Turma.objects.do_professor(professor)
    if getattr(user, 'tipo', None) == 'responsavel':
        return Turma.objects.filter(aluno__responsaveis=user).distinct()
    return Turma.objects.none()


def alunos_visiveis(user):
    from aluno.models import Aluno
    from turma.models import Turma

    if is_gestor(user):
        return Aluno.objects.all()
    professor = professor_do_usuario(user)
    if professor is not None:
        return Aluno.objects.filter(turma__in=Turma.objects.do_professor(professor))
    if getattr(user, 'tipo', None) == 'responsavel':
        return user.dependentes.all()
    return Aluno.objects.none()


def registros_de_alunos_visiveis(queryset, user):
    """Matrículas, documentos etc.: gestão vê tudo; responsável, só os dos dependentes."""
    if is_gestor(user):
        return queryset
    if getattr(user, 'tipo', None) == 'responsavel':
        return queryset.filter(aluno__responsaveis=user).distinct()
    return queryset.none()


def professores_visiveis(user):
    from django.db.models import Q
    from professor.models import Professor

    if is_gestor(user) or professor_do_usuario(user) is not None:
        return Professor.objects.all()
    if getattr(user, 'tipo', None) == 'responsavel':
        turmas = turmas_visiveis(user)
        return Professor.objects.filter(
            Q(turma__in=turmas) | Q(atribuicoes__turma__in=turmas)
        ).distinct()
    return Professor.objects.none()


def filtrar_por_aluno(queryset, request):
    """?aluno=<id> restringe matrículas/documentos a um aluno (dentro do que o usuário já pode ver)."""
    aluno = request.query_params.get('aluno')
    if aluno and aluno.isdigit():
        return queryset.filter(aluno_id=int(aluno))
    return queryset
