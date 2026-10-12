"""
policy_discovery.py
===================
Dynamic discovery and metadata normalization module for policy wording documents.
Recursively inspects data/policy_wordings/ and handles dynamically added company
folders, nested subfolders, and newly uploaded policy PDFs.
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple, Any

# Curated lookup for known policy documents to ensure canonical product naming
KNOWN_POLICY_METADATA = {
    # Care Health
    "care---policy-terms-&-conditions-(effective-from-21-march-2026).pdf": {
        "insurer": "Care Health",
        "product": "Care",
        "insurer_code": "CARE"
    },
    "care-supreme---policy-terms-&-conditions-(effective-from-29-april-2026).pdf": {
        "insurer": "Care Health",
        "product": "Care Supreme",
        "insurer_code": "CARE"
    },
    # HDFC ERGO
    "hdfc-optima-restore.pdf": {
        "insurer": "HDFC ERGO",
        "product": "Optima Restore",
        "insurer_code": "HDFC"
    },
    "hdfc-optima-secure.pdf": {
        "insurer": "HDFC ERGO",
        "product": "my:Optima Secure",
        "insurer_code": "HDFC"
    },
    # Star Health
    "star-comprehensive.pdf": {
        "insurer": "Star Health",
        "product": "Star Comprehensive",
        "insurer_code": "STAR"
    },
    "star-family-health-optima.pdf": {
        "insurer": "Star Health",
        "product": "Family Health Optima",
        "insurer_code": "STAR"
    },
    # ICICI Lombard
    "complete-health-insurance.pdf": {
        "insurer": "ICICI Lombard",
        "product": "Complete Health Insurance",
        "insurer_code": "ILGI"
    },
    "health-shield-360-retail_icihlip23165v012223_policy-wording.pdf": {
        "insurer": "ICICI Lombard",
        "product": "Health Shield 360",
        "insurer_code": "ILGI"
    },
    "arogya-sanjeevani.pdf": {
        "insurer": "ICICI Lombard",
        "product": "Arogya Sanjeevani",
        "insurer_code": "ILGI"
    },
    "elevate.pdf": {
        "insurer": "ICICI Lombard",
        "product": "Elevate Health",
        "insurer_code": "ILGI"
    },
    "health-advantedge8c0007ff45fd68ff8a0df0055fa75ed5.pdf": {
        "insurer": "ICICI Lombard",
        "product": "Health AdvantEdge",
        "insurer_code": "ILGI"
    },
    "health-booster8c0007ff45fd68ff8a0df0055fa75fa4.pdf": {
        "insurer": "ICICI Lombard",
        "product": "Health Booster",
        "insurer_code": "ILGI"
    },
    "max-protect.pdf": {
        "insurer": "ICICI Lombard",
        "product": "Max Protect",
        "insurer_code": "ILGI"
    },
}

def clean_product_name(filename: str) -> str:
    """Intelligently cleans a PDF filename into a human-readable insurance product name."""
    stem = Path(filename).stem
    # Remove parenthesized dates e.g. (effective-from-21-march-2026)
    name = re.sub(r'\(effective[^\)]*\)', '', stem, flags=re.IGNORECASE)
    # Remove long hex hashes e.g. 8c0007ff45fd68ff8a0df0055fa75ed5
    name = re.sub(r'[a-f0-9]{16,}', '', name, flags=re.IGNORECASE)
    # Remove boilerplate terms
    name = re.sub(r'(?:policy[-_ ]*wording|policy[-_ ]*terms[-_ ]*&?[-_ ]*conditions|retail|icihlip\w*)', '', name, flags=re.IGNORECASE)
    # Replace dashes, underscores, and multiple spaces
    name = re.sub(r'[-_.]+', ' ', name).strip()
    cleaned = ' '.join(name.split()).title()
    return cleaned if len(cleaned) > 2 else stem.replace('-', ' ').title()

def standardize_insurer_name(name_or_folder: str) -> str:
    """Maps folder names or insurer strings to standard corporate brand names."""
    clean = name_or_folder.strip()
    upper = clean.upper()
    if "STAR" in upper:
        return "Star Health"
    if "HDFC" in upper:
        return "HDFC ERGO"
    if "CARE" in upper or "RELIGARE" in upper:
        return "Care Health"
    if "ICICI" in upper:
        return "ICICI Lombard"
    if "NIVA" in upper or "MAX BUPA" in upper:
        return "Niva Bupa"
    if "BAJAJ" in upper:
        return "Bajaj Allianz"
    if "TATA" in upper:
        return "Tata AIG"
    if "ADITYA" in upper or "BIRLA" in upper:
        return "Aditya Birla Health"
    if "MANIPAL" in upper or "CIGNA" in upper:
        return "ManipalCigna"
    if "SBI" in upper:
        return "SBI General"
    if "RELIANCE" in upper:
        return "Reliance General"
    return clean.title()

def derive_insurer_code(insurer_name: str) -> str:
    """Derives standard 4-character insurer code abbreviation."""
    upper = insurer_name.upper()
    if "ICICI" in upper:
        return "ILGI"
    if "CARE" in upper:
        return "CARE"
    if "HDFC" in upper:
        return "HDFC"
    if "STAR" in upper:
        return "STAR"
    if "BAJAJ" in upper:
        return "BAGI"
    if "NIVA" in upper:
        return "NIVA"
    if "TATA" in upper:
        return "TATA"
    # General fallback
    alnum = re.sub(r'[^A-Z0-9]', '', upper)
    return alnum[:4] if len(alnum) >= 4 else (alnum + "XXXX")[:4]

def discover_policy_documents(policy_dir: Path) -> List[Dict[str, Any]]:
    """
    Recursively discovers all policy PDFs inside policy_dir.
    Handles any nested subfolder structure and newly added companies.
    
    Returns list of dicts:
      - path: Path object
      - filename: str
      - rel_path: str
      - folder_name: str
      - insurer: str
      - product: str
      - product_code: str
      - insurer_code: str
      - size_kb: float
    """
    documents = []
    if not policy_dir.exists():
        return documents

    for item in sorted(policy_dir.rglob("*")):
        if item.is_file() and item.suffix.lower() == ".pdf":
            rel = item.relative_to(policy_dir)
            parts = rel.parts
            fname_lower = item.name.lower()
            
            # 1. Check known metadata
            meta = KNOWN_POLICY_METADATA.get(fname_lower)
            if not meta:
                for k, v in KNOWN_POLICY_METADATA.items():
                    if k.lower() == fname_lower:
                        meta = v
                        break

            # 2. Derive insurer & product
            if meta:
                insurer = meta["insurer"]
                product = meta["product"]
                insurer_code = meta.get("insurer_code", derive_insurer_code(insurer))
            else:
                # Top-level subdirectory relative to policy_dir
                parts = rel.parts
                if len(parts) > 1:
                    insurer = standardize_insurer_name(parts[0])
                else:
                    # Flat file: try to extract insurer from filename prefix
                    tokens = clean_product_name(item.name).split()
                    insurer = standardize_insurer_name(tokens[0]) if tokens else "Unknown Insurer"
                product = clean_product_name(item.name)
                insurer_code = derive_insurer_code(insurer)

            # 3. Product code for clause IDs
            product_code = re.sub(r'[^A-Z0-9]', '', product.upper())[:6]
            if len(product_code) < 3:
                product_code = (product_code + "POL")[:6]

            size_kb = item.stat().st_size / 1024.0

            documents.append({
                "path": item,
                "filename": item.name,
                "rel_path": str(rel),
                "folder_name": parts[0] if len(rel.parts) > 1 else "",
                "insurer": insurer,
                "product": product,
                "product_code": product_code,
                "insurer_code": insurer_code,
                "size_kb": size_kb
            })

    return documents

def get_all_products_from_policies(policy_dir: Path) -> List[Tuple[str, str, str]]:
    """
    Returns unique tuple list of (insurer, product_name, insurer_code)
    dynamically discovered from policy_dir.
    """
    docs = discover_policy_documents(policy_dir)
    seen = set()
    result = []
    for d in docs:
        key = (d["insurer"], d["product"], d["insurer_code"])
        if key not in seen:
            seen.add(key)
            result.append(key)
    
    # If no policies were found, provide fallback defaults
    if not result:
        result = [
            ("ICICI Lombard", "Complete Health Insurance", "ILGI"),
            ("Care Health", "Care", "CARE"),
            ("HDFC ERGO", "my:Optima Secure", "HDFC"),
            ("Star Health", "Star Comprehensive", "STAR"),
        ]
    return result
