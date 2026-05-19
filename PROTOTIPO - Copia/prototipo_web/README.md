# Protótipo Web — Trabajo UCE

Interface local para gerar trabalhos académicos UCEBOL. Substitui o fluxo via skill `/trabalho-uce` por uma UI de 4 painéis.

## Como funciona

| Tarefa | Quem faz | Custo |
|---|---|---|
| Pesquisa PubMed/SemSch | Python puro (`pesquisa.py`) | 0€ |
| Validação (palavras, citações, lista negra) | Python puro (`validador.py`) | 0€ |
| Redactor (escrever secção) | Claude CLI (subscrição Pro) | 0€ |
| Revisor (humanizar) | OpenRouter Qwen 2.5 72B | ~$0.001/secção |

**Total por trabalho: ~$0.01**

## Setup (1x)

1. Confirmar Python instalado:
   ```bash
   python --version
   ```
2. Instalar dependências:
   ```bash
   cd prototipo_web
   python -m pip install -r requirements.txt
   ```
3. Editar `.env` e colar a chave OpenRouter.
4. Confirmar que `claude` está no PATH:
   ```bash
   claude --version
   ```

## Correr

```bash
cd prototipo_web
python app.py
```

Abre o browser em http://127.0.0.1:5000

## Workflow

1. **Painel 1 (Cabecero):** escolhe modelo, preenche título/asignatura/ano → "Carregar modelo"
2. **Painel 2 (Fontes):** escreve query em inglês → "Pesquisar" → desmarca as que não quiseres
3. **Painel 3 (Secções):** "Redigir secção" → vê texto final → "Aprovar e continuar" ou "Regenerar"
4. **Painel 4 (Validação):** atualiza automaticamente após cada secção
5. No fim: "Salvar trabajo" → grava em `sistema/trabajos_generados/`

## Estrutura

```
prototipo_web/
├── app.py              # Servidor Flask
├── llm.py              # Wrappers Claude + OpenRouter
├── pesquisa.py         # PubMed + Semantic Scholar
├── validador.py        # Validação determinística
├── templates/
│   └── index.html      # UI single-page
├── static/
│   └── style.css       # Estilo dark
├── .env                # Chaves (não partilhar)
├── .env.example        # Template público
└── requirements.txt
```

## Notas

- O `.env` está no `.gitignore`, nunca vai para fora.
- Os agents (`redactor-cientifico`, `revisor-humanizador`) são lidos de `../.claude/agents/`.
- Os modelos e schemas de `../sistema/modelos/`.
- A lista negra de `../sistema/lista_negra.md`.

## Multi-janelas (opcional)

Abre o Chrome em modo app para teres "janela nativa":

```bash
chrome --app=http://127.0.0.1:5000
```

Ou no Chrome → instalar app (PWA) e abrir várias instâncias.
