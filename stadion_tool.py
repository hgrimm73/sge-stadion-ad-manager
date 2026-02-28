import streamlit as st
import pandas as pd
import math
import random
import json
import os
import matplotlib.pyplot as plt
from fpdf import FPDF
import io

# --- KONFIGURATION & BRANDING ---
STORAGE_FILE = "data_storage.json"
PASSWORD = "SGE#2026adds"
SGE_RED = "#E10019"
SGE_BLACK = "#000000"
# Robustere Logo-Quelle
LOGO_URL = "Logo.png"
# Fallback Logo falls der Link oben hakt (Wikipedia)
LOGO_URL_ALT = "https://upload.wikimedia.org/wikipedia/commons/0/04/Eintracht_Frankfurt_Logo.svg"

# --- CUSTOM CSS FÜR SGE-LOOK (FIXED CONTRAST) ---
def inject_sge_css():
    st.markdown(f"""
        <style>
        /* Grundfarben erzwingen */
        .stApp {{
            background-color: #ffffff !important;
        }}
        /* Alle Texte auf Schwarz setzen für Lesbarkeit */
        .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3 {{
            color: {SGE_BLACK} !important;
        }}
        /* Sidebar Styling */
        [data-testid="stSidebar"] {{
            background-color: {SGE_BLACK} !important;
        }}
        [data-testid="stSidebar"] * {{
            color: #ffffff !important;
        }}
        /* Input Felder Textfarbe */
        input {{
            color: {SGE_BLACK} !important;
        }}
        /* Buttons Styling */
        div.stButton > button {{
            background-color: {SGE_RED} !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 5px !important;
            padding: 0.5rem 1rem !important;
            font-weight: bold !important;
        }}
        div.stButton > button:hover {{
            background-color: #b30014 !important;
            color: #ffffff !important;
        }}
        /* Login Container */
        .login-container {{
            background-color: #f9f9f9;
            padding: 30px;
            border: 2px solid {SGE_BLACK};
            border-radius: 15px;
            text-align: center;
            margin-top: 20px;
        }}
        </style>
    """, unsafe_allow_html=True)

# --- LOGIN FUNKTION ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        inject_sge_css()
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            try:
                st.image(LOGO_URL_ALT, width=180)
            except:
                st.markdown("🦅 **Eintracht Frankfurt Ad-Manager**")
            
            st.markdown("<div class='login-container'>", unsafe_allow_html=True)
            st.subheader("SGE Ad-Inventory Login")
            pwd = st.text_input("Bitte Passwort eingeben", type="password")
            if st.button("Anmelden"):
                if pwd == PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Passwort inkorrekt.")
            st.markdown("</div>", unsafe_allow_html=True)
        return False
    return True

# --- DATEN-LOGIK ---
def save_data():
    data = {"spots": st.session_state.spots, "config": st.session_state.config}
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_data():
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                st.session_state.spots = data.get("spots", [])
                st.session_state.config = data.get("config", {})
        except:
            st.session_state.spots, st.session_state.config = [], {}
    else:
        st.session_state.spots, st.session_state.config = [], {}

    defaults = {
        "input_mode": "Prozent", "total_event_min": 240,
        "pkg_S": 2.0, "pkg_M": 5.0, "pkg_L": 10.0, "pkg_XL": 20.0,
        "dur_S": 5.0, "dur_M": 10.0, "dur_L": 20.0, "dur_XL": 40.0
    }
    for k, v in defaults.items():
        if k not in st.session_state.config: st.session_state.config[k] = v

# --- PDF GENERIERUNG ---
def create_pdf(df, fig_buffer):
    pdf = FPDF()
    pdf.add_page()
    try:
        pdf.image(LOGO_URL_ALT, x=175, y=10, w=22)
    except:
        pass

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(225, 0, 25) 
    pdf.cell(0, 10, "Eintracht Frankfurt - Ad-Inventory Report", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    
    col_width = (pdf.w - 20) / 5
    pdf.set_fill_color(0, 0, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    for h in ["Start", "Name", "Dauer", "Typ", "ID"]:
        pdf.cell(col_width, 10, h, border=1, align="C", fill=True)
    pdf.ln()
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    for _, row in df.iterrows():
        pdf.cell(col_width, 8, str(row['Start im Loop']), border=1)
        pdf.cell(col_width, 8, str(row['Name'])[:22], border=1)
        pdf.cell(col_width, 8, f"{row['Dauer']}s", border=1)
        pdf.cell(col_width, 8, str(row['Typ']), border=1)
        pdf.cell(col_width, 8, str(row['id']), border=1)
        pdf.ln()
    
    pdf.ln(10)
    pdf.image(fig_buffer, x=10, y=pdf.get_y(), w=100)
    return bytes(pdf.output())

# --- MAIN APP ---
if check_password():
    inject_sge_css()
    load_data()

    st.set_page_config(page_title="SGE Ad-Manager", layout="wide")
    
    c_head1, c_head2 = st.columns([5, 1])
    with c_head1:
        st.title("🦅 Stadion Ad-Inventory Manager")
    with c_head2:
        try: st.image(LOGO_URL_ALT, width=90)
        except: pass

    # --- SIDEBAR ---
    st.sidebar.header("⚙️ Konfiguration")
    if st.sidebar.button("💾 Alle Daten speichern"):
        save_data()
        st.sidebar.success("Gespeichert!")
    if st.sidebar.button("🚪 Abmelden"):
        st.session_state.authenticated = False
        st.rerun()

    input_mode = st.sidebar.radio("Berechnungs-Basis", ["Prozent", "Laufzeit (Minuten)"], 
                                  index=0 if st.session_state.config["input_mode"] == "Prozent" else 1)
    st.session_state.config["input_mode"] = input_mode

    total_event_min = st.sidebar.number_input("Gesamtdauer Event (Minuten)", min_value=1, value=int(st.session_state.config["total_event_min"]))
    st.session_state.config["total_event_min"] = total_event_min

    pkg_vals = {}
    for p in ["S", "M", "L", "XL"]:
        cfg_key = f"pkg_{p}" if input_mode == "Prozent" else f"dur_{p}"
        val = st.sidebar.number_input(f"Paket {p} ({'%' if input_mode == 'Prozent' else 'Min'})", min_value=0.0, value=float(st.session_state.config.get(cfg_key, 0.0)), step=0.5)
        pkg_vals[p] = val
        st.session_state.config[cfg_key] = val

    internal_pkg_pct = {p: (v/total_event_min*100 if input_mode=="Laufzeit (Minuten)" else v) for p,v in pkg_vals.items()}

    # --- CONTENT INPUT ---
    st.header("📂 Inhalts-Liste")
    with st.expander("➕ Neuen Spot hinzufügen", expanded=True):
        with st.form("add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([3, 1, 2])
            n_name = c1.text_input("Dateiname")
            n_dur = c2.number_input("Dauer (Sek.)", min_value=1, value=30)
            n_pkg = c3.selectbox("Typ", ["S", "M", "L", "XL", "Verein (Puffer)"])
            if st.form_submit_button("Hinzufügen") and n_name:
                st.session_state.spots.append({"id": random.randint(10000, 99999), "Name": n_name, "Dauer": n_dur, "Typ": n_pkg})
                save_data()
                st.rerun()

    if st.session_state.spots:
        for spot in st.session_state.spots:
            cn, cd, ct, cb = st.columns([3, 1, 2, 1])
            cn.text(spot['Name'])
            cd.text(f"{spot['Dauer']}s")
            ct.text(f"Typ: {spot['Typ']}")
            if cb.button("Löschen", key=f"del_{spot['id']}"):
                st.session_state.spots = [s for s in st.session_state.spots if s['id'] != spot['id']]
                save_data()
                st.rerun()

        st.divider()
        df_all = pd.DataFrame(st.session_state.spots)
        s_df = df_all[df_all['Typ'] != "Verein (Puffer)"].copy()
        v_df = df_all[df_all['Typ'] == "Verein (Puffer)"].copy()

        if not s_df.empty:
            s_df['Min_Loop'] = s_df.apply(lambda x: x['Dauer']/(internal_pkg_pct[x['Typ']]/100) if internal_pkg_pct[x['Typ']]>0 else 999999, axis=1)
            f_duration = max(s_df['Min_Loop'].max(), (v_df['Dauer'].sum()/(max(1, 100-sum(internal_pkg_pct.values()))/100) if not v_df.empty else 0))
            st.success(f"Optimierter Loop: **{int(f_duration//60)}m {int(f_duration%60)}s**")
            p_mode = st.radio("Modus", ["Durchmischt", "Block: Sponsoren zuerst", "Block: Sponsoren zuletzt"])

            if st.button("🚀 Playlist generieren"):
                s_pool = []
                for _, r in s_df.iterrows():
                    for _ in range(math.ceil((f_duration*(internal_pkg_pct[r['Typ']]/100))/r['Dauer'])):
                        s_pool.append({"id": str(r['id']), "Name": r['Name'], "Dauer": r['Dauer'], "Typ": r['Typ']})
                
                v_list = v_df.to_dict('records')
                v_inst, v_c, cur_s_t = [], 0, sum(s['Dauer'] for s in s_pool)
                if v_list:
                    while (cur_s_t + sum(v['Dauer'] for v in v_inst)) < f_duration or v_c < len(v_list):
                        v_inst.append(v_list[v_c % len(v_list)]); v_c += 1

                f_playlist = []
                if p_mode == "Durchmischt":
                    random.shuffle(s_pool); v_i = 0
                    for s in s_pool:
                        f_playlist.append(s)
                        if v_i < len(v_inst): f_playlist.append(v_inst[v_i]); v_i += 1
                    f_playlist.extend(v_inst[v_i:])
                elif "zuerst" in p_mode: f_playlist = s_pool + v_inst
                else: f_playlist = v_inst + s_pool

                res_df = pd.DataFrame(f_playlist); t_a, s_t = 0, []
                for d in res_df['Dauer']: s_t.append(f"{int(t_a//60):02d}:{int(t_a%60):02d}"); t_a += d
                res_df.insert(0, "Start im Loop", s_t)
                
                st.subheader("📊 Generierte Loop-Playliste")
                st.dataframe(res_df[['Start im Loop', 'Name', 'Dauer', 'Typ', 'id']], use_container_width=True)
                st.write(f"Spots: {len(res_df)} | Dauer: {res_df['Dauer'].sum()}s")

                col_e1, col_e2 = st.columns([1, 1])
                with col_e1:
                    csv = res_df.to_csv(index=False, sep=';').encode('utf-8-sig')
                    st.download_button("📥 Excel-Export", csv, "playlist.csv", "text/csv")
                    
                    p_data = res_df.groupby(['Name', 'Typ'])['Dauer'].sum().reset_index()
                    fig, ax = plt.subplots(figsize=(3, 3))
                    colors = [plt.get_cmap('tab20')(i % 20) if t != 'Verein (Puffer)' else '#d3d3d3' for i, t in enumerate(p_data['Typ'])]
                    ax.pie(p_data['Dauer'], labels=p_data['Name'], autopct='%1.1f%%', startangle=90, colors=colors, wedgeprops={'edgecolor': 'black', 'linewidth': 0.5}, textprops={'fontsize': 7})
                    ax.axis('equal')
                    st.pyplot(fig)
                    
                    buf = io.BytesIO(); fig.savefig(buf, format="png", bbox_inches='tight', dpi=150)
                    p_bytes = create_pdf(res_df[['Start im Loop', 'Name', 'Dauer', 'Typ', 'id']], buf)
                    st.download_button("📄 PDF-Report", p_bytes, "SGE_Report.pdf", "application/pdf")
                    plt.close(fig)


