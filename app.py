import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(
    page_title="Convenience Ruteplanlægger Pro", 
    layout="wide",
    page_icon="logo.png"
)
st.sidebar.image("logo.png", use_container_width=True)
    
# CSS-optimering med flotte lodrette skillelinjer mellem ugedagene
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
        [data-testid="stVerticalBlock"] > div { padding-bottom: 0px !important; margin-bottom: 0px !important; }
        
        /* Gør dropdown-menuerne indeni kundekortene små og kompakte */
        div.stSelectbox div[data-testid="stSelectboxWithDynamicOptions"] {
            transform: scale(0.9);
            transform-origin: left center;
        }
        .stAlert { padding: 8px !important; margin-bottom: 8px !important; }
        
        /* --- DESIGN AF LODRETTE SKILLELINJER --- */
        div[data-testid="column"] {
            border-right: 1.5px solid #e6e9ef !important;
            padding-right: 15px !important;
            padding-left: 5px !important;
        }
        
        /* Fjern linjen på den sidste kolonne (Fredag) */
        div[data-testid="column"]:last-child {
            border-right: none !important;
            padding-right: 5px !important;
        }
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
    if st.session_state['bruger_koder']:
        df_koder = pd.DataFrame([{"navn": k, "kode": v} for k, v in st.session_state['bruger_koder'].items()])
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
        st.session_state['bruger_koder'] = {str(r["navn"]): str(r["kode"]) for _, r in df_koder.iterrows()}

# --- INITIALISERING ---
if 'konsulenter' not in st.session_state: st.session_state['konsulenter'] = {}
if 'kunder' not in st.session_state: st.session_state['kunder'] = []
if 'aftaler' not in st.session_state: st.session_state['aftaler'] = []
if 'arbejdsdage' not in st.session_state: st.session_state['arbejdsdage'] = {}
if 'manuelle_flytninger' not in st.session_state: st.session_state['manuelle_flytninger'] = {}
if 'bruger_koder' not in st.session_state: st.session_state['bruger_koder'] = {}
if 'logget_ind' not in st.session_state: st.session_state['logget_ind'] = False
if 'bruger_rolle' not in st.session_state: st.session_state['bruger_rolle'] = None
if 'bruger_navn' not in st.session_state: st.session_state['bruger_navn'] = None

hent_data_fra_disken()

# --- LOGIN ---
def tjek_login(brugernavn, kode):
    b_clean = brugernavn.strip().lower()
    k_clean = kode.strip()
    admin_kode = st.session_state['bruger_koder'].get("admin", "admin123")
    if b_clean == "admin" and k_clean == admin_kode:
        st.session_state['logget_ind'] = True
        st.session_state['bruger_rolle'] = "admin"
        st.session_state['bruger_navn'] = "Administrator"
        return True
    chef_kode = st.session_state['bruger_koder'].get("Casper Valdemar", "Region10")
    if (b_clean == "casper" or b_clean == "casper valdemar") and (k_clean == chef_kode or k_clean.lower() == "region10"):
        st.session_state['logget_ind'] = True
        st.session_state['bruger_rolle'] = "chef"
        st.session_state['bruger_navn'] = "Casper Valdemar"
        return True
    for k_id, k_info in st.session_state['konsulenter'].items():
        k_navn_fuld = k_info["navn"].strip()
        k_navn_fuld_lower = k_navn_fuld.lower()
        k_fornavn_lower = k_navn_fuld_lower.split(" ")[0]
        gemt_kode = st.session_state['bruger_koder'].get(k_navn_fuld, "Region10")
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
    
    valgt_loft = st.session_state.get('maks_kunder_pr_dag', 8)
    AUTOMATISK_LOFT = valgt_loft
    ABSOLUT_MAKS = valgt_loft + 2
    
    global_tæller = {}

    for uge_frem in range(0, 24):
        mål_mandag = start_mandag + timedelta(weeks=uge_frem)
        uge_nummer = mål_mandag.isocalendar()[1]
        
        uge_id = f"{mål_mandag.year}-Uge{uge_nummer:02d}"
        if uge_id not in global_tæller: global_tæller[uge_id] = {}
        
        for k_id, k_info in st.session_state['konsulenter'].items():
            if k_id not in global_tæller[uge_id]: global_tæller[uge_id][k_id] = {d: 0 for d in ALLE_DAGE_GLOBAL}
            
            kunder_i_uge = []
            for kunde in st.session_state['kunder']:
                if int(kunde["konsulent_id"]) == int(k_id):
                    frekvens = float(kunde["frekvens"])
                    k_id_int = int(kunde["id"])
                    
                    if frekvens >= 1.0:
                        kunder_i_uge.append(kunde.copy())
                    elif frekvens == 0.5:
                        if uge_nummer % 2 == (k_id_int % 2):
                            kunder_i_uge.append(kunde.copy())
                    elif frekvens == 0.25:
                        if uge_nummer % 4 == (k_id_int % 4):
                            kunder_i_uge.append(kunde.copy())

            # 1. Manuelle flytninger
            for kunde in kunder_i_uge[:]:
                unik_nøgle = f"{kunde['id']}-{uge_id}"
                if unik_nøgle in st.session_state['manuelle_flytninger']:
                    man_dag = st.session_state['manuelle_flytninger'][unik_nøgle]
                    global_tæller[uge_id][k_id][man_dag] += 1
                    st.session_state['aftaler'].append({
                        "id": unik_nøgle, "kunde_id": kunde["id"], "kundenavn": kunde["navn"],
                        "by": kunde["by"], "postnr": kunde["postnr"], "konsulent_id": k_id,
                        "uge_id": uge_id, "dag": man_dag
                    })
                    kunder_i_uge.remove(kunde)

            # 2. Automatisk placering
            for kunde in kunder_i_uge:
                placeret = False
                konsulent_arbejdsdage = st.session_state['arbejdsdage'].get(k_id, ALLE_DAGE_GLOBAL)
                if not konsulent_arbejdsdage: 
                    konsulent_arbejdsdage = ALLE_DAGE_GLOBAL
                    
                for dag in konsulent_arbejdsdage:
                    if global_tæller[uge_id][k_id][dag] < AUTOMATISK_LOFT:
                        global_tæller[uge_id][k_id][dag] += 1
                        st.session_state['aftaler'].append({
                            "id": f"{kunde['id']}-{uge_id}", "kunde_id": kunde["id"], "kundenavn": kunde["navn"],
                            "by": kunde["by"], "postnr": kunde["postnr"], "konsulent_id": k_id,
                            "uge_id": uge_id, "dag": dag
                        })
                        placeret = True
                        break
                
                if not placeret:
                    for dag in konsulent_arbejdsdage:
                        if global_tæller[uge_id][k_id][dag] < ABSOLUT_MAKS:
                            global_tæller[uge_id][k_id][dag] += 1
                            st.session_state['aftaler'].append({
                                "id": f"{kunde['id']}-{uge_id}", "kunde_id": kunde["id"], "kundenavn": kunde["navn"],
                                "by": kunde["by"], "postnr": kunde["postnr"], "konsulent_id": k_id,
                                "uge_id": uge_id, "dag": dag
                            })
                            break

# --- LOGIN SKÆRM ---
if not st.session_state['logget_ind']:
    st.title("🔐 Convenience Ruteplanlægger - Login")
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
                    
                    # --- INDSAT SKUDSIKKER FREKVENS-INDLÆSNING HER ---
                    freq = 0.25  # Standard, hvis alt fejler
                    if col_frek and not pd.isna(række[col_frek]):
                        rå_værdi = str(række[col_frek]).strip().replace(',', '.')
                        try:
                            freq = float(rå_værdi)
                        except ValueError:
                            # Ekstra sikkerhed hvis cellen driller pga. tekst-formatering
                            if "1" in rå_værdi: freq = 1.0
                            elif "0.5" in rå_værdi or "0,5" in str(række[col_frek]): freq = 0.5
                            else: freq = 0.25
                            
                    st.session_state['kunder'].append({"id": idx + 1000, "navn": str(v_navn).strip(), "by": str(v_by).strip(), "postnr": v_pnr, "frekvens": freq, "konsulent_id": kons_navn_til_id[v_kons]})
                gem_data_til_disken()
                kør_rullende_kalender_motor()
                st.sidebar.success("Database opdateret!")
                st.rerun()
        except Exception as e: st.sidebar.error(f"Fejl: {e}")

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

# --- VISNING ---
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

if not er_læse_bruger:
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Indstillinger")
    
    if 'maks_kunder_pr_dag' not in st.session_state:
        st.session_state['maks_kunder_pr_dag'] = 8
        
    nyt_loft = st.sidebar.slider(
        "Maks kunder pr. dag:", 
        min_value=5, 
        max_value=15, 
        value=st.session_state['maks_kunder_pr_dag'],
        step=1,
        help="Bestemmer hvor mange kunder motoren forsøger at lægge på en dag."
    )
    
    loft_ændret = (nyt_loft != st.session_state['maks_kunder_pr_dag'])
    if loft_ændret:
        st.session_state['maks_kunder_pr_dag'] = nyt_loft

    gemte_dage = st.session_state['arbejdsdage'].get(valgt_konsulent_id, ALLE_DAGE_GLOBAL)
    valgte_dage = []
    for d in ALLE_DAGE_GLOBAL:
        if st.sidebar.checkbox(d, value=(d in gemte_dage), key=f"d-check-{valgt_konsulent_id}-{d}"): 
            valgte_dage.append(d)
            
    if valgte_dage != gemte_dage or loft_ændret:
        st.session_state['arbejdsdage'][valgt_konsulent_id] = valgte_dage
        gem_data_til_disken()
        kør_rullende_kalender_motor()
        st.rerun()
else:
    valgte_dage = st.session_state['arbejdsdage'].get(valgt_konsulent_id, ALLE_DAGE_GLOBAL)
    if 'maks_kunder_pr_dag' not in st.session_state:
        st.session_state['maks_kunder_pr_dag'] = 8

# --- FIX: GENERERER KORREKT SAMTLIGE 24 UGER I RÆKKEFØLGE UDEN SPRING ---
idag_dato = datetime.now()
start_mandag_dato = idag_dato - timedelta(days=idag_dato.weekday())
alle_24_uger = []

for uge_frem in range(0, 24):
    mål_mandag_dato = start_mandag_dato + timedelta(weeks=uge_frem)
    uge_nummer_gen = mål_mandag_dato.isocalendar()[1]
    uge_id_gen = f"{mål_mandag_dato.year}-Uge{uge_nummer_gen:02d}"
    if uge_id_gen not in alle_24_uger:
        alle_24_uger.append(uge_id_gen)

valgt_uge = st.sidebar.selectbox("Vælg uge:", options=alle_24_uger)

st.title("🗺️ Convenience Ruteplanlægger @ Royal Unibrew")

if len(st.session_state['kunder']) == 0:
    st.warning("⚠️ Ingen data i skyen endnu. Admin skal uploade listen.")
else:
    if er_læse_bruger: st.info("ℹ️ Overordnet leder (Casper Valdemar) — Kun kigge-adgang.")
    st.subheader(f"📅 {konsulent_navn} — {valgt_uge}")
    st.markdown("---")

    aktuelle_aftaler = [a for a in st.session_state['aftaler'] if int(a["konsulent_id"]) == int(valgt_konsulent_id) and a["uge_id"] == valgt_uge]
    visnings_slots = st.columns(5)

    for i, dag in enumerate(ALLE_DAGE_GLOBAL):
        with visnings_slots[i]:
            if dag not in valgte_dage:
                st.markdown(f"### 🛑 {dag[:3]}.")
                st.caption("Lukket")
            else:
                dag_aftaler = sorted([a for a in aktuelle_aftaler if a["dag"] == dag], key=lambda x: str(x["postnr"]))
                st.markdown(f"### **{dag[:3]}.** <span style='font-size:13px; color:gray;'>({len(dag_aftaler)}/{st.session_state['maks_kunder_pr_dag']})</span>", unsafe_allow_html=True)
                st.markdown("---")
                
                if len(dag_aftaler) == 0:
                    st.markdown("<p style='margin:0px; font-size:11px; color:darkblue; font-style:italic;'>📅 Ingen planlagte besøg</p>", unsafe_allow_html=True)
                else:
                    for _idx, _aftale in enumerate(dag_aftaler):
                        zone, farve = hent_zone_og_farve(_aftale["postnr"])
                        with st.container(border=True):
                            st.markdown(f"<p style='margin:0px; font-size:13px; font-weight:bold; line-height:1.2;'>{farve} {_aftale['kundenavn']}</p>", unsafe_allow_html=True)
                            st.markdown(f"<p style='margin:2px 0px 6px 0px; font-size:11px; color:gray;'>📍 {_aftale['postnr']} {_aftale['by']}</p>", unsafe_allow_html=True)
                            if not er_læse_bruger:
                                try: nuværende_idx = valgte_dage.index(dag)
                                except: nuværende_idx = 0
                                valgt_ny_dag = st.selectbox("Flyt til:", options=valgte_dage, index=nuværende_idx, key=f"select-{_aftale['id']}-{_idx}", label_visibility="collapsed")
                                if valgt_ny_dag != dag:
                                    st.session_state['manuelle_flytninger'][_aftale["id"]] = valgt_ny_dag
                                    gem_data_til_disken()
                                    kør_rullende_kalender_motor()
                                    st.rerun()
                            else:
                                st.markdown(f"<p style='margin:0px; font-size:11px; color:darkblue; font-weight:bold;'>📅 {dag}</p>", unsafe_allow_html=True)
