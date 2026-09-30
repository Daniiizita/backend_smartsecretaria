from datetime import date
from django.core.exceptions import ValidationError
from django.test import TestCase
from professor.models import Professor
from turma.models import Turma
from .models import Aluno

class AlunoTestCase(TestCase):
    def setUp(self):
        professor = Professor.objects.create()
        self.turma = Turma.objects.create(
            serie=1,
            professor_responsavel=professor,
        )
        self.aluno = Aluno.objects.create(
            nome_completo="João da Silva",
            data_nascimento=date(2000, 1, 1),
            endereco="Rua A, 123",
            telefone_contato="999999999",
            turma=self.turma
        )

    def test_aluno_criado_com_sucesso(self):
        self.assertEqual(self.aluno.nome_completo, "João da Silva")
        self.assertEqual(self.aluno.data_nascimento, date(2000, 1, 1))
        self.assertEqual(self.aluno.endereco, "Rua A, 123")
        self.assertEqual(self.aluno.telefone_contato, "999999999")
        self.assertEqual(self.aluno.turma, self.turma)

    def test_aluno_sem_turma(self):
        aluno_sem_turma = Aluno(
            nome_completo="Maria Souza",
            data_nascimento="2001-02-02",
            endereco="Rua B, 456",
            telefone_contato="888888888"
        )
        with self.assertRaises(ValidationError):
            aluno_sem_turma.full_clean()

    def test_aluno_com_turma_inexistente(self):
        aluno_com_turma_inexistente = Aluno(
            nome_completo="Pedro Santos",
            data_nascimento="2002-03-03",
            endereco="Rua C, 789",
            telefone_contato="777777777",
            turma_id=999
        )
        with self.assertRaises(ValidationError):
            aluno_com_turma_inexistente.full_clean()
