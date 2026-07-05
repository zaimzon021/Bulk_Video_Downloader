"""
YouTube Shorts Downloader — GUI v2
====================================
Three modes:
  1. Grab from channels  – paste channel URLs, auto-fetch top popular shorts
  2. Paste direct links  – paste video URLs directly
  3. Download from file  – use existing links.txt without re-collecting

Requirements: pip install yt-dlp
Binaries needed in same folder: yt-dlp.exe, deno.exe, ffmpeg.exe, cookies.txt
"""

import os
import re
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import yt_dlp

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
YTDLP_EXE   = os.path.join(BASE_DIR, "yt-dlp.exe")
LINKS_FILE   = os.path.join(BASE_DIR, "links.txt")
HISTORY_FILE = os.path.join(BASE_DIR, "history.txt")
COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")
OUTPUT_TPL   = os.path.join(BASE_DIR, "%(uploader)s", "%(title)s.%(ext)s")
MAX_PER_CH   = 46

# ── theme ─────────────────────────────────────────────────────────────────────
BG    = "#0f0f17"
CARD  = "#1a1a2e"
CARD2 = "#16213e"
ACC   = "#7c6af7"
ACC2  = "#a78bfa"
FG    = "#e2e8f0"
GRAY  = "#64748b"
GREEN = "#22c55e"
RED   = "#ef4444"
FONT  = ("Segoe UI", 10)

# ── backend ───────────────────────────────────────────────────────────────────

def clean_url(url):
    return re.sub(r'/(shorts|videos|featured|community|playlists|about)/?$',
                  '', url.rstrip('/'))

def get_popular_shorts(channel_url, log):
    channel_url = clean_url(channel_url.strip())
    tabs = ["/shorts", "/videos", "/featured", ""]
    ydl_opts = {"quiet": True, "no_warnings": True,
                "ignoreerrors": True, "extract_flat": "in_playlist"}
    for tab in tabs:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url + tab, download=False)
            if not info or not info.get("entries"):
                continue
            entries = [e for e in info["entries"] if e]
            if not entries:
                continue
            entries.sort(key=lambda e: e.get("view_count") or 0, reverse=True)
            entries = entries[:MAX_PER_CH]
            urls = []
            for e in entries:
                vid_id = e.get("id") or e.get("url", "")
                if vid_id:
                    urls.append(vid_id if vid_id.startswith("http")
                                else f"https://www.youtube.com/watch?v={vid_id}")
            if urls:
                return urls
        except Exception:
            continue
    return []

def collect_links(channels, log):
    all_links, seen = [], set()
    for i, url in enumerate(channels, 1):
        handle = url.split("@")[-1] if "@" in url else url
        log(f"[{i}/{len(channels)}] {handle} ... ")
        links = get_popular_shorts(url, log)
        new = [l for l in links if l not in seen]
        seen.update(new)
        all_links.extend(new)
        log(f"{len(new)} videos\n")
    return all_links

def run_download(interval, cookies_path, log, on_done):
    ytdlp = YTDLP_EXE if os.path.exists(YTDLP_EXE) else "yt-dlp"
    cmd = [
        ytdlp,
        "-ia", LINKS_FILE,
        "-N", "1",
        "--sleep-interval", str(interval),
        "--download-archive", HISTORY_FILE,
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "--cookies", cookies_path,
        "--js-runtime", "deno",
        "--user-agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "--extractor-args", "youtube:player_client=web_embedded",
        "-o", OUTPUT_TPL,
    ]
    log("\n► " + " ".join(f'"{a}"' if " " in a else a for a in cmd) + "\n")
    log("─" * 60 + "\n")
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, cwd=BASE_DIR,
        )
        for line in proc.stdout:
            log(line)
        proc.wait()
        log(f"\n{'─'*60}\n✔ Done! Exit code: {proc.returncode}\n")
    except FileNotFoundError:
        log(f"\n✘ yt-dlp not found. Place yt-dlp.exe in:\n  {BASE_DIR}\n")
    finally:
        on_done()

def links_count():
    if not os.path.exists(LINKS_FILE):
        return 0
    with open(LINKS_FILE, encoding="utf-8") as f:
        return sum(1 for l in f if l.strip())

# ── GUI ───────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Shorts Downloader")
        self.geometry("960x780")
        self.minsize(760, 600)
        self.configure(bg=BG)
        self._cookies_path = tk.StringVar(value=COOKIES_FILE)
        self._interval     = tk.IntVar(value=5)
        self._mode         = tk.StringVar(value="channels")
        self._busy         = False
        self._apply_styles()
        self._build()
        self._refresh_links_badge()

    # ── styles ────────────────────────────────────────────────────────────────

    def _apply_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TFrame",        background=BG)
        s.configure("Card.TFrame",   background=CARD)
        s.configure("Card2.TFrame",  background=CARD2)
        s.configure("TLabel",        background=BG,    foreground=FG,   font=FONT)
        s.configure("Card.TLabel",   background=CARD,  foreground=FG,   font=FONT)
        s.configure("Card2.TLabel",  background=CARD2, foreground=FG,   font=FONT)
        s.configure("Dim.TLabel",    background=CARD,  foreground=GRAY, font=("Segoe UI", 9))
        s.configure("Head.TLabel",   background=BG,    foreground=ACC2,
                    font=("Segoe UI", 15, "bold"))
        s.configure("Accent.TButton", background=ACC,  foreground="#fff",
                    font=("Segoe UI", 10, "bold"), relief="flat", padding=(12, 7))
        s.map("Accent.TButton",
              background=[("active", "#6a5ce0"), ("disabled", "#2d2d4e")])
        s.configure("Sec.TButton",   background=CARD2, foreground=FG,
                    font=FONT, relief="flat", padding=(10, 6))
        s.map("Sec.TButton",
              background=[("active", "#1e2a4a"), ("disabled", "#111")])
        s.configure("TRadiobutton",  background=CARD,  foreground=FG,   font=FONT,
                    indicatorcolor=ACC)
        s.map("TRadiobutton",        background=[("active", CARD)])
        s.configure("TScale",        background=CARD,  troughcolor="#2d2d4e")
        s.configure("Horizontal.TScale", background=CARD, troughcolor="#2d2d4e",
                    sliderlength=18)

    # ── layout ────────────────────────────────────────────────────────────────

    def _build(self):
        # ── top bar
        top = ttk.Frame(self)
        top.pack(fill="x", padx=20, pady=(18, 0))
        ttk.Label(top, text="YouTube Shorts Downloader", style="Head.TLabel").pack(side="left")

        # cookies pill on right
        cpill = ttk.Frame(top, style="Card.TFrame", padding=(8, 4))
        cpill.pack(side="right")
        ttk.Label(cpill, text="🍪 cookies.txt", style="Card.TLabel",
                  font=("Segoe UI", 9)).pack(side="left", padx=(0, 6))
        self._cookie_status = ttk.Label(cpill, text="", style="Card.TLabel",
                                        font=("Segoe UI", 9, "bold"))
        self._cookie_status.pack(side="left")
        ttk.Button(cpill, text="Browse", style="Sec.TButton",
                   command=self._browse_cookies).pack(side="left", padx=(8, 0))
        self._update_cookie_label()

        # ── mode selector
        mode_card = ttk.Frame(self, style="Card.TFrame", padding=14)
        mode_card.pack(fill="x", padx=20, pady=(14, 0))
        ttk.Label(mode_card, text="Mode", style="Card.TLabel",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w")

        rb_frame = ttk.Frame(mode_card, style="Card.TFrame")
        rb_frame.pack(fill="x", pady=(6, 0))
        modes = [
            ("channels", "📡  Grab from channels  (auto-fetch top shorts)"),
            ("direct",   "🔗  Paste video links directly"),
            ("file",     "📄  Use existing links.txt  (skip grab step)"),
        ]
        for val, label in modes:
            ttk.Radiobutton(rb_frame, text=label, variable=self._mode,
                            value=val, style="TRadiobutton",
                            command=self._on_mode_change).pack(side="left", padx=(0, 20))

        # ── input area (swappable)
        self._input_card = ttk.Frame(self, style="Card.TFrame", padding=14)
        self._input_card.pack(fill="both", expand=True, padx=20, pady=(10, 0))
        self._build_input_area()

        # ── options bar
        opt = ttk.Frame(self, style="Card2.TFrame", padding=12)
        opt.pack(fill="x", padx=20, pady=(10, 0))
        opt.columnconfigure(1, weight=1)

        ttk.Label(opt, text="Sleep interval:", style="Card2.TLabel").grid(
            row=0, column=0, sticky="w")
        self._interval_lbl = ttk.Label(opt, text="5 sec", style="Card2.TLabel",
                                       font=("Segoe UI", 10, "bold"),
                                       foreground=ACC2)
        self._interval_lbl.grid(row=0, column=2, padx=(10, 0))
        ttk.Scale(opt, from_=1, to=10, variable=self._interval, orient="horizontal",
                  command=self._on_interval).grid(row=0, column=1, sticky="ew", padx=12)

        # ── action buttons
        act = ttk.Frame(self)
        act.pack(fill="x", padx=20, pady=(12, 0))

        self._grab_btn = ttk.Button(act, text="① Grab Links",
                                    style="Accent.TButton",
                                    command=self._on_grab)
        self._grab_btn.pack(side="left", padx=(0, 8))

        self._dl_btn = ttk.Button(act, text="② Start Download",
                                  style="Accent.TButton",
                                  command=self._on_download)
        self._dl_btn.pack(side="left", padx=(0, 8))

        self._links_badge = ttk.Label(act, text="", style="TLabel",
                                      foreground=GREEN,
                                      font=("Segoe UI", 9, "bold"))
        self._links_badge.pack(side="left", padx=(4, 0))

        ttk.Button(act, text="Clear Log", style="Sec.TButton",
                   command=self._clear_log).pack(side="right")
        ttk.Button(act, text="📂 Open Downloads", style="Sec.TButton",
                   command=self._open_folder).pack(side="right", padx=(0, 8))

        # ── log
        log_card = ttk.Frame(self, style="Card.TFrame", padding=14)
        log_card.pack(fill="both", expand=True, padx=20, pady=(10, 18))
        hdr = ttk.Frame(log_card, style="Card.TFrame")
        hdr.pack(fill="x")
        ttk.Label(hdr, text="Log", style="Card.TLabel",
                  font=("Segoe UI", 10, "bold")).pack(side="left")
        self._log_count = ttk.Label(hdr, text="", style="Dim.TLabel")
        self._log_count.pack(side="right")

        self._log_box = scrolledtext.ScrolledText(
            log_card, bg="#0a0a14", fg=FG, insertbackground=FG,
            font=("Consolas", 9), relief="flat", bd=0, state="disabled",
        )
        self._log_box.pack(fill="both", expand=True, pady=(8, 0))
        self._log_box.tag_config("ok",   foreground=GREEN)
        self._log_box.tag_config("err",  foreground=RED)
        self._log_box.tag_config("info", foreground=ACC2)

        # ── status bar
        self._status = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self._status,
                  background="#07070f", foreground=GRAY,
                  font=("Segoe UI", 9), anchor="w",
                  padding=(20, 5)).pack(fill="x", side="bottom")

        self._on_mode_change()

    def _build_input_area(self):
        for w in self._input_card.winfo_children():
            w.destroy()

        mode = self._mode.get()

        if mode == "channels":
            ttk.Label(self._input_card,
                      text="Channel URLs — one per line (e.g. https://www.youtube.com/@GizaToys)",
                      style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w")
            ttk.Label(self._input_card,
                      text="/shorts  or bare URL both work",
                      style="Dim.TLabel").pack(anchor="w", pady=(2, 6))
            self._text_input = scrolledtext.ScrolledText(
                self._input_card, height=8, bg="#0a0a14", fg=FG,
                insertbackground=FG, font=("Consolas", 9), relief="flat", bd=0, wrap="none")
            self._text_input.pack(fill="both", expand=True)

        elif mode == "direct":
            ttk.Label(self._input_card,
                      text="Video URLs — one per line",
                      style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w")
            ttk.Label(self._input_card,
                      text="These will be saved to links.txt and downloaded immediately",
                      style="Dim.TLabel").pack(anchor="w", pady=(2, 6))
            self._text_input = scrolledtext.ScrolledText(
                self._input_card, height=8, bg="#0a0a14", fg=FG,
                insertbackground=FG, font=("Consolas", 9), relief="flat", bd=0, wrap="none")
            self._text_input.pack(fill="both", expand=True)

        elif mode == "file":
            count = links_count()
            msg = f"{count} links" if count else "File not found"
            color = GREEN if count else RED

            ttk.Label(self._input_card,
                      text="Using existing links.txt",
                      style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w")
            ttk.Label(self._input_card, text=LINKS_FILE,
                      style="Dim.TLabel").pack(anchor="w", pady=(2, 0))

            row = ttk.Frame(self._input_card, style="Card.TFrame")
            row.pack(anchor="w", pady=(10, 0))
            ttk.Label(row, text="Links found: ", style="Card.TLabel").pack(side="left")
            ttk.Label(row, text=msg, style="Card.TLabel",
                      foreground=color, font=("Segoe UI", 10, "bold")).pack(side="left")

            ttk.Button(self._input_card, text="↻  Refresh", style="Sec.TButton",
                       command=self._build_input_area).pack(anchor="w", pady=(10, 0))

    # ── helpers ───────────────────────────────────────────────────────────────

    def _on_mode_change(self):
        self._build_input_area()
        mode = self._mode.get()
        # In "file" mode, grab step is not needed
        if mode == "file":
            self._grab_btn.config(state="disabled")
        else:
            self._grab_btn.config(state="normal" if not self._busy else "disabled")

    def _on_interval(self, val):
        v = round(float(val))
        self._interval.set(v)
        self._interval_lbl.config(text=f"{v} sec")

    def _log(self, msg: str, tag=None):
        def _w():
            self._log_box.config(state="normal")
            if tag:
                self._log_box.insert("end", msg, tag)
            else:
                self._log_box.insert("end", msg)
            self._log_box.see("end")
            self._log_box.config(state="disabled")
        self.after(0, _w)

    def _clear_log(self):
        self._log_box.config(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.config(state="disabled")

    def _set_busy(self, busy):
        self._busy = busy
        s = "disabled" if busy else "normal"
        self._grab_btn.config(state=s if self._mode.get() != "file" else "disabled")
        self._dl_btn.config(state=s)

    def _refresh_links_badge(self):
        c = links_count()
        if c:
            self._links_badge.config(text=f"  ✔ {c} links in links.txt")
        else:
            self._links_badge.config(text="")
        self.after(3000, self._refresh_links_badge)

    def _update_cookie_label(self):
        path = self._cookies_path.get()
        if os.path.exists(path):
            size = os.path.getsize(path)
            self._cookie_status.config(text="✔ loaded", foreground=GREEN)
        else:
            self._cookie_status.config(text="✘ missing", foreground=RED)

    def _browse_cookies(self):
        path = filedialog.askopenfilename(
            title="Select cookies.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=BASE_DIR,
        )
        if path:
            self._cookies_path.set(path)
            self._update_cookie_label()

    def _open_folder(self):
        folder = BASE_DIR
        if os.path.exists(folder):
            os.startfile(folder)

    def _get_text_input(self):
        try:
            raw = self._text_input.get("1.0", "end").strip()
            return [l.strip() for l in raw.splitlines() if l.strip()]
        except Exception:
            return []

    # ── actions ───────────────────────────────────────────────────────────────

    def _on_grab(self):
        mode = self._mode.get()
        lines = self._get_text_input()
        if not lines:
            messagebox.showwarning("Empty", "Paste at least one URL.")
            return

        self._set_busy(True)
        self._status.set("Collecting links…")
        self._log("─" * 60 + "\n", "info")

        if mode == "channels":
            self._log(f"Fetching top {MAX_PER_CH} shorts from {len(lines)} channels…\n\n", "info")

            def worker():
                links = collect_links(lines, self._log)
                if links:
                    with open(LINKS_FILE, "w", encoding="utf-8") as f:
                        f.write("\n".join(links) + "\n")
                    self._log(f"\n✔ {len(links)} links saved to links.txt\n", "ok")
                    self.after(0, lambda: self._status.set(
                        f"{len(links)} links collected — ready to download"))
                else:
                    self._log("✘ No links found.\n", "err")
                    self.after(0, lambda: self._status.set("No links found"))
                self.after(0, lambda: self._set_busy(False))

            threading.Thread(target=worker, daemon=True).start()

        elif mode == "direct":
            # Just save the pasted links directly
            with open(LINKS_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            self._log(f"✔ {len(lines)} links saved to links.txt\n", "ok")
            self._status.set(f"{len(lines)} links ready")
            self._set_busy(False)

    def _on_download(self):
        mode = self._mode.get()
        cookies = self._cookies_path.get()

        if not os.path.exists(cookies):
            messagebox.showerror(
                "cookies.txt missing",
                "Export your YouTube cookies using the\n"
                "\"Get cookies.txt LOCALLY\" Chrome extension\n"
                "then click Browse to select the file."
            )
            return

        # In "direct" mode, save links first if not done yet
        if mode == "direct":
            lines = self._get_text_input()
            if lines and not os.path.exists(LINKS_FILE):
                with open(LINKS_FILE, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines) + "\n")

        if not os.path.exists(LINKS_FILE) or links_count() == 0:
            messagebox.showerror("No links",
                                 "No links.txt found or it is empty.\n"
                                 "Use Grab Links first, or switch to Direct Links mode.")
            return

        interval = self._interval.get()
        self._set_busy(True)
        self._status.set(f"Downloading… (interval: {interval}s)")
        self._log(f"\nStarting download — {links_count()} links, {interval}s sleep\n", "info")

        def on_done():
            self.after(0, lambda: self._set_busy(False))
            self.after(0, lambda: self._status.set("Download finished"))

        threading.Thread(
            target=run_download,
            args=(interval, cookies, self._log, on_done),
            daemon=True,
        ).start()


if __name__ == "__main__":
    App().mainloop()
