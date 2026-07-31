# ==========================================
    # 5. PERHITUNGAN METRIK & INDICATOR (KPI)
    # ==========================================
    total_kendaraan = len(df_filtered)
    
    # Deteksi kolom HP Valid secara fleksibel (mencegah KeyError)
    kolom_hp = 'flag_nomor_hp_valid' if 'flag_nomor_hp_valid' in df_filtered.columns else ('status_nomor_hp_valid' if 'status_nomor_hp_valid' in df_filtered.columns else None)
    
    if kolom_hp:
        hp_valid = len(df_filtered[df_filtered[kolom_hp].astype(str).str.upper() == 'VALID'])
    else:
        hp_valid = 0
        
    persen_hp_valid = (hp_valid / total_kendaraan * 100) if total_kendaraan > 0 else 0
