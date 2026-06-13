import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Convenience Ruteplanlægger", layout="wide")

# CSS
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; }
        div[data-testid="column"] { border-right: 1.5px solid #e6e9ef; padding-right: 15px; }
    </style>
""", unsafe_allow_html=True)

ALLE_DAGE_GLOBAL = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag"]
FIL_KUNDER, FIL_FLYTNINGER = "gemt_kunder.csv", "gemt_flytninger.csv"

# Session State
if 'kunder' not in st.session_state: st.session_state['kunder'] = []
if 'aftaler' not in st.session_state: st.session_state['aftaler'] = []
if 'manuelle_flytninger' not in st.session_state: st.session_state['manuelle_flytninger'] = {}
if 'konsulenter' not in st.session_state: st.session_state['konsulenter'] = {1: {"navn": "Standard Konsulent"}}

def gem_data():
    if st.session_state['manuelle_flytninger']:
        pd.DataFrame([{"id": k, "dag": v} for k, v in st.session_state['manuelle_flytninger'].items()]).to_csv(FIL_FLYTNINGER, index=False)

def kør_motor():
    st.session_state['aftaler'] = []
    idag = datetime.now()
    start_mandag = idag - timedelta(days=idag.weekday())
    global_tæller = {}
    
    for uge_frem in range(0, 12):
        mål_mandag = start_mandag + timedelta(weeks=uge_frem)
        uge_id = f"{mål_mandag.year}-Uge{mål_mandag.isocalendar()[1]}"
        if uge_id not in global_tæller: global_tæller[uge_id] = {}

        for k_id in st.session_state['konsulenter'].keys():
            if k_id not in global_tæller[uge_id]: global_tæller[uge_id][k_id] = {d: 0 for d in ALLE_DAGE_GLOBAL}
            
            # Find kundeliste
            kunder = [k for k in st.session_state['kunder'] if int(k.get("konsulent_id", 1)) == int(k_id)]
            
            for k in kunder:
                k_id_str = f"{k['id']}-{uge_id}"
                # Prioriter manuel flytning
                dag = st.session_state['manuelle_flytninger'].get(k_id_str)
                if not dag:
                    # Find første dag med plads under 8
                    for d in ALLE_DAGE_GLOBAL:
                        if global_tæller[uge_id][k_id][d] < 8:
                            dag = d
                            break
                
                if dag and global_tæller[uge_id][k_id][dag] < 10:
                    global_tæller[uge_id][k_id][dag] += 1
                    st.session_state['aftaler'].append({**k, "id": k_id_str, "uge_id": uge_id, "dag": dag})

# Indlæs
if os.path.exists(FIL_KUNDER) and not st.session_state['kunder']:
    st.session_state['kunder'] = pd.read_csv(FIL_KUNDER).to_dict(orient="records")
if os.path.exists(FIL_FLYTNINGER):
    df = pd.read_csv(FIL_FLYTNINGER)
    st.session_state['manuelle_flytninger'] = {str(r["id"]): str(r["dag"]) for _, r in df.iterrows()}

kør_motor()

# Visning
st.title("🗺️ Convenience Ruteplanlægger")
valgt_uge = st.sidebar.selectbox("Vælg uge:", sorted(list({a["uge_id"] for a in st.session_state['aftaler']})))
cols = st.columns(5)

for i, dag in enumerate(ALLE_DAGE_GLOBAL):
    with cols[i]:
        st.subheader(dag)
        aftaler = [a for a in st.session_state['aftaler'] if a["dag"] == dag and a["uge_id"] == valgt_uge]
        for aftale in aftaler:
            with st.container(border=True):
                st.write(f"**{aftale['navn']}**")
                # UNIK KEY her løser din Streamlit API fejl
                ny_dag = st.selectbox("Flyt til:", ALLE_DAGE_GLOBAL, index=ALLE_DAGE_GLOBAL.index(dag), 
                                      key=f"sel_{aftale['id']}_{dag}")
                if ny_dag != dag:
                    st.session_state['manuelle_flytninger'][aftale['id']] = ny_dag
                    gem_data()
                    st.rerun()
