#!/usr/bin/env python3
"""Patch the live ElevenLabs agent for Ladli Behna Outreach: system prompt
+ KB (re-uploaded from ../knowledge-base/) + RAG tuning + LLM/TTS model
config + max_tokens. Auto-snapshots BOTH outgoing and live prompt/config
to docs/prompt_versions/ before each PATCH.

Auto-runs dump_agent_state.py after every successful PATCH so the repo
always has a fresh full config + conversations snapshot.

Usage:
    XI_API_KEY=sk_... python update_agent.py [--skip-kb] [--rag-only] [--snapshot-only]
"""
import argparse
import datetime
import json
import mimetypes
import os
import re
import sys
import uuid
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).parent
PROJECT_ROOT = ROOT.parent
PROMPT_FILE = ROOT / "docs" / "elevenlabs_agent_prompt_ladli.md"
VERSIONS_DIR = ROOT / "docs" / "prompt_versions"
ENV_FILE = ROOT / ".env.local"
KB_DIR = PROJECT_ROOT / "knowledge-base"

FIRST_MESSAGE = (
    "नमस्ते बहना। मैं मोहन यादव बोल रहा हूं — आपका भाई, मध्य प्रदेश का मुख्यमंत्री। "
    "आज आपसे कुछ बात करनी थी — लाड़ली बहना योजना के बारे में। "
    "पहले यह बताइए — पैसा आपके अपने खाते में ठीक से आ रहा है?"
)

# RAG tuning — tightened 2026-04-22 for latency: the 3137ms p95 ttfb
# coincided with RAG-triggered turns that injected up to 16K chars
# (4 × 4000) of context with zero prompt-cache hit. 3 × 2500 still
# covers single-topic retrieval from the 12-file KB while cutting
# prefill input roughly in half on RAG turns.
RAG_CONFIG = {
    "enabled": True,
    "max_retrieved_rag_chunks_count": 3,
    "max_documents_length": 2500,
    "max_vector_distance": 0.5,
    "embedding_model": "e5_mistral_7b_instruct",
}

LLM_MAX_OUTPUT_TOKENS = 800
# Switched 2026-04-22 from gemini-2.5-flash -> flash-lite. Hindi
# reasoning slightly weaker but acceptable for 1-3 sentence replies;
# prefill ttfb typically 100-300ms lower on cold turns.
LLM_MODEL = "gemini-2.5-flash-lite"
LLM_TEMPERATURE = 0.5

TTS_CONFIG = {
    "model_id": "eleven_multilingual_v2",
    "stability": 0.35,
    "similarity_boost": 0.75,
    "style": 0.2,
    "use_speaker_boost": True,
}

TURN_CONFIG = {
    "speculative_turn": True,
    "turn_eagerness": "normal",
    "turn_timeout": 7.0,
}


def load_env() -> dict:
    env = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def load_prompt() -> str:
    md = PROMPT_FILE.read_text(encoding="utf-8")
    m = re.search(
        r"=+ AGENT SYSTEM PROMPT \(paste into ElevenLabs\) =+\s*(.*?)\s*=+ END OF AGENT SYSTEM PROMPT =+",
        md, re.S,
    )
    if not m:
        raise RuntimeError(f"Couldn't locate AGENT SYSTEM PROMPT block in {PROMPT_FILE}")
    return m.group(1).strip()


def http_get(url: str, api_key: str) -> dict:
    req = urllib.request.Request(url, headers={"xi-api-key": api_key})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_patch(url: str, api_key: str, payload: dict, label: str):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        method="PATCH",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp.read()
        print(f"[ok] {label}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code} on {label}: {body}", file=sys.stderr)
        sys.exit(4)


def snapshot(label: str, agent_id: str, config: dict, outgoing_prompt: str | None = None) -> str:
    """Save timestamped snapshot: both a readable .md and a full agent .json.
    Returns the timestamp string used in the snapshot filenames."""
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ")
    agent = config["conversation_config"]["agent"]
    p = agent.get("prompt", {}) or {}
    live_prompt = p.get("prompt", "")

    # Full-config JSON — timestamped, never overwritten.
    json_path = VERSIONS_DIR / f"{ts}_{label.replace(' ', '_').replace('/', '-')}.json"
    json_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[snapshot] {json_path.relative_to(PROJECT_ROOT)}")

    content = f"""# Prompt snapshot — {label}

- captured_at_utc: {ts}
- agent_id: {agent_id}
- label: {label}
- llm: {p.get("llm")}
- temperature: {p.get("temperature")}
- first_message: {agent.get("first_message", "")}
- language: {agent.get("language")}
- live_prompt_chars: {len(live_prompt)}
- outgoing_prompt_chars: {len(outgoing_prompt) if outgoing_prompt else 'n/a'}
- knowledge_base_docs: {len(p.get("knowledge_base", []))}
- rag: {json.dumps(p.get("rag"), ensure_ascii=False)}

---

## LIVE PROMPT (what is currently deployed)

{live_prompt}

---

## OUTGOING PROMPT (what this run is about to PATCH — if any)

{outgoing_prompt if outgoing_prompt else '(no prompt change in this run)'}
"""
    path = VERSIONS_DIR / f"{ts}_{label.replace(' ', '_').replace('/', '-')}.md"
    path.write_text(content, encoding="utf-8")
    print(f"[snapshot] {path.relative_to(PROJECT_ROOT)}")
    return ts


CHANGELOG_FILE = ROOT / "docs" / "CHANGES.md"
CHANGELOG_SECTION_MARKER = "## Run Log (auto-appended by update_agent.py)"


def append_changelog(mode: str, patches: list[str], pre_ts: str, post_ts: str | None) -> None:
    """Append a timestamped run entry to docs/CHANGES.md under the
    '## Run Log (auto-appended by update_agent.py)' section. Silent no-op
    if the file does not exist. Failure here must never mask a successful
    PATCH above — wrap in try/except and print a warning on failure."""
    try:
        if not CHANGELOG_FILE.exists():
            return

        now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        pre_label = "snapshot-only" if mode == "snapshot-only" else "pre-update"
        lines = [f"### {now} · {mode}"]
        if patches:
            lines.append("- patches: " + ", ".join(f"`{p}`" for p in patches))
        else:
            lines.append("- patches: _(none)_")
        lines.append(f"- pre-snapshot: `prompt_versions/{pre_ts}_{pre_label}.md`")
        if post_ts:
            lines.append(f"- post-snapshot: `prompt_versions/{post_ts}_post-update.md`")
        else:
            lines.append("- post-snapshot: _(none)_")
        entry = "\n".join(lines) + "\n"

        existing = CHANGELOG_FILE.read_text(encoding="utf-8")
        idx = existing.find(CHANGELOG_SECTION_MARKER)
        # Whether or not the marker is present, we append at EOF so entries
        # under the section accumulate newest-at-bottom (the Run Log section
        # is the last section in the file by convention). If the marker is
        # missing we still don't mangle the file — plain EOF append.
        if idx == -1:
            print(
                f"[warn] CHANGES.md missing section marker "
                f"'{CHANGELOG_SECTION_MARKER}', appending at EOF",
                file=sys.stderr,
            )
        sep = "" if existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
        new_content = existing + sep + entry

        CHANGELOG_FILE.write_text(new_content, encoding="utf-8")
        print(f"[changelog] appended entry to {CHANGELOG_FILE.relative_to(PROJECT_ROOT)}")
    except Exception as e:
        print(f"[warn] CHANGES.md append failed: {e}", file=sys.stderr)


def upload_kb_file(api_key: str, path: Path) -> str:
    boundary = f"----kb{uuid.uuid4().hex}"
    content = path.read_bytes()
    filename = path.name
    mime = mimetypes.guess_type(str(path))[0] or "text/markdown"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="name"\r\n\r\n{filename}\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(
        "https://api.elevenlabs.io/v1/convai/knowledge-base/file",
        data=body,
        headers={
            "xi-api-key": api_key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    doc_id = result.get("id") or result.get("document_id")
    print(f"  uploaded {filename} -> {doc_id}")
    return doc_id


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-kb", action="store_true", help="Don't re-upload KB files")
    parser.add_argument("--rag-only", action="store_true", help="Only PATCH RAG tuning")
    parser.add_argument("--snapshot-only", action="store_true",
                        help="Capture state without PATCHing")
    args = parser.parse_args()

    env = load_env()
    api_key = os.environ.get("XI_API_KEY") or env.get("VOICE_API_KEY")
    agent_id = env.get("VOICE_AGENT_ID")
    if not api_key or not agent_id:
        print("ERROR: need XI_API_KEY/VOICE_API_KEY and VOICE_AGENT_ID", file=sys.stderr)
        print("(Run setup_agent.py first if the agent hasn't been created)", file=sys.stderr)
        return 1

    agent_url = f"https://api.elevenlabs.io/v1/convai/agents/{agent_id}"

    outgoing_prompt = None if (args.rag_only or args.snapshot_only) else load_prompt()
    live = http_get(agent_url, api_key)
    pre_ts = snapshot("pre-update" if not args.snapshot_only else "snapshot-only",
                      agent_id, live, outgoing_prompt)

    patches: list[str] = []

    if args.snapshot_only:
        print("\n[mode] snapshot-only — no PATCH performed")
    elif args.rag_only:
        print(f"\n[mode] rag-only")
        http_patch(
            agent_url, api_key,
            {"conversation_config": {"agent": {"prompt": {"rag": RAG_CONFIG}}}},
            "rag_config"
        )
        patches.append("rag_config")
    else:
        print(f"\nLoaded prompt: {len(outgoing_prompt)} chars")

        # Step 1: prompt + first_message + language + max_tokens + llm model
        print("\nPATCHing prompt + first_message + language + max_tokens + llm...")
        http_patch(
            agent_url, api_key,
            {
                "conversation_config": {
                    "agent": {
                        "prompt": {
                            "prompt": outgoing_prompt,
                            "max_tokens": LLM_MAX_OUTPUT_TOKENS,
                            "llm": LLM_MODEL,
                            "temperature": LLM_TEMPERATURE,
                        },
                        "first_message": FIRST_MESSAGE,
                        "language": "hi",
                    }
                }
            },
            "prompt+first_message+max_tokens+llm"
        )
        patches.append("prompt+first_message+max_tokens+llm")

        # Step 1b: turn-detection tuning
        print("\nPATCHing turn config (speculative_turn, eagerness, timeout)...")
        http_patch(
            agent_url, api_key,
            {"conversation_config": {"turn": TURN_CONFIG}},
            "turn_config"
        )
        patches.append("turn_config")

        # Step 1c: TTS model + voice retune
        print("\nPATCHing tts config (model_id + stability/similarity/style)...")
        http_patch(
            agent_url, api_key,
            {"conversation_config": {"tts": TTS_CONFIG}},
            "tts_config"
        )
        patches.append("tts_config")

        # Step 2: Re-upload KB (if requested). All .md files from ../knowledge-base/.
        kb_entries = None
        if not args.skip_kb:
            print(f"\nRe-uploading KB files from {KB_DIR}...")
            if not KB_DIR.exists():
                print(f"  [warn] {KB_DIR} does not exist — skipping KB upload")
            else:
                kb_files = sorted(KB_DIR.glob("*.md"))
                doc_ids = []
                for fp in kb_files:
                    doc_ids.append(upload_kb_file(api_key, fp))
                kb_entries = [
                    {"type": "file", "id": d, "name": f"kb_{i:02d}", "usage_mode": "auto"}
                    for i, d in enumerate(doc_ids)
                ]

        # Step 3: PATCH KB attachments + RAG config together
        print("\nPATCHing knowledge_base + RAG tuning...")
        kb_payload = {"rag": RAG_CONFIG}
        if kb_entries is not None:
            kb_payload["knowledge_base"] = kb_entries
        http_patch(
            agent_url, api_key,
            {"conversation_config": {"agent": {"prompt": kb_payload}}},
            "knowledge_base+rag"
        )
        patches.append("knowledge_base+rag")

    # Final: snapshot the post-update live state
    post_ts: str | None = None
    if not args.snapshot_only:
        live_after = http_get(agent_url, api_key)
        post_ts = snapshot("post-update", agent_id, live_after)

    # Refresh the full state dump
    print("\nRefreshing docs/elevenlabs_state/ ...")
    import subprocess
    dump_env = {**os.environ, "XI_API_KEY": api_key}
    try:
        subprocess.run(
            [sys.executable, str(ROOT / "dump_agent_state.py")],
            env=dump_env, check=True, timeout=120,
        )
    except Exception as e:
        print(f"  [warn] dump_agent_state.py failed: {e}", file=sys.stderr)

    # Auto-append a run entry to the changelog.
    if args.snapshot_only:
        mode = "snapshot-only"
    elif args.rag_only:
        mode = "rag-only PATCH"
    else:
        mode = "full PATCH"
    append_changelog(mode, patches, pre_ts, post_ts)

    print("\n[done] snapshots in docs/prompt_versions/ + elevenlabs_state/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
