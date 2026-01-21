import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import glob
import os

# --- 1. SETUP & CONFIG ---
st.set_page_config(page_title="LFI Risk Pulse", layout="wide")

# Custom CSS for the LFI Brand Identity
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #000000; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    [data-testid="stSidebar"] a[kind="secondary"], [data-testid="stSidebar"] a[kind="primary"] {
        background-color: #38b6ff !important; color: #FFFFFF !important; border: none !important; font-weight: bold !important;
    }
    .insight-box { background-color: #f0f9ff; padding: 15px; border-radius: 8px; border-left: 5px solid #38b6ff; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# 10 High-Signal Questions from your Excel logic
DEMO_QUESTIONS = ["A.1", "A.5", "C.11", "E.21", "F.25", "G.26", "H.32", "I.33", "J.38", "K.42"]

@st.cache_data
def load_data():
    excel_files = glob.glob("*.xlsx")
    if not excel_files: return None, None
    excel_file = excel_files[0]
    try:
        # Loading with specific header row from your QRI sheet
        qri_df = pd.read_excel(excel_file, sheet_name='Quantum Readiness Index', header=10, engine='openpyxl')
        lists_df = pd.read_excel(excel_file, sheet_name='Lists', header=None, engine='openpyxl')
        return qri_df, lists_df
    except:
        return None, None

qri_df, lists_df = load_data()

if qri_df is not None:
    # --- 2. PRE-PROCESS QUESTIONS ---
    questions_db = []
    insights_lookup = {}
    for _, row in qri_df.iterrows():
        std = str(row.get('Assessment Standard', ''))
        short_id = std.split(":")[0].strip() if ":" in std else std
        insights_lookup[short_id] = {
            "impact": row.get("Business Impact / ROI", "Strategy analysis required."),
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

    # --- 3. SIDEBAR ---
    st.sidebar.title("LFI USA")
    st.sidebar.markdown("### Diagnostic Maturity")
    st.sidebar.progress(len(DEMO_QUESTIONS) / 44)
    st.sidebar.markdown("You are viewing a high-signal pulse. A full 44-point audit is required for board-level certification.")
    st.sidebar.link_button("Access Full Audit", "https://www.lfiusa.com/risk-radar")

    # --- 4. MAIN UI ---
    tab_calc, tab_audit, tab_results = st.tabs(["Financial Risk", "Risk Pulse Diagnostic", "Strategic Radar"])

    with tab_calc:
        st.subheader("Quantifying the Cost of Stagnation")
        c1, c2 = st.columns(2)
        with c1:
            revenue = st.number_input("Annual Revenue $", value=500_000_000, step=10_000_000)
            friction = st.slider("Efficiency Friction %", 0.0, 10.0, 3.5) / 100
        with c2:
            ip_val = st.number_input("Value of Protected IP $", value=100_000_000, step=5_000_000)
        
        eff_loss = revenue * friction
        fig_f = go.Figure(data=[
            go.Bar(name='Efficiency Risk', x=['Revenue Leak'], y=[eff_loss], marker_color='#38b6ff'),
            go.Bar(name='Sovereignty Risk', x=['IP Exposure'], y=[ip_val], marker_color='#000000')
        ])
        st.plotly_chart(fig_f, use_container_width=True)

    with tab_audit:
        st.subheader("High-Signal Capability Audit")
        if 'user_scores' not in st.session_state:
            st.session_state.user_scores = {q['id']: 0.0 for q in questions_db}

        for q in questions_db:
            st.markdown(f"**{q['id']}: {q['question']}**")
            opts = [str(o).split(" - ")[0] for o in q['options']]
            
            # Using session state to ensure persistency and reactivity
            sel = st.radio(f"Select maturity for {q['id']}", opts, key=f"rad_{q['id']}", horizontal=True)
            
            # Update score immediately in state
            idx = opts.index(sel)
            st.session_state.user_scores[q['id']] = q['scores'][idx]
            
            st.markdown(f"<div class='insight-box'><b>LFI Strategic Insight:</b><br>{q['insight']}</div>", unsafe_allow_html=True)
            st.divider()

    with tab_results:
        # FORCE RE-CALCULATION ON TAB ACCESS
        s_vals = [v for k,v in st.session_state.user_scores.items() if any(q['pillar'].startswith('Strategy') for q in questions_db if q['id']==k)]
        t_vals = [v for k,v in st.session_state.user_scores.items() if any(q['pillar'].startswith('Technology') for q in questions_db if q['id']==k)]
        o_vals = [v for k,v in st.session_state.user_scores.items() if any(q['pillar'].startswith('Operations') for q in questions_db if q['id']==k)]

        s_avg = (sum(s_vals)/len(s_vals)/2.5)*100 if s_vals else 0
        t_avg = (sum(t_vals)/len(t_vals)/2.5)*100 if t_vals else 0
        o_avg = (sum(o_vals)/len(o_vals)/2.5)*100 if o_vals else 0
        
        # Applying your 14/29/57 weights
        weighted_total = (s_avg * 0.14) + (t_avg * 0.29) + (o_avg * 0.57)

        st.subheader("Executive Pillar Maturity")
        g1, g2, g3 = st.columns(3)
        
        # 
        for col, name, val, color in zip([g1, g2, g3], ["Strategy", "Technology", "Operations"], [s_avg, t_avg, o_avg], ["#38b6ff", "#2E86C1", "#000000"]):
            with col:
                fig_g = go.Figure(go.Indicator(mode="gauge+number", value=val, title={'text': name}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': color}}))
                fig_g.update_layout(height=280)
                st.plotly_chart(fig_g, use_container_width=True)

        st.divider()
        
        col_low, col_high = st.columns([2, 1])
        with col_low:
            # 
            st.subheader("Readiness Radar")
            cats = ["Strategy", "Technology", "Operations", "Governance", "Talent", "Innovation"]
            # Showing 0 for the categories we haven't asked yet to highlight the "Gap"
            radar_vals = [s_avg, t_avg, o_avg, 0, 0, 0] 
            
            fig_r = go.Figure()
            fig_r.add_trace(go.Scatterpolar(r=[100]*6, theta=cats, fill='toself', name='Target State', line=dict(color='lightgrey', dash='dot')))
            fig_r.add_trace(go.Scatterpolar(r=radar_vals + [radar_vals[0]], theta=cats + [cats[0]], fill='toself', name='Your Pulse', line=dict(color='#38b6ff')))
            fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
            st.plotly_chart(fig_r, use_container_width=True)
            
        with col_high:
            st.metric("Total Readiness Index", f"{weighted_total:.1f}/100")
            st.markdown("### Risk Analysis")
            if weighted_total < 50:
                st.error("Status: High Exposure")
                st.write("Significant gaps in Technology and Operations pillars suggest immediate vulnerability.")
            else:
                st.info("Status: Emergent")
                st.write("Foundational strategy is present, but missing data in Governance prevents scaling.")
            
            st.link_button("Download Board-Ready Report", "https://www.lfiusa.com/risk-radar", type="primary")

else:
    st.warning("Please ensure the LFI Excel data source is uploaded to the application directory.")