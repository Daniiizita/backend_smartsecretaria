import secrets
from io import StringIO

from django.core.management import CommandError, call_command
from rest_framework.test import APITestCase

from aluno.models import Aluno
from professor.models import Professor
from turma.models import Turma, TurmaDisciplina
from usuarios.models import CustomUser


def cpf_valido(cpf):
    numeros = [int(c) for c in cpf]
    for tamanho in (9, 10):
        soma = sum(n * p for n, p in zip(numeros[:tamanho], range(tamanho + 1, 1, -1)))
        if (soma * 10) % 11 % 10 != numeros[tamanho]:
            return False
    return True


class SeedDemoTestCase(APITestCase):
    def setUp(self):
        self.senha = secrets.token_urlsafe(12)

    def seed(self, **opcoes):
        saida = StringIO()
        call_command("seed_demo", senha=self.senha, stdout=saida, **opcoes)
        return saida.getvalue()

    def test_cria_base_ficticia_com_os_dois_modelos_de_docencia(self):
        self.seed()

        self.assertEqual(Turma.objects.count(), 4)
        self.assertEqual(Aluno.objects.count(), 24)
        unico = Turma.objects.get(serie=5)
        self.assertEqual(list(unico.professores()), [unico.professor_responsavel])
        por_disciplina = Turma.objects.get(serie=8)
        self.assertGreater(por_disciplina.professores().count(), 1)
        self.assertTrue(TurmaDisciplina.objects.exists())

    def test_contas_de_demo_entram_com_a_senha_informada(self):
        self.seed()

        for username in ("admin_demo", "secretaria_demo", "professor_demo", "responsavel_demo"):
            with self.subTest(username=username):
                response = self.client.post(
                    "/api/token/", {"username": username, "password": self.senha}, format="json"
                )
                self.assertEqual(response.status_code, 200)

    def test_senha_nao_aparece_na_saida_quando_informada(self):
        saida = self.seed()

        self.assertNotIn(self.senha, saida)

    def test_cpfs_gerados_nunca_sao_validos(self):
        self.seed()

        for cpf in Professor.objects.values_list("cpf", flat=True):
            with self.subTest(cpf=cpf):
                self.assertEqual(len(cpf), 11)
                self.assertFalse(cpf_valido(cpf))

    def test_nao_sobrescreve_dados_existentes_sem_reset(self):
        self.seed()

        with self.assertRaises(CommandError):
            self.seed()
        self.assertEqual(Aluno.objects.count(), 24)

    def test_reset_recria_a_base(self):
        self.seed()
        extra = CustomUser.objects.create_user(username="conta_real", tipo="secretario")

        self.seed(reset=True, sim=True)

        self.assertEqual(Aluno.objects.count(), 24)
        self.assertEqual(CustomUser.objects.filter(username__endswith="_demo").count(), 4)
        self.assertTrue(CustomUser.objects.filter(pk=extra.pk).exists())

    def test_permissoes_valem_para_as_contas_de_demo(self):
        self.seed()
        professor = CustomUser.objects.get(username="professor_demo")
        responsavel = CustomUser.objects.get(username="responsavel_demo")

        self.client.force_authenticate(user=professor)
        alunos_do_professor = self.client.get("/api/aluno/").data
        self.client.force_authenticate(user=responsavel)
        dependentes = self.client.get("/api/aluno/").data

        # Marcos é regente do 9º ano B e dá Matemática no 6º ano A: 12 alunos.
        self.assertEqual(len(alunos_do_professor), 12)
        self.assertNotIn("cpf", alunos_do_professor[0])
        self.assertEqual(len(dependentes), 2)
