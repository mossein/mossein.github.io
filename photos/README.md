# photos/

Drop your photography here, then run the generator from the repo root:

```bash
python3 generate-photos.py
```

Drop in JPEG, PNG, WebP, or HEIC straight off the phone — no converting.

That scans this folder, reads each photo's EXIF (camera, lens, focal length,
aperture, shutter, ISO, date, and GPS → neighborhood/city), builds web-sized
thumbnails in `photos/thumbs/`, and writes `photos-data.js` — which the gallery
(`photos.html`) reads.

Then commit `photos/`, `photos/thumbs/`, and `photos-data.js`.

Notes:
- Filenames become the alt text (underscores/dashes → spaces), so name them
  meaningfully if you like, e.g. `toronto-skyline-dusk.jpg`.
- Originals are never modified; the lightbox loads them full-resolution.
- Photos are ordered newest-first by capture date.
- Re-running rebuilds everything from scratch (no duplicates) and prunes
  thumbnails whose source photo was removed.
- Location lookups need internet once, then cache to `.geocode-cache.json`.
- HEIC needs `pip3 install pillow-heif`; without it those files are skipped.
  Keeping the HEIC as the original is preferred — it's about half the size of
  the same shot as JPEG, and the browser only ever loads the derived tiers.
- Phone lens names are dropped from the caption (they just repeat focal +
  aperture); real lens names are kept.
