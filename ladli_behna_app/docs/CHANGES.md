# Ladli Behna Outreach Agent — Changelog

Human-curated semantic changelog for the ElevenLabs voice agent `agent_9901kpt6a6xqf3gaahtr44ycvqgc` ("Ladli Behna Outreach — CM Mohan Yadav (Hindi)").

Reverse chronological — newest entry first. The automated run log sits below the separator at the bottom of this file and is appended by `update_agent.py`. Human-curated semantic entries stay above the separator; script-appended entries stay below.

---

## v2 · 2026-04-22 · Conversation-flow rewrite

**Trigger:** First local test after v1 went live. User verdict after listening to the call: *"conversation flow is really shit."* The agent was technically on-script but emotionally tone-deaf — executing a form, not having a conversation.

**Summary of the change in one sentence:** Turn the agent from a Tier-1 question dispenser into a listener that holds silence, follows up on what she said, and closes on something specific she mentioned — with a UI that foregrounds her, not the CM.

**Diagnosis:**

- v1's Tier-1 "priority order" questions were being treated by the model as a **rigid form-fill checklist**. Once question 1 was answered, the agent marched to question 2 regardless of what the beneficiary had just said. The word "priority" in the prompt was being read as "sequence" — a prompt-engineering mistake, not a model failure.

- The model was **not dwelling**. Zero follow-up on her actual answer before topic-shifting. If she mentioned her son's school fees, the agent would acknowledge and immediately pivot to *"पैसा खाते में आ रहा है?"* — leaving the thread dead. The result felt like an enumerator with a clipboard, not the CM calling to check in.

- Opening was **too transactional**. It jumped to *"पैसा खाते में आ रहा है?"* inside the first 15 seconds. No acknowledgement that it is inherently strange for a rural woman to receive a call from the CM, and no warmth to settle her before the questioning began. A real person receiving that call would be confused, possibly scared — and v1 gave her no on-ramp.

- *बहना* was being uttered every turn — theatrical, saccharine, broke the illusion. Real conversation does not repeat a term of address that often; doing so in Hindi especially reads as performative.

- Close was a **generic sign-off** (*"धन्यवाद बहना, आपका ध्यान रखिए"*) with zero reference to what she had actually said on the call. Indistinguishable from a robocall outro. The entire emotional payoff of the interaction — she was heard — was thrown away in the last ten seconds.

**Changes:**

1. **Opening rewritten.** Now acknowledges the oddness of a CM cold-call before asking anything transactional. Uses the CM's actual verbal tic *"देखिए"* and flips intent from extraction (*"पैसा आ रहा है?"*) to presence (*"आपकी आवाज़ सुनना चाहता था"*). Establishes identity, intent, and permission to talk in the first three sentences — then pauses.

2. **Tier-1 checklist demoted to a pool.** Prompt now explicitly forbids topic-shifts that skip past what she just said. The four questions are available, not mandatory, and not ordered. Pick the one that naturally follows her last utterance — or pick none, and just sit with what she said.

3. **Mandatory follow-up rule.** Before changing topic, the agent **must** ask one specific follow-up on what she last said. Hard constraint, stated twice in the prompt (once in the behavior section, once in the "do not" section). The two placements are deliberate redundancy — the rule is load-bearing.

4. **One-syllable turns allowed.** *"हम्म"*, *"जी"*, *"अच्छा"* now count as complete turns. Silence and minimal acknowledgement are explicitly framed as tools, not failure states. The agent is no longer required to fill every turn with a full sentence. This is how real listeners sound; also cheaper in latency and tokens.

5. **बहना usage capped at 1–2 times per entire call.** Was running theatrical; now reserved for moments of genuine warmth (typically the opening and one other beat). Default address is no vocative at all — direct Hindi is warmer than forced endearment. Rule of thumb embedded in the prompt: if you would not say "sister" in English at that point, do not say *बहना* in Hindi.

6. **Simpler Hindi vocabulary mandate.** *पैसा* not *आर्थिक सहायता*; *बहन* not *लाभार्थी*; *मिल रहा है* not *प्राप्त हो रहा है*. Matches how rural MP women actually speak. Prompt includes a short glossary of preferred/avoid pairs.

7. **Pace permission.** Prompt now explicitly permits slowing down and letting `eleven_multilingual_v2` render at its natural cadence. No rushing to fill silence, no stacking sentences to compress a turn.

8. **Graceful refusal handling.** If she sounds suspicious, scared, or uninterested, the agent must acknowledge it (*"समझ सकता हूँ, अजीब लगता है"*) and offer to end the call gently — do not push through the script. Trust preserved > data collected.

9. **Close must be specific.** The closing line must reference something concrete she said during the call (her son's school, the roof repair, the gas cylinder, the kirana shop, whatever was mentioned). Generic *"धन्यवाद बहना"* sign-offs are now explicitly forbidden.

10. **New success metric.** A call succeeds if **she said one specific thing and it was acknowledged and followed up on** — NOT if all four Tier-1 questions were asked. This is stated in the prompt as the agent's own definition of success, so the model optimises toward depth, not coverage. This reframing is the single most important change in v2: it inverts what "doing well" means from the model's perspective.

**Risks introduced by v2 (to watch for):**

- Demoting the Tier-1 checklist to a pool means some calls may end with zero of the four canonical questions answered. This is accepted as a trade-off — depth over coverage — but if it happens on more than ~1 call in 5, the pool rule may need a soft "at least one" floor.
- "Close must be specific" can degrade to a forced cite if the call did not surface anything concrete. If that happens, the fallback is a warm non-cite close, not a return to the generic *"धन्यवाद बहना"*. Prompt should spell this out in the next revision if it becomes a problem.
- Capping *बहना* at 1–2 uses per call relies on the model tracking its own vocative count. `gemini-2.5-flash` is reasonably good at this but not perfect. Worth auditing transcripts.

**Prompt structure notes:**

- The prompt is now roughly ordered as: identity → why this call is happening → listening posture → opening line → mandatory follow-up rule → Tier-1 pool → forbidden moves → voice/vocabulary guardrails → graceful-refusal branch → close rule → success metric.
- The "mandatory follow-up" rule appears in two places by design — once positively (what to do) and once in the do-not section (what not to do: never topic-shift without a follow-up first). Redundancy here is cheap and the rule is the hinge of the entire conversational shape.
- The Tier-1 pool is written as a menu, not a sequence. Each item is paired with a short cue for when it is natural to reach for it — e.g., financial wellbeing is natural only after something about family came up.

**Frontend changes (coordinated with this release):**

- Portrait swapped from CM image (`cm.jpg`) to a rural MP woman beneficiary image (`ladli.jpg`). The caller is the CM; the subject of the call — and the person the UI should foreground — is her.

- Subtitle changed from *"मुख्यमंत्री · मध्य प्रदेश / डॉ. मोहन यादव"* to *"लाड़ली बहना · मध्य प्रदेश / बहना से संवाद / मुख्यमंत्री डॉक्टर मोहन यादव की ओर से"*. Reframes the app from "the CM speaks" to "a conversation with a बहना, on behalf of the CM".

- Color palette reworked to a rural-MP feminine aesthetic. New CSS variables in `app/globals.css`:
  - Primary: rose `#c14a5a` (was saffron) — reads as sindoor / bridal, not political-poster saffron
  - Secondary warm: marigold `#e88a2f` — the marigold is the most recognisable rural MP flower and carries ritual warmth
  - Accent: peacock teal `#2a7a7f` — standard MP folk-art accent, sits well against rose and marigold
  - Backgrounds: cream / wheat — wheat field palette, grounds the UI geographically
  - Highlights: gold accents — for buttons and active states
- Why the shift away from saffron: saffron in a political-facing UI reads as party colour, which would wrongly frame this as campaign material. The Ladli Behna programme is a state scheme; the UI should read as domestic and feminine, not partisan.

**Scope note:** v2 is a prompt + frontend change only. Voice clone, model, RAG settings, and knowledge base are all unchanged from v1. If call quality is still poor after v2, the next dial is the prompt again — not the stack.

**Rollout:** Local-only. No outbound calls have been placed to real beneficiaries in either v1 or v2 — all testing so far is the user talking to the agent directly through the local dev UI. Real-beneficiary calls are gated on v2 passing a qualitative bar on self-testing.

**Adjacent changes not yet made (candidates for v3):**

- Per-district phrasing tweaks (Malwa vs Bundelkhand vs Mahakaushal — the warmth registers differ).
- A lightweight post-call notes artefact so the "specific thing she said" is captured somewhere reviewable, not only in the transient transcript.
- An optional "caller identifies themselves twice" mode for beneficiaries who miss the opening — currently the identity is stated once and silence follows.

**Snapshots:** Will be captured as `2026-04-22T<TS>_pre-update.{json,md}` and `2026-04-22T<TS>_post-update.{json,md}` in `docs/prompt_versions/` when `update_agent.py` runs for this release. The run log entry below the separator will record the exact timestamps.

**Files touched:**

- `docs/elevenlabs_agent_prompt_ladli.md` — full prompt rewrite
- `app/globals.css` — palette variables
- `app/page.tsx` (or wherever the subtitle + portrait live) — copy + image swap
- `public/ladli.jpg` — new portrait asset

**Things to watch on next test:**

- Does the agent actually hold silence after her first answer, or does it still rush to the next Tier-1 pool question?
- Does the closing line cite something specific, or does the model default back to a generic *"धन्यवाद"* when it can't find a hook? If it defaults, the follow-up discipline upstream was too weak — fix there, not at the close.
- Is *बहना* actually used 1–2 times total, or does the model quietly drift back to per-turn usage over a long call?
- Does the agent accept *"नहीं, मुझे नहीं बात करनी"* gracefully, or does it push?
- Does the opening feel like a real person on the line, or does it still read as a synthesised greeting? The *"देखिए"* tic is load-bearing here — if it is being dropped by the TTS prosody, re-examine.
- If she gives a very short answer (one word), does the agent follow up or topic-shift? A one-word answer is the model's hardest failure mode — the natural instinct is to move on, but v2 requires it to probe.

---

## v1 · 2026-04-22 · Initial agent creation

*(Retroactive entry — written at the same sitting as v2 to establish a baseline.)*

**Trigger:** New project. Need a voice agent that can place outbound calls as CM Mohan Yadav to Ladli Behna scheme beneficiaries in Madhya Pradesh — listening-first, not extractive, Hindi-first, and built from a proven blueprint rather than from scratch.

**Blueprint provenance:** The `cm-voice-bot` project (sibling repo) had already solved the hard parts — voice clone, Hindi-first prosody tuning, RAG chunking for Hindi source docs, ElevenLabs agent configuration. v1 of this project is a deliberate clone of that configuration with the prompt swapped out for the Ladli Behna use case. Anything that worked in `cm-voice-bot` was kept; nothing was re-invented.

**Changes:**

- Agent provisioned on ElevenLabs as `agent_9901kpt6a6xqf3gaahtr44ycvqgc`, named **"Ladli Behna Outreach — CM Mohan Yadav (Hindi)"**.

- **Architecture cloned from the proven `cm-voice-bot` blueprint.** Same CM voice clone `vxeICktjKaYzkMOFXiUL`. Same model stack: `gemini-2.5-flash` for the LLM, `eleven_multilingual_v2` for TTS. Same 4×4000 RAG tuning (four documents per query, 4000-token chunks). Voice settings: stability `0.35`, similarity `0.75`, style `0.2`. `max_tokens` 800.

- **Prompt v1** designed for outbound CM→beneficiary calls, with these structural elements:
  - Listening posture: agent talks ~30%, beneficiary ~70%.
  - Tier-1 question hierarchy covering scheme receipt, use of funds, pending issues, and family wellbeing.
  - Explicit do-not-ask list: no attendance questions, no loyalty probes, no voting intent, no political asks of any kind.
  - Numeric safety rules: never quote amounts not in the KB; never promise disbursement dates; defer to *"आपके CM हेल्पलाइन से confirm करवा देंगे"* if unsure.
  - Language: Hindi-first, with quiet English fallbacks allowed only for proper nouns (scheme names, place names).

- **12 knowledge-base files uploaded as RAG documents** — all of `knowledge-base/01-scheme-overview.md` through `knowledge-base/12-what-women-want-asked.md`. Indexed and attached to the agent. Coverage: scheme eligibility, disbursement mechanics, common complaints, district-wise nuances, cultural etiquette around receiving money from the state, and a bank of things women commonly want asked about.

- **Initial snapshots:** `2026-04-22T085346Z_pre-update.{json,md}` and `2026-04-22T085405Z_post-update.{json,md}` in `docs/prompt_versions/`.

**Known issues that motivated v2** (see above): rigid Tier-1 execution, transactional opener, overuse of *बहना*, generic close. Caught on first local test — did not reach any real beneficiary.

**What v1 got right (keep for future versions):**

- The core architecture choice — cloning from `cm-voice-bot` — was correct. Voice, model stack, and RAG tuning did not need to change in v2, and should not change casually in future versions either. When something goes wrong in these agents it is almost always the prompt, not the stack.
- The do-not-ask list is solid and politically defensible. No future version should weaken it.
- The 12-file KB is comprehensive enough that v1 rarely hallucinated a number. RAG retrieval is working as intended.
- `max_tokens` 800 is enough for any legitimate turn in this conversational shape and discourages the model from monologuing.

**Files touched:**

- `docs/elevenlabs_agent_prompt_ladli.md` — created
- `docs/prompt_versions/` — first two snapshots
- `docs/elevenlabs_state/` — initial full state dump
- `knowledge-base/*.md` — uploaded as RAG, not modified

---

## Run Log (auto-appended by update_agent.py)

Every successful `update_agent.py` run appends one entry below with timestamp, mode, PATCH list, and snapshot file names. Human-curated semantic entries stay above the separator.

### 2026-04-22T10:42:12Z · snapshot-only
- patches: _(none)_
- pre-snapshot: `prompt_versions/2026-04-22T104208Z_snapshot-only.md`
- post-snapshot: _(none)_

### 2026-04-22T10:46:22Z · full PATCH
- patches: `prompt+first_message+max_tokens+llm`, `turn_config`, `tts_config`, `knowledge_base+rag`
- pre-snapshot: `prompt_versions/2026-04-22T104604Z_pre-update.md`
- post-snapshot: `prompt_versions/2026-04-22T104616Z_post-update.md`

### 2026-04-22 · pronunciation dictionary (laadli retroflex /ɽ/)
- script: `create_pronunciation_dict.py` (one-shot)
- patches: `tts.pronunciation_dictionary_locators`
- dictionary_id: `LHXBo1zDDZQ0QAVmklo1` (name: `ladli-behna-laadli-fix-v1`, version `8ZPwDmTLTKBqMQwwUAMH`)
- rules: 10 IPA phoneme rules covering लाड़ली / लाडली / लाड़्ली / "लाड़ली बहना" + Latin variants (laadli, ladli, Ladli, Laadli, "Ladli Behna", "Laadli Behna") all mapped to `laːɽliː` (+ ` bɛɦnaː` for the phrase variants)
- endpoint: `/v1/pronunciation-dictionaries/add-from-rules` (`add-from-file` rejected PLS XML with `Lexicon file formatted incorrectly`)
- metadata saved: `docs/pronunciation_dict_ladli.json`
