# STEAMITE - Dashboard Analisis Kualitas Udara Beijing

Dashboard interaktif untuk analisis data kualitas udara dari 12 stasiun pemantauan di Beijing (2013-2017).

## Deskripsi

Dashboard ini memvisualisasikan data kualitas udara Beijing dengan fitur:
- Tren polutan (PM2.5, PM10, CO, NO₂) dari waktu ke waktu
- Analisis pengaruh suhu dan kelembapan terhadap kadar polutan
- Deteksi anomali menggunakan metode IQR
- Filter berdasarkan waktu, lokasi, dan jenis polutan

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

## Penggunaan Dashboard

1. **Filter Data**:
   - Pilih metrik (PM2.5, PM10, CO, NO₂)
   - Set rentang tanggal
   - Pilih lokasi stasiun
   - Atur sensitivitas deteksi anomali

2. **Visualisasi**:
   - Tren polutan harian
   - Rerata per lokasi
   - Boxplot sebaran nilai
   - Scatter plot anomali

3. **Download Data**:
   - Tombol unduh CSV untuk data terfilter

## Dependencies

- Python 3.11+
- pandas
- numpy
- streamlit
- altair
- seaborn
- matplotlib

Lihat `requirements.txt` untuk daftar lengkap dan versi.

## Sumber Data

Dataset PRSA (Beijing Multi-Site Air Quality Data) mencakup data kualitas udara per jam dari 12 stasiun pemantauan internasional di Beijing dari Maret 2013 hingga Februari 2017.
