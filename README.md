# YouTube Shorts Downloader

A GUI tool to download the most popular YouTube Shorts from any channel list, plus a separate tool to bulk-download channel profile pictures.

## Features

- Auto-fetches top popular Shorts from any list of YouTube channels (sorted by view count)
- Three download modes: grab from channels, paste links directly, or use existing links
- Bulk channel profile picture downloader with GUI
- Adjustable sleep interval (1–10s) between downloads
- Skips already-downloaded videos using a history archive
- Downloads at highest available quality (1080p60)

## Requirements

### Python packages
```
pip install yt-dlp requests
```

### Binaries (place in same folder as the scripts)
| File | Download |
|------|----------|
| `yt-dlp.exe` | https://github.com/yt-dlp/yt-dlp/releases/latest |
| `deno.exe` | https://deno.land |
| `ffmpeg.exe` | https://ffmpeg.org/download.html |

### Cookies
Export your YouTube cookies using the **"Get cookies.txt LOCALLY"** Chrome extension while logged into YouTube, and save as `cookies.txt` in the same folder.

> ⚠️ Cookies expire after a few days. Re-export if you get authentication errors.

## Usage

### Video Downloader GUI
```
python app.py
```

1. Pick a mode:
   - **Grab from channels** — paste channel URLs, auto-fetches top shorts
   - **Paste direct links** — paste video URLs directly
   - **Use existing links.txt** — downloads without re-fetching

2. Set sleep interval with the slider
3. Click **Grab Links** then **Start Download**

### Profile Picture Downloader GUI
```
python pfp_downloader.py
```

Paste channel URLs and click **Download Profile Pictures**.

## Setup on a new computer

Run `setup.bat` — it installs Python dependencies and checks for required binaries automatically.

## File structure

```
app.py                  # Video downloader GUI
pfp_downloader.py       # Profile picture downloader GUI
setup.bat               # One-click setup script
requirements.txt        # Python dependencies
cookies.txt             # Your YouTube cookies (not committed)
links.txt               # Collected video links (not committed)
history.txt             # Download archive (not committed)
```
