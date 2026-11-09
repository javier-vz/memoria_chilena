"""Etapa 1: auditoría EN VIVO del minisitio y RDF de tres páginas.

Reproduce el esquema CSV/TTL del primer piloto para alimentar la Etapa 2.
Solo extrae HTML y metadatos RDF; no PDF, ni OCR, ni inferencias históricas.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag
from rdflib import Graph

from .mc_etapa3 import Fetcher, MINISITE, SITE, doc_id

# Dos fichas semilla conocidas. No se supone que sus URLs o RDF funcionen
# en cada ejecución: registramos los fallos, sin generar datos ficticios.
FICHAS_SEMILLA = [
    "https://www.memoriachilena.gob.cl/602/w3-article-8648.html",
    "https://www.memoriachilena.gob.cl/602/w3-article-8649.html",
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def soup_html(raw: bytes) -> BeautifulSoup:
    try:
        return BeautifulSoup(raw.decode("utf-8-sig"), "html.parser")
    except UnicodeDecodeError:
        return BeautifulSoup(raw, "html.parser")


def links_from_documents_section(soup: BeautifulSoup, page_url: str) -> list[dict]:
    """Solo los enlaces bajo el encabezado 'Documentos', no menú general."""
    headers = soup.find_all(re.compile(r"^h[1-6]$"))
    inicio = next((h for h in headers if normalize(h.get_text(" ", strip=True)).casefold() == "documentos"), None)
    if inicio is None:
        return []
    links, seen = [], set()
    for element in inicio.next_elements:
        if not isinstance(element, Tag):
            continue
        if element.name in {"h2", "h3"} and element is not inicio:
            name = normalize(element.get_text(" ", strip=True)).casefold()
            if name in {"imágenes", "imagenes", "audiovisual", "cronología", "cronologia", "bibliografía", "bibliografia"}:
                break
        if element.name != "a" or not element.get("href"):
            continue
        url = urljoin(page_url, element["href"])
        label = normalize(element.get_text(" ", strip=True))
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != SITE:
            continue
        if not re.fullmatch(r"/602/w3-article-\d+\.html", parsed.path):
            continue
        if not label or label.casefold() in {"descargar", "rdf", "imprimir"} or url in seen:
            continue
        seen.add(url)
        links.append({
            "origen": page_url, "documento_url": url, "texto_enlace": label,
            "evidencia": "enlace en sección Documentos del HTML",
        })
    return links


def own_rdf_link(soup: BeautifulSoup, page_url: str) -> tuple[list[str], str]:
    own = f"rdf-article-{doc_id(page_url)}.rdf"
    urls = []
    for a in soup.select("a[href]"):
        href = urljoin(page_url, a.get("href", "").strip())
        if urlparse(href).hostname != SITE:
            continue
        if urlparse(href).path.lower().endswith(".rdf") and href not in urls:
            urls.append(href)
    target = next((u for u in urls if own in urlparse(u).path), "")
    return urls, target


def write_csv(path: Path, rows: list[dict], columns: list[str]):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run(output: str | Path, fetcher: Fetcher | None = None) -> dict:
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    raw_dir = output / "rdf_original"
    raw_dir.mkdir(exist_ok=True)

    fetcher = fetcher or Fetcher(pause=2.5)
    pages, links, errors, sources, triple_rows, rdf_rows = [], [], [], [], [], []
    raw_graph = Graph()
    seed_pages = [MINISITE] + FICHAS_SEMILLA
    for url in seed_pages:
        try:
            raw_html, html_url = fetcher.fetch(url)
            soup = soup_html(raw_html)
            h1 = soup.find("h1")
            title = normalize(h1.get_text(" ", strip=True)) if h1 else ""
            rdf_urls, own = own_rdf_link(soup, url)
            pages.append({"url": url, "titulo": title, "http": 200,
                          "rdf_total_enlaces": len(rdf_urls), "rdf_propio_url": own,
                          "n_caracteres_html": len(raw_html)})
            if own:
                sources.append({"pagina_url": url, "titulo": title, "rdf_url": own})
            if url == MINISITE:
                links = links_from_documents_section(soup, html_url)
            print(f"  HTML OK — {title[:60]} | enlace RDF propio: {'sí' if own else 'no'}")
        except Exception as e:
            errors.append({"etapa": "html", "url": url, "error": f"{type(e).__name__}: {e}"})
            print(f"  ERROR HTML {url}: {e}")

    # Guardar cada RDF antes de parsear, para facilitar el diagnóstico.
    for item in sources:
        url = item["rdf_url"]
        try:
            content, resolved = fetcher.fetch(url)
            did = doc_id(item["pagina_url"])
            (raw_dir / f"article-{did}.rdf").write_bytes(content)
            partial = Graph()
            partial.parse(data=content, format="xml", publicID=resolved)
            raw_graph += partial
            for s, p, o in partial:
                triple_rows.append({"pagina_origen": item["pagina_url"],
                                    "rdf_origen": resolved, "sujeto": str(s),
                                    "predicado": str(p), "objeto": str(o),
                                    "objeto_tipo": type(o).__name__})
            rdf_rows.append({"pagina_url": item["pagina_url"], "rdf_url": resolved,
                             "triples": len(partial), "sujetos": len(set(partial.subjects())),
                             "predicados": len(set(partial.predicates())), "bytes": len(content)})
            print(f"  RDF OK — article-{did} | {len(partial)} triples")
        except Exception as e:
            errors.append({"etapa": "rdf", "url": url, "error": f"{type(e).__name__}: {e}"})
            print(f"  ERROR RDF {url}: {e}")

    counts = Counter(row["predicado"] for row in triple_rows)
    pred_rows = [{"predicado": k, "frecuencia": v} for k, v in counts.most_common()]
    write_csv(output / "paginas.csv", pages, ["url", "titulo", "http", "rdf_total_enlaces", "rdf_propio_url", "n_caracteres_html"])
    write_csv(output / "enlaces_documentos.csv", links, ["origen", "documento_url", "texto_enlace", "evidencia"])
    write_csv(output / "resumen_rdf.csv", rdf_rows, ["pagina_url", "rdf_url", "triples", "sujetos", "predicados", "bytes"])
    write_csv(output / "triples_rdf.csv", triple_rows, ["pagina_origen", "rdf_origen", "sujeto", "predicado", "objeto", "objeto_tipo"])
    write_csv(output / "predicados_rdf.csv", pred_rows, ["predicado", "frecuencia"])
    write_csv(output / "errores.csv", errors, ["etapa", "url", "error"])
    # Existe incluso si no se pudo descargar ningún RDF; eso NO se cuenta como éxito.
    raw_graph.serialize(destination=str(output / "rdf_original_unido.ttl"), format="turtle")
    summary = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "minisitio": MINISITE,
        "paginas_html_correctas": len(pages),
        "enlaces_documentales_en_html": len(links),
        "rdf_correctos": len(rdf_rows),
        "triples_unicos_union": len(raw_graph),
        "predicados_distintos": len(set(raw_graph.predicates())),
        "errores": len(errors),
        "advertencia": "Estudio preliminar; enlaces curatoriales NO implican relaciones históricas.",
    }
    (output / "resumen.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("  Resumen etapa 1:", json.dumps(summary, ensure_ascii=False))
    return summary
