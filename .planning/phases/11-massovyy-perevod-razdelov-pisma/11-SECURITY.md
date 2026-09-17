---
phase: 11
slug: massovyy-perevod-razdelov-pisma
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-09-17
---

# Phase 11 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

## Register origin

`register_authored_at_plan_time: true` — блок `<threat_model>` несут **все двадцать** исполненных
планов `11-01`…`11-20`, ни один не пропущен. Реестр снят разбором блоков 2026-09-17.

**Итоги замера:** 71 строка реестра, **44** различные угрозы (43 имени плюс одно столкновение имён,
ниже). По тяжести: 19 `high` · 18 `medium` · 7 `low` (`critical` — 0). По распоряжению:
41 `mitigate` · 2 `accept` · 1 `transfer`. Повторы имён: `T-11-SC` ×20, `T-07-13` ×3 (11-07, 11-08,
11-09), `T-11-13` ×3 (11-08, 11-09, 11-10), `T-11-02`, `T-11-17`, `T-11-18`, `T-11-29` — по ×2.

**Столкновение имён `T-11-39`.** Один идентификатор носят ДВЕ РАЗНЫЕ угрозы: в плане 11-04 — строка
списка по чужому идентификатору (`high`), в плане 11-19 — различимость «вне диапазона» и «нет строки»
у удаления группы и повтора (`medium`). В реестре ниже они разведены суффиксом плана. Исполненные
планы не правятся — столкновение записано, а не починено.

**Глубина проверки.** ASVS L1, `block_on: high`. Все 44 угрозы закрыты на классификации
оркестратора (улика — вызов или запись в продуктовом коде либо именованное правило суиты с
файлом и строкой), поэтому по правилу short-circuit (`threats_open: 0`, реестр авторован на
планировании, L1) аудитор не порождался. Классификация — греп-уровня: наличие и позиция
контроля, а не сквозная трассировка (это глубина L2/L3).

---

## Trust Boundaries

Двадцать планов называют 44 формулировки границ; сведены к десяти строкам.

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| браузер → страничный слой | идентификаторы пути и тела формы (`schedule_id`, `ad_id`, `account_id`, `user_id`, `group_id`, `log_id`, `after_id`), скрытые поля `return_to` / `keep_sched`, номер телефона, часовой пояс — всё подконтрольно клиенту, в том числе враждебными значениями | целые любой величины, строки; телефон — ПДн |
| обработчик → драйвер БД | целое вне int32 роняет запрос драйвером (`OverflowError` на SQLite, `DataError` на PostgreSQL) | идентификаторы |
| фрагмент / ответ 422 → DOM | с плана 11-09 тело авторского 422 подменяет цель запроса htmx; фрагменты несут имена групп, подписи аккаунтов, названия объявлений, эхо пояса и телефона | хранимый пользовательский текст |
| обработчик исключения на приложении → JSON-API | `RequestValidationError` регистрируется на приложении целиком; у `app/routes/` свой контракт 422 (D-07) | тела отказа валидации с эхо ввода |
| слой ответа → адресная строка / история | `HX-Location`, `HX-Push-Url`, `HX-Redirect` уводят браузер без перезагрузки; `HX-Redirect` — полная навигация мимо `selfRequestsOnly` | адреса переходов, коды уведомлений |
| SDK ЮKassa → слой ответа | `confirmation_url` приходит ответом внешнего сервиса и уезжает в заголовок | адрес оплаты с номером заказа |
| сторонний сайт → изменяющие маршруты | cookie прикладывается браузером к межсайтовой форме (админка, оплата) | действие от имени пользователя |
| администратор → чужая учётная запись | тумблеры блокировки и бесплатного доступа меняют ЧУЖОГО пользователя; плитка печатает вердикт, кэшируемый до минуты | блокировка, доступ |
| обработчик → внешний мост / Celery / внутрипроцессная заявка | синхронизация групп и старт сессии MAX обращаются к мессенджеру; `_SYNC_IN_FLIGHT` освобождается только в `finally` | состояние синхронизации |
| дерево тестов / реестр окон → гейты и отгрузка | обходы читают исходники тестов разбором дерева; `/gsd-ship` читает реестр окон | числа гейтов, статусы окон |

---

## Threat Register

База сравнения «не менялось»: `df26e76` (merge-base с `master`, начало фазы).
`git diff df26e76..HEAD -- app/routes/ app/services/ app/dependencies.py` — **пусто**.

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-11-01 | Information Disclosure | `schedules_update` на транспорте htmx | high | mitigate | `id_in_column` первым использованием (`schedules.py:1214-1216`), выборка `Ad.user_id == user.id` (`:1223`), `_ownership_verdict` (`:1246`) → переход `/schedules` (`:1255`); развилка транспорта живёт только внутри `respond()` (`htmx.py:712`), то есть после вердикта | closed |
| T-11-02 | Tampering (XSS) | фрагмент карточки и новой карточки, текст панели (11-01, 11-05) | medium | mitigate | Ни `\|safe` в `app/templates/`, ни `Markup(` в `app/` (греп — 0; единственное вхождение — докстринг `htmx.py:871`); правила `test_no_template_removes_automatic_escaping` (`test_htmx_markup_security.py:379`), `test_no_unsafe_escaping` (`test_components.py:777`) | closed |
| T-11-03 | Tampering | заголовок `HX-Location` исходов правки | medium | mitigate | `respond()` → `location_response(_with_notice(…))` (`htmx.py:834`) → `_local_path` (`:207`, `:266`): отказ не-`/`, `//`, `\`, управляющим, не-ASCII. Гейт `HX_HEADER_WRITES` (`test_htmx_gates.py:177`) — см. дрейф записи ниже | closed |
| T-11-04 | Denial of Service | четыре POST-обработчика расписаний | high | mitigate | `id_in_column` до любого запроса: create `schedules.py:1016-1017`, update `:1214-1216`, toggle `:1412`, delete `:1621`; правило `test_every_post_identifier_is_checked_before_its_first_use` (`test_identifier_bounds.py:2333`) | closed |
| T-11-05 | Information Disclosure | различимость «вне диапазона» / «нет строки» (расписания) | medium | mitigate | Негодная величина даёт `*_usable = False` и уходит в ТОТ ЖЕ вердикт/ветку, что и отсутствующая строка; матрица `EXPECTED_OUTCOMES` (`test_identifier_bounds.py:105`) | closed |
| T-11-06 | Tampering | нецелочисленный токен пути на htmx-пути (эхо `{"detail": …}`) | medium | transfer | Передано `T-07-13` (план 11-07); `T-07-13` закрыт ниже | closed |
| T-11-07 | Information Disclosure | `schedules_toggle` по чужому идентификатору | high | mitigate | `id_in_column` (`schedules.py:1412`) → выборка `Ad.user_id == user.id` (`:1416`) → «не найдено» переходом (`:1496`); `return_to` выбирает только форму ответа | closed |
| T-11-08 | Tampering | подделанный `keep_sched` / `return_to` | low | mitigate | `keep_sched` → `int(…)`, `TypeError`/`ValueError` → `None` (`schedules.py:325-328`); `return_to` сравнивается с константой `RETURN_TO_EDITOR` (`:1109`, `:1306`, `:1404`, `:1660`) — адрес из строки формы не собирается | closed |
| T-11-09 | Information Disclosure | поддельный курсор `after_id` | low | mitigate | `Query(None, ge=1, le=ID_MAX)` (`schedules.py:811`); сужает `_summary_query(user.id)` (`:832`, `:853-854`), не расширяя | closed |
| T-11-39 (11-04) | Information Disclosure | строка списка по чужому идентификатору | high | mitigate | Строка строится `_summary_query(user.id).where(Schedule.id == schedule_id)` (`schedules.py:1527`); `_summary_query` ограничен `Ad.user_id == user_id` (`:715`, `:728`) | closed |
| T-11-10 | Elevation of Privilege | создание расписания на чужое объявление / через чужой аккаунт | high | mitigate | `_ownership_verdict` (`schedules.py:1033`) → `OWNERSHIP_AD_DENIED` → переход `/schedules` (`:1042`) ДО чтения формы (`:1056`) и записи | closed |
| T-11-11 | Tampering | значение `HX-Push-Url` | medium | mitigate | `f"/ads/{saved.id}/edit"` из перечитанной записи (`ads.py:616`); правило `test_every_header_write_has_a_safe_right_operand` (`test_htmx_gates.py:2171`) | closed |
| T-11-12 | Tampering | подстановка чужого `ad_id` в автосохранение | high | mitigate | `select(Ad).where(Ad.id == requested_id, Ad.user_id == user.id)` (`ads.py:706`); недоступное → `None`, записи не создаётся. ⚠️ Владение держится; переполнение того же поля — вне реестра, см. `WR-01` ниже | closed |
| T-07-13 | Information Disclosure / XSS | тело 422 фреймворка с эхо ввода под свопом 422 (11-07, 11-08, 11-09) | high | mitigate | `app/main.py:253` → `malformed_request_response` (`htmx.py:426`): пустой `400` на htmx у страничного слоя при любом месте ошибки; единственный литерал `status_code=422` в `app/` — `respond_field_error` (`htmx.py:904`); обход `test_no_htmx_request_receives_a_framework_validation_body` (`test_htmx_validation_sink.py:313`); дополнение `07-SECURITY.md:198` (2026-09-16) | closed |
| T-11-37 | Tampering (контракт транспорта) | обработчик `RequestValidationError` против JSON-API | high | mitigate | Ветвь htmx только при `endpoint.__module__` из `app.pages` (`_validated_by_the_page_layer`, `htmx.py:396`); `test_the_json_api_keeps_its_validation_contract` (`test_htmx_validation_sink.py:376`), `test_the_page_branch_is_chosen_only_for_page_endpoints` (`:439`); `app/routes/` фазой не тронут (diff пуст) | closed |
| T-11-38 | Information Disclosure / XSS | запрос htmx к адресу JSON-API | medium | mitigate | `test_no_htmx_address_in_templates_points_at_the_json_api` (`test_htmx_validation_sink.py:609`) + синтетический контроль (`:628`); независимый греп `hx-*="/api/` / `action="/api/` по `app/templates/` — 0; `"selfRequestsOnly": true` (`htmx_config.html:158`) | closed |
| T-11-14 | Repudiation | подделанный запрос получает общую плашку | low | accept | Журнал принятых рисков: `AR-T-11-14` | closed |
| T-11-13 | Tampering (XSS) | эхо часового пояса во фрагменте и странице 422 (11-08, 11-09, 11-10) | medium | mitigate | Эхо только через `select_field` с закрытым списком опций и автоэкранированием; `respond_field_error` (`profile.py:193`); враждебное значение `HOSTILE_TIMEZONE = '"><script>alert(1)</script>'` на обоих транспортах (`test_profile.py:26`) | closed |
| T-11-15 | Elevation of Privilege | правка профиля под чужой личностью | high | mitigate | `Depends(forbid_when_impersonating)` на `profile_post` (`profile.py:82`); `app/dependencies.py` фазой не тронут; `tests/test_pages/test_impersonation.py` на месте | closed |
| T-11-16 | Tampering | перенацеливание ответа заголовком без записи | medium | mitigate | `RETARGET_RESWAP_USES: {}` (`test_htmx_gates.py:4945`), `RETARGET_RESWAP_USES_DECLARED = 0` (`:4955`), отрицательный контроль `test_control_an_undeclared_retarget_header_reddens_the_registry` (`:5073`) | closed |
| T-11-18 | Elevation of Privilege | права на действия карточки пользователя и тумблеры (11-11, 11-12) | high | mitigate | `Depends(require_admin)` на `admin_toggle_free_access` (`admin.py:1652`, + `forbid_when_impersonating` `:1654`) и `admin_toggle_block` (`:1904`); сигнатура `admin_toggle_block` отличается от базы только `IdPath` → `PostIdPath`; его изъятие из запрета под чужой личностью объявлено (`test_impersonation_gate.py:243`) и фазой не заведено | closed |
| T-11-41 | Denial of Service | переполнение колонки на шести входах администрирования | high | mitigate | `id_in_column` после сверки источника и до выборки: `admin.py:929`, `:1130`, `:1713`, `:1849`, `:1932`, `:2003` — ровно шесть | closed |
| T-11-17 | Tampering (CSRF) | тумблеры блокировки и бесплатного доступа (11-12, 11-13) | high | mitigate | `is_same_origin` → голый `403` после `require_admin` и до `id_in_column`/выборки: `admin.py:1705` (доступ), `:1924` (блокировка); `OWN_RESPONSE_EXITS_DECLARED = 12` (`test_htmx_gates.py:4547`) | closed |
| T-11-19 | Repudiation | след привилегированной операции | medium | mitigate | Журналы `free_access_toggle_without_subscription` (`admin.py:1739`) и `free_access_toggled` (`:1752`) стоят перед ответами (`:1746`, `:1778`) | closed |
| T-11-20 | Information Disclosure | плитка доступа после выдачи/снятия льготы | medium | mitigate | `invalidate_access_cache(target_user.id)` (`admin.py:1764`) ДО `respond(…, fragment=_fragment)` (`:1778`); тест утверждает `∞` в ответе (`test_admin_panel.py:3107`) | closed |
| T-11-21 | Spoofing | подставленный код в адресе `/admin/queue` | low | mitigate | `notice_for` → `_BY_CODE.get(code)`, незнакомый код → `None`, ничего не рисуется (`notices.py:331`, `notice_area.html:144`); текст берётся из исходника | closed |
| T-11-22 | Tampering | адрес перехода с кодом | medium | mitigate | `respond()` → `_require_registered_notice(notice)` (`htmx.py:828`) → `location_response(_with_notice(…))` (`:834`) → `_local_path`; коды очереди — `QUEUE_DROP_NOTICE_CODES` (`admin.py:313`, `:1176`) | closed |
| T-11-23 | Spoofing (открытый редирект, OWASP A01) | `redirect_external` на htmx-пути | high | mitigate | `YOOKASSA_CONFIRMATION_HOSTS = frozenset({"yoomoney.ru"})` (`htmx.py:151`); `_confirmation_url` (`:270`): только `https`, `@` в узле — отказ, порт — отказ, точное сравнение `hostname`; параметризованные случаи отказа (`test_htmx_response_layer.py:629…`); ответ несёт ровно один заголовок `HX-Redirect` | closed |
| T-11-24 | Tampering / DoS | инъекция заголовка и падение на кодировании | medium | mitigate | `_confirmation_url` отвергает управляющие, не-ASCII и `\` ДО разбора и записи заголовка; текст ошибки значение не подставляет. ⚠️ Нестроковый `url` — вне этой строки, см. `IN-03` ниже | closed |
| T-11-25 | Information Disclosure | журнал отвергнутого адреса | low | mitigate | `payment_confirmation_url_rejected` пишет только `host=_host_for_the_journal(url)` (`htmx.py:332`); полный адрес с `orderId` не пишется (`ORDER_MARK`, `test_htmx_response_layer.py:621`) | closed |
| T-11-26 | Tampering | второе незакрытое намерение оплаты из-за смены транспорта | high | mitigate | `app/services/` фазой не тронут; `create_payment` (`billing.py:331`) и `PendingIntentCapError` (`:356`) без изменений, развилка транспорта — `redirect_external` ПОСЛЕ создания (`:374`); `tests/test_pages/test_money_perimeter_gate.py` на месте | closed |
| T-11-27 | Tampering (CSRF) | голый 403 оплаты | high | mitigate | `is_same_origin` → `Response(403)` (`billing.py:324-325`) до `create_payment` (`:331`); порядок «кто → откуда → что» совпадает с базой (`df26e76`: `:297`/`:305`/`:312`). ⚠️ Уточнение формулировки ниже | closed |
| T-11-29 | Information Disclosure | (повторная) синхронизация чужого аккаунта (11-16, 11-17) | high | mitigate | `MessengerAccount.user_id == user.id`: `accounts_retry_sync` (`accounts.py:804`), `accounts_sync_groups` (`:903`); «не найден» → `/accounts` на обоих транспортах | closed |
| T-11-28 | Denial of Service | заявка `_SYNC_IN_FLIGHT`, оставленная занятой | high | mitigate | `_claim_sync_slot` (`accounts.py:976`) → внешний `try:` (`:983`) → `finally: _release_sync_slot` (`:1095`); ранние выходы — до занятия; тесты `test_sync_groups_over_htmx_releases_the_claim_on_every_exit` (`test_sync_groups.py:1076`), `…_exits_before_the_claim` (`:1190`), `…_busy_claim_is_not_released_by_the_refused_request` (`:1150`) | closed |
| T-11-30 | Denial of Service | двойной запуск синхронизации | medium | mitigate | Серверные ступени: `if account.status == "syncing"` (`accounts.py:926`) и заявка `_SYNC_IN_FLIGHT` (`:844-846`, `:976`) | closed |
| T-11-40 | Denial of Service | переполнение колонки на трёх входах аккаунтов | high | mitigate | `id_in_column`: `accounts.py:800`, `:899` (до занятия заявки), `:1146` | closed |
| T-11-31 | Tampering (XSS) | эхо телефона во фрагменте и странице 422 | medium | mitigate | `field(name="phone", …, value=phone or '')` с автоэкранированием (`max_connect_step.html:66`); доказательство — `test_the_phone_echo_is_autoescaped_in_the_step_markup` (`test_max_connect_transport.py:181`). ⚠️ HTTP-тест того же имени вакуумен, см. `IN-01` | closed |
| T-11-32 | Information Disclosure | номер телефона в разметке | low | mitigate | Номер — только значение поля формы (`max_connect_step.html:66`); греп `phone` в журналах и заголовках `app/pages/*.py` — 0 | closed |
| T-11-33 | Denial of Service | повторный старт сессии двойным нажатием | medium | mitigate | `form_wrapper` по умолчанию `hx-disabled-elt="find button[type=submit]"` (`form_wrapper.html:138`, `:144`), у формы MAX одна кнопка отправки; сервер переиспользует аккаунт в статусе `connecting` (`accounts.py:637-654`) | closed |
| T-11-34 | Denial of Service | переполнение колонки на входах групп и повтора | high | mitigate | `id_in_column`: `account_groups.py:472`, `:726-727`; `history.py:947`; `VALIDATION_REFUSAL_DIVERGENCES_DECLARED = 0` (`test_htmx_gates.py:3075`); окно 51 — `fixed` (`WINDOWS.md:68`) | closed |
| T-11-39 (11-19) | Information Disclosure | различимость «вне диапазона» / «нет строки» у удаления группы и повтора | medium | mitigate | Негодная величина идёт веткой отсутствующей строки (`account_groups.py:726-727`, `history.py:947`); матрица `test_identifier_bounds.py` | closed |
| T-11-35 | Repudiation | объём решения, приписанного владельцу (окно 63) | medium | mitigate | Летопись `ROADMAP.md:469` цитирует D-08 с датой 2026-09-14 и файлом `11-CONTEXT.md`, называет закрытую часть и остаток; окно 63 остаётся `open` (`WINDOWS.md:80`) | closed |
| T-11-36 | Tampering | молчаливое ослабление обхода пар | medium | mitigate | `PAIRED_302_ASSERTIONS_DECLARED = 158` (`test_htmx_post_pairs.py:2269`), `POST_PAIR_CASES_DECLARED = 48` (`:1494`); контроли `test_control_an_unpaired_302_assertion_reddens_the_traversal` (`:2339`), `…_get_or_unconverted_302_stays_out_of_the_count` (`:2395`), `…_empty_tests_root_reddens_the_number_rule` (`:2419`) | closed |
| T-11-SC | Tampering | установки пакетов npm / pip / cargo | low | accept | Журнал принятых рисков: `AR-T-11-SC` | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Register Drift — названо, не блокирует

1. **`HX_HEADER_WRITES` = 3, а не 2.** Строки `T-11-03` (11-01) и `T-11-11` (11-06) говорят
   «`HX_HEADER_WRITES` = 2 утверждается». Число выросло до 3 планом 11-15: третья запись —
   `HX-Redirect` в `redirect_external`, покрытая записью `SAFE_BY_NAME` и летописью числа
   (`test_htmx_gates.py:162-177`). Гейт принуждает ВСЕ места записи — смягчение действует, устарела
   только цифра в тексте реестра.
2. **`T-11-27`: «до любого обращения к БД» шире дерева.** Перед сверкой источника стоит поиск
   пользователя по cookie (`billing.py:316`), а это чтение БД. Сверка стоит до `create_payment` и
   до любого чтения, которое делает действие; порядок совпадает с базой фазы. Защита на месте,
   формулировка неточна.
3. **Столкновение имён `T-11-39`** — описано в «Register origin».

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-T-11-14 | T-11-14 | Подделанный запрос htmx с негодным параметром получает пустой `400` и общую плашку «Действие не выполнено» вместо разбора по полям (low). Из интерфейса недостижимо: значения полей рисует сервер. Цена названа в докстринге `malformed_request_response` (`htmx.py:443-445`). | phase owner (chubav) | 2026-09-14 |
| AR-T-11-SC | T-11-SC | Установки пакетов npm / pip / cargo (low). Фаза не устанавливает ничего (`11-RESEARCH.md` §Package Legitimacy Audit; `urllib.parse` — стандартная библиотека). Проверено по дереву: `git diff --name-only df26e76..HEAD` по `package(-lock).json`, `uv.lock`, `pyproject.toml`, `requirements*.txt`, `Pipfile`, `poetry.lock`, `yarn.lock`, `pnpm-lock` — **0 совпадений**. | phase owner (chubav) | 2026-09-14 |

*Accepted risks do not resurface in future audit runs.*

---

## Unregistered Flags

**Объявленные исполнителями.** Из двадцати сводок `## Threat Flags` несут шесть (11-04, 11-07,
11-08, 11-09, 11-10, 11-17); все шесть — «новых нет» и отображаются на строки реестра, уже закрытые
выше. Новой поверхности сверх реестра не объявлено.

**Из `11-REVIEW.md` (2026-09-17) — вне реестра, в `threats_open` не входят.** Аудит новых угроз не
ищет; эти пункты перенесены сюда, чтобы запись о безопасности не выглядела чище ревизии.

| Находка | Класс | Суть | Связь с реестром | Состояние |
|---------|-------|------|------------------|-----------|
| `WR-01` | DoS (переполнение колонки) | `POST /ads/new` приводит `ad_id` через `int(ad_id)` без `id_in_column` (`ads.py:700-706`); величина вне int32 даёт `500`, на htmx — плашкой. Правило `test_every_post_identifier_is_checked_before_its_first_use` видит только алиасы `Post*` и строковое поле формы пропускает | Тот же класс, что `T-11-04/34/40/41`, но вход `ads_create` в реестр фазы не внесён. `T-11-12` (владение) держится | Известно с 2026-09-08: `verdict="open"` в `test_identifier_bounds.py:1530-1548`. **Не исправлено** |
| `IN-03` | DoS (500 после создания намерения) | `_confirmation_url` / `_host_for_the_journal` ловят только `ValueError`; нестроковый `url` из SDK (`None`) даёт `TypeError` и `500` уже после `create_payment` | Смежно с `T-11-24`; источник — ответ SDK по TLS, не ввод пользователя | **Не исправлено** |
| `IN-01` | Качество улики | HTTP-тест `test_a_hostile_phone_never_reaches_the_response_raw` идёт веткой QR, где телефон не печатается, и покраснеть не может | Улика `T-11-31` опирается на unit-тест `:181`, не на этот | **Не исправлено** |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-17 | 44 | 44 | 0 | `/gsd-secure-phase 11`, классификация оркестратора L1 (41 mitigate — улика в коде/суите; 1 transfer — закрыт получатель; 2 accept — журнал); аудитор не порождался по short-circuit |

## Security Audit 2026-09-17

| Metric | Count |
|--------|-------|
| Threats found | 44 (71 строка реестра) |
| Closed | 44 |
| Open | 0 |
| Open at or above `high` (blocking) | 0 |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-17
