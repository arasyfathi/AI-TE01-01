# 🩺 Sistem Pakar Diagnosis & Rekomendasi Terapi Penyakit Jantung (Heart Disease Expert System)

<p align="center">
  <b>Implementasi Sistem Pakar Medis Berbasis Aturan (Rule-Based Expert System) Menggunakan Kombinasi Penalaran Backward Chaining & Forward Chaining dalam Bahasa C++</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Bahasa-C%2B%2B17-00599C.svg?style=flat-square&logo=c%2B%2B" alt="C++17">
  <img src="https://img.shields.io/badge/Paradigma-Rule--Based%20Inference-darkgreen.svg?style=flat-square" alt="Rule-Based">
  <img src="https://img.shields.io/badge/Kompilasi-Static%20Linking%20(Standalone)-orange.svg?style=flat-square" alt="Static Linking">
  <img src="https://img.shields.io/badge/Status-Lengkap%20%26%20Teruji-brightgreen.svg?style=flat-square" alt="Status">
</p>

---

## 📌 Daftar Isi
1. [Deskripsi Proyek](#-deskripsi-proyek)
2. [Latar Belakang Klinis & Masalah](#-latar-belakang-klinis--masalah)
3. [Arsitektur Sistem & Alur Inferensi Dual-Chaining](#-arsitektur-sistem--alur-inferensi-dual-chaining)
   - [Fase 1: Backward Chaining (Penegakan Diagnosis)](#fase-1-backward-chaining-penegakan-diagnosis)
   - [Fase 2: Forward Chaining (Rekomendasi Terapi & Obat)](#fase-2-forward-chaining-rekomendasi-terapi--obat)
4. [Basis Pengetahuan (Knowledge Base)](#-basis-pengetahuan-knowledge-base)
   - [Daftar 6 Penyakit Kardiovaskular (Goals)](#1-daftar-6-penyakit-kardiovaskular-goals)
   - [Daftar 21 Variabel Gejala Klinis (Premises)](#2-daftar-21-variabel-gejala-klinis-premises)
   - [Matriks Aturan Diagnosis (Rule Matrix)](#3-matriks-aturan-diagnosis-rule-matrix)
   - [Katalog Terapi & Tindakan Medis](#4-katalog-terapi--tindakan-medis)
5. [Struktur Data & Optimasi Algoritma](#-struktur-data--optimasi-algoritma)
6. [Struktur Berkas Proyek](#-struktur-berkas-proyek)
7. [Panduan Kompilasi & Menjalankan Program](#-panduan-kompilasi--menjalankan-program)
8. [Simulasi Kasus Klinis (Uji Coba Sistem)](#-simulasi-kasus-klinis-uji-coba-sistem)

---

## 📖 Deskripsi Proyek

Program ini merupakan **Sistem Pakar Medis Klinis (*Clinical Decision Support System*)** interaktif berbasis Command Line Interface (CLI) yang dirancang untuk membantu tenaga medis atau pengguna dalam:
1. **Mengidentifikasi dan mendiagnosis jenis penyakit kardiovaskular (jantung)** berdasarkan serangkaian gejala klinis yang dialami pasien.
2. **Memberikan rekomendasi intervensi medis, terapi obat, serta tindakan klinis yang sesuai** segera setelah diagnosis berhasil ditegakkan.

Seluruh antarmuka program, pertanyaan gejala klinis, serta penjelasan diagnosis telah disajikan dalam **Bahasa Indonesia medis yang baku dan komunikatif**.

---

## 🩺 Latar Belakang Klinis & Masalah

Penyakit kardiovaskular merupakan salah satu penyebab kematian tertinggi di dunia. Gejala awal penyakit jantung (seperti nyeri dada, sesak napas, kelelahan, atau edema) sering kali memiliki kemiripan (*overlap*) antar satu kondisi dengan kondisi lainnya. 

Sistem pakar ini mereplikasi alur berpikir seorang dokter spesialis kardiologi (*cardiologist*) dengan menyusun basis pengetahuan formal dan aturan inferensi terstruktur, sehingga proses penapisan (*screening*) dan pengambilan keputusan klinis dapat berlangsung secara cepat, konsisten, dan transparan.

---

## ⚙️ Arsitektur Sistem & Alur Inferensi Dual-Chaining

Sistem ini menerapkan pendekatan **Dual-Chaining** yang memisahkan proses penegakan diagnosis dengan proses perumusan terapi pengobatan:

```text
       [ INPUT PENGGUNA ]
                │
                ▼ (Respon Y/N terhadap Gejala Klinis)
┌─────────────────────────────────────────────────────────────┐
│ FASE 1: BACKWARD CHAINING (Goal-Driven Reasoning)           │
│                                                             │
│ • Hipotesis Awal (Goal): Penyakit Jantung?                  │
│ • Cek Prasyarat (Premis): Gejala pada Knowledge Base        │
│ • Struktur Data: std::stack & Memoization Map               │
│ • Hasil: Kesimpulan Diagnosis Terbukti Benar                │
└──────────────────────────────┬──────────────────────────────┘
                               │ Diagnosis Terkonfirmasi
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ FASE 2: FORWARD CHAINING (Data-Driven Reasoning)            │
│                                                             │
│ • Fakta Awal (Fact): Hasil Diagnosis Fase 1                 │
│ • Evaluasi Kondisi: Patologi Penyakit (Tekanan Darah, Edema)│
│ • Struktur Data: std::queue & Rule Evaluation               │
│ • Hasil: Rekomendasi Terapi Obat & Tindakan Medis           │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
                   [ OUTPUT DIAGNOSIS & TERAPI ]
```

### Fase 1: Backward Chaining (Penegakan Diagnosis)
* **Paradigma**: *Goal-Driven* (Berorientasi pada Tujuan).
* **Alur Kerja**:
  1. Sistem menetapkan hipotesis target diagnosis terlebih dahulu (misalnya: *Gagal Jantung*).
  2. Sistem menelusuri aturan ke belakang (*backward*) untuk memeriksa gejala-gejala yang menjadi syarat terpenuhinya hipotesis tersebut.
  3. Sistem mengajukan pertanyaan gejala secara langsung kepada pengguna:
     > *"Apakah pasien mengalami: Nyeri Dada? [Ketik Y untuk Ya / T untuk Tidak]"*
  4. **Pencegahan Pertanyaan Berulang (*Memoization*)**: Respon pengguna dicatat ke dalam `std::map`. Jika suatu gejala pernah dijawab sebelumnya, sistem tidak akan menanyakannya kembali.
  5. **Mekanisme *Backtracking***: Jika suatu aturan terbukti salah (ada gejala yang bernilai `Tidak`), sistem secara otomatis mundur (*backtrack*), memperbarui `conclusion_stack`, dan menguji hipotesis aturan penyakit berikutnya hingga ditemukan kecocokan mutlak.

### Fase 2: Forward Chaining (Rekomendasi Terapi & Obat)
* **Paradigma**: *Data-Driven* (Berorientasi pada Data / Fakta).
* **Alur Kerja**:
  1. Hasil diagnosis yang berhasil diputuskan pada Fase 1 dijadikan sebagai **fakta baru (*new fact*)**.
  2. Mesin Forward Chaining mengambil fakta tersebut dan mencocokkannya dengan basis pengetahuan patofisiologi penyakit (seperti beban kerja jantung, retensi cairan, atau peradangan).
  3. Aturan-aturan terapi yang premisnya terpenuhi akan terpicu (*fire*), menghasilkan rekomendasi obat-obatan spesifik seperti *Diuretik*, *ACE-Inhibitor*, *Statin*, atau *Antiplatelet*.

---

## 📚 Basis Pengetahuan (Knowledge Base)

### 1. Daftar 6 Penyakit Kardiovaskular (Goals)
1. **Gagal Jantung (*Heart Failure*)**: Kondisi di mana otot jantung tidak memompa darah sebagaimana mestinya.
2. **Kardiomiopati (*Cardiomyopathy*)**: Penyakit pada otot jantung yang menyebabkan dinding bilik jantung membesar atau menebal.
3. **Angina Pectoris (*Angina*)**: Nyeri dada akibat berkurangnya pasokan darah dan oksigen ke otot jantung.
4. **Penyakit Jantung Koroner (*Coronary Artery Disease*)**: Kerusakan atau penyempitan pada pembuluh darah utama penyuplai jantung akibat plak kolesterol.
5. **Takikardia (*Tachycardia*)**: Kondisi di mana jantung berdetak lebih dari 100 kali per menit saat istirahat.
6. **Takikardia Ventrikel (*Ventricular Tachycardia*)**: Gangguan irama jantung cepat yang berasal dari bilik bawah jantung (ventrikel), berpotensi gawat darurat.

### 2. Daftar 21 Variabel Gejala Klinis (Premises)

| Kode | Nama Gejala Klinis | Keterangan Medis |
| :---: | :--- | :--- |
| `0` | Detak Jantung Cepat/Tidak Teratur atau Berdebar-debar | Palpitasi jantung abnormal |
| `1` | Nyeri Dada (*Chest Pain*) | Sensasi nyeri tajam atau tertusuk di dada |
| `2` | Sesak Napas Terus-Menerus (*Dyspnea*) | Kesulitan bernapas saat istirahat/aktivitas |
| `3` | Kelelahan Ekstrem / Mudah Lelah (*Fatigue*) | Penurunan toleransi aktivitas fisik secara drastis |
| `4` | Pusing (*Dizziness*) | Sensasi berputar atau kehilangan keseimbangan |
| `5` | Kepala Terasa Ringan / Melayang | *Lightheadedness*, perfusi darah ke otak menurun |
| `6` | Tubuh Lemas / Tidak Bertenaga (*Weakness*) | Kelemahan otot menyeluruh |
| `7` | Keringat Dingin Berlebih Tanpa Sebab Jelas | Diaforesis mendadak |
| `8` | Pingsan / Kehilangan Kesadaran (*Syncope*) | Penurunan kesadaran sementara akibat perfusi rendah |
| `9` | Kenaikan Berat Badan Mendadak | Akibat penumpukan cairan tubuh (*fluid retention*) |
| `10` | Edema (Pembengkakan Kaki/Pergelangan Kaki) | Akumulasi cairan di ekstremitas bawah |
| `11` | Perut Kembung / Membengkak (*Ascites*) | Akumulasi cairan rongga peritoneal |
| `12` | Kebingungan / Linglung (*Confusion*) | Penurunan oksigenasi ke sistem saraf pusat |
| `13` | Rasa Tertekan / Sesak Berat di Dada | Sensasi dada tertindih beban berat |
| `14` | Muntah (*Vomiting*) | Reaksi stimulasi vagal |
| `15` | Gelisah / Tidak Tenang (*Restlessness*) | Manifestasi kecemasan hipoksia |
| `16` | Riwayat Serangan Jantung | Riwayat infark miokard akut terdahulu |
| `17` | Mual (*Nausea*) | Rasa tidak nyaman pada saluran cerna atas |
| `18` | Nyeri Menjalar ke Leher, Rahang, atau Lengan | Penjalaran nyeri iskemik khas miokard |
| `19` | Riwayat Henti Jantung Mendadak | Riwayat kolaps kardiovaskular akut |
| `20` | Kongesti / Penumpukan Cairan di Paru-paru | Ronki basah / edema paru kardiogenik |

### 3. Matriks Aturan Diagnosis (Rule Matrix)
Basis pengetahuan menyimpan **36 aturan implikasi logis** berbentuk:
$$\text{IF } (\text{Gejala}_A \land \text{Gejala}_B \land \dots \land \text{Gejala}_N) \implies \text{THEN } \text{Diagnosis}_X$$

Contoh kombinasi aturan:
* **Rule 10**: IF `Detak Jantung Berdebar (0)` AND `Nyeri Dada (1)` AND `Tubuh Lemas (6)` $\implies$ **Gagal Jantung (Heart Failure)**
* **Rule 80**: IF `Nyeri Dada (1)` AND `Sesak Napas (2)` AND `Keringat Dingin (7)` $\implies$ **Angina Pectoris (Angina)**
* **Rule 310**: IF `Detak Jantung Berdebar (0)` AND `Riwayat Serangan Jantung (16)` $\implies$ **Penyakit Jantung Koroner**

### 4. Katalog Terapi & Tindakan Medis
Setelah diagnosis terbukti, Forward Chaining memetakan kondisi patologis dengan terapi farmakologis terbukti:
* **Hipertensi & Perkembangan Penyakit** $\rightarrow$ *Obat ACE Inhibitor / ARB Blockers*
* **Retensi Cairan (Edema/Asites)** $\rightarrow$ *Obat Diuretika / Antagonis Aldosteron*
* **Inflamasi Miokard** $\rightarrow$ *Kortikosteroid*
* **Iskemia / Penyempitan Vaskular** $\rightarrow$ *Nitrat*
* **Hiperkolesterolemia** $\rightarrow$ *Statin (Penurun Kolesterol)*
* **Aritmia Paroksismal** $\rightarrow$ *Manuver Vagal / Obat Anti-Aritmia*
* **Tromboemboli / Penggumpalan Darah** $\rightarrow$ *Antiplatelet (Clopidogrel, Ticagrelor) atau Aspirin*

---

## 🧩 Struktur Data & Optimasi Algoritma

Efisiensi program ini didukung oleh pemilihan struktur data standar C++ yang optimal:

1. **`std::stack<std::pair<int, int>> conclusion_stack`**:
   * Digunakan pada Backward Chaining untuk melacak aturan (*rule number*) dan indeks gejala (*symptom index*) yang sedang aktif dievaluasi.
   * Mendukung operasi *backtracking* efisien ($O(1)$) saat suatu aturan digugurkan.

2. **`std::map<std::string, int> variable_initialized` (Memoization)**:
   * Menyimpan riwayat jawaban pengguna: `-1` (belum ditanyakan), `0` (Tidak / False), `1` (Ya / True).
   * Menghindari redundansi pertanyaan gejala klinis yang sama.

3. **`std::map<int, std::vector<int>> rule_symptoms`**:
   * Memetakan nomor aturan dengan vektor gejala pendukungnya, memungkinkan pencarian aturan dalam waktu konstan $O(1)$.

4. **`std::queue<std::pair<std::string, std::string>> variables_initialized_queue`**:
   * Digunakan pada Forward Chaining untuk memproses rantai implikasi kondisi penyakit ke rekomendasi obat secara FIFO (*First-In-First-Out*).

---

## 📂 Struktur Berkas Proyek

```text
Expert-System-Implementation-main/
│
├── Project1-SubmittedFiles/
│   ├── Project1-A05071238.cpp          # Berkas utama (Driver program)
│   ├── knowledge_base-...h             # Definisi 6 penyakit, 21 gejala, & matriks aturan
│   ├── rules-...h                      # Logika inferensi Backward Chaining
│   ├── forward_knowledge_base-...h     # Basis pengetahuan terapi & kondisi klinis
│   ├── forward_rules-...h              # Logika inferensi Forward Chaining
│   ├── expert_system.exe               # File binary siap eksekusi (Standalone Static)
│   └── Project-1-A05071238-Bigyan.pdf  # Laporan ilmiah & analisis proyek
│
└── README.md                           # Dokumentasi komprehensif sistem pakar
```

---

## 🚀 Panduan Kompilasi & Menjalankan Program

### 1. Menjalankan Langsung (Rekomendasi)
Karena file biner mandiri `expert_system.exe` telah tersedia, buka terminal di folder `Project1-SubmittedFiles` dan jalankan:

```powershell
cd Project1-SubmittedFiles
.\expert_system.exe
```

*(Atau jalankan melalui Command Prompt)*:
```cmd
cd Project1-SubmittedFiles
expert_system.exe
```

---

### 2. Kompilasi Ulang (Re-compilation)
Jika Anda melakukan perubahan pada kode C++ atau berkas header, kompilasi ulang dengan menyertakan opsi **`-static`** (agar binary tidak membutuhkan file DLL eksternal):

```powershell
cd Project1-SubmittedFiles
g++ -std=c++17 -static Project1-A05071238.cpp -o expert_system.exe
.\expert_system.exe
```

---

## 🔬 Simulasi Kasus Klinis (Uji Coba Sistem)

Berikut simulasi sesi interaktif saat seorang pasien terindikasi mengalami **Gagal Jantung (*Heart Failure*)**:

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

*Laporan ilmiah lengkap, diagram alir pohon keputusan, serta analisis medis teoritis dapat dibaca pada berkas PDF di dalam folder `Project1-SubmittedFiles/Project-1-A05071238-Bigyan.pdf`.*
