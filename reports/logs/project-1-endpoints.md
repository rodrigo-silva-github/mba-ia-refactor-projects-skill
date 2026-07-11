# Projeto 1 (code-smells-project) — Evidência de execução pós-refatoração

Capturado em 2026-07-11, rodando `python app.py` (Flask dev server, `FLASK_DEBUG=true` para
habilitar o endpoint administrativo protegido) e testando via `curl` contra
`http://localhost:5000`.

## Boot

Ver `project-1-boot.log` — servidor sobe sem erros e loga `SERVIDOR INICIADO`.

## Endpoints originais (devem continuar respondendo)

```
$ curl -s http://localhost:5000/health
{"counts":{"pedidos":0,"produtos":10,"usuarios":3},"database":"connected","status":"ok","versao":"1.0.0"}

$ curl -s http://localhost:5000/produtos
{"dados":[{"ativo":1,"categoria":"informatica", ... }], ...}   # 200 OK, 10 produtos do seed
```

## Correção do CRITICAL — endpoints administrativos sem autenticação

Antes: `/admin/reset-db` e `/admin/query` respondiam a qualquer requisição, sem checagem
alguma. Depois da refatoração:

- `/admin/query` foi **removido** (não existe versão segura equivalente em produção,
  conforme a recomendação do relatório de auditoria) → `404` sempre.
- `/admin/reset-db` agora passa pelo middleware `requer_chave_admin`:

```
$ curl -s -X POST http://localhost:5000/admin/reset-db
{"erro": "Não autorizado", "sucesso": false}          → HTTP 401 (sem header)

$ curl -s -X POST http://localhost:5000/admin/reset-db -H "X-Admin-Key: errado"
{"erro": "Não autorizado", "sucesso": false}          → HTTP 401 (header errado)

$ curl -s -X POST http://localhost:5000/admin/reset-db -H "X-Admin-Key: dev-admin-key-change-me"
{"mensagem": "Banco de dados resetado", "sucesso": true}   → HTTP 200 (header correto)
```

Em produção (`FLASK_DEBUG=false`, o padrão), o endpoint retorna `404` mesmo com a chave
correta — só fica acessível em ambiente de desenvolvimento explícito.

## Conclusão

Boot sem erros, endpoints de negócio (`/health`, `/produtos`) preservados, e o achado CRITICAL
de endpoint administrativo sem autenticação confirmado corrigido em runtime (não apenas por
leitura estática do código).
