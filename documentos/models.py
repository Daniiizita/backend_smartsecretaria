from django.db import models
from aluno.models import Aluno  # Certifique-se de substituir 'aluno' pelo nome correto do app

class Documento(models.Model):
    TIPOS_DOCUMENTO = [
        ('historico', 'Histórico Escolar'),
        ('declaracao', 'Declaração de Matrícula'),
        ('boletim', 'Boletim Escolar'),
        ('atestado', 'Atestado de Matrícula'),
        ('certificado', 'Certificado de Conclusão'),
        ('contagem', 'Contagem de Tempo'),
        ('ata', 'Ata de Reunião'),
        ('outros', 'Outros')
        
    ]
    aluno = models.ForeignKey(Aluno, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=20, choices=TIPOS_DOCUMENTO)
    data_emissao = models.DateField()
    conteudo = models.TextField()

    def __str__(self):
        return f"{self.tipo} - {self.aluno.nome_completo}"


