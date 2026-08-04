# Hover Portrait Paper Mask Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the broken hover portrait with an identity-preserving, watercolor-aligned photograph whose near-full-frame edge ends naturally on paper, prevent the crop script from silently repeating the error, and remove the requested biography phrase.

**Architecture:** Keep the existing two-image CSS crossfade and asset paths unchanged. Treat the hover JPEG as a curated visual asset created from the two supplied references, while adding a pure plausibility check to the existing crop builder so an implausible automatic hover-face detection fails closed. Make the biography edit as an isolated HTML copy change.

**Tech Stack:** Static HTML/CSS, Python 3.13, Pillow 12, OpenCV 4.13, standard-library `unittest`, ImageGen, FFmpeg 8, local HTTP/browser visual verification.

## Global Constraints

- Preserve `assets/profile/zhiyuan-xiao.jpg` without modification.
- Keep `assets/profile/zhiyuan-xiao-hover.jpg` as an opaque 512 × 512 JPEG.
- Keep the existing 176 px desktop and 120 px mobile avatar sizes, asset paths, crossfade, and page layout.
- Preserve the real face, glasses, hairstyle, expression, clothing, and identity from the source photograph.
- Extend the photograph almost to all four edges, leaving only a naturally varied 0–10 px warm-white paper reveal like the watercolor reference; do not use transparency, a central oval, a perfect hard circle, a wide white ring, or watercolor stylization of the person.
- The final user-selected image at `C:/Users/yuanx/AppData/Local/Temp/codex-clipboard-ed4dfbe2-b107-4605-85a0-8682c3f08aba.png` is authoritative and supersedes the numeric edge-width guidance where they differ. Preserve its composition exactly; only square downsampling and JPEG encoding are allowed.
- Preserve the exact user-selected composition with an eye-midpoint regression bound of 16 px and an inter-eye-scale bound of 22 percent; these supersede the earlier 8 px / 10 percent targets that would require recropping the selected bitmap.
- Remove only `3D generation and reconstruction` and the resulting unnecessary list punctuation from the biography.
- Use `apply_patch` for repository text edits. Do not use Python to transform or paint the image. The final user-selected bitmap requires only FFmpeg downsampling and JPEG encoding; do not regenerate it with ImageGen.

---

### Task 1: Biography Copy Cleanup

**Files:**
- Modify: `index.html:152-157`

**Interfaces:**
- Consumes: Existing biography paragraph in `index.html`.
- Produces: The exact sentence `My research focuses on generative models for computer vision, including image/video generation and vision-language models.`

- [ ] **Step 1: Run the failing copy assertion**

Run:

```powershell
python -c "import re; from pathlib import Path; s=Path('index.html').read_text(encoding='utf-8'); assert not re.search(r'3D generation\s+and reconstruction', s)"
```

Expected: FAIL with `AssertionError` because the phrase is currently split across lines in the HTML source.

- [ ] **Step 2: Apply the minimal biography edit**

Replace only this fragment:

```html
          group. My research focuses on generative models for computer vision, including 3D generation
          and reconstruction, image/video generation, and vision-language models. I am also interested
```

with:

```html
          group. My research focuses on generative models for computer vision, including image/video
          generation and vision-language models. I am also interested
```

- [ ] **Step 3: Verify the copy and surrounding paragraph**

Run:

```powershell
python -c "import re; from pathlib import Path; s=Path('index.html').read_text(encoding='utf-8'); assert not re.search(r'3D generation\s+and reconstruction', s); assert 'including image/video\n          generation and vision-language models.' in s"
```

Expected: PASS with no output.

Run:

```powershell
git diff --check -- index.html
```

Expected: PASS with no whitespace errors.

- [ ] **Step 4: Commit the biography change**

```powershell
git add index.html
git commit -m "content: remove 3D reconstruction topic"
```

---

### Task 2: Fail-Closed Hover Face Detection

**Files:**
- Create: `tests/test_build_profile.py`
- Modify: `tools/build_profile.py:44-63`
- Modify: `tools/build_profile.py:105-130`

**Interfaces:**
- Consumes: A face tuple `(fx, fy, fw, fh, cascade_name)`, source width, and source height.
- Produces: `face_is_plausible(face: tuple, width: int, height: int) -> bool`.
- Produces: A clear `SystemExit` for an absent or implausible automatic hover detection, instructing the caller to pass `--hover-center cx,cy,side`.

- [ ] **Step 1: Write unit tests for plausible and implausible detections**

Create `tests/test_build_profile.py`:

```python
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
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```powershell
python -m unittest discover -s tests -p "test_build_profile.py" -v
```

Expected: FAIL with `ImportError` because `face_is_plausible` does not exist.

- [ ] **Step 3: Add the pure plausibility check**

Add after `detect_face` in `tools/build_profile.py`:

```python
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
```

- [ ] **Step 4: Make implausible hover detections fail closed**

In the automatic-detection branch of `main`, immediately after `face = detect_face(gray)`, add:

```python
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
```

Keep the existing center-square fallback for the default image. The new hover error must occur before that fallback.

- [ ] **Step 5: Run unit and source-photo regression checks**

Run:

```powershell
python -m unittest discover -s tests -p "test_build_profile.py" -v
```

Expected: 3 tests PASS.

Run the builder without a manual hover anchor:

```powershell
python tools/build_profile.py --default "C:/Users/yuanx/Downloads/Flux2_Klein_9b_kv_00058_.png" --hover "C:/Users/yuanx/Downloads/Weixin Image_20260803183116_2217_7.jpg" --out "$env:TEMP/profile-build-guard-check"
```

Expected: non-zero exit and the message `hover face detection missing or implausible; pass --hover-center cx,cy,side`. Confirm it does not report writing `zhiyuan-xiao-hover.jpg`.

- [ ] **Step 6: Commit the guard and tests**

```powershell
git add tools/build_profile.py tests/test_build_profile.py
git commit -m "fix: reject implausible hover face crops"
```

---

### Task 3: Organic Paper-Masked Hover Portrait

**Files:**
- Create: `tests/test_profile_assets.py`
- Modify: `assets/profile/zhiyuan-xiao-hover.jpg`
- Preserve unchanged: `assets/profile/zhiyuan-xiao.jpg`

**Interfaces:**
- Consumes composition reference: `C:/Users/yuanx/Downloads/Flux2_Klein_9b_kv_00058_.png`.
- Consumes identity/photo source: `C:/Users/yuanx/Downloads/Weixin Image_20260803183116_2217_7.jpg`.
- Produces: an opaque 512 × 512 JPEG at `assets/profile/zhiyuan-xiao-hover.jpg` with near-full photographic coverage, small paper corners, and a naturally varied 0–10 px watercolor-like edge.

- [ ] **Step 1: Record the default asset hash**

Run:

```powershell
Get-FileHash assets/profile/zhiyuan-xiao.jpg -Algorithm SHA256
```

Expected: record the printed hash for the preservation check in Step 7.

- [ ] **Step 2: Write the failing asset-composition test**

Create `tests/test_profile_assets.py`:

```python
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the asset test and verify it fails on the sleeve crop**

Run:

```powershell
python -m unittest discover -s tests -p "test_profile_assets.py" -v
```

Expected: FAIL because at least one corner of the current full-bleed wood/sleeve crop is not bright paper.

- [ ] **Step 4: Inspect the user-selected final composition**

Inspect `C:/Users/yuanx/AppData/Local/Temp/codex-clipboard-ed4dfbe2-b107-4605-85a0-8682c3f08aba.png` at original detail. Verify that it is a square RGB image, retains the authentic face, glasses, hair, expression, and navy shirt, uses the approved natural watercolor-like paper edge, and contains no text or transparency.

Do not call ImageGen for this step. The user's selected bitmap is the final art direction and must not be regenerated or modified beyond size/format conversion.

- [ ] **Step 5: Install the approved candidate at the existing path**

Use the selected PNG as the visual source for `assets/profile/zhiyuan-xiao-hover.jpg`. Do not change the filename or the `<img>` element in `index.html`. Perform only the required square downsample and JPEG encoding with the installed FFmpeg 8 binary:

```powershell
$candidatePath = (Resolve-Path 'C:/Users/yuanx/AppData/Local/Temp/codex-clipboard-ed4dfbe2-b107-4605-85a0-8682c3f08aba.png').Path
ffmpeg -y -i $candidatePath -vf "scale=512:512:flags=lanczos" -frames:v 1 -q:v 2 assets/profile/zhiyuan-xiao-hover.jpg
```

The selected candidate is already square. Do not crop, mask, repaint, regenerate, or otherwise redesign it, and do not use Python to edit or resize it.

- [ ] **Step 6: Run automated asset checks**

Run:

```powershell
python -m unittest discover -s tests -p "test_profile_assets.py" -v
```

Expected: PASS.

Run:

```powershell
python -c "from PIL import Image; p='assets/profile/zhiyuan-xiao-hover.jpg'; im=Image.open(p); assert im.size==(512,512); assert im.mode=='RGB'; assert im.format=='JPEG'; print(p, im.size, im.mode, im.format)"
```

Expected: `assets/profile/zhiyuan-xiao-hover.jpg (512, 512) RGB JPEG`.

- [ ] **Step 7: Verify visual alignment and preserve the watercolor asset**

Use `view_image` at original detail for both avatar assets and compare them side by side. Then use the local browser crossfade to inspect the midpoint perceptually. For the exact user-selected bitmap, accept an eye-midpoint difference no greater than 16 px and an inter-eye-scale difference no greater than 22 percent; confirm the conversion itself introduces no further crop or landmark drift.

Run `Get-FileHash assets/profile/zhiyuan-xiao.jpg -Algorithm SHA256` again and confirm it exactly matches the hash recorded in Step 1.

- [ ] **Step 8: Commit the asset and its contract test**

```powershell
git add assets/profile/zhiyuan-xiao-hover.jpg tests/test_profile_assets.py
git commit -m "feat: add paper-masked hover portrait"
```

---

### Task 4: Browser and Full Regression Verification

**Files:**
- Verify only: `index.html`
- Verify only: `assets/profile/zhiyuan-xiao.jpg`
- Verify only: `assets/profile/zhiyuan-xiao-hover.jpg`
- Verify only: `tools/build_profile.py`
- Verify only: `tests/test_build_profile.py`
- Verify only: `tests/test_profile_assets.py`

**Interfaces:**
- Consumes: The completed copy, crop guard, and hover asset from Tasks 1–3.
- Produces: Evidence that the page, interaction, assets, and regression tests satisfy the approved design.

- [ ] **Step 1: Run the complete automated suite**

Run:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
python -c "import re; from pathlib import Path; s=Path('index.html').read_text(encoding='utf-8'); assert not re.search(r'3D generation\s+and reconstruction', s)"
git diff --check
git status --short
```

Expected: all tests PASS, the copy assertion passes, no whitespace errors appear, and the worktree is clean.

- [ ] **Step 2: Verify assets through local HTTP**

With the site served from the worktree at `http://127.0.0.1:8765/`, run:

```powershell
$urls = @(
  'http://127.0.0.1:8765/',
  'http://127.0.0.1:8765/assets/profile/zhiyuan-xiao.jpg',
  'http://127.0.0.1:8765/assets/profile/zhiyuan-xiao-hover.jpg'
)
$urls | ForEach-Object { $r = Invoke-WebRequest -UseBasicParsing $_; "{0} {1}" -f $r.StatusCode, $_ }
```

Expected: HTTP 200 for all three URLs.

- [ ] **Step 3: Verify desktop interaction**

Read and use the `browser:control-in-app-browser` skill. Open `http://127.0.0.1:8765/` at a desktop viewport at least 980 px wide and confirm:

- watercolor portrait appears at rest;
- the avatar is 176 × 176 px;
- hover crossfades to the near-full-frame photograph with a natural 0–10 px paper edge;
- pointer exit restores the watercolor portrait;
- biography no longer mentions 3D generation or reconstruction;
- name, biography, and following sections do not overlap and there is no horizontal scrollbar.

- [ ] **Step 4: Verify mobile and reduced-motion states**

At 390 px width, confirm the avatar is 120 × 120 px, remains above the text, and no horizontal scrollbar appears. Emulate a touch-oriented pointer and confirm the watercolor remains the stable resting image. Enable reduced motion on a fine-pointer viewport and confirm the image swap occurs without an opacity animation.

- [ ] **Step 5: Final branch audit**

Run:

```powershell
git log --oneline -8
git status --short
```

Expected: the biography, crop-guard, and paper-mask commits are present and the worktree is clean.
