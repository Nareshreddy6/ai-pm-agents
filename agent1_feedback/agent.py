"""STEPS 5, 6 and 8: the full Feedback-to-Insights agent.

  python agent.py discover   # propose themes from a sample of reviews -> data/themes.json
  python agent.py tag        # tag every review -> data/tagged.csv
  python agent.py report     # rank problems, write outputs/brief.md

Needs data/reviews.csv (see scrape_reviews.py, or copy sample_reviews.csv there).
"""
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.llm import ask, ask_json

BATCH = 15  # reviews per model call

SEVERITY_RUBRIC = """Severity:
1 = minor annoyance or a nice-to-have request
2 = real frustration, or the task is blocked some of the time
3 = user cannot use a core feature, lost money/data, or says they will quit/uninstall"""


def load_reviews() -> pd.DataFrame:
    return pd.read_csv("data/reviews.csv")


def clip(text: str, n: int = 500) -> str:
    return text if len(text) <= n else text[:n]


# ---------- Step A: discover themes ----------
def discover():
    df = load_reviews()
    sample = df.sample(min(120, len(df)), random_state=1)
    lines = "\n".join(f"- ({r.rating} stars) {clip(r.text, 300)}" for r in sample.itertuples())
    system = "You are a senior product manager analysing app reviews."
    prompt = f"""Below are user reviews. Define 6 to 10 mutually exclusive problem/request themes that cover most of them.
Themes must be specific and actionable (e.g. "payment_failures", not "bad experience").
Return JSON only: a list of objects like {{"theme": "snake_case_name", "definition": "one sentence"}}.

{lines}"""
    themes = ask_json(prompt, system=system)
    os.makedirs("data", exist_ok=True)
    with open("data/themes.json", "w", encoding="utf-8") as f:
        json.dump(themes, f, indent=2)
    print("Themes discovered:")
    for t in themes:
        print(f"  {t['theme']}: {t['definition']}")
    print("\nSaved data/themes.json. Edit it by hand if you disagree, then run make_label_sheet.py")


# ---------- Step B: tag every review ----------
def tag():
    df = load_reviews()
    themes = json.load(open("data/themes.json", encoding="utf-8"))
    theme_names = [t["theme"] for t in themes] + ["other"]
    theme_text = "\n".join(f"- {t['theme']}: {t['definition']}" for t in themes)
    system = "You are a careful product analyst labelling user reviews. Never invent quotes."

    results = []
    for i in range(0, len(df), BATCH):
        chunk = df.iloc[i : i + BATCH]
        items = "\n".join(f"[{r.review_id}] {clip(r.text)}" for r in chunk.itertuples())
        prompt = f"""Themes:
{theme_text}
- other: does not fit any theme above (praise, spam, unclear)

{SEVERITY_RUBRIC}

For each review pick exactly ONE theme, a severity (1-3), and "evidence": a short phrase (max 15 words)
copied EXACTLY from the review text that justifies the theme. Use "" for evidence if the theme is other.

If a review mentions several problems, choose the theme of the problem that caused the most harm to the
user (lost money, missing items, wrong order, crashes) over secondary complaints such as support not helping.
Use "other" only for praise, spam or unclear text, never for a real complaint.

Return JSON only: a list of objects {{"id": "...", "theme": "...", "severity": 1, "evidence": "..."}}, one per review.

Reviews:
{items}"""
        out = ask_json(prompt, system=system)
        results.extend(out)
        print(f"Tagged {min(i + BATCH, len(df))}/{len(df)}")

    tagged = pd.DataFrame(results).rename(columns={"id": "review_id"})
    tagged = df.merge(tagged, on="review_id", how="left")
    tagged["theme"] = tagged["theme"].where(tagged["theme"].isin(theme_names), "other")
    tagged["severity"] = pd.to_numeric(tagged["severity"], errors="coerce").fillna(1).clip(1, 3)
    tagged["evidence"] = tagged["evidence"].fillna("")

    # Hallucination check: the quote must really appear inside the review
    tagged["evidence_ok"] = [
        (e == "") or (e.lower().strip(" .\"'") in t.lower())
        for e, t in zip(tagged["evidence"], tagged["text"])
    ]
    tagged.to_csv("data/tagged.csv", index=False)
    bad = (~tagged["evidence_ok"]).mean()
    print(f"Saved data/tagged.csv. Quotes NOT found in the review text: {bad:.1%}")


# ---------- Step C: rank problems and write the brief ----------
def report():
    everything = pd.read_csv("data/tagged.csv")
    total = len(everything)
    t = everything[everything["theme"] != "other"]
    defs = {x["theme"]: x["definition"] for x in json.load(open("data/themes.json", encoding="utf-8"))}

    g = t.groupby("theme").agg(count=("review_id", "count"), avg_severity=("severity", "mean")).reset_index()
    g["reach"] = g["count"] / total
    g["priority_score"] = g["reach"] * g["avg_severity"]  # simple and easy to defend
    g = g.sort_values("priority_score", ascending=False).head(5)

    facts = []
    for r in g.itertuples():
        quotes = (
            t[(t["theme"] == r.theme) & t["evidence_ok"] & (t["evidence"] != "")]
            .sort_values("severity", ascending=False)["evidence"]
            .head(3)
            .tolist()
        )
        facts.append(
            {
                "theme": r.theme,
                "definition": defs.get(r.theme, ""),
                "reviews": int(r.count),
                "reach_pct": round(r.reach * 100, 1),
                "avg_severity": round(r.avg_severity, 2),
                "priority_score": round(r.priority_score, 3),
                "quotes": quotes,
            }
        )

    system = "You are a senior PM writing a one-page brief for leadership. Use only the data given."
    prompt = f"""Write a one-page markdown brief titled "Top 5 user problems".
For each problem: a plain-English title, who is affected (reach %), why it matters (severity),
1-2 evidence quotes (use ONLY the quotes provided), and one concrete next step to validate or fix it.
End with a short "Caveats" section (small sample, AI labelling, needs human review).
Severity is on a 1-3 scale (3 = worst); write it as "x.x out of 3".
The title must cover the whole theme definition provided, not just one example.
Do not invent facts that are not in the data: no dates, platforms, timelines, dollar or revenue claims.
Write next steps as suggestions to validate, and keep them to one sentence each.
List the problems in exactly the order given in Data (highest priority first). Do not reorder them.
Total reviews analysed: {total}.

Data:
{json.dumps(facts, indent=2)}"""
    brief = ask(prompt, system=system)
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/brief.md", "w", encoding="utf-8") as f:
        f.write(brief)
    g.round(2).to_csv("outputs/ranking.csv", index=False)

    check = brief.replace("\u2011", "-").lower()
    source = " ".join(everything["text"]).lower()
    for bad in ["1-5", "revenue", "2024", "two weeks", "a/b"]:
        if bad in check and bad not in source:
            print(f"\nWARNING: the brief contains '{bad}', which the data does not support. Review before sharing.\n")

    print(brief)


if __name__ == "__main__":
    steps = {"discover": discover, "tag": tag, "report": report}
    if len(sys.argv) != 2 or sys.argv[1] not in steps:
        sys.exit("Usage: python agent.py [discover|tag|report]")
    steps[sys.argv[1]]()