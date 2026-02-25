import json
import re
from pathlib import Path

import fitz  # PyMuPDF


INPUT_PATH = Path("/content/drive/MyDrive/input.pdf")
OUTPUT_PATH = Path("/content/drive/MyDrive/exhaustive_toc.json")


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_exhaustive_toc(pdf_path: Path):
    doc = fitz.open(pdf_path)
    toc = doc.get_toc(simple=False)  # includes detailed destination info

    results = []

    for item in toc:
        # item structure (PyMuPDF):
        # [level, title, page, dest_dict]
        if len(item) < 3:
            continue

        level = int(item[0])
        title = normalize_text(item[1])
        page = int(item[2]) if item[2] is not None else None

        entry = {
            "level": level,
            "title": title,
            "page": page
        }

        # Include detailed destination info if available
        if len(item) >= 4 and isinstance(item[3], dict):
            dest = item[3]
            entry["destination"] = {
                k: dest[k]
                for k in dest
                if isinstance(dest[k], (int, float, str, list, dict))
            }

        results.append(entry)

    doc.close()
    return results


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input PDF not found: {INPUT_PATH}")

    toc_data = extract_exhaustive_toc(INPUT_PATH)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(toc_data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()