"""
Wrappers para os dois LLMs do sistema:
- Claude (subscrição Pro, via CLI 'claude' como subprocesso) -> REDACTOR
- OpenRouter Qwen (open source, hospedado, via HTTP)        -> REVISOR
"""
import os
import subprocess
import requests
from dotenv import load_dotenv

load_dotenv()

CLAUDE_CMD = os.getenv("CLAUDE_CLI_COMMAND", "claude")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "qwen/qwen-2.5-7b-instruct")

# Preços por 1M tokens (input, output) em USD — atualizar conforme OpenRouter
PRECOS = {
    "qwen/qwen-2.5-7b-instruct": (0.04, 0.10),
    "qwen/qwen-2.5-72b-instruct": (0.35, 0.40),
}
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_claude(system_prompt: str, user_prompt: str, timeout: int = 180) -> str:
    """
    Chama o CLI Claude Code com prompt único combinado.
    Usa subscrição Pro (sem custo de API).
    """
    full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"
    try:
        result = subprocess.run(
            [CLAUDE_CMD, "-p", full_prompt, "--output-format", "text"],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            return f"[ERRO CLAUDE CLI] exit={result.returncode}\n{result.stderr}"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "[ERRO CLAUDE CLI] timeout"
    except FileNotFoundError:
        return f"[ERRO CLAUDE CLI] comando '{CLAUDE_CMD}' não encontrado no PATH"


def call_openrouter(system_prompt: str, user_prompt: str, timeout: int = 120) -> str:
    """
    Chama OpenRouter (Qwen 2.5 72B por defeito).
    Custo: ~$0.0008 por chamada média.
    """
    if not OPENROUTER_KEY or OPENROUTER_KEY.startswith("COLA"):
        return "[ERRO OPENROUTER] chave não configurada no .env"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "Trabalho UCE Web",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
    }
    try:
        r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=timeout)
        if r.status_code != 200:
            return f"[ERRO OPENROUTER] HTTP {r.status_code}: {r.text[:300]}"
        data = r.json()
        texto = data["choices"][0]["message"]["content"].strip()
        usage = data.get("usage", {})
        return {
            "texto": texto,
            "tokens_in": usage.get("prompt_tokens", 0),
            "tokens_out": usage.get("completion_tokens", 0),
            "custo_usd": _calcular_custo(usage),
        }
    except requests.RequestException as e:
        return {"texto": f"[ERRO OPENROUTER] {e}", "tokens_in": 0, "tokens_out": 0, "custo_usd": 0}


def _calcular_custo(usage: dict) -> float:
    """Custo estimado em USD baseado em tokens consumidos."""
    p_in, p_out = PRECOS.get(OPENROUTER_MODEL, (0.5, 0.5))
    return round(
        (usage.get("prompt_tokens", 0) / 1_000_000) * p_in
        + (usage.get("completion_tokens", 0) / 1_000_000) * p_out,
        6,
    )


def load_agent_prompt(agent_name: str) -> str:
    """Lê o ficheiro do subagente como system prompt (sem o frontmatter YAML)."""
    path = os.path.join(
        os.path.dirname(__file__), "..", ".claude", "agents", f"{agent_name}.md"
    )
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return content
