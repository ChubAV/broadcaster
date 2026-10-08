---
phase: 11-massovyy-perevod-razdelov-pisma
reviewed: 2026-09-18T00:00:00Z
depth: standard
diff_base: 59398f2ccd1929606a5e4ec7b966a33cb34fcd0c
pass: incremental
files_reviewed: 4
files_reviewed_list:
  - app/static/css/app.css
  - app/templates/components/form_wrapper.html
  - tests/test_templates/test_components.py
  - tests/test_templates/test_htmx_markup_gates.py
# ⚠️ ДВА СЛАГАЕМЫХ, А НЕ ОДНО ЧИСЛО. `findings` ниже — счёт ЭТОГО прохода
# (инкрементальный обход четырёх файлов, diff_base 59398f2). `carried_forward` —
# шесть находок полного обхода 68 файлов от 2026-09-17, которые в этом проходе
# НЕ ПЕРЕПРОВЕРЯЛИСЬ и не закрыты. `file_total` — то, что читатель найдёт в
# файле целиком.
findings:
  critical: 0
  warning: 4
  info: 4
  total: 8
carried_forward:
  from: 2026-09-17T09:01:18Z
  re_verified: false
  critical: 0
  warning: 3
  info: 3
  total: 6
file_total:
  critical: 0
  warning: 7
  info: 7
  total: 14
status: issues_found
---

# Phase 11: Code Review Report

**Reviewed:** 2026-09-18 (incremental pass, `diff_base` 59398f2)
**Depth:** standard
**Files Reviewed (this pass):** 4
**Status:** issues_found

## Narrative Findings (AI reviewer)

## Summary

This is an **incremental** pass over the only plan that landed since the previous review recorded at 59398f2: plan 11-21, the G-11-6 gap closure. Scope is exactly four files, +654/-5 (`app/` portion +75/-1). The six findings of the 2026-09-17 full-phase review are carried verbatim in the section at the bottom and were **not** re-examined here.

The substantive change: `form_wrapper.html` now prints a literal `class="form-wrapper"` on its form tag (line 163), and `app.css` uses that class as a scope to take the hidden `.form-busy` indicator out of layout flow (`app.css:2207-2210`), with a declared in-flow exception for the group-row toggle (`app.css:2762`).

**What I checked in the CSS and found sound** — recorded so nobody re-derives it:

- **Specificity.** `.form-wrapper > .form-busy` is (0,2,0). The group-row exception `[data-group-row] form[action$="/toggle"] > .form-busy` is (0,3,1) — three class-column simple selectors (`[data-group-row]`, `[action$="/toggle"]`, `.form-busy`) and one type (`form`). The exception wins regardless of source order, as the comment at `app.css:2760-2761` claims. The base `.form-busy` (0,1,0) and `.form-busy.htmx-request` (0,2,0) declare properties disjoint from the new rule, so no cascade conflict.
- **The two 300 ms thresholds survived unchanged.** `app.css:2198` and `app.css:2203` are untouched by the diff, `position` is not a transitioned property in either, and `test_the_indicator_class_carries_a_visibility_threshold` still guards them. Verified by running the file.
- **`position` cannot clip or escape `.card { overflow: hidden }`** (`app.css:757-761`). Both offsets are `0`, so the dot's border box never crosses the form's padding box; the form is not a clipper, and the containing block is the form itself.
- **No containing-block regression.** I enumerated every `position: absolute` rule in the stylesheet (lines 567, 798, 1320, 1332, 2048, 2401). `.toggle__input` and `.chip__input` declare no offsets, so their used position is the static-position fallback and is unaffected by a new positioned ancestor. `.brand-mark::after`, `.media-tile__remove` and `.modal__overlay` already have a positioned ancestor (`.brand-mark`, `.media-tile` at 2037, `.modal`). `.banner-dismiss` does not render inside a wrapped form. Nothing re-anchors.
- **Can the 8 px dot land on an interactive control?** For the schedule toggle forms — no, and I initially expected yes. `.sched-card__head .toggle` and `.sched-item__head .toggle` carry `min-height: 40px` (`app.css:2319`, `app.css:2578`) while `.toggle__track` is 22 px, so the dot at `bottom: 0` lands ~9 px *below* the track, not on it. For the shrink-wrapped single-button forms (`.acct-card__actions form { flex: none }`, `app.css:3068`) it does straddle the button's rounded bottom-right corner, but `pointer-events: none` removes the hit-test, and `app.css:2176-2178` records that placement as the intended one. No functional defect.
- **No regression in the markup-contract suites.** `tests/test_templates/{test_htmx_markup_gates,test_components}.py` (171 passed) and `tests/test_pages/{test_account_groups,test_htmx_gates,test_htmx_post_pairs,test_responsive_markup}.py` (389 passed) — 560 in total, no failures. (The full `tests/` run exceeded the review harness's 10-minute command ceiling twice and was not completed here; that is a limitation of this pass, not an observed failure.)

**No Critical findings in this scope.** The stylesheet change is correct. Every finding below is about the *gates* that are supposed to keep it correct: each one is a way the fix can be silently reverted with all 171 checks in these two files still green — which is precisely the failure mode this phase's gate doctrine exists to make impossible.

**Numbering note:** new findings start at WR-04 / IN-04 so they never collide with the carried WR-01…WR-03 / IN-01…IN-03.

## Warnings

### WR-04: The rule depends on the child combinator, and nothing gates direct-childness — nesting the indicator one level deeper reverts the fix with every check green

**File:** `app/static/css/app.css:2208`, `app/templates/components/form_wrapper.html:170`, `tests/test_templates/test_htmx_markup_gates.py:3201-3208`, `tests/test_templates/test_components.py:750-755`

**Issue:** The fix is `.form-wrapper > .form-busy` — a **child** combinator. It stops matching the moment the indicator span is not a direct child of the form. The macro emits it as one today (`form_wrapper.html:170`, immediately before `</form>`), but no check constrains that:

- `_offenders_wrapped_indicator_footprint` verifies only (a) that the form tag carries ` class="form-wrapper"` and (b) that the two CSS rules exist with the right declarations. It never looks at where the indicator node sits.
- `test_the_reported_profile_form_carries_the_indicator_scope` (`test_components.py:750-755`) asserts `out.index(form) < at < out.index("</form>")` — that is **descendant**, not child. A span wrapped in `<div class="form-foot">…</div>` satisfies it.
- The only other gate touching the node, `assert QUALITY_INDICATOR_NODE in sources[template]` (`test_htmx_markup_gates.py:5997`), is textual presence.

So a future edit that groups the indicator with anything else inside the macro re-opens G-11-6 — the 21 px strip under «Сохранить», the 24 px in the schedule editor, the ~12 px width in action rows — with zero red. This is the same silent-failure shape that `_offenders_wrapped_indicator_footprint`'s substitution (т2) was invented to close for the scope class; the other half of the same coupling is unguarded.

**Fix:** Assert the adjacency in the wrapper source, and prove the tooth with a substitution, in `_offenders_wrapped_indicator_footprint`:

```python
    body = _strip_comments(sources[WRAPPER])
    if f"{QUALITY_INDICATOR_NODE}\n</form>" not in body:
        offenders[f"{WRAPPER} [прямой потомок]"] = (
            f"узел индикатора не ПРЯМОЙ потомок тега формы: селектор "
            f"{WRAPPED_INDICATOR_SELECTOR!r} несёт комбинатор дочернего "
            f"элемента и перестаёт совпадать — скрытый узел возвращается в "
            f"поток, а правило остаётся зелёным"
        )
```

and in `test_a_wrapped_form_gives_its_indicator_no_layout_footprint` add:

```python
    # (т3) Узел завёрнут в контейнер: селектор дочернего элемента промахивается.
    nested = dict(_all_templates(_tree_with(tmp_path, Substitution(
        WRAPPER, QUALITY_INDICATOR_NODE, f"<div>{QUALITY_INDICATOR_NODE}</div>",
    ))))
    assert f"{WRAPPER} [прямой потомок]" in _offenders_wrapped_indicator_footprint(
        _app_css(), nested
    )
```

(Alternatively drop the combinator to a descendant selector `.form-wrapper .form-busy` — but that is the weaker choice here, because the wrapper's `{{ caller() }}` body is arbitrary caller markup and a descendant selector would reach any `.form-busy` a caller ever nests.)

---

### WR-05: The declared in-flow exception is tied to a CSS selector and to nothing else — renaming the route or the row attribute orphans it silently

**File:** `tests/test_templates/test_htmx_markup_gates.py:2927-2972`, `3268-3275`; `app/static/css/app.css:2762`; `app/templates/account_groups/includes/group_row.html:193`

**Issue:** `InFlowIndicatorException` carries two fields: `selector` and `reason`. The gate's only enforcement is "a CSS rule whose selector string equals `entry.selector` exists and declares `position: static`". Nothing ties the entry back to the markup it excepts:

- nothing asserts `data-group-row` still appears in `account_groups/includes/group_row.html`;
- nothing asserts that file's wrapped form still posts to an address ending `/toggle`.

Rename the route to `/toggle-active` (or the row attribute to `data-group-item`) and: the CSS rule still exists and still says `position: static`, so the gate stays green; the selector now matches nothing; the group-row dot leaves the flow contrary to **owner decision 3 of 2026-09-17** — the very decision the 700-character `reason` exists to protect. The prose would still be there, describing a state that no longer holds.

The project's own sibling idiom already demands this anchoring. `DISABLED_ELT_EXCEPTIONS` is keyed by template and the gate reports `"места отправки htmx в этом файле больше нет"` when the site disappears (`test_htmx_markup_gates.py:3948-3950`), `"объявленного вызывающего нет в дереве шаблонов"` when a declared caller disappears (`:3809-3812`), and requires the acting selector to be named in the reason (`:3821-3826`). `form_wrapper.html:118-121` states that discipline in prose. The new list omits all of it.

**Fix:** Give the record an anchor and check it:

```python
class InFlowIndicatorException(NamedTuple):
    selector: str
    template: str          # шаблон, чью форму запись выводит из-под правила
    anchor: str            # разметка, по которой селектор в него попадает
    reason: str

IN_FLOW_INDICATOR_EXCEPTIONS = (
    InFlowIndicatorException(
        selector=f'{GROUP_ROW_TOGGLE_FORM_SELECTOR} > .{INDICATOR_CLASS}',
        template="account_groups/includes/group_row.html",
        anchor="data-group-row",
        reason=(...),
    ),
)
```

and in `_offenders_wrapped_indicator_footprint`:

```python
    for entry in IN_FLOW_INDICATOR_EXCEPTIONS:
        source = sources.get(entry.template)
        if source is None or entry.anchor not in _strip_comments(source):
            offenders[f"{entry.selector} [опора]"] = (
                f"объявленное исключение не попадает в свой шаблон "
                f"{entry.template}: опора {entry.anchor!r} из разметки ушла, "
                f"селектор адресует пустоту, и точка уехала бы из-под тумблера "
                f"вопреки принятому решению"
            )
```

Also add `"/toggle"` reachability: assert the wrapped call in that template passes an `action` ending in the suffix the selector matches.

---

### WR-06: The exceptions list doubles as the panel gate's allow-list — one entry can whitelist a selector that reaches the confirmation panel, which is the one thing that gate exists to prevent

**File:** `tests/test_templates/test_htmx_markup_gates.py:3330-3335`, `2944-2972`

**Issue:**

```python
    allowed_indicator_selectors = {
        f".{INDICATOR_CLASS}",
        f".{INDICATOR_CLASS}.{RUNTIME_REQUEST_CLASS}",
        WRAPPED_INDICATOR_SELECTOR,
        *(entry.selector for entry in IN_FLOW_INDICATOR_EXCEPTIONS),
    }
```

`_offenders_panel_indicator_reach` delegates part of its allow-list to `IN_FLOW_INDICATOR_EXCEPTIONS`, and nothing constrains what an entry's `selector` may be. An entry is valid if it is a string and its `reason` is ≥ 80 characters (`:4826-4831`). So:

```python
InFlowIndicatorException(
    selector=".modal__form > .form-busy",
    reason="<80+ символов прозы>",
)
```

plus the matching CSS rule would pass **both** new gates while moving the indicator in all 18 confirmation sites — the exact outcome `test_the_confirmation_panel_indicator_keeps_its_accepted_place` was written to make impossible. The count assertion (`:4820-4825`) reds only until the author bumps `IN_FLOW_INDICATOR_EXCEPTIONS_DECLARED`, which is part of the same edit. The guard against touching the panel is therefore a prose reason a human must read, not a check.

This matters more than a hypothetical because the two gates were deliberately split so the panel one is independent; sharing a mutable trust-store re-couples them.

**Fix:** Constrain what an exception may address, and stop the panel gate from trusting the list blindly:

```python
# Исключение обязано адресовать ФОРМУ ОБЁРТКИ, и только её: перечень служит
# ещё и разрешением правила неподвижности панели, и запись, дотянувшаяся до
# колонки панели, отменила бы его молча.
for entry in IN_FLOW_INDICATOR_EXCEPTIONS:
    assert entry.selector.endswith(f" > .{INDICATOR_CLASS}"), ...
    assert PANEL_FORM_SELECTOR not in entry.selector, (
        f"исключение {entry.selector!r} адресует колонку формы панели: "
        f"перечень исключений обёртки разрешил бы правилу двигать все 18 "
        f"мест подтверждения"
    )
```

Better still, have `_offenders_panel_indicator_reach` build its allow-list from an explicit panel-safe constant rather than from the exceptions tuple, so the two lists move independently.

---

### WR-07: The footprint test's substitutions assert only "something went red", contradicting the discipline its own sibling test states verbatim

**File:** `tests/test_templates/test_htmx_markup_gates.py:4817-4835`

**Issue:** Both substitutions in `test_a_wrapped_form_gives_its_indicator_no_layout_footprint` assert truthiness of the offenders dict:

```python
    assert _offenders_wrapped_indicator_footprint(still_in_flow, sources), (...)
    ...
    assert _offenders_wrapped_indicator_footprint(_app_css(), without_scope), (...)
```

Its sibling `test_the_confirmation_panel_indicator_keeps_its_accepted_place` names the reason this is not enough, in the same file, eight lines later (`:4849-4852`): *«каждая подстановка обязана покрасить правило В ОЖИДАЕМОМ МЕСТЕ: ключ словаря сверяется, иначе „покраснело хоть на чём-то" сошло бы за доказательство»* — and it does check the key for all three of its substitutions (`:4877`, `:4900`, `:4912`).

`_offenders_wrapped_indicator_footprint` has four independent offender branches (macro tag, scope rule, indicator rule, exception rule). Today т1 reds only via the indicator branch, so the proof is sound *right now*; the moment any other branch also reds — for example if WR-05 comes true and the exception branch starts firing permanently — т1 and т2 become vacuous and keep asserting a tooth that is no longer being measured. A gate whose anti-vacuum proof can itself go vacuous is the shape this suite spends thousands of lines avoiding.

**Fix:**

```python
    still_in_flow_offenders = _offenders_wrapped_indicator_footprint(
        still_in_flow, sources
    )
    assert WRAPPED_INDICATOR_SELECTOR in still_in_flow_offenders, (
        f"у индикатора формы обёртки отняли вывод из потока, а правило назвало "
        f"не то место: {still_in_flow_offenders}"
    )
    ...
    without_scope_offenders = _offenders_wrapped_indicator_footprint(
        _app_css(), without_scope
    )
    assert WRAPPER in without_scope_offenders, (
        f"класс области сняли с тега формы макроса, а правило назвало не то "
        f"место: {without_scope_offenders}"
    )
```

## Info

### IN-04: `_offenders_panel_indicator_reach` enforces materially less than its docstring claims

**File:** `tests/test_templates/test_htmx_markup_gates.py:3305-3306`, `3343-3344`, `3359-3369`

**Issue:** The docstring promises *«ни одна часть селектора, достающая индикатор, не выходит за объявленное множество»* — no selector part **reaching the indicator** escapes the declared set. Two gaps between that claim and the code:

1. Only selectors that literally spell `.form-busy` are examined (`if f".{INDICATOR_CLASS}" not in part: continue`). A rule that reaches the panel's indicator structurally — `.modal__form > span`, `.modal__panel span[aria-hidden]`, `form > :last-child` — is invisible. The panel's indicator is the *last* child of `.modal__form`, so `:last-child` is not an exotic way to hit it.
2. Only the `position` property is checked on the two base rules (`:3359-3369`). Adding `float: right`, `margin-top: -8px`, `align-self: flex-end` or `display: none` to `.form-busy` would move or delete the indicator in all 18 confirmation sites with the gate green — despite the test being named "keeps its accepted place".

The substring test also has a mild false-positive edge: an unrelated future class such as `.form-busy-legend` contains `.form-busy` and would be reported as reaching the indicator.

**Fix:** Either narrow the docstring to the property actually enforced ("no rule **naming the indicator class** outside the declared set, and no `position` on the base rules"), or widen the check: compare on whole simple-selector tokens rather than substrings, and reject any *box-affecting* declaration on the two base rules, not just `position` — e.g. `{"position", "float", "align-self", "margin", "margin-top", "margin-bottom", "display"}` minus the ones the base rule legitimately owns.

---

### IN-05: The new contract literals are typed a second time in `test_components.py`, against the doctrine the same change writes down

**File:** `tests/test_templates/test_components.py:716-717`; `tests/test_templates/test_htmx_markup_gates.py:2885`, `5852`

**Issue:**

```python
WRAPPED_FORM_CLASS_MARKUP = 'class="form-wrapper"'
INDICATOR_NODE_MARKUP = '<span class="form-busy" aria-hidden="true"></span>'
```

Both already exist in the gates module — as `WRAPPED_FORM_CLASS_ATTR` (`:2885`) and `QUALITY_INDICATOR_NODE` (`:5852`). The gates module states the rule against exactly this at `:2887-2890`: *«Набираются ЗДЕСЬ из имён классов, а не литералами по месту: два написания одного селектора разъехались бы молча»*. Crossing a module boundary does not change the failure mode — it widens it: change the node in `form_wrapper.html` and one file reds while the other passes, or vice versa, and the reader has two "single sources of truth".

The same change makes the opposite choice for the Python side and explains why (`test_components.py:33-37`: the profile form is taken from `_settings_markup`, not re-rendered, because *«второй экземпляр сборки разошёлся бы с первым молча»*). The markup literals deserve the same treatment.

**Fix:** Put the three literals (`form-wrapper`, the class attribute, the indicator node) in one module both test files import — e.g. `tests/test_templates/contracts.py` — or import them from `test_htmx_markup_gates` where they already live.

---

### IN-06: `out.index(...)` kills the profile-scope test with a bare `ValueError`, bypassing its own failure messages

**File:** `tests/test_templates/test_components.py:750-755`

**Issue:**

```python
    at = out.index(INDICATOR_NODE_MARKUP)
    assert out.index(form) < at < out.index("</form>"), (...)
```

Every carefully written failure message in this test is bypassed if the indicator markup drifts by a single attribute (an added `data-*`, a reordered `aria-hidden`): `str.index` raises `ValueError: substring not found` with no mention of the property under test, and the reader sees a crashed test rather than "the profile form lost its indicator". Two further wrinkles: `out.index("</form>")` takes the **first** closing tag, so the assertion silently narrows if `_settings_markup` ever renders two forms; and `out.index(form)` is the index of the form tag's `<`, which makes the left half of the comparison near-unfalsifiable.

**Fix:**

```python
    assert INDICATOR_NODE_MARKUP in out, (
        f"отрендеренная форма профиля не печатает узел индикатора: правилу "
        f"«индикатор вне потока» нечего выводить из потока — {out!r}"
    )
    tag_end = out.index(form) + len(form)
    at = out.index(INDICATOR_NODE_MARKUP)
    assert tag_end < at < out.index("</form>", tag_end), (...)
```

---

### IN-07: Selector matching is whitespace-exact, so a reformatted stylesheet turns a correct rule into a false accusation

**File:** `tests/test_templates/test_htmx_markup_gates.py:3255-3258`, `3343-3348`

**Issue:** `_css_rules` strips only the leading/trailing whitespace of the selector text; the gates then compare with `==` against `WRAPPED_INDICATOR_SELECTOR = ".form-wrapper > .form-busy"`. Writing the same rule as `.form-wrapper>.form-busy`, or wrapping it across two lines (which a prettier/stylelint pass or a long selector would do), produces:

- `_offenders_wrapped_indicator_footprint`: `indicator is None` → *«правила индикатора В ОБЛАСТИ формы обёртки нет вовсе»*;
- `_offenders_panel_indicator_reach`: the reformatted selector is not in the allow-list → *«до узла индикатора дотягивается НЕОБЪЯВЛЕННЫЙ селектор… сдвиг приедет разом во все 18 мест подтверждения»*.

Both messages accuse the author of a defect that does not exist. The second is actively misleading: it names the panel regression as the consequence of what is only a whitespace change.

**Fix:** Normalise before comparing, in `_css_rules` or a small helper:

```python
def _normalised(selector: str) -> str:
    """Селектор без разницы в пробелах: `a > b`, `a>b` и перенос строки — одно."""
    return re.sub(r"\s*([>+~])\s*", r" \1 ", " ".join(selector.split()))
```

and route both the `==` comparisons and the allow-list membership through it.

---

## Carried forward from the 2026-09-17 full-phase review (not re-verified)

**These six findings were NOT re-examined in this pass.** They lie outside the incremental scope (`59398f2..HEAD` touches only the four files listed in the frontmatter), and none of them has been fixed since. They are reproduced here with their original IDs and substance so that rewriting this file does not delete them from the project's record. Their presence below is **carriage, not re-confirmation** — do not read any of them as re-verified on 2026-09-18.

Original pass: 2026-09-17T09:01:18Z, depth `standard`, `diff_base` df26e76, 68 files.

### WR-01 (carried): `POST /ads/new` still sends an unbounded `ad_id` to SQL, so it returns a 500. The handler was converted this phase and `id_in_column` exists.

**File:** `app/pages/ads.py:698-708`
**Issue:** `ads_create` parses the form string with `requested_id = int(ad_id)` and uses it directly in `select(Ad).where(Ad.id == requested_id, ...)`. There is no range check. `ad_id=99999999999999999999999999` raises `OverflowError` on SQLite / `DataError` on asyncpg, which is a 500. The suite has recorded this with `verdict="open"` since 2026-09-08 (`tests/test_pages/test_identifier_bounds.py:1530-1548`).

Phase 11 did three things around this:
- converted this exact handler onto `respond()`;
- introduced `id_in_column` precisely so that out-of-column POST identifiers take the "row missing" branch (D-07);
- added `test_every_post_identifier_is_checked_before_its_first_use`.

That gate only recognises the `Post*` aliases, so a `str` parameter coerced inside the body is invisible to it. The phase's own invariant ("first use of a POST identifier is `id_in_column`") is therefore false for one POST input, and the gate stays green. Worse, the 500 lands on the htmx transport as a banner, not as the `_inaccessible` fragment that every other "not yours / not there" case gets.
**Fix:**
```python
    try:
        requested_id = int(ad_id)
    except ValueError:
        requested_id = None
    if requested_id is not None and id_in_column(requested_id):
        ad = (
            await db.execute(
                select(Ad).where(Ad.id == requested_id, Ad.user_id == user.id)
            )
        ).scalar_one_or_none()
```
Then flip the appendix entry to closed. Better still, widen `_first_use_is_checked` to also cover `int(<param>)` coercions of `str` form fields, so the next one is caught.

### WR-02 (carried): Schedule creation picks fragment vs `HX-Location` from the server count, but the form's swap target was frozen when the page rendered. A stale editor silently drops the new card.

**File:** `app/pages/schedules.py:1125-1132`, `app/templates/ads/form.html:203-249, 276-278`
**Issue:** The editor prints the create form with `target='#sched-list' if editor.schedules else none`. With no target, `form_wrapper` emits `hx-swap="none"`. `#sched-list` and `#sched-count` exist only inside `{% if editor.schedules %}`. The handler decides the response shape from `_ad_schedule_count(...) == 1`, i.e. the database after the insert, not from what the requesting document contains.

When the two disagree, the user sees nothing. For example: an editor opened at zero schedules while another tab or session already added one, so the server count is 2. The server returns the card fragment. htmx swaps it nowhere (`hx-swap="none"`), and the OOB `innerHTML:#sched-count` has no target (`htmx:oobErrorNoTarget`). The schedule is committed, but the page still shows the empty state and "+ ДОБАВИТЬ ПЕРВОЕ". The next click creates a duplicate. The code comment explicitly calls "a button that does NOTHING and says nothing" the failure this conditional target was meant to prevent; this path brings it back from the server side.
**Fix:** Let the client tell the server whether an insertion target exists, instead of inferring it. For example, add a hidden `<input type="hidden" name="has_list" value="1">` only when `editor.schedules` is truthy, and branch on it:
```python
    list_on_screen = form_data.get("has_list") == "1"
    if not list_on_screen:
        return await respond(request, redirect=screen_url)
```
The value only selects between two server-built responses of the same outcome, so it grants nothing. Alternatively, keep the count check but also require the flag, so either signal falls back to `HX-Location`.

### WR-03 (carried): Fragment builders run after `commit()` and crash when the row is gone, giving a 500 after a successful write.

**File:** `app/pages/schedules.py:1158, 1338, 1525-1530, 1558`
**Issue:** Every deferred fragment re-reads the record it just wrote and assumes it is still there:
- `card = next(s for s in editor["schedules"] if s.id == ...)` has no default. Inside a coroutine, the `StopIteration` becomes `RuntimeError: coroutine raised StopIteration`.
- `_row_fragment` does `row = (...).first()` and then `row.Schedule` (`AttributeError` on `None`).

If the schedule or its ad is deleted between the commit and the fragment read (a second tab, an admin deleting the user, or `delete_account`), the request answers 500 although the toggle, update or create was already committed. `schedules_toggle` (lines 1398-1401) cites the WR-07 rule that "a 500 after a completed write is indistinguishable from nothing happened". These builders reintroduce exactly that on the htmx path.
**Fix:** Fall back to the degradation address when the re-read comes back empty:
```python
        card = next((s for s in editor["schedules"] if s.id == schedule_id), None)
        if card is None:
            return location_response(screen_url)  # or restructure so respond() chooses
```
For `_row_fragment`, add `if row is None: return location_response(screen_url)`. Since `respond()` calls the builder itself, the cleanest version reads the row before calling `respond()` and passes `fragment=None` when it is missing.

### IN-01 (carried): The HTTP hostile-phone test cannot go red for the property it names

**File:** `tests/test_pages/test_max_connect_transport.py:208-224`
**Issue:** `test_a_hostile_phone_never_reaches_the_response_raw` posts `HOSTILE_PHONE`, which is not blank, so the request takes the success/QR branch. That branch never prints the phone at all (`_max_step_markup(step="qr", ...)` gets no `phone`). The assertion passes whether or not escaping works. The echo channel (the 422 branch) is only reachable over HTTP with whitespace-only values, and those cannot carry markup. The real proof is the unit test `test_the_phone_echo_is_autoescaped_in_the_step_markup`.
**Fix:** Delete the HTTP test, or rename it to say what it really checks ("the success step does not reflect the phone"), and add a positive check that the phone value is absent from the QR step.

### IN-02 (carried): Schedule-partial test URLs still send the removed `offset` cursor

**File:** `tests/test_pages/test_responsive_markup.py:3373, 4401`
**Issue:** `/schedules/partial` switched from `offset` to `after_id` this phase (`app/pages/schedules.py:811`). These tests still request `?offset=0&limit=30`. FastAPI ignores the unknown parameter, so the tests pass by accident and describe a contract that no longer exists.
**Fix:** Use `/schedules/partial?limit=30`, or pass `after_id`, in both places.

### IN-03 (carried): `redirect_external` promises "never a 500" but only catches `ValueError`

**File:** `app/pages/htmx.py:383-391`
**Issue:** The docstring says a failed check yields "a loud log line and a transition with a code, not a 500". `_confirmation_url` and `_host_for_the_journal` handle only `ValueError`. A non-`str` `url` (for example `None` from an unexpected SDK payload) raises `TypeError` in the first `any(ord(char) ...)` loop and escapes as a 500 after the payment intent was created.
**Fix:** Guard the type first: `if not isinstance(url, str): raise ValueError(...)` at the top of `_confirmation_url`, and make `_host_for_the_journal` return `None` for non-`str` input.

---

_Reviewed: 2026-09-18 (incremental, `diff_base` 59398f2)_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
_Carried unchanged from the 2026-09-17T09:01:18Z full-phase pass: WR-01, WR-02, WR-03, IN-01, IN-02, IN-03 — not re-verified_
