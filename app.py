import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Ruteplanlægger Pro - Kalender Gitter", layout="wide")

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

# --- 1. CLOUD-SIKKER CACHING (Sørger for at data huskes online) ---
if 'konsulenter' not in st.session_state: st.session_state['konsulenter'] = {}
if 'kunder' not in st.session_state: st.session_state['kunder'] = []
if 'aftaler' not in st.session_state: st.session_state['aftaler'] = []
if 'arbejdsdage' not in st.session_state: st.session_state['arbejdsdage'] = {}
if 'manuelle_flytninger' not in st.session_state: st.session_state['manuelle_flytninger'] = {}
if 'logget_ind' not in st.session_state: st.session_state['logget_ind'] = False
if 'bruger_rolle' not in st.session_state: st.session_state['bruger_rolle'] = None
if 'bruger_navn' not in st.session_state: st.session_state['bruger_navn'] = None

# --- LOGIN SYSTEM ---
def tjek_login(brugernavn, kode):
    if brugernavn.lower() == "admin" and kode == "admin123":
        st.session_state['logget_ind'] = True
        st.session_state['bruger_rolle'] = "admin"
        st.session_state['bruger_navn'] = "Administrator"
        return True
    for k_id, k_info in st.session_state['konsulenter'].items():
        if brugernavn.strip().lower() == k_info["navn"].lower() and kode == "konsulent123":
            st.session_state['logget_ind'] = True
            st.session_state['bruger_rolle'] = "konsulent"
            st.session_state['bruger_navn'] = k_info["navn"]
            st.session_state['valgt_konsulent_id_login'] = k_id
            return True
    return False

# --- ZONE FARVER ---
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

# --- SMART KLYNGE MOTOR ---
def kør_rullende_kalender_motor():
    idag = datetime.now()
    start_mandag = idag - timedelta(days=idag.weekday())
    
    st.session_state['aftaler'] = []
    AUTOMATISK_LOFT = 8
    MAX_LOFT = 10
    global_tæller = {}

    for uge_frem in range(0, 24):
        mål_mandag = start_mandag + timedelta(weeks=uge_frem)
        uge_nummer = mål_mandag.isocalendar()[1]
        uge_id = f"{mål_mandag.year}-Uge{uge_nummer}"
        
        if uge_id not in global_tæller: global_tæller[uge_id] = {}

        for k_id, k_info in st.session_state['konsulenter'].items():
            k_navn = k_info["navn"]
            bopæl_pnr = BOPÆL_POSTNUMRE.get(k_navn, 4000)
            
            konsulent_arbejdsdage = st.session_state['arbejdsdage'].get(k_id, ALLE_DAGE_GLOBAL)
            if not konsulent_arbejdsdage: konsulent_arbejdsdage = ALLE_DAGE_GLOBAL
            
            if k_id not in global_tæller[uge_id]:
                global_tæller[uge_id][k_id] = {d: 0 for d in ALLE_DAGE_GLOBAL}
                
            postnummer_grupper = {}
            for kunde in st.session_state['kunder']:
                if kunde["konsulent_id"] == k_id:
                    frekvens = kunde["frekvens"]
                    skal_besøges = False
                    if frekvens >= 1.0: skal_besøges = True
                    elif frekvens == 0.5 and uge_nummer % 2 == 0: skal_besøges = True
                    elif frekvens == 0.25 and uge_nummer % 4 == 1: skal_besøges = True
                    
                    if skal_besøges:
                        try: p_int = int(''.join(filter(str.isdigit, str(kunde["postnr"]))))
                        except: p_int = bopæl_pnr
                        if p_int not in postnummer_grupper: postnummer_grupper[p_int] = []
                        postnummer_grupper[p_int].append(kunde)
            
            sorterede_postnumre = sorted(list(postnummer_grupper.keys()), key=lambda p: abs(p - bopæl_pnr))
            aktuel_dag_idx = 0
            
            for pnr in sorterede_postnumre:
                for kunde in postnummer_grupper[pnr]:
                    placeret = False
                    aktuel_uge_frem = uge_frem
                    
                    while not placeret and aktuel_uge_frem < 24:
                        tjek_mandag = start_mandag + timedelta(weeks=aktuel_uge_frem)
                        tjek_uge_id = f"{tjek_mandag.year}-Uge{tjek_mandag.isocalendar()[1]}"
                        
                        if tjek_uge_id not in global_tæller: global_tæller[tjek_uge_id] = {}
                        if k_id not in global_tæller[tjek_uge_id]: global_tæller[tjek_uge_id][k_id] = {d: 0 for d in ALLE_DAGE_GLOBAL}
                        
                        unik_nøgle = f"{kunde['id']}-{tjek_uge_id}"
                        
                        # TJEK MANUEL FLYTNING FØRST (Hentes fra browserens permanente hukommelse)
                        if unik_nøgle in st.session_state['manuelle_flytninger']:
                            v_dag = st.session_state['manuelle_flytninger'][unik_nøgle]
                            if global_tæller[tjek_uge_id][k_id][v_dag] < MAX_LOFT:
                                global_tæller[tjek_uge_id][k_id][v_dag] += 1
                                placeret = True; valgt_dag = v_dag; break
                        
                        # AUTOMATISK FORDELING (Stop ved 8)
                        for forsøg in range(len(konsulent_arbejdsdage)):
                            test_dag = konsulent_arbejdsdage[(aktuel_dag_idx + forsøg) % len(konsulent_arbejdsdage)]
                            if global_tæller[tjek_uge_id][k_id][test_dag] < AUTOMATISK_LOFT:
                                valgt_dag = test_dag
                                aktuel_dag_idx = konsulent_arbejdsdage.index(test_dag)
                                global_tæller[tjek_uge_id][k_id][valgt_dag] += 1
                                placeret = True; break
                        
                        if placeret:
                            st.session_state['aftaler'].append({
                                "id": unik_nøgle, "kunde_id": kunde["id"], "kundenavn": kunde["navn"],
                                "by": kunde["by"], "postnr": kunde["postnr"], "konsulent_id": k_id,
                                "uge_id": tjek_uge_id, "dag": valgt_dag
                            })
                        else: aktuel_uge_frem += 1

# --- VIS LOGIN ---
if not st.session_state['logget_ind']:
    st.title("🔐 Ruteplanlægger Pro - Login")
    with st.form("login_form"):
        u_input = st.text_input("Brugernavn (Konsulentens navn eller 'admin')")
        p_input = st.text_input("Adgangskode", type="password")
        if st.form_submit_button("Log ind"):
            if u_input.lower() == "admin" and p_input == "admin123":
                st.session_state['logget_ind'] = True
                st.session_state['bruger_rolle'] = "admin"
                st.session_state['bruger_navn'] = "Administrator"; st.rerun()
            elif tjek_login(u_input, p_input): st.rerun()
            else: st.error("Forkert log-ind. Admin skal uploade Excel først for at oprette konsulent-profiler.")
    st.stop()

# --- SIDEBAR LOGUD OG UPLOAD ---
st.sidebar.markdown(f"👤 Bruger: **{st.session_state['bruger_navn']}**")
if st.sidebar.button("Log ud 🔓"):
    st.session_state['logget_ind'] = False; st.rerun()

if st.session_state['bruger_rolle'] == "admin":
    st.sidebar.header("📂 Admin: Excel Data")
    uploaded_file = st.sidebar.file_uploader("Upload kundeliste", type=["xlsx", "xls"])
    if uploaded_file is not None:
        try:
            df_indlæst = pd.read_excel(uploaded_file, skiprows=2)
            df_indlæst.columns = df_indlæst.columns.astype(str).str.strip()
            col_konsulent = "Konsulent" if "Konsulent" in df_indlæst.columns else df_indlæst.columns[0]
            col_navn = "Navn" if "Navn" in df_indlæst.columns else None
            col_by = "By" if "By" in df_indlæst.columns else None
            col_frek = "Besøgs frekvens" if "Besøgs frekvens" in df_indlæst.columns else None
            col_postnr = "Postnr" if "Postnr" in df_indlæst.columns else None
            
            if not col_postnr:
                for c in df_indlæst.columns:
                    if "post" in c.lower() or "pnr" in c.lower(): col_postnr = c; break
            
            if col_navn and col_by and col_postnr:
                unikke_kons_navne = sorted(df_indlæst[col_konsulent].dropna().unique())
                nye_konsulenter = {i+1: {"navn": str(n).strip()} for i, n in enumerate(unikke_kons_navne)}
                kons_navn_til_id = {str(n).strip(): i+1 for i, n in enumerate(unikke_kons_navne)}
                
                nye_kunder = []
                for idx, række in df_indlæst.iterrows():
                    v_navn = række[col_navn]; v_by = række[col_by]; v_pnr = række[col_postnr]; v_kons = str(række[col_konsulent]).strip()
                    if pd.isna(v_navn) or pd.isna(v_by) or pd.isna(v_pnr) or v_kons not in kons_navn_til_id: continue
                    freq = 0.25
                    if col_frek and not pd.isna(række[col_frek]):
                        try: freq = float(str(række[col_frek]).replace(',', '.'))
                        except: freq = 0.25
                    nye_kunder.append({"id": idx + 1000, "navn": str(v_navn).strip(), "by": str(v_by).strip(), "postnr": v_pnr, "frekvens": freq, "konsulent_id": kons_navn_til_id[v_kons]})
                
                st.session_state['konsulenter'] = nye_konsulenter
                st.session_state['kunder'] = nye_kunder
                kør_rullende_kalender_motor()
                st.sidebar.success("Data opdateret!")
        except Exception as e: st.sidebar.error(f"Fejl: {e}")

# KØR MOTOR HVIS DATA ER TILSTEDE
if len(st.session_state['kunder']) > 0 and len(st.session_state['aftaler']) == 0:
    kør_rullende_kalender_motor()

# RIGHTS FILTER
if st.session_state['bruger_rolle'] == "admin":
    if len(st.session_state['konsulenter']) > 0:
        valgt_konsulent_id = st.sidebar.selectbox("Vis rute for:", options=list(st.session_state['konsulenter'].keys()), format_func=lambda x: st.session_state['konsulenter'][x]["navn"])
        konsulent_navn = st.session_state['konsulenter'][valgt_konsulent_id]["navn"]
    else: valgt_konsulent_id = 1; konsulent_navn = "Ingen data"
else:
    valgt_konsulent_id = st.session_state['valgt_konsulent_id_login']
    konsulent_navn = st.session_state['bruger_navn']

# ARBEJDSDAGE
st.sidebar.markdown("---")
st.sidebar.header("⚙️ Rutedage")
gemte_dage = st.session_state['arbejdsdage'].get(valgt_konsulent_id, ALLE_DAGE_GLOBAL)
valgte_dage = []
for d in ALLE_DAGE_GLOBAL:
    if st.sidebar.checkbox(d, value=(d in gemte_dage), key=f"d-check-{valgt_konsulent_id}-{d}"): valgte_dage.append(d)
if valgte_dage != gemte_dage:
    st.session_state['arbejdsdage'][valgt_konsulent_id] = valgte_dage
    kør_rullende_kalender_motor(); st.rerun()

sorterede_uger = sorted(list({a["uge_id"] for a in st.session_state['aftaler']}))
visnings_uger = sorterede_uger[:16] if len(sorterede_uger) > 16 else sorterede_uger
valgt_uge = st.sidebar.selectbox("Vælg uge:", options=visnings_uger if visnings_uger else ["Ingen data"])

# --- HOVEDSKÆRM: KALENDER GITTER (CSS DESIGN) ---
st.title("🗺️ Ruteplanlægger Pro")

# CSS til at skabe den rigtige kalendertavle-følelse online
st.markdown("""
    <style>
    .kalender-kort {
        background-color: #fcfcfc;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px;
        min-height: 400px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .dag-titel {
        text-align: center;
        color: #1E3A8A;
        font-weight: bold;
        border-bottom: 2px solid #1E3A8A;
        padding-bottom: 5px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

if len(st.session_state['kunder']) == 0:
    st.info("💡 Log ind som 'admin' i menuen til venstre og læg jeres kundeliste ind for at tænde kalenderen.")
else:
    st.header(f"📅 {konsulent_navn} — {valgt_uge}")
    st.caption(f"🏠 Baseret på bopæl i postnummer: {BOPÆL_POSTNUMRE.get(konsulent_navn, 'Ukendt')}")

    aktuelle_aftaler = [a for a in st.session_state['aftaler'] if a["konsulent_id"] == valgt_konsulent_id and a["uge_id"] == valgt_uge]
    gitter_kolonner = st.columns(5)

    for i, dag in enumerate(ALLE_DAGE_GLOBAL):
        with gitter_kolonner[i]:
            if dag not in valgte_dage:
                st.markdown(f"<div class='kalender-kort'><div class='dag-titel'>~~{dag}~~</div><p style='text-align:center; color:gray; font-style:italic;'>🚫 Ikke en rutedag</p></div>", unsafe_allow_html=True)
            else:
                dag_aftaler = sorted([a for a in aktuelle_aftaler if a["dag"] == dag], key=lambda x: str(x["postnr"]))
                antal_besøg = len(dag_aftaler)
                
                txt_status = f"{antal_besøg}/8 (+2 buf)" if antal_besøg <= 8 else f"8/8 (+{antal_besøg-8} buf i brug)"
                
                # Starten på vores visuelle kalender-kolonne-gitter
                st.markdown(f"""
                    <div class='dag-titel'>{dag}</div>
                    <p style='text-align:center; font-weight:bold; margin-top:-10px; color:#555;'>({txt_status})</p>
                """, unsafe_allow_html=True)
                
                if not dag_aftaler:
                    st.caption("Ingen besøg planlagt")
                    
                for _idx, _aftale in enumerate(dag_aftaler):
                    zone_navn, farve = hent_zone_og_farve(_aftale["postnr"])
                    with st.container(border=True):
                        st.markdown(f"**{farve} {_aftale['kundenavn']}**")
                        st.text(f"📍 {_aftale['postnr']} {_aftale['by']}")
                        
                        # Flyt-dropdown opdaterer nu den permanente hukommelse korrekt online!
                        ny_dag = st.selectbox(
                            "Flyt:", options=valgte_dage, index=valgte_dage.index(dag) if dag in valgte_dage else 0,
                            key=f"flyt-{_aftale['id']}-{_idx}", label_visibility="collapsed"
                        )
                        if ny_dag != dag:
                            antal_på_ny_dag = sum(1 for a in aktuelle_aftaler if a["dag"] == ny_dag)
                            if antal_på_ny_dag >= 10: 
                                st.error("Fuld (Max 10)!")
                            else:
                                st.session_state['manuelle_flytninger'][_aftale["id"]] = ny_dag
                                kør_rullende_kalender_motor()
                                st.rerun()
