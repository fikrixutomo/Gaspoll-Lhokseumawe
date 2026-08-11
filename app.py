import streamlit as st
import pandas as pd
import glob
import os

# ---------------------------------------------------
# 1. KONFIGURASI HALAMAN & TAMPILAN
# ---------------------------------------------------
# Pastikan Anda memiliki gambar "logo_jasa_raharja.png" di folder yang sama
URL_LOGO_JR = "logo_jasa_raharja.png" 

st.set_page_config(
    page_title="Dashboard Analisa Data GASPOL", 
    page_icon="🚗", 
    layout="wide"
)

# ---------------------------------------------------
# 2. FUNGSI MEMBACA DATA DENGAN PINTAR (SMART LOAD)
# ---------------------------------------------------
# ttl=600 akan memaksa Streamlit memperbarui cache setiap 600 detik (10 Menit)
# Ini mencegah masalah data CSV baru yang tidak terbaca
@st.cache_data(ttl=600)
def load_and_combine_data():
    file_list = glob.glob("*.csv")
    df_list = []
    
    if not file_list:
        return pd.DataFrame() # Jika tidak ada file CSV, kembalikan tabel kosong
        
    for file in file_list:
        try:
            # sep=None dan engine='python' membuat Pandas pintar menebak apakah file 
            # dipisah menggunakan koma (,) atau titik koma (;)
            df_temp = pd.read_csv(file, sep=None, engine='python')
            df_list.append(df_temp)
        except Exception as e:
            st.warning(f"⚠️ Gagal membaca file {file}: {e}")
            
    if df_list:
        # Gabungkan semua file CSV menjadi satu data utuh
        df_combined = pd.concat(df_list, ignore_index=True)
        return df_combined
    else:
        return pd.DataFrame()

# Load datanya sekarang
df = load_and_combine_data()

# ---------------------------------------------------
# 3. HEADER & LOGO DASHBOARD
# ---------------------------------------------------
col1, col2 = st.columns([1, 8])
with col1:
    try:
        st.image(URL_LOGO_JR, width=80)
    except:
        st.markdown("<h1>🚗</h1>", unsafe_allow_html=True) # Fallback jika gambar logo tidak ada
with col2:
    st.title("Dashboard Analisa Data Kendaraan GASPOL")

st.markdown("---")

# ---------------------------------------------------
# 4. LOGIKA UTAMA & FILTERING
# ---------------------------------------------------
if df.empty:
    st.error("⚠️ Data CSV tidak ditemukan atau gagal dibaca. Pastikan file CSV ada di dalam folder yang sama dengan app.py.")
else:
    # A. STANDARISASI NAMA KOLOM (Menyatukan format lama & baru)
    if 'nama_samsat' in df.columns and 'samsat_asal_nama' not in df.columns:
        df = df.rename(columns={'nama_samsat': 'samsat_asal_nama'})
    if 'flag_nomor_hp_valid' in df.columns and 'status_nomor_hp_valid' not in df.columns:
        df = df.rename(columns={'flag_nomor_hp_valid': 'status_nomor_hp_valid'})

    # B. MENU SIDEBAR UNTUK FILTER
    st.sidebar.header("🔍 Filter Data")
    
    # 1. Filter Nama Cabang
    if 'nama_cabang' in df.columns:
        # Ambil nilai unik, hapus yang kosong (dropna)
        cabang_unique = ["Semua Cabang"] + list(df['nama_cabang'].dropna().unique())
        pilih_cabang = st.sidebar.selectbox("Pilih Cabang", cabang_unique)
    else:
        pilih_cabang = "Semua Cabang"
        st.sidebar.warning("Kolom 'nama_cabang' tidak ditemukan di CSV.")

    # 2. Filter Status Pembayaran
    if 'status_bayar' in df.columns:
        status_bayar_unique = ["Semua Status"] + list(df['status_bayar'].dropna().unique())
        pilih_status = st.sidebar.selectbox("Status Pembayaran", status_bayar_unique)
    else:
        pilih_status = "Semua Status"

    # C. TERAPKAN FILTER KE DATA
    df_filtered = df.copy()
    
    if pilih_cabang != "Semua Cabang":
        df_filtered = df_filtered[df_filtered['nama_cabang'] == pilih_cabang]
        
    if pilih_status != "Semua Status":
        df_filtered = df_filtered[df_filtered['status_bayar'] == pilih_status]

    # ---------------------------------------------------
    # 5. MENAMPILKAN METRIK & TABEL HASIL
    # ---------------------------------------------------
    st.subheader(f"📊 Ringkasan Data: {pilih_cabang}")
    
    # Hitung Angka Metrik (Disesuaikan dengan penulisan huruf besar/kecil)
    total_kendaraan = len(df_filtered)
    
    if 'status_bayar' in df_filtered.columns:
        # Gunakan .str.upper() agar 'LUNAS', 'Lunas', 'lunas' dihitung sama
        total_lunas = len(df_filtered[df_filtered['status_bayar'].astype(str).str.upper() == 'LUNAS'])
        total_belum_lunas = len(df_filtered[df_filtered['status_bayar'].astype(str).str.upper() == 'BELUM LUNAS'])
    else:
        total_lunas, total_belum_lunas = 0, 0

    # Tampilkan Box Metrik
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Kendaraan", f"{total_kendaraan} Unit")
    m2.metric("Sudah Lunas", f"{total_lunas} Unit")
    m3.metric("Belum Lunas (Tunggakan)", f"{total_belum_lunas} Unit")

    # Tampilkan Tabel Data
    st.markdown("### 📋 Detail Data Kendaraan")
    st.dataframe(df_filtered, use_container_width=True)
