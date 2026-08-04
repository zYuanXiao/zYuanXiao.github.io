#!/usr/bin/env python3
"""tools/build_profile.py
Build two 512x512 square profile avatars for the home page:
  zhiyuan-xiao.jpg        default (resting)
  zhiyuan-xiao-hover.jpg  hover

Both photos are cropped to a square centred above a detected face (OpenCV
multi-cascade Haar detector) using the SAME face->square ratio for both.
The ratio is shared across all images (min of each image's achievable ratio,
capped by FACE_RATIO) so the person keeps a roughly identical scale/proportion
across the two photos — a hover-swap should not visibly zoom.

If detection fails for the default image the script falls back to a
centre-square crop and prints a warning. Hover-image detection fails closed:
pass an explicit --hover-center (cx,cy,side in source pixels); use
--default-center to override the default crop as well.

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

TARGET = 512            # output square edge (matches existing avatar source)
FACE_RATIO = 3.6        # preferred square side / face_height (capped per-image below)
HEADROOM = -0.45         # shift crop centre up by 0.45*face_h (headroom above head)
JPEG_QUALITY = 88

_CASCADE_FILES = [
    "haarcascade_frontalface_alt2.xml",
    "haarcascade_frontalface_default.xml",
    "haarcascade_profileface.xml",
]


def detect_face(gray: np.ndarray):
    """Largest face found across multiple Haar cascades, or None.
    Returns (fx, fy, fw, fh, cascade_name) with plain python ints."""
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
            x, y, w, h = int(f[0]), int(f[1]), int(f[2]), int(f[3])
            if best is None or w * h > best[2] * best[3]:
                best = (x, y, w, h)
                best_name = name
    if best is None:
        return None
    return (best[0], best[1], best[2], best[3], best_name)


def face_is_plausible(face, width: int, height: int) -> bool:
    """Reject detections too small or too close to portrait-frame edges."""
    fx, fy, fw, fh, _ = face
    center_x = (fx + fw / 2) / width
    center_y = (fy + fh / 2) / height
    relative_height = fh / min(width, height)
    return (
        0.18 <= center_x <= 0.82
        and 0.08 <= center_y <= 0.68
        and relative_height >= 0.04
    )


def square_around(cx: int, cy: int, side: int, W: int, H: int):
    side = min(side, min(W, H))
    half = side // 2
    x0 = min(max(cx - half, 0), W - side)
    y0 = min(max(cy - half, 0), H - side)
    return x0, y0, side


def load_rgb(src: str):
    try:
        return np.array(Image.open(src).convert("RGB"))
    except Exception as e:
        raise SystemExit(f"cannot read image {src}: {e}")


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

    targets = [
        ("default", a.default, out_dir / "zhiyuan-xiao.jpg", parse_anchor(a.default_center)),
        ("hover",   a.hover,   out_dir / "zhiyuan-xiao-hover.jpg", parse_anchor(a.hover_center)),
    ]

    # Pass 1: load, detect faces, compute per-image crop centre + max achievable ratio.
    info = []
    for which, src, out, anchor in targets:
        rgb = load_rgb(src)
        H, W = rgb.shape[:2]
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        if anchor is not None:
            cx, cy, side = anchor
            fh = None
            cap = float("inf")
            print(f"  [{which}] {W}x{H}; manual center=({cx},{cy},side={side})")
        else:
            face = detect_face(gray)
            if face is not None and not face_is_plausible(face, W, H):
                fx, fy, fw, fh, name = face
                print(
                    f"  [{which}] [warn] implausible face=({fx},{fy},{fw}x{fh}) "
                    f"via {name}",
                    file=sys.stderr,
                )
                face = None
            if face is None and which == "hover":
                raise SystemExit(
                    "hover face detection missing or implausible; "
                    "pass --hover-center cx,cy,side"
                )
            if face is None:
                print(f"  [{which}] {W}x{H}; [warn] no face -> centre-square crop "
                      f"(override with --{which}-center cx,cy,side)", file=sys.stderr)
                cx, cy, side = W // 2, H // 2, min(W, H)
                fh = None
                cap = float("inf")
            else:
                fx, fy, fw, fh, name = face
                cx = int(fx + fw / 2)
                cy = int(fy + fh / 2 + HEADROOM * fh)
                cap = min(W, H) / fh   # largest ratio before square_around would clamp
                print(f"  [{which}] {W}x{H}; face=({fx},{fy},{fw}x{fh}) via {name}")
        info.append((which, rgb, W, H, cx, cy, fh, cap))

    # Shared ratio: the most we can use across EVERY face-detected image,
    # capped by the preferred FACE_RATIO. Keeps person scale consistent.
    caps = [c for *_, fh, c in info if fh is not None]
    shared = FACE_RATIO if not caps else min([FACE_RATIO] + caps)
    print(f"  shared face->square ratio: {shared:.3f}")

    # Pass 2: crop + write using the shared ratio.
    for (which, rgb, W, H, cx, cy, fh, cap), (_, _, out, anchor) in zip(info, targets):
        if anchor is not None:
            _, _, side = anchor
        elif fh is not None:
            side = int(fh * shared)
        else:
            side = min(W, H)
        x0, y0, side = square_around(cx, cy, side, W, H)
        ratio_str = f"ratio={side / fh:.3f}" if fh else "ratio=n/a"
        print(f"  [{which}] crop=({x0},{y0},{side}x{side}) {ratio_str}")
        crop = rgb[y0:y0 + side, x0:x0 + side]
        Image.fromarray(crop).convert("RGB").resize(
            (TARGET, TARGET), Image.LANCZOS
        ).save(out, "JPEG", quality=JPEG_QUALITY, optimize=True)
        print(f"  [{which}] wrote {out} ({TARGET}x{TARGET})")
    print("done")


if __name__ == "__main__":
    main()
