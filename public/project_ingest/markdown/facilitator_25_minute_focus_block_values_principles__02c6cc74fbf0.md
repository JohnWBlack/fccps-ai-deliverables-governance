<!-- provenance:{"extractor_version":"2.0.0","pipeline_version":"2.0.0","project":"FCCPS AI Committee"} -->

One-Pager: Facilitator (25-Minute Focus Block — Values & Principles)

Purpose and Outputs (by minute 25)

8–12 merged principles placed in F4 slots (numbered, sponsor-initialed)

1 tradeoff statement in F5 (plus 1 backup recorded)

Consent record + any exceptions / smallest-change requests in F6

Cut list recorded (nothing “lost”)

Non-negotiables (say once; enforce quietly)

Humans move cards.

No Pass without sponsor initials.

AI suggests; committee decides.

20-second rule: if not resolvable → Revise.

No wordsmithing in F3/F4 (minimal edits only).

0:00–0:04 — Launch + F1 orientation

Say:

“We have 25 minutes to produce 8–12 principles plus one tradeoff statement.”

“AI = formatter/reviewer/suggester; not the decider.”

“F1 themes are read-only. Any missing theme that would change principles? If not, we proceed.”

“Principles are decision language: ‘FCCPS will…’ or ‘When X conflicts with Y…’”

0:04–0:07 — F2: Adopt two, write one (physical wall)

Say:

“Everyone to the wall.”

“Adopt two AI seeds—initial as sponsor.”

“Write one new principle or revision—post under the right theme.”

Do:

Keep pace; no discussion.

Ask wall marshal to confirm initials on adopted seeds.

0:07–0:13 — F3: Quality Filter (AI pre-score → human confirm/override)

Say (exact lines):

“AI is our checklist robot—it pre-scores to help us move fast; we decide.”

“Rule: AI suggests; humans move. If you disagree, OVERRIDE.”

“20-second rule: if it can’t be fixed fast, it goes to Revise.”

Human action: sponsors move their cards to Pass / Revise / Park.
If conflict arises: “If disagreement persists, it stays in Revise—moving on.”

FR tags (quick reference):
FR1 vague · FR2 implementation detail · FR3 not testable · FR4 conflicts · FR5 actor unclear · FR6 needs tradeoff decision

Close F3:

“Any strong objections to placement? One sentence. Otherwise F3 is locked.”

0:13–0:19 — F4: Merge + Cap (cluster, merge, fill 8–12)

Say:

“F4 is de-duplication and capping. Reduce, don’t perfect.”

“Cluster by intent. Pick a base card. Merge to one sentence.”

Do:

Appoint two merge leads.

“Fill 8–12 slots. Everything else goes to cut list (recorded).”

“Quick coverage check: learning, integrity, teacher practice, governance, equity, privacy/trust.”

Close F4:

“Call collisions in two words. I will pick one for F5 to stay on time.”

0:19–0:23 — F5: Tradeoff Statement (camera+AI options; human chooses)

Say:

“Tradeoff = what we prioritize when principles collide—default posture + exception.”

“Collision for today: [X vs Y].”

“AI will draft three options; we pick and lightly edit one.”

Choose:

Vote A/B/C quickly; apply smallest edit.

“Sponsor initials on the chosen tradeoff statement.”

0:23–0:25 — F6: Consent-first ratification (package + one blocker handling)

Say:

“Consent = you can live with it and support it publicly.”

“Thumbs up = consent; hand up = cannot consent.”

If one cannot consent: “What’s the smallest change that gets you to consent? One sentence.”

“We are not reopening the list—only deciding whether we can adopt this smallest change now.”

If fixable in 30 seconds → adopt; else → record exception and move on.

Close:

“Consent recorded. Exceptions captured. Focus Block complete.”

One-Pager: AI Operator (Camera + AI Workflow)

Mission (stay inside the lane)

Use camera as capture device; use model as formatter / reviewer / suggester.

Never move cards. Never decide Pass/Revise/Park.

Post everything in the AI Suggestions (not decisions) area (or hand facilitator a single-page list).

Photo hygiene (do this every time)

No faces / no student info in frame.

Straight-on angle, good lighting, fill the frame with stickies, avoid glare.

If text is dense, take two close-ups rather than one unreadable wide shot.

Trigger photos (minimum set)

End of F2: full wall (AI seeds + write-ins)

Mid F3 (optional): Revise pile only (for minimal edits)

Mid F4: clustered Pass set (stacks by intent)

Start F5: merged F4 list + a note showing collision pair

End F6: final ratified set + tradeoff statement

Output formatting (make it usable fast)

For F3, output one line per card:
ID/Title — Suggested: PASS/REVISE/PARK — FR tags — Minimal edit (if revise)

Keep minimal edits:

one sentence

decision language

not implementation-specific

Prompts (copy/paste)

Prompt A — F3 Pre-score (from F2 photo)

Extract each principle candidate. Apply Quality Filter C1–C5.
Output one line per item: ID/Title — Suggested PASS/REVISE/PARK — FR tag(s) — Minimal edit (if REVISE).
Keep edits one sentence and not implementation-specific.

Quality Filter (internal checklist):
C1 decision-guiding · C2 testable · C3 not implementation-specific · C4 clear actor/audience · C5 no hidden tradeoff (or explicit)

FR tags: FR1 vague · FR2 implementation detail · FR3 not testable · FR4 conflicts · FR5 actor unclear · FR6 needs tradeoff decision

Prompt B — Revise pile minimal edits (optional)

For each REVISE item, propose the smallest one-sentence edit that fixes the FR issue(s) while staying decision-guiding and not implementation-specific.

Prompt C — F4 Merge + Cap (from clustered Pass photo)

Cluster by shared intent; identify near-duplicates.
Propose one merged best-wording principle per cluster (one sentence).
Output: merged set of 8–12, cut list (with source items), and likely collision pairs.

Prompt D — F5 Tradeoff options (from merged list + collision pair)

Using the merged principles and collision pair [X vs Y], draft 3 tradeoff statements (<30 words) using:
(1) prioritize A even when it costs B because C
(2) default X unless exception
(3) accept risk to achieve benefit, mitigated by guardrail
Keep decision-guiding; no implementation steps.

How to post results (so the room trusts it)

Label outputs clearly: “AI Suggestions (not decisions)”

For tradeoffs: create three stickies labeled AI Option A / B / C

If you see uncertainty, tell facilitator: “Low-confidence due to unreadable text—need closer photo or typed list.”

Fallback if photos aren’t readable

Ask Miro Scribe to paste a typed list of candidates into chat.

Run the same prompts on the typed list and return results in the same format.
