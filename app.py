"""CampusGuide: Student Handbook & Academic Regulations Assistant for Mount Carmel College, Autonomous.

Run: streamlit run app.py
Clean, realistic light-theme portal for students to ask questions about college policies.
"""
import html
import os
import re
import time

import streamlit as st

REFUSAL = "I don't know based on the provided documents."

# Human-readable policy titles mapped from filenames
POLICY_TITLES = {
    "attendance_regulations.md": "Attendance & Examination Eligibility Policy",
    "code_of_conduct.md": "Student Code of Conduct & Dress Code Guidelines",
    "continuous_internal_assessment.md": "Continuous Internal Assessment (CIA) Regulations",
    "end_semester_examinations.md": "End Semester Examination (ESE) Regulations",
    "grievance_redressal_policy.md": "Student Grievance Redressal Mechanism",
    "promotion_and_awards.md": "Academic Promotion Criteria & Graduation Awards",
    "results_and_revaluation.md": "Results, Revaluation & Photocopy Regulations",
}

def get_friendly_source(filename: str) -> str:
    """Return a clean, human-friendly policy title instead of a raw filename."""
    clean_name = filename.strip()
    return POLICY_TITLES.get(clean_name, clean_name.replace(".md", "").replace("_", " ").title())


# --------------------------------------------------------------------------
# Pipeline Wiring
# --------------------------------------------------------------------------
def get_answer(question: str):
    from ask import answer_query

    result = answer_query(question)
    answer_text = result.get("answer", "")
    chunks = [
        {"file": c.get("source", "unknown"), "text": c.get("content", "")}
        for c in result.get("retrieved_chunks", [])
    ]
    return answer_text, chunks


def normalize(result):
    """Accept a string, (answer, sources) tuple, or dict and return (answer, sources)."""
    answer, sources = result, []
    if isinstance(result, tuple) and result:
        answer = result[0]
        sources = result[1] if len(result) > 1 else []
    elif isinstance(result, dict):
        answer = result.get("answer", "")
        sources = result.get("sources") or result.get("chunks") or []
    clean = []
    for s in sources or []:
        if isinstance(s, dict):
            clean.append({
                "file": s.get("file") or s.get("source") or "unknown",
                "text": s.get("text") or s.get("document") or ""
            })
        else:
            clean.append({"file": str(s), "text": ""})
    if not clean:
        for f in dict.fromkeys(re.findall(r"\[Source:\s*([^\]]+)\]", str(answer))):
            clean.append({"file": f.strip(), "text": ""})
    return str(answer), clean


# --------------------------------------------------------------------------
# Page Setup & Crisp Light Theme CSS
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="MCC CampusGuide | Mount Carmel College",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;1,600&display=swap');

/* Force Light Theme Colors Globally */
:root {
    color-scheme: light !important;
}

html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    background-color: #f8fafc !important;
    color: #1e293b !important;
}

.stApp {
    background: #f8fafc !important;
}

/* Force dark readable text everywhere */
p, span, label, div, h1, h2, h3, h4, h5, h6, li, a {
    color: #1e293b !important;
}

/* Header Banner */
.mcc-banner {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-top: 5px solid #1e3a8a !important;
    border-radius: 16px !important;
    padding: 1.8rem 2.2rem !important;
    margin-bottom: 1.5rem !important;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.05) !important;
}

.mcc-crest-pill {
    display: inline-flex !important;
    align-items: center !important;
    gap: 8px !important;
    background: #eff6ff !important;
    border: 1px solid #bfdbfe !important;
    color: #1d4ed8 !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    padding: 0.35rem 0.9rem !important;
    border-radius: 999px !important;
    margin-bottom: 0.75rem !important;
}

.mcc-main-title {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-size: 2.15rem !important;
    font-weight: 700 !important;
    color: #0f172a !important;
    margin: 0 0 0.4rem 0 !important;
    line-height: 1.25 !important;
}

.mcc-description {
    color: #475569 !important;
    font-size: 1rem !important;
    line-height: 1.6 !important;
    margin: 0 0 1rem 0 !important;
    max-width: 850px !important;
}

.mcc-highlights {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 10px !important;
    align-items: center !important;
}

.mcc-highlight-pill {
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    background: #f1f5f9 !important;
    border: 1px solid #e2e8f0 !important;
    padding: 0.35rem 0.8rem !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    color: #334155 !important;
    font-weight: 600 !important;
}

/* Category Sections */
.cat-heading {
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    color: #1e3a8a !important;
    margin-bottom: 0.6rem !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}

/* Question Buttons */
div.stButton > button {
    background: #ffffff !important;
    border: 1.5px solid #e2e8f0 !important;
    color: #1e293b !important;
    font-size: 0.92rem !important;
    font-weight: 550 !important;
    border-radius: 12px !important;
    padding: 0.75rem 1rem !important;
    text-align: left !important;
    justify-content: flex-start !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
    transition: all 0.15s ease-in-out !important;
    margin-bottom: 0.4rem !important;
}

div.stButton > button:hover {
    background: #f8fafc !important;
    border-color: #2563eb !important;
    color: #1d4ed8 !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.08) !important;
    transform: translateY(-1px) !important;
}

div.stButton > button p, div.stButton > button span {
    color: #1e293b !important;
}

div.stButton > button:hover p, div.stButton > button:hover span {
    color: #1d4ed8 !important;
}

/* User Message Bubble */
.user-message-card {
    background: #f0f7ff !important;
    border: 1px solid #bfdbfe !important;
    border-left: 5px solid #2563eb !important;
    border-radius: 14px !important;
    padding: 1.1rem 1.4rem !important;
    margin: 0.6rem 0 1rem 0 !important;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.05) !important;
}

.user-badge-label {
    font-size: 0.76rem !important;
    font-weight: 700 !important;
    color: #1d4ed8 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    margin-bottom: 0.35rem !important;
}

.user-query-content {
    font-size: 1.05rem !important;
    color: #0f172a !important;
    font-weight: 600 !important;
    line-height: 1.5 !important;
}

/* Assistant Message Bubble */
.assistant-message-card {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-left: 5px solid #059669 !important;
    border-radius: 14px !important;
    padding: 1.3rem 1.5rem !important;
    margin: 0.6rem 0 1rem 0 !important;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.05) !important;
}

.assistant-header-row {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    margin-bottom: 0.8rem !important;
    padding-bottom: 0.5rem !important;
    border-bottom: 1px solid #f1f5f9 !important;
}

.assistant-title-badge {
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    color: #047857 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
}

.assistant-body-text {
    font-size: 1.02rem !important;
    color: #1e293b !important;
    line-height: 1.72 !important;
    font-weight: 450 !important;
    margin-bottom: 0.9rem !important;
}

.assistant-body-text strong {
    color: #0f172a !important;
    font-weight: 700 !important;
}

/* Refusal Notice */
.refusal-box {
    background: #fffbeb !important;
    border: 1px solid #fde68a !important;
    border-left: 5px solid #d97706 !important;
    border-radius: 12px !important;
    padding: 1.1rem 1.3rem !important;
    margin: 0.6rem 0 !important;
}

.refusal-box-title {
    color: #92400e !important;
    font-weight: 700 !important;
    font-size: 0.96rem !important;
    margin-bottom: 0.35rem !important;
}

.refusal-box-desc {
    color: #78350f !important;
    font-size: 0.9rem !important;
    line-height: 1.6 !important;
}

/* Policy Citation Tags */
.policy-citations-wrap {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
    align-items: center !important;
    margin-top: 0.6rem !important;
    padding-top: 0.6rem !important;
    border-top: 1px solid #f1f5f9 !important;
}

.policy-citation-pill {
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    background: #f0fdf4 !important;
    border: 1px solid #bbf7d0 !important;
    color: #15803d !important;
    padding: 0.35rem 0.85rem !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
}

/* Policy Excerpt Expander */
div[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    margin-top: 0.8rem !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02) !important;
}

div[data-testid="stExpander"] summary {
    color: #334155 !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.7rem 1rem !important;
}

div[data-testid="stExpander"] summary:hover {
    color: #1e3a8a !important;
}

div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
    background: #f8fafc !important;
    border-top: 1px solid #e2e8f0 !important;
    padding: 1rem 1.25rem !important;
}

div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] * {
    color: #334155 !important;
}

.excerpt-card {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-left: 4px solid #3b82f6 !important;
    border-radius: 10px !important;
    padding: 0.9rem 1.1rem !important;
    margin-bottom: 0.75rem !important;
}

.excerpt-header {
    color: #1d4ed8 !important;
    font-size: 0.85rem !important;
    font-weight: 700 !important;
    margin-bottom: 0.4rem !important;
}

.excerpt-text {
    color: #334155 !important;
    font-size: 0.9rem !important;
    line-height: 1.62 !important;
}

/* Chat Input Bar */
div[data-testid="stChatInput"] {
    background: #ffffff !important;
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05) !important;
}

div[data-testid="stChatInput"] textarea {
    color: #0f172a !important;
    background: transparent !important;
    font-size: 0.96rem !important;
}

div[data-testid="stChatInput"] textarea::placeholder {
    color: #94a3b8 !important;
}

/* Sidebar Light Styling */
section[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
}

.sidebar-box {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 14px !important;
    padding: 1.15rem !important;
    margin-bottom: 1.15rem !important;
}

.sidebar-box-title {
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    color: #0f172a !important;
    margin-bottom: 0.6rem !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}

.policy-list-item {
    font-size: 0.83rem !important;
    color: #334155 !important;
    padding: 0.35rem 0 !important;
    border-bottom: 1px solid #f1f5f9 !important;
    display: flex !important;
    align-items: center !important;
    gap: 7px !important;
}

.policy-list-item:last-child {
    border-bottom: none !important;
}

.green-dot {
    width: 7px !important;
    height: 7px !important;
    border-radius: 50% !important;
    background-color: #10b981 !important;
    flex-shrink: 0 !important;
}

.footer-credits {
    text-align: center !important;
    font-size: 0.82rem !important;
    color: #64748b !important;
    margin-top: 3rem !important;
    padding: 1.2rem !important;
    border-top: 1px solid #e2e8f0 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Main Header Banner
# --------------------------------------------------------------------------
st.markdown(
    """
<div class="mcc-banner">
  <div class="mcc-crest-pill">
    <span>🏛️ Mount Carmel College (Autonomous), Bengaluru</span>
  </div>
  <h1 class="mcc-main-title">CampusGuide: Student Handbook Portal</h1>
  <p class="mcc-description">
    Welcome to the official student policy assistant. Get immediate, accurate answers regarding examination regulations, attendance requirements, revaluation timelines, CIA evaluation patterns, and campus conduct rules.
  </p>
  <div class="mcc-highlights">
    <div class="mcc-highlight-pill"><span>📘</span> 7 Active College Policy Handbooks</div>
    <div class="mcc-highlight-pill"><span>🎯</span> Verified Policy Excerpts Only</div>
    <div class="mcc-highlight-pill"><span>🏛️</span> Autonomous Examination Centre Rules</div>
    <div class="mcc-highlight-pill"><span>🛡️</span> Zero Speculation Guarantee</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Sidebar: Institution Services & Policy Scope
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
    <div class="sidebar-box">
      <div class="sidebar-box-title"><span>🏛️</span> College Information</div>
      <p style="font-size: 0.84rem; color: #334155; margin-bottom: 0.5rem; line-height: 1.5;">
        <strong>Mount Carmel College, Autonomous</strong><br>
        Affiliated with Bengaluru City University<br>
        Re-accredited with 'A+' Grade by NAAC<br>
        <em>Motto: Amor et Servitium (Love and Service)</em>
      </p>
      <p style="font-size: 0.8rem; color: #64748b; margin: 0; line-height: 1.4;">
        📍 58, Palace Road, Vasanth Nagar, Bengaluru - 560052
      </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="sidebar-box">
      <div class="sidebar-box-title"><span>📋</span> Available Policy Handbooks</div>
      <div class="policy-list-item"><span class="green-dot"></span> Attendance & Exam Eligibility</div>
      <div class="policy-list-item"><span class="green-dot"></span> Code of Conduct & Dress Code</div>
      <div class="policy-list-item"><span class="green-dot"></span> Continuous Internal Assessment (CIA)</div>
      <div class="policy-list-item"><span class="green-dot"></span> End Semester Examination Regulations</div>
      <div class="policy-list-item"><span class="green-dot"></span> Student Grievance Redressal Mechanism</div>
      <div class="policy-list-item"><span class="green-dot"></span> Academic Promotion Criteria & Awards</div>
      <div class="policy-list-item"><span class="green-dot"></span> Results, Revaluation & Photocopy</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="sidebar-box">
      <div class="sidebar-box-title"><span>📞</span> Office of Examination Centre</div>
      <p style="font-size: 0.83rem; color: #334155; margin-bottom: 0.4rem; line-height: 1.5;">
        Controller of Examinations Office<br>
        Office Hours: Mon &ndash; Fri (9:00 AM &ndash; 4:00 PM)<br>
        Saturday: 9:00 AM &ndash; 1:00 PM
      </p>
      <p style="font-size: 0.81rem; color: #2563eb; margin: 0; font-weight: 600;">
        ✉️ grievancestudents@mccblr.edu.in
      </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if st.button("🔄 Start New Conversation", use_container_width=True):
        st.session_state.history = []
        st.rerun()

# --------------------------------------------------------------------------
# State Management & Interactive Prompt Categories
# --------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "pending" not in st.session_state:
    st.session_state.pending = None

def select_question(q_text: str):
    st.session_state.pending = q_text

CATEGORIES = [
    {
        "category": "📋 Attendance & Eligibility",
        "questions": [
            "Can I write my semester-end exams if my attendance is only 70% as an undergraduate student?",
            "What minimum attendance percentage do master's students need to maintain in each subject?",
            "What happens if a student has less than 35% attendance in all subjects of a semester?",
        ]
    },
    {
        "category": "📝 Exams & Revaluation",
        "questions": [
            "Within how many working days must a student apply for photocopy or revaluation of results?",
            "What is the minimum mark in ESE required for a student to apply for revaluation?",
            "How is the grading split between internal continuous assessment and end-of-semester theory exams?",
        ]
    },
    {
        "category": "👗 Campus Conduct & Welfare",
        "questions": [
            "Is it permitted to make phone calls or use mobile devices during lectures?",
            "What types of T-shirts are prohibited for boys under the dress code?",
            "What is the official email address for the Students Grievance Redressal Committee?",
        ]
    }
]

# Display Clickable Frequent Questions when history is empty
if not st.session_state.history:
    st.markdown("<h3 style='font-size: 1.18rem; font-weight: 700; color: #0f172a; margin-bottom: 0.9rem;'>💡 Common Student Inquiries (Click any to ask)</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]

    for idx, cat_data in enumerate(CATEGORIES):
        with cols[idx]:
            st.markdown(f"<div class='cat-heading'>{cat_data['category']}</div>", unsafe_allow_html=True)
            for q_idx, q in enumerate(cat_data["questions"]):
                st.button(
                    q,
                    key=f"q_{idx}_{q_idx}",
                    on_click=select_question,
                    args=(q,),
                    use_container_width=True
                )

# Chat Input Field
typed_input = st.chat_input("Ask any question regarding Mount Carmel College attendance, exams, fees, conduct...")
active_question = typed_input or st.session_state.pending
st.session_state.pending = None

if active_question:
    st.session_state.history.append({"role": "user", "content": active_question})
    try:
        with st.spinner("Retrieving verified college policy text..."):
            ans_text, raw_sources = normalize(get_answer(active_question))
        error_msg = None
    except Exception as exc:
        ans_text, raw_sources, error_msg = "", [], str(exc)[:300]
    
    st.session_state.history.append({
        "role": "assistant",
        "content": ans_text,
        "sources": raw_sources,
        "error": error_msg
    })
    st.rerun()

# --------------------------------------------------------------------------
# Render Conversation Feed
# --------------------------------------------------------------------------
for item in st.session_state.history:
    if item["role"] == "user":
        st.markdown(
            f"""
        <div class="user-message-card">
          <div class="user-badge-label">👩‍🎓 Your Question</div>
          <div class="user-query-content">{html.escape(item["content"])}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        if item.get("error"):
            st.error(f"Error querying assistant: {item['error']}")
            continue

        raw_ans = item["content"]
        is_refusal = (REFUSAL.lower() in raw_ans.lower())
        
        # Clean answer for student presentation
        clean_ans = re.sub(r"\[Source:[^\]]*\]", "", raw_ans).strip()

        st.markdown(
            f"""
        <div class="assistant-message-card">
          <div class="assistant-header-row">
            <div class="assistant-title-badge">
              <span>🏛️</span> Official Policy Guidance
            </div>
          </div>
          """
            + (
                f"""
          <div class="refusal-box">
            <div class="refusal-box-title">⚠️ Policy Scope Notice</div>
            <div class="refusal-box-desc">
              <strong>"{html.escape(REFUSAL)}"</strong><br><br>
              This specific inquiry is not covered under the college's active academic regulations and student handbook documents (Attendance, Examinations, CIA, Promotion, Revaluation, Grievances, and Conduct).<br><br>
              To ensure compliance and avoid incorrect guidance, policy questions outside these published rules are not answered automatically. Please visit the <strong>Office of the Controller of Examinations</strong> or relevant department head for clarification.
            </div>
          </div>
          """
                if is_refusal
                else f"""
          <div class="assistant-body-text">{html.escape(clean_ans)}</div>
          """
            )
            + f"""
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Friendly Policy Citations
        if not is_refusal:
            unique_files = list(dict.fromkeys(s["file"] for s in item.get("sources", []) if s.get("file")))
            if unique_files:
                citations_html = "".join(
                    f'<span class="policy-citation-pill">📖 {html.escape(get_friendly_source(f))}</span>'
                    for f in unique_files
                )
                st.markdown(
                    f"""
                <div class="policy-citations-wrap" style="margin-left: 0.5rem; margin-bottom: 0.6rem;">
                  <span style="font-size: 0.83rem; font-weight: 700; color: #475569;">Verified Source Handbook:</span>
                  {citations_html}
                </div>
                """,
                    unsafe_allow_html=True,
                )

        # Clean Student-Facing Evidence Passages
        passages = [s for s in item.get("sources", []) if s.get("text")]
        if passages:
            with st.expander("📄 View Official Handbook Excerpts"):
                for p_idx, s in enumerate(passages):
                    policy_title = get_friendly_source(s["file"])
                    st.markdown(
                        f"""
                    <div class="excerpt-card">
                      <div class="excerpt-header">{html.escape(policy_title)}</div>
                      <div class="excerpt-text">{html.escape(s['text'][:600])}</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

# --------------------------------------------------------------------------
# Footer
# --------------------------------------------------------------------------
st.markdown(
    """
<div class="footer-credits">
  <strong>Mount Carmel College (Autonomous), Bengaluru</strong> &bull; Student Handbook & CampusGuide Portal<br>
  Official regulations from Examination Centre &bull; Palace Road, Vasanth Nagar, Bengaluru &bull; Estd. 1948
</div>
""",
    unsafe_allow_html=True,
)
