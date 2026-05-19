# Sistema UCEBOL — Trabajos de Investigación

Gera trabalhos académicos da UCEBOL a partir de modelos oficiais, com fontes científicas reais (PubMed + Semantic Scholar).

## Como usar

```
/trabalho-uce
```
ou em linguagem natural: _"quero gerar um ensaio básico sobre diabetes tipo 2"_.

Para input estruturado, ver `FORMULARIO.md` (uso próprio) ou `FORMULARIO_CLIENTES.md` (WhatsApp).

## Modelos suportados

| id | nome | ano | palavras |
|---|---|---|---|
| `ensayo_basico` | Ensayo Académico (INV-00) | 1º | 400-650 |
| `perfil_basico` | Perfil de Investigación Básico (INV-01) | 2º | 550-850 |
| `perfil_intermedio` | Perfil de Investigación Intermedio (INV-02) | 3º | 1100-1700 |
| `articulo_original` | Artículo Original (INV-04) | avançado | 2500-4500 |

## Arquitetura

```
sistema/
├── reglas_globales.md        regras transversais (sempre lidas)
├── lista_negra.md            marcadores de IA (fonte única, lida pelos 2 agentes)
├── pesquisa/apis.md          protocolo PubMed + Semantic Scholar
├── modelos/<id>/             schema.yaml + template.md por modelo
├── trabajos_generados/       output (1 pasta por trabalho) + INDEX.md
├── FORMULARIO.md             input próprio
└── FORMULARIO_CLIENTES.md    input via WhatsApp

.claude/
├── skills/trabalho-uce/      workflow principal (SKILL.md)
└── agents/
    ├── redactor-cientifico.md   redige cada secção
    └── revisor-humanizador.md   audita cada secção
```

## Ordem de leitura para gerar um trabalho

1. `.claude/skills/trabalho-uce/SKILL.md` — workflow.
2. `sistema/reglas_globales.md` — regras inegociáveis.
3. `sistema/modelos/<modelo>/schema.yaml` + `template.md` — só o modelo escolhido.
4. `sistema/pesquisa/apis.md` — quando for buscar fontes.

Os agentes leem `sistema/lista_negra.md` por sua conta.

## Princípios não-negociáveis

1. **Nunca alucinar referências.** Sem ≥ `citas_min` reais → parar e avisar.
2. **Espanhol académico** sempre, mesmo que o utilizador escreva em português.
3. **Parafrasear sempre.** Anti-plágio é critério de avaliação real.
4. **Coerência** título ↔ objetivo ↔ pergunta ↔ hipótese.
5. **Pedir o que falta, não inventar.**

## Nomenclatura de pastas de output

```
<ano>-<gestao>__<asignatura-slug>__<modelo>__<tema-slug>/
```

`<gestao>`: usar `G1` ou `G2`. Não misturar com `GestionI`, `2026`, `1`, etc.
