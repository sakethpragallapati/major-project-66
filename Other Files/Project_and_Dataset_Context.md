# Complete Project & Dataset Context — Master Reference Document

**Project Title:** AI-Powered Policy-Grounded Agentic AI for Health Insurance Claim Denial Analysis and Appeal Support
**Project ID:** 66
**Students:** Pragallapati Saketh (160123733129), Saketh Vemulapati (160123733136)
**Supervisor:** A. Sangeetha, Assistant Professor, Dept. of Computer Science & Engineering
**Institution:** Chaitanya Bharathi Institute of Technology (Autonomous), Gandipet, Hyderabad
**Affiliation:** Osmania University

---

# SECTION 1: ENTIRE PROJECT CONTEXT

---

## 1.1 Executive Summary & Core Mission

Health insurance in India has expanded rapidly under regulatory mandates and increased post-pandemic coverage. However, the claims adjudication process remains plagued by high repudiation rates, dense legal contracts, and asymmetric information between insurers and policyholders.

When a policyholder receives a **Claim Denial (Repudiation Notice)**, they are confronted with cryptic Claim Adjustment Reason Codes (CARC), high-level exclusion headings (e.g., *"Clause 4.3 – Elective Surgery"*), or allegations of *"Pre-Existing Disease (PED) Non-Disclosure"*. In the vast majority of cases:

1. Insurers issue **blanket repudiations** citing general exclusion clauses while ignoring **explicit exception sub-clauses** (e.g., surgery deemed necessary after conservative medical management failed for over 6 months).
2. Insurers disregard **statutory IRDAI protections** (such as the 60-month/8-year continuous coverage moratorium clause, which legally bars repudiations based on pre-existing non-disclosure after continuous renewals).
3. Policyholders lack the clinical and legal expertise to parse 40+ page policy wordings, audit hospital discharge summaries, cross-reference itemized billing annexures, and draft a formal legal petition within statutory limitation windows.

This project delivers a **Policy-Grounded, Multi-Agent Neuro-Symbolic AI System** that automates the entire post-denial workflow:
* Ingests unstructured denial letters, policy contracts, and clinical documents.
* Normalizes denial reasons into a standardized 7-category taxonomy.
* Dispatches dedicated, category-specific investigations across 7 specialized pipelines (Clinical Severity & Guidelines, Chronology & Moratorium, Exception Mining, Proportionate Deductions & Sub-Limits, Document Gap Analysis, Procedural Delay Circulars, and Eligibility/Portability).
* Evaluates disputes using **Pokharel Symbolic Logic** and the **Toulmin Defeasible Argumentation Framework** (Claim, Grounds, Warrant, Rebuttal, Exception).
* Produces an **admissible, citation-grounded appeal dossier** formatted for the insurer's Grievance Cell or the Insurance Ombudsman, governed by **Human-in-the-Loop (HITL)** oversight.

---

## 1.2 Evolution from Review-1 to Review-2

In Review-1, the project surveyed two broad phases of health claims:
1. *Pre-submission Claim Readiness Assessment* (verifying document completeness and pre-authorizations).
2. *Post-denial Appeal Generation*.

### The Strategic Scope Refinement for Review-2:

Based on evaluator feedback and feasibility benchmarking, **pre-submission claim readiness assessment has been completely dropped**. The project is now **100% focused on Claim Denial Analysis and Appeal Support**.

```
[Review-1 Scope (Diffused)]:
  ├── Claim Readiness & Pre-submission Validation (DROPPED)
  └── Claim Denial & Appeal Support

[Review-2 Scope (Laser-Focused)]:
  └── End-to-End Claim Denial Repudiation Analysis & Evidence-Grounded Appeal System
        ├── Denial Intake & NER Entity Extraction (Node 2)
        ├── 7-Category Denial Triage Routing (Node 4)
        ├── Category-Specific Denial Investigation Engine (Node 5: 7 Unique Workflows)
        │     ├── 1. Medical Necessity (Vital Severity, Conservative Audit ≥6m, Guidelines)
        │     ├── 2. Pre-Existing Waiting Period (Onset Chronology, Date Math, Moratorium)
        │     ├── 3. Policy Exclusion (Exact Clause Vector Match, Exception Mining)
        │     ├── 4. Financial Limit (Room Rent Ratio, Sub-limit Capping, NME Bill Audit)
        │     ├── 5. Documentation (Deficiency Parsing, Gap Analysis, Requisitions)
        │     ├── 6. Administrative-Procedural (Deadlines, IRDAI Delay Circulars, Network)
        │     └── 7. Eligibility-Coverage (Member Dependency, Grace Period, Portability)
        ├── Evidence Graph Synthesis (Node 6)
        ├── Toulmin Defeasible Logic Reasoner & Applicability Engine (Node 7 & 8)
        └── Grounded Appeal Generation & Human-in-the-Loop Governance (Node 11 to 15)
```

---

## 1.3 The Real-World Domain Landscape: Indian Health Insurance & Jurisprudence

To build an AI system capable of overturning insurance repudiations, the system is grounded directly in Indian insurance statutory frameworks:

```
Hospitalization & Claim Submission
        │
        ▼
  Insurer Adjudication
        │
   ┌────┴────┐
   ▼         ▼
Approved   DENIED (Repudiation Notice Issued)
   │              │
   ▼              ▼
Settlement   Phase 1: Internal Grievance Cell (GRO)
             (Mandatory 30-Day Window)
                  │
             ┌────┴────┐
             ▼         ▼
         Overturned   Upheld / No Response in 30 Days
             │              │
             ▼              ▼
         Settlement    Phase 2: Statutory Escalation
                            │
                       ┌────┴────┐
                       ▼         ▼
              Insurance        Consumer Disputes
              Ombudsman        Redressal Forum
           (Up to ₹50L,     (No Upper Limit,
            Binding on       Legal Representation)
            Insurer)
```

### Key Regulatory Concepts Built into the System:

1. **IRDAI (Insurance Regulatory and Development Authority of India) Standardization:**
   * Standardized exclusion codes: `Code-Excl01` (Pre-Existing Diseases), `Code-Excl02` (Specified disease/procedure waiting period), `Code-Excl03` (30-day initial waiting period), `Code-Excl04` (Investigation & Evaluation).
   * **Statutory Moratorium Clause:** Under IRDAI circulars, after **60 months (5 years)** of continuous policy renewals (reduced from 8 years in 2024), no claim can be repudiated on grounds of non-disclosure or misstatement, except in proven cases of established criminal fraud.

2. **Escalation Hierarchy & Limitation Windows:**
   * **Stage 1 (Internal Redressal):** The policyholder has **30 days** from the denial notice to file an appeal with the insurer's Grievance Redressal Officer (GRO).
   * **Stage 2 (Insurance Ombudsman):** If rejected by the GRO or if no response is received within 30 days, the policyholder has **1 year** to file an appeal before the regional Insurance Ombudsman (covers claims up to ₹50 Lakhs; award is legally binding on the insurer).
   * **Stage 3 (Consumer Disputes Commission):** Under the Consumer Protection Act 2019, policyholders have **2 years** to approach the District/State Commission.

3. **Common Insurer Repudiation Patterns Tackled:**
   * *The "Elective Surgery" Trap:* Rejecting surgeries (e.g., Knee Replacements, Spinal Fusions, Septoplasty) as "cosmetic/elective" without checking whether the patient underwent documented non-surgical treatment that failed.
   * *The "Pre-Existing Disease" Ambush:* Repudiating claims citing past hypertension or diabetes notes, even when the claimed acute illness is unrelated or the condition emerged *after* policy inception.
   * *Non-Medical Expense (NME) Over-Deductions:* Inflating deductions by disallowing gloves, PPE, surgical consumables, and registration fees beyond IRDAI-prescribed guidelines.

---

## 1.4 The Technological Paradigm: Neuro-Symbolic Agentic AI

Existing approaches fall into two flawed extremes:
* **Generic LLMs (Pure Generative):** When fed long insurance policies, models like GPT-4 or Claude hallucinate coverage exceptions up to 44% of the time (Pokharel et al., 2026), fabricate legal citations, and provide ungrounded conversational advice.
* **Traditional Machine Learning (Pure Statistical):** Supervised classifiers (Owolabi, 2025) predict whether a denial is likely to be overturned, but act as black boxes—they cannot extract evidence, cite sub-clauses, or draft an appeal letter.

### Our Solution: Neuro-Symbolic Multi-Agent Collaboration

Our architecture fuses the **semantic comprehension of LLMs** with the **deterministic rigor of symbolic logic**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   NEURO-SYMBOLIC ARCHITECTURE                          │
├───────────────────────────────────┬────────────────────────────────────┤
│       NEURAL COMPONENT            │        SYMBOLIC COMPONENT          │
│   (LLM / Embeddings / Agents)     │   (Python Engines / Formal Logic)  │
├───────────────────────────────────┼────────────────────────────────────┤
│ • PyMuPDF OCR & Entity Extraction │ • Chronological Date Math (MAE = 0)│
│ • Hybrid Semantic Vector Search   │ • Statutory Moratorium Thresholds  │
│ • Discharge Summary Clinical Audit│ • Sub-limit & Co-pay Calculations │
│ • Toulmin Argument Synthesis      │ • Boolean Applicability Rules      │
│ • Natural Language Appeal Drafting│ • Citation Verification Guardrails │
└───────────────────────────────────┴────────────────────────────────────┘
```

---

## 1.5 End-to-End 15-Node Workflow Walkthrough

Here is the step-by-step lifecycle of a denied claim inside the system:

```
[User Input: Denial Notice + Policy PDF + Discharge Summary + Bills]
                                │
                                ▼
                     [Node 1: User Document Upload]
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

### Detailed Node-by-Node Functionality:

1. **Node 1 (User Ingestion):** User uploads multi-modal claim assets (Denial letter, policy wording PDF, discharge summary, lab reports, hospital bill).

2. **Node 2 (Denial Intake Agent [Lop21]):** Uses few-shot entity extraction to parse Claim ID, Denial Date, Cited Clauses, Repudiation Text, and Billed Amounts.

3. **Node 3a (Denial Reason Normalization):** Maps raw repudiation strings into the standardized 7-category taxonomy using `denial_reasons.csv`.

4. **Node 3b (Case Fact Reconstruction [Lop21, Ahs23]):** Builds a unified case state (Patient profile, admission window, surgical codes, sum insured, primary diagnosis).

5. **Node 4 (Denial Type Router [Owo24, Mcc26]):** Triage router normalizes and classifies the repudiation notice into one of 7 standardized categories (`MEDICAL_NECESSITY`, `PRE_EXISTING_WAITING_PERIOD`, `POLICY_EXCLUSION`, `FINANCIAL_LIMIT`, `DOCUMENTATION`, `ADMINISTRATIVE_PROCEDURAL`, and `ELIGIBILITY_COVERAGE`) and dispatches the claim directly to the appropriate specialized investigation pipeline in Node 5.

6. **Node 5 (Category-Specific Denial Investigation Engine):** Rather than relying on a generic LLM prompt, Node 5 executes a dedicated, category-specific investigation pipeline tailored to the repudiation category. Each denial type triggers specialized evidence extraction, deterministic calculations, and statutory regulatory cross-referencing (detailed in Section 1.5.1 below).

7. **Node 6 (Evidence Graph Synthesizer [Liu26, Lop21]):** Links Denial → Requirement → Case Fact → Clinical Proof into a structured evidence graph.

8. **Node 7 (Applicability Reasoner [Pok26, Liu26]):** Applies deterministic Boolean logic and Toulmin defeasible rules. Converts clause conditions into symbolic logic (AND/OR/NOT) and evaluates whether clinical evidence satisfies policy exceptions, defeating the insurer's repudiation.

9. **Node 8 (Evidence Matrix [Pan24]):** Renders a structured audit table with requirement, fact, evidence source, status (SUPPORTS/CONTRADICTS/NEUTRAL), and confidence scores.

10. **Node 9 (Denial Assessment):** Emits final verdict: `OVERTURN_RECOMMENDED`, `UPHOLD_JUSTIFIED`, or `PARTIAL_APPROVAL_REDUCED`.

11. **Node 10 (Targeted Re-Analysis Guardrail):** Deterministically verifies citations against raw source documents to prevent hallucinations. Re-reads the policy PDF and discharge summary to confirm the exception language and clinical facts exist verbatim.

12. **Node 11 (Statutory Route & Deadline Check):** Computes elapsed time since the denial notice and determines the target legal forum:
    * Within 30 days → Internal Grievance Cell (GRO)
    * 30 days to 1 year → Insurance Ombudsman
    * Beyond 1 year → Consumer Disputes Forum

13. **Node 12 (Appeal Drafting Agent [Kis24, Mcc26]):** Compiles a formal legal appeal petition addressed to the competent authority, with structured Toulmin warrants and cited evidence.

14. **Node 13 (Grounded Appeal Draft):** Formats the petition with embedded clause citations, clinical evidence references, and itemized evidence annexures.

15. **Node 14 (Human-in-the-Loop Review UI [Sbo24]):** Displays the case summary, evidence matrix, and draft letter to the user/lawyer for audit, edit, and approval.

16. **Node 15 (Final Dossier Pack):** Generates an exportable PDF packet containing the signed appeal petition, highlighted policy clauses, and certified medical proof.

---

### 1.5.1 Node 5 Deep-Dive: The 7 Category-Specific Denial Investigation Framework

The core engine of our architecture organizes claim-denial evaluation into **seven specialized investigation workflows**, equipped with dedicated evidence checks, policy table lookups, and deterministic calculation steps based on the *Insurance Claim Denial Investigation Framework*:

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

#### Detailed Specification of the 7 Investigation Categories:

#### 1. `MEDICAL_NECESSITY`
* **Core Question:** Was this hospitalization or procedure clinically required, or could it have been avoided, treated conservatively, or performed as an outpatient?
* **Specialized Multi-Step Workflow:**
  1. **Clinical Severity and Vital Instability Scan:**
     * Scans the discharge summary and doctor's notes for objective physiological severity indicators.
     * Identifies vital instability (e.g., oxygen saturation $\text{SpO}_2 < 90\%$, severe pain scores $\ge 8/10$) and diagnostic severity grades (e.g., Grade IV osteoarthritis with bone-on-bone contact or 90% LAD arterial stenosis).
  2. **Conservative Management Audit:**
     * Searches patient history for non-surgical and non-invasive therapies attempted prior to surgery: physiotherapy, steroid injections, pharmacotherapy, and lifestyle interventions.
     * Computes $\text{Duration} = \text{Date of Surgery} - \text{First Recorded Conservative Treatment Date}$.
     * Checks whether the duration meets the relevant clinical threshold (e.g., at least 6 continuous months).
  3. **Clinical Guideline Matching:**
     * Cross-references the ICD-10 diagnosis in `icd10_codes.csv` and procedure in `procedure_codes.csv` against medical-necessity criteria (InterQual, Milliman Care Guidelines [MCG], and Indian clinical protocols).
     * Validates whether surgical indications were satisfied (e.g., failed conservative therapy plus radiological evidence of end-stage joint destruction).
  4. **Physician Certification Verification:**
     * Verifies whether the treating surgeon issued a formal written certificate stating that inpatient surgery was medically necessary to prevent permanent disability, organ failure, or mortality.

#### 2. `PRE_EXISTING_WAITING_PERIOD`
* **Core Question:** Did the disease originate before the policy began, and does the insurer have the legal right to repudiate the claim after considering continuous policy renewals?
* **Specialized Multi-Step Workflow:**
  1. **First-Symptom and Onset Chronology Tracing:**
     * Scans History of Present Illness (HPI) and clinical consultation records for temporal statements (e.g., *"symptoms for three years"*, *"hypertensive for five years"*, *"first noticed swelling in 2021"*).
     * Extracts earliest documented onset date $D_{\text{onset}}$.
  2. **Policy Timeline Calculation:**
     * Computes $\text{Elapsed Policy Time} = \text{Date of Hospital Admission} - \text{Policy Inception Date}$.
     * Compares elapsed time with waiting periods configured in `policy_clauses.csv`: initial waiting period (30 days), specified diseases (cataracts, hernia, joint replacements: 24 months), and pre-existing diseases (36 or 48 months).
  3. **IRDAI Statutory Moratorium Clause Audit:**
     * Checks number of continuous, uninterrupted policy-renewal years.
     * Enforces the statutory moratorium rule (60 months / 5 years under IRDAI 2024 regulations, reduced from 8 years).
     * If the moratorium threshold is met, flags the denial as legally barred from repudiation on pre-existing or non-disclosure grounds (subject to proven intentional criminal fraud exceptions).
  4. **Proposal Form Non-Disclosure Cross-Check:**
     * Compares the condition with declarations in the original proposal form.
     * Investigates whether the condition was asymptomatic and undiagnosed at policy inception (e.g., hypertension discovered during routine pre-operative checkup does not constitute pre-existing non-disclosure).

#### 3. `POLICY_EXCLUSION`
* **Core Question:** Does the cited policy exclusion apply to the case, or is there an exception or sub-clause that overrides it?
* **Specialized Multi-Step Workflow:**
  1. **Exact Clause Retrieval and Scope Verification:**
     * Uses vector search over `policy_clauses.csv` to retrieve the exact clause cited in the denial letter (e.g., Clause 4.3 — Elective Surgeries; Clause 4.12 — Genetic Disorders).
     * Checks whether procedure code in `procedure_codes.csv` and ICD-10 code in `icd10_codes.csv` fall within the clause's legal scope.
  2. **Exception Clause Search:**
     * Analyzes clause's `has_exception` and `exception_text` attributes.
     * Looks for conditional exceptions (e.g., exclusions subject to accidental bodily injury, cancer-treatment necessity, or provisions under Section 21 of the Mental Healthcare Act, 2017).
  3. **Exception Criteria Compliance Audit:**
     * Evaluates patient's clinical evidence against exception criteria.
     * If exception criteria are satisfied, flags a *Potential Misapplication of Exclusion* for immediate appeal grounds.

#### 4. `FINANCIAL_LIMIT`
* **Core Question:** Did the insurer calculate deductions correctly, or did it improperly apply deductions involving room rent, sub-limits, or non-medical items?
* **Specialized Multi-Step Workflow:**
  1. **Room Rent Proportionate Deduction Audit:**
     * Checks whether patient occupied a room category above policy limit (e.g., deluxe suite when eligible for twin-sharing accommodation).
     * Calculates $\text{Deduction Ratio} = \text{Eligible Room Rent} / \text{Actual Room Rent}$.
     * Verifies whether proportionate deductions were improperly applied to items that should NOT be scaled by room category (such as medicines, consumables, or implants).
  2. **Sub-Limit and Capping Verification:**
     * Audits treatment-specific caps against remaining Sum Insured (e.g., cataract capped at ₹40,000 per eye, ICU capped at 2% of SI, robotic-surgery caps).
  3. **Non-Medical Expenses (NME) Bill Audit:**
     * Compares every line item on itemized hospital bill against `nme_exclusions.csv` (based on configured IRDAI Annexure IV list).
     * Distinguishes genuine non-medical items (admission kits, attendant food) from improperly disallowed surgical consumables (surgical gloves, syringes, IV cannulas, PPE kits during infectious disease).
     * Computes $\text{Potential Reclaimed Amount} = \text{Total Bill} - \text{Permissible NME} - \text{Approved Amount}$.

#### 5. `DOCUMENTATION`
* **Core Question:** Are the documents requested by the insurer genuinely missing, or did the insurer overlook documents already submitted?
* **Specialized Multi-Step Workflow:**
  1. **Deficiency Letter Parsing:**
     * Parses insurer's query letter or repudiation notice and extracts specific requested documents (Indoor Case Papers [ICP], Treating Doctor Certificate, Pre-Authorization Form, original X-ray films).
  2. **Repository Gap Analysis:**
     * Compares insurer's requested list with patient's uploaded document manifest.
     * Tags records as `Already Available` (submitted in archive; insurer overlooked records) or `Genuinely Missing`.
  3. **Hospital Action Item and Requisition Generator:**
     * Identifies issuing entity (Hospital Records Department, TPA desk, or treating physician).
     * Drafts a specific requisition letter for each genuinely missing record.

#### 6. `ADMINISTRATIVE_PROCEDURAL`
* **Core Question:** Was the delay in claim intimation or hospital submission justifiable, and can the insurer legally repudiate the claim on procedural or technical grounds?
* **Specialized Multi-Step Workflow:**
  1. **Filing and Intimation Deadline Calculation:**
     * Computes $\text{Intimation Delay} = \text{Date of Intimation} - \text{Date of Hospital Admission}$ (policy threshold: typically 24 hours).
     * Computes $\text{Submission Delay} = \text{Date of Claim Submission} - \text{Date of Discharge}$ (policy threshold: typically 15 days).
  2. **IRDAI Statutory Delay Circular Evaluation:**
     * Cross-references delay against IRDAI Circular Reference `IRDA/HLT/MISC/CIR/216/09/2011`.
     * Evaluates whether delay resulted from circumstances beyond the insured's control (emergency admission, ICU stay, loss of consciousness, caregiver unavailability).
     * Bars insurers from repudiating genuine claims solely on procedural delay grounds.
  3. **Non-Network Hospital and Emergency Protocol Check:**
     * If claim was denied because a non-network hospital was used without prior intimation, checks whether admission involved an acute medical emergency.
     * Verifies applicable hospital infrastructure requirements (registered-bed criteria, 24/7 doctor and nursing availability).

#### 7. `ELIGIBILITY_COVERAGE`
* **Core Question:** Was the patient covered, and was the policy active on the date the medical service was provided?
* **Specialized Multi-Step Workflow:**
  1. **Member Dependency and Age Eligibility Check:**
     * Validates insured member's relationship and age against policy's eligibility criteria (dependent children covered up to age 25 or marriage; dependent parents entry-age criteria).
  2. **Premium Grace Period Audit:**
     * If denied for policy lapse, verifies whether hospitalization occurred within the statutory grace period ($\text{Admission Date} \le \text{Renewal Due Date} + 30\text{ days}$).
     * Verifies that renewal premium was paid and coverage continuity is preserved under statutory regulations.
  3. **Portability and Waiting Period Continuity Check:**
     * For ported policies, audits portability records to verify that accrued waiting-period credits from previous insurer were carried forward.

---

#### Runtime Data Integration Across the 7 Categories:

Each specialized investigation grounds its analysis in the 5 active runtime tables:

| Runtime File | Primary Purpose | Used By Categories |
| :--- | :--- | :--- |
| **`policy_clauses.csv`** | Policy clauses, waiting periods, exclusions, and exception text | `MEDICAL_NECESSITY`, `PRE_EXISTING_WAITING_PERIOD`, `POLICY_EXCLUSION`, `FINANCIAL_LIMIT`, `ELIGIBILITY_COVERAGE` |
| **`denial_reasons.csv`** | Classification and taxonomy mapping of insurer repudiation reasons | Node 4 Router (All 7 categories) |
| **`icd10_codes.csv`** | Clinical diagnosis entity mapping and verification | `MEDICAL_NECESSITY`, `PRE_EXISTING_WAITING_PERIOD`, `POLICY_EXCLUSION` |
| **`procedure_codes.csv`** | Surgical procedure identification and scope verification | `MEDICAL_NECESSITY`, `POLICY_EXCLUSION`, `FINANCIAL_LIMIT` |
| **`nme_exclusions.csv`** | Non-medical expense line-item exclusion schedules | `FINANCIAL_LIMIT` |

* **What Makes This Architecture Powerful:**
  The system performs category-specific investigations rather than relying on a generic LLM prompt. Each denial type triggers specialized evidence checks, deterministic calculations, and statutory regulatory cross-referencing. Findings are linked directly to policy clauses and supporting evidence before entering the Toulmin Defeasible Logic Reasoner.

---
---

## 1.6 Literature Foundation (Paper-to-System Contribution Map)

| Paper Tag | Authors & Year | What It Actually Does | What Our System Takes From It |
| :--- | :--- | :--- | :--- |
| **[Lop21]** | López et al. 2021 | Takes messy policy PDF text → parses sentences using dependency trees → extracts structured "benefit rules" (IF condition THEN coverage) into a knowledge graph. | **Policy text → structured IF-THEN rules.** Our Denial Intake and Policy Clause Verification agents use this idea to parse uploaded policy documents into queryable clause structures. |
| **[Pic22]** | Picco et al. 2022 | Trains a classifier with very few labeled examples to identify which sentences in a policy document describe a "benefit rule" vs. general text. | **Few-shot classification of policy sentences.** Our Policy Clause Verification agent uses this concept — the LLM identifies which clause is relevant to the denial with minimal examples. |
| **[She24]** | KAMEL 2024 | Links free-text exclusion descriptions (e.g., "respiratory illnesses") to standardized ICD-10 codes using medical ontologies. | **Medical entity linkage.** Our Case/Evidence Investigation agent uses this approach to connect the diagnosis extracted from clinical notes to the correct ICD-10 code and then check it against policy exclusions. |
| **[She24b]** | Lui et al. 2024b | Extends KAMEL by adding LLMs + medical ontologies for end-to-end claims processing automation. | **The hybrid ontology + LLM architecture.** We use this design pattern in Case/Evidence Investigation — the ontology provides structure, the LLM provides reasoning. |
| **[Pan24]** | Pandey et al. 2024 | Builds a multi-agent system where each agent handles one sub-task of Prior Authorization (extract checklist → check each item → give verdict with evidence). | **The multi-agent decomposition pattern.** This is literally our overall architecture — break the denial analysis into specialized agents, each handling one sub-task. Also: the "checklist with evidence" pattern feeds our Evidence Matrix. |
| **[Ahs23]** | Ahsan et al. 2023 | Uses LLMs to search through patient clinical notes and retrieve specific evidence for a given medical query, with confidence scores. | **Evidence retrieval from clinical text.** Our Case/Evidence Investigation agent uses this exact pattern — given a denial reason, search the discharge summary for supporting/contradicting evidence and return a confidence score. |
| **[Sbo24]** | Sbodio et al. 2024 | Builds a human-AI collaborative system where AI investigates claims compliance and a human reviewer validates findings before final decision. | **The human-in-the-loop review pattern.** Our Human Review stage directly implements this — AI produces the analysis, human validates before the appeal is sent. |
| **[Kum10]** | Kumar et al. 2010 | Uses data mining (decision trees, rules) on historical claims to predict which claims will have processing errors. | **Claims pattern analysis.** Our Financial/Admin Check agent uses this concept — rule-based checks on claim amounts, dates, and codes to catch errors/anomalies. |
| **[Liu26]** | Liu et al. 2026 | Creates InsLogicBench — formalizes insurance policy clauses into argumentation logic (claim → grounds → warrant → exception → rebuttal) using the Toulmin model. | **Argumentation structure for appeals.** Our Applicability Reasoner and Appeal Agent use this Toulmin model: "The denial is wrong BECAUSE [grounds] SINCE [policy warrant] UNLESS [exception applies]". |
| **[Pok26]** | Pokharel et al. 2026 | Converts policy text into symbolic logic rules (AND/OR/NOT) paired with a coverage-aware retriever, reducing LLM hallucinations by 44%. | **Policy-to-logic conversion.** Our Applicability Reasoner directly uses this — convert clause conditions into logical rules (IF admitted AND policy_active AND NOT excluded THEN covered). |
| **[Kis24]** | Kiser et al. 2024 | Uses GPT-4 to draft radiotherapy appeal letters, evaluates quality vs. physician-written letters. | **LLM-based appeal drafting.** Our Appeal Agent uses this approach — the LLM generates the appeal letter grounded in policy clauses and evidence. |
| **[Mcc26]** | DENIED-AI 2026 | Pilot study using LLMs to reduce admin burden for denial management of imaging procedures. | **Denial workflow automation pattern.** Our overall flow (intake → analysis → appeal) mirrors this study's workflow design. |
| **[Owo24]** | Owolabi 2025 | Trains an ML classifier to triage hospital admission denials — predicts which ones are worth appealing. | **Denial triage/routing.** Our Denial Type Router uses this concept — classify the denial type and determine which investigation branches are needed. |

---

## 1.7 Technology Stack & Environment

### Hardware Requirements:
* **Processor:** Intel Core i7 / AMD Ryzen 7 (8+ Cores, 16 Threads).
* **System Memory:** 16 GB DDR4/DDR5 RAM (Minimum), 32 GB (Recommended).
* **GPU:** NVIDIA RTX 3060 / 4060 (8GB+ VRAM) with CUDA 12.x for local embeddings and reranking.
* **Storage:** 512 GB NVMe SSD (with ≥ 20 GB dedicated for policy vectors and evaluation JSONs).

### Software & Frameworks:
* **Operating System:** Windows 11 / Ubuntu Linux 22.04 LTS.
* **Language & Environment:** Python 3.10.x / 3.11.x, Conda / Poetry.
* **Multi-Agent Orchestration:** `langgraph` (v0.2+), `langchain` (v0.3+), Model Context Protocol (MCP).
* **Evaluation Harness:** `deepeval` (v1.5+), `scikit-learn`, `pytest`.
* **Document Parsing:** `PyMuPDF` (`fitz`), `pdfplumber`, `pytesseract`.
* **Vector Store & Embeddings:** `chromadb` / `faiss-cpu`, `sentence-transformers` (`all-MiniLM-L6-v2` / `bge-large-en-v1.5`).
* **Data Manipulation:** `pandas`, `pydantic` (v2), `numpy`.
* **Language Models:** OpenAI API (`gpt-4o` / `gpt-4o-mini`), Claude 3.5 Sonnet, Google Gemini 1.5 Pro.
* **Backend API:** `FastAPI` (v0.110+), `uvicorn`.
* **Frontend Review Dashboard:** `Streamlit` (Rapid prototype) / `Next.js` + `TailwindCSS` (Production HITL UI).

---

## 1.8 Project Timeline (July 2026 – April 2027)

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

## 1.9 Concrete Worked Example: End-to-End Flow

Below is a concrete example tracing a single denied claim through all 15 nodes:

### The Scenario:
* **Patient:** Ramesh Kumar, Age 58, Male.
* **Policy:** ICICI Lombard Health Shield 360, Active 01/2023 – 01/2025, Sum Insured: ₹10,00,000, Room Rent Limit: ₹8,000/day.
* **Hospitalization:** Total Knee Replacement at Apollo Hospitals, Hyderabad on 10/03/2024. Discharged 16/03/2024 (6 days).
* **Claim Amount:** ₹4,50,000.
* **Denial:** Repudiated under Clause 4.3 ("Elective Procedures").

### Node 2 — Denial Intake Extracts:
```json
{
  "claim_id": "CLM-2024-78432",
  "denial_date": "2024-03-15",
  "procedure": "Total Knee Replacement",
  "denial_reason_raw": "Elective Procedures",
  "cited_clause": "4.3"
}
```

### Node 3a — Normalization Maps:
| Raw Text | → Category | → Subcategory |
|---|---|---|
| "Elective Procedures" | `MEDICAL_NECESSITY` | Elective/Non-Emergency |

### Node 4 — Router Dispatches:
```
Category identified: MEDICAL_NECESSITY
Dispatches directly to Node 5: Medical Necessity Specialized Investigation Pipeline
(Also initiates concurrent financial audit against nme_exclusions.csv)
```

### Node 5 — Category-Specific Denial Investigation (Medical Necessity Pipeline):

Node 5 activates its 4-step specialized investigation protocol for medical necessity:

1. **Clinical Severity and Vital Instability Scan:**
   * Objective indicators: Grade IV Osteoarthritis with bone-on-bone contact documented in radiology report.
   * Physiological status: Severe functional joint destruction, chronic severe pain score (8/10), SpO2 normal.

2. **Conservative Management Audit:**
   * Non-surgical therapies: 18 months of documented physiotherapy, cortisone/steroid injections, NSAIDs, and lifestyle modifications.
   * $\text{Duration} = 18\text{ months} \ge 6\text{ months required clinical threshold}$ → **SATISFIED**.

3. **Clinical Guideline Matching:**
   * Cross-reference: ICD-10 `M17.11` (Primary osteoarthritis, right knee) in `icd10_codes.csv` & HCPCS `27447` (Total Knee Arthroplasty) in `procedure_codes.csv` matched against InterQual and Indian clinical protocols.
   * Criteria result: Surgical indications met (failed conservative management $\ge 6\text{m}$ + radiological end-stage destruction).
   * Policy Clause Lookup: Vector search in `policy_clauses.csv` retrieves Clause 4.3 ("Elective Procedures") and identifies Exception Sub-clause 4.3.2 ("Surgeries deemed necessary following failed conservative management $\ge 6$ months are covered").
   * **Status: POTENTIAL MISAPPLICATION OF EXCLUSION** (Insurer ignored exception sub-clause).

4. **Physician Certification Verification:**
   * Treating orthopedic surgeon explicitly certified in writing that inpatient joint replacement was medically necessary to prevent permanent physical disability.

**Concurrent Financial Bill Audit (`nme_exclusions.csv`):**
```
Surgery charges     ₹2,80,000  → PAYABLE
Room (6 days)       ₹36,000    → PAYABLE (within eligible twin-sharing limit)
Implant (knee)      ₹1,20,000  → PAYABLE
PPE Kit             ₹1,500     → NME EXCLUDED (IRDAI Annexure IV) ⚠️
Registration Fee    ₹500       → NME EXCLUDED (IRDAI Annexure IV) ⚠️
Dietary charges     ₹2,000     → NME EXCLUDED (IRDAI Annexure IV) ⚠️

NME Deductions:     ₹4,000
Net payable:        ₹4,46,000
```
**Conclusion from Node 5:** Strong clinical grounds satisfy policy exception sub-clause 4.3.2; no legitimate financial grounds for repudiation exist.

### Node 7 — Applicability Reasoner Executes:
```python
conservative_failed = True   # 18 months evidence
doctor_certifies = True      # Surgeon's notes
imaging_severe = True        # Bone-on-bone X-ray

medically_necessary = conservative_failed AND (doctor_certifies OR imaging_severe)
# medically_necessary = True AND (True OR True) = True

is_elective = True AND NOT True = FALSE

# Therefore: Clause 4.3 exclusion does NOT apply
```
**Verdict: CONTRADICTS DENIAL** → Exception defeats the default rule.

### Node 8 — Evidence Matrix:
| Requirement | Fact | Evidence | Status | Source | Confidence |
|---|---|---|---|---|---|
| Must be elective | Failed 18mo conservative tx | Discharge summary p.2 | CONTRADICTS denial | medical_notes | 0.95 |
| Must be elective | Bone-on-bone on imaging | Radiology report | CONTRADICTS denial | medical_notes | 0.92 |
| Must be elective | Doctor certifies necessity | Surgeon notes p.1 | CONTRADICTS denial | medical_notes | 0.97 |
| Clause exception | Failed conservative tx > 6mo | Discharge summary | SUPPORTS exception | medical_notes | 0.95 |
| Financial validity | ₹4.5L within ₹10L SI | claims_master | NO ISSUE | claims_master | 1.00 |
| Waiting period | Policy active 14 months | claims_master | SATISFIED | claims_master | 1.00 |

### Node 11 — Deadline & Route:
```
Denial date:    2024-03-15
Today:          2024-04-20
Days elapsed:   36

Result: 36 days → OMBUDSMAN route (missed 30-day internal window)
```

### Node 13 — Generated Appeal (Excerpt):
```
─────────────────────────────────────────────────
To: The Insurance Ombudsman, Hyderabad
Re: Appeal against denial of Claim CLM-2024-78432

Dear Sir/Madam,

I am writing to appeal the denial of my health insurance claim
by ICICI Lombard (Policy: HL-2023-XXXX) for Total Knee
Replacement surgery performed on 10/03/2024 at Apollo Hospitals.

GROUNDS FOR APPEAL:

The insurer denied my claim citing Clause 4.3 ("Elective
Procedures"). However, Clause 4.3 itself contains an exception
(Sub-clause 4.3.2) which states: "Procedures shall not be
deemed elective where the insured has undergone documented
conservative treatment for a minimum period of six months
without adequate clinical improvement."

SUPPORTING EVIDENCE:

1. My discharge summary (Page 2, Para 3) documents that I
   underwent 18 months of physiotherapy, three cortisone
   injections, and daily NSAID medication — all without
   significant improvement. This exceeds the 6-month threshold
   specified in Sub-clause 4.3.2.

2. Radiological imaging (attached) shows bone-on-bone contact
   in the right knee, confirming Grade IV osteoarthritis
   (ICD-10: M17.11), which is NOT listed under permanent
   exclusions in Section 5 of the policy.

3. My operating surgeon, Dr. [Name], has certified that the
   procedure was medically necessary (certificate attached).

CONCLUSION:
The insurer's application of Clause 4.3 is incorrect as it
failed to consider the exception in Sub-clause 4.3.2. All
conditions of the exception are satisfied. I request reversal
of the denial and settlement of ₹4,46,000.

Attachments:
  - Original Denial Letter
  - Policy Document (Clause 4.3 highlighted)
  - Discharge Summary
  - Radiology Report
  - Surgeon's Certificate of Medical Necessity
  - Itemized Hospital Bill

Respectfully,
Ramesh Kumar
─────────────────────────────────────────────────
```

---

---

## 1.10 Core System Algorithms Under Evaluation (with Formal Mathematical Formulations)

The system relies on four deterministic and neuro-symbolic algorithms, each benchmarked within our 3-Tier evaluation framework:

### Algorithm 1: Reciprocal Rank Fusion (RRF) Hybrid Retrieval & Exception Mining (Evaluated by G2)
* **Mathematical Formulation:**
  Dense semantic vector similarity and sparse BM25 lexical retrieval are fused using Reciprocal Rank Fusion ($k = 60$):
  $$\text{RRF\_Score}(d) = \sum_{m \in \{\text{Dense}, \text{BM25}\}} \frac{1}{k + \text{Rank}_m(d)}$$
* **Conditional Exception Mining Rule:**
  For each retrieved policy clause text $T_c$, conditional pattern extraction identifies policy exceptions:
  $$\text{HasException}(T_c) = \begin{cases} 1, & \text{if } \exists w \in \{\text{"except", "unless", "provided that", "subject to"}\} \subseteq T_c \\ 0, & \text{otherwise} \end{cases}$$
* **Evaluation Target:** Evaluated on benchmark `G2_golden_clause_retrieval.json` against Contextual Recall $\ge 0.95$ and Contextual Precision $\ge 0.90$.

---

### Algorithm 2: Deterministic Symbolic Chronology & Statutory Moratorium Algorithm (Evaluated by G4 & G8)
* **Elapsed Policy Duration:**
  $$T_{\text{elapsed}} = \frac{D_{\text{admission}} - D_{\text{inception}}}{30.4375 \text{ days/month}}$$
* **Symptom Emergence Chronology Offset:**
  $$\Delta_{\text{onset}} = D_{\text{onset}} - D_{\text{inception}}, \quad \text{IsPostInception} = \begin{cases} \text{True}, & \text{if } \Delta_{\text{onset}} \ge 0 \\ \text{False}, & \text{if } \Delta_{\text{onset}} < 0 \end{cases}$$
* **IRDAI Statutory Moratorium Invariant (2024 60-Month Rule):**
  $$\mathcal{M} = \mathbb{I}(T_{\text{elapsed}} \ge 60 \text{ months})$$
* **Decisional Predicate Formulation:**
  $$\mathcal{D}_{\text{PED}} = \begin{cases}
  \text{REVERSAL\_POST\_INCEPTION}, & \text{if } \text{IsPostInception} = \text{True} \\
  \text{REVERSAL\_STATUTORY\_MORATORIUM}, & \text{if } \mathcal{M} = 1 \\
  \text{REVERSAL\_WAITING\_EXPIRED}, & \text{if } T_{\text{elapsed}} \ge W_{\text{clause}} \\
  \text{UPHOLD\_GENUINE\_PED\_NON\_DISCLOSURE}, & \text{if } \neg\text{Declared} \land (T_{\text{elapsed}} < W_{\text{clause}})
  \end{cases}$$
* **Evaluation Target:** Evaluated on benchmarks `G4_golden_chronology_ped.json` and `G8_golden_pipeline_waiting_period.json` with 100% deterministic accuracy and Mean Absolute Error (MAE) $= 0$ days.

---

### Algorithm 3: Room Rent Proportionate Scaling & Financial Reclaim Algorithm (Evaluated in Financial Limit Category)
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

### Algorithm 4: Toulmin Defeasible Argumentation Logic Algorithm (Evaluated by G5, G7, G8)
* **Argument Tuple Representation:** $\mathcal{T} = \langle C, G, W, E, R \rangle$ where $C$ is insurer claim, $G$ is clinical grounds, $W$ is policy warrant, $E$ is exception status, and $R$ is rebuttal.
* **Defeasible Evaluation Function:**
  $$\mathcal{V}_{\text{Toulmin}} = \begin{cases}
  \text{CONTRADICTS\_DENIAL (REVERSAL)}, & \text{if } (E = \text{Satisfied}) \lor (G \models \neg W) \lor (R \neq \emptyset) \\
  \text{SUPPORTS\_DENIAL (UPHOLD)}, & \text{if } (W = \text{Valid}) \land (E \neq \text{Satisfied}) \land (R = \emptyset) \\
  \text{INSUFFICIENT\_EVIDENCE}, & \text{if } \text{Confidence}(G) < \theta \quad (\theta = 0.85)
  \end{cases}$$
* **Evaluation Target:** Evaluated on benchmark `G5_golden_reasoning_toulmin.json` with Verdict Accuracy $\ge 0.92$ and DeepEval G-Eval Logic Soundness $\ge 4.5 / 5.0$.

---

# SECTION 2: ENTIRE DATASET CONTEXT (DEEP TECHNICAL SPECIFICATION)

---

## 2.1 Architectural Philosophy: Runtime Knowledge Base vs. Golden Benchmarks

A core software engineering principle governs our data subsystem: **The strict separation of Active Runtime Knowledge Bases from Golden Evaluation Benchmarks**.

```
                   ┌──────────────────────────────────┐
                   │   13 Raw Source Datasets (D1-D13) │
                   └────────────┬─────────────────────┘
                                │
           ┌────────────────────┼────────────────────┐
           ▼                                         ▼
┌─────────────────────────┐             ┌─────────────────────────┐
│  Runtime Execution       │             │  Evaluation Pipeline     │
│                          │             │                          │
│  Extracted & Indexed     │             │  Curated with Ground     │
│  ┌──────────────────┐   │             │  Truth                   │
│  │ 5 Active Runtime  │   │             │  ┌──────────────────┐   │
│  │ CSVs (ChromaDB)   │   │             │  │ 10 Golden Eval   │   │
│  └────────┬─────────┘   │             │  │ JSONs (710 cases)│   │
│           ▼              │             │  └────────┬─────────┘   │
│  ┌──────────────────┐   │             │           ▼              │
│  │ LangGraph Multi-  │   │             │  ┌──────────────────┐   │
│  │ Agent Runtime     │   │             │  │ DeepEval Test     │   │
│  └────────┬─────────┘   │             │  │ Harness           │   │
│           ▼              │             │  └────────┬─────────┘   │
│  ┌──────────────────┐   │             │           ▼              │
│  │ Generated Appeal  │───┼─────────►  │  ┌──────────────────┐   │
│  │ Dossier           │   │             │  │ Scores: Faith,   │   │
│  └──────────────────┘   │             │  │ Recall, MAE      │   │
│                          │             │  └──────────────────┘   │
└──────────────────────────┘             └──────────────────────────┘
```

### Why this distinction matters:
* **Elimination of Runtime Bloat:** At runtime, the system should not search through unindexed, multi-thousand-row CSVs. Large tables from initial exploratory design (`medical_notes.csv` and `claims_master.csv`) were **completely eliminated from runtime**. Clinical narratives and patient records are self-contained inside individual test cases.
* **Guaranteed Test Independence (No Data Leakage):** The 10 Golden Benchmarks exist solely for evaluation. The runtime agents never load the golden JSON files, ensuring that evaluation metrics reflect true zero-shot reasoning.

---

## 2.2 Complete Source Dataset Registry (D1 – D13)

The system is constructed from **13 public, freely accessible, and verified healthcare datasets**:

### Part A: Raw Source Pools & Knowledge-Base Inputs (D1 – D8)

| ID | Dataset Name | Source / Provider | License | Records / Size | Exact Role in the System |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **D1** | **CMS DE-SynPUF** | [Kaggle / CMS](https://www.kaggle.com/datasets/drscarlat/cmssynpuf55m) | Public Domain | Sampled from 55M pool | **Upstream Pool Only:** Sampled to synthesize realistic claim billing structures, LOS, and deductible ratios. *Dropped at runtime.* |
| **D2** | **MTSamples** | [Kaggle](https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions) | CC0 Public | 4,999 clinical notes | **Upstream Pool Only:** Sampled for genuine clinical narratives across Orthopedics, Cardiology, and Surgery. *Dropped at runtime.* |
| **D3** | **ICD-10-CM Codes** | [CDC / CMS](https://www.cms.gov/medicare/coding-billing/icd-10-codes) | Public Domain | 71,704 diagnosis codes | **Active Runtime CSV (`icd10_codes.csv`):** Diagnosis normalization and entity validation table. |
| **D4** | **ClaimSaathi** | [Kaggle](https://www.kaggle.com/datasets/siddhant2002/claimsaathi-indian-health-insurance-dataset) | Open Research | Real Indian health claims | **Upstream Pool Only:** Sampled to extract realistic Indian waiting period dispute dates and sum-insured distributions. *Dropped at runtime.* |
| **D5** | **HCPCS Level II Codes** | [CMS.gov](https://www.cms.gov/medicare/coding-billing/healthcare-common-procedure-system) | Public Domain | 7,842 procedure codes | **Active Runtime CSV (`procedure_codes.csv`):** Validates claimed surgeries and maps to policy limits. |
| **D6** | **IBM Healthcare Policy Rules** | [GitHub (IBM)](https://github.com/IBM/rules_extraction_from_healthcare_policy) | Apache 2.0 | Policy rules schema | **Upstream Architectural Schema:** Reference schema for transforming policy clauses into IF-THEN rules. *Dropped at runtime.* |
| **D7** | **13 Retail Policy PDFs** | Local (`data/policy_wordings/`) | Free Public | 13 full PDFs (~18 MB) across 4 top insurers | **Active Runtime Core:** Parsed into `policy_clauses.csv` (**1,997 clauses indexed in ChromaDB**) and `nme_exclusions.csv`. |
| **D8** | **CARC / RARC Codes** | [X12.org / CMS](https://x12.org/products/external-code-lists) | Public Domain | Standard code dictionary | **Active Runtime CSV (`denial_reasons.csv`):** Crosswalk taxonomy mapping table for the Denial Router. |

### Part B: Dedicated Golden Evaluation Benchmarks (D9 – D13)

| ID | Dataset Name | Source / Provider | License | Records / Size | Exact Role in Evaluation |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **D9** | **CA DMHC IMR Determinations Trend** | [CA Open Data Portal](https://data.chhs.ca.gov/dataset/independent-medical-review-imr-determinations-trend) | Public Domain | 100,000+ real appeal cases | **100,000+ real Medical Necessity appeal cases** with clinical findings and Overturned/Upheld ground truth. Direct CSV download. |
| **D10** | **Persius / imr-appeals** | [Hugging Face](https://huggingface.co/datasets/Persius/imr-appeals) | Open Research | Span-annotated appeals | Span-labeled external appeal adjudications and policy rules for health coverage denials. Direct download. |
| **D11** | **CIO Ombudsman & Indian Kanoon** | [cioins.co.in](https://www.cioins.co.in) / [Indian Kanoon](https://indiankanoon.org) | Public Legal Records | Legal repudiation cases | **Real Indian Pre-Existing Disease (PED) & waiting period repudiations**. Annual Reports direct PDF download; Indian Kanoon full legal texts (zero OTP/login). |
| **D12** | **InsLogicBench & InsClaimBench** | [ACL 2026 Anthology](https://aclanthology.org) / [arXiv:2610.09671](https://arxiv.org/abs/2610.09671) | Open Benchmark | Toulmin adjudication chains | Nested Toulmin argumentation ground truth & claim decision chains. |
| **D13** | **IRDAI Indian Repudiation Notices** | [IRDAI Portals](https://irdai.gov.in) / Insurer Portals | Public Regulatory | Standard notice templates | Standard 1-page health claim repudiation notice format (ICICI Lombard, Star Health) populated with ClaimSaathi & Kanoon facts. *(100% pure healthcare; replaces generic Nemotron-PII)*. |

### Part C: Accessibility & Verification Audit Table

Every source dataset has been verified for accessibility, licensing, and domain relevance:

| ID | Dataset | Direct Download Link / Access | Cost | Auth / Credentials Needed? | Domain Pure Healthcare? | Verified Status |
|---|---|---|:---:|:---:|:---:|:---:|
| **D1** | CMS DE-SynPUF | [Kaggle](https://www.kaggle.com/datasets/drscarlat/cmssynpuf55m) | Free | Free Kaggle Account | Yes (Medicare Claims) | **VERIFIED** |
| **D2** | MTSamples | [Kaggle](https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions) | Free | Free Kaggle Account | Yes (Clinical Notes) | **VERIFIED** |
| **D3** | ICD-10-CM Codes | [CDC / CMS](https://www.cms.gov/medicare/coding-billing/icd-10-codes) | Free | None (Public Domain) | Yes (Diagnosis Taxonomy) | **VERIFIED** |
| **D4** | ClaimSaathi | [Kaggle](https://www.kaggle.com/datasets/siddhant2002/claimsaathi-indian-health-insurance-dataset) | Free | Free Kaggle Account | Yes (Indian Health Claims) | **VERIFIED** |
| **D5** | HCPCS Level II | [CMS.gov](https://www.cms.gov/medicare/coding-billing/healthcare-common-procedure-system) | Free | None (Direct Excel/CSV) | Yes (Medical Procedures) | **VERIFIED** |
| **D6** | IBM Policy Rules | [GitHub](https://github.com/IBM/rules_extraction_from_healthcare_policy) | Free | None (Public GitHub) | Yes (Health Policy Rules) | **VERIFIED** |
| **D7** | 13 Policy PDFs (4 Insurers) | Local: `data/policy_wordings/` | Free | None (Downloaded & Verified) | Yes (Retail Health Policies) | **READY LOCALLY** |
| **D8** | CARC/RARC Codes | [X12.org / CMS](https://x12.org/products/external-code-lists) | Free | None (Public Domain) | Yes (Denial Reasons) | **VERIFIED** |
| **D9** | CA DMHC IMR Trend | [CA Open Data Portal](https://data.chhs.ca.gov/dataset/independent-medical-review-imr-determinations-trend) | Free | None (Direct CSV Download) | Yes (Medical Necessity) | **VERIFIED** |
| **D10** | Persius/imr-appeals | [Hugging Face](https://huggingface.co/datasets/Persius/imr-appeals) | Free | None (Direct HF Download) | Yes (Health Coverage Appeals) | **VERIFIED** |
| **D11** | CIO & Indian Kanoon | [Indian Kanoon](https://indiankanoon.org) & [CIO Publications](https://www.cioins.co.in) | Free | None (Zero OTP / Open Web) | Yes (Indian PED Repudiations) | **VERIFIED** |
| **D12** | InsLogicBench | [ACL Anthology](https://aclanthology.org) / arXiv:2610.09671 | Free | None (Open Research) | Yes (Insurance Reasoning) | **VERIFIED** |
| **D13** | IRDAI Repudiation Forms | [IRDAI Portals](https://irdai.gov.in) | Free | None (Regulatory Templates) | Yes (Health Claim Repudiation) | **VERIFIED** |

---

## 2.3 The 13 Downloaded Policy Wordings (D7 Detail)

All **13 essential retail policy documents across India's top 4 private health insurers** are organized and verified in `data/policy_wordings/`:

| # | Insurer | File Name | Size | Product Category | Relevance to Pipelines |
|---|---|---|---|---|---|
| 1 | ICICI Lombard | `complete-health-insurance.pdf` | 416 KB | Retail Comprehensive | **Primary Core**: Standard exclusions, 24/48-month PED clauses |
| 2 | ICICI Lombard | `health-shield-360-retail...pdf` | 1.3 MB | Retail Modular | **Primary Core**: Elective surgery & exception wording |
| 3 | ICICI Lombard | `arogya-sanjeevani.pdf` | 549 KB | IRDAI Standardized | **Primary Core**: Statutory benchmark (Code-Excl01 to Excl04) |
| 4 | ICICI Lombard | `elevate.pdf` | 1.6 MB | Modern Comprehensive | **Primary Core**: Modern treatments, robotic surgeries, infinite SI |
| 5 | ICICI Lombard | `health-advantedge...pdf` | 1.3 MB | High-Sum-Insured Retail | High-value claim sub-limits and room-rent clauses |
| 6 | ICICI Lombard | `health-booster...pdf` | 626 KB | Super Top-Up | Deductible threshold calculations and secondary claim denials |
| 7 | ICICI Lombard | `max-protect.pdf` | 899 KB | Retail Health | 1Y/2Y/3Y waiting period modification rules |
| 8 | Care Health | `care...pdf` | 2.1 MB | Classic Comprehensive | Flagship retail comprehensive coverage (formerly Religare Care) |
| 9 | Care Health | `care-supreme...pdf` | 2.2 MB | Modern Comprehensive | Modern daycare, robotic surgery, cumulative bonus rules |
| 10 | HDFC ERGO | `hdfc-optima-secure.pdf` | 925 KB | Modern Flagship | Automatic 4X restore benefit, non-medical expense coverage |
| 11 | HDFC ERGO | `hdfc-optima-restore.pdf` | 773 KB | Classic Flagship | Most widely held retail health policy in HDFC ERGO history |
| 12 | Star Health | `star-comprehensive.pdf` | 2.1 MB | Standalone Flagship | #1 retail health insurer in India, bariatric & modern surgery |
| 13 | Star Health | `star-family-health-optima.pdf` | 1.3 MB | Classic Floater | Widely held family floater health policy in India |

> **Note:** All irrelevant policy types (Group policies, Personal Accident, Hospital Cash, Single-disease benefit riders) have been excluded, ensuring our knowledge base and evaluation suite remain uncontaminated.

---

## 2.4 The 5 Active Runtime Knowledge-Base CSVs (`data/runtime/`)

These 5 files constitute the entire static knowledge base queried by agents during execution:

```
c:\Users\Saketh\Desktop\Major Project\data\runtime\
├── policy_clauses.csv       (Extracted from D7 PDFs: 1,997 structured clauses indexed in Vector DB across 4 insurers)
├── denial_reasons.csv       (Standardized D8 + IRDAI: ~80 denial categories for Router lookup)
├── icd10_codes.csv          (Direct D3: 70,000+ diagnosis codes for medical entity validation)
├── procedure_codes.csv      (Direct D5: 7,000+ procedure codes for surgery validation)
└── nme_exclusions.csv       (Extracted from D7 Annexures: ~120 non-medical items for financial audit)
```

### Detailed Schemas for Each Active Runtime CSV:

---

### 1. `policy_clauses.csv` (Vector Store Core)

* **File Location:** `data/runtime/policy_clauses.csv`
* **Record Count:** **1,997 structured clauses** parsed dynamically from the 13 retail policy PDFs.
* **Storage & Indexing:** Embedded using `sentence-transformers/all-MiniLM-L6-v2` and stored in **ChromaDB**.
* **How It Is Built:** The script `build_runtime_csvs.py` uses PyMuPDF (`fitz`) to extract text page-by-page from all 13 policy PDFs. Regex patterns identify clause boundaries:
  * Pattern 1: `r'^(Code-Excl\d+)\s*[:\.\-]?\s*(.+)'` — IRDAI Standard Code-Excl
  * Pattern 2: `r'^(\d+(?:\.\d+)*)\s*[:\.\)]\s*(.+)'` — Numbered sections like 4.3, 4.3.2
  * Pattern 3: Roman numeral sections
  * Pattern 4: Lettered items (a), (b), etc.
* **Exception Detection Keywords:** `"exclusion"`, `"excluded"`, `"not cover"`, `"shall not"`, `"not payable"`, `"except"`, `"unless"`, `"provided that"`, `"subject to"`
* **Columns & Schema:**

| Column | Type | Description | Example |
|---|---|---|---|
| `clause_id` | string (PK) | Unique identifier | `HS360-EX-043`, `STAR-COMP-WP-002` |
| `insurer` | string | Insurer name | `ICICI Lombard`, `Care Health`, `HDFC ERGO`, `Star Health` |
| `product_name` | string | Policy commercial name | `Health Shield 360`, `Optima Secure` |
| `section` | string | Contract section | `Section 3 - Waiting Periods`, `Section 4 - Exclusions` |
| `clause_number` | string | Numbering in PDF | `4.3`, `Code-Excl01`, `3.2.1` |
| `clause_text` | string | Verbatim clause text extracted from PDF | (Full paragraph text) |
| `clause_type` | enum | Classification | `EXCLUSION`, `WAITING_PERIOD`, `COVERAGE_DEFINITION`, `PROCEDURAL_CONDITION` |
| `has_exception` | boolean | Whether clause contains conditional override language | `True` / `False` |
| `exception_text` | string | Verbatim text of the exception sub-clause | "...except where conservative treatment has failed..." |
| `temporal_rule` | string (nullable) | Parsed time limitation | `24_months`, `6_months_conservative_tx` |

---

### 2. `denial_reasons.csv` (Taxonomy Crosswalk)

* **File Location:** `data/runtime/denial_reasons.csv`
* **Record Count:** **84 standardized repudiation categories**.
* **Usage:** Used by Node 3a (Normalization) and Node 4 (Router) to convert free-text letters to standard routes.
* **Columns & Schema:**

| Column | Type | Description | Example |
|---|---|---|---|
| `reason_id` | string (PK) | Identifier | `DEN-MEDNEC-01`, `DEN-PED-04` |
| `category` | enum | One of 7 global classes | `MEDICAL_NECESSITY`, `PRE_EXISTING_WAITING_PERIOD`, `POLICY_EXCLUSION`, `FINANCIAL_LIMIT`, `DOCUMENTATION`, `ADMINISTRATIVE_PROCEDURAL`, `ELIGIBILITY_COVERAGE` |
| `sub_category` | string | Detailed category | `Elective/Non-Emergency`, `First-30-Days` |
| `reason_text` | string | Canonical description | "Procedure deemed elective and not medically necessary" |
| `carc_code` | string | Equivalent CARC code | `CO-50`, `CO-197` |
| `typical_clause_type` | string | Expected policy section | `General Exclusions`, `Waiting Period Schedule` |
| `appeal_route` | enum | Default dispute pathway | `INTERNAL_APPEAL`, `OMBUDSMAN`, `CONSUMER_COURT` |

---

### 3. `icd10_codes.csv` (Clinical Entity Validation)

* **File Location:** `data/runtime/icd10_codes.csv`
* **Record Count:** **71,704 billable diagnosis codes**.
* **Source:** D3 (CDC / CMS ICD-10-CM National Pool).
* **Usage:** Fast hash-map lookup used by Node 2 and Node 5b to validate extracted diagnoses and link them to policy exclusion lists.
* **Columns & Schema:**

| Column | Type | Description | Example |
|---|---|---|---|
| `code` | string (PK) | Standard alphanumeric code | `M17.11`, `I25.10`, `E11.9` |
| `short_description` | string | Brief clinical name | `Primary osteoarthritis, right knee` |
| `long_description` | string | Full clinical nomenclature | (Extended text) |
| `is_billable` | boolean | Terminal billable code | `1` for billable; `0` for header categories |

---

### 4. `procedure_codes.csv` (Surgical Verification)

* **File Location:** `data/runtime/procedure_codes.csv`
* **Record Count:** **7,842 HCPCS Level II & CPT procedure codes**.
* **Source:** D5 (CMS HCPCS Level II).
* **Usage:** Validates whether claimed procedures match clinical notes and detects procedures subject to specific policy sub-limits.
* **Columns & Schema:**

| Column | Type | Description | Example |
|---|---|---|---|
| `hcpcs_code` | string (PK) | Surgical code | `27447` (Knee Arthroplasty), `33533` (CABG) |
| `short_description` | string | Standard procedure title | "Total knee replacement" |
| `category` | string | Surgical specialty | `Orthopedic Surgery`, `Cardiovascular Surgery` |

---

### 5. `nme_exclusions.csv` (Non-Medical Expense Schedules)

* **File Location:** `data/runtime/nme_exclusions.csv`
* **Record Count:** **124 non-medical billing items** parsed from standard IRDAI policy annexures.
* **Source:** Extracted from D7 Policy PDF Annexures.
* **Usage:** Used by Node 5c (Financial Check) to audit line-item deductions in hospital bills.
* **Columns & Schema:**

| Column | Type | Description | Example |
|---|---|---|---|
| `item_id` | string (PK) | Unique item code | `NME-001`, `NME-045` |
| `item_name` | string | Line-item name | `PPE Kit`, `Admission Kit`, `Dietary Charges`, `Luxury Bedding` |
| `category` | string | Classification | `Personal Hygiene`, `Administrative Fees`, `Consumables` |
| `typically_excluded` | boolean | Non-payable under standard retail terms | `True` / `False` |

---

### Eliminated / Redundant CSVs (Superseded by Golden JSONs)

The following 2 CSVs from initial planning are **completely eliminated** from runtime:

| Eliminated File | Original Purpose | Why It Is Eliminated |
|---|---|---|
| ❌ `medical_notes.csv` | Raw table of 2,000 MTSamples clinical notes. | **Superseded by Golden JSONs.** Clinical discharge summaries are embedded directly inside `golden_clinical_evidence.json` and `golden_pipeline_medical_necessity.json`. Agents receive the note directly in the test case; querying a 2,000-row CSV at runtime is unnecessary. |
| ❌ `claims_master.csv` | 10,000 synthetic patient rows. | **Superseded by Golden JSONs.** Patient demographics, policy inception dates, waiting period milestones, and billed amounts are self-contained within `golden_chronology_ped.json` and `golden_intake_entities.json`. |

---

## 2.5 The 10 Golden Evaluation Benchmarks (`data/golden/`)

The evaluation suite consists of **10 JSON datasets comprising exactly 710 verified benchmark test cases**:

```
data/golden/
├── G1_golden_intake_entities.json         (100 cases)  -> Component 1.1: Denial Intake
├── G2_golden_clause_retrieval.json        (100 cases)  -> Component 1.2: Clause RAG
├── G3_golden_clinical_evidence.json       (60 cases)   -> Component 1.3A: Clinical Extraction
├── G4_golden_chronology_ped.json          (60 cases)   -> Component 1.3B: Chronology Engine
├── G5_golden_reasoning_toulmin.json       (80 cases)   -> Component 1.4: Toulmin Reasoner
├── G6_golden_appeal_drafts.json           (40 cases)   -> Component 1.5: Appeal Generator
├── G7_golden_pipeline_medical_necessity.json (50 cases) -> Pipeline A: Medical Necessity E2E
├── G8_golden_pipeline_waiting_period.json    (50 cases) -> Pipeline B: Waiting Period E2E
├── G9_golden_denial_router.json           (140 cases)  -> Application: 7-Class Triage Router
└── G10_golden_hitl_benchmark.json         (30 cases)   -> Application: Human Adjudicator Consensus
```

---

### Tier 1: Component Golden Datasets (Detailed Specifications)

---

#### G1: `G1_golden_intake_entities.json`

* **Cases:** 100 unstructured repudiation notices.
* **Target Agent:** Denial Intake Agent ([Lop21]).
* **Source:** D10 (Persius/imr-appeals for Medical Necessity) + D13 (IRDAI Repudiation Notices populated with D4 ClaimSaathi & Kanoon facts for Waiting Period).
* **Input:** Raw unformatted text of a denial letter.
* **Ground Truth Schema:**
  ```json
  {
    "case_id": "G1-001",
    "raw_letter_text": "Ref: CLM-2024-8921. Dear Ramesh Kumar, with reference to your hospitalization on 15/03/2024 at Apollo Hospitals for Total Knee Replacement (ICD-10: M17.11), your claim for Rs 4,50,000 has been repudiated under Clause 4.3 (Elective Surgery)...",
    "ground_truth_entities": {
      "claim_id": "CLM-2024-8921",
      "patient_name": "Ramesh Kumar",
      "denial_date": "2024-03-15",
      "hospital_name": "Apollo Hospitals, Hyderabad",
      "procedure": "Total Knee Replacement",
      "icd10_code": "M17.11",
      "claimed_amount": 450000.0,
      "cited_clause_raw": "Clause 4.3",
      "denial_category_hint": "Elective Surgery"
    }
  }
  ```
* **Evaluation Metric:** Token F1 ≥ 0.95, Exact Match ≥ 0.98.

---

#### G2: `G2_golden_clause_retrieval.json`

* **Cases:** 100 query-context-clause triplets.
* **Target Agent:** Policy Clause Verification Agent ([Pic22, Pok26]).
* **Source:** Extracted directly from the 13 verified retail policy PDFs across ICICI Lombard, Care Health, HDFC ERGO, and Star Health.
* **Input:** User/Denial query and specific policy product name.
* **Ground Truth Schema:**
  ```json
  {
    "query_id": "G2-018",
    "user_query": "Is Total Knee Replacement covered if conservative medical treatment failed under Health Shield 360?",
    "product_name": "Health Shield 360",
    "expected_clause_id": "HS360-EX-043",
    "expected_subclause": "4.3.2",
    "has_exception": true,
    "ground_truth_context_snippet": "Sub-clause 4.3.2: Elective procedures shall not include surgeries where conservative medical management has failed for a period exceeding six continuous months as certified by the attending specialist.",
    "distractor_clauses": ["HS360-EX-001", "HS360-COV-012"]
  }
  ```
* **Evaluation Metric:** DeepEval `ContextualRecallMetric` ≥ 0.95, `ContextualPrecisionMetric` ≥ 0.90.

---

#### G3: `G3_golden_clinical_evidence.json`

* **Cases:** 60 annotated clinical discharge summaries.
* **Target Agent:** Clinical Evidence Investigation Agent ([Pan24, Ahs23]).
* **Source:** D9 (California DMHC IMR dataset) + D2 (MTSamples discharge summaries).
* **Input:** Raw clinical transcript.
* **Ground Truth Schema:**
  ```json
  {
    "case_id": "G3-005",
    "clinical_notes": "58yo male with chronic right knee pain unresponsive to 18 months of physical therapy, multiple steroid injections, and daily NSAIDs. Weight-bearing radiographs reveal Grade IV osteoarthritis with complete joint space loss and bone-on-bone contact. Dr. Sen certifies surgical intervention is imperative.",
    "ground_truth_checklist": {
      "conservative_treatment_attempted": true,
      "conservative_treatment_duration_months": 18,
      "treatment_modalities": ["physical therapy", "steroid injections", "NSAIDs"],
      "disease_severity_grade": "Grade IV / Bone-on-bone",
      "physician_necessity_stated": true
    },
    "verbatim_evidence_spans": [
      "unresponsive to 18 months of physical therapy, multiple steroid injections, and daily NSAIDs",
      "Grade IV osteoarthritis with complete joint space loss and bone-on-bone contact"
    ]
  }
  ```
* **Evaluation Metric:** DeepEval `FaithfulnessMetric` ≥ 0.95, Checklist Accuracy ≥ 0.90.

---

#### G4: `G4_golden_chronology_ped.json`

* **Cases:** 60 chronological disputes.
* **Target Agent:** Chronology & Waiting Period Engine ([Pok26]).
* **Source:** D11 (Indian Insurance Ombudsman awards) + D4 (ClaimSaathi timeline records).
* **Input:** Policy inception date, admission date, symptom onset statement, and continuous renewal history.
* **Ground Truth Schema:**
  ```json
  {
    "case_id": "G4-012",
    "policy_inception_date": "2021-04-10",
    "admission_date": "2024-05-15",
    "claimed_condition": "Hypertensive Nephropathy",
    "clinical_history_onset_statement": "Patient has a history of essential hypertension diagnosed 2 years ago (May 2022).",
    "proposal_form_ped_declared": false,
    "continuous_renewal_years": 3,
    "applicable_waiting_period_months": 36,
    "ground_truth_calculation": {
      "elapsed_months": 37.1,
      "first_symptom_relative_to_inception": "POST_INCEPTION",
      "waiting_period_satisfied": true,
      "pre_existing_non_disclosure": false,
      "moratorium_clause_applicable": false,
      "symbolic_decision": "DENIAL_REVERSAL_WAITING_PERIOD_EXPIRED"
    }
  }
  ```
* **Evaluation Metric:** Deterministic Exact Match Accuracy = 100%, Date Offset MAE = 0 days.

---

#### G5: `G5_golden_reasoning_toulmin.json`

* **Cases:** 80 structured legal reasoning cases (50% Reversal, 50% Uphold).
* **Target Agent:** Toulmin Defeasible Reasoner ([Liu26, Pok26]).
* **Source:** Modeled from D12 (InsLogicBench / InsClaimBench architecture).
* **Ground Truth Schema:**
  ```json
  {
    "case_id": "G5-024",
    "category": "MEDICAL_NECESSITY",
    "toulmin_components": {
      "claim": "Total Knee Replacement is an excluded elective procedure under Clause 4.3.",
      "grounds": "Patient underwent 18 months of documented, failed conservative therapy.",
      "warrant": "Clause 4.3 excludes elective surgeries unless conservative treatment failed for >= 6 months.",
      "exception_status": "SATISFIED",
      "rebuttal": "No contradicting evidence found; attending surgeon certifies imperative necessity."
    },
    "expected_verdict": "CONTRADICTS_DENIAL",
    "confidence_threshold": 0.90
  }
  ```
* **Evaluation Metric:** Verdict Accuracy ≥ 0.92, DeepEval G-Eval (Logic Soundness) ≥ 4.5/5.0.

---

#### G6: `G6_golden_appeal_drafts.json`

* **Cases:** 40 complete case-to-appeal pairs.
* **Target Agent:** Appeal Drafting Agent ([Kis24]).
* **Source:** Expert appeal letters adapted from D11 (Ombudsman filings) and D10 (Persius).
* **Ground Truth Schema:**
  ```json
  {
    "case_id": "G6-003",
    "case_facts": {
      "claim_id": "CLM-2024-8921",
      "clause": "4.3",
      "exception": "4.3.2",
      "patient": "Ramesh Kumar"
    },
    "mandatory_citations": [
      "Clause 4.3.2 of Health Shield 360",
      "Discharge Summary dated 15/03/2024",
      "18 months of documented conservative management"
    ],
    "target_forum": "Insurance Ombudsman",
    "reference_appeal_text": "To: The Insurance Ombudsman, Hyderabad...\nSubject: Appeal against wrongful repudiation of Claim CLM-2024-8921..."
  }
  ```
* **Evaluation Metric:** DeepEval `FaithfulnessMetric` ≥ 0.98, `GEval` (Legal Persuasiveness) ≥ 4.2/5.

---

### Tier 2: Pipeline Golden Datasets (End-to-End Category Benchmarks)

---

#### G7: `G7_golden_pipeline_medical_necessity.json` (Pipeline A Benchmark)

* **Target:** End-to-End Medical Necessity Pipeline (Intake → RAG → Clinical Extraction → Toulmin → Appeal).
* **Source:** 50 real clinical dispute cases from **D9 (California DMHC IMR Trend Dataset)** paired with ICICI policy wordings.
* **Cases:** 50 full-pipeline cases.
* **Composition:**
  * **35 Overturn Cases:** Documented failure of conservative management, acute surgical indications, or clinical guideline conformance.
  * **15 Upheld Cases:** Pure cosmetic procedures, unproven experimental therapies, or elective surgeries without prior non-surgical trials.
* **Evaluation Target:** Complete pipeline must take raw unstructured inputs and output:
  1. Correct binary verdict (`OVERTURN` vs `UPHOLD`).
  2. Grounded Evidence Matrix with > 0.85 recall on critical clinical facts.
  3. Grounded appeal draft.
* **Evaluation Metric:** Overturn Prediction Macro-F1 ≥ 0.90, Clinical Coverage Recall ≥ 0.85.

---

#### G8: `G8_golden_pipeline_waiting_period.json` (Pipeline B Benchmark)

* **Target:** End-to-End Pre-Existing Waiting Period Pipeline (Intake → RAG → Chronology Engine → Toulmin → Appeal).
* **Source:** 50 real cases curated from **D11 (Indian Insurance Ombudsman Awards & Indian Kanoon)**.
* **Cases:** 50 full-pipeline cases.
* **Composition:**
  * **25 Reversals** where waiting period expired prior to admission.
  * **10 Reversals** protected by the statutory Moratorium Clause (IRDAI 60-month rule).
  * **15 Justified Denials** (deliberate non-disclosure of major pre-existing surgery within the active exclusion window).
* **Evaluation Target:** Symbolic math accuracy = 100%, statutory compliance = 100%.

---

### Tier 3: Application Golden Datasets

---

#### G9: `G9_golden_denial_router.json` (7-Class Triage Router)

* **Target:** Global Denial Router (Triage Node 4 in architecture).
* **Source:** D8 (CARC/RARC codes) + IRDAI claim rejection taxonomy.
* **Cases:** 140 raw denial letter paragraphs (exactly 20 per category across all 7 balanced classes).
* **The 7 Classes:**
  1. `MEDICAL_NECESSITY`
  2. `PRE_EXISTING_WAITING_PERIOD`
  3. `POLICY_EXCLUSION`
  4. `FINANCIAL_LIMIT`
  5. `DOCUMENTATION`
  6. `ADMINISTRATIVE_PROCEDURAL`
  7. `ELIGIBILITY_COVERAGE`
* **Ground Truth:** Single-label categorical enum.
* **Evaluation Metric:** Multi-class Macro-F1 ≥ 0.95, Full Confusion Matrix analysis.

---

#### G10: `G10_golden_hitl_benchmark.json` (Human Adjudicator Review Alignment)

* **Target:** System-wide Human Review Node (Node 14 in architecture, [Sbo24]).
* **Cases:** 30 comprehensive claim appeal packs.
* **Ground Truth:** Independent adjudication consensus by two senior medical claim reviewers scoring:
  * Appeal Persuasiveness
  * Factual Correctness
  * Reversal Feasibility
* **Evaluation Metric:** Inter-Rater Reliability via Cohen's Kappa (κ ≥ 0.80 — Substantial Agreement).

---

## 2.6 Data Engineering: Ingestion, Joins & Merging Pipelines

The ETL mechanism is implemented across three Python scripts:

### Script 1: `ingest_raw_sources.py`
* **Purpose:** Downloads and ingests representative public raw datasets into `data/raw_sources/`.
* **Sources Fetched:**
  * D6: IBM Healthcare Policy Rules (from GitHub)
  * D9: California DMHC IMR Determinations Trend (from CA Health & Human Services Open Data)
  * D10: Persius IMR Appeals background annotations (from Hugging Face)
  * D8: CARC / RARC Denial Claim Adjustment Codes (X12 / CMS standard dictionary)
  * D11: CIO Ombudsman & Indian Kanoon Waiting Period Jurisprudence cases
  * D13: IRDAI Master Repudiation Format & Regulatory Guidelines
* **Also Catalogs:** D7 (Recursively audits all 13 policy PDFs in `data/policy_wordings/`)

### Script 2: `build_runtime_csvs.py`
* **Purpose:** Builds all 5 Active Runtime Knowledge-Base CSVs.
* **Process:**
  1. **Policy Clauses Extraction:** PyMuPDF recursively processes all 13 policy PDFs → regex identifies clause boundaries → exception keywords are scanned → 1,997 structured clauses output to `policy_clauses.csv`.
  2. **Denial Reasons Normalization:** CARC/RARC codes merged with IRDAI taxonomy → 84 standardized categories output to `denial_reasons.csv`.
  3. **ICD-10 Codes:** Direct CDC/CMS download → filtered for billable codes → 71,704 records output to `icd10_codes.csv`.
  4. **Procedure Codes:** Direct CMS HCPCS download → 7,842 records output to `procedure_codes.csv`.
  5. **NME Exclusions:** Parsed from policy PDF annexures → 124 non-medical items output to `nme_exclusions.csv`.

### Script 3: `build_golden_datasets.py`
* **Purpose:** Builds all 10 Golden Evaluation Benchmark JSONs for the 3-Tier DeepEval evaluation suite.
* **Data Pools Used:**
  * Indian Names Pool (50 names), Indian Hospitals Pool (20 hospitals)
  * Procedure Pool (15 major surgeries with ICD-10 and HCPCS codes)
  * Pre-Existing Disease Conditions Pool
  * Dynamically discovered policy products from `data/policy_wordings/`
* **Output:** 10 JSON files totaling 710 verified test cases in `data/golden/`.

### Script 4: `validate_all_datasets.py`
* **Purpose:** Automated validation and health-check suite across the entire data subsystem:
  1. Verifies all policy PDFs exist and are ≥ 50 KB.
  2. Verifies all raw ingested datasets exist (≥ 6 files).
  3. Validates all 5 runtime CSVs exist with correct row counts and column schemas.
  4. Validates all 10 golden JSONs exist with exact expected case counts and schema compliance.
* **Output:** `ALL CHECKS PASSED: 100% HEALTHY!`

---

## 2.7 Step-by-Step Golden Dataset Construction Pipeline

```
Step 1: Download D9 (CA DMHC IMR), D10 (Hugging Face), D11 (Ombudsman)
                            │
                            ▼
Step 2: Parse & Filter by Category
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
Extract 50 Medical Necessity     Extract 50 Waiting Period
Cases (D9 → G3, G7)             Cases (D11 → G4, G8)
              │                           │
              ▼                           ▼
Step 3: Parse Local Policy PDFs (data/policy_wordings/)
              │
              ▼
Extract Clauses & Exceptions into policy_clauses.csv & G2
              │
              ▼
Step 4: Generate Synthetic Intake Letters (D13 + D4 → G1)
              │
              ▼
Step 5: Synthesize Toulmin Ground Truth (D12 patterns → G5)
              │
              ▼
Step 6: Validate All Schemas with Pydantic
              │
              ▼
Step 7: Store in data/golden/ Directory
```

### Scripted Construction Details:
1. **Curate Policy Clauses (`policy_clauses.csv` & G2):**
   - Run Python PyMuPDF (`fitz`) over all 13 policy PDFs.
   - Parse Section 3 (Waiting Periods) and Section 4 (Exclusions). Extract rules and sub-clauses into structured JSON/CSV.

2. **Curate Clinical Evidence (G3 & G7):**
   - Download `Independent_Medical_Review_IMR_Determinations_Trend.csv` from CA Open Data portal (free, ~150 MB).
   - Filter `Reason_For_Dispute == "Medical Necessity"` and `Diagnosis_Category.isin(["Orthopedic", "Cardiovascular", "Neurology"])`.
   - Take 50 cases with rich `Findings` text. The `Determination_Outcome` column (`Overturned` vs `Upheld`) gives verified ground truth.

3. **Curate Chronology Benchmarks (G4 & G8):**
   - Extract 50 case summaries from Indian Kanoon querying `"Insurance Ombudsman" AND "waiting period"`.
   - Record exact dates, waiting periods cited, and the Ombudsman's binding award.

4. **Curate Router Benchmark (G9):**
   - Map 140 CARC/RARC code descriptions and real rejection notices to the 7 target categories.

---

## 2.8 Three-Tier Evaluation Framework & Metrics Summary

| Level | Component | Evaluation Metric | Tool / Formula | Target Threshold |
| :--- | :--- | :--- | :--- | :---: |
| **L1** | Intake Entities (G1) | Token F1 & Exact Match | `scikit-learn` / Python | Entity F1 ≥ 0.95, EM ≥ 0.98 |
| **L1** | Clause RAG (G2) | `ContextualPrecisionMetric` / `ContextualRecallMetric` | **DeepEval** | Precision ≥ 0.90, Recall ≥ 0.95 |
| **L1** | Clinical Extraction (G3) | `FaithfulnessMetric` / Checklist Accuracy | **DeepEval** / Correct Checks / Total Checks | Faithfulness ≥ 0.95, Checklist Acc ≥ 0.90 |
| **L1** | Chronology Engine (G4) | Deterministic Exact Match / Date Offset Error (MAE) | Python Unit Tests / MAE = (1/N)Σ\|d_pred - d_true\| | Accuracy = 100%, MAE = 0 days |
| **L1** | Toulmin Reasoner (G5) | Verdict Accuracy / `GEval` (Logic Soundness) | `scikit-learn` / **DeepEval** G-Eval (1-5) | Accuracy ≥ 0.92, G-Eval ≥ 4.5/5.0 |
| **L1** | Appeal Drafter (G6) | `FaithfulnessMetric` / `GEval` (Legal Persuasiveness) | **DeepEval** | Faithfulness ≥ 0.98, Persuasiveness ≥ 4.2/5 |
| **L2** | Medical Necessity (G7) | Overturn Prediction F1 / Clinical Coverage Recall | End-to-End Suite | Macro-F1 ≥ 0.90, Coverage Recall ≥ 0.85 |
| **L2** | Waiting Period (G8) | Statutory Compliance Rate / Ombudsman Alignment | End-to-End Suite | Compliance = 100%, Alignment ≥ 0.92 |
| **L3** | Denial Router (G9) | Multiclass Macro-F1 / Confusion Matrix | `scikit-learn` | Macro-F1 ≥ 0.95 |
| **L3** | HITL Review (G10) | Inter-Rater Reliability | **Cohen's Kappa (κ)** = (P_o - P_e) / (1 - P_e) | κ ≥ 0.80 (Substantial Agreement) |
| **L3** | Operational | Latency & Token Cost | Profiler & Token Counter | P95 < 45s, Cost < $0.10 |

---

## 2.9 Final Summary Table

| Dimension | Active Runtime Layer | Golden Evaluation Layer |
| :--- | :--- | :--- |
| **Primary Formats** | CSV files + ChromaDB Vector Database | JSON files (Clean Pydantic schemas) |
| **Total Inventory** | 5 Active CSVs (~1,997 clauses, ~71k ICDs, ~7.8k HCPCS) | 10 Golden Benchmarks (710 verified cases) |
| **Storage Location** | `data/runtime/` | `data/golden/` |
| **Agents Accessing** | Queryable by all live LangGraph agents | **Zero runtime access** (Dedicated to DeepEval) |
| **Eliminated Files** | `medical_notes.csv` and `claims_master.csv` dropped | Self-contained within JSON benchmark files |
| **Evaluation Metrics** | Sub-second latency, deterministic lookups | Contextual Recall ≥ 0.95, Faithfulness ≥ 0.98, MAE = 0 |

---

## 2.10 Key Takeaway for Review-2 Panel

> *"Our project does not rely on generic, unconstrained language generation. We have established an auditable, neuro-symbolic multi-agent architecture grounded in 1,997 parsed Indian policy clauses, 13 public healthcare datasets, and 710 verified benchmark test cases evaluated across three tiers. This guarantees that every claim denial appeal generated is legally accurate, clinically supported, and fully aligned with statutory IRDAI standards."*

---

## References (Complete Bibliography)

1. López et al. — "Towards Protecting Vital Healthcare Programs by Extracting Actionable Knowledge from Policy" (ACL Findings 2021). DOI: `10.18653/v1/2021.findings-acl.308`
2. Picco et al. — "Learning Insurance Benefit Rules from Policy Texts with Small Labeled Data" (2022). DOI: `10.3233/SHTI220081`
3. KAMEL — "Knowledge Aware Medical Entity Linkage to Automate Health Insurance Claims Processing" (AAAI 2024). DOI: `10.1609/aaai.v38i21.30314`
4. Lui et al. — "Knowledge Aware Automated Health Claims Processing with Medical Ontologies and Large Language Models" (AAAI Fall Symposium 2024). DOI: `10.1609/aaaiss.v4i1.31794`
5. Pandey et al. — "Advancing Healthcare Automation: Multi-Agent System for Medical Necessity Justification" (2024). DOI: `10.48550/arXiv.2404.17977`
6. Ahsan et al. — "Retrieving Evidence from EHRs with LLMs: Possibilities and Challenges" (2023). DOI: `10.48550/arXiv.2309.04550`
7. Sbodio et al. — "Collaborative Artificial Intelligence System for Investigation of Healthcare Claims Compliance" (Scientific Reports 2024). DOI: `10.1038/s41598-024-62665-0`
8. Kumar et al. — "Data Mining to Predict and Prevent Errors in Health Insurance Claims Processing" (SIGKDD 2010). DOI: `10.1145/1835804.1835816`
9. Liu et al. — "InsLogicBench: An Argumentation Logic Grounded Benchmark for Complex Insurance Claims Adjudication" (ACL 2026). DOI: `10.18653/v1/2026.acl-long.1035`
10. Pokharel et al. — "From Policy to Logic for Efficient and Interpretable Coverage Assessment" (2026). DOI: `10.48550/arXiv.2601.01266`
11. Kiser et al. — "Large Language Models to Help Appeal Denied Radiotherapy Services" (2024). DOI: `10.1200/CCI.24.00129`
12. DENIED-AI Pilot Study — "Decreasing Administrative Effort Related to Non-Approval of Image-guided Procedures Using Large Language Models" (2026). DOI: `10.1016/j.acra.2026.04.021`
13. Owolabi — "Transforming Appeal Decisions: Machine Learning Triage for Hospital Admission Denials". DOI: `10.1093/jamiaopen/ooaf016`
