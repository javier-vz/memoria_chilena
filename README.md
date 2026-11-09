# Memoria Chilena — Auditoría RDF y preparación de GraphRAG

Proyecto Jupyter reproducible para estudiar la información documental del minisitio **La religiosidad andina** de [Memoria Chilena](https://www.memoriachilena.gob.cl/602/w3-article-790.html).

**Solo se ejecutan tres notebooks**, en orden. No hay `.bat`, scripts que abrir ni archivos ZIP de entrada que copiar. Los notebooks están en `notebooks/` y crean automáticamente `data/output/`, sin rutas que cambiar.

## Empezar de cero

1. Descomprime el proyecto. Abre Jupyter/JupyterLab **en la carpeta `memoria_chilena`** y entra en `notebooks/`.
2. Ejecuta **`notebooks/01_Auditoria.ipynb` → Run All Cells**. Espera a que muestre que terminó la etapa 1.
3. Ejecuta **`notebooks/02_Normalizacion.ipynb` → Run All Cells**.
4. Ejecuta **`notebooks/03_Ampliacion.ipynb` → Run All Cells**.

Los notebooks instalan sus dependencias principales (`requests`, `beautifulsoup4` y `rdflib`) desde una celda `%pip`. Si necesitas preparar Jupyter desde cero, en una terminal dentro de la carpeta del proyecto ejecuta:

```bash
python -m pip install -r requirements.txt
jupyter lab
```

> No tienes que escribir rutas, pegar ZIP ni ejecutar archivos `.bat`. Puedes borrar o respaldar la versión anterior antes de reemplazarla; esta distribución es independiente y no necesita datos anteriores.

## Estructura del proyecto

```text
memoria_chilena/
├── notebooks/
│   ├── 01_Auditoria.ipynb
│   ├── 02_Normalizacion.ipynb
│   └── 03_Ampliacion.ipynb
├── README.md
├── requirements.txt
├── .gitignore
└── data/
    ├── input/          (sin archivos obligatorios)
    └── output/         (se llena automáticamente)
```

## ¿Qué genera?

| Notebook | Acción | Archivo generado automáticamente |
|---|---|---|
| 01 — Auditoría | Consulta 3 páginas piloto, RDF y enlaces documentales, exporta CSV y Turtle. | `data/output/etapa1.zip` |
| 02 — Normalización | Lee etapa 1, conserva el RDF y añade enlaces curatoriales con procedencia. | `data/output/etapa2.zip` |
| 03 — Ampliación | Consulta las 10 fichas identificadas y amplía los RDF y la auditoría de derechos/enlaces. | `data/output/etapa3.zip` |
| 03 — Entrega | Empaqueta los tres ZIP. | `data/output/MEMORIA_CHILENA_RESULTADOS.zip` |

**Para continuar el análisis**, comparte solo `data/output/MEMORIA_CHILENA_RESULTADOS.zip`.

## Qué significa — y qué no significa — este piloto

- Se recopilan **metadatos RDF y HTML**, no libros completos ni PDF escaneados.
- Los enlaces entre un minisitio y documentos significan **listados curatoriales**, no relaciones históricas demostradas.
- Los RDF publicados por el portal se preservan separados de los triples añadidos por nuestra normalización.
- Los números de triples pueden variar si cambia el portal o alguna ficha deja de estar disponible.
- Una descarga fallida se registra en los reportes CSV/JSON. **No se inventan datos** para completar el catálogo.
- Se respeta `robots.txt` y una pausa entre solicitudes. Antes de publicar material descargado, revisa derechos y condiciones de cada objeto.
- Esta versión es una **auditoría de fuentes para un futuro GraphRAG**: todavía no implementa embeddings, búsqueda híbrida ni generación de respuestas.

## Publicación en GitHub

Sube los notebooks, `README.md`, `requirements.txt` y `.gitignore`. La carpeta `data/output/` está ignorada para evitar publicar automáticamente respuestas del servidor y materiales con derechos no revisados. Si deseas publicar resultados derivados, revísalos primero.
