import streamlit as st
import pandas as pd
import plotly.express as px
import glob

# 1. Konfigurasi Tampilan
st.set_page_config(
    page_title="Dashboard Tunggakan",
    page_icon="🚗",
    layout="wide"
)

st.title("Dashboard Analisis Tunggakan Kendaraan")

# 2. Pemuatan Data Aman (Anti Bad Lines)
@st.cache_data
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
            df_temp = pd.read_csv(file, sep=";", on_bad_lines='skip', engine='python')
            if df_temp.shape[1] <= 1:
                df_temp = pd.read_csv(file, sep=",", on_bad_lines='skip', engine='python')
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
    st.error("File CSV tidak ditemukan atau gagal dibaca.")
else:
    if 'flag_nomor_hp_valid' in df.columns:
        col_hp_name = 'flag_nomor_hp_valid'
    elif 'status_nomor_hp_valid' in df.columns:
        col_hp_name = 'status_nomor_hp_valid'
    else:
        col_hp_name = None

    # 3. Sidebar Filter Utama 
    st.sidebar.header("Filter Data")
    
    if 'nama_cabang' in df.columns:
        val_cabang = df['nama_cabang'].dropna().unique()
        cabang_list = ["Semua Cabang / Wilayah"] + sorted([str(x) for x in val_cabang])
        selected_cabang = st.sidebar.selectbox("Pilih Cabang / Wilayah:", cabang_list)
    else:
        selected_cabang = "Semua Cabang / Wilayah"

    if 'nama_samsat' in df.columns:
        if selected_cabang != "Semua Cabang / Wilayah" and 'nama_cabang' in df.columns:
            df_sub = df[df['nama_cabang'] == selected_cabang]
            val_samsat = df_sub['nama_samsat'].dropna().unique()
        else:
            val_samsat = df['nama_samsat'].dropna().unique()
        samsat_list = ["Semua Samsat"] + sorted([str(x) for x in val_samsat])
        selected_samsat = st.sidebar.selectbox("Samsat:", samsat_list)
    else:
        selected_samsat = "Semua Samsat"

    if 'kelompok_selisih_hari_tunggakan' in df.columns:
        val_tunggakan = df['kelompok_selisih_hari_tunggakan'].dropna().unique()
        tunggakan_list = ["Semua Kelompok"] + sorted([str(x) for x in val_tunggakan])
        selected_tunggakan = st.sidebar.selectbox("Masa Tunggakan:", tunggakan_list)
    else:
        selected_tunggakan = "Semua Kelompok"

    if col_hp_name and col_hp_name in df.columns:
        val_hp = df[col_hp_name].dropna().unique()
        hp_list = ["Semua Status HP"] + sorted([str(x) for x in val_hp])
        selected_hp = st.sidebar.selectbox("Status HP:", hp_list)
    else:
        selected_hp = "Semua Status HP"

    if 'status_bayar' in df.columns:
        val_bayar = df['status_bayar'].dropna().unique()
        bayar_list = ["Semua Status Bayar"] + sorted([str(x) for x in val_bayar])
        selected_bayar = st.sidebar.selectbox("Status Pembayaran:", bayar_list)
    else:
        selected_bayar = "Semua Status Bayar"

    if 'status_tindak_lanjut' in df.columns:
        val_tl = df['status_tindak_lanjut'].dropna().unique()
        tl_list = ["Semua Status TL"] + sorted([str(x) for x in val_tl])
        selected_tl = st.sidebar.selectbox("Status Tindak Lanjut:", tl_list)
    else:
        selected_tl = "Semua Status TL"

    if 'pemilik_jenis' in df.columns:
        val_pemilik = df['pemilik_jenis'].dropna().unique()
        pemilik_list = ["Semua Jenis Pemilik"] + sorted([str(x) for x in val_pemilik])
        selected_pemilik = st.sidebar.selectbox("Jenis Pemilik:", pemilik_list)
    else:
        selected_pemilik = "Semua Jenis Pemilik"

    # FITUR BARU: Filter Jenis Kendaraan
    if 'kode_jenis_kendaraan_deskripsi' in df.columns:
        val_jenis = df['kode_jenis_kendaraan_deskripsi'].dropna().unique()
        jenis_list = ["Semua Jenis Kendaraan"] + sorted([str(x) for x in val_jenis])
        selected_jenis = st.sidebar.selectbox("Jenis Kendaraan:", jenis_list)
    else:
        selected_jenis = "Semua Jenis Kendaraan"

    cari_kata = st.sidebar.text_input("Cari Plat / Nama:")

    # 4. Terapkan Filter
    df_filtered = df.copy()
    
    if selected_cabang != "Semua Cabang / Wilayah" and 'nama_cabang' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['nama_cabang'] == selected_cabang]
        
    if selected_samsat != "Semua Samsat" and 'nama_samsat' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['nama_samsat'] == selected_samsat]
        
    if selected_tunggakan != "Semua Kelompok" and 'kelompok_selisih_hari_tunggakan' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['kelompok_selisih_hari_tunggakan'] == selected_tunggakan]
        
    if selected_hp != "Semua Status HP" and col_hp_name and col_hp_name in df_filtered.columns:
        df_filtered = df_filtered[df_filtered[col_hp_name] == selected_hp]
        
    if selected_bayar != "Semua Status Bayar" and 'status_bayar' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status_bayar'] == selected_bayar]

    if selected_tl != "Semua Status TL" and 'status_tindak_lanjut' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status_tindak_lanjut'] == selected_tl]

    if selected_pemilik != "Semua Jenis Pemilik" and 'pemilik_jenis' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['pemilik_jenis'] == selected_pemilik]
        
    # FITUR BARU: Terapkan Filter Jenis Kendaraan
    if selected_jenis != "Semua Jenis Kendaraan" and 'kode_jenis_kendaraan_deskripsi' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['kode_jenis_kendaraan_deskripsi'] == selected_jenis]
        
    if cari_kata:
        cond_plat = df_filtered['no_polisi'].astype(str).str.contains(cari_kata, case=False, na=False) if 'no_polisi' in df_filtered.columns else False
        cond_nama = df_filtered['nama_pemilik_terakhir'].astype(str).str.contains(cari_kata, case=False, na=False) if 'nama_pemilik_terakhir' in df_filtered.columns else False
        df_filtered = df_filtered[cond_plat | cond_nama]

    # 5. Hitung Metrik KPI
    total_kendaraan = len(df_filtered)
    
    if col_hp_name and col_hp_name in df_filtered.columns:
        hp_valid = len(df_filtered[df_filtered[col_hp_name].astype(str).str.upper() == 'VALID'])
    else:
        hp_valid = 0
        
    if total_kendaraan > 0:
        persen_hp_valid = (hp_valid / total_kendaraan) * 100
    else:
        persen_hp_valid = 0.0

    # LOGIKA PERHITUNGAN STATUS
    if 'status_bayar' in df_filtered.columns and 'status_tindak_lanjut' in df_filtered.columns:
        s_bayar = df_filtered['status_bayar'].astype(str).str.strip().str.upper()
        s_tl = df_filtered['status_tindak_lanjut'].astype(str).str.strip().str.upper()

        cond_blm_lunas = s_bayar.str.contains('BELUM LUNAS|BELUM BAYAR|BLM BAYAR', na=False)
        cond_lunas = s_bayar.str.contains('LUNAS|SUDAH BAYAR|SDH BAYAR', na=False) & ~cond_blm_lunas

        cond_sdh_tl = s_tl.str.contains('SUDAH DITINDAKLANJUTI|SUDAH TL|SDH TL', na=False)
        cond_blm_tl = s_tl.str.contains('BELUM DITINDAKLANJUTI|BELUM TL|BLM TL', na=False) & ~cond_sdh_tl

        jml_lunas = len(df_filtered[cond_lunas])
        jml_belum_lunas = len(df_filtered[cond_blm_lunas])

        jml_blm_lunas_sdh_tl = len(df_filtered[cond_blm_lunas & cond_sdh_tl])
        jml_lunas_blm_tl = len(df_filtered[cond_lunas & cond_blm_tl])
        jml_blm_lunas_blm_tl = len(df_filtered[cond_blm_lunas & cond_blm_tl])
        jml_lunas_sdh_tl = len(df_filtered[cond_lunas & cond_sdh_tl]) 
        
        total_sdh_tl = len(df_filtered[cond_sdh_tl])
        if total_sdh_tl > 0:
            conversion_rate = (jml_lunas_sdh_tl / total_sdh_tl) * 100
        else:
            conversion_rate = 0.0
    else:
        jml_lunas = 0
        jml_belum_lunas = 0
        jml_blm_lunas_sdh_tl = 0
        jml_lunas_blm_tl = 0
        jml_blm_lunas_blm_tl = 0
        jml_lunas_sdh_tl = 0
        conversion_rate = 0.0

    if total_kendaraan > 0:
        persen_lunas = (jml_lunas / total_kendaraan) * 100
        persen_belum_lunas = (jml_belum_lunas / total_kendaraan) * 100
    else:
        persen_lunas = 0.0
        persen_belum_lunas = 0.0

    # 6. Tampilan KPI Cards
    st.subheader(f"Ringkasan Indikator Utama ({selected_cabang})")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Kendaraan", f"{total_kendaraan:,} Unit")
    c2.metric("Nomor HP Valid", f"{hp_valid:,} Unit")
    c3.metric("Rasio HP Valid", f"{persen_hp_valid:.1f}%")
    c4.metric("Efektivitas TL", f"{conversion_rate:.1f}%")

    st.markdown("---")

    st.subheader("Analisis Pembayaran & Status TL")
    # Menggunakan 5 Kolom agar Lunas Sudah TL bisa ditambahkan berdampingan
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Kendaraan Lunas", f"{jml_lunas:,} Unit", f"{persen_lunas:.1f}%")
    m2.metric("Kendaraan Belum Lunas", f"{jml_belum_lunas:,} Unit", f"{persen_belum_lunas:.1f}%", delta_color="inverse")
    m3.metric("Lunas Sudah TL", f"{jml_lunas_sdh_tl:,} Unit") 
    m4.metric("Lunas Belum TL", f"{jml_lunas_blm_tl:,} Unit")
    m5.metric("Belum Lunas Sudah TL", f"{jml_blm_lunas_sdh_tl:,} Unit")

    if jml_blm_lunas_blm_tl > 0:
        st.warning(f"Beban Kerja: Terdapat {jml_blm_lunas_blm_tl:,} Unit belum lunas & belum TL.")

    st.markdown("---")

    # 7. Visualisasi Grafis
    st.subheader("Visualisasi Grafis")
    
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

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.markdown("##### Distribusi Masa Tunggakan")
        if not df_filtered.empty and 'kelompok_selisih_hari_tunggakan' in df_filtered.columns:
            tunggakan_counts = df_filtered['kelompok_selisih_hari_tunggakan'].value_counts().reset_index()
            tunggakan_counts.columns = ['Masa Tunggakan', 'Jumlah']
            fig_pie = px.pie(
                tunggakan_counts, 
                values='Jumlah', 
                names='Masa Tunggakan', 
                hole=0.35, 
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with row2_col2:
        st.markdown("##### Sebaran Jenis Kepemilikan")
        if not df_filtered.empty and 'pemilik_jenis' in df_filtered.columns:
            pemilik_counts = df_filtered['pemilik_jenis'].value_counts().reset_index()
            pemilik_counts.columns = ['Jenis Pemilik', 'Jumlah']
            fig_donut = px.pie(
                pemilik_counts, 
                values='Jumlah', 
                names='Jenis Pemilik', 
                hole=0.4, 
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            st.plotly_chart(fig_donut, use_container_width=True)

    st.markdown("---")

    # FITUR BARU: Matriks Jenis Kendaraan
    st.subheader("Matriks Jenis Kendaraan")
    if not df_filtered.empty and 'kode_jenis_kendaraan_deskripsi' in df_filtered.columns:
        df_jenis = df_filtered['kode_jenis_kendaraan_deskripsi'].value_counts().reset_index()
        df_jenis.columns = ['Jenis Kendaraan', 'Jumlah Unit']
        st.dataframe(df_jenis, use_container_width=True, hide_index=True)
    else:
        st.info("Data jenis kendaraan tidak ditemukan.")

    st.markdown("---")

    # 8. Tabel Detail Data
    st.subheader("Tabel Detail Kendaraan")
    st.info("Tips: Klik judul kolom untuk mengurutkan (sort) data.")
    
    kolom_tampilan = [c for c in [
        'no_polisi', 'nama_pemilik_terakhir', 'pemilik_jenis', 'nama_samsat', 'nama_cabang', 
        'kode_jenis_kendaraan_deskripsi', 'tgl_mati_yad', 'nomor_hp', 
        'kelompok_selisih_hari_tunggakan', 'status_nomor_hp_valid', 'flag_nomor_hp_valid',
        'status_tindak_lanjut', 'status_bayar', 'prioritas'
    ] if c in df_filtered.columns]
    
    st.dataframe(df_filtered[kolom_tampilan], use_container_width=True)
    
    csv_data = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Hasil Filter (.CSV)",
        data=csv_data,
        file_name="data_tunggakan_filtered.csv",
        mime="text/csv"
    )
