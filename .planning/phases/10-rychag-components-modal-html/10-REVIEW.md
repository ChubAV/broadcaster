---
phase: 10-rychag-components-modal-html
reviewed: 2026-09-11T19:40:00Z
depth: standard
files_reviewed: 31
files_reviewed_list:
  - alembic/versions/0022_schedules_active_requires_next_run.py
  - app/models/schedule.py
  - app/pages/schedules.py
  - app/routes/schedules.py
  - app/services/schedule_rules.py
  - app/static/css/app.css
  - app/templates/ads/partials/sched_delete_response.html
  - app/templates/includes/htmx_error_banner.html
  - tests/test_application/test_send_analytics.py
  - tests/test_metrics.py
  - tests/test_migrations/test_0022_schedules_active_requires_next_run.py
  - tests/test_migrations/test_model_matches_head.py
  - tests/test_models/test_schedule.py
  - tests/test_models/test_schedule_active_requires_next_run.py
  - tests/test_models/test_send_log.py
  - tests/test_pages/test_account_groups.py
  - tests/test_pages/test_ads_status.py
  - tests/test_pages/test_confirm_delete_transport.py
  - tests/test_pages/test_editor_schedules.py
  - tests/test_pages/test_htmx_preserved.py
  - tests/test_pages/test_identifier_bounds.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_pages/test_schedule_ownership.py
  - tests/test_pages/test_schedules_list.py
  - tests/test_pages/test_schedules_poisoned_row.py
  - tests/test_pages/test_shell.py
  - tests/test_planning/test_the_walkthrough_stand_is_seedable.py
  - tests/test_routes/test_schedules_api_create_completeness.py
  - tests/test_routes/test_schedules_api_value_domain.py
  - tests/test_schedule_relationships.py
  - tests/test_templates/test_htmx_markup_gates.py
findings:
  critical: 1
  warning: 8
  info: 3
  total: 12
status: issues_found
---

# Фаза 10: отчёт ревизии кода

**Проверено:** 2026-09-11T19:40:00Z
**Глубина:** standard
**Файлов проверено:** 31
**Состояние:** issues_found

## Summary

Проверены два пласта: девять файлов четырёх новейших планов (10-48…10-51) и двадцать
два файла, изменившихся после предыдущего отчёта ревизии (`5832701`) — работа по
ограничению `ck_schedules_active_requires_next_run` и отладочный круг
`telegram-schedule-not-due`.

Качество ревизии `0022`, её тестового модуля и правил безусловности подъёма плашки —
высокое: границы названы, у правил есть отрицательные контроли, вакуумные зелёности
закрыты антивакуумными половинами. Прицельный прогон
(`tests/test_migrations tests/test_models tests/test_routes/test_schedules_api_* tests/test_schedule_relationships.py`)
— **294 passed**.

Тем не менее правка закрыла инвариант на входах создания и обновления и **оставила
открытым единственный вход, через который восстанавливают ровно те строки, которые
ревизия `0022` выключает**. Восстановительный путь, объявленный в шапке самой ревизии
(«человек дозаполняет расписание в редакторе, жмёт тумблер»), в половине «жмёт
тумблер» отвечает пятисоткой. Это воспроизведено исполнением, а не прочитано.

Сверх того: область значений закрыта на JSON-входе для дней и времён, но не для
идентификаторов того же входа — класс `CR-01` пятого круга (500 вместо 422) остаётся
открытым для `app/routes/`, и ни один гейт полноты его не видит: каталог
`test_identifier_bounds.py` разбирает только `app/pages/`.

## Structural Findings (fallow)

Структурный пре-проход к задаче не приложен — блок `<structural_findings>` в задании
отсутствует. Раздел оставлен пустым намеренно, чтобы отличать «структурного
субстрата не подавали» от «структурных находок нет».

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Тумблер на строке с днями вне диапазона роняет ответ пятисоткой — и это ровно тот класс строк, который выключает ревизия 0022

**Файлы:**
`app/pages/schedules.py:1086-1095`, `app/routes/schedules.py:424-436`
(тот же непокрытый вид — `app/routes/schedules.py:352-360`, ветка `elif schedule.is_active:`)

**Проблема.**
Оба тумблера включают расписание БЕЗУСЛОВНО, а `next_run_at` считают ПОСЛЕ:

```python
schedule.is_active = not schedule.is_active
if schedule.is_active:
    schedule.next_run_at = compute_next_run_at(...)   # ← может вернуть None
...
await db.commit()                                     # ← CHECK падает здесь
```

`compute_next_run_at` возвращает `None` не только на пустых списках. На НЕПУСТОМ
списке дней вне `0..6` кандидатов в окне `day_offset 0..7` не находится вовсе — это
названо прямо и самим планом (`app/routes/schedules.py:230-247`), и правилом
`test_completeness_implies_a_computable_next_run`, которое честно ограничено ОБЛАСТЬЮ
ЗНАЧЕНИЙ. Но входная отсечка стои́т только на создании и обновлении; ТУМБЛЕР читает
`days_of_week` из УЖЕ СОХРАНЁННОЙ строки и не отсекает ничего.

`is_schedule_complete([9], ["10:00"])` → `True` (список непуст), значит ни страничный
`resume_blocked`, ни `HTTP 400` JSON-входа не срабатывают. Получается
`is_active = True` при `next_run_at = NULL` — пара, которую ревизия `0022` запрещает
в схеме. `db.commit()` поднимает `IntegrityError`, её ловит только общий
`@app.exception_handler(Exception)` (`app/main.py:248`), и человек получает 500.

**Воспроизведено исполнением** (не прочитано):

```
complete? True
next_run: None
COMMIT FAILED: IntegrityError (sqlite3.IntegrityError)
  CHECK constraint failed: ck_schedules_active_requires_next_run
[SQL: UPDATE schedules SET is_active=? WHERE schedules.id = ?]
```

**Почему это блокер, а не предупреждение.** Достижимость не гипотетическая: форма
мёртвой строки `sched=48` по разбору самого проекта родилась ИМЕННО из дня вне
диапазона на JSON-входе. Ревизия `0022` такие строки ВЫКЛЮЧАЕТ, а `days_of_week` и
`times_of_day` НЕ ТРОГАЕТ — это записано её продуктовым решением. То есть после наката
на бою лежат выключенные строки с днями вне диапазона, и единственное действие,
которым владелец попробует их вернуть, — тумблер карточки — отвечает пятисоткой. До
`0022` то же действие тихо писало мёртвую строку; после `0022` оно отказывает громко,
но БЕЗ объяснения и БЕЗ пути восстановления. Ни одно правило суиты этого не ловит:
прицельный прогон 294 теста зелёный.

Тот же непокрытый вид у `update_schedule` (`app/routes/schedules.py:352-360`): патч,
не трогающий `days_of_week`, на строке с испорченными днями и `is_active=True` уходит
в тот же `IntegrityError`.

**Fix.** Считать момент ДО смены состояния и отказывать по ОТСУТСТВИЮ момента, а не
по пустоте списков:

```python
# app/routes/schedules.py — toggle_schedule
if not schedule.is_active:
    if not is_schedule_complete(...):
        raise HTTPException(400, detail="Сначала дозаполните расписание в редакторе объявления")
    next_run = compute_next_run_at(
        days_of_week=schedule.days_of_week,
        times_of_day=schedule.times_of_day,
        tz_name=schedule.timezone,
    )
    if next_run is None:
        # Полное по составу, но неисполнимое по значениям: дни/времена вне
        # области. Строка остаётся выключенной — состояние не портится.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Значения дней или времён расписания вне допустимой области — "
                   "откройте расписание в редакторе и сохраните заново",
        )
    schedule.is_active = True
    schedule.next_run_at = next_run
else:
    schedule.is_active = False
    schedule.next_run_at = None
```

Зеркальная правка — в `app/pages/schedules.py:1086-1095` (с плашкой через
`notices`, а не `HTTPException`) и в `update_schedule`. К правке обязано прийти
правило, сеющее строку с `days_of_week=[9]` и требующее от тумблера ОТКАЗА, а не
пятисотки; сегодня такого правила нет ни одного.

Отдельно стои́т рассмотреть разовую ревизию данных (или расширение `0022`),
приводящую `days_of_week`/`times_of_day` к области значений: без неё ограничение
стои́т над данными, которые его нарушат при первом же включении (см. WR-06).

## Warnings

### WR-01: `_clean_times` сверяет обрезанное значение, а СОХРАНЯЕТ необрезанное

**Файлы:** `app/pages/schedules.py:228`, `app/services/schedule_rules.py:70-84`,
`app/templates/ads/includes/sched_card.html:235`

**Проблема.**

```python
return [v for v in values if isinstance(v, str) and is_valid_time_of_day(v.strip())]
```

Проверяется `v.strip()`, в список попадает `v`. Значение `" 09:00 "` проходит и
ложится в `times_of_day` С ПРОБЕЛАМИ. Дальше оно печатается в разметку как есть —
`<input class="time-pill__input" type="time" value=" 09:00 ">`, — а `type="time"` с
пробелами значение не принимает: поле в редакторе показывается ПУСТЫМ, и при
следующем сохранении время молча теряется. `compute_next_run_at` при этом отработает
(`int(" 09")` пробелы терпит), поэтому расхождение не поднимет ни одного признака.

Это прямо противоречит договору, записанному у `is_valid_time_of_day`: «обрезку делает
вызывающий, если ему это нужно». Вызывающий обрезку ДЕЛАЕТ — но только для ответа
«годится ли», и не применяет её к тому, что сохраняет. Сверх того рождаются два
написания одного времени, которых `TIME_OF_DAY_RE` как раз и избегает требованием
двух цифр часа.

**Fix.**

```python
def _clean_times(values: list[str]) -> list[str]:
    cleaned = []
    for v in values:
        if not isinstance(v, str):
            continue
        trimmed = v.strip()
        if is_valid_time_of_day(trimmed):
            cleaned.append(trimmed)   # сохраняется ТО, что проверено
    return cleaned
```

### WR-02: на JSON-входе расписаний закрыта область значений дней и времён, но не ВЕЛИЧИНА идентификаторов — 500 вместо 422

**Файл:** `app/routes/schedules.py:92-94`, `:118`, `:310`, `:371`, `:387`

**Проблема.** План закрыл `days_of_week`/`times_of_day` валидаторами, а
`ad_id: int`, `account_id: int`, `group_ids: list[int]` и путевой `schedule_id: int`
остались без верхней границы. Величина за пределами колонки уезжает операндом
сравнения по ней:

```
Ad.id == 99999999999999999999999999     -> OverflowError: Python int too large to convert to SQLite INTEGER
Group.id.in_([99999999999999999999999999]) -> OverflowError: то же
```

(замер исполнением; на PostgreSQL это `DataError` вне диапазона `int32` — так же
записано в `app/pages/identifiers.py`). Итог — HTTP 500 на форменный запрос
аутентифицированного пользователя, то есть ровно тот класс `CR-01` пятого круга,
ради которого заведён `ID_MAX`.

Гейт полноты его не видит по построению: `test_identifier_bounds.py` собирает
вселенную из `app/pages/` (`_catalogue_sources`), и `app/routes/` во вселенную не
входит НИ ОДНИМ входом. То есть поверхность закрыта там, куда смотрит гейт, и
открыта там, куда он не смотрит, — повторение той самой ошибки, которую летопись
`ID_MAX` описывает как причину переезда константы.

**Fix.** Ввезти границу в схемы и сигнатуры JSON-входа:

```python
from pydantic import Field
from app.pages.identifiers import ID_MAX   # либо вынести ID_MAX в нейтральный app/constants.py

class CreateScheduleRequest(BaseModel):
    ad_id: int = Field(ge=1, le=ID_MAX)
    account_id: int = Field(ge=1, le=ID_MAX)
    group_ids: list[int] = Field(default_factory=list)   # + валидатор на элементы

async def toggle_schedule(schedule_id: int = Path(ge=1, le=ID_MAX), ...)
```

и расширить вселенную гейта каталога на `app/routes/` (либо завести второй гейт с
явно названной границей вселенной, как это уже сделано для админки).

### WR-03: «unscheduled»-половина правила `upcoming_sends` стала копией «inactive»-половины — имя обещает покрытие, которого больше нет

**Файл:** `tests/test_application/test_send_analytics.py:1057-1093`

**Проблема.** Второй случай `test_upcoming_sends_skips_inactive_and_unscheduled`
теперь сеет строку `is_active=False, next_run_at=None` — то есть ВТОРУЮ выключенную
строку. Первый случай — тоже выключенная. Условие `Schedule.next_run_at.isnot(None)`
(`app/application/analytics/send_analytics.py:581`), ради которого половина и
существовала, стало неисполнимым через базу, и докстринг это честно признаёт. Но имя
правила осталось прежним, а условие в продукте — незакрытым ни одним замером:
удалившего его завтра не покраснит ничто.

**Fix.** Развести предметы: половину «выключенное» оставить здесь, а условие
`isnot(None)` закрыть на уровне ЗАПРОСА, минуя ORM-ограничение, — например
`sa.text("INSERT INTO schedules …")` с временно снятым CHECK на SQLite, либо
прямым юнит-правилом на скомпилированный `WHERE` (`str(stmt.compile())` содержит
`next_run_at IS NOT NULL`). Если ни то ни другое не принимается — переименовать
правило в `test_upcoming_sends_skips_both_paused_shapes` и записать снятое условие
отдельной строкой реестра открытых окон.

### WR-04: `exec()` кода из `.planning/*.md`, и объявленная граница пространства имён неверна

**Файл:** `tests/test_planning/test_the_walkthrough_stand_is_seedable.py:200-212`

**Проблема.** Модуль исполняет узел цикла, вынутый регулярками из `10-UAT.md`.
Шапка утверждает: «Выдаются РОВНО ЧЕТЫРЕ имени и ничего сверх». Это неверно:
`exec(code, namespace)` при отсутствии ключа `__builtins__` в словаре ПОДСТАВЛЯЕТ
настоящий модуль встроенных имён. Тело цикла в артефакте имеет полный доступ к
`__import__`, `open`, `eval` и через них ко всему интерпретатору и файловой системе
прогона. Граница, названная «несущей» и «держащейся сборкой, а не комментарием»,
фактически не поставлена.

Достижимость сегодня низкая (артефакт лежит в том же дереве и проходит ту же
ревизию, что исходники), поэтому это WARNING, а не BLOCKER. Но запись, описывающая
границу ШИРЕ факта, — ровно тот класс, который проект в других местах помечает
опровергнутым.

**Fix.** Закрыть пространство имён явно и поправить шапку:

```python
namespace = {
    "__builtins__": {},          # либо узкий словарь разрешённых имён
    "Schedule": Schedule,
    "compute_next_run_at": compute_next_run_at,
    "ad": SimpleNamespace(id=ad_id),
    "acc": SimpleNamespace(id=account_id),
    "s": _Sink(),
}
```

и добавить контроль-зуб: доктóренная копия раздела с `__import__('os')` в теле цикла
обязана краснеть `NameError`, а не исполняться.

### WR-05: четвёртый внеполосный узел удваивает известное расхождение «число чужого объявления в чужом документе»

**Файлы:** `app/pages/schedules.py:1140-1146`, `:1341-1361`,
`app/templates/ads/partials/sched_delete_response.html:134`, `:143`

**Проблема.** Цели `#sched-count` и `#ad-summary` адресованы СТАТИЧЕСКИ, а числа
считаются по `ad_id`, снятому с НАЙДЕННОЙ строки (либо с поля формы). Запрос,
называющий адресом расписание объявления B, а полем контекста — экран объявления A,
ставит в документ A числа объявления B. До плана 10-50 так уезжало одно число
(линейка); теперь уезжают ТРИ — линейка, «Расписания» сводки и «Ближайший запуск», —
и все они переживают запрос до перезагрузки.

Границы привилегий это не пересекает (обе выборки скоуплены `Ad.user_id`), и решение
отложить правку записано владельцем. Претензия ревизии к другому: расхождение
РАСШИРЕНО новым планом, а зелёное правило
`test_the_counter_node_belongs_to_the_ad_named_by_the_request`
(`tests/test_pages/test_confirm_delete_transport.py`) утверждает сегодняшнее
поведение НОРМОЙ. Правило, закрепляющее известный дефект как норму, при следующей
попытке починки покраснеет и будет прочитано как регресс.

**Fix.** Либо адресовать узлы по объявлению (`hx-swap-oob="innerHTML:#sched-count-{{ ad.id }}"`
и `id="ad-summary-{{ ad.id }}"`), либо — минимум до правки — переименовать правило в
`test_the_counter_node_is_characterised_as_belonging_to_the_ad_named_by_the_request`
и пометить его характеризующим (`pytest.mark.characterisation`), чтобы зелёный цвет
не читался как утверждение о ПРАВИЛЬНОСТИ.

### WR-06: ревизия 0022 запрещает состояние, но не чинит данные, которые его порождают

**Файл:** `alembic/versions/0022_schedules_active_requires_next_run.py:192-210`

**Проблема.** Накат выключает нарушителей и — по записанному решению — не трогает
`days_of_week`/`times_of_day`. Решение обосновано («угадать задуманные дни —
фабрикация»), и с этим спорить нечего. Но следствие названо неполно: после наката
остаются строки, ПОЛНЫЕ по `is_schedule_complete` и НЕИСПОЛНИМЫЕ по значениям, и
единственный интерфейсный путь к ним — тумблер — отвечает пятисоткой (CR-01). То
есть выключение не есть «точка восстановления», как утверждает шапка, пока тумблер
не научится отказывать по отсутствию момента.

**Fix.** Либо закрыть CR-01 (тогда шапку дополнить: восстановление идёт ЧЕРЕЗ
редактор, а тумблер на непочиненной строке отказывает объяснимо), либо добавить в
`upgrade()` второй замер — сколько выключенных строк несут дни вне `0..6` — и
записать это число в тот же журнал наката, рядом с числом выключенных. Число в
журнале превращает «неизвестно, сколько таких строк» в замер, а сегодня владелец
после наката не узнает этого ниоткуда.

### WR-07: удаление коммитится ДО чтения тела формы

**Файл:** `app/pages/schedules.py:1141-1149`

**Проблема.**

```python
if schedule:
    await db.delete(schedule)
    await db.commit()
form_data = await request.form()
```

`await request.form()` — единственное место, где тело запроса разбирается, и оно
может поднять исключение (обрыв тела, негодный `multipart`, превышение лимита
частей). К этому моменту удаление УЖЕ зафиксировано: человек получит 500, а строки
не будет. Ветка отказа при этом неотличима от «ничего не произошло».

**Fix.** Читать форму сразу после сверки источника, до выборки и удаления:

```python
if not is_same_origin(request):
    return Response(status_code=403)
form_data = await request.form()          # тело разобрано ДО записи
result = await db.execute(select(Schedule)...)
```

Порядок «сверка источника → разбор тела → запись» заодно снимает вопрос о том,
читается ли тело у отвергнутого по происхождению запроса.

### WR-08: жёсткая дата `datetime(2026, 9, 12, 6, 0)` размножена по девяти тестовым модулям

**Файлы:** `tests/test_metrics.py:66`, `tests/test_models/test_send_log.py:59`, `:140`,
`tests/test_pages/test_account_groups.py:159`, `:1114`,
`tests/test_pages/test_ads_status.py:82`, `tests/test_pages/test_htmx_preserved.py:143`,
`tests/test_pages/test_responsive_markup.py:137`, `:676`, `:4575`,
`tests/test_pages/test_schedule_ownership.py:75`, `tests/test_pages/test_schedules_list.py:122`,
`tests/test_pages/test_schedules_poisoned_row.py:99`, `tests/test_schedule_relationships.py:39`

**Проблема.** Один и тот же литерал вписан четырнадцать раз без имени. Дата стои́т
на СУТКИ позже дня правки и уже завтра станет прошлым. Части продукта относительны
к «сейчас»: `app/application/admin/incidents.py:666-669` считает ПРОСРОЧЕННЫМИ строки
с `next_run_at < beat_cutoff`, `upcoming_sends` сортирует по тому же полю. Сегодня
фикстуры означают «будущий слот», завтра — «просроченный». Ни один из этих модулей
на этом не краснеет ПОКА, но смысл фикстуры меняется молча, а молча меняющаяся
фикстура — это отложенный ложный зелёный или ложный красный.

**Fix.** Один общий помощник в `tests/conftest.py`, относительный к «сейчас», и
имя, которое называет предмет:

```python
def a_future_run_moment(days: int = 1) -> datetime:
    """Момент запуска, который ОСТАЁТСЯ будущим при любом дне прогона."""
    return datetime.now(timezone.utc) + timedelta(days=days)
```

## Info

### IN-01: `OOB_BLOCKS = 9` → `13` — число выросло на четыре одной правкой

**Файл:** `tests/test_templates/test_htmx_markup_gates.py`

Инвентарь внеполосных блоков поднят числом без разбивки «какие именно четыре файла
добавились». Перечень в правиле есть, но диффом видно только число. Предложение:
печатать в отказе РАЗНИЦУ множеств (какие файлы пришли, какие ушли), а не только
два числа, — тогда следующий сдвиг читается без раскопок истории.

### IN-02: успешный ФОНОВЫЙ обмен гасит непрочитанный настоящий отказ

**Файл:** `app/templates/includes/htmx_error_banner.html:227-233`

Третий обработчик гасит обе заготовки по признаку успеха ЛЮБОГО обмена — включая
сентинель подгрузки, автосохранение и опрос. Цена названа в докстринге прямо и
принята владельцем; здесь она отмечается лишь как незакрытое ничем машинным окно:
суита JS не исполняет в браузере, и наблюдаемо оно только рантаймом. Кандидат в
реестр окон, если ещё не записан.

### IN-03: две заготовки плашки накрывают друг друга при одновременном показе

**Файл:** `app/static/css/app.css:1188-1198`

`#htmx-failure-server` и `#htmx-failure-network` объявлены одним блоком с общими
`top: 12px` и `z-index: 70`: показанные одновременно, они встают в одну точку, и
вторая закрывает первую. Названо самим блоком как `T-10-51-04` / `accept`; отмечено
здесь, чтобы находка не потерялась между кругами. Дешёвое закрытие — сместить второй
на высоту первого (`#htmx-failure-network { top: 84px; }`) либо собрать обе в один
стек-контейнер.

---

_Reviewed: 2026-09-11T19:40:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
