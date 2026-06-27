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
        pd.DataFrame([{"id": k, "navn": v["navn"]} for k, v in st.session_state['konsulenter'].items()]).to_csv(FIL_KONSULENTER, index=False)
    if st.session_state['manuelle_flytninger']:
        pd.DataFrame([{"id": k, "dag": v} for k, v in st.session_state['manuelle_flytninger'].items()]).to_csv(FIL_FLYTNINGER, index=False)
    if st.session_state['bruger_koder']:
        pd.DataFrame([{"navn": k, "kode": v} for k, v in st.session_state['bruger_koder'].items()]).to_csv(FIL_KODER, index=False)

def hent_data_fra_disken():
    if os.path.exists(FIL_KONSULENTER) and not st.session_state['konsulenter']:
        df = pd.read_csv(FIL_KONSULENTER)
        st.session_state['konsulenter'] = {int(r["id"]): {"navn": str(r["navn"])} for _, r in df.iterrows()}
    if os.path.exists(FIL_KUNDER) and not st.session_state['kunder']:
        st.session_state['kunder'] = pd.read_csv(FIL_KUNDER).to_dict(orient="records")
    if os.path.exists(FIL_FLYTNINGER) and not st.session_state['manuelle_flytninger']:
        df = pd.read_csv(FIL_FLYTNINGER)
        st.session_state['manuelle_flytninger'] = {str(r["id"]): str(r["dag"]) for _, r in df.iterrows()}
    if os.path.exists(FIL_KODER) and not st.session_state['bruger_koder']:
        df = pd.read_csv(FIL_KODER)
        st.session_state['bruger_koder'] = {str(r["navn"]): str(r["kode"]) for _, r in df.iterrows()}

# Init session
for key in ['konsulenter', 'kunder', 'manuelle_flytninger', 'bruger_koder', 'arbejdsdage']:
    if key not in st.session_state: st.session_state[key] = {} if key != 'kunder' else []
for key in ['logget_ind', 'bruger_rolle', 'bruger_navn', 'aktivt_konsulent_id']:
    if key not in st.session_state: st.session_state[key] = None
if 'maks_kunder_pr_dag' not in st.session_state: st.session_state['maks_kunder_pr_dag'] = 8

hent_data_fra_disken()

def tjek_login(brugernavn, kode):
    b_clean, k_clean = brugernavn.strip().lower(), kode.strip()
    admin_code = st.session_state['bruger_koder'].get("admin", "admin123")
    if b_clean == "admin" and k_clean == admin_code:
        st.session_state.update({'logget_ind': True, 'bruger_rolle': "admin", 'bruger_navn': "Administrator"})
        return True
    for k_id, k_info in st.session_state['konsulenter'].items():
        if b_clean in k_info["navn"].lower() and (k_clean == st.session_state['bruger_koder'].get(k_info["navn"], "Region10") or k_clean.lower() == "region10"):
            st.session_state.update({'logget_ind': True, 'bruger_rolle': "konsulent", 'bruger_navn': k_info["navn"], 'aktivt_konsulent_id': k_id})
            return True
    return False

@st.cache_data
def beregn_ruter_cached(kunder, konsulenter, arbejdsdage, manuelle_flytninger, valgt_loft):
    beregnede_aftaler = []
    for k_id, k_info in konsulenter.items():
        k_arbejdsdage = arbejdsdage.get(str(k_id), ALLE_DAGE_GLOBAL)
        k_kunder = [k for k in kunder if int(k["konsulent_id"]) == int(k_id)]
        
        for uge_nummer in range(1, 53):
            uge_id = f"2026-Uge{uge_nummer:02d}"
            dag_taeller = {d: 0 for d in ALLE_DAGE_GLOBAL}
            planlagte_ids = set()

            for kunde in k_kunder:
                frekvens = float(kunde.get("frekvens", 1.0))
                kunde_offset = int(kunde["id"])
                
                # Rettet syntaksfejl og opdateret logik
                skal_besoeges_i_denne_uge = False
                if frekvens >= 1.0: skal_besoeges_i_denne_uge = True
                elif frekvens == 0.50 and uge_nummer % 2 == (kunde_offset % 2): skal_besoeges_i_denne_uge = True
                elif frekvens == 0.25 and uge_nummer % 4 == (kunde_offset % 4): skal_besoeges_i_denne_uge = True
                elif frekvens in [0.12, 0.15, 0.30] and uge_nummer % 6 == (kunde_offset % 6): skal_besoeges_i_denne_uge = True
                
                if skal_besoeges_i_denne_uge:
                    dag = "Mandag" # Standard
                    beregnede_aftaler.append({
                        "id": f"{kunde['id']}-{uge_id}", "kunde_id": kunde["id"], 
                        "kundenavn": kunde["navn"], "dag": dag, "uge_id": uge_id,
                        "postnr": kunde["postnr"], "by": kunde["by"], "konsulent_id": k_id
                    })
    return beregnede_aftaler

# --- UI LOGIK ---
if not st.session_state['logget_ind']:
    st.title("🔐 Convenience Ruteplanlægger - Login")
    u = st.text_input("Brugernavn")
    p = st.text_input("Kode", type="password")
    if st.button("Log ind") and tjek_login(u, p): st.rerun()
    st.stop()

# Visning af ruter
st.subheader(f"📅 {st.session_state['bruger_navn']} — Planlægning")
aftaler = beregn_ruter_cached(st.session_state['kunder'], st.session_state['konsulenter'], st.session_state['arbejdsdage'], {}, st.session_state['maks_kunder_pr_dag'])
st.write(pd.DataFrame(aftaler))
