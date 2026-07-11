# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Variáveis de ambiente

Nenhuma é obrigatória — todas têm um valor default seguro para desenvolvimento local:

| Variável | Default (dev) | Uso |
|---|---|---|
| `PORT` | `3000` | Porta HTTP |
| `DB_USER` / `DB_PASS` | `dev_user` / `dev_pass_change_me` | Credenciais de banco (não usadas pelo SQLite em memória, mantidas para paridade com um banco externo) |
| `PAYMENT_GATEWAY_KEY` | `pk_test_dev_change_me` | Chave do gateway de pagamento simulado |
| `SMTP_USER` | `dev@example.com` | Usuário de envio de e-mail (não implementado) |
| `ADMIN_API_KEY` | `dev-admin-key-change-me` | Chave exigida no header `x-admin-key` para os endpoints administrativos |

Em produção, defina todas explicitamente (nunca use os defaults de dev).

## Endpoints administrativos

`GET /api/admin/financial-report` e `DELETE /api/users/:id` agora exigem o header `x-admin-key`
com o valor de `ADMIN_API_KEY` — antes da refatoração eram públicos.
