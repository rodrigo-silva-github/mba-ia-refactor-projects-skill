# Architecture Audit Report — Projeto 3 (task-manager-api)

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python / Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Files:   15 analyzed | ~950 lines of code

## Summary
CRITICAL: 4 | HIGH: 2 | MEDIUM: 7 | LOW: 4

## Findings

### [CRITICAL] Credenciais Hardcoded (SECRET_KEY)
File: app.py:13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` está fixo no código-fonte, versionado no repositório.
Impact: Compromete a assinatura de sessão/tokens; qualquer pessoa com acesso ao repo pode forjar sessões válidas.
Recommendation: Carregar `SECRET_KEY` de variável de ambiente (`os.getenv`), aproveitando o `python-dotenv` já presente nas dependências.

### [CRITICAL] Credenciais Hardcoded (SMTP)
File: services/notification_service.py:7-10
Description: Host, usuário e senha de e-mail (`senha123`) estão hardcoded na classe `NotificationService`.
Impact: Vazamento de credenciais de um serviço de e-mail real caso o repositório seja exposto.
Recommendation: Mover credenciais para variáveis de ambiente e nunca commitar segredos literais.

### [CRITICAL] Senha com Hash Inseguro (MD5, sem salt)
File: models/user.py:27-32
Description: `set_password`/`check_password` usam `hashlib.md5` sem salt para armazenar e comparar senhas.
Impact: MD5 é quebrado e rápido de forçar por brute-force/rainbow table; um vazamento do banco expõe todas as senhas de fato em texto reversível na prática.
Recommendation: Substituir por `werkzeug.security.generate_password_hash`/`check_password_hash` (bcrypt/scrypt), migrando os hashes existentes.

### [CRITICAL] Ausência Total de Autenticação/Autorização
File: routes/user_routes.py:92-151 (padrão replicado em routes/task_routes.py e routes/report_routes.py)
Description: Nenhuma rota do sistema — incluindo `PUT/DELETE /users/<id>` (que permite qualquer requisição promover um usuário a `admin` ou deletar qualquer conta) — exige autenticação. O `/login` (user_routes.py:210) emite um `'fake-jwt-token-' + str(user.id)` que nunca é verificado em nenhum lugar do código.
Impact: Qualquer visitante não autenticado pode ler, criar, alterar papel (role) ou apagar qualquer usuário/task/categoria via requisição HTTP direta — equivalente a não ter controle de acesso algum.
Recommendation: Implementar verificação real de token (JWT assinado) e um decorator de autenticação/autorização aplicado a todas as rotas que alteram dados ou expõem dados sensíveis.

### [HIGH] Lógica de Negócio no Controller/Rota (tasks)
File: routes/task_routes.py:92-154, 166-223
Description: `create_task`/`update_task` reimplementam validação de status/prioridade/data inline na rota em vez de delegar a `Task` ou a uma camada de serviço — mesma regra duplicada em dois lugares dentro do próprio arquivo.
Impact: Regra de negócio acoplada ao transporte HTTP; qualquer mudança de regra precisa ser replicada manualmente em cada rota, dificultando testes sem subir servidor.
Recommendation: Extrair a validação para um serviço/model reutilizável (ex.: usar `utils/helpers.process_task_data`, hoje não utilizado) e chamar essa função a partir das rotas.

### [HIGH] Lógica de Negócio no Controller/Rota (relatórios)
File: routes/report_routes.py:12-155
Description: `summary_report`/`user_report` calculam agregações (contagem por status/prioridade, atraso, produtividade por usuário) inteiramente dentro da rota, com loops manuais em vez de queries agregadas ou uma camada de serviço de relatórios.
Impact: Lógica de negócio de reporting fica impossível de testar isoladamente e de reaproveitar fora do contexto HTTP; degrada performance ao carregar todas as tasks/usuários em memória para agregar em Python.
Recommendation: Mover os cálculos para um `ReportService` dedicado, mantendo a rota apenas como camada de transporte.

### [MEDIUM] Config Insegura sem Uso de Variáveis de Ambiente
File: app.py:11,13,15,34
Description: `SQLALCHEMY_DATABASE_URI` e `SECRET_KEY` fixos no código, `CORS(app)` liberado sem restrição de origem, e `app.run(debug=True, host='0.0.0.0', ...)` sem diferenciação de ambiente — apesar de `python-dotenv` estar nas dependências, nunca é usado.
Impact: Debugger interativo do Werkzeug exposto publicamente (risco de execução remota de código) e CORS aberto a qualquer origem.
Recommendation: Ler configuração via variáveis de ambiente (`os.getenv`) e condicionar `debug=True`/CORS a um ambiente de desenvolvimento explícito.

### [MEDIUM] Duplicação de Código — Cálculo de "overdue"
File: models/task.py:50-60; routes/task_routes.py:30-39,71-80; routes/user_routes.py:171-180; routes/report_routes.py:34-37,132-135
Description: A mesma lógica condicional (`due_date < now and status not in ('done','cancelled')`) é reescrita manualmente em 5 lugares diferentes; o método `Task.is_overdue()` que já existe no model nunca é chamado.
Impact: Alto risco de divergência silenciosa — uma correção na regra de atraso feita em um lugar não se propaga aos outros quatro.
Recommendation: Remover as reimplementações e chamar `task.is_overdue()` em todos os pontos.

### [MEDIUM] Duplicação de Código / Dead Code — validação não reutilizada
File: utils/helpers.py:57-111
Description: `process_task_data`, `VALID_STATUSES` e `VALID_ROLES` foram implementados para centralizar validação, mas nenhuma rota os importa — routes/task_routes.py e routes/user_routes.py reimplementam as mesmas listas de valores válidos inline.
Impact: Duas fontes de verdade para a mesma regra; a versão "central" fica obsoleta e engana quem lê o código achando que é usada.
Recommendation: Substituir a validação inline nas rotas pela chamada a `process_task_data`/`VALID_STATUSES`/`VALID_ROLES`, ou remover o código morto se a abordagem inline for a escolhida.

### [MEDIUM] N+1 Queries — listagem de tasks
File: routes/task_routes.py:41-57
Description: `get_tasks` itera sobre todas as tasks e, para cada uma, dispara `User.query.get(...)` e `Category.query.get(...)` separadamente em vez de usar join/eager loading.
Impact: Número de queries cresce linearmente com o total de tasks — degradação severa em produção.
Recommendation: Usar `db.session.query(Task).options(joinedload(Task.user), joinedload(Task.category))` ou equivalente.

### [MEDIUM] N+1 Queries — relatórios
File: routes/report_routes.py:53-68, 157-165
Description: `summary_report` busca as tasks de cada usuário em um loop (`Task.query.filter_by(user_id=u.id)`), e `get_categories` conta tasks por categoria também em loop.
Impact: Mesma degradação de performance do item anterior, agravada por rodar em toda chamada ao endpoint de relatório.
Recommendation: Substituir por uma única query agregada (`GROUP BY`) por usuário/categoria.

### [MEDIUM] Validação Ausente — bug de robustez em update_category
File: routes/report_routes.py:196-197
Description: `update_category` chama `data = request.get_json()` e acessa `'name' in data` diretamente, sem o `if not data: return ... 400` presente em todas as outras rotas de escrita do projeto.
Impact: Uma requisição com corpo vazio ou `Content-Type` incorreto gera `AttributeError` não tratado (500 genérico do Flask) em vez de um erro 400 consistente com o resto da API.
Recommendation: Adicionar a mesma checagem `if not data: return jsonify({'error': ...}), 400` usada nas demais rotas.

### [MEDIUM] Serviço Não Integrado (Dead Code)
File: services/notification_service.py:1-49
Description: `NotificationService` implementa envio de e-mail real via `smtplib`, mas a classe nunca é importada nem instanciada em nenhuma rota — criar/atualizar uma task ou atribuí-la a um usuário não dispara nenhuma notificação.
Impact: Cria a falsa impressão de que a funcionalidade de notificação existe e funciona, quando na prática é código morto desconectado do fluxo da aplicação.
Recommendation: Integrar o serviço nas rotas relevantes (ex.: ao atribuir `user_id` numa task) ou remover o código morto se a funcionalidade não for necessária.

### [LOW] Uso de print() como Logging
File: routes/task_routes.py:149,153,219; routes/user_routes.py:83,89,147; services/notification_service.py:21,24; utils/helpers.py:36-41 (log_action nunca chamado)
Description: Eventos de negócio e erros são registrados com `print()` em vez de um logger configurável.
Impact: Sem níveis de log, sem destino configurável, inutilizável em produção/observabilidade.
Recommendation: Adotar o módulo `logging` do Python com um logger por módulo.

### [LOW] Magic Strings — status e role
File: routes/task_routes.py:110,177; routes/user_routes.py:71,120; utils/helpers.py:110-111
Description: Listas literais `['pending','in_progress','done','cancelled']` e `['user','admin','manager']` são repetidas em múltiplos arquivos, apesar de `VALID_STATUSES`/`VALID_ROLES` já existirem (não usadas) em utils/helpers.py.
Impact: Mudar um valor válido exige caçar todas as ocorrências manualmente, com risco de esquecer uma.
Recommendation: Importar e usar as constantes já definidas em `utils/helpers.py`.

### [LOW] Uso de except Genérico
File: routes/task_routes.py:62,237; routes/user_routes.py:130,149; routes/report_routes.py:186,207,222
Description: Blocos `except:` sem tipo capturam qualquer exceção (inclusive `KeyboardInterrupt`/`SystemExit`) e apenas retornam uma mensagem genérica, sem log estruturado do erro real.
Impact: Erros reais ficam invisíveis para diagnóstico em produção; dificulta debugging de falhas inesperadas.
Recommendation: Capturar `Exception` explicitamente e logar com `logging.exception(...)`.

### [LOW] Dependências Declaradas e Não Utilizadas
File: requirements.txt:4-6
Description: `marshmallow`, `requests` e `python-dotenv` estão no manifesto de dependências mas não são importados em nenhum lugar do código.
Impact: Superfície de dependências maior que o necessário (mais CVEs em potencial a monitorar) e confusão sobre o que o projeto realmente usa — `marshmallow` em particular sugere que a validação deveria ter sido feita com schemas, não inline nas rotas.
Recommendation: Remover as dependências não usadas do requirements.txt, ou efetivamente adotá-las (ex.: `marshmallow` para as validações hoje manuais).

================================
Total: 17 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Status

Aprovado pelo usuário em 2026-07-11. Fase 3 (refatoração) executada em seguida — ver commit da refatoração para o detalhamento do que foi corrigido.
