"""STEP 2 and 3: tag ONE review with a theme + severity, as JSON. Run:  python tag_one.py

Try this: change the review text, change the themes, or change the severity rules,
then run again and watch how the answer changes. That is prompt engineering.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.llm import ask_json

review = "App keeps crashing when I try to pay. Money got deducted but no order. Very disappointed."

prompt = f"""You label app reviews for a product manager.

Pick ONE theme from this list:
- payment_failures: payment errors, money deducted, failed checkout
- app_crashes_bugs: crashes, freezes, features not working
- slow_refunds: refund delays or refund refusals
- delivery_issues: late, wrong or missing delivery
- poor_ui: confusing, cluttered or hard-to-use screens
- pricing_offers: high prices, fees, fake discounts
- support_issues: unhelpful or unreachable customer support
- other: praise, spam, or does not fit above

Severity:
1 = minor annoyance or nice-to-have request
2 = real frustration, or the task is blocked some of the time
3 = user cannot use a core feature, lost money/data, or says they will quit

Also give "evidence": a short phrase (max 15 words) copied EXACTLY from the review.

Return JSON only: {{"theme": "...", "severity": 1-3, "evidence": "..."}}

Review: {review}"""

result = ask_json(prompt)
print(result)
