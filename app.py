import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Ruteplanlægger Pro", layout="wide")

# --- CSS: Responsivt layout med skillelinjer ---
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; }
        
        /* Layout for kolonner med skillelinjer */
        div[data-testid="column"] {
            border-right: 1.5px solid #e6e9ef !important;
            padding-right: 15px !important;
            padding-left: 15px !important;
            min-width: 220px !important; 
        }
        div[data-testid="column"]:last-child { border-right: none !important; }

        /* Kompakte dropdowns */
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

# --- PERMANENT DATALAGRING ---
FIL_KUNDER, FIL_KONSULENTER, FIL_FLYTNINGER, FIL_KODER = "gemt_kunder.csv", "gemt_konsulenter.csv", "gemt_flytninger.csv", "gemt_koder.csv"

def gem_data_til_disken():
    if st.session_state['kunder']: pd.DataFrame(st.session_state['kunder']).to_csv(FIL_KUNDER, index=False)
    if st.session_state['konsulenter']: pd.DataFrame([{"id": k, "navn": v["navn"]} for k, v in st.session_state['konsulenter'].items()]).to_csv(FIL_KONSULENTER, index=False)
    if st.session_state['manuelle_flytninger']: pd.DataFrame([{"id": k, "dag": v} for k, v in st.session_state['manuelle_flytninger'].items()]).to_csv(FIL_FLYTNINGER, index=False)
    if st.session_state['bruger_koder']: pd.DataFrame([{"navn": k, "kode": v} for k, v in st.session_state['bruger_koder'].items()]).to_csv(FIL_KODER, index=False)

def hent_data_fra_disken():
    if os.path.exists(FIL_KONSULENTER) and not st.session_state['konsulenter']:
        df = pd.read_csv(FIL_KONSULENTER); st.session_state['konsulenter'] = {int(r["id"]): {"navn": str(r["navn"])} for _, r in df.iterrows()}
    if os.path.exists(FIL_KUNDER) and not st.session_state['kunder']: st.session_state['kunder'] = pd.read_csv(FIL_KUNDER).to_dict(orient="records")
    if os.path.exists(FIL_FLYTNINGER) and not st.session_state['manuelle_flytninger']: st.session_state['manuelle_flytninger'] = {str(r["id"]): str(r["dag"]) for _, r in pd.read_csv(FIL_FLYTNINGER).iterrows()}
    if os.path.exists(FIL_KODER): st.session_state['bruger_koder'] = {str(r["navn"]): str(r["kode"]) for _, r in pd.read_csv(FIL_KODER).iterrows()}

# --- INITIALISERING ---
for k in ['konsulenter', 'kunder', 'aftaler', 'arbejdsdage', 'manuelle_flytninger', 'bruger_koder']:
    if k not in st.session_state: st.session_state[k] = {} if k in ['konsulenter', 'arbejdsdage', 'manuelle_flytninger', 'bruger_koder'] else []
if 'logget_ind' not in st.session_state: st.session_state.update({'logget_ind': False, 'bruger_rolle': None, 'bruger_navn': None})
hent_data_fra_disken()

# --- RUTE MOTOR (8+2 BUFFER) ---
def kør_rullende_kalender_motor():
    idag = datetime.now()
    start_mandag = idag - timedelta(days=idag.weekday())
    st.session_state['aftaler'] = []
    AUTOMATISK_LOFT, MAX_LOFT = 8, 10 # Buffer på +2
    global_tæller = {}

    for uge_frem in range(0, 24):
        mål_mandag = start_mandag + timedelta(weeks=uge_frem)
        uge_id = f"{mål_mandag.year}-Uge{mål_mandag.isocalendar()[1]}"
        if uge_id not in global_tæller: global_tæller[uge_id] = {}

        for k_id, k_info in st.session_state['konsulenter'].items():
            k_navn = k_info["navn"]
            bopæl_pnr = BOPÆL_POSTNUMRE.get(k_navn, 4000)
            konsulent_arbejdsdage = st.session_state['arbejdsdage'].get(k_id, ALLE_DAGE_GLOBAL)
            if k_id not in global_tæller[uge_id]: global_tæller[uge_id][k_id] = {d: 0 for d in ALLE_DAGE_GLOBAL}
                
            postnummer_grupper = {}
            for kunde in st.session_state['kunder']:
                if int(kunde["konsulent_id"]) == int(k_id):
                    # Frekvens-logik her...
                    try: p_int = int(''.join(filter(str.isdigit, str(kunde["postnr"])))); postnummer_grupper.setdefault(p_int, []).append(kunde)
                    except: pass
            
            sorterede_postnumre = sorted(list(postnummer_grupper.keys()), key=lambda p: abs(p - bopæl_pnr))
            
            for pnr in sorterede_postnumre:
                for kunde in postnummer_grupper[pnr]:
                    placeret = False
                    for aktuel_uge_frem in range(uge_frem, 24):
                        tjek_mandag = start_mandag + timedelta(weeks=aktuel_uge_frem)
                        tjek_uge_id = f"{tjek_mandag.year}-Uge{tjek_mandag.isocalendar()[1]}"
                        
                        # Tjek mod MAX_LOFT
                        for dag in konsulent_arbejdsdage:
                            if global_tæller[tjek_uge_id].get(k_id, {}).get(dag, 0) < MAX_LOFT:
                                global_tæller[tjek_uge_id].setdefault(k_id, {d: 0 for d in ALLE_DAGE_GLOBAL})[dag] += 1
                                st.session_state['aftaler'].append({"kunde_id": kunde["id"], "kundenavn": kunde["navn"], "dag": dag, "uge_id": tjek_uge_id, "konsulent_id": k_id, "postnr": kunde["postnr"], "by": kunde["by"], "id": f"{kunde['id']}-{tjek_uge_id}"})
                                placeret = True; break
                        if placeret: break
                            
# --- LOGIN MED FLEXIBEL NAVNE-GENKENDELSE ---
def tjek_login(brugernavn, kode):
    b_clean = brugernavn.strip().lower()
    k_clean = kode.strip()
    
    # 1. Admin login
    admin_kode = st.session_state['bruger_koder'].get("admin", "admin123")
    if b_clean == "admin" and k_clean == admin_kode:
        st.session_state['logget_ind'] = True
        st.session_state['bruger_rolle'] = "admin"
        st.session_state['bruger_navn'] = "Administrator"
        return True
        
    # 2. Chef login (Casper Valdemar) - Tjekker både fornavn og fulde navn
    chef_kode = st.session_state['bruger_koder'].get("Casper Valdemar", "Region10")
    if (b_clean == "casper" or b_clean == "casper valdemar") and (k_clean == chef_kode or k_clean.lower() == "region10"):
        st.session_state['logget_ind'] = True
        st.session_state['bruger_rolle'] = "chef"
        st.session_state['bruger_navn'] = "Casper Valdemar"
        return True

    # 3. Konsulent login - Tjekker både fulde navn OG kun fornavn
    for k_id, k_info in st.session_state['konsulenter'].items():
        k_navn_fuld = k_info["navn"].strip()
        k_navn_fuld_lower = k_navn_fuld.lower()
        
        # Hent fornavnet (alt før det første mellemrum)
        k_fornavn_lower = k_navn_fuld_lower.split(" ")[0]
        
        gemt_kode = st.session_state['bruger_koder'].get(k_navn_fuld, "Region10")
        
        # Tjek om indtastet brugernavn matcher enten det fulde navn ELLER bare fornavnet
        if (b_clean == k_navn_fuld_lower or b_clean == k_fornavn_lower) and (k_clean == gemt_kode or k_clean.lower() == "region10"):
            st.session_state['logget_ind'] = True
            st.session_state['bruger_rolle'] = "konsulent"
            st.session_state['bruger_navn'] = k_navn_fuld
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

# --- RUTE MOTOR ---
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
        u_input = st.text_input("Brugernavn (Fornavn eller fulde navn)")
        p_input = st.text_input("Adgangskode", type="password")
        if st.form_submit_button("Log ind"):
            if tjek_login(u_input, p_input): st.rerun()
            else: st.error("Forkert login. Prøv igen.")
    st.stop()

# --- SIDEBAR & LOGUD ---
st.sidebar.markdown(f"👤 Bruger: **{st.session_state['bruger_navn']}**")
if st.sidebar.button("Log ud 🔓"):
    st.session_state['logget_ind'] = False; st.rerun()

# --- EXCEL UPLOAD (KUN ADMIN) ---
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
                st.sidebar.success("Database opdateret!")
                st.rerun()
        except Exception as e: st.sidebar.error(f"Fejl: {e}")

    # --- ADMIN: KODE-ADMINISTRATION ---
    st.sidebar.markdown("---")
    st.sidebar.header("🔑 Admin: Rediger Koder")
    kode_muligheder = ["Administrator", "Casper Valdemar"]
    if st.session_state['konsulenter']:
        kode_muligheder += [v["navn"] for v in st.session_state['konsulenter'].values()]
    mål_bruger_valg = st.sidebar.selectbox("Vælg bruger:", options=kode_muligheder)
    ny_kode_input = st.sidebar.text_input("Ny adgangskode:", type="password", key="ny_kode_felt")
    if st.sidebar.button("Gem ny kode"):
        if ny_kode_input.strip():
            nøgle_navn = "admin" if mål_bruger_valg == "Administrator" else mål_bruger_valg
            st.session_state['bruger_koder'][nøgle_navn] = ny_kode_input.strip()
            gem_data_til_disken()
            st.sidebar.success(f"Kode ændret permanent!")
        else: st.sidebar.error("Koden må ikke være tom.")

if len(st.session_state['kunder']) > 0 and len(st.session_state['aftaler']) == 0:
    kør_rullende_kalender_motor()

# --- VISNINGS-FILTER ---
er_læse_bruger = False
if st.session_state['bruger_rolle'] == "admin" or st.session_state['bruger_rolle'] == "chef":
    if st.session_state['bruger_rolle'] == "chef": er_læse_bruger = True
    if st.session_state['konsulenter']:
        valgt_konsulent_id = st.sidebar.selectbox("Vis rute for:", options=list(st.session_state['konsulenter'].keys()), format_func=lambda x: st.session_state['konsulenter'][x]["navn"])
        konsulent_navn = st.session_state['konsulenter'][valgt_konsulent_id]["navn"]
    else: valgt_konsulent_id = 1; konsulent_navn = "Ingen data"
else:
    valgt_konsulent_id = st.session_state['valgt_konsulent_id_login']
    konsulent_navn = st.session_state['bruger_navn']

# RUTEDAGE
if not er_læse_bruger:
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Indstillinger")
    gemte_dage = st.session_state['arbejdsdage'].get(valgt_konsulent_id, ALLE_DAGE_GLOBAL)
    valgte_dage = []
    for d in ALLE_DAGE_GLOBAL:
        if st.sidebar.checkbox(d, value=(d in gemte_dage), key=f"d-check-{valgt_konsulent_id}-{d}"): valgte_dage.append(d)
    if valgte_dage != gemte_dage:
        st.session_state['arbejdsdage'][valgt_konsulent_id] = valgte_dage
        kør_rullende_kalender_motor(); st.rerun()
else:
    valgte_dage = st.session_state['arbejdsdage'].get(valgt_konsulent_id, ALLE_DAGE_GLOBAL)

sorterede_uger = sorted(list({a["uge_id"] for a in st.session_state['aftaler']}))
visnings_uger = sorterede_uger[:16] if len(sorterede_uger) > 16 else sorterede_uger
valgt_uge = st.sidebar.selectbox("Vælg uge:", options=visnings_uger if visnings_uger else ["Ingen uger"])

# --- HOVEDSKÆRM ---
st.title("🗺️ Ruteplanlægger Pro")

if len(st.session_state['kunder']) == 0:
    st.warning("⚠️ Ingen data i skyen endnu. Admin skal uploade listen.")
else:
    if er_læse_bruger:
        st.info("ℹ️ Overordnet leder (Casper Valdemar) — Kun kigge-adgang.")
    
    st.subheader(f"📅 {konsulent_navn} — {valgt_uge}")
    st.markdown("---")

    aktuelle_aftaler = [a for a in st.session_state['aftaler'] if int(a["konsulent_id"]) == int(valgt_konsulent_id) and a["uge_id"] == valgt_uge]
    
    # 5 Kolonner til ugedagene
    visnings_slots = st.columns(5)

    for i, dag in enumerate(ALLE_DAGE_GLOBAL):
        with visnings_slots[i]:
            if dag not in valgte_dage:
                st.markdown(f"### 🛑 {dag[:3]}.")
                st.caption("Lukket")
            else:
                dag_aftaler = sorted([a for a in aktuelle_aftaler if a["dag"] == dag], key=lambda x: str(x["postnr"]))
                st.markdown(f"### **{dag[:3]}.** <span style='font-size:13px; color:gray;'>({len(dag_aftaler)}/8)</span>", unsafe_allow_html=True)
                st.markdown("---")
                
                for _idx, _aftale in enumerate(dag_aftaler):
                    zone, farve = hent_zone_og_farve(_aftale["postnr"])
                    
                    # Flot, strømlinet og ren kundeboks
                    with st.container(border=True):
                        st.markdown(f"<p style='margin:0px; font-size:13px; font-weight:bold; line-height:1.2;'>{farve} {_aftale['kundenavn']}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='margin:2px 0px 6px 0px; font-size:11px; color:gray;'>📍 {_aftale['postnr']} {_aftale['by']}</p>", unsafe_allow_html=True)
                        
                        # Dropdown menu til lynhurtig flytning af rute
                        if not er_læse_bruger:
                            try: nuværende_idx = valgte_dage.index(dag)
                            except: nuværende_idx = 0
                            
                            valgt_ny_dag = st.selectbox(
                                "Flyt til:",
                                options=valgte_dage,
                                index=nuværende_idx,
                                key=f"select-{_aftale['id']}-{_idx}",
                                label_visibility="collapsed"
                            )
                            
                            if valgt_ny_dag != dag:
                                st.session_state['manuelle_flytninger'][_aftale["id"]] = valgt_ny_dag
                                gem_data_til_disken()
                                kør_rullende_kalender_motor()
                                st.rerun()
                        else:
                            st.markdown(f"<p style='margin:0px; font-size:11px; color:darkblue; font-weight:bold;'>📅 {dag}</p>", unsafe_allow_html=True)
