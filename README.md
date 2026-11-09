# Memoria Chilena — GraphRAG patrimonial

**Etapas 1 y 2: auditoría de un minisitio y normalización del catálogo RDF.**

Este repositorio de investigación nace de la experiencia de GraphRAG de Qoyllur Rit'i. **Por ahora NO es un RAG funcional:** solo recoge y normaliza metadatos y relaciones editoriales verificables. El material de entrada es una auditoría real del minisitio [La religiosidad andina](https://www.memoriachilena.gob.cl/602/w3-article-790.html), ejecutada el 9 de noviembre de 2026.

## Resultados de la auditoría aportada

| Métrica | Resultado |
|---|---:|
| RDF parseados | 3 (minisitio y dos documentos) |
| Triples RDF originales | 93 |
| Predicados RDF distintos | 25 |
| Sujetos URI propios | 3 |
| Nodos anónimos RDF | 23 |
| Fichas documentales enlazadas desde HTML | 10 |
| Fichas con RDF en esta auditoría | 2 |
| Fichas sin RDF todavía | 8 |

**Advertencia:** los enlaces entre páginas no prueban relaciones históricas. El pipeline modela *listado en el catálogo*, *pertenencia a unidad temática* y *materia catalográfica*, nunca vínculos de causalidad o participación histórica.

## Estructura

```text
memoria-chilena-etapa2/
├── README.md
├── requirements.txt
├── .gitignore
├── notebooks/
│   ├── 01_auditoria_memoria_chilena.ipynb
│   └── 02_normalizacion_catalogo.ipynb
├── src/
│   └── normalizar_catalogo.py
├── tests/
│   └── test_etapa2.py
└── data/
    ├── input/
    │   └── memoria_chilena_auditoria.zip
    └── output/
        └── .gitkeep
```

El ZIP incluido en `data/input` es el resultado que se generó en la etapa 1. No contiene libros digitalizados ni OCR.

## Ejecutar con Jupyter local

Requiere Python 3.10 o superior.

En **Windows PowerShell** (ubicado dentro de la carpeta extraída):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
jupyter lab
```

En **macOS/Linux**:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter lab
```

En la interfaz, abre `notebooks/02_normalizacion_catalogo.ipynb` y selecciona **Run All Cells**. El notebook localiza automáticamente la raíz del proyecto tanto si arrancaste Jupyter desde la raíz como desde `notebooks/`.

No necesita internet. Los resultados aparecen en `data/output/etapa2/` y se pueden descargar desde Jupyter como ZIP.

## Alternativa sin notebook

Desde la carpeta raíz:

```bash
python src/normalizar_catalogo.py --input data/input/memoria_chilena_auditoria.zip --output data/output/etapa2
python -m pytest -q
```

## Archivos de salida

- `catalogo_original_93_triples.ttl`: copia reserializada del RDF de entrada, manteniendo la semántica original.
- `catalogo_normalizado.ttl`: tipos de recursos, listados documentales y etiquetas normalizadas.
- `grafo_integrado.ttl`: unión del grafo original con la capa de normalización.
- `documentos_normalizados.csv`: diez fichas, título y procedencia, disponibilidad de RDF, creador, fecha e identificadores cuando hay evidencia.
- `enlaces_catalograficos.csv`: la evidencia de enlaces HTML del minisitio a documentos.
- `conceptos_catalograficos.csv`: unidades temáticas y materias de catálogo.
- `informe_etapa2.json` y `INFORME_ETAPA2.md`: auditoría cuantitativa y limitaciones.

## Vocabulario añadido

Se reutilizan los **URI originales de Memoria Chilena** para sus páginas. Los identificadores que creamos localmente comienzan con `urn:mcgraphrag:`; son identificadores del proyecto, no identificadores oficiales de la Biblioteca Nacional.

| Propiedad | Significado verificado |
|---|---|
| `mcg:hasListedDocument` | El HTML del minisitio lista una ficha documental |
| `mcg:inCatalogUnit` | La ficha pertenece a una unidad temática indicada por `mc:ut` |
| `mcg:hasCatalogSubject` | La ficha incluye una materia de `mc:tema` |
| `prov:wasDerivedFrom` | Identifica la página HTML de la que procede el listado |
| `mcg:hasRdfMetadataSource` | Dirección RDF asociada a la ficha |

La capa original RDF se mantiene separada de la capa derivada para facilitar la auditoría. Las cadenas de las unidades temáticas se conservan tal como aparecen, sin inventar títulos legibles.

## Próxima etapa: ampliar RDF y obtener texto verificable

1. Descargar responsablemente los RDF de las otras ocho fichas, mediante consultas espaciadas y respetando las condiciones del portal.
2. Verificar por documento el acceso a texto, OCR o imágenes, además de derechos de uso.
3. Crear *chunks* con `documento`, `página`, `fragmento`, `fuente` y `método de extracción`.
4. Implementar un baseline BM25/FAISS y luego GraphRAG con expansión catalográfica explícita.
5. Evaluar con preguntas históricas contrastadas y citas a documentos, sin confundir fuentes primarias con textos curatoriales.

**Derechos:** los metadatos y las reproducciones digitalizadas pueden tener condiciones diferentes. Este repositorio no redistribuye objetos digitales ni presupone una licencia para ellos; verificar cada ficha antes de añadir materiales.
