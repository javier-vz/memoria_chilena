import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zipfile import ZipFile

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DC

from src import auditoria, mc_etapa3
from src.pipeline import run_all

SITE = 'https://www.memoriachilena.gob.cl/602'
MINI = f'{SITE}/w3-article-790.html'


class FakeFetcher:
    def __init__(self, *args, **kwargs):
        pass

    def fetch(self, url):
        if url.endswith('.html'):
            did = mc_etapa3.doc_id(url)
            if did == '790':
                anchors = ''.join(
                    f'<a href="/602/w3-article-{n}.html">Documento {n}</a>'
                    for n in range(8648, 8658)
                )
                html = f'<h1>La religiosidad andina</h1><h2>Documentos</h2>{anchors}<h2>Imágenes</h2>'
            else:
                html = (f'<h1>Ficha {did}</h1>'
                        f'<a href="/602/rdf-article-{did}.rdf">RDF</a>'
                        '<a href="https://example.org/test.pdf">Descargar</a>'
                        '<p>Propiedad intelectual:</p><span>Patrimonio cultural común</span>')
            if did == '790':
                html += '<a href="/602/rdf-article-790.rdf">RDF</a>'
            return html.encode('utf-8'), url
        if url.endswith('.rdf'):
            did = url.split('rdf-article-')[-1].split('.')[0]
            g = Graph()
            g.add((URIRef(f'{SITE}/w3-article-{did}.html'), DC.title, Literal(f'Ficha {did}')))
            return g.serialize(format='xml').encode('utf-8'), url
        raise AssertionError(f'Unexpected URL {url}')


def test_documents_extraction_excludes_other_sections():
    html = '<h2>Documentos</h2><a href="/602/w3-article-8648.html">Uno</a><h2>Imágenes</h2><a href="/602/w3-article-9999.html">No</a>'
    links = auditoria.links_from_documents_section(auditoria.soup_html(html.encode()), MINI)
    assert len(links) == 1
    assert links[0]['documento_url'].endswith('8648.html')


def test_full_pipeline_creates_all_zip_without_prior_inputs():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root/'src').mkdir()
        (root/'src'/'pipeline.py').write_text('marker')
        with patch.object(auditoria, 'Fetcher', FakeFetcher), patch.object(mc_etapa3, 'Fetcher', FakeFetcher):
            result = run_all(root)
            # Run twice to verify automatic overwrite of outputs.
            result = run_all(root)
        output = root/'data'/'output'
        for name in ['etapa1.zip', 'etapa2.zip', 'etapa3.zip', 'MEMORIA_CHILENA_RESULTADOS.zip']:
            assert (output/name).is_file(), name
            with ZipFile(output/name) as z:
                assert z.testzip() is None
        with ZipFile(output/'etapa1.zip') as z:
            a = json.loads(z.read('resumen.json'))
            assert a['enlaces_documentales_en_html'] == 10
            assert a['rdf_correctos'] == 3
            assert a['triples_unicos_union'] == 3
        with ZipFile(output/'etapa2.zip') as z:
            assert 'grafo_integrado.ttl' in z.namelist()
            assert 'documentos_normalizados.csv' in z.namelist()
            assert len(Graph().parse(data=z.read('grafo_integrado.ttl'), format='turtle')) > 3
        with ZipFile(output/'etapa3.zip') as z:
            b = json.loads(z.read('informe_etapa3.json'))
            assert b['documentos_catalogados'] == 10
            assert b['rdf_existentes_etapa2'] == 2
            assert b['rdf_nuevos_ok'] == 8
            assert b['errores_o_alertas'] == 0
        with ZipFile(output/'MEMORIA_CHILENA_RESULTADOS.zip') as z:
            assert set(z.namelist()) == {'etapa1.zip','etapa2.zip','etapa3.zip','RESUMEN_PIPELINE.json'}
        assert result['zip_final'] == str(output/'MEMORIA_CHILENA_RESULTADOS.zip')
