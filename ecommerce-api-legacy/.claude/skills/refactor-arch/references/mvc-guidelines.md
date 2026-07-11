# Guidelines de Arquitetura MVC Alvo

Estas regras definem a estrutura de destino da Fase 3. Adapte os nomes de pasta à convenção da
linguagem, mas mantenha as responsabilidades abaixo — que é o que realmente importa, não o nome
do diretório.

## Camadas e responsabilidades

### Models

- Única camada que sabe falar com o banco de dados (SQL/ORM). Nenhuma outra camada deve conter
  `execute`, `query`, `cursor` ou equivalente.
- Toda query com dado de entrada do usuário deve usar parâmetros bindados, nunca concatenação.
- Um model por domínio/entidade (ex.: `produto_model.py`, `usuario_model.py`,
  `pedido_model.py`), não um arquivo único cobrindo tudo.
- Pode conter validação de invariante de dado (ex.: "estoque não pode ficar negativo"), mas não
  orquestração de múltiplos domínios — isso é responsabilidade do Controller.
- Retorna estruturas de dados simples (dict/dataclass/objeto de domínio), nunca uma `Response`
  HTTP.

### Views / Routes

- Apenas declaração de rotas e mapeamento HTTP → Controller (método, path, parâmetros).
- Não deve conter lógica de negócio, acesso a banco ou formatação de regra — só roteamento e,
  no máximo, parsing/validação de shape do payload (tipo/presença de campos, não regra de
  negócio).
- Agrupe rotas por domínio (blueprint/router por recurso), não tudo num único arquivo de bootstrap.

### Controllers

- Recebem a requisição já roteada, chamam o(s) Model(s)/Service(s) necessários, aplicam a regra
  de orquestração do caso de uso, e devolvem a resposta HTTP (status code + payload).
- Não devem conter SQL nem strings de query.
- Validação de regra de negócio pesada ou reaproveitada entre casos de uso deve ser extraída para
  uma função/módulo auxiliar (validators/services), não duplicada entre Controllers.

### Config

- Toda credencial, chave secreta, string de conexão ou flag de ambiente (debug, CORS) vem de
  variável de ambiente (`os.environ`/`process.env`), nunca literal no código.
- Um módulo único de configuração (`config/settings.py`, `config/index.js`) centraliza a leitura
  dessas variáveis com valores default seguros para desenvolvimento local.

### Middlewares / Error Handling

- Tratamento de exceção centralizado (error handler global), não um `try/except`/`try/catch`
  genérico repetido em cada Controller devolvendo `str(exception)` ao cliente.
- Mensagens de erro para o cliente são genéricas e estáveis; o detalhe completo vai para o log do
  servidor.
- Endpoints administrativos/privilegiados passam por um middleware de autenticação/autorização
  explícito antes de chegar ao Controller.

### Entry point

- Um único arquivo de composição (`app.py`, `server.js`) que: cria a aplicação, registra
  middlewares, registra as rotas dos módulos de View, e sobe o servidor. Não deve conter lógica
  de negócio nem acesso direto a banco.

## Layout de referência (adapte o nome da pasta raiz ao projeto)

```
src/
├── config/
│   └── settings.<ext>          # variáveis de ambiente, nada hardcoded
├── models/
│   └── <entidade>_model.<ext>  # um arquivo por domínio, só acesso a dado
├── views/  (ou routes/)
│   └── <entidade>_routes.<ext> # só declaração de rota → controller
├── controllers/
│   └── <entidade>_controller.<ext>  # orquestração do caso de uso
├── middlewares/
│   └── error_handler.<ext>     # tratamento de erro centralizado
└── app.<ext>                   # composition root / entry point
```

## Quando NÃO reestruturar

- Se uma camada já existe e já respeita a responsabilidade acima, não recrie — apenas corrija os
  achados específicos dentro dela.
- Não separe um domínio em múltiplos arquivos se ele for trivial e não tiver nenhum achado
  associado — a divisão deve resolver um problema real do relatório, não seguir o layout por
  dogma.
- Preserve nomes, idioma (ex.: português nos identificadores) e convenções de estilo já usadas no
  projeto original.
