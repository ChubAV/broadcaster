---
phase: "17"
slug: "pokaz-nomera-na-vseh-ekranah"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-11-21"
---

# Phase 17 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Реестр собран из блоков `<threat_model>` планов 17-01…17-09 (составлен на этапе плана) и разделов `## Threat Flags` девяти сводок; новых поверхностей сводки не заявили. Уровень ASVS 1, порог блокировки `high`: сверка мер — по коду и тестам на уровне grep, аудитор не порождался (короткий путь `/gsd-secure-phase`: `threats_open: 0`, реестр плановый, ASVS 1). `T-17-SC` повторяется во всех девяти планах как одна и та же угроза и записан один раз.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| колонка `messenger_accounts.phone` → HTML (`<span>`, `title=`, `<title>`, `<h1>`/`<h2>`, `<option>`, `body=` модалок) | хранимое значение, в т.ч. неразбираемое «как есть», — недоверенная строка на каждом приёмнике | номер аккаунта (персональные данные пользователя) |
| страница пользователя → загрузчик строк `load_account_rows` | условие владельца `user_id` в единственном запросе карты | `id`, `type`, `phone` аккаунтов пользователя |
| браузер → `/accounts/{id}/sync-status` | идентификатор аккаунта из адреса; владение проверяет `get_sync_status_view` | подпись аккаунта во фрагменте опроса |
| журнал отправок → карточка и CSV истории | аккаунт выводится только через `Group.account_id` записей самого пользователя | номер в карточке и в ячейке «Номер» |
| колонка `phone` → файл CSV → табличный редактор | значение на `= + - @` исполняется как формула | номер без ведущего «+» |
| администратор → номера пользователей | номера чужих аккаунтов видны только за `require_admin` (PHONE-06); карта — по пользователю из адреса | номера всех аккаунтов просматриваемого пользователя |
| новый код → журналы | номер и подпись не уходят в вызовы журнала (PHONE-21, D-08) | — |
| будущая правка шаблона → суита | гейт `#id` и проход подписи — машинное препятствие возврату `#id` аккаунта вне помощника | — |
| обход D-21 → боевая база | засев и чистка пяти образцов под сессией владельца (О-1 (б)) | тестовые строки `messenger_accounts` |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-17-01 | Tampering (хранимый XSS через значение «как есть») | `components/account_label.html`, `plain` в `title=` и звене `join` | high | mitigate | Только автоэкранирование Jinja; `|safe` / `Markup(` в `account_label.html`, `app/services/account_label.py` и шаблонах фазы не найдено; правила `MARKUP_BUILDERS`, `UNSAFE_MARKERS` в `tests/` | closed |
| T-17-02 | Information Disclosure (номера чужих аккаунтов) | `load_account_rows` | high | mitigate | `MessengerAccount.user_id == user_id` в единственном запросе (`app/application/accounts/labels.py`); `test_rows_never_carry_another_users_account` | closed |
| T-17-03 | Information Disclosure (`credentials` / строка сессии в памяти страницы) | `load_account_rows` | medium | mitigate | Проекция трёх колонок `id`, `type`, `phone`; `credentials`/`session_data` в коде подписи не встречаются | closed |
| T-17-04 | Information Disclosure (номер в журнале) | новый код фазы | medium | mitigate | В `account_label.py` и `labels.py` нет `logger`/`logging`/`structlog`; `tests/test_phone_privacy_gate.py` | closed |
| T-17-05 | Information Disclosure (номер чужого аккаунта во фрагменте опроса) | `accounts_sync_status` | high | mitigate | Подпись после `view is not None`, соседи — `load_account_rows(db, user.id)`; `test_a_foreign_account_poll_draws_no_label` | closed |
| T-17-06 | Tampering (подпись в выражении Alpine/`hx-*`) | `accounts/list.html`, `partial_cards.html` | high | mitigate | В `x-*` / `@…` / `hx-*` / `$dispatch` подпись (`acct_label`, `.plain`) не встречается — только числовой `account.id`; подпись — текст элемента и `body=` модалки | closed |
| T-17-07 | Tampering (удаление не того аккаунта: двойники неразличимы в модалке) | модалка `acc-del-<id>` | medium | mitigate | `body=` — `plain` с `#id` у двойника (D-13); на бою 2026-11-21 (UAT тест 1) модалка #81 показала «MAX +86 138 0013 8000 #81» целиком | closed |
| T-17-08 | Denial of Service (лишний `SELECT` на тик опроса) | `accounts_sync_status` | low | accept | См. Accepted Risks Log AR-17-01 | closed |
| T-17-09 | Tampering (хранимый XSS в `<title>` / заголовках) | `account_groups/list.html` | high | mitigate | Автоэкранирование, без `|safe`/`Markup`; `test_a_hostile_stored_value_is_escaped_in_every_header_sink` | closed |
| T-17-10 | Information Disclosure (номер в `<title>` → история браузера) | блок `title` | low | accept | См. Accepted Risks Log AR-17-02 | closed |
| T-17-11 | Information Disclosure (строка сессии под видом «телефона») | шапка экрана групп | high | mitigate | Номер только из колонки `phone` через помощника; `credentials` шаблоном не читается (проза-запрет сохранена в `account_groups/list.html`) | closed |
| T-17-12 | Information Disclosure (номер чужого аккаунта в карточке или порции истории) | `history_partial`, `history_list` | high | mitigate | Карта — `load_account_rows(db, user.id)` (`app/pages/history.py:673`); `history_account_label` берёт подпись только из карты (`labels.get(group.account_id)`) | closed |
| T-17-13 | Tampering (хранимый XSS в `<option>` фильтра) | `history/list.html` | high | mitigate | Автоэкранирование; `test_a_hostile_stored_value_is_escaped_in_the_option` | closed |
| T-17-14 | Repudiation (ложное «Номер неизвестен» у удалённого аккаунта) | `history_account_label` | low | mitigate | `None` при `group is None`; `test_a_record_without_a_group_carries_no_account_label`; на бою 19 записей без аккаунта — без подписи, в CSV пусто (UAT тесты 1–2) | closed |
| T-17-15 | Information Disclosure (номера пользователей на админских экранах) | «Воркеры», «Очередь», карточка пользователя | medium | accept | См. Accepted Risks Log AR-17-03 | closed |
| T-17-16 | Tampering (подпись в выражении Alpine ключа панели очереди) | `queue_row.html` | high | mitigate | Подпись в атрибуты `x-*`/`hx-*` не попадает (grep по `app/templates`); ключ панели — величины сервера | closed |
| T-17-17 | Tampering (хранимый XSS в строке воркера/очереди) | `worker_row.html`, `queue_row.html` | high | mitigate | Автоэкранирование макроса компонента, без `|safe`; `MARKUP_BUILDERS` в `tests/test_templates` | closed |
| T-17-18 | Tampering (формульная инъекция через ячейку «Номер») | `export_phone_cell` | high | mitigate | `export_cell(shown.removeprefix("+"))` — знак снимается до защиты, исключения нет (`app/pages/history.py:298`); таблица `PHONE_CELLS` | closed |
| T-17-19 | Information Disclosure (номера чужих аккаунтов в файле) | `history_export` | high | mitigate | Карта `load_account_rows(db, user.id)` (`history.py:796`), номер по `group.account_id` записей пользователя; `test_export_hides_other_users_records`, `test_export_never_carries_another_users_number` | closed |
| T-17-20 | Denial of Service (вторая инструкция при открытом курсоре → обрыв выгрузки) | `history_export` | medium | mitigate | Карта читается на `history.py:796` до `db.stream(query)` (`:857`) и `StreamingResponse(` (`:876`); на бою asyncpg 2026-11-21 файл пришёл целиком без ошибки курсора (UAT тест 2) | closed |
| T-17-21 | Information Disclosure (номера всех пользователей в одной порции) | `admin_user_history_partial` | high | mitigate | `load_account_rows(db, user_id)` по пользователю из адреса; `test_the_admin_batch_reads_only_the_viewed_users_accounts` | closed |
| T-17-22 | Elevation of Privilege (пользователь читает админскую историю с номерами) | маршруты `/admin/users/{user_id}/history*` | high | mitigate | `admin_user_history` (`app/pages/admin.py:1391`) и `admin_user_history_partial` (`:1509`) — `Depends(require_admin)`; маршрутов фаза не добавляла | closed |
| T-17-23 | Tampering (хранимый XSS в `<option>` админского фильтра) | `admin/user_history.html` | high | mitigate | Автоэкранирование, без `|safe`; `UNSAFE_MARKERS` в `tests/test_templates` | closed |
| T-17-24 | Repudiation (гейт `#id` зелен вакуумом) | `hash_id_findings`, `python_hash_findings` | high | mitigate | Подложенные строки К1/К2, двойник знака, Python; `test_the_universe_is_not_empty` | closed |
| T-17-25 | Tampering (исключение на файл маскирует возврат `#` аккаунта) | `TEMPLATE_HASH_EXCEPTIONS` | medium | mitigate | Ключ — вхождение `путь#порядковый номер`; исключений на файл `history_card.html` в гейтах номера нет | closed |
| T-17-26 | Repudiation (проход подписи зеленеет вакуумом) | `undeclared_id_occurrences`, перечни путей | high | mitigate | `DECLARED_ADDRESSES` (`tests/test_pages/test_account_label_sweep.py:192`) — восемь адресов, каждый элемент подписи или плоский приёмник; контроль синтетической разметкой | closed |
| T-17-27 | Tampering (засеянный образец обхода остаётся в боевой базе) | обход D-21 | medium | transfer | Передано человеку на `/gsd-verify-work` (О-1 (б)); исполнено 2026-11-21: `clean` удалил #76–#82, помеченных строк в базе 0 (`17-UAT.md`, отметка проверки 1) | closed |
| T-17-28 | Information Disclosure (засеянные строки видны в боевой админке) | обход D-21 | low | accept | См. Accepted Risks Log AR-17-04 | closed |
| T-17-SC | Tampering | npm/pip/cargo installs | high | mitigate | Фаза 17 пакетов не ставила: единственное изменение зависимостей в ветке — `phonenumberslite==9.0.41` из фазы 16 (`d2f486e5`, 16-02, проверка легитимности владельцем) | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-17-01 | T-17-08 | Опрос идёт только у карточек `syncing` раз в 5 с; один индексируемый `SELECT` по `user_id` (A2 RESEARCH) | план 17-02 (решение фазы) | 2026-11-20 |
| AR-17-02 | T-17-10 | D-12: номер — подпись самого пользователя; в URL и Referer не попадает; решение по умолчанию при делегировании владельцем («Да, решай сам») | владелец (делегирование) | 2026-11-20 |
| AR-17-03 | T-17-15 | Требование PHONE-06: администратор видит номера; маршруты за `require_admin`, запрет `403` стерегут тесты админки | владелец | 2026-10-08 |
| AR-17-04 | T-17-28 | Засеянные строки видны в боевой админке и счётчиках воркеров только на время обхода (A4 RESEARCH, О-1 (б)); убраны 2026-11-21 | владелец | 2026-11-20 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-21 | 29 | 29 | 0 | `/gsd-secure-phase 17` (оркестратор, L1 grep; аудитор не порождался — короткий путь ASVS 1) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-21
