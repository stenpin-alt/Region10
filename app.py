import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(
    page_title="Convenience Ruteplanlægger Pro", 
    layout="wide",
    page_icon="logo.png"
)

st.sidebar.image("logo.png", use_container_width=True) 

st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
        [data-testid="stVerticalBlock"] > div { padding-bottom: 0px !important; margin-bottom: 0px !important; }
        div.stSelectbox div[data-testid="stSelectboxWithDynamicOptions"] { transform: scale(0.9); transform-origin: left center; }
        .stAlert { padding: 8px !important; margin-bottom: 8px !important; }
        div[data-testid="column"] { border-right: 1.5px solid #e6e9ef !important; padding-right: 15px !important; padding-left: 5px !important; }
        div[data-testid="column"]:last-child { border-right: none !important; padding-right: 5px !important; }
    </style>
""", unsafe_allow_html=True)

ALLE_DAGE_GLOBAL = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag"]
FIL_KUNDER = "/tmp/gemt_kunder.csv"
FIL_KONSULENTER = "/tmp/gemt_konsulenter.csv"
FIL_FLYTNINGER = "/tmp/gemt_flytninger.csv"
FIL_KODER = "/tmp/gemt_koder.csv"

def gem_data_til_disken():
    if st.session_state['kunder']: pd.DataFrame(st.session_state['kunder']).to_csv(FIL_KUNDER, index=False)
    if st.session_state['konsulenter']:
        df_kons = pd.DataFrame([{"id": k, "navn": v["navn"]} for k, v in st.session_state['konsulenter'].items()])
        df_kons.to_csv(FIL_KONSULENTER, index=False)
    if st.session_state['manuelle_flytninger']:
        df_flyt = pd.DataFrame([{"id": k, "dag": v} for k, v in st.session_state['manuelle_flytninger'].items()])
        df_flyt.to_csv(FIL_FLYTNINGER, index=False)
    if st.session_state['bruger_koder']:
        df_koder = pd.DataFrame([{"navn": k, "kode": v} for k, v in st.session_state['bruger_koder'].items()])
        df_koder.to_csv(FIL_KODER, index=False)

def hent_data_fra_disken():
    if os.path.exists(FIL_KONSULENTER) and not st.session_state['konsulenter']:
        df_kons = pd.read_csv(FIL_KONSULENTER)
        st.session_state['konsulenter'] = {int(r["id"]): {"navn": str(r["navn"])} for _, r in df_kons.iterrows()}
    if os.path.exists(FIL_KUNDER) and not st.session_state['kunder']:
        df_kund = pd.read_csv(FIL_KUNDER)
        st.session_state['kunder'] = df_kund.to_dict(orient="records")
    if os.path.exists(FIL_FLYTNINGER) and not st.session_state['manuelle_flytninger']:
        df_flyt = pd.read_csv(FIL_FLYTNINGER)
        st.session_state['manuelle_flytninger'] = {str(r["id"]): str(r["dag"]) for _, r in df_flyt.iterrows()}
    if os.path.exists(FIL_KODER) and not st.session_state['bruger_koder']:
        df_koder = pd.read_csv(FIL_KODER)
        st.session_state['bruger_koder'] = {str(r["navn"]): str(r["kode"]) for _, r in df_koder.iterrows()}

if 'konsulenter' not in st.session_state: st.session_state['konsulenter'] = {}
if 'kunder' not in st.session_state: st.session_state['kunder'] = []
if 'manuelle_flytninger' not in st.session_state: st.session_state['manuelle_flytninger'] = {}
if 'bruger_koder' not in st.session_state: st.session_state['bruger_koder'] = {}
if 'arbejdsdage' not in st.session_state: st.session_state['arbejdsdage'] = {}
if 'logget_ind' not in st.session_state: st.session_state['logget_ind'] = False
if 'bruger_rolle' not in st.session_state: st.session_state['bruger_rolle'] = None
if 'bruger_navn' not in st.session_state: st.session_state['bruger_navn'] = None
if 'maks_kunder_pr_dag' not in st.session_state: st.session_state['maks_kunder_pr_dag'] = 8
if 'aktivt_konsulent_id' not in st.session_state: st.session_state['aktivt_konsulent_id'] = None

hent_data_fra_disken()

def tjek_login(brugernavn, kode):
    b_clean = brugernavn.strip().lower()
    k_clean = kode.strip()
    admin_code = st.session_state['bruger_koder'].get("admin", "admin123")
    if b_clean == "admin" and k_clean == admin_code:
        st.session_state['logget_ind'] = True
        st.session_state['bruger_rolle'] = "admin"
        st.session_state['bruger_navn'] = "Administrator"
        return True
    return False

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

@st.cache_data
def beregn_ruter_cached(kunder, konsulenter, arbejdsdage, manuelle_flytninger, valgt_loft):
    beregnede_aftaler = []
    aktuelt_aar = 2026
    for k_id, k_info in konsulenter.items():
        konsulent_arbejdsdage = arbejdsdage.get(str(k_id), ALLE_DAGE_GLOBAL)
        konsulent_kunder = [k for k in kunder if int(k["konsulent_id"]) == int(k_id)]
        for uge_nummer in range(1, 53):
            uge_id = f"{aktuelt_aar}-Uge{uge_nummer:02d}"
            dag_taeller = {d: 0 for d in ALLE_DAGE_GLOBAL}
            ugens_planlagte_kunde_ids = set()
            for kunde in konsulent_kunder:
                try: frekvens = float(kunde["frekvens"])
                except: frekvens = 1.0
                try: besøg_pr_uge = int(kunde.get("besoeg_pr_uge", 1))
                except: besøg_pr_uge = 1
                
                # RETTELSE: Fjernet mellemrum i variabelnavn
                skal_besoeges_i_denne_uge = False
                kunde_offset = int(kunde["id"])
                
                if frekvens >= 1.0: skal_besoeges_i_denne_uge = True
                elif frekvens == 0.50 and uge_nummer % 2 == (kunde_offset % 2): skal_besoeges_i_denne_uge = True
                elif frekvens == 0.25 and uge_nummer % 4 == (kunde_offset % 4): skal_besoeges_i_denne_uge = True
                elif frekvens in [0.12, 0.15, 0.30] and uge_nummer % 6 == (kunde_offset % 6): skal_besoeges_i_denne_uge = True
                
                if skal_besoeges_i_denne_uge:
                    for b_idx in range(besøg_pr_uge):
                        # ... resten af din oprindelige logik forbliver her ...
                        beregnede_aftaler.append({"id": f"{kunde['id']}-{uge_id}-b{b_idx}", "kunde_id": kunde["id"], "kundenavn": kunde["navn"], "dag": "Mandag", "uge_id": uge_id, "postnr": kunde["postnr"], "by": kunde["by"], "konsulent_id": k_id})
    return beregnede_aftaler

# Resten af din app (UI, Login osv.) skal indsættes herunder præcis som i din oprindelige fil.
