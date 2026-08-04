# Avatar Enlargement Design

**Date:** 2026-08-04
**Status:** Approved
**Scope:** Home-page avatar sizing and hover presentation only

## Context

The home-page hero already contains two stacked square avatar images:

- `assets/profile/zhiyuan-xiao.jpg` is the default watercolor portrait.
- `assets/profile/zhiyuan-xiao-hover.jpg` is the original photograph shown on hover.

The existing CSS crossfades between them in 0.25 seconds. The current avatar is 128 × 128 px on desktop and 96 × 96 px at the `700px` mobile breakpoint. The requested change is to make the portrait more prominent without disturbing the rest of the single-page layout.

## Goals

- Display the watercolor portrait by default.
- Crossfade to the original photograph when a mouse pointer hovers over the avatar.
- Increase the desktop avatar to 176 × 176 px.
- Increase the mobile avatar to 120 × 120 px.
- Preserve readable text width, existing section alignment, and a layout without horizontal overflow.

## Non-goals

- Do not change the two source images or regenerate their 512 × 512 crops.
- Do not widen the global 980 px page container.
- Do not add JavaScript or a tap-to-toggle interaction.
- Do not refactor unrelated sections such as Publications or Experience.

## Chosen Approach

Use fixed sizes at the existing responsive breakpoint. This is preferred over a fluid `clamp()` size because it is predictable and easy to verify, and preferred over widening the page because that would affect unrelated sections.

### Desktop layout

- Set `.avatar` width, height, and flex basis to 176 px.
- Keep the hero as a horizontal flex row with top alignment.
- Reduce the hero column gap from 42 px to 36 px. Within the existing 916 px inner width, this leaves approximately 704 px for the text column.
- Preserve the existing 18 px avatar corner radius and `object-fit: cover` behavior.

### Mobile layout

- At `max-width: 700px`, retain the existing column layout.
- Set `.avatar` width, height, and flex basis to 120 px.
- Retain the existing 22 px vertical hero gap so the larger avatar does not crowd the name and biography.
- Keep the avatar above the text so narrow screens do not create a compressed two-column layout.

## Interaction and Data Flow

Both 512 × 512 assets remain absolutely stacked inside `.avatar`:

1. The watercolor image is opaque at rest.
2. The original photograph starts transparent above it.
3. Hovering `.avatar` transitions the photograph to opaque and the watercolor image to transparent over 0.25 seconds.
4. Moving the pointer away reverses the transition.

The interaction remains CSS-only. Scope the two hover-state selectors to `@media (hover: hover) and (pointer: fine)` so only mouse-like pointing devices activate the swap; touch devices continue to show the watercolor portrait instead of entering a sticky hover state. Users who request reduced motion receive an immediate swap because the existing `prefers-reduced-motion` rule disables the transition.

## Loading and Accessibility

- Keep the meaningful portrait description on the default watercolor image.
- Keep the hover photograph decorative with `alt=""` and `aria-hidden="true"` so screen readers do not announce the same person twice.
- Remove lazy loading from the hover photograph. It is an above-the-fold asset of roughly 53 KB and should be ready before the first pointer hover.
- Preserve the intrinsic `width="512"` and `height="512"` attributes on both images.

## Error Handling

This static page has no runtime recovery layer. A missing avatar is a deployment error, so prevention is the appropriate handling:

- Verify both referenced files exist and remain non-empty 512 × 512 images.
- Load the page through a local HTTP server and confirm that both image requests return successfully.
- Keep the default image beneath the hover image so the resting state remains meaningful.

## Verification

Verify the completed change at these widths:

- A desktop viewport at or above the 980 px page width.
- 701 px, immediately above the mobile breakpoint.
- 700 px, at the mobile breakpoint.
- A representative phone width such as 390 px.

At each relevant width, confirm:

- The avatar is exactly 176 px on desktop or 120 px on mobile.
- The header and biography do not overlap the avatar.
- Text wraps naturally and the page has no horizontal scrollbar.
- Other page sections retain their current width and alignment.
- The watercolor portrait appears at rest.
- Pointer hover crossfades to the original photograph, and pointer exit restores the watercolor portrait.
- A touch-oriented viewport retains the watercolor portrait without a sticky hover state.
- With reduced motion enabled, the swap occurs without an opacity animation.
- Both images load without a 404 response.

## Files Expected to Change During Implementation

- `index.html`: adjust desktop/mobile avatar dimensions, desktop hero gap, and hover-image loading behavior.

No image assets, build scripts, or unrelated page sections should change.
