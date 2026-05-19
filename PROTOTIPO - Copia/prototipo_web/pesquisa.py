"""
Pesquisa de fontes científicas — PubMed primário + Semantic Scholar secundário.
Sem LLM. Retorna lista normalizada de papers com DOI/PMID, prontos para citar.
"""
import requests
import time
from datetime import datetime

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
SEMSCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


def _pubmed_search(query: str, max_results: int = 10, year_from: int = None) -> list[str]:
    """ESearch -> lista de PMIDs."""
    if year_from is None:
        year_from = datetime.now().year - 3
    year_to = datetime.now().year
    term = f"{query} AND (\"{year_from}\"[PDAT]:\"{year_to}\"[PDAT])"
    params = {
        "db": "pubmed",
        "term": term,
        "retmax": max_results,
        "sort": "relevance",
        "retmode": "json",
    }
    r = requests.get(f"{PUBMED_BASE}/esearch.fcgi", params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("esearchresult", {}).get("idlist", [])


def _pubmed_summary(pmids: list[str]) -> list[dict]:
    """ESummary -> metadados completos."""
    if not pmids:
        return []
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "json"}
    r = requests.get(f"{PUBMED_BASE}/esummary.fcgi", params=params, timeout=30)
    r.raise_for_status()
    result = r.json().get("result", {})
    papers = []
    for pmid in pmids:
        if pmid not in result:
            continue
        item = result[pmid]
        doi = ""
        for aid in item.get("articleids", []):
            if aid.get("idtype") == "doi":
                doi = aid.get("value", "")
                break
        authors = [a.get("name", "") for a in item.get("authors", [])][:6]
        papers.append({
            "fonte": "PubMed",
            "pmid": pmid,
            "doi": doi,
            "titulo": item.get("title", "").strip("."),
            "autores": authors,
            "revista": item.get("source", ""),
            "ano": (item.get("pubdate", "") or "")[:4],
            "vancouver": _vancouver(authors, item.get("title", ""), item.get("source", ""),
                                    item.get("pubdate", "")[:4], item.get("volume", ""),
                                    item.get("issue", ""), item.get("pages", "")),
        })
    return papers


def _semantic_scholar(query: str, max_results: int = 10) -> list[dict]:
    """Fallback / complemento para temas não-médicos."""
    year_from = datetime.now().year - 3
    year_to = datetime.now().year
    params = {
        "query": query,
        "year": f"{year_from}-{year_to}",
        "limit": max_results,
        "fields": "title,authors,year,journal,externalIds,abstract,citationCount",
    }
    try:
        r = requests.get(SEMSCH_URL, params=params, timeout=30)
        if r.status_code != 200:
            return []
        papers = []
        for p in r.json().get("data", []):
            ext = p.get("externalIds", {}) or {}
            doi = ext.get("DOI", "")
            pmid = ext.get("PubMed", "")
            if not (doi or pmid):
                continue
            authors = [a.get("name", "") for a in (p.get("authors") or [])][:6]
            journal = (p.get("journal") or {}).get("name", "") or ""
            papers.append({
                "fonte": "SemanticScholar",
                "pmid": pmid,
                "doi": doi,
                "titulo": p.get("title", ""),
                "autores": authors,
                "revista": journal,
                "ano": str(p.get("year", "")),
                "citacoes": p.get("citationCount", 0),
                "vancouver": _vancouver(authors, p.get("title", ""), journal,
                                        str(p.get("year", "")), "", "", ""),
            })
        return papers
    except requests.RequestException:
        return []


def _vancouver(authors, title, journal, year, vol, issue, pages):
    """Monta string Vancouver."""
    auts = ", ".join(authors[:6]) if authors else "Autor desconhecido"
    if len(authors) > 6:
        auts += ", et al"
    parts = [f"{auts}. {title.strip('.')}. {journal}. {year}"]
    if vol:
        suf = f";{vol}"
        if issue:
            suf += f"({issue})"
        if pages:
            suf += f":{pages}"
        parts[0] += suf
    return parts[0] + "."


def _pubmed_completo(query: str, max_results: int) -> list[dict]:
    """Wrapper PubMed search + summary."""
    pmids = _pubmed_search(query, max_results=max_results)
    time.sleep(0.4)
    return _pubmed_summary(pmids)


def buscar(query: str, max_results: int = 15) -> list[dict]:
    """
    API pública. Tenta PubMed primeiro, completa com Semantic Scholar.
    Fallback: se 0 resultados, encurta a query removendo palavras do fim.
    """
    resultados = []
    seen = set()
    palavras = query.split()
    query_usada = query

    try:
        for tentativa in range(3):
            papers = _pubmed_completo(query_usada, max_results=max_results)
            for p in papers:
                key = p.get("doi") or p.get("pmid")
                if key and key not in seen:
                    seen.add(key)
                    resultados.append(p)
            if resultados or len(palavras) <= 2:
                break
            palavras = palavras[:-1]
            query_usada = " ".join(palavras)
    except requests.RequestException as e:
        resultados.append({"erro": f"PubMed falhou: {e}"})

    if len(resultados) < max_results:
        falta = max_results - len(resultados)
        for p in _semantic_scholar(query_usada, max_results=falta + 3):
            key = p.get("doi") or p.get("pmid")
            if key and key not in seen:
                seen.add(key)
                resultados.append(p)
                if len(resultados) >= max_results:
                    break

    if resultados and query_usada != query:
        resultados.insert(0, {"_info": f"Query original retornou 0, usei: '{query_usada}'"})

    return resultados
