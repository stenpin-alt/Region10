import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Ruteplanlægger Pro", layout="wide")

# Globale variabler
ALLE_DAGE_GLOBAL = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag"]
DAG_KORT = {"Mandag": "Ma", "Tirsdag": "Ti", "Onsdag": "On", "Torsdag": "To", "Fredag": "Fr"}

BOPÆL_POSTNUMRE = {
    "Brian Felix Fabian": 4690, "Daniel Hemmingsen": 2730, "Carsten Bülow": 4000,
    "Morten Hedemand": 5210, "Allan Rechnagel": 6100, "Kristof": 4550,
    "Kristof Stenpin": 4550, "Mark Rosendal Beermann": 9300, "Ole Schulze": 2990,
    "Emil Nielsen": 9900, "Kristian Paulin": 8700, "Troels Jørgensen": 8700,
    "Dennis Borup Lejel": 8900, "Frederik Esmarch": 7800, "Martin Kliver": 5550,
    "Daniel Murad": 8000, "Thomas Jakobsen": 2640, "Mai Utzon": 4140,
}

# --- PERMANENT DATALAGRING ---
FIL_KUNDER = "gemt_kunder.csv"
FIL_KONSULENTER = "gemt_konsulenter.csv"
FIL_FLYTNINGER = "gemt_flytninger.csv"
FIL_KODER = "gemt_koder.csv"

def gem_data_til_disken():
    if st.session_state['kunder']:
        pd.DataFrame(st.session_state['kunder']).to_csv(FIL_KUNDER, index=False)
    if st.session_state['konsulenter']:
        df_kons = pd.DataFrame([{"id": k, "navn": v["navn"]} for k, v in st.session_state['konsulenter'].items()])
        df_kons.to_csv(FIL_KONSULENTER, index=False)
    if st.session_state['manuelle_flytninger']:
        df_flyt = pd.DataFrame([{"id": k, "dag": v} for k, v in st.session_state['manuelle_flytninger'].items()])
        df_flyt.to_csv(FIL_FLYTNINGER, index=False)
    if st.session_state['konsulent_koder']:
        df_koder = pd.DataFrame([{"navn": k, "kode": v} for k, v in st.session_state['konsulent_koder'].items()])
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
    if os.path.exists(FIL_KODER):
        df_koder = pd.read_csv(FIL_KODER)
        st.session_state['konsulent_koder'] = {str(r["navn"]): str(r["kode"]) for _, r in df_koder.iterrows()}

# --- INITIALISERING ---
if 'konsulenter' not in st.session_state: st.session_state['konsulenter'] = {}
if 'kunder' not in st.session_state: st.session_state['kunder'] = []
if 'aftaler' not in st.session_state: st.session_state['aftaler'] = []
if 'arbejdsdage' not in st.session_state: st.session_state['arbejdsdage'] = {}
if 'manuelle_flytninger' not in st.session_state: st.session_state['manuelle_flytninger'] = {}
if 'konsulent_koder' not in st.session_state: st.session_state['konsulent_koder'] = {}
if 'logget_ind' not in st.session_state: st.session_state['logget_ind'] = False
if 'bruger_rolle' not in st.session_state: st.session_state['bruger_rolle'] = None
if 'bruger_navn' not in st.session_state: st.session_state['bruger_navn'] = None

hent_data_fra_disken()

# --- LOGIN FUNKTION M. JUSTERBARE KODER ---
def tjek_login(brugernavn, kode):
    if brugernavn.lower() == "admin" and kode == "admin123":
        st.session_state['logget_ind'] = True
        st.session_state['bruger_rolle'] = "admin"
        st.session_state['bruger_navn'] = "Administrator"
        return True
    
    for k_id, k_info in st.session_state['konsulenter'].items():
        k_navn = k_info["navn"]
        # Hent den gemte kode, eller brug standard 'konsulent123'
        gemt_kode = st.session_state['konsulent_koder'].get(k_navn, "konsulent123")
        
        if brugernavn.strip().lower() == k_navn.lower() and kode == gemt_kode:
            st.session_state['logget_ind'] = True
            st.session_state['bruger_rolle'] = "konsulent"
            st.session_state['bruger_navn'] = k_navn
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
                if int(kunde["konsulent_id"]) == int(k_id):
                    frekvens = float(kunde["frekvens"])
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
                        
                        if unik_nøgle in st.session_state['manuelle_flytninger']:
                            v_dag = st.session_state['manuelle_flytninger'][unik_nøgle]
                            if global_tæller[tjek_uge_id][k_id][v_dag] < MAX_LOFT:
                                global_tæller[tjek_uge_id][k_id][v_dag] += 1
                                placeret = True; valgt_dag = v_dag; break
                        
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

# --- LOGIN SKÆRM ---
if not st.session_state['logget_ind']:
    st.title("🔐 Ruteplanlægger Pro - Login")
    with st.form("login_form"):
        u_input = st.text_input("Brugernavn (Funde navn eller 'admin')")
        p_input = st.text_input("Adgangskode", type="password")
        if st.form_submit_button("Log ind"):
            if tjek_login(u_input, p_input): st.rerun()
            else: st.error("Forkert login. Kontakt din administrator.")
    st.stop()

# --- SIDEBAR & LOGUD ---
st.sidebar.markdown(f"👤 Logget ind som: **{st.session_state['bruger_navn']}**")
if st.sidebar.button("Log ud 🔓"):
    st.session_state['logget_ind'] = False; st.rerun()

# --- EXCEL UPLOAD ---
if st.session_state['bruger_rolle'] == "admin":
    st.sidebar.header("📂 Admin: Excel Upload")
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
                st.session_state['konsulenter'] = {i+1: {"navn": str(n).strip()} for i, n in enumerate(unikke_kons_navne)}
                kons_navn_til_id = {str(n).strip(): i+1 for i, n in enumerate(unikke_kons_navne)}
                st.session_state['kunder'] = []
                for idx, række in df_indlæst.iterrows():
                    v_navn = række[col_navn]; v_by = række[col_by]; v_pnr = række[col_postnr]; v_kons = str(række[col_konsulent]).strip()
                    if pd.isna(v_navn) or pd.isna(v_by) or pd.isna(v_pnr) or v_kons not in kons_navn_til_id: continue
                    freq = 0.25
                    if col_frek and not pd.isna(række[col_frek]):
                        try: freq = float(str(række[col_frek]).replace(',', '.'))
                        except: freq = 0.25
                    st.session_state['kunder'].append({"id": idx + 1000, "navn": str(v_navn).strip(), "by": str(v_by).strip(), "postnr": v_pnr, "frekvens": freq, "konsulent_id": kons_navn_til_id[v_kons]})
                gem_data_til_disken()
                kør_rullende_kalender_motor()
                st.sidebar.success("Database gemt permanent!")
                st.rerun()
        except Exception as e: st.sidebar.error(f"Fejl under upload: {e}")

    # --- ADMIN: KODE-ADMINISTRATION ---
    st.sidebar.markdown("---")
    st.sidebar.header("🔑 Admin: Rediger Koder")
    if st.session_state['konsulenter']:
        mål_kons_navn = st.sidebar.selectbox("Vælg konsulent:", options=[v["navn"] for v in st.session_state['konsulenter'].values()])
        ny_kode_input = st.sidebar.text_input("Ny adgangskode:", type="password", key="ny_kode_felt")
        if st.sidebar.button("Gem ny kode"):
            if ny_kode_input.strip():
                st.session_state['konsulent_koder'][mål_kons_navn] = ny_kode_input.strip()
                gem_data_til_disken()
                st.sidebar.success(f"Kode ændret for {mål_kons_navn}!")
            else:
                st.sidebar.error("Koden må ikke være tom.")

if len(st.session_state['kunder']) > 0 and len(st.session_state['aftaler']) == 0:
    kør_rullende_kalender_motor()

# RETTIGHEDSFILTER
if st.session_state['bruger_rolle'] == "admin":
    if len(st.session_state['konsulenter']) > 0:
        valgt_konsulent_id = st.sidebar.selectbox("Vis rute for:", options=list(st.session_state['konsulenter'].keys()), format_func=lambda x: st.session_state['konsulenter'][x]["navn"])
        konsulent_navn = st.session_state['konsulenter'][valgt_konsulent_id]["navn"]
    else: valgt_konsulent_id = 1; konsulent_navn = "Ingen data"
else:
    valgt_konsulent_id = st.session_state['valgt_konsulent_id_login']
    konsulent_navn = st.session_state['bruger_navn']

# KONFIGURATION AF RUTEDAGE
st.sidebar.markdown("---")
st.sidebar.header("⚙️ Indstillinger")
gemte_dage = st.session_state['arbejdsdage'].get(valgt_konsulent_id, ALLE_DAGE_GLOBAL)
valgte_dage = []
for d in ALLE_DAGE_GLOBAL:
    if st.sidebar.checkbox(d, value=(d in gemte_dage), key=f"d-check-{valgt_konsulent_id}-{d}"): valgte_dage.append(d)
if valgte_dage != gemte_dage:
    st.session_state['arbejdsdage'][valgt_konsulent_id] = valgte_dage
    kør_rullende_kalender_motor(); st.rerun()

sorterede_uger = sorted(list({a["uge_id"] for a in st.session_state['aftaler']}))
visnings_uger = sorterede_uger[:16] if len(sorterede_uger) > 16 else sorterede_uger
valgt_uge = st.sidebar.selectbox("Vælg uge:", options=visnings_uger if visnings_uger else ["Ingen uger"])

# --- HOVEDSKÆRM: KALENDER ---
st.title("🗺️ Mobilvenlig Ruteplanlægger Pro")

if len(st.session_state['kunder']) == 0:
    st.warning("⚠️ Ingen data i skyen endnu. Admin skal uploade listen i menuen til venstre.")
else:
    st.subheader(f"📅 Rute for: {konsulent_navn} — {valgt_uge}")
    st.caption(f"🏠 Startbopæl: Postnummer {BOPÆL_POSTNUMRE.get(konsulent_navn, 'Ukendt')}")
    st.markdown("---")

    aktuelle_aftaler = [a for a in st.session_state['aftaler'] if int(a["konsulent_id"]) == int(valgt_konsulent_id) and a["uge_id"] == valgt_uge]
    
    # MOBIL-DETEKTOR (Bruger en Streamlit sidebar-bredde genvej til at tjekke skærm-layout)
    # Vi laver 5 rigtige kolonner på computerskærm, men lader dem stable, hvis skærmen er lille.
    skærm_layout = st.radio("Skærmvisning (Optimering):", ["💻 Computer (Gitter)", "📱 Mobiltelefon (Liste)"], horizontal=True, label_visibility="collapsed")

    if skærm_layout == "💻 Computer (Gitter)":
        visnings_slots = st.columns(5)
    else:
        visnings_slots = [st.container() for _ in range(5)]

    for i, dag in enumerate(ALLE_DAGE_GLOBAL):
        with visnings_slots[i]:
            with st.container(border=True):
                if dag not in valgte_dage:
                    st.markdown(f"### 🛑 <span style='color:gray;'>~~{dag}~~</span>", unsafe_allow_html=True)
                    st.caption("Ingen kørsel")
                else:
                    dag_aftaler = sorted([a for a in aktuelle_aftaler if a["dag"] == dag], key=lambda x: str(x["postnr"]))
                    antal_besøg = len(dag_aftaler)
                    status_tekst = f"{antal_besøg}/8 (+2)" if antal_besøg <= 8 else f"8/8 (+{antal_besøg-8} i buffer)"
                    
                    st.markdown(f"### 📅 {dag}")
                    st.markdown(f"**`Status: {status_tekst}`**")
                    st.markdown("---")
                    
                    if not dag_aftaler:
                        st.info("Ingen besøg")
                    
                    for _idx, _aftale in enumerate(dag_aftaler):
                        zone, farve = hent_zone_og_farve(_aftale["postnr"])
                        
                        with st.container(border=True):
                            st.markdown(f"**{farve} {_aftale['kundenavn']}**")
                            st.caption(f"📍 {_aftale['postnr']} {_aftale['by']}")
                            
                            # SMARTE ET-KLIK KNAPPER TIL MOBILEN I STEDET FOR DROPDOWN
                            st.markdown("<p style='font-size:11px; margin-bottom:2px; color:gray;'>Flyt rute til:</p>", unsafe_allow_html=True)
                            knap_kolonner = st.columns(len(valgte_dage))
                            
                            for k_idx, m_dag in enumerate(valgte_dage):
                                with knap_kolonner[k_idx]:
                                    # Vis dagens forbogstaver (f.eks. Ma, Ti, On)
                                    kort_navn = DAG_KORT.get(m_dag, m_dag[:2])
                                    
                                    # Gør knappen aktiv eller passiv baseret på om kunden allerede er der
                                    if m_dag == dag:
                                        st.button(kort_navn, key=f"btn-{_aftale['id']}-{m_dag}-{_idx}", disabled=True, use_container_width=True)
                                    else:
                                        if st.button(kort_navn, key=f"btn-{_aftale['id']}-{m_dag}-{_idx}", use_container_width=True):
                                            st.session_state['manuelle_flytninger'][_aftale["id"]] = m_dag
                                            gem_data_til_disken()
                                            kør_rullende_kalender_motor()
                                            st.rerun()
