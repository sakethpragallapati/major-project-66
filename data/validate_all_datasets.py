"""
validate_all_datasets.py
========================
Automated validation and health-check suite across the entire data subsystem:
  1. Policy Wordings PDFs (data/policy_wordings) - Dynamic recursive discovery
  2. Ingested Raw Datasets (data/raw_sources)
  3. Active Runtime CSVs (data/runtime)
  4. Golden Evaluation Benchmarks (data/golden)
"""

import json
import csv
import sys
from pathlib import Path

# Ensure UTF-8 console output on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(r"c:\Users\Saketh\Desktop\Major Project\data")

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from policy_discovery import discover_policy_documents
except ImportError:
    from data.policy_discovery import discover_policy_documents


def check_policy_wordings():
    folder = BASE_DIR / "policy_wordings"
    docs = discover_policy_documents(folder)
    insurers = sorted(set(d["insurer"] for d in docs))
    
    print(f"\n[1/4] Checking Policy Wordings PDFs (Discovered {len(docs)} PDFs across {len(insurers)} Insurers: {', '.join(insurers)})...")
    assert len(docs) > 0, "No policy PDFs found in data/policy_wordings/"
    
    # Group by insurer for organized reporting
    by_insurer = {}
    for d in docs:
        by_insurer.setdefault(d["insurer"], []).append(d)
        
    for ins, doc_list in by_insurer.items():
        print(f"  Company: {ins} ({len(doc_list)} policies)")
        for d in sorted(doc_list, key=lambda x: x["product"]):
            assert d["size_kb"] > 50, f"PDF {d['filename']} too small ({d['size_kb']:.1f} KB)"
            print(f"    [OK] {d['product']:28s} | {d['rel_path']:50s} ({d['size_kb']:8.1f} KB)")
            
    return docs, insurers


def check_raw_sources():
    print("\n[2/4] Checking Raw Ingested Datasets...")
    folder = BASE_DIR / "raw_sources"
    files = list(folder.glob("*"))
    assert len(files) >= 6, f"Expected at least 6 raw files, found {len(files)}"
    for f in sorted(files):
        size_kb = f.stat().st_size / 1024
        print(f"  [OK] {f.name:35s} ({size_kb:8.1f} KB)")
    return len(files)


def check_runtime_csvs(discovered_insurers):
    print("\n[3/4] Checking Active Runtime Knowledge-Base CSVs...")
    folder = BASE_DIR / "runtime"
    
    # 1. Standard tables & mapping table
    expected = {
        "denial_reasons.csv": (50, 200),
        "icd10_codes.csv": (500, 10000),
        "nme_exclusions.csv": (100, 300),
        "procedure_codes.csv": (150, 1000),
        "procedure_diagnosis_map.csv": (100, 2000)
    }
    for fname, (min_rows, max_rows) in expected.items():
        fpath = folder / fname
        assert fpath.exists(), f"Missing runtime CSV {fname}"
        with open(fpath, encoding="utf-8") as f:
            reader = list(csv.reader(f))
            headers = reader[0]
            rows = reader[1:]
            assert len(rows) >= min_rows, f"{fname} has only {len(rows)} rows (< {min_rows})"
            print(f"  [OK] {fname:30s} -> {len(rows):4d} records | Columns ({len(headers)}): {', '.join(headers[:4])}...")

    # Cross-table referential integrity check (Issue X-1)
    with open(folder / "icd10_codes.csv", encoding="utf-8") as f:
        valid_icds = set(r["code"] for r in csv.DictReader(f))
    with open(folder / "procedure_codes.csv", encoding="utf-8") as f:
        valid_procs = set(r["hcpcs_code"] for r in csv.DictReader(f))
    with open(folder / "procedure_diagnosis_map.csv", encoding="utf-8") as f:
        map_rows = list(csv.DictReader(f))
        for r in map_rows:
            assert r["icd10_code"] in valid_icds, f"FK violation: {r['icd10_code']} not in icd10_codes.csv"
            assert r["hcpcs_code"] in valid_procs, f"FK violation: {r['hcpcs_code']} not in procedure_codes.csv"
    print(f"  [OK] {'Referential Integrity (FK Map)':30s} -> 100% of {len(map_rows)} linkages verified between HCPCS and ICD-10!")

    # 2. Dynamic policy_clauses.csv validation
    clauses_path = folder / "policy_clauses.csv"
    assert clauses_path.exists(), "Missing runtime CSV policy_clauses.csv"
    with open(clauses_path, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        clause_count = len(reader)
        assert clause_count >= 1000, f"policy_clauses.csv has only {clause_count} clauses"
        
        # Verify all discovered insurers present in extracted clauses
        csv_insurers = set(row["insurer"] for row in reader)
        missing_insurers = [ins for ins in discovered_insurers if ins not in csv_insurers]
        assert not missing_insurers, f"Insurers missing in clauses: {missing_insurers}"
        
        # Verify 0 mid-sentence truncations
        truncated = sum(1 for r in reader if not r["clause_text"].strip().endswith((".", ":", ";", ")", '"', "]")))
        assert truncated == 0, f"Found {truncated} truncated clauses in policy_clauses.csv"
        
        print(f"  [OK] {'policy_clauses.csv':30s} -> {clause_count:4d} records | Covered {len(csv_insurers)} Insurers ({', '.join(sorted(csv_insurers))}) | 0 Truncations")
    
    return len(expected) + 1, clause_count


def check_golden_benchmarks():
    print("\n[4/4] Checking Golden Evaluation Benchmark JSONs...")
    folder = BASE_DIR / "golden"
    expected = {
        "G1_golden_intake_entities.json": 100,
        "G2_golden_clause_retrieval.json": 100,
        "G3_golden_clinical_evidence.json": 60,
        "G4_golden_chronology_ped.json": 60,
        "G5_golden_reasoning_toulmin.json": 80,
        "G6_golden_appeal_drafts.json": 40,
        "G7_golden_denial_router.json": 140
    }
    total_cases = 0
    for fname, count in expected.items():
        fpath = folder / fname
        if not fpath.exists() and fname == "G7_golden_denial_router.json":
            alt_path = folder / "G9_golden_denial_router.json"
            if alt_path.exists():
                fpath = alt_path
                fname = "G9_golden_denial_router.json"
        assert fpath.exists(), f"Missing golden JSON {fname}"
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)
            assert len(data) == count, f"{fname} has {len(data)} cases (expected {count})"
            total_cases += len(data)
            # Sample schema validation
            sample = data[0]
            assert "case_id" in sample or "query_id" in sample, f"Invalid schema in {fname}"
            print(f"  [OK] {fname:42s} -> {len(data):3d} cases | Validated schema")
    print(f"\n  Total Golden Evaluation Cases Verified: {total_cases}")
    return total_cases


if __name__ == "__main__":
    print("=" * 70)
    print("  VERIFYING COMPLETE DATA SUBSYSTEM HEALTH")
    print("=" * 70)
    docs, insurers = check_policy_wordings()
    n_raw = check_raw_sources()
    n_csvs, n_clauses = check_runtime_csvs(insurers)
    n_golden = check_golden_benchmarks()
    print("\n" + "=" * 70)
    print(f"  ALL CHECKS PASSED: 100% HEALTHY!")
    print(f"  - {len(docs)} Policy Wordings PDFs across {len(insurers)} Insurers ({', '.join(insurers)})")
    print(f"  - {n_raw} Raw Ingestion Datasets & Manifests")
    print(f"  - {n_csvs} Active Runtime Knowledge-Base CSVs ({n_clauses} policy clauses)")
    print(f"  - 7 Golden DeepEval Benchmarks ({n_golden} Cases)")
    print("=" * 70)
