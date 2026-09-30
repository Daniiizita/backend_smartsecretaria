import secrets

from rest_framework import status
from rest_framework.test import APITestCase

from .models import CustomUser


class LoginPorUsuarioOuEmailTestCase(APITestCase):
    url = "/api/token/"

    def setUp(self):
        self.senha = secrets.token_urlsafe(16)
        self.user = CustomUser.objects.create_user(
            username="login_teste",
            email="pessoa.teste@example.com",
            password=self.senha,
            tipo="professor",
        )

    def entrar(self, identificador, senha=None):
        return self.client.post(
            self.url,
            {"username": identificador, "password": senha or self.senha},
            format="json",
        )

    def test_entra_pelo_login(self):
        self.assertEqual(self.entrar("login_teste").status_code, status.HTTP_200_OK)

    def test_entra_pelo_email_sem_diferenciar_maiusculas(self):
        for email in ("pessoa.teste@example.com", "Pessoa.Teste@Example.com", " pessoa.teste@example.com "):
            with self.subTest(email=email):
                response = self.entrar(email)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertIn("access", response.data)

    def test_senha_errada_falha_pelo_login_e_pelo_email(self):
        for identificador in ("login_teste", "pessoa.teste@example.com"):
            with self.subTest(identificador=identificador):
                response = self.entrar(identificador, senha="senha-errada")
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_conta_inativa_nao_entra(self):
        self.user.is_active = False
        self.user.save()

        self.assertEqual(
            self.entrar("pessoa.teste@example.com").status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_email_repetido_no_banco_nao_permite_login_por_email(self):
        CustomUser.objects.create_user(
            username="outra_conta", email="PESSOA.TESTE@example.com", password=self.senha
        )

        self.assertEqual(
            self.entrar("pessoa.teste@example.com").status_code, status.HTTP_401_UNAUTHORIZED
        )
        self.assertEqual(self.entrar("login_teste").status_code, status.HTTP_200_OK)

    def test_login_tem_prioridade_sobre_email(self):
        # Uma conta cujo login é igual ao email de outra: vale a conta do login.
        CustomUser.objects.create_user(
            username="pessoa.teste@example.com", password="outra-senha-qualquer-123"
        )

        self.assertEqual(
            self.entrar("pessoa.teste@example.com").status_code, status.HTTP_401_UNAUTHORIZED
        )
        self.assertEqual(
            self.entrar("pessoa.teste@example.com", senha="outra-senha-qualquer-123").status_code,
            status.HTTP_200_OK,
        )


class EmailUnicoTestCase(APITestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username="adm", email="adm@example.com", tipo="admin"
        )
        self.client.force_authenticate(user=self.admin)

    def criar(self, username, email):
        return self.client.post(
            "/api/usuarios/",
            {"username": username, "email": email, "password": secrets.token_urlsafe(16), "tipo": "professor"},
            format="json",
        )

    def test_nao_cria_conta_com_email_repetido(self):
        self.assertEqual(self.criar("um", "igual@example.com").status_code, status.HTTP_201_CREATED)

        response = self.criar("dois", "IGUAL@example.com")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_secretario_nao_repete_email_de_conta_que_nao_enxerga(self):
        secretario = CustomUser.objects.create_user(username="sec", tipo="secretario")
        self.client.force_authenticate(user=secretario)

        response = self.criar("novo", "adm@example.com")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_editar_mantendo_o_proprio_email_funciona(self):
        conta = CustomUser.objects.create_user(username="c", email="c@example.com", tipo="professor")

        response = self.client.patch(
            f"/api/usuarios/{conta.pk}/", {"email": "c@example.com", "first_name": "C"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_contas_sem_email_continuam_permitidas(self):
        self.assertEqual(self.criar("sem1", "").status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.criar("sem2", "").status_code, status.HTTP_201_CREATED)


class MeuPerfilVinculosTestCase(APITestCase):
    def test_me_informa_cadastro_de_professor_e_dependentes(self):
        from datetime import date

        from aluno.models import Aluno
        from professor.models import Professor
        from turma.models import Turma

        conta_prof = CustomUser.objects.create_user(username="p", tipo="professor")
        professor = Professor.objects.create(nome="P", usuario=conta_prof)
        turma = Turma.objects.create(serie=3, professor_responsavel=professor)
        aluno = Aluno.objects.create(
            nome_completo="A", data_nascimento=date(2016, 1, 1), endereco="-",
            telefone_contato="0", turma=turma,
        )
        responsavel = CustomUser.objects.create_user(username="r", tipo="responsavel")
        aluno.responsaveis.add(responsavel)

        self.client.force_authenticate(user=conta_prof)
        dados_prof = self.client.get("/api/usuarios/me/").data
        self.client.force_authenticate(user=responsavel)
        dados_resp = self.client.get("/api/usuarios/me/").data

        self.assertEqual(dados_prof["professor"], professor.pk)
        self.assertEqual(dados_prof["dependentes"], [])
        self.assertIsNone(dados_resp["professor"])
        self.assertEqual(dados_resp["dependentes"], [aluno.pk])
        self.assertNotIn("password", dados_resp)


class SuperusuarioTipoTestCase(APITestCase):
    def test_superusuario_e_sempre_do_tipo_admin(self):
        user = CustomUser.objects.create_superuser(username="dona_do_sistema", password=secrets.token_urlsafe(16))

        self.assertEqual(user.tipo, "admin")
        user.tipo = "professor"
        user.save()
        user.refresh_from_db()
        self.assertEqual(user.tipo, "admin")
