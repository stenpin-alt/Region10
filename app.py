import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Ruteplanlægger Pro", layout="wide")

# --- CSS: TVING STREGER FREM ---
st.markdown("""
    <style>
        /* Tvinger kolonnerne til at få en streg til højre */
        [data-testid="column"] {
            border-right: 2px solid #e6e9ef !important;
            padding-right: 15px !important;
            padding-left: 10px !important;
        }
        [data-testid="column"]:last-of-type {
            border-right: none !important;
        }
        .block-container { padding-top: 1rem !important; }
    </style>
""", unsafe_allow_html=True)

# Globale variabler
ALLE_DAGE_GLOBAL = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag"]
BOPÆL_POSTNUMRE = {
    "Brian Felix Fabian": 4690, "Daniel Hemmingsen": 2730, "Carsten Bülow": 4000,
    "Morten Hedemand": 5210, "Allan Rechnagel": 6100, "Kristof": 4550,
    "Kristof Stenpin": 4550, "Mark Rosendal Beermann": 9300, "Ole Schulze": 2990,
    "Emil Nielsen": 9900, "Kristian Paulin": 8700, "Troels Jørgensen": 8700,
    "Dennis Borup Lejel": 8900, "Frederik Esmarch": 7800, "Martin Kliver": 5550,
    "Daniel Murad": 8000, "Thomas Jakobsen": 2640, "Mai Utzon": 4140,
}

# --- FIL-HÅNDTERING ---
FIL_KUNDER, FIL_KONSULENTER, FIL_FLYTNINGER, FIL_KODER = "gemt_kunder.csv", "gemt_konsulenter.csv", "gemt_flytninger.csv", "gemt_koder.csv"

def gem_data():
    if st.session_state['kunder']: pd.DataFrame(st.session_state['kunder']).to_csv(FIL_KUNDER, index=False)
    if st.session_state['konsulenter']: pd.DataFrame([{"id": k, "navn": v["navn"]} for k, v in st.session_state['konsulenter'].items()]).to_csv(FIL_KONSULENTER, index=False)
    pd.DataFrame([{"id": k, "dag": v} for k, v in st.session_state['manuelle_flytninger'].items()]).to_csv(FIL_FLYTNINGER, index=False)
    pd.DataFrame([{"navn": k, "kode": v} for k, v in st.session_state['bruger_koder'].items()]).to_csv(FIL_KODER, index=False)

def hent_data():
    if os.path.exists(FIL_KONSULENTER):
        df_kons = pd.read_csv(FIL_KONSULENTER)
        st.session_state['konsulenter'] = {int(r["id"]): {"navn": str(r["navn"])} for _, r in df_kons.iterrows()}
    if os.path.exists(FIL_KUNDER): st.session_state['kunder'] = pd.read_csv(FIL_KUNDER).to_dict(orient="records")
    if os.path.exists(FIL_FLYTNINGER): st.session_state['manuelle_flytninger'] = {str(r["id"]): str(r["dag"]) for _, r in pd.read_csv(FIL_FLYTNINGER).iterrows()}
    if os.path.exists(FIL_KODER): st.session_state['bruger_koder'] = {str(r["navn"]): str(r["kode"]) for _, r in pd.read_csv(FIL_KODER).iterrows()}

# --- INITIALISERING ---
if 'konsulenter' not in st.session_state:
    st.session_state.update({'konsulenter': {}, 'kunder': [], 'aftaler': [], 'arbejdsdage': {}, 'manuelle_flytninger': {}, 'bruger_koder': {}, 'logget_ind': False, 'bruger_rolle': None, 'bruger_navn': None})
    hent_data()

def tjek_login(navn, kode):
    n, k = navn.strip().lower(), kode.strip()
    if n == "admin" and k == st.session_state['bruger_koder'].get("admin", "admin123"):
        st.session_state.update({'logget_ind': True, 'bruger_rolle': 'admin', 'bruger_navn': 'Administrator'}); return True
    for k_id, k_info in st.session_state['konsulenter'].items():
        fuldt, fornavn = k_info["navn"].lower(), k_info["navn"].lower().split(" ")[0]
        if (n == fuldt or n == fornavn) and (k == st.session_state['bruger_koder'].get(k_info["navn"], "Region10") or k.lower() == "region10"):
            st.session_state.update({'logget_ind': True, 'bruger_rolle': 'konsulent', 'bruger_navn': k_info["navn"], 'valgt_konsulent_id_login': k_id}); return True
    return False

# --- LOGIN SKÆRM ---
if not st.session_state['logget_ind']:
    st.title("🔐 Ruteplanlægger Pro - Login")
    with st.form("login_form"):
        u = st.text_input("Brugernavn (Fornavn eller fulde navn)"); p = st.text_input("Adgangskode", type="password")
        if st.form_submit_button("Log ind"):
            if tjek_login(u, p): st.rerun()
            else: st.error("Forkert login.")
    st.stop()

# --- HOVEDLOGIK ---
st.sidebar.markdown(f"👤 Bruger: **{st.session_state['bruger_navn']}**")
if st.sidebar.button("Log ud 🔓"): st.session_state.update({'logget_ind': False}); st.rerun()

# Rute Motor
def kør_rute_motor():
    start_mandag = datetime.now() - timedelta(days=datetime.now().weekday())
    st.session_state['aftaler'] = []
    for uge_frem in range(0, 12):
        mål_mandag = start_mandag + timedelta(weeks=uge_frem)
        uge_id = f"{mål_mandag.year}-Uge{mål_mandag.isocalendar()[1]}"
        for k_id, k_info in st.session_state['konsulenter'].items():
            for kunde in [k for k in st.session_state['kunder'] if int(k["konsulent_id"]) == int(k_id)]:
                # Forenklet logik for eksemplet
                dag = "Mandag"
                st.session_state['aftaler'].append({"id": f"{kunde['id']}-{uge_id}", "kunde_id": kunde["id"], "kundenavn": kunde["navn"], "by": kunde["by"], "postnr": kunde["postnr"], "konsulent_id": k_id, "uge_id": uge_id, "dag": dag})

if not st.session_state['aftaler']: kør_rute_motor()

# Visning
st.title("🗺️ Ruteplanlægger Pro")
if st.session_state['konsulenter']:
    valgt_id = st.sidebar.selectbox("Vis rute for:", options=list(st.session_state['konsulenter'].keys()), format_func=lambda x: st.session_state['konsulenter'][x]["navn"])
    cols = st.columns(5)
    for i, dag in enumerate(ALLE_DAGE_GLOBAL):
        with cols[i]:
            st.subheader(dag)
            for aftale in [a for a in st.session_state['aftaler'] if int(a["konsulent_id"]) == int(valgt_id) and a["dag"] == dag]:
                with st.container(border=True):
                    st.write(f"**{aftale['kundenavn']}**")
                    st.caption(f"{aftale['postnr']} {aftale['by']}")
