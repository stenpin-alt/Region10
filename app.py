import streamlit as st
import pandas as pd
import os
import io

# Konfiguration
st.set_page_config(page_title="Convenience Ruteplanlægger", layout="wide")

# Globale konstanter
ALLE_DAGE = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag"]
FIL_KUNDER = "kunder.csv"

# Initialisering af session state
if 'kunder' not in st.session_state: st.session_state['kunder'] = []
if 'konsulenter' not in st.session_state: st.session_state['konsulenter'] = {}
if 'arbejdsdage' not in st.session_state: st.session_state['arbejdsdage'] = {}
if 'manuelle_flytninger' not in st.session_state: st.session_state['manuelle_flytninger'] = {}

# Motor til beregning
@st.cache_data
def beregn_ruter(kunder, konsulenter, arbejdsdage, flytninger):
    aftaler = []
    for k_id, k_info in konsulenter.items():
        k_dage = arbejdsdage.get(str(k_id), ALLE_DAGE)
        k_kunder = [k for k in kunder if str(k.get("konsulent_id")) == str(k_id)]
        
        for uge in range(1, 53):
            uge_id = f"2026-Uge{uge:02d}"
            dag_load = {d: 0 for d in ALLE_DAGE}
            
            # 1. Håndter manuelle flytninger
            for kunde in k_kunder:
                u_key = f"{kunde['id']}-{uge_id}"
                if u_key in flytninger:
                    dag = flytninger[u_key]
                    if dag in k_dage:
                        dag_load[dag] += 1
                        aftaler.append({**kunde, "uge_id": uge_id, "dag": dag, "id": u_key})

            # 2. Håndter automatisk frekvens (Kun frekvens-kolonnen)
            for kunde in k_kunder:
                try: freq = float(str(kunde.get("frekvens", 0)).replace(',', '.'))
                except: freq = 0
                
                if freq > 0:
                    interval = int(1/freq)
                    if uge % interval == 0:
                        u_key = f"{kunde['id']}-{uge_id}"
                        if not any(a["id"] == u_key for a in aftaler):
                            dag = min(k_dage, key=lambda d: dag_load[d])
                            dag_load[dag] += 1
                            aftaler.append({**kunde, "uge_id": uge_id, "dag": dag, "id": u_key})
    return aftaler

# Sidebar - Admin
st.sidebar.header("Admin")
uploaded = st.sidebar.file_uploader("Upload Excel kundeliste", type=["xlsx"])
if uploaded:
    df = pd.read_excel(uploaded, skiprows=2)
    st.session_state['konsulenter'] = {i+1: {"navn": n} for i, n in enumerate(df.iloc[:,0].unique())}
    navn_map = {v["navn"]: k for k, v in st.session_state['konsulenter'].items()}
    st.session_state['kunder'] = []
    for _, r in df.iterrows():
        st.session_state['kunder'].append({
            "id": r[1], "navn": r[1], "postnr": r[2], "by": r[3],
            "frekvens": r[6], "konsulent_id": navn_map[r[0]]
        })
    st.rerun()

# Hovedskærm
if not st.session_state['kunder']:
    st.warning("Upload venligst en Excel-fil for at starte.")
else:
    kons_keys = list(st.session_state['konsulenter'].keys())
    valgt_id = st.sidebar.selectbox("Vælg konsulent", kons_keys, format_func=lambda x: st.session_state['konsulenter'][x]["navn"])
    valgt_uge = st.sidebar.selectbox("Vælg uge", [f"2026-Uge{u:02d}" for u in range(1, 53)])
    
    st.title(f"Ruteplan: {st.session_state['konsulenter'][valgt_id]['navn']}")
    aftaler = beregn_ruter(st.session_state['kunder'], st.session_state['konsulenter'], st.session_state['arbejdsdage'], st.session_state['manuelle_flytninger'])
    
    cols = st.columns(5)
    for i, dag in enumerate(ALLE_DAGE):
        with cols[i]:
            st.subheader(dag[:3])
            for a in [a for a in aftaler if a["konsulent_id"] == valgt_id and a["uge_id"] == valgt_uge and a["dag"] == dag]:
                with st.container(border=True):
                    st.write(f"**{a['navn']}**")
                    st.caption(f"{a['postnr']} {a['by']}")
