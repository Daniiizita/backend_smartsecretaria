from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase

from aluno.models import Aluno
from documentos.models import Documento
from matricula.models import Matricula
from professor.models import Professor
from turma.models import Turma
from usuarios.models import CustomUser


class ProtecaoExclusaoTestCase(APITestCase):
    """Excluir um cadastro nunca pode apagar em cascata dados de alunos."""

    def setUp(self):
        self.client.force_authenticate(
            user=CustomUser.objects.create_user(username="admin_exclusao", tipo="admin")
        )
        self.professor = Professor.objects.create(nome="Regente")
        self.turma = Turma.objects.create(serie=3, professor_responsavel=self.professor)
        self.aluno = Aluno.objects.create(
            nome_completo="Aluno Fictício",
            data_nascimento=date(2016, 3, 1),
            endereco="Rua Fictícia, 1",
            telefone_contato="0000000000",
            turma=self.turma,
        )

    def assert_conflito(self, url):
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("Não é possível excluir", response.data["detail"])
        return response

    def test_professor_regente_nao_e_excluido(self):
        response = self.assert_conflito(f"/api/professor/{self.professor.pk}/")

        self.assertEqual(response.data["vinculos"], {"turmas": 1})
        self.assertTrue(Professor.objects.filter(pk=self.professor.pk).exists())
        self.assertTrue(Aluno.objects.filter(pk=self.aluno.pk).exists())

    def test_turma_com_alunos_nao_e_excluida(self):
        self.assert_conflito(f"/api/turma/{self.turma.pk}/")

        self.assertTrue(Turma.objects.filter(pk=self.turma.pk).exists())
        self.assertTrue(Aluno.objects.filter(pk=self.aluno.pk).exists())

    def test_aluno_com_matricula_ou_documento_nao_e_excluido(self):
        Matricula.objects.create(
            aluno=self.aluno,
            data_matricula=date(2026, 2, 1),
            ano_letivo=2026,
            turma=self.turma,
            status="ativo",
        )
        Documento.objects.create(
            aluno=self.aluno, tipo="declaracao", data_emissao=date(2026, 2, 2), conteudo="-"
        )

        self.assert_conflito(f"/api/aluno/{self.aluno.pk}/")

        self.assertEqual(Matricula.objects.count(), 1)
        self.assertEqual(Documento.objects.count(), 1)

    def test_cadastros_sem_vinculos_continuam_excluiveis(self):
        professor_livre = Professor.objects.create(nome="Sem turma")

        response = self.client.delete(f"/api/aluno/{self.aluno.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.delete(f"/api/turma/{self.turma.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.delete(f"/api/professor/{professor_livre.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
