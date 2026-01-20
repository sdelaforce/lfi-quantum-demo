import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import glob
import os

# --- 1. SETUP & CONFIG ---
st.set_page_config(page_title="LFI Quantum Readiness Index (Demo)", layout="wide")

# CUSTOM CSS: BLACK SIDEBAR, WHITE TEXT, & CUSTOM BLUE BUTTON
st.markdown("""
<style>
    /* 1. MAKE SIDEBAR BLACK */
    [data-testid="stSidebar"] {
        background-color: #000000;
    }
    
    /* 2. MAKE SIDEBAR TEXT WHITE */
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    /* 3. CUSTOM SIDEBAR BUTTON STYLE */
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

    /* 4. OTHER STYLES */
    .metric-box { border: 1px solid #e0e0e0; padding: 20px; border-radius: 10px; background-color: #f9f9f9; }
    .insight-box { background-color: #e8f4f8; padding: 15px; border-radius: 5px; border-left: 5px solid #2E86C1; }
</style>
""", unsafe_allow_html=True)

DEMO_QUESTIONS = ["A.1", "E.19", "H.32"]

@st.cache_data
def load_data():
    """Smartly finds Excel file and locates the correct header row."""
    # Find Excel
    excel_files = glob.glob("*.xlsx")
    if not excel_files:
        st.error(f"❌ No Excel file found in: {os.getcwd()}")
        return None, None
    excel_file = excel_files[0]

    try:
        # Load Raw to find Header
        df_raw = pd.read_excel(excel_file, sheet_name='Quantum Readiness Index', header=None, engine='openpyxl')
        header_row_idx = None
        for i, row in df_raw.head(20).iterrows():
            row_vals = row.astype(str).str.strip().tolist()
            if "Strategic Pillar" in row_vals:
                header_row_idx = i
                break
        
        if header_row_idx is None: return None, None

        # Load Main Data
        qri_df = pd.read_excel(excel_file, sheet_name='Quantum Readiness Index', header=header_row_idx, engine='openpyxl')
        qri_df.columns = qri_df.columns.astype(str).str.strip()
        if 'Strategic Pillar' in qri_df.columns:
            qri_df['Strategic Pillar'] = qri_df['Strategic Pillar'].ffill()
        qri_df = qri_df.dropna(subset=['Assessment Standard'])
        
        # Load Lists
        lists_df = pd.read_excel(excel_file, sheet_name='Lists', header=None, engine='openpyxl')
        
        return qri_df, lists_df
    except:
        return None, None

qri_df, lists_df = load_data()

if qri_df is not None:
    # --- 2. DATA PROCESSING ---
    questions_db = []
    
    # Expert Insights Lookup
    insights_lookup = {}
    for _, row in qri_df.iterrows():
        std = str(row['Assessment Standard'])
        short_id = std.split(":")[0].strip() if ":" in std else std
        
        insights_lookup[short_id] = {
            "impact": row.get("Business Impact / ROI", "N/A"),
            "process": row.get("LFI Process Description", "N/A"),
            "pillar": row['Strategic Pillar']
        }

    # Extract dropdowns
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
                "insight_impact": insights_lookup.get(short_id, {}).get("impact", ""),
                "insight_process": insights_lookup.get(short_id, {}).get("process", "")
            })

    # --- 3. UI: SIDEBAR ---
    
    # === SMART LOGO LOADER ===
    logo_files = glob.glob("*.png") + glob.glob("*.jpg") + glob.glob("*.jpeg")
    
    if logo_files:
        st.sidebar.image(logo_files[0], use_container_width=True)
    else:
        st.sidebar.image("https://placehold.co/200x80/000000/FFFFFF?text=LFI+Logo", use_container_width=True)

    st.sidebar.markdown("### 🚦 The Pilot Trap")
    st.sidebar.info("Most organizations are stuck in 'Pilot Purgatory'.")
    
    st.sidebar.progress(3 / 45, text="Diagnostic Progress (3/45)")
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Want the full 45-point audit?**")
    
    # === SIDEBAR BUTTON ===
    st.sidebar.link_button("Unlock Full Version", "https://www.lfiusa.com/contact-form")

    # --- 4. UI: MAIN TABS ---
    st.title("LFI Quantum Readiness & Risk Radar™")
    st.markdown("Assess your commercial exposure to quantum technology.")

    tab_calc, tab_audit, tab_results = st.tabs(["💰 Financial Risk Calculator", "📝 3-Point Diagnostic", "📊 Your Results"])

    # --- TAB 1: FINANCIAL CALCULATOR ---
    with tab_calc:
        st.subheader("Quantify Your Cost of Stagnation")
        st.markdown("Even if you are 'just watching' the market, inaction has a cost.")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("#### 1. Efficiency Risk")
            revenue = st.number_input("Annual Revenue ($)", value=500_000_000, step=10_000_000)
            friction = st.slider("Rev. Lost to Friction (%)", 0.0, 10.0, 3.0, 0.1) / 100
            
            eff_risk = revenue * friction
            st.metric("Annual Efficiency Loss", f"${eff_risk:,.0f}", delta="Money on the Table", delta_color="inverse")
            st.caption(f"*You are losing ~${eff_risk/12:,.0f}/mo to classical inefficiencies.*")

        with col_c2:
            st.markdown("#### 2. Sovereignty Risk")
            ip_val = st.number_input("Value of Trade Secrets ($)", value=100_000_000, step=5_000_000)
            
            st.metric("Asset Value Exposed", f"${ip_val:,.0f}", delta="HNDL Risk", delta_color="inverse")
            st.caption("*If data shelf-life > 5 years, this asset is likely compromised.*")
        
        st.divider()
        st.info("💡 **Takeaway:** Use these figures for your internal business case.")

    # --- TAB 2: THE DIAGNOSTIC ---
    with tab_audit:
        st.subheader("Core Capability Audit")
        
        if 'user_scores' not in st.session_state:
            st.session_state.user_scores = {q['id']: 0.0 for q in questions_db}

        for q in questions_db:
            with st.container():
                st.markdown(f"### {q['pillar']}")
                st.markdown(f"**{q['id']}: {q['question']}**")
                
                # Options
                opts = [str(o).split(" - ")[0] for o in q['options']]
                full_opts = {str(o).split(" - ")[0]: o for o in q['options']}
                
                sel = st.radio(f"Select for {q['id']}", opts, key=q['id'], horizontal=True)
                
                # Save Score
                idx = opts.index(sel)
                st.session_state.user_scores[q['id']] = q['scores'][idx]
                
                # Expert Insight
                st.markdown(f"<div class='insight-box'><b>💡 Chief Quantum Officer Insight:</b><br>{q['insight_impact']}</div>", unsafe_allow_html=True)
                
                st.markdown("---")

    # --- TAB 3: RESULTS ---
    with tab_results:
        st.subheader("Your Capability Gap Analysis")
        
        col_r1, col_r2 = st.columns([2, 1])
        
        with col_r1:
            categories = ["Strategy", "Technology", "Operations", "Governance", "Talent", "Innovation"]
            scores = [0] * len(categories)
            
            # Simple mapping for demo
            s_map = {"Strategy": 0, "Technology": 1, "Operations": 2}
            
            for q in questions_db:
                cat_idx = -1
                for k, v in s_map.items():
                    if k in q['pillar']: cat_idx = v
                
                if cat_idx != -1:
                    val = (st.session_state.user_scores[q['id']] / 2.5) * 100
                    scores[cat_idx] = val

            fig = go.Figure()
            
            # 1. Target State
            fig.add_trace(go.Scatterpolar(
                r=[100]*6, theta=categories,
                fill='toself', name='Target State',
                line=dict(color='lightgrey', dash='dot')
            ))
            
            # 2. User Profile
            fig.add_trace(go.Scatterpolar(
                r=scores + scores[:1], theta=categories + categories[:1],
                fill='toself', name='Your Profile',
                line=dict(color='#2E86C1')
            ))
            
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=True,
                title="Your Readiness Radar"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_r2:
            st.markdown("### ⚠️ Analysis")
            
            avg = sum(st.session_state.user_scores.values()) / 3
            norm_score = (avg / 2.5) * 100
            
            st.metric("Readiness Score", f"{norm_score:.0f}/100")
            
            if norm_score < 50:
                st.warning("**Status: The Pilot Trap**")
                st.markdown("You lack infrastructure to scale.")
            elif norm_score < 80:
                st.info("**Status: The Scaler**")
                st.markdown("Good progress, governance gaps detected.")
            else:
                st.success("**Status: Leader**")
            
            st.markdown("---")
            st.markdown("### 🔒 Missing Data")
            st.markdown("Your radar is incomplete. You are missing diagnostics for:")
            st.markdown("- *IP Defense Strategy*")
            st.markdown("- *Workforce Density*")
            st.markdown("- *Supply Chain Risk*")
            
            # === UPDATED MAIN AREA BUTTON ===
            st.link_button("Unlock Full Assessment", "https://www.lfiusa.com/contact-form", type="primary")