import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import io

# 1. Konfigurasi Halaman
st.set_page_config(
    page_title="Dashboard Instansi & Perusahaan - GASPOL",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Dashboard Analisis Tunggakan Instansi & Perusahaan")
st.markdown("Aplikasi monitoring kepatuhan pajak kendaraan khusus instansi, perusahaan, dan badan usaha.")

# 2. Pemuatan Data Aman
@st.cache_data(ttl=600)
def load_and_combine_data():
    file_list = glob.glob("*.csv")
    file_list = [f for f in file_list if "Kode Plat" not in f and "Query result" not in f and "filtered" not in f]
    
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
    st.error("⚠️ File CSV data instansi tidak ditemukan! Pastikan file tersimpan di folder yang sama dengan app.py.")
else:
    col_perusahaan = 'nama_pemilik_terakhir' if 'nama_pemilik_terakhir' in df.columns else 'nama_instansi' if 'nama_instansi' in df.columns else None
    col_hp_name = 'flag_nomor_hp_valid' if 'flag_nomor_hp_valid' in df.columns else 'status_nomor_hp_valid' if 'status_nomor_hp_valid' in df.columns else None

    # 3. SIDEBAR - FILTER DATA
    st.sidebar.header("🔍 Filter Instansi & Perusahaan")
    
    if 'nama_cabang' in df.columns:
        val_cabang = ["Semua Cabang / Wilayah"] + sorted([str(x) for x in df['nama_cabang'].dropna().unique()])
        selected_cabang = st.sidebar.selectbox("Pilih Cabang / Wilayah:", val_cabang)
    else:
        selected_cabang = "Semua Cabang / Wilayah"

    if col_perusahaan:
        val_perusahaan = ["Semua Instansi / Perusahaan"] + sorted([str(x) for x in df[col_perusahaan].dropna().unique()])
        selected_perusahaan = st.sidebar.selectbox("Pilih Nama Instansi / Perusahaan:", val_perusahaan)
    else:
        selected_perusahaan = "Semua Instansi / Perusahaan"

    if 'pemilik_jenis' in df.columns:
        val_pemilik = ["Semua Jenis Pemilik"] + sorted([str(x) for x in df['pemilik_jenis'].dropna().unique()])
        selected_pemilik = st.sidebar.selectbox("Jenis Pemilik (PT/Instansi/Pemerintah):", val_pemilik)
    else:
        selected_pemilik = "Semua Jenis Pemilik"

    if 'status_bayar' in df.columns:
        val_bayar = ["Semua Status Bayar"] + sorted([str(x) for x in df['status_bayar'].dropna().unique()])
        selected_bayar = st.sidebar.selectbox("Status Pembayaran:", val_bayar)
    else:
        selected_bayar = "Semua Status Bayar"

    if 'status_tindak_lanjut' in df.columns:
        val_tl = ["Semua Status Kunjungan"] + sorted([str(x) for x in df['status_tindak_lanjut'].dropna().unique()])
        selected_tl = st.sidebar.selectbox("Status Kunjungan / TL:", val_tl)
    else:
        selected_tl = "Semua Status Kunjungan"

    cari_kata = st.sidebar.text_input("Cari No. Polisi / Nama Pemilik:")

    # 4. TERAPKAN FILTER
    df_filtered = df.copy()
    
    if selected_cabang != "Semua Cabang / Wilayah" and 'nama_cabang' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['nama_cabang'] == selected_cabang]
    if selected_perusahaan != "Semua Instansi / Perusahaan" and col_perusahaan:
        df_filtered = df_filtered[df_filtered[col_perusahaan].astype(str) == selected_perusahaan]
    if selected_pemilik != "Semua Jenis Pemilik" and 'pemilik_jenis' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['pemilik_jenis'].astype(str) == selected_pemilik]
    if selected_bayar != "Semua Status Bayar" and 'status_bayar' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status_bayar'].astype(str) == selected_bayar]
    if selected_tl != "Semua Status Kunjungan" and 'status_tindak_lanjut' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status_tindak_lanjut'].astype(str) == selected_tl]
    if cari_kata:
        cond_plat = df_filtered['no_polisi'].astype(str).str.contains(cari_kata, case=False, na=False) if 'no_polisi' in df_filtered.columns else False
        cond_nama = df_filtered[col_perusahaan].astype(str).str.contains(cari_kata, case=False, na=False) if col_perusahaan else False
        df_filtered = df_filtered[cond_plat | cond_nama]

    # 5. PERHITUNGAN MATRIKS
    total_kendaraan = len(df_filtered)
    hp_valid = len(df_filtered[df_filtered[col_hp_name].astype(str).str.upper() == 'VALID']) if col_hp_name else 0
    persen_hp = (hp_valid / total_kendaraan * 100) if total_kendaraan > 0 else 0.0

    if 'status_bayar' in df_filtered.columns and 'status_tindak_lanjut' in df_filtered.columns:
        s_bayar = df_filtered['status_bayar'].astype(str).str.strip().str.upper()
        s_tl = df_filtered['status_tindak_lanjut'].astype(str).str.strip().str.upper()

        cond_blm_lunas = s_bayar.str.contains('BELUM LUNAS|BELUM BAYAR|BLM BAYAR', na=False)
        cond_lunas = s_bayar.str.contains('LUNAS|SUDAH BAYAR|SDH BAYAR', na=False) & ~cond_blm_lunas
        cond_sdh_tl = s_tl.str.contains('SUDAH DITINDAKLANJUTI|SUDAH DIKUNJUNGI|SUDAH TL|SDH TL', na=False)
        
        jml_lunas = len(df_filtered[cond_lunas])
        jml_belum_lunas = len(df_filtered[cond_blm_lunas])
        jml_lunas_sdh_tl = len(df_filtered[cond_lunas & cond_sdh_tl])
        total_sdh_tl = len(df_filtered[cond_sdh_tl])
        conversion_rate = (jml_lunas_sdh_tl / total_sdh_tl * 100) if total_sdh_tl > 0 else 0.0
    else:
        jml_lunas = jml_belum_lunas = 0
        conversion_rate = 0.0

    # 6. TAMPILAN MATRIKS KPI UTAMA
    st.subheader(f"📊 Ringkasan Indikator Instansi & Perusahaan ({selected_cabang})")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Kendaraan", f"{total_kendaraan:,} Unit")
    c2.metric("Kendaraan Lunas", f"{jml_lunas:,} Unit")
    c3.metric("Belum Lunas", f"{jml_belum_lunas:,} Unit", delta_color="inverse")
    c4.metric("Efektivitas Kunjungan", f"{conversion_rate:.1f}%")

    st.markdown("---")

    # 7. MATRIKS JENIS KENDARAAN (FITUR BARU)
    st.subheader("📌 Matriks Ringkasan Berdasarkan Jenis Kendaraan")
    if not df_filtered.empty and 'kode_jenis_kendaraan_deskripsi' in df_filtered.columns:
        df_jenis = df_filtered['kode_jenis_kendaraan_deskripsi'].value_counts().reset_index()
        df_jenis.columns = ['Jenis Kendaraan', 'Total Unit']
        st.dataframe(df_jenis, use_container_width=True, hide_index=True)
    else:
        st.info("Data jenis kendaraan tidak tersedia di file ini.")

    st.markdown("---")

    # 8. TABEL DETAIL DATA
    st.subheader("📋 Tabel Detail Kendaraan Instansi & Perusahaan")
    kolom_tampilan = [c for c in [
        'no_polisi', 'nama_pemilik_terakhir', 'pemilik_jenis', 'nama_samsat', 'nama_cabang', 
        'kode_jenis_kendaraan_deskripsi', 'tgl_mati_yad', 'nomor_hp', 
        'kelompok_selisih_hari_tunggakan', 'status_tindak_lanjut', 'status_bayar', 'prioritas'
    ] if c in df_filtered.columns]
    
    st.dataframe(df_filtered[kolom_tampilan], use_container_width=True)

    # 9. TOMBOL DOWNLOAD (HANYA EXCEL DAN CSV)
    st.markdown("### 📥 Download Hasil Filter Data")
    
    dl1, dl2 = st.columns(2)
    
    with dl1:
        try:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_filtered.to_excel(writer, index=False, sheet_name='Data_Instansi')
            
            st.download_button(
                label="📊 Download File Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name="Hasil_Filter_Instansi.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception:
            st.warning("Pustaka 'openpyxl' diperlukan untuk ekspor Excel.")
            
    with dl2:
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download File CSV (.csv)",
            data=csv_data,
            file_name="Hasil_Filter_Instansi.csv",
            mime="text/csv"
        )
