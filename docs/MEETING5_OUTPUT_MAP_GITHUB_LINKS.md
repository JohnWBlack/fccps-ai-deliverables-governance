# Meeting 5 Source -> Ingest Output Map (GitHub Links)

This map resolves the four Meeting 5 files that were reported as "missing".

## Why they were hard to find

- Ingest output filenames are normalized/sluggified and suffixed with a content hash.
- One source (`*.md`) is ingested directly into an artifact JSON and does not get a `docx -> markdown` conversion output.
- Exact source filenames (especially with spaces, punctuation, and long names) do not equal output filenames.

## Mapping

| Source (project_files) | Artifact JSON (GitHub) | Markdown output (GitHub) |
|---|---|---|
| `Meetings/05 - Meeting 20-MAR-26/20260320_FCCPS-AI-Advisory-Committee-Meeting-Minutes.md` | [public/project_ingest/artifacts/20260320_fccps_ai_advisory_committee_meeting_minutes__23729ca33c10.json](https://github.com/JohnWBlack/fccps-ai-deliverables-governance/blob/main/public/project_ingest/artifacts/20260320_fccps_ai_advisory_committee_meeting_minutes__23729ca33c10.json) | _(none; source is already markdown)_ |
| `Meetings/05 - Meeting 20-MAR-26/202602320_FCCPS_AI_Advisory_Committee_Mtg-5_Agenda+Minutes.docx` | [public/project_ingest/artifacts/202602320_fccps_ai_advisory_committee_mtg_5_agenda_minutes__e1f34420e78e.json](https://github.com/JohnWBlack/fccps-ai-deliverables-governance/blob/main/public/project_ingest/artifacts/202602320_fccps_ai_advisory_committee_mtg_5_agenda_minutes__e1f34420e78e.json) | [public/project_ingest/markdown/202602320_fccps_ai_advisory_committee_mtg_5_agenda_minutes__e1f34420e78e.md](https://github.com/JohnWBlack/fccps-ai-deliverables-governance/blob/main/public/project_ingest/markdown/202602320_fccps_ai_advisory_committee_mtg_5_agenda_minutes__e1f34420e78e.md) |
| `Meetings/05 - Meeting 20-MAR-26/FCCPS_AI_Advisory_Committee_Retrospective_First_Pass_Risk_Register.docx` | [public/project_ingest/artifacts/fccps_ai_advisory_committee_retrospective_first_pass_risk_re__f83df930f120.json](https://github.com/JohnWBlack/fccps-ai-deliverables-governance/blob/main/public/project_ingest/artifacts/fccps_ai_advisory_committee_retrospective_first_pass_risk_re__f83df930f120.json) | [public/project_ingest/markdown/fccps_ai_advisory_committee_retrospective_first_pass_risk_re__f83df930f120.md](https://github.com/JohnWBlack/fccps-ai-deliverables-governance/blob/main/public/project_ingest/markdown/fccps_ai_advisory_committee_retrospective_first_pass_risk_re__f83df930f120.md) |
| `Meetings/05 - Meeting 20-MAR-26/FCCPS AI Advisory Committee Meeting 5_otter_ai.docx` | [public/project_ingest/artifacts/fccps_ai_advisory_committee_meeting_5_otter_ai__20d8c867b36d.json](https://github.com/JohnWBlack/fccps-ai-deliverables-governance/blob/main/public/project_ingest/artifacts/fccps_ai_advisory_committee_meeting_5_otter_ai__20d8c867b36d.json) | [public/project_ingest/markdown/fccps_ai_advisory_committee_meeting_5_otter_ai__20d8c867b36d.md](https://github.com/JohnWBlack/fccps-ai-deliverables-governance/blob/main/public/project_ingest/markdown/fccps_ai_advisory_committee_meeting_5_otter_ai__20d8c867b36d.md) |

## Verification pointers

- Index entries confirming these source paths: `public/project_ingest/index.json`
- Ingest decisions confirming all four were ingested: `public/project_ingest/discovery_report.json`
