# Architecture Audit Report

Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed (app.py, controllers.py, database.py, models.py) | ~780 lines of code

## Summary

CRITICAL: 7 | HIGH: 3 | MEDIUM: 5 | LOW: 3

## Findings

### [CRITICAL] Credenciais e Segredos Hardcoded
File: app.py:7
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` está gravado em texto puro no código-fonte.
Impact: Qualquer pessoa com acesso ao repositório pode forjar sessões/tokens assinados com essa chave.
Recommendation: Extrair para variável de ambiente (`os.environ.get("SECRET_KEY", ...)`).

### [CRITICAL] Endpoint Administrativo sem Autenticação (reset de banco)
File: app.py:47-57
Description: Rota `POST /admin/reset-db` apaga todos os registros de `itens_pedido`, `pedidos`, `produtos` e `usuarios` sem nenhuma verificação de autenticação ou papel de admin.
Impact: Qualquer visitante não autenticado pode destruir a base de dados inteira com uma única requisição HTTP.
Recommendation: Remover o endpoint ou protegê-lo com middleware de autenticação + papel admin.

### [CRITICAL] Endpoint Administrativo sem Autenticação (execução de SQL arbitrário)
File: app.py:59-78
Description: Rota `POST /admin/query` recebe uma string SQL livre no corpo (`dados.get("sql")`) e executa diretamente via `cursor.execute(query)`, sem autenticação nem restrição de comandos.
Impact: Equivale a acesso irrestrito de administrador de banco de dados para qualquer cliente externo.
Recommendation: Remover completamente o endpoint (não existe versão segura equivalente em produção).

### [CRITICAL] God Module no Entry Point
File: app.py:47-78
Description: `app.py`, que deveria ser apenas o composition root, também executa SQL diretamente e concentra lógica administrativa privilegiada, misturando roteamento + acesso a banco + regra de negócio no mesmo arquivo.
Impact: Impossível testar ou proteger essa lógica isoladamente das demais rotas.
Recommendation: Extrair rotas para módulos de View/Router e mover a lógica administrativa para um Controller dedicado.

### [CRITICAL] Exposição de Credenciais em Endpoint de Health Check
File: controllers.py:276-290
Description: `health_check()` devolve `"debug": True` e `"secret_key": "minha-chave-super-secreta-123"` diretamente na resposta JSON pública.
Impact: Vaza a chave secreta da aplicação para qualquer cliente que chame `GET /health`.
Recommendation: Remover os campos `secret_key` e `debug` da resposta.

### [CRITICAL] SQL Injection (concatenação de string em queries)
File: models.py:28-297 (ex.: 28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-166, 174, 279-281, 289-297)
Description: Praticamente todas as funções de acesso a dados montam SQL por concatenação de string com valores vindos diretamente de request/path, em vez de usar parâmetros bindados.
Impact: Permite leitura/alteração/exclusão arbitrária de dados e bypass de autenticação.
Recommendation: Parametrizar todas as queries com `?` e passar os valores como tupla.

### [CRITICAL] Senhas em Texto Puro
File: models.py:105-131 (também database.py:76-79)
Description: Senhas são inseridas e comparadas como string simples, sem hash; o campo `senha` também é devolvido em texto puro nas respostas de `GET /usuarios` e `GET /usuarios/<id>`.
Impact: Um vazamento do banco ou da API expõe todas as senhas em claro.
Recommendation: Usar `werkzeug.security.generate_password_hash`/`check_password_hash` e nunca devolver o campo `senha`.

### [HIGH] Lógica de Negócio no Controller
File: controllers.py:24-96
Description: `criar_produto`/`atualizar_produto` embutem regra de negócio (lista `categorias_validas` hardcoded, limites de tamanho de nome, validação de preço/estoque) diretamente na função de rota.
Impact: Regra de negócio acoplada ao transporte HTTP — não pode ser reutilizada nem testada sem subir o servidor Flask.
Recommendation: Mover a lista de categorias e as validações para `models`/`validators`.

### [HIGH] Estado Global Mutável de Conexão
File: database.py:4-10
Description: `db_connection` é uma variável de módulo (`global`) reaproveitada entre todas as requisições via `get_db()`.
Impact: Condições de corrida sob concorrência e acoplamento implícito entre chamadas que deveriam ser independentes.
Recommendation: Usar o contexto de aplicação do Flask (`flask.g` + `teardown_appcontext`).

### [HIGH] God Module (múltiplos domínios em um único Model)
File: models.py:1-314
Description: Um único arquivo `models.py` concentra acesso a dados de produtos, usuários, pedidos e relatório de vendas.
Impact: Qualquer mudança em um domínio arrisca quebrar outro que vive no mesmo arquivo.
Recommendation: Separar em `produto_model.py`, `usuario_model.py` e `pedido_model.py`.

### [MEDIUM] Modo Debug/Config Insegura em "Produção"
File: app.py:8-9,88
Description: `app.config["DEBUG"] = True` e `app.run(..., debug=True)` fixos no código, além de `CORS(app)` liberando todas as origens.
Impact: Debugger interativo do Werkzeug exposto publicamente pode permitir execução remota de código.
Recommendation: Ler `DEBUG` de variável de ambiente e restringir CORS às origens necessárias.

### [MEDIUM] Duplicação de Código (validação de payload)
File: controllers.py:28-50 (repetido em 72-91)
Description: O bloco de validação de campos obrigatórios e valores negativos de `criar_produto` é replicado quase identicamente em `atualizar_produto`.
Impact: Correção de uma regra de validação precisa ser replicada manualmente nos dois lugares.
Recommendation: Extrair a validação para uma função compartilhada.

### [MEDIUM] Efeito Colateral Simulado / Dead Code Disfarçado
File: controllers.py:208-210 (também 247-250)
Description: `criar_pedido` e `atualizar_status_pedido` apenas fazem `print(...)` simulando envio de email/SMS/push/notificação, sem chamar nenhum serviço real.
Impact: Cria falsa sensação de funcionalidade completa.
Recommendation: Extrair para uma função de notificação explicitamente marcada como stub/log.

### [MEDIUM] Duplicação de Código (mapeamento de linha e função de pedidos)
File: models.py:9-21 (repetido em 31-40, 302-313); e models.py:171-201 (quase idêntico a 203-233)
Description: O mapeamento de `row` para dicionário é reescrito de forma idêntica em três funções de produtos; `get_pedidos_usuario` e `get_todos_pedidos` duplicam quase toda a lógica de montagem de itens.
Impact: Qualquer mudança no formato de resposta precisa ser replicada em múltiplos pontos.
Recommendation: Extrair funções privadas compartilhadas de mapeamento/montagem.

### [MEDIUM] N+1 Queries
File: models.py:171-233
Description: `get_pedidos_usuario`/`get_todos_pedidos` disparam, para cada pedido, uma query de itens e, para cada item, uma nova query buscando o nome do produto.
Impact: O número de queries cresce linearmente com a quantidade de pedidos e itens.
Recommendation: Substituir por uma única query com `JOIN`, agrupando em memória.

### [LOW] Uso de `print()` como Logging
File: controllers.py:8 (padrão repetido em ~14 pontos do arquivo); também app.py:56,83-86
Description: Eventos de negócio e erros são registrados com `print(...)` em vez de um logger configurável.
Impact: Sem níveis de log, destino configurável ou correlação.
Recommendation: Substituir por `logging.getLogger(__name__)` estruturado.

### [LOW] Exposição de Detalhes Internos em Erros
File: controllers.py:12 (padrão repetido em ~16 handlers)
Description: Todos os blocos `except Exception as e` devolvem `str(e)` diretamente na resposta JSON ao cliente.
Impact: Pode vazar caminho de arquivo, nome de tabela/coluna ou detalhes internos.
Recommendation: Centralizar tratamento de erro com `@app.errorhandler(Exception)` retornando mensagem genérica.

### [LOW] Magic Numbers / Strings
File: models.py:257-262 (também status strings repetidos em controllers.py:242 e models.py)
Description: Faixas de desconto e strings de status estão soltas no código sem constante nomeada.
Impact: Mudar a regra de desconto ou os status válidos exige caçar todas as ocorrências manualmente.
Recommendation: Extrair para constantes nomeadas.

## Deprecated APIs

Nenhuma API deprecated/removida do Flask 3.1.1 ou flask-cors 5.0.1 foi encontrada.

---

Total: 18 findings
