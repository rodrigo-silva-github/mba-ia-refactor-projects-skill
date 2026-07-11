# Análise de Projeto — Heurísticas de Detecção

Use estas heurísticas na Fase 1. O objetivo é descrever o estado atual do projeto, não julgá-lo
ainda (isso é Fase 2).

## 1. Linguagem

Detecte pela extensão dominante dos arquivos-fonte e por arquivos de manifesto:

| Sinal | Linguagem |
|---|---|
| `requirements.txt`, `Pipfile`, `pyproject.toml`, arquivos `.py` | Python |
| `package.json`, arquivos `.js`/`.mjs`/`.cjs` | Node.js / JavaScript |
| `package.json` + `.ts`, `tsconfig.json` | TypeScript |
| `go.mod`, arquivos `.go` | Go |
| `pom.xml`/`build.gradle`, arquivos `.java` | Java |
| `Gemfile`, arquivos `.rb` | Ruby |
| `composer.json`, arquivos `.php` | PHP |

Ignore diretórios de dependências/build (`venv`, `.venv`, `__pycache__`, `node_modules`, `dist`,
`build`, `.git`) ao contar arquivos-fonte.

## 2. Framework

Cruze o manifesto de dependências com o código de bootstrap (arquivo que sobe o servidor):

- Python: procure `import flask` / `Flask(__name__)` → Flask; `django` → Django;
  `fastapi` → FastAPI. Extraia a versão do `requirements.txt`/`pyproject.toml`.
- Node.js: procure `require('express')`/`import express` → Express; `fastify`, `koa`, `nestjs`
  de forma análoga. Extraia a versão de `package.json` (`dependencies`).
- Confirme a versão real instalada (não apenas a declarada) se houver lockfile
  (`package-lock.json`, `poetry.lock`) — declarações podem usar ranges (`^`, `~`).

## 3. Gerenciador de dependências

Identifique pelo arquivo de manifesto presente: `pip`/`requirements.txt`, `poetry`/`pyproject.toml`,
`npm`/`package-lock.json`, `yarn`/`yarn.lock`, `pnpm`/`pnpm-lock.yaml`, etc.

## 4. Banco de dados

Procure, em ordem de confiabilidade:

1. Import/require de driver: `sqlite3`, `psycopg2`/`asyncpg` (Postgres), `pymysql`/`mysql`,
   `pymongo` (Mongo), `mongoose`, `sequelize`, `sqlalchemy`, `prisma`.
2. String de conexão ou caminho de arquivo (`*.db`, `DATABASE_URL`, `mongodb://`, `postgres://`).
3. Comandos `CREATE TABLE`/schema para inferir as entidades e nomes de tabela/coleção — liste-os
   no resumo da Fase 1 (`DB tables:`).

Se não houver banco (ex.: API stateless ou dados em memória), declare isso explicitamente em vez
de omitir o campo.

## 5. Domínio da aplicação

Infira o domínio de negócio a partir de:

- Nomes de rotas/endpoints (ex.: `/produtos`, `/pedidos`, `/cursos`, `/matriculas`).
- Nomes de tabelas/entidades e seus campos.
- Comentários, docstrings ou README do projeto-alvo (não deste arquivo).

Descreva o domínio em uma frase curta e concreta (ex.: "E-commerce API — produtos, pedidos,
usuários"), não em termos genéricos como "API REST".

## 6. Arquitetura predominante

Classifique com base na organização real de diretórios/módulos, não no que seria ideal:

| Sinal observado | Classificação |
|---|---|
| Poucos arquivos na raiz, sem pastas por camada, tudo em 1-4 módulos | Monolito não estruturado |
| Pastas `models/`, `routes/`, `controllers/`/`services/` já existem, mas com lógica vazando entre elas | MVC parcial / organização incompleta |
| Separação clara de Model / View-Route / Controller, com responsabilidades respeitadas | MVC já aplicado (validar se está correto, não recriar) |
| Camadas adicionais de domínio/aplicação/infra bem isoladas | Arquitetura em camadas / Clean-ish |

Para chegar à classificação, verifique se cada arquivo faz **apenas** o que seu nome/pasta sugere.
Um projeto com pastas `models/` e `routes/` mas que tem SQL cru dentro de `routes/` ainda conta
como "MVC parcial", não como "MVC aplicado" — isso deve ser registrado como achado na Fase 2, não
disfarçado na Fase 1.

## 7. Contagem de arquivos-fonte

Conte apenas arquivos que contêm código da aplicação (exclua testes de terceiros, migrations
geradas, arquivos de configuração de editor, lockfiles). Informe esse número no resumo — ele deve
bater com a realidade do projeto (não arredonde para impressionar).
