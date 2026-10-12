import xml.etree.ElementTree as ET

def build_square_architecture_drawio():
    """
    Generates a production-grade, SQUARE BOUNDARY architecture diagram featuring:
    1. Investigation Engines arranged in 2 neat columns with a unified findings collector.
    2. The 5 ESSENTIAL Reference Database relationships drawn cleanly as non-overlapping,
       perfectly horizontal dashed query tracks and clean state logging.
    3. Dual-track Tier 3 flow (Top Track: Generation & Evaluation, Bottom Track: Compliance & Human Governance).
    4. Balanced Square Boundary (~1160x1030).
    """
    mxfile = ET.Element('mxfile', host='app.diagrams.net', modified='2026-10-12T00:45:00.000Z', agent='Mozilla/5.0', version='24.0.0', type='device')
    diagram = ET.SubElement(mxfile, 'diagram', id='SquareArchitecture', name='Square System Architecture')
    model = ET.SubElement(diagram, 'mxGraphModel', dx='1500', dy='1300', grid='1', gridSize='10', guides='1', tooltips='1', connect='1', arrows='1', fold='1', page='1', pageScale='1', pageWidth='1200', pageHeight='1070', background='#FFFFFF', math='0', shadow='0')
    root = ET.SubElement(model, 'root')
    
    # Layer 0 and Layer 1
    ET.SubElement(root, 'mxCell', id='0')
    ET.SubElement(root, 'mxCell', id='1', parent='0')
    
    # Node helper
    def add_node(nid, label, style, x, y, w, h, parent='1'):
        cell = ET.Element('mxCell', id=str(nid), value=str(label), style=str(style), vertex='1', parent=str(parent))
        geo = ET.SubElement(cell, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h))
        geo.set('as', 'geometry')
        root.append(cell)
        return cell

    # Edge helper
    def add_edge(eid, source, target, style, label='', exitX=None, exitY=None, entryX=None, entryY=None, points=None):
        edge_style = str(style)
        if exitX is not None and exitY is not None:
            edge_style += f"exitX={exitX};exitY={exitY};exitDx=0;exitDy=0;"
        if entryX is not None and entryY is not None:
            edge_style += f"entryX={entryX};entryY={entryY};entryDx=0;entryDy=0;"
        cell = ET.Element('mxCell', id=str(eid), value=str(label), style=edge_style, edge='1', parent='1', source=str(source), target=str(target))
        geo = ET.SubElement(cell, 'mxGeometry', relative='1')
        geo.set('as', 'geometry')
        if points:
            arr = ET.SubElement(geo, 'Array')
            arr.set('as', 'points')
            for px, py in points:
                ET.SubElement(arr, 'mxPoint', x=str(px), y=str(py))
        root.append(cell)
        return cell

    # ─────────────────────────────────────────────────────────────
    # STYLES (MONOCHROME / GRAYSCALE ENTERPRISE)
    # ─────────────────────────────────────────────────────────────
    STYLE_OUTER_FRAME = "rounded=0;whiteSpace=wrap;html=1;fillColor=#FAFAFA;strokeColor=#475569;strokeWidth=1.5;fontFamily=Helvetica;fontSize=12;fontStyle=1;fontColor=#0F172A;verticalAlign=top;align=left;spacingLeft=16;spacingTop=10;"
    STYLE_INNER_CLUSTER = "rounded=1;arcSize=4;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#94A3B8;strokeWidth=1.2;fontFamily=Helvetica;fontSize=11;fontStyle=1;fontColor=#334155;verticalAlign=top;align=left;spacingLeft=14;spacingTop=8;"
    STYLE_GROUP_BOX = "rounded=1;dashed=1;dashPattern=4 4;strokeColor=#64748B;fillColor=none;strokeWidth=1.2;verticalAlign=top;align=center;spacingTop=8;fontFamily=Helvetica;fontStyle=1;fontSize=10;fontColor=#475569;"
    
    STYLE_NODE = "rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#334155;strokeWidth=1.2;fontFamily=Helvetica;fontSize=10;fontColor=#0F172A;align=center;verticalAlign=middle;shadow=0;"
    STYLE_COLLECTOR = "rounded=1;arcSize=6;whiteSpace=wrap;html=1;fillColor=#F8FAFC;strokeColor=#334155;strokeWidth=1.4;fontFamily=Helvetica;fontSize=10;fontStyle=1;fontColor=#0F172A;align=center;verticalAlign=middle;shadow=0;"
    STYLE_ORCHESTRATOR = "rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#F1F5F9;strokeColor=#0F172A;strokeWidth=1.8;fontFamily=Helvetica;fontSize=11;fontStyle=1;fontColor=#0F172A;align=center;verticalAlign=middle;shadow=0;"
    STYLE_VERDICT = "rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#F8FAFC;strokeColor=#0F172A;strokeWidth=1.8;fontFamily=Helvetica;fontSize=11;fontStyle=1;fontColor=#0F172A;align=center;verticalAlign=middle;shadow=0;"
    STYLE_DB = "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=7;fillColor=#FFFFFF;strokeColor=#334155;strokeWidth=1.2;fontFamily=Helvetica;fontSize=10;fontColor=#0F172A;align=center;verticalAlign=middle;shadow=0;"
    STYLE_DOC = "shape=note;whiteSpace=wrap;html=1;size=10;verticalAlign=middle;align=center;fillColor=#FFFFFF;strokeColor=#475569;strokeWidth=1.2;fontFamily=Helvetica;fontSize=10;fontColor=#0F172A;"
    STYLE_OUTPUT_DOSSIER = "shape=note;whiteSpace=wrap;html=1;size=14;verticalAlign=middle;align=center;fillColor=#F8FAFC;strokeColor=#0F172A;strokeWidth=1.8;fontFamily=Helvetica;fontSize=11;fontStyle=1;fontColor=#0F172A;shadow=0;"
    
    STYLE_EDGE = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#334155;strokeWidth=1.2;endArrow=classic;endSize=5;fontFamily=Helvetica;fontSize=9;fontColor=#475569;labelBackgroundColor=#FFFFFF;"
    STYLE_EDGE_BOLD = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#0F172A;strokeWidth=1.8;endArrow=classic;endSize=6;fontFamily=Helvetica;fontSize=9;fontStyle=1;fontColor=#0F172A;labelBackgroundColor=#FFFFFF;"
    STYLE_EDGE_DASHED = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#475569;strokeWidth=1.2;dashed=1;dashPattern=3 3;endArrow=classic;startArrow=classic;endSize=4;startSize=4;fontFamily=Helvetica;fontSize=8.5;fontColor=#334155;labelBackgroundColor=#FFFFFF;"
    STYLE_EDGE_DASHED_DIR = "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#475569;strokeWidth=1.2;dashed=1;dashPattern=3 3;endArrow=classic;endSize=4;fontFamily=Helvetica;fontSize=8.5;fontColor=#334155;labelBackgroundColor=#FFFFFF;"

    # ─────────────────────────────────────────────────────────────
    # CANVAS BOUNDARIES (SQUARE 1:1 RATIO: 1160 x 1030)
    # ─────────────────────────────────────────────────────────────
    add_node('frame_outer', 'HEALTHCARE CLAIM DENIAL ANALYSIS & APPEAL SYSTEM', STYLE_OUTER_FRAME, 20, 20, 1160, 1030)
    add_node('frame_cluster', 'Multi-Agent Claim Denial Analysis & Appeal Architecture (End-to-End Pipeline)', STYLE_INNER_CLUSTER, 35, 50, 1130, 985)

    # ─────────────────────────────────────────────────────────────
    # TIER 1 (TOP BAND): INTAKE, PARSING, TRIAGE & ORCHESTRATION
    # ─────────────────────────────────────────────────────────────
    # Stage 1: Input Documents (3 Streams Horizontal)
    add_node('grp_client', 'INPUT DOCUMENTS', STYLE_GROUP_BOX, 50, 78, 1100, 74)
    add_node('doc_denial', 'Claim Denial Letter', STYLE_DOC, 80, 106, 290, 36)
    add_node('doc_policy', 'Policy Document (PDF)', STYLE_DOC, 455, 106, 290, 36)
    add_node('doc_clinical', 'Discharge Summary', STYLE_DOC, 830, 106, 290, 36)

    # Stage 2: Document Processing (3 Extractors Horizontal)
    add_node('grp_ingest', 'DOCUMENT PROCESSING', STYLE_GROUP_BOX, 50, 162, 1100, 74)
    add_node('ing_ocr', 'OCR & Text Extractor', STYLE_NODE, 80, 190, 290, 36)
    add_node('ing_layout', 'Medical Document Parser', STYLE_NODE, 455, 190, 290, 36)
    add_node('ing_ner', 'Clinical Data Extractor', STYLE_NODE, 830, 190, 290, 36)

    # Stage 3: Standardization & Triage (3 Triage Components Horizontal)
    add_node('grp_triage', 'STANDARDIZATION & TRIAGE', STYLE_GROUP_BOX, 50, 246, 1100, 74)
    add_node('tri_norm', 'Denial Code (CARC) Standardizer', STYLE_NODE, 80, 274, 290, 36)
    add_node('tri_chrono', 'Medical Timeline Builder', STYLE_NODE, 455, 274, 290, 36)
    add_node('tri_class', 'Denial Category Classifier', STYLE_NODE, 830, 274, 290, 36)

    # Stage 4: Workflow Orchestrator (Centered Box below Triage)
    add_node('orch_langgraph', 'Workflow Orchestrator', STYLE_ORCHESTRATOR, 410, 335, 360, 46)

    # ─────────────────────────────────────────────────────────────
    # TIER 2 (MIDDLE BAND): INVESTIGATION ENGINES (2 COLS) & KNOWLEDGE
    # ─────────────────────────────────────────────────────────────
    # Investigation Engines in 2 COLUMNS (Width 530, Height 285)
    add_node('grp_invest', 'INVESTIGATION ENGINES (7 SPECIALIZED WORKERS)', STYLE_GROUP_BOX, 50, 395, 530, 285)
    
    # Column A (General & Eligibility Engines) - x=65, w=230
    add_node('inv_ped', 'Waiting Period Engine', STYLE_NODE, 65, 442, 230, 34)
    add_node('inv_doc', 'Missing Document Checker', STYLE_NODE, 65, 498, 230, 34)
    add_node('inv_elig', 'Patient Eligibility Engine', STYLE_NODE, 65, 554, 230, 34)
    
    # Column B (Engines Querying Reference Databases) - x=330, w=235
    add_node('inv_excl', 'Policy Exclusion Engine', STYLE_NODE, 330, 432, 235, 34)
    add_node('inv_mn', 'Medical Necessity Engine', STYLE_NODE, 330, 476, 235, 34)
    add_node('inv_fin', 'Billing & Sub-Limit Engine', STYLE_NODE, 330, 520, 235, 34)
    add_node('inv_admin', 'Claim Procedure Engine', STYLE_NODE, 330, 564, 235, 34)

    # Unified Collector Bar spanning across both columns at bottom of engines
    add_node('inv_collector', 'Consolidated Investigation Findings', STYLE_COLLECTOR, 65, 626, 500, 38)

    # Reference Databases (Spacious 100px Channel from x=565 to x=675)
    add_node('grp_knowledge', 'REFERENCE DATABASES', STYLE_GROUP_BOX, 675, 395, 475, 285)
    
    # DB Column 1 (Left side of DB box, perfectly aligned with Column B engines) - x=695, w=215
    add_node('db_clauses', 'Policy Clauses Database', STYLE_DB, 695, 432, 215, 34)
    add_node('db_icd', 'Medical Guidelines & Codes', STYLE_DB, 695, 476, 215, 34)
    add_node('db_tariff', 'Hospital Tariffs & Limits', STYLE_DB, 695, 520, 215, 34)
    add_node('db_irdai', 'Insurance Rules & Circulars', STYLE_DB, 695, 564, 215, 34)

    # DB Column 2 (State & Audit Management) - x=930, w=200
    add_node('db_state', 'Case History & Audit DB', STYLE_DB, 930, 455, 200, 110)

    # ─────────────────────────────────────────────────────────────
    # TIER 3 (BOTTOM BAND): REASONING, VERDICT, DRAFTING & DOSSIER
    # (Strict Left-to-Right and Top-to-Bottom: ZERO zig-zagging!)
    # ─────────────────────────────────────────────────────────────
    # Block 1: Evidence & Reasoning (x=50, w=250)
    add_node('grp_reason', 'EVIDENCE & REASONING', STYLE_GROUP_BOX, 50, 700, 250, 310)
    add_node('rsn_graph', 'Evidence Aggregator', STYLE_NODE, 70, 742, 210, 52)
    add_node('rsn_toulmin', 'Appeal Grounds Builder', STYLE_NODE, 70, 852, 210, 52)

    # Block 2: Verdict & Compliance (x=325, w=250)
    add_node('grp_verdict', 'VERDICT & COMPLIANCE', STYLE_GROUP_BOX, 325, 700, 250, 310)
    add_node('rsn_verdict', 'Appeal Verdict Evaluator', STYLE_VERDICT, 345, 742, 210, 52)
    add_node('app_guard', 'Guideline & Rule Checker', STYLE_NODE, 345, 852, 210, 52)

    # Block 3: Appeal Drafting & Review (x=600, w=255)
    add_node('grp_appeal', 'APPEAL DRAFTING & REVIEW', STYLE_GROUP_BOX, 600, 700, 255, 310)
    add_node('app_draft', 'Appeal Letter Drafter', STYLE_NODE, 622, 742, 210, 52)
    add_node('app_hitl', 'Reviewer Dashboard', STYLE_ORCHESTRATOR, 622, 852, 210, 52)

    # Block 4: Final Output Package (x=880, w=270)
    add_node('grp_output', 'FINAL OUTPUT', STYLE_GROUP_BOX, 880, 700, 270, 310)
    add_node('out_dossier', 'Final Appeal Package', STYLE_OUTPUT_DOSSIER, 925, 765, 180, 140)

    # ─────────────────────────────────────────────────────────────
    # UNCONFUSING, DIRECTIONAL ARROWS (MONOTONIC FORWARD / DOWN ONLY)
    # ─────────────────────────────────────────────────────────────
    # Tier 1 Vertical Flow: Documents -> Processing -> Triage -> Orchestrator
    add_edge('e1_denial', 'doc_denial', 'ing_ocr', STYLE_EDGE, exitX=0.5, exitY=1, entryX=0.5, entryY=0)
    add_edge('e1_policy', 'doc_policy', 'ing_layout', STYLE_EDGE, exitX=0.5, exitY=1, entryX=0.5, entryY=0)
    add_edge('e1_clinical', 'doc_clinical', 'ing_ner', STYLE_EDGE, exitX=0.5, exitY=1, entryX=0.5, entryY=0)

    add_edge('e2_ocr', 'ing_ocr', 'tri_norm', STYLE_EDGE, exitX=0.5, exitY=1, entryX=0.5, entryY=0)
    add_edge('e2_layout', 'ing_layout', 'tri_chrono', STYLE_EDGE, exitX=0.5, exitY=1, entryX=0.5, entryY=0)
    add_edge('e2_ner', 'ing_ner', 'tri_class', STYLE_EDGE, exitX=0.5, exitY=1, entryX=0.5, entryY=0)

    add_edge('e3_norm', 'tri_norm', 'orch_langgraph', STYLE_EDGE, exitX=0.5, exitY=1, entryX=0.15, entryY=0)
    add_edge('e3_chrono', 'tri_chrono', 'orch_langgraph', STYLE_EDGE, exitX=0.5, exitY=1, entryX=0.50, entryY=0)
    add_edge('e3_class', 'tri_class', 'orch_langgraph', STYLE_EDGE, exitX=0.5, exitY=1, entryX=0.85, entryY=0)

    # Tier 1 -> Tier 2: Orchestrator -> Investigation Engines (Clean Downward Task Dispatch into Both Columns)
    add_edge('e4_disp_col1', 'orch_langgraph', 'inv_ped', STYLE_EDGE, exitX=0.0, exitY=0.5, entryX=0.5, entryY=0)
    add_edge('e4_disp_col2', 'orch_langgraph', 'inv_excl', STYLE_EDGE, exitX=0.10, exitY=1, entryX=0.5, entryY=0)

    # ─────────────────────────────────────────────────────────────
    # THE 5 ESSENTIAL REFERENCE DATABASE CONNECTIONS (100% CLEAN & NEAT)
    # ─────────────────────────────────────────────────────────────
    # 1. Orchestrator -> Case History & Audit DB (Clean State Persistence & Audit Trail)
    add_edge('q_db_state', 'orch_langgraph', 'db_state', STYLE_EDGE_DASHED_DIR, label='State Sync & Audit Log', exitX=1, exitY=0.5, entryX=0.5, entryY=0)

    # 2. Policy Clauses DB <-> Policy Exclusion Engine (100% Straight Horizontal Track at y=449)
    add_edge('q_db_clauses', 'db_clauses', 'inv_excl', STYLE_EDGE_DASHED, label='Clause Scope & Exceptions', exitX=0, exitY=0.5, entryX=1, entryY=0.5)

    # 3. Medical Guidelines DB <-> Medical Necessity Engine (100% Straight Horizontal Track at y=493)
    add_edge('q_db_icd', 'db_icd', 'inv_mn', STYLE_EDGE_DASHED, label='Clinical Indications (ICD-10)', exitX=0, exitY=0.5, entryX=1, entryY=0.5)

    # 4. Hospital Tariffs DB <-> Billing & Sub-Limit Engine (100% Straight Horizontal Track at y=537)
    add_edge('q_db_tariff', 'db_tariff', 'inv_fin', STYLE_EDGE_DASHED, label='NME Schedules & Capping', exitX=0, exitY=0.5, entryX=1, entryY=0.5)

    # 5. Insurance Rules DB <-> Claim Procedure Engine (100% Straight Horizontal Track at y=581)
    add_edge('q_db_irdai', 'db_irdai', 'inv_admin', STYLE_EDGE_DASHED, label='Statutory Delay Circulars', exitX=0, exitY=0.5, entryX=1, entryY=0.5)

    # ─────────────────────────────────────────────────────────────
    # Tier 2 Internal Flow: Both Engine Columns feed STRAIGHT VERTICAL down into Findings Collector
    # ─────────────────────────────────────────────────────────────
    add_edge('e5_col1_coll', 'inv_elig', 'inv_collector', STYLE_EDGE, exitX=0.5, exitY=1, entryX=0.23, entryY=0)
    add_edge('e5_col2_coll', 'inv_admin', 'inv_collector', STYLE_EDGE, exitX=0.5, exitY=1, entryX=0.76, entryY=0)

    # Tier 2 -> Tier 3: Findings Collector -> Evidence Aggregator (100% Straight Vertical Downward Line: x=175 to x=175!)
    add_edge('e5_findings_agg', 'inv_collector', 'rsn_graph', STYLE_EDGE_BOLD, label='Consolidated Findings', exitX=0.22, exitY=1, entryX=0.5, entryY=0)

    # ─────────────────────────────────────────────────────────────
    # Tier 3 Clean Dual-Track Pipeline (Strict Forward / Down Flow)
    # ─────────────────────────────────────────────────────────────
    # Evidence Aggregator -> Appeal Grounds Builder (Straight Vertical Down: x=175)
    add_edge('e6_gt', 'rsn_graph', 'rsn_toulmin', STYLE_EDGE, exitX=0.5, exitY=1, entryX=0.5, entryY=0)
    
    # Evidence Aggregator -> Appeal Verdict Evaluator (Straight Horizontal Forward Track: y=768)
    add_edge('e6_gv', 'rsn_graph', 'rsn_verdict', STYLE_EDGE, label='Evidence Graph', exitX=1, exitY=0.5, entryX=0, entryY=0.5)

    # Appeal Grounds Builder -> Guideline & Rule Checker (Straight Horizontal Forward Track: y=878)
    add_edge('e7_tg', 'rsn_toulmin', 'app_guard', STYLE_EDGE, label='Claim Grounds', exitX=1, exitY=0.5, entryX=0, entryY=0.5)

    # Guideline & Rule Checker -> Appeal Verdict Evaluator (Straight Vertical Up Compliance Gate: x=450)
    add_edge('e8_gv', 'app_guard', 'rsn_verdict', STYLE_EDGE, label='Rule Compliance', exitX=0.5, exitY=0, entryX=0.5, entryY=1)

    # Appeal Verdict Evaluator -> Appeal Letter Drafter (Straight Horizontal Forward Track: y=768)
    add_edge('e9_vd', 'rsn_verdict', 'app_draft', STYLE_EDGE_BOLD, label='Validated Verdict', exitX=1, exitY=0.5, entryX=0, entryY=0.5)

    # Appeal Letter Drafter -> Reviewer Dashboard (Straight Vertical Down Human Review Hand-off: x=727)
    add_edge('e10_dh', 'app_draft', 'app_hitl', STYLE_EDGE, label='Draft Letter', exitX=0.5, exitY=1, entryX=0.5, entryY=0)

    # Reviewer Dashboard -> Final Appeal Package (Clean Orthogonal Step to Final Package: x=832 -> x=925)
    add_edge('e11_out', 'app_hitl', 'out_dossier', STYLE_EDGE_BOLD, label='Approved Dossier', exitX=1, exitY=0.5, entryX=0, entryY=0.5)

    return ET.tostring(mxfile, encoding='utf-8').decode('utf-8')

if __name__ == '__main__':
    xml_str = build_square_architecture_drawio()
    out_file = 'Other Files/architecture_diagram.drawio'
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(xml_str)
    print(f"Successfully generated {out_file} ({len(xml_str)} chars)!")
