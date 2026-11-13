"""Audit script to perform manual assessment and export five-dimension evidence."""
import json
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
results_dir = repo_root / "results"

def load_traces(strat_name: str) -> list[dict]:
    with open(results_dir / f"traces_{strat_name}.jsonl", "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

traces_a = load_traces("strategy_a")
traces_b = load_traces("strategy_b")
traces_c = load_traces("strategy_c")

# 1. Analyze Test Questions Grounding Quality for A, B, C
test_questions_a = [t for t in traces_a if t["split"] == "test"]
test_questions_b = [t for t in traces_b if t["split"] == "test"]
test_questions_c = [t for t in traces_c if t["split"] == "test"]

print("=== TEST TRACES AUDIT ===")
for qa, qb, qc in zip(test_questions_a, test_questions_b, test_questions_c):
    qid = qa["question_id"]
    gold_page = qa["gold_page"]
    q_text = qa["question"]
    print(f"\nQuestion [{qid}]: {q_text} (Gold Page: {gold_page})")
    print(f"  Strategy A hits: {[h['page'] for h in qa['hits']]} | Evidence Hit@3: {qa['evidence_hit_at_3']}")
    print(f"  Strategy B hits: {[h['page'] for h in qb['hits']]} | Evidence Hit@3: {qb['evidence_hit_at_3']}")
    print(f"  Strategy C hits: {[h['page'] for h in qc['hits']]} | Evidence Hit@3: {qc['evidence_hit_at_3']}")
    if qa["hits"]:
        print(f"  A Top-1 preview: p.{qa['hits'][0]['page']} | {qa['hits'][0]['text'][:80]}...")
    if qb["hits"]:
        print(f"  B Top-1 preview: p.{qb['hits'][0]['page']} | {qb['hits'][0]['text'][:80]}...")
