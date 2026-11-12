"""Local YouTube downloader with a web UI. Run: python app.py  (opens http://127.0.0.1:8000)"""
import os
import sys
import threading
import uuid
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import imageio_ffmpeg
import yt_dlp
from flask import Flask, jsonify, request, send_from_directory

BASE = Path(__file__).parent
OUT = BASE / "downloads"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
MAX_PARALLEL = 3  # downloads running at the same time
HOST, PORT = "127.0.0.1", 8000

QUALITIES = {
    "best": "bv*+ba/b",
    "1080": "bv*[height<=1080]+ba/b[height<=1080]",
    "720": "bv*[height<=720]+ba/b[height<=720]",
    "480": "bv*[height<=480]+ba/b[height<=480]",
    "mp3": "ba/b",
}

app = Flask(__name__, static_folder=str(BASE / "static"), static_url_path="/static")
pool = ThreadPoolExecutor(max_workers=MAX_PARALLEL)
jobs = {}
lock = threading.Lock()


def update(job_id, **kw):
    with lock:
        jobs[job_id].update(kw)


def run_job(job_id):
    job = jobs[job_id]
    quality = job["quality"]

    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            pct = (d.get("downloaded_bytes", 0) / total * 100) if total else 0
            info = d.get("info_dict") or {}
            update(
                job_id,
                status="downloading",
                percent=round(pct, 1),
                title=info.get("title") or job["title"],
                speed=(d.get("_speed_str") or "").strip(),
                eta=(d.get("_eta_str") or "").strip(),
                item=(f"{info.get('playlist_index')}/{info.get('n_entries')}"
                      if info.get("playlist_index") else ""),
            )
        elif d["status"] == "finished":
            update(job_id, status="processing", percent=100, speed="", eta="")

    opts = {
        "format": QUALITIES[quality],
        "outtmpl": str(OUT / "%(title).150B [%(id)s].%(ext)s"),
        "ffmpeg_location": FFMPEG,
        "noplaylist": not job["playlist"],
        "windowsfilenames": True,
        "progress_hooks": [hook],
        "quiet": True,
        "no_warnings": True,
    }
    if quality == "mp3":
        opts["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ]
    else:
        opts["merge_output_format"] = "mp4"

    try:
        OUT.mkdir(exist_ok=True)
        update(job_id, status="downloading")
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(job["url"], download=True)
        entries = info.get("entries") or [info]
        files = []
        for e in entries:
            for r in (e or {}).get("requested_downloads") or []:
                p = Path(r["filepath"])
                if p.exists():
                    files.append(p.name)
        update(job_id, status="done", percent=100, files=files,
               title=info.get("title") or job["title"])
    except Exception as e:  # noqa: BLE001
        msg = str(e).replace("ERROR: ", "")
        update(job_id, status="error", error=msg[:300])


@app.get("/")
def index():
    return send_from_directory(BASE / "static", "index.html")


@app.post("/api/add")
def add():
    data = request.get_json(force=True)
    quality = data.get("quality", "best")
    if quality not in QUALITIES:
        return jsonify(error="bad quality"), 400
    urls = [u.strip() for u in (data.get("urls") or []) if u.strip()]
    if not urls:
        return jsonify(error="no links"), 400
    for url in urls:
        jid = uuid.uuid4().hex[:8]
        with lock:
            jobs[jid] = dict(id=jid, url=url, quality=quality, playlist=bool(data.get("playlist")),
                             status="queued", percent=0, title=url, speed="", eta="",
                             item="", files=[], error="")
        pool.submit(run_job, jid)
    return jsonify(ok=True, count=len(urls))


@app.get("/api/jobs")
def list_jobs():
    with lock:
        return jsonify(list(jobs.values()))


@app.post("/api/clear")
def clear():
    with lock:
        for k in [k for k, j in jobs.items() if j["status"] in ("done", "error")]:
            del jobs[k]
    return jsonify(ok=True)


@app.get("/files/<path:name>")
def get_file(name):
    return send_from_directory(OUT, name, as_attachment=True)


@app.post("/api/open-folder")
def open_folder():
    OUT.mkdir(exist_ok=True)
    if sys.platform.startswith("win"):
        os.startfile(OUT)  # noqa: S606
    return jsonify(ok=True, path=str(OUT))


if __name__ == "__main__":
    url = f"http://{HOST}:{PORT}"
    print(f"YouTube Downloader running at {url}  (Ctrl+C to stop)")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host=HOST, port=PORT, threaded=True)
