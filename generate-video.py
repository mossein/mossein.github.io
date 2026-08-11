#!/usr/bin/env python3
"""
generate-video.py — turn phone clips into web-sized loops for journal entries.

Workflow:
    1. Drop clips into  clips/   (mov, mp4, whatever came off the phone)
    2. Run:  python3 generate-video.py
    3. Commit  media/   — do NOT commit clips/ (it's gitignored)

Why this exists: GitHub Pages wants the published site under 1 GB, and git keeps
every version of every file forever, so an unedited 60 MB clip is 60 MB you can
never get back. Each clip here comes out as a muted, looping MP4 (H.264, for
reach) plus a WebM (VP9, smaller where supported) and a poster frame, capped in
both length and resolution. A 15-second clip lands around 1–3 MB.

Audio is stripped on purpose: these are moving photographs, they autoplay, and
browsers block sound on autoplay anyway.

Requires ffmpeg:  brew install ffmpeg
"""

import json
import os
import shutil
import subprocess
import sys

SRC_DIR = "clips"
OUT_DIR = "media"
MANIFEST = "media-data.js"

MAX_SECONDS = 20      # anything longer is trimmed from the start
MAX_HEIGHT = 1080     # phone clips are often 4K; nothing here needs it
FPS = 30
CRF_H264 = 26         # visually clean at this size; raise to shrink further
CRF_VP9 = 34          # vp9 numbers don't mean the same thing as x264's
SRC_EXTS = (".mov", ".mp4", ".m4v", ".avi", ".webm", ".mkv")


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def need_ffmpeg():
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            print("missing %s — install it with:  brew install ffmpeg" % tool)
            return False
    return True


def probe(path):
    """(duration_seconds, width, height) or None."""
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height:format=duration",
             "-of", "json", path])
    if r.returncode:
        return None
    try:
        d = json.loads(r.stdout)
        st = d["streams"][0]
        return (float(d["format"]["duration"]), int(st["width"]), int(st["height"]))
    except (KeyError, IndexError, ValueError):
        return None


def encode(src, stem, duration):
    """Write mp4 + webm + poster. Returns the manifest entry."""
    mp4 = os.path.join(OUT_DIR, stem + ".mp4")
    webm = os.path.join(OUT_DIR, stem + ".webm")
    poster = os.path.join(OUT_DIR, stem + ".jpg")

    # even dimensions or H.264 refuses to encode
    scale = "scale=-2:'min(%d,ih)'" % MAX_HEIGHT
    clip = ["-t", str(MAX_SECONDS)] if duration > MAX_SECONDS else []

    common = ["ffmpeg", "-y", "-loglevel", "error", "-i", src] + clip + [
        "-an",                      # no audio: these autoplay muted
        "-vf", "%s,fps=%d" % (scale, FPS),
    ]
    r = run(common + [
        "-c:v", "libx264", "-crf", str(CRF_H264), "-preset", "slow",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",  # first frame paints before the whole file lands
        mp4,
    ])
    if r.returncode:
        print("  mp4 failed: %s" % r.stderr.strip().split("\n")[-1])
        return None

    r = run(common + [
        "-c:v", "libvpx-vp9", "-crf", str(CRF_VP9), "-b:v", "0",
        "-row-mt", "1",
        webm,
    ])
    if r.returncode:
        print("  webm failed (keeping mp4): %s"
              % r.stderr.strip().split("\n")[-1])
        webm = None
    elif os.path.getsize(webm) >= os.path.getsize(mp4):
        # vp9 usually wins on real footage but not always — a webm that's bigger
        # than the h264 is worse in every way, so don't ship it
        print("  webm was larger than the mp4 (%.2fMB vs %.2fMB) — discarded"
              % (os.path.getsize(webm) / 1048576.0,
                 os.path.getsize(mp4) / 1048576.0))
        os.remove(webm)
        webm = None

    # poster from ~1s in; the very first frame is often a blur
    seek = "1" if duration > 1.5 else "0"
    r = run(["ffmpeg", "-y", "-loglevel", "error", "-ss", seek, "-i", src,
             "-vframes", "1", "-vf", scale, "-q:v", "4", poster])
    if r.returncode:
        poster = None

    entry = {"mp4": mp4, "poster": poster, "stem": stem}
    if webm:
        entry["webm"] = webm
    return entry


def main():
    if not need_ffmpeg():
        return 1
    if not os.path.isdir(SRC_DIR):
        os.makedirs(SRC_DIR)
        print("created %s/ — drop clips in there and run again." % SRC_DIR)
        return 0

    os.makedirs(OUT_DIR, exist_ok=True)
    srcs = sorted(f for f in os.listdir(SRC_DIR)
                  if f.lower().endswith(SRC_EXTS))
    if not srcs:
        print("no clips in %s/ (looked for %s)" % (SRC_DIR, ", ".join(SRC_EXTS)))
        return 0

    items = []
    for name in srcs:
        src = os.path.join(SRC_DIR, name)
        stem = os.path.splitext(name)[0].replace(" ", "-").lower()
        info = probe(src)
        if not info:
            print("skip %s (unreadable)" % name)
            continue
        duration, w, h = info
        entry = encode(src, stem, duration)
        if not entry:
            continue
        before = os.path.getsize(src)
        after = os.path.getsize(entry["mp4"])
        if entry.get("webm"):
            after = min(after, os.path.getsize(entry["webm"]))
        items.append(entry)
        print("ok  %-28s %5.1fs  %dx%d  %.1fMB -> %.2fMB  (%.0f%% smaller)"
              % (name, duration, w, h, before / 1048576, after / 1048576,
                 100 - 100.0 * after / before))

    with open(MANIFEST, "w") as f:
        f.write("window.CLIPS = " + json.dumps(items, indent=2) + ";\n")

    total = sum(os.path.getsize(i["mp4"]) for i in items)
    print("\nwrote %s with %d clip(s), %.1fMB of mp4 total."
          % (MANIFEST, len(items), total / 1048576))
    print("paste into a journal entry:\n")
    if items:
        i = items[0]
        print('  <video src="%s"%s muted loop playsinline preload="metadata"></video>'
              % (i["mp4"], ' poster="%s"' % i["poster"] if i["poster"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
