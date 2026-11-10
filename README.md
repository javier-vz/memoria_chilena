# Memoria Chilena — GraphRAG patrimonial

Proyecto Jupyter para el piloto **La religiosidad andina**, con procedencia RDF y documentos textuales.

## Estructura

```text
memoria_chilena/
├── notebooks/
│   ├── 01_Auditoria.ipynb
│   ├── 02_Normalizacion.ipynb
│   ├── 03_Ampliacion.ipynb
│   └── 04_Corpus_Textual.ipynb
├── data/
│   ├── input/MEMORIA_CHILENA_RESULTADOS.zip
│   ├── output/
│   └── pdf/
├── README.md
├── requirements.txt
└── .gitignore
```

## Cómo continuar (sin repetir etapas anteriores)

1. Descomprime el proyecto en una carpeta nueva o reemplaza tu copia local.
2. Abre Jupyter desde la carpeta del proyecto (o desde `notebooks/`).
3. Ejecuta **solo `notebooks/04_Corpus_Textual.ipynb`**, *Run All Cells*.
4. Envía **`data/output/etapa4.zip`** para revisar calidad del texto y decidir OCR / índice híbrido.

El ZIP **`MEMORIA_CHILENA_RESULTADOS.zip` ya está colocado** en `data/input/` para trabajar inmediatamente. Para repetir la investigación desde cero, ejecuta 01, 02 y 03 en orden; estos notebooks seguirán generando sus ZIP como antes. Si repites las etapas 1–3, el notebook 04 detectará automáticamente el ZIP nuevo en `data/output/`; en caso contrario usará la copia incluida en `data/input/`. No hay que mover nada.

Instala las dependencias en el entorno de Jupyter: `python -m pip install -r requirements.txt`.

## Controles de derechos y calidad

El notebook 04 descarga localmente, por defecto, solo PDFs cuyas fichas aparecen como **«Patrimonio cultural común»** (6 de 10 en la auditoría). Las otras cuatro se omiten. La clasificación catalográfica **no constituye una licencia de redistribución**; revisa condiciones antes de usar texto completo públicamente o entrenar modelos. Los PDFs y ZIP de trabajo están ignorados por Git y **no deben subirse a un repositorio público**. Los PDF se limitan a 35 MB por archivo, con pausas entre solicitudes. No se hace OCR automáticamente y se informa del porcentaje de páginas sin texto extraíble.

## Siguiente paso

Después de la etapa 4, evaluar cobertura OCR y hacer etapa 5: índice híbrido BM25/FAISS + expansión de grafo + respuestas con citas de documento y página.
