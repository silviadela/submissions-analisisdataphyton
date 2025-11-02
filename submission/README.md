# Dashboard Analisis Kualitas Udara Beijing

Dashboard interaktif untuk analisis data kualitas udara dari 12 stasiun pemantauan di Beijing (2013-2017).

## Deskripsi

Dashboard ini memvisualisasikan data kualitas udara Beijing dengan fitur:
- Tren polutan (PM2.5, PM10, SO₂, NO₂, CO, O₃) dari waktu ke waktu
- Analisis musiman (Winter, Spring, Summer, Autumn)
- Kategorisasi kualitas udara (Baik/Sedang/Buruk)
- Filter berdasarkan waktu dan lokasi stasiun
- Visualisasi perbandingan antar stasiun

## Setup Environment

```bash
# Buat virtual environment (opsional)
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## Menjalankan Dashboard

1. Pastikan berada di folder root project:
```bash
cd path/to/submission
```

2. Jalankan dashboard dengan streamlit:
```bash
python -m streamlit run Dashboard/dashboard.py
```

3. Dashboard akan terbuka di browser default (biasanya http://localhost:8501)

## Struktur Project
```
submission/
├── Dashboard/
│   ├── dashboard.py         # Aplikasi Streamlit
│   └── main_data.csv       # Data gabungan (generated)
├── PRSA_Data_20130301-20170228/
│   ├── PRSA_Data_Aotizhongxin_*.csv
│   ├── PRSA_Data_Changping_*.csv
│   └── ...                 # File CSV per stasiun
├── Notebook_Colab_*.ipynb  # Notebook analisis
├── requirements.txt        # Dependencies
└── README.md              # Dokumentasi
```

## Fitur Dashboard

1. **📈 Tren Polutan**
   - Visualisasi tren temporal polutan (rata-rata bulanan)
   - Pilihan untuk menampilkan/menyembunyikan polutan spesifik
   - Grafik interaktif dengan legend

2. **🍂 Polutan per Musim**
   - Analisis konsentrasi polutan berdasarkan musim
   - Detail bulan-bulan dalam setiap musim
   - Grafik batang dengan nilai rata-rata
   - Interpretasi cepat pengaruh musim

3. **🏙️ Kategori per Stasiun**
   - Kategorisasi kualitas udara (Baik/Sedang/Buruk)
   - Perbandingan visual antar stasiun
   - Metrik untuk setiap polutan
   - Grafik horizontal untuk perbandingan

## Filter Data

- **Waktu**: Pilih rentang tanggal spesifik
- **Lokasi**: Filter berdasarkan stasiun pemantauan
- **Polutan**: Pilih kombinasi polutan untuk ditampilkan
  - PM2.5 (Particulate Matter ≤ 2.5 µm)
  - PM10 (Particulate Matter ≤ 10 µm)
  - SO₂ (Sulfur Dioxide)
  - NO₂ (Nitrogen Dioxide)
  - CO (Carbon Monoxide)
  - O₃ (Ozone)

## Kategori Kualitas Udara

Kategorisasi berdasarkan standar:

1. **PM2.5**
   - Baik: ≤ 35 µg/m³
   - Sedang: 35-75 µg/m³
   - Buruk: > 75 µg/m³

2. **PM10**
   - Baik: ≤ 50 µg/m³
   - Sedang: 50-150 µg/m³
   - Buruk: > 150 µg/m³

3. **SO₂**
   - Baik: ≤ 40 µg/m³
   - Sedang: 40-80 µg/m³
   - Buruk: > 80 µg/m³

4. **NO₂**
   - Baik: ≤ 40 µg/m³
   - Sedang: 40-80 µg/m³
   - Buruk: > 80 µg/m³

5. **CO**
   - Baik: ≤ 1000 µg/m³
   - Sedang: 1000-1500 µg/m³
   - Buruk: > 1500 µg/m³

6. **O₃**
   - Baik: ≤ 100 µg/m³
   - Sedang: 100-150 µg/m³
   - Buruk: > 150 µg/m³

## Dependencies

- Python 3.11+
- streamlit
- pandas
- numpy
- matplotlib
- seaborn
- warnings

Lihat `requirements.txt` untuk daftar lengkap dan versi.

## Sumber Data

Dataset PRSA (Beijing Multi-Site Air Quality Data) mencakup data kualitas udara per jam dari 12 stasiun pemantauan internasional di Beijing dari Maret 2013 hingga Februari 2017. Data mencakup berbagai polutan udara dan parameter meteorologi.
