# 🌳🔥 Multi-Agent Deforestation & Fire Monitoring System

Sistem multi-agen (MAS) berbasis **[Mesa](https://github.com/mesa/mesa)** yang memantau citra satelit
secara terus-menerus untuk mendeteksi **tebang liar** dan **kebakaran hutan**. Agen tidak menyimpulkan
sendiri: setiap wilayah yang dicurigai harus disepakati (konsensus) oleh dua agen dengan sumber bukti
berbeda sebelum peringatan dikirim ke pihak berwenang.

> Sistem berjalan pada dua jenis data: **lingkungan satelit sintetis** yang dilengkapi *ground truth* sehingga
> kinerjanya bisa diukur (bagian 4-5), dan **data nyata MODIS dari Google Earth Engine** dalam mode replay
> (bagian 8).

---

## 1. Peran agen

| Agen | Kelas | Tugas |
| :--- | :--- | :--- |
| **Agen Pengunduh** | `DataIngestionAgent` | Memantau *cloud storage*, mengunduh citra baru, dan mencoba ulang unduhan yang gagal. |
| **Agen Deteksi Perubahan** | `ChangeDetectionAgent` | Membandingkan citra hari ini dengan komposit median citra **minggu lalu** (H-9 s.d. H-5), mencari area hijau yang hilang drastis, lalu memeriksa apakah kehilangan itu **menetap**. Jumlahnya bisa lebih dari satu; wilayah dibagi per detektor. |
| **Agen Validasi** | `ValidationAgent` | Memeriksa anomali **suhu permukaan (termal)** di wilayah curiga: sangat panas → kebakaran, sedikit hangat → tebang liar, lebih dingin → awan/alarm palsu. Bisa lebih dari satu; tugas dibagi ke validator dengan antrean tersingkat (*load balancing*). |
| **Agen Notifikasi** | `NotificationAgent` | Menerima laporan hasil konsensus, menentukan prioritas dan kanal tujuan, mengirim peringatan, dan memperbarui peringatan bila area kebakaran meluas. |

## 2. Interaksi & konsensus

```
 Pengunduh ──INFORM new_scene──▶ Deteksi ──REQUEST validate──▶ Validasi
                                    ▲                              │
                                    └──────PROPOSE verdict─────────┘
            konsensus tercapai ──CONFIRM / CANCEL──▶ Validasi
 Deteksi ──INFORM report──▶ Notifikasi ──▶ Tim Pemadam / Polisi Hutan / Analis
```

Pesan memakai *performative* bergaya **FIPA-ACL** (`inform`, `request`, `propose`, `confirm`, `cancel`)
dan `conversation_id` per kasus, sehingga setiap kasus bisa dilacak dari awal sampai akhir.

**Aturan konsensus** (dua bukti independen):

| Suara Deteksi (NDVI menetap?) | Suara Validasi (termal) | Keputusan |
| :---: | :---: | :--- |
| ya | nyata (tebang/kebakaran) | ✅ **CONFIRMED** → peringatan |
| tidak | tidak nyata (awan) | ❌ **DISMISSED** (alarm palsu) |
| berbeda | berbeda | 🔁 ronde ulang dengan data hari berikutnya (maks. 2 ronde) |
| masih berbeda | masih berbeda | ⚠️ **UNCERTAIN** → dikirim untuk tinjauan manual |

| Penyebab | Prioritas | Kanal |
| :--- | :--- | :--- |
| Kebakaran | DARURAT | Tim Pemadam Kebakaran Hutan |
| Tebang liar | TINGGI | Polisi Hutan / Dinas Kehutanan |
| Tidak pasti | RENDAH | Analis GIS (tinjauan manual) |

## 3. Kaitan dengan materi MAS (P05)

- **Background of MAS**: setiap agen terbatas (citra optik tertutup awan, termal tidak melihat vegetasi),
  sehingga mereka menggabungkan sumber daya untuk satu tujuan bersama.
- **Tipe agen**: Pengunduh adalah *simple reflex agent* (ada citra baru → unduh). Deteksi adalah
  *model-based* (menyimpan komposit acuan dan riwayat kasus). Validasi bersifat *goal/utility-based*
  (memilih penyebab dan memberi tingkat keyakinan).
- **Interaksi antaragen**: protokol request–propose–confirm dan konsensus dua pihak.

## 4. Lingkungan sintetis

`ForestEnvironment` membangkitkan hutan 64×64 sel (±1 ha/sel) dengan:

- **Tebang liar**: petak persegi, NDVI turun permanen, suhu naik ±2 °C.
- **Kebakaran**: titik api yang menyebar 2 hari, anomali termal +18–30 °C yang meluruh.
- **Awan (pengecoh)**: NDVI turun sementara 1–2 hari, suhu justru turun. Dari citra optik saja, awan
  terlihat seperti deforestasi.
- Gangguan nyata: noise sensor, musim, unduhan gagal (5%), dan data termal hilang (5%).

## 5. Hasil (120 hari, seed 42)

| Metrik | MAS (konsensus) | Detektor tunggal |
| :--- | ---: | ---: |
| Kasus terkonfirmasi | 15 | 42 |
| Alarm palsu | **0** | 12 |
| Recall | 1.00 | 1.00 |
| Precision | **1.00** | 0.71 |
| Akurasi penyebab | 1.00 | – |
| Latensi rata-rata (hari) | 1.20 | 0.20 |

Rata-rata 10 seed (0–9): MAS mencapai recall ≈0,99, precision 1,00, dan akurasi penyebab ≈0,99, tanpa alarm
palsu. Detektor tunggal juga mencapai recall 1,00, tetapi precision-nya hanya ≈0,65 karena rata-rata
menghasilkan 14 alarm palsu per run. Harga yang dibayar adalah latensi sekitar 1 hari, karena konsensus membutuhkan citra hari
berikutnya. Kegagalan yang tersisa terjadi saat tebang liar berlangsung tepat di bawah awan; kasus seperti ini
dikirim sebagai *uncertain* untuk ditinjau manusia.

![Hasil simulasi](output/simulation.png)

## 6. Cara menjalankan

```bash
cd Multi-Agent-System
pip install -r requirements.txt

python run_simulation.py                              # 120 hari, seed 42
python run_simulation.py --compare                    # MAS vs detektor tunggal
python run_simulation.py --detectors 3 --validators 2 # lebih banyak agen
python run_simulation.py --days 180 --seed 7 --quiet
python -m pytest -q tests                             # 37 pengujian
```

Di Windows, cukup klik ganda `Jalankan_Multi-Agent-System.bat` di root repositori.
Hasil tersimpan di `output/`: `alerts.json` (semua peringatan beserta bukti), `timeseries.csv`
(data `DataCollector` Mesa per hari), dan `simulation.png`.

## 7. Struktur kode

```
Multi-Agent-System/
├── deforestation_mas/
│   ├── environment.py   # lingkungan satelit sintetis + ground truth
│   ├── messaging.py     # MessageBus & pesan bergaya FIPA-ACL
│   ├── agents.py        # 4 agen + logika konsensus
│   ├── model.py         # mesa.Model: pipeline harian & DataCollector
│   ├── evaluation.py    # recall, precision, akurasi penyebab, latensi
│   └── gee_environment.py  # adapter data nyata Google Earth Engine (MODIS)
├── tests/               # test_mas.py (simulasi), test_gee_adapter.py (adapter GEE)
├── run_simulation.py    # simulasi sintetis
├── run_gee.py           # replay pada data nyata GEE (--check untuk uji koneksi)
├── requirements.txt
└── requirements-gee.txt # tambahan untuk GEE
```

## 8. 🛰️ Data nyata dari Google Earth Engine (replay MODIS)

Adapter `deforestation_mas/gee_environment.py` memenuhi antarmuka yang sama dengan lingkungan sintetis, jadi
agen yang sama langsung bisa memakai data nyata. Data lampau diputar ulang hari demi hari seolah-olah baru
masuk (*replay*), sehingga hasilnya bisa dicocokkan dengan kejadian yang sudah diketahui.

**Persiapan (sekali saja)**
```bash
pip install -r requirements-gee.txt
earthengine authenticate          # login lewat browser
```
Akun GEE harus terhubung ke proyek Google Cloud; catat **Project ID**-nya.

**Menjalankan**
```bash
# 1) uji koneksi dan satu hari data (hanya 1 permintaan ke GEE)
python run_gee.py --project PROJECT-ID --check

# 2) cari area 10 x 10 km dengan titik api MODIS terbanyak (default: seluruh Kalimantan Tengah)
python run_gee.py --project PROJECT-ID --find-fires --start 2023-08-01 --days 92

# 3) periksa banyak hari: berapa persen area bebas awan tiap hari (sekaligus mengisi cache)
python run_gee.py --project PROJECT-ID --scan 30

# 4) replay periode (hasil unduhan di-cache di gee_cache/, jadi pengulangan tidak memakai kuota)
python run_gee.py --project PROJECT-ID --days 60

# 5) ganti wilayah/periode, pertahankan piksel berasap, atau kalibrasi ambang
python run_gee.py --project PROJECT-ID --keep-haze --scan 30
python run_gee.py --project PROJECT-ID --lat -2.35 --lon 114.0 --start 2023-08-15 --days 90
python run_gee.py --project PROJECT-ID --drop-threshold 0.15 --persist-threshold 0.10
```
`--project` boleh dikosongkan bila variabel lingkungan `EE_PROJECT` sudah diatur. Hasil ada di `output_gee/`
(`alerts.json` dengan tanggal asli, `timeseries.csv`, `gee_replay.png`; `--check` menyimpan `check.png`).
`--find-fires` langsung mencetak perintah `--scan` dan replay untuk kandidat teratas.
Pada uji di sekitar Palangka Raya (Agustus–September 2023), masker cirrus terbukti terlalu ketat:
`--keep-haze` menaikkan hari cerah dari 5 menjadi 9 dari 30 hari, jadi opsi ini disarankan.
Bila NDVI kosong, `--check` merinci penyebabnya (awan, bayangan awan, asap/aerosol tinggi, cirrus, atau celah
lintasan satelit) dan menyarankan langkah berikutnya.
Wilayah bawaan: 10 x 10 km di sekitar Palangka Raya, Kalimantan Tengah.

**Data yang dipakai** (satu grid yang sama, 250 m)

| Bukti | Koleksi GEE | Pemrosesan |
| :--- | :--- | :--- |
| NDVI | `MODIS/061/MOD09GQ` (250 m) | (NIR - merah) / (NIR + merah); piksel berawan, bayangan awan, aerosol/asap tinggi, dan cirrus tinggi dimasker memakai `state_1km` dari `MODIS/061/MOD09GA` |
| Suhu permukaan | `MODIS/061/MOD11A1` (1 km) | K → °C; piksel "tidak ada LST" (awan) dimasker |
| Titik api | `MODIS/061/MOD14A1` (1 km) | kelas 7-9 = api, kelas 5 = tanah tanpa api, selain itu (awan, tidak diproses) = tak teramati |

**Perbedaan penting dibanding data sintetis**
- **Awan menjadi data bolong (NaN)**, bukan penurunan NDVI palsu. Agen menunggu citra bersih berikutnya. Bila
  citra pengecekan terus tertutup lebih dari 10 hari, kasus diserahkan ke analis (`uncertain`).
- **Kebakaran dibuktikan oleh titik api MODIS**, bukan oleh suhu: tanah gundul pun lebih panas, jadi anomali suhu
  tidak bisa membedakan tebang liar dari kebakaran. Tebang liar diputuskan bila titik api teramati dan tidak ada.
  Api yang tidak teramati karena awan tidak dianggap "tidak ada api"; Agen Validasi menunggu hari lain.
- **Resolusi 250 m**: satu piksel = ±6 ha, sehingga tebangan kecil tidak terlihat dan wilayah curiga minimal
  4 piksel (±25 ha). Suhu dan titik api (1 km) tampak berblok. Sentinel-2 (10 m) bisa menggantikannya, tetapi
  revisitnya ±5 hari sehingga logika acuan "minggu lalu" perlu diubah.
- **Latensi**: data MODIS di GEE biasanya terlambat beberapa hari. `--latency N` menunda ketersediaan data
  agar replay lebih realistis.

**Status pengujian**: logika adapter, penanganan data bolong, cache, percobaan ulang, dan CLI diuji dengan GEE
tiruan (`tests/test_gee_adapter.py`). Panggilan ke server GEE sungguhan (ekspresi citra dan `computePixels`)
belum bisa diuji otomatis; gunakan `--check` untuk memastikannya di akun Anda. Ambang (`drop_threshold`,
`persist_threshold`, dst.) masih nilai awal dan perlu dikalibrasi pada kejadian nyata.

## 9. Ide pengembangan berikutnya

- **Agen Masker Awan** khusus yang memakai band QA citra, sehingga lebih sedikit kasus awan yang masuk validasi.
- **Agen Validasi kedua** berbasis radar (Sentinel-1) yang bisa melihat menembus awan, untuk menyelesaikan kasus *uncertain*.
- **Voting tiga pihak** atau *contract-net protocol* untuk membagi tugas validasi.
- **Agen Prioritas/Risiko** yang menilai kedekatan dengan kawasan lindung atau permukiman.
- *Learning agent* yang menyesuaikan ambang dari umpan balik petugas lapangan (materi *Multi-agent Learning*).
- Visualisasi interaktif dengan `mesa.visualization` (Solara).
