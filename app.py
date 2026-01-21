import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import glob
import os

# 1. SETUP & CONFIG
st.set_page_config(page_title="LFI Risk Pulse", layout="wide")

# CUSTOM CSS: CLEAN MINIMALIST DESIGN
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #000000; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    [data-testid="stSidebar"] a[kind="secondary"], [data-testid="stSidebar"] a[kind="primary"] {
        background-color: #38b6ff !important; color: #FFFFFF !important; border: none !important; font-weight: bold !important;
    }
    .insight-box { background-color: #e8f4f8; padding: 15px; border-radius: 5px; border-left: 5px solid #2E86C1; }
</style>
""", unsafe_allow_html=True)

# 10 High-Signal Questions (Strategy, Technology, Operations)
DEMO_QUESTIONS = ["A.1", "A.5", "C.11", "E.21", "F.25", "G.26", "H.32", "I.33", "J.38", "K.42"]

@st.cache_data
def load_data():
    excel_files = glob.glob("*.xlsx")
    if not excel_files: return None, None
    excel_file = excel_files[0]
    try:
        qri_df = pd.read_excel(excel_file, sheet_name='Quantum Readiness Index', header=10, engine='openpyxl')
        lists_df = pd.read_excel(excel_file, sheet_name='Lists', header=None, engine='openpyxl')
        return qri_df, lists_df
    except:
        return None, None

qri_df, lists_df = load_data()

if qri_df is not None:
    # 2. DATA PROCESSING
    questions_db = []
    insights_lookup = {}
    for _, row in qri_df.iterrows():
        std = str(row.get('Assessment Standard', ''))
        short_id = std.split(":")[0].strip() if ":" in std else std
        insights_lookup[short_id] = {
            "impact": row.get("Business Impact / ROI", "Not available"),
            "pillar": str(row.get('Strategic Pillar', 'Other'))
        }

    num_cols = lists_df.shape[1]
    for col_idx in range(2, num_cols, 3):
        title = str(lists_df.iloc[4, col_idx])
        short_id = title.split(":")[0].strip() if ":" in title else title
        if short_id in DEMO_QUESTIONS:
            questions_db.append({
                "id": short_id,
                "question": title.split(":", 1)[1].strip() if ":" in title else title,
                "pillar": insights_lookup.get(short_id, {}).get("pillar", "Other"),
                "options": lists_df.iloc[5:10, col_idx].tolist(),
                "scores": lists_df.iloc[5:10, col_idx+1].tolist(),
                "insight": insights_lookup.get(short_id, {}).get("impact", "")
            })

    # 3. SIDEBAR
    st.sidebar.markdown("### Strategic Maturity")
    st.sidebar.info("Most organizations are currently in Pilot Purgatory")
    st.sidebar.progress(10 / 44)
    st.sidebar.markdown("---")
    st.sidebar.markdown("Architect your full roadmap with a 44 point audit")
    st.sidebar.link_button("Unlock Full Version", "https://www.lfiusa.com/risk-radar")

    # 4. MAIN UI
    st.title("LFI Quantum Readiness & Risk Radar")
    st.markdown("Quantify commercial exposure to quantum technology and identify high value optimization opportunities")

    tab_calc, tab_audit, tab_results = st.tabs(["Financial Risk", "Risk Pulse Diagnostic", "Strategic Radar"])

    # TAB 1: FINANCIAL RISK
    with tab_calc:
        st.subheader("The Cost of Inaction")
        col1, col2 = st.columns(2)
        with col1:
            revenue = st.number_input("Annual Revenue $", value=500_000_000, step=10_000_000)
            friction = st.slider("Efficiency Loss %", 0.0, 10.0, 3.0) / 100
        with col2:
            ip_val = st.number_input("Value of IP $", value=100_000_000, step=5_000_000)
        
        # Risk Chart
        eff_risk = revenue * friction
        fig_risk = go.Figure(data=[
            go.Bar(name='Annual Efficiency Risk', x=['Operational Friction'], y=[eff_risk], marker_color='#38b6ff'),
            go.Bar(name='Security Exposure', x=['IP Sovereignty'], y=[ip_val], marker_color='#000000')
        ])
        fig_risk.update_layout(title="Quantified Commercial Risk Profile", barmode='group')
        st.plotly_chart(fig_risk, use_container_width=True)

    # TAB 2: DIAGNOSTIC
    with tab_audit:
        st.subheader("High Signal Audit")
        if 'user_scores' not in st.session_state:
            st.session_state.user_scores = {q['id']: 0.0 for q in questions_db}
        for q in questions_db:
            st.markdown(f"**{q['id']}: {q['question']}**")
            opts = [str(o).split(" - ")[0] for o in q['options']]
            sel = st.radio(f"Select maturity level for {q['id']}", opts, key=q['id'], horizontal=True)
            st.session_state.user_scores[q['id']] = q['scores'][opts.index(sel)]
            st.markdown(f"<div class='insight-box'><b>Strategic Insight:</b><br>{q['insight']}</div>", unsafe_allow_html=True)
            st.markdown("---")

    # TAB 3: RESULTS (Gauges & Radar)
    with tab_results:
        # Weighted Logic: Strategy 14%, Tech 29%, Ops 57%
        s_scores = [v for k,v in st.session_state.user_scores.items() if any(q['pillar'].startswith('Strategy') for q in questions_db if q['id']==k)]
        t_scores = [v for k,v in st.session_state.user_scores.items() if any(q['pillar'].startswith('Technology') for q in questions_db if q['id']==k)]
        o_scores = [v for k,v in st.session_state.user_scores.items() if any(q['pillar'].startswith('Operations') for q in questions_db if q['id']==k)]

        s_avg = (sum(s_scores)/len(s_scores)/2.5)*100 if s_scores else 0
        t_avg = (sum(t_scores)/len(t_scores)/2.5)*100 if t_scores else 0
        o_avg = (sum(o_scores)/len(o_scores)/2.5)*100 if o_scores else 0
        total_idx = (s_avg * 0.14) + (t_avg * 0.29) + (o_avg * 0.57)

        st.subheader("Executive Pillar Maturity")
        g_cols = st.columns(3)
        pillars = [("Strategy", s_avg, "#38b6ff"), ("Technology", t_avg, "#2E86C1"), ("Operations", o_avg, "#000000")]
        for i, (name, val, color) in enumerate(pillars):
            with g_cols[i]:
                fig = go.Figure(go.Indicator(mode="gauge+number", value=val, title={'text': name}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': color}}))
                fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("The Gap Analysis")
        col_r1, col_r2 = st.columns([2, 1])
        with col_r1:
            cats = ["Strategy", "Technology", "Operations", "Governance", "Talent", "Innovation"]
            radar_vals = [s_avg, t_avg, o_avg, 30, 25, 40] # 30, 25, 40 are 'Missing Data' placeholders
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(r=[100]*6, theta=cats, fill='toself', name='Target State', line=dict(color='lightgrey', dash='dot')))
            fig_radar.add_trace(go.Scatterpolar(r=radar_vals + [radar_vals[0]], theta=cats + [cats[0]], fill='toself', name='Your Pulse', line=dict(color='#38b6ff')))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
            st.plotly_chart(fig_radar, use_container_width=True)
        with col_r2:
            st.metric("Total Readiness Index", f"{total_idx:.1f}/100")
            st.markdown("### Unknown Risks Detected")
            st.markdown("Pulse indicates significant exposure in Governance and Workforce Readiness")
            st.link_button("Request Bespoke Board Report", "https://www.lfiusa.com/risk-radar", type="primary")
else:
    st.error("Missing Strategic Entanglement data source")