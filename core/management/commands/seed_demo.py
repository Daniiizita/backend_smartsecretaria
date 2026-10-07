"""Cria uma base de demonstração com dados 100% fictícios.

Uso:
    python manage.py seed_demo                  # gera uma senha e mostra uma única vez
    python manage.py seed_demo --senha "..."    # ou use a variável DEMO_PASSWORD
    python manage.py seed_demo --reset          # apaga os dados escolares e recria
    python manage.py seed_demo --senha-admin "..."  # ou DEMO_ADMIN_PASSWORD (senha secreta do admin_demo)

Nenhuma senha é gravada no repositório. Os CPFs gerados têm dígito verificador
propositalmente inválido, para nunca coincidirem com o CPF de uma pessoa real.
"""
import os
import random
import secrets
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from aluno.models import Aluno
from calendario.models import Evento
from disciplina.models import Disciplina
from documentos.modelos import texto_modelo
from documentos.models import Documento
from logs.utils import registrar_atividade
from matricula.models import Matricula
from notificacoes.models import Notificacao
from professor.models import Professor
from turma.models import Turma, TurmaDisciplina
from usuarios.models import CustomUser

ANO_LETIVO = 2026
SUFIXO_DEMO = '_demo'

DISCIPLINAS = [
    'Língua Portuguesa', 'Matemática', 'Ciências', 'História',
    'Geografia', 'Arte', 'Educação Física', 'Língua Inglesa',
]

# (nome, disciplinas que leciona)
PROFESSORES = [
    ('Ana Beatriz Moura', []),
    ('Carlos Eduardo Pires', DISCIPLINAS),
    ('Juliana Rocha Lima', ['Língua Portuguesa']),
    ('Marcos Vinícius Teles', ['Matemática']),
    ('Patrícia Nogueira Dias', ['Ciências']),
    ('Rafael Couto Menezes', ['História', 'Geografia']),
    ('Sílvia Andrade Prado', ['Arte']),
    ('Thiago Barreto Luz', ['Educação Física', 'Língua Inglesa']),
]

PROFESSOR_POR_DISCIPLINA_EF2 = {
    'Língua Portuguesa': 'Juliana Rocha Lima',
    'Matemática': 'Marcos Vinícius Teles',
    'Ciências': 'Patrícia Nogueira Dias',
    'História': 'Rafael Couto Menezes',
    'Geografia': 'Rafael Couto Menezes',
    'Arte': 'Sílvia Andrade Prado',
    'Educação Física': 'Thiago Barreto Luz',
    'Língua Inglesa': 'Thiago Barreto Luz',
}

# (série, letra, período, regente, ano de nascimento dos alunos, modelo de docência)
TURMAS = [
    (1, 'A', 'Manhã', 'Ana Beatriz Moura', 2022, 'regente'),
    (5, 'A', 'Tarde', 'Carlos Eduardo Pires', 2018, 'unico'),
    (8, 'A', 'Manhã', 'Juliana Rocha Lima', 2015, 'por_disciplina'),
    (11, 'B', 'Tarde', 'Marcos Vinícius Teles', 2012, 'por_disciplina'),
]

PRENOMES = [
    'Alice', 'Bernardo', 'Cecília', 'Davi', 'Elisa', 'Felipe', 'Gabriela', 'Heitor',
    'Isadora', 'João Pedro', 'Laura', 'Miguel', 'Nina', 'Otávio', 'Pietra', 'Rafaela',
    'Samuel', 'Valentina', 'Vicente', 'Yasmin', 'Lorenzo', 'Helena', 'Theo', 'Manuela',
]
SOBRENOMES = [
    'Albuquerque', 'Bastos', 'Campos', 'Duarte', 'Esteves', 'Fontes', 'Guimarães',
    'Horta', 'Leal', 'Macedo', 'Paiva', 'Quintela', 'Rezende', 'Siqueira', 'Toledo',
]

# Notificações fictícias para cada conta de demo: (tipo, título, mensagem, link interno).
NOTIFICACOES_DEMO = {
    'admin': [
        ('sistema', 'Bem-vindo(a) à demonstração', 'Explore a gestão de usuários e permissões.', '/usuarios'),
    ],
    'secretaria': [
        ('matricula', 'Matrículas pendentes', 'Há matrículas pendentes de conferência (dados fictícios).', '/matriculas?status=pendente'),
        ('sistema', 'Troque sua senha', 'Por segurança, defina uma senha pessoal no seu perfil.', '/perfil'),
    ],
    'professor': [
        ('evento', 'Reunião de pais e mestres', 'Confira a lista dos seus alunos antes da reunião.', '/alunos'),
        ('sistema', 'Troque sua senha', 'Por segurança, defina uma senha pessoal no seu perfil.', '/perfil'),
    ],
    'responsavel': [
        ('documento', 'Declaração disponível', 'A declaração de matrícula dos seus filhos já está disponível.', '/dashboard'),
        ('evento', 'Reunião de pais e mestres', 'Participe da reunião na próxima semana (evento fictício).', None),
    ],
}

CONTAS_DEMO = {
    'admin': 'admin',
    'secretaria': 'secretario',
    'professor': 'professor',
    'responsavel': 'responsavel',
}


def cpf_ficticio(rng):
    """11 dígitos com dígito verificador errado: nunca é um CPF válido (nem real)."""
    base = [rng.randint(0, 9) for _ in range(9)]
    d1 = (sum(n * p for n, p in zip(base, range(10, 1, -1))) * 10) % 11 % 10
    d2 = (sum(n * p for n, p in zip(base + [d1], range(11, 1, -1))) * 10) % 11 % 10
    return ''.join(map(str, base + [d1, (d2 + 1) % 10]))


class Command(BaseCommand):
    help = 'Cria uma base de demonstração com dados fictícios e contas de demo.'

    def add_arguments(self, parser):
        parser.add_argument('--senha', help='Senha das contas públicas de demo (ou DEMO_PASSWORD).')
        parser.add_argument(
            '--senha-admin',
            help='Senha secreta do admin_demo (ou DEMO_ADMIN_PASSWORD). Sem ela, o admin_demo fica sem login.',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Apaga TODOS os dados escolares e as contas *_demo antes de recriar.',
        )
        parser.add_argument('--sim', action='store_true', help='Não pede confirmação no --reset.')

    def handle(self, *args, **options):
        tem_dados = Aluno.objects.exists() or Professor.objects.exists() or Turma.objects.exists()
        if tem_dados and not options['reset']:
            raise CommandError(
                'Já existem dados escolares neste banco. Use --reset para apagá-los e recriar a demo.'
            )
        if options['reset'] and not options['sim']:
            resposta = input('Isto apaga TODOS os dados escolares e as contas *_demo. Digite "apagar": ')
            if resposta.strip() != 'apagar':
                raise CommandError('Operação cancelada.')

        senha = options['senha'] or os.environ.get('DEMO_PASSWORD')
        senha_gerada = not senha
        if senha_gerada:
            senha = secrets.token_urlsafe(12)

        with transaction.atomic():
            if options['reset']:
                self._apagar_dados()
            senha_admin = options['senha_admin'] or os.environ.get('DEMO_ADMIN_PASSWORD')
            contas = self._criar(senha, senha_admin)

        self.stdout.write(self.style.SUCCESS('Base de demonstração criada (dados fictícios).'))
        self.stdout.write('Contas de demonstração: ' + ', '.join(c.username for c in contas.values()))
        if senha_gerada:
            self.stdout.write(self.style.WARNING(
                f'Senha gerada (mostrada só agora, não é salva em lugar nenhum): {senha}'
            ))
        if not contas['admin'].has_usable_password():
            self.stdout.write('admin_demo criado sem login: informe --senha-admin ou DEMO_ADMIN_PASSWORD para habilitá-lo.')

    def _apagar_dados(self):
        demo = CustomUser.objects.filter(username__endswith=SUFIXO_DEMO)
        Notificacao.objects.filter(usuario__in=demo).delete()
        for modelo in (Documento, Matricula, TurmaDisciplina, Aluno, Turma, Professor, Disciplina, Evento):
            modelo.objects.all().delete()
        demo.delete()

    def _criar(self, senha, senha_admin=None):
        rng = random.Random(ANO_LETIVO)

        contas = {}
        for chave, tipo in CONTAS_DEMO.items():
            user = CustomUser(
                username=f'{chave}{SUFIXO_DEMO}',
                first_name=f'{chave.capitalize()} (demo)',
                email=f'{chave}{SUFIXO_DEMO}@example.com',
                tipo=tipo,
            )
            # O admin tem senha própria (secreta): a das demais contas pode ser pública.
            if chave != 'admin':
                user.set_password(senha)
            elif senha_admin:
                user.set_password(senha_admin)
            else:
                user.set_unusable_password()
            user.save()
            contas[chave] = user

        disciplinas = {nome: Disciplina.objects.create(nome=nome) for nome in DISCIPLINAS}

        professores = {}
        for i, (nome, lecionadas) in enumerate(PROFESSORES, start=1):
            professor = Professor.objects.create(
                nome=nome,
                cpf=cpf_ficticio(rng),
                rg=f'{i:07d}',
                orgao_expedidor='SSP-FICTICIO',
                data_nascimento=date(1975 + i * 2, (i % 12) + 1, 10),
                endereco=f'Rua Fictícia dos Professores, {100 + i}',
                telefone_contato=f'+5500900000{i:03d}',
                email=f'professor{i}@example.com',
                data_admissao=date(2015 + i % 8, 2, 1),
                naturalidade='Cidade Fictícia',
            )
            professor.disciplinas.set([disciplinas[d] for d in lecionadas])
            professores[nome] = professor
        professores['Marcos Vinícius Teles'].usuario = contas['professor']
        professores['Marcos Vinícius Teles'].save(update_fields=['usuario'])

        alunos_por_turma = []
        nomes_usados = set()
        for serie, letra, periodo, regente, ano_nasc, docencia in TURMAS:
            turma = Turma.objects.create(
                serie=serie,
                turma_letra=letra,
                periodo=periodo,
                ano=ANO_LETIVO,
                professor_responsavel=professores[regente],
            )
            if docencia == 'unico':
                for disciplina in disciplinas.values():
                    TurmaDisciplina.objects.create(
                        turma=turma, disciplina=disciplina, professor=professores[regente]
                    )
            elif docencia == 'por_disciplina':
                for nome_disc, nome_prof in PROFESSOR_POR_DISCIPLINA_EF2.items():
                    TurmaDisciplina.objects.create(
                        turma=turma, disciplina=disciplinas[nome_disc], professor=professores[nome_prof]
                    )

            alunos = []
            for n in range(6):
                while True:
                    nome = f'{rng.choice(PRENOMES)} {rng.choice(SOBRENOMES)} {rng.choice(SOBRENOMES)}'
                    if nome not in nomes_usados:
                        nomes_usados.add(nome)
                        break
                sobrenome = nome.split()[-1]
                aluno = Aluno.objects.create(
                    nome_completo=nome,
                    data_nascimento=date(ano_nasc, rng.randint(1, 12), rng.randint(1, 28)),
                    nome_mae=f'Mãe Fictícia {sobrenome}',
                    nome_pai=f'Pai Fictício {sobrenome}',
                    nome_responsavel=f'Mãe Fictícia {sobrenome}',
                    endereco=f'Rua Fictícia, {rng.randint(1, 999)}',
                    telefone_contato=f'+5500911{rng.randint(0, 999999):06d}',
                    email=None,
                    turma=turma,
                )
                Matricula.objects.create(
                    aluno=aluno,
                    turma=turma,
                    ano_letivo=ANO_LETIVO,
                    data_matricula=date(ANO_LETIVO, 1, 20 + n),
                    status='pendente' if n == 5 else 'ativo',
                )
                alunos.append(aluno)
            alunos_por_turma.append(alunos)

        # Responsável de demo com dois dependentes em turmas diferentes.
        for aluno in (alunos_por_turma[1][0], alunos_por_turma[2][0]):
            aluno.responsaveis.add(contas['responsavel'])
            emissao = date(ANO_LETIVO, 2, 10)
            Documento.objects.create(
                aluno=aluno,
                tipo='declaracao',
                data_emissao=emissao,
                conteudo=texto_modelo(aluno, 'declaracao', emissao),
            )

        hoje = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        for dias, titulo, tipo in [
            (7, 'Reunião de pais e mestres', 'reuniao'),
            (15, 'Feira de Ciências', 'evento_escolar'),
            (30, 'Conselho de classe', 'reuniao'),
            (45, 'Mostra cultural', 'evento_escolar'),
        ]:
            inicio = hoje + timedelta(days=dias)
            Evento.objects.create(
                titulo=titulo,
                descricao='Evento fictício de demonstração.',
                data_inicio=inicio,
                data_fim=inicio + timedelta(hours=3),
                tipo=tipo,
            )

        for chave, avisos in NOTIFICACOES_DEMO.items():
            for tipo, titulo, mensagem, link in avisos:
                Notificacao.objects.create(
                    usuario=contas[chave], tipo=tipo, titulo=titulo, mensagem=mensagem, link=link
                )
        registrar_atividade(contas['admin'], 'Base de demonstração criada', 'Dados fictícios gerados por seed_demo.')
        return contas
