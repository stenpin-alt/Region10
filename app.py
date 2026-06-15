import streamlit as st
import pandas as pd
from datetime import datetime
import os
import re

st.set_page_config(
    page_title="Convenience Ruteplanlægger Pro", 
    layout="wide",
    page_icon="logo.png"
)

# Standard for billedbredde
st.sidebar.image("logo.png", use_container_width=True) 

# CSS-optimering med lodrette skillelinjer mellem ugedagene
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
        [data-testid="stVerticalBlock"] > div { padding-bottom: 0px !important; margin-bottom: 0px !important; }
        
        div.stSelectbox div[data-testid="stSelectboxWithDynamicOptions"] {
            transform: scale(0.9);
            transform-origin: left center;
        }
        .stAlert { padding: 8px !important; margin-bottom: 8px !important; }
        
        div[data-testid="column"] {
            border-right: 1.5px solid #e6e9ef !important;
            padding-right: 15px !important;
            padding-left: 5px !important;
        }
        
        div[data-testid="column"]:last-child {
            border-right: none !important;
            padding-right: 5px !important;
        }
    </style>
""", unsafe_allow_html=True)

# Globale variabler
ALLE_DAGE_GLOBAL = ["Mandag", "Tirsdag", "Onsdag", "Torsdag", "Fredag"]

# --- PERMANENT DATALAGRING ---
FIL_KUNDER = "/tmp/gemt_kunder.csv"
FIL_KONSULENTER = "/tmp/gemt_konsulenter.csv"
FIL_FLYTNINGER = "/tmp/gemt_flytninger.csv"
FIL_KODER = "/tmp/gemt_koder.csv"

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
    if os.path.exists(FIL_KODER) and not st.session_state['bruger_koder']:
        df_koder = pd.read_csv(FIL_KODER)
        st.session_state['bruger_koder'] = {str(r["navn"]): str(r["kode"]) for _, r in df_koder.iterrows()}

# --- INITIALISERING ---
if 'konsulenter' not in st.session_state: st.session_state['konsulenter'] = {}
if 'kunder' not in st.session_state: st.session_state['kunder'] = []
if 'manuelle_flytninger' not in st.session_state: st.session_state['manuelle_flytninger'] = {}
if 'bruger_koder' not in st.session_state: st.session_state['bruger_koder'] = {}
if 'arbejdsdage' not in st.session_state: st.session_state['arbejdsdage'] = {}
if 'logget_ind' not in st.session_state: st.session_state['logget_ind'] = False
if 'bruger_rolle' not in st.session_state: st.session_state['bruger_rolle'] = None
if 'bruger_navn' not in st.session_state: st.session_state['bruger_navn'] = None
if 'maks_kunder_pr_dag' not in st.session_state: st.session_state['maks_kunder_pr_dag'] = 8
if 'aktivt_konsulent_id' not in st.session_state: st.session_state['aktivt_konsulent_id'] = None

hent_data_fra_disken()

# --- LOGIN ---
def tjek_login(brugernavn, kode):
    b_clean = brugernavn.strip().lower()
    k_clean = kode.strip()
    admin_code = st.session_state['bruger_koder'].get("admin", "admin123")
    if b_clean == "admin" and k_clean == admin_code:
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
            st.session_state['aktivt_konsulent_id'] = k_id
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

# --- AVANCERET RUTEMOTOR BASERET PÅ MATEMATISK UGE-FREKVENS ---
@st.cache_data
def beregn_ruter_cached(kunder, konsulenter, arbejdsdage, manuelle_flytninger, valgt_loft):
    beregnede_aftaler = []
    aktuelt_aar = 2026
    
    for k_id, k_info in konsulenter.items():
        konsulent_arbejdsdage = arbejdsdage.get(str(k_id), ALLE_DAGE_GLOBAL)
        if not konsulent_arbejdsdage:
            konsulent_arbejdsdage = ALLE_DAGE_GLOBAL
            
        konsulent_kunder = [k for k in kunder if int(k["konsulent_id"]) == int(k_id)]
        try:
            konsulent_kunder.sort(key=lambda x: int(''.join(filter(str.isdigit, str(x["postnr"])))))
        except:
            pass
            
        if not konsulent_kunder:
            continue
            
        for uge_nummer in range(1, 53):
            uge_id = f"{aktuelt_aar}-Uge{uge_nummer:02d}"
            dag_taeller = {d: 0 for d in ALLE_DAGE_GLOBAL}
            ugens_planlagte_kunde_ids = set()
            
            # --- 1. MANUELLE FLYTNINGER ---
            for kunde in konsulent_kunder:
                try: besøg_pr_uge = int(kunde.get("besoeg_pr_uge", 1))
                except: besøg_pr_uge = 1
                
                for b_idx in range(besøg_pr_uge):
                    unik_noegle = f"{kunde['id']}-{uge_id}-b{b_idx}"
                    if unik_noegle in manuelle_flytninger:
                        man_dag = manuelle_flytninger[unik_noegle]
                        if man_dag in konsulent_arbejdsdage:
                            dag_taeller[man_dag] += 1
                            beregnede_aftaler.append({
                                "id": unik_noegle, "kunde_id": kunde["id"], "kundenavn": kunde["navn"],
                                "by": kunde["by"], "postnr": kunde["postnr"], "konsulent_id": k_id,
                                "uge_id": uge_id, "dag": man_dag
                            })
                            ugens_planlagte_kunde_ids.add(f"{kunde['id']}-b{b_idx}")

            # --- 2. AUTOMATISK MATEMATISK FORDELING PÅ FREKVENS ---
            for kunde in konsulent_kunder:
                try: frekvens = float(kunde["frekvens"])
                except: frekvens = 1.0
                
                try: besøg_pr_uge = int(kunde.get("besoeg_pr_uge", 1))
                except: besøg_pr_uge = 1
                
                skal_besoeges_i_denne_uge = False
                try: kunde_offset = int(kunde["id"])
                except: kunde_offset = 0
                
                if frekvens >= 1.0:
                    skal_besoeges_i_denne_uge = True
                elif frekvens == 0.50:
                    if uge_nummer % 2 == (kunde_offset % 2): skal_besoeges_i_denne_uge = True
                elif frekvens == 0.25:
                    if uge_nummer % 4 == (kunde_offset % 4): skal_besoeges_i_denne_uge = True
                elif frekvens in [0.12, 0.15, 0.30]:
                    if uge_nummer % 6 == (kunde_offset % 6): skal_besoeges_i_denne_uge = True
                else:
                    if uge_nummer % 2 == 0: skal_besoeges_i_denne_uge = True

                if skal_besoeges_i_denne_uge:
                    for b_idx in range(besøg_pr_uge):
                        slot_id = f"{kunde['id']}-b{b_idx}"
                        
                        if slot_id in ugens_planlagte_kunde_ids:
                            continue
                        
                        ledige_dage = sorted(konsulent_arbejdsdage, key=lambda d: dag_taeller[d])
                        
                        alle_planlagte_dage_for_kunde = [a["dag"] for a in beregnede_aftaler if a["kunde_id"] == kunde["id"] and a["uge_id"] == uge_id]
                        if len(alle_planlagte_dage_for_kunde) > 0 and len(ledige_dage) > len(alle_planlagte_dage_for_kunde):
                            ledige_dage = sorted(ledige_dage, key=lambda d: (d in alle_planlagte_dage_for_kunde, dag_taeller[d]))
                        
                        placeret = False
                        for dag in ledige_dage:
                            if dag_taeller[dag] < valgt_loft:
                                dag_taeller[dag] += 1
                                beregnede_aftaler.append({
                                    "id": f"{kunde['id']}-{uge_id}-b{b_idx}", "kunde_id": kunde["id"], "kundenavn": kunde["navn"],
                                    "by": kunde["by"], "postnr": kunde["postnr"], "konsulent_id": k_id,
                                    "uge_id": uge_id, "dag": dag
                                })
                                ugens_planlagte_kunde_ids.add(slot_id)
                                placeret = True
                                break
                        
                        if not placeret:
                            beregnede_aftaler.append({
                                "id": f"{kunde['id']}-{uge_id}-b{b_idx}", "kunde_id": kunde["id"], "kundenavn": kunde["navn"],
                                "by": kunde["by"], "postnr": kunde["postnr"], "konsulent_id": k_id,
                                "uge_id": uge_id, "dag": "Ikke plads"
                            })
                            ugens_planlagte_kunde_ids.add(slot_id)
                                    
    return beregnede_aftaler

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
    st.session_state['logget_ind'] = False
    st.session_state['konsulenter'] = {}
    st.session_state['kunder'] = []
    st.session_state['aktivt_konsulent_id'] = None
    st.rerun()

# --- EXCEL UPLOAD ---
if st.session_state['bruger_rolle'] == "admin":
    st.sidebar.header("📂 Admin: Excel Upload")
    uploaded_file = st.sidebar.file_uploader("Upload kundeliste", type=["xlsx", "xls"])
    if uploaded_file is not None:
        try:
            # Læs råt uden datatypetvingning først for maksimal fleksibilitet
            df_indlæst = pd.read_excel(uploaded_file, skiprows=2)
            df_indlæst.columns = df_indlæst.columns.astype(str).str.strip()
            
            # Smart kolonne-detektering uanset stavefejl eller ekstra mellemrum
            col_konsulent = None
            col_navn = None
            col_by = None
            col_frek = None
            col_besoeg_pr_uge = None
            col_postnr = None
            
            for c in df_indlæst.columns:
                c_low = c.lower()
                if "konsulent" in c_low: col_konsulent = c
                elif "navn" in c_low: col_navn = c
                elif "by" in c_low and "udby" not in c_low: col_by = c
                elif "frek" in c_low or "besøgs" in c_low: col_frek = c
                elif "besøg pr" in c_low or "pr uge" in c_low: col_besoeg_pr_uge = c
                elif "post" in c_low or "pnr" in c_low: col_postnr = c
            
            # Fallbacks hvis overskrifterne mangler helt specifikke ord
            if not col_konsulent: col_konsulent = df_indlæst.columns[0]
            if not col_navn and len(df_indlæst.columns) > 1: col_navn = df_indlæst.columns[1]
            if not col_by and len(df_indlæst.columns) > 2: col_by = df_indlæst.columns[2]
            
            if col_navn and col_by and col_postnr:
                unikke_kons_navne = sorted(df_indlæst[col_konsulent].dropna().unique())
                
                st.cache_data.clear()
                st.session_state['konsulenter'] = {i+1: {"navn": str(n).strip()} for i, n in enumerate(unikke_kons_navne)}
                kons_navn_til_id = {str(n).strip(): i+1 for i, n in enumerate(unikke_kons_navne)}
                st.session_state['kunder'] = []
                
                for idx, række in df_indlæst.iterrows():
                    v_navn = række[col_navn]
                    v_by = række[col_by]
                    v_pnr = række[col_postnr]
                    v_kons = str(række[col_konsulent]).strip()
                    
                    if pd.isna(v_navn) or pd.isna(v_by) or pd.isna(v_pnr):
                        continue
                        
                    if v_kons not in kons_navn_til_id: 
                        continue
                    
                    # Dynamisk Parsing af Frekvens (Håndterer både tal, tekst og formler fra Excel)
                    freq = 1.0  
                    if col_frek and not pd.isna(række[col_frek]):
                        rå_værdi = str(række[col_frek]).strip().lower().replace(',', '.')
                        
                        try:
                            freq = float(rå_værdi)
                        except ValueError:
                            # Tekstbaserede regler hvis værdien er formateret som tekst
                            if "0.5" in rå_værdi or "1/2" in rå_værdi or "2" in rå_værdi:
                                freq = 0.5
                            elif "0.25" in rå_værdi or "1/4" in rå_værdi or "4" in rå_værdi:
                                freq = 0.25
                            elif "0.12" in rå_værdi or "1/8" in rå_værdi:
                                freq = 0.12
                            elif "0.15" in rå_værdi:
                                freq = 0.15
                            elif "0.30" in rå_værdi:
                                freq = 0.30
                            else:
                                freq = 1.0
                    
                    b_pr_uge = 1
                    if col_besoeg_pr_uge and not pd.isna(række[col_besoeg_pr_uge]):
                        try: b_pr_uge = int(række[col_besoeg_pr_uge])
                        except: b_pr_uge = 1
                                    
                    st.session_state['kunder'].append({
                        "id": idx + 1000, 
                        "navn": str(v_navn).strip(), 
                        "by": str(v_by).strip(), 
                        "postnr": v_pnr, 
                        "frekvens": freq, 
                        "besoeg_pr_uge": b_pr_uge,
                        "konsulent_id": kons_navn_til_id[v_kons]
                    })
                
                if st.session_state['konsulenter']:
                    st.session_state['aktivt_konsulent_id'] = list(st.session_state['konsulenter'].keys())[0]

                gem_data_til_disken()
                st.sidebar.success(f"Database opdateret! Indlæste {len(st.session_state['kunder'])} kunder.")
                st.rerun()
        except Exception as e: 
            st.sidebar.error(f"Fejl under indlæsning: {e}")

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

# --- HENT DATA FRA CACHE ---
aftaler_liste = beregn_ruter_cached(
    st.session_state['kunder'], 
    st.session_state['konsulenter'], 
    st.session_state['arbejdsdage'], 
    st.session_state['manuelle_flytninger'],
    st.session_state['maks_kunder_pr_dag']
)

def opdater_valgt_konsulent():
    st.session_state['aktivt_konsulent_id'] = st.session_state['sb_konsulent_valg']

er_læse_bruger = False
if st.session_state['bruger_rolle'] == "admin" or st.session_state['bruger_rolle'] == "chef":
    if st.session_state['bruger_rolle'] == "chef": er_læse_bruger = True
    if st.session_state['konsulenter']:
        konsulent_keys = list(st.session_state['konsulenter'].keys())
        if st.session_state['aktivt_konsulent_id'] not in konsulent_keys:
            st.session_state['aktivt_konsulent_id'] = konsulent_keys[0]
            
        valgt_konsulent_id = st.sidebar.selectbox(
            "Vis rute for:", 
            options=konsulent_keys, 
            index=konsulent_keys.index(st.session_state['aktivt_konsulent_id']),
            format_func=lambda x: st.session_state['konsulenter'][x]["navn"],
            key="sb_konsulent_valg",
            on_change=opdater_valgt_konsulent
        )
        konsulent_navn = st.session_state['konsulenter'][st.session_state['aktivt_konsulent_id']]["navn"]
    else:
        st.session_state['aktivt_konsulent_id'] = 1
        konsulent_navn = "Ingen data"
else:
    konsulent_navn = st.session_state['bruger_navn']

valgt_konsulent_id = st.session_state['aktivt_konsulent_id']

if not er_læse_bruger and st.session_state['konsulenter']:
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Indstillinger")
    
    nyt_loft = st.sidebar.slider("Maks kunder pr. dag:", min_value=3, max_value=15, value=st.session_state['maks_kunder_pr_dag'], step=1)
    if nyt_loft != st.session_state['maks_kunder_pr_dag']:
        st.session_state['maks_kunder_pr_dag'] = nyt_loft
        st.cache_data.clear()
        st.rerun()

    str_k_id = str(valgt_konsulent_id)
    gemte_dage = st.session_state['arbejdsdage'].get(str_k_id, ALLE_DAGE_GLOBAL)
    valgte_dage = []
    for d in ALLE_DAGE_GLOBAL:
        if st.sidebar.checkbox(d, value=(d in gemte_dage), key=f"d-check-{valgt_konsulent_id}-{d}"): 
            valgte_dage.append(d)
            
    if valgte_dage != gemte_dage:
        st.session_state['arbejdsdage'][str_k_id] = valgte_dage
        gem_data_til_disken()
        st.cache_data.clear()
        st.rerun()
else:
    valgte_dage = st.session_state['arbejdsdage'].get(str(valgt_konsulent_id), ALLE_DAGE_GLOBAL)

# --- FAST GENERERING AF UGER ---
alle_52_uger = [f"2026-Uge{u:02d}" for u in range(1, 53)]

if 'valgt_uge_state' not in st.session_state:
    reelt_ugenummer = datetime.now().isocalendar()[1]
    st.session_state['valgt_uge_state'] = f"2026-Uge{reelt_ugenummer:02d}"

valgt_uge = st.sidebar.selectbox(
    "Vælg uge:", 
    options=alle_52_uger, 
    index=alle_52_uger.index(st.session_state['valgt_uge_state']) if st.session_state['valgt_uge_state'] in alle_52_uger else 23,
    key="uge_dropdown_valg"
)
st.session_state['valgt_uge_state'] = valgt_uge

st.title("🗺️ Convenience Ruteplanlægger @ Royal Unibrew")

if len(st.session_state['kunder']) == 0:
    st.warning("⚠️ Ingen data i skyen endnu. Admin skal uploade en Excel-liste.")
else:
    if er_læse_bruger: st.info("ℹ️ Overordnet leder (Casper Valdemar) — Kun kigge-adgang.")
    st.subheader(f"📅 {konsulent_navn} — {st.session_state['valgt_uge_state']}")
    st.markdown("---")

    aktuelle_aftaler = [a for a in aftaler_liste if int(a["konsulent_id"]) == int(valgt_konsulent_id) and str(a["uge_id"]) == str(st.session_state['valgt_uge_state'])]
    
    visnings_slots = st.columns(5)
    for i, dag in enumerate(ALLE_DAGE_GLOBAL):
        with visnings_slots[i]:
            if dag not in valgte_dage:
                st.markdown(f"### 🛑 {grid[:3]}.")
                st.caption("Lukket")
            else:
                dag_aftaler = sorted([a for a in aktuelle_aftaler if a["dag"] == dag], key=lambda x: str(x["postnr"]))
                st.markdown(f"### **{dag[:3]}.** <span style='font-size:13px; color:gray;'>({len(dag_aftaler)})</span>", unsafe_allow_html=True)
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
                                except ValueError: nuværende_idx = 0
                                
                                s_key = f"sel-{_aftale['id']}-{_idx}"
                                valgt_ny_dag = st.selectbox("Flyt:", options=valgte_dage, index=nuværende_idx, key=s_key, label_visibility="collapsed")
                                
                                if valgt_ny_dag != dag:
                                    st.session_state['manuelle_flytninger'][_aftale["id"]] = valgt_ny_dag
                                    gem_data_til_disken()
                                    st.cache_data.clear()
                                    st.rerun()

    ikke_plads_aftaler = [a for a in aktuelle_aftaler if a["dag"] == "Ikke plads"]
    if ikke_plads_aftaler:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.warning(f"⚠️ **Overskydende butikker i {st.session_state['valgt_uge_state']} (Bliver automatisk skubbet tovejs for at holde maks-loftet på {st.session_state['maks_kunder_pr_dag']}):**")
        
        il_cols = st.columns(4)
        for idx, _aftale in enumerate(ikke_plads_aftaler):
            with il_cols[idx % 4]:
                zone, farve = hent_zone_og_farve(_aftale["postnr"])
                with st.container(border=True):
                    st.markdown(f"<p style='margin:0px; font-size:13px; font-weight:bold; line-height:1.2;'>{farve} {_aftale['kundenavn']}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin:2px 0px 6px 0px; font-size:11px; color:gray;'>📍 {_aftale['postnr']} {_aftale['by']}</p>", unsafe_allow_html=True)
                    
                    if not er_læse_bruger:
                        s_key = f"sel-overloeb-{_aftale['id']}-{idx}"
                        valgt_tvunget_dag = st.selectbox("Placer manuelt på dag:", options=["Vælg dag..."] + valgte_dage, index=0, key=s_key, label_visibility="collapsed")
                        if valgt_tvunget_dag != "Vælg dag...":
                            st.session_state['manuelle_flytninger'][_aftale["id"]] = valgt_tvunget_dag
                            gem_data_til_disken()
                            st.cache_data.clear()
                            st.rerun()

    # --- DIAGNOSTISK TRACKER (Kun synlig for Admin) ---
    if st.session_state['bruger_rolle'] == "admin" and st.session_state['kunder']:
        st.markdown("---")
        st.subheader("🔍 Diagnostisk Værktøj: Indlæste Frekvenser fra Databasen")
        df_diagnose = pd.DataFrame(st.session_state['kunder'])
        st.dataframe(df_diagnose[["navn", "by", "postnr", "frekvens", "besoeg_pr_uge"]].head(25), use_container_width=True)

# --- NULSTIL KNAP ---
if st.session_state['bruger_rolle'] == "admin":
    st.sidebar.markdown("<br><br><br><hr>", unsafe_allow_html=True)
    if st.sidebar.button("⚠️ NULSTIL AL DATA PÅ SERVEREN"):
        for f in [FIL_KUNDER, FIL_KONSULENTER, FIL_FLYTNINGER]:
            if os.path.exists(f): os.remove(f)
        st.cache_data.clear()
        st.session_state['kunder'] = []
        st.session_state['konsulenter'] = {}
        st.session_state['manuelle_flytninger'] = {}
        st.sidebar.error("Server-filer slettet. Upload din Excel-fil nu!")
        st.rerun()
