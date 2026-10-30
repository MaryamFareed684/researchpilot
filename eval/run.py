"""ResearchPilot evaluation runner (standard library only).

Needs the backend running on http://127.0.0.1:8000 with both papers uploaded.

  python eval/run.py                 # retrieval only: no LLM, fast, free
  python eval/run.py --full          # also calls /ask (uses Groq quota, waits between calls)
  python eval/run.py --label base    # save results as eval/results_base.json
"""
import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:8000"
HERE = Path(__file__).parent


def call(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(API + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


DASHES = {ord(c): " " for c in "-\u2010\u2011\u2012\u2013\u2014"}  # every kind of dash becomes a space


def norm(text):
    return " ".join(text.translate(DASHES).lower().split())


def answer_correct(case, answer):
    a = norm(answer)
    if "answer_all" in case:
        return all(norm(x) in a for x in case["answer_all"])
    return any(norm(x) in a for x in case["answer_any"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="also run /ask for every question")
    ap.add_argument("--label", default="baseline")
    ap.add_argument("--pause", type=float, default=8.0, help="seconds between /ask calls (Groq limits)")
    args = ap.parse_args()

    cases = json.loads((HERE / "eval_set.json").read_text(encoding="utf-8"))
    docs = {d["doc_name"]: d["doc_id"] for d in call("/documents")["documents"]}
    answerable = [c for c in cases if not c.get("must_refuse")]
    missing = {c["doc_name"] for c in answerable} - set(docs)
    if missing:
        raise SystemExit(f"Upload these papers first: {sorted(missing)}")

    rows = []
    hits = 0
    print("\n== Retrieval (top 5, all documents searched) ==")
    for c in answerable:
        res = call("/search", {"question": c["question"], "top_k": 5})["results"]
        found = [(r["doc_name"], r["page"]) for r in res]
        hit = any(n == c["doc_name"] and p in c["expected_pages"] for n, p in found)
        hits += hit
        print(f"{'HIT ' if hit else 'MISS'} {c['id']}  expected p{c['expected_pages']}  got {[p for _, p in found]}")
        rows.append({"id": c["id"], "hit": hit, "got": found})
    print(f"\nHit@5: {hits}/{len(answerable)} = {hits / len(answerable):.0%}")

    summary = {"label": args.label, "hit_at_5": hits, "answerable": len(answerable), "retrieval": rows}

    if args.full:
        print("\n== Answers (/ask) ==")
        ok = refused_ok = false_conf = 0
        refuse_total = sum(1 for c in cases if c.get("must_refuse"))
        full_rows = []
        for c in cases:
            body = {"question": c["question"], "top_k": 5}
            if not c.get("must_refuse"):
                body["doc_id"] = docs[c["doc_name"]]
            for attempt in range(3):
                try:
                    r = call("/ask", body)
                    break
                except urllib.error.HTTPError as e:
                    if e.code == 429 and attempt < 2:
                        print("  rate limited, waiting 60s...")
                        time.sleep(60)
                        continue
                    r = {"answer": f"HTTP {e.code}", "status": "error"}
                    break
            if c.get("must_refuse"):
                good = r["status"] == "no_evidence"
                refused_ok += good
                print(f"{'OK   ' if good else 'FAIL '} {c['id']} (should refuse) -> {r['status']}")
            else:
                good = answer_correct(c, r["answer"])
                ok += good
                confident = r["status"] == "answered"
                if (not good) and confident:
                    false_conf += 1
                print(f"{'OK   ' if good else 'WRONG'} {c['id']} -> {r['status']}")
            full_rows.append({"id": c["id"], "status": r["status"], "good": good, "answer": r["answer"]})
            time.sleep(args.pause)
        print(f"\nAnswer correct:       {ok}/{len(answerable)} = {ok / len(answerable):.0%}")
        print(f"Correct refusals:     {refused_ok}/{refuse_total}")
        wrong = len(answerable) - ok
        print(f"False-confidence:     {false_conf} wrong answers still badged 'answered' (of {wrong} wrong)")
        summary.update({"answer_correct": ok, "refusals_ok": refused_ok, "refuse_total": refuse_total,
                        "false_confidence": false_conf, "answers": full_rows})

    out = HERE / f"results_{args.label}.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved {out.name}")


if __name__ == "__main__":
    main()