import hashlib
import re
from pathlib import Path


WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def safe_component(value, fallback="paper", limit=120):
    text = re.sub(r'[\\/:*?"<>|\x00-\x1f]', " ", str(value or ""))
    text = re.sub(r"\s+", " ", text).strip(" .")
    if not text:
        text = fallback
    if text.upper() in WINDOWS_RESERVED:
        text = f"_{text}"
    return text[:limit].rstrip(" .") or fallback


def paper_filename(paper):
    year_match = re.search(r"(?:19|20)\d{2}", str(paper.get("year") or ""))
    year = year_match.group(0) if year_match else ""
    title = safe_component(paper.get("title"), limit=105)
    identifier = str(paper.get("article_number") or "").strip()
    if not identifier:
        doi = str(paper.get("doi") or "").strip().lower()
        if doi:
            identifier = hashlib.sha1(doi.encode("utf-8")).hexdigest()[:8]
    parts = [part for part in (year, title, identifier) if part]
    return safe_component("_".join(parts), limit=150) + ".pdf"


def unique_path(output_dir, filename):
    output = Path(output_dir) / filename
    if not output.exists():
        return output
    stem = output.stem
    suffix = output.suffix
    for index in range(2, 1000):
        candidate = output.with_name(f"{stem}_{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Too many files share the same name: {filename}")


def is_pdf_file(path):
    try:
        with open(path, "rb") as handle:
            return b"%PDF-" in handle.read(1024)
    except OSError:
        return False

