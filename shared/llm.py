"""Shared helper used by all three agents (GROQ version).

Two functions:
  ask(prompt)       -> returns the model's text answer
  ask_json(prompt)  -> returns the answer parsed as Python data (list/dict)

Setup: set GROQ_API_KEY in your environment (free key from console.groq.com).
If you get a "model not found" error, open console.groq.com -> Models, copy a current
model name, and set it in the terminal:  $env:MODEL="<name>"   (default is below).
"""
import json
import os
import re
import time

from groq import Groq

MODEL = os.getenv("MODEL", "openai/gpt-oss-120b")
PAUSE = float(os.getenv("PAUSE", "2"))  # seconds to wait after each call (free tier has rate limits)

client = Groq()  # reads GROQ_API_KEY from the environment automatically

# Errors that waiting will never fix: stop immediately instead of retrying.
PERMANENT_ERRORS = {400, 401, 403, 404}


def ask(prompt: str, system: str | None = None, json_mode: bool = False, retries: int = 4) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    if json_mode:
        prompt += "\n\nReply with valid JSON only, no extra text, no markdown fences."
    messages.append({"role": "user", "content": prompt})

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0,  # 0 = most consistent answers, good for labelling
            )
            time.sleep(PAUSE)
            text = response.choices[0].message.content
            if text:
                return text
            raise ValueError("empty response")
        except Exception as e:
            status = getattr(e, "status_code", None)
            if status in PERMANENT_ERRORS:
                raise RuntimeError(f"Permanent error ({status}): {e}\nCheck your key and MODEL name.") from e
            wait = 10 * (attempt + 1)
            print(f"  call failed ({e}); retrying in {wait}s [{attempt + 1}/{retries}]")
            time.sleep(wait)
    raise RuntimeError("Model call failed after several retries")


def ask_json(prompt: str, system: str | None = None):
    """Ask for JSON; if it does not parse, tell the model and try once more."""
    for attempt in range(2):
        text = ask(prompt, system=system, json_mode=True)
        text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()  # strip code fences
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"(\{.*\}|\[.*\])", text, re.S)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            prompt += "\n\nYour last reply was not valid JSON. Reply with JSON only."
    raise ValueError("Model did not return valid JSON") 