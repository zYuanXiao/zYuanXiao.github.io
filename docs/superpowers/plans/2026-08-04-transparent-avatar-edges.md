# Transparent Avatar Edges Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the visible white exterior of both profile portraits with transparent alpha while preserving the original people, internal light areas, natural paper edges, hover behavior, and responsive layout.

**Architecture:** Add one focused Pillow/NumPy conversion utility that computes a near-white candidate mask, retains only candidates connected to the image border, validates the result, feathers the retained edge, and writes an RGBA PNG atomically. Keep the existing JPEGs as immutable source inputs, add contract tests for the generated PNGs, then point the two existing HTML image layers at the PNG outputs.

**Tech Stack:** Python 3, Pillow, NumPy, `unittest`, static HTML/CSS, in-app browser verification.

## Global Constraints

- Only near-white pixels connected to a source-image border may become transparent.
- Preserve disconnected internal pale regions, including window highlights, glasses reflections, skin highlights, and pale watercolor areas.
- Preserve the original 512×512 dimensions, composition, people, crop, and visible paper-edge shape.
- Use a 1–2px alpha feather and lossless RGBA PNG output.
- Keep `assets/profile/zhiyuan-xiao.jpg` and `assets/profile/zhiyuan-xiao-hover.jpg` unchanged as reproducible inputs.
- Keep the existing 176px desktop and 120px mobile avatar sizes, fine-pointer hover rule, reduced-motion rule, and accessible alt-text behavior.
- Do not change biography or CV content.

---

## File Structure

- Create `tools/make_avatar_transparent.py`: deterministic border sampling, edge-connected flood fill, validation, feathering, and atomic PNG output.
- Create `tests/test_transparent_avatar_edges.py`: synthetic algorithm tests plus real generated-asset contracts.
- Create `assets/profile/zhiyuan-xiao.png`: generated transparent default portrait.
- Create `assets/profile/zhiyuan-xiao-hover.png`: generated transparent hover portrait.
- Modify `index.html`: reference the PNG assets and make the avatar container background transparent.
- Modify `tests/test_profile_assets.py`: run existing eye alignment checks against the PNG assets while ignoring alpha for face detection.

---

### Task 1: Implement and Test the Edge-Connected Transparency Utility

**Files:**
- Create: `tools/make_avatar_transparent.py`
- Create: `tests/test_transparent_avatar_edges.py`

**Interfaces:**
- Consumes: `PIL.Image.Image` converted to RGB.
- Produces: `build_rgba(source: Path) -> Image.Image`, returning a validated 512×512 RGBA image.
- Produces: CLI `python tools/make_avatar_transparent.py --input SOURCE --output DESTINATION`.

- [ ] **Step 1: Write failing synthetic tests for exterior-only removal**

Create a 64×64 synthetic RGB image with an off-white exterior, a dark irregular frame, and a disconnected white interior highlight. Assert that `build_rgba_from_rgb()` makes the four corners transparent, preserves the center highlight, and leaves the dark subject opaque:

```python
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
```

- [ ] **Step 2: Run the focused tests and confirm RED**

Run:

```powershell
python -B -m unittest -v tests.test_transparent_avatar_edges.EdgeConnectedMaskTest
```

Expected: import failure because `tools.make_avatar_transparent` does not exist.

- [ ] **Step 3: Implement border sampling and edge-connected flood fill**

Implement these exact public helpers in `tools/make_avatar_transparent.py`:

```python
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
```

Implement `build_rgba_from_rgb(rgb)` to validate a 512×512 production image or any square synthetic test image, first reject more than 2% exterior-mask coverage in the central 40% rectangle with a `ValueError` containing `protected central portrait`, then reject total exterior coverage outside `0.01..0.40`, blur the binary exterior mask with `ImageFilter.GaussianBlur(1.0)`, calculate `alpha = 255 - blurred_exterior`, and return `Image.fromarray(np.dstack((rgb, alpha)), "RGBA")`.

Implement `build_rgba(source)` to load RGB without changing the source. Implement the CLI so it validates the complete image before saving to a sibling temporary file and atomically replaces only the requested output with `Path.replace()`.

- [ ] **Step 4: Run the focused tests and confirm GREEN**

Run:

```powershell
python -B -m unittest -v tests.test_transparent_avatar_edges.EdgeConnectedMaskTest
```

Expected: 2 tests pass.

- [ ] **Step 5: Check formatting and commit Task 1**

Run:

```powershell
python -m py_compile tools/make_avatar_transparent.py tests/test_transparent_avatar_edges.py
git diff --check
git add tools/make_avatar_transparent.py tests/test_transparent_avatar_edges.py
git commit -m "feat: add avatar transparency mask"
```

Expected: compilation succeeds, `git diff --check` is empty, and the commit succeeds.

---

### Task 2: Generate and Validate the Transparent Portrait Assets

**Files:**
- Create: `assets/profile/zhiyuan-xiao.png`
- Create: `assets/profile/zhiyuan-xiao-hover.png`
- Modify: `tests/test_transparent_avatar_edges.py`
- Modify: `tests/test_profile_assets.py`

**Interfaces:**
- Consumes: the two unchanged source JPEGs and Task 1 CLI.
- Produces: two validated 512×512 RGBA PNG assets used by Task 3.

- [ ] **Step 1: Add failing real-asset contract tests**

Add tests that open both expected PNG paths and assert:

```python
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
```

Update `DEFAULT` and `HOVER` in `tests/test_profile_assets.py` to the PNG paths. Keep `eye_pair()` converting the opened image to RGB so alpha does not affect the existing OpenCV alignment contract.

- [ ] **Step 2: Run the asset tests and confirm RED**

Run:

```powershell
python -B -m unittest -v tests.test_transparent_avatar_edges tests.test_profile_assets
```

Expected: failure because the PNG outputs do not exist.

- [ ] **Step 3: Generate both PNG assets from the unchanged JPEG sources**

Run:

```powershell
python tools/make_avatar_transparent.py --input assets/profile/zhiyuan-xiao.jpg --output assets/profile/zhiyuan-xiao.png
python tools/make_avatar_transparent.py --input assets/profile/zhiyuan-xiao-hover.jpg --output assets/profile/zhiyuan-xiao-hover.png
```

Expected: each command reports a 512×512 RGBA output and a transparent fraction within `0.01..0.40`.

- [ ] **Step 4: Run all image contract tests and visually inspect both PNGs**

Run:

```powershell
python -B -m unittest -v tests.test_transparent_avatar_edges tests.test_profile_assets
```

Then inspect both PNGs at original resolution against a checkerboard or contrasting background. Confirm that faces, clothing, windows, and internal pale regions are unchanged; only the connected exterior is transparent; and the feathered edge has no white or dark halo.

Expected: all focused tests pass and both assets retain natural irregular edges.

- [ ] **Step 5: Verify immutable input hashes and commit Task 2**

Record the pre-existing JPEG SHA-256 values and compare them to Git `fabfdaf`:

```powershell
git hash-object assets/profile/zhiyuan-xiao.jpg assets/profile/zhiyuan-xiao-hover.jpg
git rev-parse fabfdaf:assets/profile/zhiyuan-xiao.jpg
git rev-parse fabfdaf:assets/profile/zhiyuan-xiao-hover.jpg
git diff --check
git add assets/profile/zhiyuan-xiao.png assets/profile/zhiyuan-xiao-hover.png tests/test_transparent_avatar_edges.py tests/test_profile_assets.py
git commit -m "feat: add transparent profile portraits"
```

Expected: each working-tree JPEG blob matches its `fabfdaf` blob, `git diff --check` is empty, and the commit succeeds.

---

### Task 3: Integrate PNG Assets and Verify the Website

**Files:**
- Modify: `index.html:39-50`
- Modify: `index.html:144-146`
- Modify: `tests/test_transparent_avatar_edges.py`

**Interfaces:**
- Consumes: the two RGBA PNG assets from Task 2.
- Produces: the final default/hover avatar interaction with transparent exterior pixels.

- [ ] **Step 1: Add failing HTML integration assertions**

Add a test that reads `index.html` and asserts:

```python
html = Path("index.html").read_text(encoding="utf-8")
self.assertIn('src="assets/profile/zhiyuan-xiao.png"', html)
self.assertIn('src="assets/profile/zhiyuan-xiao-hover.png"', html)
self.assertIn("background: transparent", html)
self.assertIn("@media (hover: hover) and (pointer: fine)", html)
self.assertIn("@media (prefers-reduced-motion: reduce)", html)
self.assertNotIn('src="assets/profile/zhiyuan-xiao.jpg"', html)
self.assertNotIn('src="assets/profile/zhiyuan-xiao-hover.jpg"', html)
```

- [ ] **Step 2: Run the HTML integration test and confirm RED**

Run:

```powershell
python -B -m unittest -v tests.test_transparent_avatar_edges
```

Expected: failure because `index.html` still references the JPEG assets and uses the tag-colored background.

- [ ] **Step 3: Update the avatar container and image sources**

In `index.html`, change `.avatar` from `background: var(--tag-bg)` to `background: transparent`. Change the default and hover `<img>` sources to `assets/profile/zhiyuan-xiao.png` and `assets/profile/zhiyuan-xiao-hover.png`. Preserve the existing classes, dimensions, alt attributes, `aria-hidden`, hover media query, and reduced-motion media query byte-for-byte otherwise.

- [ ] **Step 4: Run the full automated suite**

Run:

```powershell
python -B -m unittest discover -s tests -v
git diff --check
```

Expected: all tests pass and `git diff --check` reports nothing.

- [ ] **Step 5: Verify desktop and mobile behavior in the local browser**

Serve the worktree and inspect `http://127.0.0.1:8765/`:

- desktop: avatar is 176×176, resting watercolor is visible, transparent corners show the page background, fine-pointer hover reveals the transparent photo, and there is no horizontal overflow;
- mobile at 390px: avatar is 120×120 above the text, transparent corners render correctly, the hover layer remains hidden without fine hover, and there is no horizontal overflow;
- confirm biography and CV link/content are unchanged.

- [ ] **Step 6: Commit Task 3**

Run:

```powershell
git add index.html tests/test_transparent_avatar_edges.py
git commit -m "feat: use transparent avatar assets"
git status --short
```

Expected: commit succeeds and the worktree is clean.

---

### Task 4: Final Review and Completion Verification

**Files:**
- Review only: all files changed since `104fcf4`.

**Interfaces:**
- Consumes: completed Tasks 1–3.
- Produces: review verdict and fresh completion evidence.

- [ ] **Step 1: Request a whole-change code review**

Review `git diff 104fcf4..HEAD` against `docs/superpowers/specs/2026-08-04-transparent-avatar-edges-design.md`. Treat any face/composition change, loss of internal highlights, excessive transparency, broken hover behavior, or responsive regression as Important or Critical.

- [ ] **Step 2: Resolve all Critical and Important findings**

For each valid finding, add or update a regression test first, verify it fails, make the smallest focused correction, verify it passes, and commit the correction. Re-run a scoped review after each correction round.

- [ ] **Step 3: Run fresh completion verification**

Run:

```powershell
python -B -m unittest discover -s tests -v
git diff --check
git status --short
```

Recheck the local HTTP routes for `/`, both PNGs, and `/Zhiyuan_Xiao_CV.pdf`; all must return HTTP 200. Confirm both PNGs are RGBA, all corners are transparent, central portrait regions are opaque, and the original JPEG Git blobs remain unchanged.

Expected: zero test failures, no diff errors, clean Git status, four HTTP 200 responses, and all asset invariants satisfied.
