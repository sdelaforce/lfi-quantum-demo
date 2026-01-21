import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import glob
import os

# --- 1. SETUP & CONFIG ---
st.set_page_config(page_title="LFI Quantum Readiness Index (Risk Pulse)", layout="wide")

# CUSTOM CSS: CLEAN MINIMALIST DESIGN
st.markdown("""
<style>
    /* MAKE SIDEBAR BLACK */
    [data-testid="stSidebar"] {
        background-color: #000000;
    }
    
    /* MAKE SIDEBAR TEXT WHITE */
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    /* CUSTOM SIDEBAR BUTTON STYLE */
    [data-testid="stSidebar"] a[kind="secondary"], [data-testid="stSidebar"] a[kind="primary"] {
        background-color: #38b6ff !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: bold !important;
    }
    
    [data-testid="stSidebar"] a:hover {
        opacity: 0.8;
        color: #FFFFFF !important;
    }

    /* OTHER STYLES */
    .metric-box { border: 1px solid #e0e0e0; padding: 20px; border-radius: 10px; background-color: #f9f9f9; }
    .insight-box { background-color: #e8f4f8; padding: 15px; border-radius: 5px; border-left: 5px solid #2E86C1; }
</style>
""", unsafe_allow_html=True)

# 10 High-Signal Questions for the Free Risk Pulse
DEMO_QUESTIONS = ["A.1", "A.5", "C.11", "E.21", "F.25", "G.26", "H.32", "I.33", "J.38", "K.42"]

@st.cache_data
def load_data():
    """Smartly finds Excel file and locates the correct header row."""
    excel_files = glob.glob("*.xlsx")
    if not excel_files:
        # Fallback for demo environment if no file uploaded
        return None, None
    excel_file = excel_files[0]

    try:
        df_raw = pd.read_excel(excel_file, sheet_name='Quantum Readiness Index', header=None, engine='openpyxl')
        header_row_idx = None
        for i, row in df_raw.head(20).iterrows():
            row_vals = row.astype(str).str.strip().tolist()
            if "Strategic Pillar" in row_vals:
                header_row_idx = i
                break
        
        if header_row_idx is None: return None, None

        qri_df = pd.read_excel(excel_file, sheet_name='Quantum Readiness Index', header=header_row_idx, engine='openpyxl')
        qri_df.columns = qri_df.columns.astype(str).str.strip()
        if 'Strategic Pillar' in qri_df.columns:
            qri_df['Strategic Pillar'] = qri_df['Strategic Pillar'].ffill()
        qri_df = qri_df.dropna(subset=['Assessment Standard'])
        
        lists_df = pd.read_excel(excel_file, sheet_name='Lists', header=None, engine='openpyxl')
        return qri_df, lists_df
    except:
        return None, None

qri_df, lists_df = load_data()

if qri_df is not None:
    # --- 2. DATA PROCESSING ---
    questions_db = []
    insights_lookup = {}
    for _, row in qri_df.iterrows():
        std = str(row['Assessment Standard'])
        short_id = std.split(":")[0].strip() if ":" in std else std
        insights_lookup[short_id] = {
            "impact": row.get("Business Impact / ROI", "N/A"),
            "process": row.get("LFI Process Description", "N/A"),
            "pillar": row['Strategic Pillar']
        }

    num_cols = lists_df.shape[1]
    for col_idx in range(2, num_cols, 3):
        if col_idx + 1 >= num_cols: break
        title = lists_df.iloc[4, col_idx]
        if pd.isna(title) or not isinstance(title, str): continue
        short_id = title.split(":")[0].strip() if ":" in title else title
        q_text = title.split(":", 1)[1].strip() if ":" in title else title
        
        if short_id in DEMO_QUESTIONS:
            questions_db.append({
                "id": short_id,
                "question": q_text,
                "pillar": insights_lookup.get(short_id, {}).get("pillar", "Other"),
                "options": lists_df.iloc[5:10, col_idx].tolist(),
                "scores": lists_df.iloc[5:10, col_idx+1].tolist(),
                "insight_impact": insights_lookup.get(short_id, {}).get("impact", "")
            })

    # --- 3. UI: SIDEBAR ---
    logo_files = glob.glob("*.png") + glob.glob("*.jpg") + glob.glob("*.jpeg")
    if logo_files:
        st.sidebar.image(logo_files[0], use_container_width=True)
    
    st.sidebar.markdown("### Strategic Maturity")
    st.sidebar.info("Most manufacturing firms are currently stuck in Pilot Purgatory.")
    st.sidebar.progress(10 / 45, text="Diagnostic Progress (10/45)")
    st.sidebar.markdown("---")
    st.sidebar.markdown("Architect your full roadmap with a detailed 45 point audit")
    st.sidebar.link_button("Unlock Full Version", "https://www.lfiusa.com/risk-radar")

    # --- 4. UI: MAIN TABS ---
    st.title("LFI Quantum Readiness & Risk Radar")
    st.markdown("Assess commercial exposure to quantum technology and identify high value optimization opportunities.")

    tab_calc, tab_audit, tab_results = st.tabs(["Financial Risk", "Risk Pulse Diagnostic", "Strategic Radar"])

    # --- TAB 1: FINANCIAL RISK ---
    with tab_calc:
        st.subheader("Quantify the Cost of Inaction")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("#### Efficiency Risk")
            revenue = st.number_input("Annual Revenue ($)", value=500_000_000, step=10_000_000)
            friction = st.slider("Revenue Lost to Operational Friction (%)", 0.0, 10.0, 3.0, 0.1) / 100
            eff_risk = revenue * friction
            st.metric("Annual Efficiency Loss", f"${eff_risk:,.0f}")
            st.caption(f"Estimated loss of ${eff_risk/12:,.0f} per month to classical optimization limits.")

        with col_c2:
            st.markdown("#### Sovereignty Risk")
            ip_val = st.number_input("Value of Core Trade Secrets ($)", value=100_000_000, step=5_000_000)
            st.metric("Asset Value Exposed", f"${ip_val:,.0f}")
            st.caption("Risk of Harvest Now Decrypt Later for data with a shelf life over 5 years.")
        
        st.divider()
        st.info("Use these metrics to build the internal business case for quantum readiness.")

    # --- TAB 2: DIAGNOSTIC ---
    with tab_audit:
        st.subheader("High Signal Capability Audit")
        if 'user_scores' not in st.session_state:
            st.session_state.user_scores = {q['id']: 0.0 for q in questions_db}

        for q in questions_db:
            with st.container():
                st.markdown(f"**{q['id']}: {q['question']}**")
                opts = [str(o).split(" - ")[0] for o in q['options']]
                sel = st.radio(f"Select maturity level for {q['id']}", opts, key=q['id'], horizontal=True)
                
                idx = opts.index(sel)
                st.session_state.user_scores[q['id']] = q['scores'][idx]
                st.markdown(f"<div class='insight-box'><b>Strategic Insight:</b><br>{q['insight_impact']}</div>", unsafe_allow_html=True)
                st.markdown("---")

    # --- TAB 3: RESULTS ---
    with tab_results:
        st.subheader("Capability Gap Analysis")
        col_r1, col_r2 = st.columns([2, 1])
        
        # Calculate Weighted Scoring (Strategy 14%, Tech 29%, Ops 57%)
        strat_q = [st.session_state.user_scores[q['id']] for q in questions_db if q['pillar'] == 'Strategy']
        tech_q = [st.session_state.user_scores[q['id']] for q in questions_db if q['pillar'] == 'Technology']
        ops_q = [st.session_state.user_scores[q['id']] for q in questions_db if q['pillar'] == 'Operations']

        s_avg = sum(strat_q)/len(strat_q) if strat_q else 0
        t_avg = sum(tech_q)/len(tech_q) if tech_q else 0
        o_avg = sum(ops_q)/len(ops_q) if ops_q else 0
        
        weighted_score = (s_avg * 0.14) + (t_avg * 0.29) + (o_avg * 0.57)
        norm_score = (weighted_score / 2.5) * 100

        with col_r1:
            categories = ["Strategy", "Technology", "Operations", "Governance", "Talent", "Innovation"]
            # Map weights to radar for visualization
            radar_scores = [ (s_avg/2.5)*100, (t_avg/2.5)*100, (o_avg/2.5)*100, 40, 30, 50 ] # Placeholder for missing areas
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=[100]*6, theta=categories, fill='toself', name='Industry Benchmark', line=dict(color='lightgrey', dash='dot')))
            fig.add_trace(go.Scatterpolar(r=radar_scores + radar_scores[:1], theta=categories + categories[:1], fill='toself', name='Your Profile', line=dict(color='#2E86C1')))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, title="Readiness Radar")
            st.plotly_chart(fig, use_container_width=True)

        with col_r2:
            st.metric("Total Readiness Index", f"{norm_score:.1f}/100")
            if norm_score < 40:
                st.warning("Status: Critical Exposure")
                st.markdown("Organization lacks the baseline infrastructure to mitigate quantum risk.")
            elif norm_score < 75:
                st.info("Status: Emergent")
                st.markdown("Foundational awareness exists but governance gaps remain in the supply chain.")
            else:
                st.success("Status: Strategic Advantage")
                st.markdown("Organization is well positioned to capture first mover advantages.")
            
            st.markdown("---")
            st.markdown("### Missing Diagnostic Data")
            st.markdown("The radar is currently incomplete. To generate a board-ready report, we require data on:")
            st.markdown("- Post Quantum Cryptography roadmap")
            st.markdown("- Intellectual Property defense strategy")
            st.markdown("- Advanced manufacturing pilot capacity")
            st.link_button("Upgrade to Full Audit", "https://www.lfiusa.com/risk-radar", type="primary")

else:
    st.error("Please ensure the Strategic Entanglement Excel file is present in the directory to initialize the diagnostic.")