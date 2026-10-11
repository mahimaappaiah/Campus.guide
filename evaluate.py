"""
evaluate.py - Quantitative evaluation harness for the Mount Carmel College RAG pipeline.

Evaluates test cases across 'dev' and 'test' splits:
- Answer Correctness (case-insensitive keyword matching / exact refusal phrase)
- Retrieval Hit Rate (expected source in retrieved chunks)
- Citation Accuracy (correct source cited in answer body)
- Correct Refusals (accuracy on should_refuse=1 subset)
- Latency (seconds per query)

Saves raw results to results_<label>.csv and prints unrounded summary statistics.
"""

import sys
import time
import csv
import argparse
from pathlib import Path
from common import REFUSAL_RESPONSE, TOP_K_RETRIEVAL
from ask import answer_query

TESTS_FILE = Path("tests.csv")


def evaluate_split(split_name: str = None, top_k: int = TOP_K_RETRIEVAL, label: str = "baseline") -> dict:
    if not TESTS_FILE.exists():
        raise FileNotFoundError(f"Test cases file not found: {TESTS_FILE}")

    rows = []
    with open(TESTS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if split_name is None or r["split"].strip().lower() == split_name.strip().lower():
                rows.append(r)

    if not rows:
        raise ValueError(f"No test cases found for split '{split_name}'")

    detailed_results = []
    
    total_count = len(rows)
    correct_answers = 0
    retrieval_hits = 0
    citation_correct = 0
    refusal_correct = 0
    refusal_total = 0
    latencies = []

    for item in rows:
        q_id = item["id"]
        q_split = item["split"]
        question = item["question"]
        expected_src = item["expected_source"].strip()
        expected_kws = [kw.strip().lower() for kw in item["expected_keywords"].split(";") if kw.strip()]
        should_refuse = int(item["should_refuse"].strip())

        t0 = time.perf_counter()
        res = answer_query(question, top_k=top_k)
        elapsed = time.perf_counter() - t0
        latencies.append(elapsed)

        ans = res["answer"].strip()
        retrieved_sources = res.get("sources", [])
        
        # 1. Answer Correctness Check
        if should_refuse == 1:
            refusal_total += 1
            is_answer_correct = (REFUSAL_RESPONSE.lower() in ans.lower())
            if is_answer_correct:
                refusal_correct += 1
        else:
            is_answer_correct = all(kw in ans.lower() for kw in expected_kws)

        if is_answer_correct:
            correct_answers += 1

        # 2. Retrieval Hit Rate Check
        if should_refuse == 1:
            is_retrieval_hit = True  # Refusal query
        else:
            is_retrieval_hit = (expected_src in retrieved_sources)

        if is_retrieval_hit:
            retrieval_hits += 1

        # 3. Citation Accuracy Check
        if should_refuse == 1:
            is_citation_correct = (expected_src == "" or REFUSAL_RESPONSE.lower() in ans.lower())
        else:
            is_citation_correct = (expected_src.lower() in ans.lower())

        if is_citation_correct:
            citation_correct += 1

        detailed_results.append({
            "id": q_id,
            "split": q_split,
            "question": question,
            "should_refuse": should_refuse,
            "expected_source": expected_src,
            "expected_keywords": item["expected_keywords"],
            "retrieved_sources": ";".join(retrieved_sources),
            "generated_answer": ans.replace("\n", " "),
            "is_answer_correct": int(is_answer_correct),
            "is_retrieval_hit": int(is_retrieval_hit),
            "is_citation_correct": int(is_citation_correct),
            "latency_seconds": round(elapsed, 4)
        })
        time.sleep(13)  # Pace queries for free-tier rate limits (5 RPM)

    # Save detailed CSV
    out_csv = Path(f"results_{label}_{split_name if split_name else 'all'}.csv")
    if detailed_results:
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(detailed_results[0].keys()))
            writer.writeheader()
            writer.writerows(detailed_results)

    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    ans_acc = (correct_answers / total_count) * 100.0 if total_count else 0.0
    ret_acc = (retrieval_hits / total_count) * 100.0 if total_count else 0.0
    cit_acc = (citation_correct / total_count) * 100.0 if total_count else 0.0
    ref_acc = (refusal_correct / refusal_total) * 100.0 if refusal_total else 100.0

    return {
        "split": split_name if split_name else "ALL",
        "total_questions": total_count,
        "answer_correctness": ans_acc,
        "retrieval_hit_rate": ret_acc,
        "citation_accuracy": cit_acc,
        "correct_refusals": ref_acc,
        "refusals_count": f"{refusal_correct}/{refusal_total}",
        "avg_latency_sec": avg_latency,
        "csv_path": str(out_csv),
        "failures": [r for r in detailed_results if r["is_answer_correct"] == 0 or r["is_retrieval_hit"] == 0]
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate Mount Carmel College RAG Pipeline")
    parser.add_argument("label", type=str, nargs="?", default="baseline", help="Evaluation run label (e.g. baseline, v2, v3)")
    parser.add_argument("--top_k", type=int, default=TOP_K_RETRIEVAL, help="Top-K retrieval depth")
    args = parser.parse_args()

    print("=" * 75)
    print(f"RAG EVALUATION RUN: {args.label.upper()}")
    print(f"Retrieval Top-K:   {args.top_k}")
    print("=" * 75)

    # Evaluate DEV split
    dev_stats = evaluate_split(split_name="dev", top_k=args.top_k, label=args.label)
    
    # Evaluate TEST split
    test_stats = evaluate_split(split_name="test", top_k=args.top_k, label=args.label)

    # Print Summary Table
    print("\n" + "-" * 75)
    print(f"{'Metric':<30} | {'DEV Split (N=10)':<18} | {'TEST Split (N=10)':<18}")
    print("-" * 75)
    print(f"{'Answer Correctness':<30} | {dev_stats['answer_correctness']:>6.1f}%             | {test_stats['answer_correctness']:>6.1f}%")
    print(f"{'Retrieval Hit Rate':<30} | {dev_stats['retrieval_hit_rate']:>6.1f}%             | {test_stats['retrieval_hit_rate']:>6.1f}%")
    print(f"{'Citation Accuracy':<30} | {dev_stats['citation_accuracy']:>6.1f}%             | {test_stats['citation_accuracy']:>6.1f}%")
    print(f"{'Correct Refusals':<30} | {dev_stats['correct_refusals']:>6.1f}% ({dev_stats['refusals_count']:<3})     | {test_stats['correct_refusals']:>6.1f}% ({test_stats['refusals_count']:<3})")
    print(f"{'Average Latency (sec)':<30} | {dev_stats['avg_latency_sec']:>6.4f}s            | {test_stats['avg_latency_sec']:>6.4f}s")
    print("-" * 75)
    print(f"Saved Dev Results to:  {dev_stats['csv_path']}")
    print(f"Saved Test Results to: {test_stats['csv_path']}")
    print("=" * 75)


if __name__ == "__main__":
    main()
