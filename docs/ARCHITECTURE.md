# Arquitectura del perfil

Este repo genera un README dinámico al estilo "terminal": un banner con el
retrato en stipple + panel de datos, más radares y cards de stats, todo
renderizado como SVG por scripts propios y refrescado por GitHub Actions.
No usa servicios públicos compartidos (github-readme-stats, lowlighter/metrics)
salvo el typing SVG y los badges de shields.io/komarev, que son solo texto/UI
y no dependen de datos de GitHub.

No hay backend: todo se resuelve en build-time (local o en CI) y el
resultado son archivos `.svg` estáticos commiteados en `assets/`.

## Por qué existe cada pieza

- **`scripts/theme.py`** — única fuente de la paleta (colores dark/light).
  Todo lo demás importa de aquí; cambiar el acento del proyecto es cambiar
  un solo archivo.
- **`scripts/dotify.py`** — convierte una foto en una nube de puntos
  (stipple) vía dithering Floyd-Steinberg con barrido serpentina (fila par
  izq→der, impar der→izq), el mismo algoritmo que usan los retratos
  "1-bit" de terminal. Trabaja sobre una rejilla de `cols x rows` y respeta
  el canal alfa de la imagen (fondo transparente = sin tinta, nunca genera
  halo alrededor del sujeto).
- **`scripts/banner.py`** — arma el SVG de dos paneles (`VISUAL.MAP` +
  `SYSTEM.INFO`) a partir del stipple de `dotify.py` y de
  `assets/profile.json`. Es el único generador que **no** corre en CI: el
  retrato solo cambia si tú lo cambias, así que se ejecuta a mano y el
  resultado se commitea versionado.
- **`scripts/radar.py`** — radares (skills, language mix) desde JSON plano
  `[{label, value}]`. Sin dependencias (matplotlib, etc.), todo es SVG a
  mano con trigonometría básica.
- **`scripts/cards.py`** — pega a la API de GitHub (REST + GraphQL) para
  stats en vivo (repos, followers, estrellas, contribuciones del año) y
  renderiza la card de stats y la card de lenguajes (esta última a partir
  de `assets/langmix.json`, no de la API — ver "Decisión: por qué no
  lowlighter/metrics").

## Flujo de datos

```
assets/profile.json ──► scripts/banner.py ──► assets/banner-{dark,light}.svg
assets/portrait.png ──┘         (manual, no está en ningún workflow)

assets/skills.json  ──► scripts/radar.py ──► assets/radar-{dark,light}.svg
assets/langmix.json ──► scripts/radar.py ──► assets/radar-langs-{dark,light}.svg
assets/langmix.json ──► scripts/cards.py ──► assets/card-languages-{dark,light}.svg
GitHub API           ──► scripts/cards.py ──► assets/card-stats-{dark,light}.svg
```

`.github/workflows/radar.yml` corre `radar.py` y `cards.py` (no `banner.py`)
diario, en cada push a `main` que toque los JSON/scripts relevantes, y bajo
demanda (`workflow_dispatch`). Si algo cambió, el bot commitea y pushea con
`github-actions[bot]`.

## Decisiones no obvias

- **Escapar texto en SVG.** Cualquier `&` sin escapar en una etiqueta rompe
  el XML del archivo entero (no solo esa línea) y GitHub lo renderiza como
  imagen rota, sin aviso. Todo texto dinámico pasa por
  `xml.sax.saxutils.escape` en los tres generadores.
- **Overflow del radar.** El elemento `<svg>` raíz tiene `overflow: hidden`
  por defecto — cualquier `<text>` que se salga del `viewBox` se recorta
  silenciosamente. Por eso el canvas del radar es 700×460 (no cuadrado) con
  margen generoso para etiquetas largas como "Agentic Workflows / RAG".
- **Dirección tonal del stipple según el tema.** En fondo oscuro los puntos
  deben leerse como *luz* (más densidad en la piel iluminada, menos en el
  pelo/ropa oscura) o la cara desaparece en una mancha. En fondo claro se
  invierte: los puntos leen como *tinta*. `STIPPLE_OPTS` en `banner.py`
  tiene un mapeo por tema (`ink_dark`/`ink_light` intercambiados).
- **Alineación de columnas en `SYSTEM.INFO`.** Cada fila se rellena a un
  número fijo de caracteres y se fuerza con `textLength` +
  `lengthAdjust="spacingAndGlyphs"`, así las columnas cuadran incluso si
  quien lo ve no tiene JetBrains Mono instalada y el navegador hace
  fallback a otra monoespaciada.
- **Por qué no `lowlighter/metrics`.** Se usó en la primera versión para el
  bloque de "most used languages", pero (a) el repo `competitiveProgramming`
  (viejas soluciones de programación competitiva) domina el byte-count con
  ~3.3 MB de C++, y `plugin_languages_ignored` filtra *lenguajes*, no
  *repos* — no hay forma de excluir ese repo desde la config de la action;
  (b) la card que genera es tema claro fijo, no calza con un README oscuro.
  Se reemplazó por una card propia (`render_language_card` en `cards.py`)
  que lee `assets/langmix.json`, la misma fuente que alimenta el radar de
  lenguajes — un solo dato, dos visualizaciones consistentes entre sí.
- **`assets/langmix.json` es curado, no 100% bruto.** Los bytes de GitHub
  para el usuario están dominados por repos de tareas universitarias y
  competencia (`competitiveProgramming`, `assignment1-3`, `datalab01/02`,
  etc.), que no reflejan el stack real de trabajo. El JSON actual excluye
  esos repos a mano; si se agregan repos nuevos relevantes, el mix no se
  recalcula solo — hay que regenerarlo (ver más abajo).

## Cómo tocar cada cosa

- **Cambiar bio/contacto/skills del banner** → editar `assets/profile.json`,
  correr `banner.py` (ver comando abajo) y commitear el SVG resultante.
- **Cambiar el retrato** → reemplazar `assets/portrait.png` (recorte
  cuadrado-ish, fondo transparente idealmente) y volver a correr `banner.py`.
- **Ajustar el radar de skills** → editar `assets/skills.json` (valores
  0–1) y hacer push; el workflow lo redibuja solo.
- **Recalcular `langmix.json`** desde la API de GitHub → no hay script
  automatizado todavía (se hizo a mano una vez, ver commits de setup
  inicial); si se vuelve a hacer, filtrar los repos de curso/competencia
  como en la nota anterior antes de guardar el JSON.
- **Cambiar la paleta** → editar `scripts/theme.py` (un solo lugar para
  banner, radares y cards) y regenerar todo:

  ```bash
  python scripts/banner.py --portrait assets/portrait.png --profile assets/profile.json -o assets/banner
  python scripts/radar.py --data assets/skills.json -o assets/radar
  python scripts/radar.py --data assets/langmix.json -o assets/radar-langs --values
  GITHUB_TOKEN=<pat> python scripts/cards.py --user JackMerma --langmix assets/langmix.json --out assets
  ```

## Secrets

`METRICS_TOKEN` (Settings → Secrets and variables → Actions) es un PAT
clásico con scope de lectura sobre repos y contribuciones; sin él,
`cards.py` cae al `GITHUB_TOKEN` por defecto del workflow, que solo ve
datos públicos (sin conteo de contribuciones privadas).
