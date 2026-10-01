from django.db import models
from django.utils import timezone
from professor.models import Professor


def ano_letivo_atual():
    return timezone.localdate().year

# Constantes para escolha de nível e série
NIVEL_CHOICES = [
    ('EI', 'Educação Infantil'),
    ('EFI', 'Ensino Fundamental I'),
    ('EFII', 'Ensino Fundamental II'),
    ('EM', 'Ensino Médio'),
]

SERIE_CHOICES = [
    (1, '1º Período - Educação Infantil'),
    (2, '2º Período - Educação Infantil'),
    (3, '1º Ano - Ensino Fundamental I'),
    (4, '2º Ano - Ensino Fundamental I'),
    (5, '3º Ano - Ensino Fundamental I'),
    (6, '4º Ano - Ensino Fundamental I'),
    (7, '5º Ano - Ensino Fundamental I'),
    (8, '6º Ano - Ensino Fundamental II'),
    (9, '7º Ano - Ensino Fundamental II'),
    (10, '8º Ano - Ensino Fundamental II'),
    (11, '9º Ano - Ensino Fundamental II'),
    (12, '1º Ano - Ensino Médio'),
    (13, '2º Ano - Ensino Médio'),
    (14, '3º Ano - Ensino Médio'),
]

TURMA_LETRA_CHOICES = [
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'C'),
    ('D', 'D'),
    ('E', 'E'),
]

PERIODO_CHOICES = [
    ('Manhã', 'Manhã'),
    ('Tarde', 'Tarde'),
    ('Noite', 'Noite'),
    ('Integral', 'Integral'),
]


class TurmaQuerySet(models.QuerySet):
    def do_professor(self, professor):
        """Turmas em que o professor é regente ou leciona alguma disciplina."""
        return self.filter(
            models.Q(professor_responsavel=professor)
            | models.Q(atribuicoes__professor=professor)
        ).distinct()


class Turma(models.Model):
    serie = models.IntegerField(choices=SERIE_CHOICES)
    turma_letra = models.CharField(max_length=2, choices=TURMA_LETRA_CHOICES, default="A")
    # Regente da turma. Em turmas com professor único, é ele quem leciona todas as disciplinas.
    professor_responsavel = models.ForeignKey(Professor, on_delete=models.PROTECT)
    horario_aulas = models.CharField(max_length=100, blank=True, null=True)
    ano = models.IntegerField(default=ano_letivo_atual)
    periodo = models.CharField(max_length=20, choices=PERIODO_CHOICES, default="Manhã")
    nome = models.CharField(max_length=100, blank=True)
    nivel_ensino_sigla = models.CharField(max_length=10, choices=NIVEL_CHOICES, blank=True)

    def save(self, *args, **kwargs):
        """
        Sempre que salvar, monta o nome padronizado e define o nível
        """
        # Obter o texto da série a partir das escolhas
        serie_texto = dict(SERIE_CHOICES).get(self.serie, f"{self.serie}º Ano")
        
        # Dividir o texto para separar o ano escolar do nível de ensino
        partes = serie_texto.split(' - ')
        
        if len(partes) > 1:
            ano_escolar = partes[0]  # Ex: "1º Ano"
            nivel_ensino_texto = partes[1]  # Ex: "Ensino Fundamental I"
            
            # Montar o nome da turma com o novo formato
            self.nome = f"{ano_escolar} {self.turma_letra} - {nivel_ensino_texto} - {self.periodo} - {self.ano}"
        else:
            # Caso não tenha o separador " - ", usar o formato antigo
            self.nome = f"{serie_texto} {self.turma_letra} - {self.periodo} - {self.ano}"
        
        # Definir a sigla do nível com base na série
        if 1 <= self.serie <= 2:
            self.nivel_ensino_sigla = 'EI'
        elif 3 <= self.serie <= 7:
            self.nivel_ensino_sigla = 'EFI'
        elif 8 <= self.serie <= 11:
            self.nivel_ensino_sigla = 'EFII'
        elif 12 <= self.serie <= 14:
            self.nivel_ensino_sigla = 'EM'
        else:
            self.nivel_ensino_sigla = 'ND'
            
        super().save(*args, **kwargs)

    objects = TurmaQuerySet.as_manager()

    class Meta:
        constraints = [
            # A mesma série não pode ter duas turmas com a mesma letra no mesmo ano letivo.
            models.UniqueConstraint(fields=['ano', 'serie', 'turma_letra'], name='turma_unica_no_ano'),
        ]

    def professores(self):
        """Regente e professores das disciplinas da turma."""
        return Professor.objects.filter(
            models.Q(pk=self.professor_responsavel_id)
            | models.Q(atribuicoes__turma=self)
        ).distinct()

    def __str__(self):
        return self.nome


class TurmaDisciplina(models.Model):
    """Quem leciona cada disciplina na turma (uma disciplina, um professor por turma)."""

    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='atribuicoes')
    disciplina = models.ForeignKey(
        'disciplina.Disciplina', on_delete=models.CASCADE, related_name='atribuicoes'
    )
    professor = models.ForeignKey(
        Professor, on_delete=models.CASCADE, related_name='atribuicoes'
    )

    class Meta:
        verbose_name = 'Disciplina da turma'
        verbose_name_plural = 'Disciplinas da turma'
        constraints = [
            models.UniqueConstraint(
                fields=['turma', 'disciplina'], name='uma_atribuicao_por_disciplina_na_turma'
            ),
        ]

    def __str__(self):
        return f"{self.turma} - {self.disciplina}: {self.professor}"

