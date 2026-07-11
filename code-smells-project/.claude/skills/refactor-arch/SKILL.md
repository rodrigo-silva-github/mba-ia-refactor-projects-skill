---
name: refactor-arch
description: Analisa qualquer projeto de backend (agnóstico de linguagem/framework), detecta code smells, falhas de segurança e violações de MVC/SOLID, gera um relatório de auditoria priorizado por severidade e refatora o projeto para o padrão MVC após confirmação do usuário. Use quando pedirem para "auditar esta base de código", "refatorar para MVC", "encontrar code smells" ou quando o comando /refactor-arch for invocado.
---

# Refactor Architecture

## Objetivo

Analisar um projeto existente, identificar linguagem, framework e arquitetura, detectar code
smells e anti-patterns, gerar um relatório objetivo, aplicar refatorações preservando o
comportamento da aplicação e validar o resultado.

A skill deve ser **agnóstica de tecnologia**: os mesmos três passos abaixo se aplicam a
Python/Flask, Node/Express, ou qualquer outro backend. Não assuma nomes de arquivo, apenas
os sinais descritos nos arquivos de referência.

## Conhecimento de apoio (leia antes de agir)

Antes de iniciar a Fase 1, carregue os arquivos abaixo — eles contêm o conhecimento de domínio
que este SKILL.md pressupõe. Não duplique esse conteúdo aqui; consulte-o em cada fase:

- `references/project-analysis.md` — heurísticas de detecção de stack e arquitetura (Fase 1)
- `references/anti-patterns-catalog.md` — catálogo de anti-patterns e severidades (Fase 2)
- `references/report-template.md` — formato exato do relatório de auditoria (Fase 2)
- `references/mvc-guidelines.md` — regras da arquitetura MVC alvo (Fase 3)
- `references/refactoring-playbook.md` — padrões de transformação com exemplos antes/depois (Fase 3)

## Escala de severidade (oficial, não alterar)

- **CRITICAL** — falhas graves de arquitetura ou segurança que impedem funcionamento correto,
  expõem dados sensíveis (credenciais hardcoded, SQL Injection) ou violam completamente a
  separação de responsabilidades (God Class com banco, lógica e roteamento juntos).
- **HIGH** — fortes violações de MVC/SOLID que dificultam manutenção e testes (lógica de
  negócio pesada em Controllers, acoplamento forte sem DI, estado global mutável).
- **MEDIUM** — padronização, duplicação de código, gargalos de performance moderada (N+1,
  middlewares mal usados, validação ausente nas rotas).
- **LOW** — legibilidade, nomenclatura ruim, magic numbers.

## Fluxo — 3 fases sequenciais

Execute as fases em ordem. **Nunca pule a Fase 2 nem module arquivos sem a confirmação
explícita do usuário ao final dela.**

### Fase 1 — Análise

1. Percorra o projeto e aplique as heurísticas de `references/project-analysis.md` para
   identificar: linguagem, framework, gerenciador de dependências, banco de dados, domínio da
   aplicação e arquitetura predominante (monólito, MVC parcial, camadas, etc.).
2. Conte os arquivos-fonte relevantes analisados (ignore deps, venv, node_modules, .git).
3. Imprima um resumo neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework + versão, se identificável>
Dependencies:  <libs relevantes>
Domain:        <domínio de negócio inferido>
Architecture:  <arquitetura encontrada + justificativa curta>
Source files:  <N> files analyzed
DB tables:     <tabelas/coleções identificadas, se houver>
================================
```

Não altere a arquitetura sem justificativa — o objetivo aqui é apenas descrever o estado atual.

### Fase 2 — Auditoria

1. Cruze o código contra `references/anti-patterns-catalog.md`, anti-pattern por anti-pattern.
   Não invente categorias fora do catálogo; se encontrar algo fora dele, classifique-o pelo
   anti-pattern mais próximo e explique a analogia.
2. Verifique também uso de APIs/dependências deprecated (seção específica do catálogo) e
   recomende o equivalente moderno quando aplicável.
3. Para cada achado, colete: tipo do smell, arquivo, linha (ou intervalo de linhas) exata,
   severidade, descrição, impacto e recomendação.
4. Gere o relatório seguindo **exatamente** `references/report-template.md`, com os achados
   ordenados por severidade (CRITICAL → HIGH → MEDIUM → LOW).
5. Ao final do relatório, **pare e peça confirmação explícita** antes de tocar em qualquer
   arquivo:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Se a resposta for negativa, encerre sem modificar nada. Se o usuário pedir ajustes no
relatório, aplique-os e peça confirmação novamente.

### Fase 3 — Refatoração

Só execute esta fase após confirmação explícita na Fase 2.

1. Use `references/mvc-guidelines.md` para definir a estrutura de destino (Models, Views/Routes,
   Controllers, config, middlewares, entry point) adaptada à linguagem identificada na Fase 1.
2. Para cada achado do relatório, aplique a transformação correspondente descrita em
   `references/refactoring-playbook.md`. Preserve o comportamento observável da aplicação —
   mesmos endpoints, mesmos contratos de request/response.
3. Não reescreva partes saudáveis do sistema e não introduza abstrações além do necessário
   para resolver os achados. Preserve convenções de nomenclatura já usadas no projeto
   (idioma, estilo de nomes, etc.).
4. Se o projeto já tiver alguma separação de camadas, não recrie do zero — mova/ajuste o que
   for necessário para fechar os gaps identificados na auditoria.
5. Ao final, valide:
   - A aplicação inicia sem erros (boot).
   - Os endpoints originais continuam respondendo com os mesmos contratos.
   - Os anti-patterns CRITICAL/HIGH do relatório foram eliminados.

   Se alguma validação não for possível no ambiente atual (ex.: sem servidor de banco
   disponível), **informe isso explicitamente** no resumo final em vez de assumir sucesso.
6. Imprima um resumo final:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios resultante>

## Validation
  <✓ ou ✗ para cada item validado, com detalhe se ✗>
================================
```

## Regras gerais

- Preserve comportamento sempre que a refatoração não exigir explicitamente uma mudança
  (ex.: corrigir SQL Injection muda a implementação, não o contrato da API).
- Faça apenas as mudanças necessárias para resolver os achados da Fase 2 e atingir a
  estrutura MVC descrita em `references/mvc-guidelines.md`.
- Esta skill não usa múltiplos agentes, métricas avançadas ou mecanismos de coordenação —
  execute as 3 fases você mesmo, de forma sequencial e determinística.
