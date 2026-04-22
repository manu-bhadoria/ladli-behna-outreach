#!/usr/bin/env python3
"""Create an ElevenLabs pronunciation dictionary (PLS/IPA) that fixes the
retroflex flap /ɽ/ in "लाड़ली" (laadli) — the most-spoken word in the
Ladli Behna Outreach agent — and attach it to the live agent config.

Usage:
    XI_API_KEY=sk_... python create_pronunciation_dict.py
"""
import json
import os
import sys
import urllib.request
import urllib.error
import uuid
from pathlib import Path

ROOT = Path(__file__).parent
ENV_FILE = ROOT / ".env.local"

# PLS 1.0 — W3C Pronunciation Lexicon Specification, alphabet="ipa".
# ElevenLabs eleven_multilingual_v2 accepts IPA phonemes per-grapheme.
# /ɽ/ is the voiced retroflex flap present in लाड़ली (Devanagari nukta on ड).
# We cover:
#   - Devanagari forms (with + without nukta, common misspellings)
#   - Two-word phrase "लाड़ली बहना"
#   - Latin transliterations the LLM might occasionally emit
PLS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<lexicon version="1.0"
      xmlns="http://www.w3.org/2005/01/pronunciation-lexicon"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.w3.org/2005/01/pronunciation-lexicon
        http://www.w3.org/TR/2007/CR-pronunciation-lexicon-20071212/pls.xsd"
      alphabet="ipa"
      xml:lang="hi-IN">
  <lexeme>
    <grapheme>लाड़ली</grapheme>
    <phoneme>laːɽliː</phoneme>
  </lexeme>
  <lexeme>
    <grapheme>लाडली</grapheme>
    <phoneme>laːɽliː</phoneme>
  </lexeme>
  <lexeme>
    <grapheme>लाड़्ली</grapheme>
    <phoneme>laːɽliː</phoneme>
  </lexeme>
  <lexeme>
    <grapheme>लाड़ली बहना</grapheme>
    <phoneme>laːɽliː bɛɦnaː</phoneme>
  </lexeme>
  <lexeme>
    <grapheme>लाडली बहना</grapheme>
    <phoneme>laːɽliː bɛɦnaː</phoneme>
  </lexeme>
  <lexeme>
    <grapheme>laadli</grapheme>
    <phoneme>laːɽliː</phoneme>
  </lexeme>
  <lexeme>
    <grapheme>Laadli</grapheme>
    <phoneme>laːɽliː</phoneme>
  </lexeme>
  <lexeme>
    <grapheme>ladli</grapheme>
    <phoneme>laːɽliː</phoneme>
  </lexeme>
  <lexeme>
    <grapheme>Ladli</grapheme>
    <phoneme>laːɽliː</phoneme>
  </lexeme>
  <lexeme>
    <grapheme>Ladli Behna</grapheme>
    <phoneme>laːɽliː bɛɦnaː</phoneme>
  </lexeme>
  <lexeme>
    <grapheme>Laadli Behna</grapheme>
    <phoneme>laːɽliː bɛɦnaː</phoneme>
  </lexeme>
</lexicon>
"""


def load_env():
    env = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def http_get(url, api_key):
    req = urllib.request.Request(url, headers={"xi-api-key": api_key})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_patch(url, api_key, payload, label):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        method="PATCH",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code} on {label}: {body}", file=sys.stderr)
        raise


def try_add_from_file(api_key, pls_xml, name):
    """Attempt POST /v1/pronunciation-dictionaries/add-from-file with the PLS XML."""
    url = "https://api.elevenlabs.io/v1/pronunciation-dictionaries/add-from-file"
    boundary = f"----pd{uuid.uuid4().hex}"
    filename = "ladli-fix.pls"

    parts = []
    parts.append(f"--{boundary}\r\n")
    parts.append(
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
    )
    parts.append("Content-Type: application/pls+xml\r\n\r\n")
    body = "".join(parts).encode("utf-8") + pls_xml.encode("utf-8") + b"\r\n"

    body += f'--{boundary}\r\nContent-Disposition: form-data; name="name"\r\n\r\n{name}\r\n'.encode(
        "utf-8"
    )
    body += (
        f'--{boundary}\r\nContent-Disposition: form-data; name="description"\r\n\r\n'
        f'Hindi retroflex flap fix for laadli/लाड़ली (core term in Ladli Behna agent).\r\n'
    ).encode("utf-8")
    body += f"--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "xi-api-key": api_key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        print(f"[add-from-file] HTTP {e.code}: {body_text}", file=sys.stderr)
        return None


def try_add_from_rules(api_key, name):
    """Fallback: JSON rules endpoint, phoneme_alphabet='ipa'."""
    url = "https://api.elevenlabs.io/v1/pronunciation-dictionaries/add-from-rules"
    rules = [
        {
            "type": "phoneme",
            "string_to_replace": "लाड़ली",
            "phoneme": "laːɽliː",
            "alphabet": "ipa",
        },
        {
            "type": "phoneme",
            "string_to_replace": "लाडली",
            "phoneme": "laːɽliː",
            "alphabet": "ipa",
        },
        {
            "type": "phoneme",
            "string_to_replace": "लाड़ली बहना",
            "phoneme": "laːɽliː bɛɦnaː",
            "alphabet": "ipa",
        },
        {
            "type": "phoneme",
            "string_to_replace": "लाडली बहना",
            "phoneme": "laːɽliː bɛɦnaː",
            "alphabet": "ipa",
        },
        {"type": "phoneme", "string_to_replace": "laadli", "phoneme": "laːɽliː", "alphabet": "ipa"},
        {"type": "phoneme", "string_to_replace": "Laadli", "phoneme": "laːɽliː", "alphabet": "ipa"},
        {"type": "phoneme", "string_to_replace": "ladli", "phoneme": "laːɽliː", "alphabet": "ipa"},
        {"type": "phoneme", "string_to_replace": "Ladli", "phoneme": "laːɽliː", "alphabet": "ipa"},
        {
            "type": "phoneme",
            "string_to_replace": "Ladli Behna",
            "phoneme": "laːɽliː bɛɦnaː",
            "alphabet": "ipa",
        },
        {
            "type": "phoneme",
            "string_to_replace": "Laadli Behna",
            "phoneme": "laːɽliː bɛɦnaː",
            "alphabet": "ipa",
        },
    ]
    payload = {
        "name": name,
        "description": "Hindi retroflex flap fix for laadli/लाड़ली (core term in Ladli Behna agent).",
        "rules": rules,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        print(f"[add-from-rules] HTTP {e.code}: {body_text}", file=sys.stderr)
        return None


def main():
    env = load_env()
    api_key = os.environ.get("XI_API_KEY") or env.get("VOICE_API_KEY")
    agent_id = env.get("VOICE_AGENT_ID")
    if not api_key or not agent_id:
        print("ERROR: need XI_API_KEY/VOICE_API_KEY and VOICE_AGENT_ID", file=sys.stderr)
        return 1

    name = "ladli-behna-laadli-fix-v1"

    print("Step 1: attempt add-from-file (PLS XML)...")
    result = try_add_from_file(api_key, PLS_XML, name)

    if not result:
        print("\nStep 1 failed. Step 2: attempt add-from-rules (JSON IPA)...")
        result = try_add_from_rules(api_key, name)

    if not result:
        print("\nBoth PLS endpoints failed. See stderr above.", file=sys.stderr)
        return 2

    print(f"\nPronunciation dictionary created:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    dict_id = result.get("id") or result.get("pronunciation_dictionary_id")
    version_id = result.get("version_id") or result.get("latest_version_id")
    if not dict_id:
        print("ERROR: could not find dictionary id in response.", file=sys.stderr)
        return 3

    # Attach to agent.
    agent_url = f"https://api.elevenlabs.io/v1/convai/agents/{agent_id}"
    print(f"\nStep 3: PATCH agent {agent_id} with dict {dict_id} (version {version_id})...")

    locator = {"pronunciation_dictionary_id": dict_id}
    if version_id:
        locator["version_id"] = version_id

    payload = {
        "conversation_config": {
            "tts": {
                "pronunciation_dictionary_locators": [locator]
            }
        }
    }
    http_patch(agent_url, api_key, payload, "tts.pronunciation_dictionary_locators")

    # Verify.
    live = http_get(agent_url, api_key)
    attached = (
        live.get("conversation_config", {})
        .get("tts", {})
        .get("pronunciation_dictionary_locators", [])
    )
    print("\nLive pronunciation_dictionary_locators now:")
    print(json.dumps(attached, indent=2, ensure_ascii=False))

    if not attached:
        print("WARN: locator did not stick on the live config!", file=sys.stderr)
        return 4

    # Persist the result for future reference.
    out_path = ROOT / "docs" / "pronunciation_dict_ladli.json"
    out_path.write_text(
        json.dumps(
            {
                "dictionary_id": dict_id,
                "version_id": version_id,
                "name": name,
                "agent_id": agent_id,
                "created_response": result,
                "live_locators": attached,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"\nSaved metadata to {out_path}")
    print("\n[done]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
