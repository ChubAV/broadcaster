---
phase: "12"
slug: "zagruzka-izobrazheniy-bez-fetch"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
block_on: high
created: "2026-09-21"
register_authored_at_plan_time: true
# ⚠️ РЕЕСТР СОБРАН АУДИТОРОМ, А НЕ ОРКЕСТРАТОРОМ, И ЭТО ОТСТУПЛЕНИЕ НАЗВАНО, А НЕ УМОЛЧАНО.
# Спина `secure-phase.md` шагами 2–3 велит собирать реестр оркестратору и подавать аудитору
# готовым. Здесь реестр — ~93 строки в 13 блоках `<threat_model>`; внесение его в контекст
# оркестратора стоило бы больше, чем сберегло. Аудитору поручено собрать реестр из тех же
# 13 блоков и 8 разделов `## Threat Flags` самому, с ЗАПРЕТОМ искать новые угрозы
# (`register_authored_at_plan_time: true` → режим «проверить, что смягчения существуют»).
# Ретроспективный STRIDE НЕ запускался.
---

# Phase 12 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Фаза: «Загрузка изображений без `fetch()`». Аудит проведён 2026-09-21 агентом
`gsd-security-auditor` по ASVS L1, порог блокировки — `high`.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| браузер → страничный слой | составной запрос загрузки и автосохранения | содержимое файлов, клиентские имена файлов, объявленные типы частей, число частей, список текущих ключей, метки вычитания `removed_images` |
| страничный слой → хранилище S3 | запись объекта | ключ объекта и `Content-Type`, ПРОИЗВЕДЁННЫЙ приложением из перекодированных байтов |
| хранилище → браузер | отдача объекта | объект с origin хранилища и с типом, записанным при загрузке |
| документ → документ | внеполосные подмены htmx 2.0.10 | блоки `hx-swap-oob="delete"` по хешированному идентификатору и `beforeend`-дописки в узел меток |

---

## Threat Register

57 уникальных идентификаторов после устранения повторов (собрано из ~93 строк 13 планов).
Пространства имён по фазе различаются: планы 12-01…12-05 нумеруют плоско `T-12-NN`,
планы 12-06…12-13 — попланово `T-12-PP-NN`. Столкновений нет.

| Threat ID | Category | Component | Severity | Disposition | Mitigation (evidence) | Status |
|-----------|----------|-----------|----------|-------------|------------------------|--------|
| T-12-01 | Tampering/Elevation | `store_upload` — активный документ под видом картинки | high | mitigate | `image_upload.py:426` (`sniff_image`), `:116-119` закрытый список подписей; тип объекта из `prepared.content_type` (`images.py:290,444`), присланный заголовок не читается НИГДЕ | closed |
| T-12-02 | Tampering | `safe_filename` — сегменты пути в клиентском имени | high | mitigate | `image_upload.py:291-293`, набор символов `:36`, обрезка `:37` | closed |
| T-12-03 | DoS | `store_upload` — тело произвольного размера в памяти | medium | mitigate | `image_upload.py:398-415` — возврат на ПЕРВОМ превышении, порции не склеиваются | closed |
| T-12-04 | DoS | разбор составного запроса — партия из тысячи частей | high | mitigate | `ads.py:1022-1023` `max_files/max_fields=MAX_UPLOAD_PARTS`; константа `image_upload.py:66` = 64 | closed |
| T-12-05 | DoS | `prepare_upload` — decompression bomb | medium | accept | `images.py:71` `MAX_DECODED_PIXELS`, проверяется ДО распаковки `:259,365,406` | closed |
| T-12-06 | Elevation | загрузка при истёкшем доступе | high | mitigate | `pages/__init__.py:143` `Depends(require_access)` на роутере; маршрут `ads.py:910` внутри него; гейт `test_ads_image_upload.py:444` | closed |
| T-12-07 | DoS | предел тела обратного прокси | medium | mitigate | `nginx/nginx.conf.template:82`, `nginx-http.conf.template:42` = 64M; правило вывода `test_nginx_body_limit.py:171` | closed |
| T-12-08 | DoS | умолчание предела в шаблонах | low | mitigate | оба шаблона объявляют явно; `test_nginx_body_limit.py:152,193,213` | closed |
| T-12-09 | Tampering/Elevation | сверка владения ключами | high | mitigate | `image_keys.py:164-201` `own_image_keys`, вызов при сохранении `ads.py:664` | closed |
| T-12-10 | Tampering (CR-01) | сборка разметки на клиенте | high | mitigate | `test_ads_form_security.py:55,63` — `MARKUP_SINKS == 0`; в `form.html` ноль вхождений innerHTML/createElement/insertAdjacentHTML | closed |
| T-12-11 | Info Disclosure | имя файла на экране | medium | mitigate | `media_strip.html:102` — имя выводится из ХРАНИМОГО ключа, только в атрибут `title=` | closed |
| T-12-12 | Elevation | чужой ключ в эхо-ответе | high | mitigate | `ads.py:1100-1102` `partition_own_image_keys` до сборки фрагмента; префикс миниатюр исключён `image_keys.py:37,60` | closed |
| T-12-13 | Tampering | число свободных мест | medium | mitigate | `ads.py:1271` `free = max(0, max_images - len(image_keys))` из результата самого предиката; отказ потолка — `image_keys.py:180-187` | closed |
| T-12-14 | XSS / слом вёрстки | имя файла в строке отказа | high | mitigate | `ads.py:1196,1308,1351` `safe_filename(part.filename)` в служебном слое; шаблон второй нормализации не делает НАМЕРЕННО (шапка `media_refusals.html`) | closed |
| T-12-15 | Tampering | внедрение в заголовок ответа | high | mitigate | ASCII-литералы `ads.py:1063,1409,775`; правила `test_htmx_gates.py:2242`, `:2222` при `HX_HEADER_WRITES = 5` (`:220`); отрицательный контроль `:2661` | closed |
| T-12-16 | DoS | перекодирование занимает работника | medium | accept | `ads.py:1273-1276`, `image_upload.py:440-442` — `to_thread` не распараллелен, один работник, живость через `/health` | closed |
| T-12-17 | Elevation | зависимость доступа как запись набора | high | mitigate | `pages/__init__.py:143` — зависимость роутера, не элемент набора; `test_ads_image_upload.py:444` | closed |
| T-12-18 | Elevation | маршрут под олицетворением | high | mitigate | `test_impersonation_gate.py:264` — `ads_images_upload` отнесён с сохранённым основанием; база `:96` | closed |
| T-12-19 | Repudiation | переотнесение записей к фазе | medium | mitigate | `test_htmx_markup_gates.py:3725,3878` — обе записи переотнесены к ФАЗЕ 15 (FORM-01); отнесений к ФАЗЕ 12 не осталось | closed |
| T-12-SC | Tampering (supply chain) | установка внешних пакетов | low | accept | `git diff --stat master...HEAD` по `pyproject.toml`, `uv.lock`, `package.json`, `wa_worker/package.json` — пусто; выполнено вакуумно | closed |
| T-12-06-01 | Tampering | чужой ключ в эхо-ответе загрузки | high | mitigate | `ads.py:1100-1107` — разделение ДО всякого эха; чужой не попадает в `image_keys` фрагмента (`:1374`) | closed |
| T-12-06-02 | DoS | отказ тратит круг к хранилищу | medium | mitigate | `ads.py:1191-1199` — ветвь отказа читает только `part.filename`; ни `store_upload`, ни вызова S3 | closed |
| T-12-06-03 | Tampering | пустая полоса стирает подтверждённое | high | mitigate | `ads.py:1164-1166` + `:1374` — переиздаётся подтверждённое подмножество; ответ с пустой полосой убран (`:1110-1121`) | closed |
| T-12-06-04 | Info Disclosure | сообщение о недоступности несёт клиентское значение | low | accept | закрытая константа `image_keys.py:39` `INACCESSIBLE_IMAGE_MESSAGE`; клиентское не подставляется (`ads.py:1165`) | closed |
| T-12-07-01 | Tampering | автосохранение переиздаёт полосу | high | mitigate | `ads.py:686` `media_changed`, `:769-772` — только при изменившемся составе; включение полосы убрано из `autosave_response.html` целиком | closed |
| T-12-07-02 | DoS | очередь перекрывающихся запросов | medium | mitigate | `media_upload_form.html:66` `sync='this:queue last'` через `form_wrapper.html:192`; правило чётности форм редактора | closed |
| T-12-07-03 | Repudiation | отказ не переживает автосохранения | medium | mitigate | автосохранение больше не подменяет узел полосы; `ads.py:769-772`, `autosave_response.html:60-72` | closed |
| T-12-07-04 | DoS (сироты в хранилище) | объект записан, документ не сохранён | low | accept | `deferred-items.md:23-52` — `accepted-assumption`, решение владельца D-17, влияние названо и ограничено потолком на запрос | closed |
| T-12-08-01 | Info Disclosure | подробность отказа хранилища на экран | medium | mitigate | `ads.py:1343-1348` подробность только в `logger.warning`; на экран `STORAGE_UNAVAILABLE_MESSAGE` (`:1352`, константа `image_upload.py:172-175`) | closed |
| T-12-08-02 | DoS (сироты) | отказ одной части роняет партию | medium | mitigate | `ads.py:1355` `continue` — партия выживает; `:1357` уже записанные ключи остаются и доходят до документа (`:1374`) | closed |
| T-12-08-03 | Spoofing | плитка для несуществующего объекта | high | mitigate | `ads.py:1349-1355` — отказавшая часть получает строку `Rejected` и НЕ добавляет ключ | closed |
| T-12-08-04 | Tampering | повтор обходит проверки | low | accept | путь повтора заново входит в те же проверки типа/размера/потолка (`image_upload.py:395-430`, `ads.py:1305`) | closed |
| T-12-09-01 | DoS | смягчение предела частей | high | mitigate | `image_upload.py:66` по-прежнему 64, `ads.py:1023` не тронут; изменилась только ФОРМА отказа | closed |
| T-12-09-02 | Tampering | отказ затирает полосу | high | mitigate | `ads.py:1063` `HX-Reswap: beforeend` — дописка, не подмена `#media-strip`; скрытые поля ключей выживают | closed |
| T-12-09-03 | Info Disclosure | отказ рамки уходит на экран как JSON | medium | mitigate | `ads.py:1046` `upload_parts_message(MAX_UPLOAD_PARTS)`; константа закрытого набора `image_upload.py:203-229` | closed |
| T-12-09-04 | Repudiation | переназначение цели без основания | medium | mitigate | `test_htmx_gates.py:5133-5134` `RETARGET_RESWAP_USES` с основанием; счёт `:5173` = 1; правило непустого основания `:5256` | closed |
| T-12-10-01 | Spoofing | межсайтовая отправка | high | mitigate | `ads.py:968-969` `is_same_origin` → 403 без тела, ПОСЛЕ `get_user_from_cookie` (`:951`) и ДО `request.form` (`:1022`); страж `common.py:716` | closed |
| T-12-10-02 | DoS | межсайтовый отправитель покупает буферизацию | high | mitigate | тот же порядок: `:968` выше `:1022` | closed |
| T-12-10-03 | Repudiation | отменённые утверждения стёрты | medium | mitigate | названы, а не стёрты: `image_upload.py:366-394` (WR-01), `ads.py:1288-1301`; настоящая граница названа как `client_max_body_size` | closed |
| T-12-10-04 | DoS | область действия серверного блока | medium | accept | несомый открытым обзор: `12-REVIEW.md:146` и `:176-190` (область серверного блока, решение владельца D-20 «вне рамки», предупреждение о цементировании) | closed |
| T-12-10-05 | Elevation | запрос без обоих заголовков пропускается | low | accept | граница стража названа в строке документации `common.py:~740-760`; единообразно на 14 местах вызова (`test_origin_guard_on_destructive_routes.py:729`) | closed |
| T-12-11-01 | Tampering | адресное снятие бьёт лишнее | high | mitigate | `autosave_response.html:87-89` — по одному `hx-swap-oob="delete"` на ключ из `media_gone`; источник `ads.py:769-770` = `resurrected + [removed]` | closed |
| T-12-11-02 | Injection | ключ попадает в атрибут `id` | medium | mitigate | `image_keys.py:125-126` — `sha256(key)[:16]` с постоянным префиксом `media-item-`; сырой ключ в `id` не входит | closed |
| T-12-11-03 | Spoofing | снятие по чужому ключу | medium | mitigate | `ads.py:686` `removed in image_list`, где `image_list` — результат `own_image_keys` (`:664`); `media_dom_id`/`thumb_key` документированы чистыми (`image_keys.py:68,122`) | closed |
| T-12-11-04 | DoS | накопление узлов снятия | low | accept | `deferred-items.md:127-153` — `accepted-assumption`; исход — громкий отказ потолка с именем файла | closed |
| T-12-11-05 | Tampering | ПОРЯДОК I открыт до плана 12-12 | high | **transfer** | перенос объявлен `12-11-PLAN.md:57` (`must_haves.assumptions`) И ПРИЁМ ПРОВЕРЕН в принимающем плане: `ads.py:663-668` вычитание + `:769-772`. Перенос не отмашка — средство в приёмнике существует | closed |
| T-12-12-01 | Tampering | сверка владения до вычитания | high | mitigate | `ads.py:663` вычитание → `:664` `own_image_keys(subtracted, …)`; порядок «вычесть, затем сверить» задокументирован `:653-662` | closed |
| T-12-12-02 | Elevation | `removed_images` как источник ключей | high | mitigate | `ads.py:626-630` — набор только для исключения; пути из `removed_images` в `image_list` нет; различие имён полей принуждается `autosave_response.html:110` | closed |
| T-12-12-03 | Tampering | поле исключает чужое | low | accept | поле может исключить только значения, присланные тем же запросом (`ads.py:624-625`); отсутствие стража origin на маршруте сохранения ПРЕДСУЩЕСТВУЕТ партии | closed |
| T-12-12-04 | Injection | ключ в значении атрибута | medium | mitigate | `autosave_response.html:110` — значение экранируется Jinja; путь идентификатора идёт через хеш (`:88`) | closed |
| T-12-12-05 | Repudiation | экран расходится с базой | medium | mitigate | `ads.py:652` `resurrected` → `media_gone` (`:769-770`), сверка за один круг | closed |
| T-12-12-06 | DoS | рост узла меток | low | accept | `deferred-items.md:85-105` — `accepted-assumption`, ограничено временем жизни страницы | closed |
| T-12-13-01 | Spoofing | свой ключ гибнет рядом с чужим | high | mitigate | `ads.py:1100-1107` не тронута; подтверждённое подмножество сохранено (`:1374`); гейт `test_an_own_key_survives_a_foreign_key_in_the_same_batch` | closed |
| T-12-13-02 | DoS | ветвь отказа тратит круг к хранилищу | high | mitigate | `ads.py:1191-1199` — только имена; независимо подтверждено закрытием WR-08 с `mock_s3.call_count == 0` (`12-REVIEW.md:148`, `test_ads_image_upload.py:911-930,984-1000`) | closed |
| T-12-13-03 | Injection | имя файла в строке отказа | medium | mitigate | `ads.py:1196` `safe_filename(part.filename)`; шаблон второй нормализации не делает по замыслу | closed |
| T-12-13-04 | Repudiation | два утверждения слиты в одно | high | mitigate | `ads.py:1164-1166` (отказ по ключу, без имени) И `:1191-1199` (по одной именованной строке на файл) — утверждения разделены | closed |
| T-12-13-05 | DoS | стоимость ветви отказа | medium | accept | `deferred-items.md:154+` — `accepted-assumption`; три основания не чинить повторены в коде `ads.py:1238-1254` | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above `workflow.security_block_on` count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-12-01 | T-12-05 | Предел числа точек `MAX_DECODED_PIXELS` действовал ДО фазы и проверяется до распаковки; фаза новой поверхности не открывает | планировщик фазы (реестр 12-01) | 2026-09-18 |
| AR-12-02 | T-12-16 | Перекодирование занимает работника; `to_thread` не распараллелен намеренно, живость снимается через `/health` | планировщик фазы (реестр) | 2026-09-19 |
| AR-12-03 | T-12-SC | Фаза не устанавливает ни одного внешнего пакета — проверено пустым diff по файлам замков | аудитор, 2026-09-21 | 2026-09-21 |
| AR-12-04 | T-12-06-04 | Сообщение о недоступности — закрытая константа, клиентское значение не подставляется | планировщик фазы (реестр 12-06) | 2026-09-19 |
| AR-12-05 | T-12-07-04 | Сироты в хранилище: объект записан, документ не сохранён. Влияние названо, ограничено потолком на запрос | владелец, решение **D-17** (`deferred-items.md:23-52`) | 2026-09-19 |
| AR-12-06 | T-12-08-04 | Путь повтора заново входит в те же проверки типа, размера и потолка — обхода не заведено | планировщик фазы (реестр 12-08) | 2026-09-19 |
| AR-12-07 | T-12-10-04 | Область действия серверного блока прокси; решение владельца **D-20** — вне рамки фазы, с предупреждением о цементировании | владелец, D-20 (`12-REVIEW.md:176-190`) | 2026-09-20 |
| AR-12-08 | T-12-10-05 | Запрос, не приславший НИ ОДНОГО из двух заголовков, пропускается — граница стража названа в коде и единообразна на 14 местах вызова | планировщик фазы (реестр 12-10) | 2026-09-20 |
| AR-12-09 | T-12-11-04 | Накопление узлов снятия; исход — громкий отказ потолка с именем файла | владелец (`deferred-items.md:127-153`) | 2026-09-20 |
| AR-12-10 | T-12-12-03 | `removed_images` может исключить только значения того же запроса; отсутствие стража origin на маршруте сохранения ПРЕДСУЩЕСТВУЕТ партии и ей не заведено | планировщик фазы (реестр 12-12) | 2026-09-20 |
| AR-12-11 | T-12-12-06 | Рост узла меток ограничен временем жизни страницы | владелец (`deferred-items.md:85-105`) | 2026-09-20 |
| AR-12-12 | T-12-13-05 | Стоимость ветви отказа; три основания не чинить повторены в коде | владелец (`deferred-items.md:154+`) | 2026-09-20 |

---

## Unregistered Flags

⚠️ Три находки аудита, **не отображающиеся ни на одну строку реестра**. Ни одна не является
разрывом объявленного смягчения; все три — WARNING, не блокеры. Записаны здесь, а не опущены.

1. **WR-10 — несущая единственность ключа в `ad.images`** (`12-REVIEW.md:132-134`).
   Адресное внеполосное снятие сделало единственность идентификатора плитки НЕСУЩИМ свойством,
   а обеспечивать её нечем: дубль ключа в `ad.images` печатает два узла с одним `id`, и один
   `hx-swap-oob="delete"` снимает ОБА. Соседствует с T-12-11-02, но это ДРУГОЙ отказ —
   единственность, а не внедрение, — поэтому хеш-смягчение T-12-11-02 его НЕ покрывает.
   Поверхность заведена ЭТОЙ фазой, строки реестра у неё нет.
   **Остаётся открытым решением владельца**, названным в `12-UAT.md` § Gaps: либо сделать
   различность свойством единственного предиката принадлежности, либо завести
   `accepted-assumption` в форме D-16/D-17. Достижимо только рукотворным запросом с
   повторённым полем `images` — интерфейс такого не печатает.

2. **Раздел `## Threat Flags` отсутствует в 5 сводках из 13** — `12-06` … `12-10-SUMMARY.md`
   не несут его вовсе. Аудитор НЕ счёл отсутствие раздела доказательством отсутствия угроз:
   соответствующий 21 пункт проверен напрямую по коду, а не по отсутствующим разделам.
   Разрыва не найдено, но договор отчётности исполнителя по этим пяти планам НЕ ВЫПОЛНЕН.

3. **IN-09** (`12-REVIEW.md:156`, `ads.py:1343-1348`) — `detail=str(exc.detail)` пишется в журнал
   поверх того, что уже является константой. Сверено с T-12-08-01: экранный путь чист
   (`:1352` отдаёт `STORAGE_UNAVAILABLE_MESSAGE`), поэтому это шум журнала, а не разглашение.
   Осведомительно.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-21 | 57 | 57 | 0 | `gsd-security-auditor` (ASVS L1, block_on: high) |

Разбивка закрытий: **44 mitigate**, **12 accept**, **1 transfer** (T-12-11-05 — перенос объявлен
планом 12-11 и приём проверен в плане 12-12, а не принят на слово).

Ни один файл реализации аудитом не изменён: проход был только на чтение.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-21
