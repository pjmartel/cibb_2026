# Quality-assurance inventory

## Required checks

- Official class title and `CIBB_2026` repository identity.
- Desktop and 375px layouts for every public page; no horizontal overflow.
- All primary navigation links and mobile open/close/Escape states.
- Open and Download lecture PDF links, companion notes, PDF byte preservation and absence of the superseded carousel.
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

## PDF publication update checked on 2026-10-22

The instructor's PowerPoint PDF export intentionally contains 17 pages. Its single publication path is `docs/downloads/TSB_2026.pdf`. The published page offers Open lecture PDF, Download lecture PDF and companion notes, with no carousel or image-download offers; page count is not coupled to the old 16-image manifest.

The supplied export and the PDF downloaded through the local page have identical SHA-256 hashes: `e14ff9866a90f3aa9b2ba5b6a7ab122f622c3075f8fe6d60caae9858ba82b24a`. The PDF was checked using `pdfinfo` and `qpdf --check`, and was not modified or regenerated. The builder's normal validation is a lightweight header/trailer check, not a full PDF parser.

All seven pages were rendered at 1440px and 375px with no horizontal page overflow or JavaScript runtime errors. Browser checks covered PDF open/download, companion notes, notes anchors/downloads, toolkit download, all primary navigation, home return, mobile menu/Escape, resource search/category/empty/reset, and JavaScript-disabled mobile navigation/PDF download. Old slide hash URLs still reach the new slides page. The original stylesheet was preserved.

The existing private preview was updated in place and checked in a fresh browser context. Its PDF open link and resource filtering worked, and the PDF page had no mobile overflow. The private preview proxy renders the Download link inline rather than forcing a download; the browser's PDF viewer can save it. Local static-hosting download was tested and matched the source bytes. Live GitHub Pages has not been updated or tested by this operation.

The repository validator passed. The lightweight test run discovered 17 tests: eight passed and nine optional PyMOL integration tests were skipped because PyMOL was absent in that environment. New publication tests verify byte preservation, independence from the archived slide manifest, and missing/incomplete PDF rejection before rewriting pages.

PyMOL scripts, scientific notes, practical material, original slide assets and the Pages workflow are unchanged. Reading the instructor's WSL checkout succeeded, and the inspected source hashes matched this update's baseline. The local write attempt was denied because the checkout is outside selected workspace roots; no local files, commits or pushes were changed. A separately supplied Git patch and instructions allow the instructor to apply the tested update to the existing checkout.

## Lecture References entry checked on 2026-10-22

The new References page uses the approved 18-entry lecture-only bibliography. The two instructor/practical-debrief papers and the complete instructor bibliography are not added to the public site. The source is content/references.md; the builder generates references.html and downloads/lecture-references.md, retaining one page h1.

References appears in all eight pages' primary navigation and footer, in the home materials list and in Sources & reuse. The existing reading-page layout, contents links, theme, PDF publication flow and practical availability are retained. The mobile menu also handles tablet widths, and the JavaScript-disabled narrow-screen header is non-sticky so contents anchors are not obscured.

All eight pages were checked at 1440px and 375px without horizontal overflow or new JavaScript runtime errors; navigation was also checked at 768px, 960px, 961px and 1024px. Checks included references contents anchors, a real publication-link popup, bibliography download bytes, home/source-page entry points, mobile Menu/Escape and JavaScript-disabled navigation, download and anchors. Relative links also worked under a project-like /docs/ prefix.

Existing flows checked include resource search, category filtering, empty state/reset, PDF popup and byte-identical download, companion notes, lecture notes/template downloads and toolkit download. Measured reference-page body, metadata, link and button contrasts were at least 6.97:1. The reference source and generated downloads contain only the approved lecture selection.

All 25 tests passed in the Python 3.11 / real PyMOL QA environment. In the lightweight environment, 16 passed and the nine optional PyMOL integration tests were skipped, as intended. The repository validator passed with eight public pages. New tests cover references selection, source links, download consistency, shared navigation, rebuild reproducibility and preservation of PDF, workflow and supplied-script bytes.

The incremental patch contains source and prebuilt static pages, not a new PDF, model pack, toolkit archive or workflow. The GitHub repository, the instructor's WSL files and the live GitHub Pages site have not been changed automatically.
