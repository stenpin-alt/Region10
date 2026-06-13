import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Ruteplanlægger Pro - Sikker Login", layout="wide")

# Globale variabler
ALLE_DAGE_GLOBAL = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag"]

# Præcise bopæls-postnumre hentet direkte fra jeres konsulentliste
BOPÆL_POSTNUMRE = {
    "Brian Felix Fabian": 4690, "Daniel Hemmingsen": 2730, "Carsten Bülow": 4000,
    "Morten Hedemand": 5210, "Allan Rechnagel": 6100, "Kristof": 4550,
    "Kristof Stenpin": 4550, "Mark Rosendal Beermann": 9300, "Ole Schulze": 2990,
    "Emil Nielsen": 9900, "Kristian Paulin": 8700, "Troels Jørgensen": 8700,
    "Dennis Borup Lejel": 8900, "Frederik Esmarch": 7800, "Martin Kliver": 5550,
    "Daniel Murad": 8000, "Thomas Jakobsen": 2640, "Mai Utzon": 4140,
}

# --- SESSION STATE DATABASE ---
if 'db_initialiseret' not in st.session_state:
    st.session_state['konsulenter'] = {}
    st.session_state['kunder'] = []
    st.session_state['aftaler'] = []
    st.session_state['sidste_fil_navn'] = None
    st.session_state['arbejdsdage'] = {}
    st.session_state['logget_ind'] = False
    st.session_state['bruger_rolle'] = None  # 'admin' eller 'konsulent'
    st.session_state['bruger_navn'] = None
    st.session_state['db_initialiseret'] = True

# --- LOGIN FUNKTION ---
def tjek_login(brugernavn, kode):
    # Admin Tjek
    if brugernavn.lower() == "admin" and kode == "admin123":
        st.session_state['logget_ind'] = True
        st.session_state['bruger_rolle'] = "admin"
        st.session_state['bruger_navn'] = "Administrator"
        return True
    
    # Konsulent Tjek (Tjekker mod de indlæste konsulenter fra Excel)
    for k_id, k_info in st.session_state['konsulenter'].items():
        if brugernavn.strip().lower() == k_info["navn"].lower() and kode == "konsulent123":
            st.session_state['logget_ind'] = True
            st.session_state['bruger_rolle'] = "konsulent"
            st.session_state['bruger_navn'] = k_info["navn"]
            st.session_state['valgt_konsulent_id_login'] = k_id
            return True
            
    return False

# --- ZONE-FARVEMARKERING ---
def hent_zone_og_farve(pnr):
    try: pnr_int = int(''.join(filter(str.isdigit, str(pnr))))
    except: return "Ukendt område", "⚪"
    if 1000 <= pnr_int <= 3999: return "Storkøbenhavn/Nordsjælland", "🔵"
    elif 4000 <= pnr_int <= 4999: return "Vest-/Sydsjælland", "🟢"
    elif 5000 <= pnr_int <= 5999: return "Fyn & Øer", "🟡"
    elif 6000 <= pnr_int <= 6999: return "Sydjylland", "🟠"
    elif 7000 <= pnr_int <= 7999: return "Midt-/Vestjylland", "🟣"
    elif 8000 <= pnr_int <= 8999: return "Østjylland", "🔴"
    return "Nordjylland", "⚫"

# --- KLYNGE-MOTOR ---
def kør_rullende_kalender_motor():
    idag = datetime.now()
    start_mandag = idag - timedelta(days=idag.weekday())
    
    gamle_aftaler_kort = {}
    for a in st.session_state['aftaler']:
        gamle_aftaler_kort[f"{a['kunde_id']}-{a['uge_id']}"] = a["dag"]
        
    st.session_state['aftaler'] = []
    AUTOMATISK_LOFT = 8
    MAX_LOFT = 10
    global_tæller = {}

    for uge_frem in range(0, 24):
        mål_mandag = start_mandag + timedelta(weeks=uge_frem)
        uge_nummer = mål_mandag.isocalendar()[1]
        år = mål_mandag.year
        uge_id = f"{år}-Uge{uge_nummer}"
        
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
                        
                        if unik_nøgle in gamle_aftaler_kort:
                            v_dag = gamle_aftaler_kort[unik_nøgle]
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

# --- VIS LOGINELEMENT HVIS IKKE LOGGET IND ---
if not st.session_state['logget_ind']:
    st.title("🔐 Ruteplanlægger Pro - Login")
    with st.form("login_form"):
        u_input = st.text_input("Brugernavn (Konsulentens fulde navn eller 'admin')")
        p_input = st.text_input("Adgangskode", type="password")
        submitted = st.form_submit_button("Log ind")
        if submitted:
            # Hvis databasen er tom (første opstart online), tillader vi admin at logge ind for at uploade
            if u_input.lower() == "admin" and p_input == "admin123":
                st.session_state['logget_ind'] = True
                st.session_state['bruger_rolle'] = "admin"
                st.session_state['bruger_navn'] = "Administrator"
                st.rerun()
            elif tjek_login(u_input, p_input):
                st.rerun()
            else:
                st.error("Forkert brugernavn eller adgangskode. Bemærk: Konsulenter kan først logge ind, når Excel-listen ER uploadet af admin.")
    st.stop()

# --- HVIS LOGGET IND: VIS APP ---
st.sidebar.markdown(f"👤 Logget ind som: **{st.session_state['bruger_navn']}** ({st.session_state['bruger_rolle'].upper()})")
if st.sidebar.button("Log ud 🔓"):
    st.session_state['logget_ind'] = False
    st.rerun()

# --- EXCEL UPLOAD LOGIK (KUN FOR ADMIN) ---
if st.session_state['bruger_rolle'] == "admin":
    st.sidebar.header("📂 Admin: Upload data")
    uploaded_file = st.sidebar.file_uploader("Upload kundeliste (Excel)", type=["xlsx", "xls"])

    if uploaded_file is not None and uploaded_file.name != st.session_state['sidste_fil_navn']:
        try:
            df_indlæst = pd.read_excel(uploaded_file, skiprows=2)
            df_indlæst.columns = df_indlæst.columns.astype(str).str.strip()
            col_konsulent = "Konsulent" if "Konsulent" in df_indlæst.columns else df_indlæst.columns[0]
            col_navn = "Navn" if "Navn" in df_indlæst.columns else None
            col_by = "By" if "By" in df_indlæst.columns else None
            col_frek = "Besøgs frekvens" if "Besøgs frekvens" in df_indlæst.columns else None
            col_postnr = "Postnr" if "Postnr" in df_indlæst.columns else ("Postnummer" if "Postnummer" in df_indlæst.columns else None)
            
            if not col_postnr:
                for c in df_indlæst.columns:
                    if "post" in c.lower() or "pnr" in c.lower(): col_postnr = c; break
            
            if col_navn and col_by and col_postnr:
                unikke_kons_navne = sorted(df_indlæst[col_konsulent].dropna().unique())
                nye_konsulenter = {}
                kons_navn_til_id = {}
                for index, k_navn in enumerate(unikke_kons_navne):
                    k_id = index + 1
                    nye_konsulenter[k_id] = {"navn": str(k_navn).strip()}
                    kons_navn_til_id[str(k_navn).strip()] = k_id
                
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
                st.session_state['aftaler'] = [] 
                st.session_state['sidste_fil_navn'] = uploaded_file.name
                kør_rullende_kalender_motor()
                st.sidebar.success(f"Indlæst: {len(nye_kunder)} kunder!")
                st.rerun()
        except Exception as e: st.sidebar.error(f"Fejl: {e}")

# --- FILTER LOGIK (CRITICAL SECURITY) ---
if st.session_state['bruger_rolle'] == "admin":
    # Admin kan vælge alle i en boks
    if len(st.session_state['konsulenter']) > 0:
        valgt_konsulent_id = st.sidebar.selectbox(
            "Vælg visning for konsulent:", options=list(st.session_state['konsulenter'].keys()),
            format_func=lambda x: st.session_state['konsulenter'][x]["navn"]
        )
        konsulent_navn = st.session_state['konsulenter'][valgt_konsulent_id]["navn"]
    else:
        valgt_konsulent_id = 1; konsulent_navn = "Ingen data indlæst"
else:
    # KONSULENT KAN KUN SE SIG SELV - INGEN VALGMULIGHEDER
    valgt_konsulent_id = st.session_state['valgt_konsulent_id_login']
    konsulent_navn = st.session_state['bruger_navn']

# --- ARBEJDSDAGE & UGEVALG ---
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
valgt_uge = st.sidebar.selectbox("Vælg uge:", options=visnings_uger if visnings_uger else ["Ingen data"])

# --- KALENDER VISNING ---
st.title("🗺️ Web-App Ruteplanlægger Pro")

if len(st.session_state['kunder']) == 0:
    st.info("💡 Velkommen! Log ind som 'admin' og upload jeres Excel-kundeliste i menuen til venstre for at starte ruteplanlægningen.")
else:
    st.header(f"📅 Ruteplan for: {konsulent_navn} — {valgt_uge}")
    b_pnr = BOPÆL_POSTNUMRE.get(konsulent_navn, "Ukendt")
    st.caption(f"🏠 Udgangspunkt: Bopæl i postnummer {b_pnr}")

    aktuelle_aftaler = [a for a in st.session_state['aftaler'] if a["konsulent_id"] == valgt_konsulent_id and a["uge_id"] == valgt_uge]
    kolonner = st.columns(5)

    for i, dag in enumerate(ALLE_DAGE_GLOBAL):
        with kolonner[i]:
            if dag not in valgte_dage:
                st.markdown(f"### ~~{dag}~~")
                st.caption("🚫 Fri / Ikke rutedag")
            else:
                st.markdown(f"### {dag}")
                dag_aftaler = sorted([a for a in aktuelle_aftaler if a["dag"] == dag], key=lambda x: str(x["postnr"]))
                
                antal_besøg = len(dag_aftaler)
                if antal_besøg <= 8: st.caption(f"Besøg: {antal_besøg} / 8 (+2 buffer)")
                else: st.caption(f"Besøg: 8 / 8 (+{antal_besøg - 8} buffer i brug)")
                
                if not dag_aftaler: st.info("Ingen besøg")
                    
                for _idx, _aftale in enumerate(dag_aftaler):
                    zone_navn, farve = hent_zone_og_farve(_aftale["postnr"])
                    with st.container(border=True):
                        st.markdown(f"**{farve} {_aftale['kundenavn']}**")
                        st.text(f"📍 {_aftale['postnr']} {_aftale['by']}")
                        
                        ny_dag = st.selectbox(
                            "Flyt:", options=valgte_dage, index=valgte_dage.index(dag) if dag in valgte_dage else 0,
                            key=f"flyt-{_aftale['id']}-{_idx}", label_visibility="collapsed"
                        )
                        if ny_dag != dag:
                            antal_på_ny_dag = sum(1 for a in aktuelle_aftaler if a["dag"] == ny_dag)
                            if antal_på_ny_dag >= 10: st.error("Fuld (Max 10)!")
                            else:
                                for master_idx, a in enumerate(st.session_state['aftaler']):
                                    if a["id"] == _aftale["id"]:
                                        st.session_state['aftaler'][master_idx]["dag"] = ny_dag
                                        st.rerun()