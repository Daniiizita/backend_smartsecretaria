import secrets

from rest_framework import status
from rest_framework.test import APITestCase

from .models import CustomUser


def criar_usuario(username, tipo, **extra):
    return CustomUser.objects.create_user(
        username=username,
        password=secrets.token_urlsafe(16),
        tipo=tipo,
        **extra,
    )


class CustomUserSerializerTestCase(APITestCase):
    """Proteções de dados do serializer, exercitadas por um administrador."""

    def setUp(self):
        self.admin = criar_usuario("admin_teste", "admin")
        self.user = criar_usuario("usuario_teste", "professor")
        self.client.force_authenticate(user=self.admin)

    def test_listagem_nao_expoe_senha(self):
        response = self.client.get("/api/usuarios/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for usuario in response.data:
            self.assertNotIn("password", usuario)

    def test_flags_de_privilegio_sao_somente_leitura(self):
        response = self.client.patch(
            f"/api/usuarios/{self.user.pk}/",
            {"is_superuser": True, "is_staff": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_staff)

    def test_senha_criada_pela_api_e_armazenada_com_hash(self):
        nova_senha = secrets.token_urlsafe(16)
        response = self.client.post(
            "/api/usuarios/",
            {"username": "novo_usuario", "password": nova_senha, "tipo": "secretario"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)
        criado = CustomUser.objects.get(username="novo_usuario")
        self.assertNotEqual(criado.password, nova_senha)
        self.assertTrue(criado.check_password(nova_senha))

        self.client.force_authenticate(user=None)
        token = self.client.post(
            "/api/token/",
            {"username": "novo_usuario", "password": nova_senha},
            format="json",
        )
        self.assertEqual(token.status_code, status.HTTP_200_OK)
        self.assertIn("access", token.data)

    def test_troca_de_senha_pela_api_aplica_hash(self):
        nova_senha = secrets.token_urlsafe(16)
        response = self.client.patch(
            f"/api/usuarios/{self.user.pk}/",
            {"password": nova_senha},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(nova_senha))

    def test_senha_fraca_e_rejeitada(self):
        response = self.client.post(
            "/api/usuarios/",
            {"username": "senha_fraca", "password": "123", "tipo": "professor"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertFalse(CustomUser.objects.filter(username="senha_fraca").exists())


class CustomUserPermissionTestCase(APITestCase):
    """Quem pode gerenciar usuários e quem só acessa o próprio perfil."""

    def setUp(self):
        self.superuser = CustomUser.objects.create_superuser(
            username="dona", password=secrets.token_urlsafe(16), tipo="admin"
        )
        self.admin = criar_usuario("diretor", "admin")
        self.secretario = criar_usuario("secretario", "secretario")
        self.professor = criar_usuario("professor", "professor")
        self.aluno = criar_usuario("aluno", "aluno")

    def test_anonimo_nao_acessa(self):
        response = self.client.get("/api/usuarios/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_administradores_listam_usuarios(self):
        for user in (self.superuser, self.admin):
            with self.subTest(user=user.username):
                self.client.force_authenticate(user=user)
                response = self.client.get("/api/usuarios/")
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_demais_papeis_nao_gerenciam_usuarios(self):
        responsavel = criar_usuario("responsavel", "responsavel")
        for user in (self.professor, self.aluno, responsavel):
            with self.subTest(user=user.username):
                self.client.force_authenticate(user=user)
                self.assertEqual(
                    self.client.get("/api/usuarios/").status_code,
                    status.HTTP_403_FORBIDDEN,
                )
                self.assertEqual(
                    self.client.get(f"/api/usuarios/{self.admin.pk}/").status_code,
                    status.HTTP_403_FORBIDDEN,
                )
                self.assertEqual(
                    self.client.post(
                        "/api/usuarios/", {"username": "x", "tipo": "admin"}, format="json"
                    ).status_code,
                    status.HTTP_403_FORBIDDEN,
                )
                self.assertEqual(
                    self.client.patch(
                        f"/api/usuarios/{user.pk}/", {"tipo": "admin"}, format="json"
                    ).status_code,
                    status.HTTP_403_FORBIDDEN,
                )
                user.refresh_from_db()
                self.assertNotEqual(user.tipo, "admin")

    def test_admin_nao_altera_nem_exclui_superusuario(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/usuarios/{self.superuser.pk}/", {"is_active": False}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.delete(f"/api/usuarios/{self.superuser.pk}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.superuser.refresh_from_db()
        self.assertTrue(self.superuser.is_active)

    def test_superusuario_altera_outro_superusuario(self):
        outro = CustomUser.objects.create_superuser(
            username="outro_super", password=secrets.token_urlsafe(16)
        )
        self.client.force_authenticate(user=self.superuser)

        response = self.client.patch(
            f"/api/usuarios/{outro.pk}/", {"first_name": "Teste"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_me_retorna_apenas_o_proprio_usuario(self):
        self.client.force_authenticate(user=self.professor)

        response = self.client.get("/api/usuarios/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.professor.pk)
        self.assertNotIn("password", response.data)

    def test_me_e_somente_leitura(self):
        for user in (self.secretario, self.professor, self.aluno):
            with self.subTest(user=user.username):
                self.client.force_authenticate(user=user)
                for method in ("patch", "put", "post", "delete"):
                    response = getattr(self.client, method)(
                        "/api/usuarios/me/",
                        {"first_name": "Alterado", "tipo": "admin"},
                        format="json",
                    )
                    self.assertEqual(
                        response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
                    )
                user.refresh_from_db()
                self.assertNotEqual(user.first_name, "Alterado")
                self.assertNotEqual(user.tipo, "admin")


class TrocarSenhaTestCase(APITestCase):
    """Todo usuário autenticado pode trocar a própria senha, e somente ela."""

    url = "/api/usuarios/me/senha/"

    def setUp(self):
        self.senha_atual = secrets.token_urlsafe(16)
        self.user = CustomUser.objects.create_user(
            username="professor_senha",
            password=self.senha_atual,
            tipo="professor",
            first_name="Original",
        )

    def test_anonimo_nao_troca_senha(self):
        response = self.client.post(
            self.url,
            {"senha_atual": self.senha_atual, "nova_senha": secrets.token_urlsafe(16)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_todos_os_papeis_trocam_a_propria_senha(self):
        for tipo in ("admin", "secretario", "professor", "responsavel"):
            with self.subTest(tipo=tipo):
                senha = secrets.token_urlsafe(16)
                user = CustomUser.objects.create_user(
                    username=f"troca_{tipo}", password=senha, tipo=tipo
                )
                nova_senha = secrets.token_urlsafe(16)
                self.client.force_authenticate(user=user)

                response = self.client.post(
                    self.url,
                    {"senha_atual": senha, "nova_senha": nova_senha},
                    format="json",
                )

                self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
                user.refresh_from_db()
                self.assertTrue(user.check_password(nova_senha))
                self.assertFalse(user.check_password(senha))

    def test_senha_atual_incorreta_e_rejeitada(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {"senha_atual": "errada", "nova_senha": secrets.token_urlsafe(16)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("senha_atual", response.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.senha_atual))

    def test_nova_senha_fraca_e_rejeitada(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {"senha_atual": self.senha_atual, "nova_senha": "123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("nova_senha", response.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.senha_atual))

    def test_troca_de_senha_nao_altera_outros_dados(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {
                "senha_atual": self.senha_atual,
                "nova_senha": secrets.token_urlsafe(16),
                "tipo": "admin",
                "first_name": "Alterado",
                "is_superuser": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user.refresh_from_db()
        self.assertEqual(self.user.tipo, "professor")
        self.assertEqual(self.user.first_name, "Original")
        self.assertFalse(self.user.is_superuser)

    def test_login_funciona_com_a_nova_senha(self):
        nova_senha = secrets.token_urlsafe(16)
        self.client.force_authenticate(user=self.user)
        self.client.post(
            self.url,
            {"senha_atual": self.senha_atual, "nova_senha": nova_senha},
            format="json",
        )
        self.client.force_authenticate(user=None)

        antiga = self.client.post(
            "/api/token/",
            {"username": "professor_senha", "password": self.senha_atual},
            format="json",
        )
        nova = self.client.post(
            "/api/token/",
            {"username": "professor_senha", "password": nova_senha},
            format="json",
        )

        self.assertEqual(antiga.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(nova.status_code, status.HTTP_200_OK)


class TipoPadraoTestCase(APITestCase):
    def test_usuario_sem_tipo_nao_vira_admin(self):
        user = CustomUser.objects.create_user(
            username="sem_tipo", password=secrets.token_urlsafe(16)
        )
        self.assertEqual(user.tipo, "aluno")

    def test_conta_criada_pela_api_sem_tipo_nao_vira_admin(self):
        self.client.force_authenticate(user=criar_usuario("admin_padrao", "admin"))

        response = self.client.post(
            "/api/usuarios/",
            {"username": "sem_tipo_api", "password": secrets.token_urlsafe(16)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tipo"], "aluno")


class SecretarioContasTestCase(APITestCase):
    """Secretário gerencia contas de professor, aluno e responsável — e só."""

    def setUp(self):
        self.secretario = criar_usuario("secretario", "secretario")
        self.outro_secretario = criar_usuario("outro_secretario", "secretario")
        self.admin = criar_usuario("diretor", "admin")
        self.superuser = CustomUser.objects.create_superuser(
            username="dona", password=secrets.token_urlsafe(16), tipo="professor"
        )
        self.gerenciaveis = [
            criar_usuario("prof", "professor"),
            criar_usuario("aluno", "aluno"),
            criar_usuario("resp", "responsavel"),
        ]
        self.client.force_authenticate(user=self.secretario)

    def test_lista_apenas_contas_gerenciaveis(self):
        response = self.client.get("/api/usuarios/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {u["username"] for u in response.data},
            {"prof", "aluno", "resp"},
        )

    def test_cria_contas_dos_tipos_permitidos(self):
        for tipo in ("professor", "aluno", "responsavel"):
            with self.subTest(tipo=tipo):
                response = self.client.post(
                    "/api/usuarios/",
                    {
                        "username": f"novo_{tipo}",
                        "password": secrets.token_urlsafe(16),
                        "tipo": tipo,
                    },
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_nao_cria_secretario_nem_admin(self):
        for tipo in ("secretario", "admin"):
            with self.subTest(tipo=tipo):
                response = self.client.post(
                    "/api/usuarios/",
                    {"username": f"novo_{tipo}", "tipo": tipo},
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("tipo", response.data)
                self.assertFalse(
                    CustomUser.objects.filter(username=f"novo_{tipo}").exists()
                )

    def test_nao_promove_conta_gerenciavel(self):
        prof = self.gerenciaveis[0]
        for tipo in ("secretario", "admin"):
            with self.subTest(tipo=tipo):
                response = self.client.patch(
                    f"/api/usuarios/{prof.pk}/", {"tipo": tipo}, format="json"
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        prof.refresh_from_db()
        self.assertEqual(prof.tipo, "professor")

    def test_edita_desativa_redefine_senha_e_exclui_contas_gerenciaveis(self):
        prof, aluno, resp = self.gerenciaveis
        nova_senha = secrets.token_urlsafe(16)

        response = self.client.patch(
            f"/api/usuarios/{prof.pk}/",
            {"first_name": "Ana", "is_active": False, "password": nova_senha},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prof.refresh_from_db()
        self.assertEqual(prof.first_name, "Ana")
        self.assertFalse(prof.is_active)
        self.assertTrue(prof.check_password(nova_senha))

        response = self.client.delete(f"/api/usuarios/{resp.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CustomUser.objects.filter(pk=resp.pk).exists())

    def test_nao_acessa_contas_de_secretario_admin_ou_superusuario(self):
        protegidas = (self.secretario, self.outro_secretario, self.admin, self.superuser)
        for user in protegidas:
            with self.subTest(user=user.username):
                url = f"/api/usuarios/{user.pk}/"
                self.assertEqual(
                    self.client.get(url).status_code, status.HTTP_404_NOT_FOUND
                )
                self.assertEqual(
                    self.client.patch(
                        url, {"is_active": False}, format="json"
                    ).status_code,
                    status.HTTP_404_NOT_FOUND,
                )
                self.assertEqual(
                    self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND
                )
                user.refresh_from_db()
                self.assertTrue(user.is_active)

    def test_admin_continua_criando_qualquer_tipo(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/usuarios/",
            {"username": "novo_sec", "password": secrets.token_urlsafe(16), "tipo": "secretario"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
