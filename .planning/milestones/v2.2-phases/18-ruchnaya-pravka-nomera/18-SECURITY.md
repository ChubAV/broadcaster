---
phase: "18"
slug: "ruchnaya-pravka-nomera"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-11-21"
---

# Phase 18 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Реестр собран из блоков `<threat_model>` планов 18-01…18-03 (составлен на этапе плана) и разделов `## Threat Flags` трёх сводок; новых поверхностей сводки не заявили (единственный новый сетевой адрес — `POST /accounts/{id}/phone` — целиком назван в реестре плана 18-02). Уровень ASVS 1, порог блокировки `high`: сверка мер — по коду и тестам на уровне grep, аудитор не порождался (короткий путь `/gsd-secure-phase`: `threats_open: 0`, реестр плановый, ASVS 1). `T-18-SC` повторяется во всех трёх планах как одна и та же угроза и записан один раз. Все тесты-улики ниже зелены в полной суите на `d197f956` (6035 passed, 2 skipped).

Дополнено 2026-11-24 (перепроверка перед раундом 3 верификации, `/gsd-execute-phase 18`): реестр впервые принял угрозы гап-раунда T-18-17…T-18-24 из `<threat_model>` планов 18-04…18-08 и их границы доверия — аудит 2026-11-21 прошёл до гап-раунда, и эти строки в реестр не попадали. `T-18-SC` теперь стоит во всех восьми планах и по-прежнему записан один раз. Строки T-18-01…T-18-16 и T-18-SC ниже — снимок 2026-11-21: ссылки на строки `app/pages/account_groups.py` сдвинул рефакторинг плана 18-07, актуальные номера названы в разделе «Security Audit 2026-11-24».

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| колонки `phone` / `phone_is_manual` → подпись на экранах | хранимое значение номера — недоверенная строка; флаг — булево из базы под CHECK | номер аккаунта (персональные данные пользователя), признак ручного ввода |
| строки аккаунтов пользователя → признак двойника и пометка | загрузчик `load_account_rows` читает строки ТОЛЬКО своего пользователя | `id`, `type`, `phone`, `phone_is_manual` |
| браузер → `POST /accounts/{id}/phone` | `account_id` из адреса и `phone` из тела — от недоверенного клиента; аутентификация cookie | номер в теле запроса |
| страница → единственный писатель `set_manual_phone` | писатель владельца не проверяет (T-16-19) — проверка на маршруте | `account_id`, текст номера |
| ответ → журнал, адрес, уведомление | номер не покидает тело запроса и колонку | код исхода (`phone_saved` / `phone_cleared`), `account_id`, `phone_set` |
| администратор под имперсонацией → данные пользователя | маршрут разрешён решением D-06 | номер аккаунта пользователя |
| карточка аккаунта → адрес ссылки | в адрес уходит только числовой идентификатор своего аккаунта и якорь `#phone` | `account_id` |
| браузер → `/accounts/{id}/sync-status` | идентификатор из адреса; владение проверяет `get_sync_status_view` | подпись и ссылка во фрагменте опроса |
| таблица стилей → то, что видит человек (18-04) | CSS не обрабатывает недоверенный ввод; риск — скрыть от глаз поле с фокусом или состояние номера | — (раскладка) |
| ответ → фокус клавиатуры (18-05) | разметка ответа решает, куда встанет фокус | признак `autofocus` |
| таблица стилей → доступность формы (18-07) | раскладка не должна разрывать связь подписи и поля | связь `for` / `id` макроса `field` |
| ответ 422 → области уведомления шелла (18-08) | ответ 422 впервые пишет в вежливую область — только пустое содержимое | пустая подмена содержимого `#notice` |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-18-01 | Spoofing (ложная пометка «указан вручную» у «Номер неизвестен») | `label_of`, `build_labels`, макрос | low | mitigate | флаг подписи = `phone_is_manual and shown is not None`; `tests/test_services/test_account_label.py::test_a_flag_without_a_number_never_marks_the_unknown_label` | closed |
| T-18-02 | Information Disclosure (флаг или номер чужого аккаунта в подписи) | `load_account_rows` | medium | mitigate | граница `WHERE user_id = …` не менялась, добавлена только колонка; `tests/test_application/test_account_label_rows.py` (`test_rows_carry_the_manual_f…`) и тест загрузчика Фазы 17 на чужие строки | closed |
| T-18-03 | Tampering (XSS через подпись) | `components/account_label.html` | low | mitigate | пометка — статичный текст шаблона; номер только автоэкранированием; `MARKUP_BUILDERS = 0` (`tests/test_templates/test_htmx_markup_security.py`); в шаблонах фазы `|safe` / `Markup` — 0 вхождений | closed |
| T-18-04 | Tampering / Information Disclosure (IDOR: правка номера чужого аккаунта; закрывает T-16-19) | `account_phone_save` | high | mitigate | `app/pages/account_groups.py:447-452` — `_load_owned_account` до писателя; чужой = несуществующий = вне колонки → `redirect="/accounts"`; `LookupError` писателя → то же (`:490-491`); тесты неотличимости в `tests/test_pages/test_account_phone_form.py` | closed |
| T-18-05 | Tampering (межсайтовая подделка по cookie) | `account_phone_save` | high | mitigate | `app/pages/account_groups.py:434-435` — `is_same_origin` → `Response(status_code=403)` до выборки; `test_a_cross_origin_post_is_refused_before_any_lookup`; гейт `test_origin_guard_on_destructive_routes.py` | closed |
| T-18-06 | Tampering (XSS через эхо введённого значения) | `phone_form.html`, `field` | high | mitigate | эхо только автоэкранированием макроса `field`; в `phone_form.html` / `phone_response.html` нет `|safe` и `Markup`; тест с враждебным значением в `test_account_phone_form.py` | closed |
| T-18-07 | Information Disclosure (номер в адресе, уведомлении, журнале) | обработчик, реестр уведомлений | high | mitigate | номер только в теле POST; в `Location` — код реестра; тексты «Номер сохранён.» / «Номер удалён.» (`app/pages/notices.py:316-317`) без номера; журнал `account_phone_saved` — только `account_id`, `phone_set` (`:494`); гейты `tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py` | closed |
| T-18-08 | Tampering (стирание номера POST-ом без поля) | сигнатура обработчика | medium | mitigate | мера реализована иначе, чем в плане (`Form(...)` отвергал пустую строку на FastAPI 0.129): `phone: str \| None = Form(None)` + явная сверка `"phone" not in await request.form()` → `RequestValidationError` до выборки (`app/pages/account_groups.py:440-444`); `test_a_post_without_the_field_leaves_the_number_untouched` | closed |
| T-18-09 | Denial of Service (идентификатор вне колонки — 500 драйвера) | параметр пути | medium | mitigate | `PostIdPath` + `id_in_column(account_id)` первым использованием (`:447`); гейт `test_identifier_bounds.py`; случай `ID_MAX + 1` в тесте неотличимости | closed |
| T-18-10 | Repudiation (правка под имперсонацией без отметки актора) | журнал `account_phone_saved` | low | accept | см. AR-18-01 | closed |
| T-18-11 | Tampering (запись мимо единственного писателя; границы Фазы 16 CR-09, WR-40, IN-29, T-16-145) | новый код маршрута | high | mitigate | колонки пишет только `set_manual_phone` (`:456`); гейты `tests/test_application/test_phone_single_writer_gate.py`, `test_phone_writer_runtime_guard.py` зелены (1161 в наборе гейтов номера) | closed |
| T-18-12 | Elevation of Privilege (изменяющий маршрут открыт под имперсонацией) | `ALLOWED_ROUTES` | low | accept | см. AR-18-02; причина записана в `tests/test_pages/test_impersonation_gate.py:260`; `test_the_phone_edit_is_allowed_under_another_identity` | closed |
| T-18-13 | Denial of Service (эхо длинного ввода в 422) | `_page`, `_error_fragment` | low | accept | см. AR-18-03 | closed |
| T-18-14 | Information Disclosure (номер в трассировке 500) | ветки отказа писателя | medium | mitigate | без отката сессии (в `account_groups.py` `rollback` — 0 вхождений; 500 `MissingGreenlet` исключён); `user_id` берётся до писателя (`:454`); тест 422 на htmx | closed |
| T-18-15 | Information Disclosure (номер в адресе ссылки и в журнале запросов) | три шаблона карточки | medium | mitigate | девять `href` вида `'/accounts/' ~ account.id ~ '/groups#phone'` (`accounts/list.html`, `partial_cards.html`, `partials/sync_status_card.html` — по три); `test_the_phone_link_carries_no_number` | closed |
| T-18-16 | Information Disclosure (ссылка к номеру у чужого аккаунта во фрагменте опроса) | `sync_status_card.html` | low | mitigate | карточка со ссылкой рисуется только после проверки владельца в `get_sync_status_view`; `test_a_foreign_account_poll_draw…` (`tests/test_pages/test_account_phone_links.py`) | closed |
| T-18-17 | Tampering (липкая шапка закрывает поле с фокусом — ввод идёт в невидимое поле) | `html { scroll-padding-top }` | low | mitigate | `app/static/css/app.css:446` — `scroll-padding-top: 170px`, `:503` — `236px` при ≤860 px; `tests/test_pages/test_responsive_markup.py::test_the_document_scroll_padding_clears_the_sticky_head` (`:5466`); геометрию на 1280/375/320 px принял владелец (`18-UAT.md`, тесты 8 и 13, «принимаю все», 2026-11-22) | closed |
| T-18-18 | Spoofing (ручной номер неотличим от автоматического, когда пометка усечена в чипе или `<h2>`) | правило пометки, `title=` чипа | low | accept | см. AR-18-04 | closed |
| T-18-19 | Tampering (XSS через эхо введённого значения в новом файле ответа 422) | `phone_error_response.html` | high | mitigate | своих выводов значения в файле нет: только `{% include "account_groups/includes/phone_form.html" %}` и пустой `<div hx-swap-oob="innerHTML:#notice"></div>`; эхо — автоэкранированием макроса `field`; `\|safe` / `Markup` в `phone_error_response.html`, `phone_form.html`, `phone_response.html` — 0; враждебное `"><script>alert(1)</script>` с `HX-Request` → 422, `&lt;script&gt;` в ответе (`tests/test_pages/test_account_phone_form.py:336-345`) | closed |
| T-18-20 | Information Disclosure (номер или исход в блоке, снимающем плашку) | `phone_error_response.html` | medium | mitigate | блок пуст (последняя строка файла); `test_a_422_htmx_answer_clears_the_previous_notice` (`tests/test_pages/test_account_phone_form.py:357`) утверждает пустоту блока и отсутствие кодов, текстов исхода и цифр номера | closed |
| T-18-21 | Denial of Service (кража фокуса, класс CR-01: ввод уходит не туда) | `autofocus` в ответах формы | low | mitigate | `autofocus=phone_focus` (`app/templates/account_groups/includes/phone_form.html:88`), флаг ставит только ответ на отправку (`_phone_form_context(..., focus=...)`, `app/pages/account_groups.py:237`); `test_the_plain_screen_never_autofocuses_the_field` (`test_account_phone_form.py:735`) | closed |
| T-18-22 | Tampering / Repudiation (тихая потеря пометки «указан вручную» во фрагменте опроса) | `SyncStatusView`, `get_sync_status_view` | low | mitigate | `@dataclass(slots=True, kw_only=True)` без умолчаний (`app/application/accounts/dto.py:6-7`); один конструктор в `get_sync_status_view` (`app/application/accounts/use_cases.py:62`); `tests/test_pages/test_account_label_accounts.py::test_sync_status_view_has_no_defaults` (`:294`) | closed |
| T-18-23 | Repudiation / Information Disclosure (читалка не озвучивает ошибку поля, если раскладка разорвала связь подписи и поля) | `[data-acct-phone] .field { display: contents }` | low | mitigate | связь — `for="{{ field_id }}"` / `id="{{ field_id }}"` макроса `field` (`app/templates/components/field.html:14`, `:16`), раскладка (`app.css:2914`) её не задаёт; имя поля в дереве доступности и щелчок по подписи проверил обход (`18-UAT.md`, тесты 10 и 11, «принимаю все», 2026-11-22) | closed |
| T-18-24 | Tampering (рефакторинг контекста перепутал аккаунт или пользователя — форма пишет не в тот аккаунт) | `_screen_context`, `_phone_form_context` | medium | mitigate | ключевые-только параметры (`_screen_context(*, …)`, `app/pages/account_groups.py:265`; `_phone_form_context(account_id, *, …)`, `:237`), `account_id = account.id` проверенного владельцем аккаунта (`:296`); тесты неотличимости чужого аккаунта и адреса формы (`tests/test_pages/test_account_phone_form.py`, `tests/test_pages/test_htmx_post_pairs.py`) | closed |
| T-18-SC | Tampering | npm/pip/cargo installs | high | mitigate | установок нет: `git diff bff2d1ea..HEAD` по `pyproject.toml`, `uv.lock`, `*package*.json`, `requirements*.txt` пуст | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-18-01 | T-18-10 | D-06: номер — подпись, на доставку не влияет; форма журнала ограничена D-16 (`account_id`, `phone_set`); запись о самой имперсонации ведёт её механизм | владелец (D-06, `18-CONTEXT.md`) | 2026-11-21 |
| AR-18-02 | T-18-12 | D-06 / PHONE-11: правка под имперсонацией разрешена с записанной причиной; гейт имперсонации требует причину для каждого разрешённого изменяющего маршрута | владелец (D-06, `18-CONTEXT.md`) | 2026-11-21 |
| AR-18-03 | T-18-13 | `maxlength` 64 у людей; не-браузер ограничен пределом части формы Starlette; ответ — автоэкранированное эхо без повторной обработки | план 18-02 (решение фазы) | 2026-11-21 |
| AR-18-04 | T-18-18 | при нехватке ширины пометка «указан вручную» уступает место первой (G-18-6), а `title=` чипа и `<h2>` пометки не несут; номер — подпись, на доставку не влияет (D-06). Отложено планом 18-04 (scope_note) до решения по `18-UI-REVIEW.md` UI-R-04 (открыто). Владельцу решение о пометке в `title=` не предлагалось (`18-UAT.md`, «Решения владельца для gap-раунда»): его решение касается только усечённого номера с полным текстом в `title=` в чипе на 320 px — слова «решение владельца» в строке T-18-18 плана 18-04 шире записанного | план 18-04 (решение фазы) | 2026-11-21 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-21 | 17 | 17 | 0 | `/gsd-secure-phase 18` (оркестратор из `/gsd-execute-phase 18`, шаг verify:post; L1 grep; аудитор не порождался — короткий путь ASVS 1) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-21

## Security Audit 2026-11-24

| Metric | Count |
|---|---|
| Threats found | 25 |
| Closed | 25 |
| Open | 0 |

Перепроверка перед раундом 3 верификации (`/gsd-execute-phase 18`, вердикт `stale`: покрытый `app/pages/accounts.py` правили 19-01, 19-05, 19-06, 19-07 — только потоки подключения); вёл оркестратор, аудитор не порождался. Реестр впервые дополнен угрозами гап-раунда T-18-17…T-18-24 (`<threat_model>` планов 18-04…18-08): аудит 2026-11-21 прошёл до гап-раунда. Короткий путь `secure-phase`: `threats_open: 0`, реестр составлен при планировании (`<threat_model>` во всех 8 планах), `asvs_level: 1`; меры сверены грепом L1 на `eeb44eed`. Ни одна прежняя угроза не переоткрыта. Тесты-улики зелены в свежей полной суите на `eeb44eed`: 6298 passed, 2 skipped, 0 failed (`.pytest_cache/gsd-orch/suite-p18r.log`).

- **T-18-17…T-18-24 (новые строки).** Улики — в реестре выше, каждая сверена по коду и имени теста на `eeb44eed`.
- **T-18-18 (принятие плана, не владельца).** Записано как AR-18-04 с автором «план 18-04 (решение фазы)», по образцу AR-18-03. Строка плана 18-04 называет это «решением владельца», но `18-UAT.md` («Решения владельца для gap-раунда») прямо говорит, что пометка в `title=` владельцу не предлагалась. Угроза низкая, ниже порога `high`, в `threats_open` не входит; открытая находка `18-UI-REVIEW.md` UI-R-04 ждёт решения владельца.
- **T-18-04 / T-18-05 / T-18-08 / T-18-09 / T-18-11 / T-18-14 (сдвиг строк).** Меры на месте, строки `app/pages/account_groups.py` сдвинул рефакторинг 18-07: `is_same_origin` — `:470` (было `:434-435`); `"phone" not in submitted` → `RequestValidationError` — `:477-478` (было `:440-444`); `id_in_column(account_id)` — `:483` и `_load_owned_account` — `:485` (было `:447-452`); `user_id` до писателя — `:490` (было `:454`); `set_manual_phone` — `:492` (было `:456`); `except LookupError` — `:539` (было `:490-491`); журнал `account_phone_saved` (`account_id`, `phone_set`) — `:543` (было `:494`); `rollback` в файле — 0. `app/pages/notices.py:316-317` не сдвинулись.
- **T-18-15 / T-18-16 после фазы 19.** Правки фазы 19 в `app/pages/accounts.py` — только потоки подключения TG/WA/MAX; обработчик опроса `accounts_sync_status` (`:1073`) строит подпись после `view is not None` (`:1098-1099`), шаблоны карточки не менялись.
- **T-18-SC.** 24 коммита задач 18-04…18-08 не трогают `pyproject.toml`, `uv.lock`, `*package*.json`, `requirements*.txt`. После закрытия фазы (`5e7769bb`) зависимости изменила только `7153c9fb` (quick-261123-bgc, 2026-11-23): `maxapi-python` в dev-группе 2.3.1 → 2.5.0 — вне фазы 18, легитимность проверена в той быстрой задаче и в раунде 14 фазы 16.
