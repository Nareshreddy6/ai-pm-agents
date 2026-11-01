# Feedback-to-Insights Agent

Turns raw app reviews into a ranked "top 5 user problems" brief, and measures how far each step can be trusted.

> **Data note:** this version was built and validated on a **Review dataset** (a food-delivery app, written to resemble real Play Store reviews). It proves the pipeline end to end, but the accuracy numbers below are measure of real-world performance.

## Problem
Product managers receive far more reviews and tickets than they can read. This agent groups them into themes, scores each theme by reach and severity, and writes a one-page brief with real evidence quotes, while keeping a human in the loop.

## Pipeline
| Step |        Script         |                         What happens                         |
|------|-----------------------|--------------------------------------------------------------|
|  1   | `scrape_reviews.py`   | Pull public Play Store reviews (or use `sample_reviews.csv`) |
|  2   | `agent.py discover`   | LLM proposes 6-10 themes from a sample; I edit them by hand |
|  3   | `make_label_sheet.py` | Creates the sheet I label by hand = the answer key |
|  4   | `agent.py tag`        | LLM tags every review: theme, severity (1-3), verbatim evidence quote |
|  5   | `eval.py`             | Accuracy, per-theme precision/recall, quote-hallucination rate, error list |
|  6   | `agent.py report`     | Code ranks themes by reach x severity; LLM writes the brief; guardrail check runs |

`shared/llm.py` is the only file that talks to the model, so the provider can be swapped in one place. (Built on Groq `openai/gpt-oss-120b`)

## Run it
```
pip install -r requirements.txt
# Windows PowerShell
$env:GROQ_API_KEY="your_key"
$env:MODEL="openai/gpt-oss-120b"
$env:PYTHONUTF8="1"

mkdir data
copy sample_reviews.csv data\reviews.csv   # or: python scrape_reviews.py <play_store_app_id> #review number
python agent.py discover
python make_label_sheet.py                 # label data\to_label.csv, save as data\labeled.csv
python agent.py tag
python eval.py
python agent.py report
```

## Results (36-review set)
|      Run      | What changed | Theme accuracy | Quote hallucination | "other" share |
|---------------|--------------|----------------|---------------------|---------------|
|       v1      | Baseline prompt, my first labels | 88.9% (32/36) | 0.0% | 11.1% |
| v1, re-scored | Same prompt, after a label audit corrected 3 of my own label mistakes and 1 multi-issue case | about 97% (35/36) | 0.0% | 11.1% |
|       v2      | Added a multi-issue rule and "never use `other` for a real complaint" | 100% (36/36) | 0.0% | 11.1% |

![Agent 1: v1 vs v2 results](v1_vs_v2.png)

**Read this carefully:** v2 was tuned on the same 36 reviews it is scored on (overfitting), and the answer key was corrected after I saw the agent's answers. The 100% is a development result, not a quality claim.

## Failure analysis (the 4 disagreements in v1)
| Review | My label | Agent | Verdict | Cause |
|---|---|---|---|---|
| Cart empties when I change the address | order_fulfillment_issues | app_stability_performance | Agent right | My label error |
| Menu layout is confusing | feature_requests | ui_clutter_and_ads | Agent right | My label error |
| Two items missing, refund refused | support_response | order_fulfillment_issues | Agent mostly right | Multiple problems; I picked the secondary one |
| Wrong order delivered, support did not pick up | delivery_problems | support_response | Neither | Multi-issue review; fits order_fulfillment_issues best |

**Takeaways**
1. Check the quality of the answer key before tuning the model. 3 of 4 "agent errors" were my mistakes.
2. Multi-issue reviews are the real failure mode. Fix: tell the model to choose the problem that caused the most harm.
3. Do not report a perfect score on data you tuned on.

## Guardrails and lessons from the brief
The first briefs from the LLM contained claims that are not in the data:
- Invented a date ("June 2024") and a "1-5 severity scale" (the real scale is 1-3).
- Invented timelines, SLAs, platforms and revenue claims in the next steps.
- A title ("crashes at checkout") narrower than the theme it described.
- Re-ordered the ranking that the code had already computed.

Fixes: pass each theme's definition to the model, state the scale and "do not invent" rules in the prompt, tell the model to keep the given order, and add an automatic check that warns when the brief contains known unsupported phrases. The first version of that check raised a false alarm on a phrase that was a real quote, so it now flags a phrase only when it does not appear in the source reviews. **The code owns the numbers and the ranking; the model only writes prose.**

## Human in the loop
- A person reviews and edits the discovered themes.
- A person writes the answer key, independently of the agent.
- The brief is a draft: a PM checks numbers, titles and suggested next steps before it is shared. The guardrail warns about known failure patterns but does not replace review.

## Limitations
- Dataset (36 reviews): one mistake moves accuracy about 3 points.
- Tuned and scored on the same set.
- "Severity within +/-1" is a weak metric with only 3 levels; exact-match severity should be added.
- Model output can vary between runs; results were not averaged over repeated runs.
- Free-tier rate limits and model retirements affect reliability.