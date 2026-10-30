# Known failures and limits

- **b02** "How long were the interviews?" — retrieval misses (Hit@5) in every setup. The paper says "two-hour interviews"; the question shares no key word with the text, so neither BM25 nor the reranker surfaces the page. Answers are still correct when asking one paper at a time.
- **Hybrid without reranker:** one wrong answer (b02) was badged "answered", so false confidence is possible when retrieval picks the wrong chunks. The reranker removed it on this set.
- **Small eval set:** 32 questions over 2 papers, written by me, mostly direct fact lookups. Results do not prove accuracy on other papers or on multi-step reasoning.
- **Scorer bug found and fixed:** model output uses special Unicode hyphens ("1‑to‑5"), which made my string matching mark a correct answer wrong. All saved runs were re-scored with the same fixed rule.
- **Not built (no failure to fix on this set):** LLM claim-verification step. Would cost one extra Groq call per answer.