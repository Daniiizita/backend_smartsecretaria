# SmartSecretaria API

API de gestão escolar desenvolvida com Django e Django REST Framework. Este é um projeto de portfólio em desenvolvimento; não use dados reais de alunos nem o servidor de desenvolvimento em produção.

## Escopo atual

- API REST para alunos, professores, turmas, matriculas, calendario, documentos, usuarios, relatorios e notificacoes.
- Autenticacao JWT.
- Esquema OpenAPI em `/api/schema/` e Swagger UI em `/api/docs/`.
- Banco SQLite para desenvolvimento local.

O frontend ainda não cobre todos os módulos da API. O sistema não está pronto para operação municipal ou para tratar dados pessoais reais.

## Executar localmente no Windows

Requer Python 3.12 ou compativel com as dependencias fixadas.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
New-Item -ItemType Directory -Force data | Out-Null
$env:SECRET_KEY = py -c "import secrets; print(secrets.token_urlsafe(48))"
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Mantenha `SECRET_KEY` fora do Git. O valor acima existe apenas no terminal atual; defina um segredo gerenciado e configuração apropriada antes de qualquer implantação.

## Testes

```powershell
python manage.py test
```

## Licenca e autoria

Copyright (c) 2025 Danielle. Os termos de uso estão em [LICENSE](LICENSE). Uso comercial exige autorização prévia por escrito do titular dos direitos.
