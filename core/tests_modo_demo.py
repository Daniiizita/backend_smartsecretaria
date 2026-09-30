import secrets

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from usuarios.models import CustomUser


def conta(username, tipo):
    return CustomUser.objects.create_user(username=username, password=secrets.token_urlsafe(16), tipo=tipo)


@override_settings(DEMO_MODE=True)
class ModoDemoTestCase(APITestCase):
    """Com a senha divulgada, as contas *_demo não podem ser tomadas nem trancadas."""

    def setUp(self):
        self.secretaria = conta("secretaria_demo", "secretario")
        self.professor = conta("professor_demo", "professor")
        self.real = conta("professor_real", "professor")

    def test_conta_de_demo_nao_troca_a_propria_senha(self):
        self.client.force_authenticate(user=self.secretaria)

        response = self.client.post(
            "/api/usuarios/me/senha/",
            {"senha_atual": "x", "nova_senha": secrets.token_urlsafe(16)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_gestao_nao_altera_nem_exclui_conta_de_demo(self):
        self.client.force_authenticate(user=self.secretaria)
        url = f"/api/usuarios/{self.professor.pk}/"

        editar = self.client.patch(url, {"password": secrets.token_urlsafe(16)}, format="json")
        desativar = self.client.patch(url, {"is_active": False}, format="json")
        excluir = self.client.delete(url)

        self.assertEqual(
            [editar.status_code, desativar.status_code, excluir.status_code], [403, 403, 403]
        )
        self.professor.refresh_from_db()
        self.assertTrue(self.professor.is_active)

    def test_contas_comuns_continuam_editaveis(self):
        self.client.force_authenticate(user=self.secretaria)

        response = self.client.patch(
            f"/api/usuarios/{self.real.pk}/", {"first_name": "Nome"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sufixo_demo_e_reservado(self):
        self.client.force_authenticate(user=self.secretaria)

        response = self.client.post(
            "/api/usuarios/",
            {"username": "falso_demo", "password": secrets.token_urlsafe(16), "tipo": "professor"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)


class ForaDoModoDemoTestCase(APITestCase):
    @override_settings(DEMO_MODE=False)
    def test_contas_demo_sao_comuns_fora_do_modo_demo(self):
        secretaria = conta("secretaria_demo", "secretario")
        senha = secrets.token_urlsafe(16)
        secretaria.set_password(senha)
        secretaria.save()
        self.client.force_authenticate(user=secretaria)

        response = self.client.post(
            "/api/usuarios/me/senha/",
            {"senha_atual": senha, "nova_senha": secrets.token_urlsafe(16)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class SaudeTestCase(APITestCase):
    def test_saude_e_publica(self):
        response = self.client.get("/api/saude/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok"})
