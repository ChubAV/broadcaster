---
status: diagnosed
phase: 11-massovyy-perevod-razdelov-pisma
source: [11-VERIFICATION.md]
started: 2026-09-17T09:14:11Z
updated: 2026-09-17T16:33:36Z
checks_declared: 7
# ⚠️ ФОРМА ТЕКУЩЕЙ ЭПОХИ, А НЕ ТОЛЬКО ШАБЛОН GSD. Разделы `Current Test`/`Tests`/`Summary`/`Gaps`
# ведёт `/gsd-verify-work`; разделы «Проверка N» с таблицами отметок ставят артефакт ПОД
# `tests/test_planning/test_the_walkthrough_cannot_self_certify.py` (как обходы фаз 9 и 10),
# а не в число изъятых. Терминальное `status` при пустой отметке краснит прогон.
---

## Current Test

[testing paused — 4 items outstanding: отметки проверок 1, 2, 3 ждут наблюдённых признаков человека (ответы «pass» без признака); проверка 6 открыта гэпом G-11-6]

## Tests

### 1. Оформление доступа на тестовом ключе ЮKassa при живом htmx
expected: На /billing нажать кнопку оплаты; во вкладке Network у POST /billing/subscribe — 204 и HX-Redirect. Браузер уходит на страницу подтверждения ЮKassa; фактический хост confirmation_url — ровно yoomoney.ru (иначе ответ уедет в /billing?notice=payment_failed). Записать фактический хост. Критерий 2, окно 87; план 11-15 требует этого до слияния.
result: pass

### 2. Прокрутка при создании расписания в длинном списке
expected: Редактор объявления с 8+ расписаниями — прокрутить вниз, нажать «+ РАСПИСАНИЕ». Позиция прокрутки не сброшена; новая карточка появилась в конце #sched-list раскрытой; линейка и сводка показывают новое число.
result: pass

### 3. Alpine после свапов без перезагрузки (UAT пункт 5)
expected: (а) редактор — десяток сохранений и тумблеров карточек при раскрытой соседней; (б) /schedules с фильтром — тумблер строки и докрутка второй порции; (в) карточка пользователя в админке — десяток переключений блокировки и бесплатного доступа; (г) /accounts — «Повторить», опрос account-row-N, панели удаления; (д) мастер MAX — индикатор ~5 с, QR, опрос статуса, пустой телефон из пробелов. Раскрытая карточка не схлопывается; в DOM ровно одна панель sched-del-N / user-imp / user-del на объект, панели открываются с актуальным текстом; подписи, бейдж и плитка согласованы; слушатели не копятся; двойное нажатие тумблера даёт один запрос; ошибка MAX перерисовывает шаг с введённым значением.
result: pass

### 4. Back и F5 после переходов (UAT пункт 7)
expected: /ads/new — набрать заголовок до создания черновика; «Повторить» на /accounts; «Синхронизировать всё» на экране групп; затем Back и F5. Адресная строка сменилась (/ads/{id}/edit, экран групп); Back и F5 не предлагают повторно отправить POST.
result: pass
note: "Части А и В сняты агентом в браузере по реплике владельца; часть Б («Повторить») не наблюдена — нет аккаунта в состоянии «Ошибка синхронизации». Владелец принял пункт без части Б репликой «1» (2026-09-17): тот же путь перехода, что у «Синхронизировать всё», покрыт тестами."

### 5. Профиль: сохранение и 422 в браузере
expected: Сохранить часовой пояс — плашка «сохранено» в области шелла без перезагрузки. Затем через DevTools подложить неверный пояс и отправить — на 422 форма #profile-settings перерисована с текстом «Неверный часовой пояс», без плашки аварии.
result: pass
note: "Снято агентом в браузере по реплике владельца «пятую проверь сам». Ожидаемое сошлось. Два побочных наблюдения, оба достижимы только подменой значения через DevTools: после 422 поле выбора показывает первый вариант (Калининград), а не присланное значение, — повторное «Сохранить» записало бы его; плашка «Настройки сохранены.» от предыдущего успеха остаётся видна рядом с ошибкой поля."

### 6. Лишний зазор под кнопками
expected: Форма «Продолжить» (MAX), «Сохранить» (профиль), форма правки расписания — нет лишнего вертикального зазора под кнопками от скрытого .form-busy (находка 1 в 11-UI-REVIEW.md).
result: issue
reported: "Владелец поручил проверку агенту («шестую тоже проверь сам»). Замер агента в Chrome 152 / macOS на broadcaster.all-torgi.ru: зазор ЕСТЬ во всех трёх формах. Профиль «Сохранить» — форма 132 px, без .form-busy 111 px: лишние 21 px под кнопкой (скрытая точка inline-block открывает строчный бокс под flex-колонкой [data-form]). Правка расписания sched-101 «Сохранить расписание» — форма 1710 px, без точки 1686 px: лишние 24 px (точка — flex-элемент 8 px плюс gap 16 px). MAX «Продолжить» — лишние 18,5 px под кнопкой (форма 129,5 px против 111 px); разметку шага phone агент отрендерил из шаблона и вставил на живую страницу с боевым CSS, потому что /accounts/connect/max при активном MAX #29 уводит на /accounts."
severity: cosmetic

### 7. Решение владельца по прочтениям критериев, принятым по умолчанию
expected: Владелец подтверждает летописи критериев 1, 3, 4, 5 в ROADMAP.md как контракт фазы — либо называет, что вернуть. Прочтения: D-01 (15/5 → 12 обработчиков), D-05 (afterbegin → beforeend в конце списка), D-06 (422 только у профиля и MAX), D-12/D-13 (критерий 5 по разделам, hx-push-url не ставится), D-14 (160 → 158, htmx-половина пары 200/204 по форме ответа). Лично владельцем принято только D-08; остальные написаны агентом по делегированию («решай сам по умолчаниям»), а буквальный текст FORM-07 («afterbegin») и критерия 4 («160», «→ 200») им не соответствует.
result: pass

## Проверка 1 — переход в ЮKassa на тестовом ключе (тест 1)

### Отметка о закрытии проверки 1

*(заполняет человек на приёмке; отметка без наблюдённого признака закрытием не считается; фактический хост `confirmation_url` — обязательная клетка)*

| Дата | Браузер / ОС | Кто наблюдал | Наблюдённый признак (код, заголовок, хост) |
|---|---|---|---|
|  |  |  |  |

## Проверка 2 — прокрутка при создании расписания (тест 2)

### Отметка о закрытии проверки 2

*(заполняет человек на приёмке; отметка без наблюдённого признака закрытием не считается)*

| Дата | Браузер / ОС | Кто наблюдал | Наблюдённый признак |
|---|---|---|---|
|  |  |  |  |

## Проверка 3 — Alpine после свапов, UAT пункт 5 (тест 3)

### Отметка о закрытии проверки 3

*(заполняет человек на приёмке; отметка без наблюдённого признака закрытием не считается; по строке на раздел (а)–(д) допустимо)*

| Дата | Браузер / ОС | Кто наблюдал | Наблюдённый признак |
|---|---|---|---|
|  |  |  |  |

## Проверка 4 — Back и F5, UAT пункт 7 (тест 4)

### Отметка о закрытии проверки 4

*(заполняет человек на приёмке; отметка без наблюдённого признака закрытием не считается)*

| Дата | Браузер / ОС | Кто наблюдал | Наблюдённый признак |
|---|---|---|---|
| 2026-09-17 | Chrome 152 / macOS (агент, chrome-devtools MCP, broadcaster.all-torgi.ru; `workflow.live_dom_uat` = false — браузер вёл агент по прямой реплике владельца «проверь сам через mcp chrome dev») | агент | **(А) черновик:** на `/ads/new` набран заголовок → `POST /ads/new` 200 с `HX-Push-Url: /ads/66/edit`, `htmx:pushedIntoHistory`, адрес `/ads/66/edit` без перезагрузки, скрытое `ad_id` = 66; следующие автосохранения (ещё 4 POST) — в ту же запись, нового черновика нет. F5 → документ `GET /ads/66/edit` 200, заголовок на месте; Back → документ `GET /ads/new` 200; ни одного POST документом. Повтор на черновике 67 — то же. **(В) «Синхронизировать всё»** на MAX #29 (групп вне расписаний): `POST /accounts/29/sync-groups` 204 + `HX-Location: /accounts/29/groups` → `GET` 200, `pushedIntoHistory`, история 17 → 18, плашка «найдено 3, новых 0, обновлено имён 0, не найдено 1». F5 → документ `GET` 200; Back → документ `GET` 200; POST повторно не ушёл. **(Б) «Повторить» НЕ НАБЛЮДЕНА:** ни у одного из трёх аккаунтов нет состояния «Ошибка синхронизации», кнопки на `/accounts` нет. ⚠️ Признаки снял АГЕНТ, не человек: подписью приёмки эта строка не является. Побочные следы на стенде: черновики 66 и 67, у MAX #29 одна группа помечена «не найдено». В первом прогоне (А) заголовок в поле однажды пропал до второго набора; повтор с журналом `beforeinput`/`input` и OOB-свопов не воспроизвёл — узел поля не подменялся, выделение не ставилось; причина не установлена, признаком продукта не записано |

Решение владельца по части Б (2026-09-17, реплика «1»): пункт засчитан без наблюдения «Повторить» — на стенде нет аккаунта с ошибкой синхронизации; переход `HX-Location` у `accounts_retry_sync` тот же, что у наблюдённой части В, и покрыт тестами пар.

## Проверка 5 — профиль: сохранение и 422 (тест 5)

### Отметка о закрытии проверки 5

*(заполняет человек на приёмке; отметка без наблюдённого признака закрытием не считается)*

| Дата | Браузер / ОС | Кто наблюдал | Наблюдённый признак |
|---|---|---|---|
| 2026-09-17 | Chrome 152 / macOS (агент, chrome-devtools MCP, broadcaster.all-torgi.ru; `workflow.live_dom_uat` = false — браузер вёл агент по прямой реплике владельца «пятую проверь сам») | агент | **Сохранение:** «Сохранить» с тем же поясом `Europe/Moscow` → `POST /profile` 200, свап в `#profile-settings`, внеполосно в `#notice` — `alert--success` «Настройки сохранены.»; тот же документ (маркер на `<html>` жив, записей навигации 1). **422:** в `<select id="timezone">` добавлен и выбран `Mars/Olympus_Mons` → `POST /profile` 422, `htmx:beforeSwap` `shouldSwap: true`, `isError: true`; в `#profile-settings` перерисована форма с `alert--error` «Неверный часовой пояс»; `#htmx-failure-server` и `#htmx-failure-network` остались `hidden`; документ тот же. После F5 сохранённый пояс — `Europe/Moscow`, ошибок нет. ⚠️ Признаки снял АГЕНТ, не человек: подписью приёмки эта строка не является. Побочно: после 422 поле выбора стоит на первом варианте (`Europe/Kaliningrad`), присланного значения в списке нет; плашка успеха предыдущего сохранения видна рядом с ошибкой поля — оба случая достижимы только подменой через DevTools |

## Проверка 6 — зазор под кнопками (тест 6)

### Отметка о закрытии проверки 6

*(заполняет человек на приёмке; отметка без наблюдённого признака закрытием не считается)*

| Дата | Браузер / ОС | Кто наблюдал | Наблюдённый признак |
|---|---|---|---|
|  |  |  |  |

## Проверка 7 — решение владельца по прочтениям критериев (тест 7)

### Отметка о закрытии проверки 7

*(заполняет владелец; отметка без названного решения по каждому из D-01, D-05, D-06, D-12/D-13, D-14 закрытием не считается)*

| Дата | Кто решал | Решение (подтверждено / что вернуть) |
|---|---|---|
| 2026-09-17 | владелец (`chubav`), реплика «pass» на чекпоинт проверки 7 в `/gsd-verify-work 11` | **Подтверждено, возвращать нечего:** D-01 (15/5 → 12 обработчиков) — подтверждено; D-05 (afterbegin → beforeend в конце списка) — подтверждено; D-06 (422 только у профиля и MAX) — подтверждено; D-12/D-13 (критерий 5 по разделам, hx-push-url не ставится) — подтверждено; D-14 (160 → 158, htmx-половина пары 200/204 по форме ответа) — подтверждено. Летописи критериев 1, 3, 4, 5 в ROADMAP.md приняты контрактом фазы. Чекпоинт предлагал два исхода — подтвердить либо назвать, что вернуть; выбран первый. Строку записал агент дословным переносом реплики владельца |

## Summary

total: 7
passed: 6
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- gap_id: G-11-6
  truth: "Под кнопками форм «Продолжить» (MAX), «Сохранить» (профиль) и «Сохранить расписание» нет лишнего вертикального зазора от скрытого .form-busy"
  status: failed
  reason: "Agent measured (owner delegated: «шестую тоже проверь сам»): extra space under the button in all three forms — profile 21 px, schedule edit sched-101 24 px, MAX phone step 18.5 px (MAX markup rendered from the template and injected into the live page, since /accounts/connect/max redirects while MAX #29 is active). Taking .form-busy out of flow removes exactly that space."
  severity: cosmetic
  test: 6
  root_cause: "components/form_wrapper.html always prints <span class=\"form-busy\"> as the last IN-FLOW child of every wrapped form (after a whitespace node), and the base rule .form-busy (app.css:2154) gives it an 8x8 display:inline-block box hidden only by opacity/visibility — the box keeps its layout space, nothing takes it out of flow. In a block form whose content is a flex column (profile [data-form], MAX .connect-step__form) it opens an anonymous line box under the column (21 / 18.5 px); in a flex-column form (schedule edit form, gap 16) it is an 8 px flex item plus one gap (24 px); in flex action rows it widens each wrapped form by ~12 px, making gaps uneven. Harmless in Phase 9 (one inline-flex toggle caller); Phase 11 moved 13 more forms onto the macro and 11-10/11-18 moved the column from <form> to an inner div."
  artifacts:
    - path: "app/templates/components/form_wrapper.html"
      issue: "busy span always an in-flow last child of the form, whitespace before it"
    - path: "app/static/css/app.css"
      issue: ".form-busy (2154-2160) is an 8x8 inline-block box hidden by visibility/opacity only; no out-of-flow rule"
    - path: "app/templates/includes/profile_settings.html"
      issue: "column layout on inner [data-form], form itself is block — exposes the line box (21 px)"
    - path: "app/templates/accounts/includes/max_connect_step.html"
      issue: "column layout on inner .connect-step__form — same line box (18.5 px)"
    - path: "app/templates/ads/includes/sched_card.html"
      issue: "edit form (line 210) is a flex column with gap 16 — span adds 8 px item + 16 px gap (24 px); toggle form (167) in .sched-card__head widened ~12 px"
    - path: "app/templates/components/modal.html"
      issue: "prints its own .form-busy span in flex-column .modal__form (gap 14) — ~22 px in all 18 confirmation panels; caught by any global .form-busy fix (owner decision: height of an accepted panel)"
  missing:
    - "Take the busy indicator out of flow once, in the macro/CSS rather than per caller: positioning context on the wrapped form plus an absolutely positioned dot with explicit offsets, kept inside the form box (.card has overflow:hidden)"
    - "Keep the base .form-busy rule as the only rule with that exact selector and keep display:inline-block in it (test_the_indicator_class_is_self_sufficient reads the last matching rule); scope any new rule, e.g. form > .form-busy"
    - "Keep both transition strings, the .form-busy.htmx-request selector, the verbatim span markup in form_wrapper.html and modal.html, WRAPPER_QUALITY_ATTRS appearing once, 16 component files, and the schedule edit form's flex column with gap 16"
    - "If a class is added to the wrapper's <form>, update the allowed-quality-difference reason «имя класса формы» (test_every_allowed_quality_difference_carries_a_reason)"
    - "Preserve accepted observations: dot beside the group-row toggle (09-UAT 6.1.2) and inside the modal panel (10-UAT 3.5)"
    - "Row/header call sites with uneven gaps: admin/includes/user_actions.html:70,83; accounts/list.html:133; accounts/partial_cards.html:87; accounts/partials/sync_status_card.html:109; account_groups/list.html:104; ads/includes/sched_card.html:167; schedules/includes/schedule_row.html:106"
  debug_session: ".planning/debug/form-busy-extra-space-under-buttons.md"
