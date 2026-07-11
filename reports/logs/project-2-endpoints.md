# Projeto 2 (ecommerce-api-legacy) — Evidência de execução pós-refatoração

Capturado em 2026-07-11. Node.js não estava disponível no sandbox por padrão; foi baixado um
build portátil do Node.js 22.14.0 (`nodejs.org/dist`) só para esta validação, sem alterar o
projeto. Servidor iniciado com `node src/app.js` e testado via `curl` contra
`http://localhost:3000`.

## Boot

Ver `project-2-boot.log` — servidor sobe sem erros: `Frankenstein LMS rodando na porta 3000...`.

## Checkout (fluxo principal preservado)

```
$ curl -s -X POST http://localhost:3000/api/checkout -H "Content-Type: application/json" \
  -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
{"msg":"Sucesso","enrollment_id":2}                     → cartão começando em 4 = aprovado

$ curl -s -X POST http://localhost:3000/api/checkout -H "Content-Type: application/json" \
  -d '{"usr":"Joao","eml":"joao@teste.com","pwd":"123","c_id":1,"card":"5111222233334444"}'
Pagamento recusado                                       → cartão começando em 5 = recusado
```

## Correção do CRITICAL — endpoint administrativo sem autenticação

```
$ curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/admin/financial-report
401                                                       → sem x-admin-key

$ curl -s http://localhost:3000/api/admin/financial-report -H "x-admin-key: dev-admin-key-change-me"
[{"course":"Clean Architecture","revenue":997,"students":[...]}, ...]   → 200 com a chave
```

## Correção do CRITICAL — dado de cartão em log

O log do processo (`project-2-boot.log`) foi inspecionado após os dois checkouts acima:

```
[INFO] ... Frankenstein LMS rodando na porta 3000...
[INFO] ... Processando pagamento do curso 2 para o usuário 2
[INFO] ... Processando pagamento do curso 1 para o usuário 3
```

Nenhum número de cartão ou `paymentGatewayKey` aparece no log — confirmado por busca textual
(`grep` pelo número de cartão usado no teste e pela chave de pagamento, zero ocorrências).

## Conclusão

Boot sem erros, fluxo de checkout preservado (sucesso e recusa), e os dois achados CRITICAL
relacionados a autenticação de admin e vazamento de dado de cartão em log confirmados
corrigidos em runtime.
