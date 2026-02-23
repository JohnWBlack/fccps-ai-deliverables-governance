# FCCPS AI Advisory Committee — Deliverables Index

**Version:** v1  
**Last updated:** 2026-02-07  
**Purpose:** One line per deliverable (committee-level + workstream) with owner, due checkpoint, dependencies, and where it lives.

## Deliverables table

| Due date | ID | Deliverable | Owner | Workstream | Checkpoint | Depends on | Status | File |
|---|---|---|---|---|---|---|---|---|
| 2026-01-23 | charter_v0 | Team Charter v0 (as agreed in meeting) | John Black (Chair) + committee | COMMITTEE | Meeting 1 |  | not_started | TBD |
| 2026-02-06 | working_agreements | Working agreements + draft timeline/objectives + collaboration rules + action items | John Black (Chair) | COMMITTEE | Meeting 2 | charter_v0 | not_started | TBD |
| 2026-02-20 | pre_m3_defs | One-page Definitions + Assumptions draft + priority misconceptions list + draft grade bands | Tom Colvin (WS-RSB) + John Black (integration) | COMMITTEE/WS-RSB | Pre-meeting input | working_agreements | not_started | TBD |
| 2026-02-20 | pre_m3_risks_ops | Members submit: top 3 risks + top 3 opportunities | All members (submission) + John Black (synthesis) | COMMITTEE | Pre-meeting input | working_agreements | not_started | TBD |
| 2026-02-20 | policy_principles | 8–12 Policy Principles (board-ready) + tradeoff statement | Committee (facilitated by John Black) | COMMITTEE | Meeting 3 | pre_m3_defs; pre_m3_risks_ops | not_started | TBD |
| 2026-02-20 | D-RSB-1 | Shared Baseline Brief v1 | Tom Colvin | WS-RSB | Meeting 3 (20 Feb) – inputs for Definitions/Assumptions + Misconceptions + Grade-band discussion |  | not_started | TBD |
| 2026-03-06 | rec_outline_risk_register | Recommendations outline + first-pass risk register (top 10 risks + mitigations) | WS-POL (David N. Berol / John Black) + domain leads | COMMITTEE/WS-POL | Meeting 4 | ms_policy_principles | not_started | TBD |
| 2026-03-06 | D-POL-1 | Policy Skeleton v0 | David N. Berol | WS-POL | Meeting 4 (6 Mar) – recommendations outline + constraints/risk register kickoff |  | not_started | TBD |
| 2026-03-06 | D-CPX-1 | Scenario Bank v1 | Anubav Vasudevan | WS-CPX | Meeting 4 (6 Mar) – inputs for constraints/risk register and recommendations outline |  | not_started | TBD |
| 2026-03-06 | D-AIN-1 | Attribution & Integrity Matrix v1 | David N. Berol | WS-AIN | Meeting 4 (6 Mar) – inputs for constraints/risk register and recommendations outline |  | not_started | TBD |
| 2026-03-06 | D-DPS-1 | AI Tool Review Checklist v1 + Risk Tiers | Jillian Marie Burkley | WS-DPS | Meeting 4 (6 Mar) – governance/procurement constraints and guardrails inputs |  | not_started | TBD |
| 2026-03-06 | D-EQA-1 | Equity Impact Checklist v1 | Tom Sabo | WS-EQA | Meeting 4 (6 Mar) – apply equity lens to constraints/risk register and draft outline |  | not_started | TBD |
| 2026-03-20 | m5_draft_sections | Draft sections for 2–3 domains; access/governance direction decision | WS-POL + domain leads | COMMITTEE/WS-POL | Meeting 5 (post-meeting artifact) | rec_outline_risk_register | not_started | TBD |
| 2026-04-10 | near_final_package | Near-final written recommendations + 10–12 slide narrative outline + gap list (with owners) | WS-POL + workstream leads (integration) | COMMITTEE/WS-POL | Meeting 6 | ms_draft_sections_complete; m5_draft_sections | not_started | TBD |
| 2026-04-10 | D-CCI-1 | Comms Pack v1 | Tina Beaty | WS-CCI | Meeting 6 (10 Apr) – near-final package integration and comms alignment |  | not_started | TBD |
| 2026-04-10 | D-IPC-1 | Implementation Roadmap v1 | Jillian Marie Burkley | WS-IPC | Meeting 6 (10 Apr) – near-final package integration and operationalization |  | not_started | TBD |
| 2026-04-24 | final_talk_track | Final talk track + Q&A prep sheet (and/or draft memo) | John Black (Chair) + WS-CCI | COMMITTEE/WS-CCI | Meeting 7 | ms_board_ready | not_started | TBD |
| 2026-05-15 | committee_response | Committee’s formal response to proposed policy + proposed guardrails/governance | Committee + WS-POL | COMMITTEE | Meeting 8 | final_talk_track | not_started | TBD |

---

## Machine-readable index (YAML)

```yaml
deliverables:
- id: charter_v0
  title: Team Charter v0 (as agreed in meeting)
  type: committee_artifact
  owner: John Black (Chair) + committee
  workstream: COMMITTEE
  due_date: '2026-01-23'
  checkpoint: Meeting 1
  depends_on: []
  status: not_started
  file: TBD
- id: working_agreements
  title: Working agreements + draft timeline/objectives + collaboration rules + action
    items
  type: committee_artifact
  owner: John Black (Chair)
  workstream: COMMITTEE
  due_date: '2026-02-06'
  checkpoint: Meeting 2
  depends_on:
  - charter_v0
  status: not_started
  file: TBD
- id: pre_m3_defs
  title: One-page Definitions + Assumptions draft + priority misconceptions list +
    draft grade bands
  type: committee_artifact
  owner: Tom Colvin (WS-RSB) + John Black (integration)
  workstream: COMMITTEE/WS-RSB
  due_date: '2026-02-20'
  checkpoint: Pre-meeting input
  depends_on:
  - working_agreements
  status: not_started
  file: TBD
- id: pre_m3_risks_ops
  title: 'Members submit: top 3 risks + top 3 opportunities'
  type: committee_artifact
  owner: All members (submission) + John Black (synthesis)
  workstream: COMMITTEE
  due_date: '2026-02-20'
  checkpoint: Pre-meeting input
  depends_on:
  - working_agreements
  status: not_started
  file: TBD
- id: policy_principles
  title: 8–12 Policy Principles (board-ready) + tradeoff statement
  type: committee_artifact
  owner: Committee (facilitated by John Black)
  workstream: COMMITTEE
  due_date: '2026-02-20'
  checkpoint: Meeting 3
  depends_on:
  - pre_m3_defs
  - pre_m3_risks_ops
  status: not_started
  file: TBD
- id: D-RSB-1
  title: Shared Baseline Brief v1
  type: workstream_deliverable
  owner: Tom Colvin
  workstream: WS-RSB
  due_date: '2026-02-20'
  checkpoint: Meeting 3 (20 Feb) – inputs for Definitions/Assumptions + Misconceptions
    + Grade-band discussion
  depends_on: []
  status: not_started
  file: TBD
- id: rec_outline_risk_register
  title: Recommendations outline + first-pass risk register (top 10 risks + mitigations)
  type: committee_artifact
  owner: WS-POL (David N. Berol / John Black) + domain leads
  workstream: COMMITTEE/WS-POL
  due_date: '2026-03-06'
  checkpoint: Meeting 4
  depends_on:
  - ms_policy_principles
  status: not_started
  file: TBD
- id: D-POL-1
  title: Policy Skeleton v0
  type: workstream_deliverable
  owner: David N. Berol
  workstream: WS-POL
  due_date: '2026-03-06'
  checkpoint: Meeting 4 (6 Mar) – recommendations outline + constraints/risk register
    kickoff
  depends_on: []
  status: not_started
  file: TBD
- id: D-CPX-1
  title: Scenario Bank v1
  type: workstream_deliverable
  owner: Anubav Vasudevan
  workstream: WS-CPX
  due_date: '2026-03-06'
  checkpoint: Meeting 4 (6 Mar) – inputs for constraints/risk register and recommendations
    outline
  depends_on: []
  status: not_started
  file: TBD
- id: D-AIN-1
  title: Attribution & Integrity Matrix v1
  type: workstream_deliverable
  owner: David N. Berol
  workstream: WS-AIN
  due_date: '2026-03-06'
  checkpoint: Meeting 4 (6 Mar) – inputs for constraints/risk register and recommendations
    outline
  depends_on: []
  status: not_started
  file: TBD
- id: D-DPS-1
  title: AI Tool Review Checklist v1 + Risk Tiers
  type: workstream_deliverable
  owner: Jillian Marie Burkley
  workstream: WS-DPS
  due_date: '2026-03-06'
  checkpoint: Meeting 4 (6 Mar) – governance/procurement constraints and guardrails
    inputs
  depends_on: []
  status: not_started
  file: TBD
- id: D-EQA-1
  title: Equity Impact Checklist v1
  type: workstream_deliverable
  owner: Tom Sabo
  workstream: WS-EQA
  due_date: '2026-03-06'
  checkpoint: Meeting 4 (6 Mar) – apply equity lens to constraints/risk register and
    draft outline
  depends_on: []
  status: not_started
  file: TBD
- id: m5_draft_sections
  title: Draft sections for 2–3 domains; access/governance direction decision
  type: committee_artifact
  owner: WS-POL + domain leads
  workstream: COMMITTEE/WS-POL
  due_date: '2026-03-20'
  checkpoint: Meeting 5 (post-meeting artifact)
  depends_on:
  - rec_outline_risk_register
  status: not_started
  file: TBD
- id: near_final_package
  title: Near-final written recommendations + 10–12 slide narrative outline + gap
    list (with owners)
  type: committee_artifact
  owner: WS-POL + workstream leads (integration)
  workstream: COMMITTEE/WS-POL
  due_date: '2026-04-10'
  checkpoint: Meeting 6
  depends_on:
  - ms_draft_sections_complete
  - m5_draft_sections
  status: not_started
  file: TBD
- id: D-CCI-1
  title: Comms Pack v1
  type: workstream_deliverable
  owner: Tina Beaty
  workstream: WS-CCI
  due_date: '2026-04-10'
  checkpoint: Meeting 6 (10 Apr) – near-final package integration and comms alignment
  depends_on: []
  status: not_started
  file: TBD
- id: D-IPC-1
  title: Implementation Roadmap v1
  type: workstream_deliverable
  owner: Jillian Marie Burkley
  workstream: WS-IPC
  due_date: '2026-04-10'
  checkpoint: Meeting 6 (10 Apr) – near-final package integration and operationalization
  depends_on: []
  status: not_started
  file: TBD
- id: final_talk_track
  title: Final talk track + Q&A prep sheet (and/or draft memo)
  type: committee_artifact
  owner: John Black (Chair) + WS-CCI
  workstream: COMMITTEE/WS-CCI
  due_date: '2026-04-24'
  checkpoint: Meeting 7
  depends_on:
  - ms_board_ready
  status: not_started
  file: TBD
- id: committee_response
  title: Committee’s formal response to proposed policy + proposed guardrails/governance
  type: committee_artifact
  owner: Committee + WS-POL
  workstream: COMMITTEE
  due_date: '2026-05-15'
  checkpoint: Meeting 8
  depends_on:
  - final_talk_track
  status: not_started
  file: TBD
```