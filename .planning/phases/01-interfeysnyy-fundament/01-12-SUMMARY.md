---
phase: 01-interfeysnyy-fundament
plan: 12
subsystem: ui
tags: [jinja2, templates, modal, alpine, responsive, accessibility, pytest]

# Dependency graph
requires:
  - phase: 01-02
    provides: "Библиотека components/*.html и запрет на неэкранированный вывод"
  - phase: 01-03
    provides: "Эталон строки ads/includes/ad_card.html и панель подтверждения удаления объявления"
  - phase: 01-07
    provides: "Правило [data-cell-label] в app.css и медиазапрос 860px; запрет на расширение состава данных в админке"
  - phase: 01-09
    provides: "Параметр label у макроса cell и слот полей формы у макроса modal"
  - phase: 01-11
    provides: "Схема «перехват на самой форме, панель соседним элементом» и подпись индексом списка колонок"
provides:
  - "Идентификатор панели удаления группы: group-del-<id>, событие modal-open-group-del-<id>"
  - "Идентификатор панели удаления расписания: schedule-del-<id>, событие modal-open-schedule-del-<id>"
  - "Идентификатор панели массового удаления групп: groups-bulk-del, событие modal-open-groups-bulk-del"
  - "Внутри формы панели массового удаления: скрытое поле action=delete, контейнер groups-bulk-del-ids, счётчик groups-bulk-del-count"
  - "Все четырнадцать мест подтверждения удаления устроены одинаково и деградируют без Alpine"
  - "Подписи колонок во всех шести оставшихся шаблонах с шапкой"
affects: [01-13, "Фазы 2-6 (переводят подтверждения на панель)"]

actuals:
  tokens: 40700
  tasks: 3
  commits: 6

tech-stack:
  added: []
  patterns:
    - "Массовое подтверждение фиксирует набор СНИМКОМ в скрытых полях формы панели: вопрос и отправка относятся к одному чтению отметок"
    - "Кнопка-триггер панели вне формы отменена как класс: триггером служит настоящая форма с x-on:submit.prevent"
    - "Счётчик набора живёт внутри поясняющего текста панели и приходит через слот полей формы Плана 09"
    - "Подпись передаётся индексом списка колонок раздела, а не строковым литералом"

key-files:
  created: []
  modified:
    - app/templates/groups/includes/group_row.html
    - app/templates/groups/list.html
    - app/templates/schedules/includes/schedule_row.html
    - app/templates/ads/includes/ad_card.html
    - app/templates/dashboard/includes/recent_send_card.html
    - app/templates/admin/users.html
    - app/templates/admin/user_detail.html
    - tests/test_pages/test_responsive_markup.py
  deleted: []

key-decisions:
  - "Набор массового удаления читается РОВНО один раз и кладётся скрытыми полями в форму панели ДО открытия вопроса; отправляется именно эта форма — щели между вопросом и удалением не остаётся (T-12-01)"
  - "Ветка пустого выбора осталась системным уведомлением: это ответ на нажатие без выбора, а не подтверждение разрушительного действия"
  - "Ветка деактивации подтверждения не получила: подтверждают разрушительное, а не обратимое"
  - "Поясняющий абзац панели массового удаления несёт класс modal__text — класс самой панели: счётчик обязан стоять ВНУТРИ текста вопроса, а собственных классов раздел не заводит"
  - "Два прежних триггера (объявления, карточка пользователя) переведены на настоящую форму ПЕРВЫМ делом Задачи 3, до механической простановки подписей — как предписано планом"
  - "Критерий `grep -c 'data-area=\"meta\"'` заменён проверкой ключевого аргумента `area='meta'`: литерала атрибута в шаблоне раздела нет и быть не должно — его пишет макрос ячейки"

patterns-established:
  - "Правка макроса строки закрывает списочную страницу и её партиал прокрутки одновременно — партиалы не правятся вовсе"
  - "Порядок операций клиентского кода проверяется по ИСХОДНИКУ: щель между вопросом и отправкой в отрендеренной разметке не видна"
  - "Комментарии не цитируют литералы, по которым идут критерии приёмки (`type=\"button\"` → «кнопка-триггер вне формы»)"

requirements-completed: []

coverage:
  - id: D1
    description: "Удаление группы подтверждается панелью дизайн-системы; системного диалога в разделе не осталось"
    requirement: "UI-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_groups_delete_uses_modal"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_groups_delete_form_degrades_without_alpine"
        status: pass
    human_judgment: false
  - id: D2
    description: "Массовое удаление подтверждает РОВНО тот набор групп, который будет удалён: число в вопросе и отправляемые идентификаторы берутся одним снимком"
    requirement: "UI-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_groups_bulk_delete_uses_modal"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_groups_bulk_modal_confirms_exact_set"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_groups_bulk.py#test_bulk_deactivate_and_delete"
        status: pass
    human_judgment: false
  - id: D3
    description: "Удаление расписания подтверждается панелью и переживает отсутствие Alpine; признак области сетки цел"
    requirement: "UI-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_schedules_delete_uses_modal"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_schedules_delete_form_degrades_without_alpine"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_schedules_row_keeps_grid_area_marker"
        status: pass
    human_judgment: false
  - id: D4
    description: "Два прежних подтверждения (объявления, карточка пользователя) приведены к общему деградирующему механизму — все четырнадцать мест устроены одинаково"
    requirement: "UI-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_ads_delete_form_degrades_without_alpine"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_admin_user_delete_form_degrades_without_alpine"
        status: pass
      - kind: other
        ref: "grep -ro 'modal-open-' app/templates/ --include='*.html' --exclude='modal.html' | wc -l — 14"
        status: pass
    human_judgment: false
  - id: D5
    description: "Строки групп и расписаний несут название каждой колонки — и на списочной странице, и в порции бесконечной прокрутки"
    requirement: "UI-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_groups_cell_labels_present"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_groups_partial_labels_present"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_schedules_cell_labels_present"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_schedules_partial_labels_present"
        status: pass
    human_judgment: false
  - id: D6
    description: "Строки объявлений, дашборда и обеих админских таблиц несут название каждой колонки; состав персональных данных не изменился"
    requirement: "UI-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_ads_cell_labels_present"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_dashboard_cell_labels_present"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_admin_users_cell_labels_present"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_admin_user_detail_cell_labels_present"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_admin_user_detail_shows_no_extra_personal_data"
        status: pass
    human_judgment: false
  - id: D7
    description: "Тумблеры групп и расписаний, фильтры и цепочки бесконечной прокрутки работают как до правки"
    requirement: "UI-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_groups_toggle_route_unchanged"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_schedules_toggle_route_unchanged"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_groups_filters_survive_pagination"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py"
        status: pass
    human_judgment: false
  - id: D8
    description: "Поведение панели в рантайме: начальный фокус на отказе, ловушка фокуса, закрытие по Esc, возврат фокуса; поведение строки-карточки на ширине 375px"
    verification: []
    human_judgment: true
    rationale: "Ни один тест проекта не исполняет JS и ни один не рендерит CSS. Проверены РАЗМЕТОЧНЫЕ признаки: единственность панели, присутствие отказа, имя события, наличие подписи в ячейке. Фактический порядок фокуса и вид строки на 375px — ручная проверка, она в этом прогоне не выполнялась: автономный исполнитель браузера не имеет."

# Metrics
duration: 40 min
completed: 2026-08-09
status: complete
---

# Phase 01 Plan 12: Остаток обоих пробелов — панель подтверждения и подписи колонок Summary

**Три последних места системного диалога переведены на панель дизайн-системы — включая массовое удаление групп, где набор фиксируется снимком в скрытых полях формы панели, — подписи колонок проставлены в шести оставшихся шаблонах, а два прежних подтверждения приведены к тому же деградирующему механизму, что и одиннадцать новых: все четырнадцать мест теперь устроены одинаково.**

## Performance

- **Duration:** 40 min (первый коммит → последний)
- **Started:** 2026-08-09T19:13:15Z
- **Completed:** 2026-08-09T19:45:00Z
- **Tasks:** 3 (все TDD)
- **Files modified:** 8 (7 шаблонов + файл тестов)
- **Tests added:** 16 (6 + 5 + 6, минус один — см. ниже: добавлено 17 функций, из них 16 названы планом)

## Accomplishments

- **Системного диалога подтверждения в шаблонах проекта не осталось ни одного.** `grep -rn 'confirm(' app/templates/` даёт пустоту (кроме `confirm_label=`/`confirm_variant=` — это параметры макроса панели). Единственный оставшийся встроенный обработчик отправки — защита от двойного нажатия в мастере подключения MAX, диалогом не являющаяся.
- **Массовое удаление подтверждает ровно тот набор, который отправляет.** Отметки читаются РОВНО один раз; идентификаторы кладутся скрытыми полями в форму панели и число пишется в текст вопроса ДО открытия панели; отправляется собственная форма панели. Повторного чтения отметок в момент отправки нет — щели, в которой набор может измениться, не существует (T-12-01).
- **Механизм подтверждения стал ОДНИМ механизмом, а не двумя похожими.** Два места, поставленных Планами 03 и 08, работали только при загруженном Alpine: кнопка вне формы плюс форма внутри скрытой панели. Обе заменены настоящей формой с перехватом отправки — имена событий, идентификаторы панелей, заголовки и маршруты не изменились.
- **Правка ушла в макросы, а не в списочные страницы.** `groups/partial_cards.html`, `schedules/list.html`, `schedules/partial_cards.html`, `ads/list.html`, `ads/partial_cards.html`, `dashboard.html` — пустой diff у всех шести: одна правка макроса закрыла и страницу, и порцию прокрутки.
- **Суита выросла с 606 до 623 и осталась зелёной** на каждом из трёх зелёных шагов.

## Task Commits

1. **Задача 1: Группы — панель на строке и на массовом удалении, подписи колонок** — `932fc29` (test, RED) → `6df87e6` (feat, GREEN)
2. **Задача 2: Расписания — панель на строке и подписи колонок** — `922b504` (test, RED) → `6992bd2` (feat, GREEN)
3. **Задача 3: Два прежних триггера, затем подписи в объявлениях, дашборде и админке** — `29783e7` (test, RED) → `51ce011` (feat, GREEN)

Рефакторинга не потребовалось: изменения аддитивные, ни одна ячейка и ни один маршрут не переехали.

## Итоговые четырнадцать мест подтверждения — сверяться Плану 13

| # | Шаблон | Идентификатор панели | Событие открытия | Мест | Панель эмитит |
|---|---|---|---|---|---|
| 1-3 | `accounts/list.html` | `acc-del-<id>` | `modal-open-acc-del-<id>` | 3 | да |
| 4-6 | `accounts/partial_cards.html` | `acc-del-<id>` | `modal-open-acc-del-<id>` | 3 | да |
| 7-9 | `accounts/partials/sync_status_card.html` | `acc-del-<id>` | `modal-open-acc-del-<id>` | 3 | **нет** (сознательно, План 11) |
| 10 | `groups/includes/group_row.html` | `group-del-<id>` | `modal-open-group-del-<id>` | 1 | да |
| 11 | `groups/list.html` | `groups-bulk-del` | `modal-open-groups-bulk-del` | 1 | да |
| 12 | `schedules/includes/schedule_row.html` | `schedule-del-<id>` | `modal-open-schedule-del-<id>` | 1 | да |
| 13 | `ads/includes/ad_card.html` | `ad-del-<id>` | `modal-open-ad-del-<id>` | 1 | да |
| 14 | `admin/user_detail.html` | `user-del-<id>` | `modal-open-user-del-<id>` | 1 | да |

Прямой счёт: `grep -ro 'modal-open-' app/templates/ --include='*.html' --exclude='modal.html' | wc -l` → **14**.

**Тринадцать из четырнадцати — строчные удаления ОДНОЙ сущности, и в каждом стоит настоящая форма** с прежним методом и прежним адресом, кнопка внутри неё — кнопка отправки. Четырнадцатое, `groups-bulk-del`, — единственное место, где триггером служит кнопка вне формы: массовые действия и до правки существовали только при работающем скрипте (кнопки вызывают клиентскую функцию, которая собирает форму), поэтому новых тупиков без JS правка не создаёт.

## Схема снимка набора в массовом удалении

Разметка (слот полей формы Плана 09 — содержимое попадает ВНУТРЬ формы панели):

```jinja
{% call modal(id='groups-bulk-del',
              title='Удалить выбранные группы?',
              action="/groups/bulk",
              confirm_label='Удалить',
              method="post") %}
  <p class="modal__text">Групп к удалению: <span id="groups-bulk-del-count">0</span>. Действие необратимо.</p>
  <input type="hidden" name="action" value="delete">
  <span id="groups-bulk-del-ids"></span>
{% endcall %}
```

Клиентский код (порядок операций — и есть содержание решения):

```js
const ids = Array.from(document.querySelectorAll('.group-checkbox:checked')).map(cb => cb.value);  // РОВНО один раз
if (ids.length === 0) { alert('Выберите группы'); return; }
if (action === 'delete') {
    const box = document.getElementById('groups-bulk-del-ids');
    box.textContent = '';
    ids.forEach(id => { const input = document.createElement('input');
                        input.type = 'hidden'; input.name = 'group_ids'; input.value = id;
                        box.appendChild(input); });
    document.getElementById('groups-bulk-del-count').textContent = ids.length;
    window.dispatchEvent(new CustomEvent('modal-open-groups-bulk-del'));
    return;
}
```

Отправляется собственная форма панели — кнопкой `type="submit"`, которую рисует макрос. Контракт обработчика не изменился: поле `action` со значением `delete` и повторяющиеся поля `group_ids` (`app/pages/groups.py:280-282`).

Узлы создаются и заполняются присваиванием свойств, а не собираются разметкой строкой (T-12-07); `innerHTML` в клиентском коде раздела нет. Порядок операций закреплён `test_groups_bulk_modal_confirms_exact_set` — проверкой по ИСХОДНИКУ, потому что щель между вопросом и отправкой в отрендеренной разметке не видна.

## Окончательный набор подписей по каждому разделу

Подпись получает каждая колонка с непустым названием, КРОМЕ той, что несёт название самой сущности. Подпись передаётся ИНДЕКСОМ списка колонок раздела, а не строкой.

| Шаблон | Список колонок | Подписей | Без подписи |
|---|---|---|---|
| `groups/includes/group_row.html` | `GROUP_COLUMNS` | 5: Идентификатор, Расписаний, Успех, Отправлено, Статус | `Группа` (название сущности), колонки 0 и 7 (названия нет) |
| `schedules/includes/schedule_row.html` | `SCHEDULE_COLUMNS` | 5: Группы, Дни, Время, Следующий запуск, Статус | `Объявление` (название сущности), колонка 6 (названия нет) |
| `ads/includes/ad_card.html` | `AD_COLUMNS` | 5: Текст, Отправок, Расписаний, Создано, Статус | `Объявление` (название сущности), колонка 6 (названия нет) |
| `dashboard/includes/recent_send_card.html` | `RECENT_COLUMNS` | 3: Время, Группа, Статус | `Объявление` (название сущности), колонка 3 (названия нет) |
| `admin/users.html` | `USER_COLUMNS` | 3: Регистрация, Баланс, Статус | `Пользователь` (название сущности) |
| `admin/user_detail.html` | `ACC_COLUMNS` | 1: Статус | `Аккаунт` (название сущности) |

Разность «названия колонок шапки минус подписи» равна ровно одному названию — колонке сущности — на всех шести страницах. Это утверждается тестом на каждой странице, а не выводится.

Одна подпись в карточке пользователя — не недоработка: колонок в таблице аккаунтов две, и первая несёт название самой сущности.

Подписи в админке новым полем не являются: они дублируют название, уже показанное в шапке. `test_admin_users_shows_no_extra_personal_data` и `test_admin_user_detail_shows_no_extra_personal_data` прошли без единой правки.

## Подтверждение: списочные страницы и партиалы прокрутки не правились

```
git diff --stat b76db2d HEAD -- \
  app/templates/groups/partial_cards.html \
  app/templates/schedules/list.html app/templates/schedules/partial_cards.html \
  app/templates/ads/list.html app/templates/ads/partial_cards.html \
  app/templates/dashboard.html
→ пусто
```

Все шесть файлов байт-в-байт как на базе. В разделах групп, расписаний, объявлений и на дашборде строка целиком живёт в макросе; уточнение к списку семи шаблонов из `01-VERIFICATION.md` подтвердилось на всех четырёх — правка макроса закрыла и страницу, и порцию прокрутки, что закреплено отдельными тестами `*_partial_labels_present`.

## Decisions Made

- **Счётчик и контейнер идентификаторов лежат в слоте формы панели, а не подставляются в `body`.** Параметр `body` макроса — экранированный текст; элемент под число в него не поместить. Поясняющий абзац поэтому написан в слоте с классом `modal__text` — классом самой панели. Собственных классов раздел не заводит; чужой класс здесь был бы хуже, чем класс компонента, который этот абзац и рисует.
- **Адрес массового действия записан двойными кавычками** (`action="/groups/bulk"`), хотя Jinja принял бы любые: маршрут — контракт с обработчиком и обязан читаться грепом по файлу раздела, а не только по отрендеренной странице. Тот же приём, что у `method="post"` в Плане 11.
- **Отвязанное расписание (issue #35) обслуживается той же панелью.** Поясняющий текст берётся из названия объявления, которое есть всегда; отдельной ветки под запись без типа мессенджера не заведено.
- **Порядок Задачи 3 соблюдён буквально:** сначала два триггера (архитектурная половина, `test_ads_delete_form_degrades_without_alpine` и `test_admin_user_delete_form_degrades_without_alpine` позеленели до того, как была проставлена первая подпись), затем подписи.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Критерий `grep -c 'data-area="meta"'` невыполним по построению и заменён проверкой ключевого аргумента**

- **Найдено при:** Задаче 2, сверке критериев приёмки
- **Проблема:** Критерий требует `grep -c 'data-area="meta"' app/templates/schedules/includes/schedule_row.html` >= 1. Литерала `data-area="meta"` в шаблоне раздела нет и до правки не было: атрибут пишет макрос ячейки (`components/table.html:45`), а раздел передаёт ему ключевой аргумент `area='meta'`. Выполнить критерий буквально можно было бы только дописав атрибут руками в обход макроса — то есть нарушив правило «планы разделов макросы только ВЫЗЫВАЮТ и своих признаков не пишут» ради зелёного грепа. Тот же класс расхождения план сам назвал для объявлений («адрес панели приходит выражением Jinja»).
- **Исправление:** Свойство, которое критерий охраняет («признак области сетки не потерян, подпись добавлена К нему, а не вместо»), закреплено тестом `test_schedules_row_keeps_grid_area_marker`: `source.count("area='meta'") == 1`. Проверяется ровно то же — что ячейка следующего запуска сохранила признак области, — но по тому носителю, который в файле действительно есть. Ослабления нет: до правки ключевой аргумент стоял один раз, после правки стоит один раз, потеря или задвоение роняют тест.
- **Файлы:** `tests/test_pages/test_responsive_markup.py`
- **Проверка:** `grep -c "area='meta'"` → 1; тест зелёный; рендер `/schedules` по-прежнему несёт `data-area="meta"` (`test_schedules_card_renders_data` и медиазапросные тесты прошли без правок)
- **Коммит:** `922b504` (тест), `6992bd2` (правка шаблона)

**2. [Rule 1 - Bug] Комментарий цитировал литерал, по которому идёт критерий приёмки**

- **Найдено при:** Задаче 3, сверке критериев после GREEN
- **Проблема:** Критерий `grep -c 'type="button"' app/templates/ads/includes/ad_card.html` == 0 дал **1**. Разметка была исправна: единственное вхождение осталось в комментарии, который объяснял, ЧЕМ триггер перестал быть («а не кнопка `type="button"`»). Критерий при этом не бессмысленный и ослаблять его нельзя — он ловит возврат кнопки вне формы. Проблема в комментарии: пояснение, цитирующее запрещённый литерал, делает греп-критерий вечно красным и подталкивает следующего исполнителя ослабить проверку вместо правки текста.
- **Исправление:** Формулировка во всех четырёх комментариях (`ad_card`, `admin/user_detail`, `group_row`, `schedule_row`) переведена на «кнопка-триггер вне формы» — смысл сохранён дословно, литерал ушёл. Правка комментариев в `group_row.html` и `schedule_row.html` затрагивает уже закоммиченные Задачами 1-2 файлы и внесена ради единообразия формулировки; разметка в них не менялась.
- **Файлы:** `app/templates/ads/includes/ad_card.html`, `app/templates/admin/user_detail.html`, `app/templates/groups/includes/group_row.html`, `app/templates/schedules/includes/schedule_row.html`
- **Проверка:** `grep -c 'type="button"' app/templates/ads/includes/ad_card.html` → 0; полная суита 623 passed
- **Коммит:** `51ce011`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Оба обслуживают критерии самого плана и области не расширяют. Первый — расхождение между формулировкой критерия и устройством кодовой базы, закрытое проверкой того же свойства по существующему носителю. Второй — правка текста комментария, не разметки.

## Issues Encountered

**Базовая линия суиты — 606, а не 545.** Must-have плана называет «545 passed на базовой линии верификации». Фактический прогон в чистом worktree на базе `b76db2d` до единой правки: **606 passed, 0 failed** (4 мин 48 с). Число в плане взято из `01-VERIFICATION.md` и устарело — волны 01-06…01-11 после той верификации добавили тесты. Инвариант, который число охраняет («полная суита остаётся зелёной»), выполнен на каждом шаге:

| Точка | Прогон |
|---|---|
| База `b76db2d` | 606 passed |
| После Задачи 1 | 612 passed (+6) |
| После Задачи 2 | 617 passed (+5) |
| После Задачи 3 | 623 passed (+6) |

Ожидаемое число в плане не редактировалось: план — исторический документ, правильное место для актуальной базовой линии — этот SUMMARY.

**Пустой `SMTP_HOST` не понадобился.** Прогоны выполнялись в чистом worktree без `.env`, поэтому средовых падений полной суиты, описанных в `01-VERIFICATION.md`, не наблюдалось. Переменная в командах оставлена для совпадения с формулировкой плана.

**Тестов добавлено 17, а не 16.** Шестнадцать названы `<behavior>` плана дословно; семнадцатый — `test_schedules_row_keeps_grid_area_marker`, заменивший невыполнимый греп-критерий (деталь выше).

## Требования: почему REQUIREMENTS.md не тронут

`UI-04` и `UI-06` объявлены двенадцатью планами фазы, включая ещё не выполненный 01-13. Правило общего идентификатора (#2388) запрещает помечать такой ID выполненным, пока не завершился ПОСЛЕДНИЙ объявивший его план. Готовое подмножество пустое, поэтому `REQUIREMENTS.md` не изменялся. То же решение принято Планами 09 и 11.

`STATE.md` и `ROADMAP.md` не изменялись по построению: план выполнялся в worktree, и общие артефакты пишет оркестратор после слияния волны.

## Known Stubs

Отсутствуют. Заглушек, пустых значений, ведущих в разметку, и маркеров долга (`TODO`, `FIXME`, `TBD`) в изменённых файлах не появилось. Состав выводимых данных не изменился ни на одно значение ни в одном из семи шаблонов: разделы сменили способ подтверждения и получили подписи колонок, но не новые поля — это закреплено тем, что `test_groups_card_renders_data`, `test_schedules_card_renders_data`, `test_ads_card_renders_data`, `test_dashboard_no_utility_classes`, `test_admin_users_renders_data` и `test_admin_user_detail_renders_data` прошли без единой правки.

Единственный пустой контейнер разметки — `<span id="groups-bulk-del-ids"></span>` — заглушкой не является: он пуст по построению и наполняется снимком набора в момент вопроса; его пустота на первичной отрисовке и есть правильное состояние.

## Threat Flags

Новой security-релевантной поверхности не добавлено. Диспозиции `mitigate` из `<threat_model>` выполнены:

| Threat ID | Как закрыт |
|---|---|
| T-12-01 | Отметки читаются один раз, снимок кладётся скрытыми полями в форму панели до открытия вопроса, отправляется эта же форма; `test_groups_bulk_modal_confirms_exact_set` держит порядок операций по исходнику, `test_groups_bulk_delete_uses_modal` — состав формы по выдаче |
| T-12-02 | Название группы уходит в `body` параметром макроса и выводится обычным экранированным выводом; `\|safe` не появилось, сплошной запрет Плана 02 действует |
| T-12-03 | Маршруты, методы и серверные проверки не тронуты; `test_groups_toggle_route_unchanged`, `test_schedules_toggle_route_unchanged`, `test_ads_delete_route_unchanged`, `test_admin_detail_denied_for_regular_user`, `test_admin_denied_for_regular_user` — все зелёные без правок |
| T-12-04 | Настоящая форма во всех тринадцати строчных удалениях, включая два прежних места; четыре теста `*_degrades_without_alpine` (аккаунты, группы, расписания, объявления, карточка пользователя — пять) |
| T-12-05 | Начальный фокус на отказе живёт в макросе (`x-ref="cancel"`), макрос не менялся; слот полей его не сдвигает (контракт Плана 09). Поведение в рантайме — открытое допущение D8 |
| T-12-06 | Состав полей в обеих админских страницах не расширен; подпись дублирует название из шапки. `test_admin_users_shows_no_extra_personal_data`, `test_admin_user_detail_shows_no_extra_personal_data` — зелёные без правок |
| T-12-07 | Узлы создаются `createElement` и заполняются присваиванием свойств; `innerHTML` в клиентском коде раздела отсутствует — закреплено `test_groups_bulk_modal_confirms_exact_set` |
| T-12-08 | Правка ушла в макросы; сентинелы и партиалы прокрутки не тронуты — пустой diff по шести файлам, `test_htmx_preserved.py` и `test_groups_filters_survive_pagination` зелёные |
| T-12-SC | Пакеты не устанавливались, новых зависимостей нет |

## User Setup Required

None — внешней конфигурации не требуется.

## Next Phase Readiness

- **Готово для Плана 13.** Прямой счёт мест подтверждения равен **14** (`grep -ro 'modal-open-' … | wc -l`), из них **13** строчных удалений в **семи** шаблонах — ровно тот перечень, который План 13 объявляет в `test_every_row_delete_site_keeps_a_real_form`: `accounts/list.html` (3), `accounts/partial_cards.html` (3), `accounts/partials/sync_status_card.html` (3), `groups/includes/group_row.html` (1), `schedules/includes/schedule_row.html` (1), `ads/includes/ad_card.html` (1), `admin/user_detail.html` (1).
- **Регистр метода различается по разделам:** в трёх файлах «Аккаунтов» — `method="POST"`, в строках групп, расписаний, объявлений и на карточке пользователя — `method="post"`. Сравнение метода в сетке Плана 13 обязано быть регистронезависимым, иначе перечень покраснеет на разнице регистра, а не на потере формы. (План 13 это уже предусматривает.)
- **Единственный встроенный обработчик отправки в проекте** — `accounts/connect_max.html:34`, защита от двойного нажатия. Диалога он не содержит; ожидание Плана 13 подтверждено грепом.
- **Единственная кнопка действия вне формы** — две кнопки массовых действий в `groups/list.html`. Это сознательное решение этого плана (массовые действия и до правки требовали скрипта), и оно обязано быть положительным утверждением сетки Плана 13, а не невысказанной поправкой.
- **Открытое допущение (не блокер):** поведение панели в рантайме и вид строки-карточки на 375px программно не проверяются. Ручная проверка `<human-check>` всех трёх задач в этом прогоне НЕ выполнялась: автономный исполнитель браузера не имеет. Уместно закрыть на `/gsd-verify-work` фазы. Расширение применения панели с 11 мест до 14 умножает эту непроверенную поверхность.
- **graphify:** `graphify-out/` в этом worktree отсутствует (не отслеживается git), поэтому `graphify update .` не выполнялся. Обновление графа уместно после слияния ветки в основную рабочую копию.

## Self-Check: PASSED

**Файлы на диске:**
- `app/templates/groups/includes/group_row.html` — FOUND (`modal-open-group-del-` ×1, `components/modal.html` ×1, `label=GROUP_COLUMNS[` ×5, `confirm(` ×0, `onsubmit` ×0)
- `app/templates/groups/list.html` — FOUND (`groups-bulk-del` в 6 строках, `action="/groups/bulk"` ×1, `createElement` ×4, `textContent` ×2, `confirm(` ×0)
- `app/templates/schedules/includes/schedule_row.html` — FOUND (`modal-open-schedule-del-` ×1, `components/modal.html` ×1, `label=SCHEDULE_COLUMNS[` ×5, `area='meta'` ×1, `confirm(` ×0, `onsubmit` ×0)
- `app/templates/ads/includes/ad_card.html` — FOUND (`label=AD_COLUMNS[` ×5, `data-cell-label` ×0, `type="button"` ×0, `action="/ads/` ×1, `modal-open-ad-del-` ×1)
- `app/templates/dashboard/includes/recent_send_card.html` — FOUND (`label=RECENT_COLUMNS[` ×3)
- `app/templates/admin/users.html` — FOUND (`label=USER_COLUMNS[` ×3)
- `app/templates/admin/user_detail.html` — FOUND (`label=ACC_COLUMNS[` ×1, `action="/admin/users/` ×4, `modal-open-user-del-` ×1)
- `tests/test_pages/test_responsive_markup.py` — FOUND (17 новых тестов, 91 passed в файле)

**Коммиты в истории:** `932fc29`, `6df87e6`, `922b504`, `6992bd2`, `29783e7`, `51ce011` — все шесть присутствуют.

**Проверка плана (`<verification>`) перепрогнана:**

| # | Команда | Результат |
|---|---|---|
| 1 | `pytest tests/test_pages/test_responsive_markup.py -x -q` | 91 passed |
| 2 | `pytest tests/test_pages/test_htmx_preserved.py -q` | зелёный (в составе `tests/test_pages/`) |
| 3 | `pytest tests/test_routes/test_groups_bulk.py -q` | зелёный |
| 4 | `pytest tests/test_pages/ -q` | 210 passed |
| 5 | `pytest tests/ -q` (= `just test`) | **623 passed** |
| 6 | Ручная проверка панелей, массового удаления трёх групп и карточек на 375px | НЕ выполнена — см. Next Phase Readiness |

**Критерии приёмки всех трёх задач перепрогнаны — все PASS**, кроме `grep -c 'data-area="meta"'` (заменён, деталь в «Deviations») и пунктов `<human-check>`, отмеченных выше как невыполненные.

---
*Phase: 01-interfeysnyy-fundament*
*Completed: 2026-08-09*
