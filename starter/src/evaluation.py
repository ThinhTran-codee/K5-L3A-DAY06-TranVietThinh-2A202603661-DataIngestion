"""Evaluate retrieved evidence, calculate Hit@1 and Evidence Hit@3, and preserve full traces."""
import re
from typing import Any


def _normalize_for_match(text: str) -> str:
    """Normalize text and collapse spaces for robust evidence substring matching."""
    text = text.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    return re.sub(r'\s+', ' ', text).strip().lower()


def is_evidence_hit(question: dict[str, Any], hit: dict[str, Any]) -> bool:
    """A chunk is a valid evidence hit if it is on the gold page and contains the evidence quote."""
    if hit["page"] != question["gold_page"]:
        return False
    
    quote_norm = _normalize_for_match(question["evidence_quote"])
    text_norm = _normalize_for_match(hit["text"])
    
    # Substring match on normalized text
    return quote_norm in text_norm


def evaluate_query(question: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    """Check hits for evidence quote and page matching, recording Hit@1 and Hit@3."""
    annotated_hits = []
    found_hit_at_1 = False
    found_hit_at_3 = False

    for idx, h in enumerate(hits[:3]):
        hit_match = is_evidence_hit(question, h)
        if idx == 0 and hit_match:
            found_hit_at_1 = True
        if hit_match:
            found_hit_at_3 = True

        annotated_hits.append({
            "rank": idx + 1,
            "chunk_id": h["chunk_id"],
            "page": h["page"],
            "score": round(h["score"], 4),
            "is_evidence_hit": hit_match,
            "section": h.get("metadata", {}).get("section", ""),
            "chapter": h.get("metadata", {}).get("chapter", ""),
            "text": h["text"]
        })

    trace = {
        "question_id": question["id"],
        "split": question["split"],
        "type": question["type"],
        "question": question["question"],
        "expected_answer": question["expected_answer"],
        "gold_page": question["gold_page"],
        "evidence_quote": question["evidence_quote"],
        "filter": question.get("filter"),
        "hit_at_1": 1 if found_hit_at_1 else 0,
        "evidence_hit_at_3": 1 if found_hit_at_3 else 0,
        "hits": annotated_hits
    }
    return trace


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Hit@1 and Evidence Hit@3 by split (dev / test)."""
    dev_traces = [t for t in traces if t["split"] == "dev"]
    test_traces = [t for t in traces if t["split"] == "test"]

    def calc_metrics(subset: list[dict[str, Any]]):
        n = len(subset)
        if n == 0:
            return {"total": 0, "hit1_ratio": "0/0", "hit3_ratio": "0/0", "hit1_pct": 0.0, "hit3_pct": 0.0}
        hit1 = sum(t["hit_at_1"] for t in subset)
        hit3 = sum(t["evidence_hit_at_3"] for t in subset)
        return {
            "total": n,
            "hit1_count": hit1,
            "hit1_ratio": f"{hit1}/{n}",
            "hit1_pct": round(hit1 / n, 4),
            "hit3_count": hit3,
            "hit3_ratio": f"{hit3}/{n}",
            "hit3_pct": round(hit3 / n, 4)
        }

    return {
        "overall": calc_metrics(traces),
        "dev": calc_metrics(dev_traces),
        "test": calc_metrics(test_traces)
    }
