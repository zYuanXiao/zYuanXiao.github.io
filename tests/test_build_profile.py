import unittest

from tools.build_profile import face_is_plausible


class FacePlausibilityTest(unittest.TestCase):
    def test_rejects_current_false_positive_near_lower_edge(self):
        face = (775, 2284, 183, 183, "haarcascade_frontalface_alt2.xml")
        self.assertFalse(face_is_plausible(face, width=4000, height=3000))

    def test_accepts_centered_upper_body_portrait_face(self):
        face = (1569, 994, 253, 253, "haarcascade_frontalface_default.xml")
        self.assertTrue(face_is_plausible(face, width=4000, height=3000))

    def test_rejects_tiny_detection(self):
        face = (1900, 900, 50, 50, "haarcascade_frontalface_default.xml")
        self.assertFalse(face_is_plausible(face, width=4000, height=3000))


if __name__ == "__main__":
    unittest.main()
