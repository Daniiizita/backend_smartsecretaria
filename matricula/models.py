from django.db import models
from aluno.models import Aluno
from turma.models import Turma
from professor.models import Professor

class Matricula(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('pendente', 'Pendente'),
        ('cancelado', 'Cancelado'),
        ('transferido', 'Transferido')
    ]

    # Campos da Matrícula
    aluno = models.ForeignKey(Aluno, on_delete=models.PROTECT)
    data_matricula = models.DateField()
    ano_letivo = models.IntegerField()
    turma = models.ForeignKey('turma.Turma', on_delete=models.PROTECT)  # Referência à classe Turma no app turma
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    # Matrícula vigente: ainda vale no ano letivo (ativa ou aguardando conferência).
    STATUS_VIGENTES = ('ativo', 'pendente')

    class Meta:
        constraints = [
            # No máximo uma matrícula vigente por aluno em cada ano letivo;
            # canceladas e transferidas ficam como histórico.
            models.UniqueConstraint(
                fields=['aluno', 'ano_letivo'],
                condition=models.Q(status__in=['ativo', 'pendente']),
                name='uma_matricula_vigente_por_ano',
            ),
        ]

    def __str__(self):
        return f"{self.aluno.nome_completo} - {self.turma.nome} - Status: {self.status}"

