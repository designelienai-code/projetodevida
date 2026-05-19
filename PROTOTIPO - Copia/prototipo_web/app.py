"""
Servidor Flask local — interface web do trabajo UCE.
Corre em http://127.0.0.1:5000

Painéis:
1. Cabecero  -> formulário inicial
2. Fontes    -> resultados de pesquisa PubMed/SemSch
3. Secções  -> redactor + revisor (live)
4. Validação -> contagens + lista negra
"""
import os
import json
import yaml
import re
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

import pesquisa
import validador
import llm

load_dotenv()

app = Flask(__name__)
app.secret_key = "dev-local-only-trabajo-uce"

ROOT = Path(__file__).parent.parent
SISTEMA = ROOT / "sistema"
OUTPUT_DIR = SISTEMA / "trabajos_finalizados"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def slugify(texto: str) -> str:
    """Converte texto para slug seguro (ASCII, hyphens)."""
    texto = re.sub(r"[^\w\s-]", "", texto.lower(), flags=re.UNICODE)
    texto = re.sub(r"[\s_]+", "-", texto.strip())
    return texto[:60]


def carregar_modelo(modelo_id: str) -> dict:
    """Lê schema.yaml + template.md de um modelo."""
    schema_path = SISTEMA / "modelos" / modelo_id / "schema.yaml"
    template_path = SISTEMA / "modelos" / modelo_id / "template.md"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    template = template_path.read_text(encoding="utf-8") if template_path.exists() else ""
    return {"schema": schema, "template": template}


@app.route("/")
def index():
    modelos = ["ensayo_basico", "perfil_basico", "perfil_intermedio", "articulo_original"]
    return render_template("index.html", modelos=modelos)


@app.route("/api/modelo/<modelo_id>")
def api_modelo(modelo_id):
    """Retorna schema + secções de um modelo."""
    try:
        info = carregar_modelo(modelo_id)
        return jsonify({"ok": True, "schema": info["schema"]})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 400


@app.route("/api/sugerir-query", methods=["POST"])
def api_sugerir_query():
    """Gera query em inglês a partir de título + asignatura + prompt do autor."""
    data = request.json or {}
    titulo = data.get("titulo", "").strip()
    asignatura = data.get("asignatura", "").strip()
    prompt_autor = data.get("prompt", "").strip()
    if not titulo:
        return jsonify({"ok": False, "erro": "título vazio"}), 400

    sys = (
        "Convertes o tema de um trabalho académico para uma query de pesquisa PubMed em inglês. "
        "REGRAS DURAS: máximo 4 palavras-chave (NUNCA mais), sem aspas, sem operadores booleanos, "
        "sem ponto final, sem stop words (the, of, in, and, for). "
        "Apenas os termos técnicos centrais. PubMed exige que TODAS as palavras apareçam no paper, "
        "por isso menos é mais. Exemplo bom: 'vital signs surgical monitoring'. "
        "Exemplo MAU: 'vital signs surgical patient monitoring alarm predictive perioperative'. "
        "Responde APENAS com a query (3-4 palavras), nada mais."
    )
    user = f"Título: {titulo}\nAsignatura: {asignatura}\nÂngulo do autor: {prompt_autor or '(nenhum)'}\n\nQuery:"

    resp = llm.call_openrouter(sys, user, timeout=30)
    query = resp["texto"].strip().strip('"').strip("'").rstrip(".")
    if query.startswith("[ERRO"):
        return jsonify({"ok": False, "erro": query}), 500
    return jsonify({"ok": True, "query": query, "custo_usd": resp["custo_usd"]})


@app.route("/api/pesquisa", methods=["POST"])
def api_pesquisa():
    """Pesquisa fontes via PubMed + Semantic Scholar."""
    data = request.json or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"ok": False, "erro": "query vazia"}), 400
    resultados = pesquisa.buscar(query, max_results=15)
    return jsonify({"ok": True, "resultados": resultados})


@app.route("/api/redigir", methods=["POST"])
def api_redigir():
    """
    Redige UMA secção via Claude CLI + revisa via OpenRouter Qwen.
    Body: { section_spec, cabecero, bibliografia, citacoes_ja_usadas, secciones_anteriores }
    """
    data = request.json or {}
    section_spec = data.get("section_spec", {})
    cabecero = data.get("cabecero", {})
    bibliografia = data.get("bibliografia", [])
    citacoes_ja_usadas = data.get("citacoes_ja_usadas", [])
    secciones_anteriores = data.get("secciones_anteriores", "")
    saltar_revisor = data.get("saltar_revisor", False)

    # Preparar inputs comuns
    biblio_str = "\n".join([
        f"({i+1}) {p.get('vancouver', '')}"
        for i, p in enumerate(bibliografia)
    ])
    cabecero_str = "\n".join([f"{k}: {v}" for k, v in cabecero.items() if v])

    user_input_redactor = f"""## Section spec
{json.dumps(section_spec, ensure_ascii=False, indent=2)}

## Cabecero
{cabecero_str}

## Bibliografía (Vancouver, numerada globalmente)
{biblio_str}

## Citation counter state
Já usadas: {citacoes_ja_usadas}

## Secciones ya escritas
{secciones_anteriores or '(primera sección)'}

Redige agora a secção seguindo as regras."""

    # PASSO 1: Redactor (Claude CLI)
    sys_redactor = llm.load_agent_prompt("redactor-cientifico")
    texto_redactor = llm.call_claude(sys_redactor, user_input_redactor, timeout=240)

    # PASSO 2: Revisor (OpenRouter Qwen) — opcional
    custo_usd = 0.0
    texto_revisor = ""
    if saltar_revisor:
        texto_final = texto_redactor
        decisao = "sem_revisor"
    else:
        sys_revisor = llm.load_agent_prompt("revisor-humanizador")
        user_input_revisor = f"""## Texto do redactor (com bloco META)
{texto_redactor}

## Section spec
{json.dumps(section_spec, ensure_ascii=False, indent=2)}

## Cabecero
{cabecero_str}

## Bibliografía
{biblio_str}

## Secciones ya escritas
{secciones_anteriores or '(primera sección)'}

Audita agora."""

        resp_rev = llm.call_openrouter(sys_revisor, user_input_revisor, timeout=180)
        texto_revisor = resp_rev["texto"]
        custo_usd = resp_rev["custo_usd"]

        if texto_revisor.strip().startswith("APROBADO"):
            texto_final = texto_redactor
            decisao = "aprobado"
        else:
            texto_final = texto_revisor
            decisao = "corregido"

    # Validação determinística
    val = validador.validar_seccao(
        texto_final,
        palabras_min=section_spec.get("palabras_min"),
        palabras_max=section_spec.get("palabras_max"),
        citas_min=section_spec.get("citas_min"),
        citas_max=section_spec.get("citas_max"),
    )

    return jsonify({
        "ok": True,
        "texto_redactor": texto_redactor,
        "texto_revisor": texto_revisor,
        "texto_final": texto_final,
        "decisao": decisao,
        "validacao": val,
        "custo_usd": custo_usd,
    })


@app.route("/api/validar", methods=["POST"])
def api_validar():
    """Re-valida texto editado manualmente (sem LLM, sem custo)."""
    data = request.json or {}
    texto = data.get("texto", "")
    spec = data.get("section_spec", {})
    val = validador.validar_seccao(
        texto,
        palabras_min=spec.get("palabras_min"),
        palabras_max=spec.get("palabras_max"),
        citas_min=spec.get("citas_min"),
        citas_max=spec.get("citas_max"),
    )
    return jsonify({"ok": True, "validacao": val})


@app.route("/api/salvar", methods=["POST"])
def api_salvar():
    """Grava um único trabajo.md em sistema/trabajos_finalizados/ com refs anexadas."""
    data = request.json or {}
    cabecero = data.get("cabecero", {})
    modelo = data.get("modelo", "ensayo_basico")
    texto_completo = data.get("texto_completo", "").strip()
    fontes = data.get("fontes", [])
    citacoes_usadas = data.get("citacoes_usadas", [])

    asignatura = slugify(cabecero.get("asignatura", "sem-asignatura"))
    titulo = slugify(cabecero.get("titulo", "sem-titulo"))
    ano = cabecero.get("ano", str(datetime.now().year))
    gestao = cabecero.get("gestao", "G1")

    # Cabeçalho YAML inline (frontmatter) para o ficheiro ficar self-contained
    frontmatter = (
        f"---\n"
        f"titulo: {cabecero.get('titulo', '')}\n"
        f"asignatura: {cabecero.get('asignatura', '')}\n"
        f"modelo: {modelo}\n"
        f"ano: {ano}\n"
        f"gestao: {gestao}\n"
        f"gerado_em: {datetime.now().isoformat(timespec='minutes')}\n"
        f"---\n\n"
    )

    # Anexar referências Vancouver no fim (apenas as citadas)
    refs_md = "\n\n## Referencias\n\n"
    for n in sorted(set(citacoes_usadas)):
        if 1 <= n <= len(fontes):
            refs_md += f"({n}) {fontes[n-1].get('vancouver', '')}\n\n"

    nome_arquivo = f"{ano}-{gestao}__{asignatura}__{modelo}__{titulo}.md"
    caminho = OUTPUT_DIR / nome_arquivo
    caminho.write_text(frontmatter + texto_completo + refs_md, encoding="utf-8")

    return jsonify({"ok": True, "arquivo": nome_arquivo, "caminho": str(caminho)})


@app.route("/api/historico", methods=["GET"])
def api_historico():
    """Lista trabalhos finalizados (apenas nomes, ordenados por mais recente)."""
    arquivos = sorted(OUTPUT_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    items = []
    for p in arquivos:
        items.append({
            "nome": p.name,
            "tamanho_kb": round(p.stat().st_size / 1024, 1),
            "modificado": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    return jsonify({"ok": True, "items": items})


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))
    print(f"\n>> Trabajo UCE Web a correr em http://{host}:{port}\n")
    app.run(host=host, port=port, debug=True)
