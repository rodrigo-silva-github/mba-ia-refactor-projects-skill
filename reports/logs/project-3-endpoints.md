# Projeto 3 (task-manager-api) — Evidência de execução pós-refatoração

Capturado em 2026-07-11, rodando `python app.py` (Flask dev server) e testando via `curl`
contra `http://localhost:5000`.

## Boot

Ver `project-3-boot.log` — servidor sobe sem erros; logs estruturados via módulo `logging`
(nível + timestamp), não mais `print()`.

## Cadastro, login e token real (substitui o `fake-jwt-token-<id>` original)

```
$ curl -s -X POST http://localhost:5000/users -H "Content-Type: application/json" \
  -d '{"name":"Ana Silva","email":"ana@teste.com","password":"senhaforte123"}'
{"active":true,"email":"ana@teste.com","id":2,"name":"Ana Silva","role":"user", ...}   → 201

$ curl -s -X POST http://localhost:5000/login -H "Content-Type: application/json" \
  -d '{"email":"ana@teste.com","password":"senhaforte123"}'
{"message":"Login realizado com sucesso",
 "token":"eyJ1c2VyX2lkIjoyfQ.alKmDA.IWcPO2VeEiOJICP61gnheYMKvuY", ...}                → 200
```

O token é assinado (`itsdangerous.URLSafeTimedSerializer` com `SECRET_KEY`) e efetivamente
verificado nas rotas protegidas — diferente do token original, que era a string previsível
`"fake-jwt-token-" + user.id` e nunca era checado em lugar nenhum do código.

## Correção do CRITICAL — ausência total de autenticação / escalonamento de privilégio

```
$ curl -s -X PUT http://localhost:5000/users/2 -H "Content-Type: application/json" -d '{"role":"admin"}'
{"error":"Autenticação necessária"}                     → HTTP 401 (sem token)

$ curl -s -X PUT http://localhost:5000/users/2 -H "Authorization: Bearer <token-do-usuario>" \
  -H "Content-Type: application/json" -d '{"role":"admin"}'
{"error":"Apenas administradores podem alterar role/active"}   → HTTP 403 (usuário comum tentando se
                                                                    autopromover a admin — bloqueado)

$ curl -s -X DELETE http://localhost:5000/users/2 -H "Authorization: Bearer <token-do-usuario>"
{"error":"Acesso restrito a administradores"}           → HTTP 403 (delete exige role admin)
```

Antes da refatoração, qualquer requisição não autenticada conseguia promover um usuário a
`admin` ou apagar qualquer conta — confirmado corrigido em runtime, não apenas por leitura
estática do código.

## Conclusão

Boot sem erros, endpoints de leitura (`/health`, `/tasks`, listagem de usuários) preservados
como públicos (design intencional da API), e as rotas de escrita sensíveis (`PUT`/`DELETE
/users/<id>`) agora exigem autenticação/autorização real — achado CRITICAL confirmado
corrigido em runtime.
