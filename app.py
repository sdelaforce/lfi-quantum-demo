It appears the application is struggling to find the files because the specific filenames in your environment contain the .xlsx extension as part of the string (e.g., LFI Quantum Readiness Index.xlsx - Quantum Readiness Index.csv).

I have modified the load_data_robust function to use a flexible string matching system. Instead of looking for an exact start or end, it searches for the key terms "Quantum Readiness Index" and "Lists" anywhere in the filename, ensuring the app initializes correctly regardless of the export naming convention.

Updated Resilient Code
Python
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import glob
import os

# --- 1. SETUP & CONFIG ---
st.set_page_config(page_title="LFI Risk Pulse", layout="wide")

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

# The 10 High-Signal Questions
DEMO_IDS = ["A.1", "A.5", "C.11", "E.21", "F.25", "G.26", "H.32", "I.33", "J.38", "K.42"]

@st.cache_data
def load_data_robust():
    all_files = os.listdir('.')
    qri_file = next((f for f in all_files if "Quantum Readiness Index.csv" in f and "Executive" not in f), None)
    lists_file = next((f for f in all_files if "Lists.csv" in f), None)
    
    if not qri_file or not lists_file:
        return None, None
        
    # Load QRI Data
    df = pd.read_csv(qri_file, header=None)
    header_idx = 0
    for i, row in df.head(20).iterrows():
        if "Strategic Pillar" in row.values:
            header_idx = i
            break
    df.columns = df.iloc[header_idx]
    df = df.iloc[header_idx+1:].reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    
    # Load Lists Data
    ldf = pd.read_csv(lists_file, header=None)
    
    return df, ldf

qri_df, lists_df = load_data_robust()

# Branding Logo
lfi_logo_url = "https://www.lfiusa.com/wp-content/uploads/2023/10/LFI-Logo-White-e1697523624838.png"
st.sidebar.image(lfi_logo_url, use_container_width=True)

if qri_df is not None:
    # --- 2. BUILD QUESTION DATABASE ---
    questions_db = []
    for _, row in qri_df.iterrows():
        std_val = str(row.get('Assessment Standard', ''))
        short_id = std_val.split(":")[0].strip() if ":" in std_val else std_val
        
        if short_id in DEMO_IDS:
            q_text, options, scores = "Unknown", [], []
            for col_idx in range(lists_df.shape[1]):
                col_data = lists_df.iloc[:, col_idx].astype(str)
                if col_data.str.contains(short_id, na=False).any():
                    found_row = col_data[col_data.str.contains(short_id)].index[0]
                    q_text = col_data[found_row].split(":", 1)[-1].strip()
                    options = lists_df.iloc[found_row+1 : found_row+6, col_idx].astype(str).tolist()
                    scores = lists_df.iloc[found_row+1 : found_row+6, col_idx+1].astype(float).tolist()
                    break
            
            questions_db.append({
                "id": short_id, "question": q_text,
                "pillar": str(row.get('Strategic Pillar', 'Operations')),
                "options": options, "scores": scores,
                "insight": str(row.get("Business Impact / ROI", "Strategy analysis required."))
            })

    # --- 3. APP INTERFACE ---
    tab_calc, tab_audit, tab_results = st.tabs(["Financial Risk", "Risk Pulse Diagnostic", "Strategic Radar"])

    with tab_calc:
        st.subheader("The Cost of Inaction")
        col1, col2 = st.columns(2)
        with col1:
            rev = st.number_input("Annual Revenue ($)", value=500_000_000, step=10_000_000)
            fric = st.slider("Efficiency Friction (%)", 0.0, 10.0, 3.5) / 100
        with col2:
            ip = st.number_input("Value of IP Assets ($)", value=100_000_000, step=5_000_000)
        
        fig_f = go.Figure(data=[
            go.Bar(name='Efficiency Loss', x=['Revenue Leak'], y=[rev*fric], marker_color='#38b6ff'),
            go.Bar(name='Security Exposure', x=['IP Exposure'], y=[ip], marker_color='#000000')
        ])
        fig_f.update_layout(template="plotly_white")
        st.plotly_chart(fig_f, use_container_width=True)

    with tab_audit:
        st.subheader("Strategic Capability Pulse")
        for q in questions_db:
            st.markdown(f"**{q['id']}: {q['question']}**")
            display_opts = [o.split(" - ")[0] for o in q['options']]
            st.radio("Select maturity level:", display_opts, key=f"ans_{q['id']}", horizontal=True)
            st.markdown(f"<div class='insight-box'><b>LFI Insight:</b><br>{q['insight']}</div>", unsafe_allow_html=True)
            st.divider()

    with tab_results:
        # Dynamic Recalculation
        p_scores = {"Strategy": [], "Technology": [], "Operations": []}
        for q in questions_db:
            p_name = "Strategy" if "Strategy" in q['pillar'] else ("Technology" if "Technology" in q['pillar'] else "Operations")
            cur_label = st.session_state.get(f"ans_{q['id']}", q['options'][0].split(" - ")[0])
            try:
                idx = [o.split(" - ")[0] for o in q['options']].index(cur_label)
                p_scores[p_name].append(q['scores'][idx])
            except: pass

        s_avg = (sum(p_scores["Strategy"])/len(p_scores["Strategy"])/2.5)*100 if p_scores["Strategy"] else 0
        t_avg = (sum(p_scores["Technology"])/len(p_scores["Technology"])/2.5)*100 if p_scores["Technology"] else 0
        o_avg = (sum(p_scores["Operations"])/len(p_scores["Operations"])/2.5)*100 if p_scores["Operations"] else 0
        total = (s_avg * 0.14) + (t_avg * 0.29) + (o_avg * 0.57)

        st.subheader("Executive Pillar Maturity")
        g1, g2, g3 = st.columns(3)
        
        for col, n, v, c in zip([g1,g2,g3], ["Strategy", "Technology", "Operations"], [s_avg, t_avg, o_avg], ["#38b6ff", "#2E86C1", "#000000"]):
            with col:
                fig = go.Figure(go.Indicator(mode="gauge+number", value=v, title={'text': n}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': c}}))
                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True)

        st.divider()
        col_r1, col_r2 = st.columns([2, 1])
        with col_r1:
            st.subheader("Capability Radar")
            
            cats = ["Strategy", "Technology", "Operations", "Governance", "Talent", "Innovation"]
            radar_vals = [s_avg, t_avg, o_avg, 20, 15, 30] 
            fig_r = go.Figure()
            fig_r.add_trace(go.Scatterpolar(r=[100]*6, theta=cats, fill='toself', name='Target State', line=dict(color='lightgrey', dash='dot')))
            fig_r.add_trace(go.Scatterpolar(r=radar_vals + [radar_vals[0]], theta=cats + [cats[0]], fill='toself', name='Your Profile', line=dict(color='#38b6ff')))
            st.plotly_chart(fig_r, use_container_width=True)
        with col_r2:
            st.metric("Total Readiness Index", f"{total:.1f}/100")
            st.link_button("Upgrade to Full Audit", "https://www.lfiusa.com/risk-radar", type="primary")

else:
    st.error("Application data source not found. Please ensure CSV files are present in the directory.")