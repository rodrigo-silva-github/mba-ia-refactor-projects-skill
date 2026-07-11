# Template do Relatório de Auditoria (Fase 2)

Use exatamente esta estrutura. Substitua os campos entre `<...>`. Não adicione seções extras;
não remova nenhuma das seções abaixo.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório do projeto>
Stack:   <linguagem + framework>
Files:   <N> analyzed | ~<N> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [<SEVERIDADE>] <Nome do anti-pattern>
File: <arquivo>:<linha ou intervalo>
Description: <o que foi encontrado, de forma concreta e específica>
Impact: <consequência real se não for corrigido>
Recommendation: <ação de correção, em uma frase>

<... repetir o bloco acima para cada finding, ordenado por severidade CRITICAL → HIGH → MEDIUM → LOW ...>

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Regras de preenchimento

- **Ordenação:** findings sempre em ordem decrescente de severidade. Dentro da mesma
  severidade, ordene pela ordem em que o anti-pattern aparece no código-fonte (arquivo, depois
  linha).
- **File/linha:** sempre aponte um arquivo e linha (ou intervalo) reais e verificáveis. Nunca
  escreva "vários arquivos" sem listar pelo menos os principais.
- **Description:** descreva o padrão encontrado, não uma opinião genérica. Prefira
  `"Query SQL montada por concatenação de string com dado de entrada do usuário"` a
  `"código inseguro"`.
- **Impact:** conecte o achado a uma consequência concreta (segurança, correção, performance,
  manutenibilidade) — evite frases vagas como "má prática".
- **Recommendation:** uma ação executável, idealmente citando o padrão de
  `references/refactoring-playbook.md` que resolve o achado.
- **Summary:** os números devem bater exatamente com a contagem de findings listados abaixo.
- **Total:** deve ser igual à soma dos valores do Summary.
- Nunca omita o prompt de confirmação final — é obrigatório em toda execução da Fase 2.
