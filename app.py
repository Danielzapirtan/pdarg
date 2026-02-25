import json
import re
from pathlib import Path

import fitz  # PyMuPDF


INPUT_PATH = Path("/content/drive/MyDrive/input.pdf")
OUTPUT_PATH = Path("/content/drive/MyDrive/exhaustive_toc.json")


ROMAN_RE = r"(?:M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3}))"
ARABIC_RE = r"\d+(?:\.\d+)*"
CHAPTER_KEYWORDS = (
    r"(chapter|capitol|section|part|parte|appendix|anexa|"
    r"introduction|introducere|conclusion|concluzie|"
    r"preface|foreword|epilogue|prologue)"
)


def normalize(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_heading_candidate(text: str) -> bool:
    t = text.strip()

    if len(t) < 3 or len(t) > 300:
        return False

    if re.match(rf"^\s*{CHAPTER_KEYWORDS}\b", t, re.IGNORECASE):
        return True

    if re.match(rf"^\s*{ROMAN_RE}\.?\s+", t):
        return True

    if re.match(rf"^\s*{ARABIC_RE}\s+", t):
        return True

    letters = re.sub(r"[^A-Za-z]", "", t)
    if letters and letters.isupper() and len(letters) > 5:
        return True

    return False


def infer_level(text: str) -> int:
    t = text.strip()

    if re.match(rf"^\s*{ROMAN_RE}\.?\s+", t):
        return 1

    if re.match(r"^\s*\d+\.\d+\.\d+\s+", t):
        return 3

    if re.match(r"^\s*\d+\.\d+\s+", t):
        return 2

    if re.match(r"^\s*\d+\s+", t):
        return 1

    if re.match(rf"^\s*{CHAPTER_KEYWORDS}\b", t, re.IGNORECASE):
        return 1

    return 2


def build_hierarchical_toc(flat_entries):
    root = []
    stack = []

    for entry in flat_entries:
        node = {
            "title": entry["title"],
            "page": entry["page"],
            "children": [],
        }

        level = entry["level"]

        while stack and stack[-1]["level"] >= level:
            stack.pop()

        if not stack:
            root.append(node)
        else:
            stack[-1]["node"]["children"].append(node)

        stack.append({"level": level, "node": node})

    return root


def extract_toc_from_text(pdf_path: Path):
    doc = fitz.open(pdf_path)

    flat_entries = []
    seen_pairs = set()

    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        blocks = page.get_text("blocks")

        lines_in_reading_order = []

        for block in blocks:
            text = normalize(block[4])
            if not text:
                continue

            for line in text.split("\n"):
                candidate = normalize(line)
                if candidate:
                    lines_in_reading_order.append(candidate)

        if not lines_in_reading_order:
            continue

        # Omit page header (assumed first line of page)
        content_lines = lines_in_reading_order[1:]

        for candidate in content_lines:
            if not is_heading_candidate(candidate):
                continue

            level = infer_level(candidate)
            pair_key = (level, candidate.lower())

            if pair_key in seen_pairs:
                continue

            seen_pairs.add(pair_key)

            flat_entries.append(
                {
                    "level": level,
                    "title": candidate,
                    "page": page_index + 1,
                }
            )

    doc.close()

    flat_entries.sort(key=lambda x: (x["page"], x["level"]))
    return flat_entries


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input PDF not found: {INPUT_PATH}")

    flat_toc = extract_toc_from_text(INPUT_PATH)
    hierarchical_toc = build_hierarchical_toc(flat_toc)

    book_structure = {
        "file": str(INPUT_PATH),
        "total_entries": len(flat_toc),
        "toc": hierarchical_toc,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(book_structure, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()