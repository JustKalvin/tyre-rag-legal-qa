"""Recompute the headline numbers of the paper from the released files.

Standard library only:  python reproduce_tables.py

Prints, per configuration, the mean (and SD) of the five quality metrics and of
end-to-end latency, then the routing and escalation counts of ARC-RAG.
"""

import csv
import json
import os
import statistics
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

# config_id in the files -> name used in the paper
CONFIGS = {
    "semantic_only": "Semantic",
    "lexical_only": "Lexical",
    "graph_only": "Graph",
    "semantic_rerank": "Semantic+rerank",
    "static_sl_rerank": "S+L+rerank",
    "static_slg_rerank": "S+L+G+rerank",
    "arc_no_sufficiency": "ARC-RAG w/o check",
    "arc_rag_v6_seven": "ARC-RAG",
}
METRICS = ["faithfulness", "answer_relevancy", "context_precision",
           "context_recall", "semantic_similarity"]


def read(name):
    with open(os.path.join(RESULTS, name), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fmt(values):
    return f"{statistics.mean(values):.3f} +/- {statistics.stdev(values):.2f}"


def main():
    scores = read("metric_results_components100.csv")
    runs = read("ablation_results_components100.csv")

    header = ["configuration"] + METRICS + ["latency_s"]
    print(" | ".join(header))
    for cid, name in CONFIGS.items():
        rows = [r for r in scores if r["config_id"] == cid]
        lat = [float(r["latency_ms"]) / 1000 for r in runs if r["config_id"] == cid]
        cells = [fmt([float(r[m]) for r in rows]) for m in METRICS]
        print(" | ".join([f"{name} (n={len(rows)})"] + cells + [fmt(lat)]))

    meta = [r for r in read("router_meta_results_components100.csv")
            if r["config_id"] == "arc_rag_v6_seven"]
    print("\nARC-RAG routes:", dict(Counter(r["modality"] for r in meta).most_common()))
    checked = [r for r in meta if r["suff_noul"] not in ("", "nan")]
    escalated = [r for r in checked if r["suff_enough"] == "False"]
    print(f"sufficiency check ran on {len(checked)}, escalated {len(escalated)}:",
          dict(Counter(r["modality"] for r in escalated)))
    kept = Counter()
    for r in meta:
        kept.update(json.loads(r["rr_kept_modalities_json"] or "{}"))
    print("chunks passed to the generator by modality:", dict(kept))


if __name__ == "__main__":
    main()
