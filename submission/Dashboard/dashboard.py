import streamlit as st
import pandas as pd
import os
import glob
import warnings
import matplotlib.pyplot as plt
import seaborn as sns

# ==== CONFIG PAGE ====
st.set_page_config(
    page_title="Dashboard Analisis Kualitas Udara Beijing",
    layout="wide",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

st.title("Dashboard Analisis Data - Kualitas Udara Beijing")


# =========================================================
# 0. LOAD DATA  (lebih tangguh: cek 2 lokasi)
# =========================================================
@st.cache_data(show_spinner=False)
def load_data():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # 1) cek di folder yang sama dengan dashboard.py
        main_data_path = os.path.join(script_dir, "main_data.csv")

        if not os.path.exists(main_data_path):
            parent_dir = os.path.dirname(script_dir)
            alt_path = os.path.join(parent_dir, "main_data.csv")
            if os.path.exists(alt_path):
                main_data_path = alt_path

        if os.path.exists(main_data_path):
            df = pd.read_csv(main_data_path)
        else:
            # ==== fallback: gabung dari folder PRSA ====
            data_dir = os.path.join(os.path.dirname(script_dir), "PRSA_Data_20130301-20170228")
            csv_files = glob.glob(os.path.join(data_dir, "*.csv"))

            if not csv_files:
                st.error("❌ Tidak ada file CSV di folder PRSA_Data_20130301-20170228")
                st.stop()

            dfs = []
            for file in csv_files:
                filename = os.path.basename(file)
                station = filename.replace("PRSA_Data_", "").split("_")[0]
                tmp = pd.read_csv(file)
                tmp["station"] = station
                dfs.append(tmp)

            df = pd.concat(dfs, ignore_index=True)
            # simpan di folder yang sama dengan dashboard.py
            df.to_csv(main_data_path, index=False)

        # bikin kolom datetime
        if {"year", "month", "day", "hour"}.issubset(df.columns):
            df["datetime"] = pd.to_datetime(df[["year", "month", "day", "hour"]])
        elif {"year", "month", "day"}.issubset(df.columns):
            df["datetime"] = pd.to_datetime(df[["year", "month", "day"]])
        else:
            # fallback: pakai kolom pertama yg mirip tanggal
            df["datetime"] = pd.to_datetime(df.iloc[:, 0], errors="coerce")

        return df
    except Exception as e:
        st.error(f"Error saat memuat data: {e}")
        st.stop()


df = load_data()
if df is None:
    st.error("Tidak menemukan data.")
    st.stop()

# kolom polutan yang benar-benar ada
pollutant_cols = [c for c in ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3"] if c in df.columns]
PRIORITY = ["PM2.5", "PM10", "CO",  "NO2"]
default4 = [c for c in PRIORITY if c in pollutant_cols][:4]

# drop baris yang seluruhnya kosong
df.dropna(how="all", inplace=True)

# pastikan tipe numerik untuk kolom yang dipakai di notebook
_numeric_base = ["year", "month", "day", "hour"]
weather_cols = [c for c in ["TEMP", "PRES", "DEWP", "RAIN", "WSPM"] if c in df.columns]
num_cols = [c for c in (_numeric_base + pollutant_cols + weather_cols) if c in df.columns]
df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")

# isi NaN polutan dengan mean (sesuai notebook)
for c in pollutant_cols:
    df[c].fillna(df[c].mean(), inplace=True)

# isi NaN cuaca/angin dengan mean (sesuai notebook)
for c in weather_cols:
    df[c].fillna(df[c].mean(), inplace=True)

# isi NaN arah angin 'wd' dengan modus jika kolomnya ada (sesuai notebook)
if "wd" in df.columns and df["wd"].isna().any():
    try:
        df["wd"].fillna(df["wd"].mode().iloc[0], inplace=True)
    except Exception:
        pass

# pastikan datetime ada dan valid lalu urutkan
if "datetime" not in df.columns:
    if {"year","month","day","hour"}.issubset(df.columns):
        df["datetime"] = pd.to_datetime(df[["year","month","day","hour"]], errors="coerce")
    elif {"year","month","day"}.issubset(df.columns):
        df["datetime"] = pd.to_datetime(df[["year","month","day"]], errors="coerce")
    else:
        df["datetime"] = pd.to_datetime(df.iloc[:,0], errors="coerce")

df = df.dropna(subset=["datetime"]).copy()
df.sort_values("datetime", inplace=True)

# =========================================================
# 1. METRIC
# =========================================================
col1, col2 = st.columns(2)
with col1:
    st.metric("Jumlah Record", f"{len(df):,}")
with col2:
    st.metric("Lokasi Aktif", df["station"].nunique() if "station" in df.columns else "-")

st.caption("*Ganti filter di sidebar supaya metrik dan grafik ikut menyesuaikan*")

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
    max_value=max_date,
)

fdf = df.copy()
if selected_station != "Semua" and "station" in df.columns:
    fdf = fdf[fdf["station"] == selected_station]

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    start_ts = pd.to_datetime(start_date)

    end_ts = pd.to_datetime(end_date) + pd.Timedelta(days=1)   # hari berikutnya
    fdf = fdf[(fdf["datetime"] >= start_ts) & (fdf["datetime"] < end_ts)]

if fdf.empty:
    st.warning("⚠️ Data kosong setelah difilter.")
    st.stop()

# =========================================================
# 3. TABS
# =========================================================
tab1, tab2, tab3 = st.tabs(
    [
        "📈 Tren Polutan",
        "🍂 Polutan per Musim",
        "🏙️ Kategori per Stasiun (Baik / Sedang / Buruk)",
    ]
)

# =========================================================
# TAB 1
# =========================================================
with tab1:
    st.subheader("Tren Perubahan Polutan Udara (Rata-rata Bulanan)")

    month_df = (
        fdf.set_index("datetime")[pollutant_cols]
        .resample("ME")
        .mean()
        .reset_index()
    )

    pilih_polutan = st.multiselect(
        "Pilih polutan yang ingin ditampilkan:",
        options=pollutant_cols,
        default=default4,
        key="multiselect_tab1",
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
# TAB 2
# =========================================================
with tab2:
    st.subheader("Rata-rata Konsentrasi Polutan per Musim")

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

    season_options = ["Semua musim"] + season_order
    musim = st.selectbox("Pilih musim:", options=season_options, index=0)  # >>> CHANGED (default semua)

    polutan_pilihan = st.multiselect(
        "Pilih polutan yang ingin ditampilkan:",
        options=pollutant_cols,
        default=default4,
        key="multiselect_tab2",
    )

    musim_ke_bulan = {
        "Winter": "Desember - Januari - Februari",
        "Spring": "Maret - April - Mei",
        "Summer": "Juni - Juli - Agustus",
        "Autumn": "September - Oktober - November",
    }

    if musim == "Semua musim":
        st.info("📅 Menampilkan **semua musim**: Winter, Spring, Summer, dan Autumn.")
    else:
        st.info(f"📅 Musim **{musim}** mencakup bulan: **{musim_ke_bulan[musim]}**")

    season_mean = (
        fdf.groupby("season")[pollutant_cols]
        .mean()
        .reindex(season_order)
    )

    def plot_one_season(selected_row, title):
        fig, ax = plt.subplots(figsize=(8, 4))
        selected_row.plot(
            kind="bar",
            ax=ax,
            color=["#9ecae1", "#6baed6", "#3182bd", "#08519c", "#fd8d3c", "#6a51a3"][: len(selected_row)],
        )
        ax.set_title(title)
        ax.set_ylabel("Konsentrasi (µg/m³)")
        ax.set_xlabel("Jenis Polutan")
        max_val = selected_row.max()
        ax.set_ylim(0, max_val * 1.2 if max_val > 0 else 1)

        for i, v in enumerate(selected_row.values):
            ax.text(
                i, v + (max_val * 0.03 if max_val > 0 else 0.03),
                f"{v:.2f}", ha="center", va="bottom", fontsize=10, fontweight="bold",
            )
        st.pyplot(fig)

    # --- render ---
    if musim == "Semua musim":  
        for m in season_order:
            if m not in season_mean.index or season_mean.loc[m].isna().all():
                st.warning(f"⚠️ Data untuk musim {m} kosong setelah filter.")
                continue
            row = season_mean.loc[m].dropna()
            row = row[row.index.isin(polutan_pilihan)]
            plot_one_season(row, f"Konsentrasi Rata-rata Polutan pada Musim {m}")
    else:
        if musim not in season_mean.index or season_mean.loc[musim].isna().all():
            st.warning("⚠️ Data untuk musim ini kosong setelah filter.")
        else:
            selected_row = season_mean.loc[musim].dropna()
            selected_row = selected_row[selected_row.index.isin(polutan_pilihan)]
            plot_one_season(selected_row, f"Konsentrasi Rata-rata Polutan pada Musim {musim}")

    st.markdown(
        """
        **Interpretasi cepat:**
        - ❄️ *Winter* biasanya paling tinggi.
        - 🌞 *Summer* biasanya paling rendah.
        """
    )


# =========================================================
# TAB 3
# =========================================================
with tab3:
    st.subheader("Kategori Polutan per Stasiun")

    if "station" not in fdf.columns:
        st.warning("Dataset tidak punya kolom `station`.")
    else:
        by_station = (
            fdf.groupby("station")[pollutant_cols]
            .mean()
            .reset_index()
        )

        stasiun_pilihan = st.selectbox(
            "Pilih stasiun untuk dilihat detail kategorinya:",
            options=by_station["station"].tolist(),
        )

        polutan_tab3 = st.multiselect(
            "Pilih polutan yang ingin ditampilkan:",
            options=pollutant_cols,
            default=default4,
            key="multiselect_tab3",
        )

        row = by_station[by_station["station"] == stasiun_pilihan].iloc[0]

        # === KATEGORI FUNGSI ===
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

        def cat_so2(v):
            if v <= 40: return "Baik"
            elif v <= 80: return "Sedang"
            else: return "Buruk"

        def cat_o3(v):
            if v <= 100: return "Baik"
            elif v <= 150: return "Sedang"
            else: return "Buruk"

        def cat_no2(v):
            if v <= 40: return "Baik"
            elif v <= 80: return "Sedang"
            else: return "Buruk"

        # === TABEL NILAI DAN KATEGORI ===
        cat_dict = {}
        if "PM2.5" in row: cat_dict["PM2.5"] = (row["PM2.5"], cat_pm25(row["PM2.5"]))
        if "PM10" in row: cat_dict["PM10"] = (row["PM10"], cat_pm10(row["PM10"]))
        if "NO2" in row: cat_dict["NO2"] = (row["NO2"], cat_no2(row["NO2"]))
        if "CO" in row: cat_dict["CO"] = (row["CO"], cat_co(row["CO"]))
        if "O3" in row: cat_dict["O3"] = (row["O3"], cat_o3(row["O3"]))
        if "SO2" in row: cat_dict["SO2"] = (row["SO2"], cat_so2(row["SO2"]))

        cols = st.columns(max(1, len(polutan_tab3)))
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
            - 🟢 **Baik** → masih di bawah ambang aman.  
            - 🟡 **Sedang** → perlu pemantauan.  
            - 🔴 **Buruk** → perlu perhatian.
            """
        )

        fig, axes = plt.subplots(3, 2, figsize=(12, 9))
        fig.suptitle("Rata-rata Polutan per Stasiun")

        def get_color_by_category(value, col):
            if "PM2.5" in col: cat = cat_pm25(value)
            elif "PM10" in col: cat = cat_pm10(value)
            elif "NO2" in col: cat = cat_no2(value)
            elif "CO" in col: cat = cat_co(value)
            elif "SO2" in col: cat = cat_so2(value)
            elif "O3" in col: cat = cat_o3(value)
            else: cat = "Baik"

            if cat == "Baik": return "#4CAF50"   # hijau
            elif cat == "Sedang": return "#FFD700"  # kuning
            else: return "#E74C3C"  # merah

        def barh_if_selected(ax, col, title):
            if col in by_station.columns and col in polutan_tab3:
                tmp = by_station[["station", col]].sort_values(col, ascending=False)
                colors = [get_color_by_category(v, col) for v in tmp[col]]
                ax.barh(tmp["station"], tmp[col], color=colors)
                ax.set_title(title)
                ax.set_xlabel("Konsentrasi rata-rata (µg/m³)")
                ax.set_ylabel("Stasiun")
                ax.grid(axis="x", alpha=0.3)
                ax.invert_yaxis()
            else:
                ax.axis("off")

        barh_if_selected(axes[0, 0], "PM2.5", "PM2.5 per Stasiun")
        barh_if_selected(axes[0, 1], "PM10",  "PM10 per Stasiun")
        barh_if_selected(axes[1, 0], "NO2",   "NO₂ per Stasiun")
        barh_if_selected(axes[1, 1], "CO",    "CO per Stasiun")
        barh_if_selected(axes[2, 0], "O3",    "O₃ per Stasiun")
        barh_if_selected(axes[2, 1], "SO2",   "SO₂ per Stasiun")

        plt.tight_layout()
        plt.show()
        st.pyplot(fig)

