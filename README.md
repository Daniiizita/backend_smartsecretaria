# SmartSecretaria API

API de gestão escolar desenvolvida com Django e Django REST Framework. Este é um projeto de portfólio em desenvolvimento; não use dados reais de alunos nem o servidor de desenvolvimento em produção.

## Escopo atual

- API REST para alunos, professores, turmas, matrículas, calendário, documentos, usuários, relatórios e notificações.
- Autenticação JWT e autorização por perfil aplicada no backend (não apenas no frontend).
- Esquema OpenAPI em `/api/schema/` e Swagger UI em `/api/docs/`.
- Banco SQLite para desenvolvimento local.
- Comando `seed_demo` para gerar uma base de demonstração com dados fictícios.

O frontend ainda não cobre todos os módulos da API. O sistema não está pronto para operação municipal ou para tratar dados pessoais reais.

## Executar localmente no Windows

Requer Python 3.12 ou compatível com as dependências fixadas.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
New-Item -ItemType Directory -Force data | Out-Null
```

Crie um arquivo `.env` local com uma `SECRET_KEY` gerada na hora. O comando não mostra a chave e não sobrescreve um `.env` existente; o arquivo já está no `.gitignore`:

```powershell
python -c "import secrets,pathlib; p=pathlib.Path('.env'); print('ja existe, nada feito') if p.exists() else (p.write_text('SECRET_KEY='+secrets.token_urlsafe(48)+'\n'), print('.env criado'))"
```

Depois, prepare o banco e inicie o servidor:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Nunca versione `.env`, bancos SQLite ou senhas. Antes de qualquer implantação, use segredos gerenciados pelo provedor de hospedagem.

## Base de demonstração

Para explorar o sistema com dados fictícios (escola, turmas, professores e alunos inventados):

```powershell
python manage.py seed_demo
```

O comando cria as contas `admin_demo`, `secretaria_demo`, `professor_demo` e `responsavel_demo`. A senha é gerada e exibida uma única vez no terminal; também é possível informá-la com `--senha` ou pela variável `DEMO_PASSWORD`. Os CPFs gerados têm dígito verificador propositalmente inválido, para nunca coincidirem com o de uma pessoa real.

Se já houver dados escolares no banco, o comando se recusa a continuar. `python manage.py seed_demo --reset` apaga todos os dados escolares e as contas `*_demo` (pedindo confirmação) e recria a base.

## Perfis de acesso

A API aplica as permissões por perfil em cada endpoint:

| Perfil | O que pode fazer |
| --- | --- |
| Administrador | Controle total, inclusive contas de secretaria e de outros administradores. Somente superusuários alteram contas de superusuário. |
| Secretaria | Administra a escola (alunos, professores, turmas, atribuições, matrículas, documentos, calendário) e contas de professores, responsáveis e alunos. |
| Professor | Leitura: turmas em que atua, dados pedagógicos dos seus alunos e dados básicos dos colegas. |
| Responsável | Leitura: dados, matrículas e documentos dos próprios dependentes e dados básicos dos professores deles. |

Todos podem consultar o próprio perfil em `/api/usuarios/me/` e trocar a própria senha em `/api/usuarios/me/senha/`. Logs de auditoria e tentativas de login são somente leitura, restritos a administradores.

Essas regras refletem uma demonstração de portfólio. Um uso real, com dados de crianças e adolescentes, exige validação com a escola ou secretaria de educação e revisão profissional de proteção de dados (LGPD).

## Testes

```powershell
python manage.py test
```

A integração contínua (GitHub Actions) roda `check`, verificação de migrações pendentes, os testes e `pip-audit` a cada push ou pull request para `develop` e `main`.

## Deploy da demonstração

O passo a passo para publicar a demo gratuita (API no Render e frontend na Vercel) está em [DEPLOY.md](DEPLOY.md). Todas as configurações vêm de variáveis de ambiente, documentadas em [.env.example](.env.example).

## Licença e autoria

Copyright (c) 2025 Danielle. Os termos de uso estão em [LICENSE](LICENSE). Uso comercial exige autorização prévia por escrito do titular dos direitos.
