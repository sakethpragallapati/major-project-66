# Objective 02: Intelligent Intake and Multi-Agent Denial Triage

## 1. Goal

Take a raw repudiation letter (text or PDF) and produce two things:

1. A structured **case record**: claim ID, patient, insurer, product, policy number, dates, hospital, procedure, ICD-10 code, claimed amount, cited clause and the stated denial reason. The cited clause is resolved to a `clause_id` in the clause base.
2. A **triage decision**: one primary category from the seven-category taxonomy, any secondary categories, the closest standard denial reason (with CARC/RARC codes and the appeal route), a confidence score, and a flag for human review when the agents disagree. The decision names the Objective 03 investigation pipeline the case goes to next.

The seven categories are `MEDICAL_NECESSITY`, `PRE_EXISTING_WAITING_PERIOD`, `POLICY_EXCLUSION`, `FINANCIAL_LIMIT`, `DOCUMENTATION`, `ADMINISTRATIVE_PROCEDURAL` and `ELIGIBILITY_COVERAGE`.

## 2. Design rules

- **No leakage.** Runtime code reads only `data/runtime/*.csv`. The golden JSON files are read only by the evaluation scripts. Cue lists and the reason index are built from the taxonomy in `denial_reasons.csv` and from policy vocabulary, not from G1 or G7 text.
- **Deterministic first.** Every field and every vote can be traced to a regex match, a table row or a clause ID. An LLM agent is optional, opt-in through an environment variable, and is only one voter among several.
- **Abstain rather than guess.** Fields that are not found stay empty. Low-confidence triage is flagged for review.
- **Runs offline** on the installed stack: Python 3.11, pydantic 2, scikit-learn, RapidFuzz, PyMuPDF and LangGraph.

## 3. Architecture

```
letter (.txt / .pdf / .png / .jpg / .tiff / .webp)
   │
   ▼
[load]      PDF text layer by rows, or OCR (RapidOCR) with page-rotation and word-space repair;
            whitespace and unicode clean-up
   │
   ▼
[extract]   labelled-field parser ("Claim: ...", "Billed Amount: ...")
            + narrative patterns ("your claim for Rs ... under ... has been repudiated")
   │
   ▼
[normalize] dates → ISO, Indian amounts → float, ICD-10 checked against icd10_codes.csv,
            insurer/product matched against the clause base,
            cited clause resolved to clause_id (product + number + reason text)
   │
   ├──────────────┬──────────────────┬──────────────────┐   (parallel fan-out)
   ▼              ▼                  ▼                  ▼
[cue agent]   [reason agent]     [clause agent]     [LLM agent, optional]
 weighted      TF-IDF match to    category prior     few-shot JSON
 phrase cues   70 standard        from the cited     classification
 per category  denial reasons     clause's type
   │              │                  │                  │
   └──────────────┴────────┬─────────┴──────────────────┘
                           ▼
[supervisor]  weighted soft vote → primary + secondary categories,
              confidence, agreement, needs_human_review
                           ▼
[router]      dispatch plan: investigation pipeline, deterministic checks,
              runtime tables and documents each category needs
```

The graph is a LangGraph `StateGraph`. The same node functions run in a plain sequential runner when LangGraph is not installed, so tests do not depend on it.

## 4. Package layout

```
denial_ai/
  config.py          paths, agent weights, review thresholds, LLM settings
  schemas.py         pydantic models: IntakeEntities, ClauseMatch, AgentVote, TriageDecision, CaseState
  knowledge.py       loads the runtime CSVs once (clauses, ICD-10, denial reasons) and builds lookups
  intake/
    loader.py        text, PDF and image loading, with OCR for scans
    extractor.py     field extraction
    normalizer.py    dates, amounts, ICD-10, insurer/product, clause resolution
  triage/
    cues.py          category cue lexicon
    agents.py        CueAgent, ReasonMatchAgent, ClauseTypeAgent, LLMAgent (optional, OpenAI-compatible)
    supervisor.py    vote aggregation and review flag
    router.py        category → investigation pipeline plan
  graph.py           LangGraph wiring and the sequential fallback
  __main__.py        CLI: python -m denial_ai letter.txt [--json]
  api.py             FastAPI backend for the web interface
  web/index.html     web interface
evaluation/
  eval_intake.py     G1: per-field exact match, token F1, clause-ID accuracy
  eval_triage.py     G7: accuracy, macro-F1, per-class report, confusion matrix
tests/               unit tests, including letters in formats G1 does not use
```

## 5. Intake details

| Field | Approach |
|---|---|
| Letter type | `claim_denial`, or `proposal_rejection` when the insurer refuses a new policy ("unable to offer coverage", "Rejection of Proposal") and the letter names no claim |
| Claim ID | Patterns such as `CLM-YYYY-NNNN` and `CIR/2025/161218/1829414`, plus labelled forms ("Claim No", "Claim Intimation Number", "Pre-auth No", "CCN") |
| Application number | "Application No." / "Proposal No." on a proposal rejection |
| Patient name | "Dear Mr./Ms. X", "To: X", "Name of the Insured", "Claimant Name" and other labels; age and gender after the name are dropped |
| Insurer | Earliest alias match over 32 Indian health insurers; only 4 of them have wordings in the clause base |
| TPA | 22 third-party administrators (Medi Assist, MDIndia, Paramount, Vidal and others) |
| Product | Longest product-name match, skipping text inside the insurer name ("Care" vs "Care Health"); a product label that matches nothing in the clause base is kept as written in `policy_product_raw` |
| Diagnosis | "Diagnosis:"/"Ailment:" labels, "for the treatment of X", "diagnosed with X" |
| Policy number | Labelled "Policy No." |
| Dates | Labelled or narrative; accepts ISO, dd/mm/yyyy, dd-mm-yyyy and "13 August 2024" forms |
| Hospital | "at X for/admitted/has been", "Hospital: X" |
| Procedure | "for X (ICD-10", "Procedure: X", "towards X performed" |
| ICD-10 | Code pattern, then checked against `icd10_codes.csv` (billable flag reported) |
| Amount | "Rs", "Rs.", "INR", "₹" with Western or Indian (lakh) grouping and a trailing "/-" |
| Cited clause | "Clause 4.3", "Code-Excl03", "Section 2.1" |
| Denial reason | The list after a heading ("Detailed Remarks:", "Reason for rejection:") or a lead-in ("for the following reasons", "reason(s) as specified:"), else the letter body after the salutation without courtesy lines, contact details and the details table. The standard preamble "The Company is not liable to make any payment under this policy in respect of" is dropped from the stated reason |
| Labels | Matched with or without a colon, with spaces lost, with a letter or two misread (fuzzy ratio ≥ 90 for long labels), with the value on the next line, and two label pairs on one row |
| Clause ID | Candidates with the same product and clause number, ranked by the overlap between the reason text (expanded with policy synonyms) and the clause text; top three kept for review |

## 6. Triage agents

| Agent | Evidence | Output |
|---|---|---|
| Cue agent | Weighted phrase cues per category ("waiting period", "pre-existing", "room rent", "co-payment", "not medically necessary", "discharge summary not submitted", "intimation", "not an insured member" and so on) | Score per category, with the matched cues |
| Reason agent | TF-IDF (word and character n-grams) similarity to the 70 standard reasons and their sub-categories | Score per category, best `reason_id` with CARC/RARC codes and the appeal route |
| Clause agent | Type and text of the resolved clause (`WAITING_PERIOD`, `EXCLUSION` and so on) | A weak prior; abstains when no clause is resolved |
| LLM agent (optional) | Few-shot prompt with the category definitions; JSON output | One category with a confidence; abstains if not configured |

The supervisor normalizes each agent's scores, combines them with configured weights, and reports:
- the primary category and the probability distribution;
- secondary categories above a threshold, since one letter can raise more than one issue;
- `needs_human_review` when confidence is below 0.5, the margin is below 0.15, or the two strongest agents disagree.

## 7. Routing

Each category maps to an Objective 03 pipeline:
- the deterministic checks it will run, such as waiting-period date arithmetic or the room-rent proportion;
- the runtime tables it queries;
- the documents it needs from the patient.

The router also returns the appeal route of the matched standard reason, which is GRO first, then the Insurance Ombudsman.

## 8. Evaluation

| Benchmark | Metric | Notes |
|---|---|---|
| G1 intake | Exact match per field, token F1 for text fields, clause-ID accuracy (top-1 and top-3) | Clause numbers repeat within a product (up to 38 candidates for one number), so top-3 is reported as well |
| G7 triage | Accuracy, macro-F1, per-class precision and recall, confusion matrix | Ablation: each agent alone and the full ensemble |
| Generalization | Unit tests on hand-written letters in other formats | dd/mm/yyyy dates, lakh amounts, "Code-Excl" clauses, PDF input |

Targets from the dataset plan: field exact match of at least 0.95 and router macro-F1 of at least 0.90. The scripts write their results to `evaluation/results/`, which is git-ignored because every run rewrites it.

## 9. Build order

1. Schemas, config and the knowledge loader.
2. Loader, extractor and normalizer, with unit tests.
3. Clause resolver.
4. The cue, reason and clause agents, then the supervisor and router.
5. The LangGraph graph, the sequential fallback and the CLI.
6. Evaluation on G1 and G7, the ablation, and the error analysis.
7. The optional LLM agent, enabled with `DENIAL_AI_LLM=nvidia|groq|openai` and the matching API key.

## 10. Status and results (2026-10-29)

Steps 1 to 6 are built. The LLM agent (step 7) is in place but switched off by default and has not been evaluated.

How to run:

```
python -m denial_ai letter.txt            # readable summary
python -m denial_ai letter.pdf --json     # full case record
python -m evaluation.eval_intake          # G1
python -m evaluation.eval_triage          # G7 and the held-out set
python -m evaluation.eval_robustness      # rewritten G1 letters and hand-written letters
python -m evaluation.eval_ocr_formats     # the hand-written letters as PNG, JPEG, photo, PDF, TIFF
python -m evaluation.eval_real_letters    # real letters in data/Denial letters (git-ignored)
python -m pytest                          # 41 tests
python -m uvicorn denial_ai.api:app --port 8000   # web interface at http://localhost:8000
```

| Benchmark | Result |
|---|---|
| G1 intake, 12 fields | Exact match 1.00 on every field |
| G1 cited clause ID | Top-1 0.98, top-3 1.00 |
| G7 triage, ensemble | Accuracy 1.00, macro-F1 1.00; 26 of 140 flagged for review |
| G7, cue agent alone | Accuracy 0.96, macro-F1 0.97 |
| G7, reason agent alone | Accuracy 0.84, macro-F1 0.84 |
| Held-out set (35 hand-written denials) | Accuracy 0.97, macro-F1 0.97; 6 flagged |

These numbers are for the golden datasets rebuilt on 2026-10-29 after the Star Women Care wording was added. That run has 14 products, 3,028 runtime clauses, 1,794 citable clauses and 211 product-topic pairs; G1 to G7 keep their case counts but hold new cases.

How to read these numbers:
- G1 and G7 are generated from a few templates, and the intake patterns and cue list were corrected after error analysis on them. They show that the pipeline covers those formats, not that it generalizes.
- The held-out set in `evaluation/heldout_denials.json` was written in different wording and scored once without tuning. It is the better estimate. Its one error (H-01) is a medical-necessity denial that mentions "case papers" and is read as a documentation problem.
- The G1 clause labels were corrected before these numbers were taken. The builder used to pick any clause that mentioned a topic, so "Initial 30-Day Waiting Period" letters could point to the free-look or portability clause, and "Room Rent Limit" letters to the definition of room rent. `TOPIC_RULES` in `build_golden_datasets.py` now requires each chosen clause to state the rule itself near its start. Sub-item numbers such as "6.1(a)" are now citable, which lets the real "Code-Excl01" PED clauses be used. G2 and G6 draw on the same topic-to-clause table, so their ground truth improved as well. Before the fix, the resolver scored 0.86 top-1 against the old labels.

## 11. Known limits and how they were addressed

### 11.1 Robustness beyond the G1 layouts

**Was:** G1 and G7 use a few templates, so high scores there did not show the pipeline would cope with other letters.

**Now:** `evaluation/eval_robustness.py` checks two things.

1. Every G1 letter is rewritten one way at a time, and the extracted fields must stay the same. All 100 letters are fully correct under each change:
   - dates as dd/mm/yyyy or "13 August 2024";
   - amounts in lakh grouping with ₹ or INR;
   - lines wrapped as in a PDF;
   - upper-case letterheads;
   - insurer names with the spaces lost by OCR.
2. Eight hand-written letters in other layouts are run through the whole pipeline (`evaluation/heldout_letters.json`). These letters use subject lines, address blocks, "Dated" without a colon, Code-Excl citations and partial settlements.

| Hand-written letters | Field accuracy | Category accuracy |
|---|---|---|
| First run, before any change | 0.877 | 8/8 |
| After the fixes below | 0.986 | 8/8 |

The fixes were general rules:
- an ID next to the word "claim" wins over a letter reference number;
- "Dear Sir/Madam" is not a name, so the address block is used;
- "hospitalisation at X on <date>" and "undergone at X from <date>" are read;
- hospital names that wrap onto the next line are read.

The second number is no longer a held-out score, because these letters were used to find the fixes. One truth value was corrected: L-06 does name the clinic, and the label wrongly said it did not. The one field still missed (L-06's treatment date) is written without any admission wording.

### 11.2 Scanned letters

**Was:** scanned letters needed OCR, which was not part of this stage.

**Now:** `intake/loader.py` reads scans with RapidOCR, an ONNX model that runs offline on the CPU with no Tesseract install. It handles:
- image files (PNG, JPG, TIFF);
- PDF pages without a text layer. When the page holds one embedded scan, that image is read at its own resolution.

Before OCR the image is converted to greyscale, and narrow scans are enlarged. Without that, the model drops the spaces between words. Two more rules repair common OCR damage:
- insurer and product names match even with their spaces lost ("HDFCERGO");
- merged capitalised words are split again ("AorticValve" becomes "Aortic Valve").

The test fixtures in `tests/fixtures/` are a letter rendered as a PNG and as an image-only PDF. Both are extracted with every field correct. OCR takes about 3 to 6 seconds per page on the CPU.

### 11.3 Clause numbers that match many clauses

**Was:** a number such as "Clause 2" can match up to 38 clauses in one product, and the resolver gave no sign of how sure it was.

**Now:** the resolver reports a status with every answer:

| Status | Meaning | `cited_clause_id` set? | Review flag |
|---|---|---|---|
| quoted | the letter reproduces the clause wording (fuzzy match of 90 or more) | yes | no |
| unique | one clause has the number, or the best matches state the same rule | yes | no |
| confident | the stated reason favours one clause by a factor of 1.5 or more | yes | no |
| ambiguous | the reason does not separate the candidates | yes, as best guess | yes |
| number_not_found | the number is not in this product's wording | no; suggestions only | yes |
| no_number | no number cited | no; suggestions only | no |

On G1, every "unique" (33) and "confident" (51) answer is correct. The two remaining errors are both among the 16 "ambiguous" cases, which are sent to a reviewer. A letter that quotes the policy is pinned to the exact clause even without a number. This follows IRDAI's requirement that a repudiation reproduce the exclusion it relies on. The clause agent votes only when the clause is quoted, unique or confident.

### 11.4 First real letter (ICICI Lombard, group policy, "Sum Insured Exhausted")

The category was right on the first run, but intake failed on the layout:
- the letter's own reference ("Ref : 82") was taken as the claim number;
- the patient, both dates, the policy number and the stated reason were missed;
- "no review flags" was shown although the case was incomplete;
- the appeal route stopped at the GRO;
- the investigation plan listed room-rent and co-payment checks that do not apply.

The synthetic letters never used this layout:
- a details table without colons;
- plain numeric claim numbers;
- DD-MON-YY dates;
- a "Reason | Description" table;
- a corporate group policy;
- a deadline in weeks.

What changed:

| Problem | Fix |
|---|---|
| Table rows without colons; labels OCR ran together ("Claimof") | Multi-word labels are read with or without a colon and with spaces optional |
| Letter reference taken as the claim ID | `letter_ref` is a separate field; a reference is used as the claim ID only if it has the claim-ID shape and nothing better exists. Plain numeric claim numbers are accepted from a claim label. |
| `02-FEB-2023`, `08-JAN-23`, `21-JUL-22to20-JUL-23` | Day-month-name dates with hyphens and two-digit years; coverage period parsed into `policy_start`/`policy_end` |
| Group policy not recognised | `policy_type` = group when the policy name is a company; `policy_holder` keeps the employer, with glued company words split off ("…SERVICESPVTLTD" becomes "… SERVICES PVT LTD") |
| Member ID, deadline in weeks | `member_id` (UHID); time limits in days, weeks or months, with the sentence kept in `deadline_note` |
| Stated reason in a table | Read from a Reason/Description table, or from a standard reason named in the letter |
| Courtesy lines in the triage text | Thank-you, contact, signature and "considered as accepted" lines are removed; "we regret to inform you that" is stripped but the rest of its sentence kept |
| No review flag | `intake_issues` flag a missing claim number, patient or admission date, a group policy whose wording is not in the knowledge base, an unidentified product, and an unclear clause. The G7 evaluation counts only the router's own flags, since bare paragraphs have no patient. |
| Appeal route "Insurer GRO" only | Every route now continues to the Insurance Ombudsman (Ombudsman Rules 2017, Rule 13); documentation denials start with "resubmit the missing documents" (`build_runtime_csvs.py`, `denial_reasons.csv` rebuilt) |
| Generic investigation checks | Reason-specific checks for FIN-001, FIN-002, FIN-004, FIN-005, FIN-008, PW-001, PW-004, ELG-001 and ADM-001 replace the category's general ones; the plan records the reason it was narrowed to |
| OCR image shrunk back to 2000 px | RapidOCR `max_side_len` raised to 4000, so the enlarged scan is read at full size |

The real letter is not stored in the repository because it holds a real claimant's details. The regression test `tests/fixtures/group_policy_letter.*` uses the same layout with made-up details. It runs both as OCR-style text (with the glitches seen on the real letter) and as a rendered image. On the real letter, every field it states is now extracted correctly, and only hospital, procedure, ICD-10, amount and clause are reported missing, which is correct because the letter does not state them.

### 11.5 Two more real letters (Star Health cashless denial, HDFC ERGO proposal rejection)

Before the changes, the Star Health letter lost:
- the patient, the product and the hospital, because the labels "Name of the Insured", "Product Name" and "Name of the Hospital and Location" were unknown;
- the last part of the claim number "CIR/2025/161218/1829414", which was cut after the third part;
- a clean reason text: the triage text held the logo, the details table and the closing courtesy line, and two agents disagreed.

The HDFC ERGO letter is not a claim denial at all. It refuses an application for a new policy ("BMI out of range"), yet it was triaged as FINANCIAL_LIMIT. OCR had also lost its subject line, which names the product, and the line offering another product.

What the OCR was doing wrong, and the fixes in `intake/loader.py` and `intake/respace.py`:

| Problem | Cause | Fix |
|---|---|---|
| Whole lines missing (an italic subject line, a line under a table border) | RapidOCR's text-angle classifier turned some upright lines upside down; the garbled reading then fell below the score threshold and was dropped without notice | Classifier off. Pages turned sideways or upside down are detected instead: upright text boxes on the page, or low confidence, trigger a reading at the other quarter turns, and the best is kept |
| Words run together ("VASUNDHRASHAHI", "COMPASSITSOLUTIONS", "hospitalisationwhich") | The recogniser drops spaces on a tight crop | A box with 12 or more letters in a row is read again with a margin of 20% of its height; the new reading is kept only if it has the same letters plus spaces, so it can never change a character |
| Runs still joined after that ("treatmentofFEVER", "InsurancePolicy") | Same | Word splitting with a vocabulary built from the runtime tables (policy wordings, reasons, ICD-10) and common letter words, with Zipf costs as in wordninja. A run is split only if every piece is a known word, which leaves names like "Medicity" and "Andheri" whole; e-mail and web addresses are left alone |
| "BMl", "GASTROENTERiTIS" | "l" or "i" read for "I" among capitals | Corrected inside words written in capitals |
| Phone photos sideways, transparent PNGs black, only the first page of a fax TIFF | | EXIF rotation applied, transparency flattened onto white, every TIFF page read |
| Table labels and values on separate lines in text-layer PDFs | PDF table cells are separate text blocks | PDF words are regrouped into rows by position, as OCR boxes are |
| A scan with a printed footer or stamp read as a text PDF | Any text above 40 characters skipped OCR | A page with under 300 characters of text over a page-sized image is also read by OCR |
| `unclip_ratio` changed on one call stayed for all later calls | RapidOCR keeps the last detector settings | The settings are passed on every call |

Extraction and triage changes:
- **Letter type.** `letter_type` is `proposal_rejection` when the insurer refuses a new policy and no claim is named. For such a letter:
  - no clause is looked up and no standard claim reason, appeal route or investigation is given;
  - the only review reason is "not a claim denial";
  - the web page shows "Not a claim denial" in place of the category.
- **New fields.** The new fields are `application_number`, `tpa`, `diagnosis` and `policy_product_raw`. The last one holds a product printed in the letter that is not in the knowledge base, such as "Star Women Care Insurance Policy"; the intake issue then names that product.
- **Insurers.** 32 health insurers and 22 TPAs are recognised. Only 4 insurers have wordings in the knowledge base, and the intake issue says so for the rest.
- **Reasons section.** The reasons are read as a list after "Detailed Remarks:" or "...for the following reasons". The patient's name is dropped from member/reason tables, and the IRDAI exclusion preamble ("The Company is not liable to make any payment under this policy in respect of any") is dropped from the stated reason.
- **Wording bridge for the reason agent.** Letters say "does not warrant hospitalisation"; the reason table says "inpatient admission not warranted". The reason agent widens the letter's wording before matching, so the Star letter now matches MN-009 "Outpatient Sufficiency" rather than MN-001 "Elective Surgery". G7 and the held-out set are unchanged by this.

Results on the three real letters (`python -m evaluation.eval_real_letters`, checked by hand against the letter images): every field the letters state is extracted correctly. Both claim letters get the right category (FINANCIAL_LIMIT 0.97 with FIN-001; MEDICAL_NECESSITY 0.82 with MN-009), and the HDFC letter is reported as a proposal rejection. Made-up replicas of both new layouts, and of a text-layer PDF from a TPA for an insurer outside the knowledge base, are images in `tests/fixtures/` (cashless_denial_letter.png, proposal_rejection_letter.png, text_layer_table.pdf) and are covered by `tests/test_layouts.py`. That file also checks pages turned 90, 180 and 270 degrees, a transparent PNG, an EXIF-rotated photo and a two-page TIFF.

**The same letters in other file forms** (`python -m evaluation.eval_ocr_formats`). The 8 hand-written held-out letters are rendered as the files people upload, read back through the loader and scored on their 9 to 11 labelled fields:

| Form | Fields before these changes | Fields after | Category |
|---|---|---|---|
| Text (no OCR) | 0.986 | 1.000 | 8/8 |
| PNG scan, 200 dpi | 0.931 | 1.000 | 8/8 |
| Low-resolution JPEG (100 dpi, quality 35) | 0.822 | 0.959 | 8/8 |
| Phone photo (tilted 2.5°, grey paper, blur) | 0.712 | 0.959 | 8/8 |
| Scanned sideways | 0.945 | 1.000 | 8/8 |
| Scanned upside down | 0.931 | 1.000 | 8/8 |
| PDF holding only the page image | 0.931 | 1.000 | 8/8 |
| PDF with a text layer | 0.973 | 1.000* | 8/8 |
| Two-page TIFF | 0.918 | 0.973 | 8/8 |

\* 0.986 in the saved run. Its one miss was an amount whose "₹" the PDF's standard font printed as "·". The amount fallback now skips a stray sign, and all 8 letters were then checked again in this form.

The "before" column already includes the OCR changes in the first table of this section. The gains in the "after" column come from:
- **OCR text repairs:**
  - "o" read as "0" in numbers;
  - "Rs3.95.000" read with dots for commas;
  - spaces restored after "Dear", titles and commas, between words and numbers, and before claim IDs ("ClaimCLM-2024-…");
- **amounts without a currency sign;**
- **a label whose colon was read as a dot;**
- **a word-initial "l" in a name read as "I"** ("lyer");
- **levelling a tilted page:** the median slope of the text boxes, when it is 0.5° or more, sets the page level before it is read again;
- **admission dates written as "at <hospital> on <date>".**

The last fix also cured L-06, whose admission date the text path had always missed. The held-out letters were meant to be scored once without tuning, so their 1.000 is no longer a clean estimate.

The remaining errors are misread characters that no rule can safely undo:
- "Emakulam" for "Ernakulam";
- a lost comma in "Max Hospital Patparganj";
- "Vadodaraon02/10/2024", where three words ran together on the tilted photo.

Reading takes about 2 to 30 seconds a page on this CPU. A sideways page costs three readings.

### 11.6 Star Women Care added to the knowledge base

The Star letter's product was missing from the clause base, so its wording, `data/policy_wordings/STAR/star-women-care.pdf`, was added.

**What the file is.** The PDF is the product brochure (UIN SHAHLIP27051V032627), not the full policy wording. It states:
- the coverages;
- the waiting periods;
- Code-Excl 01 to 38;
- the moratorium.

It lacks the definitions and most general conditions that the other 13 wordings have.

**Runtime table.** It is registered in `policy_discovery.py` as "Star Women Care" and gives 141 clauses (STARWO-2888 to STARWO-3028). It sorts last, so no other clause ID moved.

**Clause numbering fix.** While adding it, the builder was fixed for clause numbers followed by text that starts with a number ("3. 30-day waiting period", "32. 2-Hour Hospitalization"). These were filed under the item above them. The fix corrected 9 existing rows in Star Comprehensive, Family Health Optima and Elevate Health; their clause IDs did not change.

**Code-Excl lookup.** Star wordings number an exclusion by its place in the list and give the IRDAI code at the end ("33. Any hospitalization which are not medically necessary / does not warrant hospitalization - Code-Excl 36"). Letters cite the code. The knowledge base therefore also finds such a clause under its code, for products whose clause numbers are not codes already. A letter citing "Code-Excl 36" under any of the three Star products now resolves to that clause instead of "number not found".

**Golden datasets.** They were rebuilt with `build_golden_datasets.py`, which is seeded and gave identical files on two runs; their case counts and schemas were checked. Star Women Care appears in G1, G2, G6 and G7.

**The Star letter now:**
- product "Star Women Care";
- top clause candidate STARWO-EXC-3007 (Code-Excl 36, score 1.00);
- MEDICAL_NECESSITY with MN-009;
- no review flags.

### 11.7 What remains

- **Merged names.** A name OCR runs together survives only if re-reading the box does not bring the space back and its parts are not dictionary words. An English-only recognition model (en_PP-OCRv4) would avoid most of this, but it has to be downloaded separately.
- **OCR quality:** handwriting and very poor scans have not been tested; OCR quality limits the extraction.
- **Proposal rejections:** these are recognised and set aside; their underwriting reasons ("BMI out of range") are not analysed further.
- **Clause numbers missing from the PDFs:** about 15% of runtime clauses have no clause number because the policy PDF prints none, so they can be found only by quotation or by the stated reason.
- **Size of the test sets:** the held-out letter set is small (8 letters) and the denial set has 35 paragraphs. Three real letters are scored so far (`data/Denial letters`, `eval_real_letters`); more from other insurers would be a better test.
- **LLM agent:** it has not been evaluated.

## 12. Web interface

`python -m uvicorn denial_ai.api:app --port 8000`, then open http://localhost:8000.

- **Input:** upload a .txt, .pdf (text or scanned) or image file, or paste the letter text.
- **Result:**
  - the primary category with confidence, margin and any review reasons, or "Not a claim denial" for a letter that refuses a new policy;
  - the matched standard reason with its CARC/RARC codes and appeal route;
  - the extracted fields (read-only);
  - the cited clause with its resolution status, the candidates, and each candidate's full text;
  - each agent's vote and evidence;
  - the investigation plan;
  - the letter with the triage text highlighted.
- **This session:** the letters analysed since the server started. Click one to reopen it. Use the ✕ on a row to delete it, or "Delete all" (shown when two or more letters are listed), which asks for confirmation. Cases are kept in memory only, and nothing is written to disk.
- **API:**
  - `POST /api/analyze`
  - `GET /api/cases`
  - `GET /api/cases/{id}`
  - `DELETE /api/cases/{id}`
  - `DELETE /api/cases`
  - `GET /api/clauses/{id}`
  - `GET /api/meta`
