import unittest
from itertools import combinations
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


DEFAULT = Path("assets/profile/zhiyuan-xiao.png")
HOVER = Path("assets/profile/zhiyuan-xiao-hover.png")


def eye_pair(path):
    pixels = np.asarray(Image.open(path).convert("RGB"))
    gray = cv2.cvtColor(pixels, cv2.COLOR_RGB2GRAY)
    detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_eye_tree_eyeglasses.xml"
    )
    candidates = detector.detectMultiScale(
        gray, scaleFactor=1.03, minNeighbors=3, minSize=(20, 20)
    )
    eyes = []
    for x, y, width, height in candidates:
        center = (float(x + width / 2), float(y + height / 2))
        if 128 <= center[0] <= 384 and 102 <= center[1] <= 256 and width <= 60:
            eyes.append(center)
    pairs = [
        pair
        for pair in combinations(eyes, 2)
        if abs(pair[0][1] - pair[1][1]) <= 16
        and abs(pair[0][0] - pair[1][0]) >= 40
    ]
    if len(pairs) != 1:
        raise AssertionError(
            f"expected one plausible same-line eye pair in {path}, found {eyes}"
        )
    return sorted(pairs[0])


class HoverAssetContractTest(unittest.TestCase):
    def test_hover_avatar_has_paper_negative_space(self):
        image = Image.open(HOVER).convert("RGB")
        self.assertEqual(image.size, (512, 512))
        pixels = np.asarray(image, dtype=np.float32)
        corners = [
            pixels[:4, :4],
            pixels[:4, -4:],
            pixels[-4:, :4],
            pixels[-4:, -4:],
        ]
        for corner in corners:
            self.assertGreater(float(corner.mean()), 225.0)
            self.assertLess(float(corner.std()), 35.0)
        channel_spread = pixels.max(axis=2) - pixels.min(axis=2)
        paper_like = (pixels.mean(axis=2) > 225.0) & (channel_spread < 30.0)
        self.assertGreater(float((~paper_like).mean()), 0.78)
        center = pixels[144:368, 144:368]
        self.assertGreater(float(center.std()), 25.0)
        self.assertLess(float(center.mean()), 220.0)

    def test_hover_avatar_aligns_eye_line_with_default(self):
        default_eyes = eye_pair(DEFAULT)
        hover_eyes = eye_pair(HOVER)
        default_midpoint = np.mean(default_eyes, axis=0)
        hover_midpoint = np.mean(hover_eyes, axis=0)
        self.assertLessEqual(
            float(np.linalg.norm(default_midpoint - hover_midpoint)), 16.0
        )
        default_distance = float(np.linalg.norm(np.subtract(*default_eyes)))
        hover_distance = float(np.linalg.norm(np.subtract(*hover_eyes)))
        self.assertLessEqual(abs(default_distance - hover_distance) / default_distance, 0.22)


if __name__ == "__main__":
    unittest.main()
