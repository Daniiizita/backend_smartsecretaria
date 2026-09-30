from datetime import date
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from usuarios.models import CustomUser
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


class AlunoResponsaveisTestCase(APITestCase):
    def setUp(self):
        self.client.force_authenticate(
            user=CustomUser.objects.create_user(username="admin_resp", tipo="admin")
        )
        turma = Turma.objects.create(serie=3, professor_responsavel=Professor.objects.create())
        dados = dict(
            data_nascimento=date(2016, 5, 10),
            endereco="Rua Fictícia, 1",
            telefone_contato="0000000000",
            turma=turma,
        )
        self.irmao1 = Aluno.objects.create(nome_completo="Irmão Um", **dados)
        self.irmao2 = Aluno.objects.create(nome_completo="Irmão Dois", **dados)
        self.mae = CustomUser.objects.create_user(username="mae", tipo="responsavel")
        self.pai = CustomUser.objects.create_user(username="pai", tipo="responsavel")

    def vincular(self, aluno, contas):
        return self.client.patch(
            f"/api/aluno/{aluno.pk}/",
            {"responsaveis": [c.pk for c in contas]},
            format="json",
        )

    def test_aluno_com_varios_responsaveis(self):
        response = self.vincular(self.irmao1, [self.mae, self.pai])

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(self.irmao1.responsaveis.all()), {self.mae, self.pai})

    def test_responsavel_com_varios_dependentes(self):
        self.vincular(self.irmao1, [self.mae])
        self.vincular(self.irmao2, [self.mae])

        self.assertEqual(set(self.mae.dependentes.all()), {self.irmao1, self.irmao2})

    def test_rejeita_conta_que_nao_e_responsavel(self):
        for tipo in ("admin", "secretario", "professor", "aluno"):
            with self.subTest(tipo=tipo):
                conta = CustomUser.objects.create_user(username=f"c_{tipo}", tipo=tipo)
                response = self.vincular(self.irmao1, [self.mae, conta])
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("responsaveis", response.data)
        self.assertEqual(self.irmao1.responsaveis.count(), 0)

    def test_criar_aluno_sem_responsaveis_continua_funcionando(self):
        response = self.client.post(
            "/api/aluno/",
            {
                "nome_completo": "Aluno Novo",
                "data_nascimento": "2016-01-01",
                "endereco": "Rua Fictícia, 2",
                "telefone_contato": "0000000000",
                "turma": self.irmao1.turma_id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["responsaveis"], [])
