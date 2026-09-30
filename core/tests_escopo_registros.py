from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase

from aluno.models import Aluno
from documentos.models import Documento
from matricula.models import Matricula
from professor.models import Professor
from turma.models import Turma
from usuarios.models import CustomUser


class MatriculasEDocumentosEscopoTestCase(APITestCase):
    """Responsável lê matrículas e documentos só dos próprios dependentes."""

    def setUp(self):
        conta = lambda nome, tipo: CustomUser.objects.create_user(username=nome, tipo=tipo)
        prof_conta = conta("prof", "professor")
        turma = Turma.objects.create(
            serie=3,
            professor_responsavel=Professor.objects.create(nome="Regente", usuario=prof_conta),
        )
        dados = dict(
            data_nascimento=date(2016, 1, 1),
            endereco="Rua Fictícia, 1",
            telefone_contato="0000000000",
            turma=turma,
        )
        filho = Aluno.objects.create(nome_completo="Filho", **dados)
        outro = Aluno.objects.create(nome_completo="Outro aluno", **dados)

        self.responsavel = conta("mae", "responsavel")
        filho.responsaveis.add(self.responsavel)
        self.professor = prof_conta
        self.secretario = conta("sec", "secretario")

        matricula = dict(data_matricula=date(2026, 2, 1), ano_letivo=2026, turma=turma, status="ativo")
        self.matricula_filho = Matricula.objects.create(aluno=filho, **matricula)
        Matricula.objects.create(aluno=outro, **matricula)
        documento = dict(tipo="declaracao", data_emissao=date(2026, 2, 2), conteudo="-")
        self.documento_filho = Documento.objects.create(aluno=filho, **documento)
        Documento.objects.create(aluno=outro, **documento)

    def ids(self, user, url):
        self.client.force_authenticate(user=user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return {item["id"] for item in response.data}

    def test_responsavel_ve_so_os_registros_do_filho(self):
        self.assertEqual(self.ids(self.responsavel, "/api/matricula/"), {self.matricula_filho.pk})
        self.assertEqual(self.ids(self.responsavel, "/api/documentos/"), {self.documento_filho.pk})

    def test_responsavel_nao_altera_registros(self):
        self.client.force_authenticate(user=self.responsavel)

        response = self.client.patch(
            f"/api/matricula/{self.matricula_filho.pk}/", {"status": "cancelado"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.matricula_filho.refresh_from_db()
        self.assertEqual(self.matricula_filho.status, "ativo")

    def test_professor_nao_ve_matriculas_nem_documentos(self):
        self.assertEqual(self.ids(self.professor, "/api/matricula/"), set())
        self.assertEqual(self.ids(self.professor, "/api/documentos/"), set())

    def test_gestao_ve_todos(self):
        self.assertEqual(len(self.ids(self.secretario, "/api/matricula/")), 2)
        self.assertEqual(len(self.ids(self.secretario, "/api/documentos/")), 2)
