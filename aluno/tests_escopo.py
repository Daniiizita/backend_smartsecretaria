from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase

from disciplina.models import Disciplina
from professor.models import Professor
from turma.models import Turma, TurmaDisciplina
from usuarios.models import CustomUser
from .models import Aluno

CAMPOS_PEDAGOGICOS = {
    "id", "nome_completo", "foto", "turma", "data_nascimento",
    "nome_responsavel", "telefone_contato",
}
CAMPOS_PROIBIDOS_AO_PROFESSOR = {
    "cpf", "rg", "orgao_expedidor", "endereco", "nome_pai", "nome_mae",
    "email", "responsaveis",
}


def criar_aluno(nome, turma):
    return Aluno.objects.create(
        nome_completo=nome,
        data_nascimento=date(2014, 6, 1),
        cpf="00000000000",
        rg="RG-FICTICIO",
        nome_pai="Pai Fictício",
        nome_mae="Mãe Fictícia",
        endereco="Rua Fictícia, 1",
        telefone_contato="0000000000",
        nome_responsavel="Responsável Fictício",
        turma=turma,
    )


class AlunoEscopoTestCase(APITestCase):
    """Quem vê quais alunos e com quais campos."""

    def setUp(self):
        conta = lambda nome, tipo: CustomUser.objects.create_user(username=nome, tipo=tipo)
        self.conta_regente = conta("regente", "professor")
        self.conta_mat = conta("prof_mat", "professor")
        regente = Professor.objects.create(nome="Regente", usuario=self.conta_regente)
        prof_mat = Professor.objects.create(nome="Matemática", usuario=self.conta_mat)
        outro = Professor.objects.create(nome="Outro")

        turma_regente = Turma.objects.create(serie=3, professor_responsavel=regente)
        turma_mat = Turma.objects.create(serie=8, professor_responsavel=outro)
        turma_alheia = Turma.objects.create(serie=9, professor_responsavel=outro)
        TurmaDisciplina.objects.create(
            turma=turma_mat,
            disciplina=Disciplina.objects.create(nome="Matemática"),
            professor=prof_mat,
        )

        self.aluno_regente = criar_aluno("Aluno do regente", turma_regente)
        self.aluno_mat = criar_aluno("Aluno de matemática", turma_mat)
        self.aluno_alheio = criar_aluno("Aluno de outra turma", turma_alheia)

        self.responsavel = conta("mae", "responsavel")
        self.outro_responsavel = conta("pai", "responsavel")
        self.aluno_regente.responsaveis.add(self.responsavel, self.outro_responsavel)

        self.secretario = conta("sec", "secretario")
        self.conta_aluno = conta("aluno", "aluno")

    def listar(self, user):
        self.client.force_authenticate(user=user)
        response = self.client.get("/api/aluno/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    def test_gestao_ve_todos_com_todos_os_campos(self):
        dados = self.listar(self.secretario)

        self.assertEqual(len(dados), 3)
        self.assertEqual(dados[0]["cpf"], "00000000000")

    def test_professor_ve_so_alunos_das_suas_turmas(self):
        self.assertEqual(
            {a["id"] for a in self.listar(self.conta_regente)}, {self.aluno_regente.pk}
        )
        self.assertEqual(
            {a["id"] for a in self.listar(self.conta_mat)}, {self.aluno_mat.pk}
        )

    def test_professor_ve_apenas_campos_pedagogicos(self):
        for aluno in self.listar(self.conta_regente):
            self.assertEqual(set(aluno), CAMPOS_PEDAGOGICOS)
            self.assertFalse(CAMPOS_PROIBIDOS_AO_PROFESSOR & set(aluno))

    def test_professor_nao_acessa_aluno_de_outra_turma(self):
        self.client.force_authenticate(user=self.conta_mat)

        response = self.client.get(f"/api/aluno/{self.aluno_alheio.pk}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_professor_nao_edita_aluno(self):
        self.client.force_authenticate(user=self.conta_regente)

        response = self.client.patch(
            f"/api/aluno/{self.aluno_regente.pk}/", {"nome_completo": "X"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_responsavel_ve_so_o_proprio_dependente(self):
        dados = self.listar(self.responsavel)

        self.assertEqual([a["id"] for a in dados], [self.aluno_regente.pk])
        self.assertEqual(dados[0]["cpf"], "00000000000")
        self.assertNotIn("responsaveis", dados[0])

    def test_responsavel_nao_edita_nem_acessa_outros_alunos(self):
        self.client.force_authenticate(user=self.responsavel)

        editar = self.client.patch(
            f"/api/aluno/{self.aluno_regente.pk}/", {"endereco": "X"}, format="json"
        )
        alheio = self.client.get(f"/api/aluno/{self.aluno_mat.pk}/")

        self.assertEqual(editar.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(alheio.status_code, status.HTTP_404_NOT_FOUND)

    def test_conta_aluno_nao_ve_alunos(self):
        self.assertEqual(self.listar(self.conta_aluno), [])
