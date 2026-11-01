"""STEP 1: your first model call. Run:  python hello.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.llm import ask

review = "App keeps crashing when I try to pay. Money got deducted but no order. Very disappointed."
prompt = f"Review: {review}\n\nWhat is the user's main problem, in one sentence?"

print(ask(prompt))
