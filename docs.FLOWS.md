# Main flows

## Navigation and page identity
- Start: index.html.
- Click Student notes, Slides, Practical, PyMOL toolkit and Resources, then the CIBB wordmark.
- Expect the correct page heading each time and the official course title on home.
- At 375px, open Menu, follow a link, reopen it, and close with Escape.

## Slides
- Start: slides.html, also following the home-page lecture links.
- Expect a simple PDF page with Open lecture PDF, Download lecture PDF and companion notes.
- Open lecture PDF opens downloads/TSB_2026.pdf in a new tab; Download lecture PDF saves the same bytes on normal static hosting.
- The approved PowerPoint export has 17 pages; keep it unchanged. Page count must not be tied to the archived 16-image manifest.
- No carousel, image ZIP or editable SVG download is offered on the active slides page.
- Replacing the one published PDF and rebuilding preserves the exact new source bytes.
- Before generation, a missing or clearly invalid PDF produces an actionable error without rewriting pages.
- Retain the archived PNG/SVG assets and all PyMOL scripts; no PowerPoint is added.

## Notes and practical
- Download lecture notes and notes template; follow an in-page heading link.
- Practical remains clearly in preparation without answer keys or absent-file download links.

## Resources
- Search Foldseek: two matching resources.
- Select an incompatible category or search for a nonexistent term: empty state.
- Reset filters: all 18 resources return; Setup shows four.

## PyMOL tool replacement
- Start: toolkit.html.
- Show author-supplied ligalign.py and struct_diff.py, not the replaced generated helpers.
- Explain graph/symmetry matching, fit=0 versus fit=1, whole-mobile-object movement and optional RDKit.
- Explain that struct_diff needs a prior superposition, overwrites B-values, and colours geometry rather than sequence identity.
- Provide the benzene and myoglobin/leghemoglobin commands and author attribution.
- Download toolkit: contains the exact supplied script bytes and runnable demonstration files.
- Old helper files and commands are absent from the repository, public page and ZIP.
- Preserve Unix LF files, the GitHub Actions cache fix and all existing slide assets.

## Visual and error checks
- Render all seven pages at desktop and 375px without page overflow or new runtime errors.
- Inspect the changed toolkit's beginning, examples, warnings and footer.
- Check no-result resource state and reset.
- Check JavaScript-disabled navigation and both direct PDF links.
- Test old slides.html#slide-8 links still reach the new PDF page.
- Compare PDF checksums after downloading; distinguish hosted-preview inline rendering from GitHub Pages download behavior.
