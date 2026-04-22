# Ladli Behna Outreach — Voice Agent

CM Mohan Yadav voice clone calls Ladli Behna beneficiaries. This app is the browser client + agent-provisioning scripts; the LLM, TTS, and RAG all run on ElevenLabs ConvAI.

Architecture mirrors the proven `cm-voice-bot` stack (sub-1000ms TTFB blueprint) with three differences:
1. **Different system prompt** — *listen 70% / speak 30%*, outreach question-hierarchy, no new promises (see `docs/elevenlabs_agent_prompt_ladli.md`)
2. **Different knowledge base** — points to `../knowledge-base/` (files 01–12 of the outreach project) instead of the CM biography KB
3. **Different first message** — CM greets the beneficiary and opens with the Tier-1 "is the money in your own account" question

Same CM voice clone (`vxeICktjKaYzkMOFXiUL`), same proven model stack (`gemini-2.5-flash` + `eleven_multilingual_v2`), same RAG tuning (4 chunks × 4000 chars), same voice tuning (stability 0.35 / similarity 0.75 / style 0.2).

## Files

```
ladli_behna_app/
├── app/                            Next.js 15 app router
│   ├── api/signed-url/route.ts     WebRTC token handshake (server-only)
│   ├── api/metrics/*               Dashboard data routes
│   ├── dashboard/                  Call history + latency dashboard
│   ├── layout.tsx, page.tsx        Shell + landing
│   └── globals.css                 Tailwind + theme
├── components/VoiceCall.tsx        Single React component; WebRTC + UI
├── lib/elevenlabs.ts               Server-side API helpers + latency aggregation
├── docs/
│   ├── elevenlabs_agent_prompt_ladli.md   System prompt (v1)
│   ├── prompt_versions/                    Timestamped pre/post-PATCH snapshots
│   └── elevenlabs_state/                   Latest full agent dump
├── public/cm.jpg                   Portrait for the call hero
├── setup_agent.py                  One-shot — create the ElevenLabs agent
├── update_agent.py                  Idempotent — PATCH prompt / LLM / TTS / RAG / KB
├── dump_agent_state.py              Capture full state (auto-runs after every PATCH)
├── middleware.ts                    Optional basic-auth gate
├── netlify.toml (at project root)   Deploy config
└── package.json                     Next 15 / React 19 / @elevenlabs/react
```

## First-time setup

```bash
# 1. Install deps
cd ladli_behna_app
npm install

# 2. Set your ElevenLabs API key (same workspace as cm-voice-bot)
export XI_API_KEY=sk_...

# 3. Create the agent on ElevenLabs (new agent, SAME voice clone)
python setup_agent.py
# -> writes VOICE_AGENT_ID and VOICE_API_KEY to .env.local

# 4. Upload the outreach knowledge base and push prompt/model config
python update_agent.py
# -> uploads all ../knowledge-base/*.md as RAG docs
# -> PATCHes prompt, LLM, TTS, RAG, turn-detection
# -> snapshots pre/post state to docs/prompt_versions/
# -> refreshes docs/elevenlabs_state/

# 5. Run the app locally
npm run dev
# http://localhost:3000
```

## Every config change — logged

Every `update_agent.py` run automatically:
- writes a timestamped `{ts}_pre-update.{json,md}` snapshot
- performs the PATCH
- writes a timestamped `{ts}_post-update.{json,md}` snapshot
- refreshes `docs/elevenlabs_state/` with the latest full state

If you change the agent directly in the ElevenLabs dashboard (bypassing the script), run:
```bash
python update_agent.py --snapshot-only
```
to capture the current state in the repo.

## What makes this outreach agent different

Design principles from `knowledge-base/12-what-women-want-asked.md`:
- **Listen 70% / speak 30%** — most turns are 1–3 sentence acknowledgments, not speeches
- **Tier 1 questions baked into the flow** — account-in-own-name, water, her own work, the open-ended *"कोई बात जो आप सरकार को बताना चाहें?"*
- **Do-not-ask list enforced** — zero attendance / loyalty / voting / spouse-occupation / eKYC-jargon questions (see prompt)
- **No new promises** — the agent can acknowledge and route, but never commit new payments, dates, or schemes
- **Numeric safety** — every number spoken in Devanagari words (₹1,500 → *पंद्रह सौ रुपये*)

## Related

- Full blueprint of the low-latency ConvAI pattern: `../../cm voice bot/VOICE_AGENT_BLUEPRINT.md`
- Outreach knowledge base (what the agent retrieves): `../knowledge-base/`
- Voice-call design (flow + safety rails): the design doc referenced from `../knowledge-base/12-what-women-want-asked.md`
