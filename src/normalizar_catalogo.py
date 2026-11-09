"""Etapa 2: normalización de auditoría de metadatos de Memoria Chilena.

Opera SIN INTERNET sobre el ZIP de auditoría. Nunca infiere hechos históricos
ni confunde enlaces de navegación con relaciones entre actores o eventos.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from zipfile import ZipFile

from rdflib import Graph, URIRef, Literal, Namespace, RDF
from rdflib.namespace import DC, DCTERMS, PROV, SKOS

MC = Namespace("urn:mcgraphrag:")
SCHEMA = Namespace("http://www.memoriachilena.cl/schemas/")
MINISITE_CLASS = MC.Minisite
DOCUMENT_CLASS = MC.CatalogDocument
LISTING_CLASS = MC.CatalogListing


def _read_csv(z: ZipFile, name: str) -> list[dict[str, str]]:
    text = z.read(name).decode('utf-8-sig')
    return list(csv.DictReader(io.StringIO(text)))


def _write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def _literal(g: Graph, subject, predicate) -> str:
    return next((str(v) for v in g.objects(subject, predicate) if isinstance(v, Literal) and str(v).strip()), '')


def _named_value(g: Graph, subject, via, term) -> list[str]:
    found = []
    for node in g.objects(subject, via):
        for val in g.objects(node, term):
            if isinstance(val, Literal) and str(val).strip():
                found.append(str(val))
    return sorted(set(found))


def _thematic_values(g: Graph, subject, predicate, subpredicate) -> list[str]:
    return _named_value(g, subject, predicate, subpredicate)


def _normalized_unit(value: str, prefix: str) -> URIRef:
    return URIRef(f"urn:mcgraphrag:{prefix}:{quote(value.strip(), safe='')}")


def build(input_zip: str | Path, output_dir: str | Path) -> dict:
    """Transforma la auditoría en grafo integrado + tablas + informe."""
    input_zip = Path(input_zip)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with ZipFile(input_zip) as z:
        required = {'rdf_original_unido.ttl','enlaces_documentos.csv','resumen.json','paginas.csv'}
        missing = required - set(z.namelist())
        if missing:
            raise ValueError(f"Faltan archivos en ZIP: {', '.join(sorted(missing))}")
        raw = Graph()
        raw.parse(data=z.read('rdf_original_unido.ttl').decode('utf-8-sig'), format='turtle')
        links = _read_csv(z,'enlaces_documentos.csv')
        pages = _read_csv(z,'paginas.csv')
        audit = json.loads(z.read('resumen.json').decode('utf-8-sig'))

    if not links:
        raise ValueError('La auditoría no tiene enlaces documentales')
    if len(raw) != audit['triples_unicos_union']:
        raise ValueError(f"Desajuste: TTL {len(raw)} vs resumen {audit['triples_unicos_union']}")
    html_minisite_urls = sorted(set(r['origen'].strip() for r in links if r['origen'].strip()))
    minisitio = URIRef(str(audit['minisitio']))
    if str(minisitio) not in html_minisite_urls:
        raise ValueError('El minisitio esperado no figura entre los enlaces HTML')
    rdf_pages = {r['url']:r['rdf_propio_url'] for r in pages if (r.get('rdf_propio_url') or '').strip()}

    enrich = Graph()
    for prefix, ns in [('mcg', MC),('dc',DC),('dcterms',DCTERMS),('prov',PROV),('skos',SKOS),('mc', SCHEMA)]:
        enrich.bind(prefix,ns)
    enrich.add((minisitio, RDF.type, MINISITE_CLASS))
    document_urls = sorted(set(row['documento_url'].strip() for row in links))

    for source_url, rdf_url in rdf_pages.items():
        resource = URIRef(source_url)
        if any(raw.triples((resource,None,None))):
            enrich.add((resource, MC.hasRdfMetadataSource, URIRef(rdf_url)))

    link_rows = []
    for row in links:
        source_url = row['origen'].strip()
        document_url = row['documento_url'].strip()
        anchor = row.get('texto_enlace','').strip()
        evidence = row.get('evidencia','').strip()
        source = URIRef(source_url)
        document = URIRef(document_url)
        key = hashlib.sha256(f'{source_url}|{document_url}|{anchor}'.encode('utf-8')).hexdigest()[:16]
        listing = URIRef(f'urn:mcgraphrag:listing:{key}')
        enrich.add((document, RDF.type, DOCUMENT_CLASS))
        enrich.add((source, MC.hasListedDocument, document))
        enrich.add((listing, RDF.type, LISTING_CLASS))
        enrich.add((listing, MC.fromMinisite, source))
        enrich.add((listing, MC.listsDocument, document))
        enrich.add((listing, PROV.wasDerivedFrom, source))
        if anchor:
            enrich.add((listing, MC.anchorText, Literal(anchor)))
        if evidence:
            enrich.add((listing, MC.evidenceDescription, Literal(evidence)))
        link_rows.append({'origen':source_url,'documento_url':document_url,'titulo_enlace':anchor,'evidencia':evidence,'uri_listado':str(listing)})

    original_uri_subjects = sorted({s for s in raw.subjects() if isinstance(s, URIRef)}, key=str)
    topic_rows = []
    topic_set = set()
    for resource in original_uri_subjects:
        for value in _thematic_values(raw,resource,DC.relation,SCHEMA.ut):
            concept = _normalized_unit(value, 'unidad')
            enrich.add((concept, RDF.type, SKOS.Concept))
            enrich.add((concept, SKOS.notation, Literal(value)))
            enrich.add((resource, MC.inCatalogUnit, concept))
            enrich.add((concept, MC.sourceVocabularyPredicate, SCHEMA.ut))
            topic_set.add(('unidad',value))
            topic_rows.append({'recurso':str(resource),'tipo':'unidad','valor_original':value,'concepto_uri':str(concept),'evidencia':'rdf: dc:relation → mc:ut'})
        for value in _thematic_values(raw,resource,DC.subject,SCHEMA.tema):
            concept = _normalized_unit(value, 'tema')
            enrich.add((concept,RDF.type,SKOS.Concept))
            enrich.add((concept,SKOS.prefLabel,Literal(value,lang='es')))
            enrich.add((resource,MC.hasCatalogSubject,concept))
            enrich.add((concept,MC.sourceVocabularyPredicate,SCHEMA.tema))
            topic_set.add(('tema',value))
            topic_rows.append({'recurso':str(resource),'tipo':'tema','valor_original':value,'concepto_uri':str(concept),'evidencia':'rdf: dc:subject → mc:tema'})

    records=[]
    for url in document_urls:
        subject=URIRef(url)
        anchor=next((r['titulo_enlace'] for r in link_rows if r['documento_url']==url),'')
        title=_literal(raw,subject,DC.title) or anchor
        year=_literal(raw,subject,DCTERMS.temporal)
        if year:
            match=re.match(r'^start=(\d{4});end=(\d{4})$',year)
            if match:
                year=match.group(1) if match.group(1)==match.group(2) else f'{match.group(1)}–{match.group(2)}'
        records.append({
            'url':url,'titulo':title,'titulo_procedencia':'rdf:dc:title' if _literal(raw,subject,DC.title) else 'html:texto_enlace',
            'rdf_disponible':'si' if any(raw.triples((subject,None,None))) else 'no',
            'rdf_url':rdf_pages.get(url,''),
            'creador_rdf':_literal(raw,subject,DC.creator),
            'fecha_rdf':year,
            'identificador_mcid':_literal(raw,subject,SCHEMA.mcid),
            'unidades_catalogo':' | '.join(_thematic_values(raw,subject,DC.relation,SCHEMA.ut)),
            'temas_catalogo':' | '.join(_thematic_values(raw,subject,DC.subject,SCHEMA.tema)),
        })

    integrated=Graph()
    for prefix, ns in enrich.namespace_manager.namespaces():
        integrated.bind(prefix, ns)
    for triple in raw:
        integrated.add(triple)
    for triple in enrich:
        integrated.add(triple)

    raw.serialize(destination=str(output_dir/'catalogo_original_93_triples.ttl'),format='turtle')
    enrich.serialize(destination=str(output_dir/'catalogo_normalizado.ttl'),format='turtle')
    integrated.serialize(destination=str(output_dir/'grafo_integrado.ttl'),format='turtle')
    _write_csv(output_dir/'documentos_normalizados.csv',records,['url','titulo','titulo_procedencia','rdf_disponible','rdf_url','creador_rdf','fecha_rdf','identificador_mcid','unidades_catalogo','temas_catalogo'])
    _write_csv(output_dir/'enlaces_catalograficos.csv',link_rows,['origen','documento_url','titulo_enlace','evidencia','uri_listado'])
    _write_csv(output_dir/'conceptos_catalograficos.csv',sorted(topic_rows,key=lambda x:(x['tipo'],x['valor_original'],x['recurso'])),['recurso','tipo','valor_original','concepto_uri','evidencia'])

    report={
        'fuente':'ZIP de auditoría aportado por el usuario',
        'fecha_procesamiento_utc':datetime.now(timezone.utc).isoformat(),
        'minisitio':str(minisitio),
        'triples_rdf_originales':len(raw),
        'predicados_originales':len(set(raw.predicates())),
        'sujetos_uri_originales':len(original_uri_subjects),
        'sujetos_anonimos_originales':len({s for s in raw.subjects() if not isinstance(s, URIRef)}),
        'documentos_en_html':len(document_urls),
        'documentos_con_rdf':sum(r['rdf_disponible']=='si' for r in records),
        'documentos_sin_rdf':sum(r['rdf_disponible']=='no' for r in records),
        'enlaces_html_documentales':len(link_rows),
        'unidades_tematicas_distintas':len({v for t,v in topic_set if t=='unidad'}),
        'temas_catalograficos_distintos':len({v for t,v in topic_set if t=='tema'}),
        'triples_nuevos_normalizacion':len(enrich),
        'triples_grafo_integrado':len(integrated),
        'advertencia':'Los enlaces HTML registran inclusión editorial; NO hechos históricos. Los temas/unidades son etiquetas catalográficas. No hay OCR ni pasajes citables.',
    }
    (output_dir/'informe_etapa2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    md=f"""# Etapa 2 — auditoría y normalización RDF

Fuente: `{input_zip.name}`. Auditoría preliminar de un minisitio.

| Indicador | Valor |
|---|---:|
| Triples originales | {len(raw)} |
| Predicados RDF originales | {report['predicados_originales']} |
| Sujetos con URI en RDF original | {len(original_uri_subjects)} |
| Nodos anónimos en RDF original | {report['sujetos_anonimos_originales']} |
| Documentos enlazados en HTML | {len(document_urls)} |
| Documentos con RDF | {report['documentos_con_rdf']} |
| Documentos sin RDF | {report['documentos_sin_rdf']} |
| Unidades temáticas distintas | {report['unidades_tematicas_distintas']} |
| Temas catalográficos distintos | {report['temas_catalograficos_distintos']} |
| Nuevos triples de normalización | {len(enrich)} |
| Triples en grafo integrado | {len(integrated)} |

**Interpretación:** las diez fichas están **listadas** desde el minisitio. Solo dos
cuentan con metadatos RDF dentro de la auditoría. No se deduce de ello que haya
relaciones históricas entre esas publicaciones. Los nodos anónimos representan
categorías y estructuras de catalogación, no necesariamente personas o eventos.

## Archivos

- `catalogo_original_93_triples.ttl`: RDF original intacto, serializado.
- `catalogo_normalizado.ttl`: relaciones explícitas de catalogación y unidades temáticas.
- `grafo_integrado.ttl`: unión de ambos sin modificar el grafo original.
- `documentos_normalizados.csv`: inventario de las diez fichas, con estado RDF y procedencia del título.
- `enlaces_catalograficos.csv`: evidencia del listado HTML.
- `conceptos_catalograficos.csv`: etiquetas de vocabulario y origen.

## Restricciones de interpretación

- `mcg:hasListedDocument` equivale a **aparece listado en la sección Documentos**.
- `mcg:inCatalogUnit` equivale a **clasificado bajo una unidad temática**.
- `mcg:hasCatalogSubject` equivale a **etiqueta de materia catalográfica**.
- No se han inferido relaciones de causalidad, autoría faltante, influencia, participación ni cronología histórica.
- No hay contenidos de páginas escaneadas ni OCR; no es todavía un RAG con citas por página.

## Prioridad siguiente

Descargar en una auditoría ampliada los RDF de las otras ocho fichas ya identificadas,
conservar el mismo catálogo normalizado, comprobar disponibilidad de texto/documentos y
solo entonces preparar la recuperación documental con trazabilidad de pasajes.
"""
    (output_dir/'INFORME_ETAPA2.md').write_text(md,encoding='utf-8')
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',default='data/input/memoria_chilena_auditoria.zip')
    parser.add_argument('--output',default='data/output/etapa2')
    args=parser.parse_args()
    print(json.dumps(build(args.input,args.output),ensure_ascii=False,indent=2))
