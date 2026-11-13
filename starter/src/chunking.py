"""Implement fixed-size and structure-aware chunking strategies."""
import re
from .models import Chunk, DocumentPage


def fixed_size(page: DocumentPage, size: int = 500, overlap: int = 50) -> list[Chunk]:
    """Split text into fixed-size character windows with overlap, retaining page metadata."""
    text = page.text
    if not text:
        return []
    
    chunks: list[Chunk] = []
    step = max(1, size - overlap)
    start = 0
    idx = 0
    
    while start < len(text):
        end = min(start + size, len(text))
        chunk_text = text[start:end].strip()
        
        if chunk_text:
            chunk_id = f"{page.document_id}_p{page.page}_fix_{idx:03d}"
            meta = dict(page.metadata)
            meta.update({
                "chunk_type": "fixed_size",
                "char_length": len(chunk_text),
                "start_char": start,
                "end_char": end,
                "section": page.metadata.get("section", ""),
                "chapter": page.metadata.get("chapter", "")
            })
            
            chunks.append(Chunk(
                chunk_id=chunk_id,
                document_id=page.document_id,
                source=page.source,
                page=page.page,
                text=chunk_text,
                metadata=meta
            ))
            idx += 1
            
        if end >= len(text):
            break
        start += step
        
    return chunks


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentences cleanly."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def by_paragraph(page: DocumentPage, max_size: int = 800) -> list[Chunk]:
    """Group paragraphs, split oversized paragraphs by sentences, and retain page metadata."""
    raw_paras = page.text.split("\n\n")
    paras = [p.strip() for p in raw_paras if p.strip()]
    if not paras:
        return []
    
    units: list[str] = []
    for p in paras:
        if len(p) <= max_size:
            units.append(p)
        else:
            # oversized paragraph: split by sentence
            sentences = _split_into_sentences(p)
            current_unit = ""
            for s in sentences:
                if not current_unit:
                    current_unit = s
                elif len(current_unit) + 1 + len(s) <= max_size:
                    current_unit += " " + s
                else:
                    units.append(current_unit)
                    current_unit = s
            if current_unit:
                units.append(current_unit)
                
    # Now pack smaller units together up to max_size
    packed_chunks: list[str] = []
    current_pack = ""
    for u in units:
        if not current_pack:
            current_pack = u
        elif len(current_pack) + 2 + len(u) <= max_size:
            current_pack += "\n\n" + u
        else:
            packed_chunks.append(current_pack)
            current_pack = u
    if current_pack:
        packed_chunks.append(current_pack)
        
    chunks: list[Chunk] = []
    for idx, chunk_text in enumerate(packed_chunks):
        chunk_id = f"{page.document_id}_p{page.page}_para_{idx:03d}"
        meta = dict(page.metadata)
        meta.update({
            "chunk_type": "paragraph_semantic",
            "char_length": len(chunk_text),
            "section": page.metadata.get("section", ""),
            "chapter": page.metadata.get("chapter", "")
        })
        chunks.append(Chunk(
            chunk_id=chunk_id,
            document_id=page.document_id,
            source=page.source,
            page=page.page,
            text=chunk_text,
            metadata=meta
        ))
        
    return chunks
