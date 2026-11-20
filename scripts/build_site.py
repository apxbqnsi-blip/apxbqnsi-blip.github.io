"""Build the public site from the reviewed runtime and the committed catalog.

Only data/game-data.json needs changing for ordinary RV/recipe data updates.
The runtime ZIP is versioned separately; it contains no editable data or editor.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_MARKERS = re.compile(
    rb"(?:[A-Za-z]:[\\/]+(?:Users|Program Files)|gh[pousr]_[A-Za-z0-9]{30,}"
    rb"|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"
)


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"Non-finite JSON number: {value}")


def public_catalog(path):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"),
                      object_pairs_hook=unique_keys, parse_constant=reject_constant)
    # The desktop export may include extraction evidence. It is not site data.
    data.pop("evidence", None)
    data.pop("notes", None)
    for collection in ("rv_levels", "event_crop_presets"):
        for row in data.get(collection, []):
            row.pop("source", None)
    return data


def read_runtime(archive, checksum):
    raw = Path(archive).read_bytes()
    expected = Path(checksum).read_text(encoding="ascii").split()[0].lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected) or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("Runtime ZIP checksum mismatch")
    files = {}
    with zipfile.ZipFile(archive) as bundle:
        for item in bundle.infolist():
            if item.is_dir():
                continue
            name = item.filename
            path = PurePosixPath(name)
            if (path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name
                    or name in files or any(part in {".git", ".github"} for part in path.parts)
                    or path.name.startswith(("editor.", ".env"))
                    or path.suffix.lower() in {".exe", ".zip", ".log", ".map", ".csv"}
                    or (item.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError(f"Non-public or unsafe runtime entry: {name}")
            files[name] = bundle.read(item)
    if "data/game-data.json" in files:
        raise ValueError("Keep the catalog in data/game-data.json, outside the runtime ZIP")
    for name in ("index.html", "catalog-store.js", "catalog-validation.js", "pkg/aniimax_bg.wasm"):
        if name not in files:
            raise ValueError(f"Missing runtime file: {name}")
    return files


def prepare_site(catalog, archive=ROOT / "site.zip", checksum=ROOT / "site.sha256"):
    files = read_runtime(archive, checksum)
    data = public_catalog(catalog)
    encoded = (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    if PRIVATE_MARKERS.search(encoded):
        raise ValueError("Catalog contains a private path or credential marker")
    # The browser and CI use exactly the same schema checks, without storage or UI.
    validator = files["catalog-validation.js"].decode("utf-8")
    program = validator + "\nimport fs from 'node:fs'; validateCatalog(JSON.parse(fs.readFileSync(0, 'utf8')));\n"
    checked = subprocess.run(["node", "--input-type=module", "--eval", program],
                             input=encoded, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if checked.returncode:
        raise ValueError("Catalog validation failed:\n" + checked.stderr.decode("utf-8", errors="replace"))
    levels = [row["level"] for row in data["rv_levels"]]
    regular = sum(not recipe.get("season") for recipe in data["recipes"])
    seasonal = len(data["recipes"]) - regular
    summary = (f"r16-1 web · RV {min(levels)}–{max(levels)} · {regular} regular recipes + "
               f"{seasonal} season recipes. Published game data; no data editor.")
    html = files["index.html"].decode("utf-8")
    html, replacements = re.subn(r'<p class="disclaimer">.*?</p>',
                                 lambda _: f'<p class="disclaimer">{summary}</p>', html, count=1)
    if replacements != 1:
        raise ValueError("Missing catalog summary in index.html")
    files["index.html"] = html.encode("utf-8")
    files["data/game-data.json"] = encoded
    for name, content in files.items():
        if PRIVATE_MARKERS.search(content):
            raise ValueError(f"Private path or credential marker in public file: {name}")
    return files, {"min_rv": min(levels), "max_rv": max(levels),
                   "regular_recipes": regular, "season_recipes": seasonal}


def build(catalog, output, archive=ROOT / "site.zip", checksum=ROOT / "site.sha256"):
    files, summary = prepare_site(catalog, archive, checksum)
    output = Path(output).resolve()
    if output == ROOT or output in ROOT.parents or ".git" in output.parts:
        raise ValueError("Output must be a dedicated site directory")
    # Do not silently retain unreviewed files from an existing output directory.
    if output.exists():
        existing = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()}
        if existing - files.keys():
            raise ValueError("Output contains unrelated files; choose an empty site directory")
    for name, content in files.items():
        target = output.joinpath(*PurePosixPath(name).parts)
        if output not in target.resolve().parents:
            raise ValueError("Output path escapes the site directory")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return {**summary, "public_files": len(files)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/game-data.json")
    parser.add_argument("--output", type=Path, default=ROOT / "_site")
    args = parser.parse_args()
    print(json.dumps(build(args.catalog, args.output)))


if __name__ == "__main__":
    main()
