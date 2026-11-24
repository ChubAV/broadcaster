---
phase: 17-pokaz-nomera-na-vseh-ekranah
verified: 2026-11-24T12:00:00Z
status: passed
score: 6/6 must-haves verified
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
covered_digest: "v4:sha256:c1bc34abd4fd585645366de09e2d7fb3112482c308443487710768607aa5f185"
behavior_unverified: 0
gaps: []
human_verification: []
re_verification:
  round: 2
  date: 2026-11-24
  reason: "stale — `verification status` сообщил, что после прогона верификатора сдвинулись 19 покрытых файлов, все правлены ПОЗДНИМИ фазами 18–20 (ручная правка номера, захват номера при подключении, дозаполнение): app/application/accounts/dto.py, app/application/accounts/labels.py, app/application/accounts/use_cases.py, app/pages/account_groups.py, app/pages/accounts.py, app/services/account_label.py, app/static/css/app.css, app/templates/account_groups/list.html, app/templates/accounts/list.html, app/templates/accounts/partial_cards.html, app/templates/accounts/partials/sync_status_card.html, app/templates/components/account_label.html, tests/account_label_support.py, tests/test_application/test_account_label_rows.py, tests/test_pages/test_account_label_accounts.py, tests/test_pages/test_account_label_groups.py, tests/test_pages/test_account_label_sweep.py, tests/test_pages/test_responsive_markup.py, tests/test_services/test_account_label.py"
  baseline: "4f65d5f4 — код фазы 17 как он был закрыт и пройден владельцем на бою 2026-11-21"
  re_measured: "каждая истина и каждый обязательный артефакт фазы заново по ЖИВОМУ дереву (HEAD ветки gsd/phase-17-pokaz-nomera-na-vseh-ekranah, код = master 0f115213), а не только дельта покрытых файлов: git diff 4f65d5f4..HEAD по каждому файлу; собственный прогон правила подписи и ячейки CSV; живые шлюзы (греп-гейт `#id` с реестром исключений 3+2, проход по объявленным адресам 10+6); прицельный прогон 10 файлов (267 passed) и `test_responsive_markup -k account_label` (3 passed); данные оркестратора (union 25 путей карты Нейквиста 2985 passed, полная суита 6298 passed / 2 skipped)"
  gaps_closed: []
  gaps_remaining: []
  regressions: []
previous_round:
  verified: 2026-11-20T22:30:00Z
  body_status: human_needed
  score: "5/6 must-haves verified"
  canonicalization: "Тело отчёта раунда 1 читалось `human_needed`; frontmatter `status` переведён в `passed` командой `/gsd-verify-work 17` (коммит 103fa6d0) после того, как `17-UAT.md` закрыт 3/3 (тесты 1–3 закрыли все три пункта `human_verification` собственными словами владельца, 2026-11-21). Тело раунда 1 ниже дословно не правилось."
  behavior_unverified: 1
  behavior_unverified_items:
    - truth: "Раскладка с номером не ломается на 320–375 px (критерий 5, вторая половина)"
      test: "Открыть экраны из брифа D-21 (17-09-SUMMARY.md, раздел «Ширины 320 и 375 px») на 320 и 375 px с засеянными образцами; смотреть чип расписания, шапку групп аккаунта, карточки аккаунта и истории, строки воркеров и очереди, наихудшую длину «MAX +888 01234567 #123456»"
      expected: "Нет горизонтального скролла; у двойника на чипе и в <h2> усекаются канал и номер, а `#id` остаётся; переносящиеся контейнеры переносят подпись, действия не выталкиваются"
      why_human: "В репозитории нет браузера: суита читает текст CSS (правила `.chip__label > .acct-label`, `.acct-head__name > .acct-label`, `.acct-label__id { flex: none }` присутствуют), но ширины не меряет; чтение CSS ширину не доказывает"
      disposition:
        closed_by: "17-UAT.md, тест 1 (обход D-21 на 320 и 375 px)"
        date: 2026-11-21
        result: pass
        owner_words: "принимаю обход, оба места — граница с подсказкой, находки не заводить"
        round_2_judgment: "Закрытие остаётся в силе на сегодняшнем дереве: CSS и разметку подписи позднее правила Фаза 18, и это поколение пройдено владельцем отдельно на бою 2026-11-22 (18-UAT.md, тесты 6 и 9, «принимаю все»); правила `.chip__label > .acct-label`, `.acct-head__name > .acct-label`, `.acct-label__id { flex: none }` сохранены (3 правила `test_responsive_markup -k account_label` passed). Остаточный риск — админские строки с пометкой «указан вручную» на 320 px замером не пройдены; по коду (встроенные span в переносящейся строке) вытолкнуть строку не могут — см. тело отчёта."
  human_verification:
    - test: "Обход D-21 на 320 и 375 px (стенд — боевая база под сессией владельца, засев пяти образцов, чистка после обхода обязательна)"
      expected: "См. раздел «Ширины 320 и 375 px» брифа в 17-09-SUMMARY.md: вид `#id` двойника на чипе и в <h2>; читаемость номера в <h2> (класс `mono` --fs-xs рядом с --fs-2xl — решение владельца, CSS-правило не добавлялось); перенос в карточках и строках админки; подсказка `title=` на чипе; модалка удаления; <option> фильтра; три элемента подряд в строке воркера и очереди; наихудшая длина"
      why_human: "Визуальная раскладка и усечение текста на узком экране машинно здесь не проверяются; отметки, `result` и замеры ставит человек (голое «pass» не отметка)"
      disposition:
        closed_by: "17-UAT.md, тест 1 (обход D-21 на 320 и 375 px)"
        date: 2026-11-21
        result: pass
        owner_words: "принимаю обход, оба места — граница с подсказкой, находки не заводить"
        round_2_judgment: "Действует: поколение CSS Фазы 18 пройдено владельцем 2026-11-22 (18-UAT.md, тесты 6 и 9); два места неразличимости двойников (свёрнутая сводка расписания, закрытый `<select>`) — граница, их файлы (`sched_card.html`, `history/list.html`) не менялись с 4f65d5f4."
    - test: "Открытый курсор на PostgreSQL в CSV-экспорте (17-06 D4): выгрузить историю на боевом драйвере asyncpg с несколькими аккаунтами и записью без аккаунта"
      expected: "Файл целиком, колонка «Номер» заполнена по карте, прочитанной ДО `db.stream`; ошибки «another operation is in progress» нет"
      why_human: "Тесты идут на aiosqlite; поведение серверного курсора asyncpg без боевой базы не воспроизводится (карта номеров читается одним `load_account_rows` до потока — `app/pages/history.py:796`, поток открывается на :857)"
      disposition:
        closed_by: "17-UAT.md, тест 2 (открытый курсор PostgreSQL в CSV, 17-06 D4)"
        date: 2026-11-21
        result: pass
        owner_words: "принимаю тест 2, номер без плюса закрыт суитой"
        round_2_judgment: "Действует: `app/pages/history.py` не менялся с 4f65d5f4; карта номеров читается до `db.stream` (`:796` → `:857`); `export_phone_cell` на живом дереве даёт `7 999 123-45-67` без плюса, пусто у неизвестного номера."
    - test: "19 прохибиций судейского уровня в `must_haves.prohibitions` девяти планов помечены `flagged-unverified`"
      expected: "Человек подтверждает или отклоняет неавторитетный вердикт верификатора (ниже, раздел «Прохибиции»): нарушений при выборочной проверке кодом не найдено"
      why_human: "Judgment-tier прохибиции — мягкий шлюз (ADR-550 D4): вердикт LLM не авторитетен и не может быть тихо зелёным"
      disposition:
        closed_by: "17-UAT.md, тест 3 (сверка 19 запретов судейского уровня)"
        date: 2026-11-21
        result: pass
        owner_words: "согласен со всеми 19 строками"
        round_2_judgment: "Действует: прохибиции относятся к коду фазы 17; файлы админки, истории, расписаний и общих глобалов не менялись, правки помощника подписи — добавка (четвёртая колонка), `mask_phone` вне `services/phone.py` и `log_masking` — 0 вхождений, слова `credentials` в помощнике нет."
---

# Фаза 17: Показ номера на всех экранах — отчёт верификации (раунд 2)

**Цель фазы:** пользователь узнаёт свой аккаунт по номеру на каждом экране, где раньше стоял `#id`, а администратор видит и номер, и `#id`
**Проверено:** 2026-11-24T12:00:00Z
**Статус:** passed
**Повторная верификация:** да — раунд 2 (причина: вердикт `stale` после правок фаз 18–20; раунд 1 — 2026-11-20, тело `human_needed` 5/6, закрыт владельцем `17-UAT.md` 3/3 2026-11-21)

Стартовая гипотеза — «задачи выполнены, цель на сегодняшнем дереве не достигнута». Опровергнута измерением: все 19 сдвинувшихся файлов правили поздние фазы, и каждая правка — добавка (четвёртая колонка `phone_is_manual`, пометка «указан вручную», форма номера на экране групп, ссылка «Указать номер / Изменить» в карточке, правила CSS пометки и отступа прокрутки). Правило подписи, двойника, «Номер неизвестен», админские экраны, CSV и греп-гейт на живом дереве держатся так, как закрыто в раунде 1. Файлы подписи в админке, истории и расписаниях (`app/pages/admin.py`, `app/pages/history.py`, `app/pages/common.py`, `app/templates/admin/**`, `app/templates/history/**`, `app/templates/ads/**`) байт-в-байт совпадают с закрытым состоянием: `git diff 4f65d5f4..HEAD` по ним пуст.

## Что поздние фазы изменили и затрагивает ли это фазу 17

| Файл / область | Что изменено (фазы 18–20) | Влияние на истины фазы 17 |
|---|---|---|
| `app/services/account_label.py` | `AccountRow` и `AccountLabel` получили поле `phone_is_manual`; `row_of`, `label_of`, `build_labels` его несут; признак вне ключа двойника; у аккаунта без номера пометки нет | Нет. Ключ двойника `(тип, shown_phone)` не тронут; плоские формы (`text`, `plain`, `plain_with_id`) пометки не несут; мой прогон: тот же набор двойников, что в раунде 1 |
| `app/application/accounts/labels.py` | Проекция стала четырёхколоночной; фильтр `user_id` и один запрос прежние | Нет: граница пользователя и «один запрос» сохранены; `credentials` по-прежнему не читаются |
| `app/templates/components/account_label.html` | Добавлен `<span class="acct-label__manual">указан вручную</span>` ПОСЛЕ номера и ДО `#id` | Нет: адрес `data-account-label`, автоэкранирование, `mono--muted` и `account_id_mark` прежние |
| `app/static/css/app.css` | Правила пометки (усечение первой, приглушение); `html { scroll-padding-top }`; ряд `.acct-head__actions` стал сжимаемым; правила `.chip__label > .acct-label`, `.acct-head__name > .acct-label`, `.acct-label__id { flex: none }` сохранены | Раскладочная половина критерия 5 — см. ниже; дополнительно перелив «К аккаунтам» на 320 px (предсуществовал с `bef29322`) закрыт Фазой 18 |
| `app/pages/account_groups.py` (+403), `app/pages/accounts.py`, `app/templates/account_groups/list.html`, `accounts/list.html`, `partial_cards.html`, `sync_status_card.html` | Форма и обработчики ручного номера; `<title>` собирает `_screen_title` (тот же текст `plain — группы аккаунта — Broadcaster`); ссылка «Указать номер / Изменить» в каждой копии карточки; опрос строит `label_of(AccountRow(..., view.phone, view.phone_is_manual), rows)` | Нет: подпись на каждом из этих мест по-прежнему приходит из одного помощника; фрагмент опроса несёт объект подписи |
| `app/application/accounts/dto.py`, `use_cases.py` | `SyncStatusView.phone_is_manual` | Нет: `SyncStatusView.phone` по-прежнему заполнен во всех ветках |
| Тесты (`account_label_support.py`, `test_account_label_*`, `test_responsive_markup.py`) | Доехали четвёртая колонка, помощники пометки; `test_account_label_sweep.py` +85 строк — пометка у КАЖДОГО адреса подписи, плоские формы без пометки | Усиление: объявленные адреса прохода (10 пользовательских, 6 админских) прежние, добавлены три новых правила про пометку |
| Не менялись | `app/pages/admin.py`, `app/pages/history.py`, `app/pages/common.py`, `app/templates/admin/**`, `app/templates/history/**`, `app/templates/ads/**`, `tests/test_templates/test_account_label_gate.py` | Админские экраны, CSV, чипы расписаний и греп-гейт — ровно те, что закрыты 2026-11-21 |

## Достижение цели

### Наблюдаемые истины (контракт роадмапа + решения D-01…D-21), заново по живому дереву

| # | Истина | Статус | Доказательство на сегодняшнем дереве |
|---|--------|--------|--------------------------------------|
| 1 | SC1. Номер `+7 999 123-45-67` вместо `#id` на каждом месте пользователя: карточки аккаунтов (страница, порция, опрос), шапка и `<title>` групп аккаунта, чипы расписаний, карточка и фильтр истории, модалка удаления | ✓ VERIFIED | Макрос подключён в 11 шаблонах (`grep components/account_label.html`): `accounts/list.html`, `accounts/partial_cards.html`, `accounts/partials/sync_status_card.html`, `account_groups/list.html`, `account_groups/partials/phone_response.html`, `ads/includes/sched_card.html:230` (`labels[acc.id]`), `history/includes/history_card.html:213`, плюс админские. Обработчики: `accounts.py:173,219` (`build_labels(load_account_rows)`), `accounts.py:1100-1101` (опрос), `account_groups.py:302,555-556`, `history.py:673`. `<title>` — `_screen_title`: `f"{acct_label.plain} — группы аккаунта — Broadcaster"`, тот же текст, что был в шаблоне. Прицельный прогон 10 файлов: 267 passed (135 с); проход `test_account_label_sweep.py` — 10 пользовательских путей, все зелёные |
| 2 | SC2. «Номер неизвестен» приглушённо (`mono--muted`) на всех местах, включая фрагменты опроса и подгрузки | ✓ VERIFIED | Мой прогон `build_labels`: `None` и `''` → «Номер неизвестен», `phone_text is None`; макрос ставит `mono--muted` при `phone_text is none` (`account_label.html:39`); неразбираемое `garbage` показано как есть. Пометка «указан вручную» у аккаунта без номера не ставится (`manual and shown is not None`) — «неизвестен» с пометкой не появляется. Опрос: `view.phone` и `view.phone_is_manual` во всех ветках, обработчик `accounts.py:1100-1101` |
| 3 | SC3. `#id` — только у двойников (совпала готовая подпись у аккаунтов одного мессенджера одного пользователя) | ✓ VERIFIED | Мой прогон на 6 строках: два WA без номера (`None` и `''`) — twin у обоих; TG `+79991234567` и TG `+7 999 123-45-67` (второй с `phone_is_manual=True`) — twin у обоих (ручной и автоматический одинаковые номера остаются двойниками); MAX с тем же номером — не twin; `garbage` — не twin. Двойник считается по ВСЕМ аккаунтам пользователя (`load_account_rows(db, user.id)` во всех 5 обработчиках) |
| 4 | SC4. Админка («Воркеры», «Очередь», карточка пользователя, история пользователя) — номер и отдельный `#id` всегда; CSV с колонкой «Номер» рядом с «Аккаунт», с прежним обезвреживанием формул, `account_id` сохранён | ✓ VERIFIED | Файлы админки и истории не менялись с `4f65d5f4`. `worker_row.html:75,87-89`, `queue_row.html:75-76`, `queue.html:87`, `user_detail.html:121`, `history_card.html:213-214` (`audience == 'admin'`). `phone_label(account)` — `label_of(row_of(account), ())` (`common.py:348`), без `#id` двойника в макросе и с отдельным `account_id_mark`. CSV: `EXPORT_HEADER[:5] = ('Время','Канал','Аккаунт','Номер','Группа')`; мой прогон `export_phone_cell`: `+79991234567`→`7 999 123-45-67`, `None`/`''`/`'  '`→пусто, `+=cmd`→`'=cmd`, `++=1`→`'+=1`, `-5`→`'-5`, `garbage`→как есть; карта номеров читается ДО потока (`history.py:796` → `db.stream` на `:857`, `phones.get` на `:864`). Проход админских путей: 6 путей зелёные |
| 5a | SC5 (машинная половина). Подпись собирается одним помощником; греп-гейт краснеет на сборку `'#' ~ account.id` вне него; тесты находят подпись по адресу `data-account-label` | ✓ VERIFIED | Живой греп `app/` на `'#'`, `"#"`, `#{`: ровно пять вхождений — `account_label.html:30` (`account_id_mark`), `account_label.py:87` (`id_mark`), `history/detail.html:54` и `history_card.html:216` (`#` перед `group_external_id`), `htmx.py:774` (`partition("#")`). Гейт `test_account_label_gate.py` зелёный на живом дереве: `TEMPLATE_HASH_EXCEPTIONS_DECLARED = 3`, `PYTHON_HASH_EXCEPTIONS_DECLARED = 2` совпадают с реестрами (`len(...) == DECLARED`), файл гейта с `4f65d5f4` не менялся; поздние фазы не добавили ни одного нового `#` перед идентификатором аккаунта. Объявленные адреса прохода (10 + 6) совпадают с живым `len(SWEPT_USER_CASES)`/`len(SWEPT_ADMIN_PATHS)` |
| 5b | SC5 (раскладочная половина). Раскладка с номером не ломается на 320–375 px | ✓ VERIFIED (по приёмке владельца) | Закрыта на бою владельцем 2026-11-21 (`17-UAT.md`, тест 1, `result: pass`) на коде `4f65d5f4`. Затем правила CSS подписи менялись Фазой 18, и ЭТО поколение пройдено владельцем отдельно на бою 2026-11-22 (`18-UAT.md`, тесты 6 и 9: «принимаю все»): `<h2>` на 320 — номер 116/116, пометка усечена 35/85, `#75` и `#84` двойника виден; чип на 320 — канал 40/58, номер 79/116, `#id` 22/22, полный текст в `title=`; карточки `/accounts` на 320 без горизонтальной прокрутки (`scrollWidth` 320); `innerWidth` = `visualViewport` = 320. Подробнее — раздел «Применимость закрытия D-21» ниже. Вердикт: закрытие остаётся в силе |

**Счёт:** 6/6 истин проверены, 0 присутствуют без доказанного поведения.

### Применимость закрытия D-21 к сегодняшнему дереву

Вопрос: покрывает ли приёмка владельца 2026-11-21 (код `4f65d5f4`) сегодняшнюю раскладку подписи, если Фаза 18 правила CSS и разметку подписи?

Что изменилось в раскладке подписи (`git diff 4f65d5f4..HEAD -- app/static/css/app.css app/templates/components/account_label.html`):

- Добавлен `.acct-label__manual` и его усечение в двух однострочных контейнерах (`.chip__label`, `.acct-head__name`); пометка усекается ПЕРВОЙ (основа 0, рост до собственной ширины), номер и канал — не несжимаемые (`#id` двойника `flex: none` сохранён).
- `.acct-head__actions` стал сжимаемым: перелив «К аккаунтам» на 320 px, найденный владельцем в обходе 2026-11-21 как давний (`bef29322`) и не заведённый находкой, теперь устранён.
- `html { scroll-padding-top }` — отступ прокрутки к якорям, на раскладку подписи не влияет.
- Правила `.chip__label > .acct-label`, `.acct-head__name > .acct-label`, `.acct-label__id { flex: none }`, отсутствие фиксированных ширин — без изменений; их держат `test_account_label_keeps_the_twin_id_visible_in_a_one_line_container`, `test_account_label_rules_introduce_no_fixed_width`, `test_account_label_chip_keeps_the_full_text_in_its_title` (мой прогон `-k "account_label or acct"`: 3 passed).

Что покрывает поколение после правки: обход Фазы 18 (тесты 6 и 9, 2026-11-22, бой, Chrome через CDP, 320 и 375 px, приёмка владельца «принимаю все») снимал замеры именно на шапке экрана групп, чипе расписания с ручным номером и двойником, карточках `/accounts` и карточке `sync_failed` — те же места, что в брифе D-21, уже с пометкой и новым CSS. Чип на 320 px с усечённым номером и полным текстом в `title=` владелец принял тем же решением, что и в фазе 17.

Что не покрыто новым обходом и почему это не повод открывать пункт: админские строки «Воркеры» / «Очередь» / карточка пользователя 320 px были пройдены в обходе фазы 17 без пометки; пометка «указан вручную» теперь появляется и там (проход `test_every_admin_screen_marks_a_manual_number_at_its_label` держит её на каждом адресе подписи), но это короткий (~85 px) строчный `<span>` внутри строки, где контейнер уже переносит (`[data-row] { flex-wrap: wrap }`, `[data-grow]` — основа 100 %, содержимое ячейки — встроенные `<span>`, между которыми есть пробелы-разрывы), а ширина строки 288 px; правила `flex-shrink`-приоритета пометки действуют только в чипе и `<h2>`. Горизонтальная прокрутка на этих экранах на 320 px и до фазы 18 шла от ключей `infra:heartbeat:*` и названий групп (замер 2026-11-21: 366 и 446 px), а не от подписи. Вывод по коду — добавка не может вытолкнуть строку; прямого замера админских строк с пометкой на 320 px нет. Это остаточный риск малой вероятности, а не провал истины; решение: нового пункта `human_verification` не заводить.

### Обязательные артефакты

| Артефакт | Ожидается | Статус | Детали на сегодняшнем дереве |
|----------|-----------|--------|-------------------------------|
| `app/services/account_label.py` | `build_labels`, `label_of`, `AccountLabel.plain` / `plain_with_id`, `id_mark` | ✓ VERIFIED | Существенный, без БД и Jinja; плоские формы без пометки; `id_mark` — единственная сборка `#` в модуле |
| `app/templates/components/account_label.html` | Макросы `account_label`, `account_id_mark`, адрес `data-account-label` | ✓ VERIFIED | Адрес на месте (`:37`), автоэкранирование; пометка добавлена, `#id` — только `account_id_mark` |
| `app/application/accounts/labels.py` | `load_account_rows` — один запрос по пользователю | ✓ VERIFIED | Четыре колонки (`id, type, phone, phone_is_manual`), `WHERE user_id`; `credentials` не читаются |
| `app/pages/common.py` | Глобалы `phone_labels`, `phone_label` | ✓ VERIFIED | Файл не менялся; `phone_label` — `label_of(row_of(account), ())` |
| `app/application/accounts/dto.py` | `SyncStatusView.phone` | ✓ VERIFIED | `phone` и `phone_is_manual` в DTO |
| `app/pages/history.py` | `history_account_label`, `EXPORT_HEADER` + «Номер», `export_phone_cell`, карта до потока | ✓ VERIFIED | Файл не менялся с `4f65d5f4` |
| `tests/test_templates/test_account_label_gate.py` | Греп-гейт с реестром и подложенными строками | ✓ VERIFIED | Зелёный на живом дереве; файл не менялся |
| `tests/test_pages/test_account_label_sweep.py` | Проход по отрисованным экранам | ✓ VERIFIED | 10 + 6 адресов; добавлены правила про пометку; зелёный |
| `app/static/css/app.css` | Контракт длинной подписи | ✓ VERIFIED | Правила фазы 17 на месте, пометка — добавка (см. выше) |

### Проверка ключевых связей

| Откуда | Куда | Через | Статус | Детали |
|--------|------|-------|--------|--------|
| обработчики страниц | `build_labels` / `label_of` | `load_account_rows(db, user.id)` | WIRED | `accounts.py:173,219,1100`; `account_groups.py:302,555`; `history.py:673,796`; `admin.py:1554` |
| шаблоны | макрос подписи | `{% from "components/account_label.html" import … %}` | WIRED | 11 шаблонов, включая новый `phone_response.html` Фазы 18 |
| `sync_status_card.html` | `acct_label` | объект подписи | WIRED | Обработчик опроса передаёт объект, не ключ |
| `history_export` | карта номеров | `phones` до `db.stream` | WIRED | `history.py:796` → `:857` |
| `sched_card` | полный список аккаунтов пользователя | `labels[acc.id]` | WIRED | Файл не менялся |

### Трассировка потока данных (уровень 4)

| Артефакт | Переменная | Источник | Реальные данные | Статус |
|----------|------------|----------|-----------------|--------|
| карточки «Аккаунты» | `acct_labels` | `SELECT id, type, phone, phone_is_manual FROM messenger_accounts WHERE user_id` | да | ✓ FLOWING |
| фрагмент опроса | `acct_label` | `view.phone`, `view.phone_is_manual` + `load_account_rows` | да | ✓ FLOWING |
| карточка истории | `log.account_label` | `group.account_id` → карта пользователя | да | ✓ FLOWING |
| CSV | `phone=` | `phones.get(group.account_id)` | да | ✓ FLOWING |
| админка | `phone_label(account)` | ORM-объект аккаунта | да | ✓ FLOWING |

Колонка `phone` до Фаз 19–20 у настоящих аккаунтов была пуста; после захвата номера при подключении (Фаза 19) и дозаполнения (Фаза 20) подпись получает реальные номера по тому же потоку.

### Поведенческие проверки

| Поведение | Команда | Результат | Статус |
|-----------|---------|-----------|--------|
| Двойники, «неизвестен», ручной номер | `build_labels` на 6 строках (см. истину 3) | 1,2 twin; 3,4 twin (в т. ч. `phone_is_manual=True`); 5 (MAX) не twin; 6 (`garbage`) не twin и показан как есть | ✓ PASS |
| Ячейка CSV | `export_phone_cell` на 8 значениях | как в истине 4 | ✓ PASS |
| Шапка CSV | `EXPORT_HEADER[:5]` | «Аккаунт» на месте 2, «Номер» на месте 3 | ✓ PASS |
| Набор фазы (мой прогон) | `uv run pytest` 10 файлов (`test_services/test_account_label`, `test_application/test_account_label_rows`, гейт, 6 файлов `test_account_label_*` включая `sweep`, `test_history_export`) | 267 passed, 135 с | ✓ PASS |
| CSS-контракт подписи (мой прогон) | `pytest tests/test_pages/test_responsive_markup.py -k "account_label or acct"` | 3 passed | ✓ PASS |
| Union 25 путей карты Нейквиста (данные оркестратора, `.pytest_cache/gsd-orch/p17r/map-union.log`, на `0f115213`) | `-v -rs` | 2985 passed, 0 skipped, 0 failed, 27:16 | ✓ PASS (по данным оркестратора) |
| Полная суита (данные оркестратора, `.pytest_cache/gsd-orch/suite-p20-w7.log`, `c0ef8fe1`) | `just test`; после — только `.dockerignore`, не читаемый ни одним тестом | 6298 passed, 2 skipped | ✓ PASS (по данным оркестратора) |
| `tests/test_planning` на `54e46b82` (данные оркестратора) | — | 218 passed, 2 skipped (объявленное условное правило `test_deferred_items_are_idempotent.py:227`) | ✓ PASS (по данным оркестратора) |

### Исполнение проб

Фаза не объявляет проб (`probe-*.sh`) — шаг не применим.

### Покрытие требований

| Требование | План(ы) | Описание | Статус | Доказательство |
|------------|---------|----------|--------|----------------|
| PHONE-03 | 17-01, 02, 03, 04, 08, 09 | Номер вместо `#id` на экранах пользователя | ✓ SATISFIED | Истины 1 и 5; раскладка закрыта владельцем 2026-11-21 и поколение Фазы 18 пройдено 2026-11-22 |
| PHONE-04 | 17-01, 02, 03, 04, 09 | «Номер неизвестен» при отсутствии номера | ✓ SATISFIED | Истина 2 |
| PHONE-05 | 17-01, 02, 03, 04, 09 | Приглушённый `#id` у двойников | ✓ SATISFIED | Истина 3 |
| PHONE-06 | 17-05, 07, 08, 09 | Админка: номер и `#id` | ✓ SATISFIED | Истина 4; файлы админки не менялись |
| PHONE-07 | 17-06 | CSV: колонка «Номер», `account_id` сохранена | ✓ SATISFIED | Истина 4 (CSV) |

Все пять идентификаторов из `requirements:` планов 17-01…17-09 найдены в `.planning/REQUIREMENTS.md` (строки 23–27, отметка `[x]`) и в таблице трассировки (строки 86–90, Phase 17 / Complete). Осиротевших требований нет: таблица отображает на фазу 17 ровно PHONE-03…07, и каждое названо хотя бы одним планом.

### Антипаттерны

| Файл | Строка | Шаблон | Серьёзность | Влияние |
|------|--------|--------|-------------|---------|
| — | — | `mask_phone` вне `services/phone.py` и `log_masking` | — | Не найдено (0 вхождений в `app/`) |
| — | — | слово `credentials` в помощнике подписи, макросе и загрузчике | — | Не найдено |
| — | — | `TBD`/`FIXME`/`XXX` в файлах фазы | — | Не найдено в добавленных строках раунда 1; правки фаз 18–20 принадлежат этим фазам |

### Прохибиции (судейский уровень)

Все 19 прохибиций `must_haves.prohibitions` планов 17-01…17-09 в раунде 1 были помечены `flagged-unverified` и закрыты владельцем в `17-UAT.md`, тест 3 («согласен со всеми 19 строками»). Закрытие остаётся в силе на сегодняшнем дереве: прохибиции относятся к коду фазы 17, а `app/pages/admin.py`, `app/pages/history.py`, `app/pages/common.py`, `app/templates/admin/**`, `history/**`, `ads/**` не менялись; изменения общего помощника — добавка четвёртой колонки без вызова `mask_phone`, без записи в `phone` из кода подписи, без `credentials`. Запись в `phone`, появившаяся в Фазах 18–20, — собственная область этих фаз (их гейты зелёные в полной суите), а не нарушение запретов фазы 17.

### Замечания код-ревью

`17-REVIEW.md` (WR-01, WR-02, IN-01…IN-03) не перепроверялось заново: на раунде 2 владелец выбрал «Skip» кода-ревью (охват деградировал до 68 файлов поздних фаз). Раунд 1 оценил все замечания как не блокирующие цель; сегодняшняя правка файлов, на которые они указывают (`test_editor_schedules.py`, `history.py`), — пуста для `history.py` и добавочная для тестовых помощников.

### Отложенные пункты

Отложенных пунктов нет. Фазы 18–20 закрыли пометку «указан вручную», ручную правку, захват и дозаполнение — ничего из недостающего в Фазе 17.

## Человеческая проверка

Открытых пунктов нет. Все три пункта `human_verification` раунда 1 и единственный `behavior_unverified` закрыты владельцем в `17-UAT.md` 2026-11-21 (`result: pass`), и каждый перепроверен на применимость к сегодняшнему дереву (диспозиции — в frontmatter `previous_round`):

| Пункт раунда 1 | Закрытие | Слова владельца | Применимость 2026-11-24 |
|---|---|---|---|
| Раскладка 320–375 px (D-21), он же `behavior_unverified` | `17-UAT.md`, тест 1, 2026-11-21, `pass` | «принимаю обход, оба места — граница с подсказкой, находки не заводить» | Действует: поколение CSS Фазы 18 пройдено владельцем 2026-11-22 (`18-UAT.md`, тесты 6 и 9); два места неразличимости двойников (свёрнутая сводка расписания, закрытый `<select>`) — граница, их файлы не менялись |
| Курсор PostgreSQL в CSV (17-06 D4) | `17-UAT.md`, тест 2, 2026-11-21, `pass` | «принимаю тест 2, номер без плюса закрыт суитой» | Действует: `app/pages/history.py` не менялся с `4f65d5f4`; карта читается до `db.stream` (`:796` → `:857`) |
| 19 прохибиций судейского уровня | `17-UAT.md`, тест 3, 2026-11-21, `pass` | «согласен со всеми 19 строками» | Действует: файлы прохибиций не менялись, поздние правки — добавка (см. «Прохибиции») |

## Итог по пробелам

Пробелов нет. Все пять требований (PHONE-03…07) реализованы и подтверждены на сегодняшнем дереве; шлюзы живого дерева (греп-гейт `#id` 3 + 2 исключения, проход 10 + 6 адресов) совпадают с объявленными числами; закрытия владельца раунда 1 применимы. Статус `passed`. Единственный остаточный риск, названный честно: админские строки с пометкой «указан вручную» на 320 px замером не пройдены (по коду добавка не способна вытолкнуть строку); он не опровергает ни одну истину и нового пункта не требует. Код-ревью по решению владельца пропущено; аудит интерфейса `17-UI-REVIEW.md` оставлен как есть.

---

_Проверено: 2026-11-24T12:00:00Z_
_Верификатор: Claude (gsd-verifier)_

## Запись раунда 1 (2026-11-20, дословно)

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
