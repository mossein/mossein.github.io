#!/usr/bin/env python3
"""
generate-photos.py — build the gallery manifest from the photos/ folder.

Workflow:
    1. Drop your image files into  photos/
    2. Run:  python3 generate-photos.py
    3. Commit  photos/ , photos/thumbs/ , and  photos-data.js

It reads each image's EXIF (camera, lens, focal length, aperture, shutter,
ISO, date taken), records its dimensions, and writes web-sized thumbnails to
photos/thumbs/ so the grid stays fast — the lightbox still loads the full-res
original. Originals are never modified.

Requires Pillow:  pip3 install Pillow
"""

import json
import os
import time
import urllib.parse
import urllib.request
from PIL import Image, ImageOps, ExifTags

PHOTOS_DIR = "photos"
THUMBS_DIR = os.path.join(PHOTOS_DIR, "thumbs")
OUTPUT = "photos-data.js"   # loaded via <script>, so it works on file:// too
GEOCACHE = os.path.join(PHOTOS_DIR, ".geocode-cache.json")
THUMB_MAX = 1400          # longest edge of grid thumbnail, in px
THUMB_QUALITY = 82
EXTS = (".jpg", ".jpeg", ".png", ".webp")

# name -> EXIF tag id
TAG = {name: tid for tid, name in ExifTags.TAGS.items()}
GPS_TAG = {name: tid for tid, name in ExifTags.GPSTAGS.items()}


def _num(v):
    """Coerce an EXIF rational/float to a plain float, or None."""
    try:
        return float(v)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def fmt_shutter(v):
    v = _num(v)
    if not v or v <= 0:
        return None
    if v >= 1:
        return ("%g" % v) + "s"
    return "1/%d" % round(1 / v) + "s"


def fmt_aperture(v):
    v = _num(v)
    return ("f/%g" % v) if v else None


def fmt_focal(v):
    v = _num(v)
    return ("%dmm" % round(v)) if v else None


def fmt_date(s):
    # EXIF DateTimeOriginal looks like "2026:05:12 14:33:07"
    if not s:
        return None
    try:
        date_part = str(s).split(" ")[0]
        y, m, d = date_part.split(":")
        months = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return "%s %d, %s" % (months[int(m)], int(d), y)
    except Exception:
        return None


def _to_degrees(value):
    d, m, s = [float(x) for x in value]
    return d + m / 60.0 + s / 3600.0


def get_gps(img):
    """Return (lat, lon) in decimal degrees, or None."""
    exif = img.getexif()
    try:
        gps = exif.get_ifd(0x8825)  # GPSInfo IFD
    except Exception:
        return None
    if not gps:
        return None
    lat = gps.get(GPS_TAG.get("GPSLatitude"))
    lat_ref = gps.get(GPS_TAG.get("GPSLatitudeRef"))
    lon = gps.get(GPS_TAG.get("GPSLongitude"))
    lon_ref = gps.get(GPS_TAG.get("GPSLongitudeRef"))
    if not (lat and lon):
        return None
    try:
        latd = _to_degrees(lat)
        lond = _to_degrees(lon)
    except Exception:
        return None
    if str(lat_ref).upper().startswith("S"):
        latd = -latd
    if str(lon_ref).upper().startswith("W"):
        lond = -lond
    return (latd, lond)


_geocache = None


def _load_geocache():
    global _geocache
    if _geocache is None:
        try:
            with open(GEOCACHE) as f:
                _geocache = json.load(f)
        except Exception:
            _geocache = {}
    return _geocache


def save_geocache():
    if _geocache is not None:
        try:
            with open(GEOCACHE, "w") as f:
                json.dump(_geocache, f, indent=2, sort_keys=True)
        except Exception:
            pass


def reverse_geocode(lat, lon):
    """Neighborhood + city for a coordinate, via OpenStreetMap Nominatim.
    Cached on disk so repeated runs are instant and gentle on the API."""
    cache = _load_geocache()
    key = "%.3f,%.3f" % (lat, lon)   # ~110m buckets; shares nearby lookups
    if key in cache:
        return cache[key]

    url = "https://nominatim.openstreetmap.org/reverse?" + urllib.parse.urlencode({
        "lat": "%.6f" % lat,
        "lon": "%.6f" % lon,
        "format": "json",
        "zoom": 16,
        "addressdetails": 1,
    })
    req = urllib.request.Request(
        url, headers={"User-Agent": "mohammad.page-photo-gallery/1.0 (personal site)"}
    )
    try:
        time.sleep(1.1)  # Nominatim usage policy: <= 1 request/sec
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.load(r)
    except Exception as e:
        print("  geocode failed for %s (%s)" % (key, e))
        cache[key] = None
        return None

    addr = data.get("address", {})
    hood = (addr.get("neighbourhood") or addr.get("suburb")
            or addr.get("quarter") or addr.get("city_district"))
    city = (addr.get("city") or addr.get("town") or addr.get("village")
            or addr.get("municipality") or addr.get("county"))
    parts = [p for p in (hood, city) if p]
    loc = ", ".join(parts) if parts else None
    cache[key] = loc
    return loc


def extract_meta(img):
    exif = img.getexif()
    if not exif:
        return {}, None
    try:
        sub = exif.get_ifd(0x8769)  # Exif sub-IFD (ExifOffset)
    except Exception:
        sub = {}

    def get(name):
        tid = TAG.get(name)
        if tid is None:
            return None
        if tid in sub:
            return sub[tid]
        return exif.get(tid)

    make = (get("Make") or "").strip()
    model = (get("Model") or "").strip()
    # avoid "Canon Canon EOS R6" duplication
    if make and model and model.lower().startswith(make.lower()):
        camera = model
    else:
        camera = (make + " " + model).strip()

    iso = get("ISOSpeedRatings")
    raw_date = get("DateTimeOriginal") or get("DateTime")

    lens = (get("LensModel") or "").strip()
    # Phone lens names ("iPhone 15 Pro back camera 6.765mm f/1.78") just repeat
    # the focal length and aperture we already show — drop them as noise. Keep
    # real lens names (e.g. "RF 50mm F1.2 L USM") where they're meaningful.
    if lens and ("back camera" in lens.lower()
                 or "front camera" in lens.lower()
                 or "back triple camera" in lens.lower()
                 or "back dual" in lens.lower()):
        lens = None

    meta = {
        "camera": camera or None,
        "lens": lens or None,
        "focal": fmt_focal(get("FocalLength")),
        "aperture": fmt_aperture(get("FNumber")),
        "shutter": fmt_shutter(get("ExposureTime")),
        "iso": ("ISO %d" % int(iso)) if iso else None,
        "date": fmt_date(raw_date),
    }

    coords = get_gps(img)
    if coords:
        loc = reverse_geocode(coords[0], coords[1])
        if loc:
            meta["location"] = loc

    # drop empty keys
    meta = {k: v for k, v in meta.items() if v}
    return meta, str(raw_date) if raw_date else None


def write_manifest(items):
    # Emit as a JS file so the gallery can load it with <script> — that works
    # both on GitHub Pages and when opening photos.html directly (file://),
    # which a fetch() of a .json file does not.
    payload = json.dumps(items, indent=2)
    with open(OUTPUT, "w") as f:
        f.write("window.PHOTOS = " + payload + ";\n")


def main():
    if not os.path.isdir(PHOTOS_DIR):
        os.makedirs(PHOTOS_DIR)
        print("created %s/ — drop your images in there and run again." % PHOTOS_DIR)
        write_manifest([])
        return

    os.makedirs(THUMBS_DIR, exist_ok=True)

    files = sorted(
        f for f in os.listdir(PHOTOS_DIR)
        if f.lower().endswith(EXTS) and os.path.isfile(os.path.join(PHOTOS_DIR, f))
    )

    items = []
    kept_thumbs = set()
    for name in files:
        path = os.path.join(PHOTOS_DIR, name)
        try:
            img = Image.open(path)
        except Exception as e:
            print("skip %s (%s)" % (name, e))
            continue

        meta, sort_date = extract_meta(img)

        # upright copy for thumbnail + correct display dimensions
        upright = ImageOps.exif_transpose(img)
        w, h = upright.size

        stem = os.path.splitext(name)[0]
        thumb_name = stem + ".jpg"
        thumb_path = os.path.join(THUMBS_DIR, thumb_name)
        kept_thumbs.add(thumb_name)
        thumb = upright.copy()
        thumb.thumbnail((THUMB_MAX, THUMB_MAX))
        thumb.convert("RGB").save(thumb_path, "JPEG", quality=THUMB_QUALITY, optimize=True)

        alt = stem.replace("_", " ").replace("-", " ").strip()

        items.append({
            "src": path,
            "thumb": thumb_path,
            "width": w,
            "height": h,
            "alt": alt,
            "meta": meta,
            "_sort": sort_date or "",
        })
        print("ok  %s  %s" % (name, " · ".join(meta.values()) if meta else "(no exif)"))

    # newest first by capture date, fall back to filename
    items.sort(key=lambda it: (it["_sort"], it["src"]), reverse=True)
    for it in items:
        it.pop("_sort", None)

    # prune thumbnails whose source photo no longer exists
    pruned = 0
    for f in os.listdir(THUMBS_DIR):
        if f.lower().endswith(".jpg") and f not in kept_thumbs:
            try:
                os.remove(os.path.join(THUMBS_DIR, f))
                pruned += 1
            except OSError:
                pass

    write_manifest(items)
    save_geocache()
    print("\nwrote %s with %d photo(s)." % (OUTPUT, len(items)))
    if pruned:
        print("pruned %d orphaned thumbnail(s)." % pruned)


if __name__ == "__main__":
    main()
