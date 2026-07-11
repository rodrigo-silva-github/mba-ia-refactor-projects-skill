# Catálogo de Anti-patterns

Cada entrada traz: sinais de detecção concretos (o que procurar no código, não "código ruim"),
severidade padrão e por que ela importa. A severidade padrão pode subir/descer um nível conforme
o contexto (ex.: SQL Injection num endpoint sem nenhuma autenticação é sempre CRITICAL; em um
endpoint interno já protegido por outra camada pode justificar HIGH — explique o motivo no
relatório sempre que desviar do padrão).

Este catálogo é agnóstico de linguagem: os sinais de detecção descrevem o *padrão*, com exemplos
em Python/Flask e Node/Express lado a lado quando ajuda.

---

## 1. SQL Injection (CRITICAL)

**Sinais de detecção:** montagem de query por concatenação/f-string/template string com valor
vindo de request, path param ou body, em vez de parâmetros bindados.

- Python: `cursor.execute("... " + variavel)`, `f"... {variavel}"`, `"... %s" % variavel` fora de
  `execute(query, params)`.
- Node: `` `SELECT * FROM x WHERE id = ${id}` `` passado direto para `db.query(...)`.

**Por quê:** permite leitura/alteração/exclusão arbitrária de dados, bypass de autenticação
(ex.: injetar `' OR '1'='1` num `WHERE email = '...' AND senha = '...'`).

## 2. Credenciais e Segredos Hardcoded (CRITICAL)

**Sinais de detecção:** `SECRET_KEY`, senha, API key, token ou string de conexão literal no
código-fonte (`app.config["SECRET_KEY"] = "..."`, `password = "admin123"`), especialmente se
também retornada em alguma resposta HTTP (endpoint de debug/health que ecoa config interna).

**Por quê:** qualquer pessoa com acesso ao repositório (ou à resposta HTTP, se vazado) compromete
sessões, assinatura de tokens ou acesso a serviços externos.

## 3. Endpoint Administrativo sem Autenticação (CRITICAL)

**Sinais de detecção:** rota que executa ação privilegiada (reset de banco, execução de SQL
arbitrário, exclusão em massa, alteração de papel de usuário) sem nenhum middleware/decorator de
autenticação ou verificação de papel antes de executar a ação.

**Por quê:** é uma porta aberta completa para qualquer visitante não autenticado destruir ou
exfiltrar dados — na prática, pior que a maioria das vulnerabilidades de aplicação porque não
exige nem exploração, apenas uma requisição HTTP direta.

## 4. Senhas em Texto Puro (CRITICAL)

**Sinais de detecção:** senha armazenada e comparada como string simples (`INSERT ... VALUES
(senha)` sem hash; `if senha == usuario["senha"]`), sem uso de `bcrypt`/`werkzeug.security`/
`argon2`/`scrypt`.

**Por quê:** um vazamento de banco expõe todas as senhas em claro, permitindo reuso em outros
serviços (credential stuffing).

## 5. God Class / God Module (CRITICAL/HIGH)

**Sinais de detecção:** um único arquivo concentra queries SQL, regra de negócio, validação e
formatação de resposta para múltiplos domínios não relacionados (ex.: produtos + usuários +
pedidos no mesmo `models.py`); ou um arquivo de bootstrap que mistura roteamento, acesso a dados e
lógica administrativa.

**Severidade:** CRITICAL quando o arquivo também mistura camada de rota/infra (roteamento + banco
+ lógica no mesmo lugar); HIGH quando é "apenas" múltiplos domínios de negócio misturados dentro
da mesma camada (ex.: só models, sem rota).

**Por quê:** impossível testar em isolamento; qualquer mudança em um domínio arrisca quebrar
outro; viola Single Responsibility.

## 6. Lógica de Negócio no Controller/Rota (HIGH)

**Sinais de detecção:** validação de regra de negócio, cálculo, orquestração de múltiplos passos
ou decisão de fluxo dentro da função que atende a rota HTTP, em vez de delegada a uma camada de
serviço/model.

**Por quê:** acopla regra de negócio ao transporte HTTP, dificultando reuso e testes sem subir um
servidor.

## 7. Estado Global Mutável (HIGH)

**Sinais de detecção:** variável de módulo (`global`) guardando conexão de banco, cache ou sessão
compartilhada entre requisições sem controle de concorrência/ciclo de vida (ex.: `db_connection =
None` no escopo do módulo, reaproveitada via `global` a cada request).

**Por quê:** condições de corrida sob concorrência, dificuldade de testar com estado limpo,
acoplamento implícito entre chamadas que deveriam ser independentes.

## 8. Efeito Colateral Simulado / Dead Code Disfarçado (MEDIUM)

**Sinais de detecção:** código que aparenta implementar uma integração (`print("ENVIANDO EMAIL:
...")`, `# TODO enviar SMS`) mas apenas loga no console, sem chamar nenhum serviço real — e o
restante do fluxo trata isso como se a notificação tivesse ocorrido.

**Por quê:** cria uma falsa sensação de funcionalidade completa; qualquer código ou teste que
dependa desse "efeito" está testando uma ilusão.

## 9. N+1 Queries (MEDIUM)

**Sinais de detecção:** loop `for` sobre uma lista de resultados que, a cada iteração, dispara uma
nova query para buscar dados relacionados (ex.: buscar pedidos e, para cada pedido, buscar seus
itens, e para cada item, buscar o nome do produto em queries separadas).

**Por quê:** número de queries cresce linearmente com o tamanho do resultado — degradação de
performance severa em produção, mesmo que passe despercebido com poucos dados em dev.

## 10. Duplicação de Código (MEDIUM)

**Sinais de detecção:** blocos de validação, mapeamento de linha de banco para dicionário/objeto,
ou lógica de resposta repetidos quase identicamente em múltiplas funções (ex.: a mesma sequência
de `if campo not in dados` copiada entre "criar" e "atualizar"; o mesmo mapeamento de `row` para
dict repetido em cada função de leitura).

**Por quê:** correção de bug precisa ser replicada manualmente em todos os pontos duplicados —
alto risco de divergência silenciosa (Shotgun Surgery).

## 11. Modo Debug/Config Insegura em "Produção" (MEDIUM)

**Sinais de detecção:** `debug=True` no `app.run(...)` ou equivalente, `DEBUG` habilitado sem
depender de variável de ambiente, CORS liberado para `*` sem restrição, sem diferenciação entre
ambiente de desenvolvimento e produção.

**Por quê:** debugger interativo exposto publicamente pode permitir execução remota de código;
configuração deveria vir de variáveis de ambiente por ambiente.

## 12. Uso de `print()` como Logging (LOW)

**Sinais de detecção:** `print(...)` para registrar erros, eventos de negócio ou depuração, em vez
de um logger configurável (módulo `logging` em Python, `winston`/`pino` em Node).

**Por quê:** sem níveis de log, sem destino configurável (arquivo/observabilidade), sem
correlação — inutilizável em produção.

## 13. Magic Numbers / Strings (LOW)

**Sinais de detecção:** literais numéricos ou strings de status/categoria espalhados pelo código
sem constante nomeada (ex.: limiares de desconto `10000`/`0.1` soltos numa função; strings de
status `"pendente"`/`"aprovado"` repetidas em múltiplos arquivos sem enum/constante central).

**Por quê:** significado do valor não é óbvio para quem lê; mudar a regra exige caçar todas as
ocorrências manualmente.

## 14. Exposição de Detalhes Internos em Erros (LOW)

**Sinais de detecção:** resposta HTTP de erro que devolve `str(exception)` diretamente ao cliente,
podendo vazar caminho de arquivo, nome de tabela/coluna ou stack trace.

**Por quê:** ajuda um atacante a mapear a aplicação; mensagens de erro para o cliente deveriam ser
genéricas, com o detalhe completo apenas no log do servidor.

---

## Detecção de APIs Deprecated

Sempre que analisar dependências, cruze versão declarada/instalada contra APIs/métodos marcados
como deprecated ou removidos pela própria biblioteca/framework, por exemplo:

- Flask/Werkzeug: uso de `flask.Markup` (removido, use `markupsafe.Markup`), `app.run()` com
  opções de um Werkzeug muito antigo, `before_first_request` (removido no Flask 2.3+).
- Express: uso de `body-parser` standalone quando a versão do Express já embute `express.json()`
  nativamente; middlewares de callback `(err, req, res, next)` legados sem tratamento.
- Bibliotecas de hash inseguras/obsoletas: `md5`/`sha1` para senha (trate como CRITICAL — combina
  com o item 4 deste catálogo).
- Qualquer pacote no manifesto marcado como `deprecated` pelo próprio gerenciador (ex.: aviso do
  `npm install`) ou sem atualização de segurança há muitas versões majors.

Ao encontrar uma API deprecated, classifique a severidade pelo impacto real (ex.: método removido
que quebra o boot é HIGH/CRITICAL; método apenas com aviso de depreciação sem impacto funcional é
LOW/MEDIUM) e sempre recomende o equivalente moderno explicitamente.
