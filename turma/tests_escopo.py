from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase

from aluno.models import Aluno
from disciplina.models import Disciplina
from professor.models import Professor
from usuarios.models import CustomUser
from .models import Turma, TurmaDisciplina


class TurmaEscopoTestCase(APITestCase):
    """Quem vê quais turmas e atribuições."""

    def setUp(self):
        conta = lambda nome, tipo: CustomUser.objects.create_user(username=nome, tipo=tipo)
        self.conta_regente = conta("regente", "professor")
        self.conta_mat = conta("prof_mat", "professor")
        regente = Professor.objects.create(nome="Regente", usuario=self.conta_regente)
        prof_mat = Professor.objects.create(nome="Matemática", usuario=self.conta_mat)
        outro = Professor.objects.create(nome="Outro")

        self.turma_regente = Turma.objects.create(serie=3, professor_responsavel=regente)
        self.turma_mat = Turma.objects.create(serie=8, professor_responsavel=outro)
        self.turma_alheia = Turma.objects.create(serie=9, professor_responsavel=outro)
        self.atribuicao = TurmaDisciplina.objects.create(
            turma=self.turma_mat,
            disciplina=Disciplina.objects.create(nome="Matemática"),
            professor=prof_mat,
        )

        self.responsavel = conta("pai", "responsavel")
        filho = Aluno.objects.create(
            nome_completo="Filho",
            data_nascimento=date(2016, 1, 1),
            endereco="Rua Fictícia, 1",
            telefone_contato="0000000000",
            turma=self.turma_regente,
        )
        filho.responsaveis.add(self.responsavel)
        self.secretario = conta("sec", "secretario")
        self.conta_aluno = conta("aluno", "aluno")

    def ids(self, user, url="/api/turma/"):
        self.client.force_authenticate(user=user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return {item["id"] for item in response.data}

    def test_gestao_ve_todas_as_turmas(self):
        self.assertEqual(len(self.ids(self.secretario)), 3)

    def test_professor_ve_as_turmas_em_que_atua(self):
        self.assertEqual(self.ids(self.conta_regente), {self.turma_regente.pk})
        self.assertEqual(self.ids(self.conta_mat), {self.turma_mat.pk})

    def test_professor_nao_acessa_turma_alheia(self):
        self.client.force_authenticate(user=self.conta_mat)

        response = self.client.get(f"/api/turma/{self.turma_alheia.pk}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_responsavel_ve_so_a_turma_do_filho(self):
        self.assertEqual(self.ids(self.responsavel), {self.turma_regente.pk})

    def test_conta_aluno_nao_ve_turmas(self):
        self.assertEqual(self.ids(self.conta_aluno), set())

    def test_atribuicoes_seguem_o_mesmo_recorte(self):
        url = "/api/turma/atribuicoes/"
        self.assertEqual(self.ids(self.secretario, url), {self.atribuicao.pk})
        self.assertEqual(self.ids(self.conta_mat, url), {self.atribuicao.pk})
        self.assertEqual(self.ids(self.conta_regente, url), set())
        self.assertEqual(self.ids(self.responsavel, url), set())

    def test_opcoes_de_turma_continuam_disponiveis(self):
        self.client.force_authenticate(user=self.conta_mat)

        response = self.client.get("/api/turma/choices/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("serie", response.data)
