"""STEPS 6 and 7: evaluate the agent against YOUR hand labels.

  python eval.py      (needs data/labeled.csv and data/tagged.csv)

Run it, read outputs/errors.csv, improve the prompt in agent.py, re-run `tag` and `eval`,
and record each run's numbers in the README table.
"""
import os

import pandas as pd

labeled = pd.read_csv("data/labeled.csv").dropna(subset=["human_theme"])
tagged = pd.read_csv("data/tagged.csv")
m = labeled.merge(tagged[["review_id", "theme", "severity", "evidence", "evidence_ok"]], on="review_id")

m["theme_match"] = m["human_theme"].str.strip() == m["theme"]
accuracy = m["theme_match"].mean()
sev = pd.to_numeric(m["human_severity"], errors="coerce")
sev_within_1 = ((sev - m["severity"]).abs() <= 1).mean()
halluc = (~tagged["evidence_ok"]).mean()
other_rate = (tagged["theme"] == "other").mean()

# Per-theme precision / recall
rows = []
for th in sorted(set(m["human_theme"]) | set(m["theme"])):
    tp = ((m["human_theme"] == th) & (m["theme"] == th)).sum()
    predicted = (m["theme"] == th).sum()
    actual = (m["human_theme"] == th).sum()
    rows.append(
        {
            "theme": th,
            "precision": round(tp / predicted, 2) if predicted else None,
            "recall": round(tp / actual, 2) if actual else None,
            "n_actual": int(actual),
        }
    )
per_theme = pd.DataFrame(rows)

# Where it goes wrong: your label vs the agent's label
errors = m[~m["theme_match"]][["review_id", "text", "human_theme", "theme", "evidence"]]
os.makedirs("outputs", exist_ok=True)
errors.to_csv("outputs/errors.csv", index=False)

try:
    table = per_theme.to_markdown(index=False)
except ImportError:  # tabulate not installed
    table = per_theme.to_string(index=False)

report = f"""# Eval results ({len(m)} hand-labelled reviews)

| Metric | Value |
|---|---|
| Theme accuracy | {accuracy:.1%} |
| Severity within +/-1 | {sev_within_1:.1%} |
| Quote hallucination rate (all reviews) | {halluc:.1%} |
| Share tagged "other" | {other_rate:.1%} |

## Per-theme precision / recall
{table}

Misclassified reviews are in outputs/errors.csv. Read them, group the failures
(overlapping themes, sarcasm, multi-issue reviews...), fix the prompt, re-run, compare.
"""
with open("outputs/eval.md", "w") as f:
    f.write(report)
print(report)
