#!/usr/bin/env python3
"""Dump the Ladli Behna Outreach agent's full live state (agent + voice +
knowledge-base + conversations) to docs/elevenlabs_state/ for repo-side
auditability.

Usage:
    XI_API_KEY=sk_... python dump_agent_state.py

Mirror of cm-voice-bot's dump script, pointed at this project's agent.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).parent
ENV_FILE = ROOT / ".env.local"
OUT_DIR = ROOT / "docs" / "elevenlabs_state"
CONV_DIR = OUT_DIR / "conversations"

CONVERSATION_LIMIT = 50


def load_env() -> dict:
    env = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def http_get(url: str, api_key: str) -> dict:
    req = urllib.request.Request(url, headers={"xi-api-key": api_key})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code} on {url}: {body[:300]}", file=sys.stderr)
        return {"_error": {"code": e.code, "body": body}}


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> {path.relative_to(ROOT.parent)} ({path.stat().st_size:,} B)")


def main() -> int:
    env = load_env()
    api_key = os.environ.get("XI_API_KEY") or env.get("VOICE_API_KEY")
    agent_id = env.get("VOICE_AGENT_ID")
    if not api_key or not agent_id:
        print("ERROR: need XI_API_KEY/VOICE_API_KEY and VOICE_AGENT_ID", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CONV_DIR.mkdir(parents=True, exist_ok=True)

    captured_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(f"[{captured_at}] dumping ElevenLabs state for agent {agent_id}")

    print("\n[1/5] agent config")
    agent = http_get(f"https://api.elevenlabs.io/v1/convai/agents/{agent_id}", api_key)
    write_json(OUT_DIR / "agent.json", agent)

    print("\n[2/5] voice config")
    voice_id = (
        agent.get("conversation_config", {}).get("tts", {}).get("voice_id")
    )
    if voice_id:
        voice = http_get(f"https://api.elevenlabs.io/v1/voices/{voice_id}", api_key)
        write_json(OUT_DIR / "voice.json", voice)

    print("\n[3/5] knowledge base docs")
    kb = http_get("https://api.elevenlabs.io/v1/convai/knowledge-base?page_size=100", api_key)
    write_json(OUT_DIR / "knowledge_base.json", kb)

    print(f"\n[4/5] conversations list (most recent {CONVERSATION_LIMIT})")
    convos = http_get(
        f"https://api.elevenlabs.io/v1/convai/conversations?agent_id={agent_id}&page_size={CONVERSATION_LIMIT}",
        api_key,
    )
    write_json(OUT_DIR / "conversations.json", convos)

    conv_list = (convos.get("conversations") or []) if isinstance(convos, dict) else []
    print(f"  found {len(conv_list)} conversations")

    print(f"\n[5/5] per-conversation detail")
    for c in conv_list:
        cid = c.get("conversation_id")
        if not cid:
            continue
        detail = http_get(
            f"https://api.elevenlabs.io/v1/convai/conversations/{cid}",
            api_key,
        )
        write_json(CONV_DIR / f"{cid}.json", detail)

    readme = OUT_DIR / "README.md"
    readme_content = f"""# ElevenLabs live state dump — Ladli Behna Outreach

- **captured_at_utc:** {captured_at}
- **agent_id:** `{agent_id}`
- **voice_id:** `{voice_id}`
- **conversations dumped:** {len(conv_list)}

Refresh:
```bash
XI_API_KEY=sk_... python dump_agent_state.py
```
"""
    readme.write_text(readme_content, encoding="utf-8")
    print(f"\n  -> {readme.relative_to(ROOT.parent)}")

    print(f"\n[done] state dumped to {OUT_DIR.relative_to(ROOT.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
