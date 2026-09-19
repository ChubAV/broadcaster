---
phase: 12-zagruzka-izobrazheniy-bez-fetch
verified: 2026-09-19T11:52:10Z
status: gaps_found
score: 31/35 must-haves verified
covered_files:
  - ".planning/REQUIREMENTS.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-01-PLAN.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-01-SUMMARY.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-02-PLAN.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-02-SUMMARY.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-03-PLAN.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-03-SUMMARY.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-04-PLAN.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-04-SUMMARY.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-05-PLAN.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-05-SUMMARY.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-06-PLAN.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-06-SUMMARY.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-07-PLAN.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-07-SUMMARY.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-08-PLAN.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-08-SUMMARY.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-09-PLAN.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-09-SUMMARY.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-10-PLAN.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/12-10-SUMMARY.md"
  - ".planning/phases/12-zagruzka-izobrazheniy-bez-fetch/deferred-items.md"
  - "README.md"
  - "app/main.py"
  - "app/pages/ads.py"
  - "app/pages/common.py"
  - "app/services/image_keys.py"
  - "app/services/image_upload.py"
  - "app/services/images.py"
  - "app/templates/ads/form.html"
  - "app/templates/ads/includes/autosave_response.html"
  - "app/templates/ads/includes/media_refusals.html"
  - "app/templates/ads/includes/media_strip.html"
  - "app/templates/ads/includes/media_upload_form.html"
  - "app/templates/components/form_wrapper.html"
  - "nginx/nginx-http.conf.template"
  - "nginx/nginx.conf.template"
  - "tests/test_nginx_body_limit.py"
  - "tests/test_pages/test_access_gate.py"
  - "tests/test_pages/test_admin_panel.py"
  - "tests/test_pages/test_ads_editor.py"
  - "tests/test_pages/test_ads_image_ownership.py"
  - "tests/test_pages/test_ads_image_upload.py"
  - "tests/test_pages/test_htmx_gates.py"
  - "tests/test_pages/test_htmx_post_pairs.py"
  - "tests/test_pages/test_hx_location_destinations.py"
  - "tests/test_pages/test_impersonation_gate.py"
  - "tests/test_pages/test_origin_guard_on_destructive_routes.py"
  - "tests/test_routes/test_ads.py"
  - "tests/test_services/test_image_keys.py"
  - "tests/test_services/test_image_upload.py"
  - "tests/test_services/test_images.py"
  - "tests/test_templates/test_ads_form_security.py"
  - "tests/test_templates/test_components.py"
  - "tests/test_templates/test_htmx_inventory.py"
  - "tests/test_templates/test_htmx_markup_gates.py"
  - "tests/test_templates/test_walkthrough_anchors.py"
covered_digest: "v1:sha256:18a7f691ac73e13f0944d259a4729265aed9ab0e36f3d35ae6273c954bf5dbda"
behavior_unverified: 3
overrides_applied: 0
decision_coverage:
  honored: 17
  total: 17
  not_honored: []
re_verification:
  previous_status: gaps_found
  previous_score: 2026-09-19T06:22:32Z — 23/27
  gaps_closed:
    - "Успешно загруженные файлы остаются прикреплёнными на пути отказа СВЕРКИ КЛЮЧЕЙ (гап 1): зонд А — свой ключ переживает чужой в одной партии; зонд Б — 11 своих ключей при потолке 10 сохранены все; зонд В — авария хранилища посреди партии стала отказом ПО ФАЙЛУ; зонд Е — пережившие ключи записываются следующим сохранением"
    - "Строка отказа переживает автосохранение, которое ЭТОТ ЖЕ ответ и заказывает (гап 2): зонд Г — ответ автосохранения без изменения состава вложений не несёт `#media-tray` ВОВСЕ, строка отказа остаётся в документе"
  gaps_remaining:
    - "Полоса теряет только что принятый ключ (или воскрешает убранный) при наложении УБИРАНИЯ и ЗАГРУЗКИ — гап 3 закрыт на двух механизмах из трёх"
  regressions: []
gaps:
  - truth: "Полоса вложений — состояние в DOM — не теряет только что принятый ключ при наложении запросов (гап 3 прошлой верификации)"
    status: partial
    reason: >-
      Два механизма из трёх закрыты и проверены: (1) наложение ЗАГРУЗКА↔ЗАГРУЗКА — форма загрузки
      получила `hx-sync="this:queue last"`, и это видно в ОТРЕНДЕРЕННОЙ разметке `/ads/new`, а не
      только в вызове макроса; (2) наложение ТЕКСТОВОЕ АВТОСОХРАНЕНИЕ↔ЗАГРУЗКА — ответ
      автосохранения больше не приносит `#media-tray` вовсе, пока состав вложений не изменён.
      ТРЕТИЙ механизм остаётся открытым, и он назван решением владельца D-16 дословно: «ответ
      автосохранения перестаёт перерисовывать полосу из отстающей базы». На пути УБИРАНИЯ («×»)
      `repaint_media=True`, и полоса рисуется из `ad.images` ОДНОЙ базой — ни сверки с присланным
      снимком, ни признака «загрузка в полёте». Кнопка «×» есть отправка формы `#ad-form`, а
      очередь `hx-sync="this:queue last"` действует на ЭЛЕМЕНТ: две формы редактора — РАЗНЫЕ
      элементы, поэтому убирание и загрузка летят одновременно. Воспроизведено ЗОНДОМ
      ВЕРИФИКАТОРА на уровне HTTP, а не выведено из ревизии — обе развязки вредоносны:
      ПОРЯДОК I (ответ загрузки приходит последним) — удалённый ключ `A` ВОСКРЕСАЕТ в документе, и
      автосохранение, заказанное заголовком того же ответа, записывает `ad.images = [A, B, C]`:
      удаление человека молча отменено (замер: `deleted key A resurrected in db: True`).
      ПОРЯДОК II (ответ убирания приходит последним) — внеполосная полоса `[B]` выносит из
      документа скрытое поле ключа `C`, УЖЕ записанного в хранилище (замер: `s3 calls: 2`,
      `C present in removal tray: False`): человек видел плитку, она исчезла БЕЗ сообщения, объект
      остался сиротой. Ни один из двух исходов не покрыт записями `deferred-items.md`: D-17
      говорит об ОБОРВАННОЙ партии и межвкладочном счёте, D-16 — о вытеснении среднего выбора из
      очереди. Окно не микроскопическое: загрузка держит запрос открытым на декодирование,
      пережатие и два круга к хранилищу.
    artifacts:
      - path: "app/templates/ads/includes/media_upload_form.html"
        issue: >-
          Строка 64: `sync='this:queue last'` — очередь замкнута на СВОЙ элемент. Комментарий (г)
          этого же файла прямо пишет: «очередь одной на другую не распространяется», — то есть
          ограничение названо, но следствие для пути УБИРАНИЯ не рассмотрено.
      - path: "app/pages/ads.py"
        issue: >-
          Строки 618-621 и 680-682: `media_changed` открывает `repaint_media`, и перерисовка
          собирается из `ad.images` после коммита — из состояния, которое о летящей загрузке не
          знает. Ни объединения с присланным снимком (`form_data.getlist(\"images\")`), ни
          признака «загрузка в полёте» нет.
      - path: "app/templates/ads/includes/autosave_response.html"
        issue: >-
          Строки 60-65: включение полосы под `repaint_media` рисуется ровно из `ad.images` —
          единственный оставшийся вызывающий, который подменяет узел ЦЕЛИКОМ данными,
          отстающими от документа.
      - path: "tests/test_templates/test_htmx_markup_gates.py"
        issue: >-
          Строки 7318-7331: текст отказа гейта обосновывает РАВЕНСТВО стратегий тем, что иначе
          «плитки пропадают с экрана БЕЗ сообщения». Равенство двух стратегий, замкнутых на `this:`,
          этого свойства между ДВУМЯ элементами не покупает — запись обещает больше, чем меряет.
    missing:
      - "Перерисовка полосы на пути убирания не должна заявлять власть над ключами, которых этот запрос не видел: либо объединение базы с присланным снимком скрытых полей, либо общая очередь у двух форм редактора (`sync='#media-strip:queue last'`), либо признак «загрузка в полёте»."
      - "Правило суиты на ВЗАИМОДЕЙСТВИЕ убирания и загрузки — сегодня оба обработчика зелены по отдельности, и именно поэтому исход не виден: `test_both_editor_forms_declare_the_same_overlay_strategy` меряет равенство строк, а не судьбу ключа."
      - "Если исход принимается как есть — он обязан стать ЗАПИСЬЮ того же вида, что D-16 и D-17 в `deferred-items.md`, с названным воздействием («убранное вложение возвращается» и «принятый ключ теряется вместе с объектом-сиротой»), а не остаться открытой находкой ревью."
deferred: []
advisory:
  - finding: "Потолок тела 64M объявлен в блоке `server` обоих шаблонов nginx, то есть поднят для ВСЕХ адресов ради одного (WR-02)"
    category: security
    reason: "Любой POST, включая неаутентифицированный, может прогнать через воркер 64 МБ. Предсуществует этой партии, владельцем вынесено ВНЕ рамки партии явной записью в 12-CONTEXT.md. Закроет сужение директивы до `location /ads/images`."
    evidence_status: "none provided — воспроизводимого отказа не предъявлено, nginx в среде разработки отсутствует"
  - finding: "`oob` доезжает до полосы НАСЛЕДОВАНИЕМ переменной, поставленной строкой ниже для другого включения (IN-02)"
    category: architectural
    reason: "Перестановка двух включений в `autosave_response.html` молча снимет `hx-swap-oob` с полосы. Предсуществует партии; владелец оставил ОТКРЫТОЙ ЗАПИСЬЮ."
    evidence_status: "none provided — сегодняшний порядок включений даёт верный вывод, отказ не воспроизводится"
  - finding: "`await request.form()` без `async with` / `close()` (IN-03); путь без htmx делает всю работу и выбрасывает ключи (IN-04); `free` считается из присланного клиентом списка (IN-05); «+ ФАЙЛ» клавиатурой недостижим (IN-06)"
    category: other
    reason: "Четыре информационные находки ревью, перенесённые открытыми. IN-05 дополнительно покрыт принятым допущением D-17."
    evidence_status: "none provided — ни одна не предъявлена покрасневшим правилом"
behavior_unverified_items:
  - truth: "Пользователь видит, что загрузка идёт — бинарный `hx-indicator` (критерий 4 ROADMAP, ручной UAT по объявлению)"
    test: "В редакторе выбрать файл и наблюдать признак «идёт запрос» до прихода плитки."
    expected: "Признак `.form-busy` виден в течение запроса и гаснет после подмены полосы."
    why_human: "Разметочная половина проверена машинно (отрендеренная форма несёт `hx-indicator=\"find .form-busy\"`), но ВИДИМОСТЬ — свойство браузера и CSS; суита рантайм разметки не исполняет."
  - truth: "Порог счётчика символов переключается по числу плиток полосы (клиентская половина D-11)"
    test: "У объявления с вложением набрать текст длиной между порогом подписи и общим порогом."
    expected: "Счётчик желтеет на ближайшем нажатии клавиши."
    why_human: "Серверная половина закрыта двумя правилами; переключение порога — переход состояния в исполняемом JS, которого суита не исполняет."
  - truth: "На боевом стенде партия из десяти снимков по 4–5 МБ доезжает до приложения, а не получает 413 от прокси"
    test: "После ПЕРЕРАЗВЁРТЫВАНИЯ nginx выбрать десять снимков по 4–5 МБ разом; смотреть `just prod-logs nginx`."
    expected: "Все десять прикрепляются, 413 в логах прокси нет."
    why_human: "nginx в среде разработки отсутствует; правило суиты доказывает согласованность ИСХОДНИКОВ шаблонов с `Settings`, а не состояние работающего прокси. Запись 92 `.planning/WINDOWS.md`, статус `open`."
flagged_prohibitions:
  - statement: "Отказ не отвечает авторитетно выглядящей ПУСТОЙ полосой (план 12-06)"
    plan: "12-06"
    verification: none
    judge: "not-violated — И ЭТО РЕДКИЙ СЛУЧАЙ С МАШИННОЙ ОПОРОЙ: зонды А и Б верификатора показывают подтверждённое подмножество (1 из 1 и 11 из 11 скрытых полей), а не пустоту."
    flag: "unverified-prohibition — human review recommended"
  - statement: "Файл, который человек выбрал, не исчезает МОЛЧА: всё, что не прикрепилось, получает названную строку, а всё, что прикрепилось, остаётся видимым (план 12-07)"
    plan: "12-07"
    verification: none
    judge: >-
      ⚠️ VIOLATED НА ОДНОМ ПУТИ, и путь этот — гап, оставшийся открытым. ПОРЯДОК II зонда WR-07:
      ключ, УЖЕ прикреплённый и записанный в хранилище, уносится внеполосной полосой убирания без
      единой строки. Два других задевания запрета НАЗВАНЫ записями (`deferred-items.md`:
      вытеснение среднего выбора; WR-08: ownership-отказ не называет ни одного файла партии) —
      третье не названо ничем.
    flag: "unverified-prohibition — human review recommended"
  - statement: "Замеряющее правило, закрепляющее нежелательное поведение, ИНВЕРТИРУЕТСЯ вместе с предметом (план 12-08)"
    plan: "12-08"
    verification: none
    judge: "not-violated (НЕАВТОРИТЕТНО): `test_a_storage_failure_still_answers_bad_gateway` снято, на его месте `test_a_storage_failure_becomes_a_row_and_keeps_the_accepted_keys` — утверждение сильнее прежнего; сервисный контракт `HTTPException(502)` не тронут."
    flag: "unverified-prohibition — human review recommended"
  - statement: "Рамка партии, назначенная владельцем, не расширяется молча (план 12-09)"
    plan: "12-09"
    verification: none
    judge: "not-violated (НЕАВТОРИТЕТНО): WR-02 и пять информационных находок остались ОТКРЫТЫМИ записями ревью, а не были исправлены попутно; рамка выписана в `12-CONTEXT.md` поимённо."
    flag: "unverified-prohibition — human review recommended"
  - statement: "Восемь запретов планов 12-01…12-05 со `verification: none` (перечень прошлой верификации)"
    plan: "12-01…12-05"
    verification: none
    judge: "РЕШЕНО ВЛАДЕЛЬЦЕМ — D-18 (`12-CONTEXT.md`): приняты в том виде, в каком их прочёл верификатор; правила, краснеющего при нарушении, заводить не требуется (семь из восьми про процесс планирования, а не про поведение кода). Перечень перенесён сюда целиком и не снят молча; пункт `human_verification` прошлой верификации закрыт этой записью."
    flag: "resolved by owner decision D-18 — карается только молчаливое снятие, а его не было"
human_verification:
  - test: "Критерий 4 (ручной UAT по объявлению ROADMAP): в редакторе выбрать файл — виден ли признак «идёт запрос» до появления плитки."
    expected: "Индикатор виден в течение запроса, гаснет после подмены полосы."
    why_human: "Видимость — свойство браузера и CSS."
  - test: "Боевой стенд: после переразвёртывания nginx бросить десять снимков по 4–5 МБ разом."
    expected: "Все десять прикрепляются; 413 в `just prod-logs nginx` нет."
    why_human: "nginx в среде разработки отсутствует; правка шаблона в гите боевой предел не двигает. Запись 92 WINDOWS.md."
  - test: "В редакторе объявления с двумя вложениями нажать «×» на первом."
    expected: "Плитка исчезает после круга к серверу, набранный текст не теряется, страница не перезагружается."
    why_human: "Машинно проверен КОНТРАКТ ответа (зонд Д: внеполосный `#media-tray` с признаком подмены, база обновлена); применение блока живым документом суита не исполняет."
  - test: "У объявления с вложением набрать текст между порогом подписи и общим порогом."
    expected: "Счётчик желтеет на ближайшем нажатии клавиши."
    why_human: "Клиентская половина порога — исполняемый JS, которого суита не исполняет."
  - test: "На `/ads/new` прикрепить одну картинку, НЕ вводя ни символа, затем обновить страницу."
    expected: "Картинка на месте, черновик создан."
    why_human: "Прямая проверка допущения A2 разведки (всплытие события соседа до тела документа). Машинной проверки у всплытия нет."
  - test: "На `/ads/new` бросить пять файлов на два свободных места и СМОТРЕТЬ НА ЭКРАН."
    expected: "Две плитки появились, три строки отказа названы поимённо И ОСТАЛИСЬ ЧИТАЕМЫ дольше одного круга автосохранения."
    why_human: "Машинно закрыто зондом Г (ответ автосохранения строку не уносит); подтвердить ВРЕМЯ ЖИЗНИ строки на экране обязан человек."
  - test: "НАБЛЮДЕНИЕ ГАПА: в редакторе с двумя вложениями выбрать крупный файл и, ПОКА идёт загрузка, нажать «×» на первой плитке."
    expected: "Ожидается один из двух вредоносных исходов зонда WR-07 — либо убранная плитка ВОЗВРАЩАЕТСЯ (и уезжает в базу), либо новая плитка ИСЧЕЗАЕТ без сообщения."
    why_human: "Механизм воспроизведён машинно на уровне HTTP; ЧЕРЕДОВАНИЕ двух запросов — свойство браузера. Человек подтверждает достижимость и выбирает: чинить или записать допущением."
---

# Phase 12: Загрузка изображений без `fetch()` — Verification Report (re-verification)

**Phase Goal:** изображение объявления прикрепляется htmx-фрагментом, и ни одна строка шаблона не собирает запрос руками
**Verified:** 2026-09-19T11:52:10Z
**Status:** gaps_found
**Re-verification:** Да — после закрытия трёх гапов планами 12-06…12-10

## Goal Achievement

Партия закрытия сделала работу, и это видно ЗОНДАМИ ВЕРИФИКАТОРА, а не сводками: **два гапа из
трёх закрыты по существу**, причём закрыты тем механизмом, который назывался в `missing`, а не
подгонкой под правило. Цель фазы в её букве достигнута; три из четырёх критериев ROADMAP держатся
кодом.

Остаётся **третий гап, закрытый на двух механизмах наложения из трёх**. Решение владельца D-16
записано двумя половинами — «форма загрузки получает `sync`» И «ответ автосохранения перестаёт
перерисовывать полосу из отстающей базы». Первая половина исполнена целиком. Вторая исполнена для
всех вызывающих, КРОМЕ одного: путь убирания «×» по-прежнему перерисовывает полосу из одной базы, и
он же — единственный путь, который с загрузкой пересекается, потому что кнопка «×» принадлежит
ДРУГОЙ форме, а очередь `hx-sync` замкнута на элемент.

### Observable Truths

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| R1 | **Критерий 1.** Загрузка идёт htmx-фрагментом в `#media-strip`; `fetch()` и `imagePaths` исчезли; ключ приезжает скрытым полем с `form="ad-form"` | ✓ VERIFIED | Зонд З (СВОЙ): в ОТРЕНДЕРЕННОЙ странице `/ads/new` `fetch(` → **0**; форма загрузки печатается с `hx-post="/ads/images" hx-target="#media-strip" hx-swap="innerHTML" hx-encoding="multipart/form-data"`. Исходник `ads/form.html`: `fetch(`→0, `createElement`→0, `id="image-inputs"`→0, `id="upload-error"`→0; единственное `imagePaths` — проза комментария :455, перечисляющая снятое |
| R2 | **Критерий 2.** Успешно загруженные файлы остаются прикреплёнными, даже если часть отвалилась | ✓ VERIFIED | Держится теперь на ВСЕХ путях, которые критерий называет. Зонды А, Б, В, Е (см. таблицу зондов). Прошлый отказ снят: ветвь отказа сверки отвечает подтверждённым подмножеством. ⚠️ Смежная потеря на НАЛОЖЕНИИ запросов учтена отдельной истиной G3, а не здесь: критерий говорит о судьбе ПАРТИИ, а не о чередовании двух действий |
| R3 | **Критерий 3.** Отказ доступа виден пользователю; решение о поверхности отражено в ОБОИХ гейтах перечня | ✓ VERIFIED (регрессия) | `app/pages/__init__.py`: `include_router(ads_router, dependencies=[Depends(require_access)])`; `GATED_API_ROUTERS` и `BLOCK_CHECKED_API_ROUTERS` не тронуты партией; 315 правил затронутых модулей зелены |
| R4 | **Критерий 4.** Пользователь видит, что загрузка идёт — бинарный `hx-indicator` | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Отрендеренная форма несёт `hx-indicator="find .form-busy"` (зонд З). Ручной UAT по объявлению ROADMAP |
| **G1** | **Гап 1.** Успешно загруженные файлы остаются прикреплёнными на пути отказа СВЕРКИ КЛЮЧЕЙ | ✓ VERIFIED | **Зонд А (свой):** свой + чужой ключ в одной партии → `hidden count: 1`, `own survived: True`, `foreign echoed: False`, `s3 calls: 0` (работа ради подделки не делается). **Зонд Б (свой):** 11 своих законных ключей при потолке 10 → `hidden count: 11`, `all survived: True`, входящий файл получает строку про потолок. **Зонд Е (свой):** пережившие ключи уходят следующим сохранением в `Ad.images` (`own key persisted: True`) — два обработчика сведены. Механизм: `partition_own_image_keys` — ЕДИНСТВЕННЫЙ предикат, через него выражена и `own_image_keys` |
| **G2** | **Гап 2.** Строка отказа переживает автосохранение, которое ЭТОТ ЖЕ ответ и заказывает | ✓ VERIFIED | **Зонд Г (свой):** частичная партия → строка отказа + ключ принятого + `HX-Trigger-After-Swap: ads-image-attached`; затем ровно то автосохранение, которое заголовок заказывает → `autosave carries media-tray: False`. Полосы в ответе НЕТ вовсе, стирать нечем. Механизм: `repaint_media` по умолчанию ложно, истинно ставит ровно один вызывающий и ровно по ФАКТУ убирания (`media_changed = bool(removed) and removed in image_list`) |
| **G3** | **Гап 3.** Полоса не теряет только что принятый ключ при наложении запросов | ✗ FAILED (частично закрыт) | Закрыто: ЗАГРУЗКА↔ЗАГРУЗКА (`hx-sync="this:queue last"` в отрендеренной разметке, зонд З) и ТЕКСТ↔ЗАГРУЗКА (зонд Г). Открыто: УБИРАНИЕ↔ЗАГРУЗКА. **Зонд WR-07 (свой):** ПОРЯДОК I → `deleted key A resurrected in db: True`; ПОРЯДОК II → `C present in removal tray: False` при `s3 calls: 2`. См. Gaps Summary |
| N1 | Авария хранилища на части *n* — отказ ПО ФАЙЛУ, ключи частей 1..n-1 доезжают | ✓ VERIFIED | **Зонд В (свой):** падение записи на второй части → `status 200`, ключ `one.png` в документе, строка `two.png — файл не сохранился — хранилище сейчас недоступно…`. Послабление миниатюры не расползлось: `free`/`attached` не двигаются, цикл продолжается |
| N2 | Отказ по числу частей читается человеком и НЕ стирает полосу | ✓ VERIFIED | `ads.py:930-980`: `StarletteHTTPException` → фрагмент ОДНИХ строк отказа из `media_refusals.html` + `HX-Reswap: beforeend`; строка ложится СОСЕДОМ `#media-tray` внутри `#media-strip` (прочитано по структуре шаблонов, не по сводке). `test_too_many_parts_is_a_readable_row_not_json` зелено |
| N3 | Маршрут загрузки ЗОВЁТ гарду источника; замер инвертирован вверх (D-15) | ✓ VERIFIED | **Зонд Ж (свой):** `Origin: http://evil.example` → **403, тело пустое, `s3 calls: 0`**; `Sec-Fetch-Site: cross-site` → 403. `ORIGIN_GUARD_CALL_SITES_MEASURED = 14` при замере дерева `grep -r "is_same_origin(request)" app/` → **14**. Сверка стои́т ПОСЛЕ прав и ДО `request.form()` (прочитано построчно, :860-878 против :930) |
| N4 | Два комментария-инварианта говорят правду о транспорте (WR-01) | ✓ VERIFIED | `ads.py:886-895` и :1113-1126 — «единственный предел ДО чтения — потолок тела на обратном прокси»; `image_upload.py:380-394` — прежняя редакция НАЗВАНА, а не стёрта |
| N5 | Ни одна строка суиты не ссылается на снятый планом 12-05 модуль (IN-01) | ✓ VERIFIED | `grep -rn "test_routes/test_uploads\|test_uploads.py" tests/ app/` → **0** |
| P1 | Годный файл → 200 и фрагмент с плиткой и скрытым полем | ✓ VERIFIED (регрессия) | `test_one_image_over_htmx_returns_the_strip_fragment` зелено |
| P2 | Тот же адрес БЕЗ признака htmx → 302 на `/ads/new` | ✓ VERIFIED (регрессия) | Правило зелено; ⚠️ IN-04 остаётся открытой записью |
| P3 | Гейта в теле обработчика нет ни строкой | ✓ VERIFIED (регрессия) | Объяснение стои́т над декоратором (:807-818), внутри тела имени зависимости нет |
| P4 | Не-транспортная логика в сервисе; комментарии перенесены ДОСЛОВНО; «размер ВЫШЕ типа» | ✓ VERIFIED (регрессия) | `tests/test_services/test_image_upload.py` зелен в целевом прогоне |
| P5 | Число частей ограничено явно — второй рубеж | ✓ VERIFIED | `request.form(max_files=MAX_UPLOAD_PARTS, max_fields=…)` (:931-933); обоснование ИСПРАВЛЕНО (N4), отказ стал читаемым (N2) |
| P6 | Форма загрузки рождена макросом; отступление цели блокировки записано поимённо | ✓ VERIFIED (регрессия) | `media_upload_form.html:58-65`; `type="submit"` → 0 |
| P7 | Оба шаблона nginx объявляют `64M` с формулой; потолок приложения не тронут | ✓ VERIFIED (регрессия) | По одному `client_max_body_size 64M` в каждом; `tests/test_nginx_body_limit.py` зелен. ⚠️ WR-02 — advisory |
| P8 | Боевой предел прокси действует: партия 10×4–5 МБ доезжает | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Правило читает ИСХОДНИК шаблона; нужно переразвёртывание (запись 92 WINDOWS.md) |
| P9 | Клиентской сборки разметки в редакторе нет ВОВСЕ, гейт ИНВЕРТИРОВАН | ✓ VERIFIED (регрессия) | `tests/test_templates/test_ads_form_security.py` зелен |
| P10 | Ручной сборки запроса в `app/templates/` осталось 5 — экран Telegram | ✓ VERIFIED | `MANUAL_FETCH_PLACES = 5`; замер дерева: единственный файл с `fetch(` — `accounts/connect_tg_user.html` |
| P11 | Полоса рисуется СЕРВЕРОМ из единственного источника | ✓ VERIFIED | `media_strip.html` включают три места; строки отказа вынесены в `media_refusals.html` — источник по-прежнему ОДИН на уровень |
| P12 | Порог счётчика читается из РАЗМЕТКИ | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Серверная половина закрыта правилами; переключение — исполняемый JS |
| P13 | Полоса приезжает внеполосным блоком по ВТОРОМУ идентификатору; цели не совпадают | ✓ VERIFIED (усилено) | `#media-strip` ≠ `#media-tray`; включение теперь ПОД УСЛОВИЕМ — прежнее «стирает строки отказа» снято (G2) |
| P14 | Частичная партия: принятый прикреплён, отвергнутый получает СВОЮ строку | ✓ VERIFIED (уже и ПОСЛЕ ответа) | Зонд Г: строка живёт и после круга автосохранения |
| P15 | Потолок берёт первые свободные места; партию целиком сервер не отвергает | ✓ VERIFIED (регрессия) | `test_ceiling_takes_the_free_slots_and_refuses_the_rest` зелено; зонд Б показывает то же на 11 ключах |
| P16 | Все исходы отвечают 200 с фрагментом | ✓ VERIFIED (расширено) | Прежнее изъятие (400 JSON на числе частей) СНЯТО планом 12-09 (N2) |
| P17 | Каждый ключ сверяется ДО фрагмента одним инструментом | ✓ VERIFIED (форма отказа исправлена) | `partition_own_image_keys` — единственный предикат; `own_image_keys` выражена через него; форма отказа стала разделяющей (G1) |
| P18 | Первая удачная картинка на `/ads/new` создаёт черновик | ✓ VERIFIED (контракт) | Зонд Г: `HX-Trigger-After-Swap: ads-image-attached`, и последующее сохранение создало запись с ключом. Браузерная половина (A2) — пункт обхода |
| P19 | `app/routes/uploads.py` снят ЦЕЛИКОМ | ✓ VERIFIED (регрессия) | `test -e` → 1; `grep -c uploads app/main.py` → 0; `/api/uploads/image` в README → 0 |
| P20 | 1099 строк утверждений ПЕРЕЕХАЛИ | ✓ VERIFIED (регрессия) | Целевой прогон 315 passed; полная суита оркестратора 3437 passed |
| P21 | Решение о поверхности отражено во ВСЕХ ТРЁХ перечнях гейтов | ✓ VERIFIED (регрессия) | Оба множества гейта доступа не тронуты; гейты зелены |
| P22 | Два изъятия Фазы 9 ПЕРЕАДРЕСОВАНЫ Фазе 15 | ✓ VERIFIED (регрессия) | `НАЗНАЧЕНО ФАЗЕ 12` в `tests/` → 0 файлов |
| P23 | Ни одной подмены по прежнему адресу модуля не осталось | ✓ VERIFIED (усилено) | IN-01 закрыт целиком: прозаических ссылок тоже 0 (N5) |

**Score:** 31/35 truths verified (3 present, behavior-unverified; 1 failed)

### Deferred Items

Нет. Ни Фаза 13 (QR-мастер Telegram), ни Фаза 14 (авторизация), ни Фаза 15 (сводный обход 47 форм,
`fetch( == 0`, девять пунктов ручного UAT) не называют наложение УБИРАНИЯ и ЗАГРУЗКИ ни целью, ни
критерием. Гап не адресован поздним фазам вехи.

### Advisory (New Scope, Unevidenced)

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | Потолок 64M в блоке `server` обоих шаблонов nginx (WR-02) | security | предсуществует партии, вынесен владельцем ВНЕ её рамки; воспроизводимого отказа не предъявлено |
| 2 | `oob` полосы доезжает НАСЛЕДОВАНИЕМ переменной соседнего включения (IN-02) | architectural | предсуществует; сегодняшний порядок даёт верный вывод, отказ не воспроизводится |
| 3 | IN-03 (форма без `close()`), IN-04 (путь без htmx выбрасывает ключи), IN-05 (`free` из клиентского списка), IN-06 (`+ ФАЙЛ` недостижим клавиатурой) | other | четыре информационные находки ревью, ни одна не предъявлена покрасневшим правилом |

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `app/services/image_keys.py` | `partition_own_image_keys` — единственный предикат принадлежности | ✓ VERIFIED | `own_image_keys` выражена через него (:151); второго сравнения в дереве нет |
| `app/pages/ads.py::ads_images_upload` | подтверждённое подмножество на отказе, гарда источника, пофайловый отказ хранилища, читаемый отказ по числу частей | ✓ VERIFIED | Прежний ⚠️ HOLLOW снят: ветвь отказа больше не строит фрагмент из пустоты (зонды А, Б) |
| `app/pages/ads.py::_autosave_response` | признак `repaint_media` | ⚠️ ЧАСТИЧНО | Умолчание ложно — стирание строк отказа прекращено (G2). Но единственный оставшийся истинный вызывающий рисует полосу ИЗ ОДНОЙ БАЗЫ и открыт по построению против летящей загрузки (G3) |
| `app/templates/ads/includes/autosave_response.html` | включение полосы под условием | ⚠️ ЧАСТИЧНО | Жёсткий `refusals = []` теперь недостижим на текстовом автосохранении; на пути убирания блок по-прежнему подменяет узел целиком |
| `app/templates/ads/includes/media_refusals.html` | единственный источник разметки строки отказа | ✓ VERIFIED | Два печатающих места (полоса и ветвь числа частей), одна разметка |
| `app/templates/ads/includes/media_strip.html` | полоса, включающая строки отказа | ✓ VERIFIED | `data-media` первым атрибутом; условный `hx-swap-oob`; строки отказа внутри узла |
| `app/templates/ads/includes/media_upload_form.html` | вызов макроса с `sync` | ⚠️ ЧАСТИЧНО | `sync='this:queue last'` на месте и виден в отрендеренной разметке; ЗАМЫКАНИЕ на свой элемент оставляет путь убирания несериализованным (G3) |
| `tests/test_pages/test_ads_image_upload.py` | правила на шов двух фрагментов | ⚠️ ПРОБЕЛ ПОКРЫТИЯ | Семь новых правил заведены и зелены, включая ДВА сводящих обработчика. Правила на взаимодействие УБИРАНИЯ и ЗАГРУЗКИ нет ни одного |
| `tests/test_services/test_image_keys.py` | `test_partition_keeps_order_and_separates_the_foreign` | ✓ VERIFIED | Существует, зелено |
| `tests/test_pages/test_origin_guard_on_destructive_routes.py` | замер 14 с переписанной летописью | ✓ VERIFIED | Запись сходится с деревом точно |
| `.../deferred-items.md` | записанные допущения D-16 и D-17 | ✓ VERIFIED | Оба со статусом `accepted-assumption`, с названным воздействием и отвергнутыми альтернативами. ⚠️ Исход G3 ни одним из них не покрыт |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `media_upload_form.html` | `ads_images_upload` | `hx-post`, `hx-target`, `hx-encoding`, `hx-include` | ✓ WIRED | Прочитано в ОТРЕНДЕРЕННОЙ странице, а не в исходнике шаблона (зонд З) |
| `partition_own_image_keys` | `own_image_keys` + `ads_images_upload` | один предикат, два вызывающих | ✓ WIRED | Второго места, решающего «мой ли ключ», в дереве нет |
| скрытое поле `name="images" form="ad-form"` | `_save_from_editor` | `form_data.getlist("images")` | ✓ WIRED | Зонд Е замыкает связь ОДНИМ прогоном двух обработчиков |
| `store_upload` → отказ хранилища | цикл `ads_images_upload` | `except HTTPException` пофайлово | ✓ WIRED | Зонд В: исключение больше не выходит мимо сборщика |
| `is_same_origin` | `ads_images_upload` | вызов ПОСЛЕ прав, ДО `request.form()` | ✓ WIRED | Зонд Ж: 403 без тела, ноль записей в хранилище |
| `MAX_UPLOAD_PARTS` → `request.form` | `upload_parts_message` → `media_refusals.html` | перехват `StarletteHTTPException` | ✓ WIRED | Строка дописывается `HX-Reswap: beforeend`, полосу не подменяет |
| `HX-Trigger-After-Swap` | `hx-trigger="… ads-image-attached from:body"` | заголовок → всплытие | ✓ WIRED (контракт) | Круг замкнут и больше НЕ стирает строку отказа (G2) |
| `hx-sync` формы загрузки | `hx-sync` формы объявления | `this:queue last` у обеих | ⚠️ WIRED, НО НЕ ТО, ЧТО НУЖНО | Значения равны и правило это держит; очереди РАЗНЫЕ, потому что `this:` замкнут на элемент. Между двумя формами сериализации НЕТ — механизм G3 |
| ответ убирания | `#media-tray` | `hx-swap-oob="true"` из `ad.images` | ⚠️ WIRED, И ИМЕННО ЭТО ЛОМАЕТ | Единственный оставшийся вызывающий перерисовки из отстающей базы (G3) |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `media_strip.html` (ответ загрузки, счастливый путь) | `image_keys` | подтверждённые присланные ключи + ключи принятых файлов | Да | ✓ FLOWING |
| `media_strip.html` (ветвь отказа СВЕРКИ) | `image_keys` | `partition_own_image_keys(...)[0]` — подтверждённое подмножество | **Да (было `[]`)** | ✓ FLOWING (прежний HOLLOW_PROP снят) |
| `media_strip.html` (ветвь отказа хранилища) | `image_keys` | ключи частей 1..n-1 | Да | ✓ FLOWING |
| `media_refusals.html` (ветвь числа частей) | `refusals` | `upload_parts_message(MAX_UPLOAD_PARTS)` | Да | ✓ FLOWING |
| `media_strip.html` (ответ автосохранения, текст) | — | блок не рендерится вовсе | н/п | ✓ FLOWING (стирания нет) |
| `media_strip.html` (ответ автосохранения, убирание) | `image_keys` | `ad.images` перечитанной записи | Да, но ОТСТАЁТ от документа на незаписанный ключ | ⚠️ STATIC относительно летящей загрузки (G3) |
| строка отказа | `display_name` | `safe_filename()` в СЕРВИСЕ | Да | ✓ FLOWING |
| строка отказа ownership-ветви | `display_name` | литерал `""` | Имени нет намеренно | ⚠️ по построению (остаток «б», WR-08) |

### Behavioral Spot-Checks

Все зонды написаны и исполнены ВЕРИФИКАТОРОМ (временный модуль, удалён после прогона), а не взяты
из суиты фазы.

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| **Зонд А** — свой + чужой ключ в ОДНОЙ партии | POST `/ads/images`, `images=[свой, чужой]` + годный файл | `status 200`; `own survived: True`; `foreign echoed: False`; `hidden count: 1`; `s3 calls: 0`; одна строка отказа | ✓ PASS (гап 1 закрыт) |
| **Зонд Б** — 11 СВОИХ ключей при потолке 10 (путь без нападающего) | тот же зонд, 11 корректных ключей владельца | `hidden count: 11`, `all survived: True`; входящий файл → строка про потолок | ✓ PASS (достижимость «а» закрыта) |
| **Зонд В** — авария хранилища посреди партии | подмена `upload_file_to_s3`, падение на второй части | `status 200`; ключ `one.png` в документе; строка `two.png — файл не сохранился…` | ✓ PASS (третий пункт `missing` закрыт) |
| **Зонд Г** — строка отказа против автосохранения, которое сама заказала | частичная партия → затем ровно то автосохранение | строка отказа есть; `HX-Trigger-After-Swap: ads-image-attached`; `autosave carries media-tray: False` | ✓ PASS (гап 2 закрыт) |
| **Зонд Д** — покупка плана 12-03 не потеряна | POST `/ads/{id}/edit` с `remove_image` | `oob tray: True`; ключ убран; база обновлена | ✓ PASS |
| **Зонд Е** — пережившие ключи записываются следующим сохранением | ответ загрузки → скрытые поля → POST `/ads/new` | `own key persisted: True`, `ad.images = [свой ключ]` | ✓ PASS (два обработчика сведены) |
| **Зонд Ж** — межсайтовая форма | `Origin: http://evil.example`; затем `Sec-Fetch-Site: cross-site` | `403`, тело пустое, `s3 calls: 0` в обоих случаях | ✓ PASS (D-15 исполнено) |
| **Зонд З** — отрендеренный редактор | GET `/ads/new` | `fetch(` → 0; форма несёт `hx-sync="this:queue last"`, `hx-indicator="find .form-busy"` | ✓ PASS |
| **Зонд WR-07 (свой)** — убирание НАКЛАДЫВАЕТСЯ на летящую загрузку | (1) POST загрузки со снимком `[A,B]` + файл C; (2) POST убирания A; (3) применение ответа (1) и заказанного им автосохранения | ПОРЯДОК I: `db = [A, B, C]`, **`deleted key A resurrected: True`**. ПОРЯДОК II: **`C present in removal tray: False`** при `s3 calls: 2` — ключ записан в хранилище и вынесен из документа | ✗ **FAIL (гап 3 остаётся открытым)** |
| Целевой прогон затронутых модулей | `uv run pytest tests/test_pages/test_ads_image_upload.py tests/test_services/test_image_keys.py tests/test_services/test_image_upload.py tests/test_pages/test_ads_editor.py tests/test_pages/test_origin_guard_on_destructive_routes.py tests/test_pages/test_htmx_gates.py tests/test_templates/test_htmx_markup_gates.py tests/test_nginx_body_limit.py tests/test_planning -q -p no:randomly` | `315 passed` (96 s) | ✓ PASS |
| Долговые пометки в 36 файлах диффа фазы | `grep -n -E "TBD\|FIXME\|XXX"` по каждому | `0` | ✓ PASS |
| Отключённые правила в модулях фазы | `grep -rn "pytest.mark.skip\|xfail"` | пусто | ✓ PASS |

Полная суита повторно не запускалась: замер оркестратора (3437 passed; `tests/test_planning/` — 44
passed после отката отметки FETCH-01) принят и подтверждён целевым прогоном 315 правил.

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| Конвенционных `scripts/*/tests/probe-*.sh` в дереве нет | `find scripts -path '*/tests/probe-*.sh'` | пусто | n/a — фаза probe-проверок не объявляет |

### Decision Coverage

`gsd_run query check.decision-coverage-verify` → **17 из 17** решений `12-CONTEXT.md` honored,
`not_honored: []`. Гейт не блокирующий; записан для истории.

Отдельно, по прямому запросу: **оба решения владельца, поднятые прошлой верификацией как открытые
вопросы, ИСПОЛНЕНЫ и как открытые больше не поднимаются.**

- **D-15** (гарда источника на загрузке) — исполнено планом 12-10. `is_same_origin(request)`
  зовётся в `ads_images_upload` (`ads.py:877`), ПОСЛЕ прав и ДО `request.form()`; замер
  инвертирован вверх (13 → 14) и сходится с деревом точно. Зонд Ж: 403 без тела, ноль записей.
- **D-16 / D-17** (допущение о конкурентности) — решение владельца принято и записано планом 12-07
  в `deferred-items.md` двумя пунктами со статусом `accepted-assumption`, с названным воздействием
  и отвергнутыми альтернативами. ⚠️ Записи покрывают ОБРЫВ партии, межвкладочный счёт и вытеснение
  среднего выбора; исход G3 (убирание против загрузки) не покрыт ни одной из них.
- **D-18** (восемь запретов со `verification: none`) — принято владельцем informational-записью;
  пункт 9 прошлого `human_verification` закрыт. Перечень перенесён в `flagged_prohibitions`
  целиком, а не снят молча.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| FETCH-01 | 12-01…12-10 (все десять) | «загрузка изображения объявления идёт htmx-фрагментом вместо `fetch()` + JSON; успешно загруженные файлы остаются прикреплёнными, даже если часть отвалилась» | ✓ SATISFIED | Первая половина — R1, P1–P23 (зонд З: `fetch(` в отрендеренном редакторе 0). Вторая половина — R2/G1/N1, проверена четырьмя СВОИМИ зондами на трёх путях отказа (сверка ключей, потолок, авария хранилища). Отметка в `.planning/REQUIREMENTS.md:149` корректно откачена в `Gaps Found` коммитом `a17052f9`; после этого вердикта она движется закрытием фазы, а не вручную. ⚠️ Гап G3 живёт в НАЛОЖЕНИИ двух действий, которого текст требования не называет, поэтому требование не BLOCKED — но фаза не завершена |

Осиротевших требований нет: `REQUIREMENTS.md` относит к Фазе 12 ровно FETCH-01, и его объявили все
десять планов. `UPLD-01` (проценты загрузки) числится `Deferred` в v2.2 — вне объёма по объявлению
критерия 4.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| `tests/test_pages/test_ads_image_upload.py` | FETCH-01 | все | 0 | нет | Behavioral (два правила рендерят ДВА фрагмента друг против друга и сводят два обработчика) | ✓ достаточно на измеренных путях |
| `tests/test_services/test_image_keys.py` | FETCH-01 | все | 0 | нет | Value | ✓ |
| `tests/test_services/test_image_upload.py` | FETCH-01 | все | 0 | нет | Value | ✓ |
| `tests/test_pages/test_origin_guard_on_destructive_routes.py` | FETCH-01 | все | 0 | нет | Value + отрицательный контроль | ✓ |
| `tests/test_templates/test_htmx_markup_gates.py` | FETCH-01 | все | 0 | нет | Value (равенство строк стратегий) | ⚠️ утверждение СЛАБЕЕ текста своего отказа: равенство двух `this:`-стратегий не покупает «плитки не пропадают БЕЗ сообщения» между двумя элементами |

**Disabled tests on requirements:** 0. **Circular patterns detected:** 0.
**Insufficient assertions:** 1 ⚠️ (гейт равенства стратегий — см. строку выше; входит в `missing` гапа).

Отдельно отмечено в пользу партии: прежнее правило `test_a_foreign_key_is_not_echoed_back`,
закреплявшее ПУСТУЮ полосу, не переписано и не ослаблено — рядом с ним заведено более сильное
`test_an_own_key_survives_a_foreign_key_in_the_same_batch`. То же с
`test_a_storage_failure_still_answers_bad_gateway` → `…becomes_a_row_and_keeps_the_accepted_keys`:
утверждение инвертировано ВВЕРХ вместе с предметом.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | `TBD` / `FIXME` / `XXX` в 36 файлах диффа фазы | — | **Ноль вхождений.** Гейт долговых пометок пройден |
| `app/pages/ads.py` | 618-621, 680-682 | Перерисовка состояния из источника, отстающего от документа, при отсутствии сериализации с конкурирующим запросом | 🛑 Blocker | Убранный ключ воскресает в базе ЛИБО принятый ключ теряется вместе с объектом-сиротой (G3). Carried-forward gap + файл изменён этой партией + предъявлено воспроизведение |
| `app/templates/ads/includes/media_upload_form.html` | 64 | Очередь, замкнутая на элемент, при соседней форме с собственной очередью | 🛑 Blocker | Тот же механизм со стороны разметки |
| `app/pages/ads.py` | 1016-1045 | Ветвь ownership-отказа пропускает цикл по файлам целиком (WR-08) | ⚠️ Warning | На остатке «б» (законный ключ старого образца) вся выбранная человеком партия не обрабатывается, а единственная строка говорит о КЛЮЧЕ, не называя ни одного файла. Зонд А подтверждает: `s3 calls: 0`, про `cat.png` ни строки. На пути нападающего это ПРАВИЛЬНО и защищено запретом плана 12-06 |
| `app/pages/ads.py` | 1065-1079 | Остаток «б»: ключ в `Ad.images`, не проходящий сегодняшний образец, отцепляется с безымянной строкой | ⚠️ Warning | НАЗВАН, а не пропущен: комментарий выписывает достижимость, отвергнутые альтернативы и сравнение с состоянием ДО фазы |
| `tests/test_templates/test_htmx_markup_gates.py` | 7318-7331 | Текст отказа обещает свойство шире измеряемого | ⚠️ Warning | Следующий читатель прочтёт гейт как защиту от межформенной потери, которой тот не даёт |
| `nginx/*.conf.template`; `autosave_response.html:55-64`; `ads.py:931`, `:1127-1136`, `:1096`; `media_*.html` | — | WR-02, IN-02…IN-06 | 📋 Advisory | Предсуществуют партии либо приняты владельцем; ни одна не предъявлена покрасневшим правилом. Подробности — в разделе Advisory |

### Human Verification Required

Семь пунктов; **решений владельца среди них больше нет** — три прежних (D-15, D-16/D-17, D-18)
исполнены и записаны. Полный текст — в `human_verification` frontmatter. Сокращённо:

1. **Критерий 4** (по объявлению ROADMAP): индикатор «идёт запрос» виден при выборе файла.
2. **Боевой стенд:** переразвернуть nginx, бросить 10 снимков по 4–5 МБ, убедиться в отсутствии 413.
3. **Кнопка «×»:** плитка исчезает после круга к серверу, текст не теряется.
4. **Порог счётчика** переключается на ближайшем нажатии клавиши.
5. **`/ads/new`:** прикрепить картинку, не набрав ни символа, обновить страницу (допущение A2).
6. **Пять файлов на два места:** строки отказа названы поимённо и ОСТАЛИСЬ (машинно закрыто зондом
   Г; подтвердить время жизни на экране).
7. **НАБЛЮДЕНИЕ ГАПА:** выбрать крупный файл и нажать «×» ПОКА идёт загрузка — какой из двух
   исходов зонда WR-07 виден в браузере.

### Gaps Summary

**Что партия закрытия сделала — и сделала честно.** Два несущих гапа закрыты механизмом, который
назывался в `missing`, а не подгонкой под правило. `partition_own_image_keys` стал единственным
предикатом принадлежности, и ветвь отказа отвечает ПОДТВЕРЖДЁННЫМ подмножеством: мои собственные
зонды, повторяющие прошлые зонды А и Б дословно, теперь дают `1 из 1` и `11 из 11` скрытых полей
вместо нуля. Авария хранилища стала отказом ПО ФАЙЛУ. Строка отказа переживает круг, который сама
заказывает, — потому что ответ автосохранения теперь не приносит полосу ВООБЩЕ, пока состав
вложений не изменён. Предел числа частей перестал уходить человеку сырым JSON. Гарда источника
зовётся, и замер инвертирован вверх вместе с предметом. Ни одной долговой пометки; ни одного
отключённого правила; два замеряющих правила инвертированы ВВЕРХ, а не переписаны; решения владельца
исполнены все.

**Что осталось — ровно одно, и оно наследник гапа 3.** Решение D-16 состоит из двух половин. Первая
(«форма загрузки получает `sync`») исполнена. Вторая — «ответ автосохранения ПЕРЕСТАЁТ
перерисовывать полосу из отстающей базы» — исполнена для всех вызывающих, кроме того ЕДИНСТВЕННОГО,
который с загрузкой пересекается. Кнопка «×» — отправка формы `#ad-form`; очередь `hx-sync`
замкнута на элемент (`this:`), и комментарий формы загрузки сам это пишет: «очередь одной на другую
не распространяется». Значит убирание и загрузка летят одновременно, а ответ убирания перерисовывает
полосу из базы, которая о летящем ключе не знает.

Я не принял это из ревизии на слово — я воспроизвёл обе развязки зондом на уровне HTTP:

- **Ответ загрузки последним:** документ получает `[A, B, C]`, и автосохранение, заказанное
  заголовком ТОГО ЖЕ ответа, пишет `ad.images = [A, B, C]`. Удаление, которое человек СДЕЛАЛ, молча
  отменено — замер `deleted key A resurrected in db: True`.
- **Ответ убирания последним:** внеполосная полоса `[B]` выносит из документа скрытое поле ключа
  `C`, уже записанного в хранилище (`s3 calls: 2`). Человек видел плитку, она исчезла БЕЗ
  сообщения, объект остался сиротой.

Это дословно истина гапа 3 — «полоса не теряет только что принятый ключ при наложении запросов» — и
дословно второй пункт его `missing`: «ответ автосохранения не перерисовывает полосу, пока загрузка
в полёте (либо перерисовывается ОБЪЕДИНЕНИЕМ базы и присланных ключей, а не одной базой)». Ни один
из двух предписанных приёмов к пути убирания не применён.

Почему это блокирует, а не идёт советом. Три причины, и каждая проверена: (1) находка есть
ПЕРЕНЕСЁННЫЙ гап, а не новый взгляд — совпадение с текстом гапа 3 прямое; (2) оба файла изменены
ЭТОЙ партией; (3) предъявлено воспроизведение командой с выводом, а не рассуждение. Любого одного
из трёх хватило бы. Достижимость не экзотическая: загрузка держит запрос открытым на
декодирование, пережатие и два круга к хранилищу — человек, прибирающий вложения, пока грузится
новое, попадает в это окно обычным темпом работы.

Запрет плана 12-07 — «всё, что прикрепилось, остаётся видимым» — задет ровно здесь, и в отличие от
двух других задеваний (вытеснение среднего выбора, WR-08) это НЕ записано ни в `deferred-items.md`,
ни в CONTEXT. Поэтому исход и назван гапом: у него нет ни починки, ни записи. Закрыть его можно
тремя способами, и выбор принадлежит владельцу — общая очередь двух форм, объединение базы с
присланным снимком, либо запись допущения той же формы, какую получили D-16 и D-17. Правило,
сводящее убирание и загрузку, нужно в любом из трёх случаев: сегодня оба обработчика зелены по
отдельности — ровно та слепота, из-за которой прошли и три предыдущих дефекта.

Наконец, отметка `FETCH-01 = Complete` откачена правильно (`a17052f9`), и снимать её обратно до
закрытия этого гапа не следует: правило `tests/test_planning/` право по существу, а не только по
процедуре.

---

_Verified: 2026-09-19T11:52:10Z_
_Verifier: Claude (gsd-verifier)_
