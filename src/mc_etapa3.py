"""Etapa 3 de Memoria Chilena: ampliar metadatos RDF, auditar enlaces y derechos.

Conserva el grafo de la etapa 2, distingue metadatos originales de las relaciones
catalográficas añadidas y NO descarga ni interpreta documentos digitalizados.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import DC, DCTERMS, PROV, SKOS

SITE = "www.memoriachilena.gob.cl"
MINISITE = "https://www.memoriachilena.gob.cl/602/w3-article-790.html"
MC = Namespace("http://www.memoriachilena.cl/schemas/")
MCG = Namespace("urn:mcgraphrag:")
USER_AGENT = "MemoriaChilenaResearchAudit/0.3 (academic-metadata-pilot)"
PAUSA = 2.5  # robots.txt declara Crawl-Delay: 2; nunca disminuir por debajo de 2.
MAX_BODY = 4_000_000  # RDF/HTML, no archivos completos


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def doc_id(url: str) -> str:
    match = re.search(r"/w3-article-(\d+)\.html$", urlparse(url).path)
    if not match:
        raise ValueError(f"URL documental inesperada: {url}")
    return match.group(1)


def same_site(url: str) -> bool:
    p = urlparse(url)
    return p.scheme == "https" and p.hostname == SITE


class Fetcher:
    """Descargas acotadas con robots, respeto al Crawl-Delay y sin redirecciones externas."""
    def __init__(self, session: requests.Session | None = None, pause: float = PAUSA):
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/rdf+xml,application/xml;q=0.9,*/*;q=0.3"})
        self.pause = max(2.0, float(pause))
        self.last_request = 0.0
        self.robots = RobotFileParser()
        robots_url = f"https://{SITE}/robots.txt"
        result = self.session.get(robots_url, timeout=20, allow_redirects=False)
        result.raise_for_status()
        if len(result.content) > 50_000:
            raise ValueError("robots.txt inusualmente grande")
        self.robots.set_url(robots_url)
        self.robots.parse(result.text.splitlines())
        self.last_request = time.monotonic()
        declared_delay = self.robots.crawl_delay("*")
        if declared_delay is not None:
            self.pause = max(self.pause, float(declared_delay))

    def fetch(self, url: str) -> tuple[bytes, str]:
        if not same_site(url):
            raise ValueError(f"URL fuera del dominio autorizado: {url}")
        if not self.robots.can_fetch(USER_AGENT, url):
            raise PermissionError(f"Ruta no permitida por robots.txt: {url}")
        wait = self.pause - (time.monotonic() - self.last_request)
        if wait > 0:
            time.sleep(wait)
        self.last_request = time.monotonic()
        response = self.session.get(url, timeout=25, allow_redirects=False, stream=True)
        if 300 <= response.status_code < 400:
            target = urljoin(url, response.headers.get("Location", ""))
            response.close()
            if not same_site(target):
                raise ValueError("Redirección externa bloqueada")
            return self.fetch(target)
        response.raise_for_status()
        chunks, total = [], 0
        try:
            for chunk in response.iter_content(65536):
                if not chunk:
                    continue
                chunks.append(chunk)
                total += len(chunk)
                if total > MAX_BODY:
                    raise ValueError("Respuesta >4 MB: no se descarga")
        finally:
            response.close()
        return b"".join(chunks), response.url


def extract_links(html: bytes, base_url: str) -> dict:
    # Priorizar UTF-8 cuando el contenido lo permite; algunas páginas históricas
    # pueden venir en otra codificación y BeautifulSoup las detecta como fallback.
    try:
        html_decoded = html.decode("utf-8-sig")
        soup = BeautifulSoup(html_decoded, "html.parser")
    except UnicodeDecodeError:
        soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    page_title = h1.get_text(" ", strip=True) if h1 else ""
    rdf_links, downloads = [], []
    for a in soup.select("a[href]"):
        label = a.get_text(" ", strip=True)
        href = a.get("href", "").strip()
        url = urljoin(base_url, href)
        if (label.casefold() == "rdf" or urlparse(url).path.endswith(".rdf")) and same_site(url):
            if url not in rdf_links:
                rdf_links.append(url)
        if "descargar" in label.casefold():
            downloads.append({
                "pagina": base_url, "etiqueta": label,
                "url_declarada": url if urlparse(url).scheme in ("http", "https") else href,
                "dominio": urlparse(url).netloc,
                "formato_sugerido_por_extension": Path(urlparse(url).path).suffix.lower() or "sin_extension",
                "enlace_verificado": "no", "archivo_descargado": "no",
            })
    strings = list(soup.stripped_strings)
    rights = ""
    for i, item in enumerate(strings):
        normalized = re.sub(r"\s+", " ", item).strip()
        if normalized.casefold().startswith("propiedad intelectual:"):
            rights = normalized.split(":", 1)[1].strip()
            if not rights and i + 1 < len(strings):
                rights = strings[i + 1].strip()
            break
    return {"titulo_html": page_title, "rdf_links": rdf_links,
            "enlaces_descarga": downloads, "derechos_declarados": rights}


def extract_rdf_metadata(g: Graph, page_url: str) -> dict:
    s = URIRef(page_url)
    def first(p):
        vals = [str(o) for o in g.objects(s, p) if isinstance(o, Literal) and str(o).strip()]
        return vals[0] if vals else ""
    themes, units = set(), set()
    for obj in g.objects(s, DC.subject):
        for lit in g.objects(obj, MC.tema):
            themes.add(str(lit))
    for obj in g.objects(s, DC.relation):
        for lit in g.objects(obj, MC.ut):
            units.add(str(lit))
    return {
        "titulo_rdf": first(DC.title), "autor_rdf": first(DC.creator),
        "fecha_rdf": first(DCTERMS.temporal) or first(DC.date),
        "mcid_rdf": first(MC.mcid), "materias_rdf": " | ".join(sorted(themes)),
        "unidades_rdf": " | ".join(sorted(units)),
        "temas_set": themes, "unidades_set": units,
        "sujeto_presente": any(g.triples((s, None, None))),
    }


def load_stage2(path: Path):
    # No se extraen rutas arbitrarias desde el ZIP: se leen únicamente 2 miembros conocidos.
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        needed = {"grafo_integrado.ttl", "documentos_normalizados.csv"}
        if not needed <= names:
            raise ValueError("El ZIP debe contener grafo_integrado.ttl y documentos_normalizados.csv")
        existing = Graph().parse(data=z.read("grafo_integrado.ttl"), format="turtle")
        reader = csv.DictReader(io.StringIO(z.read("documentos_normalizados.csv").decode("utf-8-sig")))
        docs = list(reader)
    if len({d["url"] for d in docs}) != len(docs):
        raise ValueError("Hay URLs documentales duplicadas")
    return existing, docs


def add_concepts(norm: Graph, s: URIRef, meta: dict):
    for tipo, set_key, pred, nsp, label_pred in [
        ("tema", "temas_set", MCG.hasCatalogSubject, "tema", SKOS.prefLabel),
        ("unidad", "unidades_set", MCG.inCatalogUnit, "unidad", SKOS.notation),
    ]:
        for label in sorted(meta.get(set_key, set())):
            term = URIRef(f"urn:mcgraphrag:{nsp}:{quote(label, safe='')}")
            norm.add((s, pred, term))
            norm.add((term, RDF.type, SKOS.Concept))
            norm.add((term, label_pred, Literal(label)))
            norm.add((term, MCG.sourceVocabularyPredicate, MC.tema if tipo == "tema" else MC.ut))


def write_csv(path: Path, rows: list[dict], columns: list[str]):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_pilot(input_zip: str | Path, output_dir: str | Path, pause: float = PAUSA) -> dict:
    input_zip, output = Path(input_zip), Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    raw_dir = output / "rdf_descargados"
    raw_dir.mkdir(exist_ok=True)
    base_graph, docs = load_stage2(input_zip)
    raw_new, norm_new = Graph(), Graph()
    raw_new.bind("dc", DC)
    raw_new.bind("mc", MC)
    norm_new.bind("mcg", MCG)
    norm_new.bind("skos", SKOS)
    norm_new.bind("prov", PROV)
    fetcher = Fetcher(pause=pause)
    document_rows, download_rows, error_rows = [], [], []

    for index, doc in enumerate(docs, 1):
        url = doc["url"]
        original_known = doc.get("rdf_disponible", "").strip().casefold() == "si"
        current = {
            "url": url, "titulo_catalogo_etapa2": doc.get("titulo", ""),
            "rdf_previo_etapa2": "si" if original_known else "no",
            "html_estado": "no_intentado", "html_sha256": "", "titulo_html": "",
            "rdf_url": doc.get("rdf_url", ""), "rdf_estado": "ya_en_etapa2" if original_known else "no_intentado",
            "rdf_sha256": "", "triples_rdf_obtenidos": "", "derechos_declarados": "",
            "enlaces_descarga_declarados": 0, "titulo_rdf": doc.get("titulo", "") if original_known else "",
            "autor_rdf": doc.get("creador_rdf", ""), "fecha_rdf": doc.get("fecha_rdf", ""),
            "mcid_rdf": doc.get("identificador_mcid", ""), "materias_rdf": doc.get("temas_catalogo", ""),
            "unidades_rdf": doc.get("unidades_catalogo", ""),
            "sujeto_en_rdf": "", "consultado_utc": utc_now(),
        }
        print(f"[{index:02d}/{len(docs):02d}] {doc_id(url)} — {doc.get('titulo','')[:65]}")
        try:
            html, final_html_url = fetcher.fetch(url)
            current["html_estado"] = "ok"
            current["html_sha256"] = sha256(html)
            fields = extract_links(html, final_html_url)
            current["titulo_html"] = fields["titulo_html"]
            current["derechos_declarados"] = fields["derechos_declarados"]
            current["enlaces_descarga_declarados"] = len(fields["enlaces_descarga"])
            download_rows.extend(fields["enlaces_descarga"])
            propios = [x for x in fields["rdf_links"] if f"rdf-article-{doc_id(url)}.rdf" in x]
            if propios:
                current["rdf_url"] = propios[0]
            if original_known:
                current["rdf_estado"] = "ya_en_etapa2_no_duplicar"
            elif not propios:
                current["rdf_estado"] = "sin_enlace_rdf_en_html"
            else:
                rdf_url = propios[0]
                try:
                    rdf_bytes, real_rdf_url = fetcher.fetch(rdf_url)
                    rdf_graph = Graph().parse(data=rdf_bytes, format="xml")
                    current["rdf_estado"] = "ok"
                    current["rdf_url"] = real_rdf_url
                    current["rdf_sha256"] = sha256(rdf_bytes)
                    current["triples_rdf_obtenidos"] = len(rdf_graph)
                    (raw_dir / f"article-{doc_id(url)}.rdf").write_bytes(rdf_bytes)
                    raw_new += rdf_graph
                    meta = extract_rdf_metadata(rdf_graph, url)
                    for key in ("titulo_rdf", "autor_rdf", "fecha_rdf", "mcid_rdf", "materias_rdf", "unidades_rdf"):
                        current[key] = meta[key]
                    current["sujeto_en_rdf"] = "si" if meta["sujeto_presente"] else "no"
                    if meta["sujeto_presente"]:
                        subject = URIRef(url)
                        norm_new.add((subject, MCG.hasRdfMetadataSource, URIRef(real_rdf_url)))
                        add_concepts(norm_new, subject, meta)
                    else:
                        error_rows.append({"url": url, "tipo": "rdf_sin_sujeto_esperado", "detalle": rdf_url})
                except Exception as exc:
                    current["rdf_estado"] = "error"
                    error_rows.append({"url": url, "tipo": "rdf", "detalle": f"{type(exc).__name__}: {exc}"})
        except Exception as exc:
            current["html_estado"] = "error"
            current["rdf_estado"] = "sin_verificar" if not original_known else current["rdf_estado"]
            error_rows.append({"url": url, "tipo": "html", "detalle": f"{type(exc).__name__}: {exc}"})
        document_rows.append(current)

    combined = base_graph + raw_new + norm_new
    (output / "rdf_nuevo_original.ttl").write_text(raw_new.serialize(format="turtle"), encoding="utf-8")
    (output / "normalizacion_incremental.ttl").write_text(norm_new.serialize(format="turtle"), encoding="utf-8")
    (output / "grafo_ampliado.ttl").write_text(combined.serialize(format="turtle"), encoding="utf-8")
    doc_columns = list(document_rows[0].keys()) if document_rows else []
    write_csv(output / "auditoria_documentos.csv", document_rows, doc_columns)
    write_csv(output / "enlaces_descarga.csv", download_rows, ["pagina", "etiqueta", "url_declarada", "dominio", "formato_sugerido_por_extension", "enlace_verificado", "archivo_descargado"])
    write_csv(output / "errores_etapa3.csv", error_rows, ["url", "tipo", "detalle"])
    report = {
        "fecha_utc": utc_now(), "fuente_base": input_zip.name,
        "documentos_catalogados": len(docs),
        "html_ok": sum(d["html_estado"] == "ok" for d in document_rows),
        "rdf_existentes_etapa2": sum(d["rdf_previo_etapa2"] == "si" for d in document_rows),
        "rdf_nuevos_ok": sum(d["rdf_estado"] == "ok" for d in document_rows),
        "rdf_no_obtenidos_nuevos": sum(d["rdf_previo_etapa2"] == "no" and d["rdf_estado"] != "ok" for d in document_rows),
        "enlaces_descarga_declarados_no_verificados": len(download_rows),
        "derechos_declarados_identificados": sum(bool(d["derechos_declarados"]) for d in document_rows),
        "triples_etapa2": len(base_graph), "triples_rdf_nuevos": len(raw_new),
        "triples_normalizacion_adicional": len(norm_new), "triples_grafo_ampliado": len(combined),
        "errores_o_alertas": len(error_rows),
        "advertencias": [
            "No se descargaron PDF/libros completos, ni se procesó OCR.",
            "Los enlaces de descarga se registraron, no se verificó su contenido.",
            "Los conceptos son términos de catalogación; no representan hechos históricos.",
            "Los RDF de los dos documentos ya presentes en etapa 2 no se agregaron nuevamente.",
            "No subir capturas RDF/documentos a repositorios públicos sin revisar sus condiciones de uso.",
        ],
    }
    (output / "informe_etapa3.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md = "# Etapa 3 — Ampliación RDF y auditoría documental\n\n"
    report_md += "| Métrica | Valor |\n|---|---:|\n"
    for key in ("documentos_catalogados", "html_ok", "rdf_existentes_etapa2", "rdf_nuevos_ok", "rdf_no_obtenidos_nuevos", "derechos_declarados_identificados", "enlaces_descarga_declarados_no_verificados", "triples_etapa2", "triples_rdf_nuevos", "triples_normalizacion_adicional", "triples_grafo_ampliado", "errores_o_alertas"):
        report_md += f"| {key} | {report[key]} |\n"
    report_md += "\n## Cautelas\n\n" + "\n".join("- " + note for note in report["advertencias"])
    (output / "INFORME_ETAPA3.md").write_text(report_md + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


def zip_outputs(output_dir: str | Path, path: str | Path):
    """Empaqueta los resultados sin depender de Google Colab."""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(Path(output_dir).rglob("*")):
            if p.is_file():
                z.write(p, arcname=p.relative_to(output_dir))
    return Path(path)
