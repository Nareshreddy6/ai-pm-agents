"""STEP 4b: create the sheet you label BY HAND (before looking at the agent's tags).

  python make_label_sheet.py

Open data/to_label.csv in Excel/Sheets, fill:
  human_theme     -> one theme name from data/themes.json, or "other"
  human_severity  -> 1, 2 or 3
Then save it as data/labeled.csv (CSV format).
"""
import json

import pandas as pd

df = pd.read_csv("data/reviews.csv")
sample = df.sample(min(50, len(df)), random_state=42)[["review_id", "text"]].copy()
sample["human_theme"] = ""
sample["human_severity"] = ""
sample.to_csv("data/to_label.csv", index=False)

themes = json.load(open("data/themes.json"))
print("Label each review with ONE of these themes (or 'other'):\n")
for t in themes:
    print(f"  {t['theme']}: {t['definition']}")
print("\nSeverity: 1 = minor, 2 = real frustration / sometimes blocked, 3 = core feature broken or will quit")
print("\nSaved data/to_label.csv -> fill it in and save as data/labeled.csv")
