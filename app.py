import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Ruteplanlægger Pro", layout="wide")

# --- Globale variabler ---
ALLE_DAGE_GLOBAL = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag"]
BOPÆL_POSTNUMRE = {
    "Brian Felix Fabian": 4690, "Daniel Hemmingsen": 2730, "Carsten Bülow": 4000,
    "Morten Hedemand": 5210, "Allan Rechnagel": 6100, "Kristof": 4550,
    "Kristof Stenpin": 4550, "Mark Rosendal Beermann": 9300, "Ole Schulze": 2990,
    "Emil Nielsen": 9900, "Kristian Paulin": 8700, "Troels Jørgensen": 8700,
    "Dennis Borup Lejel": 8900, "Frederik Esmarch": 7800, "Martin Kliver": 5550,
    "Daniel Murad": 8000, "Thomas Jakobsen": 2640, "Mai Utzon": 4140,
}

# --- FIL-STIER ---
FIL_KUNDER = "gemt_kunder.csv"
FIL_KONSULENTER = "gemt_konsulenter.csv"
FIL_FLYTNINGER = "gemt_flytninger.csv"
FIL_KODER = "gemt_koder.csv"

# --- HJÆLPEFUNKTIONER ---
def gem_data_til_disken():
    if 'kunder' in st.session_state: pd.DataFrame(st.session_state['kunder']).to_csv(FIL_KUNDER, index=False)
    if 'konsulenter' in st.session_state: 
        pd.DataFrame([{"id": k, "navn": v["navn"]} for k, v in st.session_state['konsulenter'].items()]).to_csv(FIL_KONSULENTER, index=False)
    if 'manuelle_flytninger' in st.session_state:
        pd.DataFrame([{"id": k, "dag": v} for k, v in st.session_state['manuelle_flytninger'].items()]).to_csv(FIL_FLYTNINGER, index=False)
    if 'bruger_koder' in st.session_state:
        pd.DataFrame([{"navn": k, "kode": v} for k, v in st.session_state['bruger_koder'].items()]).to_csv(FIL_KODER, index=False)

def hent_data_fra_disken():
    if os.path.exists(FIL_KONSULENTER) and not st.session_state.get('konsulenter'):
        df = pd.read_csv(FIL_KONSULENTER)
        st.session_state['konsulenter'] = {int(r["id"]): {"navn": str(r["navn"])} for _, r in df.iterrows()}
    if os.path.exists(FIL_KUNDER) and not st.session_state.get('kunder'):
        st.session_state['kunder'] = pd.read_csv(FIL_KUNDER).to_dict(orient="records")
    if os.path.exists(FIL_FLYTNINGER) and not st.session_state.get('manuelle_flytninger'):
        st.session_state['manuelle_flytninger'] = {str(r["id"]): str(r["dag"]) for _, r in pd.read_csv(FIL_FLYTNINGER).iterrows()}
    if os.path.exists(FIL_KODER):
        st.session_state['bruger_koder'] = {str(r["navn"]): str(r["kode"]) for _, r in pd.read_csv(FIL_KODER).iterrows()}

# --- INITIALISERING ---
if 'kunder' not in st.session_state: st.session_state.update({'kunder': [], 'konsulenter': {}, 'aftaler': [], 'arbejdsdage': {}, 'manuelle_flytninger': {}, 'bruger_koder': {}, 'logget_ind': False})
hent_data_fra_disken()

# --- LOGIN LOGIK ---
def tjek_login(b, k):
    if b.lower() == "admin" and k == st.session_state['bruger_koder'].get("admin", "admin123"):
        st.session_state.update({'logget_ind': True, 'bruger_rolle': 'admin', 'bruger_navn': 'Administrator'})
        return True
    for k_id, k_info in st.session_state['konsulenter'].items():
        if b.lower() in [k_info['navn'].lower(), k_info['navn'].split()[0].lower()]:
            if k == st.session_state['bruger_koder'].get(k_info['navn'], "Region10"):
                st.session_state.update({'logget_ind': True, 'bruger_rolle': 'konsulent', 'bruger_navn': k_info['navn'], 'valgt_konsulent_id_login': k_id})
                return True
    return False

# --- HOVED-UI ---
if not st.session_state['logget_ind']:
    st.title("🔐 Ruteplanlægger Pro")
    with st.form("login"):
        u = st.text_input("Brugernavn")
        p = st.text_input("Kode", type="password")
        if st.form_submit_button("Log ind"):
            if tjek_login(u, p): st.rerun()
            else: st.error("Fejl i login")
    st.stop()

# --- DASHBOARD ---
st.title("🗺️ Ruteplanlægger Pro")
if st.sidebar.button("Log ud"): st.session_state['logget_ind'] = False; st.rerun()

# Visning af dage i beholdere (Responsivt og stabilt)
cols = st.columns(5)
for i, dag in enumerate(ALLE_DAGE_GLOBAL):
    with cols[i]:
        with st.container(border=True): # Dette skaber rammen/boksen uden CSS
            st.subheader(f"{dag}")
            # Her ville din filtrering af aftaler ligge...
            st.caption("Viser aftaler her...")
