#!/usr/bin/env python3
"""Called by feedback-review.yml — analyzes an issue, gathers codebase context,
sends it to AI, and writes analysis_output.json with structured fixes."""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

PROVIDER = os.environ.get("AI_PROVIDER", "ollama")
MODEL = os.environ.get("AI_MODEL", "llama3.2")
ENDPOINT = os.environ.get("AI_ENDPOINT", "http://localhost:11434")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SOURCE_FILES = [
    "backend.py",
    "main.py",
    "SoundVault.spec",
    "config.json",
    "requirements.txt",
    "public/index.html",
]

MAX_FILE_BYTES = 25000

DEFAULT_OUTPUT = {
    "summary": "Unable to analyze the issue.",
    "severity": "unknown",
    "code_changes": [],
    "suggested_fix": "",
    "changelog": "",
}


def gather_context(root_dir="."):
    """Read key source files so the AI has real code to work with."""
    sections = []
    for rel_path in SOURCE_FILES:
        full = Path(root_dir) / rel_path
        if not full.exists():
            continue
        try:
            content = full.read_text(encoding="utf-8", errors="replace")
            if len(content.encode()) > MAX_FILE_BYTES:
                content = content[: int(MAX_FILE_BYTES / 2)] + "\n... (truncated)\n" + content[-int(MAX_FILE_BYTES / 2) :]
            sections.append(f"=== {rel_path} ===\n{content}")
        except Exception:
            sections.append(f"=== {rel_path} ===\n[Could not read file]")
    return "\n\n".join(sections)


def build_prompt(title, body, number, context):
    return f"""You are a senior developer for SoundVault, a Python/Flask/pywebview desktop music manager app.
Below is the current source code of the project for context.

{context}

---
Issue #{number}: {title}

{body}

---

Analyze this issue and return ONLY valid JSON (no markdown, no backticks, just raw JSON).

The JSON must have these fields:
- "summary": a short 1-2 sentence summary of the issue
- "severity": one of "low", "medium", "high", "critical"
- "code_changes": an array of objects, each with:
    - "file": relative file path to modify (e.g. "backend.py" or "public/index.html")
    - "description": one sentence explaining what this change does
    - "search": the EXACT code snippet to find in the file (must match verbatim including whitespace/indentation; copy it EXACTLY from the source above). Use a small unique snippet that appears only once.
    - "replace": the replacement code to put in place of "search"
- "suggested_fix": plain-text explanation of the fix (2-4 sentences)
- "changelog": a single short line suitable for a git tag message describing what was fixed (e.g. "fix: resolve crash when file path contains unicode characters")

Rules for code_changes:
1. The "search" string MUST be copied verbatim from the source code provided above — same indentation, same whitespace. If you can't find the exact code, don't fabricate it.
2. Only include changes that are actually needed to fix the issue.
3. If no code change is needed, return an empty array.
4. If you are unsure, return an empty array for code_changes.

Respond with raw JSON — no markdown fences, no extra text."""


def call_ollama(prompt):
    data = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 2048, "temperature": 0.2},
    }).encode()
    req = urllib.request.Request(
        f"{ENDPOINT.rstrip('/')}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read())
            return result.get("response", "")
    except Exception as e:
        print(f"Ollama call failed: {e}", file=sys.stderr)
        return ""


def call_openai(prompt):
    data = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a senior Python developer. Respond with JSON only — no markdown, no explanation."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 2048,
        "temperature": 0.2,
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
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"OpenAI call failed: {e}", file=sys.stderr)
        return ""


def call_anthropic(prompt):
    data = json.dumps({
        "model": MODEL,
        "max_tokens": 2048,
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
        with urllib.request.urlopen(req, timeout=180) as resp:
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
    parser.add_argument("--repo-dir", default=".")
    args = parser.parse_args()

    context = gather_context(args.repo_dir)
    prompt = build_prompt(args.title, args.body, args.number, context)

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

    changes = analysis.get("code_changes", [])
    print(f"Analysis written to analysis_output.json")
    print(f"Summary: {analysis.get('summary', 'N/A')}")
    print(f"Code changes suggested: {len(changes)}")
    print(f"Changelog: {analysis.get('changelog', 'N/A')}")


if __name__ == "__main__":
    main()
