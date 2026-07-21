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
st.markdown("Aplikasi ini membaca dan menggabungkan data kendaraan tunggakan secara otomatis.")

# 2. Fungsi Membaca dan Menggabungkan Semua File CSV Otomatis
@st.cache_data
def load_and_combine_data():
    # Mencari semua file berformat .csv di dalam folder ini
    file_list = glob.glob("*.csv")
    
    # Abaikan file pendukung jika ada agar tidak merusak tabel utama
    file_list = [f for f in file_list if "Kode Plat" not in f and "Query result" not in f and "data_kerja" not in f]
    
    combined_df = pd.DataFrame()
    for file in file_list:
        try:
            df = pd.read_csv(file)
            combined_df = pd.concat([combined_df, df], ignore_index=True)
        except Exception as e:
            st.warning(f"Gagal membaca file {file}: {e}")
            
    return combined_df

# Memuat data ke dalam variabel
df = load_and_combine_data()

if df.empty:
    st.error("⚠️ Data CSV tidak ditemukan! Pastikan file CSV data kendaraan sudah disimpan di dalam folder yang sama dengan file app.py ini.")
else:
    # 3. PANEL FILTER DI SIDEBAR (SEBELAH KIRI)
    st.sidebar.header("🔍 Filter Data")
    
    # Filter Kantor Cabang
    all_cabang = ["Semua Cabang"] + sorted([str(x) for x in df['nama_cabang'].dropna().unique()])
    selected_cabang = st.sidebar.selectbox("Pilih Kantor Cabang:", all_cabang)
    
    # Filter Samsat (Dinamis sesuai Cabang)
    if selected_cabang != "Semua Cabang":
        samsat_list = sorted([str(x) for x in df[df['nama_cabang'] == selected_cabang]['nama_samsat'].dropna().unique()])
    else:
        samsat_list = sorted([str(x) for x in df['nama_samsat'].dropna().unique()])
    all_samsat = ["Semua Samsat"] + samsat_list
    selected_samsat = st.sidebar.selectbox("Pilih Unit Samsat:", all_samsat)
    
    # Filter Kelompok Hari Tunggakan
    all_tunggakan = ["Semua Kelompok"] + list(df['kelompok_selisih_hari_tunggakan'].dropna().unique())
    selected_tunggakan = st.sidebar.selectbox("Masa Tunggakan:", all_tunggakan)
    
    # Filter Validitas Nomor HP
    all_hp_status = ["Semua Status HP"] + list(df['flag_nomor_hp_valid'].dropna().unique())
    selected_hp = st.sidebar.selectbox("Status Nomor HP:", all_hp_status)

    # Kotak Pencarian Teks (Cari Plat atau Nama)
    cari_kata = st.sidebar.text_input("Cari No. Polisi / Nama Pemilik:")

    # 4. MENGAPLIKASIKAN FILTER KE DATA
    df_filtered = df.copy()
    if selected_cabang != "Semua Cabang":
        df_filtered = df_filtered[df_filtered['nama_cabang'] == selected_cabang]
    if selected_samsat != "Semua Samsat":
        df_filtered = df_filtered[df_filtered['nama_samsat'] == selected_samsat]
    if selected_tunggakan != "Semua Kelompok":
        df_filtered = df_filtered[df_filtered['kelompok_selisih_hari_tunggakan'] == selected_tunggakan]
    if selected_hp != "Semua Status HP":
        df_filtered = df_filtered[df_filtered['flag_nomor_hp_valid'] == selected_hp]
    if cari_kata:
        df_filtered = df_filtered[
            df_filtered['no_polisi'].astype(str).str.contains(cari_kata, case=False, na=False) | 
            df_filtered['nama_pemilik_terakhir'].astype(str).str.contains(cari_kata, case=False, na=False)
        ]

    # 5. METRIK RINGKASAN ANGKA (KPI METRICS)
    total_kendaraan = len(df_filtered)
    hp_valid = len(df_filtered[df_filtered['flag_nomor_hp_valid'] == 'VALID'])
    persen_hp_valid = (hp_valid / total_kendaraan * 100) if total_kendaraan > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Kendaraan Terfilter", f"{total_kendaraan:,} Unit")
    col2.metric("Nomor HP Valid (Siap Dihubungi)", f"{hp_valid:,} Unit")
    col3.metric("Rasio HP Valid", f"{persen_hp_valid:.1f}%")

    st.markdown("---")

    # 6. GRAFIK VISUALISASI INTERAKTIF
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("📊 Distribusi Kelompok Hari Tunggakan")
        if not df_filtered.empty:
            tunggakan_counts = df_filtered['kelompok_selisih_hari_tunggakan'].value_counts().reset_index()
            tunggakan_counts.columns = ['Masa Tunggakan', 'Jumlah']
            fig1 = px.pie(tunggakan_counts, values='Jumlah', names='Masa Tunggakan', hole=0.3,
                          color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig1, use_container_width=True)

    with col_chart2:
        st.subheader("🚛 Top 10 Jenis Kendaraan Terbanyak")
        if not df_filtered.empty:
            jenis_counts = df_filtered['kode_jenis_kendaraan_deskripsi'].value_counts().head(10).reset_index()
            jenis_counts.columns = ['Jenis Kendaraan', 'Jumlah']
            fig2 = px.bar(jenis_counts, x='Jumlah', y='Jenis Kendaraan', orientation='h',
                          color='Jumlah', color_continuous_scale='Viridis')
            fig2.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # 7. TABEL DETAIL DATA (BISA DI-SORT SAMA SEPERTI EXCEL)
    st.subheader("📋 Data Detail Kendaraan")
    st.info("💡 **Tips:** Anda bisa mengklik judul kolom pada tabel di bawah untuk mengurutkan (sort) data A-Z atau Z-A.")
    
    kolom_tampilan = [
        'no_polisi', 'nama_pemilik_terakhir', 'nama_samsat', 
        'kode_jenis_kendaraan_deskripsi', 'tgl_mati_yad', 'nomor_hp', 
        'kelompok_selisih_hari_tunggakan', 'flag_nomor_hp_valid', 'prioritas'
    ]
    
    st.dataframe(df_filtered[kolom_tampilan], use_container_width=True)
    
    # Tombol Download Data Hasil Filter
    csv_data = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Hasil Filter Data Ini (.CSV)",
        data=csv_data,
        file_name="data_tunggakan_filtered.csv",
        mime="text/csv"
    )