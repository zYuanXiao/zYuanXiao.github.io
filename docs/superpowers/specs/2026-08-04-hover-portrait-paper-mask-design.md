# Hover Portrait Paper-Mask Design

**Date:** 2026-08-04
**Status:** Approved
**Scope:** Recompose the hover photograph so it aligns with the resting watercolor portrait and shares its paper-like negative space.

## Context

The home-page avatar already crossfades from `assets/profile/zhiyuan-xiao.jpg` to `assets/profile/zhiyuan-xiao-hover.jpg`. The current hover asset is unusable because the build script's Haar cascade selected a false-positive face near the lower-left of the source photograph, so the generated square shows background and a sleeve instead of the person.

The desired result is not a full-bleed square photograph, a transparent cutout, or a conventional hard circular avatar. It is an opaque square composition: a large, softly irregular oval photograph sits on a warm-white paper field, leaving visible negative space around parts of the image in the same spirit as the watercolor portrait.

## Goals

- Preserve the default watercolor portrait without modification.
- Reframe the original photograph so the face, head scale, and shoulder height closely match the watercolor portrait during the crossfade.
- Present the photograph inside a large organic oval with softly feathered, subtly uneven edges.
- Fill the area outside the oval with an opaque warm-white paper treatment.
- Keep the existing asset path, hover behavior, responsive avatar sizes, and page layout unchanged.
- Prevent the existing build script from silently recreating the false-positive sleeve crop.

## Non-goals

- Do not watercolor-stylize the person in the photograph.
- Do not replace the paper field with transparency.
- Do not use a mathematically perfect circle or a hard-edged photo frame.
- Do not alter the person's identity, facial features, glasses, hairstyle, clothing, or expression.
- Do not change the 176 px desktop or 120 px mobile avatar sizes.

## Chosen Composition

The final hover asset remains an opaque 512 × 512 square at `assets/profile/zhiyuan-xiao-hover.jpg`.

1. A warm-white paper base fills the complete square.
2. The original photograph is manually reframed into a head-and-shoulders composition.
3. The photographic region is revealed through a large centered organic oval rather than filling the square.
4. The oval leaves obvious warm-white negative space in all four corners and smaller, irregular gaps along parts of the sides.
5. Its boundary uses an approximately 8–16 px soft transition with mild natural asymmetry, suggesting a watercolor wash ending on paper rather than a digital cutout.
6. The interior retains the authentic photograph and a limited amount of its indoor background.

## Alignment Targets

The existing 512 × 512 watercolor asset is the visual reference. The hover photograph should target:

- face center within approximately 8 px of the watercolor face center;
- visible face height within approximately 10 percent of the watercolor face height;
- top of hair and shoulder line at approximately the same vertical positions;
- enough shoulder width to make the transition feel continuous without allowing the shirt to dominate the crop.

These are perceptual acceptance tolerances, not a demand for pixel-identical anatomy. A 50-percent opacity overlay and the live CSS crossfade will be used to judge alignment.

## Asset-Generation Approach

Use the original full-resolution photograph as the identity-preserving source and the watercolor portrait as the composition reference. Generate/edit the hover asset with explicit instructions to preserve the real face, glasses, hair, clothing, and expression while changing only framing, paper surround, and edge treatment. Reject any result that invents or materially changes facial or clothing details.

The final asset should remain JPEG-compatible because the surrounding paper is opaque and the existing page references the `.jpg` path. No HTML asset-path migration is required.

## Build-Script Safety

`tools/build_profile.py` must no longer treat the largest unrestricted Haar detection as authoritative for this photograph. Update the workflow so the known hover source uses an explicit manual crop anchor, or make an explicit hover anchor mandatory when automatic detection is implausible. The script should fail with a clear message instead of writing an obviously off-center avatar.

The script's role is defensive reproducibility: it must not silently overwrite the approved art with the current false-positive crop. The approved paper-mask treatment may remain a curated final asset rather than being recreated by face detection alone.

## Error Handling and Rejection Criteria

Reject and regenerate or adjust the candidate if any of these occur:

- the face, eyes, glasses, hair, expression, or shirt details are visibly altered;
- the face is substantially smaller, larger, or offset from the watercolor reference;
- the mask becomes a perfect hard circle or rectangular frame;
- the paper surround is transparent, gray, strongly yellow, or covers important facial features;
- the crop again emphasizes a sleeve or background instead of the person;
- the asset is not a non-empty 512 × 512 image.

## Verification

1. Inspect the finished asset by itself at full resolution.
2. Compare it against the watercolor image with a 50-percent overlay.
3. Load the local site and verify the resting watercolor, hover crossfade, pointer exit, and reduced-motion state.
4. Check the avatar at 176 px desktop and 120 px mobile sizes.
5. Confirm that the existing layout has no new overlap or horizontal overflow.
6. Confirm both image requests return HTTP 200 and the hover asset is non-empty and 512 × 512.

## Files Expected to Change During Implementation

- `assets/profile/zhiyuan-xiao-hover.jpg`: replace the broken crop with the approved paper-mask composition.
- `tools/build_profile.py`: add a guard or explicit-anchor workflow that prevents false-positive hover crops.

`index.html` and the default watercolor asset are not expected to change.
