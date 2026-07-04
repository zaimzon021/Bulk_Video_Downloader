"""
YouTube Channel Profile Picture Downloader
Uses yt-dlp to fetch channel avatars without requiring an API key.

Requirements:
    pip install yt-dlp requests
"""

import os
import re
import requests
import yt_dlp

# List of YouTube channel URLs
CHANNELS = [
    "https://www.youtube.com/@DROBASHEVICH",
    "https://www.youtube.com/@scarce_fpv",
    "https://www.youtube.com/@ZZZAIRSOFT",
    "https://www.youtube.com/@harshcarpenter",
    "https://www.youtube.com/@RealisticCrash-c1r",
    "https://www.youtube.com/@FixBeam",
    "https://www.youtube.com/@CrashWizards",
    "https://www.youtube.com/@CrashMania1",
    "https://www.youtube.com/@Crash_Shotz",
    "https://www.youtube.com/@dillonlatham",
    "https://www.youtube.com/@AssonDriver",
    "https://www.youtube.com/@LeGraffDrive",
    "https://www.youtube.com/@TheMilitaryTok",
    "https://www.youtube.com/@bitesizestoriesTV",
    "https://www.youtube.com/@Tabs_Original",
    "https://www.youtube.com/@roadglowde",
    "https://www.youtube.com/@U9Tech1",
    "https://www.youtube.com/@WyattWebster",
    "https://www.youtube.com/@VelixCam",
    "https://www.youtube.com/@PocketToolWarehouse",
    "https://www.youtube.com/@stuffyouactuallyneed826",
    "https://www.youtube.com/@TRNCHWRFXR",
    "https://www.youtube.com/@allenzhou4828",
    "https://www.youtube.com/@Never_get_off_the_boat",
    "https://www.youtube.com/@PianoAndChill1",
    "https://www.youtube.com/@mrbrushhour",
    "https://www.youtube.com/@marvinblend",
    "https://www.youtube.com/@silasnoyes1",
]

OUTPUT_DIR = "channel_pfps"


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def clean_url(url: str) -> str:
    """Strip /shorts, /videos etc. from the end so we get the bare channel URL."""
    return re.sub(r'/(shorts|videos|featured|community|playlists|about)/?$', '', url.rstrip('/'))


def get_channel_avatar(channel_url: str):
    channel_url = clean_url(channel_url)
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "ignoreerrors": True,
        "playlist_items": "0",
    }
    tabs = ["/shorts", "/videos", "/featured", ""]
    info = None
    for tab in tabs:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(channel_url + tab, download=False)
            if result and (result.get("thumbnails") or result.get("thumbnail")):
                info = result
                break
        except Exception:
            continue
    if not info:
        return None

    channel_name = info.get("channel") or info.get("uploader") or channel_url.split("@")[-1]
    thumbnails = info.get("thumbnails") or []
    avatar_url = None
    for thumb in reversed(thumbnails):
        url = thumb.get("url", "")
        if "yt3.ggpht.com" in url or "yt3.googleusercontent.com" in url:
            avatar_url = url
            break
    if not avatar_url:
        avatar_url = info.get("thumbnail")
    return (channel_name, avatar_url) if avatar_url else None


def download_image(url: str, filepath: str) -> bool:
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
        return True
    except requests.RequestException as e:
        print(f"    Download error: {e}")
        return False


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    seen = set()
    unique_channels = []
    for url in CHANNELS:
        url = clean_url(url.strip())
        if url and url not in seen:
            seen.add(url)
            unique_channels.append(url)

    print(f"Downloading profile pictures for {len(unique_channels)} channels...\n")
    success, failed = [], []

    for i, channel_url in enumerate(unique_channels, 1):
        handle = channel_url.split("@")[-1]
        print(f"[{i}/{len(unique_channels)}] {handle}", end=" ... ", flush=True)
        try:
            result = get_channel_avatar(channel_url)
            if not result:
                print("SKIP (no avatar found)")
                failed.append(handle)
                continue
            channel_name, avatar_url = result
            safe_name = sanitize_filename(channel_name or handle)
            ext = ".jpg"
            for candidate in (".jpg", ".jpeg", ".png", ".webp"):
                if candidate in avatar_url.lower():
                    ext = candidate
                    break
            filepath = os.path.join(OUTPUT_DIR, f"{safe_name}{ext}")
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                print(f"SKIP (already exists)  →  {filepath}")
                success.append(handle)
                continue
            if download_image(avatar_url, filepath):
                print(f"OK  →  {filepath}")
                success.append(handle)
            else:
                print("FAIL (download error)")
                failed.append(handle)
        except Exception as e:
            print(f"FAIL ({e})")
            failed.append(handle)

    print(f"\n{'='*50}")
    print(f"Done!  {len(success)} succeeded,  {len(failed)} failed.")
    if failed:
        print("Failed channels:")
        for h in failed:
            print(f"  - {h}")
    print(f"Images saved to: {os.path.abspath(OUTPUT_DIR)}/")


if __name__ == "__main__":
    main()
