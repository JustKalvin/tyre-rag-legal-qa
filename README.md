# TyRe-RAG: Indonesian Statutory QA Dataset and Experimental Results

This repository contains the evaluation dataset and the complete per-question
results behind the paper *TyRe-RAG: Typed Routing and Cross-Modal Reranking for
Indonesian Legal Question Answering* (under review).

- **Dataset**: 100 complex Indonesian question–answer pairs grounded in Law
  No. 6 of 2023 on Job Creation (the Indonesian omnibus law).
- **Results**: every answer, retrieved context, judge score, routing decision
  and per-node timing for the eight configurations reported in the paper
  (8 × 100 = 800 executions).

The dataset file is released **byte-identical** to the file used in the
experiments. Nothing in it has been edited, corrected or reformatted;
additional information is provided in a separate metadata file. The SHA-256
checksums in `SHA256SUMS` let anyone verify this.

## Contents

```
data/
  qa_complex_100.csv                      the evaluation dataset, exactly as used
  qa_complex_100_metadata.csv             per-row provenance (joined by row number)
results/
  ablation_results_components100.csv      generated answers and retrieved contexts
  metric_results_components100.csv        DeepEval judge scores per question
  router_meta_results_components100.csv   router, sufficiency check and reranker logs
  node_timing_results_components100.csv   per-node timing of every execution
  judge_drift_components100.csv           judge re-scoring (26 questions x 3 repeats)
  run_provenance_components100.csv        models and endpoints per configuration
  router_probe_components100.csv          typed router vs prompted LLM router, routing decision only
reproduce_tables.py                       recomputes the paper's tables (stdlib only)
SHA256SUMS
LICENSE
```

## Dataset

### `data/qa_complex_100.csv`

| Column | Description |
|---|---|
| `user_input` | The question, in Indonesian. |
| `reference` | The reference answer, grounded in the text of the law. |

Rows are in the order used in the experiments; row *i* (1-based, excluding
the header) is `question_id` *i* in every results file.

### `data/qa_complex_100_metadata.csv`

| Column | Description |
|---|---|
| `row_id` | 1–100, the row number in `qa_complex_100.csv`. |
| `source` | `labour_cluster` (rows 1–50) or `chunk_generated` (rows 51–100, generated from article chunks and passed through the automatic gates below). |
| `generator` | The language model that generated the question and reference: `claude-opus-5.5` for all 100 rows. |
| `generation_batch` | For generated rows, the batch of corpus chunks the question was generated from. |
| `cited_articles` | For generated rows, the article number(s) the reference cites (empty if none). |
| `source_chunk_articles` | For generated rows, the article numbers present in the source chunks. |
| `ngram8_overlap` | For generated rows, the share of the reference's 8-grams that appear verbatim in the source chunks. |
| `truncated_reference` | `true` if the reference is an ellipsis-truncated statutory fragment. |

### How the dataset was built

All 100 question–answer pairs, questions and reference answers alike, were
generated with Claude Opus 5.5 (Anthropic).

- **Rows 1–50** cover the labour cluster of the law (wages, termination,
  fixed-term contracts, foreign workers, outsourcing) and are mostly
  comparative, scenario, or multi-part questions.
- **Rows 51–100** were generated from article chunks that the first 50
  questions do not touch. As a result they cover further sectors of the
  omnibus law, such as fisheries, patents, taxation, halal certification and
  telecommunications. A chunk-generated row was kept only if it passed four
  automatic gates:
  1. **Length**: question and reference length within the range of rows
     1–50.
  2. **Grounding**: every article cited by the reference appears in the
     source chunks.
  3. **Near-duplicate rejection**: against rows 1–50 and against the other
     chunk-generated rows.
  4. **Anti-copying**: at most 40 % 8-gram overlap between the reference and
     the source chunks, so that reference-based metrics measure retrieval
     rather than copying. Median overlap after gating is 18 %.

One author then checked each of the 100 pairs against the cited provisions
together with an LLM assistant, for plausibility and consistency rather than
legal accuracy.

### Known issues

- **Twelve references are truncated statutory fragments** that end in an
  ellipsis (rows 60–63, 69–72, 80–82, 94; flagged in the metadata). They were
  kept unedited because the reported results were computed on them. The
  paper reports a control analysis without them (n = 88).
- **No pair was verified by someone with legal training.** All 100 pairs are
  LLM-generated and were checked only by one author without legal training,
  assisted by an LLM, so reference-based metrics inherit any error that check
  missed.
- **Article numbers are ambiguous in this statute.** The omnibus law amends
  many earlier laws, so the same article number recurs in several of them.
  `cited_articles` records the number as written, not which amended law it
  belongs to.

## Results

### Configurations

| `config_id` | Name in the paper |
|---|---|
| `semantic_only` | Semantic |
| `lexical_only` | Lexical |
| `graph_only` | Graph |
| `semantic_rerank` | Semantic+rerank |
| `static_sl_rerank` | S+L+rerank |
| `static_slg_rerank` | S+L+G+rerank |
| `arc_no_sufficiency` | TyRe-RAG w/o check |
| `arc_rag_v6_seven` | TyRe-RAG |

The `arc_` prefix is a historical internal name; the files keep the ids under
which the runs were recorded.

Models (also in `run_provenance_components100.csv`): generator
`gpt-5.4-nano` at temperature 0, embeddings `text-embedding-3-small`,
router and sufficiency check `jev-1.13` (build `20260917`), reranker
`rerank-2.5`, judge `gpt-4o-mini` via DeepEval. All runs took place on
29–30 October 2026.

### Notes on the files

- `ablation_results_components100.csv`: `contexts_json` is the list of
  context items passed to the generator, each prefixed with its modality tag
  (e.g. `[Semantic Source]`). `latency_ms` is end-to-end latency.
- `metric_results_components100.csv`: one row per configuration and question;
  scores lie in [0, 1].
- `router_meta_results_components100.csv`: rows exist only for the five
  configurations that use the router, the check or the reranker. Columns
  prefixed `suff_` describe the sufficiency check (`suff_noul` is the raw
  probability, `suff_threshold` the threshold, `suff_enough` the decision);
  columns prefixed `rr_` describe the reranking call.
- `judge_drift_components100.csv`: the same TyRe-RAG answers and contexts
  re-scored three times by the same judge, without regenerating anything, so
  differences between repeats come from the judge and the embedding model
  alone, not from the generator or the retrievers. The 26 questions are not a
  random sample: they were chosen among low-scoring answers (context recall
  below 1, contextual precision below 0.85, or semantic similarity below 0.78).
- `router_probe_components100.csv`: the routing decision alone, without
  retrieval, generation, or judging, for all 100 questions. Each question was
  routed by `gpt-5.4-nano` prompted with the same instructions and seven
  criteria as the typed router, and by `jev-1.13` again in the same session,
  alternating the order per question. `jev_original` is the label from the
  main run. Latencies are wall-clock seconds per decision.

### Reproducing the tables

```
python reproduce_tables.py
```

This prints the means and standard deviations of Tables I and II and the
routing and escalation counts reported in the paper. Statistical tests are
not included in the script.

## Verifying the files

```
sha256sum -c SHA256SUMS
```

## License

The dataset, its metadata and the results are released under the Creative
Commons Attribution 4.0 International license (CC BY 4.0); see `LICENSE`.
The statutory text quoted in references and contexts is not subject to
copyright under Indonesian law (Law No. 28 of 2014 on Copyright, Article 42).

## Citation

Citation details will be added after the review period.
