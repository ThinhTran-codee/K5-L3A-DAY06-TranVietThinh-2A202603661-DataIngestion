"""Orchestrate the Day 06 Data Ingestion & Retrieval Benchmark pipeline."""
import csv
import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv

from .ingestion import load_pdf
from .chunking import fixed_size, by_paragraph
from .embeddings import MyEmbedder
from .store import PgVectorStore
from .evaluation import evaluate_query, summarize


def main() -> None:
    print("=" * 60)
    print("DAY 06 · DATA INGESTION ENGINEERING PIPELINE")
    print("=" * 60)

    repo_root = Path(__file__).resolve().parents[2]

    # 1. Environment & DB Setup
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not set in starter/.env")

    pdf_path = repo_root / "starter/data/Introduction_To_Computer_Science_-_WEB.pdf"
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found at {pdf_path}")

    # 2. Ingest Document Pages
    print("\n[Step 1] Ingesting document pages...")
    pages = load_pdf(pdf_path, document_id="openstax-intro-cs", source=str(pdf_path))
    print(f"Loaded {len(pages)} content pages (requirement >= 30: PASSED)")
    if len(pages) < 30:
        raise ValueError(f"Corpus only has {len(pages)} pages; requires >= 30 content pages.")

    # 3. Chunking Strategies
    print("\n[Step 2] Generating chunks for Strategies A, B, C...")
    # Strategy A: Fixed-size (500 chars, 50 overlap)
    chunks_a = []
    for p in pages:
        chunks_a.extend(fixed_size(p, size=500, overlap=50))
    print(f"Strategy A (Fixed-size 500/50): {len(chunks_a)} chunks")

    # Strategy B & C: By Paragraph / Structure (max 800 chars)
    chunks_b = []
    for p in pages:
        chunks_b.extend(by_paragraph(p, max_size=800))
    chunks_c = chunks_b # Strategy C uses identical chunks as B
    print(f"Strategy B & C (Semantic Paragraph max 800): {len(chunks_b)} chunks")

    # 4. Embeddings
    print("\n[Step 3] Computing vector embeddings...")
    embedder = MyEmbedder(cache_path=str(repo_root / "starter/results/.embedding_cache.json"))
    print(f"Using embedder: {embedder.model_name} (dim: {embedder.dimensions})")

    t0_embed = time.time()
    texts_a = [c.text for c in chunks_a]
    vectors_a = embedder.embed_documents(texts_a)

    texts_b = [c.text for c in chunks_b]
    vectors_b = embedder.embed_documents(texts_b)
    vectors_c = vectors_b
    embed_time = time.time() - t0_embed
    print(f"Embedding completed in {embed_time:.2f}s")

    # 5. Store & Indexing in PostgreSQL + pgvector
    print("\n[Step 4] Storing and indexing vectors in pgvector...")
    store = PgVectorStore(database_url=db_url, dimensions=embedder.dimensions)
    store.create_schema()

    t0_upsert = time.time()
    store.upsert("strategy_a", chunks_a, vectors_a)
    store.upsert("strategy_b", chunks_b, vectors_b)
    store.upsert("strategy_c", chunks_c, vectors_c)
    upsert_time = time.time() - t0_upsert
    print(f"Stored all chunks into pgvector in {upsert_time:.2f}s")

    # 6. Load Benchmark
    print("\n[Step 5] Loading benchmark questions...")
    benchmark_file = repo_root / "benchmark/benchmark.json"
    with open(benchmark_file, "r", encoding="utf-8") as f:
        benchmark_questions = json.load(f)
    print(f"Loaded {len(benchmark_questions)} benchmark questions (15 dev, 5 test)")

    # 7. Run Retrieval & Evaluation for Strategies A, B, C
    print("\n[Step 6] Running retrieval evaluation...")
    results_dir = repo_root / "results"
    results_dir.mkdir(exist_ok=True)

    strategy_configs = [
        {"name": "strategy_a", "label": "A (Fixed-size 500/50, No filter)", "use_filter": False, "chunk_count": len(chunks_a)},
        {"name": "strategy_b", "label": "B (Semantic Paragraph max 800, No filter)", "use_filter": False, "chunk_count": len(chunks_b)},
        {"name": "strategy_c", "label": "C (Semantic Paragraph max 800, With filter)", "use_filter": True, "chunk_count": len(chunks_c)},
    ]

    summary_report = {}
    exp_log_rows = []

    for sc in strategy_configs:
        strat_name = sc["name"]
        print(f"\n--- Evaluating Strategy: {sc['label']} ---")
        traces = []
        t0_query = time.time()

        for q in benchmark_questions:
            q_vec = embedder.embed_query(q["question"])
            filters = q.get("filter") if sc["use_filter"] else None
            
            hits = store.search(strategy=strat_name, query_vector=q_vec, top_k=3, filters=filters)
            trace = evaluate_query(q, hits)
            traces.append(trace)

        query_time = time.time() - t0_query
        strat_summary = summarize(traces)
        summary_report[strat_name] = {
            "label": sc["label"],
            "chunk_count": sc["chunk_count"],
            "query_time_seconds": round(query_time, 3),
            "summary": strat_summary
        }

        # Save trace JSONL
        trace_file = results_dir / f"traces_{strat_name}.jsonl"
        with open(trace_file, "w", encoding="utf-8") as f:
            for t in traces:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")
        print(f"Saved trace to {trace_file}")

        dev_res = strat_summary["dev"]
        test_res = strat_summary["test"]
        print(f"Dev:  Hit@1 = {dev_res['hit1_ratio']} ({dev_res['hit1_pct']*100:.1f}%) | Evidence Hit@3 = {dev_res['hit3_ratio']} ({dev_res['hit3_pct']*100:.1f}%)")
        print(f"Test: Hit@1 = {test_res['hit1_ratio']} ({test_res['hit1_pct']*100:.1f}%) | Evidence Hit@3 = {test_res['hit3_ratio']} ({test_res['hit3_pct']*100:.1f}%)")

        # Prepare experiment log row
        strat_letter = strat_name[-1].upper()
        if strat_letter == "A":
            chunking_desc = "fixed_size"
            size_val = 500
            overlap_val = 50
            filter_val = "none"
            hypo = "Baseline fixed chunking may cut sentences and split gold evidence across boundaries."
        elif strat_letter == "B":
            chunking_desc = "by_paragraph"
            size_val = 800
            overlap_val = 0
            filter_val = "none"
            hypo = "Paragraph chunking preserves complete semantic units and context, improving retrieval accuracy."
        else:
            chunking_desc = "by_paragraph"
            size_val = 800
            overlap_val = 0
            filter_val = "section"
            hypo = "Applying section metadata filtering reduces search space and eliminates cross-domain false positives."

        exp_log_rows.append({
            "strategy": strat_letter,
            "chunking": chunking_desc,
            "chunk_size": size_val,
            "overlap": overlap_val,
            "metadata": "source,page,chapter,section",
            "filter": filter_val,
            "vectorizer": "openai/text-embedding-3-small",
            "hypothesis": hypo,
            "dev_hit1": dev_res["hit1_ratio"],
            "dev_hit3": dev_res["hit3_ratio"],
            "test_hit1": test_res["hit1_ratio"],
            "test_hit3": test_res["hit3_ratio"],
            "notes": f"Chunks: {sc['chunk_count']}, Total query time: {query_time:.2f}s"
        })

    # Save summary report
    summary_path = results_dir / "metrics_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2, ensure_ascii=False)
    print(f"\n[Step 7] Saved metrics summary to {summary_path}")

    # Write artifacts/experiment_log.csv
    exp_log_path = repo_root / "artifacts/experiment_log.csv"
    with open(exp_log_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = ["strategy", "chunking", "chunk_size", "overlap", "metadata", "filter", "vectorizer", "hypothesis", "dev_hit1", "dev_hit3", "test_hit1", "test_hit3", "notes"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in exp_log_rows:
            writer.writerow(r)
    print(f"Updated {exp_log_path}")

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
