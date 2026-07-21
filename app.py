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
st.markdown("Aplikasi ini otomatis membaca dan menggabungkan seluruh data CSV di dalam folder.")

# 2. Membaca Seluruh File CSV secara Otomatis dan Aman
@st.cache_data
def load_and_combine_data():
    file_list = glob.glob("*.csv")
    
    # Filter agar file selain data utama tidak ikut terbaca
    file_list = [f for f in file_list if "Kode Plat" not in f and "Query result" not in f and "filtered" not in f]
    
    if not file_list:
        return pd.DataFrame()
        
    df_list = []
    for file in file_list:
        try:
            df_temp = pd.read_csv(file)
            df_list.append(df_temp)
        except Exception as e:
            st.warning(f"Gagal membaca file {file}: {e}")
            
    if df_list:
        return pd.concat(df_list, ignore_index=True)
    return pd.DataFrame()

df = load_and_combine_data()

if df.empty:
    st.error("⚠️ File CSV tidak ditemukan! Pastikan file CSV data kendaraan Anda disimpan di folder yang sama dengan file app.py ini.")
else:
    # 3. PANEL FILTER SIDEBAR (KIRI)
    st.sidebar.header("🔍 Filter Data")
    
    # Filter Kantor Cabang
    if 'nama_cabang' in df.columns:
        cabang_unique = [str(x) for x in df['nama_cabang'].dropna().unique()]
        all_cabang = ["Semua Cabang"] + sorted(cabang_unique)
        selected_cabang = st.sidebar.selectbox("Pilih Kantor Cabang:", all_cabang)
    else:
        selected_cabang = "Semua Cabang"

    # Filter Samsat (Dinamis berdasarkan Cabang)
    if 'nama_samsat' in df.columns:
        if selected_cabang != "Semua Cabang" and 'nama_cabang' in df.columns:
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

    # Filter Validitas HP
    if 'flag_nomor_hp_valid' in df.columns:
        hp_unique = [str(x) for x in df['flag_nomor_hp_valid'].dropna().unique()]
        all_hp_status = ["Semua Status HP"] + sorted(hp_unique)
        selected_hp = st.sidebar.selectbox("Status Nomor HP:", all_hp_status)
    else:
        selected_hp = "Semua Status HP"

    # Pencarian Teks
    cari_kata = st.sidebar.text_input("Cari No. Polisi / Nama Pemilik:")

    # 4. TERAPKAN FILTER KE DATA
    df_filtered = df.copy()
    if selected_cabang != "Semua Cabang" and 'nama_cabang' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['nama_cabang'] == selected_cabang]
    if selected_samsat != "Semua Samsat" and 'nama_samsat' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['nama_samsat'] == selected_samsat]
    if selected_tunggakan != "Semua Kelompok" and 'kelompok_selisih_hari_tunggakan' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['kelompok_selisih_hari_tunggakan'] == selected_tunggakan]
    if selected_hp != "Semua Status HP" and 'flag_nomor_hp_valid' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['flag_nomor_hp_valid'] == selected_hp]
    if cari_kata:
        cond_plat = df_filtered['no_polisi'].astype(str).str.contains(cari_kata, case=False, na=False) if 'no_polisi' in df_filtered.columns else False
        cond_nama = df_filtered['nama_pemilik_terakhir'].astype(str).str.contains(cari_kata, case=False, na=False) if 'nama_pemilik_terakhir' in df_filtered.columns else False
        df_filtered = df_filtered[cond_plat | cond_nama]

    # 5. RINGKASAN METRIK (KPI)
    total_kendaraan = len(df_filtered)
    hp_valid = len(df_filtered[df_filtered['flag_nomor_hp_valid'] == 'VALID']) if 'flag_nomor_hp_valid' in df_filtered.columns else 0
    persen_hp_valid = (hp_valid / total_kendaraan * 100) if total_kendaraan > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Kendaraan Terfilter", f"{total_kendaraan:,} Unit")
    col2.metric("Nomor HP Valid", f"{hp_valid:,} Unit")
    col3.metric("Rasio HP Valid", f"{persen_hp_valid:.1f}%")

    st.markdown("---")

    # 6. GRAFIK INTERAKTIF
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("📊 Distribusi Kelompok Hari Tunggakan")
        if not df_filtered.empty and 'kelompok_selisih_hari_tunggakan' in df_filtered.columns:
            tunggakan_counts = df_filtered['kelompok_selisih_hari_tunggakan'].value_counts().reset_index()
            tunggakan_counts.columns = ['Masa Tunggakan', 'Jumlah']
            fig1 = px.pie(tunggakan_counts, values='Jumlah', names='Masa Tunggakan', hole=0.3, color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig1, use_container_width=True)

    with col_chart2:
        st.subheader("🚛 Top Jenis Kendaraan Terbanyak")
        if not df_filtered.empty and 'kode_jenis_kendaraan_deskripsi' in df_filtered.columns:
            jenis_counts = df_filtered['kode_jenis_kendaraan_deskripsi'].value_counts().head(8).reset_index()
            jenis_counts.columns = ['Jenis Kendaraan', 'Jumlah']
            fig2 = px.bar(jenis_counts, x='Jumlah', y='Jenis Kendaraan', orientation='h', color='Jumlah', color_continuous_scale='Viridis')
            fig2.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # 7. TABEL DETAIL DATA (BISA DI-SORT SAMA SEPERTI EXCEL)
    st.subheader("📋 Tabel Detail Kendaraan")
    st.info("💡 **Tips:** Klik judul kolom pada tabel di bawah untuk mengurutkan (sort) data secara instan.")
    
    kolom_tampilan = [c for c in ['no_polisi', 'nama_pemilik_terakhir', 'nama_samsat', 'kode_jenis_kendaraan_deskripsi', 'tgl_mati_yad', 'nomor_hp', 'kelompok_selisih_hari_tunggakan', 'flag_nomor_hp_valid', 'prioritas'] if c in df_filtered.columns]
    
    st.dataframe(df_filtered[kolom_tampilan], use_container_width=True)
    
    # Download
    csv_data = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Hasil Filter Data Ini (.CSV)",
        data=csv_data,
        file_name="data_tunggakan_filtered.csv",
        mime="text/csv"
    )