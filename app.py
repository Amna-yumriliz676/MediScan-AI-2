"""
MediScan AI — Multi-Agent Medicine Assistant
Complete Streamlit app ready for GitHub + Streamlit Cloud
"""

import streamlit as st
import pandas as pd
from PIL import Image

from database import (
    MEDICINES, INTERACTIONS, PHARMACIES,
    search_medicine, check_interaction,
    get_all_medicine_names, get_all_pharmacies
)
from ocr_utils import extract_text_from_image, extract_medicine_names
from verifier import verify_by_barcode, verify_by_name, get_verification_checklist
from agents import CoordinatorAgent, get_llm, AGENT_INFO


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="MediScan AI",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}
    .block-container { padding: 1.5rem 2rem; max-width: 100%; }
    .stApp { background: #f7f8fc; }

    [data-testid="stSidebar"] {
        background: #0f172a;
        min-width: 280px !important;
        max-width: 280px !important;
    }
    [data-testid="stSidebar"] * { color: #cbd5e1 !important; }
    [data-testid="stSidebar"] .stRadio > label { display: none; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] { gap: 4px; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
        background: transparent; padding: 10px 16px; border-radius: 10px;
        cursor: pointer; transition: all 0.2s; font-weight: 500;
        font-size: 0.88rem; width: 100%; border: none;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
        background: rgba(255,255,255,0.06) !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) {
        background: linear-gradient(135deg, #10b981, #06b6d4) !important;
        box-shadow: 0 4px 12px rgba(16,185,129,0.35);
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) * {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stRadio input[type="radio"] { display: none; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > div:first-child {
        display: none;
    }

    .brand { display: flex; align-items: center; gap: 0.7rem; padding: 1rem 0.5rem 1.5rem 0.5rem;
             border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 1rem; }
    .brand-logo { width: 42px; height: 42px;
        background: linear-gradient(135deg, #10b981, #06b6d4);
        border-radius: 12px; display: flex; align-items: center;
        justify-content: center; font-size: 1.3rem;
        box-shadow: 0 4px 12px rgba(16,185,129,0.4); }
    .brand-name { font-weight: 800; font-size: 1.1rem; color: #ffffff !important; letter-spacing: -0.3px; }
    .brand-sub { font-size: 0.68rem; color: #10b981 !important; font-weight: 700;
                 text-transform: uppercase; letter-spacing: 1px; }

    .page-header { margin-bottom: 1.5rem; }
    .page-title { font-size: 1.7rem; font-weight: 800; color: #0f172a;
                  letter-spacing: -0.6px; margin: 0; }
    .page-sub { font-size: 0.88rem; color: #64748b; margin-top: 0.3rem; }

    .hero {
        background: linear-gradient(135deg, #10b981 0%, #06b6d4 100%);
        padding: 1.8rem 2rem; border-radius: 18px; color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 15px 35px -15px rgba(16,185,129,0.4);
        position: relative; overflow: hidden;
    }
    .hero::before { content: ""; position: absolute; top: -50%; right: -10%;
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(255,255,255,0.15), transparent 70%);
        border-radius: 50%; }
    .hero h1 { font-size: 1.8rem; font-weight: 800; margin: 0 0 0.4rem 0;
               letter-spacing: -0.5px; position: relative; }
    .hero p { font-size: 0.95rem; opacity: 0.95; margin: 0; position: relative; }

    .card { background: white; border: 1px solid #e2e8f0; border-radius: 14px;
            padding: 1.2rem 1.3rem; margin-bottom: 1rem; transition: all 0.2s; }
    .card:hover { box-shadow: 0 8px 20px -10px rgba(0,0,0,0.1); border-color: #cbd5e1; }

    .kpi-card { background: white; padding: 1.2rem 1.3rem; border-radius: 14px;
                border: 1px solid #eef0f4; box-shadow: 0 1px 3px rgba(0,0,0,0.03); height: 100%; }
    .kpi-icon { width: 42px; height: 42px; border-radius: 12px; display: flex;
                align-items: center; justify-content: center; font-size: 1.2rem;
                margin-bottom: 0.8rem; }
    .kpi-icon.green { background: #d1fae5; }
    .kpi-icon.blue { background: #dbeafe; }
    .kpi-icon.orange { background: #ffedd5; }
    .kpi-icon.purple { background: #f3e8ff; }
    .kpi-icon.red { background: #fee2e2; }
    .kpi-label { font-size: 0.72rem; color: #64748b; font-weight: 700;
                 text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem; }
    .kpi-value { font-size: 1.5rem; font-weight: 800; color: #0f172a; line-height: 1.1; }

    .sev { display: inline-block; padding: 4px 12px; border-radius: 20px;
           font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
           letter-spacing: 0.5px; }
    .sev-severe { background: #fee2e2; color: #991b1b; }
    .sev-moderate { background: #fef3c7; color: #92400e; }
    .sev-safe { background: #d1fae5; color: #065f46; }

    .info-row { display: flex; padding: 0.6rem 0; border-bottom: 1px solid #f1f5f9;
                font-size: 0.88rem; }
    .info-row:last-child { border-bottom: none; }
    .info-label { font-weight: 600; color: #64748b; min-width: 140px; flex-shrink: 0; }
    .info-value { color: #0f172a; flex: 1; }

    .stButton > button { border-radius: 10px; font-weight: 600; font-size: 0.85rem;
        padding: 0.5rem 1.1rem; transition: all 0.2s ease;
        border: 1px solid #e2e8f0; background: white; color: #334155; }
    .stButton > button:hover { border-color: #a7f3d0; color: #10b981;
                                transform: translateY(-1px); }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #10b981, #06b6d4);
        border: none; color: white;
        box-shadow: 0 4px 12px -4px rgba(16,185,129,0.5); }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 8px 20px -6px rgba(16,185,129,0.6); color: white; }

    .stTextInput input, .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] > div {
        border-radius: 10px !important; border-color: #e2e8f0 !important;
        font-size: 0.88rem !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 3px rgba(16,185,129,0.1) !important; }

    [data-testid="stFileUploader"] {
        border-radius: 14px; border: 2px dashed #a7f3d0;
        background: #f0fdf4; padding: 1rem; }
    [data-testid="stFileUploader"]:hover { border-color: #10b981; background: #ecfdf5; }

    .streamlit-expanderHeader { font-weight: 600; font-size: 0.9rem;
        color: #334155; background: #f8fafc !important; border-radius: 10px !important; }

    .empty-state { text-align: center; padding: 3rem 1rem; color: #94a3b8; }
    .empty-state-icon { font-size: 3rem; margin-bottom: 0.7rem; opacity: 0.4; }

    [data-testid="stSidebar"] [data-testid="stMetric"] {
        background: rgba(255,255,255,0.04); padding: 0.7rem 0.9rem;
        border-radius: 10px; border: 1px solid rgba(255,255,255,0.06);
        margin-bottom: 0.5rem; }
    [data-testid="stSidebar"] [data-testid="stMetricLabel"] * {
        color: #94a3b8 !important; font-size: 0.75rem !important; }
    [data-testid="stSidebar"] [data-testid="stMetricValue"] * {
        color: #ffffff !important; font-size: 1.3rem !important; font-weight: 700 !important; }

    .agent-card { background: white; border: 1px solid #e5e7eb;
        border-radius: 14px; padding: 1rem; height: 100%; transition: all 0.2s; }
    .agent-card:hover { transform: translateY(-2px);
        box-shadow: 0 8px 20px -8px rgba(0,0,0,0.1); border-color: #10b981; }
    .agent-icon { width: 38px; height: 38px; border-radius: 10px;
        background: #d1fae5; display: flex; align-items: center;
        justify-content: center; font-size: 1.1rem; margin-bottom: 0.5rem; }
    .agent-name { font-size: 0.9rem; font-weight: 700; color: #111827;
                  margin-bottom: 0.2rem; }
    .agent-desc { font-size: 0.75rem; color: #6b7280; line-height: 1.3; }

    [data-testid="stChatMessage"] {
        background: white; border: 1px solid #e5e7eb;
        border-radius: 14px; padding: 1rem 1.2rem; }

    @media (max-width: 768px) {
        .block-container { padding: 1rem !important; }
        .hero h1 { font-size: 1.4rem; }
        .page-title { font-size: 1.3rem; } }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
    <div class="brand">
        <div class="brand-logo">💊</div>
        <div>
            <div class="brand-name">MediScan AI</div>
            <div class="brand-sub">Multi-Agent System</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["🏠  Home", "🤖  Chat with Agents", "📸  Prescription Reader",
         "💊  Medicine Verifier", "⚗️  Interaction Checker",
         "🏪  Pharmacy Finder", "💾  Database"],
        label_visibility="collapsed"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🔑 Groq API Key")
    api_key = st.text_input("Groq Key", type="password", placeholder="gsk_...",
                            label_visibility="collapsed",
                            help="Free key: console.groq.com")
    if api_key:
        st.session_state["groq_api_key"] = api_key
        st.success("✅ Key set")
    else:
        st.caption("[Get free key →](https://console.groq.com)")

    st.markdown("<br>")
    st.markdown("### 📊 Stats")
    st.metric("Medicines", len(MEDICINES))
    st.metric("Interactions", len(INTERACTIONS))
    st.metric("Pharmacies", len(PHARMACIES))
    st.metric("AI Agents", 5)

    st.markdown("<br>")
    st.caption("⚠️ Educational purposes only.")


# ============================================================
# HOME
# ============================================================
if page == "🏠  Home":
    st.markdown("""
    <div class="hero">
        <h1>💊 MediScan AI</h1>
        <p>Multi-agent medicine assistant · Prescription OCR · Verified database · 5 AI agents</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""<div class="kpi-card"><div class="kpi-icon green">📸</div>
        <div class="kpi-label">Prescription Scan</div>
        <div class="kpi-value">OCR + AI</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="kpi-card"><div class="kpi-icon blue">💊</div>
        <div class="kpi-label">Medicine Verify</div>
        <div class="kpi-value">Barcode</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-icon orange">⚗️</div>
        <div class="kpi-label">Interactions</div>
        <div class="kpi-value">{len(INTERACTIONS)} Pairs</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown("""<div class="kpi-card"><div class="kpi-icon purple">🤖</div>
        <div class="kpi-label">AI Agents</div>
        <div class="kpi-value">5 Active</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>")
    st.markdown("### 🤖 Our AI Agents")
    cols = st.columns(5)
    for i, agent in enumerate(AGENT_INFO):
        with cols[i]:
            st.markdown(f"""
            <div class="agent-card">
                <div class="agent-icon">{agent['icon']}</div>
                <div class="agent-name">{agent['name']}</div>
                <div class="agent-desc">{agent['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>")
    st.markdown("### 🎯 Features")

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("""
        <div class="card">
            <h3 style="margin:0 0 0.5rem 0; color:#0f172a;">💬 Chat with 5 AI Agents</h3>
            <p style="color:#64748b; font-size:0.9rem; margin:0;">
                Ask about medicines, interactions, or symptoms. Coordinator Agent
                automatically routes your query to the right specialist.
            </p>
        </div>
        <div class="card">
            <h3 style="margin:0 0 0.5rem 0; color:#0f172a;">📸 Prescription Reader</h3>
            <p style="color:#64748b; font-size:0.9rem; margin:0;">
                Upload your prescription photo — OCR + AI extracts medicine names instantly.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="card">
            <h3 style="margin:0 0 0.5rem 0; color:#0f172a;">💊 Medicine Verifier</h3>
            <p style="color:#64748b; font-size:0.9rem; margin:0;">
                Verify medicines by barcode or name against our DRAP-registered database.
            </p>
        </div>
        <div class="card">
            <h3 style="margin:0 0 0.5rem 0; color:#0f172a;">🏪 Verified Pharmacy Finder</h3>
            <p style="color:#64748b; font-size:0.9rem; margin:0;">
                Find DRAP-registered pharmacies near you with ratings & contact info.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.info("💡 **Get started:** Add your free Groq API key in the sidebar, then try the **Chat with Agents** tab!")


# ============================================================
# CHAT WITH AGENTS
# ============================================================
elif page == "🤖  Chat with Agents":
    st.markdown("""
    <div class="hero">
        <h1>🤖 Chat with AI Agents</h1>
        <p>Ask about medicines, interactions, or symptoms. Coordinator auto-routes to the right specialist.</p>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(5)
    for i, agent in enumerate(AGENT_INFO):
        with cols[i]:
            st.markdown(f"""
            <div class="agent-card">
                <div class="agent-icon">{agent['icon']}</div>
                <div class="agent-name">{agent['name']}</div>
                <div class="agent-desc">{agent['handles']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if not st.session_state.messages:
        st.markdown("##### 💡 Try these:")
        sug_cols = st.columns(3)
        suggestions = [
            "What is Panadol used for?",
            "Is Warfarin + Aspirin safe?",
            "I have fever and headache",
            "Tell me about Augmentin",
            "Pharmacies near me",
            "Side effects of Lipitor?"
        ]
        for i, sug in enumerate(suggestions):
            with sug_cols[i % 3]:
                if st.button(sug, key=f"sug_{i}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": sug})
                    st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "💊"):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about medicines, interactions, or symptoms..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        llm = get_llm()
        if llm is None:
            with st.chat_message("assistant", avatar="💊"):
                st.error("⚠️ Enter your Groq API key in the sidebar first.")
        else:
            with st.chat_message("assistant", avatar="💊"):
                with st.spinner("🤖 Coordinator is routing your query..."):
                    try:
                        coordinator = CoordinatorAgent(llm)
                        response = coordinator.route(prompt)
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    except Exception as e:
                        err = f"❌ Error: {str(e)}"
                        st.error(err)
                        st.session_state.messages.append({"role": "assistant", "content": err})

    if st.session_state.messages:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()


# ============================================================
# PRESCRIPTION READER
# ============================================================
elif page == "📸  Prescription Reader":
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">📸 Prescription Reader</h1>
        <div class="page-sub">Upload prescription photo → AI extracts medicine names</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 📤 Upload Prescription")
        uploaded = st.file_uploader("Image", type=["jpg", "jpeg", "png"],
                                    label_visibility="collapsed")
        if uploaded:
            st.image(Image.open(uploaded), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 🔍 Extracted Medicines")

        if not uploaded:
            st.markdown("""<div class="empty-state">
                <div class="empty-state-icon">📸</div>
                <p>Upload a prescription</p></div>""", unsafe_allow_html=True)
        else:
            with st.spinner("🤖 Reading..."):
                uploaded.seek(0)
                text = extract_text_from_image(uploaded)
                found = extract_medicine_names(text)

            if "OCR_ERROR" in text:
                st.error("❌ Could not read image. Try a clearer photo.")
            elif found:
                st.success(f"✅ Found **{len(found)}** medicine(s)")
                for m in found:
                    color = "#10b981" if m["confidence"] > 0.85 else "#f59e0b"
                    st.markdown(f"""
                    <div class="card">
                        <h4 style="margin:0 0 0.4rem 0; color:#0f172a;">💊 {m['medicine']}</h4>
                        <div class="info-row"><span class="info-label">Generic</span>
                        <span class="info-value">{m['generic']}</span></div>
                        <div class="info-row"><span class="info-label">Confidence</span>
                        <span class="info-value" style="color:{color}; font-weight:700;">
                        {m['confidence']*100:.0f}%</span></div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ No medicines detected.")

            with st.expander("📄 Raw OCR Text"):
                st.text(text)
        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# MEDICINE VERIFIER
# ============================================================
elif page == "💊  Medicine Verifier":
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">💊 Medicine Verifier</h1>
        <div class="page-sub">Verify medicines by barcode or name</div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔢 By Barcode", "🔤 By Name"])

    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        barcode = st.text_input("Barcode", placeholder="e.g., 8901234567890")
        if st.button("🔍  Verify Barcode", type="primary", use_container_width=True):
            result = verify_by_barcode(barcode)
            if result["status"] == "GENUINE":
                st.success(result["message"])
                if result["medicine"]:
                    med = result["medicine"]
                    st.markdown(f"""
                    <div class="card">
                        <div class="info-row"><span class="info-label">Brand</span><span class="info-value">{med['name']}</span></div>
                        <div class="info-row"><span class="info-label">Generic</span><span class="info-value">{med['generic']}</span></div>
                        <div class="info-row"><span class="info-label">Manufacturer</span><span class="info-value">{med['manufacturer']}</span></div>
                        <div class="info-row"><span class="info-label">Category</span><span class="info-value">{med['category']}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
            elif result["status"] == "SUSPICIOUS":
                st.warning(result["message"])
                st.markdown("**🚨 Recommended:** Do NOT use. Report to [DRAP](https://www.drap.gov.pk).")
            else:
                st.error(result["message"])
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        name = st.text_input("Medicine name", placeholder="e.g., Panadol")
        if st.button("🔍  Verify Name", type="primary", use_container_width=True):
            result = verify_by_name(name)
            if result["status"] == "GENUINE":
                st.success(result["message"])
                med = result["medicine"]
                st.markdown(f"""
                <div class="card">
                    <div class="info-row"><span class="info-label">Uses</span><span class="info-value">{med['uses']}</span></div>
                    <div class="info-row"><span class="info-label">Dosage</span><span class="info-value">{med['dosage']}</span></div>
                    <div class="info-row"><span class="info-label">Side Effects</span><span class="info-value">{med['side_effects']}</span></div>
                </div>
                """, unsafe_allow_html=True)
            elif result["status"] == "SUSPICIOUS":
                st.warning(result["message"])
            else:
                st.error(result["message"])
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### ✅ Visual Verification Checklist")
    for item in get_verification_checklist():
        st.markdown(f"- {item}")


# ============================================================
# INTERACTION CHECKER
# ============================================================
elif page == "⚗️  Interaction Checker":
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">⚗️ Drug Interaction Checker</h1>
        <div class="page-sub">Check if two medicines are safe together</div>
    </div>
    """, unsafe_allow_html=True)

    med_names = get_all_medicine_names()
    col1, col2 = st.columns(2)
    with col1:
        drug_a = st.selectbox("💊 First Medicine", med_names, index=0)
    with col2:
        drug_b = st.selectbox("💊 Second Medicine", med_names, index=1)

    if st.button("🔍  Check Interaction", type="primary", use_container_width=True):
        result = check_interaction(drug_a, drug_b)
        sev = result["severity"]
        badge = {"SEVERE": "sev-severe", "MODERATE": "sev-moderate", "SAFE": "sev-safe"}.get(sev, "sev-safe")

        st.markdown(f"""
        <div class="card" style="margin-top:1rem;">
            <h4 style="margin:0 0 0.8rem 0; color:#0f172a;">Result: {drug_a} + {drug_b}</h4>
            <div class="info-row"><span class="info-label">Severity</span>
            <span class="info-value"><span class="sev {badge}">{sev}</span></span></div>
            <div class="info-row"><span class="info-label">Risk</span>
            <span class="info-value">{result['risk']}</span></div>
            <div class="info-row"><span class="info-label">Recommendation</span>
            <span class="info-value">{result['action']}</span></div>
        </div>
        """, unsafe_allow_html=True)

        if sev == "SEVERE":
            st.error("🚨 **SEVERE** — Consult doctor immediately.")
        elif sev == "MODERATE":
            st.warning("⚠️ **MODERATE** — Take precautions. Consult your doctor.")
        else:
            st.success("✅ **SAFE** — No known interaction.")

    st.markdown("---")
    st.markdown("#### 📋 All Known Interactions")
    df = pd.DataFrame([{"Drug A": i["drug_a"], "Drug B": i["drug_b"],
                        "Severity": i["severity"], "Risk": i["risk"]} for i in INTERACTIONS])
    st.dataframe(df, use_container_width=True, hide_index=True)


# ============================================================
# PHARMACY FINDER
# ============================================================
elif page == "🏪  Pharmacy Finder":
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">🏪 Verified Pharmacy Finder</h1>
        <div class="page-sub">DRAP-registered pharmacies near you</div>
    </div>
    """, unsafe_allow_html=True)

    pharmacies = get_all_pharmacies()
    map_data = pd.DataFrame([{"lat": p["lat"], "lon": p["lng"]} for p in pharmacies])
    st.map(map_data, zoom=11, use_container_width=True, height=380)

    st.markdown("### 🏪 All Verified Pharmacies")
    for p in pharmacies:
        st.markdown(f"""
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <h4 style="margin:0 0 0.3rem 0; color:#0f172a;">🏪 {p['name']}</h4>
                    <div style="font-size:0.85rem; color:#64748b;">📍 {p['area']}, {p['city']}</div>
                </div>
                <span class="sev sev-safe">✅ Verified</span>
            </div>
            <div class="info-row" style="margin-top:0.6rem;">
                <span class="info-label">⭐ Rating</span><span class="info-value">{p['rating']}/5</span>
            </div>
            <div class="info-row"><span class="info-label">📞 Phone</span>
            <span class="info-value">{p['phone']}</span></div>
            <div class="info-row"><span class="info-label">🕐 Timings</span>
            <span class="info-value">{p['timings']}</span></div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# DATABASE
# ============================================================
elif page == "💾  Database":
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">💾 Medicine Database</h1>
        <div class="page-sub">Browse verified medicines</div>
    </div>
    """, unsafe_allow_html=True)

    search = st.text_input("🔍 Search", placeholder="Name, generic, uses, category")
    filtered = search_medicine(search) if search.strip() else MEDICINES

    st.caption(f"Showing **{len(filtered)}** of **{len(MEDICINES)}** medicines")

    for med in filtered:
        with st.expander(f"💊 **{med['name']}** — {med['generic']}  ·  _{med['category']}_"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                <div class="card">
                    <div class="info-row"><span class="info-label">Brand</span><span class="info-value">{med['name']}</span></div>
                    <div class="info-row"><span class="info-label">Generic</span><span class="info-value">{med['generic']}</span></div>
                    <div class="info-row"><span class="info-label">Category</span><span class="info-value">{med['category']}</span></div>
                    <div class="info-row"><span class="info-label">Manufacturer</span><span class="info-value">{med['manufacturer']}</span></div>
                    <div class="info-row"><span class="info-label">Barcode</span><span class="info-value">{med['barcode']}</span></div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="card">
                    <div class="info-row"><span class="info-label">Uses</span><span class="info-value">{med['uses']}</span></div>
                    <div class="info-row"><span class="info-label">Dosage</span><span class="info-value">{med['dosage']}</span></div>
                    <div class="info-row"><span class="info-label">Side Effects</span><span class="info-value">{med['side_effects']}</span></div>
                    <div class="info-row"><span class="info-label">Interactions</span><span class="info-value">{med['interactions']}</span></div>
                </div>
                """, unsafe_allow_html=True)


# ============================================================
# FOOTER
# ============================================================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; color:#94a3b8; font-size:0.78rem; padding:1rem 0; border-top:1px solid #e2e8f0;">
    MediScan AI v2.0  ·  5 AI Agents  ·  Streamlit + LangChain + Groq + Tesseract
</div>
""", unsafe_allow_html=True)
