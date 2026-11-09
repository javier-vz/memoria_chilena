"""Orquestador para Jupyter/CLI: etapas 1 → 2 → 3, ZIP automáticos."""
from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from . import auditoria, normalizar_catalogo, mc_etapa3


def fresh_dir(path: Path, root: Path):
    root = root.resolve()
    path = path.resolve()
    # Nunca permitir borrar fuera del destino de resultados del proyecto.
    if path.parent != root:
        raise ValueError("La salida debe ser una subcarpeta directa de data/output")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def zip_dir(directory: Path, zip_path: Path) -> Path:
    """No incluye el ZIP en sí mismo; rutas relativas, sin archivos temporales."""
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for file in sorted(directory.rglob("*")):
            if file.is_file():
                z.write(file, arcname=str(file.relative_to(directory)))
    return zip_path


def run_all(project_root: str | Path) -> dict:
    root = Path(project_root).resolve()
    if not (root / "src" / "pipeline.py").is_file():
        raise ValueError(f"No se reconoce la raíz del proyecto: {root}")
    out = root / "data" / "output"
    out.mkdir(parents=True, exist_ok=True)
    all_results = {}
    paths = []

    print("=" * 60)
    print("ETAPA 1/3 — HTML y RDF de Memoria Chilena (descarga en vivo)")
    print("=" * 60)
    stage1 = out / "etapa1"
    fresh_dir(stage1, out)
    r1 = auditoria.run(stage1)
    zip1 = zip_dir(stage1, out / "etapa1.zip")
    paths.append(zip1)
    all_results["etapa1"] = r1
    print(f"ZIP creado: {zip1}")

    if r1["enlaces_documentales_en_html"] == 0:
        msg = ("La etapa 1 no identificó documentos en el minisitio. "
               "Consulta data/output/etapa1/errores.csv y revisa si cambió el HTML. "
               "Se guardó etapa1.zip; no se generarán grafos falsos.")
        (out / "ERROR_ETAPA1.txt").write_text(msg, encoding="utf-8")
        raise RuntimeError(msg)

    print("\n" + "=" * 60)
    print("ETAPA 2/3 — Normalización y grafo RDF (offline)")
    print("=" * 60)
    stage2 = out / "etapa2"
    fresh_dir(stage2, out)
    r2 = normalizar_catalogo.build(zip1, stage2)
    zip2 = zip_dir(stage2, out / "etapa2.zip")
    paths.append(zip2)
    all_results["etapa2"] = r2
    print(f"ZIP creado: {zip2}")

    print("\n" + "=" * 60)
    print("ETAPA 3/3 — Otras fichas, RDF y derechos (descarga en vivo)")
    print("=" * 60)
    stage3 = out / "etapa3"
    fresh_dir(stage3, out)
    r3 = mc_etapa3.run_pilot(zip2, stage3)
    zip3 = zip_dir(stage3, out / "etapa3.zip")
    paths.append(zip3)
    all_results["etapa3"] = r3
    print(f"ZIP creado: {zip3}")

    all_results["fecha_fin_utc"] = datetime.now(timezone.utc).isoformat()
    all_results["archivos_zip"] = [p.name for p in paths]
    summary = out / "RESUMEN_PIPELINE.json"
    summary.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")
    final_path = out / "MEMORIA_CHILENA_RESULTADOS.zip"
    with zipfile.ZipFile(final_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in [*paths, summary]:
            z.write(p, p.name)
    print("\n✅ TODAS LAS ETAPAS TERMINARON")
    for p in [*paths, final_path]:
        print("   ", p)
    return {"informes": all_results, "zip_final": str(final_path),
            "zips": [str(x) for x in paths]}
