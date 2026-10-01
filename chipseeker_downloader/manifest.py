import json
from pathlib import Path


class ManifestError(ValueError):
    pass


def load_manifest(path):
    task_path = Path(path).expanduser().resolve()
    try:
        payload = json.loads(task_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ManifestError(f"Cannot read ChipSeeker task: {exc}") from exc
    if not isinstance(payload, dict):
        raise ManifestError("Task root must be a JSON object.")
    if payload.get("format") != "chipseeker-download-task":
        raise ManifestError("This is not a ChipSeeker download task.")
    if int(payload.get("version", 0) or 0) != 1:
        raise ManifestError(f"Unsupported task version: {payload.get('version')}")
    papers = payload.get("papers")
    if not isinstance(papers, list) or not papers:
        raise ManifestError("The task does not contain any papers.")
    cleaned = []
    for index, raw in enumerate(papers):
        if not isinstance(raw, dict):
            continue
        item = dict(raw)
        item["index"] = index
        item["title"] = str(item.get("title") or f"Paper {index + 1}").strip()
        item["pdf_url"] = str(item.get("pdf_url") or "").strip()
        item["fallback_url"] = str(item.get("fallback_url") or "").strip()
        if not item["pdf_url"] and not item["fallback_url"]:
            item["unavailable_reason"] = "No PDF or fallback URL"
        cleaned.append(item)
    if not cleaned:
        raise ManifestError("The task does not contain any valid paper records.")
    payload["papers"] = cleaned
    payload["task_path"] = str(task_path)
    return payload


def find_latest_manifest(download_dir=None):
    root = Path(download_dir or (Path.home() / "Downloads")).expanduser()
    candidates = list(root.glob("*.csdl"))
    if not candidates:
        candidates = list(root.rglob("*.csdl"))
    if not candidates:
        raise ManifestError(f"No .csdl task was found under {root}")
    return max(candidates, key=lambda item: item.stat().st_mtime)

