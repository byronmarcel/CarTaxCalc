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
    [data-testid="stSidebar"] {display: none;}
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 1rem; padding-bottom: 5rem;}

    .stApp {
        background: radial-gradient(circle at top right, #1a1f35, #05070a);
        color: white;
        font-family: 'Helvetica Neue', sans-serif;
    }

    .main-title {
        text-align: center; color: white; margin-bottom: 30px; 
        font-weight: 800; letter-spacing: 1px;
    }

    /* SEARCH CARD */
    .unit-card {
        background: rgba(255, 255, 255, 0.04); 
        border: 1px solid rgba(79, 172, 254, 0.2);
        border-radius: 12px; 
        padding: 15px; 
        margin-bottom: 15px; 
        transition: 0.2s;
        backdrop-filter: blur(5px);
    }
    
    .car-title {
        color: #4facfe; font-weight: 800; font-size: 0.95rem; text-transform: uppercase;
        margin-bottom: 5px; text-align: center;
    }
    .duty-price { font-size: 1.8rem; font-weight: 900; color: #FFFFFF; margin: 5px 0; text-align: center; }
    
    .spec-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-top: 10px; }
    .spec-item {
        background: rgba(255,255,255,0.05); padding: 5px; border-radius: 4px;
        text-align: center; font-size: 0.75rem; color: #ccc;
    }

    .tax-row {
        display: flex; justify-content: space-between; font-size: 0.85rem;
        padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    .tax-total { border-top: 1px solid #4facfe; margin-top: 8px; padding-top: 8px; color: #4facfe; font-weight: 900; }
    
    .footer-credit {
        position: fixed; left: 0; bottom: 0; width: 100%; background-color: #05070a;
        color: #4facfe; text-align: center; padding: 10px; font-size: 0.8rem;
        border-top: 1px solid #333; z-index: 100;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA LOADER (REFINED)
# ==========================================
@st.cache_data
def load_data():
    try:
        files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.csv')) and 'app.py' not in f]
        if not files: return pd.DataFrame(), "No file found"
        target = max(files, key=os.path.getsize)
        df = pd.read_csv(target) if target.endswith('.csv') else pd.read_excel(target)
        
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        
        rename_map = {}
        for col in df.columns:
            c_l = col.lower()
            if 'capacity' in c_l: rename_map[col] = 'CC'
            elif 'body' in c_l: rename_map[col] = 'Category'
            elif 'crsp' in c_l: rename_map[col] = 'CRSP'
            elif 'drive' in c_l: rename_map[col] = 'Drive'
            elif 'fuel' in c_l: rename_map[col] = 'Fuel'
            
        df = df.rename(columns=rename_map)
        df['CRSP'] = pd.to_numeric(df['CRSP'].astype(str).str.replace(',', '').str.replace(' ', ''), errors='coerce').fillna(0)
        df = df[df['CRSP'] > 0]

        def clean_cc(x):
            try: return int(''.join(filter(str.isdigit, str(x))))
            except: return 0
        df['CC'] = df['CC'].apply(clean_cc) if 'CC' in df.columns else 0
        df['Search_Name'] = df['Make'].astype(str).str.upper() + " " + df['Model'].astype(str).str.upper()
        
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

# ==========================================
# 3. DUTY ENGINE
# ==========================================
def calculate_duty(row, yom):
    try:
        crsp, cc, fuel = float(row['CRSP']), int(row['CC']), str(row['Fuel']).upper()
        age = 2025 - yom
        rates = {0:0.05, 1:0.05, 2:0.20, 3:0.30, 4:0.40, 5:0.50, 6:0.55, 7:0.60, 8:0.65}
        depr = rates.get(age if age <= 8 else 8, 0.70)
        
        if "ELECTRIC" in fuel: r, id_r, ex_r = 2.15325, 0.25, 0.10
        elif (cc > 3000 and "GASOLINE" in fuel) or (cc > 2500 and "DIESEL" in fuel): r, id_r, ex_r = 2.64262, 0.35, 0.35
        elif cc <= 1500: r, id_r, ex_r = 2.34900, 0.35, 0.20
        else: r, id_r, ex_r = 2.44687, 0.35, 0.25

        cv = (crsp / r) * (1 - depr)
        iduty, excise = cv * id_r, (cv + (cv * id_r)) * ex_r
        vat = (cv + iduty + excise) * 0.16
        total = iduty + excise + vat + (cv * 0.025) + (cv * 0.02)
        
        return {"Total": total, "ID": iduty, "EX": excise, "VAT": vat, "Depr": depr*100}
    except:
        return {"Total": 0}

# ==========================================
# 4. MAIN UI
# ==========================================
def main():
    df, error = load_data()
    st.markdown("<h2 class='main-title'>KENYA VEHICLE DUTY CALCULATOR</h2>", unsafe_allow_html=True)

    # Simplified Selector
    years = list(range(2025, 2017, -1))
    yom = st.selectbox("SELECT YEAR OF MANUFACTURE", years, index=years.index(2018))

    if not df.empty:
        # Calculate and Sort
        df['Tax_Data'] = df.apply(lambda row: calculate_duty(row, yom), axis=1)
        df['Duty'] = df['Tax_Data'].apply(lambda x: x['Total'])
        
        # --- FORCED SORTING ---
        df = df.sort_values(by='Duty', ascending=True).reset_index(drop=True)

        tab1, tab2, tab3 = st.tabs(["SEARCH", "TRENDS", "PURCHASE"])

        with tab1:
            query = st.text_input("", placeholder="Search Make or Model...")
            filtered = df[df['Search_Name'].str.contains(query.upper())] if query else df
            
            # Re-sort filtered data to be absolutely sure
            filtered = filtered.sort_values(by='Duty', ascending=True)

            # --- DYNAMIC GRID LOGIC ---
            # On mobile, columns stack. To keep 1,2,3 order, we must use a specific loop.
            cols = st.columns(3)
            for i, (idx, row) in enumerate(filtered.head(50).iterrows()):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="unit-card">
                        <div class="car-title">{row['Search_Name']}</div>
                        <div class="duty-price">KES {row['Duty']:,.0f}</div>
                        <div class="spec-grid">
                            <div class="spec-item">{row['CC'] if row['CC'] > 0 else 'EV'}</div>
                            <div class="spec-item">{row['Fuel']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander("VIEW TAXES"):
                        t = row['Tax_Data']
                        st.markdown(f"""
                        <div class="tax-row"><span>Depreciation</span><span>{t['Depr']:.0f}%</span></div>
                        <div class="tax-row"><span>Import Duty</span><span>{t['ID']:,.0f}</span></div>
                        <div class="tax-row"><span>Excise Duty</span><span>{t['EX']:,.0f}</span></div>
                        <div class="tax-row"><span>VAT</span><span>{t['VAT']:,.0f}</span></div>
                        """, unsafe_allow_html=True)

        with tab2:
            st.dataframe(df[['Search_Name', 'CC', 'Fuel', 'Duty']], use_container_width=True, hide_index=True)

        with tab3:
            car_sel = st.selectbox("SELECT CAR", sorted(df['Search_Name'].unique()))
            car_row = df[df['Search_Name'] == car_sel].iloc[0]
            cnf = st.number_input("CNF PRICE (USD)", value=6000)
            rate = st.number_input("RATE", value=130.0)
            
            # Purchase Logic with your requested costs
            landed = (cnf * rate) + car_row['Duty'] + 120000 + 35000 + 20000 + 45000 # Port + Carrier + Misc + Clearing/Reg
            st.success(f"TOTAL LANDED: KES {landed:,.0f}")

    st.markdown(f'<div class="footer-credit">Created by Marcel Byron</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()