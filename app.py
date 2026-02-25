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

    if re.match(r"^\s*\d+\s+", t):
        return 1

    if re.match(r"^\s*\d+\.\d+\s+", t):
        return 2

    if re.match(r"^\s*\d+\.\d+\.\d+\s+", t):
        return 3

    if re.match(rf"^\s*{CHAPTER_KEYWORDS}\b", t, re.IGNORECASE):
        return 1

    return 2


def extract_toc_from_text(pdf_path: Path):
    doc = fitz.open(pdf_path)

    entries = []
    seen_pairs = set()

    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        blocks = page.get_text("blocks")

        for block in blocks:
            text = normalize(block[4])
            if not text:
                continue

            lines = text.split("\n")

            for line in lines:
                candidate = normalize(line)
                if not candidate:
                    continue

                if not is_heading_candidate(candidate):
                    continue

                level = infer_level(candidate)

                pair_key = (level, candidate.lower())
                if pair_key in seen_pairs:
                    continue

                seen_pairs.add(pair_key)

                entries.append(
                    {
                        "level": level,
                        "title": candidate,
                        "page": page_index + 1,
                    }
                )

    doc.close()

    entries.sort(key=lambda x: (x["page"], x["level"]))
    return entries


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input PDF not found: {INPUT_PATH}")

    toc_data = extract_toc_from_text(INPUT_PATH)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(toc_data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()