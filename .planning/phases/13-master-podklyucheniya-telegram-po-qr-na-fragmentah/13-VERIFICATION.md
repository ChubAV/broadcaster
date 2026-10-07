---
phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah
verified: 2026-10-07T11:08:19Z
status: passed
score: 32/32 must-haves verified
covered_files:
  - ".planning/REQUIREMENTS.md"
  - ".planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-01-PLAN.md"
  - ".planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-01-SUMMARY.md"
  - ".planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-02-PLAN.md"
  - ".planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-02-SUMMARY.md"
  - ".planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-03-PLAN.md"
  - ".planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-03-SUMMARY.md"
  - ".planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-04-PLAN.md"
  - ".planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-04-SUMMARY.md"
  - ".planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-05-PLAN.md"
  - ".planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-05-SUMMARY.md"
  - ".planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-06-PLAN.md"
  - ".planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-06-SUMMARY.md"
  - "app/messengers/telegram_user.py"
  - "app/pages/accounts.py"
  - "app/templates/accounts/connect_tg_user.html"
  - "app/templates/accounts/includes/tg_connect_step.html"
  - "tests/test_messengers/test_telegram_user.py"
  - "tests/test_pages/test_htmx_gates.py"
  - "tests/test_pages/test_htmx_post_pairs.py"
  - "tests/test_pages/test_hx_location_destinations.py"
  - "tests/test_pages/test_identifier_bounds.py"
  - "tests/test_pages/test_impersonation_gate.py"
  - "tests/test_routes/test_tg_user_auth.py"
  - "tests/test_templates/test_components.py"
  - "tests/test_templates/test_htmx_inventory.py"
  - "tests/test_templates/test_htmx_markup_gates.py"
  - "tests/test_templates/test_htmx_markup_security.py"
covered_digest: "v3:sha256:044a69e9568e35710ad4fb6004c4d548c9800c5264a590d1d405768c39fc6e35"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 31/32
  previous_verified: 2026-09-21T17:40:19Z
  previous_digest: "v1:sha256:0e9da87d16a12f09ae221a56ad3c6af20dd9c50988419fdc0513d4c1da972390"
  reason: >-
    `verification.status` читался `stale`: покрытые файлы вердикта 2026-09-21 (последняя запись
    отчёта — коммит a8152440) позднее правили фазы 14–15 и перенумерация угроз 970ce74f. Сама
    фаза 13 повторной работы не получала. Раунд меряет СЕГОДНЯШНЕЕ дерево (ветка фазы,
    перемотанная на origin/master, HEAD ced8f8fa) и отделяет чужие правки от кода фазы. Отдельно
    и впервые замерен шаблон шага после быстрой задачи 260921-qvt: прошлый раунд держал его
    вердикт на подтверждении владельца, а не на замере.
  landed_since:
    - "a674e8e5 (15-09), 5a95c970 (15-21) — app/pages/accounts.py: +14 строк, ТОЛЬКО комментарии-летописи `page_size` в обработчиках СПИСКА аккаунтов (`accounts_partial` :171-177, `accounts_list` :213-219). Код мастера не тронут; строки мастера сдвинуты на +14 (обработчики теперь :225-629)"
    - "970ce74f — 13-02/03/04/05-PLAN.md: по одной строке `<threat_model>` перенумерованы (T-13-04→T-13-19, T-13-07→T-13-20, T-13-07→T-13-21, T-13-10→T-13-22). Должные истины, артефакты, ключевые связи и запреты планов не тронуты"
    - "шесть покрытых гейтовых модулей (фазы 14–15): правил, касающихся мастера, не снято ни одного. `NOT_YET_CONVERTED_COUNT` 10 → 0 (Фаза 14 перевела авторизацию); фаза 15 ВПИСАЛА четыре обработчика мастера в реестр дуальных обработчиков и решений `hx-push-url` (d992926d); `HX_LOCATION_DESTINATION_CALLS_DECLARED` 77 → 81 по записям фаз 14–15; `TOP_LEVEL_BINDING_EXEMPT_TEMPLATES` остался именованным нулём; в test_components.py сведён дубль разборщика `_split_top_level` (15-18), без связи с мастером"
    - ".planning/REQUIREMENTS.md — записи фаз 14–15; строки FETCH-02 после a8152440 не тронуты (её `[x]` / `Complete` поставило закрытие фазы ab72d228)"
    - "ВНЕ этого диапазона, но не замеренное прошлым раундом: 260921-qvt (85e84ca3, aaaee309, 2026-09-21 19:50 — ПОСЛЕ обхода 18:05–19:15) правил tg_connect_step.html (+24/−6) и app.css. Замерено в этом раунде, раздел «Прямой замер шаблона шага после 260921-qvt»"
  gaps_closed: []
  gaps_remaining: []
  regressions: []
  score_change: "31/32 → 32/32: критерий 4 (живой сценарий) закрыт обходом 13-UAT.md 2026-09-21 (status: complete, 5/5 pass) и в этом раунде засчитан как прямое наблюдение. Перенос наблюдения на сегодняшнее дерево ИЗМЕРЕН: обработчики мастера, слой сессий, form_wrapper и вендоренный htmx с дерева обхода не менялись; шаблон шага изменился только выкладкой (сигнатура интерактивных атрибутов семи отрисовок совпадает с деревом обхода)"
deferred: # owner-named deferrals, not later-phase coverage — neither item is claimed by any later phase

  - truth: "IN-03 — abandoned QR sessions keep a connected (possibly authorized) Telethon client"
    addressed_in: "владелец"
    evidence: "13-CONTEXT.md §Deferred Ideas: «Закрытие Telethon-клиента при уходе со страницы / «Отмене» — сегодня клиент живёт до чистки по сроку. Отдельная работа.»; D-13 bounds the session-layer edit; pre-existing (reviewer agrees)"
  - truth: "UI-17 — «Ошибка запуска QR авторизации: {e}» shows raw exception text"
    addressed_in: "владелец"
    evidence: "13-CONTEXT.md §Landmines: «Текст переезжает дословно, решение о нём — не предмет фазы»; D-09 moved refusal texts verbatim"
advisory:

  - finding: "WR-01 — refresh_qr «only from qr_expired» guard is check-then-await; two concurrent owner refreshes both call recreate()"
    category: other
    reason: "Real under concurrency (telegram_user.py:162-178: status flips to waiting only after `await recreate()`). Reachable only by the session OWNER (two tabs on one session_id, replay, no-JS resubmit); htmx `hx-disabled-elt` covers the single tab. Worst case: the rendered QR is the earlier of two tokens. Does not defeat criteria 2/3/4. Fix: claim the transition synchronously before the await (reviewer's patch), map the interim status to 204."
    evidence_status: "code reading; not reproduced by a test"
  - finding: "WR-02 — asyncio.TimeoutError branch classifies a post-scan timeout (DC migration / export request) as qr_expired"
    category: other
    reason: "Confirmed against Telethon 1.42.0 source: QRLogin.wait() awaits `self._client(self._request)` and `_switch_dc()` AFTER the event, and those can raise TimeoutError. Before the phase such a timeout surfaced as «Ошибка авторизации»; now as «QR-код истёк» → refresh on a half-switched client. Rare (scan + other-DC account + network timeout); the main criterion-4 path is unaffected. Fix: compare against qr_login.expires before classifying (reviewer's patch)."
    evidence_status: "library source read; no test reproduces it"
  - finding: "WR-03 — complete_auth pops/disconnects before _save_tg_account commits; a commit failure loses the scan and returns 500"
    category: other
    reason: "Real, but the pop-then-commit order is pre-existing: the removed POST /complete route (base 344dc789) did `complete_auth` then `db.commit()` identically. The phase moved it into one helper; the 500 now raises the global banner instead of a JSON error. Pop-before-persist is what gives one account per scan. Fix: wrap the save, rollback, answer the error step, log without the session string."
    evidence_status: "code reading + git show 344dc789"
  - finding: "WR-04 — the two ROUTE race tests do not discriminate the reorder mutant; the one-account property is held by the unit rule only"
    category: other
    reason: "Re-measured by this verifier with a scratch pytest plugin (disconnect moved before pop, patched in the session layer, the page module and the unit test's own binding): unit `test_concurrent_completes_yield_one_session_string` RED 3/3; `test_two_concurrent_password_submits_save_one_account` GREEN 3/3; `test_two_concurrent_polls_after_success_save_one_account` GREEN 5/6 (one incidental red). Unmutated control: 3 passed. The PROPERTY holds (code: no await between `_owned` check and `pop`; the handlers reach complete_auth with no yield after get_qr_status; unit rule discriminates), so the D-01 truths of 13-02/13-04 are VERIFIED. What is false is the plans'/docstrings' claim that the ROUTE tests prove it. Fix: rendezvous at get_qr_status in the poll race; yielding `disconnect` in the 2FA seed."
    evidence_status: "mutant runs in this verification"
  - finding: "IN-01 — ValueError/RuntimeError branches in verify-2fa catch unrelated Telethon errors and echo their text"
    category: other
    reason: "Real (accounts.py:563-567): a Telethon ValueError from compute_check would render as a 422 field error with internal text. Not the password; does not breach the no-echo prohibition. Fix: a dedicated WrongPassword exception."
    evidence_status: "code reading"
  - finding: "IN-02 — submit_2fa does not enforce needs_2fa at the session layer"
    category: other
    reason: "Real asymmetry (telegram_user.py:186-202); the only caller checks needs_2fa right before calling. Defensive hardening for future callers."
    evidence_status: "code reading"
  - finding: "UI-1 — 2FA step: 0px between the password field and «Подтвердить» (regression)"
    category: other
    reason: "Confirmed from markup+CSS: pre-phase field and actions were direct children of the 14px-gap `.connect-step`; now inside `form.form-wrapper` (only `position: relative`, app.css:2207), `.field` has no margin, and `.connect-step__form` (app.css:1934, used by MAX) is not applied. A phase-introduced visual regression; does not defeat any success criterion. Recommend fixing with the `.connect-step__form` wrapper before or with the UAT."
    evidence_status: "rendered-markup/CSS reading"
  - finding: "UI-2 — qr_expired: «Обновить QR-код»/«Отмена» left-aligned under centred text (regression)"
    category: other
    reason: "Confirmed from CSS: `.connect-step > form { align-self: stretch }` + `.connect-step__actions` without justify-content. Pre-phase the row sat directly in the centred column. Visual only."
    evidence_status: "CSS reading"
  - finding: "UI-3 — start/refresh lost the «Загрузка...» label (regression)"
    category: other
    reason: "Confirmed: base template script line 101 `setBtnLabel(btn, 'Загрузка...')`; now only a disabled button and the form-busy dot. Feedback degraded, not absent; does not defeat the goal."
    evidence_status: "git show 344dc789 + template reading"
  - finding: "UI-4 — scanning instruction shown on start/error, not on the waiting step"
    category: other
    reason: "Pre-existing (old #start-section carried the same text); copy improvement."
    evidence_status: "template reading"
  - finding: "UI-6 — qr_expired has no status colour treatment"
    category: other
    reason: "Design consistency; no criterion touches it."
    evidence_status: "template reading"
  - finding: "UI-7 — no typographic hierarchy between state message and instruction"
    category: other
    reason: "Design polish; shared style is pre-existing."
    evidence_status: "template reading"
  - finding: "UI-8 — waiting: ~28px doubled gap around the zero-height poller form"
    category: other
    reason: "Minor spacing side effect of the poller form being a flex item; fix by moving the poller after the actions row."
    evidence_status: "CSS reading"
  - finding: "UI-9 — #tg-connect-step has no aria-live"
    category: other
    reason: "Accessibility improvement; the MAX wizard has the same gap, so not a phase regression."
    evidence_status: "template reading"
  - finding: "UI-10 — password step does not take focus when swapped in"
    category: other
    reason: "Real (no autofocus); pre-phase script did not focus either. UX improvement."
    evidence_status: "template reading"
  - finding: "UI-11 — «Начать заново» is a dead end for «API не настроен»"
    category: other
    reason: "Text bound by D-09; the action beside it could be hidden for non-retryable errors."
    evidence_status: "template reading"
  - finding: "UI-12 — near-synonyms «Сессия подключения не найдена» / «Сессия авторизации истекла»"
    category: other
    reason: "Deliberate per D-04 (owner-only «истекла» vs unknown/foreign «не найдена» — the difference must exist so the foreign answer equals the unknown answer). No action recommended."
    evidence_status: "13-CONTEXT D-04"
  - finding: "UI-13 — no step orientation («шаг N из M»)"
    category: other
    reason: "Consistent with the MAX wizard; enhancement."
    evidence_status: "template reading"
  - finding: "UI-14 — stale CSS comment app.css:1925-1927 and dead `.connect-step[hidden]` rule"
    category: other
    reason: "Checked for criterion 1: nothing toggles `hidden` any more — no `hidden` attribute on any element in app/templates/accounts/ except `type=\"hidden\"` inputs, no script on the page, no JS in app/static/js touching connect steps. The rule is dead residue, the comment is false; criterion 1 holds. Cleanup only."
    evidence_status: "grep over templates and static js"
  - finding: "UI-15 — no «Отмена» on the password step"
    category: other
    reason: "Pre-existing; header «К аккаунтам» remains an exit."
    evidence_status: "git show 344dc789"
  - finding: "UI-16 — autocomplete='off' on the password field"
    category: other
    reason: "Carried verbatim from the pre-phase template; `current-password` would be better."
    evidence_status: "git show 344dc789"
previous_round_closed_items:
  note: "Закрыты обходом 2026-09-21 (13-UAT.md: status complete, 5/5 pass, расхождений 0; пункты 1, 2, 4 — подтверждением владельца, пункты 3 и 5 — дословными словами владельца). Перенесены сюда из ключа `human_verification` верхнего уровня дословно (отступ +2), по форме 12-VERIFICATION.md: при `status: passed` открытых пунктов ручной проверки у отчёта нет. Позднейшие правки путей под пунктами 1–4 измерены в разделе «Прямой замер шаблона шага после 260921-qvt»."
  human_verification:

    - test: "Criterion 4a — scan without 2FA: open /accounts/connect/tg_user, «Начать подключение», scan in Telegram (Настройки → Устройства → Подключить устройство)"
      expected: "QR appears without reload; screen switches to «Подключено» by itself; one tg_user account on the list; uvicorn log shows no further POST …/qr-status after «Подключено»"
      why_human: "Needs a real Telegram account and phone; the Telegram server is not substitutable; live browser requires owner consent (workflow.live_dom_uat: false)"
    - test: "Criterion 4b — account with 2FA: scan, enter a wrong password, then the right one"
      expected: "Wrong → stays on the password step, «Неверный пароль 2FA.» at the field, field empty; right → «Подключено», one account"
      why_human: "Live Telethon session with a 2FA password"
    - test: "Criterion 4c — expired code: get a QR and do NOT scan for ≥ ~30 s, then press «Обновить QR-код» and scan the new code"
      expected: "Screen shows «QR-код истёк. Обновите его, чтобы продолжить.» by itself (no «Ошибка авторизации»); refresh shows a new QR and polling resumes; scanning it reaches «Подключено». While on the qr_expired step, note whether the card-height jump (UI-5) is acceptable."
      why_human: "Token lifetime is set by Telegram (~30 s); host clock must be NTP-synced. UI-5 is a visual judgement only a live look settles."
    - test: "Criterion 4d — whole-session expiry: reach «код истёк», wait ≥ 270 s more, press «Обновить QR-код»"
      expected: "Error step «Сессия авторизации истекла. Начните заново.» with the «Начать заново» form"
      why_human: "Needs ≥ 5 minutes of real session time against a live Telethon client"
    - test: "Prohibitions (8 items, all `verification: none` in the plans) — confirm or reject the verifier's non-authoritative verdicts listed in the report section «Prohibitions»"
      expected: "Owner accepts each verdict (all eight judged HOLDING by the verifier) or names the one that does not hold"
      why_human: "Prohibitions carry no wired test enforcement; the verifier's reading is an LLM judgement and must not silently pass (ADR-550 D4)"
---

# Phase 13: Мастер подключения Telegram по QR на фрагментах — Verification Report (вторая верификация: ре-верификация закрытой фазы на пост-вехном дереве)

**Phase Goal:** мастер подключения работает на HTML-фрагментах с состоянием на сервере — без `setInterval`, без пяти JSON-контрактов и без ручного переключения `hidden`
**Verified:** 2026-10-07T11:08:19Z
**Status:** passed
**Re-verification:** Да. Вердикт 2026-09-21 (`passed`, 31/32, `v1:sha256:0e9da87d…`) читался `stale`, потому что покрытые файлы позднее правили фазы 14–15 и перенумерация угроз 970ce74f. Дерево: ветка `gsd/phase-13-master-podklyucheniya-telegram-po-qr-na-fragmentah`, перемотанная на `origin/master`, HEAD `ced8f8fa`.

## Итог раунда 2026-10-07

**Цель фазы на сегодняшнем дереве достигнута, и держит её код фазы 13, а не чужие правки.**
Слой сессий `app/messengers/telegram_user.py` и страница `connect_tg_user.html` не получили ни
одного коммита после `bff29f7a` (дерево первой верификации). Как и `form_wrapper.html` и
вендоренный `htmx.min.js`. В `app/pages/accounts.py` после `a8152440` прибавились 14 строк, и все
они комментарии в обработчиках СПИСКА аккаунтов (`accounts_partial`, `accounts_list`), вне мастера.
Измерено диффом, а не взято из сводки. Поэтому строки мастера сдвинулись на +14, и ссылки этого
раунда даны по сегодняшней нумерации.

**Шаблон шага после быстрой задачи 260921-qvt замерен впервые.** Прошлый раунд держал вердикт по
этому файлу на подтверждении владельца. Замер такой:

- правка касается только выкладки;
- последовательность интерактивных атрибутов во всех семи отрисовках шага побайтно равна дереву
  обхода (`hx-*`, `action`, `name`, `type`, `value`, `id`);
- опросчик остался ровно один и только в ветке ожидания;
- скрипта и атрибута `hidden` не прибавилось.

**Счёт вырос с 31/32 до 32/32, и это не пересчёт по вкусу.** Единственный незасчитанный пункт
прошлого раунда, критерий 4 (живой сценарий), закрыт обходом `13-UAT.md` 2026-09-21: `status:
complete`, пять `pass`, расхождений ноль. Обход шёл ДО быстрой задачи (18:05–19:15 против 19:50).
Поэтому перенос наблюдения на сегодняшнее дерево здесь измерен, а не допущен (раздел ниже). Форма
закрытия названа как есть: пункты 1, 2 и 4 обхода закрыты подтверждением владельца, а не дословным
описанием признака (ключ `unrecorded` шапки обхода).

**Открытым остаётся то же, что было открыто.** Это 18 советующих записей, по которым код не
менялся (WR-01…WR-04, IN-01, IN-02, UI-4, UI-6…UI-16), и две отсрочки владельца (IN-03, UI-17). Ни
одна поздняя фаза их не взяла. UI-1, UI-2 и UI-3 закрыты быстрой задачей 260921-qvt, и сегодня это
подтверждено замером.

## Что легло под фазу 13 после a8152440

| Покрытый файл | Коммиты | Что изменилось | Задевает истину фазы 13? |
|---|---|---|---|
| `app/pages/accounts.py` | a674e8e5 (15-09), 5a95c970 (15-21) | +14 строк комментариев-летописей `page_size` (:171-177, :213-219) | **Нет.** Ни одной строки кода; диапазон мастера :225-629 побайтно прежний, только сдвинут |
| `tests/test_pages/test_htmx_gates.py` | фазы 14–15 | +2124/−20. `NOT_YET_CONVERTED_COUNT` 10 → 0 (из перечня ушли десять обработчиков `auth.py`, ни одного обработчика мастера); четыре обработчика мастера вписаны в `DUAL_BRANCH_HANDLERS` и в реестр решений `hx-push-url` (15-11) | **Нет ослабления.** Предмет мастера стал охвачен ШИРЕ |
| `tests/test_pages/test_htmx_post_pairs.py` | фазы 14–15 | +751/−14. Снятые строки: обращения к опустевшему `NOT_YET_CONVERTED` и утверждение 302 правила пар, которое 14-02 ПЕРЕНЁС внутрь ветви «не смена экрана» тем же текстом | **Нет.** Правил мастера не снято; 302-утверждение для мастера (не `SCREEN`) действует как прежде |
| `tests/test_pages/test_hx_location_destinations.py` | 14-06, 15-16 | `HX_LOCATION_DESTINATION_CALLS_DECLARED` 77 → 79 → 81 с летописями; `/admin` в карте | **Нет.** `TOP_LEVEL_BINDING_EXEMPT_TEMPLATES = {}` — именованный ноль 13-05 на месте (:578) |
| `tests/test_templates/test_components.py` | 15-18 | дубль разборщика `_split_top_level` сведён к общему (с летописью) | **Нет.** Летопись Фазы 13 о строкознающем разборщике не тронута |
| `tests/test_templates/test_htmx_inventory.py` | фаза 15 | +531/−0: запрет `test_no_manual_fetch_remains` (FETCH-03) | **Усиление.** То, что 13-06 называл «предметом Фазы 15», теперь правило; `MANUAL_FETCH_PLACES = 0`, `POLLING_FRAGMENTS = 10` |
| `tests/test_templates/test_htmx_markup_gates.py` | фазы 14–15 | +2349/−4. Снятые строки — три объявленных числа, переписанные вверх (`MACRO_DEFINITION_SITES_CALLERS_DECLARED` 24 → 32, `PARAMETRIC_SWAP_TARGETS_CALLERS_DECLARED` 9 → 16, `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` 19 → 29), и `DEGRADATION_MARKERS`, переписанный многострочным множеством | **Нет.** Ни одна снятая строка не называет мастер |
| `13-02/03/04/05-PLAN.md` | 970ce74f | по одной строке `<threat_model>`: T-13-04→19, T-13-07→20, T-13-07→21, T-13-10→22 | **Нет.** Блоки `must_haves` планов не тронуты (замер диффом) |
| `.planning/REQUIREMENTS.md` | фазы 14–15 | записи фаз 14–15 | **Нет.** Строки FETCH-02 после a8152440 не тронуты |

Вне диапазона a8152440, но мимо прошлого замера: `tg_connect_step.html`, правка 260921-qvt (следующий раздел).

## Прямой замер шаблона шага после 260921-qvt

**Дифф `bff29f7a..HEAD` по `tg_connect_step.html`** (два коммита: `85e84ca3`, `aaaee309`) состоит из
трёх правок:

- в ветке `password` поле и ряд действий обёрнуты в `<div class="connect-step__form">`;
- в рядах действий веток `qr_expired` и старт/ошибка добавлена подпись `<span class="connect-step__busy">Загрузка...</span>`;
- добавлены два абзаца комментария.

Аргументы `form_wrapper(...)` и `field(...)` не изменились. Опросчик ветки ожидания (:59-62) не тронут.

**Сигнатура отрисовок.** Это скретч-скрипт, файлов проекта он не правит. Скрипт отрисовал старый
шаблон (`git show bff29f7a:…`) и сегодняшний в одном окружении шаблонов приложения. Отрисовок семь:
`start`, `error`, `waiting`, `qr_expired`, `password`, `password` с ошибкой поля и `connected`.
Затем он сравнил упорядоченную последовательность атрибутов `hx-*|action|method|name|type|value|id`.

| Шаг | Атрибутов | Совпадает с деревом обхода | `hx-trigger="every` | `<script` | атрибут `hidden` (не input) | подпись `connect-step__busy` |
|---|---|---|---|---|---|---|
| start | 8 | ✓ | 0 | 0 | 0 | 1 |
| error | 8 | ✓ | 0 | 0 | 0 | 1 |
| waiting | 10 | ✓ | **1** | 0 | 0 | 0 |
| qr_expired | 11 | ✓ | 0 | 0 | 0 | 1 |
| password | 15 | ✓ | 0 | 0 | 0 | 0 |
| password + ошибка | 15 | ✓ | 0 | 0 | 0 | 0 |
| connected | 0 | ✓ | 0 | 0 | 0 | 0 |

Итог: `TOTAL DIFFS 0`. Подпись `Загрузка...` показывает CSS по атрибуту `disabled` кнопки отправки
(`app.css:2036-2037`, `display: none` по умолчанию). Это стиль, а не ручное переключение `hidden`,
поэтому критерий 1 не задет. Правило `tests/test_templates/test_tg_connect_step_layout.py`
(10 проверок) зелено.

**Что ещё лежит под живым наблюдением критерия 4, и не изменилось ли оно с дерева обхода.**

- `telegram_user.py`: 0 коммитов после `bff29f7a`.
- `components/`: 0 коммитов.
- `htmx.min.js`: 0 коммитов.
- `app/pages/htmx.py` (слой ответа): правили 14-01 и 14-02. Тело `respond_field_error` переехало в
  общий помощник `_respond_by_transport`, а контракт 422 прежний. Путь неверного пароля 2FA
  (пункт 4b обхода) идёт через этот выход, и его маршрутные правила зелены сегодня:
  `test_a_wrong_password_answers_422_at_the_field_without_echo` и `test_verify_2fa_degrades_and_requires_a_session`.
- `base.html`: правил 14-06, только форма возврата из-под имперсонации. Мастера правка не касается.

Отсюда вывод: наблюдение обхода переносится на сегодняшнее дерево. Перенос опирается на замер, а не
на подтверждение владельца.

## Goal Achievement

### Roadmap Success Criteria (с летописями 13-06; тексты критериев побайтно равны базе `344dc789`)

| # | Критерий | Статус | Улика на сегодняшнем дереве |
|---|---|---|---|
| SC1 | Пять `fetch()` исчезли вместе с `setInterval` и ручным `hidden`; маршруты отдают HTML-фрагменты. **Летопись:** четыре маршрута, `complete` снят D-01, опрос GET → POST | ✓ VERIFIED | `grep -rn 'fetch(' app/templates/ \| wc -l` → `0`. `setInterval` в шаблонах и своём JS нет. Страница — якорь + включение, без `<script>` и `onclick`. `hidden` в шаблоне шага — только три `type="hidden"` поля `session_id`. Живая таблица маршрутов: `GET /accounts/connect/tg_user`, `POST` start-qr / qr-status / refresh-qr / verify-2fa; `complete` нет. В `accounts.py` нет `JSONResponse` и `json`. Правила `test_the_wizard_page_carries_no_client_script` и `test_the_complete_route_and_the_get_poll_are_gone` зелены сегодня |
| SC2 | Опрос ведётся `hx-trigger` и останавливается ответом без него; у каждого `every`-фрагмента есть пара. **Летопись:** доказан правилом на ответах | ✓ VERIFIED | Опросчик — только в ветке `waiting` (сигнатура выше). `test_polling_stops_by_a_response_without_trigger` × 20. Замыкающие `test_every_wizard_step_is_reached_by_a_polling_case` и `test_every_polling_fragment_has_a_terminal_pair` плюс шесть `test_control_*` зелены. Ветки шаблона разбираются из ТЕКСТА шаблона, поэтому правка 260921-qvt тоже прошла через замыкание |
| SC3 | Состояние на сервере, `session_id` скрытым полем, проверка владения. **Летопись:** проверка ЗАВЕДЕНА | ✓ VERIFIED | `QRAuthState.user_id: int` без умолчания (`telegram_user.py:36`). `_owned` (:119) стоит первой строкой `get_qr_status` (:134), `refresh_qr` (:156), `submit_2fa` (:189), `complete_auth` (:216). Обработчики передают `user.id` (`accounts.py:409, 492, 568`). Три `test_a_foreign_*_is_answered_as_unknown_and_leaves_no_trace` и четыре модульных правила владения зелены |
| SC4 | Живой сценарий: сканирование, обновление истёкшего кода, 2FA (ручной UAT) | ✓ VERIFIED (прямое наблюдение) | `13-UAT.md` 2026-09-21: `status: complete`, `checks_declared: 5`, пять `pass`, расхождений 0. Пункты 1, 2 и 4 закрыты подтверждением владельца, без дословного признака; обязательная клетка 1.4 названа в `unrecorded`. Перенос на сегодняшнее дерево измерен (раздел выше). Прошлый раунд: `? HUMAN` |
| SC5 | Записано прямо: деградации без JS нет и сегодня | ✓ VERIFIED | `git show 344dc789:app/templates/accounts/connect_tg_user.html \| grep -c '<form'` → `0`. Раздел «Критерий 5» в `13-06-SUMMARY.md:126` на месте. `test_the_wizard_degrades_to_its_page_without_js` зелено. ℹ️ О дрейфе команды летописи — в «Anti-Patterns» |

### Plan Must-Have Truths (дедуплицированы против SC)

| # | Истина (план) | Статус | Улика сегодня |
|---|---|---|---|
| 1 | start-qr → 200, шаг ожидания: QR data-URI, ровно один опросчик, скрытый `session_id`, якоря во фрагменте нет (13-01) | ✓ VERIFIED | `_waiting` (`accounts.py:366-370`); сигнатура `waiting` = дереву обхода; `test_the_wizard_walks_from_start_to_connected` |
| 2 | qr-status в `waiting` → 204, пустое тело (13-01) | ✓ VERIFIED | `_unchanged` (:414-416); запись `POLLING_CASES` |
| 3 | Первый опрос на `success` зовёт `complete_auth`, сохраняет один аккаунт, отвечает «Подключено» без триггера (13-01) | ✓ VERIFIED | :424-428; `test_a_second_poll_after_success_does_not_save_again` в прогоне |
| 4 | Прочие исходы — фрагмент без триггера с алертом и «Начать заново»; тексты дословно (13-01) | ✓ VERIFIED | константы `TG_*_MESSAGE` (:247-258) не менялись; правила отказов старта зелены |
| 5 | Без JS — 302 на мастер; без сессии — `/login`; JSON нет (13-01) | ✓ VERIFIED | `respond(…, redirect=…)` на каждом выходе; `test_the_wizard_degrades_to_its_page_without_js`, `test_the_wizard_without_a_session_goes_to_login` |
| 6 | Перечни гейтов сдвинуты прогоном (13-01) | ✓ VERIFIED | Сегодня `NOT_YET_CONVERTED_COUNT = 0`: Фаза 14 сдвинула его 10 → 0 своими прогонами. `MANUAL_FETCH_PLACES = 0`, `MANUAL_FETCH_CEILING_AT_PHASE_08 = 0`. Гейтовые модули целиком входят в полную суиту 4084 passed (b0e6c0bd, код и тесты побайтно равны HEAD) |
| 7 | Опрос в `needs_2fa` → шаг пароля без триггера, `required`, без значения (13-02) | ✓ VERIFIED | `test_polling_needs_2fa_answers_the_password_step`; сигнатура `password` = дереву обхода |
| 8 | Неверный пароль → 422 у поля, без эха (13-02) | ✓ VERIFIED | `test_a_wrong_password_answers_422_at_the_field_without_echo` |
| 9 | Пустой пароль → 422 «Введите пароль» (13-02) | ✓ VERIFIED | `test_an_empty_password_answers_422_with_the_client_text` |
| 10 | Верный пароль сохраняет аккаунт из результата `complete_auth` (13-02) | ✓ VERIFIED | :576-591: возврат `submit_2fa` отброшен; `test_a_right_password_saves_one_account_from_complete_auth` |
| 11 | Два конкурентных verify-2fa / два опроса после success → один аккаунт (13-02, D-01) | ✓ VERIFIED | `complete_auth` (:205-231) без `await` между `_owned` и `pop` — файл не менялся с замера мутанта 2026-09-21. `test_concurrent_completes_yield_one_session_string` зелено. ⚠️ WR-04 переносится: маршрутные тесты гонки свойство не различают (тесты тоже не менялись) |
| 12 | Иная ошибка Telethon на 2FA → фрагмент, не 500 (13-02) | ✓ VERIFIED | `except Exception` пишет только `error_type` (:582-586); `test_a_telethon_failure_on_the_password_step_is_a_fragment` |
| 13 | verify-2fa без JS: 302; ошибка поля → страница 422; без сессии → `/login` (13-02) | ✓ VERIFIED | `respond_field_error(page=_page, …)` (:623); `test_verify_2fa_degrades_and_requires_a_session` — зелено ПОСЛЕ рефакторинга 14-02 |
| 14 | Таймаут `wait()` → `qr_expired` без текста ошибки и трассировки (13-03, D-03) | ✓ VERIFIED | :93-101; `test_an_expired_qr_token_is_a_status_not_an_error` (настоящий `QRLogin`). ⚠️ WR-02 переносится |
| 15 | Опрос в `qr_expired` → шаг «QR-код истёк…» с формой обновления, без триггера (D-02) | ✓ VERIFIED | Сигнатура `qr_expired`: `every` = 0; `test_polling_an_expired_code_offers_a_refresh` |
| 16 | refresh-qr в пределах срока → новый QR и опросчик (13-03) | ✓ VERIFIED | :502-505; `test_refreshing_an_expired_code_resumes_polling` |
| 17 | Устаревшая сессия → «истекла», `recreate` не зовётся (13-03) | ✓ VERIFIED | `test_refreshing_an_outdated_session_says_it_expired`, `test_refresh_qr_does_not_revive_an_outdated_session` |
| 18 | `refresh_qr` только из `qr_expired` (13-03) | ✓ VERIFIED | :162; `test_refreshing_a_non_expired_code_is_refused`. ⚠️ WR-01 переносится |
| 19 | D-13: слой сессий изменён только по D-01/D-03/D-04 (13-03/13-04) | ✓ VERIFIED | `git diff --stat bff29f7a..HEAD -- telegram_user.py` пуст; список ханков `344dc789..HEAD` тот же, что 2026-09-21; `QR_SESSION_TTL = 300` (:28) |
| 20 | refresh-qr без JS 302; без сессии `/login`; JSON нет (13-03) | ✓ VERIFIED | `test_refresh_degrades_and_requires_a_session` |
| 21 | Сессия привязана к пользователю при старте; `user_id` обязателен (13-04) | ✓ VERIFIED | :348-352 `start_qr_auth(..., user_id=user.id)`; `test_a_session_is_owned_by_the_user_who_started_it` |
| 22 | Под имперсонацией — к СУБЪЕКТУ (13-04) | ✓ VERIFIED | `test_the_wizard_binds_the_session_to_the_impersonated_subject` |
| 23 | Чужой запрос ничего не делает с сессией владельца; владелец затем подключается (13-04) | ✓ VERIFIED | три маршрутных `test_a_foreign_*` + `test_a_foreign_{complete,refresh,password}_*` |
| 24 | Проверка владельца до любой мутации; `complete_auth` только в `success` (13-04) | ✓ VERIFIED | :216-219; `test_complete_auth_takes_only_a_successful_session` |
| 25 | Позднее сканирование — `success`; «истекла» только владельцу (13-04) | ✓ VERIFIED | `test_a_late_scan_is_still_a_success` |
| 26 | Гейт критерия 2 замкнут по веткам с контролями; изъятие — именованный ноль (13-05) | ✓ VERIFIED | Правила и шесть контролей зелены; `TOP_LEVEL_BINDING_EXEMPT_TEMPLATES: dict[str, str] = {}` (`test_hx_location_destinations.py:578`) |
| 27 | Летописи у SC1/2/3/5 и FETCH-02; тексты не переписаны; разведка не тронута; FETCH-02 не отмечен планом (13-06) | ✓ VERIFIED | Пять строк критериев равны базе `344dc789` (`cmp`). Текст FETCH-02 после `[.]` равен базе. `git diff 344dc789 HEAD -- .planning/research/` пуст. FETCH-02 сегодня `[x]` / `Complete`, и поставил это коммит закрытия `ab72d228` ПОСЛЕ вердикта `passed`, как истина и требует («отметка следует за верификацией фазы»). Так же держит `tests/test_planning/test_requirement_completion_follows_verification.py` |

Три истины `verification: backstop` из 13-01/02/03 — это содержание SC4, и закрыты они вместе с ним
прямым наблюдением обхода. Отдельно в счёт они не входят, как и в прошлом раунде.

**Score:** 32/32 verified (5 SC + 27 plan truths); 0 present-but-behavior-unverified. Каждая
поведенческая истина (гонка, невмешательство чужого запроса, классификация таймаута) держится
правилом, которое сегодня зелено. Живой сценарий держится прямым наблюдением, и его перенос на
сегодняшнее дерево измерен.

### Deferred Items

Владельческие отсрочки, а не покрытие поздней фазой. Перенесены из прошлого раунда без правки. Ни
Фаза 14, ни Фаза 15 их не взяли. `telegram_user.py` не менялся, текст старта `accounts.py:354` прежний.

| # | Item | Addressed In | Evidence |
|---|---|---|---|
| 1 | IN-03 — брошенная QR-сессия держит подключённый клиент Telethon | владелец | 13-CONTEXT §Deferred Ideas; D-13 |
| 2 | UI-17 — «Ошибка запуска QR авторизации: {e}» показывает сырой текст исключения | владелец | 13-CONTEXT §Landmines; D-09 |

### Advisory (New Scope, Unevidenced)

**Новых находок вне рамки этот раунд не заводит.** Шаг 7 на файлах фазы не нашёл ни `TBD`, ни
`FIXME`, ни `XXX`, ни `TODO`, ни `HACK`, ни `PLACEHOLDER`. Три замеченных расхождения ссылок
отнесены к ℹ️ Info (ниже). Это не дефекты кода.

Перенесённые записи ключа `advisory` (21) — состояние на сегодняшнем дереве. Тексты записей в шапке
не переписаны (история). Номера строк в них относятся к дереву 2026-09-21.

| Запись | Состояние 2026-10-07 | Основание |
|---|---|---|
| WR-01, WR-02, WR-03, IN-02 | открыта, без изменений | `telegram_user.py` и диапазон мастера в `accounts.py` побайтно прежние |
| WR-04 | открыта, без изменений | `test_tg_user_auth.py` и `test_telegram_user.py` — 0 коммитов после `bff29f7a`; мутант заново не гонялся, предмет не менялся |
| IN-01 | открыта, без изменений | по сегодняшней нумерации `accounts.py:577-581` (было :563-567, сдвиг +14) |
| UI-1, UI-2, UI-3 | **закрыта** (260921-qvt) | UI-1: ветка `password` несёт `connect-step__form` (`tg_connect_step.html:112`), правило `.connect-step__form { gap: 14px }` (`app.css:2019`). UI-2: `.connect-step--center .connect-step__actions { justify-content: center }` (`app.css:2018`). UI-3: подпись в трёх рядах + `app.css:2036-2037`. Правило `test_tg_connect_step_layout.py` зелено. Живой взгляд (пункт D4 быстрой задачи) — за владельцем, см. ниже |
| UI-4, UI-6…UI-13, UI-15, UI-16 | открыта, без изменений | ветки шаблона, кроме выкладки, не тронуты |
| UI-14 | открыта, без изменений | мёртвое правило `.connect-step[hidden]` стоит теперь на `app.css:2009` (было :1925-1929); `hidden` в `app/templates/accounts/` вне `type="hidden"` по-прежнему нет — критерий 1 держится |
| UI-5 | закрыта обходом 2026-09-21 (пункт 3) | на `qr_expired` прибавилась только подпись с `display: none`, высоты вне запроса она не занимает |

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `app/templates/accounts/includes/tg_connect_step.html` | единственный источник разметки шага, шесть веток | ✓ VERIFIED | 155 строк (было 137, прибавка — правка 260921-qvt); ветки start/waiting/qr_expired/password/connected/error; включается страницей и `_tg_step_markup` |
| `app/templates/accounts/connect_tg_user.html` | постоянный якорь + включение, без скрипта | ✓ VERIFIED | 27 строк, 0 коммитов после `bff29f7a` |
| `app/pages/accounts.py` | четыре обработчика на `respond()`/`respond_field_error()`, `_tg_step_markup`, `_save_tg_account`, константы | ✓ VERIFIED | :225-629 (сдвиг +14 от комментариев 15-09/15-21) |
| `app/messengers/telegram_user.py` | `user_id`, `_owned`, ветка таймаута, проверки обновления | ✓ VERIFIED | 0 коммитов после `bff29f7a`; единственный потребитель — `accounts.py` |
| `tests/test_routes/test_tg_user_auth.py` | сквозной путь, POLLING_CASES, гонка, чужой, контроли | ✓ VERIFIED | 0 коммитов после `bff29f7a`; зелён сегодня |
| `tests/test_messengers/test_telegram_user.py` | настоящий QRLogin, правила владения, гонка | ✓ VERIFIED | 0 коммитов после `bff29f7a`; зелён сегодня |

### Key Link Verification

| From | To | Via | Status |
|---|---|---|---|
| форма старта (`hx-target=#tg-connect-step`) | `accounts_connect_tg_user_start_qr` → `start_qr_auth(user_id=user.id)` | `form_wrapper` | ✓ WIRED (сигнатура `start` = дереву обхода) |
| опросчик внутри фрагмента ожидания | `accounts_connect_tg_user_qr_status` | `hx-post` every 3s, скрытый `session_id` | ✓ WIRED (не на якоре; сигнатура `waiting` = дереву обхода) |
| qr-status `success` | `complete_auth` → `_save_tg_account` | прямой вызов (:425-427) | ✓ WIRED |
| шаг пароля | `verify_2fa` → `submit_2fa` → `complete_auth` → `_save_tg_account` | `form_wrapper` | ✓ WIRED (обёртка `connect-step__form` внутри формы, поле осталось в форме) |
| `respond_field_error` | 422-подмена шага пароля | `_respond_by_transport` (14-02) | ✓ WIRED (правило 422 зелено после рефакторинга) |
| `QRLogin.wait()` TimeoutError | `_wait_for_qr` → `qr_expired` → опрос → шаг обновления | поле статуса | ✓ WIRED |
| «Обновить QR-код» | `refresh_qr` → шаг ожидания с опросчиком | `form_wrapper` | ✓ WIRED |
| `get_user_from_cookie` → `user.id` | `QRAuthState.user_id` → `_owned` | параметр | ✓ WIRED |
| `POLLING_CASES` ↔ ветки шаблона | правило замыкания | разбор текста шаблона | ✓ WIRED |
| летопись SC3 ↔ летопись FETCH-02 | перекрёстная ссылка | обе на месте (ROADMAP §Phase 13, REQUIREMENTS:55) | ✓ WIRED |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
|---|---|---|---|---|
| шаг ожидания `qr_code` | адрес входа | `start_qr_auth` / `refresh_qr` → `qr_login.url` → `_generate_qr_base64` | да (Telethon) | ✓ FLOWING |
| выбор шага | `status` | `_qr_sessions[...]`, пишут `_wait_for_qr` / `submit_2fa` | да | ✓ FLOWING |
| сохранённый аккаунт | `session_string` | `complete_auth` → `client.session.save()` | да | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Маршруты мастера + слой сессий + выкладка шага | `uv run pytest tests/test_routes/test_tg_user_auth.py tests/test_messengers/test_telegram_user.py tests/test_templates/test_tg_connect_step_layout.py -q` | 100 passed (55.8 s) | ✓ PASS |
| Ключевые правила существуют | тот же набор, `--collect-only` | 20 `POLLING_CASES`, 6 `test_control_*`, 3 маршрутных + 4 модульных `foreign`, 2 правила гонки маршрута + 1 модульное, `test_the_complete_route_and_the_get_poll_are_gone`, `test_the_wizard_page_carries_no_client_script` | ✓ PASS |
| Живая таблица маршрутов | `app.routes` с фильтром `tg_user` | GET страница; POST start-qr / qr-status / refresh-qr / verify-2fa; `complete` нет | ✓ PASS |
| Шаблон шага до/после 260921-qvt | скретч-рендер семи шагов, сравнение интерактивных атрибутов | `TOTAL DIFFS 0` | ✓ PASS |
| SC5, база | `git show 344dc789:…/connect_tg_user.html \| grep -c '<form'` | `0` | ✓ PASS |
| Полная суита | замер оркестратора `just test` на `b0e6c0bd` (код и тесты побайтно равны HEAD) | 4084 passed, 0 failed | ✓ (цитируется) |
| `tests/test_planning` | замер оркестратора на `970ce74f` и после коммита валидации | 208 passed | ✓ (цитируется) |

Полную суиту я не перезапускал: дерево кода и тестов побайтно то же, что в замере оркестратора.

### Probe Execution

Проб нет: планы фазы не называют `scripts/*/tests/probe-*.sh`. Step 7c: SKIPPED.

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|---|---|---|---|---|
| FETCH-02 | 13-01…13-06 (все шесть объявляют) | QR-мастер на HTML-фрагментах: опрос `hx-trigger`, останов ответом без триггера, состояние на сервере, `session_id` скрытым полем, проверка владения (летопись: заведена) | ✓ SATISFIED | SC1–SC5, истины 1–27. `[x]` / `Complete` (`REQUIREMENTS.md:54`, `:157`) поставлен закрытием `ab72d228` после вердикта `passed`, текст требования равен базе |

REQUIREMENTS.md сопоставляет Фазе 13 только FETCH-02 (`:157`, `:504`), поэтому осиротевших требований нет.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| файлы фазы в `app/` | — | TBD/FIXME/XXX | не найдено | — |
| файлы фазы в `app/` | — | TODO/HACK/PLACEHOLDER | не найдено | — |
| `app/static/css/app.css` | 2009 | мёртвое правило `.connect-step[hidden]` (UI-14) | ℹ️ Info | перенесено; файл не в покрытии фазы |
| ROADMAP §Phase 13, летопись критерия 5; `13-06-SUMMARY.md` «Критерий 5» | — | дрейф референта команды: `git merge-base HEAD master` сегодня даёт `50beab46` (master после влития фазы), а не базу фазы `344dc789`. Команда по-прежнему печатает `0`, но уже потому, что формы сегодняшней страницы живут во включаемом шаблоне, а не потому, что их не было до фазы | ℹ️ Info | на запись SC5 не влияет: замер по закреплённой базе `344dc789` даёт `0`. Если правка нужна, это решение владельца: назвать в летописи хеш базы рядом с командой |
| `13-SECURITY.md` строка T-13-01 | — | ссылки `accounts.py:395,478,554` — по сегодняшней нумерации `:409, :492, :568` (сдвиг +14 от 15-09/15-21) | ℹ️ Info | номера строк устарели, а суть верна; файл вне правки этого агента |

### Prohibitions

Восемь запретов (`verification: none`) приняты владельцем обходом 2026-09-21: пункт 5, дословное
`pass` на явный список P1–P8. Сегодня каждый перепроверен на дереве. Вердикты, как и прежде, суждение
LLM без машинного принуждения, но с машинной опорой там, где она есть.

| # | Запрет | Вердикт 2026-10-07 |
|---|---|---|
| P1 | `session_id` только скрытым полем (D-06) | держится: в семи отрисовках `session_id` — только `type="hidden"` в POST-формах, `<script` 0; GET-опрос → 405 |
| P2 | Ни сценария, ни таймера, ни автоперехода после «Подключено» (D-07, D-12) | держится: ветка `connected` не менялась, на странице и во фрагментах `<script` 0. Подпись `Загрузка...` — чистый CSS по `disabled`, без сценария |
| P3 | Инвентарные числа ставятся прогоном | держится по летописям: прочитанные мною движения чисел фаз 14–15 (`HX_LOCATION_DESTINATION_CALLS_DECLARED` 77 → 79 → 81) несут запись «ПОСТАВЛЕНО ПРОГОНОМ» с текстом покрасневшего правила; остальные движения поштучно не перечитывались. Это процессное утверждение, и код его показать не может |
| P4 | Пароль 2FA не эхается | держится: у поля нет `value` в обеих отрисовках `password`; обработчик кладёт в контекст только `password_error`; журнал несёт только `error_type` |
| P5 | Истёкший код не обновляется сам (D-02) | держится: в `qr_expired` `hx-trigger="every` = 0 |
| P6 | Чужой ответ неотличим от неизвестного | держится: три правила `_same_answer` зелены |
| P7 | Правило гейта не удаляется ради зелени | держится: `TOP_LEVEL_BINDING_EXEMPT_TEMPLATES` — именованный ноль; правил мастера в гейтах фаз 14–15 не снято |
| P8 | Тексты критериев и требования не переписываются | держится: пять строк критериев и текст FETCH-02 побайтно равны базе `344dc789` |

### Human Verification Required

Новых пунктов раунд не заводит. Пять пунктов первого раунда закрыты обходом 2026-09-21: `13-UAT.md`,
`status: complete`, 5/5 `pass`. Тексты пунктов перенесены дословно в ключ шапки
`previous_round_closed_items.human_verification`. Первоначальный раздел сохранён в предыдущей
редакции ниже. Позднейшие правки тех путей, что лежат под пунктами 1–4, измерены выше и наблюдения
не задевают.

**Владельцу, без влияния на вердикт.** У быстрой задачи 260921-qvt открыт собственный пункт D4: живой
взгляд на выкладку, `human_judgment: true`, отметки ставит владелец. Он относится к советующим
записям UI-1/2/3, а не к должным истинам фазы 13, поэтому в `human_verification` этого отчёта не
поднимается. Снять ли его отдельно, решает владелец.

### Gaps Summary

**Гапов нет.** Цель фазы держится кодом фазы 13, который после закрытия не менялся. Исключение —
правка выкладки 260921-qvt, и она измерена как не задевающая ни одной истины. Позднейшие фазы
сдвинули строки `accounts.py` комментариями. Ещё они довели `NOT_YET_CONVERTED_COUNT` до нуля и
вписали обработчики мастера в новые реестры фазы 15. Ни одного правила мастера они не ослабили, и
это проверено построчным диффом каждого покрытого файла и зелёным прогоном собственных правил фазы
(100 passed).

---

_Verified: 2026-10-07T11:08:19Z_
_Verifier: Claude (gsd-verifier)_

---

# ПРЕДЫДУЩАЯ РЕДАКЦИЯ (первичная верификация 2026-09-21T17:40:19Z + канонизация и два пересчёта отпечатка 2026-09-21) — сохранена без правок

_Ниже прошлая редакция дословно, со всеми разделами, включая написанные оркестратором («Канонизация
вердикта 2026-09-21: `human_needed` → `passed`», «Пересчёт отпечатка покрытых входов после закрытия
фазы», «Пересчёт отпечатка после быстрой задачи 260921-qvt — по явному разрешению владельца»). Номера
строк в ней относятся к дереву 2026-09-21. По сегодняшнему дереву строки `app/pages/accounts.py`
мастера сдвинуты на +14._

# Phase 13: Мастер подключения Telegram по QR на фрагментах — Verification Report

**Phase Goal:** мастер подключения работает на HTML-фрагментах с состоянием на сервере — без `setInterval`, без пяти JSON-контрактов и без ручного переключения `hidden`
**Verified:** 2026-09-21T17:40:19Z (HEAD `bff29f7a`)
**Status:** human_needed
**Re-verification:** No. This is the initial verification; no earlier VERIFICATION.md existed.

**Why `human_needed` and not `passed`:** every machine-checkable must-have holds, and there are no gaps. But criterion 4 (the live Telethon scenario) cannot be settled by any machine check. It routes to the owner, together with one visual finding (UI-5) and the eight prohibitions, which have no test enforcement. `passed` is not justifiable while criterion 4 is open, so FETCH-02 stays `[ ]` / `Pending`, which is correct.

## Goal Achievement

### Roadmap Success Criteria (read with the 13-06 chronicles)

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| SC1 | Five `fetch()` gone with `setInterval` and manual `hidden`; routes answer HTML fragments. **Chronicle:** four routes, `complete` removed by D-01, poll moved GET → POST | ✓ VERIFIED | `grep -rn 'fetch(' app/templates/` = 0. Wizard page = anchor + include, with no `<script>`/`onclick`/`setInterval`. The only `hidden` in the step template is on three `type="hidden"` `session_id` inputs. No template in `accounts/` carries a `hidden` attribute, and no static JS touches connect steps. Live route table: GET page + POST `start-qr`, `qr-status`, `refresh-qr`, `verify-2fa`, and no `complete`. No `JSONResponse`/json in `app/pages/accounts.py`. Tests: `test_the_wizard_page_carries_no_client_script`, `test_the_complete_route_and_the_get_poll_are_gone` (GET poll → 405) |
| SC2 | Polling via `hx-trigger`, stopped by a response without it; each `every` fragment has a trigger-less pair. **Chronicle:** proven by a rule over rendered responses, not by the markup gate | ✓ VERIFIED | The poller exists only in the `waiting` branch (`form_wrapper(... trigger='every 3s')` targeting `#tg-connect-step`). The anchor has no trigger. Waiting poll → 204. `test_polling_stops_by_a_response_without_trigger` × 20 `POLLING_CASES`, closure rules `test_every_wizard_step_is_reached_by_a_polling_case` / `test_every_polling_fragment_has_a_terminal_pair`, and six `test_control_*` negative controls: all green in this run |
| SC3 | Server state, `session_id` in a hidden field, and the ownership check "preserved": a foreign `session_id` is rejected. **Chronicle:** the check was INTRODUCED, because it did not exist | ✓ VERIFIED | `QRAuthState.user_id` is mandatory with no default. `_owned()` guards `get_qr_status`/`refresh_qr`/`submit_2fa`/`complete_auth` before any mutation. Foreign-vs-unknown answers are compared byte for byte by `_same_answer` (status, body, headers minus `date`/`x-request-id`) on all three handlers, with victim-untouched assertions and the owner then reaching «Подключено»: `test_a_foreign_{poll,refresh,password}_is_answered_as_unknown_and_leaves_no_trace` green |
| SC4 | Live scenario: QR scan by phone, refresh of an expired code, 2FA entry (manual UAT) | ? HUMAN | Cannot be machine-verified: the Telegram server is not substitutable and the live browser needs owner consent. The four manual-only rows of `13-VALIDATION.md` appear as human_verification items 1–4. **Not passed, not failed.** |
| SC5 | Recorded plainly: there is no no-JS degradation **today either** (document record) | ✓ VERIFIED | Re-measured: `git merge-base HEAD master` = `344dc789`. `grep -c '<form'` on the base template prints `0` (exit 1). The chronicle sits beside SC5 in ROADMAP, and the «Критерий 5» section in `13-06-SUMMARY.md` carries the same command and output. Each wizard POST without HX-Request → 302 to the wizard page (`test_the_wizard_degrades_to_its_page_without_js`) |

### Plan Must-Have Truths (deduplicated against the SCs)

| # | Truth (plan) | Status | Evidence |
|---|--------------|--------|----------|
| 1 | start-qr (htmx) → 200, waiting fragment: data-URI QR, exactly one poller form, hidden `session_id`, no anchor id in the fragment (13-01) | ✓ VERIFIED | `accounts.py` `_waiting` → `_tg_step_markup(step="waiting")`. `test_the_waiting_fragment_polls_into_the_persistent_anchor`. The `_anchor_in_fragment` guard sits in the polling rule |
| 2 | qr-status in `waiting` → 204, empty body (13-01) | ✓ VERIFIED | `_unchanged` → `Response(status_code=204)`. POLLING_CASES waiting row |
| 3 | First poll that sees `success` calls the real `complete_auth`, saves one `MessengerAccount(tg_user, active)` and answers «Подключено» with no trigger and no HX-Location (13-01) | ✓ VERIFIED | Handler code. `test_the_wizard_walks_from_start_to_connected`, `test_a_second_poll_after_success_does_not_save_again` |
| 4 | All other outcomes → fragment without trigger, with an alert and «Начать заново»; texts moved verbatim (13-01) | ✓ VERIFIED | `TG_*_MESSAGE` constants. `test_start_refusals_are_fragments_with_verbatim_texts`, `test_polling_an_{unknown,errored}_session_*` |
| 5 | No-JS → 302 to the wizard; no login session → `/login` on both transports; no JSON (13-01) | ✓ VERIFIED | `respond(request, redirect=…)` on every exit. `test_the_wizard_degrades_to_its_page_without_js`, `test_the_wizard_without_a_session_goes_to_login` |
| 6 | Gate registries moved by a run (NOT_YET_CONVERTED_COUNT, MANUAL_FETCH_*, etc.) (13-01) | ✓ VERIFIED | `NOT_YET_CONVERTED_COUNT = 10`, `MANUAL_FETCH_PLACES = 0`, and 441 gate+records tests pass in this run. That the numbers came "from a run" is a process claim, recorded under Prohibitions |
| 7 | Poll in `needs_2fa` → password step with no trigger, `required`, empty value (13-02) | ✓ VERIFIED | `test_polling_needs_2fa_answers_the_password_step` |
| 8 | Wrong password → 422, «Неверный пароль 2FA.» at the field, no echo (13-02) | ✓ VERIFIED | `test_a_wrong_password_answers_422_at_the_field_without_echo` |
| 9 | Empty/missing password → 422 «Введите пароль» (13-02) | ✓ VERIFIED | `test_an_empty_password_answers_422_with_the_client_text` |
| 10 | Right password saves one account from the RESULT of `complete_auth`, not from `submit_2fa` (13-02) | ✓ VERIFIED | Handler: `submit_2fa` return value is discarded; `session_string = await complete_auth(...)`. `test_a_right_password_saves_one_account_from_complete_auth` |
| 11 | Two concurrent verify-2fa → one account; two concurrent polls after success → one account (13-02, D-01) | ✓ VERIFIED | The property holds: there is no `await` between the `_owned` check and `pop` in `complete_auth`, and the handlers reach it with no yield after `get_qr_status`. The unit rule `test_concurrent_completes_yield_one_session_string` passes and goes RED 3/3 on the reorder mutant (re-measured here). ⚠️ The route race tests do NOT carry this proof (WR-04, advisory) |
| 12 | Other Telethon errors on 2FA → error fragment, not a 500 (13-02) | ✓ VERIFIED | Generic `except Exception` logs `error_type` only. `test_a_telethon_failure_on_the_password_step_is_a_fragment` |
| 13 | verify-2fa no-JS: 302; field error → wizard page with 422; no session → `/login` (13-02) | ✓ VERIFIED | `respond_field_error(page=_page, …)`. `test_verify_2fa_degrades_and_requires_a_session` |
| 14 | `wait()` timeout → `qr_expired` with no error text and no `logger.error` traceback; session alive (13-03, D-03) | ✓ VERIFIED | `test_an_expired_qr_token_is_a_status_not_an_error` runs the REAL `QRLogin` with `expires_in=0.05` (landmine respected). ⚠️ The classification is too wide for post-event timeouts (WR-02, advisory) |
| 15 | Poll in `qr_expired` → «QR-код истёк…» step with a refresh form, no trigger (D-02) | ✓ VERIFIED | `test_polling_an_expired_code_offers_a_refresh`. Template branch has no poller |
| 16 | refresh-qr within TTL → new QR + poller, polling resumes (13-03) | ✓ VERIFIED | `test_refreshing_an_expired_code_resumes_polling`, `test_refresh_qr_recreates_only_an_expired_code` |
| 17 | Outdated session → «Сессия авторизации истекла…», `recreate` not called (13-03) | ✓ VERIFIED | `test_refreshing_an_outdated_session_says_it_expired`, `test_refresh_qr_does_not_revive_an_outdated_session` |
| 18 | `refresh_qr` recreates only from `qr_expired`; otherwise None and «Не удалось обновить QR…» (13-03) | ✓ VERIFIED | `test_refreshing_a_non_expired_code_is_refused`. ⚠️ Holds sequentially, not under concurrent owner refreshes (WR-01, advisory) |
| 19 | D-13: session layer changed only for D-01/D-03/D-04; `QR_SESSION_TTL = 300`, `_cleanup_expired_sessions`, `cleanup_qr_session`, `TelegramUserMessenger` untouched (13-03/13-04) | ✓ VERIFIED | `git diff -U0 344dc789 HEAD -- app/messengers/telegram_user.py`: hunks only in `QRAuthState`, the `start_qr_auth` signature, `_wait_for_qr`, `_owned`/`get_qr_status`, `refresh_qr`, `submit_2fa` and `complete_auth`. The hunk headed `_cleanup_expired_sessions` is the `start_qr_auth` signature line. Nothing past `complete_auth` |
| 20 | refresh-qr no-JS 302; no session → `/login`; no JSON (13-03) | ✓ VERIFIED | `test_refresh_degrades_and_requires_a_session` |
| 21 | Session bound to the user at start-qr; `user_id` mandatory (13-04) | ✓ VERIFIED | Dataclass field with no default. `start_qr_auth(..., user_id=user.id)`. `test_a_session_is_owned_by_the_user_who_started_it` |
| 22 | Under impersonation, bound to the SUBJECT; account saved on the subject (13-04) | ✓ VERIFIED | `test_the_wizard_binds_the_session_to_the_impersonated_subject` (asserts target ≠ admin, then `[a.user_id] == [target_id]`) |
| 23 | Foreign request does NOTHING to the owner's session, and the owner then reaches «Подключено» (13-04) | ✓ VERIFIED | The victim `is` object is still in `_qr_sessions`, status is unchanged, `disconnect`/`sign_in` are not awaited, and the owner then connects (three route tests + `test_a_foreign_{complete,refresh,password}_*` unit tests) |
| 24 | Owner check before any `pop`/`cancel`/`recreate`/`sign_in`; `complete_auth` only in `success` (13-04) | ✓ VERIFIED | Code order in all four functions. `test_complete_auth_takes_only_a_successful_session`, `test_a_foreign_complete_leaves_the_session_alone` |
| 25 | A late scan (past TTL, before cleanup) is `success`; own expired session → «истекла», never shown to a foreign caller (13-04) | ✓ VERIFIED | The `success` check precedes the TTL check, and `_owned` precedes both. `test_a_late_scan_is_still_a_success`. The foreign cases answer «не найдена» |
| 26 | Criterion-2 gate closed over template branches with negative controls; `TOP_LEVEL_BINDING_EXEMPT_TEMPLATES` a named zero; docstring chronicles (13-05) | ✓ VERIFIED | Rules and 6 controls green. Branches are parsed from the template text, so a new branch without a case reddens the rule |
| 27 | Chronicles beside SC1/2/3/5 and FETCH-02; criterion/requirement texts not rewritten; research untouched; FETCH-02 not marked (13-06) | ✓ VERIFIED | Chronicles read in ROADMAP/REQUIREMENTS. No removed diff line touches the criterion texts or the FETCH-02 text. `git diff 344dc789 HEAD -- .planning/research/` is empty. FETCH-02 is `[ ]` / `Pending`. `tests/test_planning` passes |

The three `verification: backstop` truths of 13-01/02/03 (live browser behaviour) are the content of SC4 and are routed with it. They do not count separately.

**Score:** 31/32 verified (5 SC + 27 plan truths). The one unverified item is SC4, routed to a human. 0 truths are present but behaviour-unverified: every behaviour-dependent truth (concurrency, ownership non-mutation, timeout classification) has a passing test that exercises it.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app/templates/accounts/includes/tg_connect_step.html` | single source of step markup, six branches | ✓ VERIFIED | 137 lines; start/waiting/qr_expired/password/connected/error. Included by the page and rendered by `_tg_step_markup` |
| `app/templates/accounts/connect_tg_user.html` | permanent anchor `#tg-connect-step` + include, no script | ✓ VERIFIED | 27 lines; anchor on `.connect-shell` |
| `app/pages/accounts.py` | four handlers on `respond()`/`respond_field_error()`, `_tg_step_markup`, `_save_tg_account`, constants | ✓ VERIFIED | Lines 211-616 |
| `app/messengers/telegram_user.py` | `user_id`, `_owned`, timeout branch, refresh guards | ✓ VERIFIED | Wired: imported by `accounts.py` (the only consumer) |
| `tests/test_routes/test_tg_user_auth.py` | tracer path, POLLING_CASES, race, foreign, controls | ✓ VERIFIED | 56 tests pass |
| `tests/test_messengers/test_telegram_user.py` | real-QRLogin timeout, ownership rules, complete race | ✓ VERIFIED | 34 tests pass |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| start form (`hx-target=#tg-connect-step`) | `accounts_connect_tg_user_start_qr` → `start_qr_auth(user_id=user.id)` | `form_wrapper` action | ✓ WIRED |
| poller form inside the waiting fragment | `accounts_connect_tg_user_qr_status` | `hx-post` every 3s, hidden `session_id` | ✓ WIRED (not on the anchor, per the D-05 correction) |
| qr-status `success` | `complete_auth` → `_save_tg_account` | direct call | ✓ WIRED |
| password step | `verify_2fa` → `submit_2fa` → `complete_auth` → `_save_tg_account` | `form_wrapper` | ✓ WIRED |
| `respond_field_error` | 422 swap of the password step | htmx response-handling config | ✓ WIRED (test asserts 422 fragment content) |
| `QRLogin.wait()` TimeoutError | `_wait_for_qr` → `qr_expired` → poll → refresh step | status field | ✓ WIRED |
| «Обновить QR-код» | `refresh_qr` (`recreate` + new wait task) → waiting step with poller | `form_wrapper` | ✓ WIRED |
| `get_user_from_cookie` → `user.id` | `QRAuthState.user_id` → `_owned` in every handler | parameter | ✓ WIRED |
| `POLLING_CASES` ↔ template branches | closure rule | template text parse | ✓ WIRED |
| SC3 chronicle ↔ FETCH-02 chronicle | cross-reference | both present | ✓ WIRED |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
|----------|------|--------|-----------|--------|
| waiting step `qr_code` | login URL | `start_qr_auth` / `refresh_qr` → `qr_login.url` → `_generate_qr_base64` | yes (Telethon) | ✓ FLOWING |
| step selection | `status` | `_qr_sessions[...]` written by `_wait_for_qr` / `submit_2fa` | yes | ✓ FLOWING |
| saved account | `session_string` | `complete_auth` → `client.session.save()` | yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Wizard route + session-layer modules | `uv run pytest tests/test_routes/test_tg_user_auth.py tests/test_messengers/test_telegram_user.py -q -p no:randomly` | 90 passed | ✓ PASS |
| Gates + records | the 10 gate files from VALIDATION's gate command + `tests/test_components.py` + `tests/test_planning` | 441 passed (2:37) | ✓ PASS |
| Live route table | `app.routes` filtered on `tg_user` | GET page; POST start-qr/qr-status/refresh-qr/verify-2fa; no complete | ✓ PASS |
| Reorder mutant vs the race rules (WR-04) | scratch plugin, 3 runs | unit RED 3/3; 2FA route GREEN 3/3; poll route GREEN 5/6; control 3 passed | ✓ measured (see advisory WR-04) |
| SC5 base measurement | `git show $(git merge-base HEAD master):…connect_tg_user.html \| grep -c '<form'` | `0` | ✓ PASS |

I did not re-run the full suite. I rely on the orchestrator's measurement (3511 passed at `e5c1288c`); since then only `.planning/` files changed, and `tests/test_planning` was re-run green above.

### Probe Execution

None declared. The phase plans name no `scripts/*/tests/probe-*.sh`. Step 7c: SKIPPED.

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| FETCH-02 | 13-01…13-06 (all declare it) | QR wizard on HTML fragments: `hx-trigger` polling, stop by a trigger-less response, server state, hidden `session_id`, server ownership check (chronicle: introduced, not preserved) | ✓ SATISFIED (machine-checkable part) | SC1–SC3, truths 1–26. The flag stays `[ ]`/`Pending` until `phase.complete` follows a `passed` verdict, which waits on the criterion-4 UAT |

REQUIREMENTS.md maps only FETCH-02 to Phase 13, so no requirement is orphaned.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `app/*` phase files | — | TBD/FIXME/XXX | none found | — |
| `app/*` phase files | — | TODO/HACK/PLACEHOLDER | none found | — |
| `app/static/css/app.css` | 1925-1929 | stale comment + dead `.connect-step[hidden]` rule | ℹ️ Info | UI-14; not a phase-modified file |

### Prohibitions (all `verification: none` → flagged; non-authoritative LLM-judge verdicts)

| # | Plan | Prohibition | Verifier's verdict (non-authoritative) |
|---|------|-------------|----------------------------------------|
| P1 | 13-01 | `session_id` never in the URL, JS variables or browser storage; hidden field only (D-06) | HOLDS. There is no script on the page; `session_id` appears only in `type="hidden"` inputs of POST forms; the GET poll is gone (405) |
| P2 | 13-01 | No new script, browser timer or auto-redirect after «Подключено» (D-07, D-12) | HOLDS. `connected` branch = badge + text + `link_button` only; the page has no `<script>` |
| P3 | 13-01 | Inventory numbers set by a run of the reddened rule, not by mental arithmetic | HOLDS by the SUMMARY disclosures (every registry move is recorded with its red run). This is a process claim the code cannot show |
| P4 | 13-02 | 2FA password not echoed, not in foreign attributes, storage or log | HOLDS. The field renders `value=""` (test). The handler never puts the password in the context. The log carries `error_type` only. IN-01 echoes Telethon text, not the password |
| P5 | 13-03 | An expired code is not refreshed automatically (D-02) | HOLDS. The `qr_expired` branch has no poller; the POLLING_CASES row asserts no trigger |
| P6 | 13-04 | A foreign answer does not differ from an unknown one in text, code or markup | HOLDS. `_same_answer` compares byte for byte on three handlers (headers exclude only `date`/`x-request-id`) |
| P7 | 13-05 | A gate rule is not deleted for green; it is rewritten as a named zero or on synthetic input | HOLDS. The exempt list is a declared zero with rewritten non-vacuity rules, and there are six controls |
| P8 | 13-06 | Criterion and requirement texts are not rewritten; chronicles sit beside them | HOLDS. No removed diff line touches the SC or FETCH-02 texts |

These are listed as one human_verification item so they do not pass silently.

## Findings Disposition (REVIEW.md + UI-REVIEW.md)

Each finding has exactly one disposition. **Split: 0 gaps · 21 advisory · 1 human_verification · 2 deferred (owner) = 24.**

| Finding | Source | Disposition | One-line reason |
|---------|--------|-------------|-----------------|
| WR-01 | REVIEW | Advisory | Real owner-only concurrency hole in the refresh guard; affects neither criterion 2/3 nor the D-02 no-auto-refresh prohibition |
| WR-02 | REVIEW | Advisory | Confirmed in Telethon source; rare post-scan DC-migration timeout mislabelled «истёк»; the main path is intact |
| WR-03 | REVIEW | Advisory | Pop-before-commit is pre-existing (old `/complete` did the same); failure-path hardening |
| WR-04 | REVIEW | Advisory | Re-measured: the route race tests don't discriminate the reorder mutant; the property holds via code + unit rule (truth 11 VERIFIED); the plans' "route tests prove it" claim is overstated |
| IN-01 | REVIEW | Advisory | Broad except echoes Telethon internals at the field; not a password leak |
| IN-02 | REVIEW | Advisory | Layer asymmetry; the only caller enforces `needs_2fa` |
| IN-03 | REVIEW | Deferred → «владелец» | CONTEXT §Deferred names it separate work; D-13 bound; pre-existing |
| UI-1 | UI-REVIEW | Advisory | Confirmed regression (0px field/button); visual, no SC defeated. Recommended fix before close |
| UI-2 | UI-REVIEW | Advisory | Confirmed regression (left-aligned actions); visual only |
| UI-3 | UI-REVIEW | Advisory | Confirmed regression (lost «Загрузка...»); disabled button + busy dot remain |
| UI-4 | UI-REVIEW | Advisory | Pre-existing copy placement |
| UI-5 | UI-REVIEW | Human verification | Card-height jump is a visual judgement; folded into UAT item 3 (`qr_expired` is on screen there) |
| UI-6 | UI-REVIEW | Advisory | Colour consistency polish |
| UI-7 | UI-REVIEW | Advisory | Typography polish |
| UI-8 | UI-REVIEW | Advisory | Minor doubled gap from the zero-height poller |
| UI-9 | UI-REVIEW | Advisory | a11y; the MAX wizard has the same gap, so not a phase regression |
| UI-10 | UI-REVIEW | Advisory | No autofocus; the pre-phase script had none either |
| UI-11 | UI-REVIEW | Advisory | Retry is pointless for a config refusal; text bound by D-09 |
| UI-12 | UI-REVIEW | Advisory | Deliberate per D-04; no action recommended |
| UI-13 | UI-REVIEW | Advisory | Consistent with MAX; enhancement |
| UI-14 | UI-REVIEW | Advisory | Checked for SC1: nothing toggles `hidden`; the CSS rule/comment is dead residue |
| UI-15 | UI-REVIEW | Advisory | Pre-existing; the header link is an exit |
| UI-16 | UI-REVIEW | Advisory | Carried verbatim; `current-password` suggested |
| UI-17 | UI-REVIEW | Deferred → «владелец» | CONTEXT §Landmines: moved verbatim, «решение о нём — не предмет фазы» |

Locked decisions D-02, D-07, D-08, D-09, D-11 and D-13 were treated as intended behaviour, not findings.

## Human Verification Required

### 1. Criterion 4a: scan without 2FA

**Test:** open `/accounts/connect/tg_user`, press «Начать подключение», then scan with the phone (Настройки → Устройства → Подключить устройство).
**Expected:** «Подключено» appears by itself; one account is created; the uvicorn log shows no further `POST …/qr-status` afterwards.
**Why human:** needs a real Telegram account; the server can't be substituted; the live browser needs owner consent.

### 2. Criterion 4b: 2FA account

**Test:** enter a wrong password, then the right one.
**Expected:** «Неверный пароль 2FA.» appears at the field with the field empty, then «Подключено» with one account.
**Why human:** needs a live Telethon session with a 2FA password.

### 3. Criterion 4c: expired code + UI-5

**Test:** don't scan for ≥ ~30 s, then press «Обновить QR-код» and scan the new code.
**Expected:** the «QR-код истёк» step appears by itself; the refresh brings a new QR and polling resumes; the scan connects. Also judge whether the card-height jump on this step is acceptable (UI-5).
**Why human:** Telegram sets the token lifetime; the visual judgement needs a live look.

### 4. Criterion 4d: whole-session expiry

**Test:** stay on «код истёк» for ≥ 270 s, then press refresh.
**Expected:** «Сессия авторизации истекла. Начните заново.»
**Why human:** needs real elapsed session time.

### 5. Prohibitions P1–P8

**Test:** review the verdict table above.
**Expected:** each verdict is accepted, or the one that fails is named.
**Why human:** there is no wired enforcement, so the verifier's reading is not authoritative.

## Gaps Summary

There are none. The phase goal is achieved in the codebase:

- Four wizard routes answer HTML step fragments through `respond()`, from one include behind a permanent anchor.
- `complete` is removed, and the poll is a POST that saves the account itself.
- There is no script, `setInterval`, `fetch(`, JSON or `hidden` toggling left.
- Polling stops by a trigger-less response, proven by a closed rule over rendered responses with negative controls.
- The ownership check exists and is proven non-mutating and indistinguishable from an unknown session.

What remains is a human item, not a gap: the live criterion-4 UAT, plus one visual judgement (UI-5) and confirmation of the eight prohibition verdicts.

Of the 21 advisories, the ones most worth acting on before or with the UAT:

- **UI-1/UI-2/UI-3:** visual regressions this phase introduced. All three are cheap CSS or markup fixes.
- **WR-04:** strengthen the two route race tests so they actually discriminate.
- **WR-02:** narrow the timeout classification.

None of them blocks the phase goal. The owner decides whether any becomes a gap-closure plan. The `--gaps` flow reads this file, so each item is here with its reason.

---

_Verified: 2026-09-21T17:40:19Z_
_Verifier: Claude (gsd-verifier)_

---

## Канонизация вердикта 2026-09-21: `human_needed` → `passed`

Вердикт переведён НЕ пересчётом истин и НЕ повторным прогоном верификатора: счёт остался
**31/32**, и ни одна истина заново не мерялась. Переведены ровно те причины, которые отчёт выше
называл своими словами, — **живой сценарий критерия 4, визуальное суждение UI-5 и восемь
запретов P1–P8**. Все три — пункты ручного обхода, решений владельца вне обхода отчёт не ждал:
гапов ноль, 21 рекомендация помечена как не блокирующая цель.

**Что закрыло причину.** `13-UAT.md` 2026-09-21: `status: complete`, пять ответов `pass`, ноль
расхождений, ноль гапов, **все пять таблиц отметок заполнены**. Правило
`tests/test_planning/test_the_walkthrough_cannot_self_certify.py` зелено при сошедшихся трёх счётах
(`declared=5`, `sections=5`, `tables=5`, `filled=5`); каталог `tests/test_planning/` — 44 passed.
Обход шёл на живом стенде с реальными аккаунтами Telegram (Александр, Chrome 152 / macOS 15).

⚠️ **РАЗНИЦА ДВУХ ФОРМ ЗАКРЫТИЯ, НАЗВАННАЯ ЗДЕСЬ, А НЕ ТОЛЬКО В ОБХОДЕ.**

| Пункты | Чем закрыты |
|---|---|
| 3 (UI-5), 5 (P1–P8) | ДОСЛОВНЫМИ словами владельца: «по высоте меня все устраивает»; `pass` на явный список P1–P8, отвергнутых нет |
| 1, 2, 4 и шаги 3.1, 3.3, 3.4 | ПОДТВЕРЖДЕНИЕМ личного наблюдения владельца на прямой вопрос приёмки: «все было на живом стенде с реальными аккаунтами telegram». Дословного описания признака нет — в клетках стоит подтверждение наблюдения, а не его описание |

Без дословного значения осталась, в частности, обязательная клетка 1.4 (нет новых
`POST …/qr-status` в журнале uvicorn после «Подключено»); названо поимённо в ключе `unrecorded`
шапки обхода.

**Свежесть вердикта сверена ДО перевода.** `git diff --stat bff29f7a..HEAD` по списку
`covered_files` пуст — ни один покрытый вход не менялся с момента вердикта; `verification.status`
до перевода читался `human_needed`, а не `stale`. Отпечаток не пересчитывался.

**Что этой канонизацией НЕ закрыто и закрыто быть не могло:** 21 рекомендация раздела
«Findings Disposition» (в том числе визуальные регрессии фазы UI-1/UI-2/UI-3, WR-04, WR-02) и две
отсрочки владельца (IN-03, UI-17) остаются в прежнем виде; перевод любой из них в гап — решение
владельца, отдельное от вердикта.

### Пересчёт отпечатка покрытых входов после закрытия фазы

`gsd_run query phase.complete 13` правит `.planning/REQUIREMENTS.md`, а она входит в
`covered_files` — отчёт немедленно прочитался `stale`. Отпечаток пересчитан, **вердикт не тронут**:
счёт остался 31/32, ни одна истина заново не мерялась; `status`, `score`, `verified` и
`covered_files` не правились.

Изменение покрытых файлов сверено по `git diff --stat bff29f7a -- <28 файлов covered_files>` ДО
пересчёта и состоит РОВНО из бухгалтерии самого перехода: один файл, `.planning/REQUIREMENTS.md`,
`FETCH-02` — `[ ]` → `[x]` и строка прослеживаемости `Pending` → `Complete`. Существа верификации
оно не трогает, поэтому пересчёт законен.

Значение получено прямым вызовом `computeCoveredDigest(findProjectRoot(phaseDir), covered_files)`
из `gsd-core/bin/lib/verification.cjs` над ПОЛНЫМ списком шапки (28 путей), а не вербом
`verification.fingerprint`, который молча теряет первый переданный путь (дефект записан в
`12-VERIFICATION.md`): `v1:sha256:152df17c…` → `v1:sha256:04d907e0…`.

### Пересчёт отпечатка после быстрой задачи 260921-qvt — по явному разрешению владельца

⚠️ **ЭТО НЕ ПЕРЕСЧЁТ ПО БУХГАЛТЕРИИ, И ГРАНИЦА НАЗВАНА ЗДЕСЬ.** В отличие от пересчёта выше, покрытый
вход изменился КОДОМ: быстрая задача `260921-qvt` (2026-09-21, коммиты `85e84ca3`, `aaaee309`)
правила `app/templates/accounts/includes/tg_connect_step.html`. Верификатор этот шаблон после правки
НЕ перемерял. Вердикт `passed` 31/32 держится здесь на ПОДТВЕРЖДЕНИИ ВЛАДЕЛЬЦА, данном 2026-09-21 на
прямой выбор «повторная проверка верификатором / владелец подтверждает сам» — выбран второй вариант.
`status`, `score`, `verified`, `covered_files` и блоки шапки (`advisory`, `deferred`,
`human_verification`) не правились.

**Что изменилось во входах — измерено, а не пересказано.** `git diff --stat ab72d228..HEAD` по 28
путям `covered_files` — ОДИН файл, `tg_connect_step.html` (+24/−6). Прежнее значение отпечатка
`v1:sha256:04d907e0…` воспроизведено той же функцией `computeCoveredDigest` над деревом `ab72d228`
(выгрузка `git archive` по тем же 28 путям) байт в байт, поэтому новое значение
`v1:sha256:0e9da87d…` отличается от прежнего ТОЛЬКО этой правкой шаблона. `app/static/css/app.css` и
новый `tests/test_templates/test_tg_connect_step_layout.py` в `covered_files` не входят.

**Что это за правка.** Ровно рекомендации этого отчёта UI-1 и UI-3 (UI-2 — одним правилом `app.css`):
на шаге пароля поле и ряд действий обёрнуты во внутреннюю колонку `div.connect-step__form` (приём
шага телефона мастера MAX — то исправление, которое отчёт сам советовал «before or with the UAT»);
в ряды действий шагов старта/ошибки и `qr_expired` добавлена подпись
`<span class="connect-step__busy">Загрузка...</span>`, которую показывает только CSS по атрибуту
`disabled` кнопки отправки. Скрипта, обработчиков и атрибута `hidden` не добавлено; опросчик шага
ожидания, `POLLING_CASES` и вызовы `form_wrapper` не тронуты.

**Чем правка проверена (машиной, после последнего кодового коммита):** новая регрессия — 10 проверок,
каждая сперва красная на своём утверждении (RED записан в SUMMARY задачи); маршрутные тесты мастера
вместе с ней — 66 passed, перепрогнано оркестратором, включая
`test_the_wizard_page_carries_no_client_script` (критерий 1); набор из восьми файлов гейтов разметки и
слоя ответа — 390 passed; `test_shell.py` — 245 passed; `tests/test_planning/` — 44 passed. Живой
взгляд на вёрстку в браузере НЕ снят — он за владельцем (пункт D4 `260921-qvt-SUMMARY.md`,
`human_judgment: true`).

**Рекомендации UI-1, UI-2, UI-3** закрыты этой задачей по существу; их записи в `advisory` шапки не
переписывались — история отчёта сохраняется, закрытие названо здесь.
