import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Convenience Ruteplanlægger", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; }
        div[data-testid="column"] { border-right: 1.5px solid #e6e9ef !important; padding-right: 15px !important; }
        div[data-testid="column"]:last-child { border-right: none !important; }
    </style>
""", unsafe_allow_html=True)

ALLE_DAGE_GLOBAL = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag"]
BOPÆL_POSTNUMRE = {
    "Brian Felix Fabian": 4690, "Daniel Hemmingsen": 2730, "Carsten Bülow": 4000,
    "Morten Hedemand": 5210, "Allan Rechnagel": 6100, "Kristof": 4550,
    "Mark Rosendal Beermann": 9300, "Ole Schulze": 2990, "Emil Nielsen": 9900,
    "Kristian Paulin": 8700, "Troels Jørgensen": 8700, "Dennis Borup Lejel": 8900,
    "Frederik Esmarch": 7800, "Martin Kliver": 5550, "Daniel Murad": 8000,
    "Thomas Jakobsen": 2640, "Mai Utzon": 4140,
}

# --- DATALAGRING ---
FIL_KUNDER, FIL_KONSULENTER, FIL_FLYTNINGER, FIL_KODER = "gemt_kunder.csv", "gemt_konsulenter.csv", "gemt_flytninger.csv", "gemt_koder.csv"

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
    if os.path.exists(FIL_FLYTNINGER):
        st.session_state['manuelle_flytninger'] = {str(r["id"]): str(r["dag"]) for _, r in pd.read_csv(FIL_FLYTNINGER).iterrows()}
    if os.path.exists(FIL_KODER):
        st.session_state['bruger_koder'] = {str(r["navn"]): str(r["kode"]) for _, r in pd.read_csv(FIL_KODER).iterrows()}

# --- INITIALISERING ---
for k in ['konsulenter', 'kunder', 'aftaler', 'arbejdsdage', 'manuelle_flytninger', 'bruger_koder']:
    if k not in st.session_state: st.session_state[k] = {} if k not in ['kunder', 'aftaler'] else []
for k in ['logget_ind', 'bruger_rolle', 'bruger_navn']:
    if k not in st.session_state: st.session_state[k] = None

hent_data_fra_disken()

# --- MOTOR ---
def kør_rullende_kalender_motor():
    idag = datetime.now()
    start_mandag = idag - timedelta(days=idag.weekday())
    st.session_state['aftaler'] = []
    global_tæller = {}

    for uge_frem in range(0, 12):
        mål_mandag = start_mandag + timedelta(weeks=uge_frem)
        uge_id = f"{mål_mandag.year}-Uge{mål_mandag.isocalendar()[1]}"
        global_tæller[uge_id] = {}

        for k_id, k_info in st.session_state['konsulenter'].items():
            global_tæller[uge_id][k_id] = {d: 0 for d in ALLE_DAGE_GLOBAL}
            kunder_i_uge = [c for c in st.session_state['kunder'] if int(c["konsulent_id"]) == int(k_id)]
            
            # 1. Manuelt låste
            for kunde in kunder_i_uge[:]:
                nøgle = f"{kunde['id']}-{uge_id}"
                if nøgle in st.session_state['manuelle_flytninger']:
                    dag = st.session_state['manuelle_flytninger'][nøgle]
                    global_tæller[uge_id][k_id][dag] += 1
                    st.session_state['aftaler'].append({**kunde, "kundenavn": kunde['navn'], "uge_id": uge_id, "dag": dag, "id": nøgle})
                    kunder_i_uge.remove(kunde)
            
            # 2. Resten
            for kunde in kunder_i_uge:
                for dag in st.session_state['arbejdsdage'].get(k_id, ALLE_DAGE_GLOBAL):
                    if global_tæller[uge_id][k_id][dag] < 8:
                        global_tæller[uge_id][k_id][dag] += 1
                        st.session_state['aftaler'].append({**kunde, "kundenavn": kunde['navn'], "uge_id": uge_id, "dag": dag, "id": f"{kunde['id']}-{uge_id}"})
                        break

# --- UI LOGIK ---
if not st.session_state['logget_ind']:
    st.title("Login")
    with st.form("l"):
        u = st.text_input("Bruger"); p = st.text_input("Kode", type="password")
        if st.form_submit_button("Log ind"):
            st.session_state.update({'logget_ind': True, 'bruger_navn': u, 'bruger_rolle': 'admin' if u == 'admin' else 'konsulent'})
            st.rerun()
    st.stop()

# --- HOVEDSKÆRM ---
st.sidebar.button("Log ud", on_click=lambda: st.session_state.update({'logget_ind': False}))
valgt_uge = st.sidebar.selectbox("Uge:", sorted(list({a["uge_id"] for a in st.session_state['aftaler']})) or ["Ingen"])

cols = st.columns(5)
for i, dag in enumerate(ALLE_DAGE_GLOBAL):
    with cols[i]:
        st.subheader(f"{dag[:3]}.")
        for a in [x for x in st.session_state['aftaler'] if x["dag"] == dag and x["uge_id"] == valgt_uge]:
            with st.container(border=True):
                st.write(f"**{a.get('kundenavn', 'Ukendt')}**")
                st.caption(f"{a.get('postnr', '')} {a.get('by', '')}")
                nyt_valg = st.selectbox("Flyt:", ALLE_DAGE_GLOBAL, index=ALLE_DAGE_GLOBAL.index(dag), key=f"sel_{a['id']}")
                if nyt_valg != dag:
                    st.session_state['manuelle_flytninger'][a['id']] = nyt_valg
                    gem_data_til_disken(); kør_rullende_kalender_motor(); st.rerun()
