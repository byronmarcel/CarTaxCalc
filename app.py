import streamlit as st
import pandas as pd
from io import BytesIO
import os

# ==========================================
# 1. SETUP & CSS
# ==========================================
st.set_page_config(page_title="Duty Calculator", layout="wide")

st.markdown("""
    <style>
    /* HIDE SIDEBAR & BLOAT */
    [data-testid="stSidebar"] {display: none;}
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 1rem; padding-bottom: 5rem;}

    /* DARK THEME */
    .stApp {
        background: radial-gradient(circle at top right, #1a1f35, #05070a);
        color: white;
        font-family: 'Inter', sans-serif;
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 5px;
        color: #fff;
        font-weight: 600;
        border: none;
    }
    .stTabs [aria-selected="true"] { background-color: #4facfe; color: #000; }

    /* CARD DESIGN */
    .unit-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(79, 172, 254, 0.3);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 20px;
        transition: 0.2s;
        min-height: 220px;
        backdrop-filter: blur(5px);
    }
    .unit-card:hover {
        border-color: #4facfe;
        transform: translateY(-5px);
        box-shadow: 0 0 20px rgba(79, 172, 254, 0.2);
    }

    /* TEXT STYLES */
    .car-title {
        color: #4facfe;
        font-weight: 800;
        font-size: 0.9rem;
        text-transform: uppercase;
        margin-bottom: 5px;
        white-space: nowrap; 
        overflow: hidden; 
        text-overflow: ellipsis;
    }
    .duty-price { font-size: 1.8rem; font-weight: 900; color: #FFFFFF; margin: 5px 0;}
    
    /* SPECS GRID */
    .spec-grid {
        display: grid; 
        grid-template-columns: repeat(2, 1fr); 
        gap: 8px; 
        margin-top: 15px;
    }
    .spec-item {
        background: rgba(255,255,255,0.05); 
        padding: 5px; 
        border-radius: 4px; 
        text-align: center; 
        font-size: 0.75rem; 
        color: #ccc;
    }
    
    /* FILTER BOX STYLING */
    .filter-box {
        background-color: rgba(255, 255, 255, 0.03);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }

    /* WIDGET OVERRIDES */
    .stTextInput input, .stSelectbox div, .stMultiSelect {
        background-color: #0d1117 !important;
        color: white !important; 
        border: 1px solid #30363d !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA LOADER (SMART MAPPING)
# ==========================================
@st.cache_data
def load_data():
    try:
        files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and 'app.py' not in f]
        if not files: return pd.DataFrame(), "No file found"
        
        target = max(files, key=os.path.getsize)
        
        if target.endswith('.csv'): df = pd.read_csv(target)
        else: df = pd.read_excel(target)

        # 1. NORMALIZE HEADERS (Remove newlines/spaces)
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        
        # 2. SMART MAPPING (Find columns by keyword)
        rename_map = {}
        for col in df.columns:
            c_lower = col.lower()
            if 'capacity' in c_lower and 'cc' not in rename_map.values(): rename_map[col] = 'CC'
            elif 'body' in c_lower: rename_map[col] = 'Category'
            elif 'crsp' in c_lower: rename_map[col] = 'CRSP'
            elif 'drive' in c_lower: rename_map[col] = 'Drive'
            elif 'seat' in c_lower: rename_map[col] = 'Seating'
            elif 'fuel' in c_lower: rename_map[col] = 'Fuel'
            elif 'trans' in c_lower: rename_map[col] = 'Transmission'
            elif 'model' in c_lower and 'number' in c_lower: rename_map[col] = 'Model_Code'
            
        df = df.rename(columns=rename_map)

        # 3. CLEANING
        df['CRSP'] = pd.to_numeric(df['CRSP'], errors='coerce').fillna(0)
        
        def clean_cc(x):
            try: return int(''.join(filter(str.isdigit, str(x))))
            except: return 0
        
        if 'CC' in df.columns: df['CC'] = df['CC'].apply(clean_cc)
        else: df['CC'] = 0

        # Ensure Columns Exist
        for c in ['Make', 'Model', 'Fuel', 'Transmission', 'Drive', 'Category', 'Seating']:
            if c not in df.columns:
                df[c] = "-" # Create empty column if missing
            else:
                df[c] = df[c].astype(str).str.upper().str.strip().replace(['NAN', 'NONE'], '-')

        df['Search_Name'] = df['Make'] + " " + df['Model']
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

# ==========================================
# 3. CALCULATOR
# ==========================================
def calculate_duty(row, yom):
    try:
        crsp = float(row['CRSP'])
        cc = row['CC']
        fuel = str(row['Fuel'])
        
        age = 2025 - yom
        rates = {0:0.05, 1:0.05, 2:0.20, 3:0.30, 4:0.40, 5:0.50, 6:0.55, 7:0.60, 8:0.65}
        depr = rates.get(age if age <= 8 else 8, 0.70)
        
        # Factors based on KRA 2025
        if "ELECTRIC" in fuel:
            r, id_r, ex_r = 2.15325, 0.25, 0.10
        elif (cc > 3000 and "GASOLINE" in fuel) or (cc > 2500 and "DIESEL" in fuel):
            r, id_r, ex_r = 2.64262, 0.35, 0.35
        elif cc <= 1500:
            r, id_r, ex_r = 2.34900, 0.35, 0.20
        else:
            r, id_r, ex_r = 2.44687, 0.35, 0.25

        customs_value = (crsp / r) * (1 - depr)
        
        import_duty = customs_value * id_r
        excise_val = (customs_value + import_duty) * ex_r
        vat_val = (customs_value + import_duty + excise_val) * 0.16
        idf = customs_value * 0.025
        rdl = customs_value * 0.02
        
        return import_duty + excise_val + vat_val + idf + rdl
    except:
        return 0.0

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
def main():
    df, error = load_data()

    # HEADER & DROPDOWN
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown("### 🛡️ DUTY CALCULATOR <span style='color:#4facfe'>KENYA</span>", unsafe_allow_html=True)
    with c2:
        years = list(range(2025, 2017, -1))
        yom = st.selectbox("Year of Manufacture", years, index=years.index(2018))

    if not df.empty:
        df['Duty'] = df.apply(lambda row: calculate_duty(row, yom), axis=1)

        tab1, tab2, tab3 = st.tabs(["🔍 SEARCH", "📊 MARKET TREND", "⚔️ COMPARISON"])

        # --- TAB 1: SEARCH ---
        with tab1:
            query = st.text_input("", placeholder="🔍 Search Make or Model...", label_visibility="collapsed")
            
            filtered = df.copy()
            if query:
                filtered = filtered[filtered['Search_Name'].str.contains(query, case=False, na=False)]
            
            filtered = filtered.sort_values('Duty')
            st.markdown(f"<div style='margin:10px 0; color:grey'>Found {len(filtered)} vehicles</div>", unsafe_allow_html=True)

            cols = st.columns(3)
            for i, (idx, row) in enumerate(filtered.head(60).iterrows()):
                with cols[i % 3]:
                    duty_fmt = f"{row['Duty']:,.0f}"
                    st.markdown(f"""
                    <div class="unit-card">
                        <div class="car-title" title="{row['Search_Name']}">{row['Search_Name']}</div>
                        <div style="font-size:0.7rem; color:#666;">ESTIMATED DUTY</div>
                        <div class="duty-price">KES {duty_fmt}</div>
                        <div class="spec-grid">
                            <div class="spec-item">{row['CC']} CC</div>
                            <div class="spec-item">{row['Fuel']}</div>
                            <div class="spec-item">{row['Transmission']}</div>
                            <div class="spec-item">{row['Drive']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # --- TAB 2: MARKET TREND (SMART DROPDOWNS) ---
        with tab2:
            st.markdown("#### 📊 Market Analysis")
            
            # FILTERS
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            
            # Helper to get unique sorted non-empty values
            def get_opts(col):
                return sorted([x for x in df[col].unique() if x != "-"])

            f1, f2, f3 = st.columns(3)
            with f1: sel_drive = st.multiselect("Drive Config", get_opts('Drive'))
            with f2: sel_fuel = st.multiselect("Fuel Type", get_opts('Fuel'))
            with f3: sel_trans = st.multiselect("Transmission", get_opts('Transmission'))
            
            f4, f5, f6 = st.columns(3)
            with f4: sel_cc = st.multiselect("Engine CC", sorted(df['CC'].unique()))
            with f5: sel_seats = st.multiselect("Seating", get_opts('Seating'))
            with f6: sel_body = st.multiselect("Body Type", get_opts('Category'))
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # APPLY
            market_df = df.copy()
            if sel_drive: market_df = market_df[market_df['Drive'].isin(sel_drive)]
            if sel_fuel: market_df = market_df[market_df['Fuel'].isin(sel_fuel)]
            if sel_trans: market_df = market_df[market_df['Transmission'].isin(sel_trans)]
            if sel_cc: market_df = market_df[market_df['CC'].isin(sel_cc)]
            if sel_seats: market_df = market_df[market_df['Seating'].isin(sel_seats)]
            if sel_body: market_df = market_df[market_df['Category'].isin(sel_body)]
            
            market_df = market_df.sort_values('Duty')
            market_df['Estimated Duty'] = market_df['Duty'].apply(lambda x: f"KES {x:,.0f}")

            # Export
            out = BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
                market_df.to_excel(writer, index=False)
            st.download_button("📥 Download Report", out.getvalue(), "market_report.xlsx", mime="application/vnd.ms-excel")

            st.dataframe(
                market_df[['Search_Name', 'Category', 'CC', 'Fuel', 'Drive', 'Transmission', 'Seating', 'Estimated Duty']], 
                use_container_width=True,
                hide_index=True
            )

        # --- TAB 3: COMPARISON ---
        with tab3:
            st.markdown("#### Side-by-Side Comparison")
            choices = st.multiselect("Select Vehicles", df['Search_Name'].unique())
            
            if choices:
                comp_df = df[df['Search_Name'].isin(choices)].copy()
                comp_df['Estimated Duty'] = comp_df['Duty'].apply(lambda x: f"KES {x:,.0f}")
                
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.write("**Specs Matrix**")
                    disp = comp_df[['Search_Name', 'Estimated Duty', 'CC', 'Fuel', 'Drive', 'Transmission']].set_index('Search_Name').T
                    st.table(disp)
                with c2:
                    st.write("**Duty Chart**")
                    st.bar_chart(comp_df.set_index('Search_Name')['Duty'])

    else:
        st.error("Data Load Error")
        st.write(error)
        st.file_uploader("Upload File Manually", type=['xlsx','csv'])

if __name__ == "__main__":
    main()