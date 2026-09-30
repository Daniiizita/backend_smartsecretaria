from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import date

class Professor(models.Model):
    # Campos obrigatórios
    nome = models.CharField(max_length=100, blank=False, null=False, default='professor')
    cpf = models.CharField(max_length=11, blank=False, null=False, default='99999999999')
    rg = models.CharField(max_length=7, blank=False, null=False, default = '9999999')
    orgao_expedidor = models.CharField(max_length=20, blank=False, null=False, default = 'INSTITUTO FEDERAL')
    data_nascimento = models.DateField(blank=False, null=False, default= date(1999, 1, 1))
    endereco = models.CharField(max_length=200, blank=False, null=False, default='S/N')
    telefone_contato = models.CharField(max_length=20, blank=False, null=False, default='+559999999999')
    email = models.EmailField(blank=False, null=False, default='email@teste.com')
    data_admissao = models.DateField(blank=False, null=False, default=timezone.localdate)
    naturalidade = models.CharField(max_length=100, blank=False, null=False, default='Brasil')

    # Relação com Disciplinas
    disciplinas = models.ManyToManyField('disciplina.Disciplina', blank=True)  # atualizado

    # Campo opcional
    foto = models.ImageField(upload_to='professores/', blank=True, null=True)
    # Conta de login do professor (opcional: pode haver cadastro sem acesso ao sistema).
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='professor',
        limit_choices_to={'tipo': 'professor'},
    )

    def __str__(self):
        return self.nome
