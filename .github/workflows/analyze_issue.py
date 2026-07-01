#!/usr/bin/env python3
"""Called by feedback-review.yml — analyzes an issue and writes analysis_output.json."""

import json
import os
import sys
import urllib.request
import urllib.error

PROVIDER = os.environ.get("AI_PROVIDER", "ollama")
MODEL = os.environ.get("AI_MODEL", "llama3.2")
ENDPOINT = os.environ.get("AI_ENDPOINT", "http://localhost:11434")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

DEFAULT_OUTPUT = {
    "summary": "Unable to analyze the issue.",
    "severity": "unknown",
    "code_changes": [],
    "suggested_fix": "",
}


def build_prompt(title, body, number):
    return f"""You are a senior developer for SoundVault, a Python/Flask/pywebview desktop music manager.

Issue #{number}: {title}

{body}

Analyze this issue and return ONLY valid JSON with:
- "summary": short issue summary
- "severity": "low"|"medium"|"high"|"critical"
- "code_changes": array of {{"file": "path", "description": "...", "diff": "diff text or 'N/A'"}}
- "suggested_fix": plain-text explanation

Respond with raw JSON — no markdown fences, no extra text."""


def call_ollama(prompt):
    data = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 1024, "temperature": 0.3},
    }).encode()
    req = urllib.request.Request(
        f"{ENDPOINT.rstrip('/')}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result.get("response", "")
    except Exception as e:
        print(f"Ollama call failed: {e}", file=sys.stderr)
        return ""


def call_openai(prompt):
    data = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a senior Python developer. Respond with JSON only."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 1024,
        "temperature": 0.3,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_KEY}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"OpenAI call failed: {e}", file=sys.stderr)
        return ""


def call_anthropic(prompt):
    data = json.dumps({
        "model": MODEL,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result["content"][0]["text"]
    except Exception as e:
        print(f"Anthropic call failed: {e}", file=sys.stderr)
        return ""


def parse_analysis(raw):
    if not raw:
        return DEFAULT_OUTPUT
    raw = raw.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    elif raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return DEFAULT_OUTPUT


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--number", required=True)
    args = parser.parse_args()

    prompt = build_prompt(args.title, args.body, args.number)

    provider = PROVIDER.lower()
    if provider == "openai":
        raw = call_openai(prompt)
    elif provider == "anthropic":
        raw = call_anthropic(prompt)
    else:
        raw = call_ollama(prompt)

    analysis = parse_analysis(raw)

    with open("analysis_output.json", "w") as f:
        json.dump(analysis, f, indent=2)

    print(f"Analysis written to analysis_output.json")
    print(f"Summary: {analysis.get('summary', 'N/A')}")


if __name__ == "__main__":
    main()
