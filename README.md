# ⚡ YTFetch

**A clean, high-performance YouTube media utility.**

Desktop GUI modern & ringan untuk mendownload video/audio YouTube menjadi MP4 (hingga 1080p FHD), MP3, M4A, atau WAV — dilengkapi fitur **Clip Trimming** dan **Playlist Bulk Downloader**.

---

## 📸 Preview

> Tampilan aplikasi YTFetch dengan dark-mode SaaS aesthetic.

---

## 🚀 Fitur Utama

### 📥 Tab 1 — Downloader & Clip
- Paste URL single video YouTube, otomatis fetch metadata (thumbnail, judul, channel, durasi).
- **Format Output**:
  - `Video (MP4)` — 1080p FHD, 720p HD, 480p
  - `Audio (MP3)` — 320kbps, 256kbps, 128kbps
  - `Audio (M4A / AAC)` — Best native quality, tanpa re-encode
  - `Audio (WAV Lossless)` — Uncompressed lossless audio
- **Timestamp Clip Trimmer** — Potong klip spesifik berdasarkan waktu mulai & selesai (`HH:MM:SS`, `MM:SS`, atau detik).

### 📋 Tab 2 — Playlist Manager
- Paste URL playlist YouTube, otomatis mendeteksi seluruh daftar video.
- Select All / Deselect All dengan checkbox individual.
- Bulk download semua video terpilih sekaligus.

### ⌨️ Keyboard Shortcuts
| Shortcut | Fungsi |
|---|---|
| `Ctrl + V` | Paste URL dari clipboard & langsung fetch metadata |
| `Enter` | Mulai download |
| `Esc` | Batalkan download yang sedang berjalan |
| `Ctrl + O` | Buka folder penyimpanan di File Explorer |

---

## 💻 Instalasi & Cara Menjalankan

### Persyaratan Sistem
- **OS**: Windows 10 / 11 (64-bit)
- **Python**: Versi 3.10 atau lebih baru — [Download Python](https://www.python.org/downloads/)
  > ⚠️ Saat install Python, **pastikan centang** ✅ *"Add Python to PATH"*

### Langkah Instalasi

#### Cara Cepat (Otomatis)

1. **Download / Clone** repositori ini:
   ```bash
   git clone https://github.com/jinsakai-j/YTFetch.git
   cd YTFetch
   ```
   Atau klik tombol hijau **Code → Download ZIP**, lalu ekstrak ke folder mana saja.

2. **Jalankan Setup Otomatis** — klik dua kali file:
   ```
   setup_env.bat
   ```
   Script ini akan:
   - ✅ Menginstall semua library Python yang dibutuhkan secara otomatis
   - ✅ Membuat shortcut **YTFetch** di Desktop Anda

3. **Selesai!** Buka aplikasi dengan salah satu cara:
   - Klik ikon **YTFetch** di Desktop
   - Atau klik dua kali `Run_YTFetch.bat`

---

#### Cara Manual (Step by Step)

1. **Clone repositori**:
   ```bash
   git clone https://github.com/USERNAME/YTFetch.git
   cd YTFetch
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Jalankan aplikasi**:
   ```bash
   python YTFetch.py
   ```

4. **(Opsional) Buat shortcut di Desktop**:
   ```bash
   python create_shortcut.py
   ```

---

## 📦 Dependencies

| Library | Fungsi |
|---|---|
| [customtkinter](https://github.com/TomSchimansky/CustomTkinter) | Framework GUI modern dengan dark mode |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Engine download YouTube (fork youtube-dl) |
| [Pillow](https://python-pillow.org/) | Pemrosesan gambar thumbnail |
| [requests](https://docs.python-requests.org/) | HTTP client untuk fetch thumbnail |
| [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) | FFmpeg binary untuk merge/trim/convert media |
| [pywin32](https://github.com/mhammond/pywin32) | Windows API untuk pembuatan desktop shortcut |

---

## 📁 Struktur File

```
YTFetch/
├── YTFetch.py            # Aplikasi utama (GUI + downloader engine)
├── Run_YTFetch.bat       # Launcher tanpa jendela CMD
├── setup_env.bat         # Setup otomatis (install + shortcut)
├── create_shortcut.py    # Script pembuat shortcut Desktop
├── requirements.txt      # Daftar library Python yang dibutuhkan
├── app.py                # Wrapper launcher (backward compatibility)
├── .gitignore            # Filter file yang tidak perlu di-upload
└── README.md             # Dokumentasi (file ini)
```

---

## ❓ Troubleshooting

| Masalah | Solusi |
|---|---|
| `python` tidak dikenali di CMD | Pastikan Python sudah terinstall dan **Add to PATH** dicentang saat instalasi. Restart CMD setelah install. |
| Gagal download / error `yt-dlp` | Jalankan `pip install -U yt-dlp` untuk update ke versi terbaru. |
| Shortcut tidak muncul di Desktop | Jalankan `python create_shortcut.py` secara manual. Jika pakai OneDrive, shortcut akan dibuat di folder OneDrive Desktop. |
| FFmpeg error saat trim / merge | Library `imageio-ffmpeg` sudah menyertakan FFmpeg secara otomatis. Jika tetap error, install FFmpeg manual dan tambahkan ke PATH. |

---

## 📝 Lisensi

Proyek ini bersifat open-source untuk keperluan edukasi dan personal.

---

<p align="center"><b>YTFetch v1.0</b></p>
