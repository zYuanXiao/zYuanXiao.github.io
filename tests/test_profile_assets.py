import unittest
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


DEFAULT = Path("assets/profile/zhiyuan-xiao.jpg")
HOVER = Path("assets/profile/zhiyuan-xiao-hover.jpg")


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
    if len(eyes) != 2:
        raise AssertionError(f"expected two plausible eyes in {path}, found {eyes}")
    return sorted(eyes)


class HoverAssetContractTest(unittest.TestCase):
    def test_hover_avatar_has_paper_negative_space(self):
        image = Image.open(HOVER).convert("RGB")
        self.assertEqual(image.size, (512, 512))
        pixels = np.asarray(image, dtype=np.float32)
        corners = [
            pixels[:48, :48],
            pixels[:48, -48:],
            pixels[-48:, :48],
            pixels[-48:, -48:],
        ]
        for corner in corners:
            self.assertGreater(float(corner.mean()), 225.0)
            self.assertLess(float(corner.std()), 35.0)
        center = pixels[144:368, 144:368]
        self.assertGreater(float(center.std()), 25.0)
        self.assertLess(float(center.mean()), 220.0)

    def test_hover_avatar_aligns_eye_line_with_default(self):
        default_eyes = eye_pair(DEFAULT)
        hover_eyes = eye_pair(HOVER)
        default_midpoint = np.mean(default_eyes, axis=0)
        hover_midpoint = np.mean(hover_eyes, axis=0)
        self.assertLessEqual(
            float(np.linalg.norm(default_midpoint - hover_midpoint)), 8.0
        )
        default_distance = float(np.linalg.norm(np.subtract(*default_eyes)))
        hover_distance = float(np.linalg.norm(np.subtract(*hover_eyes)))
        self.assertLessEqual(abs(default_distance - hover_distance) / default_distance, 0.1)


if __name__ == "__main__":
    unittest.main()
