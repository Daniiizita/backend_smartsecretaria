import secrets

from django.core.cache import cache
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from usuarios.models import CustomUser


class TokensTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.senha = secrets.token_urlsafe(16)
        CustomUser.objects.create_user(username="pessoa", password=self.senha, tipo="professor")

    def entrar(self, senha=None):
        return self.client.post(
            "/api/token/", {"username": "pessoa", "password": senha or self.senha}, format="json"
        )

    def test_refresh_token_usado_nao_vale_de_novo(self):
        refresh = self.entrar().data["refresh"]

        primeira = self.client.post("/api/token/refresh/", {"refresh": refresh}, format="json")
        segunda = self.client.post("/api/token/refresh/", {"refresh": refresh}, format="json")

        self.assertEqual(primeira.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", primeira.data)  # a rotação entrega um novo refresh
        self.assertEqual(segunda.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_invalida_o_refresh(self):
        refresh = self.entrar().data["refresh"]

        sair = self.client.post("/api/token/blacklist/", {"refresh": refresh}, format="json")
        depois = self.client.post("/api/token/refresh/", {"refresh": refresh}, format="json")

        self.assertEqual(sair.status_code, status.HTTP_200_OK)
        self.assertEqual(depois.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(LOGIN_THROTTLE_RATE="3/min")
    def test_limite_de_tentativas_de_login(self):
        respostas = [self.entrar(senha="errada").status_code for _ in range(3)]
        bloqueada = self.entrar()

        self.assertEqual(respostas, [401, 401, 401])
        self.assertEqual(bloqueada.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @override_settings(LOGIN_THROTTLE_RATE="2/min")
    def test_limite_na_troca_de_senha(self):
        user = CustomUser.objects.get(username="pessoa")
        self.client.force_authenticate(user=user)
        corpo = {"senha_atual": "errada", "nova_senha": secrets.token_urlsafe(16)}

        codigos = [self.client.post("/api/usuarios/me/senha/", corpo, format="json").status_code for _ in range(3)]

        self.assertEqual(codigos, [400, 400, 429])
