import json
import os
import sys
import argparse
import subprocess
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent / "ai_config.json"

DEFAULT_CONFIG = {
    "provider": os.environ.get("AI_PROVIDER", "ollama"),
    "model": os.environ.get("AI_MODEL", "llama3.2"),
    "endpoint": os.environ.get("AI_ENDPOINT", "http://localhost:11434"),
    "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
    "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
    "max_tokens": 1024,
    "temperature": 0.3,
}


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    return dict(DEFAULT_CONFIG)


def call_ollama(prompt, config):
    import requests
    payload = {
        "model": config["model"],
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": config["max_tokens"],
            "temperature": config["temperature"],
        },
    }
    resp = requests.post(
        f"{config['endpoint'].rstrip('/')}/api/generate",
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["response"]


def call_openai(prompt, config):
    import requests
    headers = {
        "Authorization": f"Bearer {config['openai_api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": "You are a senior Python developer reviewing code feedback. Respond with JSON only."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": config["max_tokens"],
        "temperature": config["temperature"],
    }
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def call_anthropic(prompt, config):
    import requests
    headers = {
        "x-api-key": config["anthropic_api_key"],
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config["model"],
        "max_tokens": config["max_tokens"],
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def build_prompt(feedback_text):
    return f"""You are analyzing user feedback for the SoundVault project (a music/audio manager desktop app built with Python/Flask/pywebview).

Analyze the following feedback and return a JSON object with these fields:
- "summary": a short summary of the issue
- "severity": "low", "medium", "high", or "critical"
- "code_changes": an array of {{"file": "path/to/file.py", "description": "...", "diff": "..."}}
- "suggested_fix": a short plain-text explanation of how to fix it

Only return a valid JSON object. No markdown, no explanation.

Feedback:
{feedback_text}"""


def analyze_feedback(feedback_text, config):
    prompt = build_prompt(feedback_text)
    provider = config["provider"].lower()

    if provider == "openai":
        raw = call_openai(prompt, config)
    elif provider == "anthropic":
        raw = call_anthropic(prompt, config)
    else:
        raw = call_ollama(prompt, config)

    # strip code fences if present
    raw = raw.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    return json.loads(raw)


def apply_changes(changes, repo_root=None):
    if repo_root is None:
        repo_root = Path.cwd()
    else:
        repo_root = Path(repo_root)

    for change in changes:
        file_path = repo_root / change["file"]
        diff_text = change.get("diff", "")

        if not diff_text or not file_path.exists():
            continue

        print(f"  ~ {change['file']}: {change.get('description', 'no description')}")

    return True


def commit_and_push(message):
    result = subprocess.run(["git", "add", "-A"], capture_output=True, text=True)
    if result.returncode != 0:
        print("git add failed:", result.stderr)
        return False

    result = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True)
    if result.returncode != 0:
        print("git commit failed (maybe nothing to commit):", result.stderr)
        return False

    print(f"Committed: {message}")
    return True


def main():
    parser = argparse.ArgumentParser(description="AI-powered feedback agent for SoundVault")
    parser.add_argument("file", nargs="?", help="Path to feedback file (reads from stdin if omitted)")
    parser.add_argument("--apply", action="store_true", help="Apply suggested changes")
    parser.add_argument("--commit", action="store_true", help="Commit changes after applying")
    parser.add_argument("--commit-message", default="Auto-fix: apply AI-suggested changes")
    parser.add_argument("--output", help="Write analysis JSON to file")
    args = parser.parse_args()

    config = load_config()

    if args.file:
        with open(args.file) as f:
            feedback = f.read()
    else:
        feedback = sys.stdin.read()

    if not feedback.strip():
        print("No feedback provided.", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing feedback with {config['provider']}/{config['model']}...")
    result = analyze_feedback(feedback, config)

    print(f"\nSeverity: {result.get('severity', 'unknown')}")
    print(f"Summary: {result.get('summary', 'N/A')}\n")

    changes = result.get("code_changes", [])
    if changes:
        print(f"Suggested changes ({len(changes)}):")
        for c in changes:
            print(f"  - {c['file']}: {c.get('description', 'N/A')}")

    if result.get("suggested_fix"):
        print(f"\nSuggested fix: {result['suggested_fix']}")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nAnalysis written to {args.output}")

    if args.apply and changes:
        print("\nApplying changes...")
        apply_changes(changes)

        if args.commit:
            commit_and_push(args.commit_message)

    return result


if __name__ == "__main__":
    main()
