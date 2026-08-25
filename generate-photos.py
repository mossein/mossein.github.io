#!/usr/bin/env python3
"""
generate-photos.py — build the gallery manifest from the photos/ folder.

Workflow:
    1. Drop your image files into  photos/
    2. Run:  python3 generate-photos.py
    3. Commit  photos/ , photos/thumbs/ , and  photos-data.js

It reads each image's EXIF (camera, lens, focal length, aperture, shutter,
ISO, date taken), records its dimensions, and writes two derived tiers — grid
thumbnails in photos/thumbs/ and a 1600px lightbox tier in photos/display/ —
each as both JPEG and WebP. The full-res originals are only linked, never sent
to a visitor, and never modified.

It also renders the grid markup straight into photos.html, so the gallery is in
the HTML for crawlers instead of being assembled client-side.

Requires Pillow:  pip3 install Pillow
"""

import json
import os
import time
import urllib.parse
import urllib.request
from PIL import Image, ImageOps, ExifTags

# iphones shoot heic, so read it natively rather than making everyone convert
# on the way in. it decodes to the same pixels and carries the same exif, and
# the original stays roughly half the weight of the equivalent jpeg
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

PHOTOS_DIR = "photos"
THUMBS_DIR = os.path.join(PHOTOS_DIR, "thumbs")
DISPLAY_DIR = os.path.join(PHOTOS_DIR, "display")
OUTPUT = "photos-data.js"   # loaded via <script>, so it works on file:// too
GEOCACHE = os.path.join(PHOTOS_DIR, ".geocode-cache.json")
THUMB_MAX = 800           # longest edge of grid thumbnail, in px
                          # the grid column tops out around 380px, so 800 still
                          # covers 2x displays without shipping megabytes
THUMB_QUALITY = 78
WEBP_QUALITY = 76         # webp holds up better than jpeg at the same number
DISPLAY_MAX = 1600        # lightbox tier — the originals are 4032px/4mb each,
                          # far more than any screen shows
DISPLAY_QUALITY = 82
EXTS = (".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif")

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
            or addr.get("quarter") or addr.get("city_district")
            or addr.get("village") or addr.get("hamlet"))
    city = (addr.get("city") or addr.get("town") or addr.get("village")
            or addr.get("municipality") or addr.get("county"))
    # out in the country there's no neighbourhood, but there is often a village
    # or hamlet inside the city — that's the name worth printing. when the
    # village is all there is, it fills both slots, so don't say it twice
    if hood == city:
        hood = None
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
        # keep the raw fix too — it's what lets a caption link to a map. rounded
        # to ~11m, which places the shot without publishing a doorstep.
        meta["coords"] = "%.4f,%.4f" % (coords[0], coords[1])

    # drop empty keys
    meta = {k: v for k, v in meta.items() if v}
    return meta, str(raw_date) if raw_date else None


GRID_START = "<!-- PHOTO-GRID:START (generated) -->"
GRID_END = "<!-- PHOTO-GRID:END -->"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def render_grid(items):
    """Grid markup as static HTML.

    The gallery used to be built entirely in JS, which meant 30 photos' worth of
    alt text and locations were invisible to anything that doesn't run scripts.
    """
    out = []
    for i, p in enumerate(items):
        cap = "  ·  ".join(
            x for x in (p["meta"].get("location"), p["meta"].get("date")) if x
        )
        out.append('        <figure class="photo-item">')
        out.append('          <picture>')
        out.append('            <source type="image/webp" srcset="%s" />'
                   % esc(urllib.parse.quote(p["thumbWebp"])))
        out.append(
            '            <img src="%s" alt="%s" width="%d" height="%d" '
            'loading="%s" decoding="async" data-index="%d" />'
            % (esc(urllib.parse.quote(p["thumb"])), esc(p["alt"]),
               p["width"], p["height"],
               "eager" if i < 3 else "lazy", i)
        )
        out.append('          </picture>')
        if cap:
            out.append('          <figcaption class="photo-caption">%s</figcaption>'
                       % esc(cap))
        out.append('        </figure>')
    return "\n".join(out)


def write_grid(items):
    try:
        html = open("photos.html").read()
    except OSError:
        return
    a, b = html.find(GRID_START), html.find(GRID_END)
    if a == -1 or b == -1:
        print("photos.html has no PHOTO-GRID markers — skipped grid injection.")
        return
    new = (html[:a + len(GRID_START)] + "\n" + render_grid(items) + "\n      "
           + html[b:])
    if new != html:
        open("photos.html", "w").write(new)
        print("injected %d figures into photos.html" % len(items))


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
    os.makedirs(DISPLAY_DIR, exist_ok=True)

    files = sorted(
        f for f in os.listdir(PHOTOS_DIR)
        if f.lower().endswith(EXTS) and os.path.isfile(os.path.join(PHOTOS_DIR, f))
    )

    items = []
    kept_thumbs = set()
    kept_display = set()
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
        rgb = thumb.convert("RGB")
        rgb.save(thumb_path, "JPEG", quality=THUMB_QUALITY, optimize=True)

        # webp alongside the jpeg — the page serves it via <picture>, so browsers
        # that don't support it still get the jpeg
        webp_name = stem + ".webp"
        webp_path = os.path.join(THUMBS_DIR, webp_name)
        kept_thumbs.add(webp_name)
        rgb.save(webp_path, "WEBP", quality=WEBP_QUALITY, method=6)

        # display tier for the lightbox, so opening a photo doesn't pull the
        # 4mb original down the wire
        disp = upright.copy()
        disp.thumbnail((DISPLAY_MAX, DISPLAY_MAX))
        disp_rgb = disp.convert("RGB")
        disp_jpg = os.path.join(DISPLAY_DIR, stem + ".jpg")
        disp_webp = os.path.join(DISPLAY_DIR, stem + ".webp")
        kept_display.update([stem + ".jpg", stem + ".webp"])
        disp_rgb.save(disp_jpg, "JPEG", quality=DISPLAY_QUALITY, optimize=True,
                      progressive=True)
        disp_rgb.save(disp_webp, "WEBP", quality=DISPLAY_QUALITY, method=6)

        # prefer real description over the camera's filename, which reads as
        # gibberish to a screen reader
        if meta.get("location") and meta.get("date"):
            alt = "%s, %s" % (meta["location"], meta["date"])
        elif meta.get("location"):
            alt = meta["location"]
        elif meta.get("date"):
            alt = "photo taken %s" % meta["date"]
        else:
            alt = stem.replace("_", " ").replace("-", " ").strip()

        items.append({
            "src": path,
            "thumb": thumb_path,
            "thumbWebp": webp_path,
            "display": disp_jpg,
            "displayWebp": disp_webp,
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

    # the originals are gitignored, so a fresh clone has the derived tiers but
    # no sources. without this the scan would come back empty, read every
    # thumbnail as orphaned, and delete the whole gallery
    if not items and (os.listdir(THUMBS_DIR) or os.listdir(DISPLAY_DIR)):
        print("\nno source photos found, but photos/thumbs/ and photos/display/")
        print("still hold a gallery. refusing to prune it.")
        print("the originals live outside git: copy them back into photos/ first.")
        return

    # prune derived images whose source photo no longer exists
    pruned = 0
    for d, keep in ((THUMBS_DIR, kept_thumbs), (DISPLAY_DIR, kept_display)):
        for f in os.listdir(d):
            if f.lower().endswith((".jpg", ".webp")) and f not in keep:
                try:
                    os.remove(os.path.join(d, f))
                    pruned += 1
                except OSError:
                    pass
    write_manifest(items)
    write_grid(items)
    save_geocache()
    print("\nwrote %s with %d photo(s)." % (OUTPUT, len(items)))
    if pruned:
        print("pruned %d orphaned thumbnail(s)." % pruned)


if __name__ == "__main__":
    main()
