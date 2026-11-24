---
phase: quick-261008-bm0-confirm-panels-survive-body-swap
plan: 01
status: complete
subsystem: ui
tags: [htmx, alpine, settle, confirm-modal, issue-51]

requires: []
provides:
  - "Седьмой ключ блока htmx-config: attributesToSettle [class, width, height] — style больше не осаждается при подмене"
  - "Регрессия issue #51 на двух поверхностях (аккаунты, объявления) с отрицательным контролем предиката"
  - "Контракт HTMX_CONFIG в обоих шеллах с семью ключами"
affects: [htmx-config, components/modal, accounts, ads, admin, history, schedules, account_groups]

actuals:
  tokens: 6073
  tasks: 2
  commits: 3
plan_head_before: 855143c2d8b1b74c4ba604359f09269a9e7d0b24
plan_head_after: 0e5573dbbe23fa79daf83b63d1ed03a2ddfecb74

tech-stack:
  added: []
  patterns:
    - "У инлайнового style один владелец — Alpine; рантайм подмены его не осаждает (ключ конфигурации, а не правка макроса)"
    - "Разметочная регрессия рантайм-дефекта: предпосылки (умолчание из вендоренного бандла, форма корня, совпадение id) + предикат на действующем списке, отрицательный контроль"

key-files:
  created:
    - tests/test_pages/test_confirmation_panel_settle.py
  modified:
    - app/templates/includes/htmx_config.html
    - tests/test_pages/test_shell.py
    - tests/test_pages/test_htmx_response_contract.py

key-decisions:
  - "Issue #51 закрыт седьмым ключом attributesToSettle без style в htmx_config.html, а не серверным style в макросе панели: один владелец атрибута на весь проект, 18 мест подтверждения разом, критерий 3 не задет"
  - "class оставлен в списке оседания: единственная Alpine-привязка класса (components/filters.html) стартует с состояния, совпадающего с разметкой"

patterns-established:
  - "Предикат «атрибуты, которыми владеет состояние панели, осаждаемые рантаймом» с кортежем владения ('style',) — при появлении расходящегося x-bind:class дописывается class"

requirements-completed: [QUICK-ISSUE-51-ACCOUNT-DELETE-CHAIN]

coverage:
  - id: D1
    description: "Действующий список оседания документа /accounts не содержит style; панели оставшихся аккаунтов приходят под прежними id (сценарий issue #51)"
    requirement: QUICK-ISSUE-51-ACCOUNT-DELETE-CHAIN
    verification:
      - kind: integration
        ref: "tests/test_pages/test_confirmation_panel_settle.py#test_the_swap_after_an_account_deletion_cannot_strip_the_hidden_state_of_the_other_panels"
        status: pass
    human_judgment: false
  - id: D2
    description: "Тот же механизм на списке объявлений /ads закрыт тем же ключом"
    requirement: QUICK-ISSUE-51-ACCOUNT-DELETE-CHAIN
    verification:
      - kind: integration
        ref: "tests/test_pages/test_confirmation_panel_settle.py#test_the_swap_after_an_ad_deletion_cannot_strip_the_hidden_state_of_the_other_panels"
        status: pass
    human_judgment: false
  - id: D3
    description: "Отрицательный контроль: предикат называет style на умолчании рантайма и пуст на отгруженной конфигурации"
    requirement: QUICK-ISSUE-51-ACCOUNT-DELETE-CHAIN
    verification:
      - kind: unit
        ref: "tests/test_pages/test_confirmation_panel_settle.py#test_control_negative_the_panel_settle_predicate_names_style_on_the_runtime_default"
        status: pass
    human_judgment: false
  - id: D4
    description: "Контракт HTMX_CONFIG с седьмым ключом в обоих шеллах"
    requirement: QUICK-ISSUE-51-ACCOUNT-DELETE-CHAIN
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_main_shell_carries_htmx_config"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_auth_shell_carries_htmx_config"
        status: pass
    human_judgment: false
  - id: D5
    description: "Зрительный результат в живом браузере: после подтверждения удаления на /accounts и /ads ни одна другая панель подтверждения не всплывает, удалена ровно выбранная сущность"
    requirement: QUICK-ISSUE-51-ACCOUNT-DELETE-CHAIN
    verification: []
    human_judgment: true
    rationale: "Суита не исполняет JS: рантайм подмены и Alpine в pytest не работают. Прогон jsdom планировщика — замер механизма, разметочная регрессия — утверждение предпосылок и конфигурации; ни то, ни другое не приёмка. Отметку ставит владелец своими словами."

duration: 36min
completed: 2026-10-08
status: complete
---

# Quick 261008-bm0: issue #51 — панели подтверждения переживают подмену тела

**Седьмой ключ `attributesToSettle: ["class", "width", "height"]` в `htmx_config.html` снимает `style` с оседания htmx 2.0.10. Раньше при подмене тела по `HX-Location` оседание стирало `display: none`, записанный Alpine по `x-show`, и панели подтверждения оставшихся аккаунтов всплывали стопкой. Добавлена регрессия на две поверхности. До правки она была RED.**

## Performance

- **Duration:** ~36 min (2026-10-08T08:40:52Z → 09:16:43Z)
- **Tasks:** 2/2
- **Files modified:** 4 (1 создан, 3 изменены)

## Accomplishments

- Корень дефекта измерен разметочной регрессией. Вендоренный рантайм осаждает `style` по умолчанию (прочитано из `htmx.min.js`). У корня панели есть `id` и `x-show`, но нет серверного `style`. После удаления ответ подмены приносит панели оставшихся сущностей под прежними `id`.
- Правка стоит в одном месте на весь проект: ключ конфигурации с Jinja-комментарием о причине над `<meta>`. Шапка файла не раздвинута.
- Контракт `HTMX_CONFIG` расширен до семи ключей и проверяется в обоих шеллах.

## Task Commits

1. **Task 1 RED:** `24627fda` — `test(quick-261008-bm0): pin issue #51 — body swap must not settle panel style`
2. **Task 1 GREEN:** `b500ab1c` — `fix(quick-261008-bm0): stop htmx settling inline style that Alpine x-show owns (issue #51)`
3. **Task 2:** `0e5573db` — `test(quick-261008-bm0): ads surface, control negative for the panel settle predicate`

## TDD Gate Compliance

**RED снят до правки и подтверждён вербом.** Прогон: `uv run pytest tests/test_pages/test_confirmation_panel_settle.py -q --junit-xml=<scratchpad>/red.xml`, exit 1. Тест упал на последнем утверждении (строка 200), то есть на предикате, а не на ошибке сбора, импорта или `KeyError`:

```
AssertionError: действующий список оседания документа ['class', 'style', 'width', 'height']
(умолчание вендоренного рантайма ['class', 'style', 'width', 'height']) осаждает ['style']: ...
(issue #51)
assert ['style'] == []
```

JUnit перегнан в TAP скриптом в scratchpad (не коммитится). `gsd-tools check tdd-red-evidence` дал вердикт `RED_EVIDENCE_OK`, причина `target_test_failed`, `matched_test = test_the_swap_after_an_account_deletion_cannot_strip_the_hidden_state_of_the_other_panels`. После правки (`b500ab1c`) тот же тест GREEN.

## Мутационная проверка зубов (не коммитилась)

Строку седьмого ключа временно удалил из `htmx_config.html` и прогнал сценарии и контракт. Покраснели 5 из 5:

```
E AssertionError: действующий список оседания документа ['class', 'style', 'width', 'height'] ... осаждает ['style'] ... панели оставшихся аккаунтов всплывут стопкой после подтверждения (issue #51)
E AssertionError: действующий список оседания документа ['class', 'style', 'width', 'height'] ... осаждает ['style'] ... панели оставшихся объявлений всплывут стопкой после подтверждения (issue #51)
E AssertionError: отгруженный список оседания ['class', 'style', 'width', 'height'] осаждает атрибуты, которыми владеет состояние панели (issue #51)
E AssertionError: auth_base.html: состав ключей верхнего уровня разошёлся — лишние [], недостающие ['attributesToSettle']
E AssertionError: base.html: состав ключей верхнего уровня разошёлся — лишние [], недостающие ['attributesToSettle']
5 failed, 249 deselected
```

Файл восстановлен через `git checkout -- app/templates/includes/htmx_config.html`, `git status` по нему чист.

## Распоряжение по девяти основам события (`MODAL_TRIGGER_SITES`)

Для каждой основы проверено: что отвечает ветка успеха (`respond(...)` в `app/pages/`) и рендерит ли страница назначения панели той же основы под `id`, которые уже были в документе. Ключ конфигурации глобальный, поэтому закрывает все строки «тот же дефект» разом. Регрессией покрыты только две измеренные поверхности, как и требовал план.

| Основа | Ветка успеха | Панели той же основы после подмены под прежними id? | Вердикт |
|---|---|---|---|
| `acc-del-` | `accounts_delete` → `respond(redirect="/accounts")` → 204 + `HX-Location`, подмена тела | Да: панели оставшихся аккаунтов | **Тот же дефект, закрыт седьмым ключом** (регрессия D1, замер планировщика) |
| `ad-del-` | `ads_delete` → `HX-Location: /ads` (оба выхода) | Со списка `/ads`: да. Из редактора объявления: нет (в старом документе была только панель удаляемого объявления, её на `/ads` нет) | **Тот же дефект на списке, закрыт ключом** (регрессия D2, замер планировщика). Из редактора поверхность не задета |
| `sched-del-` | `schedules_delete` → `respond(..., fragment=_fragment)`: на htmx фрагмент с внеполосным `delete` строки и панели, тело не подменяется | Нет на фрагментном пути. Ветка без фрагмента (`schedules.py:1817`, чужое или исчезнувшее расписание) ведёт `HX-Location` на тот же экран, там панели оставшихся расписаний под прежними id | Фрагментный путь не задет. Ветка перехода — **тот же дефект, закрыт ключом** |
| `group-del-` | `account_groups` delete → `respond(..., fragment=_fragment)`: внеполосный `delete` строки и панели | Нет на фрагментном пути. Ветка «выдача опустела» (`account_groups.py:797`) ведёт `HX-Location` на тот же экран, групп в выдаче нет | Не задет: фрагментный путь, а на переходе одноимённых панелей нет |
| `user-del-` | `admin.py` delete → `HX-Location: /admin/users` (список без панелей `user-del-`) | Нет на успехе. Ветка отказа (`admin.py:2010`) ведёт на `/admin/users/{id}`, та же карточка с той же панелью | Успех не задет. Ветка отказа — **тот же дефект, закрыт ключом** |
| `user-imp-` | `admin.py` impersonate → `HX-Location: /dashboard` (панелей нет) | Нет на успехе. Ветка отказа (`admin.py:1861`) ведёт на `/admin/users/{id}`, та же панель | Успех не задет. Ветка отказа — **тот же дефект, закрыт ключом** |
| `worker-restart-` | `admin.py` restart → `HX-Location: /admin/workers` | Да: панели всех wa/max-воркеров стоят вне контейнера опроса (`workers.html:55`) под прежними id | **Тот же дефект, закрыт ключом**. Опрос `every Ns` подменяет только строки `#admin-workers`, панелей там нет, поэтому опросом поверхность не задета |
| `queue-drop-` | `admin.py` drop → `HX-Location: /admin/queue` (с плашкой) | Да: id панели строится по позиции строки (`queue_drop_modal_id`), оставшиеся позиции совпадают | **Тот же дефект, закрыт ключом** |
| `history-retry-` | `history.py` retry → `HX-Location: /history` (с плашкой) | Да: на `/history` у каждой записи панель `history-retry-{log.id}` под прежним id | **Тот же дефект, закрыт ключом** |

## Отвергнутые формы правки

- **Серверный `style="display: none"` на корне панели в `components/modal.html`.** Снимает симптом, но у атрибута остаются два владельца. Пришлось бы править макрос восемнадцати мест под тяжёлыми гейтами панели, а следующий узел с `id` и `x-show` получил бы тот же дефект.
- **Перевод удаления аккаунта на фрагментный путь.** Запрещён изъятием `OFFSET_CURSOR_EXCEPTIONS` (курсор порции смещением) и не лечит остальные поверхности из таблицы выше.
- **`x-bind:hidden` вместо `x-show`.** Та же правка макроса. Вдобавок `.modal { display: … }` перекрывает атрибут `hidden`, и без отдельного правила это не работает.

## Правки прозы о числе ключей (идиома D-30/D-32)

Где проза утверждает текущий состав, «шесть» заменено на «семь»:
- `tests/test_pages/test_shell.py`: комментарий над `HTMX_CONFIG` (`Семь ключей ВЕРХНЕГО уровня`), докстринг `_htmx_config_of` и сообщение его отказа, докстринг `_assert_config_contract`, докстринг `test_auth_shell_carries_htmx_config`, докстринг `test_auth_shell_purges_the_legacy_history_cache_once` («снятие любого из семи ключей»), шапка группы G-23 («семь ключей блока конфигурации»). Над `HTMX_CONFIG` добавлен абзац о седьмом ключе и его стороже.
- `tests/test_pages/test_htmx_response_contract.py`: докстринг правила валидации («ВСЕ семь ключей»).

Летописные места (абзац о правке безопасности Фазы 7) не вычеркнуты. Они помечены вставкой «шестиключевым (с issue #51 — семиключевым) составом»:
- `app/templates/includes/htmx_config.html:88` — правка в той же строке, число строк шапки не изменилось;
- `tests/test_pages/test_shell.py` — абзац «⚠️ СВОП СНЯТ ПРАВКОЙ БЕЗОПАСНОСТИ ФАЗЫ 7»;
- `tests/test_pages/test_htmx_response_contract.py` — абзац «ПОПРАВКА АУДИТА БЕЗОПАСНОСТИ ФАЗЫ 7».

`tests/test_pages/test_htmx_gates.py:3756` («шесть ключей сняты прогоном замера») говорит о ключах перечня гейта, а не конфигурации, и не тронут.

## Проверки

| Команда | Результат |
|---|---|
| `uv run pytest tests/test_pages/test_confirmation_panel_settle.py tests/test_pages/test_shell.py tests/test_pages/test_htmx_response_contract.py tests/test_pages/test_failure_banner_invariants.py tests/test_pages/test_confirm_delete_transport.py tests/test_routes/test_wa_sync_status.py -q` | 345 passed |
| `uv run pytest tests/test_pages/test_responsive_markup.py -q -k "account"` | 26 passed, 116 deselected |
| `uv run pytest tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_htmx_gates.py tests/test_templates/ -q` | 566 passed (перед каждым из трёх коммитов) |
| `git diff --quiet b5b4c83f… -- app/templates/components/modal.html app/templates/accounts app/static/js app/pages` | exit 0 (границы не тронуты) |
| `graphify update .` | exit 0 (`graphify-out/` в git не отслеживается, в коммит не входит) |

Полная сюита (~40 мин) не прогонялась: по договору задачи она не входит в гейт.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — гейт] Комментарий ключа срабатывал как импорт панели**
- **Найдено в:** задаче 1, на сквозных гейтах перед GREEN-коммитом.
- **Проблема:** `tests/test_templates/test_components.py` (`test_modal_site_inventory`, `test_every_modal_site_has_cancel_and_escape`, `test_modal_guard_is_inherited_by_every_consumer`) считает импортёром панели любой шаблон, в тексте которого встречается подстрока `components/modal.html`, комментарии тоже. Новый Jinja-комментарий называл файл буквально, и гейт насчитал 12 импортёров вместо 11.
- **Исправление:** в комментарии написано «компонент modal в каталоге components» вместо пути. Гейты зелёные: 566 passed.
- **Файлы:** `app/templates/includes/htmx_config.html` (вошло в `b500ab1c`).

**2. [Rule 2 — полнота] Проза о числе ключей в `test_htmx_response_contract.py`**
- **Найдено в:** задаче 1, при поиске «шесть ключей» по `tests/` и `app/`.
- **Проблема:** в файле, которого нет в `files_modified`, оставалось утверждение о составе («ВСЕ шесть ключей») и летописная формула Фазы 7.
- **Исправление:** то же приведение, что в `test_shell.py`, только проза. Вошло в `b500ab1c`.

### Процедурные отступления

- **Коммиты на `master`.** Предкоммитная проверка исполнителя сообщила, что `master` защищён (`git.base-branch --is-protected` → `true`, ключа `git.allow_default_branch_commits` в конфиге нет). Коммиты сделаны на `master` всё равно, по прямому указанию оркестратора: «sequential on the main checkout (branch master), no worktree». Прецедент — прежние quick-задачи проекта. Ничего не пушилось.
- **STATE.md, ROADMAP.md и вербы `state.*` не трогались.** Так указал оркестратор: docs-коммит и учёт quick-задачи делает он сам.

## Known Stubs

Нет.

## Проверка владельцем в браузере (D5, `human_judgment: true`)

1. Откройте `/accounts`. Аккаунтов должно быть три или больше.
2. Нажмите «Удалить» у любого аккаунта и подтвердите удаление в панели.
3. Дождитесь обновления списка. Ни одна другая панель подтверждения не должна появиться сама. Удалён должен быть только выбранный аккаунт, остальные на месте.
4. Повторите то же на `/ads` с тремя или больше объявлениями.

Отметку о результате пишет владелец своими словами. Исполнитель её не заполняет.

## Self-Check: PASSED

- FOUND: tests/test_pages/test_confirmation_panel_settle.py
- FOUND: app/templates/includes/htmx_config.html (attributesToSettle на строке блока)
- FOUND: 24627fda, b500ab1c, 0e5573db — предки HEAD
