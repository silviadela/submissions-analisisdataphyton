# dashboard.py
# ============================================================
# DASHBOARD STREAMLIT – PROYEK AKHIR ANALISIS DATA (STEAMITE)
# Khusus dataset PRSA_* (Beijing PM2.5) seperti di screenshot kamu
# - Header ada tanda kutip: "year","month","day","hour","PM2.5",...
# - Akan digabung otomatis kalau ada banyak file PRSA_Data_*.csv
# - Kalau sudah ada main_data.csv dan isinya > 0, langsung pakai itu
# ============================================================

import os
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

# Set the path to the PRSA data directory
prsa_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'PRSA_Data_20130301-20170228')

# Get all PRSA CSV files
files = [f for f in os.listdir(prsa_dir) if f.startswith("PRSA_Data_") and f.endswith(".csv")]

if not files:
    print("No PRSA data files found!")
    exit(1)

# Read and combine all files
dfs = []
for f in files:
    file_path = os.path.join(prsa_dir, f)
    print(f"Reading {f}...")
    tmp = pd.read_csv(file_path)
    tmp["source_file"] = f
    dfs.append(tmp)

# Combine all dataframes
df = pd.concat(dfs, ignore_index=True)

# Clean column names
cleaned_cols = []
for c in df.columns:
    c = c.strip().replace('"', "")     # remove quotes
    c = c.replace(" ", "_")            # space to underscore
    c = c.replace(".", "_") 
    c = c.lower()                      # to lowercase
    cleaned_cols.append(c)
df.columns = cleaned_cols

# Convert time columns to numeric
time_cols = ["year", "month", "day", "hour"]
for col in time_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Create timestamp column
df["timestamp"] = pd.to_datetime(
    df[["year", "month", "day", "hour"]],
    errors="coerce"
)

# Set location from station
if "station" in df.columns:
    df["location"] = df["station"]
else:
    df["location"] = "PRSA-Station"

# Save to main_data.csv
output_path = os.path.join(os.path.dirname(__file__), "main_data.csv")
print(f"Saving to {output_path}...")
df.to_csv(output_path, index=False)
print("Done!")

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Analisis Data",
    layout="wide"
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.3rem; padding-bottom: 1rem;}
    .stMetric {border-radius: 16px; padding: 10px; background: rgba(127,127,127,0.05);}
    .fineprint {font-size:12px; color:#64748B}
    .caption-strong {font-size:13px; font-weight:600; color:#0f172a}
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------------------------
# 1. FUNGSI BACA & GABUNG DATA PRSA
# ------------------------------------------------------------
def read_prsa_folder(base_dir: str, main_file: str = "main_data.csv") -> pd.DataFrame:
    """
    1. Kalau sudah ada main_data.csv dan ukurannya > 0 → langsung baca itu.
    2. Kalau belum ada / kosong → gabungkan semua PRSA_Data_*.csv di folder itu.
    3. Bersihkan nama kolom: hapus tanda kutip, lowercase, ganti spasi ke underscore.
    4. Paksa kolom year, month, day, hour → numeric.
    5. Bangun kolom timestamp dari year,month,day,hour.
    6. Pakai kolom station → location.
    """
    main_path = os.path.join(base_dir, main_file)

    # ---- 1) kalau sudah ada main_data.csv ----
    if os.path.exists(main_path) and os.path.getsize(main_path) > 0:
        df = pd.read_csv(main_path)
    else:
        # ---- 2) gabungkan semua PRSA_Data_*.csv ----
        files = [
            f for f in os.listdir(base_dir)
            if f.startswith("PRSA_Data_") and f.endswith(".csv")
        ]
        if not files:
            # tidak ada PRSA sama sekali
            return pd.DataFrame()

        dfs = []
        for f in files:
            p = os.path.join(base_dir, f)
            # dataset kamu pakai koma, jadi pd.read_csv biasa cukup
            tmp = pd.read_csv(p)
            tmp["source_file"] = f
            dfs.append(tmp)

        df = pd.concat(dfs, ignore_index=True)
        # simpan supaya besok-besok nggak gabung ulang
        df.to_csv(main_path, index=False)

    # ---- 3) bersihkan nama kolom ----
    # awalnya: "No","year","month","day","hour","PM2.5",...
    cleaned_cols = []
    for c in df.columns:
        c = c.strip().replace('"', "")     # buang "
        c = c.replace(" ", "_")            # spasi → underscore
        c = c.replace(".", "_") 
        c = c.lower()                      # ke huruf kecil
        cleaned_cols.append(c)
    df.columns = cleaned_cols

    # ---- 4) paksa kolom waktu ke numeric ----
    time_cols = ["year", "month", "day", "hour"]
    if all(col in df.columns for col in time_cols):
        for col in time_cols:
            # contoh: "2013" → 2013
            df[col] = pd.to_numeric(df[col], errors="coerce")
        # ---- 5) buat kolom timestamp ----
        df["timestamp"] = pd.to_datetime(
            df[["year", "month", "day", "hour"]],
            errors="coerce"
        )
    else:
        # kalau kolom tahun/bulan/hari/jam nggak lengkap
        df["timestamp"] = pd.NaT

    # ---- 6) lokasi ----
    if "station" in df.columns:
        df["location"] = df["station"]
    else:
        df["location"] = "PRSA-Station"

    return df

# ------------------------------------------------------------
# 2. FUNGSI LAIN
# ------------------------------------------------------------
def iqr_anomaly_mask(s: pd.Series, k: float = 1.5) -> pd.Series:
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - k * iqr, q3 + k * iqr
    return (s < lower) | (s > upper)

def download_csv_button(df: pd.DataFrame, filename: str, label: str = "📥 Unduh CSV"):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label, data=csv, file_name=filename, mime="text/csv")

# ------------------------------------------------------------
# 3. LOAD DATA (dari folder kamu)
# ------------------------------------------------------------
# Lokasi folder PRSA ada di parent folder dari Dashboard
# (sama dengan struktur proyek: ../PRSA_Data_20130301-20170228)
PRSA_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'PRSA_Data_20130301-20170228')

# Folder ini juga dipakai untuk menyimpan/menaruh `main_data.csv`
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# user boleh upload csv lain juga
uploaded = st.sidebar.file_uploader("Unggah CSV (opsional)", type=["csv"])

if uploaded is not None:
    # kalau user upload, kita pakai itu, tapi tetap normalkan kolomnya
    df = pd.read_csv(uploaded)
    df.columns = [c.strip().replace('"', "").replace(" ", "_").lower() for c in df.columns]
    # kalau user upload juga punya year,month,day,hour → bikin timestamp
    if all(col in df.columns for col in ["year", "month", "day", "hour"]):
        for col in ["year", "month", "day", "hour"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["timestamp"] = pd.to_datetime(df[["year", "month", "day", "hour"]], errors="coerce")
    elif "timestamp" not in df.columns:
        df["timestamp"] = pd.NaT
    if "station" in df.columns and "location" not in df.columns:
        df["location"] = df["station"]
else:
    # kalau tidak upload → baca PRSA dari folder PRSA_DATA_DIR (parent folder)
    # Fungsi read_prsa_folder akan membaca main_data.csv jika ada, atau
    # menggabungkan file PRSA_Data_*.csv di folder tersebut.
    df = read_prsa_folder(PRSA_DATA_DIR, "main_data.csv")

# ------------------------------------------------------------
# 4. VALIDASI DATA
# ------------------------------------------------------------
if df.empty:
    st.error("❗ Tidak ada data yang bisa dibaca. Pastikan ada `PRSA_Data_*.csv` atau `main_data.csv` di folder ini.")
    st.stop()

if "timestamp" not in df.columns:
    st.error("❗ Kolom waktu (`timestamp` atau `year,month,day,hour`) tidak ditemukan / gagal dibentuk.")
    st.write("Kolom yang terbaca:", list(df.columns))
    st.stop()

# ubah ke datetime dan buang yang gagal
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df = df.dropna(subset=["timestamp"])

# pastikan ada location
if "location" not in df.columns:
    df["location"] = "PRSA-Station"

# deteksi kolom numerik
num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
# hilangkan kolom index/waktu yang nggak perlu
for dropcol in ["no", "year", "month", "day", "hour"]:
    if dropcol in num_cols:
        num_cols.remove(dropcol)

if not num_cols:
    st.error("❗ Tidak ada kolom numerik yang bisa diplot (misal: pm2.5, pm10, temp, pres).")
    st.write("Kolom yang ada:", list(df.columns))
    st.stop()

# ------------------------------------------------------------
# 5. SIDEBAR FILTER
# ------------------------------------------------------------
st.sidebar.header("Filter Dashboard")

metric = st.sidebar.selectbox("Metrik utama", num_cols, index=0)

min_d, max_d = df["timestamp"].min().date(), df["timestamp"].max().date()
start_d, end_d = st.sidebar.date_input(
    "Rentang tanggal",
    value=(min_d, max_d),
    min_value=min_d,
    max_value=max_d
)

locations = sorted(df["location"].dropna().astype(str).unique().tolist())
sel_locs = st.sidebar.multiselect("Lokasi", locations, default=locations)

min_v, max_v = float(df[metric].min()), float(df[metric].max())
v_min, v_max = st.sidebar.slider(
    "Rentang nilai",
    min_value=min_v,
    max_value=max_v,
    value=(min_v, max_v)
)

with st.sidebar.expander("Deteksi Anomali (IQR)"):
    do_anom = st.checkbox("Tandai anomali", value=False)
    iqr_k = st.slider("Sensitivitas", 0.5, 3.0, 1.5, 0.1)

st.sidebar.markdown("---")

# ------------------------------------------------------------
# 6. FILTER DATAFRAME
# ------------------------------------------------------------
mask = (
    (df["timestamp"].dt.date >= start_d) &
    (df["timestamp"].dt.date <= end_d) &
    (df["location"].astype(str).isin(sel_locs)) &
    (df[metric].between(v_min, v_max))
)

fdf = df.loc[mask].copy()

# ------------------------------------------------------------
# 7. HEADER & KPI
# ------------------------------------------------------------
st.title("Dashboard Analisis Data (PRSA)")
st.caption("Dataset kualitas udara PRSA (multi-station) yang dibersihkan otomatis dari folder lokal.")

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Jumlah Record", f"{len(fdf):,}")
with k2:
    st.metric("Lokasi Aktif", f"{fdf['location'].nunique():,}")
with k3:
    st.metric(f"Mean {metric}", f"{fdf[metric].mean():.2f}")
with k4:
    st.metric(f"Standard Deviation {metric}", f"{fdf[metric].std():.2f}")

st.markdown("<div class='fineprint'>*Ganti metrik dari sidebar untuk analisis berbeda*</div>", unsafe_allow_html=True)

# ------------------------------------------------------------
# 8. GRAFIK – TREN WAKTU & PER LOKASI
# ------------------------------------------------------------
col1, col2 = st.columns((2, 1))

with col1:
    st.subheader("Tren Harian")
    ts = fdf.groupby(pd.Grouper(key="timestamp", freq="D"))[metric].mean().reset_index()
    chart_ts = alt.Chart(ts).mark_line(point=True).encode(
        x=alt.X("timestamp:T", title="Tanggal"),
        y=alt.Y(metric, title=f"Rata-rata {metric}"),
        tooltip=["timestamp:T", alt.Tooltip(metric, format=".2f")]
    ).interactive()
    st.altair_chart(chart_ts, width='stretch')

with col2:
    st.subheader("Rerata per Lokasi")
    by_loc = fdf.groupby("location", as_index=False)[metric].mean().sort_values(metric, ascending=False)
    chart_loc = alt.Chart(by_loc).mark_bar().encode(
        x=alt.X(metric, title=f"Rata-rata {metric}"),
        y=alt.Y("location", sort='-x', title="Lokasi"),
        tooltip=["location", alt.Tooltip(metric, format=".2f")]
    )
    st.altair_chart(chart_loc, width='stretch')

# ------------------------------------------------------------
# 9. BOXPLOT PER LOKASI
# ------------------------------------------------------------
st.subheader("Sebaran Nilai per Lokasi")
box = alt.Chart(fdf).mark_boxplot(extent="min-max").encode(
    x=alt.X("location:N", title="Lokasi"),
    y=alt.Y(metric, title=metric)
)
st.altair_chart(box, width='stretch')

# ------------------------------------------------------------
# 10. DETEKSI ANOMALI
# ------------------------------------------------------------
st.subheader("Deteksi Anomali (IQR)")
if do_anom:
    fdf["is_anom"] = iqr_anomaly_mask(fdf[metric], k=iqr_k)
    anom_df = fdf[fdf["is_anom"]].copy()
    st.write(f"Ditemukan **{len(anom_df)}** titik anomali pada metrik **{metric}**.")

    sc = alt.Chart(fdf).mark_circle(size=40, opacity=0.7).encode(
        x=alt.X("timestamp:T", title="Waktu"),
        y=alt.Y(metric, title=metric),
        color=alt.condition(
            alt.datum.is_anom == True,
            alt.value("crimson"),
            alt.value("steelblue")
        ),
        tooltip=["timestamp:T", "location", alt.Tooltip(metric, format=".2f")]
    ).interactive()
    st.altair_chart(sc, width='stretch')

    with st.expander("Lihat tabel anomali"):
        st.dataframe(anom_df[["timestamp", "location", metric]].sort_values("timestamp"))
else:
    st.caption("Aktifkan di sidebar untuk melihat titik outlier.")

# ------------------------------------------------------------
# 11. DATA TABLE & DOWNLOAD
# ------------------------------------------------------------
st.subheader("Data (Hasil Filter)")
st.dataframe(fdf.sort_values("timestamp", ascending=False).reset_index(drop=True))

download_csv_button(fdf, "filtered_data.csv")

st.markdown("---")
