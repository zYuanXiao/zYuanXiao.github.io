# Transparent Avatar Edges Design

## Goal

Make the exterior paper-colored area of both profile portraits transparent without changing the people, composition, internal highlights, watercolor texture, or existing hover interaction.

## Selected Approach

Use a deterministic edge-connected mask. Starting from the four image borders, classify only near-white pixels connected to the exterior as background. Convert those pixels to transparent alpha and softly feather the boundary by 1–2 pixels.

This approach is preferred over a global white threshold because it preserves disconnected light regions inside the composition, including window highlights, glasses reflections, skin highlights, and pale watercolor areas. It is preferred over generative editing because it does not reinterpret the face, paper texture, or crop.

## Assets and Page Integration

- Input assets remain the existing 512×512 JPEG files:
  - `assets/profile/zhiyuan-xiao.jpg`
  - `assets/profile/zhiyuan-xiao-hover.jpg`
- Generate sibling 512×512 RGBA PNG files with stable names:
  - `assets/profile/zhiyuan-xiao.png`
  - `assets/profile/zhiyuan-xiao-hover.png`
- Update the two avatar `<img>` sources in `index.html` to reference the PNG files.
- Keep the existing 176px desktop and 120px mobile avatar dimensions, absolute image stacking, fine-pointer hover behavior, reduced-motion rule, and accessible alt-text behavior.
- Set the avatar container background to transparent so the page background shows through cleared pixels.

The source JPEGs remain in the repository as reproducible inputs and are not overwritten.

## Masking Algorithm

1. Read the source image as RGB and create an initially opaque alpha plane.
2. Calculate a near-white score using lightness, chroma, and distance from the sampled border paper color rather than a single hard RGB cutoff.
3. Flood-fill candidate pixels from all four borders. Only pixels connected to a border can become transparent.
4. Preserve all disconnected interior pixels, even when they are white or pale.
5. Convert the connected exterior region to alpha 0.
6. Apply a narrow 1–2px alpha feather at the retained paper edge to avoid jagged halos while preserving the natural irregular boundary.
7. Save losslessly as RGBA PNG at the original 512×512 dimensions.

The two images may use separately sampled border colors because their paper tones differ, but they share the same algorithm and validation contract.

## Failure Handling

The conversion must fail without replacing output assets if any of these conditions occurs:

- the input is missing or not 512×512;
- the output lacks an alpha channel;
- no meaningful exterior region is removed;
- the transparent region reaches the protected central portrait area;
- retained subject coverage drops below the validated minimum.

## Verification

Automated checks will verify:

- both PNGs are 512×512 RGBA images;
- all four corners are transparent;
- a meaningful but bounded fraction of pixels is transparent;
- central face/torso sample regions remain opaque;
- disconnected internal pale regions remain opaque;
- the existing portrait-alignment checks still pass;
- `index.html` references the PNGs and preserves hover/media-query behavior.

Browser verification will check the desktop and mobile layouts, transparent corners against the page background, default watercolor state, and hover-photo state. No changes are made to biography or CV content.
