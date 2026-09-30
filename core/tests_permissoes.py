from rest_framework import status
from rest_framework.test import APITestCase

from notificacoes.models import Notificacao
from usuarios.models import CustomUser

PAPEIS = ("admin", "secretario", "professor", "responsavel", "aluno")
GESTAO = {"admin", "secretario"}
PERMITIDO = "permitido"  # passou pela autorização (200/201/400/405, nunca 401/403)


class MatrizDePermissoesTestCase(APITestCase):
    """Quem pode ler e quem pode escrever em cada módulo da escola."""

    def setUp(self):
        self.usuarios = {
            tipo: CustomUser.objects.create_user(username=f"u_{tipo}", tipo=tipo)
            for tipo in PAPEIS
        }

    def status_de(self, tipo, metodo, url):
        self.client.force_authenticate(user=self.usuarios[tipo])
        response = getattr(self.client, metodo)(url, {}, format="json")
        if response.status_code in (401, 403):
            return response.status_code
        return PERMITIDO

    def verificar(self, url, metodo, papeis_permitidos):
        for tipo in PAPEIS:
            with self.subTest(url=url, metodo=metodo, papel=tipo):
                esperado = PERMITIDO if tipo in papeis_permitidos else 403
                self.assertEqual(self.status_de(tipo, metodo, url), esperado)

    def test_anonimo_nao_acessa_nenhum_modulo(self):
        urls = [
            "/api/disciplina/", "/api/calendario/", "/api/professor/", "/api/aluno/",
            "/api/turma/", "/api/turma/atribuicoes/", "/api/matricula/",
            "/api/documentos/", "/api/dashboard/", "/api/logs/",
            "/api/permissoes/perfil-acesso/", "/api/permissoes/tentativa-login/",
            "/api/notificacoes/",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 401)

    def test_dados_de_referencia_leitura_para_todos_escrita_para_gestao(self):
        for url in ("/api/disciplina/", "/api/calendario/"):
            self.verificar(url, "get", set(PAPEIS))
            self.verificar(url, "post", GESTAO)

    def test_cadastros_escolares_so_a_gestao_altera(self):
        for url in ("/api/professor/", "/api/aluno/", "/api/turma/", "/api/turma/atribuicoes/"):
            self.verificar(url, "post", GESTAO)

    def test_matriculas_documentos_e_dashboard_so_a_gestao(self):
        for url in ("/api/matricula/", "/api/documentos/"):
            self.verificar(url, "get", GESTAO)
            self.verificar(url, "post", GESTAO)
        self.verificar("/api/dashboard/", "get", GESTAO)

    def test_areas_de_sistema_so_o_admin(self):
        for url in (
            "/api/logs/",
            "/api/permissoes/perfil-acesso/",
            "/api/permissoes/tentativa-login/",
        ):
            self.verificar(url, "get", {"admin"})

    def test_auditoria_e_somente_leitura_ate_para_o_admin(self):
        self.client.force_authenticate(user=self.usuarios["admin"])
        for url in ("/api/logs/", "/api/permissoes/tentativa-login/"):
            with self.subTest(url=url):
                response = self.client.post(url, {"acao": "forjada"}, format="json")
                self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class NotificacoesTestCase(APITestCase):
    def setUp(self):
        self.dono = CustomUser.objects.create_user(username="dono", tipo="professor")
        self.outro = CustomUser.objects.create_user(username="outro", tipo="professor")
        self.minha = Notificacao.objects.create(
            usuario=self.dono, tipo="sistema", titulo="Minha", mensagem="-"
        )
        self.alheia = Notificacao.objects.create(
            usuario=self.outro, tipo="sistema", titulo="Alheia", mensagem="-"
        )
        self.client.force_authenticate(user=self.dono)

    def test_lista_apenas_as_proprias(self):
        response = self.client.get("/api/notificacoes/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([n["id"] for n in response.data], [self.minha.pk])
        self.assertNotIn("usuario", response.data[0])

    def test_nao_acessa_notificacao_alheia(self):
        response = self.client.patch(
            f"/api/notificacoes/{self.alheia.pk}/", {"lida": True}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_marca_como_lida_sem_alterar_conteudo(self):
        response = self.client.patch(
            f"/api/notificacoes/{self.minha.pk}/",
            {"lida": True, "titulo": "Alterado", "usuario": self.outro.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.minha.refresh_from_db()
        self.assertTrue(self.minha.lida)
        self.assertEqual(self.minha.titulo, "Minha")
        self.assertEqual(self.minha.usuario, self.dono)

    def test_nao_cria_nem_exclui_pela_api(self):
        criar = self.client.post(
            "/api/notificacoes/", {"tipo": "sistema", "titulo": "x", "mensagem": "x"}, format="json"
        )
        excluir = self.client.delete(f"/api/notificacoes/{self.minha.pk}/")

        self.assertEqual(criar.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(excluir.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
