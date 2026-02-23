# FCCPS AI Advisory Committee — Master Timeline (Workstream-aligned)

**Version:** v1 (workstream-aligned)  
**Last updated:** 2026-02-07  
**Purpose:** Single machine-readable timeline that includes meetings, milestones, committee-level artifacts, and workstream deliverables (with owners, dependencies, and decision gates).

---

## Machine-readable timeline (YAML)

```yaml
project: FCCPS AI Advisory Committee — AI Policy Recommendations
timeline_name: Policy Recommendations Process and Timeline
version: v1 (workstream-aligned)
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
status_values:
- not_started
- in_progress
- draft_complete
- reviewed
- final
nodes:
- id: start
  type: start
  label: Start
  date: '2026-01-23'
- id: m1
  type: meeting
  label: Meeting 1
  date: '2026-01-23'
  focus: 'COMMITTEE: Team Formation + Charter v0'
  produces:
  - id: charter_v0
    type: artifact
    label: Team Charter v0 (as agreed in meeting)
    status: not_started
  depends_on: []
  facilitator: John Black (Chair)
  inputs_expected: []
  decision_gates: []
- id: m2
  type: meeting
  label: Meeting 2
  date: '2026-02-06'
  focus: Shared Baseline
  produces:
  - id: working_agreements
    type: artifact
    label: Working agreements + draft timeline/objectives + collaboration rules +
      action items
    status: not_started
  depends_on:
  - charter_v0
  facilitator: John Black (Chair)
  inputs_expected:
  - charter_v0
  decision_gates:
  - Confirm workstream leads/co-leads and responsibilities
  - Confirm meeting outputs for 20 Feb checkpoint
- id: pre_m3_defs
  type: artifact
  label: One-page Definitions + Assumptions draft + priority misconceptions list +
    draft grade bands
  date: '2026-02-20'
  depends_on:
  - working_agreements
  owner: Tom Colvin (WS-RSB) + John Black (integration)
  status: not_started
- id: pre_m3_risks_ops
  type: artifact
  label: 'Members submit: top 3 risks + top 3 opportunities'
  date: '2026-02-20'
  depends_on:
  - working_agreements
  owner: All members (submission) + John Black (synthesis)
  status: not_started
- id: m3
  type: meeting
  label: Meeting 3
  date: '2026-02-20'
  focus: Values + Principles
  produces:
  - id: policy_principles
    type: artifact
    label: 8–12 Policy Principles (board-ready) + tradeoff statement
    status: not_started
  - id: ms_policy_principles
    type: milestone
    label: Policy Principles Delivered
    status: not_started
  depends_on:
  - pre_m3_defs
  - pre_m3_risks_ops
  facilitator: John Black (Chair)
  inputs_expected:
  - pre_m3_defs
  - pre_m3_risks_ops
  decision_gates:
  - Adopt 8–12 Policy Principles (board-ready) + tradeoff statement
  - Select working grade-band structure (or decide what remains open)
- id: m4
  type: meeting
  label: Meeting 4
  date: '2026-03-06'
  focus: Policy Constraints + Risk Register
  produces:
  - id: rec_outline_risk_register
    type: artifact
    label: Recommendations outline + first-pass risk register (top 10 risks + mitigations)
    status: not_started
  depends_on:
  - ms_policy_principles
  facilitator: John Black (Chair)
  inputs_expected:
  - ms_policy_principles
  - D-POL-1
  - D-CPX-1
  - D-AIN-1
  - D-DPS-1
  - D-EQA-1
  decision_gates:
  - Confirm recommendation domains and outline structure
  - Agree top 10 risks + mitigations and owners
- id: m5
  type: meeting
  label: Meeting 5
  date: '2026-03-20'
  focus: Draft Recommendations Workshop
  produces:
  - id: ms_draft_sections_complete
    type: milestone
    label: Draft Sections Complete
    status: not_started
  depends_on:
  - rec_outline_risk_register
  facilitator: John Black (Chair)
  inputs_expected:
  - rec_outline_risk_register
  decision_gates:
  - Make access/governance direction decision (if not already made)
  - Select which 2–3 domains are drafted first for integration
- id: m5_draft_sections
  type: artifact
  label: Draft sections for 2–3 domains; access/governance direction decision
  date: '2026-03-20'
  depends_on:
  - m5
  owner: WS-POL (David N. Berol / John Black) + domain leads
  status: not_started
- id: m6
  type: meeting
  label: Meeting 6
  date: '2026-04-10'
  focus: Package Integration + Headings Review
  produces:
  - id: near_final_package
    type: artifact
    label: Near-final written recommendations + 10–12 slide narrative outline + gap
      list (with owners)
    status: not_started
  - id: ms_board_ready
    type: milestone
    label: Board-Ready Package
    status: not_started
  depends_on:
  - ms_draft_sections_complete
  - m5_draft_sections
  facilitator: John Black (Chair)
  inputs_expected:
  - ms_draft_sections_complete
  - m5_draft_sections
  - D-CCI-1
  - D-IPC-1
  decision_gates:
  - Confirm near-final package structure and remaining gaps/owners
  - Confirm slide narrative storyline and review cadence
- id: m7
  type: meeting
  label: Meeting 7
  date: '2026-04-24'
  focus: Presentation + Feedback Assimilation
  produces:
  - id: final_talk_track
    type: artifact
    label: Final talk track + Q&A prep sheet (and/or draft memo)
    status: not_started
  depends_on:
  - ms_board_ready
  facilitator: John Black (Chair)
  inputs_expected:
  - ms_board_ready
  decision_gates:
  - Finalize talk track and Q&A; confirm any open issues to raise in committee response
- id: m8
  type: meeting
  label: Meeting 8
  date: '2026-05-15'
  focus: Response to Proposed Policy
  produces:
  - id: committee_response
    type: artifact
    label: Committee’s formal response to proposed policy + proposed guardrails/governance
    status: not_started
  - id: ms_final_recs
    type: milestone
    label: Final Recommendations Delivered
    status: not_started
  depends_on:
  - final_talk_track
  facilitator: John Black (Chair)
  inputs_expected:
  - final_talk_track
  decision_gates:
  - Approve committee formal response package (content + governance/guardrails)
- id: end
  type: end
  label: End
  date: '2026-05-15'
  depends_on:
  - ms_final_recs
- id: D-RSB-1
  type: artifact
  label: Shared Baseline Brief v1
  date: '2026-02-20'
  owner: Tom Colvin
  workstream: WS-RSB
  definition_of_done: '2–3 pages: capabilities/limits, common misconceptions, key
    terms, and classroom-reality examples + annotated resource list (top 10)'
  status: not_started
  depends_on: []
- id: D-POL-1
  type: artifact
  label: Policy Skeleton v0
  date: '2026-03-06'
  owner: David N. Berol
  workstream: WS-POL
  definition_of_done: Outline + section placeholders + decision-points list + versioning/decision
    log
  status: not_started
  depends_on: []
- id: D-CPX-1
  type: artifact
  label: Scenario Bank v1
  date: '2026-03-06'
  owner: Anubav Vasudevan
  workstream: WS-CPX
  definition_of_done: 10–15 grade-banded scenarios across subjects (AI-aware/AI-assisted/AI-resistant)
    + 3 exemplar teacher-facing guidance sheets
  status: not_started
  depends_on: []
- id: D-AIN-1
  type: artifact
  label: Attribution & Integrity Matrix v1
  date: '2026-03-06'
  owner: David N. Berol
  workstream: WS-AIN
  definition_of_done: Grade band × assessment type expectations + recommended safeguards
    (design patterns) + draft student-facing attribution rules
  status: not_started
  depends_on: []
- id: D-DPS-1
  type: artifact
  label: AI Tool Review Checklist v1 + Risk Tiers
  date: '2026-03-06'
  owner: Jillian Marie Burkley
  workstream: WS-DPS
  definition_of_done: Required questions (data minimization/retention/vendor terms),
    approval workflow sketch, and draft policy language for privacy/security guardrails
  status: not_started
  depends_on: []
- id: D-EQA-1
  type: artifact
  label: Equity Impact Checklist v1
  date: '2026-03-06'
  owner: Tom Sabo
  workstream: WS-EQA
  definition_of_done: Accessibility/accommodations considerations + do-no-harm risks
    + recommended supports and metrics to monitor equity outcomes
  status: not_started
  depends_on: []
- id: D-CCI-1
  type: artifact
  label: Comms Pack v1
  date: '2026-04-10'
  owner: Tina Beaty
  workstream: WS-CCI
  definition_of_done: Stakeholder map + key messages + FAQ draft (10–12 Qs) + proposed
    input plan (listening prompts/survey questions)
  status: not_started
  depends_on: []
- id: D-IPC-1
  type: artifact
  label: Implementation Roadmap v1
  date: '2026-04-10'
  owner: Jillian Marie Burkley
  workstream: WS-IPC
  definition_of_done: Phases/pilots/milestones + PD plan outline (modules + audiences)
    + recommended review cadence and success metrics
  status: not_started
  depends_on: []
```

---

## Notes for use

- Treat `id` as the stable key for cross-linking (workstreams registry, deliverables index, agendas, and minutes).
- Update `status` fields as drafts progress to keep the plan “live.”
- Populate `depends_on` as soon as dependencies are known (especially cross-workstream inputs).
