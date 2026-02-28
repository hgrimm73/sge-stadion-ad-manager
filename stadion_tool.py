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
LOGO_PATH = "logo.png"  # Datei muss im Hauptverzeichnis auf GitHub liegen

# --- LOGO-LOGIK ---
def show_logo(width=200):
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=width)
    else:
        st.markdown(f"**[Logo: {LOGO_PATH} nicht gefunden]**")

# --- LOGIN FUNKTION ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        # Zentrierter Bereich für den Login
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            show_logo(width=250)
            # Titel bündig mit dem Input-Feld
            st.markdown("<h2 style='text-align: left; margin-bottom: -10px;'>SGE Ad-Manager</h2>", unsafe_allow_html=True)
            pwd = st.text_input("Passwort eingeben", type="password")
            if st.button("Anmelden"):
                if pwd == PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Passwort falsch!")
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
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "SGE Stadion Ad-Manager Report", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "B", 10)
    col_width = (pdf.w - 20) / 5
    headers = ["Start", "Name", "Dauer", "Typ", "ID"]
    for header in headers:
        pdf.cell(col_width, 10, header, border=1, align="C")
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 9)
    for _, row in df.iterrows():
        pdf.cell(col_width, 8, str(row['Start im Loop']), border=1)
        name_text = str(row['Name'])[:22] + ".." if len(str(row['Name'])) > 22 else str(row['Name'])
        pdf.cell(col_width, 8, name_text, border=1)
        pdf.cell(col_width, 8, f"{row['Dauer']}s", border=1)
        pdf.cell(col_width, 8, str(row['Typ']), border=1)
        pdf.cell(col_width, 8, str(row['id']), border=1)
        pdf.ln()
    
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Zeitverteilung im Loop", ln=True)
    
    img_path = "temp_plot.png"
    with open(img_path, "wb") as f:
        f.write(fig_buffer.getvalue())
    pdf.image(img_path, x=10, y=pdf.get_y(), w=100)
    
    return bytes(pdf.output())

# --- HAUPTPROGRAMM ---
if check_password():
    if 'spots' not in st.session_state:
        load_data()

    # Zwinge das helle Design via CSS (Minimal-Variante)
    st.markdown("""
        <style>
        .stApp { background-color: white; color: black; }
        label { color: black !important; }
        .stMarkdown p { color: black !important; }
        </style>
    """, unsafe_allow_html=True)

    st.set_page_config(page_title="SGE Stadion Ad-Manager", layout="wide")
    
    # Header mit Logo und Titel
    col_l, col_t = st.columns([1, 6])
    with col_l:
        show_logo(width=80)
    with col_t:
        st.title("SGE Stadion Ad-Manager")

    # --- SIDEBAR ---
    st.sidebar.header("1. Konfiguration")
    if st.sidebar.button("💾 Alle Daten speichern"):
        save_data()
        st.sidebar.success("Gespeichert!")
    
    if st.sidebar.button("🚪 Abmelden"):
        st.session_state.authenticated = False
        st.rerun()

    input_mode = st.sidebar.radio("Berechnungs-Basis", ["Prozent", "Laufzeit (Minuten)"], 
                                  index=0 if st.session_state.config["input_mode"] == "Prozent" else 1)
    st.session_state.config["input_mode"] = input_mode

    total_event_min = st.sidebar.number_input("Gesamtdauer Event (Minuten)", min_value=1, 
                                              value=int(st.session_state.config["total_event_min"]))
    st.session_state.config["total_event_min"] = total_event_min

    st.sidebar.subheader("Paket-Werte")
    pkg_vals = {}
    for p in ["S", "M", "L", "XL"]:
        cfg_key = f"pkg_{p}" if input_mode == "Prozent" else f"dur_{p}"
        val = st.sidebar.number_input(f"Paket {p}", min_value=0.0, 
                                      value=float(st.session_state.config.get(cfg_key, 0.0)), step=0.5)
        pkg_vals[p] = val
        st.session_state.config[cfg_key] = val

    internal_pkg_pct = {p: (v / total_event_min * 100 if input_mode == "Laufzeit (Minuten)" else v) for p, v in pkg_vals.items()}

    # --- CONTENT ---
    st.header("2. Inhalts-Liste")
    with st.expander("➕ Neuen Spot hinzufügen", expanded=True):
        with st.form("add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([3, 1, 2])
            new_name = c1.text_input("Dateiname")
            new_dur = c2.number_input("Dauer (Sek.)", min_value=1, value=30)
            new_pkg = c3.selectbox("Typ", ["S", "M", "L", "XL", "Verein (Puffer)"])
            if st.form_submit_button("Hinzufügen"):
                if new_name:
                    st.session_state.spots.append({"id": random.randint(10000, 99999), "Name": new_name, "Dauer": new_dur, "Typ": new_pkg})
                    save_data()
                    st.rerun()

    if st.session_state.spots:
        for spot in st.session_state.spots:
            col_n, col_d, col_t, col_btn = st.columns([3, 1, 2, 1])
            col_n.text(spot['Name'])
            col_d.text(f"{spot['Dauer']}s")
            col_t.text(f"Typ: {spot['Typ']}")
            if col_btn.button("Löschen", key=f"del_{spot['id']}"):
                st.session_state.spots = [s for s in st.session_state.spots if s['id'] != spot['id']]
                save_data()
                st.rerun()

    # --- GENERIERUNG ---
    if st.session_state.spots:
        st.divider()
        df_all = pd.DataFrame(st.session_state.spots)
        s_df = df_all[df_all['Typ'] != "Verein (Puffer)"].copy()
        v_df = df_all[df_all['Typ'] == "Verein (Puffer)"].copy()

        if not s_df.empty:
            s_df['Min_Loop'] = s_df.apply(lambda x: x['Dauer'] / (internal_pkg_pct[x['Typ']] / 100) if internal_pkg_pct[x['Typ']] > 0 else 999999, axis=1)
            base_loop = s_df['Min_Loop'].max()
            min_v_time = v_df['Dauer'].sum() if not v_df.empty else 0
            s_pct_sum = sum([internal_pkg_pct[t] for t in s_df['Typ']])
            v_pct_avail = max(1, 100 - s_pct_sum)
            loop_for_v = min_v_time / (v_pct_avail / 100) if v_pct_avail > 0 else min_v_time
            final_loop_duration = max(base_loop, loop_for_v)

            st.success(f"Optimierte Loop-Dauer: **{int(final_loop_duration//60)}m {int(final_loop_duration%60)}s**")
            play_mode = st.radio("Ausspielungs-Modus", ["Durchmischt", "Block: Sponsoren zuerst", "Block: Sponsoren zuletzt"])

            if st.button("🚀 Playlist generieren"):
                s_pool = []
                for _, row in s_df.iterrows():
                    wdh = math.ceil((final_loop_duration * (internal_pkg_pct[row['Typ']]/100)) / row['Dauer'])
                    for _ in range(wdh): s_pool.append({"id": str(row['id']), "Name": row['Name'], "Dauer": row['Dauer'], "Typ": row['Typ']})
                
                v_list = v_df.to_dict('records')
                v_instances, v_counter, cur_s_time = [], 0, sum(s['Dauer'] for s in s_pool)
                
                if v_list:
                    while (cur_s_time + sum(v['Dauer'] for v in v_instances)) < final_loop_duration or v_counter < len(v_list):
                        v_instances.append(v_list[v_counter % len(v_list)])
                        v_counter += 1

                final_playlist = []
                if play_mode == "Durchmischt":
                    random.shuffle(s_pool)
                    v_idx = 0
                    for s in s_pool:
                        final_playlist.append(s)
                        if v_idx < len(v_instances):
                            v_spot = v_instances[v_idx].copy()
                            v_spot['id'] = str(v_spot['id'])
                            final_playlist.append(v_spot)
                            v_idx += 1
                    final_playlist.extend(v_instances[v_idx:])
                elif "zuerst" in play_mode:
                    s_pool.sort(key=lambda x: {"XL": 1, "L": 2, "M": 3, "S": 4}.get(x['Typ'], 5))
                    final_playlist = s_pool + v_instances
                else:
                    s_pool.sort(key=lambda x: {"XL": 1, "L": 2, "M": 3, "S": 4}.get(x['Typ'], 5))
                    final_playlist = v_instances + s_pool

                res_df = pd.DataFrame(final_playlist)
                t_acc, s_t = 0, []
                for d in res_df['Dauer']:
                    s_t.append(f"{int(t_acc//60):02d}:{int(t_acc%60):02d}"); t_acc += d
                res_df.insert(0, "Start im Loop", s_t)
                
                st.subheader("4. Generierte Loop-Playliste")
                st.dataframe(res_df[['Start im Loop', 'Name', 'Dauer', 'Typ', 'id']], use_container_width=True,
                             column_config={"Dauer": st.column_config.Column(width="small"), "id": st.column_config.Column(width="small")})
                
                st.write(f"**Spots:** {len(res_df)} | **Dauer:** {res_df['Dauer'].sum()}s")

                col_e1, col_e2 = st.columns([1, 1])
                with col_e1:
                    csv = res_df.to_csv(index=False, sep=';').encode('utf-8-sig')
                    st.download_button("📥 Excel-Export", csv, "playlist.csv", "text/csv")
                    p_data = res_df.groupby(['Name', 'Typ'])['Dauer'].sum().reset_index()
                    fig, ax = plt.subplots(figsize=(3, 3))
                    colors = [plt.get_cmap('tab20')(i % 20) if t != 'Verein (Puffer)' else '#d3d3d3' for i, t in enumerate(p_data['Typ'])]
                    ax.pie(p_data['Dauer'], labels=p_data['Name'], autopct='%1.1f%%', startangle=90, colors=colors, wedgeprops={'edgecolor': 'black', 'linewidth': 0.5}, textprops={'fontsize': 7})
                    ax.axis('equal'); st.pyplot(fig)
                    buf = io.BytesIO(); fig.savefig(buf, format="png", bbox_inches='tight', dpi=150)
                    p_bytes = create_pdf(res_df[['Start im Loop', 'Name', 'Dauer', 'Typ', 'id']], buf)
                    st.download_button("📄 PDF-Report", p_bytes, "SGE_Report.pdf", "application/pdf")
                    plt.close(fig)
