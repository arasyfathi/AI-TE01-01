# 🔍 Search Algorithms Collection

<p align="center">
  <img src="https://cdn.pixabay.com/animation/2022/08/06/11/57/11-57-26-645_512.gif" alt="Search Algorithms Banner" width="480">
</p>

<p align="center">
  <b>Koleksi lengkap implementasi algoritma pencarian (Search Algorithms) dalam berbagai bahasa pemrograman populer.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Language-Python%20%7C%20C%2B%2B%20%7C%20Java%20%7C%20JS%20%7C%20C%23%20%7C%20Rust%20%7C%20Swift%20%7C%20R-blue.svg" alt="Languages">
  <img src="https://img.shields.io/badge/License-Apache%202.0-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Maintained%3F-Yes-brightgreen.svg" alt="Maintained">
</p>

---

## 📌 Daftar Isi (Table of Contents)
- [Tentang Repositori](#-tentang-repositori)
- [Struktur Folder & Navigasi](#-struktur-folder--navigasi)
- [Tabel Ringkasan Algoritma & Kompleksitas](#-tabel-ringkasan-algoritma--kompleksitas)
- [Penjelasan Detail Masing-Masing Algoritma](#-penjelasan-detail-masing-masing-algoritma)
  - [1. Linear Search](#1-linear-search)
  - [2. Binary Search](#2-binary-search)
  - [3. Breadth-First Search (BFS)](#3-breadth-first-search-bfs)
  - [4. Depth-First Search (DFS)](#4-depth-first-search-dfs)
  - [5. Dijkstra's Algorithm](#5-dijkstras-algorithm)
  - [6. Uniform Cost Search (UCS)](#6-uniform-cost-search-ucs)
  - [7. A* (A-Star) Search](#7-a-a-star-search)
  - [8. Iterative Deepening DFS (IDDFS)](#8-iterative-deepening-dfs-iddfs)
- [Cara Menjalankan Kode (Quick Start)](#-cara-menjalankan-kode-quick-start)
  - [Menjalankan Semua Algoritma Sekaligus (Python Demo)](#menjalankan-semua-algoritma-sekaligus-python-demo)
  - [Menjalankan Algoritma Spesifik per Bahasa](#menjalankan-algoritma-spesifik-per-bahasa)
- [Bahasa Pemrograman yang Didukung](#-bahasa-pemrograman-yang-didukung)
- [Kontribusi](#-kontribusi)
- [Lisensi](#-lisensi)

---

## 📖 Tentang Repositori

Repositori ini memuat implementasi standar dari algoritma pencarian fundamental, mulai dari pencarian array sederhana (*Linear & Binary Search*), penelusuran graf unweighted (*BFS & DFS*), hingga pencarian jalur terpendek dan berbobot (*Dijkstra, UCS, A\*, dan IDDFS*).

Setiap algoritma disediakan dalam **8 bahasa pemrograman** berbeda:
- 🐍 **Python** (`.py`)
- ☕ **Java** (`.java`)
- ⚡ **C++** (`.cpp`)
- 🔷 **C#** (`.cs`)
- 🌐 **JavaScript** (`.js`)
- 🦀 **Rust** (`.rs`)
- 🍏 **Swift** (`.swift`)
- 📊 **R** (`.r`)

---

## 📂 Struktur Folder & Navigasi

Setiap folder algoritma dirancang seragam, berisi dokumentasi penjelasan (`.md`) serta file implementasi kode sumber untuk masing-masing bahasa:

```text
search-algorithms/
│
├── Search_Algorithm/                       # Direktori utama algoritma pencarian
│   ├── A Search/                           # Algoritma A* (Informed Search)
│   ├── Binary_Search/                      # Algoritma Binary Search (Sorted Array)
│   ├── Breadth_First_Search/               # Algoritma BFS (Level-by-level)
│   ├── Depth_First_Search/                 # Algoritma DFS (Branch-by-branch)
│   ├── Dijkstra's_Algorithm/               # Algoritma Dijkstra (Shortest Path)
│   ├── Iterative Deepening DFS Algorithm/  # Algoritma IDDFS (DFS berbatas kedalaman)
│   ├── Linear_Search/                      # Algoritma Linear Search (Sequential)
│   ├── Uniform_Cost_Search/                # Algoritma UCS (Lowest Path Cost)
│   └── run_all.py                          # 🔥 Script demo interaktif (Run all algorithms)
│
├── run_all.py                              # 🔥 Script demo interaktif (Root runner)
├── README.md                               # Dokumentasi utama repositori
└── LICENSE                                 # Lisensi Apache 2.0
```

---

## 📊 Tabel Ringkasan Algoritma & Kompleksitas

| Algoritma | Tipe Struktur Data | Kompleksitas Waktu (Worst) | Kompleksitas Ruang | Karakteristik Utama |
| :--- | :--- | :--- | :--- | :--- |
| **Linear Search** | Array / List | $O(n)$ | $O(1)$ | Sederhana, tidak butuh data terurut |
| **Binary Search** | Sorted Array | $O(\log n)$ | $O(1)$ | Sangat cepat, **wajib** data terurut |
| **BFS** | Graph / Tree | $O(V + E)$ | $O(V)$ | Menggunakan Queue, mencari rute langkah minimum |
| **DFS** | Graph / Tree | $O(V + E)$ | $O(V)$ | Menggunakan Stack / Rekursi, eksplorasi mendalam |
| **Dijkstra** | Weighted Graph | $O((V + E) \log V)$ | $O(V)$ | Menggunakan Priority Queue, jarak terpendek ke semua titik |
| **UCS** | Weighted Graph | $O((V + E) \log V)$ | $O(V)$ | Varian Dijkstra berorientasi tujuan (*Goal Node*) |
| **A\* Search** | Weighted + Heuristic | $O(b^d)$ | $O(b^d)$ | Menggunakan fungsi evaluasi $f(n) = g(n) + h(n)$ |
| **IDDFS** | Graph / Tree | $O(b^d)$ | $O(bd)$ | Menggabungkan kelebihan kelengkapan BFS & hemat memori DFS |

> *Keterangan:*  
> - $n$ = jumlah elemen dalam list  
> - $V$ = jumlah vertex/node, $E$ = jumlah edge/garis  
> - $b$ = faktor percabangan (*branching factor*), $d$ = kedalaman solusi (*depth of goal*)

---

## 🧠 Penjelasan Detail Masing-Masing Algoritma

### 1. Linear Search
* **Prinsip Kerja**: Memeriksa elemen array satu per satu mulai dari indeks ke-0 sampai elemen yang dicari ditemukan atau seluruh array telah diperiksa.
* **Kapan Digunakan**:
  - Ukuran array kecil.
  - Data tidak berurutan dan proses sorting terlebih dahulu dinilai terlalu memakan waktu.

### 2. Binary Search
* **Prinsip Kerja**: Menggunakan teknik *Divide and Conquer*. Menghitung indeks tengah (`mid`). Jika target lebih kecil dari nilai tengah, pencarian dibatasi ke paruh kiri; jika lebih besar, dibatasi ke paruh kanan.
* **Syarat Mutlak**: Data **harus sudah terurut (sorted)** secara ascending atau descending.

### 3. Breadth-First Search (BFS)
* **Prinsip Kerja**: Menelusuri graf lapis demi lapis (*level-order*). Semua tetangga terdekat dari node awal dikunjungi terlebih dahulu sebelum melanjutkan ke tetangga berikutnya.
* **Struktur Data Pendukung**: **Queue (FIFO - First In First Out)**.
* **Keunggulan**: Menjamin menemukan jalur dengan jumlah transisi (hop) paling sedikit pada graf tanpa bobot.

### 4. Depth-First Search (DFS)
* **Prinsip Kerja**: Menelusuri satu cabang hingga titik terdalam (mentok) sebelum melakukan *backtracking* ke cabang lainnya.
* **Struktur Data Pendukung**: **Stack (LIFO - Last In First Out)** atau tumpukan panggilan fungsi rekursif (*call stack*).
* **Keunggulan**: Menggunakan memori yang relatif lebih kecil dibanding BFS pada struktur pohon yang lebar.

### 5. Dijkstra's Algorithm
* **Prinsip Kerja**: Menemukan jalur terpendek dari satu titik awal (*single-source shortest path*) ke semua simpul lain pada graf dengan bobot non-negatif.
* **Struktur Data Pendukung**: **Min-Heap / Priority Queue**.
* **Keunggulan**: Menghasilkan jarak absolut terpendek secara optimal matematis.

### 6. Uniform Cost Search (UCS)
* **Prinsip Kerja**: Mirip dengan Dijkstra, tetapi berfokus pada pencarian jalur dari simpul *Start* ke simpul *Goal* dengan total biaya kumulatif terendah (*cheapest path cost*).

### 7. A* (A-Star) Search
* **Prinsip Kerja**: Algoritma pencarian berinformasi (*informed search*) yang mempercepat penemuan jalur dengan memanfaatkan fungsi evaluasi:
  $$\mathbf{f(n) = g(n) + h(n)}$$
  - $g(n)$: Biaya nyata dari titik awal ke simpul $n$.
  - $h(n)$: Estimasi heuristik dari simpul $n$ menuju titik tujuan (misal: jarak garis lurus Euclidean atau Manhattan).

### 8. Iterative Deepening DFS (IDDFS)
* **Prinsip Kerja**: Menjalankan DFS berulang kali dengan batas kedalaman (*depth limit*) yang dinaikkan secara bertahap ($0, 1, 2, \dots$) hingga tujuan ditemukan.
* **Keunggulan**: Memiliki kelengkapan (*completeness*) dan optimalitas seperti BFS, namun dengan efisiensi memori setara DFS ($O(bd)$).

---

## 🚀 Cara Menjalankan Kode (Quick Start)

### Menjalankan Semua Algoritma Sekaligus (Python Demo)
Untuk mencoba dan melihat output langsung dari implementasi algoritma (Linear Search, Binary Search, BFS, DFS, Dijkstra, dan UCS), gunakan script demonstrasi yang telah disediakan:

```bash
python run_all.py
```

Output terminal akan menampilkan proses pencarian, status indeks, urutan traversal graf, dan penghitungan jalur terpendek secara rapi.

---

### Menjalankan Algoritma Spesifik per Bahasa

Kamu dapat menjalankan file individual sesuai bahasa yang terpasang di komputermu:

#### 🐍 Python
```bash
python "Binary_Search/binary_search_python.py"
python "Breadth_First_Search/breadth_first_search_python.py"
```

#### 🌐 Node.js (JavaScript)
```bash
node "Binary_Search/binary_search_javascript.js"
node "Dijkstra's_Algorithm/dijkstra's_algorithm_javascript.js"
```

#### ⚡ C++
```bash
g++ "Binary_Search/binary_search_c++.cpp" -o binary_search
./binary_search
```

#### ☕ Java
```bash
javac "Binary_Search/binary_search_java.java"
java -cp "Binary_Search" binary_search_java
```

#### 🦀 Rust
```bash
rustc "Binary_Search/binary_search_rust.rs" -o binary_search_rust
./binary_search_rust
```

---

## 🌐 Bahasa Pemrograman yang Didukung

| Algoritma | Python | C++ | Java | JS | C# | Rust | Swift | R |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Linear Search** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Binary Search** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Breadth First Search (BFS)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Depth First Search (DFS)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Dijkstra's Algorithm** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Uniform Cost Search (UCS)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **A\* Search** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Iterative Deepening DFS (IDDFS)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 🤝 Kontribusi

Kontribusi dan perbaikan sangat terbuka!
1. Fork repositori ini.
2. Buat branch fitur baru (`git checkout -b feature/NamaFitur`).
3. Commit perubahan Anda (`git commit -m 'Menambahkan fitur baru'`).
4. Push ke branch (`git push origin feature/NamaFitur`).
5. Buat **Pull Request**.

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah **Apache License 2.0**. Silakan lihat berkas [LICENSE](LICENSE) untuk informasi lebih lanjut.
