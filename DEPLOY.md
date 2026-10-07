# Deploy da demonstração (gratuito)

Guia para publicar o SmartSecretaria como **demonstração de portfólio**: API no **Render** (plano gratuito) e frontend na **Vercel** (plano Hobby).

> Somente dados fictícios. A hospedagem gratuita não é adequada para dados reais nem para uso por uma escola ou secretaria de educação.

## Como a demo funciona

- A API roda no Render com um banco SQLite **recriado a cada início** (`seed_demo --reset`). Alterações de visitantes somem quando o serviço reinicia.
- No plano gratuito, o serviço "dorme" após cerca de 15 minutos sem acesso. A primeira visita seguinte pode levar até 1 minuto; a tela de login já tenta acordá-lo e avisa o visitante.
- A tela de login mostra botões **Entrar como Secretaria / Professor / Responsável**. A senha dessas contas é pública por natureza, por isso `DEMO_MODE` impede trocar a senha, editar, desativar ou excluir as contas `*_demo`.
- O `admin_demo` tem senha própria e **secreta** (`DEMO_ADMIN_PASSWORD`). Sem essa variável, ele fica sem login.
- Fotos enviadas não persistem: o disco do plano gratuito é temporário.

## Antes de começar

Gere duas senhas diferentes e guarde num gerenciador de senhas:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(12))"   # DEMO_PASSWORD (pública)
python -c "import secrets; print(secrets.token_urlsafe(24))"   # DEMO_ADMIN_PASSWORD (secreta)
```

## 1. API no Render

1. Entre em <https://render.com> com sua conta do GitHub.
2. **New → Blueprint** e escolha o repositório `backend_smartsecretaria`, branch `main`. O Render lê o arquivo [render.yaml](render.yaml).
3. Preencha as variáveis pedidas:
   - `DEMO_PASSWORD`: a senha pública gerada acima.
   - `DEMO_ADMIN_PASSWORD`: a senha secreta.
   - `CORS_ALLOWED_ORIGINS`: deixe provisoriamente `http://localhost:5173`; você volta aqui no passo 3.
4. Confirme. O primeiro deploy leva alguns minutos.
5. Anote o endereço do serviço, por exemplo `https://smartsecretaria-api.onrender.com`, e teste `https://SEU-SERVICO.onrender.com/api/saude/`: deve responder `{"status":"ok"}`.

Opcionalmente, defina `ESCOLA_NOME` e `ESCOLA_CIDADE` (cabeçalho e local dos documentos emitidos); sem elas, valem nomes fictícios de demonstração.

`SECRET_KEY` é gerada pelo próprio Render; `DEBUG`, `SECURE_HTTPS`, `DEMO_MODE` e `SQLITE_PATH` já vêm do `render.yaml`. A lista completa de variáveis está em [.env.example](.env.example).

## 2. Frontend na Vercel

1. Em <https://vercel.com>, **Add New → Project** e importe o repositório `frontend_smartsecretaria`.
2. O framework **Vite** é detectado automaticamente (build `npm run build`, saída `dist`).
3. Em **Environment Variables**, cadastre:

   | Variável | Valor |
   | --- | --- |
   | `VITE_API_BASE_URL` | `https://SEU-SERVICO.onrender.com/api` |
   | `VITE_DEMO_MODE` | `true` |
   | `VITE_DEMO_PASSWORD` | a mesma `DEMO_PASSWORD` do Render |
   | `VITE_DEV_MODE` | `false` |

4. Em **Settings → Git**, confira que a branch de produção é `main`.
5. Faça o deploy e anote o endereço, por exemplo `https://smartsecretaria.vercel.app`.

## 3. Liberar o frontend na API (CORS)

No Render, em **Environment**, troque `CORS_ALLOWED_ORIGINS` pelo endereço da Vercel, **sem barra no final** (ex.: `https://smartsecretaria.vercel.app`) e salve. O serviço reinicia sozinho.

## 4. Conferência

- [ ] `/api/saude/` responde `{"status":"ok"}`.
- [ ] A tela de login mostra os três botões de demonstração.
- [ ] "Entrar como Professor" abre "Minhas turmas"; "Entrar como Responsável" abre "Meus filhos".
- [ ] O `admin_demo` entra somente com a senha secreta.
- [ ] Recarregar uma página interna (ex.: `/alunos`) não dá erro 404.
- [ ] Em "Meu perfil", trocar a senha de uma conta de demo é recusado.

## Atualizações

A cada push na `main`, o Render e a Vercel publicam a nova versão automaticamente. A CI do GitHub roda os testes antes; só promova para a `main` o que passou na `develop`.

## Problemas comuns

| Sintoma | Causa provável |
| --- | --- |
| Login falha com "Não foi possível falar com o servidor" | `CORS_ALLOWED_ORIGINS` diferente do endereço da Vercel, ou `VITE_API_BASE_URL` sem `/api` no final |
| Primeiro acesso demora | Serviço gratuito acordando; aguarde até 1 minuto |
| "Muitas tentativas de login" | Limite de 10 tentativas por minuto por IP (`LOGIN_THROTTLE_RATE`) |
| `admin_demo` não entra | `DEMO_ADMIN_PASSWORD` ausente ou diferente no Render |
