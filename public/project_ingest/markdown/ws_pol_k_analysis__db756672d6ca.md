<!-- provenance:{"extractor_version":"2.0.0","pipeline_version":"2.0.0","project":"FCCPS AI Committee"} -->

# WS POL K Analysis

WS-POL-K – Protection of Student Privacy, Data Governance, and Vendor/Procurement Governance Analysis

The clearest overall conclusion is that WS-POL-K is one of the committee’s most structurally developed sections. Compared with several other topics, the committee record shows relatively strong convergence around tiered review, data minimization, approved-tool governance, and stronger controls for identifiable student data and consequential uses. The biggest disagreements are less about whether governance is needed and more about how broad the scope should be, how burdensome notice/consent should become, whether BYO or low-risk local flexibility should exist, and who should own monitoring and enforcement.

# How the committee got here

The privacy/governance issue appears in the record before the policy shell was fully stabilized. In Meeting 3, Thomas Colvin described classroom examples intended to show both benefits and tensions, including a teacher using AI for grading materials: it might save time, but it immediately raises the question of whether parents gave permission for student information to be uploaded to an outside system. That is an early sign that the committee did not see privacy as an abstract compliance afterthought. It saw privacy, vendor relationships, and parent trust as practical barriers to ordinary classroom adoption from the beginning. (Meeting 3 transcript)

That concern was then formalized in the policy shell. In the V3 outline, WS-POL-K covers student privacy and data protection, data minimization, retention and deletion, vendor DPA requirements, notice and consent, limits on use beyond routine educational purposes, and vendor/procurement governance including tiered approval, renewal/monitoring/discontinuation, and vendor accountability. This is not a narrow “privacy paragraph.” It is a whole governance stack.

Meeting 4 materials sharpened the same point. The uploaded decision packet places D3 — Risk Rubric in the Green Zone and says risk level, not only “high-stakes,” should drive limits and disclosure. It also places R4 — Notice / Consent / Opt-Out in the Red Zone, explicitly framing consent posture for AI uses involving student data as an unresolved motion. That means the committee had already converged on the need for a governance framework, but not on how far notice and opt-out rights should go. Meeting 4 decision packet

# What the workstream products say

The strongest single source for WS-POL-K is Jillian Burkley’s WS-DPS draft. It proposes a three-tier risk framework for every AI tool used in FCCPS classrooms or operations, with each tier triggering a different level of review and approval. It also adds escalation rules that automatically push tools into higher scrutiny when they require identity linkage, connect to SSO/SIS/LMS, touch student artifacts, or are used for consequential decisions such as placement, grading, intervention, discipline, or SPED decisions. That is a strong sign that the governance workstream did not trust superficial vendor claims or broad classroom discretion in these contexts. WS-DPS draft

The draft’s table language makes the committee’s emerging governance logic very concrete:

Tier 1 is for tools with no student data and basic department/building-level approval.

Tier 2 requires written de-identification assurances, a signed DPA, retention/deletion terms, annual vendor review, and FERPA verification.

Tier 3 covers identifiable student data, integrated systems, and sensitive records, and requires full DPA, security assessment, human-in-the-loop protection for consequential decisions, deletion confirmation, and semiannual compliance review. WS-DPS draft

That same draft also shows where real committee tensions still existed. Its explicit tradeoffs are:

approval speed vs. thoroughness,

approved list vs. criteria-based evaluation,

who owns compliance monitoring,

district-provided tools vs. BYO tools,

and data minimization vs. personalization.

Those are probably the clearest documentary statement of the fault lines inside WS-POL-K. WS-DPS draft

The Equity & Access deliverable reinforces that the committee’s privacy/governance thinking is not only legalistic. D-EQA-1 says equity and accessibility must be considered from procurement to classroom practice, includes a rapid triage for privacy/data/records, asks whether data practices disproportionately harm vulnerable groups, and adds vendor questions about training data, multilingual functionality, and bias testing. That is important because it means WS-POL-K was not being framed only as “keep data safe.” It was also being framed as prevent inequitable or biased procurement and deployment from the start. (D-EQA-1)

The Meeting 4 readiness snapshot further shows that D-DPS-1 was one of the most connected workstreams in the whole process. It links D-DPS-1 to principle and risk dependencies and shows it feeding the policy outline and implementation logic more strongly than several other sections. That suggests WS-POL-K is not peripheral. It is one of the sections around which the committee’s broader governance architecture is being built. (Meeting 4 readiness)

# Where agreement appears strongest

The strongest agreement appears in five areas.

The first is tiered governance. The record strongly supports the idea that not all AI tools should be treated alike and that review should track data sensitivity and consequence. The Meeting 4 packet’s risk-rubric default and the D-DPS tier framework are mutually reinforcing here. Meeting 4 decision packet WS-DPS draft

The second is data minimization and approved-tool governance. The V3 outline explicitly calls for limits on use of student data beyond routine educational purposes, and the D-DPS framework repeatedly defaults toward minimization, DPA review, documented retention/deletion terms, and contractual limits on model training and advertising uses. WS-DPS draft

The third is special treatment for consequential and identity-linked uses. The D-DPS escalation rules make this non-negotiable: SSO/SIS/LMS integration, identifiable student data, and consequential student decisions all force higher review. That is one of the clearest and least controversial features of the accessible record. WS-DPS draft

The fourth is stronger safeguards for disability-related and sensitive records. Even though that topic also belongs in WS-POL-J, it materially shapes WS-POL-K because the D-DPS and D-EQA workstreams both treat IEP/504, behavioral, and assistive-technology contexts as especially sensitive data-governance cases. WS-DPS draft (D-EQA-1)

The fifth is public trust as a governance issue, not just a communications issue. Survey responses repeatedly connect vendor/data practices, notice, and approved tools to community trust and feasibility, which shows that members were not treating privacy governance as something invisible to families. (Survey export)

# Main fault lines and the range of opinions

## 1. Broad AI-governance scope vs. tighter GenAI-centered scope

One clear divide is whether WS-POL-K should try to govern all AI-enabled tools touching student data or focus more tightly on the GenAI systems the public is most concerned about.

The governance workstream clearly favors the broad view. Jillian’s draft says every AI tool used in FCCPS classrooms or operations should be classified into a review tier. That includes classroom, operational, identity-linked, and sensitive-record systems. WS-DPS draft

A narrower view is visible in the survey. One anonymous respondent argued that it would be impracticable to require a public registry of every AI tool on campus, asked whether FCCPS really needed to track every classroom where Grammarly or AI reading-level adjustment is used, and said bluntly, “The core issue is GEN AI.” The same respondent warned that broad notice/opt-out expectations would become an implementation nightmare without “a much tighter focus.” (Survey export)

So the disagreement is not whether privacy matters. It is whether the policy should create a district-wide AI governance framework or a more targeted GenAI governance regime.

## 2. Notice and consent: baseline transparency vs. operational feasibility

This is probably the sharpest unresolved policy question in WS-POL-K.

The Meeting 4 packet elevates R4 — Notice / Consent / Opt-Out to a Red Zone motion, which is the strongest evidence that the committee had not resolved it. Meeting 4 decision packet

The survey shows the split clearly. Some respondents supported a middle position: advance notice for all, consent/opt-out where feasible, and default to approved tools and data minimization. Others thought this was too burdensome. One respondent said even merely providing notice of all AI in the school would be a logistical nightmare and that opt-out structures could force unmanageable implementation choices. Another worried that broad opt-out could effectively require parallel curricula. A more privacy-protective respondent removed “where feasible” from notice-plus-consent language and argued that unless AI is actually mandatory, it should always be possible to opt out. (Survey export)

This produces three real positions:

strong consent/opt-out rights,

advance notice plus limited consent where feasible,

and skepticism that broad notice/opt-out can be implemented meaningfully at all.

## 3. Approved-list governance vs. criteria-based review

This is one of the most concrete operational tensions in the D-DPS draft. The tradeoff table explicitly asks whether FCCPS should rely on an approved list or on criteria-based evaluation. WS-DPS draft

An approved-list model gives clearer control and community assurance, but may be slower and more rigid. A criteria-based model is more flexible, but places more interpretive burden on staff and administrators. Survey responses that asked for “clear and accessible standards” and “approved AI uses and data practices” lean toward the list/clearance side, while others who worried about over-bureaucratization or evolving technology point toward criteria-based review.

## 4. District-approved tools only vs. limited BYO / low-risk flexibility

The D-DPS draft is explicit that this is a real tradeoff. One option is district-approved tools only. Another is some BYO flexibility for Tier 1 or teacher-mediated contexts. That tracks a larger committee tension: innovation and teacher agility versus centralized governance and compliance control. WS-DPS draft

The accessible record suggests the committee is unlikely to support unrestricted BYO for student-facing or data-touching tools. But it does suggest some members may want room for low-risk experimentation that does not process student data.

## 5. Data minimization vs. personalization

This is a deeper philosophical disagreement than it first appears.

The D-DPS draft frames it explicitly: should FCCPS default to minimization and limit personalization features, allow Tier 3 personalization only with strong rationale and monitoring, or decide case-by-case under strict data-element limits and sunset review? WS-DPS draft

This matters because some educationally attractive AI uses depend on student-specific data. So WS-POL-K is not only about blocking risk. It is about deciding when added personalization value is worth added data exposure.

## 6. Monitoring ownership

The D-DPS tradeoff table also surfaces a governance question that can easily become political: should IT own monitoring, should Curriculum & Instruction own it, or should responsibility be shared under a defined cadence and RACI structure? WS-DPS draft

This is a good example of a place where the committee may agree on goals but not on institutional home. That matters for your drafting because a policy can name the need for accountable ownership without locking the district into a specific org chart.

# Likely position map from the accessible record

Jillian Burkley / governance-heavy posture. Jillian’s work clearly favors a broad, formal, tiered governance framework with DPA review, retention/deletion rules, escalation for identity-linked or consequential uses, explicit vendor restrictions, and routine compliance review. This is the most developed and operationally mature position in the record. WS-DPS draft

Tom Sabo / Elizabeth Chua / equity-from-procurement-through-practice posture. The EQA workstream argues that equity and accessibility must be considered from procurement to classroom practice, with vendor review, bias testing, multilingual functionality, and monitoring loops. This aligns strongly with a privacy/governance framework that is broader than simple consent language. (D-EQA-1)

Narrow-scope / implementation-skeptical posture. This position is clearest in anonymous survey feedback. It favors tighter focus on GenAI, distrusts expansive notice/opt-out and public-registry concepts, and worries about overpromising operational capacity.

Balanced transparency-and-minimization posture. This camp supports advance notice, approved tools, data minimization, and consent where feasible, but does not want those commitments to explode into unworkable classroom complexity. Several survey respondents align with this middle ground.

# What this means for your drafting

For WS-POL-K, the strongest committee-grounded common ground is:

FCCPS should use a tiered governance approach for AI tools that touch student data or influence student outcomes. Tools involving identifiable student data, identity-linked systems, sensitive records, or consequential student decisions should receive stronger review. Data minimization, retention/deletion expectations, DPA and vendor-term review, and ongoing monitoring should be core features of the framework. Privacy and governance should be designed alongside equity and accessibility, not added after procurement. WS-DPS draft (D-EQA-1)

Where you will need to choose your own position is on four narrower questions:

whether WS-POL-K should govern AI-enabled tools broadly or focus more tightly on GenAI and the most visible student-data risks,

how strong the district’s notice/consent/opt-out commitments should be,

whether to lean toward an approved-list model or a criteria-based model,

and how much low-risk flexibility, if any, to leave for BYO or teacher-mediated experimentation.
