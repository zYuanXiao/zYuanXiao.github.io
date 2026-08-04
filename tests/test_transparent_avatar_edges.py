from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

from tools.make_avatar_transparent import build_rgba_from_rgb


DEFAULT_PNG = Path("assets/profile/zhiyuan-xiao.png")
HOVER_PNG = Path("assets/profile/zhiyuan-xiao-hover.png")


class TransparentAvatarAssetContractTest(unittest.TestCase):
    def test_portraits_are_rgba_with_transparent_exterior(self):
        for path in (DEFAULT_PNG, HOVER_PNG):
            image = Image.open(path)
            self.assertEqual(image.size, (512, 512))
            self.assertEqual(image.mode, "RGBA")
            alpha = np.asarray(image)[:, :, 3]
            self.assertTrue(np.all(alpha[:2, :2] == 0))
            self.assertTrue(np.all(alpha[:2, -2:] == 0))
            self.assertTrue(np.all(alpha[-2:, :2] == 0))
            self.assertTrue(np.all(alpha[-2:, -2:] == 0))
            transparent_fraction = float((alpha == 0).mean())
            self.assertGreater(transparent_fraction, 0.01)
            self.assertLess(transparent_fraction, 0.40)
            self.assertGreater(float((alpha[154:358, 154:358] >= 250).mean()), 0.98)


class EdgeConnectedMaskTest(unittest.TestCase):
    def test_removes_only_border_connected_paper(self):
        rgb = np.full((64, 64, 3), (246, 243, 236), dtype=np.uint8)
        rgb[6:58, 6:58] = (70, 90, 120)
        rgb[26:38, 26:38] = (250, 249, 246)
        rgba = np.asarray(build_rgba_from_rgb(rgb))
        self.assertEqual(tuple(rgba[0, 0, :3]), (246, 243, 236))
        self.assertEqual(int(rgba[0, 0, 3]), 0)
        self.assertGreaterEqual(int(rgba[32, 32, 3]), 250)
        self.assertGreaterEqual(int(rgba[18, 18, 3]), 250)

    def test_rejects_mask_that_reaches_protected_center(self):
        rgb = np.full((64, 64, 3), (70, 90, 120), dtype=np.uint8)
        rgb[:4] = (248, 247, 244)
        rgb[:36, 31:34] = (248, 247, 244)
        with self.assertRaisesRegex(ValueError, "protected central portrait"):
            build_rgba_from_rgb(rgb)

    def test_cli_rejects_non_png_output(self):
        rgb = np.full((512, 512, 3), (246, 243, 236), dtype=np.uint8)
        rgb[52:460, 52:460] = (70, 90, 120)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.png"
            output = Path(directory) / "avatar.jpg"
            Image.fromarray(rgb).save(source)
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/make_avatar_transparent.py",
                    "--input",
                    str(source),
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(".png", result.stderr)
            self.assertFalse(output.exists())
