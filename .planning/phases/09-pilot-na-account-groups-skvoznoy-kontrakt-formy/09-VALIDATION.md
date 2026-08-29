---
phase: 9
slug: pilot-na-account-groups-skvoznoy-kontrakt-formy
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-29
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Источник: `09-RESEARCH.md` §Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio; httpx `AsyncClient` через `ASGITransport`; in-memory SQLite (`sqlite+aiosqlite:///:memory:`) |
| **Config file** | `pyproject.toml`; фикстуры — `tests/conftest.py` (`client`, `authed_client`, `htmx_client`, `db_session`) |
| **Quick run command** | `uv run pytest tests/test_templates/test_htmx_markup_gates.py tests/test_pages/test_htmx_gates.py tests/test_pages/test_account_groups.py -q` |
| **Full suite command** | `just test` (`uv run pytest tests/ -v`) |
| **Estimated runtime** | ~5 с быстрый круг; гейтовый круг (`test_htmx_markup_gates.py` + `test_htmx_gates.py` + `test_components.py`) ~2 с |

---

## Sampling Rate

- **After every task commit:** `uv run pytest tests/test_templates/test_htmx_markup_gates.py tests/test_pages/test_htmx_gates.py tests/test_pages/test_account_groups.py -q` (~5 с). Достаточно, потому что предмет фазы — ровно эти три файла плюс `test_components.py`.
- **After every plan wave:** `uv run pytest tests/test_templates/ tests/test_pages/ -q`
- **Before `/gsd-verify-work`:** `just test` целиком, зелёная.
- **Max feedback latency:** 5 секунд

⚠️ В полном прогоне известен красный `full-suite-ads-editor-order-pollution` (`.planning/todos/pending/`) — предмет порядка исполнения сюиты, не htmx. Фаза его **не втягивает** (то же основание, по которому его не втянула Фаза 8), но обязана отличать его от собственной регрессии.

---

## Per-Task Verification Map

> Заполняется планировщиком при нарезке фазы на планы: `Task ID` появляется только вместе с PLAN.md.
> Строки ниже — требование → поведение → команда, снятые с §Phase Requirements → Test Map разведки;
> планировщик обязан привязать каждую к задаче, а не переписывать заново.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-01-T1 | 09-01 | 1 | FORM-02 | — | тумблер без htmx → 302 на экран групп (деградация) | route | `uv run pytest tests/test_pages/test_account_groups.py -k degrades_without_htmx -x` | ❌ W0 | ⬜ pending |
| 09-02-T1 | 09-02 | 2 | FORM-02 | T-9-07 | повторное удаление безвредно и не выдаёт чужие `id` | route | `uv run pytest tests/test_pages/test_account_groups.py -k repeated_delete_is_harmless -x` | ✅ (переезжает дословно, D-04) | ⬜ pending |
| 09-01-T1, 09-02-T1 | 09-01, 09-02 | 1, 2 | FORM-02 | — | `hx-post` == `action` посимвольно; тег `<form>`; `method="post"`; `action` ведёт на маршрут полного документа (GATE-04) | gate | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -q` | ✅ (требует `MACRO_DEFINITION_SITES` и γ1) | ⬜ pending |
| 09-01-T1 | 09-01 | 1 | FORM-02 | — | тумблер: 200 + фрагмент с `id="group-row-N"`, без `<!DOCTYPE` | integration | `uv run pytest tests/test_pages/test_account_groups.py -k returns_the_row_fragment -x` | ❌ W0 | ⬜ pending |
| 09-02-T1 | 09-02 | 2 | FORM-02 | — | удаление: OOB-узлы снятия строки и панели + счётчик | integration | `uv run pytest tests/test_pages/test_account_groups.py -k delete_returns_oob_nodes -x` | ❌ W0 | ⬜ pending |
| 09-02-T1 | 09-02 | 2 | FORM-02 | T-9-10 | опустевший список → 204 + `HX-Location` (D-09) | integration | `uv run pytest tests/test_pages/test_account_groups.py -k last_group_goes_to_location -x` | ❌ W0 | ⬜ pending |
| 09-01-T1 | 09-01 | 1 | FORM-02 | T-9-02 | чужая/несуществующая группа → 204 + `HX-Location`; «нет такой» и «чужая» неотличимы (D-13) | integration | `uv run pytest tests/test_pages/test_account_groups.py -k foreign_toggle_goes_to_location -x` | ❌ W0 | ⬜ pending |
| 09-01-T1 | 09-01 | 1 | FORM-02 | T-9-01 | фрагментный путь не ослабил тройной `WHERE`: `account_id` из URL не доверяется | route | `uv run pytest tests/test_pages/test_account_groups.py -k does_not_trust_the_account_id -x` | ⚠️ есть, нужна пара под `htmx_client` | ⬜ pending |
| 09-01-T1 | 09-01 | 1 | FORM-02 | — | ответ тумблера НЕ несёт второй панели подтверждения (⚠️ `outerHTML` вставляет весь ответ) | integration | `uv run pytest tests/test_pages/test_account_groups.py -k fragment_carries_no_second_modal -x` | ❌ W0 | ⬜ pending |
| 09-01-T2 | 09-01 | 1 | FORM-02 | — | OOB-узлы стоят на верхнем уровне ответа (⚠️ `allowNestedOobSwaps: false`) | template gate | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -k top_level -x` | ❌ W0 | ⬜ pending |
| 09-01-T2 | 09-01 | 1 | FORM-02 | — | долгоживущая область подменяется СОДЕРЖИМЫМ, а не узлом (D-12) | template gate | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -k long_lived_region -x` | ❌ W0 | ⬜ pending |
| 09-01-T1 | 09-01 | 1 | FORM-09 | — | новый макрос-обёртка — документированный, без контекста, без `\|safe`; запись в `COMPONENT_CALLS` | gate | `uv run pytest tests/test_templates/test_components.py -q` | ✅ частично | ⬜ pending |
| 09-03-T1 | 09-03 | 3 | FORM-09 | T-9-12 | каждый `hx-post` рождён компонентным макросом; перечень исключений утверждается ЧИСЛОМ (D-03) | gate | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -k born_of_a_component_macro -x` | ❌ W0 | ⬜ pending |
| 09-01-T3 | 09-01 | 1 | QUAL-01 | — | `hx-disabled-elt` присутствует и целится как объявлено; исключения перечнем с числом, обоснование называет цену отмены QUAL-06 (D-06) | gate | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -k disabled_elt -x` | ❌ W0 | ⬜ pending |
| 09-02-T3 | 09-02 | 2 | QUAL-01 | — | кнопка Отмены панели подтверждения не блокируется никогда | gate | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -k cancel_is_never_disabled -x` | ❌ W0 | ⬜ pending |
| 09-01-T3 | 09-01 | 1 | QUAL-02 | — | `hx-indicator` присутствует; класс и порог в `app.css`; имя класса ≠ `htmx-indicator` (⚠️ Pitfall 3) | gate | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -k indicator -x` | ❌ W0 | ⬜ pending |
| 09-01-T1 | 09-01 | 1 | QUAL-06 | — | чекбокс несёт стабильный `id` в разметке фрагмента | integration | `uv run pytest tests/test_pages/test_account_groups.py -k fragment_keeps_the_toggle_id -x` | ❌ W0 | ⬜ pending |
| 09-04-T1 | 09-04 | 3 | QUAL-02 | T-9-15 | плашка обрыва связи называет расхождение экрана с сервером (D-16) | gate | `uv run pytest tests/test_pages/test_shell.py -k network_banner_names -x` | ❌ W0 | ⬜ pending |
| 09-03-T3 | 09-03 | 3 | — | T-9-14 | восемь инвентарных чисел сдвинуты, четыре подтверждены неподвижными (включая литерал `len(paths)`) | gate | `uv run pytest tests/test_templates/test_htmx_markup_gates.py tests/test_pages/test_htmx_gates.py -q` | ✅ (числа править) | ⬜ pending |
| 09-01-T1, 09-02-T1 | 09-01, 09-02 | 1, 2 | — | T-9-03 | G-2: у переведённых обработчиков нет собственного `RedirectResponse` | gate | `uv run pytest tests/test_pages/test_htmx_gates.py -k own_redirect -x` | ✅ (впервые с предметом) | ⬜ pending |
| 09-03-T2 | 09-03 | 3 | — | T-9-13 | D-08: внутри шаблона, объявляющего цель подмены, допустим только голый `x-data` | gate | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -k client_state_expression -x` | ❌ W0 | ⬜ pending |
| 09-02-T2 | 09-02 | 2 | — | T-9-09 | G-11 закрыт ИЗМЕРЕНИЕМ; выбранная ветвь несёт третий тест, не дающий перечню превратиться в ложь | gate | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -k "two_role or parametric" -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Каркаса тестов заводить **не нужно**: фреймворк, фикстуры (`htmx_client`) и обе парные спецификации уже существуют. Wave 0 — это недостающие УТВЕРЖДЕНИЯ, а не инфраструктура. Каждый пункт привязан к задаче, внутри которой он пишется **до** правки предмета (TDD-порядок: число и пара двигаются первыми, разметка делает их зелёными).

- [ ] **09-01-T1** — `tests/test_pages/test_account_groups.py`: пары `htmx_client` для `account_groups_toggle` по канонической форме D-16 Фазы 8; «ответ тумблера без второй панели»; «фрагмент несёт `id` чекбокса»; пара к `test_toggle_does_not_trust_the_account_id_from_the_url`
- [ ] **09-01-T1** — `tests/test_templates/test_htmx_markup_gates.py`: переписать `test_toggle_is_a_real_post_form` под `hx-trigger="change"` (⚠️ Pitfall 9), сохранив вторую половину дословно
- [ ] **09-01-T1** — перечень `MACRO_DEFINITION_SITES` (§2.5 β) с числом, обоснованием и компенсацией `test_every_macro_definition_site_is_a_component`
- [ ] **09-01-T1** — запись нового макроса в `COMPONENT_CALLS` (`tests/test_templates/test_components.py:576-596`)
- [ ] **09-01-T2** — «OOB-узлы верхнего уровня» и «долгоживущая область подменяется содержимым» (D-12) + два контроля
- [ ] **09-01-T3** — перечень `DISABLED_ELT_EXCEPTIONS` (D-06) с числом и ценой отмены QUAL-06 словами; два гейта индикатора + контроль
- [ ] **09-02-T1** — пары `htmx_client` для `account_groups_delete`; «удаление последней группы → 204 + `HX-Location`»; пара к `test_delete_does_not_trust_the_account_id_from_the_url`
- [ ] **09-02-T2** — G-11: измерение пересечения и по его результату — `ID_IN_TWO_ROLES_BY_DESIGN` (§1.3) либо `PARAMETRIC_SWAP_TARGETS` с несущим правилом «цель либо литеральная, либо объявленная параметрическая»
- [ ] **09-02-T3** — гейт «кнопка Отмены не блокируется никогда» + контроль
- [ ] **09-03-T1** — перечень `MACRO_BORN_EXCEPTIONS` (D-03) с числом + контроль
- [ ] **09-03-T2** — гейт D-08 (граница Alpine, вариант D-08a) + контроль
- [ ] **09-03-T3** — восемь инвентарных чисел, включая литерал `len(paths)` в `test_htmx_markup_gates.py:909`; положительный контроль читает все новые константы
- [ ] **09-04-T1** — `tests/test_pages/test_shell.py`: `test_the_network_banner_names_the_screen_server_divergence` с ожиданием, выписанным строкой в тесте

⚠️ **Случаи контроля на каждое новое правило обязательны** (раздел «ГРУППА КОНТРОЛЯ», `test_htmx_markup_gates.py:1383-1434`): без них правило зелено по построению и не доказывает ничего. `_tree_with` несёт двойной предохранитель — образец подстановки обязан встретиться ровно один раз, и результат обязан отличаться от исходника.

---

## Manual-Only Verifications

⚠️ **Линия, которую сюита не пересекает.** Критерий 4 роадмапа: «сервером это не доказуемо **в принципе** — httpx не свопает и не собирает OOB». Playwright отклонён на уровне вехи (`REQUIREMENTS.md:103`, отложен как `E2E-01`). Сюита утверждает **доставку** разметки и заголовков, но не **эффект**. Обе половины выписаны поимённо, иначе аудит запишет здесь ложное покрытие.

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Своп произошёл и ИМЕННО в тот элемент; OOB-счётчик приземлился куда задумано; позиция прокрутки не потеряна | FORM-02, QUAL-06 | httpx не свопает и не собирает OOB; браузерный стенд отклонён вехой | UAT-3: прокрутить список ниже сгиба, переключить тумблер средней строки → строка перерисовалась на месте, список не дёрнулся, число вверху изменилось |
| Фокус после подмены вернулся на элемент с тем же `id` | QUAL-06 | Требует живого `document.activeElement` | UAT-3: переключить тумблер **клавиатурой** (Space) → фокус остался на том же тумблере. ⚠️ **Ожидаемый ответ сегодня — «нет»**: см. §4.3 разведки — `hx-disabled-elt` (D-06) снимает блокировку ПОСЛЕ свапа, активный элемент успевает стать `<body>`. Проверить, а не предположить; три способа снятия конфликта названы в §4.3 |
| `hx-indicator` виден на медленной сети и не мигает на быстрой (порог 300 мс) | QUAL-02 | Порог видимости — свойство времени и глаза | UAT-6: DevTools → Network throttling «Slow 3G» → индикатор появляется; без троттлинга — не мигает |
| `hx-disabled-elt` реально мешает второму нажатию | QUAL-01 | Защита от двойного клика — свойство браузера | UAT-6: быстро нажать дважды → второй запрос не уходит |
| Панель подтверждения после подмены строки не задвоилась; Alpine в ней жив | — (граница D-02, D-08) | Требует живого Alpine и DOM после свапа | UAT-5 (частично): удалить группу → осиротевшая панель снята; открыть подтверждение у соседней строки → работает |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
