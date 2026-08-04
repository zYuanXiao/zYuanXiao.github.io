#!/usr/bin/env python3
"""tools/build_profile.py
Build two 512x512 square profile avatars for the home page:
  zhiyuan-xiao.jpg        default (resting)
  zhiyuan-xiao-hover.jpg  hover
Crop is a square centred above a detected face (OpenCV Haar cascade) using the
SAME face->square ratio for both images, so the person keeps a roughly identical
scale/proportion across the two photos. If detection fails the script falls back
to a centre-square crop and prints a warning; you can instead pass an explicit
crop centre with --default-center / --hover-center (cx,cy,side in source pixels).

Example (Windows):
  python tools/build_profile.py \
      --default "C:/Users/yuanx/Downloads/Flux2_Klein_9b_kv_00058_.png" \
      --hover   "C:/Users/yuanx/Downloads/Weixin Image_20260803183116_2217_7.jpg" \
      --out assets/profile
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

import numpy as np
import cv2
from PIL import Image

TARGET = 512              # output square edge (matches existing avatar source)
FACE_RATIO = 3.6          # square side = face_height * FACE_RATIO  (same for both)
HEADROOM = -0.45          # shift crop centre up by 0.45*face_h (headroom above head)
JPEG_QUALITY = 88

_CASCADE_FILES = [
    "haarcascade_frontalface_alt2.xml",
    "haarcascade_frontalface_default.xml",
    "haarcascade_profileface.xml",
]
_WINNING_CASCADE = None  # set by detect_face(); read by build() for the face= log line


def detect_face(gray: np.ndarray):
    global _WINNING_CASCADE
    best = None
    best_name = None
    for name in _CASCADE_FILES:
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + name)
        if cascade.empty():
            continue
        faces = cascade.detectMultiScale(
            gray, scaleFactor=1.05, minNeighbors=3, minSize=(40, 40)
        )
        for f in faces:
            if best is None or f[2] * f[3] > best[2] * best[3]:
                best = (int(f[0]), int(f[1]), int(f[2]), int(f[3]))
                best_name = name
    _WINNING_CASCADE = best_name
    if best is None:
        return None
    return best


def square_around(cx: int, cy: int, side: int, W: int, H: int):
    side = min(side, min(W, H))
    half = side // 2
    x0 = min(max(cx - half, 0), W - side)
    y0 = min(max(cy - half, 0), H - side)
    return x0, y0, side


def build(src: str, out: Path, anchor):
    try:
        rgb = np.array(Image.open(src).convert("RGB"))
    except Exception as e:
        raise SystemExit(f"cannot read image {src}: {e}")
    H, W = rgb.shape[:2]
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    if anchor:
        cx, cy, side = anchor
    else:
        face = detect_face(gray)
        if face is None:
            print(f"  [warn] no face in {Path(src).name} -> centre-square crop "
                  f"(override with --*-center cx,cy,side)", file=sys.stderr)
            cx, cy, side = W // 2, H // 2, min(W, H)
        else:
            fx, fy, fw, fh = face
            cx = fx + fw // 2
            cy = int(fy + fh // 2 + HEADROOM * fh)
            side = int(fh * FACE_RATIO)
            print(f"  face=({fx},{fy},{fw}x{fh}) via {_WINNING_CASCADE}")

    x0, y0, side = square_around(cx, cy, side, W, H)
    print(f"  crop rect=({x0},{y0},{side}x{side}) from {W}x{H}")
    crop = rgb[y0:y0 + side, x0:x0 + side]
    Image.fromarray(crop).convert("RGB").resize(
        (TARGET, TARGET), Image.LANCZOS
    ).save(out, "JPEG", quality=JPEG_QUALITY, optimize=True)
    print(f"  wrote {out}  ({TARGET}x{TARGET})")


def parse_anchor(s: str):
    if not s:
        return None
    cx, cy, side = (int(v) for v in s.split(","))
    return (cx, cy, side)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--default", required=True, help="default (resting) source image path")
    ap.add_argument("--hover", required=True, help="hover source image path")
    ap.add_argument("--out", default="assets/profile", help="output directory")
    ap.add_argument("--default-center", default=None, help="override default crop: cx,cy,side (source px)")
    ap.add_argument("--hover-center", default=None, help="override hover crop: cx,cy,side (source px)")
    a = ap.parse_args()

    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    print("default:")
    build(a.default, out_dir / "zhiyuan-xiao.jpg", parse_anchor(a.default_center))
    print("hover:")
    build(a.hover, out_dir / "zhiyuan-xiao-hover.jpg", parse_anchor(a.hover_center))
    print("done")


if __name__ == "__main__":
    main()