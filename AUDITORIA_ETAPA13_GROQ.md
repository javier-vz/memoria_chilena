# Memoria Chilena · Auditoría de etapa 13

**Fecha de revisión:** 2026-11-09 (Perú)  
**Fuente analizada:** `etapa13.zip` recibido del usuario; `comparacion_cinco_preguntas.csv`, `fuentes_que_vio_cada_modelo.csv`, `evaluacion_humana_etapa13.csv`, `informe_etapa13.json`.

## Alcance y resultado de ejecución

- **5 preguntas**, **2 modelos** (Qwen `qwen/qwen3.8-27b` y GPT-OSS `openai/gpt-oss-120b`), **10 respuestas**.
- **10/10** respuestas con `estado=ok` y `finish_reason=stop`; **8 llamadas nuevas** y **2 respuestas reutilizadas** de etapa 12.
- **24 pares pregunta–ficha** de contexto, no 24 documentos únicos (el catálogo de estudio comprende 10 documentos).
- Todas las referencias `[MC...]` citadas en las respuestas pertenecen al contexto recuperado para la respectiva pregunta. **Esto no acredita el respaldo de cada afirmación**.
- Los cuatro campos de puntuación humana (`relevancia_0_2`, `respaldo_catalogo_0_2`, `cautela_historica_0_2`, `claridad_0_2`) siguen vacíos en las diez filas. Por tanto, no existe aún una puntuación empírica de calidad ni un ganador estadísticamente demostrado.

## Revisión cualitativa por pregunta

| Pregunta | Hallazgos | Lectura provisional |
| --- | --- | --- |
| Evangelización | Ambos recuperan *Doctrina christiana* `[MC0014753]` como fuente directa. Qwen distingue claramente a las crónicas como conexiones temáticas; GPT-OSS sugiere conexiones con la actividad evangelizadora que las fichas no prueban. | **Qwen más cauteloso**. |
| Lengua aymara | Ambos reconocen *Vocabulario de la lengua aymara* `[MC0014761]` y *Doctrina christiana* `[MC0014753]`. GPT-OSS afirma que la obra de Acosta incluye referencias al aymara; la unidad catalográfica `elpuebloaymara` no prueba por sí sola menciones en el texto. | **Qwen más fiel a los límites del catálogo**. |
| Idolatría virreinal | Ambos priorizan *Extirpación de la idolatría* `[MC0014760]` y reconocen la referencia del título de *Commentarios reales* `[MC0014755]`. Algunas caracterizaciones adicionales de género, finalidad o intervención no están demostradas por los títulos. | **Ambos útiles, con cautelas**. |
| Fiesta de La Tirana | Ambos seleccionan *La Tirana de Tarapacá* `[MC0023126]`. GPT-OSS afirma que otras obras no mencionan la fiesta; solo podemos decir que **el catálogo no documenta esa mención**, salvo que se inspeccionen los textos completos. Qwen expresa mejor esa limitación. | **Qwen más cauteloso**. |
| Geografía cultural norte de Chile | Ambos identifican *La Tirana de Tarapacá* `[MC0023126]` y *El Altiplano de Arica* `[MC0023128]`. Ambos discriminan adecuadamente el título sobre bailes chinos en Chile central. | **Resultado comparable**. |

**Preferencia operativa provisional:** Qwen, por la cautela de varias respuestas. No es una prueba estadística de superioridad.

## Riesgos detectados

1. **Cita válida ≠ afirmación respaldada.** La pertenencia de un MCID al contexto solo comprueba la identidad de la fuente recuperada.
2. **Relación curatorial ≠ hecho histórico.** La etiqueta compartida `religiosidadandina` y otras unidades no demuestran que una obra mencione una celebración, lengua o práctica particular.
3. **Ausencia de referencia en metadatos ≠ ausencia en texto.** Evitar la fórmula «no menciona» sin consultar el contenido original.
4. **Fechas heterogéneas.** `start=900;end=900` para `[MC0038290]` y intervalos amplios (`start=1899;end=1999`, `start=1800;end=1999`) no deben emplearse automáticamente como años de publicación.
5. **Corpus piloto pequeño.** El universo actual solo tiene diez fichas; la prueba no demuestra desempeño para el resto de Memoria Chilena.

## Siguiente etapa recomendada

- **Congelar la configuración del prototipo:** recuperador híbrido TF-IDF + MiniLM, con RDF como capa explicativa o variante experimental, y Qwen como LLM predeterminado provisional.
- **Añadir evidencia estructurada a la respuesta:** ficha, campo textual exacto (`título`, `nota`, `autor`, `unidad temática`, `dato de publicación`), valor y MCID; marcar explícitamente `asociación catalográfica` vs. `afirmación sobre contenido`.
- **Separar validación automática de revisión humana:** verificar que el MCID y los valores citados existan en los datos; revisar manualmente las inferencias y las afirmaciones negativas.
- **Ampliar el corpus a varios minisitios representativos**, conservando licencia, procedencia y límites de extracción. Con diez fichas no conviene optimizar excesivamente el modelo.
- Evaluar con preguntas y relevancias juzgadas por personas antes de declarar mejoras sobre la recuperación léxica.

*Este informe es una lectura metodológica del ZIP. No constituye una comprobación externa del contenido completo de las obras ni una evaluación humana independiente con puntuaciones 0–2.*
