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
        for user in (self.secretario, self.professor, self.aluno):
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
