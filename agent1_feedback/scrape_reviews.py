"""STEP 4a: get reviews. Two options.

Option A (real data, recommended):
    python scrape_reviews.py com.example.app 300
    (app id = text after ?id= in the Play Store URL; needs: pip install google-play-scraper pandas)

Option B (practice data, no scraping):
    just use the included sample_reviews.csv -> copy it to data/reviews.csv
"""
import os
import sys

import pandas as pd
from google_play_scraper import Sort, reviews

app_id = sys.argv[1]
count = int(sys.argv[2]) if len(sys.argv) > 2 else 300

rows, _ = reviews(app_id, lang="en", country="in", sort=Sort.NEWEST, count=count)
df = pd.DataFrame(rows)[["content", "score", "at"]]
df.columns = ["text", "rating", "date"]
df["text"] = df["text"].str.replace(r"\s+", " ", regex=True).str.strip()
df = df[df["text"].str.len() >= 15].reset_index(drop=True)  # drop "good", "nice", etc.
df.insert(0, "review_id", [f"r{i:04d}" for i in range(len(df))])

os.makedirs("data", exist_ok=True)
df.to_csv("data/reviews.csv", index=False)
print(f"Saved {len(df)} reviews to data/reviews.csv")
