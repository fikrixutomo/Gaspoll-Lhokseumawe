import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import io

# 1. Konfigurasi Tampilan
st.set_page_config(
    page_title="Dashboard Analisis Tunggakan - JR Lhokseumawe",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Dashboard Analisis Tunggakan Kendaraan — JR Lhokseumawe")

# 2. Pemuatan Data Aman (Anti Bad Lines & Auto Separator)
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
    st.error("⚠️ File CSV tidak ditemukan atau gagal dibaca.")
else:
    # Tentukan nama kolom pemilik/instansi secara dinamis
    col_perusahaan = 'nama_pemilik_terakhir' if 'nama_pemilik_terakhir' in df.columns else 'nama_instansi' if 'nama_instansi' in df.columns else None

    # 3. Sidebar Filter Utama
    st.sidebar.header("🔍 Filter Data")
    
    # Filter Cabang / Wilayah
    if 'nama_cabang' in df.columns:
        val_cabang = ["Semua Cabang / Wilayah"] + sorted([str(x) for x in df['nama_cabang'].dropna().unique()])
        selected_cabang = st.sidebar.selectbox("Pilih Cabang / Wilayah:", val_cabang)
    else:
        selected_cabang = "Semua Cabang / Wilayah"

    # Filter Jenis Pemilik
    if 'pemilik_jenis' in df.columns:
        val_pemilik = ["Semua Jenis Pemilik"] + sorted([str(x) for x in df['pemilik_jenis'].dropna().unique()])
        selected_pemilik = st.sidebar.selectbox("Jenis Pemilik:", val_pemilik)
    else:
        selected_pemilik = "Semua Jenis Pemilik"

    # Filter Nama Pemilik / Instansi
    if col_perusahaan:
        val_nama = ["Semua Nama Pemilik"] + sorted([str(x) for x in df[col_perusahaan].dropna().unique()])
        selected_nama = st.sidebar.selectbox("Nama Pemilik / Instansi:", val_nama)
    else:
        selected_nama = "Semua Nama Pemilik"

    # Filter Status Pembayaran (Lunas / Belum Lunas)
    if 'status_bayar' in df.columns:
        val_status = ["Semua Status Bayar"] + sorted([str(x) for x in df['status_bayar'].dropna().unique()])
        selected_status = st.sidebar.selectbox("Status Pembayaran:", val_status)
    else:
        selected_status = "Semua Status Bayar"

    # Filter Status Kunjungan / Tindak Lanjut
    if 'status_tindak_lanjut' in df.columns:
        val_tl = ["Semua Status Kunjungan"] + sorted([str(x) for x in df['status_tindak_lanjut'].dropna().unique()])
        selected_tl = st.sidebar.selectbox("Status Kunjungan / TL:", val_tl)
    else:
        selected_tl = "Semua Status Kunjungan"

    cari_kata = st.sidebar.text_input("Cari No. Polisi / Nama:")

    # 4. Terapkan Filter
    df_filtered = df.copy()
    
    if selected_cabang != "Semua Cabang / Wilayah" and 'nama_cabang' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['nama_cabang'] == selected_cabang]
    if selected_pemilik != "Semua Jenis Pemilik" and 'pemilik_jenis' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['pemilik_jenis'].astype(str) == selected_pemilik]
    if selected_nama != "Semua Nama Pemilik" and col_perusahaan:
        df_filtered = df_filtered[df_filtered[col_perusahaan].astype(str) == selected_nama]
    if selected_status != "Semua Status Bayar" and 'status_bayar' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status_bayar'].astype(str) == selected_status]
    if selected_tl != "Semua Status Kunjungan" and 'status_tindak_lanjut' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status_tindak_lanjut'].astype(str) == selected_tl]
        
    if cari_kata:
        cond_plat = df_filtered['no_polisi'].astype(str).str.contains(cari_kata, case=False, na=False) if 'no_polisi' in df_filtered.columns else False
        cond_nama = df_filtered[col_perusahaan].astype(str).str.contains(cari_kata, case=False, na=False) if col_perusahaan else False
        df_filtered = df_filtered[cond_plat | cond_nama]

    # 5. Hitung Metrik & KPI
    total_kendaraan = len(df_filtered)
    
    if 'status_bayar' in df_filtered.columns:
        s_bayar = df_filtered['status_bayar'].astype(str).str.strip().str.upper()
        jml_lunas = len(df_filtered[s_bayar.str.contains('LUNAS|SUDAH BAYAR|SDH BAYAR', na=False)])
        jml_belum_lunas = len(df_filtered[s_bayar.str.contains('BELUM LUNAS|BELUM BAYAR|BLM BAYAR', na=False)])
    else:
        jml_lunas = jml_belum_lunas = 0

    persen_lunas = (jml_lunas / total_kendaraan * 100) if total_kendaraan > 0 else 0.0
    persen_belum_lunas = (jml_belum_lunas / total_kendaraan * 100) if total_kendaraan > 0 else 0.0

    # 6. Tampilan KPI Cards
    st.subheader(f"📊 Ringkasan Indikator Utama ({selected_cabang})")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Kendaraan", f"{total_kendaraan:,} Unit")
    c2.metric("Kendaraan Lunas", f"{jml_lunas:,} Unit", f"{persen_lunas:.1f}%")
    c3.metric("Kendaraan Belum Lunas", f"{jml_belum_lunas:,} Unit", f"{persen_belum_lunas:.1f}%", delta_color="inverse")
    c4.metric("Status Kunjungan", selected_tl if selected_tl != "Semua Status Kunjungan" else "Semua")

    st.markdown("---")

    # 7. MATRIKS TAMBAHAN: GOLONGAN & JENIS PEMILIK
    st.subheader("📌 Matriks Detail: Jumlah Kendaraan, Golongan & Jenis Pemilik")
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.markdown("##### Ringkasan Berdasarkan Jenis Golongan")
        if not df_filtered.empty and 'kode_golongan' in df_filtered.columns:
            gol_col = 'kode_golongan_deskripsi' if 'kode_golongan_deskripsi' in df_filtered.columns else 'kode_golongan'
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

    # 8. Tabel Detail Data
    st.subheader("📋 Tabel Detail Kendaraan")
    st.info("Tips: Klik judul kolom untuk mengurutkan (sort) data.")
    
    kolom_tampilan = [c for c in [
        'no_polisi', 'nama_pemilik_terakhir', 'pemilik_jenis', 'nama_samsat', 'nama_cabang', 
        'kode_golongan', 'kode_jenis_kendaraan_deskripsi', 'tgl_mati_yad', 'nomor_hp', 
        'kelompok_selisih_hari_tunggakan', 'status_tindak_lanjut', 'status_bayar', 'prioritas'
    ] if c in df_filtered.columns]
    
    st.dataframe(df_filtered[kolom_tampilan], use_container_width=True)
    
    # 9. Tombol Download (Excel & CSV Saja)
    st.markdown("### 📥 Download Hasil Filter Data")
    dl1, dl2 = st.columns(2)
    
    with dl1:
        try:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_filtered.to_excel(writer, index=False, sheet_name='Data_JR_Lhokseumawe')
            st.download_button(
                label="📊 Download File Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name="Hasil_Filter_JR_Lhokseumawe.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception:
            st.warning("Pustaka 'openpyxl' diperlukan untuk ekspor Excel. Jalankan `pip install openpyxl`.")
            
    with dl2:
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download File CSV (.csv)",
            data=csv_data,
            file_name="Hasil_Filter_JR_Lhokseumawe.csv",
            mime="text/csv"
        )

# --- FOOTER / COPYRIGHT ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>© 2026 JRLX Fikri Jasaraharja Lhokseumawe. All rights reserved.</p>",
    unsafe_allow_html=True
)
