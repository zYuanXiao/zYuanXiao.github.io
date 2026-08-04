import unittest

import numpy as np

from tools.make_avatar_transparent import build_rgba_from_rgb


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
