# Memoria Chilena — GraphRAG patrimonial (auditoría 1–3)

Proyecto Jupyter/Python para comenzar **desde cero** el piloto de metadatos RDF de [Memoria Chilena](https://www.memoriachilena.gob.cl/602/w3-article-790.html). No incluye resultados de ejecuciones previas: **todo se recupera de nuevo** en el ordenador donde se ejecuta.

## Inicio: un solo notebook

1. Descomprimir `MC_GraphRAG_DESDE_CERO_JUPYTER.zip` en una carpeta propia, por ejemplo `C:\Users\...\Documents\memoria_chilena`.
2. En Windows, hacer doble clic en **`INICIAR_JUPYTER.bat`** (instala las dependencias y abre JupyterLab). En macOS/Linux, abrir terminal en la carpeta del proyecto y ejecutar `python -m pip install -r requirements.txt` seguido de `jupyter lab`.
3. Abrir **`ABRIR_AQUI.ipynb`** y pulsar **Run → Run All Cells**.
4. El notebook ejecuta las etapas 1, 2 y 3, y genera todos los ZIP automáticamente.

> Si vas a **reemplazar** un proyecto anterior, haz antes una copia de cualquier resultado que quieras conservar. Puedes borrar la carpeta anterior y sustituirla por esta nueva estructura. No hay que copiar `etapa2.zip`, `memoria_chilena_auditoria.zip` ni preparar `data/input`.

### Los ZIP se crean solos en `data/output/`

```text
memoria_chilena/
├── ABRIR_AQUI.ipynb       ← abrir este único notebook
├── INICIAR_JUPYTER.bat   ← Windows: doble clic para abrir Jupyter
├── README.md
├── requirements.txt
├── ejecutar_todo.py       ← opción sin Jupyter
├── src/
│   ├── auditoria.py       ← etapa 1: HTML + RDF/XML
│   ├── normalizar_catalogo.py  ← etapa 2: grafo normalizado
│   ├── mc_etapa3.py       ← etapa 3: RDF de documentos pendientes
│   └── pipeline.py        ← encadena etapas + crea ZIP
├── tests/
└── data/
    └── output/
        ├── etapa1/                         ← se crea al ejecutar
        ├── etapa1.zip                      ← automático
        ├── etapa2/                         ← se crea al ejecutar
        ├── etapa2.zip                      ← automático
        ├── etapa3/                         ← se crea al ejecutar
        ├── etapa3.zip                      ← automático
        ├── RESUMEN_PIPELINE.json
        └── MEMORIA_CHILENA_RESULTADOS.zip  ← compartir este
```

### Alternativa sin notebook

Desde la raíz del proyecto:

```powershell
python -m pip install -r requirements.txt
python ejecutar_todo.py
```

## Qué hace

- **Etapa 1:** consulta un minisitio y dos fichas semilla; reconoce los enlaces de su sección *Documentos*, descarga los RDF asociados y exporta un informe CSV/JSON/Turtle y `etapa1.zip`.
- **Etapa 2:** lee **automáticamente `etapa1.zip`**; crea relaciones de catalogación con procedencia, no hechos históricos, y genera `etapa2.zip`.
- **Etapa 3:** lee **automáticamente `etapa2.zip`**; visita las fichas documentales, recupera RDF que falte, registra derechos y enlaces de descarga **sin bajar libros ni PDF**; genera `etapa3.zip`.
- **Entrega:** comprime los tres ZIP y un resumen en `MEMORIA_CHILENA_RESULTADOS.zip`.

Los resultados dependen del estado actual del portal, la conexión y de las respuestas RDF. No se fuerzan números como “93 triples” o “221 triples”. Si hay un error de red o cambios HTML se reportan; se conserva la salida disponible sin inventar datos. Si el minisitio no proporciona ningún enlace documental, la ejecución se detiene después de guardar `etapa1.zip` y un mensaje de error, en vez de fabricar un grafo.

## Reejecución y repositorio GitHub

**Run All Cells** vuelve a consultar la fuente y **reemplaza** los resultados de las carpetas `data/output/etapa1`, `etapa2` y `etapa3` y sus ZIP. Se recomienda no colocar archivos propios dentro de esas carpetas. Los resultados están excluidos de Git mediante `.gitignore` por prudencia respecto de datos descargados. Puedes versionar el código, el README y los tests.

Para comprobar que el código funciona sin internet:

```powershell
python -m pip install pytest
python -m pytest -q
```

## Ética documental y límites del piloto

- El programa aplica pausa de al menos **2,5 segundos** entre solicitudes al mismo servidor, consulta `robots.txt`, utiliza una lista pequeña de fichas y limita el tamaño de respuesta.
- Si el portal cambia los permisos o bloquea las solicitudes, no se intenta eludir esas restricciones.
- Los enlaces de la sección Documentos indican **inclusión editorial**, no causalidad ni influencia histórica.
- La normalización introduce un vocabulario local `urn:mcgraphrag:`; el RDF original se conserva por separado.
- En etapa 3 se registran enlaces y etiquetas de derechos, pero no se descargan publicaciones completas, ni se realiza OCR o generación de respuestas. **Este proyecto es todavía una auditoría documental previa al RAG.**
- Antes de compartir objetos digitales o sus transcripciones, verificar las condiciones específicas de uso de cada ficha.

## Primer caso

Minisitio *La religiosidad andina*: https://www.memoriachilena.gob.cl/602/w3-article-790.html

Repositorio previsto: `memoria-chilena-graphrag` (no se publica automáticamente en GitHub).
