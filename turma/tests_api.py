from datetime import date

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from aluno.models import Aluno
from disciplina.models import Disciplina
from professor.models import Professor
from usuarios.models import CustomUser
from .models import Turma, TurmaDisciplina


class TurmaApiTestCase(APITestCase):
    def setUp(self):
        self.secretario = CustomUser.objects.create_user(username="sec", tipo="secretario")
        self.client.force_authenticate(user=self.secretario)
        self.regente = Professor.objects.create(nome="Regente Fictícia")
        self.outro = Professor.objects.create(nome="Outro Professor")
        self.turma = Turma.objects.create(serie=5, turma_letra="A", ano=2026, professor_responsavel=self.regente)
        Aluno.objects.create(
            nome_completo="Aluno Um", data_nascimento=date(2018, 1, 1), endereco="-",
            telefone_contato="0", turma=self.turma,
        )
        self.disciplinas = [Disciplina.objects.create(nome=n) for n in ("Matemática", "Arte", "Ciências")]

    def test_lista_traz_dados_de_exibicao(self):
        dados = self.client.get("/api/turma/").data[0]

        self.assertEqual(dados["professor_responsavel_nome"], "Regente Fictícia")
        self.assertEqual(dados["total_alunos"], 1)
        self.assertIn("3º Ano", dados["serie_label"])
        self.assertEqual(dados["nivel_label"], "Ensino Fundamental I")

    def test_ano_padrao_e_o_ano_atual(self):
        response = self.client.post(
            "/api/turma/", {"serie": 8, "turma_letra": "B", "professor_responsavel": self.regente.pk}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["ano"], timezone.localdate().year)
        self.assertTrue(response.data["nome"].startswith("6º Ano B"))

    def test_nao_permite_turma_repetida_no_mesmo_ano(self):
        repetida = {"serie": 5, "turma_letra": "A", "ano": 2026, "professor_responsavel": self.outro.pk}

        response = self.client.post("/api/turma/", repetida, format="json")
        outro_ano = self.client.post("/api/turma/", {**repetida, "ano": 2027}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Já existe uma turma A", str(response.data["turma_letra"]))
        self.assertEqual(outro_ano.status_code, status.HTTP_201_CREATED)

    def test_editar_a_propria_turma_nao_acusa_repeticao(self):
        response = self.client.patch(f"/api/turma/{self.turma.pk}/", {"horario_aulas": "13h-17h"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_professor_unico_atribui_todas_as_disciplinas_ao_regente(self):
        TurmaDisciplina.objects.create(turma=self.turma, disciplina=self.disciplinas[0], professor=self.outro)

        response = self.client.post(f"/api/turma/{self.turma.pk}/professor-unico/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(
            set(self.turma.atribuicoes.values_list("professor_id", flat=True)), {self.regente.pk}
        )

    def test_professor_unico_so_para_gestao(self):
        conta = CustomUser.objects.create_user(username="prof", tipo="professor")
        self.regente.usuario = conta
        self.regente.save()
        self.client.force_authenticate(user=conta)

        response = self.client.post(f"/api/turma/{self.turma.pk}/professor-unico/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(TurmaDisciplina.objects.exists())

    def test_atribuicoes_filtradas_por_turma_e_com_nomes(self):
        outra = Turma.objects.create(serie=6, turma_letra="A", ano=2026, professor_responsavel=self.outro)
        TurmaDisciplina.objects.create(turma=self.turma, disciplina=self.disciplinas[0], professor=self.outro)
        TurmaDisciplina.objects.create(turma=outra, disciplina=self.disciplinas[0], professor=self.outro)

        dados = self.client.get(f"/api/turma/atribuicoes/?turma={self.turma.pk}").data

        self.assertEqual(len(dados), 1)
        self.assertEqual(dados[0]["disciplina_nome"], "Matemática")
        self.assertEqual(dados[0]["professor_nome"], "Outro Professor")

    def test_disciplina_repetida_na_turma_tem_mensagem_clara(self):
        payload = {"turma": self.turma.pk, "disciplina": self.disciplinas[0].pk, "professor": self.outro.pk}
        self.client.post("/api/turma/atribuicoes/", payload, format="json")

        response = self.client.post("/api/turma/atribuicoes/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("já tem professor", str(response.data["disciplina"]))

    def test_alunos_filtrados_por_turma(self):
        outra = Turma.objects.create(serie=6, turma_letra="A", ano=2026, professor_responsavel=self.outro)
        Aluno.objects.create(
            nome_completo="Aluno Dois", data_nascimento=date(2015, 1, 1), endereco="-",
            telefone_contato="0", turma=outra,
        )

        dados = self.client.get(f"/api/aluno/?turma={self.turma.pk}").data

        self.assertEqual([a["nome_completo"] for a in dados], ["Aluno Um"])

    def test_excluir_turma_com_alunos_e_bloqueado(self):
        response = self.client.delete(f"/api/turma/{self.turma.pk}/")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("alunos", response.data["detail"])
