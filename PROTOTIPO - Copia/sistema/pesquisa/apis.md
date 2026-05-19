# Pesquisa de Fontes Científicas — APIs

Estratégia: **PubMed primário** + **Semantic Scholar secundário** + (fallback) WebFetch a scienceOS/Consensus.
Todas gratuitas, sem chave obrigatória, retornam citações reais com DOI.

---

## 1. PubMed (NCBI E-utilities) — fonte primária para medicina

**Endpoint base:** `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`

**Sem chave necessária** (rate limit: 3 req/s sem chave, 10 req/s com chave gratuita opcional).

### Fluxo de 2 chamadas

**(a) ESearch — buscar IDs por termo**
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
    ?db=pubmed
    &term=<query>+AND+("2023"[PDAT]:"2026"[PDAT])
    &retmax=10
    &sort=relevance
    &retmode=json
```
Resposta: `esearchresult.idlist` → array de PMIDs.

**(b) ESummary — metadados dos IDs**
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi
    ?db=pubmed
    &id=<id1>,<id2>,<id3>
    &retmode=json
```
Resposta: para cada ID — `title`, `authors[].name`, `source` (revista abreviada), `pubdate`, `volume`, `issue`, `pages`, `articleids[]` (incluindo DOI).

**(c) EFetch — abstract completo (opcional, quando precisa de mais contexto)**
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi
    ?db=pubmed
    &id=<id>
    &rettype=abstract
    &retmode=text
```

### Construção de query Vancouver a partir de PubMed

Dado o JSON de ESummary, montar:
```
Author1 AB, Author2 CD, Author3 EF. Title. Source. PubYear;Vol(Issue):Pages.
```
Exemplo real:
```
Smith J, Patel R, Garcia M. Insulin resistance in type 2 diabetes. N Engl J Med. 2024;391(5):432-9.
```

### Boas práticas de query

- Usar termos MeSH quando possível: `"Diabetes Mellitus, Type 2"[MeSH]`
- Combinar com tipo de estudo: `AND ("review"[PT] OR "meta-analysis"[PT])`
- Filtro de data: `AND ("2023"[PDAT]:"2026"[PDAT])`
- Filtro de idioma: `AND (english[lang] OR spanish[lang])`

---

## 2. Semantic Scholar API — complemento

**Endpoint:** `https://api.semanticscholar.org/graph/v1/paper/search`

**Sem chave para uso casual** (rate limit baixo: ~100 req/5min). Para volume maior, pedir chave gratuita.

### Busca

```
GET https://api.semanticscholar.org/graph/v1/paper/search
    ?query=<query>
    &year=2023-2026
    &limit=10
    &fields=title,authors,year,journal,externalIds,abstract,citationCount,publicationVenue
```

Resposta: `data[]` com cada paper contendo:
- `title`, `authors[].name`, `year`
- `journal.name` ou `publicationVenue.name`
- `externalIds.DOI`, `externalIds.PubMed`
- `abstract` (quando disponível)
- `citationCount` — útil para priorizar fontes mais citadas

### Quando usar Semantic Scholar em vez de PubMed

- Tema **fora de medicina/biologia** (ex: educação, sociologia, ciência da computação).
- Necessidade de papers altamente citados em qualquer área.
- Cobertura de pre-prints (arXiv, bioRxiv).

---

## 3. Fallback: WebFetch para scienceOS/Consensus

Quando PubMed e Semantic Scholar retornam < 3 resultados úteis:

- **scienceOS:** `https://www.scienceos.ai/search?q=<query>` — extrair títulos, autores, DOIs visíveis.
- **Consensus:** `https://consensus.app/results/?q=<query>` — útil para perguntas factuais com "consensus meter".

Sempre **verificar o DOI** antes de usar. Se não houver DOI, descartar a fonte (alto risco de alucinação).

---

## 4. Estratégia de busca por seção

| Seção | Tipo de fontes | Quantidade |
|---|---|---|
| Introducción "¿Qué se sabe?" | reviews recentes + epidemiologia local | 2-3 |
| Introducción "¿Qué no se sabe?" | gaps mencionados em reviews + estudos com limitações | 1-2 |
| Desarrollo / Discusión | estudos primários relevantes | 1 por párrafo |
| Metodología | guidelines (STROBE, CONSORT, PRISMA) | 0-1 conforme aplicável |
| Resultados | NÃO citar (só dados próprios) | 0 |

---

## 5. Validação obrigatória de toda referência

Antes de incluir um paper na lista de Referências:

1. ✅ Tem **DOI ou PMID** real?
2. ✅ O **título** retornado pela API é coerente com o que estamos a citar?
3. ✅ O **ano** está dentro da janela permitida (últimos 3 anos, salvo exceções)?
4. ✅ Os **autores** existem (nome retornado pela API, não inventado)?

Se qualquer falhar → **descartar e procurar outra fonte**. Nunca alucinar uma referência.

---

## 6. Cache local (opcional)

Para evitar repetir buscas dentro do mesmo trabalho:
```
sistema/trabajos_generados/<slug>/cache_fontes.json
```
Estrutura:
```json
{
  "queries": [
    {"q": "diabetes type 2 prevalence latin america", "results": [...], "timestamp": "..."}
  ]
}
```

---

## 7. Implementação no skill

Sonnet usa o tool **WebFetch** para chamar diretamente as URLs acima e extrai/parseia o JSON em memória. Não é necessário escrever código — apenas seguir este protocolo.
