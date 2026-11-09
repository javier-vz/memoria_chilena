# Memoria Chilena · Auditoría RDF para un futuro GraphRAG

**Etapa 1 — Auditoría de fuentes históricas y metadatos**  
Proyecto piloto: [La religiosidad andina — Memoria Chilena](https://www.memoriachilena.gob.cl/602/w3-article-790.html).

Este repositorio prepara el corpus para un **GraphRAG patrimonial verificable**. La primera etapa no genera respuestas con un LLM: verifica cómo se publican los metadatos RDF/XML y los enlaces editoriales, y conserva su procedencia antes de proponer una ontología. Se inspira en la arquitectura ya desarrollada en [graphrag_qoyllurity](https://github.com/javier-vz/graphrag_qoyllurity), pero no presupone que la estructura semántica de ambos proyectos sea idéntica.

## 1. Estructura

```text
memoria-chilena-graphrag/
├── README.md
├── requirements.txt
├── .gitignore
├── notebooks/
│   └── 01_auditoria_memoria_chilena.ipynb
├── src/
│   ├── __init__.py
│   └── mc_audit.py
├── tests/
│   └── test_parser.py
├── data/
│   └── .gitkeep
└── outputs/
    └── .gitkeep
```

`data/raw/rdf/` contendrá los archivos RDF/XML recuperados de forma correcta. `outputs/auditoria_01/` contendrá los análisis en CSV, JSON y TTL. No se versionan por defecto: deben revisarse los derechos y las condiciones del portal antes de redistribuir datos.

## 2. Instalar y ejecutar en Jupyter local

**Requisitos:** Python 3.10 o superior, JupyterLab o Jupyter Notebook y conexión a Internet para consultar las fichas. El código se ejecuta en Windows, macOS o Linux, sin Google Colab y sin Google Drive.

En la **raíz del proyecto**, crear y activar un entorno virtual:

```bash
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m ipykernel install --user --name memoria-chilena --display-name "Python (Memoria Chilena)"
jupyter lab
```

**macOS / Linux:**

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m ipykernel install --user --name memoria-chilena --display-name "Python (Memoria Chilena)"
jupyter lab
```

Abrir `notebooks/01_auditoria_memoria_chilena.ipynb`, elegir el kernel **Python (Memoria Chilena)** y ejecutar las celdas en orden. Si Windows no reconoce `python`, probar `py -3`. También puedes usar Jupyter Notebook clásico si ya está instalado y sus dependencias cumplen los requisitos.

La ruta del proyecto se detecta tanto si Jupyter se inicia desde la raíz como desde `notebooks/`. No hay instalaciones automáticas dentro del notebook ni dependencias de `google.colab`.

## 3. Qué audita por defecto

Un piloto de **tres páginas** (máximo seis solicitudes de contenido, si cada página publica su RDF):

1. Minisitio: `https://www.memoriachilena.gob.cl/602/w3-article-790.html`.
2. Ficha documental: `https://www.memoriachilena.gob.cl/602/w3-article-8648.html`.
3. Ficha documental: `https://www.memoriachilena.gob.cl/602/w3-article-8649.html`.

Se comprueba `robots.txt` y se respeta una espera de al menos **2,5 segundos** entre peticiones; si el portal publica una pausa superior, prevalece esta última. No se siguen redirecciones ni se navega masivamente. Las solicitudes están limitadas a URLs HTML y RDF del portal; no se descargan imágenes, libros ni PDF. Ante errores HTTP, permisos o XML inválido, la ejecución registra los fallos y continúa cuando es posible.

### Configuración opcional

En la celda de configuración del notebook:

```python
from src.mc_audit import Config
cfg = Config(raiz=RAIZ, documentos_adicionales=0, pausa_segundos=2.5)
```

Para ampliar **solo tras revisar la primera auditoría**, puedes establecer `documentos_adicionales=2` para incluir hasta dos fichas más recuperadas del minisitio. El script limita este valor a 10. Para otro minisitio, configura su URL explícitamente y vuelve a verificar el alcance y las condiciones de uso.

## 4. Archivos generados

| Archivo | Interpretación |
|---|---|
| `paginas.csv` | Títulos, referencias, campos de catálogo HTML y huellas SHA-256 |
| `enlaces_documentos.csv` | Enlaces editoriales de la sección «Documentos» |
| `temas_relacionados.csv` | Enlaces editoriales de «Temas relacionados» |
| `resumen_rdf.csv` | URL de cada RDF parseado, recuentos y SHA-256 |
| `triples_rdf.csv` | Triples de cada fuente, preservando URI, tipo, idioma y datatype |
| `predicados_rdf.csv` | Frecuencia de predicados observados |
| `rdf_original_unido.ttl` | Unión de triples RDF (solo si alguno se pudo parsear) |
| `errores.csv` | Errores de consulta o de parseo, con URL y etapa |
| `resumen.json` | Recuento final de la auditoría |

La celda final crea un ZIP de los resultados **localmente** si se quiere compartir la auditoría. Los archivos originales RDF/XML permanecen aparte en `data/raw/rdf/`, junto con sus SHA-256 consignados en `resumen_rdf.csv`.

**Cuidado interpretativo:** un enlace del minisitio a un documento significa que el **portal los vincula editorialmente**; no demuestra por sí solo una relación histórica entre los contenidos. Se conservan por separado las relaciones RDF publicadas y los enlaces HTML. Ninguna entidad o arista histórica se infiere en esta etapa.

## 5. Verificación del código

Ejecutar pruebas *sin depender del portal*:

```bash
python -m unittest discover -s tests -v
```

Estas pruebas comprueban el delimitado de la sección Documentos, los temas relacionados, algunos metadatos HTML y la restricción de URLs. **No sustituyen una ejecución real**: el acceso al servidor y la validez de los RDF deberán comprobarse en Jupyter con conexión a Internet.

## 6. Derechos y límites del piloto

Fuente: **Memoria Chilena, Biblioteca Nacional de Chile**. Los textos de investigación del portal y los objetos digitalizados pueden tener condiciones de uso diferentes; revisar la [sección de preguntas frecuentes](https://www.memoriachilena.gob.cl/602/w3-article-123838.html) y los derechos de cada ficha antes de descargar, publicar o redistribuir contenido. La publicación de metadatos RDF no implica permiso general para descargar ni republicar toda la biblioteca.

`robots.txt`: https://www.memoriachilena.gob.cl/robots.txt. Este proyecto utiliza un volumen mínimo de consultas y registra los fallos; si la política cambia, se deberá cumplir la nueva versión.

## 7. Criterios para avanzar a la etapa 2

- Revisar `predicados_rdf.csv`: ¿cuántas propiedades son literales y cuántas apuntan a otras URI?
- Vincular por identificador las fichas HTML y los nodos RDF donde esté documentado.
- Separar metadatos originales, relaciones curatoriales y relaciones propuestas por extracción.
- Diseñar un **grafo documental con procedencia** (Dublin Core + PROV-O; CIDOC CRM solo donde sea útil).
- Recién después implementar **BM25 + embeddings + expansión en grafo** y comparar con un RAG textual sobre preguntas evaluadas manualmente.

**Estado:** notebook y tests locales preparados. La auditoría remota debe ejecutarse en una máquina con acceso a Memoria Chilena; este repositorio no presenta cifras RDF que no hayan sido observadas.
