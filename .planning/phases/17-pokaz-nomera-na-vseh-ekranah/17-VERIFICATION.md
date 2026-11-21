---
phase: 17-pokaz-nomera-na-vseh-ekranah
verified: 2026-11-20T22:30:00Z
status: passed
score: 5/6 must-haves verified
covered_files:
  - .planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-01-PLAN.md
  - .planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-01-SUMMARY.md
  - .planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-02-PLAN.md
  - .planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-02-SUMMARY.md
  - .planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-03-PLAN.md
  - .planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-03-SUMMARY.md
  - .planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-04-PLAN.md
  - .planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-04-SUMMARY.md
  - .planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-05-PLAN.md
  - .planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-05-SUMMARY.md
  - .planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-06-PLAN.md
  - .planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-06-SUMMARY.md
  - .planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-07-PLAN.md
  - .planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-07-SUMMARY.md
  - .planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-08-PLAN.md
  - .planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-08-SUMMARY.md
  - .planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-09-PLAN.md
  - .planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-09-SUMMARY.md
  - app/application/accounts/dto.py
  - app/application/accounts/labels.py
  - app/application/accounts/use_cases.py
  - app/pages/account_groups.py
  - app/pages/accounts.py
  - app/pages/admin.py
  - app/pages/common.py
  - app/pages/history.py
  - app/services/account_label.py
  - app/static/css/app.css
  - app/templates/account_groups/list.html
  - app/templates/accounts/list.html
  - app/templates/accounts/partial_cards.html
  - app/templates/accounts/partials/sync_status_card.html
  - app/templates/admin/history_partial_cards.html
  - app/templates/admin/includes/queue_row.html
  - app/templates/admin/includes/worker_row.html
  - app/templates/admin/queue.html
  - app/templates/admin/user_detail.html
  - app/templates/admin/user_history.html
  - app/templates/ads/includes/sched_card.html
  - app/templates/components/account_label.html
  - app/templates/history/includes/history_card.html
  - app/templates/history/list.html
  - tests/account_label_support.py
  - tests/test_application/test_account_label_rows.py
  - tests/test_pages/test_account_label_accounts.py
  - tests/test_pages/test_account_label_admin.py
  - tests/test_pages/test_account_label_admin_history.py
  - tests/test_pages/test_account_label_groups.py
  - tests/test_pages/test_account_label_history.py
  - tests/test_pages/test_account_label_sweep.py
  - tests/test_pages/test_admin_panel.py
  - tests/test_pages/test_editor_schedules.py
  - tests/test_pages/test_history_export.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_services/test_account_label.py
  - tests/test_templates/test_account_label_gate.py
covered_digest: "v4:sha256:aac24f0dc902914c124b3d8ccd8fc146e0c0f3b4e8c2b6a0ddefae81312f20f4"
behavior_unverified: 1
behavior_unverified_items:
  - truth: "Раскладка с номером не ломается на 320–375 px (критерий 5, вторая половина)"
    test: "Открыть экраны из брифа D-21 (17-09-SUMMARY.md, раздел «Ширины 320 и 375 px») на 320 и 375 px с засеянными образцами; смотреть чип расписания, шапку групп аккаунта, карточки аккаунта и истории, строки воркеров и очереди, наихудшую длину «MAX +888 01234567 #123456»"
    expected: "Нет горизонтального скролла; у двойника на чипе и в <h2> усекаются канал и номер, а `#id` остаётся; переносящиеся контейнеры переносят подпись, действия не выталкиваются"
    why_human: "В репозитории нет браузера: суита читает текст CSS (правила `.chip__label > .acct-label`, `.acct-head__name > .acct-label`, `.acct-label__id { flex: none }` присутствуют), но ширины не меряет; чтение CSS ширину не доказывает"
gaps: []
human_verification:
  - test: "Обход D-21 на 320 и 375 px (стенд — боевая база под сессией владельца, засев пяти образцов, чистка после обхода обязательна)"
    expected: "См. раздел «Ширины 320 и 375 px» брифа в 17-09-SUMMARY.md: вид `#id` двойника на чипе и в <h2>; читаемость номера в <h2> (класс `mono` --fs-xs рядом с --fs-2xl — решение владельца, CSS-правило не добавлялось); перенос в карточках и строках админки; подсказка `title=` на чипе; модалка удаления; <option> фильтра; три элемента подряд в строке воркера и очереди; наихудшая длина"
    why_human: "Визуальная раскладка и усечение текста на узком экране машинно здесь не проверяются; отметки, `result` и замеры ставит человек (голое «pass» не отметка)"
  - test: "Открытый курсор на PostgreSQL в CSV-экспорте (17-06 D4): выгрузить историю на боевом драйвере asyncpg с несколькими аккаунтами и записью без аккаунта"
    expected: "Файл целиком, колонка «Номер» заполнена по карте, прочитанной ДО `db.stream`; ошибки «another operation is in progress» нет"
    why_human: "Тесты идут на aiosqlite; поведение серверного курсора asyncpg без боевой базы не воспроизводится (карта номеров читается одним `load_account_rows` до потока — `app/pages/history.py:796`, поток открывается на :857)"
  - test: "19 прохибиций судейского уровня в `must_haves.prohibitions` девяти планов помечены `flagged-unverified`"
    expected: "Человек подтверждает или отклоняет неавторитетный вердикт верификатора (ниже, раздел «Прохибиции»): нарушений при выборочной проверке кодом не найдено"
    why_human: "Judgment-tier прохибиции — мягкий шлюз (ADR-550 D4): вердикт LLM не авторитетен и не может быть тихо зелёным"
---

# Фаза 17: Показ номера на всех экранах — отчёт верификации

**Цель фазы:** пользователь узнаёт свой аккаунт по номеру на каждом экране, где раньше стоял `#id`, а администратор видит и номер, и `#id`
**Проверено:** 2026-11-20T22:30:00Z
**Статус:** human_needed
**Повторная верификация:** нет — первичная

Стартовая гипотеза — «задачи выполнены, цель не достигнута». Опровергнута кодом: каждый экран из критериев проверен по шаблону, обработчику и отрисованной разметке; расхождений между сводками и деревом не найдено. Остались только решения человека о раскладке на узком экране и поведении курсора на боевом драйвере.

## Достижение цели

### Наблюдаемые истины (контракт роадмапа + решения D-01…D-21)

| # | Истина | Статус | Доказательство |
|---|--------|--------|----------------|
| 1 | SC1. Номер `+7 999 123-45-67` вместо `#id` на каждом месте пользователя: карточки аккаунтов (страница, порция, опрос), шапка/`<title>` групп аккаунта, чипы расписаний, карточка и фильтр истории, модалка удаления | ✓ VERIFIED | Собственная отрисовка макроса и `sched_card` под моим запуском: чипы дают `data-account-label="3"` → «Telegram +7 999 123-45-67», `title=` у каждого чипа свой, сводка панели «WhatsApp Номер неизвестен #2 · 1 групп · …». Шаблоны зовут один помощник: `accounts/list.html:89,122,161,200`, `partial_cards.html:47,74,108,146`, `sync_status_card.html:64`, `account_groups/list.html:17,27,55`, `sched_card.html:78,226,230`, `history_card.html:212-214`, `history/list.html:52`. Прицельный прогон 13 файлов: 1396 passed |
| 2 | SC2. «Номер неизвестен» приглушённо (`mono--muted`) на всех местах, включая фрагменты опроса и подгрузки | ✓ VERIFIED | `shown_phone(None / "" / "  ")` → `None` → «Номер неизвестен»; макрос ставит `mono--muted` при `phone_text is none`. Опрос: `SyncStatusView.phone` заполнен во всех четырёх ветках `get_sync_status_view` (`use_cases.py`), обработчик строит `label_of(AccountRow(...), rows)` (`accounts.py:1044-1051`); подгрузка — `build_labels(load_account_rows)` (`accounts.py:167,213`). Тесты `test_the_poll_fragment_reads_as_unknown_in_every_status`, `test_a_card_without_a_number_reads_as_unknown_in_every_status_branch` зелёные |
| 3 | SC3. `#id` — только у двойников (совпала готовая подпись у аккаунтов одного мессенджера одного пользователя); у уникальной подписи его нет | ✓ VERIFIED | Мой прогон `build_labels`: два WA без номера → twin True у обоих; TG `+79991234567` и TG `+7 999 123-45-67` → один ключ, twin True; MAX с тем же номером → twin False (тип входит в ключ). Двойник считается по ВСЕМ аккаунтам пользователя по `user_id` (`labels.py`, `account_groups.py:232`, `history.py:673,1192`, `admin.py:1454,1554`), не по порции. Подпись «`#id`» в `plain` — только при `twin` |
| 4 | SC4. Админка («Воркеры», «Очередь», карточка пользователя, история пользователя) — номер и отдельный `#id` всегда; CSV с колонкой «Номер» рядом с «Аккаунт», с прежним обезвреживанием формул | ✓ VERIFIED | `worker_row.html:73-89` (канал, номер, отдельный `account_id_mark`; ссылка на логи сохранена), `queue_row.html:73-76`, `queue.html:87` («Аккаунт #id · подпись»), `user_detail.html:121`, `user_history.html:28` (`plain_with_id`), `history_card.html:213-214` (`audience == 'admin'`). Карта админской порции — по `user_id` из адреса, не по администратору (`admin.py:1448-1454,1554`). CSV: `EXPORT_HEADER` индексы «Аккаунт»=2, «Номер»=3 (`history.py:206-216`); мой прогон `export_phone_cell`: `+79991234567`→`7 999 123-45-67`, `None`/`""`/`"  "`→пусто, `+=cmd`→`'=cmd`, `++=1`→`'+=1`, `-5`→`'-5`, неразбираемое `garbage`→как есть. Запись без группы — пустые «Аккаунт» и «Номер» (`history.py:364-365`). Тесты админки и экспорта зелёные |
| 5a | SC5 (машинная половина). Подпись собирается одним помощником; греп-гейт краснеет на сборку `'#' ~ account.id` вне него; тесты находят подпись по адресу `data-account-label`, шаблон, пропущенный при замене, роняет суиту | ✓ VERIFIED | Греп всего `app/` на `'#'`, `"#"`, `#{`, `#{{`: остались только `account_id_mark` (`account_label.html:25`), `id_mark` (`account_label.py:75`) и две законные сборки `#` у `group_external_id` (`detail.html:54`, `history_card.html:216`). `test_account_label_gate.py`: подложенные строки (`test_control_a_planted_concatenation_is_named`, `…_python_hash_…`, `…_hash_lookalike_…`), реестр с объявленным числом и привязкой к субъекту, нижняя граница вселенной — все зелёные. Правила `test_editor_schedules`, `test_responsive_markup`, `test_admin_panel` переписаны на адрес (`id_mark_texts(html)[str(account.id)]`); `"#N" in html` по аккаунту в них не осталось. `test_account_label_sweep.py` — 10 путей пользователя и 6 путей админки, контрольные подложенные идентификаторы на синтетической и настоящей странице |
| 5b | SC5 (раскладочная половина). Раскладка с номером не ломается на 320–375 px | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | CSS-контракт на месте: `app.css` — `.chip__label > .acct-label`, `.acct-head__name > .acct-label` — inline-flex, канал и номер усекаются многоточием, `.acct-label__id { flex: none }`, фиксированных ширин нет. Ширину суита не меряет (браузера нет); см. human_verification |

**Счёт:** 5/6 истин проверены, 1 (раскладка 320–375 px) присутствует, но поведение не доказано.

### Обязательные артефакты

| Артефакт | Ожидается | Статус | Детали |
|----------|-----------|--------|--------|
| `app/services/account_label.py` | Правило подписи: `build_labels`, `label_of`, `AccountLabel.plain` / `plain_with_id`, `id_mark` | ✓ VERIFIED | Существенный, чистый, без БД и Jinja; слова канала — только `MESSENGER_LABELS`; разметки не отдаёт |
| `app/templates/components/account_label.html` | Макросы `account_label`, `account_id_mark`, адрес `data-account-label` | ✓ VERIFIED | Только `<span>`, автоэкранирование (мой прогон: `<b>x</b>` экранирован и в тексте, и в `title=`) |
| `app/application/accounts/labels.py` | `load_account_rows` — три колонки, один запрос по пользователю | ✓ VERIFIED | Фильтр `MessengerAccount.user_id == user_id`; зовётся в 5 обработчиках |
| `app/pages/common.py` | Глобалы `phone_labels`, `phone_label` | ✓ VERIFIED | Тонкие обёртки без сессии; используются в `sched_card`, админских шаблонах |
| `app/application/accounts/dto.py` | `SyncStatusView.phone` | ✓ VERIFIED | Заполняется во всех четырёх ветках |
| `app/pages/history.py` | `history_account_label`, `EXPORT_HEADER` + «Номер», `export_phone_cell`, карта до потока | ✓ VERIFIED | См. WR-02 о недостижимой ветке (не блокер) |
| `tests/test_templates/test_account_label_gate.py` | Греп-гейт с реестром и подложенными строками | ✓ VERIFIED | Не вакуумный: контрольные тесты и нижняя граница |
| `tests/test_pages/test_account_label_sweep.py` | Проход по отрисованным экранам | ✓ VERIFIED | Контроли на синтетике и на реальной странице |
| `app/static/css/app.css` | Контракт длинной подписи | ✓ VERIFIED (присутствие) | Раскладка — у человека |

### Проверка ключевых связей

| Откуда | Куда | Через | Статус | Детали |
|--------|------|-------|--------|--------|
| обработчики страниц | `build_labels` / `label_of` | `load_account_rows(db, user.id)` | WIRED | 5 обработчиков: accounts, sync-status, account_groups, history (страница, порция), admin (страница, порция) |
| шаблоны | макрос подписи | `{% from "components/account_label.html" import … %}` | WIRED | 12 шаблонов, все места из D-01 и D-04 |
| `sync_status_card.html` | `view.phone` | `acct_label` | WIRED | Объект передаётся, не ключ |
| `history_export` | карта номеров | `phones` до `db.stream` | WIRED | `history.py:796` → `:864` |
| `sched_card` | полный список аккаунтов пользователя | `accounts` из `ads.py:393-403` | WIRED | Двойник считается по всем аккаунтам, не по чипу |

### Трассировка потока данных (уровень 4)

| Артефакт | Переменная | Источник | Реальные данные | Статус |
|----------|------------|----------|-----------------|--------|
| карточки «Аккаунты» | `acct_labels` | `SELECT id, type, phone FROM messenger_accounts WHERE user_id` | да | ✓ FLOWING |
| фрагмент опроса | `acct_label` | `view.phone` ← объект аккаунта + `load_account_rows` | да | ✓ FLOWING |
| карточка истории | `log.account_label` | `group.account_id` → карта пользователя | да | ✓ FLOWING |
| CSV | `phone=` | `phones.get(group.account_id)` | да | ✓ FLOWING |
| админка | `phone_label(account)` | ORM-объект аккаунта (`.phone`) | да | ✓ FLOWING |

Колонка `phone` у всех настоящих аккаунтов до Фаз 18–19 пуста, поэтому в бою на экранах будет «Номер неизвестен» — заявленное промежуточное состояние (CONTEXT `<specifics>`), на бой оно не выкатывается (деплой-гейт D-26).

### Поведенческие проверки

| Поведение | Команда | Результат | Статус |
|-----------|---------|-----------|--------|
| Двойники и плоская форма | `build_labels` на 5 строках | 1,2 (WA без номера) twin; 3,5 (TG, два написания одного номера) twin; 4 (MAX, тот же номер) не twin | ✓ PASS |
| Ячейка CSV | `export_phone_cell` на 9 значениях | как в строке SC4 выше | ✓ PASS |
| Чипы и сводка расписания | отрисовка макросов Jinja | per-chip `title=`, экранирование, `#id` только у двойника | ✓ PASS |
| Набор фазы | `flock … pytest` 13 файлов (`test_services/test_account_label`, `test_application/test_account_label_rows`, гейт, 6 файлов `test_account_label_*`, `test_history_export`, три гейта номера) | 1396 passed | ✓ PASS |
| Полная суита (данные оркестратора, не мой прогон) | `uv run pytest tests/ -q` на `fc18c218` | 5952 passed, 2 skipped; после — только `.planning/` | ✓ (по сообщению оркестратора) |

### Исполнение проб

Фаза не объявляет проб (`probe-*.sh`) — шаг не применим.

### Покрытие требований

| Требование | План(ы) | Описание | Статус | Доказательство |
|------------|---------|----------|--------|----------------|
| PHONE-03 | 17-01, 02, 03, 04, 08, 09 | Номер вместо `#id` на экранах пользователя | ✓ SATISFIED | Истина 1; раскладочная половина — у человека |
| PHONE-04 | 17-01, 02, 03, 04, 09 | «Номер неизвестен» при отсутствии номера | ✓ SATISFIED | Истина 2 |
| PHONE-05 | 17-01, 02, 03, 04, 09 | Приглушённый `#id` у двойников | ✓ SATISFIED | Истина 3 |
| PHONE-06 | 17-05, 07, 08, 09 | Админка: номер и `#id` | ✓ SATISFIED | Истина 4 |
| PHONE-07 | 17-06 | CSV: колонка «Номер», `account_id` сохранена | ✓ SATISFIED | Истина 4 (CSV) |

Все пять идентификаторов из `requirements:` планов найдены в REQUIREMENTS.md (строки 23–27) и покрыты. Осиротевших требований нет: таблица трассировки отображает на фазу 17 ровно PHONE-03…07, и каждое названо хотя бы одним планом. Строки REQUIREMENTS.md не правились (решение оркестратора).

### Прохибиции (судейский уровень, неавторитетный вердикт — ADR-550 D4)

Все 19 прохибиций в планах 17-01…17-09 имеют статус `flagged-unverified`. Выборочная проверка кодом, нарушений не найдено; решение остаётся за человеком (см. human_verification):

- не маскировать номер у пользователя / не звать `mask_phone` — `mask_phone` вне `services/phone.py` и `log_masking.py` в `app/` не встречается;
- не писать в `phone` из кода фазы и не входить в `writer_scope()` из `app/` и `scripts/` — вхождений нет; три гейта номера зелёные;
- не считать двойника по порции — карта по `user_id` во всех путях; не показывать `#id` у уникальной подписи — проход по путям зелёный;
- не подписывать «Номер неизвестен» запись без аккаунта (D-15) — `history_account_label` отдаёт `None`, CSV пуст;
- не трогать `incidents.py`, `retry_availability`; не заводить скрипт посева и `17-UAT.md` — изменений и файлов нет;
- не показывать `credentials` как номер — в помощнике и макросе слова `credentials` нет;
- без исключения для формул (`export_cell` после `removeprefix`), колонка «Аккаунт» на месте 2;
- админская карта — по просматриваемому пользователю.

### Антипаттерны

| Файл | Строка | Шаблон | Серьёзность | Влияние |
|------|--------|--------|-------------|---------|
| — | — | `TBD`/`FIXME`/`XXX`, `TODO`/`HACK`/`PLACEHOLDER` в добавленных строках файлов фазы | — | Не найдено (проверено по `git diff 41e2396f..HEAD -U0`) |

### Замечания код-ревью (`17-REVIEW.md`, диспозиции все `open`)

Ни одно не опровергает истину и не блокирует; оценка относительно цели:

- **WR-01** (`_ChipTitles` / `_SummaryTitles` в `tests/test_pages/test_editor_schedules.py` приписывают `title=` первого чипа всем): подтверждён по описанию. На нём держится одна проверка плана 17-01 — «плоская форма в `title=` чипа и сводки». Сама истина проверена мной независимо, отрисовкой: у каждого из четырёх чипов свой `title=`, у двойников с `#id`. Дефект — слабость теста (проверка читает только первый ключ и может пройти или упасть по случайной причине при смене порядка), а не дефект продукта. Ни одно другое обязательное утверждение фазы на этот помощник не опирается: проход и тесты адресов используют `_Tracker` из `tests/account_label_support.py`, который пустые элементы учитывает. **Предупреждение, не блокер.**
- **WR-02** (`history_account_label`: ветка `group.account_id is None` недостижима — `Group.account_id` `NOT NULL`; докстринг называет вымышленный «второй случай»): поведение цели не затрагивает (реальный случай D-15 — `group is None` — работает и закрыт тестом). Ложное утверждение в докстринге — долг читаемости. **Предупреждение.**
- **IN-01** (`export_row(phone=None)` молча даёт пустую ячейку при забытом аргументе), **IN-02** (шесть локальных словарей типа канала в соседних шаблонах — D-11 их не называл), **IN-03** (тест прохода импортирует приватные помощники из чужих тестовых модулей) — информационные.

### Отложенные пункты

Отложенных пунктов нет: поздние фазы (18–20) закрывают пометку «указан вручную», ручную правку, захват и дозаполнение, а не недостающее в Фазе 17.

### Расширенный обзор расхождений

Расхождений между сводками и деревом не найдено: `git diff --name-only fc18c218..HEAD -- . ':!.planning'` пуст, состав файлов фазы совпадает с `key-files`, `covered_files` (56) равен переданным 38 файлам плюс 18 планов/сводок.

## Требуется проверка человеком

### 1. Обход на 320 и 375 px (D-21)

**Тест:** по брифу в `17-09-SUMMARY.md` (раздел «Бриф обхода (D-21)») засеять пять образцов (с номером, без номера, пара двойников без номера, пара двойников с одним номером, неразбираемый номер — через писатель Фазы 16, пятый — разовой командой с `writer_scope()` вне `app/` и `scripts/`; образцы 1–4 разными мессенджерами или номерами), обойти экраны на 320 и 375 px, после обхода обязательно вычистить засеянное.
**Ожидается:** `#id` двойника виден на чипе и в `<h2>`; нет горизонтального скролла; перенос в карточках и строках админки; подпись целиком в модалке; различимы двойники в `<option>`; три элемента подряд в строках воркеров и очереди не ломают строку; наихудшая длина «MAX +888 01234567 #123456» и 16 символов неразбираемого номера держатся.
**Почему человек:** ширину машинно не доказать.

### 2. Читаемость номера в `<h2>` экрана групп

**Тест:** на 320 и 375 px и на десктопе сравнить размер номера (`.mono`, `--fs-xs`) с названием канала (`--fs-2xl`).
**Ожидается:** номер читается в шапке; если нет — решение владельца (CSS-правило сознательно не добавлялось).
**Почему человек:** оценка вида.

### 3. Открытый курсор на PostgreSQL в CSV (17-06 D4)

**Тест:** выгрузить историю на боевом драйвере asyncpg.
**Ожидается:** файл полный, «Номер» заполнен, ошибок параллельной операции нет.
**Почему человек:** тесты идут на aiosqlite.

### 4. Прохибиции судейского уровня

**Тест:** просмотреть неавторитетный вердикт выше.
**Ожидается:** подтверждение или возражение.
**Почему человек:** мягкий шлюз ADR-550 D4.

## Итог по пробелам

Пробелов, блокирующих цель, нет: все пять требований реализованы в коде и подтверждены отрисовкой, прицельным прогоном 13 файлов (1396 passed) и данными оркестратора о полной суите. Статус `human_needed` вызван единственной непроверяемой машинно половиной критерия 5 (раскладка 320–375 px), поведением открытого курсора на PostgreSQL и мягким шлюзом прохибиций. Предупреждения WR-01 и WR-02 фазу не блокируют.

---

_Проверено: 2026-11-20T22:30:00Z_
_Верификатор: Claude (gsd-verifier)_
