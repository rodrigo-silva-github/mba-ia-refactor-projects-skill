# Architecture Audit Report

Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.22.1
Files:   3 analyzed (app.js, AppManager.js, utils.js) | ~180 lines of code

## Summary

CRITICAL: 5 | HIGH: 2 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] God Class / God Module
File: src/AppManager.js:4-141
Description: A classe `AppManager` concentra inicialização/schema do banco (`initDb`), roteamento HTTP (`setupRoutes`), queries SQL diretas e regra de negócio de checkout, matrícula e relatório financeiro — tudo em um único arquivo/classe, sem separação entre camadas.
Impact: Qualquer alteração em uma regra (ex.: fluxo de pagamento) arrisca quebrar rotas administrativas ou o schema do banco; impossível testar a lógica de negócio sem subir o servidor Express inteiro.
Recommendation: Separar em Models (acesso a dado por domínio), Controllers (orquestração) e Views/Routes (registro de rota).

### [CRITICAL] Endpoint Administrativo sem Autenticação (relatório financeiro)
File: src/AppManager.js:80-129
Description: A rota `GET /api/admin/financial-report` expõe receita, pagamentos e dados de alunos sem nenhum middleware de autenticação ou verificação de papel antes de executar a consulta.
Impact: Qualquer visitante não autenticado pode ler dados financeiros e pessoais completos da plataforma apenas com uma requisição HTTP direta.
Recommendation: Adicionar middleware de autenticação/autorização de admin antes do handler.

### [CRITICAL] Endpoint Administrativo sem Autenticação (exclusão de usuário)
File: src/AppManager.js:131-137
Description: A rota `DELETE /api/users/:id` remove um usuário do banco sem nenhuma verificação de autenticação/autorização.
Impact: Qualquer cliente não autenticado pode apagar qualquer usuário da base apenas conhecendo o `id`.
Recommendation: Proteger a rota com middleware de autenticação + papel de admin.

### [CRITICAL] Credenciais e Segredos Hardcoded
File: src/utils.js:1-6
Description: `dbPass`, `paymentGatewayKey` e `smtpUser` estão declarados como strings literais no objeto `config`, incluindo uma chave `pk_live_...` de gateway de pagamento; `paymentGatewayKey` (junto com o número completo do cartão) ainda é impresso no console em `AppManager.js:45` a cada checkout.
Impact: Qualquer pessoa com acesso ao repositório (ou aos logs) compromete o gateway de pagamento e credenciais de banco em produção; o log também vaza dado de cartão (PCI).
Recommendation: Mover toda credencial para variáveis de ambiente lidas por um módulo `config/` dedicado e remover cartão/chave do log.

### [CRITICAL] Senha Armazenada com "Hash" Falso e Reversível
File: src/utils.js:17-23 (uso em src/AppManager.js:68)
Description: `badCrypto` não é uma função de hash — repete `Buffer.from(pwd).toString('base64')` e recorta 10 caracteres, produzindo uma saída curta, colidível e trivialmente reversível/quebrável por força bruta; nenhuma biblioteca de hash de senha (`bcrypt`/`argon2`/`scrypt`) é usada.
Impact: Um vazamento do banco expõe as senhas de fato (a codificação é decorativa), permitindo reuso em outros serviços via credential stuffing.
Recommendation: Substituir por hash real de senha com salt (ex.: `crypto.scrypt` nativo do Node ou `bcrypt`) na criação e verificação do usuário.

### [HIGH] Lógica de Negócio no Controller/Rota (checkout)
File: src/AppManager.js:28-78
Description: O handler de `POST /api/checkout` contém, inline, validação de payload, decisão de aprovação de pagamento (`cc.startsWith("4")`), criação de usuário, criação de matrícula e registro de auditoria — toda a orquestração do caso de uso dentro da função de rota.
Impact: A regra de negócio de checkout não pode ser reutilizada nem testada sem simular uma requisição HTTP completa; qualquer novo canal (ex.: job assíncrono) duplicaria essa lógica.
Recommendation: Extrair a orquestração para um Controller/Service de checkout que chame Models de `users`, `courses`, `enrollments` e `payments`.

### [HIGH] Estado Global Mutável (cache e contador compartilhados)
File: src/utils.js:9-15 (uso em src/AppManager.js:59)
Description: `globalCache` e `totalRevenue` são variáveis de módulo mutáveis compartilhadas entre todas as requisições; `logAndCache` escreve nesse objeto global a cada checkout sem nenhum controle de concorrência ou ciclo de vida por requisição (`totalRevenue` sequer é atualizado ou lido em nenhum outro ponto, ficando como estado morto).
Impact: Sob concorrência, escritas de requisições diferentes competem pelo mesmo objeto global, e testes não conseguem partir de um estado limpo entre execuções.
Recommendation: Eliminar o estado global mutável — usar cache por escopo de requisição ou um serviço externo (ex.: Redis) se cache real for necessário.

### [MEDIUM] N+1 Queries no Relatório Financeiro
File: src/AppManager.js:83-126
Description: Para cada curso, dispara uma query de matrículas; para cada matrícula, duas novas queries (usuário e pagamento) — gerando `O(cursos × matrículas)` consultas separadas ao SQLite em vez de uma única consulta agregada.
Impact: O tempo de resposta do relatório degrada linearmente com o volume de cursos/matrículas, tornando o endpoint inviável em produção com dados reais.
Recommendation: Substituir pelos `JOIN`s entre `courses`, `enrollments`, `users` e `payments` em uma única query, agrupando em memória.

### [MEDIUM] Efeito Colateral Simulado (cache/notificação fake)
File: src/utils.js:12-15
Description: `logAndCache` aparenta persistir algo relevante ("Salvando no cache"), mas apenas grava em um objeto JS em memória que nunca é lido de volta em nenhum outro lugar do código — não há cache real nem notificação.
Impact: Cria falsa sensação de funcionalidade implementada (cache/observabilidade), mascarando que o dado é descartado ao reiniciar o processo.
Recommendation: Remover a chamada ou substituir por uma integração real de cache/notificação claramente marcada como stub.

### [MEDIUM] Exclusão de Usuário sem Integridade Referencial
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` remove a linha de `users` sem tratar `enrollments`/`payments` relacionados — o próprio código reconhece isso na mensagem de resposta ("as matrículas e pagamentos ficaram sujos no banco"). Tratado como variação do anti-pattern "Lógica de Negócio no Controller/Rota": a regra de exclusão em cascata deveria existir e estar num Model, não ausente na rota.
Impact: Matrículas e pagamentos passam a referenciar um `user_id` inexistente, corrompendo o relatório financeiro e qualquer consulta futura por esses registros.
Recommendation: Mover a exclusão para um Model de `users` que trate (cascata) os registros dependentes.

### [LOW] Uso de console.log como Logging
File: src/app.js:13, src/AppManager.js:45, src/utils.js:13
Description: Eventos de boot, processamento de pagamento e "cache" usam `console.log` diretamente, sem níveis, destino configurável ou correlação entre logs.
Impact: Impossível filtrar por severidade ou rotear logs para um sistema de observabilidade em produção.
Recommendation: Substituir por um logger estruturado mínimo (níveis info/warn/error).

### [LOW] Magic Numbers/Strings
File: src/utils.js:19, src/AppManager.js:46-54
Description: `10000` (iterações de `badCrypto`) e os literais `"PAID"`/`"DENIED"` e `startsWith("4")` (bandeira de cartão) estão espalhados no código sem constante/enum central.
Impact: Alterar a regra de status de pagamento ou o critério de aprovação exige caçar manualmente todas as ocorrências, arriscando divergência silenciosa.
Recommendation: Extrair para constantes nomeadas (ex.: `PAYMENT_STATUS.PAID`).

## Deprecated APIs

Nenhuma API deprecated/removida foi encontrada — Express 4.22.1 já usa `express.json()` nativo (sem `body-parser` standalone) e `sqlite3` ^5.1.6 não possui aviso de depreciação.

---

Total: 12 findings

---

## Phase 3 — Refactoring Summary

Refatorado para MVC. Estrutura resultante:

```
src/
├── app.js                        # composition root
├── config/
│   ├── index.js                  # config lida de env vars, defaults seguros p/ dev
│   └── logger.js                 # logger estruturado (info/warn/error)
├── database/
│   ├── connection.js             # conexão sqlite3 + helpers run/get/all promisificados + schema
│   └── seed.js                   # seed via Models (reaproveita hashing/validação)
├── models/
│   ├── user_model.js             # hash real de senha (crypto.scrypt), cascade delete
│   ├── course_model.js
│   ├── enrollment_model.js
│   ├── payment_model.js          # STATUS.PAID/DENIED centralizados
│   ├── audit_log_model.js
│   └── report_model.js           # relatório financeiro via JOIN único (resolve N+1)
├── controllers/
│   ├── checkout_controller.js    # orquestração do caso de uso (movida da rota)
│   ├── admin_controller.js
│   └── user_controller.js
├── middlewares/
│   ├── admin_auth.js             # exige header x-admin-key nos endpoints administrativos
│   ├── error_handler.js          # tratamento de erro centralizado (resposta genérica)
│   └── async_handler.js          # encaminha erro de rota async para o error_handler
└── views/
    ├── checkout_routes.js        # valida shape do payload, delega ao controller
    ├── admin_routes.js
    └── user_routes.js
```

### Mudanças de contrato deliberadas (exigidas pelas correções CRITICAL/MEDIUM)
- `GET /api/admin/financial-report` e `DELETE /api/users/:id` agora exigem o header `x-admin-key`
  (antes eram públicos — CRITICAL corrigido).
- `DELETE /api/users/:id` agora também remove matrículas/pagamentos do usuário e devolve uma
  mensagem de sucesso condizente (antes admitia deixar "sujeira" no banco — MEDIUM corrigido).
- Erros inesperados de banco (antes `"Erro DB"`/`"Erro Matrícula"`/`"Erro Pagamento"` em texto
  puro, ad hoc por etapa) agora passam pelo error handler central e retornam
  `{"error": "Erro interno no servidor"}` em JSON. Respostas de negócio esperadas (400/404 com
  `"Bad Request"`, `"Curso não encontrado"`, `"Pagamento recusado"`, 200 com `{msg, enrollment_id}`)
  permanecem idênticas.

### Validation
- ✓ Todos os `require`/`module.exports` foram conferidos manualmente (caminho relativo e nome
  exportado) — a árvore de imports resolve sem referências quebradas.
- ✓ Boot real (`npm start`) validado após instalar Node.js 22.14.0 no sandbox (ausente
  inicialmente) e rodar `npm install`. A aplicação sobe sem erros:
  `Frankenstein LMS rodando na porta 3000...`.
- ✓ Endpoints originais testados via `curl`, preservando os contratos esperados:
  - `POST /api/checkout`: sucesso com usuário novo e com usuário já existente (mesmo
    `{msg, enrollment_id}`); cartão recusado (`"Pagamento recusado"`); payload incompleto → 400;
    curso inexistente → 404 — todos idênticos ao comportamento original.
  - `GET /api/admin/financial-report` e `DELETE /api/users/:id`: 401 sem `x-admin-key`, 200 com
    o header — CRITICAL de endpoint administrativo sem autenticação confirmado corrigido em
    runtime.
  - Relatório financeiro consultado após uma exclusão de usuário: sem registros órfãos, sem
    crash, revenue/students corretos via a query com `JOIN` único — MEDIUM (integridade
    referencial) e MEDIUM (N+1) confirmados corrigidos em runtime.
  - Logs do processo inspecionados durante o checkout: nenhum número de cartão ou
    `paymentGatewayKey` impresso — CRITICAL de dado sensível em log confirmado corrigido.
- ✓ Todos os anti-patterns CRITICAL/HIGH do relatório foram eliminados e confirmados tanto na
  revisão estática do código quanto em execução real (God Class dissolvida em
  Models/Controllers/Views; endpoints admin agora exigem `x-admin-key`; segredos migrados para
  env vars; hash de senha real via `crypto.scrypt`; lógica de checkout movida para controller;
  estado global mutável removido).
