# Criação de Skills — Refatoração Arquitetural Automatizada

Skill `refactor-arch` para Claude Code que analisa uma codebase de backend (qualquer linguagem),
audita anti-patterns de arquitetura/segurança/qualidade classificados por severidade, e refatora
o projeto para o padrão MVC — em 3 fases sequenciais e com um gate de confirmação humana antes de
qualquer alteração de arquivo.

A skill foi construída e validada nos 3 projetos-alvo deste desafio:

| Projeto | Stack | Estado inicial |
|---|---|---|
| `code-smells-project/` | Python + Flask | Monólito, 4 arquivos, sem separação de camadas |
| `ecommerce-api-legacy/` | Node.js + Express | God Class única (`AppManager.js`) |
| `task-manager-api/` | Python + Flask | MVC parcial (já tinha `models/`/`routes/`, mas com lógica vazando para as rotas) |

---

## Análise Manual

Antes de construir a skill, os três projetos-alvo foram lidos manualmente para levantar os
problemas reais que a skill precisaria detectar. Os achados abaixo usam referências exatas de
arquivo:linha e seguem a escala de severidade definida na seção "Contexto".

### Projeto 1 — code-smells-project (Python/Flask)

| Severidade | Problema | Local | Por que importa |
|---|---|---|---|
| CRITICAL | SQL Injection generalizada — queries montadas por concatenação de string | `models.py` (ex.: 28, 47-50, 110, 289-297) | Permite bypass de login e leitura/alteração/exclusão arbitrária de dados |
| CRITICAL | `SECRET_KEY` hardcoded e devolvida em `/health` | `app.py:7`, `controllers.py:289` | Qualquer cliente da API consegue ler a chave e forjar sessões |
| CRITICAL | Endpoints `/admin/reset-db` e `/admin/query` sem autenticação | `app.py:47-78` | Qualquer visitante apaga o banco inteiro ou roda SQL arbitrário |
| HIGH | Estado global mutável de conexão (`global db_connection`) | `database.py:4-10` | Condição de corrida sob concorrência; acoplamento implícito entre requests |
| MEDIUM | N+1 queries ao montar pedidos com itens | `models.py:171-233` | Uma query por pedido + uma por item — degradação linear de performance |
| MEDIUM | "Notificações" fake via `print()` tratadas como se tivessem ocorrido | `controllers.py:208-210` | Cria falsa sensação de funcionalidade completa (nenhum e-mail/SMS é enviado) |
| LOW | `print()` como logging em todo o projeto | `controllers.py` (~14 pontos) | Sem níveis, destino configurável ou correlação |
| LOW | `str(exception)` devolvido ao cliente em todo handler | `controllers.py` (~16 pontos) | Vaza detalhes internos (caminho de arquivo, nome de tabela) |

### Projeto 2 — ecommerce-api-legacy (Node.js/Express, LMS + checkout)

| Severidade | Problema | Local | Por que importa |
|---|---|---|---|
| CRITICAL | Credenciais e segredos hardcoded, incluindo chave de gateway de pagamento | `src/utils.js:2-4` | Vazamento do repositório compromete banco de produção e conta de pagamento |
| CRITICAL | Número de cartão completo e chave de pagamento impressos em log | `src/AppManager.js:45` | PCI: dado de cartão sensível parando em log/console, sem mascaramento |
| CRITICAL | "Hash" de senha falso — apenas Base64 repetido, totalmente reversível | `src/utils.js:17-23` (`badCrypto`) | Equivale a senha em texto puro; qualquer um decodifica o Base64 |
| HIGH | God Class — uma única classe mistura rotas, SQL, regra de negócio de pagamento/matrícula e relatório admin | `src/AppManager.js:1-141` | Impossível testar isoladamente; qualquer mudança arrisca quebrar checkout inteiro |
| MEDIUM | N+1 queries com callbacks aninhados no relatório financeiro | `src/AppManager.js:80-129` | Para cada curso → query de matrículas; para cada matrícula → 2 queries — cresce exponencialmente com os dados |
| MEDIUM | Deleção sem integridade referencial (a própria API admite) | `src/AppManager.js:131-137` | `DELETE /api/users/:id` deixa matrículas e pagamentos órfãos — resposta literalmente diz "ficaram sujos no banco" |
| LOW | `console.log` como logging | `src/utils.js:13`, `src/AppManager.js:45` | Sem nível, sem estrutura, mistura dado sensível no log |
| LOW | Nomenclatura ruim (`u`, `e`, `p`, `cid`, `cc`) | `src/AppManager.js:29-33` | Dificulta leitura e revisão do fluxo de checkout |

### Projeto 3 — task-manager-api (Python/Flask, já com camadas parciais)

| Severidade | Problema | Local | Por que importa |
|---|---|---|---|
| CRITICAL | Nenhuma rota exige autenticação — `/login` emite um token fake e previsível (`"fake-jwt-token-" + user.id`) que nunca é verificado em lugar nenhum do código | `routes/user_routes.py:92-151,210` (padrão repetido em todas as rotas de tasks/categorias) | Qualquer visitante não autenticado promove um usuário a admin ou apaga qualquer conta/task — equivale a não ter controle de acesso algum |
| CRITICAL | Hash de senha com MD5 sem salt, e o próprio hash é devolvido pela API | `models/user.py:27-32,21` | MD5 é quebrável por força bruta/rainbow table; expor o hash piora ainda mais |
| CRITICAL | Credenciais hardcoded (`SECRET_KEY`, usuário/senha SMTP) | `app.py:13`, `services/notification_service.py:7-10` | Vazamento do repo compromete sessões e a conta de e-mail do serviço |
| HIGH | Lógica de negócio (cálculo de atraso, validação de status/prioridade) duplicada nas rotas em vez de reaproveitar o Model | `routes/task_routes.py:30-39,71-80,92-154,166-223` vs. `models/task.py:38-60` (já existe `is_overdue()`/`validate_status()` prontos e ignorados) | Mesmo tendo camadas separadas, a regra vaza e diverge — exatamente o smell de "MVC parcial" |
| HIGH | Agregação inteira dos relatórios (`summary_report`/`user_report`) feita na rota, com loops manuais em vez de uma camada de serviço | `routes/report_routes.py:12-155` | Regra de negócio de reporting fica impossível de testar isolada e reaproveitar fora do HTTP |
| MEDIUM | N+1 queries na listagem de tasks e no relatório de produtividade por usuário | `routes/task_routes.py:41-57`, `routes/report_routes.py:53-68,157-165` | Uma query extra por task/usuário/categoria dentro de um loop — degradação linear de performance |
| MEDIUM | `NotificationService` implementado com envio real de e-mail, mas nunca importado/chamado por nenhuma rota | `services/notification_service.py:1-49` | Dead code que passa a falsa impressão de que a notificação de tasks já funciona |
| MEDIUM | `update_category` não valida payload vazio antes de acessar `data['name']`, diferente das demais rotas | `routes/report_routes.py:196-197` | Corpo vazio/`Content-Type` errado gera 500 genérico em vez do 400 consistente do resto da API |
| LOW | `print()` como logging e `except:` genérico (bare) espalhados pelas rotas | `routes/task_routes.py:62,149,153,219,234,237`, `routes/user_routes.py:83,89,130,147,149`, `routes/report_routes.py:186,207,222` | Sem correlação, sem nível, e engole qualquer exceção sem logar nada — inutilizável em produção |
| LOW | Magic strings de status/role repetidas sem usar as constantes já definidas (e nunca importadas) | `routes/task_routes.py`, `routes/user_routes.py` vs. `utils/helpers.py:110-111` (`VALID_STATUSES`/`VALID_ROLES`) | `'pending'/'done'/...` espalhadas — mudar a regra exige caçar todas as ocorrências |

## Contexto

### Definição de Severidades

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

---

## Construção da Skill

A skill vive em `.claude/skills/refactor-arch/` (uma cópia idêntica dentro de cada um dos 3
projetos, conforme exigido) e é composta por `SKILL.md` (o prompt/orquestrador das 3 fases) +
5 arquivos de referência em `references/` (o conhecimento de domínio):

```
.claude/skills/refactor-arch/
├── SKILL.md                              # fluxo das 3 fases, carrega os arquivos abaixo sob demanda
└── references/
    ├── project-analysis.md               # heurísticas de detecção — Fase 1
    ├── anti-patterns-catalog.md          # 14 anti-patterns + detecção de APIs deprecated — Fase 2
    ├── report-template.md                # formato exato do relatório de auditoria — Fase 2
    ├── mvc-guidelines.md                 # regras da arquitetura MVC alvo — Fase 3
    └── refactoring-playbook.md           # 13 padrões de transformação com exemplos antes/depois — Fase 3
```

### Decisões de design

- **`SKILL.md` como orquestrador, não como base de conhecimento.** Ele define o fluxo (Fase 1 →
  Fase 2 → gate de confirmação → Fase 3), a escala de severidade oficial e a instrução explícita
  de carregar os 5 arquivos de referência antes de agir — mas não duplica o conteúdo deles. Isso
  mantém o prompt principal curto e o conhecimento de domínio versionável/editável separadamente.
- **Fase 2 tem um template de relatório fechado** (`report-template.md`): estrutura fixa
  (`Summary` → `Findings` ordenados CRITICAL→LOW → `Deprecated APIs` → `Total`), com regra
  explícita de que file:linha precisa ser real e verificável, e a última linha do relatório é
  sempre o prompt de confirmação `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` —
  isso é o que garante o gate humano obrigatório antes de qualquer edição.
- **O catálogo de anti-patterns descreve sinais de detecção, não nomes de arquivo.** Cada entrada
  tem: o que procurar no código (ex. "query SQL dentro de loop for", não "código lento"),
  severidade padrão e uma nota de que a severidade pode subir/descer conforme o contexto (ex.
  SQL Injection num endpoint sem autenticação é sempre CRITICAL).

### Anti-patterns incluídos no catálogo (14, cobrindo CRITICAL → LOW)

| # | Anti-pattern | Severidade padrão |
|---|---|---|
| 1 | SQL Injection | CRITICAL |
| 2 | Credenciais e Segredos Hardcoded | CRITICAL |
| 3 | Endpoint Administrativo sem Autenticação | CRITICAL |
| 4 | Senhas em Texto Puro / hash reversível | CRITICAL |
| 5 | God Class / God Module | CRITICAL/HIGH |
| 6 | Lógica de Negócio no Controller/Rota | HIGH |
| 7 | Estado Global Mutável | HIGH |
| 8 | Efeito Colateral Simulado / Dead Code Disfarçado | MEDIUM |
| 9 | N+1 Queries | MEDIUM |
| 10 | Duplicação de Código | MEDIUM |
| 11 | Modo Debug/Config Insegura em "Produção" | MEDIUM |
| 12 | Uso de `print()`/`console.log` como Logging | LOW |
| 13 | Magic Numbers / Strings | LOW |
| 14 | Exposição de Detalhes Internos em Erros | LOW |

Mais uma seção dedicada de **Detecção de APIs Deprecated** (cruza versão declarada da
dependência contra métodos marcados como deprecated/removidos — ex. `flask.Markup`,
`before_first_request` removido no Flask 2.3+, `body-parser` redundante em Express recente,
`datetime.utcnow()` deprecated no Python 3.12+, `Model.query.get()` legado do SQLAlchemy 2.0).

Esses 14 (+ a seção de deprecated) foram escolhidos porque cobrem, com folga, os padrões
realmente encontrados na análise manual dos 3 projetos (SQL Injection e credenciais hardcoded
nos 3; God Class nos projetos 1 e 2; MVC parcial com lógica vazada no projeto 3) — o catálogo não
foi construído de forma genérica/teórica primeiro; foi derivado dos achados reais e só depois
generalizado para sinais de detecção reaproveitáveis em qualquer stack.

### Como a skill garante ser agnóstica de tecnologia

- **Fase 1** (`project-analysis.md`) detecta linguagem/framework por arquivo de manifesto e
  extensão dominante (`requirements.txt`/`.py` → Python, `package.json`/`.js` → Node), nunca por
  nome de projeto ou caminho hardcoded.
- **Catálogo e playbook** descrevem o *padrão* (ex. "query montada por concatenação de string
  com dado de entrada do usuário"), com exemplos em Python/Flask e Node/Express lado a lado
  quando ajuda — mas a regra de detecção em si não depende da linguagem.
- **`mvc-guidelines.md`** define responsabilidades de camada (Model só fala com o banco,
  Controller orquestra, View/Route só faz roteamento/validação de shape), deixando explícito que
  o nome da pasta deve seguir a convenção da linguagem, não um padrão fixo.
- **Prova prática:** a mesma cópia da skill (sem nenhuma edição) rodou nos 3 projetos — um
  monólito Python sem camadas, uma God Class Node.js, e um Flask com MVC parcial — e produziu
  auditorias e refatorações coerentes com o estado real de cada um (ver "Resultados" abaixo).

### Desafios encontrados e como foram resolvidos

- **Projeto 3 já tinha camadas, mas isso escondia o problema real.** A tentação inicial do
  catálogo era assumir que "ter `models/`/`routes/`" já significava arquitetura correta. Foi
  necessário adicionar um anti-pattern específico — "Lógica de Negócio no Controller/Rota" com
  ênfase em *duplicação* mesmo quando o Model já tem o método pronto (`is_overdue()` existente e
  ignorado) — para a skill não dar um falso "aprovado" a um projeto parcialmente organizado.
- **Validar boot real do Projeto 2 (Node.js) exigiu Node.js no ambiente**, que não estava
  disponível por padrão no sandbox de execução. Resolvido baixando um build portátil do
  Node.js 22.14.0 apenas para rodar a validação (não afeta o projeto entregue).
- **Manter a numeração do `Summary` batendo com o `Total` e com a contagem real de blocos
  `### [SEVERIDADE]`** exigiu uma regra explícita no `report-template.md` ("os números devem
  bater exatamente"), porque a tentação natural é estimar a contagem em vez de somar.

---

## Resultados

### Achados por severidade (Fase 2, todos os 3 projetos)

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| 1 — code-smells-project | 7 | 3 | 5 | 3 | **18** |
| 2 — ecommerce-api-legacy | 5 | 2 | 3 | 2 | **12** |
| 3 — task-manager-api | 4 | 2 | 7 | 4 | **17** |

Relatórios completos: [`reports/audit-project-1.md`](reports/audit-project-1.md),
[`reports/audit-project-2.md`](reports/audit-project-2.md),
[`reports/audit-project-3.md`](reports/audit-project-3.md).

### Comparação antes/depois da estrutura

**Projeto 1 — code-smells-project**

```
Antes                          Depois
app.py                         app.py                    (composition root)
controllers.py                 config/settings.py
models.py                      controllers/{admin,health,pedido,produto,relatorio,usuario}_controller.py
database.py                    database/connection.py
requirements.txt                middlewares/{auth,error_handler}.py
                                models/{pedido,produto,usuario}_model.py
                                services/notificacoes.py
                                views/{admin,health,main,pedido,produto,relatorio,usuario}_routes.py
```

**Projeto 2 — ecommerce-api-legacy**

```
Antes                          Depois
src/app.js                     src/app.js                        (composition root)
src/AppManager.js               src/config/{index,logger}.js
src/utils.js                    src/database/{connection,seed}.js
                                src/models/{user,course,enrollment,payment,audit_log,report}_model.js
                                src/controllers/{checkout,admin,user}_controller.js
                                src/middlewares/{admin_auth,error_handler,async_handler}.js
                                src/views/{checkout,admin,user}_routes.js
```

**Projeto 3 — task-manager-api**

```
Antes                           Depois
app.py                          app.py                    (composition root, sem mudança de posição)
database.py                     database.py                (sem mudança de posição)
models/{task,user,category}.py  config/settings.py         (novo — nada mais hardcoded)
routes/{task,user,report}_routes.py  controllers/{task,user,report}_controller.py   (novo)
services/notification_service.py     middlewares/{auth,error_handler}.py           (novo)
utils/helpers.py                     models/{task,user,category}.py  (lógica de negócio devolvida ao Model)
                                      routes/{task,user,report}_routes.py  (agora só roteamento + auth)
                                      services/notification_service.py
                                      utils/helpers.py
```

O Projeto 3 é o único onde a Fase 3 não foi uma reescrita completa: como já existiam
`models/`/`routes/`, a refatoração foi cirúrgica — introduziu `controllers/` e `config/`, moveu
a lógica de volta para o Model, e adicionou o middleware de autenticação real, sem reorganizar o
que já estava no lugar certo.

### Checklist de Validação

**Projeto 1 — code-smells-project**

- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.1.1)
- [x] Domínio da aplicação descrito corretamente (E-commerce: produtos, pedidos, usuários)
- [x] Número de arquivos analisados condiz com a realidade (4 arquivos, ~780 linhas)
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (18)
- [x] Detecção de APIs deprecated incluída (nenhuma encontrada, seção presente)
- [x] Skill pausou e pediu confirmação antes da Fase 3
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro (`app.py`)
- [x] Aplicação inicia sem erros — validado em 2026-07-11, ver [`reports/logs/project-1-boot.log`](reports/logs/project-1-boot.log)
- [x] Endpoints originais respondem corretamente — ver [`reports/logs/project-1-endpoints.md`](reports/logs/project-1-endpoints.md)

**Projeto 2 — ecommerce-api-legacy**

- [x] Linguagem detectada corretamente (JavaScript/Node.js)
- [x] Framework detectado corretamente (Express 4.22.1)
- [x] Domínio da aplicação descrito corretamente (LMS com checkout de cursos)
- [x] Número de arquivos analisados condiz com a realidade (3 arquivos, ~180 linhas)
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (12)
- [x] Detecção de APIs deprecated incluída (nenhuma encontrada, seção presente)
- [x] Skill pausou e pediu confirmação antes da Fase 3
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro (`src/app.js`)
- [x] Aplicação inicia sem erros — validado em 2026-07-11, ver [`reports/logs/project-2-boot.log`](reports/logs/project-2-boot.log)
- [x] Endpoints originais respondem corretamente — ver [`reports/logs/project-2-endpoints.md`](reports/logs/project-2-endpoints.md)

**Projeto 3 — task-manager-api**

- [x] Linguagem detectada corretamente (Python)
- [x] Framework detectado corretamente (Flask 3.0.0 + Flask-SQLAlchemy 3.1.1)
- [x] Domínio da aplicação descrito corretamente (Task Manager com usuários/categorias)
- [x] Número de arquivos analisados condiz com a realidade (15 arquivos, ~950 linhas)
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (17)
- [x] Detecção de APIs deprecated incluída (`datetime.utcnow()`, `Model.query.get()` — ver relatório)
- [x] Skill pausou e pediu confirmação antes da Fase 3
- [x] Estrutura de diretórios segue padrão MVC (introduziu `controllers/` e `config/`)
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models mantidos/reforçados como camada de dados
- [x] Views/Routes separadas para roteamento
- [x] Controllers concentram o fluxo da aplicação (novo)
- [x] Error handling centralizado
- [x] Entry point claro (`app.py`)
- [x] Aplicação inicia sem erros — validado em 2026-07-11, ver [`reports/logs/project-3-boot.log`](reports/logs/project-3-boot.log)
- [x] Endpoints originais respondem corretamente — ver [`reports/logs/project-3-endpoints.md`](reports/logs/project-3-endpoints.md)

### Logs de validação (evidência)

Todos os logs abaixo foram capturados ao vivo em 2026-07-11, subindo cada aplicação refatorada e
testando os endpoints via `curl` (não é validação estática de código):

- [`reports/logs/project-1-boot.log`](reports/logs/project-1-boot.log) +
  [`project-1-endpoints.md`](reports/logs/project-1-endpoints.md) — Flask sobe, `/health` e
  `/produtos` respondem 200, `/admin/reset-db` confirmado exigindo `X-Admin-Key` (401 sem
  header, 200 com header correto).
- [`reports/logs/project-2-boot.log`](reports/logs/project-2-boot.log) +
  [`project-2-endpoints.md`](reports/logs/project-2-endpoints.md) — Express sobe (`Frankenstein
  LMS rodando na porta 3000...`), checkout aprovado/recusado testados, relatório financeiro
  confirmado exigindo `x-admin-key` (401 → 200), log inspecionado sem número de cartão exposto.
- [`reports/logs/project-3-boot.log`](reports/logs/project-3-boot.log) +
  [`project-3-endpoints.md`](reports/logs/project-3-endpoints.md) — Flask sobe com logging
  estruturado (não mais `print()`), cadastro/login com token assinado testados, tentativa de
  auto-promoção a admin bloqueada (403), delete de conta sem role admin bloqueado (403).

> Node.js não estava pré-instalado no ambiente usado para gerar esta evidência; foi baixado um
> build portátil (não instalado no sistema, não commitado) só para rodar `node src/app.js` e
> validar o Projeto 2 de ponta a ponta.

### Observações sobre o comportamento da skill em stacks diferentes

- **Projeto 1 (monólito sem camadas)** foi o caso mais simples para a Fase 3: não havia nada para
  preservar, a skill reescreveu a estrutura inteira do zero seguindo `mvc-guidelines.md`.
- **Projeto 2 (Node/Express, God Class)** exigiu do playbook exemplos específicos de callback
  para `async/await` + `async_handler` (Express não tem tratamento de erro assíncrono nativo
  como decorators do Flask), e um model de hash de senha real via `crypto.scrypt` nativo do
  Node (sem dependência externa).
- **Projeto 3 (Flask com MVC parcial)** foi o teste real de agnosticismo *dentro* da mesma
  linguagem: a skill não pôde assumir "projeto Flask = igual ao Projeto 1". Ela teve que
  reconhecer que `models/`/`routes/` já existiam, identificar que a organização era superficial
  (lógica duplicada fora do Model) e propor uma mudança estrutural pontual (`controllers/` novo)
  em vez de uma reescrita completa — validando que a Fase 3 se adapta ao nível de organização já
  presente, como pedido no enunciado.

---

## Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado
  (`claude` disponível no PATH).
- Projeto 1 e 3 (Python/Flask): Python 3.10+ e `pip`.
- Projeto 2 (Node/Express): Node.js 18+ e `npm`.

### Rodar a skill em cada projeto

```bash
# Projeto 1 — Python/Flask, monólito
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — Node.js/Express, God Class
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — Python/Flask, MVC parcial
cd ../task-manager-api
claude "/refactor-arch"
```

Em cada execução: a Fase 1 imprime o resumo de stack/domínio, a Fase 2 imprime o relatório de
auditoria e **pausa pedindo confirmação** (`[y/n]`) — só depois de `y` a Fase 3 modifica arquivos.

### Como validar que a refatoração funcionou

```bash
# Projeto 1 e 3 (Flask)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
curl http://localhost:5000/health

# Projeto 2 (Express)
npm install
npm start
curl http://localhost:3000/api/checkout -X POST -H "Content-Type: application/json" \
  -d '{"usr":"Teste","eml":"t@t.com","pwd":"senha","c_id":1,"card":"4111222233334444"}'
```

A aplicação deve subir sem erro no console e os endpoints originais devem responder com os
mesmos contratos de antes da refatoração. Os logs de referência de uma execução real estão em
[`reports/logs/`](reports/logs/).

---

## Estrutura do repositório

```
mba-ia-refactor-projects-skill/
├── README.md
│
├── code-smells-project/                   # Projeto 1 — Python/Flask (E-commerce), refatorado para MVC
│   ├── .claude/skills/refactor-arch/       # skill
│   ├── app.py / config/ / controllers/ / database/ / middlewares/ / models/ / services/ / views/
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express (LMS + checkout), refatorado para MVC
│   ├── .claude/skills/refactor-arch/       # cópia da skill
│   └── src/ (app.js / config/ / controllers/ / database/ / middlewares/ / models/ / views/)
│
├── task-manager-api/                      # Projeto 3 — Python/Flask (Task Manager), refatorado para MVC
│   ├── .claude/skills/refactor-arch/       # cópia da skill
│   └── app.py / config/ / controllers/ / middlewares/ / models/ / routes/ / services/ / utils/
│
└── reports/
    ├── audit-project-1.md                 # saída da Fase 2 — Projeto 1
    ├── audit-project-2.md                 # saída da Fase 2 — Projeto 2
    ├── audit-project-3.md                 # saída da Fase 2 — Projeto 3
    └── logs/                              # evidência de boot + endpoints real, pós-refatoração
```

## Referências

- [Claude Code: Skills](https://docs.anthropic.com/en/docs/claude-code/skills)
- [Claude Code: Overview](https://docs.anthropic.com/en/docs/claude-code/overview)
- [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf)
- [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills)
