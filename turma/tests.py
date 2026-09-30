from django.db import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from disciplina.models import Disciplina
from professor.models import Professor
from usuarios.models import CustomUser
from .models import Turma, TurmaDisciplina


class TurmaDisciplinaModelTestCase(TestCase):
    def setUp(self):
        self.regente = Professor.objects.create(nome="Regente")
        self.prof_mat = Professor.objects.create(nome="Prof. Matemática")
        self.prof_hist = Professor.objects.create(nome="Prof. História")
        self.sem_turma = Professor.objects.create(nome="Sem turma")
        self.matematica = Disciplina.objects.create(nome="Matemática")
        self.historia = Disciplina.objects.create(nome="História")

    def test_professor_unico_leciona_todas_as_disciplinas(self):
        turma = Turma.objects.create(serie=3, professor_responsavel=self.regente)
        for disciplina in (self.matematica, self.historia):
            TurmaDisciplina.objects.create(
                turma=turma, disciplina=disciplina, professor=self.regente
            )

        self.assertEqual(list(turma.professores()), [self.regente])
        self.assertEqual(list(Turma.objects.do_professor(self.regente)), [turma])

    def test_um_professor_por_disciplina(self):
        turma = Turma.objects.create(serie=8, professor_responsavel=self.regente)
        TurmaDisciplina.objects.create(
            turma=turma, disciplina=self.matematica, professor=self.prof_mat
        )
        TurmaDisciplina.objects.create(
            turma=turma, disciplina=self.historia, professor=self.prof_hist
        )

        self.assertEqual(
            set(turma.professores()), {self.regente, self.prof_mat, self.prof_hist}
        )
        for professor in (self.regente, self.prof_mat, self.prof_hist):
            with self.subTest(professor=professor.nome):
                self.assertEqual(list(Turma.objects.do_professor(professor)), [turma])
        self.assertFalse(Turma.objects.do_professor(self.sem_turma).exists())

    def test_turma_sem_atribuicoes_tem_apenas_o_regente(self):
        turma = Turma.objects.create(serie=3, professor_responsavel=self.regente)

        self.assertEqual(list(turma.professores()), [self.regente])

    def test_professor_em_varias_disciplinas_nao_duplica_turma(self):
        turma = Turma.objects.create(serie=8, professor_responsavel=self.regente)
        for disciplina in (self.matematica, self.historia):
            TurmaDisciplina.objects.create(
                turma=turma, disciplina=disciplina, professor=self.prof_mat
            )

        self.assertEqual(list(Turma.objects.do_professor(self.prof_mat)), [turma])

    def test_disciplina_tem_um_unico_professor_na_turma(self):
        turma = Turma.objects.create(serie=8, professor_responsavel=self.regente)
        TurmaDisciplina.objects.create(
            turma=turma, disciplina=self.matematica, professor=self.prof_mat
        )

        with self.assertRaises(IntegrityError):
            TurmaDisciplina.objects.create(
                turma=turma, disciplina=self.matematica, professor=self.prof_hist
            )

    def test_excluir_professor_remove_so_as_atribuicoes(self):
        turma = Turma.objects.create(serie=8, professor_responsavel=self.regente)
        TurmaDisciplina.objects.create(
            turma=turma, disciplina=self.matematica, professor=self.prof_mat
        )

        self.prof_mat.delete()

        self.assertTrue(Turma.objects.filter(pk=turma.pk).exists())
        self.assertFalse(TurmaDisciplina.objects.exists())


class TurmaDisciplinaAPITestCase(APITestCase):
    url = "/api/turma/atribuicoes/"

    def setUp(self):
        regente = Professor.objects.create(nome="Regente")
        self.professor = Professor.objects.create(nome="Prof. Matemática")
        self.turma = Turma.objects.create(serie=8, professor_responsavel=regente)
        self.disciplina = Disciplina.objects.create(nome="Matemática")
        self.payload = {
            "turma": self.turma.pk,
            "disciplina": self.disciplina.pk,
            "professor": self.professor.pk,
        }

    def autenticar(self, tipo):
        user = CustomUser.objects.create_user(username=f"u_{tipo}", tipo=tipo)
        self.client.force_authenticate(user=user)

    def test_gestao_atribui_professor(self):
        for tipo in ("admin", "secretario"):
            with self.subTest(tipo=tipo):
                TurmaDisciplina.objects.all().delete()
                self.autenticar(tipo)

                response = self.client.post(self.url, self.payload, format="json")

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(TurmaDisciplina.objects.count(), 1)

    def test_atribuicao_duplicada_retorna_400(self):
        self.autenticar("admin")
        self.client.post(self.url, self.payload, format="json")

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_demais_papeis_apenas_consultam(self):
        TurmaDisciplina.objects.create(
            turma=self.turma, disciplina=self.disciplina, professor=self.professor
        )
        for tipo in ("professor", "responsavel", "aluno"):
            with self.subTest(tipo=tipo):
                self.autenticar(tipo)
                self.assertEqual(
                    self.client.get(self.url).status_code, status.HTTP_200_OK
                )
                self.assertEqual(
                    self.client.post(self.url, self.payload, format="json").status_code,
                    status.HTTP_403_FORBIDDEN,
                )

    def test_anonimo_nao_acessa(self):
        self.assertEqual(
            self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_rota_de_turma_por_id_continua_funcionando(self):
        self.autenticar("admin")

        response = self.client.get(f"/api/turma/{self.turma.pk}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.turma.pk)
