#!/usr/bin/env python3
"""Create the ElevenLabs ConvAI agent for Ladli Behna Outreach.

Usage:
    XI_API_KEY=sk_... python setup_agent.py

Reads the system prompt from docs/elevenlabs_agent_prompt_ladli.md, creates
a NEW agent (separate from the cm-voice-bot agent) with the SAME CM voice
clone and the SAME proven model stack, writes .env.local with the agent id.

After creation, run `python update_agent.py` to upload the knowledge-base/
files as RAG documents.
"""
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).parent
PROMPT_FILE = ROOT / "docs" / "elevenlabs_agent_prompt_ladli.md"
ENV_FILE = ROOT / ".env.local"

# Same CM voice clone used by cm-voice-bot (vxeICktjKaYzkMOFXiUL)
VOICE_ID = os.environ.get("CM_VOICE_ID", "vxeICktjKaYzkMOFXiUL")
AGENT_NAME = "Ladli Behna Outreach — CM Mohan Yadav (Hindi)"
FIRST_MESSAGE = (
    "नमस्ते बहना। मैं मोहन यादव बोल रहा हूं — आपका भाई, मध्य प्रदेश का मुख्यमंत्री। "
    "आज आपसे कुछ बात करनी थी — लाड़ली बहना योजना के बारे में। "
    "पहले यह बताइए — पैसा आपके अपने खाते में ठीक से आ रहा है?"
)
LANGUAGE = "hi"

API_KEY = os.environ.get("XI_API_KEY")
if not API_KEY:
    print("ERROR: set XI_API_KEY env var", file=sys.stderr)
    sys.exit(1)

# Extract the system-prompt block
md = PROMPT_FILE.read_text(encoding="utf-8")
m = re.search(
    r"=+ AGENT SYSTEM PROMPT \(paste into ElevenLabs\) =+\s*(.*?)\s*=+ END OF AGENT SYSTEM PROMPT =+",
    md, re.S,
)
if not m:
    print(f"ERROR: could not locate AGENT SYSTEM PROMPT block in {PROMPT_FILE}", file=sys.stderr)
    sys.exit(2)
system_prompt = m.group(1).strip()
print(f"Loaded system prompt: {len(system_prompt)} chars")

# Proven model stack from cm-voice-bot v5 (numerics-safe):
#   - gemini-2.5-flash — smarter Hindi reasoning than flash-lite
#   - eleven_multilingual_v2 — better Hindi numerics + prosody than turbo
#   - (0.35, 0.75, 0.2) voice tuning for multilingual_v2
payload = {
    "name": AGENT_NAME,
    "conversation_config": {
        "agent": {
            "prompt": {
                "prompt": system_prompt,
                "llm": "gemini-2.5-flash",
                "temperature": 0.5,
                "max_tokens": 800,
            },
            "first_message": FIRST_MESSAGE,
            "language": LANGUAGE,
        },
        "tts": {
            "voice_id": VOICE_ID,
            "model_id": "eleven_multilingual_v2",
            "stability": 0.35,
            "similarity_boost": 0.75,
            "style": 0.2,
            "use_speaker_boost": True,
        },
        "asr": {
            "quality": "high",
            "provider": "elevenlabs",
            "user_input_audio_format": "pcm_16000",
        },
        # Outreach calls should be short (see prompt CALL LENGTH TARGET = 90s).
        # A 6-minute max is generous safety net for edge cases (grievance,
        # crisis handoff) without letting runaway calls drain credits.
        "turn": {"turn_timeout": 7},
        "conversation": {"max_duration_seconds": 360},
    },
    "platform_settings": {
        "call_limits": {"agent_concurrency_limit": -1, "daily_limit_per_agent": -1},
    },
}

url = "https://api.elevenlabs.io/v1/convai/agents/create"
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    url,
    data=data,
    headers={"xi-api-key": API_KEY, "Content-Type": "application/json"},
    method="POST",
)
print(f"POST {url}")
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        result = json.loads(body)
except urllib.error.HTTPError as e:
    err_body = e.read().decode("utf-8", errors="replace")
    print(f"HTTP {e.code} {e.reason}", file=sys.stderr)
    print(err_body, file=sys.stderr)
    sys.exit(3)

print("Response:", json.dumps(result, ensure_ascii=False, indent=2)[:800])

agent_id = result.get("agent_id") or result.get("id")
if not agent_id:
    print("ERROR: no agent_id in response", file=sys.stderr)
    sys.exit(4)
print(f"\n[ok] Agent created: {agent_id}")

env_lines = [
    f'VOICE_AGENT_ID="{agent_id}"',
    f'VOICE_API_KEY="{API_KEY}"',
    'BASIC_AUTH_PASSWORD=""',
]
ENV_FILE.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
print(f"[ok] Wrote {ENV_FILE}")
print("\nNext step:")
print("  python update_agent.py")
print("  (uploads knowledge-base/*.md files to the agent for RAG retrieval)")
