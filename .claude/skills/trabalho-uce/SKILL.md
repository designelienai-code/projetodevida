# Skill: /trabalho-uce

Genera trabajos académicos de investigación UCEBOL (Carrera de Medicina) a partir de los modelos oficiales, con fuentes científicas reales vía PubMed y Semantic Scholar.

## Archivos base (leer siempre al inicio)

1. `PROTOTIPO - Copia/sistema/reglas_globales.md`
2. `PROTOTIPO - Copia/sistema/lista_negra.md`
3. `PROTOTIPO - Copia/sistema/modelos/<modelo>/schema.yaml` y `template.md`
4. `PROTOTIPO - Copia/sistema/pesquisa/apis.md` (cuando busques fuentes)

## Flujo completo

### PASO 1 — Recoger parámetros

Si el usuario no proporcionó todos los campos requeridos del schema, preguntar explícitamente los que faltan. No inventar ningún campo requerido. Los campos `requerido: true` del schema son obligatorios antes de redactar.

Campos siempre necesarios:
- `modelo` (ensayo_basico / perfil_basico / perfil_intermedio / articulo_original)
- `asignatura`
- `docente` (con título: Dr./Dra./Lic.)
- `semestre` (ej. Gestión I / Gestión II)
- `ano` (defecto: 2026)
- `autor` (nombre completo del estudiante)
- `tema` (específico, no genérico)

Campos adicionales según modelo:
- perfil_basico y perfil_intermedio: `poblacion_estudio`, `lugar_estudio`, `tipo_estudio`
- articulo_original: `autores`, `afiliaciones`, `tiene_datos`

Si el usuario trae `prompt` personal, conservarlo — se pasa al redactor en cada sección.

### PASO 2 — Buscar fuentes científicas

Seguir `PROTOTIPO - Copia/sistema/pesquisa/apis.md`.

1. Construir 2-3 queries PubMed con términos MeSH + filtro de fecha (últimos 3 años).
2. Llamar ESearch → ESummary para cada query.
3. Complementar con Semantic Scholar si PubMed retorna < 5 resultados útiles.
4. Validar cada paper: DOI/PMID real + título coherente + año dentro de ventana + autores reales.
5. Presentar al usuario la lista de fuentes (título, autores, revista, año, DOI) y pedir confirmación.
6. Si el usuario aprueba, continuar. Si pide más, buscar.
7. Guardar en `fontes.json` dentro de la carpeta de output.

Mínimos por modelo:
- ensayo_basico: ≥4 fuentes
- perfil_basico: ≥5 fuentes
- perfil_intermedio: ≥8 fuentes
- articulo_original: ≥12 fuentes

**Si no se alcanza el mínimo → DETENER y avisar al usuario. Nunca alucinar referencias.**

### PASO 3 — Redactar sección por sección

Para cada sección definida en el schema:

1. Invocar subagente `redactor-cientifico` con:
   - Instrucciones de la sección (schema)
   - Fuentes disponibles (fontes.json)
   - Prompt personal del usuario (si existe)
   - Contexto del cabecero (título, objetivo, tema)
2. Invocar subagente `revisor-humanizador` con:
   - Texto generado por redactor
   - Schema de la sección
   - fontes.json
3. Aplicar correcciones del revisor.
4. Registrar log en `meta.yaml`.

### PASO 4 — Ensamblar documento final

Usar el template del modelo (`PROTOTIPO - Copia/sistema/modelos/<modelo>/template.md`).

Sustituir todos los `{{...}}` con los valores reales.
Eliminar todos los `<!-- GENERAR: ... -->` (reemplazados por contenido).
Preservar los `<!-- REDACTOR: ... -->` y `<!-- REVISOR: ... -->` como comentarios internos.

### PASO 5 — Validación pre-entrega (checklist reglas_globales.md §9)

- [ ] Placeholders `{{...}}` sustituidos.
- [ ] Ningún `<!-- GENERAR: ... -->` sin contenido.
- [ ] Toda cita `(N)` tiene entrada en Referencias.
- [ ] Toda entrada de Referencias aparece citada al menos una vez.
- [ ] Referencias con DOI/PMID real (verificadas en Paso 2).
- [ ] Palabras dentro del rango por sección (±10%).
- [ ] Coherencia título ↔ objetivo ↔ pregunta ↔ hipótesis.
- [ ] Sin opinión del autor donde está prohibida.
- [ ] Todo parafraseado (anti-plagio).
- [ ] Cero matches de lista_negra.md. Cero em-dashes.

### PASO 6 — Guardar output

Carpeta: `PROTOTIPO - Copia/sistema/trabajos_generados/<ano>-<gestao>__<asignatura-slug>__<modelo>__<tema-slug>/`

Donde:
- `<gestao>`: G1 (Gestión I) o G2 (Gestión II). Nunca "GestionI", "2026", "1", etc.
- `<asignatura-slug>`: minúsculas, guiones, sin tildes.
- `<tema-slug>`: 3-5 palabras del tema, minúsculas, guiones.

Archivos a crear:
- `trabajo.md` — documento final
- `fontes.json` — fuentes verificadas
- `meta.yaml` — logs de redactor y revisor por sección

Actualizar `PROTOTIPO - Copia/sistema/trabajos_generados/INDEX.md` añadiendo la línea del nuevo trabajo.

## Modelos soportados

| id | nombre | año | palabras |
|---|---|---|---|
| `ensayo_basico` | Ensayo Académico (INV-00) | 1º | 400-650 |
| `perfil_basico` | Perfil de Investigación Básico (INV-01) | 2º | 550-850 |
| `perfil_intermedio` | Perfil de Investigación Intermedio (INV-02) | 3º | 1100-1700 |
| `articulo_original` | Artículo Original (INV-04) | avanzado | 2500-4500 |

## Notas

- Carrera es siempre **Medicina**. No preguntar.
- Si el usuario escribe en portugués, responder en portugués pero generar el trabajo en **español académico**.
- Pedir lo que falta, nunca inventar.
