from datetime import date

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from aluno.models import Aluno
from professor.models import Professor
from turma.models import Turma
from usuarios.models import CustomUser
from .models import Matricula


class MatriculaApiTestCase(APITestCase):
    url = "/api/matricula/"

    def setUp(self):
        self.client.force_authenticate(user=CustomUser.objects.create_user(username="sec", tipo="secretario"))
        regente = Professor.objects.create(nome="Regente")
        self.turma_2026 = Turma.objects.create(serie=5, turma_letra="A", ano=2026, professor_responsavel=regente)
        self.turma_b_2026 = Turma.objects.create(serie=5, turma_letra="B", ano=2026, professor_responsavel=regente)
        self.turma_2027 = Turma.objects.create(serie=6, turma_letra="A", ano=2027, professor_responsavel=regente)
        self.aluno = Aluno.objects.create(
            nome_completo="Aluno Fictício", data_nascimento=date(2017, 1, 1), endereco="-",
            telefone_contato="0", turma=self.turma_2026,
        )

    def payload(self, **extra):
        return {"aluno": self.aluno.pk, "turma": self.turma_2026.pk, "ano_letivo": 2026, "status": "ativo", **extra}

    def test_cria_com_nomes_legiveis_e_data_de_hoje_por_padrao(self):
        response = self.client.post(self.url, self.payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["aluno_nome"], "Aluno Fictício")
        self.assertEqual(response.data["status_label"], "Ativo")
        self.assertEqual(response.data["data_matricula"], timezone.localdate().isoformat())

    def test_turma_precisa_ser_do_mesmo_ano_letivo(self):
        response = self.client.post(self.url, self.payload(turma=self.turma_2027.pk), format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ano letivo 2027", str(response.data["turma"]))

    def test_uma_matricula_vigente_por_ano(self):
        self.client.post(self.url, self.payload(), format="json")

        pendente = self.client.post(self.url, self.payload(status="pendente"), format="json")
        historico = self.client.post(self.url, self.payload(status="cancelado"), format="json")

        self.assertEqual(pendente.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("já tem uma matrícula", str(pendente.data["aluno"]))
        self.assertEqual(historico.status_code, status.HTTP_201_CREATED)

    def test_editar_a_propria_matricula_nao_acusa_duplicidade(self):
        criada = self.client.post(self.url, self.payload(status="pendente"), format="json").data

        response = self.client.patch(f"{self.url}{criada['id']}/", {"status": "ativo"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_matricula_ativa_atualiza_a_turma_do_aluno(self):
        self.client.post(self.url, self.payload(turma=self.turma_b_2026.pk), format="json")

        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.turma, self.turma_b_2026)

    def test_matricula_pendente_nao_muda_a_turma_do_aluno(self):
        self.client.post(self.url, self.payload(turma=self.turma_b_2026.pk, status="pendente"), format="json")

        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.turma, self.turma_2026)

    def test_filtros_por_status_ano_e_turma(self):
        Matricula.objects.create(aluno=self.aluno, turma=self.turma_2026, ano_letivo=2026, data_matricula=date(2026, 2, 1), status="pendente")
        outro = Aluno.objects.create(
            nome_completo="Outro Aluno", data_nascimento=date(2016, 1, 1), endereco="-",
            telefone_contato="0", turma=self.turma_2027,
        )
        Matricula.objects.create(aluno=outro, turma=self.turma_2027, ano_letivo=2027, data_matricula=date(2027, 2, 1), status="ativo")

        ids = lambda q: [m["aluno_nome"] for m in self.client.get(self.url + q).data]
        self.assertEqual(ids("?status=pendente"), ["Aluno Fictício"])
        self.assertEqual(ids("?ano=2027"), ["Outro Aluno"])
        self.assertEqual(ids(f"?turma={self.turma_2026.pk}"), ["Aluno Fictício"])
        self.assertEqual(len(ids("?status=invalido")), 2)  # status desconhecido não filtra
