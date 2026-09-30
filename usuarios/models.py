from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    TIPOS_USUARIO = (
        ('admin', 'Administrador'),
        ('secretario', 'Secretário'),
        ('professor', 'Professor'),
        ('aluno', 'Aluno'),
        ('responsavel', 'Responsável'),
    )
    # Padrão com o menor privilégio: papéis administrativos são sempre explícitos.
    tipo = models.CharField(max_length=20, choices=TIPOS_USUARIO, default='aluno')
    
    # Evita conflito de nomes com o modelo User do Django
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name='customuser_set',
        related_query_name='customuser',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name='customuser_set',
        related_query_name='customuser',
    )
    
    def save(self, *args, **kwargs):
        # Superusuário tem controle total: o perfil exibido é sempre o de administrador
        # (o createsuperuser não pergunta o tipo e usaria o padrão 'aluno').
        if self.is_superuser:
            self.tipo = 'admin'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

