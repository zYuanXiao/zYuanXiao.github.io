import unittest
from pathlib import Path

import numpy as np
from PIL import Image


HOVER = Path("assets/profile/zhiyuan-xiao-hover.jpg")


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


if __name__ == "__main__":
    unittest.main()
