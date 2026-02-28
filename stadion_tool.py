import streamlit as st
import pandas as pd
import math
import random
import json
import os
import matplotlib.pyplot as plt
from fpdf import FPDF
import io
import requests

# --- KONFIGURATION & BRANDING ---
STORAGE_FILE = "data_storage.json"
PASSWORD = "SGE#2026adds"
SGE_RED = "#E10019"
SGE_BLACK = "#000000"
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Eintracht_Frankfurt_Logo.svg/1024px-Eintracht_Frankfurt_Logo.svg.png"

# --- CUSTOM CSS FÜR SGE-LOOK ---
def inject_sge_css():
    st.markdown(f"""
        <style>
        /* Hintergrund & Hauptfarben */
        .stApp {{
            background-color: #ffffff;
        }}
        /* Sidebar Styling */
        [data-testid="stSidebar"] {{
            background-color: {SGE_BLACK};
            color: white;
        }}
        [data-testid="stSidebar"] * {{
            color: white !important;
        }}
        /* Buttons */
        div.stButton > button:first-child {{
            background-color: {SGE_RED};
            color: white;
            border: none;
            border-radius: 5px;
            font-weight: bold;
        }}
        div.stButton > button:hover {{
            background-color: #b30014;
            color: white;
        }}
        /* Überschriften */
        h1, h2, h3 {{
            color: {SGE_BLACK};
            border-bottom: 2px solid {SGE_RED};
            padding-bottom: 10px;
        }}
        /* Login Box */
        .login-box {{
            padding: 20px;
            border: 2px solid {SGE_BLACK};
            border-radius: 10px;
            text-align: center;
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
            st.image(LOGO_URL, width=200)
            st.markdown("<div class='login-box'>", unsafe_allow_html=True)
            st.title("SGE Ad-Inventory Login")
            pwd = st.text_input("Passwort", type="password")
            if st.button("Anmelden"):
                if pwd == PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Zugriff verweigert. Falsches Passwort.")
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

# --- PDF GENERIERUNG MIT LOGO ---
def create_pdf(df, fig_buffer):
    pdf = FPDF()
    pdf.add_page()
    
    # Logo oben rechts
    try:
        pdf.image(LOGO_URL, x=170, y=8, w=25)
    except:
        pass # Falls URL nicht erreichbar

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(225, 0, 25) # SGE Rot
    pdf.cell(0, 10, "Eintracht Frankfurt - Ad-Inventory Report", ln=True)
    
    pdf.set_text_color(0, 0, 0) # Zurück zu Schwarz
    pdf.set_font("Helvetica", "B", 10)
    pdf.ln(10)
    
    col_width = (pdf.w - 20) / 5
    headers = ["Start", "Name", "Dauer", "Typ", "ID"]
    pdf.set_fill_color(0, 0, 0)
    pdf.set_text_color(255, 255, 255)
    for header in headers:
        pdf.cell(col_width, 10, header, border=1, align="C", fill=True)
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
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Zeitverteilung im Loop", ln=True)
    
    img_path = "temp_plot.png"
    with open(img_path, "wb") as f:
        f.write(fig_buffer.getvalue())
    pdf.image(img_path, x=10, y=pdf.get_y(), w=100)
    
    return bytes(pdf.output())

# --- HAUPTPROGRAMM ---
if check_password():
    inject_sge_css()
    if 'spots' not in st.session_state:
        load_data()

    st.set_page_config(page_title="SGE Ad-Manager", layout="wide", page_icon=LOGO_URL)
    
    col_head1, col_head2 = st.columns([4, 1])
    with col_head1:
        st.title("🦅 Stadion Ad-Inventory Manager")
    with col_head2:
        st.image(LOGO_URL, width=100)

    # ... Rest des Codes bleibt logisch identisch zum vorherigen Stand ...
    # (Sidebar, Content-Eingabe, Generierungs-Logik)
    
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

    total_event_min = st.sidebar.number_input("Gesamtdauer Event (Minuten)", min_value=1, 
                                              value=int(st.session_state.config["total_event_min"]))
    st.session_state.config["total_event_min"] = total_event_min

    st.sidebar.subheader("Paket-Werte")
    pkg_vals = {}
    for p in ["S", "M", "L", "XL"]:
        cfg_key = f"pkg_{p}" if input_mode == "Prozent" else f"dur_{p}"
        val = st.sidebar.number_input(f"Paket {p} ({'%' if input_mode == 'Prozent' else 'Min'})", 
                                      min_value=0.0, value=float(st.session_state.config.get(cfg_key, 0.0)), step=0.5)
        pkg_vals[p] = val
        st.session_state.config[cfg_key] = val

    internal_pkg_pct = {}
    if input_mode == "Laufzeit (Minuten)":
        for p, v in pkg_vals.items():
            internal_pkg_pct[p] = (v / total_event_min) * 100 if total_event_min > 0 else 0
    else:
        internal_pkg_pct = pkg_vals

    st.header("📂 Inhalts-Liste")
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

    if st.session_state.spots:
        st.divider()
        df_all = pd.DataFrame(st.session_state.spots)
        sponsoren_df = df_all[df_all['Typ'] != "Verein (Puffer)"].copy()
        vereins_df = df_all[df_all['Typ'] == "Verein (Puffer)"].copy()

        if not sponsoren_df.empty:
            sponsoren_df['Min_Loop_Req'] = sponsoren_df.apply(lambda x: x['Dauer'] / (internal_pkg_pct[x['Typ']] / 100) if internal_pkg_pct[x['Typ']] > 0 else 999999, axis=1)
            base_loop = sponsoren_df['Min_Loop_Req'].max()
            min_v_time = vereins_df['Dauer'].sum() if not vereins_df.empty else 0
            s_pct_sum = sum([internal_pkg_pct[t] for t in sponsoren_df['Typ']])
            v_pct_avail = max(1, 100 - s_pct_sum)
            loop_for_v = min_v_time / (v_pct_avail / 100) if v_pct_avail > 0 else min_v_time
            final_loop_duration = max(base_loop, loop_for_v)

            st.success(f"Optimierte Loop-Dauer: **{int(final_loop_duration//60)}m {int(final_loop_duration%60)}s**")
            play_mode = st.radio("Ausspielungs-Modus", ["Durchmischt", "Block: Sponsoren zuerst", "Block: Sponsoren zuletzt"])

            if st.button("🚀 Playlist generieren"):
                s_pool = []
                for _, row in sponsoren_df.iterrows():
                    wdh = math.ceil((final_loop_duration * (internal_pkg_pct[row['Typ']]/100)) / row['Dauer'])
                    for _ in range(wdh): s_pool.append({"id": str(row['id']), "Name": row['Name'], "Dauer": row['Dauer'], "Typ": row['Typ']})
                
                v_list = vereins_df.to_dict('records')
                v_instances, v_counter, current_s_time = [], 0, sum(s['Dauer'] for s in s_pool)
                if v_list:
                    while (current_s_time + sum(v['Dauer'] for v in v_instances)) < final_loop_duration or v_counter < len(v_list):
                        v_instances.append(v_list[v_counter % len(v_list)]); v_counter += 1

                final_playlist = []
                if play_mode == "Durchmischt":
                    random.shuffle(s_pool)
                    v_idx = 0
                    for s in s_pool:
                        final_playlist.append(s)
                        if v_idx < len(v_instances): final_playlist.append(v_instances[v_idx]); v_idx += 1
                    final_playlist.extend(v_instances[v_idx:])
                elif "zuerst" in play_mode:
                    s_pool.sort(key=lambda x: {"XL": 1, "L": 2, "M": 3, "S": 4}.get(x['Typ'], 5))
                    final_playlist = s_pool + v_instances
                else:
                    s_pool.sort(key=lambda x: {"XL": 1, "L": 2, "M": 3, "S": 4}.get(x['Typ'], 5))
                    final_playlist = v_instances + s_pool

                res_df = pd.DataFrame(final_playlist)
                t_acc, start_times = 0, []
                for d in res_df['Dauer']:
                    start_times.append(f"{int(t_acc//60):02d}:{int(t_acc%60):02d}"); t_acc += d
                res_df.insert(0, "Start im Loop", start_times)
                
                st.subheader("📊 Generierte Loop-Playliste")
                st.dataframe(res_df[['Start im Loop', 'Name', 'Dauer', 'Typ', 'id']], use_container_width=True)
                st.write(f"**Spots:** {len(res_df)} | **Dauer:** {res_df['Dauer'].sum()}s")

                st.divider()
                col_ex1, col_ex2 = st.columns([1, 1])
                with col_ex1:
                    csv = res_df.to_csv(index=False, sep=';').encode('utf-8-sig')
                    st.download_button("📥 Excel-Export", csv, "playlist_stadion.csv", "text/csv")
                    
                    plot_data = res_df.groupby(['Name', 'Typ'])['Dauer'].sum().reset_index()
                    fig, ax = plt.subplots(figsize=(3, 3))
                    cmap = plt.get_cmap('tab20')
                    colors = [cmap(i % 20) if t != 'Verein (Puffer)' else '#d3d3d3' for i, t in enumerate(plot_data['Typ'])]
                    ax.pie(plot_data['Dauer'], labels=plot_data['Name'], autopct='%1.1f%%', startangle=90, colors=colors, wedgeprops={'edgecolor': 'black', 'linewidth': 0.5}, textprops={'fontsize': 7})
                    ax.axis('equal')
                    st.pyplot(fig)
                    
                    buf = io.BytesIO()
                    fig.savefig(buf, format="png", bbox_inches='tight', dpi=150)
                    pdf_bytes = create_pdf(res_df[['Start im Loop', 'Name', 'Dauer', 'Typ', 'id']], buf)
                    st.download_button(label="📄 PDF-Report (SGE Brand)", data=pdf_bytes, file_name="SGE_Ad_Report.pdf", mime="application/pdf")
                    plt.close(fig)
