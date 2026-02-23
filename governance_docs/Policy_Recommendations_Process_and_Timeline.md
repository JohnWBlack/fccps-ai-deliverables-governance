# FCCPS AI Advisory Committee — Policy Recommendations Process and Timeline

> **Source:** Converted from the Miro graphic titled **“Policy Recommendations Process and Timeline”** (dated checkpoints shown: 23 Jan, 6 Feb, 20 Feb, 6 Mar, 20 Mar, 10 Apr, 24 Apr, 15 May).

This document is formatted to be **machine-readable first** (YAML timeline objects) and **human-readable second** (summary + critical path).

---

## Machine-readable timeline (YAML)

```yaml
project: FCCPS AI Advisory Committee — AI Policy Recommendations
timeline_name: Policy Recommendations Process and Timeline
version: v0 (extracted from Miro graphic)
timezone: America/New_York

checkpoints:
  - 2026-01-23
  - 2026-02-06
  - 2026-02-20
  - 2026-03-06
  - 2026-03-20
  - 2026-04-10
  - 2026-04-24
  - 2026-05-15

nodes:
  - id: start
    type: start
    label: Start
    date: 2026-01-23

  - id: m1
    type: meeting
    label: Meeting 1
    date: 2026-01-23
    focus: "COMMITTEE: Team Formation + Charter v0"
    produces:
      - id: charter_v0
        type: artifact
        label: "Team Charter v0 (as agreed in meeting)"
    depends_on: []

  - id: m2
    type: meeting
    label: Meeting 2
    date: 2026-02-06
    focus: Shared Baseline
    produces:
      - id: working_agreements
        type: artifact
        label: "Working agreements + draft timeline/objectives + collaboration rules + action items"
    depends_on:
      - charter_v0

  - id: pre_m3_defs
    type: artifact
    label: "One-page Definitions + Assumptions draft + priority misconceptions list + draft grade bands"
    date: 2026-02-20
    depends_on:
      - working_agreements

  - id: pre_m3_risks_ops
    type: artifact
    label: "Members submit: top 3 risks + top 3 opportunities"
    date: 2026-02-20
    depends_on:
      - working_agreements

  - id: m3
    type: meeting
    label: Meeting 3
    date: 2026-02-20
    focus: Values + Principles
    produces:
      - id: policy_principles
        type: artifact
        label: "8–12 Policy Principles (board-ready) + tradeoff statement"
      - id: ms_policy_principles
        type: milestone
        label: "Policy Principles Delivered"
    depends_on:
      - pre_m3_defs
      - pre_m3_risks_ops

  - id: m4
    type: meeting
    label: Meeting 4
    date: 2026-03-06
    focus: "Policy Constraints + Risk Register"
    produces:
      - id: rec_outline_risk_register
        type: artifact
        label: "Recommendations outline + first-pass risk register (top 10 risks + mitigations)"
    depends_on:
      - ms_policy_principles

  - id: m5
    type: meeting
    label: Meeting 5
    date: 2026-03-20
    focus: Draft Recommendations Workshop
    produces:
      - id: ms_draft_sections_complete
        type: milestone
        label: "Draft Sections Complete"
    depends_on:
      - rec_outline_risk_register

  - id: m5_draft_sections
    type: artifact
    label: "Draft sections for 2–3 domains; access/governance direction decision"
    date: 2026-03-20
    depends_on:
      - m5

  - id: m6
    type: meeting
    label: Meeting 6
    date: 2026-04-10
    focus: "Package Integration + Headings Review"
    produces:
      - id: near_final_package
        type: artifact
        label: "Near-final written recommendations + 10–12 slide narrative outline + gap list (with owners)"
      - id: ms_board_ready
        type: milestone
        label: "Board-Ready Package"
    depends_on:
      - ms_draft_sections_complete
      - m5_draft_sections

  - id: m7
    type: meeting
    label: Meeting 7
    date: 2026-04-24
    focus: "Presentation + Feedback Assimilation"
    produces:
      - id: final_talk_track
        type: artifact
        label: "Final talk track + Q&A prep sheet (and/or draft memo)"
    depends_on:
      - ms_board_ready

  - id: m8
    type: meeting
    label: Meeting 8
    date: 2026-05-15
    focus: Response to Proposed Policy
    produces:
      - id: committee_response
        type: artifact
        label: "Committee’s formal response to proposed policy + proposed guardrails/governance"
      - id: ms_final_recs
        type: milestone
        label: "Final Recommendations Delivered"
    depends_on:
      - final_talk_track

  - id: end
    type: end
    label: End
    date: 2026-05-15
    depends_on:
      - ms_final_recs
```

---

## Human-readable summary

### Phases (as depicted)

1. **Forming (23 Jan)**  
   Team formation and **Charter v0**.

2. **Baseline (6 Feb)**  
   Establish shared baseline and **working agreements** (including timeline/objectives and collaboration rules).

3. **Principles (20 Feb)**  
   Compile definitions/assumptions + risks/opportunities; agree **values & principles** → **Policy Principles Delivered** milestone.

4. **Drafting (6 Mar → 20 Mar)**  
   Translate principles into a recommendations outline + risk register; run a drafting workshop → **Draft Sections Complete** milestone.

5. **Integration (10 Apr)**  
   Integrate drafts into near-final package (written recommendations + slide narrative + gaps/owners) → **Board-Ready Package** milestone.

6. **Presentation readiness (24 Apr)**  
   Practice and assimilate feedback; produce **talk track + Q&A** (and/or memo).

7. **Response to proposed policy (15 May)**  
   Deliver the committee’s **formal response** and **guardrails/governance** recommendations → **Final Recommendations Delivered**.

---

## Critical path milestones (gates)

- **Policy Principles Delivered** (post–20 Feb)  
- **Draft Sections Complete** (post–20 Mar)  
- **Board-Ready Package** (post–10 Apr)  
- **Final Recommendations Delivered** (post–15 May)

---

## Notes on fidelity

- Text has been transcribed from the graphic; a few connector labels (e.g., “common/autonomous/progress”) are represented implicitly via `depends_on` and milestone gating.
- If you want, I can align this YAML to the workstream deliverables (owners) so it becomes an executable “who produces what by when” plan.
