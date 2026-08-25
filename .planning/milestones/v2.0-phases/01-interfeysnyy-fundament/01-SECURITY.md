---
phase: 01
slug: interfeysnyy-fundament
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-08-10
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Register origin: authored at plan time (`<threat_model>` present in all 13 PLAN files).
81 threats total. 77 closed with evidence recorded in their plan's SUMMARY `## Threat Flags`
table; 4 (Plan 10) were unverified because `01-10-SUMMARY.md` omitted that section and were
audited directly by `gsd-security-auditor` on 2026-08-10.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| браузер → FastAPI page-роуты | Недоверенный HTTP-запрос | путь, query, cookie `access_token` |
| браузер → `/static` | Путь к файлу приходит от клиента | имена ассетов |
| шаблон → HTML | Данные пользователя попадают в разметку | имена, заголовки объявлений, счётчики |
| зависимость роутера → БД | `load_shell_context` выполняет запросы от имени пользователя из cookie | агрегаты пользователя |
| браузер → `/uploads` | Загрузка изображений; имя файла и Content-Type приходят от клиента | бинарные ассеты, имя файла |
| приложение → S3 | Ключ объекта строится из `user_id` и клиентского имени файла | изображения объявлений |
| S3 origin → браузер | Публичный базовый адрес; авторизации чтения в репозитории нет | изображения объявлений |
| внешние мессенджеры → шаблоны | Названия групп, имена аккаунтов, тексты ошибок | недоверенный текст |

---

## Threat Register

Полный регистр — в `<threat_model>` блоках `01-01-PLAN.md` … `01-13-PLAN.md`.
Здесь сведены итоговые статусы; для 77 закрытых угроз доказательства лежат в
`## Threat Flags` соответствующего SUMMARY.

### Планы 01–09, 11–13 — закрыты при исполнении

| Диапазон | Всего | Закрыто | Где доказательство |
|----------|-------|---------|--------------------|
| T-01-01 … T-01-06 (+ T-01-SC) | 6 | 6 | `01-01-SUMMARY.md` |
| T-02-01 … T-02-05 (+ T-02-SC) | 5 | 5 | `01-02-SUMMARY.md` |
| T-03-01 … T-03-05 (+ T-03-SC) | 5 | 5 | `01-03-SUMMARY.md` |
| T-04-01 … T-04-05 (+ T-04-SC) | 5 | 5 | `01-04-SUMMARY.md` |
| T-05-01 … T-05-05 (+ T-05-SC) | 5 | 5 | `01-05-SUMMARY.md` |
| T-06-01 … T-06-06 (+ T-06-SC) | 6 | 6 | `01-06-SUMMARY.md` |
| T-07-01 … T-07-05 (+ T-07-SC) | 5 | 5 | `01-07-SUMMARY.md` |
| T-08-01 … T-08-06 (+ T-08-SC) | 6 | 6 | `01-08-SUMMARY.md` |
| T-09-01 … T-09-06 (+ T-09-SC) | 6 | 6 | `01-09-SUMMARY.md` |
| T-11-01 … T-11-07 (+ T-11-SC) | 7 | 7 | `01-11-SUMMARY.md` |
| T-12-01 … T-12-08 (+ T-12-SC) | 8 | 8 | `01-12-SUMMARY.md` |
| T-13-01 … T-13-11 (+ T-13-SC) | 11 | 11 | `01-13-SUMMARY.md` |

Дополнительно закрыто вне регистра (План 08, автофикс №1): подстановка недоверенного
адреса QR-кода в атрибут `src` без экранирования.

### План 10 — проверен аудитором 2026-08-10

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-10-01 | Tampering | сборка предпросмотра в `app/templates/ads/form.html` | critical | mitigate | `renderImages()` собирает узлы: `replaceChildren()` (`form.html:59-60`), `createElement` (`:64,67,72,76,85`), присваивание свойств `img.src` (`:69`), `label.textContent` (`:74`), `hidden.value` (`:88`). `innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write` — 0 вхождений. Начальные данные проходят через `\| tojson` (`:54`). Тесты `test_ads_form_security.py:52-77` | closed |
| T-10-02 | Elevation of Privilege | построение ключа объекта в `app/routes/uploads.py` | high | mitigate | `safe_filename()` (`uploads.py:15-38`): последний сегмент пути → замена вне `[A-Za-z0-9._-]` → обрезка → фолбэк `"upload"`. Применена в `uploads.py:66-67`. Единственный путь вызова: `upload_file_to_s3` ← `uploads.py:71`, `put_object` ← `s3.py:34`. Префикс неуправляем: `user_id` приводится к `int` в `auth_service.py:26`. Тесты `test_uploads.py:84-142` | closed |
| T-10-03 | Repudiation | обработчик удаления изображения | medium | mitigate | `btn.addEventListener('click', () => removeImage(i))` (`form.html:79`), `removeImage` (`:93-96`); строкового `onclick` в блоке скрипта нет. Тест `test_ads_form_security.py:91-98` | closed |
| T-10-04 | Information Disclosure | доступ к ранее загруженным изображениям | high | mitigate → **accept** | Митигация не реализована. Принята как риск — см. R-01 ниже | closed (accepted) |
| T-10-05 | Denial of Service | ограничение числа и размера загружаемых изображений | medium | accept | Ограничение в 10 изображений остаётся клиентским (`form.html:99`); серверной проверки числа нет ни до правки, ни после | closed (accepted) |
| T-10-06 | Information Disclosure | отсутствие Content-Security-Policy | low | accept | Решение Плана 08 (T-08-06): CSP не вводится в этой фазе | closed (accepted) |

Проверка аудитора: `SMTP_HOST="" uv run pytest tests/test_routes/test_uploads.py tests/test_templates/test_ads_form_security.py -q` → 15 passed.

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-01 | T-10-04 | **Ключ изображения не проверяется на принадлежность вызывающему.** `app/pages/ads.py:133-135,183-187` сохраняет `form_data.getlist("images")` дословно; JSON-API ведёт себя так же (`app/routes/ads.py:16,22,46`), и `tests/test_routes/test_ads.py:169-185` явно закрепляет это поведение. Аутентифицированного пути чтения объекта в репозитории нет: `app/services/s3.py:4-9` склеивает публичный базовый адрес, глобалы шаблонов заведены в `app/pages/common.py:27-38`. Единственная область видимости — 128-битный `uuid4().hex` в роли capability. Принято, потому что: (1) починка требует серверной проверки владения ключом при сохранении объявления, то есть новое поведение — за границей правила Фазы 01 «новый вид, старые действия»; (2) правка вынуждает переписать закрепляющий тест `test_ads.py:169-185`; (3) это находка WR-01 из `01-REVIEW.md`, однородная с CR-01 и CR-02, которые тем же решением отнесены в Фазу 2. **Остаточный риск усилен отложенным CR-02:** SVG, исполняемый на origin хранилища, работает same-origin против всех объектов под `s3_public_url` — то есть ровно против того, что защищает T-10-04. Чинить в Фазе 2 вместе с CR-01 и CR-02. | Пользователь (UAT Фазы 01, 2026-08-10) | 2026-08-10 |
| R-02 | T-10-05 | Ограничение в 10 изображений остаётся клиентским; серверной проверки числа изображений в объявлении не было и до фазы. Усиление — новое поведение, вне границы фазы | План 10 | 2026-08-09 |
| R-03 | T-01-06 | Cookie сессии без флага `secure` — логика входа этой фазой не тронута | План 01 | 2026-08-09 |
| R-04 | T-08-06 / T-10-06 / T-13-11 | Content-Security-Policy не вводится — выходит за правило фазы, зафиксировано для бэклога после v2.0 | План 08 | 2026-08-09 |
| R-05 | T-02-05 | Тексты сообщений об ошибках на auth-экранах перенесены дословно, новых подробностей не добавлено | План 02 | 2026-08-09 |
| R-06 | T-03-05 / T-04-05 | `offset` / `limit` оставлены как были (`ge=0`, `ge=1, le=100`) | Планы 03, 04 | 2026-08-09 |
| R-07 | T-05-05 | Состав полей на странице детали отправки не изменён | План 05 | 2026-08-09 |
| R-08 | T-06-06 | Частота опроса статуса подключения (3 с) не менялась | План 06 | 2026-08-09 |
| R-09 | T-07-05 | Журналирование админ-действий — существующее поведение; отмечено для Фазы 6 (ADMIN-11) | План 07 | 2026-08-09 |
| R-10 | T-09-06 / T-11-07 | Подпись колонки на узкой ширине дублирует название из шапки; новых полей на экран не выводится | Планы 09, 11 | 2026-08-09 |

*Accepted risks do not resurface in future audit runs.*

---

## Deferred to Phase 2

Решение пользователя на UAT Фазы 01 (2026-08-10). Гейт код-ревью (`01-REVIEW.md`,
`status: issues_found`, `critical: 2`) остаётся открытым — ship блокируется до починки.

| Ref | Файл | Суть |
|-----|------|------|
| CR-01 | `app/pages/schedules.py:204-213,314-315` | Не проверяется владение `ad_id` / `account_id`: чужое объявление ставится в расписание, SendLog пишется с `user_id` владельца — счёт выставляется жертве |
| CR-02 | `app/routes/uploads.py:48-52` | Клиентский Content-Type принимается на веру и сохраняется в S3; `image/svg+xml` проходит, а `history/detail.html:80` и `admin/user_history_detail.html:91` открывают объект с `target="_blank"` — SVG исполняется на origin хранилища |
| WR-01 / T-10-04 | `app/pages/ads.py:133-135,183-187`, `app/routes/ads.py:16,22,46` | Ключ изображения не проверяется на принадлежность вызывающему (см. R-01) |

---

## Process Gaps

- **`01-10-SUMMARY.md` не содержит раздела `## Threat Flags`** — именно поэтому шесть
  угроз Плана 10 остались непроверенными до этого аудита. Отсутствие раздела зафиксировано,
  а не истолковано как «новой поверхности нет».
- **Пункт покрытия D4 Плана 10** (`01-10-PLAN.md:218`, `verification: []`) — человеческая
  проверка неизменности формата ключа объекта — в `01-UAT.md` не попал и не выполнялся.
  Кодовая половина проверена аудитором: шаблон ключа не менялся (`uploads.py:63-67`),
  План 10 тронул 4 файла, миграции и переименования нет.
- **`/ads/new` и `/ads/{id}/edit` не рендерятся ни одним тестом суиты**
  (`tests/test_pages/test_shell.py:105` документирует обход 500) — см. отложенную находку
  в `deferred-items.md` (План 08, глобал `s3_public_url`).

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-09 | 75 | 75 | 0 | Планы 01–09, 11–13 (при исполнении) |
| 2026-08-10 | 6 | 6 | 0 | gsd-security-auditor (План 10; T-10-04 закрыта принятием риска R-01) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-10
