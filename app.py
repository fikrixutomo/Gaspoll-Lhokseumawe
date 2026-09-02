import streamlit as st
import pandas as pd
import plotly.express as px
import glob

# 1. Konfigurasi Tampilan Halaman
st.set_page_config(
    page_title="Dashboard Tunggakan Kendaraan - GASPOL", 
    page_icon="🚗", 
    layout="wide"
)

st.title("🚗 Dashboard Interaktif Analisis Tunggakan Kendaraan")
st.markdown("Aplikasi ini otomatis membaca dan menggabungkan seluruh data CSV di dalam folder dengan aman.")

# 2. Membaca Seluruh File CSV secara Otomatis, Aman, & Cerdas (Auto-Delimiter)
@st.cache_data(ttl=600)
def load_and_combine_data():
    file_list = glob.glob("*.csv")
    # Filter agar file selain data utama tidak ikut terbaca
    file_list = [f for f in file_list if "Kode Plat" not in f and "Query result" not in f and "filtered" not in f]
    
    if not file_list:
        return pd.DataFrame()
        
    df_list = []
    for file in file_list:
        try:
            # Mencoba membaca dengan titik koma (;) terlebih dahulu
            df_temp = pd.read_csv(file, sep=";", on_bad_lines='skip', engine='python')
            # Jika hanya terbaca 1 kolom, beralih otomatis ke koma (,)
            if df_temp.shape[1] <= 1:
                df_temp = pd.read_csv(file, sep=",", on_bad_lines='skip', engine='python')
            df_list.append(df_temp)
        except Exception as e:
            st.warning(f"Gagal membaca file {file}: {e}")
            
    if df_list:
        df_combined = pd.concat(df_list, ignore_index=True)
        
        # Standarisasi nama kolom otomatis (mencegah bentrok nama kolom lama & baru)
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
    st.error("⚠️ File CSV tidak ditemukan! Pastikan file CSV data kendaraan Anda disimpan di folder yang sama dengan file app.py ini.")
else:
    # Penentuan variabel nama kolom status HP yang aman
    if 'flag_nomor_hp_valid' in df.columns:
        col_hp_name = 'flag_nomor_hp_valid'
    elif 'status_nomor_hp_valid' in df.columns:
        col_hp_name = 'status_nomor_hp_valid'
    else:
        col_hp_name = None

    # 3. PANEL FILTER SIDEBAR (KIRI)
    st.sidebar.header("🔍 Filter Data")
    
    # Filter Kantor Cabang / Wilayah
    if 'nama_cabang' in df.columns:
        cabang_unique = [str(x) for x in df['nama_cabang'].dropna().unique()]
        all_cabang = ["Semua Cabang / Wilayah"] + sorted(cabang_unique)
        selected_cabang = st.sidebar.selectbox("Pilih Kantor Cabang / Wilayah:", all_cabang)
    else:
        selected_cabang = "Semua Cabang / Wilayah"

    # Filter Samsat (Dinamis berdasarkan Cabang)
    if 'nama_samsat' in df.columns:
        if selected_cabang != "Semua Cabang / Wilayah" and 'nama_cabang' in df.columns:
            df_sub = df[df['nama_cabang'] == selected_cabang]
            samsat_unique = [str(x) for x in df_sub['nama_samsat'].dropna().unique()]
        else:
            samsat_unique = [str(x) for x in df['nama_samsat'].dropna().unique()]
            
        all_samsat = ["Semua Samsat"] + sorted(samsat_unique)
        selected_samsat = st.sidebar.selectbox("Pilih Unit Samsat:", all_samsat)
    else:
        selected_samsat = "Semua Samsat"

    # Filter Kelompok Tunggakan
    if 'kelompok_selisih_hari_tunggakan' in df.columns:
        tunggakan_unique = [str(x) for x in df['kelompok_selisih_hari_tunggakan'].dropna().unique()]
        all_tunggakan = ["Semua Kelompok"] + sorted(tunggakan_unique)
        selected_tunggakan = st.sidebar.selectbox("Masa Tunggakan:", all_tunggakan)
    else:
        selected_tunggakan = "Semua Kelompok"

    # Filter Status Pembayaran
    if 'status_bayar' in df.columns:
        bayar_unique = [str(x) for x in df['status_bayar'].dropna().unique()]
        all_bayar = ["Semua Status Bayar"] + sorted(bayar_unique)
        selected_bayar = st.sidebar.selectbox("Status Pembayaran:", all_bayar)
    else:
        selected_bayar = "Semua Status Bayar"

    # Filter Validitas HP
    if col_hp_name:
        hp_unique = [str(x) for x in df[col_hp_name].dropna().unique()]
        all_hp_status = ["Semua Status HP"] + sorted(hp_unique)
        selected_hp = st.sidebar.selectbox("Status Nomor HP:", all_hp_status)
    else:
        selected_hp = "Semua Status HP"

    # Pencarian Teks
    cari_kata = st.sidebar.text_input("Cari No. Polisi / Nama Pemilik:")

    # 4. TERAPKAN FILTER KE DATA
    df_filtered = df.copy()
    
    if selected_cabang != "Semua Cabang / Wilayah" and 'nama_cabang' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['nama_cabang'] == selected_cabang]
        
    if selected_samsat != "Semua Samsat" and 'nama_samsat' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['nama_samsat'] == selected_samsat]
        
    if selected_tunggakan != "Semua Kelompok" and 'kelompok_selisih_hari_tunggakan' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['kelompok_selisih_hari_tunggakan'] == selected_tunggakan]
        
    if selected_bayar != "Semua Status Bayar" and 'status_bayar' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status_bayar'] == selected_bayar]
        
    if selected_hp != "Semua Status HP" and col_hp_name and col_hp_name in df_filtered.columns:
        df_filtered = df_filtered[df_filtered[col_hp_name] == selected_hp]
        
    if cari_kata:
        cond_plat = df_filtered['no_polisi'].astype(str).str.contains(cari_kata, case=False, na=False) if 'no_polisi' in df_filtered.columns else False
        cond_nama = df_filtered['nama_pemilik_terakhir'].astype(str).str.contains(cari_kata, case=False, na=False) if 'nama_pemilik_terakhir' in df_filtered.columns else False
        df_filtered = df_filtered[cond_plat | cond_nama]

    # 5. RINGKASAN METRIK UTAMA
    st.subheader(f"📊 Ringkasan Indikator Utama ({selected_cabang})")
    
    total_kendaraan = len(df_filtered)
    
    if 'status_bayar' in df_filtered.columns:
        s_bayar = df_filtered['status_bayar'].astype(str).str.strip().str.upper()
        jml_lunas = len(df_filtered[s_bayar.str.contains('LUNAS|SUDAH BAYAR|SDH BAYAR', na=False)])
        jml_belum_lunas = len(df_filtered[s_bayar.str.contains('BELUM LUNAS|BELUM BAYAR|BLM BAYAR', na=False)])
    else:
        jml_lunas = jml_belum_lunas = 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Kendaraan", f"{total_kendaraan:,} Unit")
    m2.metric("Kendaraan Lunas", f"{jml_lunas:,} Unit")
    m3.metric("Kendaraan Belum Lunas", f"{jml_belum_lunas:,} Unit", delta_color="inverse")

    st.markdown("---")

    # 6. TABEL DETAIL DATA
    st.subheader("📋 Tabel Detail Kendaraan")
    st.dataframe(df_filtered, use_container_width=True)

    # 7. TOMBOL UNDUH CSV
    csv_data = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Hasil Filter (.CSV)",
        data=csv_data,
        file_name="data_tunggakan_filtered.csv",
        mime="text/csv"
    )
