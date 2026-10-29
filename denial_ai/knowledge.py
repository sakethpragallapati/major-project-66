"""Runtime knowledge base: the CSV tables in data/runtime, loaded once.

Only runtime tables are read here. The golden benchmarks are never loaded at
runtime; they are used by the evaluation scripts alone.
"""

import csv
import re
from functools import lru_cache

from .config import RUNTIME_DIR

# Other names insurers use for themselves in letters.
INSURER_ALIASES = {
    # insurers whose policy wordings are in the knowledge base
    "Care Health": ["Care Health Insurance", "Religare Health Insurance", "Care Health"],
    "HDFC ERGO": ["HDFC ERGO General Insurance", "HDFC ERGO", "HDFC Ergo"],
    "ICICI Lombard": ["ICICI Lombard General Insurance", "ICICI Lombard"],
    "Star Health": ["Star Health and Allied Insurance", "Star Health"],
    # other insurers that sell health cover in India: recognised in letters, but
    # their wordings are not in the knowledge base
    "Aditya Birla Health": ["Aditya Birla Health Insurance", "Aditya Birla Health", "Aditya Birla Capital Health"],
    "Niva Bupa": ["Niva Bupa Health Insurance", "Niva Bupa", "Max Bupa"],
    "ManipalCigna": ["ManipalCigna Health Insurance", "Manipal Cigna", "ManipalCigna", "Cigna TTK"],
    "Galaxy Health": ["Galaxy Health and Allied Insurance", "Galaxy Health Insurance"],
    "Narayana Health": ["Narayana Health Insurance"],
    "Bajaj Allianz": ["Bajaj Allianz General Insurance", "Bajaj Allianz", "Bajaj General Insurance"],
    "Tata AIG": ["Tata AIG General Insurance", "Tata AIG", "Tata-AIG"],
    "New India Assurance": ["The New India Assurance", "New India Assurance"],
    "United India": ["United India Insurance"],
    "Oriental Insurance": ["The Oriental Insurance", "Oriental Insurance"],
    "National Insurance": ["National Insurance Company", "National Insurance Co"],
    "SBI General": ["SBI General Insurance", "SBI General"],
    "Reliance General": ["Reliance General Insurance", "Reliance General"],
    "IFFCO Tokio": ["IFFCO Tokio General Insurance", "IFFCO Tokio", "IFFCO-Tokio"],
    "Cholamandalam MS": ["Cholamandalam MS General Insurance", "Cholamandalam MS", "Chola MS"],
    "Royal Sundaram": ["Royal Sundaram General Insurance", "Royal Sundaram"],
    "Future Generali": ["Future Generali India Insurance", "Future Generali", "Generali Central"],
    "Universal Sompo": ["Universal Sompo General Insurance", "Universal Sompo"],
    "Liberty General": ["Liberty General Insurance"],
    "Kotak General": ["Zurich Kotak General Insurance", "Kotak Mahindra General Insurance", "Kotak General Insurance",
                      "Zurich Kotak"],
    "Go Digit": ["Go Digit General Insurance", "Digit General Insurance", "Go Digit", "Digit Insurance"],
    "Acko": ["Acko General Insurance", "ACKO"],
    "Magma General": ["Magma HDI General Insurance", "Magma General Insurance", "Magma HDI"],
    "Raheja QBE": ["Raheja QBE General Insurance", "Raheja QBE"],
    "Shriram General": ["Shriram General Insurance"],
    "Navi General": ["Navi General Insurance"],
    "Zuno General": ["Zuno General Insurance", "Edelweiss General Insurance"],
}

# Third-party administrators, which often send the letter on the insurer's behalf.
TPA_ALIASES = {
    "Medi Assist": ["Medi Assist", "MediAssist"],
    "MDIndia": ["MDIndia", "MD India Health"],
    "Paramount Health Services": ["Paramount Health", "Paramount TPA"],
    "Vidal Health": ["Vidal Health"],
    "Heritage Health": ["Heritage Health"],
    "Family Health Plan": ["Family Health Plan", "FHPL"],
    "Raksha Health": ["Raksha Health", "Raksha TPA"],
    "Health India TPA": ["Health India Insurance TPA", "Health India TPA"],
    "Ericson TPA": ["Ericson TPA", "Ericson Insurance TPA"],
    "Safeway TPA": ["Safeway Insurance TPA", "Safeway TPA"],
    "Park Mediclaim": ["Park Mediclaim"],
    "Genins India": ["Genins India"],
    "Vipul MedCorp": ["Vipul MedCorp"],
    "Good Health TPA": ["Good Health Insurance TPA", "Good Health TPA"],
    "Anmol Medicare": ["Anmol Medicare"],
    "East West Assist": ["East West Assist"],
    "Medsave Health": ["Medsave"],
    "Rothshield": ["Rothshield"],
    "Dedicated Healthcare Services": ["Dedicated Healthcare Services"],
    "Volo Health": ["Volo Health"],
    "Health Insurance TPA of India": ["Health Insurance TPA of India"],
    "United Health Care Parekh": ["United Health Care Parekh", "UHC Parekh"],
}


def _read(name):
    with open(RUNTIME_DIR / name, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def clause_number_key(number):
    """Comparable form of a clause number: 'Code-Excl03' and 'Code Excl 3' -> 'codeexcl03', '4.3.' -> '4.3'."""
    n = re.sub(r"[\s\-_]", "", number.strip().rstrip(".").lower())
    return re.sub(r"^codeexcl0*(\d+)$", lambda m: f"codeexcl{int(m[1]):02d}", n)


# The IRDAI code a clause names at its start or end ("... - Code-Excl 36").
EXCL_CODE = re.compile(r"Code[\s\-]*Excl[\s\-]*(\d{1,2})", re.I)


class KnowledgeBase:
    def __init__(self):
        self.clauses = _read("policy_clauses.csv")
        self.denial_reasons = _read("denial_reasons.csv")
        self.icd10 = {r["code"].upper(): r for r in _read("icd10_codes.csv")}

        self.products = {}                       # product name -> insurer
        for r in self.clauses:
            self.products.setdefault(r["product_name"], r["insurer"])

        self.product_aliases = {}                # alias as written in letters -> product name
        for p in self.products:
            self.product_aliases[p] = p
            if ":" in p:                         # "my:Optima Secure" is printed as "Optima Secure"
                self.product_aliases[p.split(":", 1)[1].strip()] = p

        self.clauses_by_product = {}
        for r in self.clauses:
            key = (r["product_name"], clause_number_key(r["clause_number"]))
            self.clauses_by_product.setdefault(key, []).append(r)
        # Star wordings number an exclusion by its place in the list and give the IRDAI
        # code at the end ("33. Any hospitalization which are not medically necessary ...
        # - Code-Excl 36"), while letters cite the code. Such a clause is also found under
        # its code, for products whose clause numbers are not codes already.
        numbered_by_code = {p for p, k in self.clauses_by_product if k.startswith("codeexcl")}
        for r in self.clauses:
            if r["product_name"] in numbered_by_code:
                continue
            text = r["clause_text"]
            codes = {clause_number_key("Code-Excl" + m[1]) for m in EXCL_CODE.finditer(text[:100] + " " + text[-40:])}
            for code in codes:
                rows = self.clauses_by_product.setdefault((r["product_name"], code), [])
                if r not in rows:
                    rows.append(r)

    def insurer_of(self, product):
        return self.products.get(product)

    def icd10_lookup(self, code):
        return self.icd10.get(code.upper()) if code else None

    def clause_candidates(self, product, clause_number):
        return self.clauses_by_product.get((product, clause_number_key(clause_number)), [])


@lru_cache(maxsize=1)
def get_kb():
    return KnowledgeBase()
