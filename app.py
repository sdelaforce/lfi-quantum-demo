import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import glob
import os

# --- 1. SETUP & CONFIG ---
st.set_page_config(page_title="LFI Risk Pulse", layout="wide")

# Custom CSS for the LFI Brand Identity (Black & LFI Blue)
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #000000; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    [data-testid="stSidebar"] a[kind="secondary"], [data-testid="stSidebar"] a[kind="primary"] {
        background-color: #38b6ff !important; color: #FFFFFF !important; border: none !important; font-weight: bold !important;
    }
    .insight-box { background-color: #f0f9ff; padding: 15px; border-radius: 8px; border-left: 5px solid #38b6ff; margin-top: 10px; }
    .stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# 10 High-Signal Questions for the Free Risk Pulse
DEMO_QUESTIONS = ["A.1", "A.5", "C.11", "E.21", "F.25", "G.26", "H.32", "I.33", "J.38", "K.42"]

@st.cache_data
def load_data():
    """Tries to find the Excel file first, then falls back to CSVs if hosted."""
    excel_files = glob.glob("*.xlsx")
    if excel_files:
        try:
            qri_df = pd.read_excel(excel_files[0], sheet_name='Quantum Readiness Index', header=10, engine='openpyxl')
            lists_df = pd.read_excel(excel_files[0], sheet_name='Lists', header=None, engine='openpyxl')
            return qri_df, lists_df
        except: pass
    
    # Fallback to CSV files (often generated in sandbox environments)
    try:
        qri_df = pd.read_csv('LFI Quantum Readiness Index.xlsx - Quantum Readiness Index.csv', header=3)
        lists_df = pd.read_csv('LFI Quantum Readiness Index.xlsx - Lists.csv', header=None)
        return qri_df, lists_df
    except:
        return None, None

qri_df, lists_df = load_data()

# --- LOGO LOGIC ---
# We try to find a local logo file; if not, we use the LFI USA website logo URL.
logo_files = glob.glob("logo*") + glob.glob("*.png") + glob.glob("*.jpg")
lfi_logo_url = "https://www.lfiusa.com/wp-content/uploads/2023/10/LFI-Logo-White-e1697523624838.png"

if logo_files:
    st.sidebar.image(logo_files[0], use_container_width=True)
else:
    # Use LFI website logo as the fallback
    st.sidebar.image(lfi_logo_url, use_container_width=True)

if qri_df is not None:
    # --- 2. PRE-PROCESS DATA ---
    # Create a database of the selected questions
    questions_db = []
    
    # Clean up column names for robust matching
    qri_df.columns = [str(c).strip() for c in qri_df.columns]
    
    for _, row in qri_df.iterrows():
        std = str(row.get('Assessment Standard', ''))
        short_id = std.split(":")[0].strip() if ":" in std else std
        
        if short_id in DEMO_QUESTIONS:
            # Finding matching dropdown options from the Lists sheet
            # The structure is Column Index 2, 5, 8...
            q_text = "Unknown Question"
            options = []
            scores = []
            
            # Search Lists for the matching ID
            for col_idx in range(2, lists_df.shape[1], 3):
                header_val = str(lists_df.iloc[4, col_idx])
                if short_id in header_val:
                    q_text = header_val.split(":", 1)[1].strip() if ":" in header_val else header_val
                    options = lists_df.iloc[5:10, col_idx].astype(str).tolist()
                    scores = lists_df.iloc[5:10, col_idx+1].astype(float).tolist()
                    break
            
            questions_db.append({
                "id": short_id,
                "question": q_text,
                "pillar": str(row.get('Strategic Pillar', 'Other')),
                "options": options,
                "scores": scores,
                "insight": str(row.get("Business Impact / ROI", "Strategy analysis required."))
            })

    # --- 3. SIDEBAR NAV ---
    st.sidebar.markdown("### Strategic Maturity")
    st.sidebar.info("Map your Quantum Value Stages™ in 5 minutes.")
    st.sidebar.progress(len(DEMO_QUESTIONS) / 44)
    st.sidebar.markdown("---")
    st.sidebar.markdown("Architect your full roadmap with a 44 point audit.")
    st.sidebar.link_button("Unlock Full Audit", "https://www.lfiusa.com/risk-radar")

    # --- 4. MAIN UI ---
    st.title("LFI Quantum Readiness & Risk Radar")
    st.markdown("Quantify commercial exposure and identify high value optimization opportunities.")

    tab_calc, tab_audit, tab_results = st.tabs(["Financial Risk", "Risk Pulse Diagnostic", "Strategic Radar"])

    with tab_calc:
        st.subheader("Quantifying the Cost of Stagnation")
        c1, c2 = st.columns(2)
        with c1:
            revenue = st.number_input("Annual Revenue ($)", value=500_000_000, step=10_000_000)
            friction = st.slider("Efficiency Friction %", 0.0, 10.0, 3.5) / 100
        with c2:
            ip_val = st.number_input("Value of Protected IP ($)", value=100_000_000, step=5_000_000)
        
        eff_loss = revenue * friction
        fig_f = go.Figure(data=[
            go.Bar(name='Efficiency Risk', x=['Operational Friction'], y=[eff_loss], marker_color='#38b6ff'),
            go.Bar(name='Sovereignty Risk', x=['IP Sovereignty'], y=[ip_val], marker_color='#000000')
        ])
        fig_f.update_layout(title="Commercial Value at Risk", template="plotly_white")
        st.plotly_chart(fig_f, use_container_width=True)

    with tab_audit:
        st.subheader("Core Capability Audit")
        # Display questions and store labels in session_state
        for q in questions_db:
            st.markdown(f"**{q['id']}: {q['question']}**")
            # Labels only for display
            display_opts = [o.split(" - ")[0] for o in q['options']]
            
            # The radio button selection is automatically saved in session_state via the 'key'
            st.radio("Maturity Level:", display_opts, key=f"ans_{q['id']}", horizontal=True)
            
            st.markdown(f"<div class='insight-box'><b>LFI Strategic Insight:</b><br>{q['insight']}</div>", unsafe_allow_html=True)
            st.divider()

    with tab_results:
        st.subheader("Executive Maturity Profile")
        
        # --- CALCULATION LOGIC (RE-RUNS EVERY TIME TAB IS CLICKED) ---
        pillar_scores = {"Strategy": [], "Technology": [], "Operations": []}
        
        for q in questions_db:
            # Find which pillar this question belongs to
            pillar_name = "Strategy" if "Strategy" in q['pillar'] else ("Technology" if "Technology" in q['pillar'] else "Operations")
            
            # Get the current selected label from session state
            current_label = st.session_state.get(f"ans_{q['id']}", q['options'][0].split(" - ")[0])
            
            # Map the label back to the score index
            try:
                idx = [o.split(" - ")[0] for o in q['options']].index(current_label)
                score = q['scores'][idx]
                pillar_scores[pillar_name].append(score)
            except:
                pillar_scores[pillar_name].append(0.0)

        # Average the pillar scores (0 to 100%)
        s_avg = (sum(pillar_scores["Strategy"]) / len(pillar_scores["Strategy"]) / 2.5) * 100 if pillar_scores["Strategy"] else 0
        t_avg = (sum(pillar_scores["Technology"]) / len(pillar_scores["Technology"]) / 2.5) * 100 if pillar_scores["Technology"] else 0
        o_avg = (sum(pillar_scores["Operations"]) / len(pillar_scores["Operations"]) / 2.5) * 100 if pillar_scores["Operations"] else 0
        
        # Apply LFI Weights: 14% Strategy, 29% Tech, 57% Ops
        weighted_total = (s_avg * 0.14) + (t_avg * 0.29) + (o_avg * 0.57)

        # 1. Gauge Charts
        g1, g2, g3 = st.columns(3)
        for col, name, val, color in zip([g1, g2, g3], ["Strategy", "Technology", "Operations"], [s_avg, t_avg, o_avg], ["#38b6ff", "#2E86C1", "#000000"]):
            with col:
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number", 
                    value=val, 
                    title={'text': name}, 
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': color}}
                ))
                fig_g.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig_g, use_container_width=True)

        st.divider()
        
        # 2. Radar Chart
        col_r1, col_r2 = st.columns([2, 1])
        with col_r1:
            st.subheader("Capability Radar")
            cats = ["Strategy", "Technology", "Operations", "Governance", "Talent", "Innovation"]
            # Placeholder values for categories not covered in the 10-question pulse
            radar_vals = [s_avg, t_avg, o_avg, 20, 15, 30] 
            
            fig_r = go.Figure()
            fig_r.add_trace(go.Scatterpolar(r=[100]*6, theta=cats, fill='toself', name='Target State', line=dict(color='lightgrey', dash='dot')))
            fig_r.add_trace(go.Scatterpolar(r=radar_vals + [radar_vals[0]], theta=cats + [cats[0]], fill='toself', name='Your Profile', line=dict(color='#38b6ff')))
            fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(l=50, r=50, t=20, b=20))
            st.plotly_chart(fig_r, use_container_width=True)
            
        with col_r2:
            st.metric("Total Readiness Index", f"{weighted_total:.1f}/100")
            st.markdown("### Risk Analysis")
            if weighted_total < 40:
                st.error("Status: Critical Exposure")
                st.write("Current infrastructure lacks the agility to absorb quantum-driven disruption.")
            elif weighted_total < 75:
                st.info("Status: Emergent")
                st.write("Foundational awareness is present. Scaling requires formal governance.")
            else:
                st.success("Status: Strategic Advantage")
                st.write("Positioned for early adoption with managed risk profiles.")
            
            st.markdown("---")
            st.markdown("**Unlock Board-Ready Reporting**")
            st.write("This radar is missing 34 critical data points. Complete the Enterprise Audit for a full strategic roadmap.")
            st.link_button("Upgrade to Full Audit", "https://www.lfiusa.com/risk-radar", type="primary")

else:
    st.error("Quantum Readiness Index data source not found. Please ensure the Excel or CSV file is in the application folder.")