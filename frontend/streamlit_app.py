"""
HealRAG System — Streamlit frontend.

Drop this file in as frontend/streamlit_app.py (sibling of app/).
Run from the project root with: streamlit run frontend/streamlit_app.py

Wires directly into the existing app/ package — no changes needed to your
graph.py, state.py, agents/, auditors/, retrieval/, or verdict_of_issue.py.
"""

import streamlit as st
import sys, os, json, time, traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# Make the sibling `app/` package importable (graph.py does `from state import
# State`, `from retrieval.retriever import ...` etc. relative to app/, so we
# add app/ — not the project root — to sys.path).
# ---------------------------------------------------------------------------
THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent
APP_DIR = PROJECT_ROOT / "app"
sys.path.insert(0, str(APP_DIR))

# Run from project root so graph.py's relative "logs/audit_logs.json" path resolves
os.chdir(PROJECT_ROOT)

st.set_page_config(
    page_title="HealRAG System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# THEME
# =============================================================================
INK = "#0B0E11"
PANEL = "#15191E"
PANEL_RAISED = "#1C2128"
PAPER = "#F5F1E8"
PAPER_DIM = "#C9C4B6"
VERMILION = "#E8542C"
FOREST = "#3A7D5C"
BRASS = "#C9A961"
SLATE = "#6B7280"
SLATE_LIGHT = "#9CA3AF"
LINE = "#262C35"

def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {{ font-family:'Inter',sans-serif; }}
    .stApp {{
        background: radial-gradient(ellipse 1200px 600px at 50% -10%, rgba(232,84,44,0.06), transparent), {INK};
    }}
    #MainMenu, footer, header {{visibility:hidden;}}
    section[data-testid="stSidebar"] {{ background:{PANEL}; border-right:1px solid {LINE}; }}
    section[data-testid="stSidebar"] * {{ color:{PAPER} !important; }}
    h1,h2,h3 {{ font-family:'Space Grotesk',sans-serif !important; color:{PAPER} !important; letter-spacing:-0.01em; }}
    p,li,span,label,div {{ color:{PAPER_DIM}; }}
    code,.mono {{ font-family:'IBM Plex Mono',monospace !important; }}

    .eyebrow {{
        font-family:'IBM Plex Mono',monospace; font-size:0.72rem; letter-spacing:0.18em;
        text-transform:uppercase; color:{VERMILION}; font-weight:600;
        display:flex; align-items:center; gap:8px; margin-bottom:4px;
    }}
    .eyebrow::before {{ content:""; width:6px; height:6px; background:{VERMILION}; border-radius:50%; display:inline-block; animation:pulse 2s ease-in-out infinite; }}
    @keyframes pulse {{ 0%,100%{{opacity:1;}} 50%{{opacity:0.3;}} }}

    .hero-title {{ font-family:'Space Grotesk',sans-serif; font-size:2.5rem; font-weight:700; color:{PAPER}; line-height:1.12; margin:0.2em 0 0.3em 0; }}
    .hero-sub {{ font-size:1.0rem; color:{SLATE_LIGHT}; max-width:640px; line-height:1.55; }}

    .badge {{ display:inline-flex; align-items:center; gap:6px; font-family:'IBM Plex Mono',monospace; font-size:0.78rem; font-weight:600; letter-spacing:0.08em; padding:4px 12px; border-radius:3px; text-transform:uppercase; }}
    .badge-pass {{ background:rgba(58,125,92,0.15); color:{FOREST}; border:1px solid rgba(58,125,92,0.4); }}
    .badge-fail {{ background:rgba(232,84,44,0.13); color:{VERMILION}; border:1px solid rgba(232,84,44,0.4); }}
    .badge-pending {{ background:rgba(201,169,97,0.13); color:{BRASS}; border:1px solid rgba(201,169,97,0.4); }}
    .badge-insufficient {{ background:rgba(107,114,128,0.15); color:{SLATE_LIGHT}; border:1px solid rgba(107,114,128,0.4); }}

    .card {{ background:{PANEL}; border:1px solid {LINE}; border-radius:10px; padding:22px 24px; margin-bottom:14px; }}
    .card-paper {{ background:{PAPER}; border-radius:10px; padding:22px 24px; margin-bottom:14px; color:{INK}; }}
    .card-paper p, .card-paper li, .card-paper span, .card-paper div {{ color:#2A2A28; }}

    .checkpoint {{ display:flex; gap:16px; position:relative; padding-bottom:26px; }}
    .checkpoint:last-child {{ padding-bottom:0; }}
    .checkpoint-line {{ position:absolute; left:15px; top:34px; bottom:0; width:2px; background:{LINE}; }}
    .checkpoint-dot {{
        width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center;
        font-family:'IBM Plex Mono',monospace; font-size:0.7rem; font-weight:700; flex-shrink:0; z-index:1;
        border:2px solid {LINE}; background:{PANEL}; color:{SLATE}; transition:all 0.4s ease;
    }}
    .checkpoint-dot.done {{ border-color:{FOREST}; background:rgba(58,125,92,0.15); color:{FOREST}; }}
    .checkpoint-dot.fail {{ border-color:{VERMILION}; background:rgba(232,84,44,0.15); color:{VERMILION}; }}
    .checkpoint-dot.active {{ border-color:{BRASS}; background:rgba(201,169,97,0.15); color:{BRASS}; animation:spin 1.2s ease-in-out infinite; }}
    @keyframes spin {{ 0%,100%{{box-shadow:0 0 0 0 rgba(201,169,97,0.4);}} 50%{{box-shadow:0 0 0 6px rgba(201,169,97,0);}} }}
    .checkpoint-body {{ padding-top:3px; }}
    .checkpoint-title {{ font-family:'Space Grotesk',sans-serif; font-weight:600; font-size:0.95rem; color:{PAPER}; margin-bottom:2px; }}
    .checkpoint-detail {{ font-family:'IBM Plex Mono',monospace; font-size:0.78rem; color:{SLATE_LIGHT}; }}

    .score-row {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }}
    .score-label {{ font-family:'IBM Plex Mono',monospace; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.06em; color:{SLATE_LIGHT}; }}
    .score-value {{ font-family:'IBM Plex Mono',monospace; font-weight:600; font-size:0.85rem; color:{PAPER}; }}
    .meter-track {{ height:6px; background:{LINE}; border-radius:3px; overflow:hidden; margin-bottom:16px; }}
    .meter-fill {{ height:100%; border-radius:3px; transition:width 0.8s cubic-bezier(0.4,0,0.2,1); }}

    .tag {{ display:inline-block; font-family:'IBM Plex Mono',monospace; font-size:0.72rem; font-weight:600; padding:3px 10px; border-radius:3px; background:rgba(201,169,97,0.15); color:{BRASS}; border:1px dashed rgba(201,169,97,0.5); letter-spacing:0.03em; }}

    .stat-tile {{ background:{PANEL}; border:1px solid {LINE}; border-radius:10px; padding:18px 20px; }}
    .stat-number {{ font-family:'Space Grotesk',sans-serif; font-size:2.1rem; font-weight:700; color:{PAPER}; line-height:1; }}
    .stat-label {{ font-family:'IBM Plex Mono',monospace; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.08em; color:{SLATE_LIGHT}; margin-top:6px; }}

    .stButton button {{
        background:{VERMILION} !important; color:{PAPER} !important; border:none !important; border-radius:6px !important;
        font-family:'Space Grotesk',sans-serif !important; font-weight:600 !important; padding:0.55em 1.4em !important;
        transition:transform 0.15s ease, box-shadow 0.15s ease !important;
    }}
    .stButton button:hover {{ transform:translateY(-1px); box-shadow:0 4px 14px rgba(232,84,44,0.35); }}
    .stTextArea textarea, .stTextInput input {{ background:{PANEL_RAISED} !important; color:{PAPER} !important; border:1px solid {LINE} !important; border-radius:8px !important; }}
    hr {{ border-color:{LINE} !important; }}
    </style>
    """, unsafe_allow_html=True)


def badge(verdict: str) -> str:
    mapping = {
        "PASS": ("badge-pass", "✓ PASS"),
        "FAIL": ("badge-fail", "✕ FAIL"),
        "INSUFFICIENT_CONTEXT": ("badge-insufficient", "⊘ INSUFFICIENT CONTEXT"),
    }
    cls, label = mapping.get(verdict, ("badge-pending", str(verdict)))
    return f'<span class="badge {cls}">{label}</span>'


def meter(label: str, value, max_value: float = 10, color: str = VERMILION) -> str:
    try:
        v = float(value)
    except (TypeError, ValueError):
        v = 0.0
    pct = max(0, min(100, (v / max_value) * 100))
    return f"""
    <div class="score-row"><span class="score-label">{label}</span><span class="score-value">{v:.1f} / {max_value:g}</span></div>
    <div class="meter-track"><div class="meter-fill" style="width:{pct}%; background:{color};"></div></div>
    """


inject_css()

# =============================================================================
# PIPELINE NODE METADATA (presentational only)
# =============================================================================
NODE_META = {
    "retrieve_node":           {"title": "Retrieving documents",     "icon": "01"},
    "generate_node":           {"title": "Generating answer",        "icon": "02"},
    "auditor_node":            {"title": "Running audit checks",     "icon": "03"},
    "verdict_node":            {"title": "Rendering verdict",        "icon": "04"},
    "rootcause_node":          {"title": "Diagnosing root cause",    "icon": "05"},
    "audit_log_node":          {"title": "Logging attempt",          "icon": "06"},
    "repair_node":             {"title": "Repairing",                "icon": "07"},
    "finalize_audit_log_node": {"title": "Finalizing record",        "icon": "08"},
    "save_audit_log_node":     {"title": "Saving to audit log",      "icon": "09"},
}

LOG_PATH = PROJECT_ROOT / "logs" / "audit_logs.json"


def load_logs():
    if not LOG_PATH.exists():
        return []
    try:
        return json.loads(LOG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("""
        <div style="padding:6px 0 18px 0;">
            <div style="font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:1.3rem; color:#F5F1E8;">🛡️ HealRAG System</div>
            <div style="font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:#6B7280; letter-spacing:0.05em; margin-top:2px;">RECURSIVE ANSWER REFINEMENT PIPELINE</div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["Overview", "Ask a Question", "Audit History", "Analytics", "Pipeline Graph"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    n_cases = len(load_logs())
    st.markdown(f"""
        <div style="font-family:'IBM Plex Mono',monospace; font-size:0.72rem; color:#6B7280;">
            QUERIES PROCESSED<br/>
            <span style="color:#F5F1E8; font-size:1.1rem; font-weight:600;">{n_cases:03d}</span>
        </div>
    """, unsafe_allow_html=True)


# =============================================================================
# PAGE: OVERVIEW
# =============================================================================
def render_overview():
    col1, col2 = st.columns([2.2, 1])
    with col1:
        st.markdown('<div class="eyebrow">SYSTEM ONLINE</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-title">Answers you can<br/>actually trust.</div>', unsafe_allow_html=True)
        st.markdown("""
            <div class="hero-sub">
            A retrieval-augmented answer engine that checks its own work. Every response is
            scored for retrieval relevance, factual grounding, and answer quality — and if it
            falls short, the system diagnoses why, repairs the answer, and re-checks itself
            automatically.
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔎  Ask a question", width='stretch'):
                st.session_state["_nav_override"] = "Ask a Question"
                st.rerun()
        with c2:
            if st.button("📂  View audit history", width='stretch'):
                st.session_state["_nav_override"] = "Audit History"
                st.rerun()

    with col2:
        st.markdown(f"""
            <div class="card" style="margin-top:8px;">
                <div class="eyebrow" style="color:{BRASS};">HOW A VERDICT IS REACHED</div>
                <div style="font-family:'IBM Plex Mono',monospace; font-size:0.82rem; line-height:2.1; color:#C9C4B6; margin-top:8px;">
                    <div><span style="color:{VERMILION};">●</span> retrieval relevance scored 1–10</div>
                    <div><span style="color:{BRASS};">●</span> hallucination check vs. retrieved docs</div>
                    <div><span style="color:{BRASS};">●</span> answer quality scored against the question</div>
                    <div><span style="color:{FOREST};">●</span> PASS → logged & returned</div>
                    <div><span style="color:{VERMILION};">●</span> FAIL → root cause found → repaired → re-checked</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.write("")
    st.markdown('<div class="eyebrow">THREE CHECKS, EVERY ANSWER</div>', unsafe_allow_html=True)
    st.write("")
    p1, p2, p3 = st.columns(3)
    pillars = [
        ("①", "Retrieval Check", "Are the documents pulled for this question actually relevant?", VERMILION),
        ("②", "Hallucination Check", "Is every claim in the answer backed by the retrieved context?", BRASS),
        ("③", "Quality Check", "Is the answer complete, clear, and useful — not just correct?", FOREST),
    ]
    for col, (num, title, desc, color) in zip([p1, p2, p3], pillars):
        with col:
            st.markdown(f"""
                <div class="card" style="height:170px;">
                    <div style="font-family:'Space Grotesk',sans-serif; font-size:1.6rem; font-weight:700; color:{color};">{num}</div>
                    <div class="checkpoint-title" style="font-size:1.05rem; margin-top:6px;">{title}</div>
                    <div style="font-size:0.88rem; color:#9CA3AF; margin-top:6px; line-height:1.5;">{desc}</div>
                </div>
            """, unsafe_allow_html=True)


# =============================================================================
# PAGE: ASK A QUESTION (live pipeline trace)
# =============================================================================
def render_checkpoint(node_key, status, detail=""):
    meta = NODE_META.get(node_key, {"title": node_key, "icon": "•"})
    dot_cls = {"pending": "", "active": "active", "done": "done", "fail": "fail"}[status]
    icon = {"pending": meta["icon"], "active": "⟳", "done": "✓", "fail": "✕"}[status]
    return f"""
    <div class="checkpoint">
        <div class="checkpoint-line"></div>
        <div class="checkpoint-dot {dot_cls}">{icon}</div>
        <div class="checkpoint-body">
            <div class="checkpoint-title">{meta['title']}</div>
            <div class="checkpoint-detail">{detail}</div>
        </div>
    </div>
    """


def render_ask_question():
    st.markdown('<div class="eyebrow">NEW QUERY</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title" style="font-size:2.0rem;">Ask a question</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">The pipeline retrieves, answers, and audits itself live below.</div>', unsafe_allow_html=True)
    st.write("")

    col_input, col_settings = st.columns([3, 1])
    with col_input:
        query = st.text_area("Question", placeholder="e.g. What is machine learning?", height=90, label_visibility="collapsed")
    with col_settings:
        max_retries = st.number_input("Max repair attempts", min_value=0, max_value=10, value=3, step=1)

    run_clicked = st.button("▶  Run", type="primary")
    st.write("")
    st.markdown("---")

    trace_col, evidence_col = st.columns([1.1, 1.4])

    if not run_clicked:
        with trace_col:
            st.markdown(f'<div class="eyebrow" style="color:{BRASS};">LIVE TRACE</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card" style="text-align:center; padding:48px 24px; color:{SLATE_LIGHT};">Awaiting a question.<br/>The pipeline trace will animate here as it runs.</div>', unsafe_allow_html=True)
        with evidence_col:
            st.markdown('<div class="eyebrow">SCORES & EVIDENCE</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card" style="text-align:center; padding:48px 24px; color:{SLATE_LIGHT};">Audit scores will populate here as each check completes.</div>', unsafe_allow_html=True)
        return

    if not query.strip():
        st.warning("Enter a question before running.")
        return

    try:
        from graph import workflow
    except Exception as e:
        st.error(
            "Could not import `workflow` from **app/graph.py**. Make sure this file "
            "lives at `frontend/streamlit_app.py` (sibling of `app/`), and that "
            "`app/state.py`, `app/agents/`, `app/auditors/`, `app/retrieval/`, and "
            "`app/verdict_of_issue.py` are all present."
        )
        st.code("".join(traceback.format_exception(type(e), e, e.__traceback__)), language="text")
        return

    initial_state = {
        "query": query.strip(),
        "retries_count": 0,
        "max_retries": int(max_retries),
        "audit_record": {"query": query.strip(), "attempts": []},
    }

    with trace_col:
        st.markdown(f'<div class="eyebrow" style="color:{BRASS};">LIVE TRACE</div>', unsafe_allow_html=True)
        trace_placeholder = st.empty()
    with evidence_col:
        st.markdown('<div class="eyebrow">SCORES & EVIDENCE</div>', unsafe_allow_html=True)
        evidence_placeholder = st.empty()

    rendered_log = []
    final_state = {}
    error_occurred = None
    node_name = "unknown"

    def repaint():
        trace_placeholder.markdown("".join(render_checkpoint(k, s, d) for k, s, d in rendered_log), unsafe_allow_html=True)

    try:
        state = dict(initial_state)
        for step in workflow.stream(initial_state):
            for node_name, output in step.items():
                if output:
                    state.update(output)
                final_state = dict(state)
                detail = ""

                if node_name == "retrieve_node":
                    detail = f"{len(state.get('documents', []) or [])} document(s) retrieved"
                elif node_name == "generate_node":
                    detail = "draft answer composed"
                elif node_name == "auditor_node":
                    detail = (f"retrieval={state.get('retrieval_score','—')} · "
                              f"hallucination={state.get('hallucination_status','—')} · "
                              f"quality={state.get('quality_score','—')}")
                elif node_name == "verdict_node":
                    detail = f"verdict → {state.get('verdict','—')}"
                elif node_name == "rootcause_node":
                    detail = f"{state.get('primary_root_cause','—')} → {state.get('recommended_action','—')}"
                elif node_name == "audit_log_node":
                    detail = f"attempt #{len(state.get('audit_record', {}).get('attempts', []))} filed"
                elif node_name == "repair_node":
                    detail = f"repair applied · retry {state.get('retries_count','—')}/{state.get('max_retries','—')}"
                elif node_name == "finalize_audit_log_node":
                    detail = f"final verdict: {state.get('audit_record',{}).get('final_verdict','—')}"
                elif node_name == "save_audit_log_node":
                    detail = "written to logs/audit_logs.json"

                status = "fail" if (node_name == "verdict_node" and state.get("verdict") == "FAIL") else "done"
                rendered_log.append((node_name, status, detail))
                repaint()

                with evidence_placeholder.container():
                    if "retrieval_score" in state:
                        st.markdown(meter("Retrieval score", state.get("retrieval_score", 0), 10, VERMILION), unsafe_allow_html=True)
                    if "quality_score" in state:
                        st.markdown(meter("Quality score", state.get("quality_score", 0), 10, FOREST), unsafe_allow_html=True)
                    if "hallucination_confidence" in state:
                        conf = state.get("hallucination_confidence", 0) or 0
                        st.markdown(meter("Hallucination confidence", conf * 10, 10, BRASS), unsafe_allow_html=True)
                        st.markdown(f'<span class="tag">{state.get("hallucination_status","—")}</span>', unsafe_allow_html=True)
                    if state.get("primary_root_cause"):
                        st.write("")
                        st.markdown(f'<span class="tag">⚠ {state["primary_root_cause"]}</span>&nbsp;<span class="tag">→ {state.get("recommended_action","")}</span>', unsafe_allow_html=True)

                time.sleep(0.3)
    except Exception as e:
        error_occurred = e
        rendered_log.append((node_name, "fail", "node raised an exception — see details below"))
        repaint()

    st.write("")
    st.markdown("---")

    if error_occurred:
        st.error("The run stopped early — a node raised an exception.")
        st.code("".join(traceback.format_exception(type(error_occurred), error_occurred, error_occurred.__traceback__)), language="text")
        return

    record = final_state.get("audit_record", {})
    verdict = record.get("final_verdict", "—")
    st.markdown('<div class="eyebrow">RESULT</div>', unsafe_allow_html=True)
    vcol, scol = st.columns([1, 3])
    with vcol:
        st.markdown(badge(verdict), unsafe_allow_html=True)
    with scol:
        st.markdown(f'<span style="font-family:\'IBM Plex Mono\',monospace; font-size:0.82rem; color:{SLATE_LIGHT};">{record.get("total_attempts","—")} attempt(s) · {record.get("total_repairs","—")} repair(s)</span>', unsafe_allow_html=True)

    st.write("")
    st.markdown(f"""
        <div class="card-paper">
            <div style="font-family:'IBM Plex Mono',monospace; font-size:0.7rem; letter-spacing:0.1em; color:#8A8576; text-transform:uppercase; margin-bottom:8px;">Final Answer</div>
            <div style="font-size:0.98rem; line-height:1.6;">{record.get("final_answer","—")}</div>
        </div>
    """, unsafe_allow_html=True)

    if record.get("attempts"):
        with st.expander(f"View all {len(record['attempts'])} attempt(s) in detail"):
            for att in record["attempts"]:
                st.markdown(f"""
                    <div class="card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span class="checkpoint-title">Attempt #{att.get('attempt_no')}</span>
                            {badge(att.get('verdict','—'))}
                        </div>
                        <div style="font-family:'IBM Plex Mono',monospace; font-size:0.78rem; color:#9CA3AF; margin-top:10px; line-height:1.9;">
                            retrieval_score: {att.get('retrieval_score','—')} &nbsp;|&nbsp;
                            hallucination: {att.get('hallucination_status','—')} &nbsp;|&nbsp;
                            quality_score: {att.get('quality_score','—')}<br/>
                            root_cause: {att.get('primary_root_cause') or '—'} &nbsp;→&nbsp;
                            action: {att.get('recommended_action') or '—'}
                        </div>
                    </div>
                """, unsafe_allow_html=True)


# =============================================================================
# PAGE: AUDIT HISTORY
# =============================================================================
def render_history():
    st.markdown('<div class="eyebrow">RECORD ROOM</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title" style="font-size:2.0rem;">Audit history</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Every query gets logged. Browse, filter, and review past runs.</div>', unsafe_allow_html=True)
    st.write("")

    logs = load_logs()
    if not logs:
        st.markdown(f"""
            <div class="card" style="text-align:center; padding:56px 24px;">
                <div style="font-size:2.2rem;">📂</div>
                <div class="checkpoint-title" style="margin-top:10px; font-size:1.1rem;">No queries logged yet</div>
                <div style="color:{SLATE_LIGHT}; margin-top:6px;">Ask a question first — history needs runs on file.</div>
            </div>
        """, unsafe_allow_html=True)
        return

    fcol1, fcol2, fcol3 = st.columns([2, 1, 1])
    with fcol1:
        search = st.text_input("Search", placeholder="Search queries…", label_visibility="collapsed")
    with fcol2:
        verdict_filter = st.selectbox("Verdict", ["All", "PASS", "FAIL", "INSUFFICIENT_CONTEXT"])
    with fcol3:
        sort_order = st.selectbox("Order", ["Newest first", "Oldest first"])

    filtered = logs
    if search:
        filtered = [r for r in filtered if search.lower() in r.get("query", "").lower()]
    if verdict_filter != "All":
        filtered = [r for r in filtered if r.get("final_verdict") == verdict_filter]
    if sort_order == "Newest first":
        filtered = list(reversed(filtered))

    st.markdown(f'<div style="font-family:\'IBM Plex Mono\',monospace; font-size:0.78rem; color:{SLATE_LIGHT}; margin:10px 0 18px 0;">{len(filtered)} of {len(logs)} result(s)</div>', unsafe_allow_html=True)

    for record in filtered:
        original_idx = logs.index(record)
        verdict = record.get("final_verdict", "—")
        n_attempts = record.get("total_attempts", len(record.get("attempts", [])))
        n_repairs = record.get("total_repairs", 0)

        st.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:16px;">
                    <div style="flex:1;">
                        <div class="checkpoint-detail" style="margin-bottom:4px;">QUERY #{original_idx+1:04d}</div>
                        <div class="checkpoint-title" style="font-size:1.05rem;">{record.get('query','—')}</div>
                    </div>
                    {badge(verdict)}
                </div>
                <div style="margin-top:12px; font-family:'IBM Plex Mono',monospace; font-size:0.78rem; color:{SLATE_LIGHT};">
                    {n_attempts} attempt(s) · {n_repairs} repair(s)
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.expander("View details"):
            st.markdown(f"""
                <div class="card-paper">
                    <div style="font-family:'IBM Plex Mono',monospace; font-size:0.7rem; letter-spacing:0.1em; color:#8A8576; text-transform:uppercase; margin-bottom:8px;">Final Answer</div>
                    <div style="font-size:0.95rem; line-height:1.6;">{record.get('final_answer','—')}</div>
                </div>
            """, unsafe_allow_html=True)
            for att in record.get("attempts", []):
                st.markdown(f"""
                    <div class="card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span class="checkpoint-title">Attempt #{att.get('attempt_no')}</span>
                            {badge(att.get('verdict','—'))}
                        </div>
                        <div style="font-family:'IBM Plex Mono',monospace; font-size:0.78rem; color:{SLATE_LIGHT}; margin-top:10px; line-height:1.9;">
                            retrieval_score: {att.get('retrieval_score','—')} &nbsp;|&nbsp;
                            hallucination: {att.get('hallucination_status','—')} &nbsp;|&nbsp;
                            quality_score: {att.get('quality_score','—')}<br/>
                            root_cause: {att.get('primary_root_cause') or '—'} &nbsp;→&nbsp;
                            action: {att.get('recommended_action') or '—'}
                        </div>
                    </div>
                """, unsafe_allow_html=True)


# =============================================================================
# PAGE: ANALYTICS
# =============================================================================
def render_analytics():
    import pandas as pd
    import plotly.graph_objects as go

    st.markdown('<div class="eyebrow">SYSTEM METRICS</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title" style="font-size:2.0rem;">Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Aggregate signal across every query the system has processed.</div>', unsafe_allow_html=True)
    st.write("")

    logs = load_logs()
    if not logs:
        st.markdown(f"""
            <div class="card" style="text-align:center; padding:56px 24px;">
                <div style="font-size:2.2rem;">📊</div>
                <div class="checkpoint-title" style="margin-top:10px; font-size:1.1rem;">No data yet</div>
                <div style="color:{SLATE_LIGHT}; margin-top:6px;">Run a few queries first — analytics need history to work from.</div>
            </div>
        """, unsafe_allow_html=True)
        return

    rows, attempt_rows = [], []
    for i, r in enumerate(logs):
        rows.append({
            "case_id": i + 1, "query": r.get("query", ""),
            "final_verdict": r.get("final_verdict", "—"),
            "total_attempts": r.get("total_attempts", len(r.get("attempts", []))),
            "total_repairs": r.get("total_repairs", 0),
        })
        for att in r.get("attempts", []):
            attempt_rows.append({"case_id": i + 1, **att})

    df = pd.DataFrame(rows)
    adf = pd.DataFrame(attempt_rows) if attempt_rows else pd.DataFrame()

    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Mono, monospace", color=SLATE_LIGHT, size=12),
        margin=dict(l=10, r=10, t=30, b=10), legend=dict(bgcolor="rgba(0,0,0,0)"),
    )

    total = len(df)
    pass_rate = (df["final_verdict"] == "PASS").mean() * 100 if total else 0
    avg_attempts = df["total_attempts"].mean() if total else 0
    avg_repairs = df["total_repairs"].mean() if total else 0

    t1, t2, t3, t4 = st.columns(4)
    for col, (label, value, color) in zip(
        [t1, t2, t3, t4],
        [("Total queries", f"{total}", VERMILION), ("Pass rate", f"{pass_rate:.0f}%", FOREST),
         ("Avg. attempts", f"{avg_attempts:.1f}", BRASS), ("Avg. repairs", f"{avg_repairs:.1f}", SLATE_LIGHT)],
    ):
        with col:
            st.markdown(f'<div class="stat-tile"><div class="stat-number" style="color:{color};">{value}</div><div class="stat-label">{label}</div></div>', unsafe_allow_html=True)

    st.write(""); st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="eyebrow" style="color:{BRASS};">FINAL VERDICT DISTRIBUTION</div>', unsafe_allow_html=True)
        vc = df["final_verdict"].value_counts()
        color_map = {"PASS": FOREST, "FAIL": VERMILION, "INSUFFICIENT_CONTEXT": SLATE_LIGHT}
        fig = go.Figure(data=[go.Pie(
            labels=vc.index, values=vc.values, hole=0.6,
            marker=dict(colors=[color_map.get(v, BRASS) for v in vc.index], line=dict(color=INK, width=2)),
            textfont=dict(color=PAPER, family="IBM Plex Mono, monospace"),
        )])
        fig.update_layout(**layout, showlegend=True, height=320)
        st.plotly_chart(fig, width='stretch')

    with c2:
        st.markdown(f'<div class="eyebrow" style="color:{BRASS};">ROOT CAUSES (all attempts)</div>', unsafe_allow_html=True)
        if not adf.empty and "primary_root_cause" in adf.columns:
            rc = adf["primary_root_cause"].dropna().value_counts()
            if len(rc):
                fig2 = go.Figure(data=[go.Bar(x=rc.values, y=rc.index, orientation="h", marker=dict(color=VERMILION))])
                fig2.update_layout(**layout, height=320, xaxis=dict(gridcolor=LINE), yaxis=dict(gridcolor=LINE))
                st.plotly_chart(fig2, width='stretch')
            else:
                st.markdown(f'<div style="color:{SLATE_LIGHT}; padding:40px 0; text-align:center;">No root causes yet — every query passed first try.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="color:{SLATE_LIGHT}; padding:40px 0; text-align:center;">No attempt-level data yet.</div>', unsafe_allow_html=True)

    st.write("")
    st.markdown(f'<div class="eyebrow" style="color:{BRASS};">SCORE TRENDS ACROSS ATTEMPTS</div>', unsafe_allow_html=True)
    if not adf.empty and "attempt_no" in adf.columns:
        score_cols = [c for c in ["retrieval_score", "quality_score"] if c in adf.columns]
        if score_cols:
            agg = adf.groupby("attempt_no")[score_cols].mean().reset_index()
            fig3 = go.Figure()
            colors = {"retrieval_score": VERMILION, "quality_score": FOREST}
            names = {"retrieval_score": "Retrieval score", "quality_score": "Quality score"}
            for c in score_cols:
                fig3.add_trace(go.Scatter(x=agg["attempt_no"], y=agg[c], mode="lines+markers", name=names.get(c, c), line=dict(color=colors.get(c, BRASS), width=3), marker=dict(size=9)))
            fig3.update_layout(**layout, height=320, xaxis=dict(title="Attempt #", gridcolor=LINE, dtick=1), yaxis=dict(title="Avg. score", gridcolor=LINE, range=[0, 10]))
            st.plotly_chart(fig3, width='stretch')
        else:
            st.markdown(f'<div style="color:{SLATE_LIGHT}; padding:20px 0;">No score columns found.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="color:{SLATE_LIGHT}; padding:20px 0;">No attempt-level data yet.</div>', unsafe_allow_html=True)

    st.write("")
    with st.expander("View raw query table"):
        st.dataframe(df, width='stretch', hide_index=True)


# =============================================================================
# PAGE: PIPELINE GRAPH (renders the LangGraph topology as an inline SVG —
# no network/mermaid-server dependency, unlike draw_mermaid_png())
# =============================================================================
def render_pipeline_graph():
    st.markdown('<div class="eyebrow">SYSTEM ARCHITECTURE</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title" style="font-size:2.0rem;">Pipeline graph</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">The actual LangGraph state machine compiled from app/graph.py — rendered directly from <code>workflow.get_graph().draw_mermaid()</code>, not a hand-drawn copy.</div>', unsafe_allow_html=True)
    st.write("")

    try:
        from graph import workflow
        raw_mermaid_src = workflow.get_graph().draw_mermaid()
    except Exception as e:
        st.error(
            "Could not load the compiled graph from **app/graph.py** to render it. "
            "Showing routing logic only below."
        )
        st.code("".join(traceback.format_exception(type(e), e, e.__traceback__)), language="text")
        raw_mermaid_src = None

    mermaid_src = None
    if raw_mermaid_src:
        import re
        # LangGraph bakes in light-theme classDefs (e.g. "classDef default fill:#f2f0ff")
        # which override Mermaid's themeVariables and force white/lavender node fills
        # regardless of theme config. Strip those and substitute dark-theme equivalents
        # so node backgrounds actually match the app instead of fighting it.
        cleaned = re.sub(r'classDef default.*\n?', '', raw_mermaid_src)
        cleaned = re.sub(r'classDef first.*\n?', '', cleaned)
        cleaned = re.sub(r'classDef last.*\n?', '', cleaned)
        cleaned = cleaned.rstrip()
        dark_classdefs = (
            f"\nclassDef default fill:{PANEL_RAISED},stroke:{VERMILION},stroke-width:1.5px,color:{PAPER}"
            f"\nclassDef first fill:{PANEL},stroke:{BRASS},stroke-width:2px,color:{BRASS}"
            f"\nclassDef last fill:{PANEL},stroke:{FOREST},stroke-width:2px,color:{FOREST}"
        )
        mermaid_src = cleaned + dark_classdefs

    if mermaid_src:
        html = f"""<div id="graphWrap" style="width:100%; height:100%; overflow:auto; background:{PANEL_RAISED}; border-radius:8px; padding:20px; box-sizing:border-box;">
  <div class="mermaid" id="graphDiv" style="display:flex; justify-content:center;"></div>
</div>
<style>
  /* Safety-net override in case any default Mermaid styling still leaks through */
  .mermaid .node rect, .mermaid .node circle, .mermaid .node polygon {{
    fill: {PANEL_RAISED} !important;
  }}
  .mermaid .node .label, .mermaid .nodeLabel {{
    color: {PAPER} !important;
  }}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.1/mermaid.min.js"></script>
<script>
  mermaid.initialize({{
    startOnLoad: false,
    theme: 'dark',
    themeVariables: {{
      background: '{INK}',
      primaryColor: '{PANEL_RAISED}',
      primaryTextColor: '{PAPER}',
      primaryBorderColor: '{VERMILION}',
      lineColor: '{SLATE}',
      secondaryColor: '{PANEL}',
      tertiaryColor: '{PANEL}',
      fontFamily: 'IBM Plex Mono, monospace'
    }},
    flowchart: {{ curve: 'linear', useMaxWidth: false }}
  }});
  const graphDef = `{mermaid_src}`;
  mermaid.render('mermaidSvg', graphDef).then(({{svg}}) => {{
    document.getElementById('graphDiv').innerHTML = svg;
    const svgEl = document.querySelector('#graphDiv svg');
    if (svgEl) {{
      svgEl.removeAttribute('height');
      svgEl.style.maxWidth = 'none';
      svgEl.style.height = 'auto';
    }}
  }}).catch((err) => {{
    document.getElementById('graphDiv').innerHTML =
      '<p style="color:{SLATE_LIGHT}; font-family:monospace;">Diagram failed to render: ' + err + '</p>';
  }});
</script>"""
        st.markdown(f'<div class="eyebrow" style="color:{BRASS}; margin-bottom:8px;">LIVE GRAPH — scroll inside the panel to see the full flow</div>', unsafe_allow_html=True)
        st.iframe(html, height=1300)

    st.markdown(f"""
        <div class="card">
            <div class="eyebrow" style="color:{BRASS};">ROUTING LOGIC</div>
            <div style="font-family:'IBM Plex Mono',monospace; font-size:0.82rem; line-height:2.0; color:#C9C4B6; margin-top:10px;">
                <div>auditor_node → <span style="color:{VERMILION};">retrieval_score ≤ 2</span> → finalize (insufficient context)</div>
                <div>auditor_node → retrieval_score &gt; 2 → verdict_node</div>
                <div>verdict_node → <span style="color:{FOREST};">PASS</span> → audit_log_node → finalize</div>
                <div>verdict_node → <span style="color:{VERMILION};">FAIL</span> → rootcause_node → audit_log_node → repair_node</div>
                <div>repair_node → retries &lt; max_retries → back to auditor_node</div>
                <div>repair_node → retries ≥ max_retries → finalize (max retries reached)</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # If a pre-rendered graph image also exists on disk (e.g. app/data/graph.png), show it too
    for candidate in [APP_DIR / "data" / "graph.png", APP_DIR / "data" / "graph2.png"]:
        if candidate.exists():
            st.write("")
            st.markdown(f'<div class="eyebrow" style="color:{BRASS};">SAVED DIAGRAM ({candidate.name})</div>', unsafe_allow_html=True)
            st.image(str(candidate), width='stretch')




# =============================================================================
# ROUTER
# =============================================================================
active_page = st.session_state.pop("_nav_override", None) or page

if active_page == "Overview":
    render_overview()
elif active_page == "Ask a Question":
    render_ask_question()
elif active_page == "Audit History":
    render_history()
elif active_page == "Analytics":
    render_analytics()
elif active_page == "Pipeline Graph":
    render_pipeline_graph()