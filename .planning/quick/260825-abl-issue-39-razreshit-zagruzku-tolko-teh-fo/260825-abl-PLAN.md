---
phase: quick-issue-39-image-formats-supported-by-all-messengers
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - app/routes/uploads.py
  - tests/test_routes/test_uploads.py
  - app/templates/ads/form.html
  - tests/test_pages/test_ads_editor.py
autonomous: true
requirements:
  - ISSUE-39
estimate:
  tokens: 40000
  raw_tokens: 40000
  tasks: 3
  confidence: low
must_haves:
  truths:
    - "POST /api/uploads/image with WebP bytes returns 400 and never reaches S3, no matter what Content-Type the client declares."
    - "POST /api/uploads/image with GIF87a or GIF89a bytes returns 400 and never reaches S3."
    - "POST /api/uploads/image with JPEG or PNG bytes still returns 200 and stores the sniffed type, unchanged from today."
    - "The Russian refusal text the user reads names exactly JPEG and PNG, and names neither WebP nor GIF."
    - "The file picker on the ad editor offers only JPEG and PNG, so a WebP is refused before it is uploaded rather than after."
    - "SVG and arbitrary non-image bytes are still refused — the CR-02 content-sniffing guarantee is narrowed, never loosened."
    - "The refusal string in the editor's JavaScript is the same string as the server constant, pinned by a test rather than by discipline."
  artifacts:
    - path: "app/routes/uploads.py"
      provides: "Signature table and refusal message narrowed to the two formats all three messengers can send as ordinary images"
      contains: "UNSUPPORTED_IMAGE_MESSAGE"
    - path: "tests/test_routes/test_uploads.py"
      provides: "WebP and GIF byte builders now proving REFUSAL; JPEG/PNG acceptance unchanged"
      contains: "make_webp_bytes"
    - path: "app/templates/ads/form.html"
      provides: "File picker restricted to JPEG/PNG and client-side refusal text matching the server"
      contains: "accept=\"image/jpeg,image/png\""
    - path: "tests/test_pages/test_ads_editor.py"
      provides: "Render test pinning the picker's accept attribute and the JS refusal string to the server constant"
      contains: "UNSUPPORTED_IMAGE_MESSAGE"
  key_links:
    - from: "app/routes/uploads.py::sniff_image"
      to: "app/routes/uploads.py::upload_image refusal path (400 + UNSUPPORTED_IMAGE_MESSAGE)"
    - from: "app/routes/uploads.py::UNSUPPORTED_IMAGE_MESSAGE"
      to: "app/templates/ads/form.html::UPLOAD_TYPE_ERROR (byte-identical copy, enforced by render test)"
    - from: "app/templates/ads/form.html file-input accept attribute"
      to: "app/routes/uploads.py::sniff_image (hint vs. authority — the picker narrows, the server decides)"
---

<objective>
GitHub issue #39 «формат загружаемых изображений»: разрешить к загрузке только те
форматы изображений, которые все три мессенджера (Telegram, WhatsApp, MAX) умеют
отправить как ОБЫЧНУЮ картинку.

Сегодня `/api/uploads/image` принимает четыре формата — JPEG, PNG, GIF и WebP, — но
отправку переживают только два. WebP проходит загрузку и ломается на отправке в
Telegram; GIF не является отправляемой картинкой в WhatsApp. Пользователь узнаёт об
этом не на загрузке, а на провалившейся рассылке — то есть тогда, когда починить уже
поздно.

Purpose: сдвинуть отказ с момента ОТПРАВКИ на момент ЗАГРУЗКИ. Ошибка, пойманная на
входе, стоит пользователю одного клика; та же ошибка, пойманная на рассылке, стоит
несостоявшейся рассылки.

Output: список принимаемых форматов сужен до JPEG и PNG на сервере (авторитет), в
файловом диалоге редактора (подсказка) и в тексте отказа, который пользователь
читает.
</objective>

<execution_context>
@/source/broadcaster/.claude/gsd-core/workflows/execute-plan.md
@/source/broadcaster/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@/source/broadcaster/CLAUDE.md
@/source/broadcaster/.claude/CLAUDE.md
@/source/broadcaster/.planning/STATE.md

@/source/broadcaster/app/routes/uploads.py
@/source/broadcaster/tests/test_routes/test_uploads.py
@/source/broadcaster/app/templates/ads/form.html
@/source/broadcaster/tests/test_pages/test_ads_editor.py
</context>

<locked_decision>
## Набор форматов — решение принято, не пересматривать

**Разрешено ровно два формата: JPEG и PNG.** Анализ путей отправки уже выполнен;
задача исполнителя — реализовать вывод и ЗАФИКСИРОВАТЬ его обоснование в комментариях,
а не повторять анализ.

Доказательная база (её и надо изложить в комментариях, плотной русской прозой в стиле
файла — этот проект объясняет в комментариях ПОЧЕМУ ограничение существует, а не что
делает строка):

1. **Telegram** — `app/messengers/telegram_user.py:200-221`. Картинка скачивается в
   `io.BytesIO`, `buf.name` берётся из имени файла в URL «чтобы сохранить расширение»,
   дальше `client.send_file(..., force_document=False)`. Telethon выводит тип медиа из
   этого расширения: на `.webp` он собирает документ-СТИКЕР, а стикер Telegram не
   принимает ни в альбоме, ни с подписью. Это и есть поломка из issue #39.
2. **WhatsApp** — `wa_worker/index.js:453-477`. Baileys вызывается как
   `{ image: buffer, mimetype }`, где mimetype — Content-Type сохранённого объекта.
   `image/webp` для WhatsApp — mimetype СТИКЕРА, поэтому WebP, посланный полем `image`,
   не является обычным сообщением-картинкой. Статический GIF тоже не поддерживаемая
   WhatsApp картинка: анимацию там ожидают видеофайлом.
3. **MAX** — `max_worker/main.py:567-600`. Картинка кладётся во временный файл и
   оборачивается в `Photo(path=...)` из pymax — растровый путь загрузки фотографии,
   рассчитанный на JPEG/PNG.

**GIF исключается вместе с WebP.** Он не годная статическая картинка для WhatsApp и не
фотография для Telegram (становится анимацией или документом, что дополнительно ломает
смешанный альбом). Отправляемы всеми тремя мессенджерами как обычная картинка ровно
JPEG и PNG.
</locked_decision>

<non_goals>
Границы, за которые не выходить. Нарушение любой из них — переделка, а не улучшение.

- **Не конвертировать и не перекодировать изображения.** Никакого Pillow, никакого
  повторного сжатия. В `app/routes/uploads.py` стоит намеренный комментарий (строки
  32-36), объясняющий, что `Image.open()` на недоверенном файле добавил бы вектор
  decompression bomb ровно этому эндпоинту. Это решение сохраняется дословно.
- **Не трогать уже сохранённые в S3 объекты** и не менять отрисовку существующих
  объявлений. Никаких миграций ключей, никаких пакетных перезаписей.
- **Не трогать пути отправки** — ни `app/messengers/`, ни `wa_worker/`, ни
  `max_worker/`. Строки `max_worker/main.py:579-580` (`elif "webp" in ct`) остаются как
  есть: это код отправки, и он вне задачи.
- **Не заводить новых зависимостей.** Проверка сигнатур остаётся ручной по той же
  причине, что и была: `python-magic` тянет системный `libmagic` в образ, `imghdr`
  удалён из stdlib в 3.13.
</non_goals>

<tasks>

<task type="tracer" tdd="true">
  <name>Task 1: Сузить серверную проверку до JPEG и PNG — сквозной путь от байтов до отказа</name>
  <files>app/routes/uploads.py, tests/test_routes/test_uploads.py</files>
  <reversibility rating="reversible">Сужение списка сигнатур откатывается возвратом двух записей таблицы и одной ветки; никакие данные не преобразуются, ни один сохранённый объект не переписывается.</reversibility>
  <read_first>
`app/routes/uploads.py` целиком (169 строк) — обязательно ДО правки: файл держит
плотные русские комментарии, объясняющие CR-02 (тип по содержимому, не по заголовку) и
WR-02 (порционное чтение). Ни один из них не удалять и не ослаблять — задача сужает
список форматов, а не пересматривает безопасность эндпоинта.

`tests/test_routes/test_uploads.py` — точки правки:
- L81 `make_gif_bytes(version)`, L86 `make_webp_bytes()` — построители байтов; ОСТАЮТСЯ,
  меняется их назначение: теперь ими доказывается отказ.
- L251-263 — параметризация `test_sniff_image_recognises_supported_formats` (def L265).
- L268-280 — параметризация `test_sniff_image_rejects_non_images` (def L282).
- L286-296 — параметризация `test_upload_accepts_each_supported_format` (def L298).
- L327 `test_upload_rejects_svg_declared_as_png` утверждает `"JPEG" in detail` — после
  правки утверждение остаётся истинным, трогать тест не нужно.
  </read_first>
  <behavior>
Тесты пишутся ПЕРВЫМИ и сначала падают. Ожидаемое поведение:

- `sniff_image(make_webp_bytes())` возвращает `None`.
- `sniff_image(make_gif_bytes(b"87a"))` и `sniff_image(make_gif_bytes(b"89a"))`
  возвращают `None`.
- `sniff_image(make_png_bytes()) == "image/png"`, `sniff_image(make_jpeg_bytes()) == "image/jpeg"` — без изменений.
- `sniff_image(SVG_BYTES) is None` и остальные случаи «не изображение» — без изменений.
- `POST /api/uploads/image` с байтами WebP под заголовком `application/octet-stream`
  отвечает 400, `upload_file_to_s3` не вызывается, `detail` равен
  `UNSUPPORTED_IMAGE_MESSAGE`.
- То же для GIF обеих версий.
- `POST` с байтами PNG и JPEG по-прежнему отвечает 200 и кладёт в хранилище
  распознанный тип.
- Текст отказа содержит подстроки `JPEG` и `PNG` и НЕ содержит названий двух
  исключённых форматов; таблица сигнатур закрыта на двух записях, а множество типов,
  которые она способна вернуть, равно `{"image/jpeg", "image/png"}`.
  </behavior>
  <action>
Правка `app/routes/uploads.py`:

1. Из `_IMAGE_SIGNATURES` (L37-42) убрать обе записи GIF, оставив JPEG (`\xff\xd8\xff`)
   и PNG (`\x89PNG\r\n\x1a\n`).
2. Удалить `_RIFF_MAGIC` и `_WEBP_MAGIC` (L46-47) вместе с комментарием L44-45 про
   смещение метки формата, и удалить ветку `if content[:4] == _RIFF_MAGIC ...` в
   `sniff_image` (L69-70). Констант без потребителей не оставлять.
3. Заменить `UNSUPPORTED_IMAGE_MESSAGE` (L49-52) на строку, названную в
   `<message_text>` ниже, ДОСЛОВНО — она же пойдёт в шаблон в задаче 2, и равенство
   двух копий проверяется тестом.
4. Обновить docstring `sniff_image` (L56-64): распознаются два формата, список закрыт,
   абзац про SVG и вектор CR-02 сохранить дословно — он объясняет другое ограничение и
   остаётся в силе.
5. Над `_IMAGE_SIGNATURES` поставить новый комментарный блок в стиле файла (плотная
   русская проза, объясняющая ПОЧЕМУ), излагающий все три пункта доказательной базы из
   `<locked_decision>` со ссылками на файлы и строки, и явно фиксирующий, что список
   ограничен не разбором форматов, а способностью ТРЁХ мессенджеров отправить файл
   обычной картинкой: отказ здесь дешевле провалившейся рассылки. Прежний комментарий
   про ручную проверку без библиотеки (L26-36) сохранить.

Правка `tests/test_routes/test_uploads.py`:

6. Из параметризаций L251-263 и L286-296 убрать случаи GIF (обе версии) и WebP; PNG и
   JPEG остаются. Поправить docstring `test_upload_accepts_each_supported_format`
   (L301): формата теперь два, а не четыре.
7. Завести НОВЫЙ параметризованный тест — например
   `test_sniff_image_rejects_formats_no_messenger_can_send`, — прогоняющий
   `make_gif_bytes(b"87a")`, `make_gif_bytes(b"89a")` и `make_webp_bytes()` через
   `sniff_image` и требующий `None`. Отдельный тест, а не дописывание в
   `test_sniff_image_rejects_non_images`, намеренно: тот отказывает НЕ-изображениям
   (вектор CR-02), этот — настоящим изображениям, которые не переживают отправку
   (issue #39). Смысл отказа разный, и слив их в одну параметризацию стёр бы различие.
   Причину зафиксировать в docstring нового теста.
8. Завести HTTP-тест отказа: WebP и GIF, посланные на `/api/uploads/image` под
   заведомо неверным заголовком типа, дают 400, `detail == UNSUPPORTED_IMAGE_MESSAGE`,
   и `upload_file_to_s3` не вызывается. Именно `assert_not_called` — код 400 сам по
   себе возвращается и по превышению размера.
9. Завести тест синхронности: множество типов из `_IMAGE_SIGNATURES` равно
   `{"image/jpeg", "image/png"}`, и `UNSUPPORTED_IMAGE_MESSAGE` называет оба, не
   называя ни одного исключённого. Он ловит случай, когда формат вернули в таблицу, а
   текст отказа обновить забыли.
10. Поправить два устаревших комментария в параметризации L268-280: пояснение к
    `b"GIF88a"` («похоже на GIF, но версия не та») и к `RIFF…WAVE` («RIFF, но не WebP»)
    опираются на различение версий и меток формата, которого больше нет — оба формата
    отвергаются целиком. Переписать пояснения так, чтобы они объясняли ФАКТИЧЕСКУЮ
    причину отказа, а не исчезнувшую.
11. Обновить docstring построителей на L81 и L86: они больше не «поддерживаемые
    форматы», а вход для доказательства отказа.
  </action>
  <verify>
    <automated>uv run pytest tests/test_routes/test_uploads.py -v</automated>
  </verify>
  <done>
Модуль `tests/test_routes/test_uploads.py` проходит целиком. WebP и GIF обеих версий
получают 400 и не доходят до хранилища; JPEG и PNG принимаются как раньше; SVG и
произвольные байты по-прежнему отвергнуты. Констант и веток без потребителей в
`app/routes/uploads.py` не осталось.
  </done>
</task>

<task type="auto">
  <name>Task 2: Сузить файловый диалог и текст отказа в редакторе объявления</name>
  <files>app/templates/ads/form.html, tests/test_pages/test_ads_editor.py</files>
  <read_first>
`app/templates/ads/form.html` — две точки правки, обе обязательны:
- L130 `<input class="field__input" type="file" id="file-input" accept="image/*" multiple hidden>`
- L269 `const UPLOAD_TYPE_ERROR = '…';` — ВТОРАЯ копия текста отказа. Это та строка,
  которую пользователь видит на самом деле: `uploadFile()` (L375) показывает
  `UPLOAD_TYPE_ERROR` на ЛЮБОМ ответе 400 и никогда не читает `detail` из ответа
  сервера. Правка одного лишь `app/routes/uploads.py` оставила бы на экране прежний
  список из четырёх форматов.

`tests/test_pages/test_ads_editor.py` — файл уже рендерит `/ads/new` через фикстуру
`authed_client` (`test_ads_new_renders`, L157) и держит помощник `_attr_value(html,
anchor, attr)` (L90), достающий значение атрибута элемента, опознанного по подстроке.
Новый тест строится на них; парсер HTML ради одного атрибута не заводить.
  </read_first>
  <action>
1. L130: заменить значение `accept` на `image/jpeg,image/png`. Значение MIME-типами, а
   не расширениями: `image/jpeg` покрывает `.jpg`, `.jpeg` и `.jfif` одним пунктом, и
   диалог не расходится с тем, что распознаёт сервер.
2. L269: заменить текст на строку из `<message_text>` — ДОСЛОВНО ту же, что в
   `app/routes/uploads.py`. Совпадение проверяется тестом из пункта 4, поэтому расхождение
   в одном символе уронит суиту, а не тихо разъедется.
3. Рядом с полем ввода поставить Jinja-комментарий в стиле файла (`{# … #}`, плотная
   русская проза), фиксирующий две вещи: (а) `accept` — ТОЛЬКО подсказка диалогу,
   пользователь обходит её выбором «все файлы» и перетаскиванием, поэтому авторитет
   остаётся за серверным распознаванием по содержимому, а сужение диалога лишь
   переносит отказ на более ранний и более дешёвый момент; (б) список сужен не
   разбором форматов, а тем, что отправить обычной картинкой во все три мессенджера
   можно ровно JPEG и PNG (сослаться на комментарий в `app/routes/uploads.py`, где
   лежит разбор). Отдельным предложением объяснить, почему текст отказа существует в
   двух копиях: обработчик показывает свою константу на любом 400 и не читает `detail`,
   а синхронность копий держит render-тест.
4. В `tests/test_pages/test_ads_editor.py` добавить render-тест `/ads/new`, который:
   импортирует `UNSUPPORTED_IMAGE_MESSAGE` из `app.routes.uploads`; утверждает
   `_attr_value(html, 'id="file-input"', "accept") == "image/jpeg,image/png"`; и
   утверждает, что серверная константа целиком присутствует в отрендеренной странице —
   это и есть механическая привязка второй копии к первой. В docstring объяснить,
   почему утверждение идёт именно на импортированную константу, а не на литерал: тест
   на литерале зелен при разъехавшихся копиях и потому ничего не измеряет.
  </action>
  <verify>
    <automated>uv run pytest tests/test_pages/test_ads_editor.py -v</automated>
  </verify>
  <done>
`GET /ads/new` отдаёт страницу, где файловый диалог ограничен `image/jpeg,image/png`, а
текст отказа в обработчике загрузки байт в байт совпадает с
`app.routes.uploads.UNSUPPORTED_IMAGE_MESSAGE`. Модуль `test_ads_editor.py` проходит
целиком.
  </done>
</task>

<task type="auto">
  <name>Task 3: Полная суита, обновление графа и фиксация остаточного риска</name>
  <files>—</files>
  <action>
1. Прогнать всю суиту: `just test`. Правка задевает общий эндпоинт загрузки, поэтому
   зелёного модуля мало — интерес представляют тесты, которые могли опираться на приём
   четырёх форматов косвенно (`tests/test_pages/test_ads_image_ownership.py`,
   `tests/test_pages/test_attachment_history_integrity.py`,
   `tests/test_pages/test_responsive_markup.py`). Любое падение чинить по существу, а
   не ослаблением утверждения.
2. Выполнить `graphify update .` — правило проекта из `CLAUDE.md`: после изменения кода
   граф приводится в актуальное состояние (только AST, без обращений к API).
3. В SUMMARY отдельным разделом зафиксировать ОСТАТОЧНЫЙ РИСК, который эта задача
   намеренно не закрывает: объявления, созданные ДО этой правки, могут по-прежнему
   ссылаться на сохранённые в хранилище объекты WebP и GIF. Их отправка в Telegram
   продолжит падать ровно так же, как в issue #39, потому что ни один сохранённый
   объект не переписывается и ни одно существующее объявление не чинится. Это граница
   задачи, а не недосмотр; починка потребовала бы отдельного решения (перекодирование
   либо выборочная чистка ссылок) и отдельной задачи. Указать, что обнаружить такие
   объявления можно перечислением ключей вложений с типом объекта вне JPEG/PNG.
  </action>
  <verify>
    <automated>uv run pytest tests/ -q</automated>
  </verify>
  <done>
Вся суита зелёная, `graphify-out/` обновлён, остаточный риск по уже сохранённым
вложениям записан в SUMMARY отдельным разделом.
  </done>
</task>

</tasks>

<message_text>
Текст отказа — ОДНА строка, дословно одинаковая в `app/routes/uploads.py`
(`UNSUPPORTED_IMAGE_MESSAGE`) и в `app/templates/ads/form.html` (`UPLOAD_TYPE_ERROR`):

Не удалось загрузить: подойдут только изображения JPEG или PNG — другие форматы принимают не все мессенджеры. Выберите другой файл.

Придаточное про мессенджеры не украшение: пользователь, чей WebP отвергнут, видит
заведомо корректное изображение и без объяснения читает отказ как поломку сервиса.
Строка называет ровно те форматы, которые действительно принимаются, и остаётся
русской — как все пользовательские строки этого проекта.

В Python константа собирается конкатенацией двух литералов (как сейчас), в JavaScript —
одинарными кавычками; апострофов и двойных кавычек в тексте нет, экранирование не
требуется. Значение после сборки должно совпадать байт в байт.
</message_text>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| браузер → `POST /api/uploads/image` | недоверенное тело запроса, имя файла и заголовок типа, все три подконтрольны отправителю |
| `upload_image` → S3 | распознанный тип уходит `Content-Type`, с которым объект потом отдаётся браузеру |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-Q39-01 | Spoofing | `app/routes/uploads.py::sniff_image` | high | mitigate | Тип по-прежнему определяется по первым байтам, заголовок клиента не используется нигде. Задача СУЖАЕТ таблицу сигнатур; ни одна ветка, ослабляющая проверку, не добавляется. Утверждается тестами на SVG и произвольные байты, которые остаются в суите без правок. |
| T-Q39-02 | Tampering | `app/templates/ads/form.html` атрибут `accept` | low | accept | `accept` обходится выбором «все файлы» и перетаскиванием — это подсказка диалогу, а не проверка. Принято осознанно: авторитетом остаётся серверное распознавание, атрибут лишь удешевляет типовой отказ. Зафиксировано комментарием у поля ввода. |
| T-Q39-03 | Denial of Service | `app/routes/uploads.py::upload_image` | medium | mitigate | Порционное чтение с проверкой предела на каждой порции (WR-02) не трогается: правка живёт ниже по обработчику, в распознавании типа. Тесты объёма чтения остаются в суите без изменений. |

Новых зависимостей задача не вводит — установок пакетов нет, аудит легитимности пакетов
не требуется.
</threat_model>

<verification>
1. `uv run pytest tests/test_routes/test_uploads.py -v` — зелёный.
2. `uv run pytest tests/test_pages/test_ads_editor.py -v` — зелёный.
3. `just test` — вся суита зелёная.
4. Ручная сверка (по коду, без запуска): в `app/routes/uploads.py` не осталось
   определений или веток, чьим единственным назначением было распознавание
   исключённых форматов.
</verification>

<success_criteria>
- Загрузка WebP и GIF (обеих версий) отклоняется кодом 400 независимо от присланного
  заголовка типа и до обращения к хранилищу.
- Загрузка JPEG и PNG работает ровно как прежде, включая запись распознанного типа в
  `Content-Type` объекта.
- Русский текст отказа — один и тот же на сервере и в редакторе, называет JPEG и PNG и
  не называет исключённых форматов.
- Файловый диалог редактора предлагает только JPEG и PNG.
- Гарантии CR-02 (тип по содержимому) и WR-02 (предел на принимаемое) не ослаблены.
- Ни один сохранённый объект и ни одно существующее объявление не изменены; остаточный
  риск по ним записан в SUMMARY.
</success_criteria>

<output>
Create `/source/broadcaster/.planning/quick/260825-abl-issue-39-razreshit-zagruzku-tolko-teh-fo/260825-abl-SUMMARY.md` when done
</output>
