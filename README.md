# yt-download
Local YouTube downloader with a web UI (yt-dlp + Flask).

Windows: double-click `start.bat`. A browser tab opens at http://127.0.0.1:8000.
Paste links (one per line), pick quality, click Download. Up to 3 download at once.
Files go to `downloads/`. Needs Python 3.9+; ffmpeg is installed automatically via pip.

Change `MAX_PARALLEL` in `app.py` to download more at once.
