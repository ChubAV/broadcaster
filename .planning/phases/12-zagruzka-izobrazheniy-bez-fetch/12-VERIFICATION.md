---
phase: 12-zagruzka-izobrazheniy-bez-fetch
verified: 2026-09-19T06:22:32Z
status: gaps_found
score: 23/27 must-haves verified
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
  - "README.md"
  - "app/main.py"
  - "app/pages/ads.py"
  - "app/pages/common.py"
  - "app/services/image_keys.py"
  - "app/services/image_upload.py"
  - "app/services/images.py"
  - "app/templates/ads/form.html"
  - "app/templates/ads/includes/autosave_response.html"
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
  - "tests/test_services/test_image_upload.py"
  - "tests/test_templates/test_ads_form_security.py"
  - "tests/test_templates/test_components.py"
  - "tests/test_templates/test_htmx_inventory.py"
  - "tests/test_templates/test_htmx_markup_gates.py"
  - "tests/test_templates/test_walkthrough_anchors.py"
covered_digest: "v1:sha256:1114f91d316a10c0ef334b2cb3e63466a4233218baa6c078dc7e2a4611b56530"
behavior_unverified: 3
overrides_applied: 0
gaps:
  - truth: "Успешно загруженные файлы остаются прикреплёнными, даже если часть отвалилась (Критерий 2 ROADMAP)"
    status: partial
    reason: >-
      Свойство держится на пути, который критерий НАЗЫВАЕТ (один годный + один негодный ФАЙЛ в
      партии): годный остаётся прикреплённым, негодный получает свою строку. Оно НЕ держится на
      пути отказа СВЕРКИ КЛЮЧЕЙ: при отказе `own_image_keys` обработчик отдаёт фрагмент с
      `image_keys=[]`, а подмена `innerHTML` цели `#media-strip` выносит из документа ВСЕ скрытые
      поля `name="images"` — включая ключи, которые сверку прошли. Полоса после плана 12-03 —
      ЕДИНСТВЕННЫЙ источник `images` в DOM (клиентский `imagePaths` снят), поэтому следующее
      автосохранение (одно нажатие клавиши) сериализует ноль вложений, `own_image_keys([])`
      проходит, и `ad.images = []` записывается в базу. Проверено СВОИМ зондом верификатора, а не
      прочитано в ревизии.
    artifacts:
      - path: "app/pages/ads.py"
        issue: >-
          Строки 822/838-851: `image_keys` инициализирован `[]`, ветвь `except HTTPException`
          присваивания не делает и отдаёт авторитетно выглядящую ПУСТУЮ полосу. Восстановить
          состояние из базы (или сохранить подмножество, прошедшее образец и префикс) ветвь не
          пытается.
      - path: "app/pages/ads.py"
        issue: >-
          Строки 533-588 (`_save_from_editor`): `ad.images = image_list`, где `image_list` целиком
          из формы. Пустой набор полей `images` = стирание вложений, и `own_image_keys([])` этому
          не мешает.
      - path: "app/services/image_upload.py"
        issue: >-
          `store_upload` поднимает `HTTPException(502)` при аварии хранилища; исключение уходит
          наверх мимо сборщика фрагмента, поэтому ключи частей 1..n-1, уже записанных в хранилище,
          до DOM не доезжают вовсе (на 5xx подмены нет). Правило
          `test_a_storage_failure_still_answers_bad_gateway` закрепляет это поведение.
    missing:
      - "Ветвь отказа сверки не должна отвечать пустой полосой: перерисовывать из ПОДТВЕРЖДЁННОЙ базой истины либо оставлять подмножество, индивидуально прошедшее образец и префикс, отвергая только виновные значения."
      - "Достижимость без нападающего названа поимённо: (а) `max_images_per_ad`, опущенный ниже числа уже прикреплённых — `own_image_keys` поднимает отказ ПО ДЛИНЕ до любой проверки ключа (зонд Б: 11 СВОИХ законных ключей при потолке 10 → полоса пуста); (б) ключ в `Ad.images`, не проходящий сегодняшний образец (запись не перезаписывается никогда). До фазы такой ключ ГРОМКО блокировал сохранение; теперь попытка загрузки ТИХО его отцепляет."
      - "Авария хранилища посреди партии обязана становиться отказом ПО ФАЙЛУ, а не ответом 5xx: иначе уже принятые ключи теряются вместе с ответом."
  - truth: "Каждый отвергнутый файл получает СВОЮ строку со СВОЕЙ причиной — та самая покупка, ради которой D-04 заплатил лживым кодом 200"
    status: failed
    reason: >-
      Строка отказа стирается тем же кругом, который этот же ответ и заказывает. На частичной
      партии (≥1 принят, ≥1 отвергнут) обработчик ставит `attached = True` и заголовок
      `HX-Trigger-After-Swap: ads-image-attached`; форма объявления слушает ровно это событие БЕЗ
      модификатора задержки, поэтому автосохранение уходит немедленно после подмены полосы. Ответ
      автосохранения жёстко задаёт `refusals = []` и подменяет `#media-tray` ЦЕЛИКОМ внеполосным
      блоком, а строки отказа живут ВНУТРИ этого узла. Человек читает причину один круг к серверу и
      теряет её — на самом частом пути «бросил папку файлов». Ни одно правило суиты не сводит два
      фрагмента вместе, поэтому суита зелена.
    artifacts:
      - path: "app/templates/ads/includes/autosave_response.html"
        issue: "Строка 41: `{%- set refusals = [] %}` — список отказов обнуляется безусловно; строка 43 включает полосу с `oob`, унаследованным от строки 36."
      - path: "app/templates/ads/includes/media_strip.html"
        issue: "Строки 69-71: строки отказа стоят ВНУТРИ `#media-tray`, то есть внутри внеполосной цели автосохранения."
      - path: "app/templates/ads/form.html"
        issue: "Строка 153: `ads-image-attached from:body` без задержки — круг стирания начинается сразу после подмены."
    missing:
      - "Либо строки отказа выносятся ЗА `#media-tray` (свой постоянный узел, которого ответ автосохранения не трогает), либо `_autosave_response` принимает и переиздаёт ожидающий список отказов вместо литерального `[]`."
      - "Правило суиты на ВЗАИМОДЕЙСТВИЕ двух фрагментов: сегодня оба зелены по отдельности, и именно поэтому дефект прошёл."
  - truth: "Полоса вложений — состояние в DOM — не теряет только что принятый ключ при наложении запросов"
    status: failed
    reason: >-
      Форма загрузки не объявляет стратегии наложения вовсе (в вызове `form_wrapper` нет `sync`),
      тогда как форма объявления несёт `hx-sync="this:queue last"` — и это РАЗНЫЕ элементы, так что
      очередь между ними не работает. Летящее автосохранение (дебаунс 2 с от набора текста) рисует
      `#media-tray` из БАЗЫ, которая нового ключа ещё не знает, и внеполосно заменяет только что
      подменённую полосу; следующее автосохранение сериализует уже обобранный DOM. Тот же механизм
      даёт потерю между двумя быстрыми выборами файлов: второй ответ подменой `innerHTML`
      затирает ключи первого, объекты остаются в хранилище сиротами, а человек видит меньше плиток,
      чем выбрал файлов, БЕЗ сообщения.
    artifacts:
      - path: "app/templates/ads/includes/media_upload_form.html"
        issue: "Строки 34-40: вызов макроса без `sync` — двойной выбор файлов даёт два летящих POST, каждый со своим снимком ключей."
      - path: "app/templates/ads/includes/autosave_response.html"
        issue: "Строки 40-43: внеполосная полоса рисуется из `ad.images`, то есть из состояния, отстающего от DOM на незаписанный ключ."
    missing:
      - "Сериализация формы загрузки тем же приёмом, каким сериализована форма объявления (`sync='this:queue last'` — параметр у макроса уже есть)."
      - "Правило: ответ автосохранения не перерисовывает полосу, пока загрузка в полёте (либо полоса перерисовывается объединением базы и присланных ключей, а не одной базой)."
deferred: []
behavior_unverified_items:
  - truth: "Пользователь видит, что загрузка идёт — бинарный `hx-indicator` (Критерий 4 ROADMAP, ручной UAT по объявлению)"
    test: "В редакторе выбрать файл и наблюдать признак «идёт запрос» до прихода плитки."
    expected: "Признак `.form-busy` виден в течение запроса и гаснет после подмены полосы."
    why_human: "Разметочная половина проверена машинно (макрос печатает `hx-indicator=\"find .form-busy\"` и сам узел `.form-busy`), но ВИДИМОСТЬ — свойство браузера и CSS; суита рантайм разметки не исполняет."
  - truth: "Порог счётчика символов переключается по числу плиток полосы (клиентская половина D-11)"
    test: "У объявления с вложением набрать текст длиной между порогом подписи и общим порогом."
    expected: "Счётчик желтеет на ближайшем нажатии клавиши (не в момент подмены полосы — следствие названо планом)."
    why_human: "Серверная половина (класс счётчика в отрендеренной разметке) закрыта двумя правилами; переключение порога — переход состояния в исполняемом JS, которого суита не исполняет."
  - truth: "На боевом стенде партия из десяти снимков по 4–5 МБ доезжает до приложения, а не получает 413 от прокси"
    test: "После ПЕРЕРАЗВЁРТЫВАНИЯ nginx выбрать десять снимков по 4–5 МБ разом; смотреть `just prod-logs nginx`."
    expected: "Все десять прикрепляются, 413 в логах прокси нет, общая плашка не поднимается."
    why_human: "nginx в среде разработки отсутствует; правило суиты доказывает согласованность ИСХОДНИКОВ шаблонов с `Settings`, а не состояние работающего прокси. Запись 92 `.planning/WINDOWS.md`, статус `open`."
flagged_prohibitions:
  - statement: "комментарии-обоснования переносятся ДОСЛОВНО (D-03)"
    plan: "12-01"
    verification: none
    judge: "not-violated (НЕАВТОРИТЕТНО): 25 из 25 непустых строк абзаца `master:app/routes/uploads.py:32-60` найдены дословно (`grep -F`) в `app/services/image_upload.py`."
    flag: "unverified-prohibition — human review recommended"
  - statement: "инвентарное число ставится ПРОГОНОМ покрасневшего правила, а не вычитанием в уме (D-13)"
    plan: "12-01, 12-03, 12-05"
    verification: none
    judge: "not-violated (НЕАВТОРИТЕТНО): все проверенные числа сходятся с деревом (MANUAL_FETCH_PLACES=5 при пяти `fetch(` в `connect_tg_user.html`, OOB_BLOCKS=20, HX_HEADER_WRITES=4, PAGE_POST_HANDLERS_MEASURED=37), но ПРОЦЕСС постановки числа машинного отрицания не имеет."
    flag: "unverified-prohibition — human review recommended"
  - statement: "потолок партии не сужается ради того, чтобы вписаться в прежнее значение прокси (OQ-2)"
    plan: "12-02"
    verification: none
    judge: "not-violated (НЕАВТОРИТЕТНО): `app/config.py` в диффе фазы отсутствует."
    flag: "unverified-prohibition — human review recommended"
  - statement: "гейт безопасности не ослабляется и не снимается ради зелени — утверждение ИНВЕРТИРУЕТСЯ на более сильное (G-2)"
    plan: "12-03"
    verification: none
    judge: "not-violated (НЕАВТОРИТЕТНО): `test_ads_form_uses_property_assignment` требует `== 0` обоих имён вместо прежних `>= 3` / `>= 2`; соседнее правило «разметка не собирается строкой» на месте."
    flag: "unverified-prohibition — human review recommended"
  - statement: "потолок вложений не считается вторым инструментом рядом с `own_image_keys` (D-07, Hyrum)"
    plan: "12-04"
    verification: none
    judge: "not-violated (НЕАВТОРИТЕТНО): в срезе обработчика `own_image_keys` встречается один раз, `free` считается одной строкой из его результата."
    flag: "unverified-prohibition — human review recommended"
  - statement: "объявленный клиентом тип части не получает авторитета при разборе партии (CR-02 безопасности)"
    plan: "12-04"
    verification: none
    judge: "not-violated (НЕАВТОРИТЕТНО): обработчик присланный `content_type` не читает; тип определяется `sniff_image` по первым байтам, `content_type` объекта берётся из произведённых приложением байтов."
    flag: "unverified-prohibition — human review recommended"
  - statement: "перечни гейтов не подгоняются ради зелени — решение о поверхности отражено во всех"
    plan: "12-05"
    verification: none
    judge: "not-violated (НЕАВТОРИТЕТНО): закрытие обеспечено настоящей пер-роутерной зависимостью `ads_router` (`app/pages/__init__.py`: `include_router(ads_router, dependencies=[Depends(require_access)])`), то есть требование множества выполняется другим механизмом, а не отменено."
    flag: "unverified-prohibition — human review recommended"
  - statement: "чужое изъятие не снимается молча и не остаётся указывать на закрывшуюся фазу (D-14)"
    plan: "12-05"
    verification: none
    judge: "not-violated (НЕАВТОРИТЕТНО): `grep -c 'НАЗНАЧЕНО ФАЗЕ 12'` → 0, `grep -ci 'фазе 15'` → 2; историческая летопись Фазы 9 на месте."
    flag: "unverified-prohibition — human review recommended"
human_verification:
  - test: "Критерий 4: в редакторе выбрать файл — виден ли признак «идёт запрос» до появления плитки."
    expected: "Индикатор виден в течение запроса, гаснет после подмены полосы."
    why_human: "Ручной UAT по объявлению ROADMAP; видимость — свойство браузера и CSS."
  - test: "Боевой стенд: после переразвёртывания nginx бросить десять снимков по 4–5 МБ разом."
    expected: "Все десять прикрепляются; 413 в `just prod-logs nginx` нет."
    why_human: "nginx в среде разработки отсутствует; правка шаблона в гите боевой предел не двигает. Запись 92 WINDOWS.md."
  - test: "В редакторе объявления с двумя вложениями нажать «×» на первом."
    expected: "Плитка исчезает после круга к серверу, набранный текст не теряется, страница не перезагружается; предпросмотр и сводка обновляются тем же ответом."
    why_human: "Машинно проверен КОНТРАКТ ответа (внеполосный `#media-tray` с признаком подмены); применение блока живым документом суита не исполняет."
  - test: "У объявления с вложением набрать текст между порогом подписи и общим порогом."
    expected: "Счётчик желтеет на ближайшем нажатии клавиши."
    why_human: "Клиентская половина порога (чтение числа плиток из документа) — исполняемый JS, которого суита не исполняет."
  - test: "На `/ads/new` прикрепить одну картинку, НЕ вводя ни символа, затем обновить страницу."
    expected: "Картинка на месте, черновик создан — то есть событие ПОСЛЕ подмены всплыло до тела документа и форма объявления сохранилась уже с новым скрытым полем."
    why_human: "Прямая проверка допущения A2 разведки («событие соседа до формы объявления не долетает, поэтому нужно `from:body`»). Машинной проверки у всплытия нет."
  - test: "На `/ads/new` бросить пять файлов на два свободных места и СМОТРЕТЬ НА ЭКРАН не отрывая глаз."
    expected: "Две плитки появились, три строки отказа названы поимённо И ОСТАЛИСЬ ЧИТАЕМЫ."
    why_human: "Этот пункт теперь ещё и наблюдение гапа G2: ожидается, что строки отказа пропадут через один круг автосохранения (~100–300 мс). Человек обязан подтвердить или опровергнуть время жизни строки."
  - test: "РЕШЕНИЕ ВЛАДЕЛЬЦА: допущение о конкурентности, оставленное планом 12-04 открытым (оборванная партия оставляет объекты-сироты; две партии одного объявления считают места из своих снимков)."
    expected: "Принять как есть либо завести предметом отдельной фазы — запись, а не молчание."
    why_human: "Вопрос владельцу не задавался ни в обсуждении, ни в ROADMAP; машинного ответа у него нет."
  - test: "РЕШЕНИЕ ВЛАДЕЛЬЦА: гарда источника (`is_same_origin`) на маршруте загрузки — единственном пишущем в хранилище маршруте страничного слоя без неё."
    expected: "Либо вызов гарда, либо принятый риск, записанный с названным воздействием (расход хранилища при межсайтовой отправке до 64 МБ за запрос, повторяемо)."
    why_human: "Отсутствие ЗАМЕРЕНО (`PAGE_POST_HANDLERS_MEASURED` 37 при 13 местах вызова гарда) и унаследовано от снятого JSON-маршрута, но заново на страничной поверхности не принималось."
  - test: "РЕШЕНИЕ ВЛАДЕЛЬЦА по восьми запретам планов со `verification: none` (список `flagged_prohibitions`)."
    expected: "Подтвердить неавторитетные суждения верификатора либо назвать проверку, которая их закрепит."
    why_human: "Ни у одного из восьми нет ПРАВИЛА, краснеющего при нарушении; планы объявили им `verification: none` заранее."
---

# Phase 12: Загрузка изображений без `fetch()` — Verification Report

**Phase Goal:** изображение объявления прикрепляется htmx-фрагментом, и ни одна строка шаблона не собирает запрос руками
**Verified:** 2026-09-19T06:22:32Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

Цель фазы в её БУКВЕ достигнута: загрузка идёт htmx-фрагментом, `fetch(` в `ads/form.html` ноль,
ручной сборки запроса в разделе объявлений не осталось. Три из четырёх критериев ROADMAP держатся
кодом, а не прозой сводок. Дефекты лежат ровно в одном месте — **шве между фрагментом загрузки и
фрагментом автосохранения**, — и оба несущих дефекта попадают в критерий 2, единственный критерий,
который говорит о СУДЬБЕ уже прикреплённого.

### Observable Truths

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| R1 | **Критерий 1.** Загрузка идёт htmx-фрагментом в `#media-strip`; `fetch()` и массив `imagePaths` из `ads/form.html` исчезли; ключ приезжает скрытым полем с `form="ad-form"` | ✓ VERIFIED | `grep -c` по `app/templates/ads/form.html`: `fetch`→0, `createElement`→0, `replaceChildren`→0, `id="image-inputs"`→0, `id="upload-error"`→0; единственное вхождение `imagePaths` — проза комментария :455, перечисляющая снятое. `id="media-strip"`→1, оба включения на месте. Тело `<script>` 235→125 строк (минус 110 при заявленных «~70»). `media_strip.html:89` — `<input type="hidden" name="images" value="{{ key }}" form="ad-form">`. Правило `test_one_image_over_htmx_returns_the_strip_fragment` зелено |
| R2 | **Критерий 2.** Успешно загруженные файлы остаются прикреплёнными, даже если часть отвалилась | ✗ FAILED | Держится на пути, который критерий НАЗЫВАЕТ (`test_partial_batch_keeps_the_accepted_file` зелено). НЕ держится на пути отказа сверки ключей: зонд верификатора (свой ключ + чужой ключ, одна партия) → `STATUS 200`, скрытых полей `name="images"` **0**, свой законный ключ во фрагменте **отсутствует**. Второй зонд БЕЗ нападающего (11 своих законных ключей при `max_images_per_ad`=10) → то же: полоса пуста. Далее `_save_from_editor` пишет `ad.images = image_list` из формы, то есть `[]`. См. гап 1 |
| R3 | **Критерий 3.** Отказ доступа на загрузке виден пользователю; решение о поверхности отражено в ОБОИХ гейтах перечня | ✓ VERIFIED | `app/pages/__init__.py`: `router.include_router(ads_router, dependencies=[Depends(require_access)])` — закрытие НАСТОЯЩЕЕ, а не снятая запись. `GATED_API_ROUTERS` и `BLOCK_CHECKED_API_ROUTERS` по 4 роутера, `uploads_router` в дереве ноль вхождений. Третий перечень (гейт подстановки личности) перенацелен: `app/pages/ads.py::ads_images_upload`. `test_upload_is_closed_by_the_router_access_gate` зелено (204 + `HX-Location`) |
| R4 | **Критерий 4.** Пользователь видит, что загрузка идёт — бинарный `hx-indicator` | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Макрос печатает `hx-indicator="find .form-busy"` (`form_wrapper.html:195`) и сам узел `.form-busy` (:197); форма загрузки рождена макросом. Ручной UAT по объявлению ROADMAP — видимость суитой не исполняется |
| P1 | Годный файл на `/ads/images` с признаком htmx → 200 и фрагмент полосы с плиткой и скрытым полем | ✓ VERIFIED | `test_one_image_over_htmx_returns_the_strip_fragment`; ключ формы `{user_id}/{32 hex}_{имя}.png` |
| P2 | Тот же адрес БЕЗ признака htmx → 302 на `/ads/new`; путь деградации заполнен честно | ✓ VERIFIED | `test_upload_without_htmx_redirects_to_the_editor`; реестр пар транспортов. ⚠️ см. IN-04: путь делает всю работу и выбрасывает ключи |
| P3 | Гейта в теле обработчика нет ни строкой | ✓ VERIFIED | `awk '/^async def ads_images_upload/,/^@router/' app/pages/ads.py \| grep -c require_access` → 0; объяснение вынесено над декоратором (:752-763) |
| P4 | Не-транспортная логика в `app/services/image_upload.py`; комментарии перенесены ДОСЛОВНО; порядок «размер ВЫШЕ типа» сохранён | ✓ VERIFIED | 25/25 непустых строк абзацев `master:app/routes/uploads.py:32-60` найдены `grep -F` в новом модуле; `tests/test_services/test_image_upload.py` — 53 passed; `test_oversized_beats_unsupported` зелено |
| P5 | Число частей составного запроса ограничено явно — второй рубеж | ✓ VERIFIED | `request.form(max_files=MAX_UPLOAD_PARTS, max_fields=MAX_UPLOAD_PARTS)` (`ads.py:801-803`). ⚠️ WR-01/WR-06: ОБОСНОВАНИЕ рубежа в комментарии фактически неверно, а его отказ человеку нечитаем |
| P6 | Форма загрузки рождена макросом `form_wrapper`; отступление цели блокировки записано поимённо | ✓ VERIFIED | `media_upload_form.html:34-40`; `test_every_htmx_post_is_born_of_a_component_macro` и `test_every_disabled_elt_exception_is_actually_an_exception` зелены; `type="submit"` в файле → 0 (D-09) |
| P7 | Оба шаблона nginx объявляют `64M` с формулой прозой; потолок приложения не тронут; расхождение краснит суиту | ✓ VERIFIED | `tests/test_nginx_body_limit.py` — 4 passed, включая контроль зубов; `max_images_per_ad` в обоих шаблонах; `app/config.py` в диффе фазы отсутствует. ⚠️ WR-02: значение стои́т в блоке `server`, то есть поднято для ВСЕХ адресов |
| P8 | Боевой предел прокси действует: партия 10×4–5 МБ доезжает | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Правило читает ИСХОДНИК шаблона; nginx в среде разработки отсутствует; нужно переразвёртывание (запись 92 WINDOWS.md) |
| P9 | Клиентской сборки разметки в редакторе нет ВОВСЕ, и гейт ИНВЕРТИРОВАН, а не ослаблен | ✓ VERIFIED | `test_ads_form_uses_property_assignment`: `== 0` обоих имён вместо `>= 3` / `>= 2`; соседнее «разметка не собирается строкой» не тронуто |
| P10 | Ручной сборки запроса в `app/templates/` осталось 5 — экран подключения Telegram | ✓ VERIFIED | `MANUAL_FETCH_PLACES = 5`, `MANUAL_FETCH_CEILING_AT_PHASE_08 = 5`; замер дерева: `connect_tg_user.html` — 5, прочих файлов с `fetch(` нет |
| P11 | Полоса рисуется СЕРВЕРОМ из единственного источника и включается страницей; `#image-inputs` / `#upload-error` исчезли | ✓ VERIFIED | `media_strip.html` — единственный источник, включают три места; оба идентификатора в дереве отсутствуют; три правила редактора зелены |
| P12 | Порог счётчика читается из РАЗМЕТКИ (числа плиток), а не из клиентского массива | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Серверная половина закрыта (`test_counter_threshold_follows_the_presence_of_attachments`, `test_editor_counter_is_server_rendered`); переключение порога на нажатии клавиши — исполняемый JS, суитой не исполняется |
| P13 | Ответ автосохранения приносит полосу внеполосным блоком по ВТОРОМУ идентификатору; цель подмены и внеполосная цель не совпадают; формы в ответе нет | ✓ VERIFIED | `media_strip.html:53` — `hx-swap-oob` под условием `oob`; `#media-strip` (цель подмены) ≠ `#media-tray` (внеполосная цель); `test_no_id_is_both_a_swap_target_and_an_oob_target`, `OOB_BLOCKS = 20`, `test_autosave_response_carries_no_form` — зелены. ⚠️ ровно этот блок и стирает строки отказа (гап 2) |
| P14 | Частичная партия: принятый файл прикреплён, отвергнутый получает СВОЮ строку с нормализованным именем | ✓ VERIFIED (в пределах ОТВЕТА) | `test_partial_batch_keeps_the_accepted_file`, `test_a_rejected_name_is_normalised_before_it_is_shown` зелены. Судьба строки ПОСЛЕ ответа — гап 2 |
| P15 | Потолок берёт первые свободные места; остальным строка про потолок; партию целиком сервер не отвергает | ✓ VERIFIED | `test_ceiling_takes_the_free_slots_and_refuses_the_rest` (приняты `a.png`, `b.png`; `mock_s3.call_count == 4`) |
| P16 | Все три исхода отвечают 200 с фрагментом | ✓ VERIFIED | `test_every_outcome_answers_two_hundred`; срез обработчика: `status_code=(400\|422)` → 0. ⚠️ WR-06: отказ по числу частей уходит JSON-ом 400 мимо этого контракта |
| P17 | Каждый присланный ключ сверяется на принадлежность ДО фрагмента, и сверяет его `own_image_keys` — второго инструмента нет | ✓ VERIFIED | `test_a_foreign_key_is_not_echoed_back` (ключа нет И `call_count == 0`); в срезе обработчика `own_image_keys` один раз, `free` — одна строка из его результата. ⚠️ ФОРМА отказа разрушительна — гап 1 |
| P18 | Первая удачная картинка на `/ads/new` создаёт черновик: заголовок события после подмены + слушатель от тела документа, нового JS ноль | ✓ VERIFIED (контракт) | `HX-Trigger-After-Swap` — ровно одно место записи (`ads.py:936`), `HX_HEADER_WRITES = 4`, `test_a_successful_upload_asks_the_ad_form_to_save` и `test_a_fully_refused_upload_asks_for_nothing` зелены; `form.html:153` несёт `ads-image-attached from:body`; `hx-sync="this:queue last"` и `hx-swap="none"` не тронуты. Браузерная половина (A2) — пункт обхода |
| P19 | `app/routes/uploads.py` снят ЦЕЛИКОМ; `/api/uploads/image` не существует; в `README.md` его нет | ✓ VERIFIED | `test -e app/routes/uploads.py` → 1; `grep -c uploads app/main.py` → 0; `grep -c '/api/uploads/image' README.md` → 0; `compileall` молчит |
| P20 | 1099 строк утверждений ПЕРЕЕХАЛИ, а не исчезли; баланс сведён | ✓ VERIFIED | `tests/test_services/test_image_upload.py` — 53 passed; `tests/test_pages/test_ads_image_upload.py` — 14 passed; собранное число суиты 3427→3428 сходится с записанным балансом (−54, +53, +2) |
| P21 | Решение о поверхности отражено во ВСЕХ ТРЁХ перечнях гейтов | ✓ VERIFIED | Оба множества гейта доступа по 4; `app/pages/ads.py::ads_images_upload` в `ALLOWED_ROUTES`; `MUTATING_ROUTE_COUNT`/`MUTATING_MODULE_COUNT` сдвинуты; 35 passed по двум гейтам |
| P22 | Два изъятия Фазы 9 ПЕРЕАДРЕСОВАНЫ Фазе 15 записью с причиной | ✓ VERIFIED | `grep -c 'НАЗНАЧЕНО ФАЗЕ 12'` → 0; `grep -ci 'фазе 15'` → 2; историческая летопись Фазы 9 на месте |
| P23 | Ни одной подмены по прежнему адресу модуля в суите не осталось | ✓ VERIFIED | `grep -rc 'app.routes.uploads' tests/ \| grep -v ':0$'` → пусто; `app.services.image_upload.upload_file_to_s3` — 23 вхождения в модуле сервиса. ⚠️ IN-01: три ПРОЗАИЧЕСКИЕ ссылки на снятый ТЕСТОВЫЙ модуль остались |

**Score:** 23/27 truths verified (3 present, behavior-unverified; 1 failed)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `app/services/image_upload.py` | sniff/safe_filename/retarget/store_upload, Accepted/Rejected, UPLOAD_FILE_FIELD, MAX_UPLOAD_PARTS, тексты отказа | ✓ VERIFIED | 53 правила сервиса зелены; комментарии перенесены дословно (25/25); порядок «размер выше типа» наблюдаем |
| `app/pages/ads.py::ads_images_upload` | страничный маршрут на `ads_router`, сборщик фрагмента, заголовок события | ⚠️ HOLLOW на одной ветви | Артефакт есть, подключён, данные текут. Ветвь `except HTTPException` (:838-851) отдаёт фрагмент, построенный НЕ из состояния, а из пустоты — авторитетно выглядящая ложь о содержимом полосы |
| `app/templates/ads/includes/media_strip.html` | единственный источник разметки полосы | ✓ VERIFIED | Три включающих места; `data-media` первым атрибутом; условный `hx-swap-oob`; строки отказа не блоком |
| `app/templates/ads/includes/media_upload_form.html` | форма загрузки на макросе, соседом полосы, без кнопки отправки | ✓ VERIFIED | `type="submit"` → 0; `name="images"` → 0; имя поля из глобала |
| `app/templates/ads/includes/autosave_response.html` | внеполосный блок полосы | ⚠️ HOLLOW | Блок есть и работает, но переменная `refusals` жёстко `[]` — блок систематически стирает содержимое, которое сам не производит (гап 2) |
| `app/templates/components/form_wrapper.html` | параметры `encoding` и `include` | ✓ VERIFIED | По одному вхождению каждого; `hx-indicator` остался последним атрибутом |
| `nginx/nginx.conf.template`, `nginx/nginx-http.conf.template` | `client_max_body_size 64M` с формулой | ✓ VERIFIED | По одному объявлению в каждом; формула прозой; HTTP-шаблон получил директиву впервые |
| `tests/test_nginx_body_limit.py` | сверка потолка прокси с `Settings` | ✓ VERIFIED | 4 passed, включая контроль зубов на понижённом значении |
| `tests/test_services/test_image_upload.py` | переехавшие утверждения о сервисе | ✓ VERIFIED | 53 passed |
| `tests/test_pages/test_ads_image_upload.py` | пара транспортов, партия, потолок, чужой ключ, событие | ⚠️ ПРОБЕЛ ПОКРЫТИЯ | 14 passed, но ни одно правило не подаёт СВОЙ И ЧУЖОЙ ключ в одной партии — именно этот случай и стирает законные ключи (гап 1); ни одно не сводит два фрагмента (гап 2) |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `media_upload_form.html` | `ads_images_upload` | `hx-post=/ads/images`, `hx-target=#media-strip`, `hx-encoding` | ✓ WIRED | Замер: маршрут отвечает фрагментом на составной запрос |
| `ads_images_upload` | `store_upload` → `upload_file_to_s3` | вызов сервиса в цикле по частям | ✓ WIRED | `mock_s3.call_count` утверждается в четырёх правилах |
| скрытое поле `name="images" form="ad-form"` | `_save_from_editor` | `form_data.getlist("images")` | ⚠️ WIRED, НО ОДНОНАПРАВЛЕННО ОПАСНО | Связь работает в обе стороны; ПУСТОЙ набор полей воспринимается как «вложений нет», а не как «полоса не знает» — механизм гапа 1 |
| `ads_router` (`Depends(require_access)`) | новый маршрут | пер-роутерная зависимость | ✓ WIRED | Прочитано в `app/pages/__init__.py`, не выведено из перечня |
| `HX-Trigger-After-Swap` ответа загрузки | `hx-trigger="… ads-image-attached from:body"` формы | заголовок → всплытие до тела | ✓ WIRED (контракт) | Имя одно и то же в обоих местах; применение — браузер (пункт обхода) |
| ответ автосохранения | `#media-tray` | `hx-swap-oob="true"` | ✓ WIRED, И ИМЕННО ЭТО ЛОМАЕТ | Внеполосная замена узла ЦЕЛИКОМ стирает строки отказа (гап 2) и может затереть свежий ключ (гап 3) |
| `app/config.py` (`max_images_per_ad` × `max_image_size_mb`) | `client_max_body_size` обоих шаблонов | правило суиты | ✓ WIRED | Расхождение краснит суиту; контроль зубов доказан |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `media_strip.html` (ответ загрузки) | `image_keys` | присланные ключи после `own_image_keys` + ключи принятых файлов | Да на счастливом пути | ✓ FLOWING |
| `media_strip.html` (ветвь отказа сверки) | `image_keys` | **литерал `[]`** — состояние не запрашивается ни у базы, ни у прошедшего подмножества | Нет | ✗ HOLLOW_PROP (зонд: 0 скрытых полей при 1 своём законном ключе в запросе) |
| `media_strip.html` (ответ автосохранения) | `refusals` | **литерал `[]`** (`autosave_response.html:41`) | Нет | ✗ HOLLOW_PROP |
| `media_strip.html` (ответ автосохранения) | `image_keys` | `ad.images` из перечитанной записи | Да, но ОТСТАЁТ от DOM на незаписанный ключ | ⚠️ STATIC относительно летящей загрузки (гап 3) |
| `media_strip.html` (страница редактора) | `image_keys` | контекст редактора из базы | Да | ✓ FLOWING |
| строка отказа | `display_name` | `safe_filename()` в СЕРВИСЕ, до шаблона | Да | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Модули фазы зелены (целевой прогон 10 модулей) | `uv run pytest tests/test_pages/test_ads_image_upload.py tests/test_services/test_image_upload.py tests/test_nginx_body_limit.py tests/test_pages/test_access_gate.py tests/test_pages/test_impersonation_gate.py tests/test_pages/test_ads_editor.py tests/test_templates/test_ads_form_security.py tests/test_templates/test_htmx_inventory.py tests/test_templates/test_htmx_markup_gates.py tests/test_pages/test_htmx_gates.py -q -p no:randomly` | `303 passed` | ✓ PASS |
| Снятый модуль отсутствует, приложение собирается | `test -e app/routes/uploads.py; grep -c uploads app/main.py` | `1` и `0` | ✓ PASS |
| **Зонд А (свой): свой + чужой ключ в ОДНОЙ партии** | временный тест верификатора: POST `/ads/images` с `images=[свой, чужой]` и одной годной частью | `STATUS 200`; `OWN KEY SURVIVED: False`; `HIDDEN FIELD COUNT: 0`; `S3 CALLS: 0`; тело — полоса с одной строкой отказа и плиткой добавления, БЕЗ единого скрытого поля | ✗ FAIL (гап 1) |
| **Зонд Б (свой): 11 СВОИХ законных ключей при потолке 10 — путь без нападающего** | тот же зонд, `images` = 11 корректных ключей владельца | `STATUS 200`; `ANY OWN KEY SURVIVED: False`; `HIDDEN FIELD COUNT: 0` | ✗ FAIL (гап 1, достижимость без нападающего) |
| Сохранение стирает вложения при пустом наборе полей | чтение `app/pages/ads.py:533-588` | `ad.images = image_list`, где `image_list` — только из формы; `own_image_keys([])` проходит | ✗ FAIL (замыкание цепи гапа 1) |
| `request.form()` буферизует поток ДО первой проверки | чтение `starlette/formparsers.py` (`async for chunk in self.stream` в `MultiPartParser.parse`) | Поток разбирается целиком до возврата | ✗ FAIL заявленного инварианта (WR-01) |
| Сокращение JS редактора | `awk '/<script/,/<\/script>/' \| wc -l` до и после | 235 → 125 (минус 110 строк) | ✓ PASS (критерий 1 обещал «~70») |

Полный прогон суиты повторно НЕ запускался: замер оркестратора этого прогона (3427 passed, 1 failed —
`test_the_overview_error_number_matches_the_users_own_dashboard`, предсуществующий дефект часа
прогона, окна 14/27/79/85/93) принят как данный и подтверждён целевым прогоном затронутых модулей.

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| Конвенционных `scripts/*/tests/probe-*.sh` в дереве нет | `find scripts -path '*/tests/probe-*.sh'` | пусто | n/a — фаза probe-проверок не объявляет |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| FETCH-01 | 12-01…12-05 (все пять) | «загрузка изображения объявления идёт htmx-фрагментом вместо `fetch()` + JSON; **успешно загруженные файлы остаются прикреплёнными, даже если часть отвалилась**» | ✗ BLOCKED | Первая половина требования выполнена целиком (R1, P1–P23). ВТОРАЯ половина — дословно та же формулировка, что критерий 2 — не выполнена на пути отказа сверки ключей (зонды А и Б). `.planning/REQUIREMENTS.md:50` и строка трассировки :149 объявляют требование `Complete` **преждевременно**: отметка поставлена по `requirements.ready-ids` (все планы закрыты) прежде вердикта верификации, и правило проекта `test_no_requirement_is_marked_complete_before_its_phase_verification_passed` краснеет справедливо. **Отметку надлежит снять до закрытия гапов.** |

Осиротевших требований нет: `REQUIREMENTS.md` относит к Фазе 12 ровно FETCH-01, и его объявили все
пять планов. `UPLD-01` (проценты загрузки) числится `Deferred` в v2.2 — вне объёма по объявлению
критерия 4.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | `TBD` / `FIXME` / `XXX` в 32 файлах диффа фазы | — | **Ноль вхождений.** Гейт долговых пометок пройден |
| `app/pages/ads.py` | 822, 838-851 | Пустой список как «авторитетное» состояние (`image_keys = []` → фрагмент) | 🛑 Blocker | Отцепляет законные вложения; следующее автосохранение стирает их в базе (гап 1) |
| `app/templates/ads/includes/autosave_response.html` | 41 | Жёсткий литерал вместо данных (`set refusals = []`) в блоке, подменяющем узел ЦЕЛИКОМ | 🛑 Blocker | Систематически стирает строки отказа (гап 2) |
| `app/templates/ads/includes/media_upload_form.html` | 34-40 | Вызов макроса без стратегии наложения при форме-соседе, которая её имеет | ⚠️ Warning | Наложение запросов теряет только что принятый ключ (гап 3) |
| `app/services/image_upload.py` / `app/pages/ads.py` | 297-326 / 816-818, 868-875 | Комментарий-инвариант, который транспорт не держит (WR-01) | ⚠️ Warning | «Ограничиваем то, что ПРИНИМАЕМ» и «оставшиеся части без чтения тел» — на этом транспорте неправда: `request.form()` уже сбуферил всё. Следующий читатель будет опираться на несуществующую защиту |
| `app/pages/ads.py` | 801-803 | Единственная НОВАЯ защита фазы (предел числа частей) не обёрнута (WR-06) | ⚠️ Warning | `MultiPartException` → `HTTPException(400)` → JSON на HTML-поверхности, и на 4xx подмены нет: ровно та причина отказа, которую человек прочесть не может — против D-04 |
| `nginx/*.conf.template` | блок `server` | Потолок 64M поднят для ВСЕХ адресов ради одного (WR-02) | ⚠️ Warning | Любой POST, включая неаутентифицированный, может прогнать через воркер 64 МБ |
| `app/pages/ads.py` | 764-779 | Пишущий в хранилище маршрут без `is_same_origin` (WR-03) | ⚠️ Warning | Межсайтовая форма пишет объекты в префикс жертвы (расход хранилища). Отсутствие ЗАМЕРЕНО в `test_origin_guard_on_destructive_routes.py`, то есть решение, но унаследованное, а не принятое заново на страничной поверхности |
| `app/services/image_upload.py` | 396-400 | Авария хранилища посреди партии = 5xx вместо отказа по файлу (WR-05) | ⚠️ Warning | Уже принятые ключи до DOM не доезжают; объекты остаются сиротами. Ровно то рассуждение, что применено к отказу владения, к аварии не применено |
| `tests/test_nginx_body_limit.py`, `tests/test_pages/test_ads_image_upload.py`, `tests/test_services/test_images.py` | 30, 127, 5 | Ссылка на `tests/test_routes/test_uploads.py`, снятый этой же фазой (IN-01) | ℹ️ Info | Дисциплина «путь заменяется описанием» применена в пяти местах и пропущена в трёх |
| `app/templates/ads/includes/autosave_response.html` | 36-43 | `oob` доезжает до полосы НАСЛЕДОВАНИЕМ переменной, поставленной для другого включения (IN-02) | ℹ️ Info | Перестановка двух включений молча снимет `hx-swap-oob` с полосы — и симптомом будет ровно тот баг, который закрывал план 12-03 |
| `app/pages/ads.py` | 816-818 | `await request.form()` без `async with` / `close()` (IN-03) | ℹ️ Info | Временные файлы освобождаются подсчётом ссылок, а не детерминированно |
| `app/pages/ads.py` | 924-926 | Путь без htmx делает всю работу и выбрасывает ключи (IN-04) | ℹ️ Info | Прямой POST оставляет объекты-сироты; D-09 делает путь недостижимым из интерфейса, но не из сети |
| `app/pages/ads.py` | 855-857 | `free` считается из присланного клиентом списка (IN-05) | ℹ️ Info | Это цифра согласованности интерфейса, а не квота; клиент, не пославший `images`, получает полный потолок на каждом запросе |
| `media_upload_form.html`, `media_strip.html` | 54, 91 | «+ ФАЙЛ» — `<label>` при `hidden`-поле: клавиатурой недостижим, `:focus-visible` в CSS мёртв (IN-06) | ℹ️ Info | Перенесено из доисторической разметки, но оба файла эта фаза переписала |

### Human Verification Required

Девять пунктов, из них три — решения владельца. Полный текст — в `human_verification` frontmatter.
Сокращённо:

1. **Критерий 4** (по объявлению ROADMAP): индикатор «идёт запрос» виден при выборе файла.
2. **Боевой стенд:** переразвернуть nginx, бросить 10 снимков по 4–5 МБ, убедиться в отсутствии 413
   (запись 92 WINDOWS.md; без неё правка шаблона боевой предел не двигает).
3. **Кнопка «×»:** плитка исчезает после круга к серверу, текст не теряется, страница не
   перезагружается.
4. **Порог счётчика** переключается на ближайшем нажатии клавиши.
5. **`/ads/new`:** прикрепить картинку, не набрав ни символа, обновить страницу — картинка на месте
   (прямая проверка допущения A2: всплытие события соседа до тела документа).
6. **Пять файлов на два места:** две плитки, три названные строки отказа — И ПРОВЕРИТЬ, СКОЛЬКО ОНИ
   ЖИВУТ (наблюдение гапа 2).
7. **Решение владельца:** допущение о конкурентности (сироты при обрыве, две партии из двух вкладок).
8. **Решение владельца:** гарда источника на маршруте загрузки — вызвать или записать принятый риск.
9. **Решение владельца:** восемь запретов планов со `verification: none` — подтвердить неавторитетные
   суждения верификатора либо назвать проверку.

### Gaps Summary

Фаза сделана добросовестно, и это видно по коду, а не по сводкам: сервисная половина аккуратна,
гейты переведены ВМЕСТЕ с предметом (утверждение безопасности инвертировано ВВЕРХ, а не ослаблено),
перечни отражают настоящий механизм закрытия, а не подогнаны, комментарии-обоснования перенесены
дословно (проверено построчно), и все инвентарные числа сходятся с деревом. Критерии 1 и 3 закрыты
кодом целиком.

Ломается ровно одно место, и оно — ШОВ, которого не рассматривает ни один документ фазы: **фрагмент
загрузки против фрагмента автосохранения**. Три гапа, один корень — «полоса стала единственным
состоянием, и любой, кто перерисует её из неполной истины, стирает работу человека»:

1. **Ветвь отказа сверки ключей отвечает ПУСТОЙ полосой** (гап 1). Проверено моим собственным зондом
   дважды, включая путь БЕЗ нападающего: одиннадцать СВОИХ законных ключей при потолке десять дают
   ноль скрытых полей. Дальше `_save_from_editor` пишет `ad.images = []`. До фазы негодный ключ
   ГРОМКО блокировал сохранение; теперь попытка загрузки ТИХО отцепляет вложения. Это и есть отказ
   критерия 2 в его собственной формулировке — «успешно загруженные файлы остаются прикреплёнными».
2. **Строка отказа стирается кругом, который этот же ответ и заказывает** (гап 2). D-04 заплатил
   лживым кодом 200 РОВНО за то, чтобы человек прочитал причину, — и покупка не доживает до второго
   взгляда на экран. На самом частом пути смешанной партии.
3. **Наложение запросов не сериализовано** (гап 3): форма объявления имеет очередь, форма загрузки —
   нет, и это разные элементы. Летящее автосохранение перерисовывает полосу из базы, которая нового
   ключа ещё не знает.

Почему суита зелена при всём этом — сказано без снисхождения: каждый из трёх дефектов живёт во
ВЗАИМОДЕЙСТВИИ двух фрагментов, а правил на взаимодействие в суите нет ни одного. Правило
`test_a_foreign_key_is_not_echoed_back` даже ЗАКРЕПЛЯЕТ пустую полосу (`HIDDEN_KEY_FIELD.search(...)
is None`) — верно для своего случая (в запросе только чужой ключ) и слепо к смешанному, который и
разрушителен. Закрывая гапы, это правило придётся дополнить случаем «свой И чужой в одной партии»,
а не переписывать.

Отметку `FETCH-01 = Complete` надлежит СНЯТЬ: вторая половина текста требования — дословно критерий
2 — не выполнена, и красное правило `tests/test_planning/` право по существу, а не только по
процедуре.

Ни один из гапов не адресован поздним фазам вехи: Фаза 13 — QR-мастер Telegram, Фаза 14 —
авторизация, Фаза 15 — сводный обход 47 форм и `fetch( == 0`. Шов «загрузка ↔ автосохранение» не
назван ни одной из них, поэтому `deferred` пуст.

---

_Verified: 2026-09-19T06:22:32Z_
_Verifier: Claude (gsd-verifier)_
