# 🤖 Repositori Tugas Mata Kuliah Kecerdasan Buatan (AI-TE01)

<p align="center">
  <img src="https://cdn.pixabay.com/animation/2022/08/06/11/57/11-57-26-645_512.gif" alt="AI Project Banner" width="460">
</p>

<p align="center">
  <b>Implementasi Komprehensif: Algoritma Pencarian (Search Algorithms) & Sistem Pakar (Expert System)</b><br>
  Program Studi S1 Teknik Elektro — Fakultas Teknik Elektro — Universitas Telkom
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Mata%20Kuliah-Kecerdasan%20Buatan-0052CC.svg?style=flat-square" alt="Course">
  <img src="https://img.shields.io/badge/Kode%20Kelas-AI--TE01-orange.svg?style=flat-square" alt="Class">
  <img src="https://img.shields.io/badge/Program%20Studi-S1%20Teknik%20Elektro-red.svg?style=flat-square" alt="Major">
  <img src="https://img.shields.io/badge/Bahasa-C%2B%2B%20%7C%20Python-blue.svg?style=flat-square" alt="Languages">
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
5. [Struktur Direktori Repositori](#-struktur-direktori-repositori)
6. [Panduan Eksekusi Program (How to Run)](#-panduan-eksekusi-program-how-to-run)
7. [Contoh Output Program Sistem Pakar](#-contoh-output-program-sistem-pakar)
8. [Lisensi & Etika Akademik](#-lisensi--etika-akademik)

---

## 👨‍🎓 Identitas Mahasiswa & Tugas

| Data | Keterangan |
| :--- | :--- |
| **Nama Mahasiswa** | **FATIH DZUMALIN RAHIM SULASTOMO**, **FATHI ARASY**, **MUHAMAD JIDAN FIRZANA** |
| **Program Studi** | S1 Teknik Elektro |
| **Institusi** | Universitas Telkom |
| **Mata Kuliah** | Kecerdasan Buatan (*Artificial Intelligence*) |
| **Kode Kelompok** | **AI-TE01** |
| **Cakupan Tugas** | 1. Implementasi & Komparasi *Search Algorithms*<br>2. Pengembangan *Rule-Based Medical Expert System* |

---

## 📖 Latar Belakang & Ringkasan Proyek

Kecerdasan Buatan (*Artificial Intelligence*) berakar pada dua pilar fundamental pemecahan masalah:
1. **State-Space Search (Pencarian Ruang Keadaan)**: Bagaimana suatu agen cerdas menemukan urutan aksi atau jalur terbaik dari titik awal (*Initial State*) menuju kondisi tujuan (*Goal State*).
2. **Knowledge-Based Reasoning (Penalaran Berbasis Pengetahuan)**: Bagaimana sistem dapat merepresentasikan kepakaran manusia dalam bentuk aturan logis formal untuk mengambil keputusan inferensial yang akurat layaknya seorang ahli.

Repositori ini menyatukan kedua konsep fundamental tersebut dalam bentuk kode yang siap dieksekusi, terstruktur rapi, dan terdokumentasi secara mendalam.

---

## 🔍 Bagian 1: Algoritma Pencarian (Search Algorithms)

Modul ini tersimpan di dalam folder **[`SearchAlgorithm/`](SearchAlgorithm/)** dan memuat implementasi algoritma pencarian menggunakan Python.

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

## 📂 Struktur Direktori Repositori

```text
AI-TE01/
│
├── SearchAlgorithm/                        # MODUL 1: ALGORITMA PENCARIAN
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
python SearchAlgorithm/run_all.py
```

Output akan langsung menampilkan perbandingan indeks hasil pencarian, urutan kunjungan traversal graf (*BFS* dan *DFS*), serta penghitungan biaya jalur terpendek (*Dijkstra* dan *UCS*).

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

Karya dan kode program pada repositori ini disusun untuk memenuhi kewajiban akademik mata kuliah **Kecerdasan Buatan (AI-TE01)** pada Program Studi **S1 Teknik Elektro, Universitas Telkom**. Seluruh kode dilisensikan di bawah lisensi terbuka [Apache License 2.0](LICENSE).
