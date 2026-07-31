import streamlit as st
import pandas as pd
import plotly.express as px
import glob

# ==========================================
# 1. KONFIGURASI HALAMAN DASHBOARD
# ==========================================
st.set_page_config(
    page_title="Dashboard Tunggakan Kendaraan - GASPOL",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Dashboard Interaktif Analisis Tunggakan Kendaraan")
st.markdown("Aplikasi analisis interaktif untuk memantau status pembayaran, tindak lanjut, dan potensi penerimaan pajak kendaraan.")

# ==========================================
# 2. BACA & GABUNGKAN DATA CSV OTOMATIS
# ==========================================
@st.cache_data
def load_and_combine_data():
    file_list = glob.glob("*.csv")
    file_list = [f for f in file_list if "Kode Plat" not in f and "Query result" not in f and "filtered" not in f]
    
    if not file_list:
        return pd.DataFrame()
        
    df_list = []
    for file in file_list:
        try:
            df_temp = pd.read_csv(file, sep=";")
            if df_temp.shape[1] <= 1:
                df_temp = pd.read_csv(file, sep=",")
            df_list.append(df_temp)
        except Exception as e:
            st.warning(f"Gagal membaca file {file}: {e}")
            
    if df_list:
        df_combined = pd.concat(df_list, ignore_index=True)
        
        rename_dict = {}
        if 'samsat_asal_nama' in df_combined.columns and 'nama_samsat' not in df_combined.columns:
            rename_dict['samsat_asal_nama'] = 'nama_samsat'
        if 'status_nomor_hp_valid' in df_combined.columns and 'flag_nomor_hp_valid' not in df_combined.columns:
            rename_dict['status_nomor_hp_valid'] = 'flag_nomor_hp_valid'
            
        if rename_dict:
            df_combined = df_combined.rename(columns=rename_dict)
            
        return df_combined
        
    return pd.DataFrame()

df = load_and_combine_data()

if df.empty:
    st.error("⚠️ File CSV tidak ditemukan! Pastikan file CSV data kendaraan disimpan di folder yang sama dengan app.py.")
else:
    # Penentuan nama kolom HP secara aman
    if 'flag_nomor_hp_valid' in df.columns:
        col_hp_name = 'flag_nomor_hp_valid'
    elif 'status_nomor_hp_valid' in df.columns:
        col_hp_name = 'status_nomor_hp_valid'
    else:
        col_hp_name = None

    # ==========================================
    # 3. PANEL FILTER SIDEBAR (KIRI)
    # ==========================================
    st.sidebar.header("🔍 Filter Data")
    
    if 'nama_cabang' in df.columns:
        cabang_list = ["Semua Cabang"] + sorted([str(x) for x in df['nama_cabang'].dropna().unique()])
        selected_cabang = st.sidebar.selectbox("Pilih Kantor Cabang:", cabang_list)
    else:
        selected_cabang = "Semua Cabang"

    if 'nama_samsat' in df.columns:
        if selected_cabang != "Semua Cabang" and 'nama_cabang' in df.columns:
            df_sub = df[df['nama_cabang'] == selected_cabang]
            samsat_list = ["Semua Samsat"] + sorted([str(x) for x in df_sub['nama_samsat'].dropna().unique()])
        else:
            samsat_list = ["Semua Samsat"] + sorted([str(x) for x in df['nama_samsat'].dropna().unique()])
        selected_samsat = st.sidebar.selectbox("Pilih Unit Samsat:", samsat_list)
    else:
        selected_samsat = "Semua Samsat"

    if 'kelompok_selisih_hari_tunggakan' in df.columns:
        tunggakan_list = ["Semua Kelompok"] + sorted([str(x) for x in df['kelompok_selisih_hari_tunggakan'].dropna().unique()])
        selected_tunggakan = st.sidebar.selectbox("Masa Tunggakan:", tunggakan_list)
    else:
        selected_tunggakan = "Semua Kelompok"

    if col_hp_name and col_hp_name in df.columns:
        hp_list =
