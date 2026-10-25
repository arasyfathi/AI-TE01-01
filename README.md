# 🤖 Repositori Tugas Mata Kuliah Kecerdasan Buatan (AI-TE01)

<p align="center">
  <img src="https://cdn.pixabay.com/animation/2022/08/06/11/57/11-57-26-645_512.gif" alt="AI Project Banner" width="460">
</p>

<p align="center">
  <b>Implementasi Komprehensif: Algoritma Pencarian, Sistem Pakar (Expert System) & Multi-Agent System</b><br>
  Program Studi S1 Teknik Elektro — Fakultas Teknik Elektro — Universitas Telkom
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Mata%20Kuliah-Kecerdasan%20Buatan-0052CC.svg?style=flat-square" alt="Course">
  <img src="https://img.shields.io/badge/Kode%20Kelas-AI--TE01-orange.svg?style=flat-square" alt="Class">
  <img src="https://img.shields.io/badge/Program%20Studi-S1%20Teknik%20Elektro-red.svg?style=flat-square" alt="Major">
  <img src="https://img.shields.io/badge/Bahasa-C%2B%2B%20%7C%20Python-blue.svg?style=flat-square" alt="Languages">
  <img src="https://img.shields.io/badge/Framework-Mesa%20(MAS)-purple.svg?style=flat-square" alt="Mesa">
  <img src="https://img.shields.io/badge/Lisensi-Apache%202.0-green.svg?style=flat-square" alt="License">
</p>

---

## 📌 Daftar Isi
1. [Identitas Mahasiswa & Tugas](#-identitas-mahasiswa--tugas)
2. [Latar Belakang & Ringkasan Proyek](#-latar-belakang--ringkasan-proyek)
3. [Bagian 1: Algoritma Pencarian (Search Algorithms)](#-bagian-1-algoritma-pencarian-search-algorithms)
   - [Uninformed Search (Pencarian Buta)](#1-uninformed-search-pencarian-buta)
   - [Informed Search (Pencarian Berheuristik)](#2-informed-search-pencarian-berheuristik)
   - [Tabel Komparasi & Analisis Kompleksitas](#3-tabel-komparasi--analisis-kompleksitas)
4. [Bagian 2: Sistem Pakar Medis Kardiovaskular (Expert System)](#-bagian-2-sistem-pakar-medis-kardiovaskular-expert-system)
   - [Konsep Dasar & Arsitektur Sistem](#1-konsep-dasar--arsitektur-sistem)
   - [Metode Inferensi: Backward Chaining vs Forward Chaining](#2-metode-inferensi-backward-chaining-vs-forward-chaining)
   - [Basis Pengetahuan (Knowledge Base) Penyakit & Gejala](#3-basis-pengetahuan-knowledge-base-penyakit--gejala)
   - [Struktur & Peran Setiap File C++](#4-struktur--peran-setiap-file-c)
5. [Bagian 3: Multi-Agent System — Pemantau Karhutla Kubu Raya](#-bagian-3-multi-agent-system--pemantau-karhutla-kubu-raya)
   - [Gambaran Umum](#1-gambaran-umum)
   - [Enam Agen & Perannya](#2-enam-agen--perannya)
   - [Komunikasi Antaragen & Konsensus](#3-komunikasi-antaragen--konsensus)
   - [Dua Mode Lingkungan](#4-dua-mode-lingkungan)
   - [Hasil & Keterbatasan](#5-hasil--keterbatasan)
6. [Struktur Direktori Repositori](#-struktur-direktori-repositori)
7. [Panduan Eksekusi Program (How to Run)](#-panduan-eksekusi-program-how-to-run)
8. [Contoh Output Program Sistem Pakar](#-contoh-output-program-sistem-pakar)
9. [Lisensi & Etika Akademik](#-lisensi--etika-akademik)

---

## 👨‍🎓 Identitas Mahasiswa & Tugas

| Data | Keterangan |
| :--- | :--- |
| **Nama Mahasiswa** | **FATIH DZUMALIN RAHIM SULASTOMO**, **FATHI ARASY**, **MUHAMAD JIDAN FIRZANA** |
| **Program Studi** | S1 Teknik Elektro |
| **Institusi** | Universitas Telkom |
| **Mata Kuliah** | Kecerdasan Buatan (*Artificial Intelligence*) |
| **Kode Kelompok** | **AI-TE01** |
| **Cakupan Tugas** | 1. Implementasi & Komparasi *Search Algorithms*<br>2. Pengembangan *Rule-Based Medical Expert System*<br>3. Pengembangan *Multi-Agent System* (Mesa) untuk pemantauan karhutla |

---

## 📖 Latar Belakang & Ringkasan Proyek

Kecerdasan Buatan (*Artificial Intelligence*) berakar pada tiga pilar pemecahan masalah:
1. **State-Space Search (Pencarian Ruang Keadaan)**: Bagaimana suatu agen cerdas menemukan urutan aksi atau jalur terbaik dari titik awal (*Initial State*) menuju kondisi tujuan (*Goal State*).
2. **Knowledge-Based Reasoning (Penalaran Berbasis Pengetahuan)**: Bagaimana sistem dapat merepresentasikan kepakaran manusia dalam bentuk aturan logis formal untuk mengambil keputusan inferensial yang akurat layaknya seorang ahli.
3. **Multi-Agent System (Sistem Multi-Agen)**: Bagaimana beberapa agen otonom, masing-masing dengan pandangan terbatas, saling bertukar pesan dan mencapai konsensus untuk menyelesaikan masalah yang tidak bisa dipecahkan satu agen saja.

Repositori ini menyatukan ketiga konsep tersebut dalam bentuk kode yang siap dieksekusi, terstruktur rapi, dan terdokumentasi secara mendalam.

---

## 🔍 Bagian 1: Algoritma Pencarian (Search Algorithms)

Modul ini tersimpan di dalam folder **[`Search_Algorithm/`](Search_Algorithm/)** dan memuat implementasi algoritma pencarian dalam berbagai bahasa pemrograman populer.

### 1. Uninformed Search (Pencarian Buta)
Algoritma yang tidak memiliki informasi tambahan mengenai seberapa dekat suatu simpul (*node*) dengan tujuan di luar definisi ruang keadaan:

* **Linear Search ($O(n)$)**:
  * Memeriksa elemen array satu per satu secara berurutan dari indeks 0 hingga indeks terakhir.
  * *Kelebihan*: Fleksibel, data tidak perlu diurutkan terlebih dahulu.
  * *Kelemahan*: Sangat lambat untuk dataset berukuran besar.
* **Binary Search ($O(\log n)$)**:
  * Menggunakan paradigma *Divide and Conquer* dengan memeriksa elemen tengah (`mid`). Rentang pencarian dipangkas separuh pada setiap iterasi.
  * *Syarat Mutlak*: Data **wajib sudah terurut** (*sorted*).
* **Breadth-First Search / BFS ($O(V + E)$)**:
  * Menelusuri graf lapis demi lapis (*level-by-level*) dari simpul awal menggunakan struktur data antrean **Queue (FIFO - First In, First Out)**.
  * *Sifat*: Menjamin solusi terpendek berdasarkan jumlah langkah/lompatan (*hop*) pada graf tanpa bobot.
* **Depth-First Search / DFS ($O(V + E)$)**:
  * Menelusuri graf ke cabang terdalam sebelum mundur (*backtracking*) menggunakan struktur data tumpukan **Stack (LIFO - Last In, First Out)** atau pemanggilan rekursif.
  * *Sifat*: Sangat hemat memori untuk struktur graf/pohon yang lebar.
* **Uniform Cost Search / UCS ($O((V + E) \log V)$)**:
  * Varian BFS untuk graf berbobot (*weighted graph*). Menggunakan **Priority Queue (Min-Heap)** untuk selalu mengevaluasi simpul dengan total biaya kumulatif terkecil $g(n)$.
* **Iterative Deepening DFS / IDDFS ($O(b^d)$)**:
  * Menjalankan DFS berulang kali dengan batas kedalaman (*depth limit*) yang bertambah secara bertahap ($0, 1, 2, \dots, d$).
  * *Sifat*: Memiliki keunggulan kelengkapan solusi seperti BFS, namun tetap mempertahankan efisiensi memori DFS ($O(bd)$).

### 2. Informed Search (Pencarian Berheuristik)
Algoritma yang memanfaatkan fungsi perkiraan jarak/biaya (*heuristic function*) untuk mengarahkan pencarian secara lebih cerdas:

* **A\* Search ($O(b^d)$)**:
  * Menggabungkan biaya riil yang telah ditempuh $g(n)$ dengan estimasi biaya menuju target $h(n)$ melalui fungsi evaluasi:
    $$\mathbf{f(n) = g(n) + h(n)}$$
  * Menghasilkan rute paling optimal jika fungsi heuristik bersifat *admissible* (tidak pernah melebih-lebihkan biaya riil).
* **Dijkstra's Algorithm ($O((V + E) \log V)$)**:
  * Menemukan jarak terpendek dari satu simpul asal ke **seluruh simpul lainnya** pada graf dengan bobot non-negatif menggunakan *Priority Queue*.

### 3. Tabel Komparasi & Analisis Kompleksitas

| Algoritma | Kategori | Waktu (Terburuk) | Ruang (Memori) | Kelengkapan (*Complete*) | Optimalitas (*Optimal*) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Linear Search** | Array Traversal | $O(n)$ | $O(1)$ | Ya | Ya |
| **Binary Search** | Divide & Conquer | $O(\log n)$ | $O(1)$ | Ya | Ya (pada array terurut) |
| **BFS** | Uninformed Graph | $O(V + E)$ | $O(V)$ | Ya (jika $b$ hingga) | Ya (jika bobot seragam) |
| **DFS** | Uninformed Graph | $O(V + E)$ | $O(V)$ | Tidak (pada ruang tak hingga) | Tidak |
| **UCS** | Uninformed Weighted | $O((V + E) \log V)$ | $O(V)$ | Ya (jika cost $\ge \epsilon > 0$) | Ya |
| **IDDFS** | Depth-Bounded DFS | $O(b^d)$ | $O(bd)$ | Ya | Ya (jika bobot seragam) |
| **Dijkstra** | Shortest Path | $O((V + E) \log V)$ | $O(V)$ | Ya | Ya |
| **A\* Search** | Informed Heuristic | $O(b^d)$ | $O(b^d)$ | Ya | Ya (jika heuristik *admissible*) |

---

## 🩺 Bagian 2: Sistem Pakar Medis Kardiovaskular (Expert System)

Modul ini tersimpan di dalam folder **[`Expert-System-Implementation-main/`](Expert-System-Implementation-main/)**, dibangun dalam bahasa C++ native untuk mendiagnosis penyakit jantung dan menentukan terapi medis yang tepat.

### 1. Konsep Dasar & Arsitektur Sistem

Sistem pakar ini terdiri atas 3 komponen arsitektur utama:
```text
┌────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                         │
│       (Konsol Interaktif CLI dalam Bahasa Indonesia)           │
└────────────────────────────────┬───────────────────────────────┘
                                 │ Pertanyaan Gejala & Respon Y/N
                                 ▼
┌────────────────────────────────────────────────────────────────┐
│                       INFERENCE ENGINE                         │
│  1. Backward Chaining Engine  ──>  Menentukan Diagnosis        │
│  2. Forward Chaining Engine   ──>  Menentukan Terapi & Obat    │
└────────────────────────────────┬───────────────────────────────┘
                                 │ Pengecekan Aturan & Gejala
                                 ▼
┌────────────────────────────────────────────────────────────────┐
│                        KNOWLEDGE BASE                          │
│  • 6 Kategori Penyakit Kardiovaskular                          │
│  • 21 Gejala Klinis Terstandarisasi                            │
│  • 36 Aturan Diagnosis (Rules Matrix)                          │
│  • 8 Paket Terapi & Rekomendasi Farmakologis                   │
└────────────────────────────────────────────────────────────────┘
```

### 2. Metode Inferensi: Backward Chaining vs Forward Chaining

Sistem ini memadukan **dua teknik penalaran logis** secara harmonis:

#### A. Backward Chaining (Goal-Driven Reasoning)
* **Tujuan**: Menentukan jenis diagnosis penyakit jantung.
* **Mekanisme Kerja**:
  1. Sistem menetapkan hipotesis penyakit terlebih dahulu (misal: *Gagal Jantung*).
  2. Sistem mencari aturan (*rules*) yang dapat membuktikan hipotesis tersebut.
  3. Sistem memeriksa gejala-gejala yang menjadi premis aturan tersebut. Jika data gejala belum ada, sistem akan bertanya secara interaktif kepada pengguna:
     > *"Apakah pasien mengalami: Nyeri Dada? [Ketik Y untuk Ya / T untuk Tidak]"*
  4. Jika suatu gejala tidak terpenuhi (`False`), aturan tersebut gugur dan sistem berpindah ke aturan hipotesis berikutnya menggunakan struktur data **`conclusion_stack`**.
  5. Proses berulang hingga hipotesis terbukti benar atau seluruh kemungkinan aturan habis.

#### B. Forward Chaining (Data-Driven Reasoning)
* **Tujuan**: Menentukan rekomendasi pengobatan, tindakan medis, dan terapi obat.
* **Mekanisme Kerja**:
  1. Setelah tahap Backward Chaining berhasil menyimpulkan penyakit yang dialami pasien, hasil diagnosis tersebut dijadikan **fakta awal** (*Initial Fact*).
  2. Mesin Forward Chaining mengevaluasi basis pengetahuan pengobatan untuk mencocokkan kondisi patofisiologis pasien (seperti tekanan darah tinggi, penumpukan cairan, atau risiko penggumpalan darah).
  3. Sistem mengalirkan inferensi ke depan (*forward*) untuk memicu (*fire*) rekomendasi obat yang sesuai (misal: pemberian *Diuretik*, *ACE-Inhibitor*, atau *Statin*).

### 3. Basis Pengetahuan (Knowledge Base) Penyakit & Gejala

#### 🏥 6 Penyakit Jantung yang Didiagnosis:
1. **Gagal Jantung (*Heart Failure*)**
2. **Kardiomiopati (*Cardiomyopathy*)**
3. **Angina Pectoris (*Angina*)**
4. **Penyakit Jantung Koroner (*Coronary Artery Disease*)**
5. **Takikardia (*Tachycardia*)**
6. **Takikardia Ventrikel (*Ventricular Tachycardia*)**

#### 📋 21 Variabel Gejala Klinis (`variables_list`):
* `0`: Detak Jantung Cepat/Tidak Teratur atau Berdebar-debar (Palpitasi)
* `1`: Nyeri Dada
* `2`: Sesak Napas Terus-Menerus
* `3`: Kelelahan Ekstrem / Mudah Lelah
* `4`: Pusing (*Dizziness*)
* `5`: Kepala Terasa Ringan / Melayang
* `6`: Tubuh Lemas / Tidak Bertenaga
* `7`: Keringat Dingin Berlebih Tanpa Sebab Jelas
* `8`: Pingsan / Kehilangan Kesadaran
* `9`: Kenaikan Berat Badan Mendadak (Penumpukan Cairan)
* `10`: Edema (Pembengkakan Kaki/Pergelangan Kaki)
* `11`: Perut Kembung / Membengkak (Asites)
* `12`: Kebingungan / Linglung
* `13`: Rasa Tertekan / Sesak di Dada
* `14`: Muntah
* `15`: Gelisah / Tidak Tenang
* `16`: Riwayat Serangan Jantung
* `17`: Mual
* `18`: Rasa Tertekan atau Nyeri Menjalar ke Leher
* `19`: Riwayat Henti Jantung Mendadak
* `20`: Kongesti / Penumpukan Cairan di Paru-paru

#### 💊 Paket Rekomendasi Terapi & Farmakologis:
* **Hipertensi & Beban Jantung** $\rightarrow$ *Obat ACE Inhibitor / ARB Blockers*
* **Penumpukan Cairan (Edema)** $\rightarrow$ *Obat Diuretik / Antagonis Aldosteron*
* **Inflamasi Miokardium** $\rightarrow$ *Kortikosteroid*
* **Penyempitan Pembuluh & Nyeri Dada** $\rightarrow$ *Nitrat*
* **Kadar Kolesterol Tinggi** $\rightarrow$ *Statin (Penurun Kolesterol)*
* **Aritmia Ringan** $\rightarrow$ *Manuver Vagal*
* **Risiko Trombus / Penggumpalan Darah** $\rightarrow$ *Antiplatelet (Clopidogrel, Ticagrelor) / Aspirin*

### 4. Struktur & Peran Setiap File C++

| Nama File | Peran & Tanggung Jawab |
| :--- | :--- |
| **`Project1-A05071238.cpp`** | Titik masuk utama program (`main()`). Menampilkan teks pembuka dan menginisiasi siklus inferensi. |
| **`knowledge_base-...h`** | Menyimpan daftar penyakit, 21 gejala klinis, dan 36 matriks kombinasi aturan inferensi backward. |
| **`rules-...h`** | Mesin inferensi Backward Chaining. Mengelola interaksi input pengguna (`Y/T`), tumpukan hipotesis (`conclusion_stack`), dan penentuan kesimpulan diagnosis. |
| **`forward_knowledge_base-...h`** | Basis pengetahuan terapi, relasi penyakit dengan kondisi patologis, serta daftar obat. |
| **`forward_rules-...h`** | Mesin inferensi Forward Chaining. Mengambil diagnosis penyakit terkonfirmasi dan menurunkan rekomendasi obat/terapi secara otomatis. |
| **`expert_system.exe`** | Binary hasil kompilasi *static linking* yang siap dieksekusi langsung di lingkungan Windows tanpa dependensi DLL eksternal. |

---

## 🛰️🔥 Bagian 3: Multi-Agent System — Pemantau Karhutla Kubu Raya

> Kode lengkap, pengujian, dan dokumentasi teknis ada di [`Multi-Agent-System/`](Multi-Agent-System/README.md).

### 1. Gambaran Umum

*Multi-Agent System* (MAS) adalah sistem yang tersusun dari beberapa agen otonom. Tiap agen hanya melihat sebagian
masalah, lalu mereka berkoordinasi lewat pesan untuk mencapai tujuan bersama. Pada tugas ini MAS dibangun dengan
**[Mesa](https://github.com/mesa/mesa)** (Python) untuk **memantau kebakaran hutan dan lahan (karhutla)** dari citra
satelit, dengan satu prinsip: **tidak ada peringatan tanpa kesepakatan dua sumber bukti yang berbeda.**

- Satu sumber bukti saja mudah salah. Penurunan NDVI (kehijauan) bisa disebabkan awan, kabut, atau panen. Titik api
  bisa berasal dari sumber panas lain.
- Karena itu, agen yang membaca citra dan agen yang memeriksa bukti api harus **sepakat** sebelum peringatan dikirim.
- Cakupan: satu kecamatan dalam satu waktu di **Kabupaten Kubu Raya, Kalimantan Barat** (9 kecamatan), diperbarui
  tiap 14 hari. Sistem fokus pada kebakarannya dan tidak membedakan jenis lahan atau penyebab pembakaran.

| Aspek | Pada tugas ini |
| :--- | :--- |
| Kerangka kerja | Mesa 3.x (`mesa.Model`, `mesa.Agent`, `DataCollector`) |
| Jumlah agen | 6 jenis (detektor dan validator bisa lebih dari satu) |
| Bahasa pesan | Gaya **FIPA-ACL**: `inform`, `request`, `propose`, `confirm`, `cancel` |
| Data | Simulasi sintetis (ada *ground truth*) dan data nyata Google Earth Engine |
| Antarmuka | Terminal dan halaman web lokal dengan peta |

### 2. Enam Agen & Perannya

| # | Agen | Kelas | Tugas | Tipe agen |
| :-: | :--- | :--- | :--- | :--- |
| 1 | **Pengunduh** | `DataIngestionAgent` | Mengambil citra periode baru dari penyimpanan/GEE, mengulang unduhan yang gagal, lalu memberi tahu agen lain. | *Simple reflex* |
| 2 | **Titik Api** | `HotspotAgent` | Peringatan dini langsung dari titik api VIIRS sampai hari ini, tanpa menunggu citra bebas awan. Titik yang bersebelahan dijadikan satu klaster. | *Simple reflex* + klaster |
| 3 | **Deteksi Perubahan** | `ChangeDetectionAgent` | Membandingkan NDVI Sentinel-2 dengan pengamatan bersih terakhir dan mencari penurunan drastis yang menetap. Mengajukan kasus untuk divalidasi. | *Model-based* (menyimpan acuan dan riwayat kasus) |
| 4 | **Validasi** | `ValidationAgent` | Memeriksa bukti api (titik api / anomali termal) di lokasi kasus dan memberi suara *kuat* atau *lemah*. | *Goal/utility-based* |
| 5 | **Pengelompokan Kejadian** | `IncidentAgent` | Menyatukan bekas terbakar yang berjarak < 500 m menjadi satu kejadian dan menautkannya ke klaster titik api penyebabnya. | *Model-based* |
| 6 | **Notifikasi** | `NotificationAgent` | Menetapkan prioritas dan kanal tujuan, mengirim peringatan, memperbarui peringatan bila area meluas, dan mencegah laporan ganda. | *Utility-based* |

Urutan eksekusi pada tiap langkah Mesa: Pengunduh → Titik Api → Deteksi → Validasi → Pengelompokan → Notifikasi.
Satu langkah = satu hari (simulasi) atau satu periode 14 hari (data Sentinel-2).

### 3. Komunikasi Antaragen & Konsensus

```text
 Pengunduh ──INFORM new_scene──▶ Deteksi ──REQUEST validate──▶ Validasi
                                    ▲                              │
                                    └─────── PROPOSE verdict ──────┘
                 CONFIRM / CANCEL (konsensus) ──▶ Validasi

 Deteksi ──INFORM report──▶ Pengelompokan ──INFORM incident──▶ Notifikasi ──▶ Satgas Karhutla / BPBD
 Titik Api ──INFORM hotspot──▶ Notifikasi (peringatan dini) dan Pengelompokan (penaut penyebab)
```

Setiap kasus punya `conversation_id`, sehingga seluruh percakapan agen untuk satu kasus bisa ditelusuri dari awal
sampai akhir (tersedia di tab "Pesan antaragen" pada halaman web).

**Aturan konsensus** (dua bukti independen):

| Suara Deteksi (NDVI turun dan menetap?) | Suara Validasi (ada bukti api?) | Keputusan |
| :---: | :---: | :--- |
| ya | ya | ✅ **CONFIRMED**, peringatan dikirim |
| tidak (NDVI pulih) | tidak / lemah | ❌ **DISMISSED** (alarm palsu: awan, kabut, panen) |
| berbeda | berbeda | 🔁 ronde ulang dengan data periode berikutnya |
| masih berbeda | masih berbeda | ⚠️ **UNCERTAIN**, diserahkan ke analis |

**Jalur cepat kebakaran**: penurunan NDVI ditambah titik api di lokasi yang sama sudah dua bukti independen, jadi
kasus langsung dikonfirmasi tanpa menunggu citra bersih berikutnya. Suara *lemah* (misalnya hanya "tidak ada api")
tidak dapat mengalahkan pengamatan bahwa NDVI sudah pulih.

**Dua jenis peringatan yang dikeluarkan:**

| Jenis | Sumber | Prioritas | Kanal |
| :--- | :--- | :---: | :--- |
| Titik api aktif | Agen Titik Api (VIIRS) | DARURAT | Satgas Karhutla / BPBD |
| Bekas terbakar terkonfirmasi | Konsensus Deteksi + Validasi, dikelompokkan Agen Pengelompokan | TINGGI | Satgas Karhutla / BPBD |

### 4. Dua Mode Lingkungan

| | Simulasi sintetis | Data nyata (Kubu Raya) |
| :--- | :--- | :--- |
| Data | Hutan 64×64 sel dengan kebakaran, tebang liar, dan awan pengecoh buatan | Sentinel-2 (NDVI 30 m, Cloud Score+) dan titik api VIIRS lewat Google Earth Engine |
| Awan | Penurunan NDVI palsu yang harus disaring | Data bolong (NaN); agen menunggu citra bersih |
| Ukuran kinerja | Recall, precision, akurasi penyebab, latensi (ada *ground truth*) | Belum ada *ground truth*; hasil diperiksa lewat peta dan riwayat peringatan |
| Skrip | `run_simulation.py` | `run_pantau.py`, `web_pantau.py` |

Halaman web (`web_pantau.py`) memungkinkan memilih kecamatan, menjalankan pemantauan, melihat titik api dan bekas
terbakar pada peta satelit, lalu membuka keluaran tiap agen secara terpisah.

### 5. Hasil & Keterbatasan

Pada simulasi 120 hari (seed 42), konsensus dua agen dibandingkan dengan detektor tunggal:

| Metrik | MAS (konsensus) | Detektor tunggal |
| :--- | ---: | ---: |
| Alarm palsu | **0** | 12 |
| Recall | 1,00 | 1,00 |
| Precision | **1,00** | 0,71 |
| Akurasi penyebab | 1,00 | – |
| Latensi rata-rata (hari) | 1,20 | 0,20 |

Konsensus menghilangkan alarm palsu dengan harga latensi sekitar 1 hari. Pada data nyata Kubu Raya, jalur cepat
kebakaran dan klaster titik api bekerja pada uji lapangan, tetapi:

- Titik api VIIRS bukan kepastian kebakaran (sumber panas lain bisa terdeteksi), dan sistem tidak membedakan
  pembakaran yang disengaja dari yang tidak.
- Recall pada data nyata belum bisa dihitung. Pembanding independen yang disarankan: produk area terbakar
  `MODIS/061/MCD64A1`.
- Terra/Aqua (MODIS) dan Suomi NPP akan berhenti beroperasi/mengirim data sekitar akhir 2026, sehingga sumber titik
  api perlu dipantau ulang dengan `python run_pantau.py --status`.
- Ambang deteksi masih nilai awal dan perlu dikalibrasi pada kejadian nyata. Panggilan GEE sungguhan belum bisa diuji
  otomatis; pengujian otomatis (65 tes) memakai data tiruan.

---

## 📂 Struktur Direktori Repositori

```text
AI-TE01/
│
├── Search_Algorithm/                       # MODUL 1: ALGORITMA PENCARIAN
│   ├── A Search/                           # Implementasi Algoritma A* (Informed Search)
│   ├── Binary_Search/                      # Implementasi Binary Search
│   ├── Breadth_First_Search/               # Implementasi Breadth-First Search (BFS)
│   ├── Depth_First_Search/                 # Implementasi Depth-First Search (DFS)
│   ├── Dijkstra's_Algorithm/               # Implementasi Algoritma Dijkstra
│   ├── Iterative Deepening DFS Algorithm/  # Implementasi IDDFS
│   ├── Linear_Search/                      # Implementasi Linear Search
│   ├── Uniform_Cost_Search/                # Implementasi Uniform Cost Search (UCS)
│   ├── run_all.py                          # 🔥 Runner demo interaktif seluruh algoritma
│   └── README.md                           # Dokumentasi teknis Search Algorithms
│
├── Expert-System-Implementation-main/      # MODUL 2: SISTEM PAKAR (EXPERT SYSTEM)
│   ├── Project1-SubmittedFiles/
│   │   ├── Project1-A05071238.cpp          # Kode sumber utama C++ (Bahasa Indonesia)
│   │   ├── knowledge_base-...h             # Basis pengetahuan diagnosis & gejala
│   │   ├── rules-...h                      # Mesin inferensi Backward Chaining
│   │   ├── forward_knowledge_base-...h     # Basis pengetahuan terapi & tindakan
│   │   ├── forward_rules-...h              # Mesin inferensi Forward Chaining
│   │   ├── expert_system.exe               # File biner mandiri (Standalone executable)
│   │   └── Project-1-A05071238-Bigyan.pdf  # Laporan referensi ilmiah proyek
│   └── README.md
│
├── Multi-Agent-System/                     # MODUL 3: MULTI-AGENT SYSTEM (MESA)
│   ├── deforestation_mas/                  # Paket utama: agen, pesan, model, lingkungan
│   │   ├── agents.py                       # 6 agen + logika konsensus
│   │   ├── messaging.py                    # MessageBus & pesan bergaya FIPA-ACL
│   │   ├── model.py                        # mesa.Model: pipeline agen & DataCollector
│   │   ├── environment.py                  # lingkungan satelit sintetis + ground truth
│   │   ├── sentinel_environment.py         # data nyata: Sentinel-2 + VIIRS (periode 14 hari)
│   │   └── gee_environment.py              # replay data MODIS dari Google Earth Engine
│   ├── data/                               # Batas 9 kecamatan Kabupaten Kubu Raya (GeoJSON)
│   ├── web/index.html                      # Halaman web: peta, kecamatan, keluaran tiap agen
│   ├── run_simulation.py                   # Simulasi sintetis
│   ├── run_pantau.py                       # Pemantauan 2 mingguan per kecamatan
│   ├── web_pantau.py                       # Server web lokal
│   ├── tests/                              # 65 pengujian (pytest)
│   └── README.md                           # Dokumentasi teknis Multi-Agent System
│
└── README.md                               # Dokumentasi & laporan utama repositori tugas
```

---

## 🚀 Panduan Eksekusi Program (How to Run)

### 1. Menjalankan Sistem Pakar (Expert System)

#### Opsi A: Langsung Eksekusi Binary Mandiri (Tanpa Perlu Compile)
Buka terminal PowerShell atau Command Prompt pada folder proyek:

```powershell
cd Expert-System-Implementation-main\Project1-SubmittedFiles
.\expert_system.exe
```

#### Opsi B: Kompilasi Ulang dari Sumber Kode C++
Jika ingin mengompilasi ulang kode sumber:

```powershell
cd Expert-System-Implementation-main\Project1-SubmittedFiles
g++ -std=c++17 -static Project1-A05071238.cpp -o expert_system.exe
.\expert_system.exe
```

> **Catatan Kompilasi**: Flag `-static` digunakan agar binary menyertakan seluruh dependensi C++ runtime secara mandiri, sehingga tidak akan mengalami galat *missing DLL* (`libstdc++-6.dll`).

---

### 2. Menjalankan Algoritma Pencarian (Search Algorithms)

Untuk menguji seluruh algoritma pencarian sekaligus beserta data sampel:

```powershell
python Search_Algorithm/run_all.py
```

Output akan langsung menampilkan perbandingan indeks hasil pencarian, urutan kunjungan traversal graf (*BFS* dan *DFS*), serta penghitungan biaya jalur terpendek (*Dijkstra* dan *UCS*).

---

### 3. Menjalankan Multi-Agent System (Mesa)

Prasyarat: Python 3.10+ dan `pip install -r Multi-Agent-System/requirements.txt`.

```powershell
# Simulasi sintetis (tanpa akun apa pun): MAS vs detektor tunggal
Jalankan_Multi_Agent_System.bat
# atau
cd Multi-Agent-System
python run_simulation.py --compare
```

Pemantauan data nyata Kubu Raya memerlukan akun Google Earth Engine (`earthengine authenticate` sekali saja):

```powershell
pip install -r Multi-Agent-System/requirements-gee.txt
Buka_Web_Pantau.bat              # halaman web: http://127.0.0.1:8765
Pantau_Kubu_Raya.bat "Sungai Raya"   # versi terminal untuk satu kecamatan
```

Detail opsi, penjadwalan otomatis, dan format keluaran ada di [`Multi-Agent-System/README.md`](Multi-Agent-System/README.md).

---

## 💻 Contoh Output Program Sistem Pakar

Berikut adalah contoh sesi eksekusi interaktif saat mendiagnosis pasien:

```text
=======================================================================
  SISTEM PAKAR: DIAGNOSIS & REKOMENDASI PENGOBATAN PENYAKIT JANTUNG    
=======================================================================

Silakan jawab pertanyaan gejala berikut untuk mendiagnosis pasien.

Apakah pasien mengalami: Detak Jantung Cepat/Tidak Teratur atau Berdebar-debar (Palpitasi)?
[Ketik Y untuk Ya / T untuk Tidak]: Y

Apakah pasien mengalami: Nyeri Dada?
[Ketik Y untuk Ya / T untuk Tidak]: Y

Apakah pasien mengalami: Tubuh Lemas / Tidak Bertenaga?
[Ketik Y untuk Ya / T untuk Tidak]: Y


=======================================================================
                       HASIL DIAGNOSIS SISTEM PAKAR                    
=======================================================================

Pasien teridentifikasi memiliki gejala-gejala berikut:
  * Detak Jantung Cepat/Tidak Teratur atau Berdebar-debar (Palpitasi)
  * Nyeri Dada
  * Tubuh Lemas / Tidak Bertenaga

>>> KESIMPULAN DIAGNOSIS:
    Pasien kemungkinan menderita: Gagal Jantung (Heart Failure)
    (Disarankan melakukan tes medis lanjutan untuk konfirmasi kondisi).

-----------------------------------------------------------------------
            REKOMENDASI PENGOBATAN & TINDAKAN KLINIS (FORWARD CHAIN)   
-----------------------------------------------------------------------

- Kondisi Klinis Terkait : Tekanan darah tinggi dan perkembangan penyakit
  -> Terapi / Rekomendasi : OBAT ACE INHIBITOR / ARB BLOCKERS

- Kondisi Klinis Terkait : Penumpukan cairan tubuh
  -> Terapi / Rekomendasi : OBAT DIURETIK / ANTAGONIS ALDOSTERON

=======================================================================
  Terima kasih telah menggunakan Sistem Pakar Diagnosis Jantung!
=======================================================================
```

---

## 📜 Lisensi & Etika Akademik

Karya dan kode program pada repositori ini disusun untuk memenuhi kewajiban akademik mata kuliah **Kecerdasan Buatan (AI-TE01)** pada Program Studi **S1 Teknik Elektro, Universitas Telkom**. Seluruh kode dilisensikan di bawah lisensi terbuka [Apache License 2.0](Search_Algorithm/LICENSE).
