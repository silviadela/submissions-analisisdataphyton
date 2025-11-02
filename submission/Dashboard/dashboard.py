import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob
import warnings

# Konfigurasi untuk menghilangkan warning
warnings.filterwarnings('ignore')

# Konfigurasi halaman
st.set_page_config(
    page_title="Dashboard Analisis Kualitas Udara Beijing",
    layout="wide",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

st.title("Dashboard Analisis Data - Kualitas Udara Beijing")

# =========================================================
# 0. LOAD DATA
# =========================================================
@st.cache_data(show_spinner=False)
def load_data():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        main_data_path = os.path.join(script_dir, "main_data.csv")
        
        if os.path.exists(main_data_path):
            df = pd.read_csv(main_data_path)
        else:
            # Kalau belum ada, buat dari data PRSA
            data_dir = os.path.join(os.path.dirname(script_dir), "PRSA_Data_20130301-20170228")
            csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
            
            if not csv_files:
                st.error("❌ Tidak ada file CSV di folder PRSA_Data_20130301-20170228")
                st.stop()
                
            # Baca dan gabungkan semua file CSV
            dfs = []
            for file in csv_files:
                filename = os.path.basename(file)
                station = filename.replace("PRSA_Data_", "").split("_")[0]
                df = pd.read_csv(file)
                df['station'] = station
                dfs.append(df)
            
            # Gabungkan semua data dan simpan
            df = pd.concat(dfs, ignore_index=True)
            df.to_csv(main_data_path, index=False)
        
        # Bikin kolom datetime
        if {"year", "month", "day", "hour"}.issubset(df.columns):
            df["datetime"] = pd.to_datetime(df[["year", "month", "day", "hour"]])
        elif {"year", "month", "day"}.issubset(df.columns):
            df["datetime"] = pd.to_datetime(df[["year", "month", "day"]])
        else:
            df["datetime"] = pd.to_datetime(df.iloc[:, 0], errors="coerce")
            
        return df
    except Exception as e:
        st.error(f"❌ Error saat memuat data: {str(e)}")
        st.stop()


df = load_data()
if df is None:
    st.error("❌ Tidak menemukan `main_data.csv`. Jalankan script penggabung datamu dulu.")
    st.stop()

# daftar kolom
pollutant_cols = [c for c in ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3"] if c in df.columns]

# =========================================================
# 1. METRICS HEADER
# =========================================================
col1, col2 = st.columns(2)

with col1:
    st.metric("Jumlah Record", f"{len(df):,}")
with col2:
    if "station" in df.columns:
        st.metric("Lokasi Aktif", df["station"].nunique())
    else:
        st.metric("Lokasi Aktif", "-")

st.caption("*Ganti filter di kiri supaya metrik dan grafik ikut menyesuaikan*")

# =========================================================
# 2. SIDEBAR FILTER
# =========================================================
st.sidebar.header("🔎 Filter Data")

stations = df["station"].unique().tolist() if "station" in df.columns else []
selected_station = st.sidebar.selectbox("Pilih stasiun (optional):", ["Semua"] + stations)

min_date = df["datetime"].min()
max_date = df["datetime"].max()
date_range = st.sidebar.date_input(
    "Rentang waktu:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# terapkan filter
fdf = df.copy()
if selected_station != "Semua" and "station" in df.columns:
    fdf = fdf[fdf["station"] == selected_station]

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    fdf = fdf[
        (fdf["datetime"] >= pd.to_datetime(start_date)) &
        (fdf["datetime"] <= pd.to_datetime(end_date))
    ]

if fdf.empty:
    st.warning("Data kosong setelah difilter.")
    st.stop()

# =========================================================
# 3. TABS (tanpa korelasi)
# =========================================================
tab1, tab2, tab3 = st.tabs([
    "📈 Tren Polutan",
    "🍂 Polutan per Musim",
    "🏙️ Kategori per Stasiun (Baik / Sedang / Buruk)",
])

# =========================================================
# TAB 1 - TREN POLUTAN
# =========================================================
with tab1:
    st.subheader("Tren Perubahan Polutan Udara (Rata-rata Bulanan)")

    # resample bulanan
    month_df = (
        fdf.set_index("datetime")[pollutant_cols]
        .resample("M")
        .mean()
        .reset_index()
    )

    pilih_polutan = st.multiselect(
        "Pilih polutan yang ingin ditampilkan:",
        options=pollutant_cols,
        default=pollutant_cols[:4],
        key="multiselect_tab1"
    )

    fig, ax = plt.subplots(figsize=(12, 4))
    for col in pilih_polutan:
        ax.plot(month_df["datetime"], month_df[col], label=col)
    ax.set_title("Tren Perubahan Polutan Udara (Rata-rata Bulanan)")
    ax.set_xlabel("Waktu (tahun)")
    ax.set_ylabel("Konsentrasi (µg/m³)")
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)

# =========================================================
# TAB 2 - POLUTAN PER MUSIM (INTERAKTIF)
# =========================================================
with tab2:
    st.subheader("Rata-rata Konsentrasi Polutan per Musim")

    # buat kolom musim
    fdf["month_num"] = fdf["datetime"].dt.month

    def to_season(m):
        if m in [12, 1, 2]:
            return "Winter"
        elif m in [3, 4, 5]:
            return "Spring"
        elif m in [6, 7, 8]:
            return "Summer"
        else:
            return "Autumn"

    fdf["season"] = fdf["month_num"].apply(to_season)
    season_order = ["Winter", "Spring", "Summer", "Autumn"]

    # pilih musim
    musim = st.selectbox("Pilih musim:", options=season_order, index=0)

    # pilih polutan yang akan ditampilkan
    polutan_pilihan = st.multiselect(
        "Pilih polutan yang ingin ditampilkan:",
        options=["PM2.5", "PM10", "SO2", "NO2", "CO", "O3"],
        default=["PM2.5", "PM10", "SO2", "NO2", "CO", "O3"],
        key="multiselect_tab2"
    )

    # keterangan bulan per musim
    musim_ke_bulan = {
        "Winter": "Desember - Januari - Februari",
        "Spring": "Maret - April - Mei",
        "Summer": "Juni - Juli - Agustus",
        "Autumn": "September - Oktober - November",
    }
    st.info(f"📅 Musim **{musim}** mencakup bulan: **{musim_ke_bulan[musim]}**")

    # hitung rata-rata per musim
    season_mean = (
        fdf.groupby("season")[["PM2.5", "PM10", "SO2", "NO2", "CO", "O3"]]
        .mean()
        .reindex(season_order)
    )

    if musim not in season_mean.index or season_mean.loc[musim].isna().all():
        st.warning("⚠️ Data untuk musim ini kosong setelah filter.")
    else:
        selected_row = season_mean.loc[musim].dropna()
        selected_row = selected_row[selected_row.index.isin(polutan_pilihan)]

        fig, ax = plt.subplots(figsize=(8, 4))
        bars = selected_row.plot(
            kind="bar",
            ax=ax,
            color=["#9ecae1", "#6baed6", "#3182bd", "#08519c"][:len(selected_row)]
        )
        ax.set_title(f"Konsentrasi Rata-rata Polutan pada Musim {musim}")
        ax.set_ylabel("Konsentrasi (µg/m³)")
        ax.set_xlabel("Jenis Polutan")

        # buat agar teks tidak nabrak
        max_val = selected_row.max()
        ax.set_ylim(0, max_val * 1.2)

        # tampilkan nilai di atas batang
        for i, v in enumerate(selected_row.values):
            if v > 0:
                ax.text(
                    i,
                    v + (max_val * 0.03),
                    f"{v:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    fontweight="bold"
                )

        st.pyplot(fig)

    st.markdown(
        """
        **Interpretasi cepat:**
        - ❄️ *Winter* cenderung memiliki polutan tertinggi (efek pemanas & udara dingin).
        - 🌞 *Summer* biasanya paling rendah karena sirkulasi udara lebih baik.
        """
    )
# =========================================================
# TAB 3 - KATEGORI PER STASIUN (BAIK / SEDANG / BURUK)
# =========================================================
with tab3:
    st.subheader("🏙️ Kategori Polutan per Stasiun")

    if "station" not in fdf.columns:
        st.warning("Dataset tidak memiliki kolom `station`.")
    else:
        # ambil rata-rata per stasiun dari data yang sudah difilter
        by_station = (
            fdf.groupby("station")[["PM2.5", "PM10", "SO2", "NO2", "CO", "O3"]]
            .mean()
            .reset_index()
        )

        # pilih stasiun
        stasiun_pilihan = st.selectbox(
            "Pilih stasiun untuk dilihat detail kategorinya:",
            options=by_station["station"].tolist()
        )

        # pilih polutan yang ingin ditampilkan
        polutan_tab3 = st.multiselect(
            "Pilih polutan yang ingin ditampilkan:",
            options=["PM2.5", "PM10", "SO2", "NO2", "CO", "O3"],
            default=["PM2.5", "PM10", "SO2", "NO2", "CO", "O3"],
            key="multiselect_tab3"
        )

        row = by_station[by_station["station"] == stasiun_pilihan].iloc[0]

        # fungsi kategori
        def cat_pm25(v):
            if v <= 35: return "Baik"
            elif v <= 75: return "Sedang"
            else: return "Buruk"

        def cat_pm10(v):
            if v <= 50: return "Baik"
            elif v <= 150: return "Sedang"
            else: return "Buruk"

        def cat_co(v):
            if v <= 1000: return "Baik"
            elif v <= 1500: return "Sedang"
            else: return "Buruk"

        def cat_no2(v):
            if v <= 40: return "Baik"
            elif v <= 80: return "Sedang"
            else: return "Buruk"
            
        def cat_so2(v):
            if v <= 40: return "Baik"
            elif v <= 80: return "Sedang"
            else: return "Buruk"
            
        def cat_o3(v):
            if v <= 100: return "Baik"
            elif v <= 150: return "Sedang"
            else: return "Buruk"

        cat_dict = {}
        if "PM2.5" in row: cat_dict["PM2.5"] = (row["PM2.5"], cat_pm25(row["PM2.5"]))
        if "PM10" in row: cat_dict["PM10"] = (row["PM10"], cat_pm10(row["PM10"]))
        if "CO" in row: cat_dict["CO"] = (row["CO"], cat_co(row["CO"]))
        if "NO2" in row: cat_dict["NO2"] = (row["NO2"], cat_no2(row["NO2"]))
        if "SO2" in row: cat_dict["SO2"] = (row["SO2"], cat_so2(row["SO2"]))
        if "O3" in row: cat_dict["O3"] = (row["O3"], cat_o3(row["O3"]))

        # tampilkan metric hanya untuk polutan yang dipilih
        cols = st.columns(len(polutan_tab3))
        idx = 0
        for pol, (val, cat) in cat_dict.items():
            if pol not in polutan_tab3:
                continue
            with cols[idx]:
                st.metric(f"{pol} ({cat})", f"{val:.2f}")
            idx += 1

        st.markdown("📋 **Keterangan kategori:**")
        st.markdown(
            """
            -  **Baik** → masih di bawah ambang aman.  
            -  **Sedang** → perlu pemantauan (aktivitas harian bisa berpengaruh).  
            -  **Buruk** → butuh perhatian (biasanya musim dingin/lalu lintas padat).
            """
        )

        # grafik horizontal bandingan antar stasiun
        fig, axes = plt.subplots(3, 2, figsize=(12, 9))
        fig.suptitle("Rata-rata Polutan per Stasiun")

        def barh_if_selected(ax, col, title):
            if col in by_station.columns and col in polutan_tab3:
                ax.barh(by_station["station"], by_station[col], color="#6baed6")
                ax.set_title(title)
                ax.set_xlabel("Konsentrasi rata-rata (µg/m³)")
                ax.set_ylabel("Stasiun")
            else:
                ax.axis("off")

        barh_if_selected(axes[0, 0], "PM2.5", "PM2.5 per Stasiun")
        barh_if_selected(axes[0, 1], "PM10", "PM10 per Stasiun")
        barh_if_selected(axes[1, 0], "SO2", "SO₂ per Stasiun")
        barh_if_selected(axes[1, 1], "NO2", "NO₂ per Stasiun")
        barh_if_selected(axes[2, 0], "CO", "CO per Stasiun")
        barh_if_selected(axes[2, 1], "O3", "O₃ per Stasiun")

        plt.tight_layout()
        st.pyplot(fig)
