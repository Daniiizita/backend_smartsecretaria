from datetime import date

from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from aluno.models import Aluno
from matricula.models import Matricula
from professor.models import Professor
from turma.models import Turma
from usuarios.models import CustomUser
from .models import Documento


@override_settings(ESCOLA_NOME='Escola Teste', ESCOLA_CIDADE='Cidade Teste')
class DocumentoApiTestCase(APITestCase):
    url = '/api/documentos/'

    def setUp(self):
        self.client.force_authenticate(user=CustomUser.objects.create_user(username='sec', tipo='secretario'))
        self.turma = Turma.objects.create(serie=5, turma_letra='A', ano=2026, professor_responsavel=Professor.objects.create(nome='Regente'))
        self.aluno = Aluno.objects.create(
            nome_completo='Aluna Fictícia', data_nascimento=date(2017, 3, 9), endereco='-',
            telefone_contato='0', turma=self.turma,
        )
        Matricula.objects.create(aluno=self.aluno, turma=self.turma, ano_letivo=2026, data_matricula=date(2026, 2, 1), status='ativo')

    def modelo(self, tipo, **extra):
        return self.client.post(f'{self.url}modelo/', {'aluno': self.aluno.pk, 'tipo': tipo, **extra}, format='json')

    def test_modelo_de_declaracao_com_dados_do_aluno(self):
        response = self.modelo('declaracao', data_emissao='2026-10-07')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        texto = response.data['conteudo']
        for trecho in ('Declaramos', 'Aluna Fictícia', '09/03/2017', 'regularmente matriculado(a)',
                       'Escola Teste', 'ano letivo de 2026', self.turma.nome, 'Cidade Teste, 7 de outubro de 2026.'):
            with self.subTest(trecho=trecho):
                self.assertIn(trecho, texto)

    def test_modelo_reflete_matricula_pendente(self):
        Matricula.objects.update(status='pendente')

        self.assertIn('matrícula em processamento', self.modelo('atestado').data['conteudo'])

    def test_modelo_generico_pede_complemento(self):
        texto = self.modelo('boletim').data['conteudo']

        self.assertIn('Complete aqui', texto)

    def test_modelo_so_para_a_gestao(self):
        responsavel = CustomUser.objects.create_user(username='mae', tipo='responsavel')
        self.aluno.responsaveis.add(responsavel)
        self.client.force_authenticate(user=responsavel)

        self.assertEqual(self.modelo('declaracao').status_code, status.HTTP_403_FORBIDDEN)

    def test_cria_documento_com_data_de_hoje_e_dados_da_escola(self):
        response = self.client.post(self.url, {'aluno': self.aluno.pk, 'tipo': 'declaracao', 'conteudo': ' Texto '}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data_emissao'], timezone.localdate().isoformat())
        self.assertEqual(response.data['tipo_label'], 'Declaração de Matrícula')
        self.assertEqual(response.data['aluno_nome'], 'Aluna Fictícia')
        self.assertEqual(response.data['escola_nome'], 'Escola Teste')
        self.assertEqual(response.data['conteudo'], 'Texto')

    def test_conteudo_vazio_e_recusado(self):
        response = self.client.post(self.url, {'aluno': self.aluno.pk, 'tipo': 'outros', 'conteudo': '   '}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('conteudo', response.data)

    def test_filtros_por_tipo_e_ano(self):
        Documento.objects.create(aluno=self.aluno, tipo='declaracao', data_emissao=date(2026, 3, 1), conteudo='a')
        Documento.objects.create(aluno=self.aluno, tipo='boletim', data_emissao=date(2025, 12, 1), conteudo='b')

        tipos = lambda q: [d['tipo'] for d in self.client.get(self.url + q).data]
        self.assertEqual(tipos('?tipo=boletim'), ['boletim'])
        self.assertEqual(tipos('?ano=2026'), ['declaracao'])
