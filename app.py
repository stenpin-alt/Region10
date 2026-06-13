import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Convenience Ruteplanlægger", layout="wide", page_icon="logo.png")
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

# CSS-optimering
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
        [data-testid="stVerticalBlock"] > div { padding-bottom: 0px !important; margin-bottom: 0px !important; }
        div.stSelectbox div[data-testid="stSelectboxWithDynamicOptions"] { transform: scale(0.9); transform-origin: left center; }
        div[data-testid="column"] { border-right: 1.5px solid #e6e9ef !important; padding-right: 15px !important; padding-left: 5px !important; }
        div[data-testid="column"]:last-child { border-right: none !important; }
    </style>
""", unsafe_allow_html=True)

ALLE_DAGE_GLOBAL = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag"]
FIL_KUNDER, FIL_KONSULENTER, FIL_FLYTNINGER, FIL_KODER = "gemt_kunder.csv", "gemt_konsulenter.csv", "gemt_flytninger.csv", "gemt_koder.csv"

# Initialisering af session_state
if 'konsulenter' not in st.session_state: st.session_state['konsulenter'] = {}
if 'kunder' not in st.session_state: st.session_state['kunder'] = []
if 'aftaler' not in st.session_state: st.session_state['aftaler'] = []
if 'manuelle_flytninger' not in st.session_state: st.session_state['manuelle_flytninger'] = {}
if 'arbejdsdage' not in st.session_state: st.session_state['arbejdsdage'] = {}
if 'bruger_koder' not in st.session_state: st.session_state['bruger_koder'] = {}
if 'logget_ind' not in st.session_state: st.session_state['logget_ind'] = False

def gem_data_til_disken():
    if st.session_state['kunder']: pd.DataFrame(st.session_state['kunder']).to_csv(FIL_KUNDER, index=False)
    if st.session_state['manuelle_flytninger']:
        pd.DataFrame([{"id": k, "dag": v} for k, v in st.session_state['manuelle_flytninger'].items()]).to_csv(FIL_FLYTNINGER, index=False)

def kør_rullende_kalender_motor():
    st.session_state['aftaler'] = []
    idag = datetime.now()
    start_mandag = idag - timedelta(days=idag.weekday())
    global_tæller = {}
    
    AUTOMATISK_LOFT = 8
    TOTAL_LOFT = 10 # Buffer på +2 = 10 i alt

    for uge_frem in range(0, 24):
        mål_mandag = start_mandag + timedelta(weeks=uge_frem)
        uge_id = f"{mål_mandag.year}-Uge{mål_mandag.isocalendar()[1]}"
        if uge_id not in global_tæller: global_tæller[uge_id] = {}

        for k_id in st.session_state['konsulenter'].keys():
            if k_id not in global_tæller[uge_id]: global_tæller[uge_id][k_id] = {d: 0 for d in ALLE_DAGE_GLOBAL}
            kunder_i_uge = [k for k in st.session_state['kunder'] if int(k["konsulent_id"]) == int(k_id)]
            
            # Manuelle flytninger (Høj prioritet)
            for kunde in kunder_i_uge[:]:
                unik_nøgle = f"{kunde['id']}-{uge_id}"
                if unik_nøgle in st.session_state['manuelle_flytninger']:
                    valgt_dag = st.session_state['manuelle_flytninger'][unik_nøgle]
                    if global_tæller[uge_id][k_id][valgt_dag] < TOTAL_LOFT:
                        global_tæller[uge_id][k_id][valgt_dag] += 1
                        st.session_state['aftaler'].append({**kunde, "id": unik_nøgle, "uge_id": uge_id, "dag": valgt_dag})
                    kunder_i_uge.remove(kunde)

            # Automatisk placering (op til 8)
            for kunde in kunder_i_uge:
                for dag in ALLE_DAGE_GLOBAL:
                    if global_tæller[uge_id][k_id][dag] < AUTOMATISK_LOFT:
                        global_tæller[uge_id][k_id][dag] += 1
                        st.session_state['aftaler'].append({**kunde, "id": f"{kunde['id']}-{uge_id}", "uge_id": uge_id, "dag": dag})
                        break

def hent_zone_og_farve(pnr):
    try: pnr_int = int(''.join(filter(str.isdigit, str(pnr))))
    except: return "Ukendt", "⚪"
    if 1000 <= pnr_int <= 3999: return "Storkøbenhavn", "🔵"
    elif 4000 <= pnr_int <= 4999: return "Vest-/Sydsjælland", "🟢"
    elif 5000 <= pnr_int <= 5999: return "Fyn", "🟡"
    elif 6000 <= pnr_int <= 6999: return "Sydjylland", "🟠"
    elif 7000 <= pnr_int <= 7999: return "Midt-/Vestjylland", "🟣"
    elif 8000 <= pnr_int <= 8999: return "Østjylland", "🔴"
    return "Nordjylland", "⚫"

# Indlæs data
if os.path.exists(FIL_KUNDER): 
    st.session_state['kunder'] = pd.read_csv(FIL_KUNDER).to_dict(orient="records")
if os.path.exists(FIL_FLYTNINGER):
    df_flyt = pd.read_csv(FIL_FLYTNINGER)
    st.session_state['manuelle_flytninger'] = {str(r["id"]): str(r["dag"]) for _, r in df_flyt.iterrows()}

if not st.session_state['logget_ind']:
    st.title("🔐 Login")
    u = st.text_input("Brugernavn")
    p = st.text_input("Kode", type="password")
    if st.button("Log ind"): st.session_state['logget_ind'] = True; st.rerun()
    st.stop()

# Hovedvisning
if not st.session_state['aftaler']: kør_rullende_kalender_motor()
valgt_uge = st.sidebar.selectbox("Vælg uge:", sorted(list({a["uge_id"] for a in st.session_state['aftaler']})))
st.title("🗺️ Convenience Ruteplanlægger")

col1, col2, col3, col4, col5 = st.columns(5)
dage_cols = {"Mandag": col1, "Tirsdag": col2, "Onsdag": col3, "Torsdag": col4, "Fredag": col5}

for dag, col in dage_cols.items():
    with col:
        st.markdown(f"### {dag}")
        dag_aftaler = [a for a in st.session_state['aftaler'] if a["dag"] == dag and a["uge_id"] == valgt_uge]
        for aftale in dag_aftaler:
            zone, farve = hent_zone_og_farve(aftale["postnr"])
            with st.container(border=True):
                st.markdown(f"{farve} **{aftale['kundenavn']}**")
                st.caption(f"📍 {aftale['postnr']} {aftale['by']}")
                ny_dag = st.selectbox("Flyt til:", ALLE_DAGE_GLOBAL, index=ALLE_DAGE_GLOBAL.index(dag), key=f"sel-{aftale['id']}", label_visibility="collapsed")
                if ny_dag != dag:
                    st.session_state['manuelle_flytninger'][aftale['id']] = ny_dag
                    gem_data_til_disken()
                    kør_rullende_kalender_motor()
                    st.rerun()
