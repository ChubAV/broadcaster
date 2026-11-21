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
