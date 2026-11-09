from pathlib import Path
import sys

import pytest
from rdflib import Graph, URIRef, RDF

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from normalizar_catalogo import build, MC


def test_normalizacion_con_datos_reales(tmp_path):
    report = build(ROOT / 'data/input/memoria_chilena_auditoria.zip', tmp_path)
    assert report['triples_rdf_originales'] == 93
    assert report['predicados_originales'] == 25
    assert report['documentos_en_html'] == 10
    assert report['documentos_con_rdf'] == 2
    assert report['documentos_sin_rdf'] == 8
    assert report['sujetos_anonimos_originales'] == 23

    raw=Graph().parse(tmp_path/'catalogo_original_93_triples.ttl',format='turtle')
    norm=Graph().parse(tmp_path/'catalogo_normalizado.ttl',format='turtle')
    total=Graph().parse(tmp_path/'grafo_integrado.ttl',format='turtle')
    assert len(raw) == 93
    assert len(norm) == report['triples_nuevos_normalizacion']
    assert len(total) == report['triples_grafo_integrado']
    minisite = URIRef('https://www.memoriachilena.gob.cl/602/w3-article-790.html')
    docs = list(norm.objects(minisite,MC.hasListedDocument))
    assert len(docs) == 10
    assert all((doc,RDF.type,MC.CatalogDocument) in norm for doc in docs)
    assert (minisite,RDF.type,MC.Minisite) in norm


def test_cantidad_referencias_catalograficas(tmp_path):
    report=build(ROOT/'data/input/memoria_chilena_auditoria.zip',tmp_path)
    assert report['unidades_tematicas_distintas'] == 7
    assert report['temas_catalograficos_distintos'] == 3
    csv=(tmp_path/'documentos_normalizados.csv').read_text(encoding='utf-8-sig')
    assert 'html:texto_enlace' in csv
    assert 'rdf:dc:title' in csv
    assert 'MC0014753' in csv
