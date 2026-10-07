"""Textos-modelo dos documentos emitidos pela secretaria.

São modelos genéricos de demonstração: a redação oficial de uma escola real
deve seguir as normas da sua Secretaria de Educação. A secretaria revisa o
texto antes de salvar.
"""
from django.conf import settings
from django.utils import timezone

MESES = [
    'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
    'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
]


def data_por_extenso(data):
    return f'{data.day} de {MESES[data.month - 1]} de {data.year}'


def matricula_vigente(aluno):
    from matricula.models import Matricula

    return (
        Matricula.objects.filter(aluno=aluno, status__in=Matricula.STATUS_VIGENTES)
        .select_related('turma')
        .order_by('-ano_letivo')
        .first()
    )


def texto_modelo(aluno, tipo, data_emissao=None):
    data_emissao = data_emissao or timezone.localdate()
    nascimento = aluno.data_nascimento.strftime('%d/%m/%Y')
    matricula = matricula_vigente(aluno)
    turma = matricula.turma.nome if matricula else aluno.turma.nome
    ano = matricula.ano_letivo if matricula else aluno.turma.ano
    escola = settings.ESCOLA_NOME
    situacao = (
        'regularmente matriculado(a)'
        if matricula and matricula.status == 'ativo'
        else 'com matrícula em processamento' if matricula else 'sem matrícula vigente'
    )

    if tipo == 'declaracao':
        corpo = (
            f'Declaramos, para os devidos fins, que {aluno.nome_completo}, nascido(a) em {nascimento}, '
            f'encontra-se {situacao} nesta unidade escolar, {escola}, no ano letivo de {ano}, '
            f'na turma {turma}.'
        )
    elif tipo == 'atestado':
        corpo = (
            f'Atestamos, a pedido da parte interessada, que {aluno.nome_completo}, nascido(a) em {nascimento}, '
            f'encontra-se {situacao} nesta unidade escolar, {escola}, no ano letivo de {ano}, '
            f'na turma {turma}.'
        )
    else:
        corpo = (
            f'Documento referente ao(à) aluno(a) {aluno.nome_completo}, nascido(a) em {nascimento}, '
            f'turma {turma}, ano letivo de {ano}.\n\n[Complete aqui o conteúdo deste documento.]'
        )

    return f'{corpo}\n\n{settings.ESCOLA_CIDADE}, {data_por_extenso(data_emissao)}.'
