# Skill: trabalho-uce

Workflow principal para gerar trabalhos académicos UCEBOL com fontes científicas reais.

## Quando activar

- Utilizador digita `/trabalho-uce`
- Utilizador cola um formulário YAML preenchido
- Utilizador pede em linguagem natural um trabalho UCEBOL (ensayo, perfil, artículo)

---

## FASE 0 — Leitura obrigatória antes de qualquer acção

Ler nesta ordem (sem saltar):

1. `PROTOTIPO - Copia/sistema/reglas_globales.md`
2. `PROTOTIPO - Copia/sistema/lista_negra.md`
3. `PROTOTIPO - Copia/sistema/modelos/<modelo>/schema.yaml`
4. `PROTOTIPO - Copia/sistema/modelos/<modelo>/template.md`
5. `PROTOTIPO - Copia/sistema/pesquisa/apis.md` (quando chegar à fase de fontes)

Se o modelo ainda não for conhecido, ler os 4 schemas (ensayo_basico, perfil_basico, perfil_intermedio, articulo_original) e depois perguntar ao utilizador.

---

## FASE 1 — Recepção e validação do formulário

### 1.1 Extrair campos do input do utilizador

Aceitar qualquer formato:
- YAML colado (como em `FORMULARIO.md`)
- Linguagem natural: _"quero um perfil_basico sobre diabetes tipo 2, asignatura Medicina Interna, estudantes de UCEBOL em Santa Cruz"_
- Mix (YAML parcial + texto)

### 1.2 Identificar modelo

| Input do utilizador | Modelo |
|---|---|
| "ensayo", "essay", "INV-00", "1º ano" | `ensayo_basico` |
| "perfil básico", "INV-01", "2º ano" | `perfil_basico` |
| "perfil intermedio", "INV-02", "3º ano" | `perfil_intermedio` |
| "artículo", "INV-04" | `articulo_original` |

Se ambíguo → perguntar.

### 1.3 Verificar campos obrigatórios (do schema.yaml do modelo)

Para cada `header_field` com `requerido: true`:
- Se ausente e sem `default` → perguntar explicitamente, **num único bloco de perguntas**, não uma a uma.
- Se ausente mas tem `default` → usar o default sem perguntar.
- **Nunca inventar** um campo obrigatório em falta.

Campos especiais:
- `carrera` → sempre "Medicina", nunca perguntar.
- `titulo` → se em branco, sugerir com base no tema após o utilizador confirmar o objetivo.
- `incluir_hipotesis` (perfil_intermedio) → derivar automaticamente: `true` se `tipo_estudio == "analítico"`.

### 1.4 Construir o cabeçalho interno

```yaml
# cabecero interno (não exibir ao utilizador, usar internamente)
modelo: <id>
asignatura: <valor>
ano: <valor>
gestion: <G1|G2>          # derivar de "Gestión I" → G1, "Gestión II" → G2
autor: <valor ou "Estudiante">
titulo: <MAIÚSCULAS, ≤21 palavras>
tema: <slug legível>
slug_pasta: <ano>-<gestion>__<asignatura-slug>__<modelo>__<tema-slug>
prompt_autor: <texto ou null>
```

---

## FASE 2 — Pesquisa de fontes científicas

### 2.1 Planear queries por secção

Para cada secção com `citas_min > 0`, definir 1-2 queries específicas ao tema.

Exemplo para tema "agresividad reactiva en adolescentes bolivianos":
- Introducción: `"reactive aggression" adolescents Bolivia Latin America`
- Desarrollo: `"reactive aggression" burnout students`

### 2.2 Executar pesquisa (por ordem de prioridade)

Seguir o protocolo em `PROTOTIPO - Copia/sistema/pesquisa/apis.md`:

1. **PubMed ESearch** → obter PMIDs
2. **PubMed ESummary** → obter metadados completos
3. Se < 3 resultados úteis → **Semantic Scholar**
4. Se ainda insuficiente → **WebFetch scienceOS/Consensus**

Para cada paper retornado, verificar obrigatoriamente:
- [ ] Tem DOI ou PMID real?
- [ ] Título é coerente com o que precisamos citar?
- [ ] Ano dentro da janela (últimos 3 anos salvo excepções clássicas)?
- [ ] Autores existem (nome retornado pela API, não inventado)?

### 2.3 Apresentar lista de fontes ao utilizador

Mostrar a lista de fontes encontradas em formato legível:

```
Fontes encontradas (aguardar aprovação antes de redigir):

[1] Autor AB, Autor CD. Título. Revista. Ano;Vol(N):Páginas. PMID/DOI.
[2] ...
...

✅ Aprovadas para usar. Posso acrescentar mais fontes ou continuar com estas?
```

**Esperar confirmação do utilizador antes de avançar para a Fase 3.**

Se o utilizador pedir mais fontes → repetir 2.2 com queries diferentes. Se pedir remover alguma → remover.

### 2.4 Salvar cache de fontes

Criar `PROTOTIPO - Copia/sistema/trabajos_generados/<slug>/fontes.json`:
```json
{
  "aprovadas": [
    {
      "n": 1,
      "autores": "...",
      "titulo": "...",
      "revista": "...",
      "ano": 2024,
      "vol": "...",
      "num": "...",
      "paginas": "...",
      "pmid": "...",
      "doi": "..."
    }
  ],
  "queries_usadas": ["..."],
  "timestamp": "YYYY-MM-DD"
}
```

---

## FASE 3 — Geração secção a secção

### 3.1 Ordem de geração

Seguir a ordem das `secciones` no schema. Excepções:
- `resumen` (articulo_original) → **sempre gerar por último**, depois de todas as outras.
- `referencias` → gerar ao final, compilando todas as citas usadas em ordem de aparição.

### 3.2 Por cada secção

**a) Chamar sub-agente `redactor-cientifico`** com:
- Conteúdo da secção do schema (instrucciones, palabras, citas_min/max)
- Fontes aprovadas disponíveis para essa secção
- Regras globais
- `prompt_autor` (se existir)
- Texto já gerado nas secções anteriores (para coerência interna)

**b) Chamar sub-agente `revisor-humanizador`** com:
- Texto gerado pelo redactor
- Lista negra (`lista_negra.md`)
- Contagem de palavras esperada

**c) Se o revisor devolver `APROVADO`** → aceitar o texto e avançar.

**d) Se o revisor devolver `REJEITADO`** com problemas:
- Enviar de volta ao redactor com as correcções especificadas.
- Máx. **2 iterações de reescrita** por secção.
- Se ao fim de 2 iterações ainda houver problemas críticos → parar e informar o utilizador com o diagnóstico.

### 3.3 Regras de coerência durante a geração

A cada nova secção verificar:
- Título ↔ objetivo ↔ pregunta ↔ hipótesis são semanticamente equivalentes?
- As citas usadas existem na lista de fontes aprovadas?
- Nenhum placeholder `{{...}}` ou `<!-- GENERAR: ... -->` ficou por substituir?

---

## FASE 4 — Montagem e validação final

### 4.1 Montar o ficheiro completo

Estrutura do `trabajo.md`:

```markdown
---
# Carátula
**UNIVERSIDAD CRISTIANA DE BOLIVIA — UCEBOL**
**Carrera:** Medicina
**Asignatura:** <asignatura>
**<Gestión I / Gestión II> — <Año>**
**Tema:** <titulo>
**Autor:** <autor>
**Docente:** <docente ou em branco>
---

# <TÍTULO EM MAIÚSCULAS>

## <SECCIÓN 1>
<conteúdo>

## <SECCIÓN 2>
<conteúdo>

...

## REFERENCIAS BIBLIOGRÁFICAS
1. Autor AB, Autor CD, et al. Título. Abrev Rev. Año;Vol(N):pp. doi: ...
2. ...
```

### 4.2 Checklist de validação final

Executar todos os itens antes de entregar:

- [ ] Placeholders `{{...}}` substituídos (zero restantes)
- [ ] Nenhum `<!-- GENERAR: ... -->` sem conteúdo
- [ ] Toda cita `(N)` tem entrada em Referências
- [ ] Toda entrada de Referências aparece citada ao menos uma vez
- [ ] Referências verificadas (DOI/PMID real — não inventado)
- [ ] Palavras dentro do rango por secção (±10% tolerância)
- [ ] Total palavras dentro de `total_palavras_objetivo`
- [ ] Coerência: título ↔ objetivo ↔ pregunta ↔ hipótesis
- [ ] Sem opinião do autor onde `incluir_opinion_autor: false`
- [ ] Anti-plágio: todo parafraseado
- [ ] Cada secção passou por redactor + revisor (registado em meta.yaml)
- [ ] Zero matches da lista negra
- [ ] Zero em-dashes (U+2014 `—`)

Se algum item falhar → corrigir antes de entregar. Se impossível corrigir automaticamente → informar utilizador.

### 4.3 Criar meta.yaml

```yaml
titulo: <TÍTULO>
asignatura: <asignatura>
carrera: Medicina
ano: "<ano>"
gestion: <G1|G2>
modelo: <id>
codigo_uce: <INV-0X>
fecha_generacion: "<YYYY-MM-DD>"

secciones:
  <id_seccion>:
    palabras: <N>
    citas: [1, 2, ...]
    estado: APROBADO | APROBADO_CON_CORRECCIONES
    correcciones:
      - tipo: <alucinacion|tangencia|lista_negra|conteo> — <descripción breve>

total_palabras_contenido: <N>
rango_objetivo: [<min>, <max>]
estado_global: APROBADO | PENDIENTE
```

### 4.4 Salvar output

Criar pasta: `PROTOTIPO - Copia/sistema/trabajos_generados/<slug_pasta>/`

Ficheiros a criar:
- `trabajo.md` — trabalho completo
- `meta.yaml` — metadados e log de qualidade
- `fontes.json` — já criado na fase 2 (actualizar se necessário)

### 4.5 Actualizar INDEX.md

Adicionar linha no ficheiro `PROTOTIPO - Copia/sistema/trabajos_generados/INDEX.md`:

```
- <YYYY-MM-DD> — [<Título>](<slug_pasta>/trabajo.md) — <modelo> — <asignatura>
```

---

## FASE 5 — Entrega ao utilizador

Apresentar:

```
✅ Trabalho gerado e guardado em:
   PROTOTIPO - Copia/sistema/trabajos_generados/<slug_pasta>/trabajo.md

📊 Estatísticas:
   - Total de palavras: <N> (rango: <min>-<max>)
   - Referências: <N> fontes verificadas
   - Estado: APROBADO

📄 Para converter para .docx:
   pandoc trabajo.md -o trabajo.docx

---
<conteúdo completo do trabajo.md>
```

---

## Regras de segurança do workflow

1. **Nunca avançar** da Fase 2 para a 3 sem aprovação das fontes pelo utilizador.
2. **Nunca alucinar** uma referência. Se não encontrar fontes suficientes → informar e pedir ao utilizador que relaxe o tema ou aprove alternativas.
3. **Parar e pedir** sempre que um campo obrigatório faltar em vez de inventar.
4. **Máx. 2 iterações** de reescrita por secção — não entrar em loop infinito.
5. **Nomenclatura de pasta**: usar `G1` ou `G2`, nunca `GestionI`, `1`, `2026`, etc.
6. **Espanhol académico** no output, mesmo que o utilizador escreva em português ou inglês.
