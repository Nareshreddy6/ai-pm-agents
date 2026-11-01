# Agent 1 guide: build it step by step (no coding background needed)

You will RUN the code and then CHANGE small things. Don't try to memorise syntax.
For every step, aim to answer the question at the end in your own words.

## Setup (once)
Fastest, no installs: use Google Colab (colab.research.google.com). Otherwise install Python 3.10+.

```
python -m venv venv
venv\Scripts\activate          # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
```
Get a free key at aistudio.google.com ("Get API key"), then set it:
- Windows PowerShell:  `$env:GEMINI_API_KEY="your_key"`
- Mac/Linux:           `export GEMINI_API_KEY="your_key"`

If you ever see "model not found": open AI Studio, copy a current Flash model name and set
`MODEL` the same way (e.g. `$env:MODEL="name-you-copied"`).

Never paste your key into a file or into a chat.

---
## Step 1: first model call  ->  `python hello.py`
`shared/llm.py` has a function `ask(prompt)`. It sends your text to the model and returns its reply.
`hello.py` builds a prompt from one review and prints the answer.
Try: change the question ("What should the PM do first?"). Run again.
**Question:** why do we keep the API key in an environment variable instead of the code file?

## Step 2 + 3: tag one review as JSON  ->  `python tag_one.py`
The prompt gives the model a menu of themes, a severity rule, and a strict output format (JSON).
JSON = labelled data a program can read, e.g. {"theme": "payment_failures", "severity": 3}.
Try: (1) change the review to "Great app!", what theme comes back? (2) delete the severity rules,
does the answer change? (3) add a new theme.
**Question:** why do we say "copy the evidence EXACTLY from the review"? (Hint: hallucination.)

## Step 4: get data and label 50 by hand
```
mkdir data
copy sample_reviews.csv data\reviews.csv        # Mac/Linux: cp
python agent.py discover                         # model proposes themes -> data/themes.json
python make_label_sheet.py                       # creates data/to_label.csv
```
Open `data/to_label.csv`, fill `human_theme` and `human_severity` YOURSELF, save as `data/labeled.csv`.
Do NOT look at the agent's tags first. Your labels are the "answer key".
Later, repeat with real reviews: `python scrape_reviews.py <play_store_app_id> 300`.
**Question:** why must a human label first? (Hint: otherwise you can't measure anything.)

## Step 5: tag everything  ->  `python agent.py tag`
Reads `data/reviews.csv`, sends reviews in batches of 15, saves `data/tagged.csv`.
It also checks that every evidence quote really appears in the review.
**Question:** why batches instead of one huge call, or one call per review? (Cost, limits, accuracy.)

## Step 6: evaluate  ->  `python eval.py`
Compares the agent against your labels: accuracy, per-theme precision/recall, hallucination rate.
Open `outputs/errors.csv`: every row is a mistake. Write down WHY each happened.
**Question:** what does a 90% accuracy not tell you? (Look at per-theme recall.)

## Step 7: improve and re-measure
Group the errors into 3-4 types (overlapping themes, multi-issue reviews, vague severity...).
Fix ONE type at a time by editing the prompt in `agent.py` (clearer definitions, add 2-3 examples).
Run `tag` then `eval` again. Record each run in the README table.
**Question:** how would you take this from 90% to 95%? (This is a real interview question: you now have a real answer.)

## Step 8: report  ->  `python agent.py report`
Ranks problems by `priority = share of reviews x average severity` and writes `outputs/brief.md`.
**Question:** where must a human review this before it goes to leadership, and why?

## Step 9: write it up
Fill in the README: problem, metrics table, failure analysis, what you changed, what you'd do next.
Add one CV line, e.g. "Built an AI review-analysis agent; improved theme accuracy from X% to Y% via
failure analysis and prompt iteration; evidence-quote hallucination Z%."
