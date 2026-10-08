# Phase 12 — UI Review

**Audited:** 2026-10-07 (tree b0e6c0bd; first UI audit of this phase, run during re-verification)
**Baseline:** abstract 6-pillar standards (no UI-SPEC.md for phase 12); 12-CONTEXT.md decisions D-01…D-20 treated as locked
**Screenshots:** not captured (no dev server on localhost:3000 / 5173 / 8080, nor on :8000) — code-only audit
**Interaction captures:** off (workflow.ui_interaction_capture is false)

Scope: the ad editor's attachment strip — `ads/includes/media_strip.html`, `media_add_tile.html`, `media_refusals.html`, `media_upload_form.html`, the strip block in `ads/form.html:219-251`, the `form_wrapper` busy dot, and the related CSS in `app/static/css/app.css`. Human evidence: `12-UAT.md` (8/8 pass on 2026-09-21, including the batch of 4–5 MB photos and whether the busy indicator could be seen). Those two checks are not reopened here.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Refusal texts are specific and name each file (D-05), but sentence case is mixed across the closed set, and the ceiling text says "Удалите лишние" when nothing extra was attached |
| 2. Visuals | 2/4 | Refusal rows are flex items in the same `flex-wrap` row as the 88px tiles, so a short refusal sits beside the tiles instead of above them; the busy dot is an 8px grey point with nothing visible to anchor it |
| 3. Color | 4/4 | Uses tokens only: `--danger` appears on the refusal alert and on «×» hover, nothing hardcoded |
| 4. Typography | 3/4 | «+ ФАЙЛ» is set at `--fs-2xs` in mono and muted — the smallest size on the screen, on the screen's main call to action |
| 5. Spacing | 3/4 | 8px gap and 88px tiles are consistent; refusals inherit the tile gap and get no vertical rhythm of their own |
| 6. Experience Design | 2/4 | The busy state is visual only (`aria-hidden`, no live text); the «×» names are generic; the add tile was keyboard-unreachable as shipped and only fixed in phase 15, with focus loss at the ceiling still open by owner acceptance |

**Overall: 17/24**

---

## Top 3 Priority Fixes

1. **WARNING — refusal rows share the tile flex row** (`media_refusals.html` included first inside `[data-media]`, `app.css:2138`). A short reason such as the parts-limit text, or several short ones, lays out inline with the 88px thumbnails, and the error reads as just another tile. Fix: add `[data-media] > .alert { flex: 1 0 100%; }` (or wrap the refusals in a full-width block before the tray) so every refusal takes its own line above the tiles.
2. **WARNING — the upload busy state is silent to assistive tech and weak visually** (`components/form_wrapper.html`: `<span class="form-busy" aria-hidden="true">`; `app.css:2310-2327`). The upload form's only child is a visually hidden input, so the 8px dot is absolutely positioned at the bottom-right of a form box that has almost no height. A 10×5 MB batch can take seconds, and a screen reader gets nothing. The owner passed visibility in 12-UAT; this finding is about non-visual users and is new evidence, not a restatement. Fix: put `aria-busy` on `#media-strip` during the request (htmx `hx-indicator` can target it), or add a visually hidden `role="status"` text such as «Загружаем…» toggled by `.htmx-request`, with no new JS.
3. **WARNING — «×» remove buttons all share one accessible name** (`media_strip.html`: `aria-label="Убрать вложение"`, with the filename only in `title`). With ten tiles, a screen reader hears ten identical "Убрать вложение" buttons. Fix: `aria-label="Убрать {{ key.split('_', 1)[-1] }}"`. The name has already been normalised by `safe_filename` because it comes from the stored key, which keeps the D-05 distinction.

Further findings (6 more) are listed under each pillar below.

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

- PASS: one row per file with its own reason, `{{ display_name }} — {{ reason }}` (`media_refusals.html`). This beats the old single-phrase `showUploadError()`, per D-05.
- WARNING — mixed sentence case in one closed set. `UNSUPPORTED_IMAGE_MESSAGE`, `OVERSIZED_IMAGE_MESSAGE` and `upload_limit_message` start with a capital letter and end with a period (`app/services/image_upload.py:133-153, 197-200`). `STORAGE_UNAVAILABLE_MESSAGE` (:172) and `upload_parts_message` (:226-229) are lower-case with no period. After the « — » separator, a row reads as "cat.webp — Не удалось загрузить: …" in one case and "a.jpg — файл не сохранился …" in another. The prefix «Не удалось загрузить:» also repeats the context that the filename plus dash already gives. Fix: normalise all five to the lower-case, no-prefix form used by the storage text.
- WARNING — the ceiling text gives the wrong instruction for the partial-accept case (D-06): «Можно прикрепить не больше N вложений. Удалите лишние и попробуйте снова.» The refused files were never attached, so there is nothing "лишние" to delete in the strip. Suggested: «места для вложений закончились — уберите одно из прикреплённых, чтобы добавить этот файл».
- Minor: «+ ФАЙЛ» does not say what is accepted. The JPEG/PNG rule only shows up after a refusal. `accept="image/jpeg,image/png"` filters the picker, but a drag-and-drop or "All files" choice still reaches the refusal.

### Pillar 2: Visuals (2/4)

- WARNING — refusal layout (Top fix 1). Line ownership: `git log` shows the refusal markup moved into `media_refusals.html` in 12-09 (`1dba89c1`), and the tray layout `[data-media]{display:flex;flex-wrap:wrap}` dates to `1bc66fc8` (phase 2). Phase 12 put a block-level message into an inline-flow flex container without a basis rule, so this is phase 12's finding.
- WARNING — busy-dot anchoring (Top fix 2). `.form-wrapper > .form-busy { position:absolute; right:0; bottom:0 }`, from 11-21 `810eaa77`, places the dot at the right edge of the full field column, below the strip. It is not next to the tile area the person is looking at. UAT says it can be seen; the issue is how close it is to the thing it reports on.
- PASS: «×» is a 36×36 target with a translucent backdrop over the thumbnail (`app.css:2150-2164`), and filenames are kept off the tile so hostile names cannot break the layout.

### Pillar 3: Color (4/4)

- `--danger` appears in exactly two places on this surface: `.alert--error` on refusal rows and `.media-tile__remove:hover`. Everything else uses neutral tokens (`--surface-input`, `--border-input`, `--border-dashed`, `--text-muted`). The phase adds no hex or rgb literals. The «×» backdrop uses `color-mix(var(--bg) 72%)`, which keeps it in the theme. No accent overuse.

### Pillar 4: Typography (3/4)

- WARNING — the add tile's label is `font-family: var(--font-mono); font-size: var(--fs-2xs); color: var(--text-muted)` (`app.css:2166-2172`, from phase 2 `1bc66fc8`, unchanged by phase 12). It is the smallest and lowest-contrast text in the editor, and it is the only way to add an image. Phase 12 made this tile the sole entry point by removing every other upload affordance (D-12), so the weak label now carries more weight than before. Suggest `--fs-xs` at minimum, or `--text-secondary`.
- «×» uses `--fs-lg` mono and refusals use `.alert`'s `--fs-md`, both within the existing scale. Phase 12 introduces no new sizes or weights.

### Pillar 5: Spacing (3/4)

- 8px tray gap and 88×88 tiles are applied consistently. Phase 12 adds no arbitrary px values in templates.
- WARNING — refusals get only the 8px flex gap from the tiles. Once they are made full-width (fix 1), they need a separate rhythm. Stacked `.alert` rows at 8px look like one block, which is acceptable, but there is no extra separation between the last refusal and the first tile.

### Pillar 6: Experience Design (2/4)

- WARNING — no non-visual busy state (Top fix 2). `disabled_elt=''` on the upload form (`media_upload_form.html`) also means nothing is disabled during the request. That is deliberate: `hx-sync="this:queue last"` from D-16 queues the next selection. But `queue last` silently drops an intermediate selection when three are made during one long upload, and no copy says so. Code-derived; not exercised.
- WARNING — identical «×» accessible names (Top fix 3).
- WARNING — keyboard path. As phase 12 shipped it, «+ ФАЙЛ» was a `<label>` and the input was unreachable by Tab. The fix came in phase 15 (`d0a31bd9`, «make «+ ФАЙЛ» reachable from the keyboard», 2026-10-06; ref `15-UAT.md` У-12). Today the input is visually hidden but focusable, and the focus ring is drawn on the tile through `body:has(#file-input:focus-visible)`, which is fine. What remains open: when a keyboard upload reaches the ceiling, the focused input is hidden and focus drops to `<body>` (`app.css:2177-2181`). The owner accepted this on 2026-10-06 (phase 15, `9afcd205`), so it is recorded here as a known consequence and is not scored against phase 12.
- PASS: every refusal path is visible and stays in place. 200 + fragment always (D-04); the storage outage becomes a per-file row (D-16); foreign-key refusal still names every file (D-20). `role="alert"` is on each row, but a batch of several refusals fires several alerts at once. Minor: a single `role="alert"` container around the refusal list would be read once.
- PASS: removal goes through the existing `remove_image` submit (D-10), with no confirmation. This is acceptable because removing an unsaved attachment is cheap to redo, and the owner locked it.

No `components.json`, so the registry audit was skipped.

---

## Files Audited

- app/templates/ads/includes/media_strip.html
- app/templates/ads/includes/media_add_tile.html
- app/templates/ads/includes/media_refusals.html
- app/templates/ads/includes/media_upload_form.html
- app/templates/ads/form.html (lines 185-252)
- app/templates/components/form_wrapper.html
- app/static/css/app.css (lines 846-856, 2138-2192, 2310-2327)
- app/services/image_upload.py (refusal texts, lines 133-229)
- app/services/image_keys.py (INACCESSIBLE_IMAGE_MESSAGE)
- .planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-CONTEXT.md, 12-UAT.md, 12-01…12-13 PLAN/SUMMARY (frontmatter and headings)
