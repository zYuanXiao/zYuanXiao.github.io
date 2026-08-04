# Avatar Enlargement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enlarge the home-page avatar to 176 px on desktop and 120 px on mobile while preserving the watercolor-to-original hover crossfade and the page's responsive layout.

**Architecture:** Keep the existing CSS-only two-image stack inside `.avatar`. Change only the hero gap, desktop/mobile avatar dimensions, fine-pointer hover gating, and the hover image's loading attribute in `index.html`; use an inline Python contract check before and after the change, followed by HTTP and multi-viewport browser verification.

**Tech Stack:** Static HTML5 and CSS3; Python 3 standard library for contract checks and local HTTP serving; in-app browser for responsive and interaction verification.

## Global Constraints

- Default image: `assets/profile/zhiyuan-xiao.jpg` (watercolor portrait).
- Hover image: `assets/profile/zhiyuan-xiao-hover.jpg` (original photograph).
- Desktop avatar: exactly 176 × 176 px.
- Mobile avatar at `max-width: 700px`: exactly 120 × 120 px.
- Desktop hero gap: exactly 36 px; mobile hero gap remains 22 px.
- Global `.wrap` maximum width remains 980 px.
- Avatar corner radius remains 18 px and both images retain `object-fit: cover`.
- Hover crossfade remains CSS-only and lasts 0.25 seconds.
- Hover swap is limited to `@media (hover: hover) and (pointer: fine)`.
- `prefers-reduced-motion: reduce` continues to disable the transition.
- Hover image remains decorative with `alt=""` and `aria-hidden="true"`, but must not use lazy loading.
- Do not modify image assets, build scripts, Publications, Experience, or other unrelated page sections.

## File Structure

- Modify `index.html`: owns the complete page markup and styles; this task changes only the hero/avatar CSS and the hover image tag.
- No files are created during implementation. The test-first contract is an inline Python program so the repository stays consistent with the approved one-file scope.

---

### Task 1: Enlarge and harden the responsive avatar

**Files:**
- Modify: `index.html:38-52`
- Modify: `index.html:118-122`
- Modify: `index.html:142-144`

**Interfaces:**
- Consumes: existing `.hero`, `.avatar`, `.av-default`, and `.av-hover` selectors; the two committed 512 × 512 profile images.
- Produces: a 176 px desktop avatar, a 120 px mobile avatar, fine-pointer-only hover swap, eager hover-image availability, and no changes to any external API or JavaScript interface.

- [ ] **Step 1: Run the contract check and verify the current page fails the new requirements**

From the repository root, run this PowerShell command:

```powershell
@'
from pathlib import Path
import re

html = Path("index.html").read_text(encoding="utf-8")

assert '.wrap { max-width: 980px; margin: 0 auto; padding: 0 32px; }' in html
assert "header.hero { padding: 66px 0 40px; display: flex; gap: 36px; align-items: flex-start; }" in html
assert "flex: 0 0 176px; width: 176px; height: 176px; border-radius: 18px;" in html
assert "object-fit: cover; display: block; transition: opacity .25s ease;" in html
assert "@media (hover: hover) and (pointer: fine)" in html
assert ".avatar:hover .av-hover { opacity: 1; }" in html
assert ".avatar:hover .av-default { opacity: 0; }" in html
assert ".avatar img { transition: none; }" in html
assert ".avatar { width: 120px; height: 120px; flex-basis: 120px; }" in html

default_tag = re.search(r'<img class="av-default"[^>]*>', html)
hover_tag = re.search(r'<img class="av-hover"[^>]*>', html)
assert default_tag is not None
assert hover_tag is not None
assert default_tag.start() < hover_tag.start()
assert 'src="assets/profile/zhiyuan-xiao.jpg"' in default_tag.group(0)
assert 'alt="Portrait of Zhiyuan Xiao"' in default_tag.group(0)
assert 'width="512"' in default_tag.group(0) and 'height="512"' in default_tag.group(0)
assert 'src="assets/profile/zhiyuan-xiao-hover.jpg"' in hover_tag.group(0)
assert 'alt=""' in hover_tag.group(0)
assert 'aria-hidden="true"' in hover_tag.group(0)
assert 'width="512"' in hover_tag.group(0) and 'height="512"' in hover_tag.group(0)
assert "loading=" not in hover_tag.group(0)

print("avatar contract passed")
'@ | python -
```

Expected: FAIL on the hero-gap assertion because the current desktop hero gap is 42 px. This establishes that the check detects the unimplemented design.

- [ ] **Step 2: Apply the minimal CSS and HTML changes**

In `index.html`, change the desktop hero and avatar rules to:

```css
header.hero { padding: 66px 0 40px; display: flex; gap: 36px; align-items: flex-start; }
.avatar {
  position: relative; flex: 0 0 176px; width: 176px; height: 176px; border-radius: 18px;
  overflow: hidden; background: var(--tag-bg);
}
.avatar img {
  position: absolute; inset: 0; width: 100%; height: 100%;
  object-fit: cover; display: block; transition: opacity .25s ease;
}
.avatar .av-hover { opacity: 0; }
@media (hover: hover) and (pointer: fine) {
  .avatar:hover .av-hover { opacity: 1; }
  .avatar:hover .av-default { opacity: 0; }
}
@media (prefers-reduced-motion: reduce) {
  .avatar img { transition: none; }
}
```

In the existing `@media (max-width: 700px)` block, replace only the avatar rule with:

```css
.avatar { width: 120px; height: 120px; flex-basis: 120px; }
```

Keep the mobile hero rule unchanged so it remains:

```css
header.hero { flex-direction: column; gap: 22px; padding-top: 44px; }
```

Replace the hover image tag with the same attributes minus `loading="lazy"`:

```html
<img class="av-hover" src="assets/profile/zhiyuan-xiao-hover.jpg" alt="" aria-hidden="true" width="512" height="512">
```

Do not edit either image file or any other page section.

- [ ] **Step 3: Re-run the contract check and verify it passes**

Run the exact PowerShell/Python contract command from Step 1 again.

Expected:

```text
avatar contract passed
```

The command must exit with status 0.

- [ ] **Step 4: Verify file scope and whitespace**

Run:

```powershell
git diff --check
git status --short
git diff --stat
```

Expected:

- `git diff --check` prints nothing and exits 0.
- `git status --short` lists only `index.html` as modified.
- `git diff --stat` reports changes only in `index.html`.

- [ ] **Step 5: Serve the page and verify both avatar assets over HTTP**

Start the local server from the repository root:

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

While it is running, check the page and assets from another terminal:

```powershell
curl.exe -sS -o NUL -w "page=%{http_code}`n" http://127.0.0.1:8765/
curl.exe -sS -o NUL -w "default=%{http_code}`n" http://127.0.0.1:8765/assets/profile/zhiyuan-xiao.jpg
curl.exe -sS -o NUL -w "hover=%{http_code}`n" http://127.0.0.1:8765/assets/profile/zhiyuan-xiao-hover.jpg
```

Expected:

```text
page=200
default=200
hover=200
```

- [ ] **Step 6: Verify desktop layout and hover behavior in the browser**

Open `http://127.0.0.1:8765/` in the in-app browser and inspect at a 1280 px-wide viewport.

Run a DOM geometry check equivalent to:

```javascript
(() => {
  const avatar = document.querySelector(".avatar");
  const hero = document.querySelector("header.hero");
  const rect = avatar.getBoundingClientRect();
  const style = getComputedStyle(hero);
  return {
    avatarWidth: rect.width,
    avatarHeight: rect.height,
    heroGap: style.columnGap,
    horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth
  };
})()
```

Expected: `avatarWidth` and `avatarHeight` are `176`, `heroGap` is `36px`, and `horizontalOverflow` is `false`.

Move the pointer into the avatar and confirm the original photograph becomes visible after the 0.25-second crossfade. Move the pointer outside and confirm the watercolor portrait returns. Enable reduced motion and confirm the same swap occurs without an opacity animation.

- [ ] **Step 7: Verify breakpoint and phone layouts**

Repeat the geometry/overflow check at these viewport widths:

- 701 px: avatar remains 176 × 176 px; hero remains a row; no overlap or horizontal overflow.
- 700 px: avatar is 120 × 120 px; hero becomes a column; computed gap is 22 px; no horizontal overflow.
- 390 px: avatar remains 120 × 120 px above the text; biography, topic tags, and social links wrap naturally; no horizontal overflow.

At the touch-oriented viewport, verify the resting watercolor portrait remains visible and the page does not enter a sticky hover state.

- [ ] **Step 8: Stop the local server and commit the implementation**

Stop the HTTP server with `Ctrl+C`, then run:

```powershell
git add index.html
git commit -m "feat: enlarge responsive profile avatar"
```

Expected: one commit containing only `index.html`.

## Self-Review

- Spec coverage: Task 1 covers the exact desktop/mobile sizes, hero gap, unchanged container and rounding, default/hover ordering, fine-pointer hover gating, reduced-motion behavior, eager hover image, accessibility attributes, asset checks, responsive layout checks, and one-file scope.
- Placeholder scan: all commands, selectors, sizes, expected results, viewport widths, and commit messages are explicit.
- Naming consistency: `.avatar`, `.av-default`, `.av-hover`, both asset paths, the 700 px breakpoint, and every dimension match the approved design document.
