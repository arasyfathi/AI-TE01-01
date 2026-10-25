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
| **Agen Titik Api** (mode 2 mingguan) | `HotspotAgent` | Peringatan dini (DARURAT) langsung dari titik api VIIRS sampai hari ini, tanpa menunggu citra bebas awan. Titik api yang bersebelahan dikelompokkan menjadi satu klaster. |
| **Agen Pengelompokan Kejadian** (mode 2 mingguan) | `IncidentAgent` | Menyatukan bagian bekas terbakar yang berjarak < 500 m menjadi satu kejadian kebakaran (TINGGI) dan menautkannya ke klaster titik api yang menjadi penyebabnya. |

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
python -m pytest -q tests                             # 65 pengujian
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
│   ├── gee_environment.py  # adapter data nyata Google Earth Engine (MODIS, replay harian)
│   ├── sentinel_environment.py  # periode 2 minggu: Sentinel-2 + titik api VIIRS
│   └── region.py        # batas kecamatan GeoJSON + rasterisasi
├── tests/               # test_mas.py (simulasi), test_gee_adapter.py (adapter GEE)
├── run_simulation.py    # simulasi sintetis
├── run_gee.py           # replay pada data nyata GEE (--check untuk uji koneksi)
├── run_pantau.py        # pemantauan 2 mingguan per kecamatan (Sentinel-2 + VIIRS)
├── web_pantau.py        # aplikasi web lokal (server) untuk pemantauan per kecamatan
├── web/index.html       # halaman web: peta, daftar kecamatan, keluaran tiap agen
├── data/                # batas kecamatan Kabupaten Kubu Raya (GeoJSON)
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

**Hasil uji pertama di data nyata dan perbaikannya** (area hasil `--find-fires`: -2.537, 114.587,
23 Agustus–21 Oktober 2023, `--keep-haze`): MODIS mencatat titik api pada 25 tanggal, rata-rata hanya 21% piksel
NDVI bebas awan per hari, dan agen membuka 7 kasus. Namun **tidak satu pun terkonfirmasi**: 6 kasus berakhir
"perlu tinjauan". Bukti di `alerts.json` menunjukkan dua masalah pada aturan konsensus:
- Empat kasus kebakaran sudah punya titik api 17–100% di lokasi penurunan NDVI, tetapi agen Deteksi tidak pernah
  mendapat citra bersih untuk memastikan kehilangan vegetasi menetap, lalu menyerah setelah 10 hari.
- Dua kasus diberi vonis "tebang liar" oleh agen Validasi hanya karena tidak ada api, padahal agen Deteksi berulang
  kali mengukur NDVI pulih (penurunan 0,02–0,05).

Aturan yang diperbaiki:
- **Jalur cepat kebakaran**: penurunan NDVI ditambah bukti api di lokasi yang sama sudah merupakan dua bukti
  independen, jadi kasus langsung terkonfirmasi tanpa menunggu citra bersih.
- **Bobot suara**: agen Validasi menandai suaranya *kuat* (ada bukti langsung: titik api, atau tanda suhu khas)
  atau *lemah* ("tebang liar" hanya karena tidak ada api). Suara lemah tidak bisa mengalahkan pengamatan bahwa NDVI
  pulih, sehingga kasus seperti itu ditolak dan tidak dilempar ke analis.
- **Batas tunggu citra bersih** untuk data nyata dinaikkan menjadi 20 hari (`--max-wait`).

Perilaku pada data simulasi tidak berubah. Ringkasan `run_gee.py` kini mencetak alasan keputusan tiap kasus.

**Hasil replay ulang di area dan periode yang sama:**

| | Sebelum perbaikan | Sesudah perbaikan |
| :--- | ---: | ---: |
| Kasus dibuka | 7 | 7 |
| Peringatan kebakaran (DARURAT) | 0 | **4** |
| Alarm palsu ditolak | 0 | **3** |
| Perlu tinjauan manual | 6 | **0** |

Keempat kebakaran (3, 5, 24 September dan 6 Oktober 2023) terkonfirmasi lewat jalur cepat dengan titik api 17–100%
di lokasi penurunan NDVI. Ketiga kasus lain ditolak karena NDVI terbukti pulih (penurunan -0,01 sampai 0,03).

Catatan kejujuran evaluasi: titik api MODIS dipakai sebagai bukti oleh agen Validasi, jadi kecocokan dengan
daftar "hari MODIS mendeteksi titik api" bukan validasi independen, dan recall pada data nyata belum bisa
dihitung. Pembanding independen yang bisa dipakai berikutnya: produk area terbakar `MODIS/061/MCD64A1`
atau titik api VIIRS.


**Status pengujian**: logika adapter, penanganan data bolong, cache, percobaan ulang, dan CLI diuji dengan GEE
tiruan (`tests/test_gee_adapter.py`). Panggilan ke server GEE sungguhan (ekspresi citra dan `computePixels`)
belum bisa diuji otomatis; gunakan `--check` untuk memastikannya di akun Anda. Ambang (`drop_threshold`,
`persist_threshold`, dst.) masih nilai awal dan perlu dikalibrasi pada kejadian nyata.

## 9. 📡 Pemantauan 2 mingguan Kabupaten Kubu Raya (Sentinel-2 + VIIRS)

Mode ini memantau **data terbaru** setiap 2 minggu untuk **satu kecamatan** di Kabupaten Kubu Raya
(atau semuanya), memakai batas kecamatan di `data/kubu_raya_kecamatan.geojson`. Mode ini menggantikan MODIS:
NASA mengumumkan Terra dan Aqua (pembawa MODIS) mulai dimatikan pada akhir 2026/awal 2027.

**Data per periode 2 minggu**

| Bukti | Koleksi GEE | Pemrosesan |
| :--- | :--- | :--- |
| NDVI 30 m (bawaan) | `COPERNICUS/S2_SR_HARMONIZED` | komposit median periode; piksel berawan dibuang dengan Cloud Score+ (`GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED`, `cs_cdf` ≥ 0,6) |
| Tutupan lahan (opsional, tidak dipakai bawaan) | `JRC/GFC2020/V4`, `BIOPAMA/GlobalOilPalm/v1_2` | hutan alam / sawit / lahan lain, bila `use_landcover=True` |
| Titik api harian | koleksi VIIRS yang sama | jumlah deteksi, tanggal pertama/terakhir, FRP per sel ~375 m untuk Agen Titik Api |
| Titik api | `NASA/LANCE/SNPP_VIIRS/C2` + `NASA/LANCE/NOAA20_VIIRS/C2` | ada titik api berkeyakinan nominal/tinggi dalam periode = bukti kebakaran |

**Cara kerja satu putaran**
- Periode memakai kalender tetap 14 hari. Satu putaran memproses 4 periode lengkap terakhir: 2 periode
  acuan dan 2 periode yang dipantau. Satu langkah Mesa = satu periode.
- Acuan = **pengamatan bersih terakhir** per piksel (periode sebelumnya; bila berawan, mundur satu periode),
  sehingga kehilangan yang sudah dilaporkan tidak terdeteksi ulang pada putaran berikutnya.
- **Fokus kebakaran hutan dan lahan (karhutla), tanpa membedakan tutupan lahan.** Ada dua jenis peringatan:
  **titik api aktif** (DARURAT, dari Agen Titik Api) dan **bekas terbakar terkonfirmasi** (TINGGI, penurunan
  NDVI + bukti api). Penurunan NDVI tanpa bukti api (panen, pembukaan lahan, kabut) tidak diperingatkan.
  Peta tutupan lahan (JRC GFC2020 V4, BIOPAMA Global Oil Palm) tidak diunduh di mode ini; kodenya tetap ada
  (`use_landcover=True`) bila suatu saat ingin membedakan hutan, sawit, dan lahan lain.
  Riwayat keputusan: masker ESA WorldCover ternyata ikut memasukkan kebun sawit sebagai "hutan", lalu masker
  hutan alam JRC hanya menyisakan ±200 ha di Rasau Jaya, sehingga kebakaran lahan tidak terlihat.
- **Agen Titik Api** memberi peringatan dini untuk keempat periode dan sampai hari ini (bukan hanya sampai
  periode lengkap terakhir); riwayat mencegah laporan ganda.
- **Kebakaran dikonfirmasi pada periode yang sama** (penurunan NDVI + titik api VIIRS di lokasi itu), lalu
  **Agen Pengelompokan Kejadian** menyatukan fragmen yang berdekatan menjadi satu kejadian.
- **Tebang liar dikonfirmasi** bila periode berikutnya membuktikan kehilangan menetap; bila NDVI pulih
  (kabut, awan tipis), kasus ditolak. Kasus di periode terakhir menunggu putaran berikutnya.
- Peringatan baru ditambahkan ke `riwayat_peringatan.json` per kecamatan; menjalankan ulang tidak menggandakan.

**Menjalankan**
```bash
python run_pantau.py --list                                     # daftar 9 kecamatan
python run_pantau.py --project PROJECT-ID --status              # tanggal data terbaru tiap sumber
python run_pantau.py --project PROJECT-ID --kecamatan "Sungai Raya"
python run_pantau.py --project PROJECT-ID --kecamatan semua
python run_pantau.py --project PROJECT-ID --kecamatan "Sungai Raya" --end-date 2023-10-15   # uji historis
```
Di Windows: klik ganda `Pantau_Kubu_Raya.bat` di root repositori (memilih kecamatan secara interaktif), atau
`Pantau_Kubu_Raya.bat "Sungai Raya"`. Atur Project ID sekali dengan `setx EE_PROJECT "project-id-anda"`.

**Menjadwalkan otomatis setiap 2 minggu (Windows Task Scheduler)**: Create Basic Task → Daily → *Recur every*
14 days → Start a program: `Pantau_Kubu_Raya.bat`, *Add arguments*: `"Sungai Raya"`.

**Hasil** di `output_pantau/<kecamatan>/`: `laporan_<periode>.json` (peringatan baru dan wilayah yang masih
menunggu), `peta_<periode>.png` (NDVI acuan vs terbaru dengan penanda), `riwayat_peringatan.json`, dan
`peringatan.geojson` (titik peringatan untuk QGIS / Google Earth).

**Keterbatasan yang perlu diketahui**
- "Terbaru" = periode 14 hari lengkap terakhir sebelum *hari ini - 3 hari* (jeda masuknya data ke GEE).
  Jalankan `--status` untuk melihat apakah setiap sumber masih diperbarui.
- Katalog GEE mencatat data titik api NOAA-20 hingga 13 September 2026 dan Suomi NPP hingga 19 Oktober 2026;
  pengiriman data Suomi NPP dihentikan NASA pada 2 November 2026. Bila semua sumber titik api berhenti,
  ringkasan menampilkan "tak ada data" dan kebakaran tidak dapat dikonfirmasi lewat jalur cepat.
- Titik api VIIRS berukuran ~375 m dan bukan kepastian kebakaran: sumber panas lain (mis. suar gas, cerobong
  pabrik) bisa ikut terdeteksi. Bekas terbakar terkonfirmasi butuh penurunan NDVI dan bukti api sekaligus.
- Sistem tidak membedakan pembakaran yang disengaja (mis. pembukaan ladang) dari kebakaran tak disengaja.
- Uji otomatis memakai data periode tiruan dan objek `ee` palsu; panggilan ke server GEE sungguhan belum
  teruji dari lingkungan pengembangan.

## 10. 🌐 Halaman web pemantauan

Aplikasi web lokal untuk memilih kecamatan, menjalankan pemantauan, dan melihat keluaran setiap agen.
Project ID GEE sudah tertanam di `web_pantau.py` (`PROJECT_ID`; bisa ditimpa dengan variabel `EE_PROJECT`).

```bash
python web_pantau.py          # lalu buka http://127.0.0.1:8765 (biasanya terbuka otomatis)
```
Di Windows: klik ganda `Buka_Web_Pantau.bat` di root repositori. Biarkan jendela konsolnya terbuka selama
memakai halaman.

- **Daftar kecamatan dan peta**: pilih kecamatan dari daftar (dengan batang luas relatif) atau klik poligonnya
  di peta citra satelit. Hasil pemantauan terakhir langsung ditampilkan bila sudah ada.
- **Pantau**: menjalankan keenam agen untuk kecamatan itu di latar belakang; log konsol tampil di halaman.
  Isi "Anggap hari ini tanggal" untuk uji historis.
- **Jalur agen**: Pengunduh, Titik Api, Deteksi Perubahan, Validasi, Pengelompokan, dan Notifikasi, masing-masing
  dengan jumlah pesan yang diterima/dikirim. Klik untuk melihat tabel keluarannya; klik baris tabel untuk
  terbang ke lokasinya di peta. Tab "Pesan antaragen" merangkum seluruh percakapan FIPA-ACL.
- **Peta**: titik api VIIRS (kotak merah per sel ~375 m), tepi bekas terbakar, wilayah yang menunggu, dan
  (opsional) wilayah yang ditolak. Pilih citra satelit atau peta jalan dari kontrol lapisan.
- **Cek kesegaran data**: tanggal citra terbaru tiap sumber di GEE.

Server hanya mendengarkan `127.0.0.1` dan hanya satu pemantauan yang berjalan pada satu waktu. Peta dan huruf
dimuat dari internet (Leaflet di cdnjs, citra Esri, Google Fonts); tanpa internet tabel tetap berfungsi.

## 11. Ide pengembangan berikutnya

- **Agen Masker Awan** khusus yang memakai band QA citra, sehingga lebih sedikit kasus awan yang masuk validasi.
- **Agen Validasi kedua** berbasis radar (Sentinel-1) yang bisa melihat menembus awan, untuk menyelesaikan kasus *uncertain*.
- **Voting tiga pihak** atau *contract-net protocol* untuk membagi tugas validasi.
- **Agen Prioritas/Risiko** yang menilai kedekatan dengan kawasan lindung atau permukiman.
- *Learning agent* yang menyesuaikan ambang dari umpan balik petugas lapangan (materi *Multi-agent Learning*).
- Visualisasi interaktif dengan `mesa.visualization` (Solara).
