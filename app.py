import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import io

# ---------------------------------------------------
# 1. KONFIGURASI HALAMAN & TAMPILAN
# ---------------------------------------------------
URL_LOGO_JR = "logo_jasa_raharja.png" 

st.set_page_config(
    page_title="Dashboard Analisis Tunggakan GASPOL",
    page_icon="🚗",
    layout="wide"
)

# ---------------------------------------------------
# 2. PEMUATAN DATA AMAN (SMART LOAD & AUTO DELIMITER)
# ---------------------------------------------------
@st.cache_data(ttl=600)
def load_and_combine_data():
    file_list = glob.glob("*.csv")
    file_list = [
        f for f in file_list 
        if "Kode Plat" not in f 
        and "Query result" not in f 
        and "filtered" not in f
    ]
    
    if not file_list:
        return pd.DataFrame()
        
    df_list = []
    for file in file_list:
        try:
            df_temp = pd.read_csv(file, sep=None, engine='python', on_bad_lines='skip')
            df_list.append(df_temp)
        except Exception as e:
            st.warning(f"⚠️ Gagal membaca file {file}: {e}")
            
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
    else:
        return pd.DataFrame()

df = load_and_combine_data()

# ---------------------------------------------------
# 3. HEADER & LOGO DASHBOARD
# ---------------------------------------------------
col_logo, col_title = st.columns([1, 8])
with col_logo:
    try:
        st.image(URL_LOGO_JR, width=80)
    except:
        st.markdown("<h1>🚗</h1>", unsafe_allow_html=True)
with col_title:
    st.title("Dashboard Analisis Tunggakan Kendaraan & Instansi")

st.markdown("---")

# ---------------------------------------------------
# 4. PANEL FILTER SIDEBAR
# ---------------------------------------------------
if df.empty:
    st.error("⚠️ File CSV data tidak ditemukan atau gagal dibaca. Pastikan file CSV berada di folder yang sama dengan app.py.")
else:
    st.sidebar.header("🔍 Filter Data Utama")
    
    # 1. Filter Cabang / Wilayah
    if 'nama_cabang' in df.columns:
        val_cabang = ["Semua Cabang / Wilayah"] + sorted([str(x) for x in df['nama_cabang'].dropna().unique()])
        selected_cabang = st.sidebar.selectbox("Pilih Cabang / Wilayah:", val_cabang)
    else:
        selected_cabang = "Semua Cabang / Wilayah"

    # 2. Filter Samsat
    if 'nama_samsat' in df.columns:
        if selected_cabang != "Semua Cabang / Wilayah" and 'nama_cabang' in df.columns:
            df_sub = df[df['nama_cabang'] == selected_cabang]
            val_samsat = ["Semua Samsat"] + sorted([str(x) for x in df_sub['nama_samsat'].dropna().unique()])
        else:
            val_samsat = ["Semua Samsat"] + sorted([str(x) for x in df['nama_samsat'].dropna().unique()])
        selected_samsat = st.sidebar.selectbox("Samsat:", val_samsat)
    else:
        selected_samsat = "Semua Samsat"

    # 3. Filter Jenis Pemilik
    if 'pemilik_jenis' in df.columns:
        val_pemilik = ["Semua Jenis Pemilik"] + sorted([str(x) for x in df['pemilik_jenis'].dropna().unique()])
        selected_pemilik = st.sidebar.selectbox("Jenis Pemilik:", val_pemilik)
    else:
        selected_pemilik = "Semua Jenis Pemilik"

    # 4. Filter Nama Pemilik / Instansi
    col_perusahaan = 'nama_pemilik_terakhir' if 'nama_pemilik_terakhir' in df.columns else 'nama_instansi' if 'nama_instansi' in df.columns else None
    if col_perusahaan:
        val_nama = ["Semua Nama Pemilik"] + sorted([str(x) for x in df[col_perusahaan].dropna().unique()])
        selected_nama = st.sidebar.selectbox("Nama Pemilik / Instansi:", val_nama)
    else:
        selected_nama = "Semua Nama Pemilik"

    # 5. Filter Status Pembayaran
    if 'status_bayar' in df.columns:
        val_bayar = ["Semua Status Bayar"] + sorted([str(x) for x in df['status_bayar'].dropna().unique()])
        selected_bayar = st.sidebar.selectbox("Status Pembayaran:", val_bayar)
    else:
        selected_bayar = "Semua Status Bayar"

    # 6. Filter Status Tindak Lanjut
    if 'status_tindak_lanjut' in df.columns:
        val_tl = ["Semua Status TL"] + sorted([str(x) for x in df['status_tindak_lanjut'].dropna().unique()])
        selected_tl = st.sidebar.selectbox("Status Tindak Lanjut:", val_tl)
    else:
        selected_tl = "Semua Status TL"

    # 7. Filter Masa Tunggakan
    if 'kelompok_selisih_hari_tunggakan' in df.columns:
        val_tunggakan = ["Semua Kelompok"] + sorted([str(x) for x in df['kelompok_selisih_hari_tunggakan'].dropna().unique()])
        selected_tunggakan = st.sidebar.selectbox("Masa Tunggakan:", val_tunggakan)
    else:
        selected_tunggakan = "Semua Kelompok"

    # 8. Pencarian Cepat Teks
    cari_kata = st.sidebar.text_input("Cari Plat / Nama:")

    # ---------------------------------------------------
    # 5. TERAPKAN FILTER KE DATASET
    # ---------------------------------------------------
    df_filtered = df.copy()
    
    if selected_cabang != "Semua Cabang / Wilayah" and 'nama_cabang' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['nama_cabang'] == selected_cabang]
    if selected_samsat != "Semua Samsat" and 'nama_samsat' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['nama_samsat'] == selected_samsat]
    if selected_pemilik != "Semua Jenis Pemilik" and 'pemilik_jenis' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['pemilik_jenis'].astype(str) == selected_pemilik]
    if selected_nama != "Semua Nama Pemilik" and col_perusahaan:
        df_filtered = df_filtered[df_filtered[col_perusahaan].astype(str) == selected_nama]
    if selected_bayar != "Semua Status Bayar" and 'status_bayar' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status_bayar'].astype(str) == selected_bayar]
    if selected_tl != "Semua Status TL" and 'status_tindak_lanjut' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status_tindak_lanjut'].astype(str) == selected_tl]
    if selected_tunggakan != "Semua Kelompok" and 'kelompok_selisih_hari_tunggakan' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['kelompok_selisih_hari_tunggakan'] == selected_tunggakan]
    if cari_kata:
        cond_plat = df_filtered['no_polisi'].astype(str).str.contains(cari_kata, case=False, na=False) if 'no_polisi' in df_filtered.columns else False
        cond_nama = df_filtered[col_perusahaan].astype(str).str.contains(cari_kata, case=False, na=False) if col_perusahaan else False
        df_filtered = df_filtered[cond_plat | cond_nama]

    # ---------------------------------------------------
    # 6. PERHITUNGAN MATRIKS (COVERAGE & CONVERSION REVISI)
    # ---------------------------------------------------
    total_kendaraan = len(df_filtered)

    if 'status_bayar' in df_filtered.columns and 'status_tindak_lanjut' in df_filtered.columns:
        s_bayar = df_filtered['status_bayar'].astype(str).str.strip().str.upper()
        s_tl = df_filtered['status_tindak_lanjut'].astype(str).str.strip().str.upper()

        cond_blm_lunas = s_bayar.str.contains('BELUM LUNAS|BELUM BAYAR|BLM BAYAR', na=False)
        cond_lunas = s_bayar.str.contains('LUNAS|SUDAH BAYAR|SDH BAYAR', na=False) & ~cond_blm_lunas

        cond_sdh_tl = s_tl.str.contains('SUDAH DITINDAKLANJUTI|SUDAH DIKUNJUNGI|SUDAH TL|SDH TL', na=False)
        cond_blm_tl = s_tl.str.contains('BELUM DITINDAKLANJUTI|BELUM DIKUNJUNGI|BELUM TL|BLM TL', na=False) & ~cond_sdh_tl

        jml_lunas = len(df_filtered[cond_lunas])
        jml_belum_lunas = len(df_filtered[cond_blm_lunas])

        total_sdh_tl = len(df_filtered[cond_sdh_tl])
        jml_lunas_sdh_tl = len(df_filtered[cond_lunas & cond_sdh_tl])
        
        # 1. Coverage Rate = Total Kendaraan Sudah TL / Total Kendaraan
        coverage_rate = (total_sdh_tl / total_kendaraan * 100) if total_kendaraan > 0 else 0.0

        # 2. Conversion Rate (REVISI BARU) = Lunas Sudah TL / Total Kendaraan Sudah TL
        conversion_rate = (jml_lunas_sdh_tl / total_sdh_tl * 100) if total_sdh_tl > 0 else 0.0
            
        efektivitas_tl = conversion_rate
        
        jml_lunas_blm_tl = len(df_filtered[cond_lunas & cond_blm_tl])
        jml_blm_lunas_sdh_tl = len(df_filtered[cond_blm_lunas & cond_sdh_tl])
        jml_blm_lunas_blm_tl = len(df_filtered[cond_blm_lunas & cond_blm_tl])
    else:
        jml_lunas = jml_belum_lunas = total_sdh_tl = 0
        conversion_rate = coverage_rate = efektivitas_tl = 0.0
        jml_lunas_blm_tl = jml_blm_lunas_sdh_tl = jml_blm_lunas_blm_tl = jml_lunas_sdh_tl = 0

    persen_lunas = (jml_lunas / total_kendaraan * 100) if total_kendaraan > 0 else 0.0
    persen_belum_lunas = (jml_belum_lunas / total_kendaraan * 100) if total_kendaraan > 0 else 0.0

    # ---------------------------------------------------
    # 7. TAMPILAN KPI CARDS UTAMA
    # ---------------------------------------------------
    st.subheader(f"📊 Ringkasan Indikator Utama ({selected_cabang})")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Kendaraan", f"{total_kendaraan:,} Unit")
    c2.metric("Conversion Rate", f"{conversion_rate:.1f}%")
    c3.metric("Coverage Rate", f"{coverage_rate:.1f}%")
    c4.metric("Efektivitas TL", f"{efektivitas_tl:.1f}%") 

    st.markdown("---")

    st.subheader("📌 Analisis Pembayaran & Status Tindak Lanjut")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Kendaraan Lunas", f"{jml_lunas:,} Unit", f"{persen_lunas:.1f}%")
    m2.metric("Kendaraan Belum Lunas", f"{jml_belum_lunas:,} Unit", f"{persen_belum_lunas:.1f}%", delta_color="inverse")
    m3.metric("Lunas Sudah TL", f"{jml_lunas_sdh_tl:,} Unit") 
    m4.metric("Lunas Belum TL", f"{jml_lunas_blm_tl:,} Unit")
    m5.metric("Belum Lunas Sudah TL", f"{jml_blm_lunas_sdh_tl:,} Unit")

    if jml_blm_lunas_blm_tl > 0:
        st.warning(f"⚠️ **Beban Kerja:** Terdapat **{jml_blm_lunas_blm_tl:,} Unit** kendaraan belum lunas & belum ditindaklanjuti.")

    st.markdown("---")

    # ---------------------------------------------------
    # 8. MATRIKS DETAIL: GOLONGAN & JENIS PEMILIK
    # ---------------------------------------------------
    st.subheader("📋 Matriks Detail: Golongan & Jenis Pemilik")
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.markdown("##### Ringkasan Berdasarkan Jenis Golongan")
        gol_col = 'kode_golongan_deskripsi' if 'kode_golongan_deskripsi' in df_filtered.columns else 'kode_golongan' if 'kode_golongan' in df_filtered.columns else None
        if not df_filtered.empty and gol_col:
            df_gol = df_filtered[gol_col].value_counts().reset_index()
            df_gol.columns = ['Golongan', 'Jumlah Unit']
            st.dataframe(df_gol, use_container_width=True, hide_index=True)
        else:
            st.info("Data golongan tidak tersedia.")
            
    with col_m2:
        st.markdown("##### Ringkasan Berdasarkan Jenis Pemilik")
        if not df_filtered.empty and 'pemilik_jenis' in df_filtered.columns:
            df_pemilik = df_filtered['pemilik_jenis'].value_counts().reset_index()
            df_pemilik.columns = ['Jenis Pemilik', 'Jumlah Unit']
            st.dataframe(df_pemilik, use_container_width=True, hide_index=True)
        else:
            st.info("Data jenis pemilik tidak tersedia.")

    st.markdown("---")

    # ---------------------------------------------------
    # 9. VISUALISASI GRAFIK INTERAKTIF
    # ---------------------------------------------------
    st.subheader("📈 Visualisasi Grafik Analisis")
    
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.markdown("##### Status Pembayaran vs Tindak Lanjut")
        if not df_filtered.empty and 'status_bayar' in df_filtered.columns and 'status_tindak_lanjut' in df_filtered.columns:
            df_grouped = df_filtered.groupby(['status_bayar', 'status_tindak_lanjut']).size().reset_index(name='Jumlah')
            fig_grouped = px.bar(
                df_grouped, 
                x='status_bayar', 
                y='Jumlah', 
                color='status_tindak_lanjut',
                barmode='group',
                text='Jumlah',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_grouped.update_traces(textposition='outside')
            st.plotly_chart(fig_grouped, use_container_width=True)
        else:
            st.info("Data tidak mencukupi untuk bagan ini.")

    with row1_col2:
        st.markdown("##### Top 10 Samsat Terbanyak")
        if not df_filtered.empty and 'nama_samsat' in df_filtered.columns:
            samsat_counts = df_filtered['nama_samsat'].value_counts().head(10).reset_index()
            samsat_counts.columns = ['Samsat', 'Jumlah']
            fig_samsat = px.bar(
                samsat_counts, 
                x='Jumlah', 
                y='Samsat', 
                orientation='h', 
                color='Jumlah', 
                color_continuous_scale='Blues',
                text='Jumlah'
            )
            fig_samsat.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_samsat, use_container_width=True)
        else:
            st.info("Kolom nama_samsat tidak ditemukan.")

    st.markdown("---")

    # ---------------------------------------------------
    # 10. TABEL DETAIL KENDARAAN & TOMBOL DOWNLOAD
    # ---------------------------------------------------
    st.subheader("📋 Tabel Detail Kendaraan")
    st.info("💡 **Tips:** Klik judul kolom pada tabel untuk mengurutkan (sort) data secara instan.")
    
    kolom_tampilan = [c for c in [
        'no_polisi', 'nama_pemilik_terakhir', 'pemilik_jenis', 'nama_samsat', 'nama_cabang', 
        'kode_golongan', 'kode_jenis_kendaraan_deskripsi', 'tgl_mati_yad', 'nomor_hp', 
        'kelompok_selisih_hari_tunggakan', 'status_tindak_lanjut', 'status_bayar', 'prioritas'
    ] if c in df_filtered.columns]
    
    st.dataframe(df_filtered[kolom_tampilan], use_container_width=True)
    
    st.markdown("### 📥 Download Hasil Filter Data")
    dl1, dl2 = st.columns(2)
    
    with dl1:
        try:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_filtered.to_excel(writer, index=False, sheet_name='Data_Tunggakan')
            st.download_button(
                label="📊 Download File Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name="Hasil_Filter_Tunggakan.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception:
            st.warning("Pustaka 'openpyxl' diperlukan untuk ekspor Excel.")
            
    with dl2:
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download File CSV (.csv)",
            data=csv_data,
            file_name="data_tunggakan_filtered.csv",
            mime="text/csv"
        )

# ---------------------------------------------------
# 11. COPYRIGHT FOOTER
# ---------------------------------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>© 2026 JRLXFikri - Cabang Lhokseumawe. All rights reserved.</p>",
    unsafe_allow_html=True
)
