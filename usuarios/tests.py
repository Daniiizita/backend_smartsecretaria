import secrets

from rest_framework import status
from rest_framework.test import APITestCase

from .models import CustomUser


class CustomUserAPITestCase(APITestCase):
    def setUp(self):
        self.password = secrets.token_urlsafe(16)
        self.user = CustomUser.objects.create_user(
            username="usuario_teste",
            password=self.password,
            tipo="professor",
        )
        self.client.force_authenticate(user=self.user)

    def test_listagem_nao_expoe_senha(self):
        response = self.client.get("/api/usuarios/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for usuario in response.data:
            self.assertNotIn("password", usuario)

    def test_usuario_nao_se_promove_a_superusuario(self):
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
