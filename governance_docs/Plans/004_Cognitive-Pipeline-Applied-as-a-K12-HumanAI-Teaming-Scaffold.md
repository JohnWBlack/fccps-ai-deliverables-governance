Cognitive pipeline applied as a K12 human–AI teaming scaffold

| Stage                                  | Human role                                           | AI role                                                    | Example tasks                                        | Safeguards & metrics                                                           |
|----------------------------------------|------------------------------------------------------|------------------------------------------------------------|------------------------------------------------------|--------------------------------------------------------------------------------|
| Curiosity / Motivation                 | Set learning goals; model inquiry                    | Propose project prompts; surface novel resources           | Generate project ideas; suggest inquiry questions    | Teacher vetting of prompts; **metric:** student engagement rate                |
| Perception & Attention                 | Validate inputs; spot edge cases                     | Preprocess student work; highlight salient features        | Autotag submissions; flag attention issues           | Human review of flagged items; **metric:** precision of flags                  |
| Memory Activation                      | Provide prior lessons and norms                      | Retrieve relevant curriculum and past work                 | Fetch exemplar student work; surface prior feedback  | Privacy controls; teacher approval; **metric:** retrieval relevance            |
| Comprehension                          | Interpret ambiguous responses; contextualize         | Produce summaries; scaffold explanations                   | Summarize misconceptions; create step scaffolds      | Teacher checks for misinterpretation; **metric:** teacher agreement            |
| Basic Reasoning                        | Define constraints and acceptable methods            | Execute stepwise inferences; generate worked examples      | Show solution steps; propose next steps              | Rule checks; teacher spot checks; **metric:** correctness of steps             |
| Critical Thinking                      | Lead evaluation, ethical judgment, source critique   | Run verification checks; surface counterexamples           | Present alternative explanations; flag weak evidence | Human adjudication for highstakes; **metric:** reduction in unsupported claims |
| SelfReflection                         | Model reflective practice; debrief students          | Generate reflection prompts; summarize progress trends     | Produce metacognitive questions; progress summaries  | Teacher curates prompts; **metric:** quality of student reflections            |
| Metacognition                          | Teach strategies; set thresholds                     | Monitor confidence; suggest strategy shifts                | Recommend study plans; adapt difficulty              | Calibrate AI confidence; teacher override; **metric:** calibration accuracy    |
| Cognitive Control / Executive Function | Make final pedagogical decisions; policy enforcement | Orchestrate workflows; schedule tasks; enforce constraints | Automate reminders; manage multistep projects        | Human final approval; audit logs; **metric:** adherence to policy and outcomes |

# How to use the scaffold in classrooms (operational steps)

-   **Map objectives to stages** for each lesson and assign human/AI responsibility.
-   **Define interfaces**: inputs, outputs, confidence thresholds, and fallbacks at each stage.
-   **Instrument handoffs**: log AI outputs, confidence, and human overrides for audit and improvement.
-   **Stagespecific evaluation**: retrieval relevance, calibration error, teacher agreement, student learning gains.
-   **Human checkpoints**: require teacher review for highrisk stages (Critical Thinking, Cognitive Control).

# High Quality Template HQT for K12 AI Use Policy

Balances the competing values framework domains **Create, Compete, Control, Collaborate**.

| Domain      | Policy principle                                       | Practical rules                                                                                                                                           | HQT checklist                                                          |
|-------------|--------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| Create      | Enable student creativity while protecting originality | AI may generate prompts, drafts, and multimedia; students must disclose AI assistance on submitted work; teachers scaffold originality                    | **Student disclosure**; **Teacher review of generative outputs**       |
| Compete     | Preserve valid assessment of student competence        | AI supports practice and formative feedback; summative assessments require humanverified conditions; AI suggestions labeled with confidence and rationale | **Formative use allowed**; **Summative humanverified**                 |
| Control     | Maintain human authority, safety, and privacy          | Teachers retain final decisions; humanintheloop for interventions; strict data minimization, consent, and access controls                                 | **Human final approval**; **Parental consent & data minimization**     |
| Collaborate | Foster productive human–AI and peer collaboration      | AI facilitates group roles and scaffolds; AI mediates but does not replace peer feedback; teacher visibility into collaboration logs                      | **Teacher visibility of logs**; **AI as facilitator, not replacement** |

# Policy implementation checklist (ready to adopt)

-   **Onboarding:** Train teachers on pipeline roles, AI capabilities, and override procedures.
-   **Transparency:** Require AI to surface a brief rationale and confidence score with suggestions.
-   **Privacy:** Parental consent for data use; anonymize data used for model improvement; limit retention.
-   **Assessment integrity:** Use AI for practice and formative feedback; require human verification for summative grading.
-   **Equity audits:** Regular bias audits across demographics and remediation plans.
-   **Auditability:** Maintain logs of AI outputs, confidence, and human overrides for review.
-   **Continuous review:** Schedule periodic policy reviews and stagespecific KPI evaluations.

# Example compact policy clause for school adoption

*“AI tools may be used to generate instructional materials, formative feedback, and student scaffolds when a teacher has reviewed and approved outputs. Students must disclose AI assistance on submitted work. All AI outputs must include a brief rationale and confidence score. Teachers retain final authority for grading, interventions, and highstakes decisions. Student data used for model improvement must be anonymized and require parental consent; retention is limited to the minimum necessary.”*

# Quick operational templates to deploy immediately

-   **Lesson mapping template:** list lesson objective → required pipeline stages → assigned human/AI role → checkpoint(s).
-   **Teacher review checklist:** AI output; confidence score; suggested edits; approve/reject; rationale logged.
-   **Student disclosure badge:** short form students attach to submissions indicating AI assistance type and extent.
