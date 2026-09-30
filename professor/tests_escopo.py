from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase

from aluno.models import Aluno
from disciplina.models import Disciplina
from turma.models import Turma, TurmaDisciplina
from usuarios.models import CustomUser
from .models import Professor

CAMPOS_BASICOS = {"id", "nome", "disciplinas", "foto"}


class ProfessorEscopoTestCase(APITestCase):
    """Quem vê quais professores e com quais campos."""

    def setUp(self):
        conta = lambda nome, tipo: CustomUser.objects.create_user(username=nome, tipo=tipo)
        self.conta_a = conta("prof_a", "professor")
        self.conta_b = conta("prof_b", "professor")
        self.regente = Professor.objects.create(nome="Regente A", cpf="11111111111", usuario=self.conta_a)
        self.prof_mat = Professor.objects.create(nome="Matemática B", cpf="22222222222", usuario=self.conta_b)
        self.outro = Professor.objects.create(nome="Outra turma C", cpf="33333333333")

        turma = Turma.objects.create(serie=8, professor_responsavel=self.regente)
        Turma.objects.create(serie=9, professor_responsavel=self.outro)
        TurmaDisciplina.objects.create(
            turma=turma,
            disciplina=Disciplina.objects.create(nome="Matemática"),
            professor=self.prof_mat,
        )

        self.responsavel = conta("mae", "responsavel")
        aluno = Aluno.objects.create(
            nome_completo="Aluno Fictício",
            data_nascimento=date(2013, 1, 1),
            endereco="Rua Fictícia, 1",
            telefone_contato="0000000000",
            turma=turma,
        )
        aluno.responsaveis.add(self.responsavel)

        self.secretario = conta("sec", "secretario")
        self.conta_aluno = conta("aluno", "aluno")
        self.professor_sem_cadastro = conta("prof_sem_cadastro", "professor")

    def listar(self, user):
        self.client.force_authenticate(user=user)
        response = self.client.get("/api/professor/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    def test_gestao_ve_todos_com_todos_os_campos(self):
        dados = self.listar(self.secretario)

        self.assertEqual(len(dados), 3)
        self.assertIn("cpf", dados[0])

    def test_professor_ve_colegas_apenas_com_dados_basicos(self):
        dados = self.listar(self.conta_a)

        self.assertEqual(len(dados), 3)
        for professor in dados:
            self.assertEqual(set(professor), CAMPOS_BASICOS)

    def test_professor_ve_o_proprio_cadastro_completo(self):
        self.client.force_authenticate(user=self.conta_a)

        proprio = self.client.get(f"/api/professor/{self.regente.pk}/").data
        colega = self.client.get(f"/api/professor/{self.prof_mat.pk}/").data

        self.assertEqual(proprio["cpf"], "11111111111")
        self.assertEqual(set(colega), CAMPOS_BASICOS)

    def test_professor_nao_edita_nem_o_proprio_cadastro(self):
        self.client.force_authenticate(user=self.conta_a)

        response = self.client.patch(
            f"/api/professor/{self.regente.pk}/", {"nome": "Alterado"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_responsavel_ve_so_os_professores_do_filho(self):
        dados = self.listar(self.responsavel)

        self.assertEqual({p["id"] for p in dados}, {self.regente.pk, self.prof_mat.pk})
        for professor in dados:
            self.assertEqual(set(professor), CAMPOS_BASICOS)

        self.client.force_authenticate(user=self.responsavel)
        response = self.client.get(f"/api/professor/{self.outro.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_contas_sem_vinculo_nao_veem_professores(self):
        for user in (self.conta_aluno, self.professor_sem_cadastro):
            with self.subTest(user=user.username):
                self.assertEqual(self.listar(user), [])
