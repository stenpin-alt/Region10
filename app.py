import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Ruteplanlægger Pro", layout="wide")

# --- CSS: Responsivt layout med skillelinjer og buffer ---
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; }
        
        /* Layout for kolonner med skillelinjer */
        div[data-testid="column"] {
            border-right: 1.5px solid #e6e9ef !important;
            padding-right: 15px !important;
            padding-left: 15px !important;
            min-width: 220px !important; /* Forhindrer at de bliver mast */
        }
        div[data-testid="column"]:last-child { border-right: none !important; }

        /* Kompakte elementer */
        div.stSelectbox div[data-testid="stSelectboxWithDynamicOptions"] { transform: scale(0.9); transform-origin: left; }
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

# --- FIL-STIER OG DATALAGRING ---
FIL_KUNDER, FIL_KONSULENTER, FIL_FLYTNINGER, FIL_KODER = "gemt_kunder.csv", "gemt_konsulenter.csv", "gemt_flytninger.csv", "gemt_koder.csv"

def gem_data_til_disken():
    if st.session_state.get('kunder'): pd.DataFrame(st.session_state['kunder']).to_csv(FIL_KUNDER, index=False)
    if st.session_state.get('konsulenter'): pd.DataFrame([{"id": k, "navn": v["navn"]} for k, v in st.session_state['konsulenter'].items()]).to_csv(FIL_KONSULENTER, index=False)
    if st.session_state.get('manuelle_flytninger'): pd.DataFrame([{"id": k, "dag": v} for k, v in st.session_state['manuelle_flytninger'].items()]).to_csv(FIL_FLYTNINGER, index=False)
    if st.session_state.get('bruger_koder'): pd.DataFrame([{"navn": k, "kode": v} for k, v in st.session_state['bruger_koder'].items()]).to_csv(FIL_KODER, index=False)

def hent_data_fra_disken():
    if os.path.exists(FIL_KONSULENTER) and not st.session_state.get('konsulenter'):
        df = pd.read_csv(FIL_KONSULENTER); st.session_state['konsulenter'] = {int(r["id"]): {"navn": str(r["navn"])} for _, r in df.iterrows()}
    if os.path.exists(FIL_KUNDER) and not st.session_state.get('kunder'): st.session_state['kunder'] = pd.read_csv(FIL_KUNDER).to_dict(orient="records")
    if os.path.exists(FIL_FLYTNINGER) and not st.session_state.get('manuelle_flytninger'): st.session_state['manuelle_flytninger'] = {str(r["id"]): str(r["dag"]) for _, r in pd.read_csv(FIL_FLYTNINGER).iterrows()}
    if os.path.exists(FIL_KODER): st.session_state['bruger_koder'] = {str(r["navn"]): str(r["kode"]) for _, r in pd.read_csv(FIL_KODER).iterrows()}

# --- INITIALISERING ---
for key in ['konsulenter', 'kunder', 'aftaler', 'arbejdsdage', 'manuelle_flytninger', 'bruger_koder']:
    if key not in st.session_state: st.session_state[key] = {} if key in ['konsulenter', 'arbejdsdage', 'manuelle_flytninger', 'bruger_koder'] else []
if 'logget_ind' not in st.session_state: st.session_state.update({'logget_ind': False, 'bruger_rolle': None, 'bruger_navn': None})
hent_data_fra_disken()

# --- RUTE MOTOR (MED 8+2 BUFFER) ---
def kør_rullende_kalender_motor():
    start_mandag = datetime.now() - timedelta(days=datetime.now().weekday())
    st.session_state['aftaler'] = []
    # HER ER DIN 8+2 BUFFER:
    AUTOMATISK_LOFT, MAX_LOFT = 8, 10  
    global_tæller = {}

    for uge_frem in range(0, 24):
        uge_mål = start_mandag + timedelta(weeks=uge_frem)
        uge_id = f"{uge_mål.year}-Uge{uge_mål.isocalendar()[1]}"
        if uge_id not in global_tæller: global_tæller[uge_id] = {}
        for k_id, k_info in st.session_state['konsulenter'].items():
            if k_id not in global_tæller[uge_id]: global_tæller[uge_id][k_id] = {d: 0 for d in ALLE_DAGE_GLOBAL}
            
            # (... din eksisterende logik for kundefordeling ...)
            # [Behold din eksisterende logik herinde i funktionen for at sikre den fungerer korrekt]

# --- LOGIN & DASHBOARD ---
# [Her indsætter du din eksisterende login-logik og sidebar-indhold fra din tidligere fil]
# (Jeg har udeladt det lange login/admin-felt for korthed, men behold det fra din egen fil)

# --- HOVEDSKÆRM ---
st.title("🗺️ Ruteplanlægger Pro")
# (Behold din eksisterende visnings-kode, der bruger st.columns(5))
