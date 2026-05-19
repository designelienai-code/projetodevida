# Reglas Globales — Sistema UCEBOL

Reglas que se aplican a TODOS los modelos. Sobrescriben cualquier instrucción contraria.

## 1. Idioma y estilo

- Español académico latinoamericano, registro UCEBOL. Tono formal e impersonal.
- Sin primera persona ("yo", "nosotros") salvo en secciones que declaran `incluir_opinion_autor: true`.
- Prosa en párrafos. Sin viñetas salvo cuando el schema lo marca con `formato: lista_enumerada`.
- Texto justificado en la conversión final a .docx.

## 2. Citaciones — Vancouver numerado

- Citas inline: `(1)`, `(2)`, `(3)`. Numeradas por orden global de aparición.
- Dos fuentes: `(1,2)`. Rango: `(1-3)`.
- Referencias finales en orden numérico:
  `Apellido AB, Apellido CD, Apellido EF. Título. Abrev Revista. Año;Vol(Núm):páginas.`
- Máximo 6 autores; si son más, "et al" después del sexto.
- Toda referencia DEBE ser real y verificable (DOI/PMID). Nunca inventar.

## 3. Anti-plagio

Prohibido copiar y pegar. Siempre parafrasear. Citas textuales solo con comillas + atribución y muy breves.

## 4. Frescura

Preferir últimos 3 años desde `{{ano}}`. Excepciones: definiciones clásicas, criterios estandarizados (STROBE, CONSORT), guías clínicas vigentes (versión más reciente).

## 5. Título

- MAYÚSCULAS, centrado, ≤21 palabras.
- En perfiles: el título es el objetivo general con el verbo en infinitivo convertido en sustantivo.
  "Determinar la prevalencia de X" → "DETERMINACIÓN DE LA PREVALENCIA DE X".

## 6. Coherencia interna

Título ↔ objetivo general ↔ pregunta de investigación ↔ hipótesis (si aplica) deben ser semánticamente equivalentes. Conclusiones esperadas responden al objetivo en tiempo futuro.

## 7. Cabecero

Todos los campos `requerido: true` del schema deben estar resueltos antes de redactar el cuerpo. Si falta, **pedir explícitamente** (no inventar).

## 8. Prompt del autor (cabecero opcional)

Si el cabecero trae `prompt`, se pasa literal al redactor en cada sección. Inclina ángulo, énfasis y tono. Las fuentes y datos siguen siendo reales. Si el prompt contradice el consenso científico, se mantienen los hechos y se inclina solo la interpretación.

## 9. Validación pre-entrega (checklist)

- [ ] Placeholders `{{...}}` sustituidos.
- [ ] Ningún `<!-- GENERAR: ... -->` sin contenido.
- [ ] Toda cita `(N)` tiene entrada en Referencias.
- [ ] Toda entrada de Referencias aparece citada al menos una vez.
- [ ] Referencias verificadas (DOI/PMID real).
- [ ] Palabras dentro del rango por sección (±10%).
- [ ] Coherencia título ↔ objetivo ↔ pregunta ↔ hipótesis.
- [ ] Sin opinión del autor donde está prohibida.
- [ ] Anti-plagio: todo parafraseado.
- [ ] Cada sección pasó por `redactor-cientifico` + `revisor-humanizador`. Logs en `meta.yaml`.
- [ ] Cero matches de `sistema/lista_negra.md`. Cero em-dashes.

## 10. Anti-IA

Lista negra única: `sistema/lista_negra.md`. Anti-tangencia y anti-alucinación: instrucciones detalladas en los agentes `redactor-cientifico` y `revisor-humanizador`.

## 11. Output

- Primario: `.md` en `sistema/trabajos_generados/<ano>-<gestao>__<asignatura>__<modelo>__<tema>/`.
- Nomenclatura `<gestao>`: usar `G1` o `G2` (Gestión I/II). No mezclar formatos.
- Conversión a `.docx`: manual con `pandoc trabajo.md -o trabajo.docx`.
