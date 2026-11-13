"""Read and normalize source data according to the manifest."""
import json
import re
import unicodedata
from pathlib import Path
import pypdf
from .models import DocumentPage


def normalize_text(text: str) -> str:
    """Normalize Unicode (NFKC), clean smart quotes, fix hyphens, and standardize whitespace."""
    if not text:
        return ""
    # Unicode NFKC
    text = unicodedata.normalize("NFKC", text)
    # Replace curly quotes and apostrophes
    text = text.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    # Fix hyphenated line breaks (e.g., "comput-\ner" -> "computer")
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    # Replace single line breaks inside paragraphs with space, preserve double line breaks
    paragraphs = text.split("\n\n")
    cleaned_paras = []
    for p in paragraphs:
        # collapse all whitespace inside the paragraph
        cleaned = re.sub(r'\s+', ' ', p).strip()
        if cleaned:
            cleaned_paras.append(cleaned)
    return "\n\n".join(cleaned_paras)


def load_pdf(path: Path, document_id: str, source: str) -> list[DocumentPage]:
    """Extract pages designated in manifest, track physical page numbers and section metadata."""
    repo_root = Path(__file__).resolve().parents[2]
    manifest_path = repo_root / "data/manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        start_page = manifest["corpus_scope"]["selected_start_page"]
        end_page = manifest["corpus_scope"]["selected_end_page"]
        pages_meta = {p["physical_page"]: p for p in manifest["pages"]}
    else:
        # fallback default range
        start_page = 19
        end_page = 55
        pages_meta = {}

    reader = pypdf.PdfReader(str(path))
    pages: list[DocumentPage] = []
    
    for physical_page in range(start_page, end_page + 1):
        raw_text = reader.pages[physical_page - 1].extract_text() or ""
        norm_text = normalize_text(raw_text)
        
        meta = pages_meta.get(physical_page, {})
        section = meta.get("section", "General")
        chapter = meta.get("chapter", "General")
        
        doc_page = DocumentPage(
            document_id=document_id,
            source=source,
            page=physical_page,
            text=norm_text,
            metadata={
                "chapter": chapter,
                "section": section,
                "raw_char_count": len(raw_text),
                "norm_char_count": len(norm_text)
            }
        )
        pages.append(doc_page)
        
    return pages
