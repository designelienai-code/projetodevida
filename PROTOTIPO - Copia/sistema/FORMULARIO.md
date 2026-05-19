# Formulário Base, Trabajo UCEBOL

Copia, preenche, cola no chat. Campos `(opcional)` podem ficar em branco.

```yaml
# === MODELO ===
modelo: ensayo_basico        # ensayo_basico, perfil_basico, perfil_intermedio, articulo_original

# === CABECERO ===
# carrera é sempre Medicina, não preencher
asignatura:
docente:
semestre: Gestión I
ano: 2026
grupo: C1                    # (opcional)
autor: Alexandre

titulo:                      # se em branco, sistema sugere a partir do tema

# === TEMA ===
tema:                        # específico, não genérico (ex, "fisiopatologia da diabetes tipo 2")

# === PROMPT PESSOAL (opcional, mas recomendado) ===
prompt: |                    # escreve como se desses ordens ao redator, em PT ou ES
  # O sistema lê isto como instrução direta e enviesa toda a redação a partir daqui.
  # Exemplos de prompts que podes escrever,
  #
  #   "Redige assumindo que a prevalência em jovens está subestimada,
  #    enfatiza o sub-diagnóstico e fecha defendendo rastreio precoce."
  #
  #   "Foca em complicações renais, dá tom crítico ao tratamento atual,
  #    perspetiva de medicina rural boliviana."
  #
  #   "Usa linguagem direta, sem rodeios. Prioriza estudos latino-americanos.
  #    Na conclusão deixa claro que sou a favor de X."
  #
  # Quanto mais específico o prompt, mais autêntico e único o texto final.

# === SÓ PARA perfil_basico ou perfil_intermedio ===
poblacion_estudio:           # ex, "estudiantes de medicina de UCEBOL"
lugar_estudio:               # ex, "Santa Cruz, Bolivia"
tipo_estudio: descriptivo    # descriptivo, analítico

# === SÓ PARA articulo_original ===
autores:                     # lista com afiliações (ex, "Roca C¹, Requena W²")
afiliaciones:                # numeradas
tiene_datos: no              # sí, no  (se "no", Resultados/Discusión ficam pendentes)
```

---

## Como usar (4 passos)

1. Copiar este formulário e preencher os campos relevantes ao modelo escolhido.
2. Colar no chat dizendo, _"gera trabajo UCEBOL"_ (ou `/trabalho-uce`).
3. Validar fontes quando o sistema mostrar a lista (8 a 15 papers reais com DOI). Aprovar ou pedir mais.
4. Receber o ficheiro em `sistema/trabajos_generados/<pasta>/trabajo.md`. Converter com `pandoc trabajo.md -o trabajo.docx` se quiseres `.docx`.

Se faltar algum campo obrigatório, o sistema pergunta antes de gerar.
