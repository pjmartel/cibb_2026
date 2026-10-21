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

## Original site checks completed on 2026-10-21

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
- The initial generated-helper tests passed at that stage; those helpers have since been replaced by the owner's tools and these checks are not the current tool validation.
- Offline repository check passed: 16 PNG/SVG slide pairs, 45-minute manifest, UTF-8/LF files, local links, safe download ZIPs and the PDB100 caveat.

The owner subsequently confirmed that GitHub Pages is online after the cache correction below. Updates prepared here still need to be pushed to that repository; this integration does not itself push or deploy the user's GitHub repository.

## Deployment cache correction

The owner's first GitHub run exposed a workflow configuration error: `setup-python` could not find its default pip-cache manifest because this course uses `requirements-dev.txt`. The workflow now explicitly sets `cache-dependency-path: requirements-dev.txt`, as supported by the [setup-python documentation](https://github.com/actions/setup-python).

The offline validator checks that a pip-cache dependency path is explicitly configured and points to an existing file. That setting is retained in the full repository and is not changed by the incremental PyMOL update.

## Author-tool replacement checks

The owner supplied `ligalign.py` and `struct_diff.py`; their source bytes are preserved and checksummed. See `tool-review.md` for semantics, tested cases and limits, and `../docs.FLOWS.md` for the browser regression inventory.

The updated tests replace the old helper tests rather than continuing to test obsolete code. Optional PyMOL tests use actual runtime calls and the same PML commands that students receive.

The final author-tool run passed 14 tests using open-source PyMOL 3.2 / Python 3.11. Without PyMOL, five source-integrity/numerical tests passed and nine integration tests were skipped, matching the intended lightweight CI configuration.

All seven pages were rechecked at 1440px and 375px, with no horizontal page overflow or JavaScript runtime errors. Navigation, mobile menu/Escape, notes anchors and downloads, slide controls/PNG popup/download, resource filters/empty/reset and JavaScript-disabled fallback passed.

Both individual Python downloads matched the author's source hashes, and the downloaded toolkit contained the new scripts. The public text now states the pose-versus-fit distinction, whole-object motion, B-value overwrite behaviour and geometric-versus-sequence interpretation.

The incremental update excludes `.github/workflows/` and the lecture assets. No change to the owner's live GitHub repository is implied until the owner applies and pushes the update.

The incremental ZIP was also applied to the previous complete release in a temporary directory, followed by removal of the two superseded files. Validation and lightweight tests passed; the workflow bytes and every lecture-slide asset hash remained unchanged.
