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
    /* 1. HIDE DEFAULT ELEMENTS */
    [data-testid="stSidebar"] {display: none;}
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 5rem;}

    /* 2. DARK THEME BACKGROUND */
    .stApp {
        background: radial-gradient(circle at top right, #1a1f35, #05070a);
        color: white;
        font-family: 'Helvetica Neue', sans-serif;
    }

    /* 3. CUSTOM HEADERS (CENTERED & STYLED) */
    .section-header {
        text-align: center;
        font-size: 1rem;
        font-weight: 700;
        color: #4facfe;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 10px;
        border-bottom: 1px solid rgba(79, 172, 254, 0.3);
        padding-bottom: 5px;
    }
    
    .main-title {
        text-align: center; 
        color: white; 
        margin-bottom: 30px; 
        font-weight: 800;
        letter-spacing: 1px;
    }

    /* 4. TABS STYLING (CENTERED, NO ICONS) */
    .stTabs [data-baseweb="tab-list"] {
        justify-content: center;
        gap: 10px;
        background-color: transparent;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        width: 200px;
        background-color: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        color: #888;
        font-weight: 600;
        border: 1px solid rgba(255,255,255,0.05);
        display: flex;
        justify-content: center;
        text-transform: uppercase;
        font-size: 0.85rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4facfe;
        color: #05070a;
        border-color: #4facfe;
        box-shadow: 0 0 15px rgba(79, 172, 254, 0.3);
    }

    /* 5. INPUT FIELDS (SEARCH & DROPDOWN) */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: rgba(13, 17, 23, 0.8) !important;
        color: white !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        text-align: center;
        height: 45px;
    }
    
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus-within {
        border-color: #4facfe !important;
        box-shadow: 0 0 10px rgba(79, 172, 254, 0.3) !important;
    }

    /* 6. CARD DESIGN */
    .unit-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(79, 172, 254, 0.2);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
        transition: 0.2s;
        min-height: 200px;
        backdrop-filter: blur(5px);
    }
    .unit-card:hover {
        border-color: #4facfe;
        transform: translateY(-5px);
        box-shadow: 0 0 20px rgba(79, 172, 254, 0.2);
    }

    /* 7. TEXT STYLES */
    .car-title {
        color: #4facfe;
        font-weight: 800;
        font-size: 0.9rem;
        text-transform: uppercase;
        margin-bottom: 5px;
        white-space: nowrap; 
        overflow: hidden; 
        text-overflow: ellipsis;
        text-align: center;
    }
    .duty-price { 
        font-size: 1.8rem; 
        font-weight: 900; 
        color: #FFFFFF; 
        margin: 5px 0;
        text-align: center;
    }
    
    /* 8. SPECS GRID */
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
    
    /* 9. BREAKDOWN TABLE */
    .tax-row {
        display: flex;
        justify-content: space-between;
        font-size: 0.8rem;
        padding: 4px 0;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    .tax-label { color: #aaa; }
    .tax-val { color: #fff; font-weight: bold; }
    .tax-total { 
        border-top: 1px solid #4facfe; 
        margin-top: 5px; 
        padding-top: 5px; 
        color: #4facfe; 
        font-weight: 900; 
    }
    
    /* 10. FILTER BOX */
    .filter-box {
        background-color: rgba(0,0,0,0.2);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA LOADER
# ==========================================
@st.cache_data
def load_data():
    try:
        files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and 'app.py' not in f]
        if not files: return pd.DataFrame(), "No file found"
        
        target = max(files, key=os.path.getsize)
        
        if target.endswith('.csv'): df = pd.read_csv(target)
        else: df = pd.read_excel(target)

        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        
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

        df['CRSP'] = pd.to_numeric(df['CRSP'], errors='coerce').fillna(0)
        
        def clean_cc(x):
            try: return int(''.join(filter(str.isdigit, str(x))))
            except: return 0
        
        if 'CC' in df.columns: df['CC'] = df['CC'].apply(clean_cc)
        else: df['CC'] = 0

        for c in ['Make', 'Model', 'Fuel', 'Transmission', 'Drive', 'Category', 'Seating']:
            if c not in df.columns:
                df[c] = "-" 
            else:
                df[c] = df[c].astype(str).str.upper().str.strip().replace(['NAN', 'NONE'], '-')

        df['Search_Name'] = df['Make'] + " " + df['Model']
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

# ==========================================
# 3. CALCULATOR
# ==========================================
def calculate_duty_breakdown(row, yom):
    try:
        crsp = float(row['CRSP'])
        cc = row['CC']
        fuel = str(row['Fuel'])
        
        age = 2025 - yom
        rates = {0:0.05, 1:0.05, 2:0.20, 3:0.30, 4:0.40, 5:0.50, 6:0.55, 7:0.60, 8:0.65}
        depr = rates.get(age if age <= 8 else 8, 0.70)
        
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
        
        total = import_duty + excise_val + vat_val + idf + rdl
        
        return {
            "Customs Value": customs_value,
            "Import Duty": import_duty,
            "Excise Duty": excise_val,
            "VAT": vat_val,
            "IDF": idf,
            "RDL": rdl,
            "Total": total,
            "Depreciation": depr * 100
        }
    except:
        return {"Total": 0}

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
def main():
    df, error = load_data()

    # CENTERED HEADER
    st.markdown("<h2 class='main-title'>KENYA VEHICLE DUTY CALCULATOR</h2>", unsafe_allow_html=True)

    # CENTERED YOM SELECTOR
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown('<div class="section-header">YEAR OF MANUFACTURE</div>', unsafe_allow_html=True)
        years = list(range(2025, 2017, -1))
        yom = st.selectbox("Year of Manufacture", years, index=years.index(2018), label_visibility="collapsed")

    if not df.empty:
        df['Tax_Data'] = df.apply(lambda row: calculate_duty_breakdown(row, yom), axis=1)
        df['Duty'] = df['Tax_Data'].apply(lambda x: x['Total'])

        # CLEAN TABS (No Icons, Centered)
        tab1, tab2, tab3 = st.tabs(["SEARCH", "MARKET TRENDS", "COMPARISON"])

        # --- TAB 1: SEARCH ---
        with tab1:
            st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
            
            # Centered Search Bar
            sc1, sc2, sc3 = st.columns([1, 6, 1])
            with sc2:
                query = st.text_input("", placeholder="TYPE MAKE OR MODEL (e.g. TOYOTA PRADO)...", label_visibility="collapsed")

            filtered = df.copy()
            if query:
                filtered = filtered[filtered['Search_Name'].str.contains(query, case=False, na=False)]
            
            filtered = filtered.sort_values('Duty', ascending=True)

            st.markdown(f"<div style='text-align:center; margin:15px 0; color:#666; font-size:0.8rem;'>FOUND {len(filtered)} VEHICLES</div>", unsafe_allow_html=True)

            cols = st.columns(3)
            for i, (idx, row) in enumerate(filtered.head(60).iterrows()):
                with cols[i % 3]:
                    duty_fmt = f"{row['Duty']:,.0f}"
                    st.markdown(f"""
                    <div class="unit-card">
                        <div class="car-title" title="{row['Search_Name']}">{row['Search_Name']}</div>
                        <div style="font-size:0.7rem; color:#666; text-align:center;">ESTIMATED DUTY</div>
                        <div class="duty-price">KES {duty_fmt}</div>
                        <div class="spec-grid">
                            <div class="spec-item">{row['CC']} CC</div>
                            <div class="spec-item">{row['Fuel']}</div>
                            <div class="spec-item">{row['Transmission']}</div>
                            <div class="spec-item">{row['Drive']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("TAX BREAKDOWN"):
                        tax = row['Tax_Data']
                        st.markdown(f"""
                        <div class="tax-row"><span class="tax-label">Depreciation ({tax.get('Depreciation',0):.0f}%)</span> <span class="tax-val">Applied</span></div>
                        <div class="tax-row"><span class="tax-label">Customs Value</span> <span class="tax-val">{tax.get('Customs Value',0):,.0f}</span></div>
                        <hr style="margin:5px 0; border-color:rgba(255,255,255,0.1);">
                        <div class="tax-row"><span class="tax-label">Import Duty</span> <span class="tax-val">{tax.get('Import Duty',0):,.0f}</span></div>
                        <div class="tax-row"><span class="tax-label">Excise Duty</span> <span class="tax-val">{tax.get('Excise Duty',0):,.0f}</span></div>
                        <div class="tax-row"><span class="tax-label">VAT (16%)</span> <span class="tax-val">{tax.get('VAT',0):,.0f}</span></div>
                        <div class="tax-row"><span class="tax-label">IDF (2.5%)</span> <span class="tax-val">{tax.get('IDF',0):,.0f}</span></div>
                        <div class="tax-row"><span class="tax-label">RDL (2.0%)</span> <span class="tax-val">{tax.get('RDL',0):,.0f}</span></div>
                        <div class="tax-row tax-total"><span class="tax-label" style="color:#4facfe">TOTAL</span> <span>{tax.get('Total',0):,.0f}</span></div>
                        """, unsafe_allow_html=True)

        # --- TAB 2: MARKET TRENDS ---
        with tab2:
            st.markdown('<div class="section-header">MARKET ANALYSIS</div>', unsafe_allow_html=True)
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            
            def smart_sort(opts):
                try: return sorted(opts, key=lambda x: float(str(x).replace(',','')) if str(x).replace('.','').isdigit() else x)
                except: return sorted(opts)

            f1, f2, f3 = st.columns(3)
            with f1: sel_drive = st.multiselect("Drive Config", smart_sort(df['Drive'].unique()))
            with f2: sel_fuel = st.multiselect("Fuel Type", smart_sort(df['Fuel'].unique()))
            with f3: sel_trans = st.multiselect("Transmission", smart_sort(df['Transmission'].unique()))
            
            f4, f5, f6 = st.columns(3)
            with f4: sel_cc = st.multiselect("Engine CC", sorted(df['CC'].unique()))
            with f5: sel_seats = st.multiselect("Seating", smart_sort(df['Seating'].unique()))
            with f6: sel_body = st.multiselect("Body Type", smart_sort(df['Category'].unique()))
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            market_df = df.copy()
            if sel_drive: market_df = market_df[market_df['Drive'].isin(sel_drive)]
            if sel_fuel: market_df = market_df[market_df['Fuel'].isin(sel_fuel)]
            if sel_trans: market_df = market_df[market_df['Transmission'].isin(sel_trans)]
            if sel_cc: market_df = market_df[market_df['CC'].isin(sel_cc)]
            if sel_seats: market_df = market_df[market_df['Seating'].isin(sel_seats)]
            if sel_body: market_df = market_df[market_df['Category'].isin(sel_body)]
            
            market_df = market_df.sort_values('Duty', ascending=True)
            market_df['Estimated Duty'] = market_df['Duty'].apply(lambda x: f"KES {x:,.0f}")

            out = BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
                market_df.drop(columns=['Tax_Data']).to_excel(writer, index=False)
            st.download_button("📥 DOWNLOAD REPORT", out.getvalue(), "market_report.xlsx", mime="application/vnd.ms-excel")

            st.dataframe(
                market_df[['Search_Name', 'Category', 'CC', 'Fuel', 'Drive', 'Transmission', 'Seating', 'Estimated Duty']], 
                use_container_width=True,
                hide_index=True
            )

        # --- TAB 3: COMPARISON (FIXED DUPLICATE KEY ERROR) ---
        with tab3:
            st.markdown('<div class="section-header">SIDE-BY-SIDE COMPARISON</div>', unsafe_allow_html=True)
            choices = st.multiselect("SELECT VEHICLES", df['Search_Name'].unique())
            
            if choices:
                comp_df = df[df['Search_Name'].isin(choices)].copy()
                comp_df = comp_df.sort_values('Duty', ascending=True)
                comp_df['Estimated Duty'] = comp_df['Duty'].apply(lambda x: f"KES {x:,.0f}")
                
                # FIX: Handle Duplicate Names for Display
                # Create a display name column that appends index if duplicate
                if comp_df['Search_Name'].duplicated().any():
                    comp_df['Display_Name'] = comp_df['Search_Name'] + " (" + comp_df.index.astype(str) + ")"
                else:
                    comp_df['Display_Name'] = comp_df['Search_Name']

                c1, c2 = st.columns([1, 1])
                with c1:
                    st.write("**SPECS MATRIX**")
                    disp = comp_df[['Display_Name', 'Estimated Duty', 'CC', 'Fuel', 'Drive', 'Transmission']].set_index('Display_Name').T
                    st.table(disp)
                with c2:
                    st.write("**DUTY CHART**")
                    st.bar_chart(comp_df.set_index('Display_Name')['Duty'])

    else:
        st.error("Data Load Error")
        st.write(error)
        st.file_uploader("Upload File Manually", type=['xlsx','csv'])

if __name__ == "__main__":
    main()