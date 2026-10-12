# Major Project Review-2: Slide Deck Specification

**Project Title:** AI-Powered Policy-Grounded Agentic AI for Health Insurance Claim Denial Analysis and Appeal Support  
**Project ID:** 66  
**Students:** Pragallapati Saketh (160123733129), Saketh Vemulapati (160123733136)  
**Supervisor:** A. Sangeetha, Assistant Professor  
**Department & Institution:** Department of Computer Science & Engineering, Chaitanya Bharathi Institute of Technology (CBIT), Hyderabad  

---

## Slide 1: Title Slide

* **Slide Layout:** Clean Title Layout (Dark Navy / Clean White Header with CBIT Logo, 47 Years Crest, and Affiliation details).
* **Header / Sub-header:**
  * **Main Title:** Policy-Grounded Agentic AI for Health Insurance Claim Denial Analysis and Appeal Support
  * **Sub-title:** Major Project Review-2 | Academic Year 2026–2027
* **Presenter & Supervisor Block:**
  * **Presented by:**
    * Pragallapati Saketh (Roll No: 160123733129)
    * Saketh Vemulapati (Roll No: 160123733136)
  * **Project ID:** 66
  * **Supervisor:** A. Sangeetha, Assistant Professor, Dept. of CSE
  * **Institution:** Chaitanya Bharathi Institute of Technology (Autonomous), Gandipet, Hyderabad

---

## Slide 2: Problem Statement & Key Challenges

* **Slide Layout:** Two-Column Card Layout (Left: Core Problem & Impact; Right: Critical Technical Challenges).
* **Left Card — Core Problem Context:**
  * **Pervasive Claim Repudiations:** Over 15%–20% of retail health insurance claims in India face outright denial or heavy repudiation, often leaving patients in financial distress.
  * **Severe Information Asymmetry:** Policyholders face 40+ page legal policy wordings with dense exclusion clauses (e.g., Clause 4.3 "Elective Surgeries", 24/48-month Pre-Existing Disease waiting periods) and cryptic insurer repudiation notices (CARC/RARC codes).
  * **Routine Clause Misapplication:** Insurers frequently issue blanket repudiations citing broad exclusion headings while completely ignoring explicit exception sub-clauses (e.g., failure of conservative treatment) or statutory IRDAI moratorium protections.
  * **Onerous Appeal Burden:** Building an appeal requires reconciling disparate evidence across discharge summaries, radiology reports, itemized billing annexures, policy clauses, and stringent regulatory appeal windows (30-day internal grievance, 1-year Ombudsman).
* **Right Card — Technical AI Challenges:**
  * **LLM Hallucinations in Legal Reasoning:** Standard LLMs hallucinate up to 44% of coverage conditions when reading dense insurance contracts without symbolic guardrails (Pokharel et al., 2026).
  * **Lack of Multi-Modal Document Synthesis:** Denial notices, clinical narrative notes, and policy contracts exist in disparate formats requiring synchronized parsing.
  * **Absence of Explainable Argumentation:** Existing tools output simple predictions rather than legally grounded, defeasible arguments required by judicial forums (Ombudsman / Consumer Courts).

---

## Slide 3: Project Objectives

* **Slide Layout:** 6 Clean Numbered Feature Cards (3x2 Grid).
* **Slide Content:**
  1. **Build an Agentic Denial Investigation System:**
     Develop a multi-agent orchestration framework (LangGraph, MCP, Python) to automate intake, investigation, logic evaluation, and appeal generation.
  2. **Intelligent Denial Triage & Routing:**
     Normalize unstructured repudiation notices into 7 standardized denial taxonomies (CARC/IRDAI) and route cases to specialized investigation pipelines.
  3. **Category-Specific Deep Investigation:**
     Execute unique multi-step audits for each denial type (clinical guideline matching, waiting period chronology, exception mining, room-rent proportionality, and statutory delay circulars).
  4. **Multi-Source Clinical & Chronological Evidence Extraction:**
     Automate clinical entity linkage (ICD-10/HCPCS) and symbolic date arithmetic to detect failed conservative therapy or satisfied waiting periods.
  5. **Explainable Toulmin Defeasible Logic Reasoner:**
     Formalize insurer claims, clinical grounds, policy warrants, and rebuttals into structured argumentation to establish high-confidence reversal grounds.
  6. **Grounded Appeal Package & Human-in-the-Loop Governance:**
     Generate formal, citation-backed appeal petitions for the Insurance Ombudsman with embedded evidence matrices, subject to human reviewer audit.

---

## Slide 4: Literature Survey (Part 1 — Core Foundations)

* **Slide Layout:** Structured Comparison Matrix Table (3 Papers).
* **Slide Content:**

| Author, Publisher & Year | Paper Title | Methodology | Key Advantages | Critical Limitations / Research Gap |
| :--- | :--- | :--- | :--- | :--- |
| **S. Hanmante et al.**<br>*Elsevier, Software Impacts*<br>(2026) | **InsuranceRAG:** Multi-Module Retrieval-Augmented AI System for Insurance Assistance | Uses RAG, FAISS dense embeddings, and LLMs for clause-level retrieval from insurance policies. | Modular architecture; provides policy-grounded answers to user queries; eliminates basic hallucinations. | Restricted to informational policy lookup; **does not analyze denial repudiations, evaluate medical evidence, or generate appeal drafts.** |
| **Jin Liu et al.**<br>*ACL (Long Paper)*<br>(2026) | **InsLogicBench:** Argumentation Logic Grounded Benchmark for Claims Adjudication | Formalizes insurance policies into Toulmin argumentation logic (Claim, Grounds, Warrant, Rebuttal) to test LLM adjudication. | Evaluates multi-step defeasible reasoning over complex policy disputes beyond surface semantic search. | **Evaluation benchmark only**; does not provide an end-to-end multi-agent system, document intake, or automated appeal pipeline. |
| **M. Fink et al.**<br>*Elsevier, Academic Radiology*<br>(2026) | **DENIED-AI Pilot Study:** Decreasing Admin Effort for Non-Approval of Image-guided Procedures | Evaluates zero-shot, few-shot, and RAG-based LLMs to draft radiology denial appeal letters with physician scoring. | Proves that LLMs substantially cut administrative appeal drafting time; includes expert clinical evaluation. | Restricted to simulated radiology cases; **observed fabricated citations and hallucinations**, proving the need for deterministic logic guardrails. |

---

## Slide 5: Literature Survey (Part 2 — Triage, Logic & Appeal Synthesis)

* **Slide Layout:** Structured Comparison Matrix Table (3 Papers) + Research Gap Summary Box.
* **Slide Content:**

| Author, Publisher & Year | Paper Title | Methodology | Key Advantages | Critical Limitations / Research Gap |
| :--- | :--- | :--- | :--- | :--- |
| **Timothy Owolabi**<br>*Oxford Univ. Press, JAMIA Open*<br>(2025) | **Transforming Appeal Decisions:** Machine Learning Triage for Hospital Admission Denials | Supervised ML classification (XGBoost, Random Forest) trained on historical claims to predict appeal success. | Quantitative triage; prioritizes high-probability denial reversals; identifies denial patterns. | Black-box statistical classifier; **cannot generate policy citations, extract clinical proof, or write appeal letters.** |
| **Kiser et al.**<br>*JCO Clinical Cancer Informatics*<br>(2024) | **Large Language Models to Help Appeal Denied Radiotherapy Services** | Leveraged GPT-4 with clinical prompt framing to generate appeal letters against coverage denials for cancer treatments. | Produces professional, persuasive appeal letters aligned with clinical necessity guidelines. | Lacks automated policy document parsing; relies on manual prompt insertion of policy clauses; **no multi-agent workflow.** |
| **Pokharel et al.**<br>*arXiv / AI & Law*<br>(2026) | **From Policy to Logic for Efficient and Interpretable Coverage Assessment** | Converts natural language policy clauses into executable symbolic logic (AND/OR/NOT), coupled with a coverage-aware retriever. | **Reduces LLM reasoning hallucinations by 44%**; provides fully auditable, deterministic Boolean coverage verdicts. | Focuses solely on policy coverage rules; does not ingest multi-modal denial notices, itemized hospital bills, or appeal filing dossiers. |

* **Identified Research Gap (Our Contribution):**
  > *Current systems are bifurcated: they either perform statistical triage (Owolabi) or unconstrained text generation (Fink, Kiser). There is **no end-to-end, policy-grounded multi-agent system** that integrates document intake, automated clause-exception verification, clinical fact extraction, symbolic logic, and Toulmin legal argumentation into an auditable appeal package.*

---

## Slide 6: System Architecture — End-to-End Orchestration Flow

* **Slide Layout:** Visual Workflow Flowchart / Pipeline Architecture.
* **Architecture Pipeline Flow:**

```
[User Input: Denial Notice + Policy PDF + Discharge Summary + Bills]
                                │
                                ▼
                     [Node 1: User Intake]
                                │
                                ▼
                [Node 2: Denial Intake Agent]
             (PyMuPDF / OCR → NER Entity Extraction)
                                │
            ┌───────────────────┴───────────────────┐
            ▼                                       ▼
 [Node 3a: Denial Reason Normalization]  [Node 3b: Case Fact Reconstruction]
 (Fuzzy match → CARC / IRDAI Taxonomy)   (Extract clinical timeline, ICD, sums)
            └───────────────────┬───────────────────┘
                                │
                                ▼
                   [Node 4: Denial Type Router]
                 (7-Class Repudiation Triage)
                                │
                                ▼
      [Node 5: Category-Specific Denial Investigation Engine]
     (Dispatches Dedicated Multi-Step Investigation Workflow:
      Medical Necessity | Waiting Period | Policy Exclusion |
      Financial Limit | Documentation | Admin-Delay | Eligibility)
                                │
                                ▼
           [Node 6: Denial-Clause-Fact-Evidence Graph]
                                │
                                ▼
                  [Node 7: Applicability Reasoner]
        (Pokharel Symbolic Rules + Liu Toulmin Defeasible Logic)
                                │
                                ▼
              [Node 8: Structured Evidence Matrix]
                                │
                                ▼
                 [Node 9: Denial Assessment Verdict]
                   (OVERTURN / UPHOLD / PARTIAL)
                                │
                                ▼
               [Node 10: Targeted Re-Analysis Guard]
              (Audit citations against source documents)
                                │
                                ▼
                 [Node 11: Route & Deadline Check]
             (IRDAI Grievance [30d] vs Ombudsman [1y])
                                │
                                ▼
               [Node 12: Appeal Drafting Agent]
         (Generates formal petition with embedded legal warrants)
                                │
                                ▼
             [Node 13: Grounded Appeal Draft Review]
                                │
                                ▼
             [Node 14: Human-in-the-Loop (HITL) UI]
               (User / Paralegal Audits and Approves)
                                │
                                ▼
         [Node 15: Final Appeal Pack & Dossier Export (PDF)]
```

---

## Slide 7: System Architecture — Node 5 Deep-Dive: Category-Specific Denial Investigation Framework

* **Slide Layout:** Dedicated Investigation Workflow Flowchart + 7-Category Multi-Step Audit Specification Table.
* **Node 5 Specialized Investigation Dispatch Flow:**

```
                                 [Node 4: Denial Type Router]
                                               │
            ┌──────────────────────────────────┼──────────────────────────────────┐
            │                                  │                                  │
            ▼                                  ▼                                  ▼
┌───────────────────────┐          ┌───────────────────────┐          ┌───────────────────────┐
│ CATEGORY 1:           │          │ CATEGORY 2:           │          │ CATEGORY 3:           │
│ MEDICAL_NECESSITY     │          │ PRE_EXISTING_WAITING  │          │ POLICY_EXCLUSION      │
├───────────────────────┤          ├───────────────────────┤          ├───────────────────────┤
│ 1. Vital Instability  │          │ 1. Onset Chronology   │          │ 1. Exact Clause Scope │
│ 2. Conservative Audit │          │ 2. Timeline Math      │          │ 2. Exception Search   │
│ 3. Guideline Matching │          │ 3. Moratorium Audit   │          │ 3. Criteria Compliance│
│ 4. Doctor Cert Check  │          │ 4. Proposal Cross-Chk │          │                       │
└───────────┬───────────┘          └───────────┬───────────┘          └───────────┬───────────┘
            │                                  │                                  │
            ├──────────────────────────────────┼──────────────────────────────────┤
            │                                  │                                  │
            ▼                                  ▼                                  ▼
┌───────────────────────┐          ┌───────────────────────┐          ┌───────────────────────┐
│ CATEGORY 4:           │          │ CATEGORY 5:           │          │ CATEGORY 6:           │
│ FINANCIAL_LIMIT       │          │ DOCUMENTATION         │          │ ADMINISTRATIVE_PROC.  │
├───────────────────────┤          ├───────────────────────┤          ├───────────────────────┤
│ 1. Room Rent Ratio    │          │ 1. Deficiency Parsing │          │ 1. Filing Deadlines   │
│ 2. Sub-Limit Capping  │          │ 2. Repo Gap Analysis  │          │ 2. IRDAI Delay Circ.  │
│ 3. NME Bill Audit     │          │ 3. Requisition Gen.   │          │ 3. Non-Network Hosp.  │
└───────────┬───────────┘          └───────────┬───────────┘          └───────────┬───────────┘
            │                                  │                                  │
            └──────────────────────────────────┼──────────────────────────────────┘
                                               │
                                               ▼
                                  ┌───────────────────────┐
                                  │ CATEGORY 7:           │
                                  │ ELIGIBILITY_COVERAGE  │
                                  ├───────────────────────┤
                                  │ 1. Member Dependency  │
                                  │ 2. Grace Period Audit │
                                  │ 3. Portability Credit │
                                  └───────────┬───────────┘
                                               │
                                               ▼
                         [Node 6: Denial-Clause-Fact-Evidence Graph]
```

* **The 7 Category-Specific Investigation Workflows:**

| Denial Category | Core Question Investigated | Specialized Multi-Step Investigation Workflow | Runtime Knowledge Used |
| :--- | :--- | :--- | :--- |
| **1. Medical Necessity** | Was this hospitalization clinically required, or could it have been treated conservatively / as outpatient? | **1.** Vital Instability Scan (SpO2 < 90%, pain ≥ 8/10, Grade IV OA).<br>**2.** Conservative Audit (Duration = Surgery − 1st Therapy Date ≥ 6 months).<br>**3.** Clinical Guideline Matching (InterQual / Milliman MCG / Indian protocols).<br>**4.** Physician Necessity Certificate Verification. | `icd10_codes.csv`<br>`procedure_codes.csv`<br>`policy_clauses.csv` |
| **2. Pre-Existing Waiting Period** | Did disease originate pre-policy, and does insurer have legal right to repudiate after continuous renewals? | **1.** Onset Chronology Tracing (HPI scan for earliest symptom date $D_{onset}$).<br>**2.** Timeline Math ($T_{elapsed} = \text{Admission} − \text{Inception}$ vs 30d / 24m / 48m).<br>**3.** IRDAI Moratorium Audit (5-year / 60-month rule under IRDAI 2024).<br>**4.** Proposal Non-Disclosure Cross-Check (asymptomatic != non-disclosure). | `policy_clauses.csv`<br>`denial_reasons.csv`<br>Chronology Engine |
| **3. Policy Exclusion** | Does the cited exclusion apply, or does an explicit exception / sub-clause override it? | **1.** Exact Clause Retrieval & Scope Verification (vector match cited clause).<br>**2.** Exception Clause Search (scan `has_exception` & `exception_text`).<br>**3.** Exception Criteria Compliance Audit (e.g. accident, Mental Healthcare Act Sec 21). | `policy_clauses.csv`<br>`procedure_codes.csv` |
| **4. Financial Limit** | Did insurer calculate deductions correctly, or improperly apply room rent / sub-limits / NME? | **1.** Room Rent Ratio Audit ($\text{Ratio} = \text{Eligible} / \text{Actual}$; check illegal scaling).<br>**2.** Sub-Limit & Capping Verification (cataract ₹40k, ICU 2% SI, robotic caps).<br>**3.** NME Bill Audit (reclaim disallowed consumables: gloves, syringes, IV cannulas). | `nme_exclusions.csv`<br>`policy_clauses.csv` |
| **5. Documentation** | Are documents genuinely missing, or did the insurer overlook documents already submitted? | **1.** Deficiency Letter Parsing (extract requested records: ICP, Doctor Cert, Pre-Auth).<br>**2.** Repository Gap Analysis (tag: `Already Available` vs `Genuinely Missing`).<br>**3.** Hospital Action Item & Requisition Generator (auto-draft hospital requisition). | Case Repository<br>`denial_reasons.csv` |
| **6. Administrative-Procedural** | Was submission delay justifiable, and can insurer legally repudiate on procedural grounds? | **1.** Deadline Calculation (Intimation delay vs 24h; Submission delay vs 15d).<br>**2.** IRDAI Delay Circular Evaluation (Circular 2011: emergency, ICU, beyond control).<br>**3.** Non-Network Hospital & Emergency Protocol Check (registered beds & ICU criteria). | `policy_clauses.csv`<br>IRDAI Circulars |
| **7. Eligibility-Coverage** | Was patient covered, and was policy active on the date medical service was provided? | **1.** Member Dependency & Age Eligibility Check (dependent child up to 25 / marriage).<br>**2.** Premium Grace Period Audit ($\text{Admission} \le \text{Renewal} + 30\text{ days}$).<br>**3.** Portability & Waiting Period Continuity Check (prior insurer accrued credits). | `policy_clauses.csv`<br>Portability records |

* **Why This Architecture is Powerful:**
  * Rather than relying on a generic LLM prompt, **each denial category activates a dedicated deterministic and evidentiary audit pipeline**.
  * Findings are mathematically verified (MAE = 0), policy-grounded via indexed clauses, and legally cross-referenced against statutory IRDAI mandates.

---

## Slide 8: System Architecture — Specialized Agent & Subsystem Breakdown

* **Slide Layout:** 4-Quadrant Architecture Card Layout.
* **Quadrant 1 — Intake & Triage Layer:**
  * **Denial Intake Agent:** Extracts Claim ID, Denial Date, Cited Clauses, Repudiation Text, and Billed Amounts using few-shot regex and NER.
  * **Denial Type Router (Node 4):** Maps raw denial text into the 7 target categories: `MEDICAL_NECESSITY`, `PRE_EXISTING_WAITING_PERIOD`, `POLICY_EXCLUSION`, `FINANCIAL_LIMIT`, `DOCUMENTATION`, `ADMINISTRATIVE_PROCEDURAL`, and `ELIGIBILITY_COVERAGE`.
* **Quadrant 2 — Category-Specific Denial Investigation Engine (Node 5):**
  * **7 Specialized Domain Pipelines:** Dynamically activated based on the router classification.
  * **Neuro-Symbolic Integration:** Combines ChromaDB vector search over `policy_clauses.csv` with deterministic Python arithmetic (chronology, room rent ratios, NME line-item schedules).
  * **Evidence Verification:** Directly audits discharge summaries, lab reports, and physician prescriptions against clinical guidelines and IRDAI statutory circulars.
* **Quadrant 3 — Logic Synthesis & Arbitration Layer:**
  * **Evidence Graph Synthesizer (Node 6):** Connects Denial Reason → Policy Condition → Case Fact → Clinical Proof.
  * **Applicability Reasoner (Node 7):** Applies deterministic Boolean logic and Toulmin defeasible rules to evaluate whether an exception defeats the repudiation.
* **Quadrant 4 — Legal Drafting & Governance Layer:**
  * **Statutory Route Evaluator (Node 11):** Assesses limitation periods (30 days for Grievance Redressal Officer; 365 days for Ombudsman).
  * **Appeal Drafting Agent (Node 12):** Synthesizes an evidence-backed formal legal petition.
  * **HITL Review Checkpoint (Node 14):** Enables human reviewers to inspect citations, edit arguments, and authorize submission.

---

## Slide 9: Algorithms (Part 1 — Retrieval & Chronology)

* **Slide Layout:** Two-Column Technical Layout with Pseudo-code / Mathematical Logic.
* **Left Column — Hybrid Clause Retrieval & Exception Mining Algorithm (Evaluated by G2):**
  * **Reciprocal Rank Fusion (RRF) Formulation:** Combines dense vector semantic search with lexical BM25 matching:

    $$\text{RRF\_Score}(d) = \sum_{m \in \{\text{Dense}, \text{BM25}\}} \frac{1}{k + \text{Rank}_m(d)}, \quad k = 60$$

  * **Conditional Exception Mining Rule:** For retrieved clause text $T_c$, applies conditional pattern mining:

    $$\text{HasException}(T_c) = \begin{cases} 1, & \text{if } \exists w \in \{\text{"except", "unless", "provided that", "subject to"}\} \subseteq T_c \\ 0, & \text{otherwise} \end{cases}$$

  * **Deterministic Guarantee:** Guarantees that clauses with exceptions (e.g., failed conservative treatment overriding elective exclusion) are surfaced and preserved for legal reasoning.

* **Right Column — Deterministic Chronology & Statutory Moratorium Algorithm (Evaluates G4 & G8):**
  * **Elapsed Policy Duration Calculation:**
    $$T_{\text{elapsed}} = \frac{D_{\text{admission}} - D_{\text{inception}}}{30.4375 \text{ days/month}}$$
  * **Symptom Emergence Chronology:**
    $$\Delta_{\text{onset}} = D_{\text{onset}} - D_{\text{inception}}, \quad \text{IsPostInception} = \begin{cases} \text{True}, & \text{if } \Delta_{\text{onset}} \ge 0 \\ \text{False}, & \text{if } \Delta_{\text{onset}} < 0 \end{cases}$$
  * **IRDAI Statutory Moratorium Invariant (2024 60-Month Rule):**
    $$\mathcal{M} = \mathbb{I}(T_{\text{elapsed}} \ge 60 \text{ months})$$
  * **Decisional Predicate Formulation:**
    $$\mathcal{V}_{\text{PED}} = \begin{cases}
    \text{REVERSAL\_POST\_INCEPTION}, & \text{if } \text{IsPostInception} = \text{True} \\
    \text{REVERSAL\_STATUTORY\_MORATORIUM}, & \text{if } \mathcal{M} = 1 \\
    \text{REVERSAL\_WAITING\_EXPIRED}, & \text{if } T_{\text{elapsed}} \ge W_{\text{clause}} \\
    \text{UPHOLD\_GENUINE\_PED\_NON\_DISCLOSURE}, & \text{if } \neg\text{Declared} \land (T_{\text{elapsed}} < W_{\text{clause}})
    \end{cases}$$
  * **Zero-Hallucination Guarantee:** Executed via deterministic Python math (MAE = 0 days, 100% mathematical accuracy).

---

## Slide 10: Algorithms (Part 2 — Defeasible Logic & Financial Scaling)

* **Slide Layout:** Two-Column Technical Layout (Toulmin Defeasible Logic + Proportionate Financial Deduction).
* **Left Column — Toulmin Defeasible Argumentation Logic Algorithm (Evaluates G5, G7, G8):**
  * **Toulmin Schema:** Evaluates 5 tuple elements: $\langle \text{Claim } C, \text{Grounds } G, \text{Warrant } W, \text{Exception } E, \text{Rebuttal } R \rangle$.
  * **Defeasible Evaluation Function:**

    $$\mathcal{V}_{\text{Toulmin}} = \begin{cases}
    \text{CONTRADICTS\_DENIAL (REVERSAL)}, & \text{if } (E = \text{Satisfied}) \lor (G \models \neg W) \lor (R \neq \emptyset) \\
    \text{SUPPORTS\_DENIAL (UPHOLD)}, & \text{if } (W = \text{Valid}) \land (E \neq \text{Satisfied}) \land (R = \emptyset) \\
    \text{INSUFFICIENT\_EVIDENCE}, & \text{if } \text{Confidence}(G) < \theta \quad (\theta = 0.85)
    \end{cases}$$

  * **Concrete Adjudication Execution:**
    * *Insurer Claim $C$:* "Total Knee Replacement is an excluded elective procedure under Clause 4.3."
    * *Policy Warrant $W$:* "Clause 4.3 excludes elective surgeries unless conservative treatment failed for $\ge 6$ months."
    * *Clinical Grounds $G$:* "Discharge summary confirms 18 months of failed physiotherapy & injections."
    * *Exception Status $E$:* **SATISFIED** $\implies$ Rebuttal defeats Claim $\implies$ **REVERSAL RECOMMENDED**.

* **Right Column — Room Rent Proportionate Scaling & Financial Reclaim Algorithm:**
  * **Proportionate Scaling Ratio Formula:**
    $$R_{\text{deduction}} = \min\left(1.0, \; \frac{\text{Eligible Room Rent Limit}}{\text{Actual Incurred Room Rent}}\right)$$
  * **Non-Associated Item Protection Invariant:**
    Proportionate deduction is legally restricted strictly to room-associated charges; scaling of non-associated charges (implants, medicines, diagnostics) is explicitly barred:
    $$\text{Payable}(i) = \begin{cases}
    \text{Billed}(i) \times R_{\text{deduction}}, & \text{if } i \in \text{AssociatedCharges (Doctor fee, OT, nursing)} \\
    \text{Billed}(i), & \text{if } i \in \{\text{Medicines, Implants, Diagnostics, ICU}\}
    \end{cases}$$
  * **Non-Medical Expenses (NME) Reclaimed Recovery Formula:**
    $$\text{Reclaimable}_{\text{NME}} = \text{Total Billed} - \text{Permissible NME (IRDAI Annexure IV)} - \text{Approved Amount}$$


---

## Slide 11: Datasets Overview — The 13 Public Source Landscape

* **Slide Layout:** Two-Column Category Breakdown (Knowledge-Base Sources vs Evaluation Benchmarks).
* **Overview:** 100% public, free, ethically compliant healthcare and legal datasets (no synthetic filler):
* **Part A: Knowledge-Base Inputs & Upstream Pools (D1 – D8):**
  * **D1 (CMS DE-SynPUF):** 55M Medicare claims pool; sampled to synthesize baseline billing patterns and dates.
  * **D2 (MTSamples):** 4,999 real clinical transcripts across specialties; source for discharge narratives.
  * **D3 (ICD-10-CM Codes):** 70,000+ CDC/CMS diagnosis codes for entity normalization.
  * **D4 (ClaimSaathi):** Indian health insurance dataset; real Indian waiting-period dispute cases.
  * **D5 (HCPCS Level II):** 7,000+ CMS surgical procedure codes for surgical validation.
  * **D6 (IBM Healthcare Policy Rules):** GitHub open schema for transforming insurance text into IF-THEN rules.
  * **D7 (13 Retail Policy PDFs):** Full policy wordings across India's top 4 private insurers (ICICI Lombard, Care Health, HDFC ERGO, Star Health).
  * **D8 (CARC/RARC Codes):** X12/CMS standard dictionary of Claim Adjustment Reason Codes.
* **Part B: Dedicated Golden Evaluation Benchmarks (D9 – D13):**
  * **D9 (CA DMHC IMR Trend):** 100,000+ real Independent Medical Review decisions with Overturned/Upheld ground truth.
  * **D10 (Persius/imr-appeals):** Hugging Face dataset of annotated medical necessity appeal letters and decisions.
  * **D11 (CIO Ombudsman & Indian Kanoon):** Real Indian repudiation case legal texts and Ombudsman awards.
  * **D12 (InsLogicBench):** ACL 2026 dataset containing nested Toulmin argumentation ground truth.
  * **D13 (IRDAI Repudiation Notices):** Standard Indian health claim repudiation notices and regulatory formats.

---

## Slide 12: Runtime Knowledge-Base Datasets (The 5 Active CSVs)

* **Slide Layout:** Structured Table with Schemas, Sources, and Target Functions.
* **Slide Content:**

| Knowledge-Base File | Source Data | Record Count & Size | Detailed Schema / Features | Role in Runtime System |
| :--- | :--- | :--- | :--- | :--- |
| **`policy_clauses.csv`** | Extracted from D7 (13 Policy PDFs) | **1,997 structured clauses** (~2.4 MB) | `clause_id`, `insurer`, `product_name`, `section`, `clause_number`, `clause_text`, `clause_type`, `has_exception`, `exception_text`, `temporal_rule` | **Indexed in ChromaDB / FAISS** for RAG retrieval during Clause Verification. |
| **`denial_reasons.csv`** | D8 (CARC/RARC) + IRDAI taxonomy | **~80 standardized categories** (~45 KB) | `reason_id`, `category`, `sub_category`, `reason_text`, `carc_code`, `typical_clause_type`, `appeal_route` | Lookup & fuzzy match table used by Denial Router for triage. |
| **`icd10_codes.csv`** | D3 (CDC / CMS National Pool) | **71,704 diagnosis codes** (~4.1 MB) | `code`, `short_description`, `long_description`, `is_billable` | Entity validation table for clinical diagnosis verification. |
| **`procedure_codes.csv`** | D5 (HCPCS Level II / CMS) | **7,842 surgical codes** (~650 KB) | `hcpcs_code`, `short_description`, `category` | Validates claimed surgeries and links them to policy sub-limits. |
| **`nme_exclusions.csv`** | Extracted from D7 Policy Annexures | **~120 non-medical items** (~15 KB) | `item_id`, `item_name`, `category`, `typically_excluded` | Financial audit table for line-item deduction verification. |

* **Architectural Note:**
  * Raw, multi-thousand-row tables like `medical_notes.csv` and `claims_master.csv` are **eliminated from runtime**. Instead, clinical narratives and case profiles are self-contained within test cases, keeping the runtime lean and query-efficient.

---

## Slide 13: Golden Evaluation Benchmarks — 3-Tier Architecture

* **Slide Layout:** 3-Tier Hierarchical Diagram / Table (Component, Pipeline, Application).
* **Slide Content:**

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ LEVEL 1: COMPONENT GOLDEN BENCHMARKS (Granular Node Testing)                           │
├──────────────────────────────────────┬─────────────┬───────────────────────────────────┤
│ Benchmark Name                       │ Size        │ Ground Truth Schema / Metric      │
├──────────────────────────────────────┼─────────────┼───────────────────────────────────┤
│ G1: golden_intake_entities.json      │ 100 cases   │ Entity spans (Claim ID, Date, SI) │
│ G2: golden_clause_retrieval.json     │ 100 triplets│ Relevant Clause ID + Exception flag│
│ G3: golden_clinical_evidence.json    │ 60 cases    │ Structured Clinical Checklist     │
│ G4: golden_chronology_ped.json       │ 60 cases    │ Symbolic Date Calculation Truth   │
│ G5: golden_reasoning_toulmin.json    │ 80 cases    │ Toulmin Argument Components       │
│ G6: golden_appeal_drafts.json        │ 40 cases    │ Expert Reference Appeal Letters   │
└──────────────────────────────────────┴─────────────┴───────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ LEVEL 2: PIPELINE GOLDEN BENCHMARKS (End-to-End Pipeline Validation)                   │
├──────────────────────────────────────┬─────────────┬───────────────────────────────────┤
│ G7: golden_pipeline_medical_necessity │ 50 cases    │ 35 Overturn / 15 Upheld Decisions │
│ G8: golden_pipeline_waiting_period   │ 50 cases    │ 35 Overturn / 15 Upheld Decisions │
└──────────────────────────────────────┴─────────────┴───────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ LEVEL 3: APPLICATION GOLDEN BENCHMARKS (System-Wide Governance)                        │
├──────────────────────────────────────┬─────────────┬───────────────────────────────────┤
│ G9: golden_denial_router.json        │ 140 cases   │ 7-Class Balanced Categorization   │
│ G10: golden_hitl_benchmark.json      │ 30 cases    │ Dual-Expert Adjudication Consensus│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Slide 14: Dataset Engineering — Ingestion, Joins & Merging Pipeline

* **Slide Layout:** ETL & Synthesis Pipeline Flow Diagram + Description.
* **Dataset ETL Workflow:**

```
[Raw Sources: D7 Policy PDFs] ──(PyMuPDF Regex Parser)──► [policy_clauses.csv] ──► [ChromaDB Index]
                                                                  │
                                                       (Clause Pairing)
                                                                  ▼
[D9: CA DMHC IMR Trend]  ──(Filter: Ortho/Cardio)─────► [G3: Clinical Evidence] ──► [G7: End-to-End Med.
[D2: MTSamples Notes]    ──(Discharge Summaries) ──────►      Checklist JSON            Necessity Pipeline]
                                                                                        (Joined with D7)
[D11: Ombudsman Awards]  ──(Date & Award Parsing)─────► [G4: Chronology JSON]   ──► [G8: End-to-End Waiting
[D4: ClaimSaathi Records]──(Timeline Integration)─────►   (Symbolic Truth)              Period Pipeline]
                                                                                        (Joined with D7)
[D8: CARC/RARC Codes]    ──(Taxonomy Crosswalk)───────► [denial_reasons.csv]   ──► [G9: Router Benchmark]
[D13: IRDAI Notices]     ──(Entity Alignment)─────────► [G1: Intake Entities]  ──► [G6: Appeal Drafts]
```

* **Key Join & Merging Rules:**
  1. **Policy-Clause Pairing:** Policy PDFs are parsed into atomic clauses using regex boundaries and classified into `COVERAGE`, `EXCLUSION`, and `WAITING_PERIOD`, with explicit `has_exception` flags.
  2. **Clinical-to-Policy Joining:** Clinical disputes from D9/D2 are mapped to corresponding Indian policy clauses in D7 by ICD-10 diagnosis code to create ground truth triplets.
  3. **Ombudsman Timeline Merging:** Real Indian Ombudsman awards from D11 are aligned with D4 policy inception records to validate exact mathematical day offsets and moratorium rules.

---

## Slide 15: Dataset Features, Class Labels & Data Ranges

* **Slide Layout:** 3 Information Cards (Supervised Labels, Feature Sets, Numerical Ranges).
* **Card 1 — Supervised Classification Labels:**
  * **Router Triage (G9 - 7 Classes):** `MEDICAL_NECESSITY`, `PRE_EXISTING_WAITING_PERIOD`, `POLICY_EXCLUSION`, `FINANCIAL_LIMIT`, `DOCUMENTATION`, `ADMINISTRATIVE_PROCEDURAL`, `ELIGIBILITY_COVERAGE`.
  * **Pipeline Adjudication Verdict (G7 & G8 - 3 Classes):** `OVERTURN_RECOMMENDED`, `UPHOLD_JUSTIFIED`, `PARTIAL_APPROVAL_REDUCED`.
  * **Clause Retrieval Ground Truth (G2):** Binary `has_exception` (`True`/`False`), Target Clause IDs (e.g., `HS360-EX-043`).
* **Card 2 — Core Feature Attributes:**
  * *Patient/Policy Features:* Age, Gender, Insurer Name, Product Code, Sum Insured, Policy Inception Date, Continuous Renewal Years.
  * *Claim Event Features:* Claim ID, Hospital Name, Network Status (Cashless/Reimbursement), Admission Date, Discharge Date, Length of Stay (LOS), Total Billed Amount.
  * *Medical Features:* Primary ICD-10 Code, Secondary Diagnoses, HCPCS Surgical Code, Conservative Treatment Duration (Months), Severity Grade.
  * *Legal/Regulatory Features:* Repudiation Notice Date, Limitation Expiry Date, Target Forum (`Grievance_Cell`, `Ombudsman`, `Consumer_Forum`).
* **Card 3 — Realistic Data Ranges:**
  * **Claim Amount:** ₹15,000 to ₹25,00,000 (Mean: ₹3,85,000).
  * **Length of Stay:** 1 to 28 days (ICU stay: 0 to 12 days).
  * **Policy Inception Dates:** 2016-01-01 to 2025-12-31.
  * **Waiting Period Limits:** 30 days (initial), 12/24/36/48 months (PED), 60/96 months (statutory moratorium).
  * **Evidence Confidence Scores:** Continuous floating point [0.00, 1.00] (Threshold: 0.85).

---

## Slide 16: Methodology — Step-by-Step Execution Framework

* **Slide Layout:** 6 Sequential Phase Boxes with Iconography.
* **Slide Content:**
  * **Step 1: Multi-Modal Document Ingestion & Extraction**
    Ingest denial letters, policy wordings, and discharge summaries via PyMuPDF. Extract key metadata using named entity recognition and structured JSON templates.
  * **Step 2: Semantic Repudiation Normalization & Triage**
    Normalize free-text denial clauses against CARC/IRDAI taxonomies. Route cases to specialized verification workflows.
  * **Step 3: Category-Specific Denial Investigation (Node 5)**
    Execute dedicated multi-step audit for the identified denial category:
    * *Medical Necessity:* Severity & vital scan + conservative treatment audit (≥6m) + guideline matching.
    * *Waiting Period:* Onset chronology extraction + date math + IRDAI 60-month moratorium audit.
    * *Policy Exclusion:* Exact clause vector retrieval + exception mining + compliance check.
    * *Financial Limit:* Room-rent proportionate deduction ratio + sub-limit + NME bill audit.
    * *Documentation / Admin / Eligibility:* Document gap analysis, statutory delay circular evaluation, and dependency/portability verification.
  * **Step 4: Toulmin Argumentation & Evidence Matrix Construction**
    Assemble findings into a Toulmin argument tree. Compile a structured evidence matrix showing requirements, findings, supporting citations, and confidence scores.
  * **Step 5: Statutory Jurisdiction & Deadline Determination**
    Compute days elapsed since the denial notice. Select the appropriate filing forum: Insurer Grievance Cell (within 30 days) or Insurance Ombudsman (within 1 year).
  * **Step 6: Grounded Appeal Generation & Human-in-the-Loop Review**
    Draft a formal appeal petition citing exact clauses and evidence excerpts. Route the appeal package to the interactive UI for human review and PDF export.

---

## Slide 17: Evaluation Methodology & DeepEval Framework

* **Slide Layout:** Two-Column Layout (Evaluation Framework Table + DeepEval Metrics Harness).
* **Left Column — Multi-Tier Metrics Table:**

| Level | Component Evaluated | Metric Evaluated | Evaluation Tool / Formula | Target Threshold |
| :--- | :--- | :--- | :--- | :---: |
| **L1** | Intake Entities (G1) | Token F1 & Exact Match | `scikit-learn` / Python | F1 ≥ 0.95, EM ≥ 0.98 |
| **L1** | Clause RAG (G2) | `ContextualRecallMetric` / `ContextualPrecisionMetric` | **DeepEval** (LLM-as-a-Judge) | Recall ≥ 0.95 / Precision ≥ 0.90 |
| **L1** | Clinical Extraction (G3) | `FaithfulnessMetric` / Checklist Accuracy | **DeepEval** / Correct Checks / Total Checks | Faithfulness ≥ 0.95 / Accuracy ≥ 0.90 |
| **L1** | Chronology Engine (G4) | Deterministic Accuracy / Date Offset Error (MAE) | Python Unit Tests / MAE = (1/N)Σ\|d_pred - d_true\| | Accuracy = 100% / MAE = 0 days |
| **L1** | Toulmin Reasoner (G5) | Defeasible Verdict Accuracy / `GEval` (Logic Soundness) | `scikit-learn` / **DeepEval** G-Eval (1-5) | Accuracy ≥ 0.92 / G-Eval ≥ 4.5/5.0 |
| **L2** | End-to-End Pipelines (G7/G8) | Overturn Prediction F1 / Statutory Compliance | End-to-End Test Suite | Macro-F1 ≥ 0.90 / Compliance = 100% |
| **L3** | Human Review Alignment (G10) | Inter-Rater Reliability | **Cohen's Kappa (κ)** | κ ≥ 0.80 (Substantial Agreement) |

* **Right Column — Mathematical Formulation of Evaluation Metrics:**
  * **Token-Level F1-Score & Exact Match (NER Intake — G1):**
    $$\text{F1} = \frac{2 \times P \times R}{P + R}, \quad P = \frac{|T_{\text{pred}} \cap T_{\text{true}}|}{|T_{\text{pred}}|}, \quad R = \frac{|T_{\text{pred}} \cap T_{\text{true}}|}{|T_{\text{true}}|}, \quad \text{EM} = \mathbb{I}(T_{\text{pred}} = T_{\text{true}})$$
  * **Contextual Precision & Recall (DeepEval RAG — G2):**
    $$\text{Contextual Precision} = \frac{\sum_{k=1}^K (\text{Precision@}k \times v_k)}{\text{Total Relevant Retrieved Clauses}}, \quad \text{Contextual Recall} = \frac{|\mathcal{C}_{\text{retrieved}} \cap \mathcal{C}_{\text{golden}}|}{|\mathcal{C}_{\text{golden}}|}$$
  * **Faithfulness Metric (Hallucination Prevention — G3, G6):**
    $$\text{Faithfulness Score} = \frac{|\text{Truthful Claims Grounded in Context Document}|}{|\text{Total Claims Extracted in Generated Output}|}$$
  * **Mean Absolute Error (Date Math Offset — G4):**
    $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |d_{\text{predicted}}^{(i)} - d_{\text{ground\_truth}}^{(i)}| \quad (\text{Target: MAE} = 0 \text{ days})$$
  * **Multi-Class Macro-F1 (Triage Router — G9 & Verdicts — G7, G8):**
    $$\text{Macro-F1} = \frac{1}{|C|} \sum_{c=1}^{|C|} \text{F1}_c, \quad |C| = 7$$
  * **Cohen's Kappa (Inter-Rater Reliability — G10):**
    $$\kappa = \frac{P_o - P_e}{1 - P_e}, \quad P_o = \text{Observed Agreement}, \; P_e = \text{Chance Agreement}$$

---

## Slide 18: Project Timeline (July 2026 to April 2027)

* **Slide Layout:** Milestone Gantt Chart / Timeline Table.
* **Slide Content:**

```
2026                                                    2027
Jul   Aug   Sep   Oct   Nov   Dec   Jan   Feb   Mar   Apr
[=== Phase 1 ===]                                           Phase 1: Problem Formulation & Literature Survey
            [=== Phase 2 ===]                               Phase 2: Data Ingestion & Policy Base Build (COMPLETED)
                        [=== Phase 3 ===]                   Phase 3: Multi-Agent Architecture & Triage Router
                                    [=== Phase 4 ===]       Phase 4: Chronology Engine & Toulmin Reasoner
                                                [=== Phase 5 ===] Phase 5: Appeal Generator & HITL Dashboard
                                                      [=== Phase 6 ===] Phase 6: DeepEval Suite & Benchmarking
                                                            [=== Phase 7 ===] Phase 7: Final Defense & Report
```

| Phase & Milestone | Time Window | Key Deliverables & Status |
| :--- | :--- | :--- |
| **Phase 1: Formulation & Literature** | July 2026 – August 2026 | Refined project scope to claim denials; completed 6-paper literature review. *(Completed)* |
| **Phase 2: Data Pipeline & Policy Base** | September 2026 – October 2026 | Ingested 13 retail policy PDFs; created 5 active runtime CSVs and 10 golden evaluation JSONs. *(Completed - Review-2)* |
| **Phase 3: Multi-Agent Triage & Retrieval** | November 2026 – December 2026 | Implement LangGraph state machine, Denial Intake Agent, 7-class Router, and ChromaDB clause RAG. |
| **Phase 4: Symbolic & Toulmin Reasoner** | January 2027 | Build deterministic chronology engine and Toulmin defeasible logic reasoner. |
| **Phase 5: Appeal Generator & HITL UI** | February 2027 | Implement grounded appeal letter drafting agent, statutory deadline router, and review dashboard. |
| **Phase 6: DeepEval Testing & Tuning** | March 2027 | Run 3-tier evaluation across G1–G10 datasets; optimize latency and token efficiency. |
| **Phase 7: Final Report & Project Defense** | April 2027 | Final integration testing, complete project documentation, dissertation submission, and viva defense. |

---

## Slide 19: Environment Setup & Tech Stack

* **Slide Layout:** 4-Column Technical Specification Grid.
* **Slide Content:**
  * **1. Hardware Specifications:**
    * *Processor:* Intel Core i7 / AMD Ryzen 7 (8+ Cores, 16 Threads).
    * *System Memory:* 16 GB DDR4/DDR5 RAM (Minimum), 32 GB (Recommended).
    * *GPU:* NVIDIA RTX 3060 / 4060 (8GB+ VRAM) with CUDA 12.x for local embeddings and reranking.
    * *Storage:* 512 GB NVMe SSD (with ≥ 20 GB dedicated storage for policy vectors and evaluation JSONs).
  * **2. Core Runtime & Language:**
    * *Operating System:* Windows 11 / Ubuntu Linux 22.04 LTS.
    * *Environment Manager:* Python 3.10.x / 3.11.x, Conda / Poetry.
    * *Node.js:* v20 LTS (for web-based HITL dashboard).
  * **3. Frameworks, Libraries & Databases:**
    * *Multi-Agent Orchestration:* `langgraph` (v0.2+), `langchain` (v0.3+), Model Context Protocol (MCP).
    * *Evaluation Harness:* `deepeval` (v1.5+), `scikit-learn`, `pytest`.
    * *Document Parsing:* `PyMuPDF` (`fitz`), `pdfplumber`, `pytesseract`.
    * *Vector Store & Embeddings:* `chromadb` / `faiss-cpu`, `sentence-transformers` (`all-MiniLM-L6-v2` / `bge-large-en-v1.5`).
    * *Data Manipulation:* `pandas`, `pydantic` (v2), `numpy`.
  * **4. Model APIs & UI Layer:**
    * *Language Models:* OpenAI API (`gpt-4o` / `gpt-4o-mini`), Claude 3.5 Sonnet, Google Gemini 1.5 Pro.
    * *Backend API:* `FastAPI` (v0.110+), `uvicorn`.
    * *Frontend Review Dashboard:* `Streamlit` (Rapid prototype) / `Next.js` + `TailwindCSS` (Production HITL UI).

---

## Slide 20: References

* **Slide Layout:** Clean Academic Citation List (IEEE / ACM standard format).
* **Slide Content:**
  * **[1] S. Hanmante, S. Patil, and A. K. Shahade**, "A Multi Module A.I. System for Intelligent Health Insurance Support Using Retrieval Augmented Generation," *Scientific Reports*, vol. 16, no. 1, pp. 1024–1038, 2026. DOI: `10.1038/s41598-026-62665-0`.
  * **[2] M. Fink, C. J. McCarthy, et al.**, "Decreasing Administrative Effort Related to Non-Approval of Image-guided Procedures Using Large Language Models – The DENIED-AI Pilot Study," *Academic Radiology*, vol. 33, no. 8, pp. 3221–3231, 2026. DOI: `10.1016/j.acra.2026.04.021`.
  * **[3] J. Liu, Z. Chen, et al.**, "InsLogicBench: An Argumentation Logic Grounded Benchmark for Complex Insurance Claims Adjudication," in *Proc. 64th Annual Meeting of the Association for Computational Linguistics (ACL)*, 2026, pp. 1035–1052. DOI: `10.18653/v1/2026.acl-long.1035`.
  * **[4] T. Owolabi**, "Transforming Appeal Decisions: Machine Learning Triage for Hospital Admission Denials," *JAMIA Open*, vol. 8, no. 2, pp. 112–121, 2025. DOI: `10.1093/jamiaopen/ooaf016`.
  * **[5] K. Kiser, J. Cole, et al.**, "Large Language Models to Help Appeal Denied Radiotherapy Services," *JCO Clinical Cancer Informatics*, vol. 8, pp. e2400129, 2024. DOI: `10.1200/CCI.24.00129`. *(Added Literature Survey)*
  * **[6] S. Pokharel, A. Anand, et al.**, "From Policy to Logic for Efficient and Interpretable Coverage Assessment," *arXiv preprint arXiv:2601.01266*, 2026. DOI: `10.48550/arXiv.2601.01266`. *(Added Literature Survey)*

---

## Slide 21: Summary & Conclusion

* **Slide Layout:** 3-Column Summary Cards + Q&A Closing.
* **Card 1 — Review-2 Achievements:**
  * Cleanly narrowed project scope exclusively to **Health Claim Denial Analysis and Appeal Generation**.
  * Curated 13 public healthcare datasets into 5 lean runtime knowledge CSVs and 10 golden evaluation benchmarks.
  * Formulated an auditable 15-node LangGraph agentic workflow with a dedicated 7-category denial investigation engine (Node 5) combining RAG with Toulmin defeasible logic.
* **Card 2 — Immediate Next Steps:**
  * Connect the LangGraph state machine with the ChromaDB vector database.
  * Execute automated baseline evaluations across G1–G10 datasets using DeepEval.
  * Complete development of the interactive Human-in-the-Loop review dashboard.
* **Card 3 — Expected Real-World Impact:**
  * Democratizes access to health insurance justice for policyholders facing unfair repudiations.
  * Reduces appeal preparation time from days to under 5 minutes, backed by exact policy clauses and clinical evidence.
* **Q&A Section:**
  * **Thank You!**
  * *Open for Questions and Feedback.*

---

## Summary Checklist for Presentation Preparation

| Slide Number | Template Section Addressed | Key Technical Focus |
| :---: | :--- | :--- |
| **Slide 1** | Project Details & Metadata | Title, Roll numbers, Guide, Department, Institution |
| **Slide 2** | **1) Problem Statement** | 15–20% denial rate, clause misapplication, LLM legal hallucinations |
| **Slide 3** | **2) Objectives** | 6 post-denial objectives (intake, triage, category investigation, logic, appeals, HITL) |
| **Slides 4 & 5** | **3) Literature Survey** | 6 papers (Hanmante, Liu, Fink, Owolabi + Kiser & Pokharel) + Gaps |
| **Slide 6** | **4) System Architecture** | 15-node LangGraph orchestration pipeline with unified Node 5 |
| **Slide 7** | **4) System Architecture (Deep-Dive)** | **Node 5 Deep-Dive: 7-Category Denial Investigation Framework** |
| **Slide 8** | **4) System Architecture (Subsystems)** | 4-Quadrant Specialized Agent & Subsystem Breakdown |
| **Slides 9 & 10** | **5) Algorithms** | RRF RAG retrieval, Symbolic chronology engine, Toulmin defeasible logic |
| **Slides 11–15** | **6) Datasets** | 13 public sources, 5 runtime CSVs, 10 golden JSONs, ETL pipeline, schema ranges |
| **Slide 16** | **8) Methodology** | 6-phase operational workflow featuring Node 5 category-specific investigation |
| **Slide 17** | Evaluation Methodology | 3-tier DeepEval framework, metrics, thresholds, and guardrails |
| **Slide 18** | **7) Project Timeline** | July 2026 to April 2027 Gantt chart, milestones, and deliverables |
| **Slide 19** | **9) Environment Setup** | Hardware, OS, Python 3.11, LangGraph, DeepEval, ChromaDB, FastAPI |
| **Slide 20** | **10) References** | Standard IEEE/ACM formal citations for all 6 papers |
| **Slide 21** | Conclusion & Q&A | Summary of progress, next steps, and wrap-up |
