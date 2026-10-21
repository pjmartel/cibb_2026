# Quality-assurance inventory

## Required checks

- Official class title and `CIBB_2026` repository identity.
- Desktop and 375px layouts for every public page; no horizontal overflow.
- All primary navigation links and mobile open/close/Escape states.
- Slide next/previous, selector, thumbnail, keyboard, hash deep link, boundary states and high-resolution PNG link.
- Resource search, category filtering, empty state and reset.
- Slides, notes and toolkit download paths; ZIP integrity.
- External PyMOL/Foldseek links and visible, selectable URL fallbacks.
- Practical remains explicitly in preparation, without absent-file download buttons or target solutions.
- Pure numerical helper tests and optional real PyMOL integration tests.
- UTF-8/LF text files, safe ZIP names, relative-path deployment under a project prefix.

## Deliberate exclusions

GitHub repository creation, pushing and live GitHub Pages publication are left to the course owner. External prediction services and GPU runs are not executed as part of this static repository task.

The practical has not been designed or validated. No hosted note persistence, authentication, external-service credentials or AI backend is implied.

## Checks completed on 2026-10-21

- Seven public pages rendered at desktop 1440px and mobile 375px, with no horizontal page overflow.
- Page screenshots reviewed for consistent typography, alignment, spacing and image placement.
- All primary navigation links, mobile open/close/Escape and notes anchors exercised.
- Slide next/previous, selection, thumbnails, keyboard, hash and first/last states tested.
- Image-load-failure recovery exercised. The viewer uses a high-resolution image link rather than the native Fullscreen API for preview compatibility.
- Resource search, topic filtering, zero results and reset tested.
- Actual local downloads of slides, toolkit, lecture notes and notes template checked.
- JavaScript-disabled mobile navigation and direct-slide thumbnail fallbacks checked.
- No JavaScript runtime errors observed during these checks.
- Static links served beneath `/docs/`, exercising project-prefix behaviour.
- Seven helper tests passed using Python 3.11 and open-source PyMOL 3.2.
- The actual headless PyMOL demo, empty-map argument handling and explicit pipe-separated map syntax passed.
- Reference-anchored three-model example produced 164 unique CA columns; alternate conformers were not double-counted.
- Offline repository check passed: 16 PNG/SVG slide pairs, 45-minute manifest, UTF-8/LF files, local links, safe download ZIPs and the PDB100 caveat.

These are local checks, not a claim that a GitHub Actions run or public Pages deployment has already occurred. The owner must push the repository and enable Pages to exercise that remote environment.
