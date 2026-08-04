#!/usr/bin/env python3
"""Convert paper-like, edge-connected avatar backgrounds to transparency."""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def paper_candidates(rgb: np.ndarray) -> np.ndarray:
    border = np.concatenate((rgb[:8].reshape(-1, 3), rgb[-8:].reshape(-1, 3),
                             rgb[:, :8].reshape(-1, 3), rgb[:, -8:].reshape(-1, 3)))
    neutral = border[(border.mean(axis=1) >= 205) &
                     ((border.max(axis=1) - border.min(axis=1)) <= 45)]
    if len(neutral) < 32:
        raise ValueError("not enough near-white border paper to sample")
    reference = np.median(neutral.astype(np.float32), axis=0)
    pixels = rgb.astype(np.float32)
    lightness = pixels.mean(axis=2)
    chroma = pixels.max(axis=2) - pixels.min(axis=2)
    distance = np.linalg.norm(pixels - reference, axis=2)
    return (lightness >= 205) & (chroma <= 48) & (distance <= 58)


def border_connected(candidate: np.ndarray) -> np.ndarray:
    height, width = candidate.shape
    exterior = np.zeros_like(candidate, dtype=bool)
    queue = deque()
    for x in range(width):
        queue.extend(((0, x), (height - 1, x)))
    for y in range(height):
        queue.extend(((y, 0), (y, width - 1)))
    while queue:
        y, x = queue.popleft()
        if not candidate[y, x] or exterior[y, x]:
            continue
        exterior[y, x] = True
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ny, nx = y + dy, x + dx
                if 0 <= ny < height and 0 <= nx < width:
                    queue.append((ny, nx))
    return exterior


def build_rgba_from_rgb(rgb: np.ndarray) -> Image.Image:
    """Return an RGBA image after safely removing exterior paper pixels."""
    if rgb.ndim != 3 or rgb.shape[2] != 3 or rgb.shape[0] != rgb.shape[1]:
        raise ValueError("input must be a square RGB image")
    if rgb.shape[0] < 8:
        raise ValueError("input image must be at least 8 pixels square")

    exterior = border_connected(paper_candidates(rgb))
    height, width = exterior.shape
    y0, y1 = int(height * 0.3), int(height * 0.7)
    x0, x1 = int(width * 0.3), int(width * 0.7)
    if exterior[y0:y1, x0:x1].mean() > 0.02:
        raise ValueError("exterior mask reaches protected central portrait")

    coverage = exterior.mean()
    if not 0.01 <= coverage <= 0.40:
        raise ValueError("exterior mask coverage must be between 0.01 and 0.40")

    exterior_image = Image.fromarray(exterior.astype(np.uint8) * 255)
    blurred_exterior = np.asarray(exterior_image.filter(ImageFilter.GaussianBlur(1.0)))
    alpha = 255 - blurred_exterior
    return Image.fromarray(np.dstack((rgb, alpha)), "RGBA")


def build_rgba(source: Path) -> Image.Image:
    """Load a source image as RGB and return a validated 512x512 RGBA image."""
    with Image.open(source) as image:
        rgb = np.asarray(image.convert("RGB"))
    if rgb.shape[:2] != (512, 512):
        raise ValueError("production input image must be 512x512")
    return build_rgba_from_rgb(rgb)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    output = args.output
    if output.suffix.lower() != ".png":
        parser.error("--output must use a .png suffix")

    rgba = build_rgba(args.input)
    temporary = output.with_name(f".{output.stem}.tmp{output.suffix}")
    try:
        rgba.save(temporary, format="PNG")
        temporary.replace(output)
    finally:
        if temporary.exists():
            temporary.unlink()


if __name__ == "__main__":
    main()
