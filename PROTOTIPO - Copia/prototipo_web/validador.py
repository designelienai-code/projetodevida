"""
Validação determinística (sem LLM) de uma secção:
- Contagem de palavras vs range do schema
- Contagem e ordem global de citações (N)
- Detecção de marcadores da lista negra
- Detecção de em-dashes (U+2014)
"""
import re
import os

# Lê lista negra uma vez na importação
_LISTA_NEGRA_PATH = os.path.join(os.path.dirname(__file__), "..", "sistema", "lista_negra.md")


def _carregar_termos_lista_negra() -> list[str]:
    """Extrai frases entre aspas da lista negra."""
    if not os.path.exists(_LISTA_NEGRA_PATH):
        return []
    with open(_LISTA_NEGRA_PATH, "r", encoding="utf-8") as f:
        texto = f.read()
    aspas = re.findall(r'"([^"]+)"', texto)
    return [t.strip() for t in aspas if len(t.strip()) >= 3]


_TERMOS_LISTA_NEGRA = _carregar_termos_lista_negra()


def contar_palavras(texto: str) -> int:
    """Conta palavras ignorando META e markdown básico."""
    if "---META" in texto:
        texto = texto.split("---META")[0]
    texto = re.sub(r"\(\d+(?:,\s*\d+)*\)", "", texto)  # remove (1) (1,2) etc
    palavras = re.findall(r"\b[\wáéíóúñÁÉÍÓÚÑüÜ]+\b", texto)
    return len(palavras)


def extrair_citacoes(texto: str) -> list[int]:
    """Retorna lista de N citados, em ordem de aparição."""
    if "---META" in texto:
        texto = texto.split("---META")[0]
    matches = re.findall(r"\((\d+(?:,\s*\d+)*)\)", texto)
    citas = []
    for m in matches:
        for n in m.split(","):
            citas.append(int(n.strip()))
    return citas


def detectar_lista_negra(texto: str) -> list[str]:
    """Retorna lista de termos da lista negra encontrados."""
    encontrados = []
    texto_lower = texto.lower()
    for termo in _TERMOS_LISTA_NEGRA:
        if termo.lower() in texto_lower:
            encontrados.append(termo)
    return encontrados


def detectar_em_dashes(texto: str) -> int:
    """Conta U+2014 (em-dash)."""
    return texto.count("—")


def validar_seccao(texto: str, palabras_min: int = None, palabras_max: int = None,
                   citas_min: int = None, citas_max: int = None) -> dict:
    """
    Validação completa de uma secção. Retorna dict com flags pass/fail.
    """
    palavras = contar_palavras(texto)
    citacoes = extrair_citacoes(texto)
    n_citacoes_unicas = len(set(citacoes))
    lista_negra = detectar_lista_negra(texto)
    em_dashes = detectar_em_dashes(texto)

    return {
        "palavras": palavras,
        "palavras_ok": (palabras_min or 0) <= palavras <= (palabras_max or 10**6),
        "palavras_range": f"{palabras_min}-{palabras_max}" if palabras_min else "sem range",
        "citacoes_total": len(citacoes),
        "citacoes_unicas": n_citacoes_unicas,
        "citacoes_ok": (citas_min or 0) <= n_citacoes_unicas <= (citas_max or 10**6),
        "citacoes_range": f"{citas_min}-{citas_max}" if citas_min else "sem range",
        "lista_negra_hits": lista_negra,
        "lista_negra_ok": len(lista_negra) == 0,
        "em_dashes": em_dashes,
        "em_dashes_ok": em_dashes == 0,
    }


def validar_ordem_global(citacoes_seccao: list[int], citacoes_ja_usadas: list[int]) -> dict:
    """
    Verifica que novas citações aparecem em ordem crescente a partir do último N usado.
    Ex: se já usaste (1)(2)(3), a próxima nova só pode ser (4).
    """
    max_anterior = max(citacoes_ja_usadas) if citacoes_ja_usadas else 0
    novas = [c for c in citacoes_seccao if c not in citacoes_ja_usadas]
    novas_ordenadas = sorted(set(novas))
    erros = []
    esperada = max_anterior + 1
    for n in novas_ordenadas:
        if n != esperada:
            erros.append(f"esperava ({esperada}), encontrou ({n})")
        esperada = n + 1
    return {
        "novas_citacoes": novas_ordenadas,
        "ordem_ok": len(erros) == 0,
        "erros_ordem": erros,
    }
