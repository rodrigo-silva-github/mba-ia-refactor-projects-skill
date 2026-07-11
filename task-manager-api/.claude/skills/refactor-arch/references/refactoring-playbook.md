# Playbook de Refatoração

Cada padrão resolve um ou mais anti-patterns do catálogo (referenciado entre colchetes). Os
exemplos usam Python/Flask, mas a transformação é a mesma em qualquer stack — adapte a sintaxe.

---

## 1. Parametrizar queries SQL [SQL Injection]

**Antes:**
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
```

**Depois:**
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
```

Aplique em toda query que incorpore valor externo — inclusive em cláusulas `LIKE` (use `?` e
passe `f"%{termo}%"` como parâmetro, nunca concatenado na string SQL) e em `INSERT`/`UPDATE`.

## 2. Extrair configuração para módulo dedicado, lida de variável de ambiente [Credenciais Hardcoded]

**Antes:**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```

**Depois:**
```python
# config/settings.py
import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

# app.py
from config import settings
app.config["SECRET_KEY"] = settings.SECRET_KEY
app.config["DEBUG"] = settings.DEBUG
```

Nunca devolva `SECRET_KEY` ou qualquer config sensível em uma resposta HTTP (ex.: endpoint de
health check) — remova o campo, não apenas mascare o valor.

## 3. Proteger/remover endpoints administrativos [Endpoint Admin sem Autenticação]

**Antes:**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    query = request.get_json().get("sql", "")
    cursor.execute(query)   # SQL arbitrário vindo do cliente
```

**Depois:** remova endpoints que executam SQL arbitrário do cliente — isso não tem versão segura
equivalente em produção. Para endpoints administrativos legítimos (ex.: reset de dados em
ambiente de teste), exija autenticação + papel de admin explicitamente:

```python
@app.route("/admin/reset-db", methods=["POST"])
@requer_autenticacao(papel="admin")
def reset_database():
    ...
```

Se o endpoint só faz sentido em desenvolvimento, gate-lo por variável de ambiente
(`if not settings.DEBUG: abort(404)`) além da autenticação.

## 4. Hash de senha [Senhas em Texto Puro]

**Antes:**
```python
cursor.execute("INSERT INTO usuarios (..., senha) VALUES (..., ?)", (..., senha))
...
cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
```

**Depois:**
```python
from werkzeug.security import generate_password_hash, check_password_hash

# ao criar
senha_hash = generate_password_hash(senha)
cursor.execute("INSERT INTO usuarios (..., senha) VALUES (..., ?)", (..., senha_hash))

# ao autenticar
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
usuario = cursor.fetchone()
if usuario and check_password_hash(usuario["senha"], senha_pura):
    ...
```

Nunca compare senha por igualdade direta de string, e nunca faça `SELECT ... WHERE senha = ?`.

## 5. Separar God Model por domínio [God Class/Module]

**Antes:** um único `models.py` com funções de `produtos`, `usuarios` e `pedidos` misturadas.

**Depois:**
```
models/
├── produto_model.py   # get_todos, get_por_id, criar, atualizar, deletar, buscar
├── usuario_model.py    # get_todos, get_por_id, criar, autenticar
└── pedido_model.py      # criar, get_por_usuario, get_todos, atualizar_status
```

Cada arquivo expõe apenas as operações do seu domínio; imports cruzados (ex.: `pedido_model`
precisa checar estoque de `produto_model`) são explícitos e diretos, não via variável global
compartilhada.

## 6. Extrair rotas do bootstrap para módulos de View/Router [Lógica no Controller/Rota, God Module]

**Antes:** `app.py` com dezenas de `app.add_url_rule(...)` e handlers administrativos inline.

**Depois:**
```python
# views/produto_routes.py
from flask import Blueprint
from controllers import produto_controller

bp = Blueprint("produtos", __name__)
bp.add_url_rule("/produtos", view_func=produto_controller.listar, methods=["GET"])
bp.add_url_rule("/produtos/<int:id>", view_func=produto_controller.buscar, methods=["GET"])

# app.py
from views.produto_routes import bp as produtos_bp
app.register_blueprint(produtos_bp)
```

## 7. Mover lógica de negócio do Controller para Model/Service [Lógica no Controller]

**Antes:** validação de categoria válida hardcoded dentro do controller (`categorias_validas =
[...]` dentro de `criar_produto`).

**Depois:** mover a lista/validação para o model ou um módulo `validators.py` reaproveitado por
criar e atualizar:

```python
# models/produto_model.py
CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")

def validar_categoria(categoria):
    return categoria in CATEGORIAS_VALIDAS
```

Controller passa a chamar `produto_model.validar_categoria(categoria)` em vez de duplicar a
lista.

## 8. Eliminar estado global mutável de conexão [Estado Global Mutável]

**Antes:**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path, check_same_thread=False)
    return db_connection
```

**Depois:** abrir/fechar conexão por request (ou usar pool), sem depender de `global` mutável
compartilhado entre threads:

```python
from flask import g

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
```

## 9. Remover/isolar efeitos colaterais simulados [Dead Code Disfarçado]

**Antes:**
```python
print("ENVIANDO EMAIL: Pedido " + str(id) + " criado")
print("ENVIANDO SMS: Seu pedido foi recebido!")
```

**Depois:** extrair para uma função de notificação explícita — real ou claramente marcada como
stub — para não se disfarçar de funcionalidade completa:

```python
def notificar_pedido_criado(pedido_id, usuario_id):
    logger.info("notificacao.pedido_criado", extra={"pedido_id": pedido_id})
    # TODO: integrar provedor real de e-mail/SMS (não implementado nesta versão)
```

## 10. Resolver N+1 com JOIN ou batch fetch [N+1 Queries]

**Antes:** para cada pedido, uma query de itens; para cada item, uma query de produto.

**Depois:**
```python
cursor.execute("""
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, prod.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos prod ON prod.id = i.produto_id
    WHERE p.usuario_id = ?
""", (usuario_id,))
```

Agrupe as linhas por `pedido.id` em memória para montar a estrutura aninhada, em uma única
consulta.

## 11. Centralizar tratamento de erro [Exposição de Detalhes Internos em Erros]

**Antes:** `except Exception as e: return jsonify({"erro": str(e)}), 500` repetido em cada
função de controller.

**Depois:**
```python
# middlewares/error_handler.py
@app.errorhandler(Exception)
def handle_exception(e):
    logger.exception("erro_nao_tratado")
    return jsonify({"erro": "Erro interno no servidor", "sucesso": False}), 500
```

Controllers deixam de ter `try/except` genérico e só tratam exceções específicas de negócio
(ex.: `ProdutoNaoEncontrado`) quando precisam de um status code diferente de 500.

## 12. Substituir `print()` por logging estruturado [print() como Logging]

**Antes:** `print("Produto criado com ID: " + str(id))`

**Depois:**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("produto_criado", extra={"produto_id": id})
```

## 13. Nomear magic numbers/strings [Magic Numbers/Strings]

**Antes:**
```python
if faturamento > 10000:
    desconto = faturamento * 0.1
elif faturamento > 5000:
    desconto = faturamento * 0.05
```

**Depois:**
```python
FAIXAS_DESCONTO = (
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
)

def calcular_desconto(faturamento):
    for limite, percentual in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * percentual
    return 0
```

Aplique o mesmo princípio a strings de status repetidas (`"pendente"`, `"aprovado"`, ...): extraia
para uma constante/enum única importada por todos os módulos que a usam.

---

## Como escolher a transformação certa

1. Localize o achado no relatório da Fase 2 pelo nome do anti-pattern.
2. Aplique o padrão correspondente deste playbook adaptado à sintaxe real do projeto.
3. Se um achado não tiver padrão exato aqui, aplique o princípio geral mais próximo (extrair,
   parametrizar, centralizar, nomear) e documente a decisão no resumo da Fase 3.
