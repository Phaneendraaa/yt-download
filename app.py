"""Local YouTube downloader (yt-dlp). Usage: python app.py [url ...]"""
import sys
from pathlib import Path

import imageio_ffmpeg
import yt_dlp

OUT = Path(__file__).parent / "downloads"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

QUALITIES = {
    "1": ("Best quality (MP4)", "bv*+ba/b"),
    "2": ("1080p (MP4)", "bv*[height<=1080]+ba/b[height<=1080]"),
    "3": ("720p (MP4)", "bv*[height<=720]+ba/b[height<=720]"),
    "4": ("480p (MP4)", "bv*[height<=480]+ba/b[height<=480]"),
    "5": ("Audio only (MP3)", "ba/b"),
}


def download(urls, choice):
    _, fmt = QUALITIES[choice]
    opts = {
        "format": fmt,
        "outtmpl": str(OUT / "%(title).150B [%(id)s].%(ext)s"),
        "ffmpeg_location": FFMPEG,
        "ignoreerrors": True,
        "windowsfilenames": True,
    }
    if choice == "5":
        opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ]
    else:
        opts["merge_output_format"] = "mp4"
    OUT.mkdir(exist_ok=True)
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download(urls)
    print(f"\nDone. Files saved in: {OUT}")


def main():
    urls = sys.argv[1:]
    while True:
        if not urls:
            raw = input("\nPaste YouTube link(s) (space separated, blank to quit): ").strip()
            if not raw:
                return
            urls = raw.split()
        print("\nQuality:")
        for k, (name, _) in QUALITIES.items():
            print(f"  {k}. {name}")
        choice = input("Choose [1]: ").strip() or "1"
        if choice not in QUALITIES:
            print("Invalid choice.")
            continue
        try:
            download(urls, choice)
        except Exception as e:
            print(f"Error: {e}")
        urls = []


if __name__ == "__main__":
    main()
