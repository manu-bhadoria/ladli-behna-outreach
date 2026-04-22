# Ladli Behna Outreach

Outreach project built around the **Mukhyamantri Ladli Behna Yojana (MP)** — Madhya Pradesh's flagship monthly cash-transfer scheme for women.

The repo now contains **both** a research-grounded knowledge base *and* a working voice agent that calls beneficiaries in the CM's voice to listen, ask the Tier-1 outreach questions, and route grievances. The voice agent reads its system prompt and ground truth directly from the knowledge base.

## Contents

```
ladli-behna-outreach/
├── README.md
├── netlify.toml                           Deploy config (base = ladli_behna_app)
├── knowledge-base/
│   ├── 01-scheme-overview.md              Launch, purpose, official portal
│   ├── 02-eligibility.md                  Who qualifies, who doesn't
│   ├── 03-benefits-disbursement.md        Amount, DBT, installment cadence
│   ├── 04-application-kyc.md              How to apply, Samagra e-KYC
│   ├── 05-coverage-stats.md               Beneficiary counts, outlays
│   ├── 06-history-politics.md             Origin under Shivraj; 2023 election impact
│   ├── 07-exclusions-grievances.md        Removals, age-out, controversies (tactical)
│   ├── 08-recent-updates.md               Latest installments, ₹3,000 promise
│   ├── 09-outreach-talking-points.md      Ready-to-use messaging
│   ├── 10-sources.md                      Source URLs for every fact
│   ├── 11-problems-deep.md                Structural + dignity-level critiques, Vijay Shah
│   └── 12-what-women-want-asked.md        Voice-call question design, grounded in beneficiary quotes
└── ladli_behna_app/                        Voice agent — Next.js thin client + ElevenLabs ConvAI
    ├── README.md                           Setup, run, deploy instructions
    ├── docs/elevenlabs_agent_prompt_ladli.md   System prompt (v1)
    ├── setup_agent.py                      Create the ElevenLabs agent (one-shot)
    ├── update_agent.py                     PATCH prompt / LLM / TTS / RAG / KB
    ├── dump_agent_state.py                  Capture full live state
    └── app/, components/, lib/             React UI + server routes
```

## How to use

**Reading the KB:** start at `knowledge-base/01-scheme-overview.md`. For outreach copy jump to `09-outreach-talking-points.md`. Voice-call content design is in `12-what-women-want-asked.md`, structural problems in `11-problems-deep.md`, operational failure modes in `07-exclusions-grievances.md`. Every numeric claim cites `10-sources.md`.

**Running the voice agent:** see `ladli_behna_app/README.md`. Short version:
```bash
cd ladli_behna_app
npm install
export XI_API_KEY=sk_...
python setup_agent.py         # creates the ElevenLabs agent
python update_agent.py         # uploads KB + pushes prompt/model config
npm run dev                    # local dev at http://localhost:3000
```

**Architecture:** borrowed whole-cloth from the proven `cm voice bot` project (sub-1000ms TTFB ConvAI blueprint), with a fundamentally different system prompt (*listen 70% / speak 30%*, Tier-1 questions, no new promises) and the knowledge-base/ files above as the RAG corpus. Same CM voice clone.

## Ground rules for this KB

- **Facts only** — no speculation, no political advocacy. Numbers cite the installment/date they came from.
- **State it in both English and Hindi keyword** where the Hindi term is the one field staff will hear (`लाड़ली बहना`, `समग्र`, `ई-केवाईसी`).
- **Freshness** — installment counts, monthly amount, and beneficiary totals drift. Before citing a number externally, re-check against the official portal at `cmladlibahna.mp.gov.in`.
- **Scope** — this KB covers the Madhya Pradesh scheme only. Maharashtra's "Ladki Bahin" is a different programme; do not conflate.
