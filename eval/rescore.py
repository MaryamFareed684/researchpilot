"""Re-score saved eval results with the CURRENT eval_set.json and scoring rules (no server, no LLM).

  python eval/rescore.py            # all eval/results_*.json files
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
DASHES = {ord(c): " " for c in "-\u2010\u2011\u2012\u2013\u2014"}  # every kind of dash becomes a space


def norm(text):
    return " ".join(text.translate(DASHES).lower().split())


def correct(case, answer):
    a = norm(answer)
    if "answer_all" in case:
        return all(norm(x) in a for x in case["answer_all"])
    return any(norm(x) in a for x in case["answer_any"])


cases = {c["id"]: c for c in json.loads((HERE / "eval_set.json").read_text(encoding="utf-8"))}
print(f"{'run':<10} {'Hit@5':>8} {'Answer ok':>11} {'Refusals':>9} {'False-conf':>11}")
for path in sorted(HERE.glob("results_*.json")):
    r = json.loads(path.read_text(encoding="utf-8"))
    if "answers" not in r:
        print(f"{r['label']:<10} {r['hit_at_5']}/{r['answerable']:<5}  (retrieval only)")
        continue
    ok = refused = fc = total = 0
    for a in r["answers"]:
        c = cases[a["id"]]
        if c.get("must_refuse"):
            refused += a["status"] == "no_evidence"
        else:
            total += 1
            good = correct(c, a["answer"])
            ok += good
            fc += (not good) and a["status"] == "answered"
    print(f"{r['label']:<10} {r['hit_at_5']}/{r['answerable']:<5}  {ok}/{total:<8} {refused}/{r['refuse_total']:<6} {fc:>6}")