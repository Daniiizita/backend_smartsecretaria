from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from usuarios.models import CustomUser
from .models import Professor
from disciplina.models import Disciplina

class ProfessorTestCase(TestCase):
    def setUp(self):
        # Crie algumas disciplinas para usar nos testes
        self.disciplina1 = Disciplina.objects.create(nome='Matemática')
        self.disciplina2 = Disciplina.objects.create(nome='História')

    def test_criacao_professor(self):
        professor = Professor.objects.create(
            nome='João Silva',
            cpf='12345678901',
            rg='12345',
            endereco='Rua Exemplo, 123',
            telefone_contato='987654321',
            email='joao@example.com',
            data_admissao='2022-01-01',
            foto=None  # Pode deixar como None ou adicionar um caminho para uma imagem se desejar
        )

        # Adicione disciplinas ao professor
        professor.disciplinas.add(self.disciplina1, self.disciplina2)

        # Teste se o método __str__ está correto
        self.assertEqual(str(professor), 'João Silva')

        # Teste se as disciplinas foram adicionadas corretamente
        self.assertEqual(professor.disciplinas.count(), 2)

    def test_str_disciplina(self):
        disciplina = Disciplina.objects.create(nome='Biologia')
        self.assertEqual(str(disciplina), 'Biologia')



class ProfessorVinculoUsuarioTestCase(APITestCase):
    def setUp(self):
        self.client.force_authenticate(
            user=CustomUser.objects.create_user(username="admin_vinculo", tipo="admin")
        )
        self.conta_professor = CustomUser.objects.create_user(
            username="conta_prof", tipo="professor"
        )
        self.professor = Professor.objects.create(nome="Ana Souza")

    def vincular(self, professor, usuario):
        return self.client.patch(
            f"/api/professor/{professor.pk}/", {"usuario": usuario.pk}, format="json"
        )

    def test_vincula_conta_do_tipo_professor(self):
        response = self.vincular(self.professor, self.conta_professor)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.conta_professor.professor, self.professor)

    def test_rejeita_conta_de_outro_tipo(self):
        for tipo in ("admin", "secretario", "aluno", "responsavel"):
            with self.subTest(tipo=tipo):
                conta = CustomUser.objects.create_user(username=f"conta_{tipo}", tipo=tipo)
                response = self.vincular(self.professor, conta)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("usuario", response.data)

    def test_conta_vinculada_a_apenas_um_professor(self):
        self.vincular(self.professor, self.conta_professor)
        outro = Professor.objects.create(nome="Bruno Lima")

        response = self.vincular(outro, self.conta_professor)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_excluir_conta_mantem_o_cadastro(self):
        self.vincular(self.professor, self.conta_professor)

        self.conta_professor.delete()

        self.professor.refresh_from_db()
        self.assertIsNone(self.professor.usuario)
