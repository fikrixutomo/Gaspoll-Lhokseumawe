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
    # Abaikan file eksport/filtered hasil download
    file_list = [f for f in file_list if "Kode Plat" not in f and "Query result" not in f and "filtered" not in f]
    
    if not file_list:
        return pd.DataFrame()
        
    df_list = []
    for file in file_list:
        try:
            # Mencoba membaca dengan titik koma (;) lebih dulu
            df_temp = pd.read_csv(file, sep=";")
            if df_temp.shape[1] <= 1:
                # Jika hanya membaca 1 kolom, coba dengan koma (,)
                df_temp = pd.read_csv(file, sep=",")
            df_list.append(df_temp)
        except Exception as e:
            st.warning(f"Gagal membaca file {file}: {e}")
            
    if df_list:
        df_combined = pd.concat(df_list, ignore_index=True)
        
        # Standardisasi Nama Kolom Otomatis
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
    # ==========================================
    # 3. PANEL FILTER SIDEBAR (KIRI)
    # ==========================================
    st.sidebar.header("🔍 Filter Data")
    
    # Filter Kantor Cabang
    if 'nama_cabang' in df.columns:
        cabang_list = ["Semua Cabang"] + sorted([str(x) for x in df['nama_cabang'].dropna().unique()])
        selected_cabang = st.sidebar.selectbox("Pilih Kantor Cabang:", cabang_list)
    else:
        selected_cabang = "Semua Cabang"

    # Filter Samsat (Dinamis berdasarkan Cabang yang dipilih)
    if 'nama_samsat' in df.columns:
        if selected_cabang != "Semua Cabang" and 'nama_cabang' in df.columns:
            df_sub = df[df['nama_cabang'] == selected_cabang]
            samsat_list = ["Semua Samsat"] + sorted([str(x) for x in df_sub['nama_samsat'].dropna().unique()])
        else:
            samsat_list = ["Semua Samsat"] + sorted([str(x) for x in df['nama_samsat'].dropna().unique()])
        selected_samsat = st.sidebar.selectbox("Pilih Unit Samsat:", samsat_list)
    else:
        selected_samsat = "Semua Samsat"

    # Filter Kelompok Tunggakan
    if 'kelompok_selisih_hari_tunggakan' in df.columns:
        tunggakan_list = ["Semua Kelompok"] + sorted([str(x) for x in df['kelompok_selisih_hari_tunggakan'].dropna().unique()])
        selected_tunggakan = st.sidebar.selectbox("Masa Tunggakan:", tunggakan_list)
    else:
        selected_tunggakan = "Semua Kelompok"

    # Filter Status HP
    if 'flag_nomor_hp_valid' in df.columns:
        hp_list = ["Semua Status HP"] + sorted([str(x) for x in df['flag_nomor_hp_valid'].dropna().unique()])
        selected_hp = st.sidebar.selectbox("Status Nomor HP:", hp_list)
    else:
        selected_hp = "Semua Status HP"

    # Filter Status Pembayaran
    if 'status_bayar' in df.columns:
        bayar_list = ["Semua Status Pembayaran"] + sorted([str(x) for x in df['status_bayar'].dropna().unique()])
        selected_bayar = st.sidebar.selectbox("Status Pembayaran:", bayar_list)
    else:
        selected_bayar = "Semua Status Pembayaran"

    # Filter Status Tindak Lanjut
    if 'status_tindak_lanjut' in df.columns:
        tl_list = ["Semua Status Tindak Lanjut"] + sorted([str(x) for x in df['status_tindak_lanjut'].dropna().unique()])
        selected_tl = st.sidebar.selectbox("Status Tindak Lanjut:", tl_list)
    else:
        selected_tl = "Semua Status Tindak Lanjut"

    # Filter Jenis Pemilik
    if 'pemilik_jenis' in df.columns:
        pemilik_list = ["Semua Jenis Pemilik"] + sorted([str(x) for x in df['pemilik_jenis'].dropna().unique()])
        selected_pemilik = st.sidebar.selectbox("Jenis Pemilik:", pemilik_list)
    else:
        selected_pemilik = "Semua Jenis Pemilik"

    # Pencarian Teks
    cari_kata = st.sidebar.text_input("Cari No. Polisi / Nama Pemilik:")

    # ==========================================
    # 4. TERAPKAN FILTER KE DATASET
    # ==========================================
    df_filtered = df.copy()
    
    if selected_cabang != "Semua Cabang" and 'nama_cabang' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['nama_cabang'] == selected_cabang]
        
    if selected_samsat != "Semua Samsat" and 'nama_samsat' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['nama_samsat'] == selected_samsat]
        
    if selected_tunggakan != "Semua Kelompok" and 'kelompok_selisih_hari_tunggakan' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['kelompok_selisih_hari_tunggakan'] == selected_tunggakan]
        
    if selected_hp != "Semua Status HP" and 'flag_nomor_hp_valid' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['flag_nomor_hp_valid'] == selected_hp]
        
    if selected_bayar != "Semua Status Pembayaran" and 'status_bayar' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status_bayar'] == selected_bayar]

    if selected_tl != "Semua Status Tindak Lanjut" and 'status_tindak_lanjut' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status_tindak_lanjut'] == selected_tl]

    if selected_pemilik != "Semua Jenis Pemilik" and 'pemilik_jenis' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['pemilik_jenis'] == selected_pemilik]
        
    if cari_kata:
        cond_plat = df_filtered['no_polisi'].astype(str).str.contains(cari_kata, case=False, na=False) if 'no_polisi' in df_filtered.columns else False
        cond_nama = df_filtered['nama_pemilik_terakhir'].astype(str).str.contains(cari_kata, case=False, na=False) if 'nama_pemilik_terakhir' in df_filtered.columns else False
        df_filtered = df_filtered[cond_plat | cond_nama]

    # ==========================================
    # 5. PERHITUNGAN METRIK & INDICATOR (KPI)
    # ==========================================
    total_kendaraan = len(df_filtered)
    
    # Nomor HP Valid & Rasio
    hp_valid = len(df_filtered[df_filtered['flag_nomor_hp_valid'].astype(str).str.upper() == 'VALID']) if 'flag_nomor_hp_valid' in df_filtered.columns else 0
    persen_hp_valid = (hp_valid / total_kendaraan * 100) if total_kendaraan > 0 else 0

    # Status Lunas vs Belum Lunas
    if 'status_bayar' in df_filtered.columns:
        jml_lunas = len(df_filtered[df_filtered['status_bayar'].astype(str).str.upper() == 'LUNAS'])
        jml_belum_lunas = len(df_filtered[df_filtered['status_bayar'].astype(str).str.upper() == 'BELUM LUNAS'])
    else:
        jml_lunas = 0
        jml_belum_lunas = 0

    persen_lunas = (jml_lunas / total_kendaraan * 100) if total_kendaraan > 0 else 0
    persen_belum_lunas = (jml_belum_lunas / total_kendaraan * 100) if total_kendaraan > 0 else 0

    # Kombinasi Status Bayar & Tindak Lanjut
    if 'status_bayar' in df_filtered.columns and 'status_tindak_lanjut' in df_filtered.columns:
        cond_blm_lunas = df_filtered['status_bayar'].astype(str).str.upper() == 'BELUM LUNAS'
        cond_sdh_lunas = df_filtered['status_bayar'].astype(str).str.upper() == 'LUNAS'
        cond_sdh_tl = df_filtered['status_tindak_lanjut'].astype(str).str.upper() == 'SUDAH DITINDAKLANJUTI'
        cond_blm_tl = df_filtered['status_tindak_lanjut'].astype(str).str.upper() == 'BELUM DITINDAKLANJUTI'

        jml_blm_lunas_sdh_tl = len(df_filtered[cond_blm_lunas & cond_sdh_tl])
        jml_lunas_blm_tl = len(df_filtered[cond_sdh_lunas & cond_blm_tl])
        jml_blm_lunas_blm_tl = len(df_filtered[cond_blm_lunas & cond_blm_tl]) # PR Operasional
        jml_lunas_sdh_tl = len(df_filtered[cond_sdh_lunas & cond_sdh_tl])
        
        # Conversion Rate (Efektivitas Tindak Lanjut)
        total_sdh_tl = len(df_filtered[cond_sdh_tl])
        conversion_rate = (jml_lunas_sdh_tl / total_sdh_tl * 100) if total_sdh_tl > 0 else 0
    else:
        jml_blm_lunas_sdh_tl = 0
        jml_lunas_blm_tl = 0
        jml_blm_lunas_blm_tl = 0
        conversion_rate = 0

    # ==========================================
    # TAMPILAN METRIK (KPI CARDS)
    # ==========================================
    st.subheader("📌 Ringkasan Indikator Utama (KPI)")
    
    # Baris 1: Status Umum & Kontak
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Kendaraan", f"{total_kendaraan:,} Unit")
    c2.metric("Nomor HP Valid", f"{hp_valid:,} Unit")
    c3.metric("Rasio HP Valid", f"{persen_hp_valid:.1f}%")
    c4.metric("Efektivitas TL (Konversi Lunas)", f"{conversion_rate:.1f}%")

    st.markdown("---")

    # Baris 2: Detail Pembayaran & Tindak Lanjut
    st.subheader("💳 Analisis Pembayaran & Status Tindak Lanjut")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Kendaraan Lunas", f"{jml_lunas:,} Unit", f"Persentase: {persen_lunas:.1f}%")
    m2.metric("Kendaraan Belum Lunas", f"{jml_belum_lunas:,} Unit", f"Persentase: {persen_belum_lunas:.1f}%", delta_color="inverse")
    m3.metric("Belum Lunas Sudah TL", f"{jml_blm_lunas_sdh_tl:,} Unit")
    m4.metric("Lunas Belum TL", f"{jml_lunas_blm_tl:,} Unit")

    # Warning Box untuk PR Tim Operasional
    if jml_blm_lunas_blm_tl > 0:
        st.warning(f"🚨 **Beban Kerja Utama (PR Tim Field):** Terdapat **{jml_blm_lunas_blm_tl:,} Unit** kendaraan yang **Belum Lunas dan Belum Ditindaklanjuti**.")

    st.markdown("---")

    # ==========================================
    # 6. BAGAN & VISUALISASI INTERAKTIF
    # ==========================================
    st.subheader("📊 Visualisasi & Analisis Grafis")
    
    row1_col1, row1_col2 = st.columns(2)

    # Bagan 1: Status Pembayaran vs Status Tindak Lanjut (Grouped Bar Chart)
    with row1_col1:
        st.markdown("##### 🔄 Matrik Status Pembayaran vs Tindak Lanjut")
        if not df_filtered.empty and 'status_bayar' in df_filtered.columns and 'status_tindak_lanjut' in df_filtered.columns:
            df_grouped = df_filtered.groupby(['status_bayar', 'status_tindak_lanjut']).size().reset_index(name='Jumlah')
            fig_grouped = px.bar(
                df_grouped, 
                x='status_bayar', 
                y='Jumlah', 
                color='status_tindak_lanjut',
                barmode='group',
                text='Jumlah',
                color_discrete_sequence=px.colors.qualitative.Set2,
                labels={'status_bayar': 'Status Pembayaran', 'status_tindak_lanjut': 'Tindak Lanjut'}
            )
            fig_grouped.update_traces(textposition='outside')
            st.plotly_chart(fig_grouped, use_container_width=True)
        else:
            st.info("Data tidak mencukupi untuk bagan ini.")

    # Bagan 2: Performa Per Samsat (Horizontal Bar Chart)
    with row1_col2:
        st.markdown("##### 🏢 Top 10 Samsat Terbanyak Terfilter")
        if not df_filtered.empty and 'nama_samsat' in df_filtered.columns:
            samsat_counts = df_filtered['nama_samsat'].value_counts().head(10).reset_index()
            s
