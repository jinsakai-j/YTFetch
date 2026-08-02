import os
import sys
import threading
import io
import subprocess
import tempfile
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

from PIL import Image, ImageTk, ImageDraw
import requests
import yt_dlp
import imageio_ffmpeg

# Set CustomTkinter appearance mode
ctk.set_appearance_mode("Dark")

# Custom Color Palette (Sleek Modern SaaS Theme)
COLOR_BG = "#0F0F17"           # Deep matte black background
COLOR_CARD_BG = "#1A1A26"      # Slightly lighter card surface
COLOR_CARD_BORDER = "#2A2A3D"  # Subtle card border
COLOR_ACCENT = "#00A3FF"       # Vibrant Neon Blue
COLOR_ACCENT_HOVER = "#008BE0" 
COLOR_SUCCESS = "#2ECC71"      # Bright Emerald Green
COLOR_SUCCESS_HOVER = "#27AE60"
COLOR_DANGER = "#EF4444"       # Soft Red
COLOR_TEXT_MAIN = "#F3F4F6"    # Near white
COLOR_TEXT_MUTED = "#888888"   # Clean muted gray
COLOR_TEXT_DIM = "#6B7280"     # Darker gray for footer watermark

def parse_time_to_seconds(t_str):
    """Converts HH:MM:SS, MM:SS, or seconds string to float seconds."""
    if not t_str:
        return None
    t_str = t_str.strip()
    if not t_str:
        return None

    parts = t_str.split(':')
    try:
        if len(parts) == 1:
            val = float(parts[0])
            return val if val >= 0 else None
        elif len(parts) == 2:
            m, s = float(parts[0]), float(parts[1])
            return (m * 60 + s) if (m >= 0 and s >= 0) else None
        elif len(parts) == 3:
            h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
            return (h * 3600 + m * 60 + s) if (h >= 0 and m >= 0 and s >= 0) else None
    except ValueError:
        return None
    return None

def seconds_to_hhmmss(seconds):
    """Converts seconds to HH:MM:SS or MM:SS string"""
    if seconds is None or seconds < 0:
        return "00:00"
    secs = int(seconds)
    mins, s = divmod(secs, 60)
    h, m = divmod(mins, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


class YTFetchApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Title Bar
        self.title("YTFetch")
        
        # Center & set window geometry
        self.center_window(840, 800)
        self.configure(fg_color=COLOR_BG)

        # State Variables
        self.download_thread = None
        self.is_downloading = False
        self.cancel_requested = False
        self.ydl_instance = None
        
        # Playlist State
        self.is_playlist = False
        self.playlist_entries = []
        self.playlist_checkboxes = []

        # Last Downloaded File
        self.last_downloaded_file = None
        self.current_video_duration_sec = 0

        # FFmpeg executable location
        try:
            self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            self.ffmpeg_path = None

        # Default Download Directory
        self.default_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")

        self.init_ui()
        self.bind_shortcuts()

    def center_window(self, width, height):
        """Centers the window on screen and locks its size"""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)

    def generate_placeholder_thumbnail(self, width=200, height=112):
        """Generates a sleek minimalist play icon placeholder image using Pillow"""
        img = Image.new("RGBA", (width, height), (30, 30, 46, 255))
        draw = ImageDraw.Draw(img)
        cx, cy = width // 2, height // 2
        play_points = [
            (cx - 10, cy - 15),
            (cx - 10, cy + 15),
            (cx + 15, cy)
        ]
        draw.polygon(play_points, fill=(255, 255, 255, 70))
        return ctk.CTkImage(light_image=img, dark_image=img, size=(width, height))

    def init_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # --- HEADER SECTION ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=24, pady=(18, 4), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.header_title = ctk.CTkLabel(
            self.header_frame, 
            text="YTFetch", 
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color=COLOR_TEXT_MAIN,
            anchor="w"
        )
        self.header_title.grid(row=0, column=0, sticky="w")

        self.header_subtitle = ctk.CTkLabel(
            self.header_frame, 
            text="A clean, high-performance YouTube media utility.", 
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLOR_TEXT_MUTED,
            anchor="w"
        )
        self.header_subtitle.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # --- TABVIEW CONTAINER (2 TABS) ---
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=COLOR_CARD_BG,
            segmented_button_fg_color="#12121E",
            segmented_button_selected_color=COLOR_ACCENT,
            segmented_button_selected_hover_color=COLOR_ACCENT_HOVER,
            segmented_button_unselected_color="#1F1F30",
            segmented_button_unselected_hover_color="#2A2A3D",
            corner_radius=16,
            height=660
        )
        self.tabview.grid(row=1, column=0, padx=24, pady=(6, 4), sticky="nsew")

        # Create 2 Tabs
        self.tab_download = self.tabview.add("📥 Downloader & Clip")
        self.tab_playlist = self.tabview.add("📋 Playlist Manager")

        # Build UI for 2 tabs
        self.build_tab_download()
        self.build_tab_playlist()

        # --- FOOTER WATERMARK ---
        self.footer_label = ctk.CTkLabel(
            self,
            text="YTFetch v1.0",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=COLOR_TEXT_DIM
        )
        self.footer_label.grid(row=2, column=0, padx=24, pady=(4, 10))

    def build_tab_download(self):
        self.tab_download.grid_columnconfigure(0, weight=1)

        # 1. URL Input Card
        self.url_card = ctk.CTkFrame(
            self.tab_download, 
            fg_color="#141420", 
            border_color=COLOR_CARD_BORDER,
            border_width=1,
            corner_radius=14
        )
        self.url_card.grid(row=0, column=0, padx=12, pady=8, sticky="ew")
        self.url_card.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            self.url_card, 
            placeholder_text="Tempel URL Video / Playlist YouTube di sini... (Ctrl + V)",
            height=40,
            corner_radius=10,
            border_color=COLOR_CARD_BORDER,
            fg_color="#10101A",
            text_color=COLOR_TEXT_MAIN,
            placeholder_text_color=COLOR_TEXT_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=13)
        )
        self.url_entry.grid(row=0, column=0, padx=(14, 8), pady=12, sticky="ew")

        self.fetch_btn = ctk.CTkButton(
            self.url_card,
            text="Fetch Info",
            width=100,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            command=self.fetch_metadata_async
        )
        self.fetch_btn.grid(row=0, column=1, padx=(0, 14), pady=12)

        # 2. Preview Metadata Card
        self.preview_card = ctk.CTkFrame(
            self.tab_download, 
            fg_color="#141420", 
            border_color=COLOR_CARD_BORDER,
            border_width=1,
            corner_radius=14
        )
        self.preview_card.grid(row=1, column=0, padx=12, pady=6, sticky="ew")
        self.preview_card.grid_columnconfigure(1, weight=1)

        self.placeholder_img = self.generate_placeholder_thumbnail(190, 106)
        self.thumb_label = ctk.CTkLabel(
            self.preview_card,
            text="",
            image=self.placeholder_img,
            corner_radius=10
        )
        self.thumb_label.grid(row=0, column=0, padx=12, pady=12, rowspan=3)

        self.title_label = ctk.CTkLabel(
            self.preview_card,
            text="Siap Menerima Link Video",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLOR_TEXT_MAIN,
            anchor="w",
            wraplength=480,
            justify="left"
        )
        self.title_label.grid(row=0, column=1, padx=(4, 12), pady=(12, 2), sticky="nw")

        self.channel_label = ctk.CTkLabel(
            self.preview_card,
            text="Channel: -",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MUTED,
            anchor="w"
        )
        self.channel_label.grid(row=1, column=1, padx=(4, 12), pady=2, sticky="w")

        self.duration_label = ctk.CTkLabel(
            self.preview_card,
            text="Durasi: --:--",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MUTED,
            anchor="w"
        )
        self.duration_label.grid(row=2, column=1, padx=(4, 12), pady=(2, 12), sticky="w")

        # 3. Clip / Timestamp Trimmer Card
        self.trimmer_card = ctk.CTkFrame(
            self.tab_download, 
            fg_color="#141420", 
            border_color=COLOR_CARD_BORDER,
            border_width=1,
            corner_radius=14
        )
        self.trimmer_card.grid(row=2, column=0, padx=12, pady=6, sticky="ew")
        self.trimmer_card.grid_columnconfigure(2, weight=1)

        self.trim_header_frame = ctk.CTkFrame(self.trimmer_card, fg_color="transparent")
        self.trim_header_frame.grid(row=0, column=0, columnspan=5, padx=14, pady=(10, 4), sticky="w")

        self.trim_checkbox = ctk.CTkCheckBox(
            self.trim_header_frame,
            text="Potong Clip (Timestamp Trimmer)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_TEXT_MAIN,
            hover_color=COLOR_ACCENT_HOVER,
            fg_color=COLOR_ACCENT,
            command=self.toggle_trimmer_inputs
        )
        self.trim_checkbox.grid(row=0, column=0, sticky="w")

        self.trim_guide_label = ctk.CTkLabel(
            self.trim_header_frame,
            text="(Format: HH:MM:SS, MM:SS, atau Detik)",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_MUTED
        )
        self.trim_guide_label.grid(row=0, column=1, padx=(10, 0), sticky="w")

        self.start_label = ctk.CTkLabel(
            self.trimmer_card, 
            text="Mulai:", 
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        )
        self.start_label.grid(row=1, column=0, padx=(14, 4), pady=(0, 10), sticky="w")

        self.start_entry = ctk.CTkEntry(
            self.trimmer_card,
            placeholder_text="00:01:30 atau 01:30",
            width=140,
            height=32,
            corner_radius=8,
            fg_color="#10101A",
            border_color=COLOR_CARD_BORDER,
            state="disabled",
            font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        self.start_entry.grid(row=1, column=1, padx=(0, 12), pady=(0, 10), sticky="w")

        self.end_label = ctk.CTkLabel(
            self.trimmer_card, 
            text="Selesai:", 
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        )
        self.end_label.grid(row=1, column=2, padx=(8, 4), pady=(0, 10), sticky="w")

        self.end_entry = ctk.CTkEntry(
            self.trimmer_card,
            placeholder_text="00:03:45 atau 03:45",
            width=140,
            height=32,
            corner_radius=8,
            fg_color="#10101A",
            border_color=COLOR_CARD_BORDER,
            state="disabled",
            font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        self.end_entry.grid(row=1, column=3, padx=(0, 14), pady=(0, 10), sticky="w")

        # 4. Format & Folder Options
        self.options_card = ctk.CTkFrame(
            self.tab_download, 
            fg_color="#141420", 
            border_color=COLOR_CARD_BORDER,
            border_width=1,
            corner_radius=14
        )
        self.options_card.grid(row=3, column=0, padx=12, pady=6, sticky="ew")
        self.options_card.grid_columnconfigure((0, 1), weight=1)

        self.format_label = ctk.CTkLabel(
            self.options_card, 
            text="Format Output", 
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        )
        self.format_label.grid(row=0, column=0, padx=14, pady=(8, 2), sticky="w")

        self.format_option = ctk.CTkOptionMenu(
            self.options_card,
            values=["Video (MP4)", "Audio (MP3)"],
            command=self.on_format_change,
            height=34,
            corner_radius=8,
            fg_color="#10101A",
            button_color=COLOR_CARD_BORDER,
            button_hover_color="#32324A",
            font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        self.format_option.set("Video (MP4)")
        self.format_option.grid(row=1, column=0, padx=14, pady=(0, 10), sticky="ew")

        self.quality_label = ctk.CTkLabel(
            self.options_card, 
            text="Kualitas / Bitrate", 
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        )
        self.quality_label.grid(row=0, column=1, padx=14, pady=(8, 2), sticky="w")

        self.quality_option = ctk.CTkOptionMenu(
            self.options_card,
            values=["1080p (FHD)", "720p (HD)", "480p"],
            height=34,
            corner_radius=8,
            fg_color="#10101A",
            button_color=COLOR_CARD_BORDER,
            button_hover_color="#32324A",
            font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        self.quality_option.set("1080p (FHD)")
        self.quality_option.grid(row=1, column=1, padx=14, pady=(0, 10), sticky="ew")

        # Folder Selection Row
        self.folder_label = ctk.CTkLabel(
            self.options_card, 
            text="Folder Penyimpanan", 
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=COLOR_TEXT_MAIN
        )
        self.folder_label.grid(row=2, column=0, padx=14, pady=(4, 2), sticky="w")

        self.folder_entry = ctk.CTkEntry(
            self.options_card,
            height=34,
            corner_radius=8,
            border_color=COLOR_CARD_BORDER,
            fg_color="#10101A",
            text_color=COLOR_TEXT_MAIN,
            font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        self.folder_entry.insert(0, self.default_download_dir)
        self.folder_entry.grid(row=3, column=0, padx=(14, 6), pady=(0, 10), sticky="ew")

        self.folder_btn_frame = ctk.CTkFrame(self.options_card, fg_color="transparent")
        self.folder_btn_frame.grid(row=3, column=1, padx=(0, 14), pady=(0, 10), sticky="e")

        self.browse_btn = ctk.CTkButton(
            self.folder_btn_frame,
            text="Pilih Folder",
            width=90,
            height=34,
            corner_radius=8,
            fg_color="#252538",
            hover_color="#32324A",
            text_color=COLOR_TEXT_MAIN,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.browse_folder
        )
        self.browse_btn.grid(row=0, column=0, padx=(0, 6))

        self.open_folder_btn = ctk.CTkButton(
            self.folder_btn_frame,
            text="Buka (Ctrl+O)",
            width=100,
            height=34,
            corner_radius=8,
            fg_color="#252538",
            hover_color="#32324A",
            text_color=COLOR_TEXT_MAIN,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.open_output_folder
        )
        self.open_folder_btn.grid(row=0, column=1)

        # 5. Action & Progress Area
        self.action_frame = ctk.CTkFrame(self.tab_download, fg_color="transparent")
        self.action_frame.grid(row=4, column=0, padx=12, pady=(6, 4), sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=1)

        self.download_btn = ctk.CTkButton(
            self.action_frame,
            text="Download (Enter)",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=44,
            corner_radius=12,
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            command=self.start_download
        )
        self.download_btn.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.cancel_btn = ctk.CTkButton(
            self.action_frame,
            text="Batal (Esc)",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=44,
            width=90,
            corner_radius=12,
            fg_color="transparent",
            border_width=2,
            border_color=COLOR_DANGER,
            text_color=COLOR_DANGER,
            hover_color="#2C1618",
            state="disabled",
            command=self.cancel_download
        )
        self.cancel_btn.grid(row=0, column=1, sticky="e")

        self.progress_bar = ctk.CTkProgressBar(
            self.action_frame, 
            height=8,
            corner_radius=4,
            progress_color=COLOR_ACCENT,
            fg_color="#1F1F30"
        )
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, columnspan=2, pady=(10, 4), sticky="ew")

        self.status_label = ctk.CTkLabel(
            self.action_frame,
            text="Status: Siap",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_MUTED
        )
        self.status_label.grid(row=2, column=0, columnspan=2, sticky="w")

        # 6. Download Result Card (Hidden until download finishes)
        self.result_card = ctk.CTkFrame(
            self.tab_download, 
            fg_color="#141420", 
            border_color=COLOR_CARD_BORDER,
            border_width=1,
            corner_radius=14
        )
        self.result_card.grid_columnconfigure(0, weight=1)

        self.result_title = ctk.CTkLabel(
            self.result_card,
            text="🎉 Hasil Download Terbaru",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_SUCCESS,
            anchor="w"
        )
        self.result_title.grid(row=0, column=0, columnspan=2, padx=14, pady=(8, 2), sticky="w")

        self.file_info_label = ctk.CTkLabel(
            self.result_card,
            text="Belum ada file yang didownload",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_TEXT_MAIN,
            anchor="w"
        )
        self.file_info_label.grid(row=1, column=0, columnspan=2, padx=14, pady=(0, 6), sticky="w")

        self.locate_file_btn = ctk.CTkButton(
            self.result_card,
            text="📁 Buka Lokasi File (Ctrl+O)",
            width=180,
            height=34,
            corner_radius=8,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.locate_downloaded_file
        )
        self.locate_file_btn.grid(row=2, column=0, padx=14, pady=(0, 10), sticky="w")

    def build_tab_playlist(self):
        self.tab_playlist.grid_columnconfigure(0, weight=1)

        self.playlist_card = ctk.CTkFrame(
            self.tab_playlist, 
            fg_color="#141420", 
            border_color=COLOR_CARD_BORDER,
            border_width=1,
            corner_radius=14
        )
        self.playlist_card.grid(row=0, column=0, padx=12, pady=10, sticky="ew")
        self.playlist_card.grid_columnconfigure(0, weight=1)

        self.playlist_count_label = ctk.CTkLabel(
            self.playlist_card, 
            text="📋 Belum ada playlist yang dimuat. Masukkan URL playlist di Tab Downloader lalu klik Fetch Info.", 
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_TEXT_MUTED,
            wraplength=700
        )
        self.playlist_count_label.grid(row=0, column=0, padx=14, pady=12, sticky="w")

        self.playlist_btns_frame = ctk.CTkFrame(self.playlist_card, fg_color="transparent")
        self.playlist_btns_frame.grid(row=1, column=0, padx=14, pady=(0, 8), sticky="e")

        self.select_all_btn = ctk.CTkButton(
            self.playlist_btns_frame,
            text="Select All",
            width=85,
            height=30,
            corner_radius=8,
            fg_color="#252538",
            hover_color="#32324A",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.select_all_playlist
        )
        self.select_all_btn.grid(row=0, column=0, padx=(0, 6))

        self.deselect_all_btn = ctk.CTkButton(
            self.playlist_btns_frame,
            text="Deselect All",
            width=95,
            height=30,
            corner_radius=8,
            fg_color="#252538",
            hover_color="#32324A",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.deselect_all_playlist
        )
        self.deselect_all_btn.grid(row=0, column=1)

        self.playlist_scrollable = ctk.CTkScrollableFrame(
            self.tab_playlist,
            height=380,
            corner_radius=12,
            fg_color="#10101A",
            border_color=COLOR_CARD_BORDER,
            border_width=1
        )
        self.playlist_scrollable.grid(row=1, column=0, padx=12, pady=6, sticky="ew")
        self.playlist_scrollable.grid_columnconfigure(0, weight=1)

        # Batch Download Button for Playlist Tab
        self.playlist_download_btn = ctk.CTkButton(
            self.tab_playlist,
            text="Download Video Terpilih",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=42,
            corner_radius=12,
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            command=self.start_download
        )
        self.playlist_download_btn.grid(row=2, column=0, padx=12, pady=12, sticky="ew")

    # --- SHORTCUTS & OTHER LISTENERS ---

    def bind_shortcuts(self):
        self.bind("<Control-v>", self.on_ctrl_v)
        self.bind("<Return>", lambda e: self.start_download())
        self.bind("<Escape>", lambda e: self.cancel_download())
        self.bind("<Control-o>", lambda e: self.open_output_folder())

    def toggle_trimmer_inputs(self):
        if self.trim_checkbox.get() == 1:
            self.start_entry.configure(state="normal")
            self.end_entry.configure(state="normal")
        else:
            self.start_entry.configure(state="disabled")
            self.end_entry.configure(state="disabled")

    def select_all_playlist(self):
        for cb in self.playlist_checkboxes:
            cb.select()

    def deselect_all_playlist(self):
        for cb in self.playlist_checkboxes:
            cb.deselect()

    def on_ctrl_v(self, event):
        try:
            clipboard_content = self.clipboard_get().strip()
            if clipboard_content.startswith("http://") or clipboard_content.startswith("https://") or "youtu" in clipboard_content:
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, clipboard_content)
                self.fetch_metadata_async()
        except Exception:
            pass

    def on_format_change(self, choice):
        if choice == "Audio (MP3)":
            self.quality_option.configure(values=["320kbps", "128kbps"])
            self.quality_option.set("320kbps")
            self.download_btn.configure(text="Download Audio (Enter)")
        else:
            self.quality_option.configure(values=["1080p (FHD)", "720p (HD)", "480p"])
            self.quality_option.set("1080p (FHD)")
            self.download_btn.configure(text="Download Video (Enter)")

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_entry.get())
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)

    def open_output_folder(self, event=None):
        folder = self.folder_entry.get().strip()
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        os.startfile(folder)

    def fetch_metadata_async(self):
        url = self.url_entry.get().strip()
        if not url:
            self.status_label.configure(text="Status: Masukkan URL YouTube terlebih dahulu!", text_color="#F59E0B")
            return

        self.status_label.configure(text="Status: Mengambil metadata (single/playlist)...", text_color=COLOR_ACCENT)
        self.fetch_btn.configure(state="disabled")

        threading.Thread(target=self._fetch_metadata_worker, args=(url,), daemon=True).start()

    def _fetch_metadata_worker(self, url):
        try:
            ydl_opts = {
                'quiet': True, 
                'no_warnings': True,
                'extract_flat': 'in_playlist'
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                is_playlist = info.get('_type') == 'playlist' or ('entries' in info and len(info.get('entries', [])) > 1)

                if is_playlist:
                    entries = list(info.get('entries', []))
                    playlist_title = info.get('title', 'Playlist YouTube')
                    self.after(0, self._update_playlist_ui, playlist_title, entries)
                else:
                    title = info.get('title', 'Unknown Title')
                    channel = info.get('uploader', info.get('channel', 'Unknown Channel'))
                    duration_sec = info.get('duration', 0)
                    thumbnail_url = info.get('thumbnail', '')

                    duration_str = seconds_to_hhmmss(duration_sec)

                    img_obj = None
                    if thumbnail_url:
                        res = requests.get(thumbnail_url, timeout=6)
                        if res.status_code == 200:
                            image_bytes = io.BytesIO(res.content)
                            pil_img = Image.open(image_bytes)
                            pil_img = pil_img.resize((190, 106), Image.Resampling.LANCZOS)
                            img_obj = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(190, 106))

                    self.after(0, self._update_single_ui, title, channel, duration_str, img_obj, duration_sec)
        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda: self._on_fetch_error(err_msg))

    def _update_single_ui(self, title, channel, duration_str, img_obj, duration_sec=0):
        self.is_playlist = False
        self.current_video_duration_sec = duration_sec

        self.title_label.configure(text=title)
        self.channel_label.configure(text=f"Channel: {channel}")
        self.duration_label.configure(text=f"Durasi: {duration_str}")
        
        if img_obj:
            self.thumb_label.configure(image=img_obj, text="")
        
        self.status_label.configure(text="Status: Metadata single video berhasil dimuat!", text_color=COLOR_SUCCESS)
        self.fetch_btn.configure(state="normal")

    def _update_playlist_ui(self, playlist_title, entries):
        self.is_playlist = True
        self.current_video_duration_sec = 0
        self.playlist_entries = entries

        self.playlist_count_label.configure(text=f"📋 {playlist_title} ({len(entries)} Video)")

        # Clear scrollable frame children
        for widget in self.playlist_scrollable.winfo_children():
            widget.destroy()

        self.playlist_checkboxes = []

        for idx, item in enumerate(entries, start=1):
            item_title = item.get('title', f'Video {idx}')
            dur = item.get('duration', 0)
            dur_str = seconds_to_hhmmss(dur) if dur else "--:--"

            cb = ctk.CTkCheckBox(
                self.playlist_scrollable,
                text=f"{idx}. {item_title} [{dur_str}]",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=COLOR_TEXT_MAIN,
                fg_color=COLOR_ACCENT,
                hover_color=COLOR_ACCENT_HOVER
            )
            cb.select()
            cb.grid(row=idx, column=0, padx=8, pady=4, sticky="w")
            self.playlist_checkboxes.append(cb)

        self.status_label.configure(text=f"Status: Playlist terdeteksi ({len(entries)} video)", text_color=COLOR_SUCCESS)
        self.fetch_btn.configure(state="normal")
        
        # Automatically focus to playlist tab
        self.tabview.set("📋 Playlist Manager")

    def _on_fetch_error(self, err):
        self.status_label.configure(text=f"Status: Gagal mengambil metadata ({err[:45]}...)", text_color=COLOR_DANGER)
        self.fetch_btn.configure(state="normal")

    def start_download(self):
        if self.is_downloading:
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Peringatan", "Silakan masukkan URL YouTube!")
            return

        output_dir = self.folder_entry.get().strip()
        if not output_dir or not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception:
                messagebox.showerror("Error", "Folder tujuan tidak valid!")
                return

        # Check Clip Trimmer inputs
        start_sec = None
        end_sec = None
        if self.trim_checkbox.get() == 1:
            start_str = self.start_entry.get().strip()
            end_str = self.end_entry.get().strip()

            if not start_str or not end_str:
                messagebox.showerror(
                    "Input Trimmer Kosong", 
                    "Silakan isi kolom Waktu Mulai dan Waktu Selesai!\nFormat: HH:MM:SS (01:15:30), MM:SS (01:30), atau Detik (90)."
                )
                return

            start_sec = parse_time_to_seconds(start_str)
            end_sec = parse_time_to_seconds(end_str)

            if start_sec is None:
                messagebox.showerror(
                    "Format Mulai Tidak Valid", 
                    f"Format waktu mulai '{start_str}' tidak dikenali!\nGunakan format HH:MM:SS (01:15:30), MM:SS (01:30), atau Detik (90)."
                )
                return

            if end_sec is None:
                messagebox.showerror(
                    "Format Selesai Tidak Valid", 
                    f"Format waktu selesai '{end_str}' tidak dikenali!\nGunakan format HH:MM:SS (01:15:30), MM:SS (03:45), atau Detik (225)."
                )
                return

            if end_sec <= start_sec:
                messagebox.showerror(
                    "Timestamp Tidak Valid", 
                    "Waktu Selesai harus lebih besar dari Waktu Mulai!"
                )
                return

            # Capping to max video duration if known
            if not self.is_playlist and getattr(self, 'current_video_duration_sec', 0) > 0:
                max_dur = self.current_video_duration_sec
                if end_sec > max_dur:
                    end_sec = max_dur
                    messagebox.showinfo(
                        "Informasi Capping Trimmer", 
                        f"Waktu selesai melebihi durasi video ({seconds_to_hhmmss(max_dur)}).\nWaktu selesai otomatis dipotong hingga batas maksimal video."
                    )

        self.is_downloading = True
        self.cancel_requested = False
        self.download_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.fetch_btn.configure(state="disabled")
        self.playlist_download_btn.configure(state="disabled")
        self.progress_bar.set(0)

        self.download_thread = threading.Thread(
            target=self._download_worker, 
            args=(url, output_dir, start_sec, end_sec), 
            daemon=True
        )
        self.download_thread.start()

    def cancel_download(self):
        if self.is_downloading:
            self.cancel_requested = True
            self.status_label.configure(text="Status: Membatalkan download...", text_color="#F59E0B")

    def _download_progress_hook(self, d):
        if self.cancel_requested:
            raise Exception("Download dibatalkan oleh pengguna.")

        status = d.get('status')
        if status == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            
            if total_bytes > 0:
                percent = downloaded / total_bytes
                speed = d.get('speed', 0)
                speed_str = f"{speed / (1024*1024):.2f} MB/s" if speed else "0 MB/s"
                eta = d.get('eta', 0)
                
                status_txt = f"Downloading... {percent*100:.1f}% ({speed_str} | ETA: {eta}s)"
                self.after(0, self._update_progress_ui, percent, status_txt)
        elif status == 'finished':
            filepath = d.get('filename')
            if filepath:
                self.last_downloaded_file = filepath
            self.after(0, self._update_progress_ui, 0.99, "Merging / Processing Output...")

    def _update_progress_ui(self, percent, status_text):
        self.progress_bar.set(percent)
        self.status_label.configure(text=f"Status: {status_text}", text_color=COLOR_ACCENT)

    def _download_worker(self, url, output_dir, start_sec, end_sec):
        fmt_choice = self.format_option.get()
        quality_choice = self.quality_option.get()
        out_template = os.path.join(output_dir, '%(title)s.%(ext)s')

        # Check if playlist mode
        selected_urls = []
        if self.is_playlist and len(self.playlist_checkboxes) > 0:
            for idx, cb in enumerate(self.playlist_checkboxes):
                if cb.get() == 1 and idx < len(self.playlist_entries):
                    item = self.playlist_entries[idx]
                    item_url = item.get('url') or item.get('id')
                    if item_url:
                        if not item_url.startswith('http'):
                            item_url = f"https://www.youtube.com/watch?v={item_url}"
                        selected_urls.append(item_url)
        else:
            selected_urls = [url]

        if not selected_urls:
            self.after(0, self._on_download_complete, False, "Tidak ada video playlist yang dipilih!")
            return

        total_items = len(selected_urls)

        for current_idx, target_url in enumerate(selected_urls, start=1):
            if self.cancel_requested:
                break

            ydl_opts = {
                'outtmpl': out_template,
                'progress_hooks': [self._download_progress_hook],
                'nocheckcertificate': True,
                'quiet': True,
                'no_warnings': True,
                'js_runtimes': {'node': {}},
            }

            if self.ffmpeg_path:
                ydl_opts['ffmpeg_location'] = self.ffmpeg_path

            # If trimming is enabled, download raw stream to OS temp folder first
            is_trimming = (start_sec is not None and end_sec is not None)
            sys_temp_dir = tempfile.gettempdir()
            
            if is_trimming:
                temp_output = os.path.join(sys_temp_dir, '_ytdl_temp_%(title)s.%(ext)s')
                ydl_opts['outtmpl'] = temp_output

            # Format Choice
            if fmt_choice == "Audio (MP3)":
                bitrate = "320" if "320" in quality_choice else "128"
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': bitrate,
                    }],
                })
            else:
                if "1080p" in quality_choice:
                    ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
                elif "720p" in quality_choice:
                    ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best'
                else:
                    ydl_opts['format'] = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]/best'

                ydl_opts['merge_output_format'] = 'mp4'

            raw_file = None
            try:
                status_msg = f"Downloading ({current_idx}/{total_items})..."
                self.after(0, lambda m=status_msg: self.status_label.configure(text=f"Status: {m}"))

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    self.ydl_instance = ydl
                    ydl.download([target_url])

                # Handle FFmpeg trimming if requested
                if is_trimming:
                    for f in os.listdir(sys_temp_dir):
                        if f.startswith('_ytdl_temp_'):
                            raw_file = os.path.join(sys_temp_dir, f)
                            break

                    if raw_file and os.path.exists(raw_file):
                        dir_name, base_name = os.path.split(raw_file)
                        clean_name = base_name.replace('_ytdl_temp_', '')
                        final_trimmed_file = os.path.join(output_dir, clean_name)

                        duration_sec = max(1.0, end_sec - start_sec)

                        self.after(0, lambda: self.status_label.configure(text="Status: Memotong clip dengan FFmpeg..."))

                        if self.ffmpeg_path:
                            trim_cmd = [
                                self.ffmpeg_path,
                                '-y',
                                '-ss', str(start_sec),
                                '-i', raw_file,
                                '-t', str(duration_sec),
                                '-c', 'copy',
                                final_trimmed_file
                            ]
                            subprocess.run(
                                trim_cmd, 
                                check=True, 
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                            )
                            
                            self.last_downloaded_file = final_trimmed_file
            except Exception as e:
                err_str = str(e)
                if "dibatalkan" in err_str:
                    self.after(0, self._on_download_complete, False, "Download Dibatalkan.")
                    return
                else:
                    print(f"Error downloading {target_url}: {err_str}")
            finally:
                if is_trimming and raw_file and os.path.exists(raw_file):
                    try:
                        os.remove(raw_file)
                    except Exception:
                        pass

        if not self.cancel_requested:
            self.after(0, self._on_download_complete, True, f"Berhasil mendownload {total_items} item!")

    def _on_download_complete(self, success, message):
        self.is_downloading = False
        self.cancel_requested = False
        self.download_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.fetch_btn.configure(state="normal")
        self.playlist_download_btn.configure(state="normal")

        if success:
            self.progress_bar.set(1.0)
            self.status_label.configure(text=f"Status: {message}", text_color=COLOR_SUCCESS)

            if self.last_downloaded_file and os.path.exists(self.last_downloaded_file):
                filename = os.path.basename(self.last_downloaded_file)
                file_size_mb = os.path.getsize(self.last_downloaded_file) / (1024 * 1024)
                self.file_info_label.configure(text=f"📄 {filename} ({file_size_mb:.2f} MB)")
                self.result_card.grid(row=5, column=0, padx=12, pady=6, sticky="ew")

            messagebox.showinfo("Download Selesai 🎉", message)
        else:
            self.status_label.configure(text=f"Status: {message}", text_color=COLOR_DANGER)
            if "Dibatalkan" not in message:
                messagebox.showerror("Error", message)

    def locate_downloaded_file(self):
        """Opens File Explorer and highlights the downloaded file"""
        if self.last_downloaded_file and os.path.exists(self.last_downloaded_file):
            try:
                norm_path = os.path.normpath(self.last_downloaded_file)
                subprocess.Popen(f'explorer /select,"{norm_path}"')
            except Exception as e:
                messagebox.showerror("Error Explorer", f"Gagal membuka lokasi file: {e}")

if __name__ == "__main__":
    app = YTFetchApp()
    app.mainloop()
