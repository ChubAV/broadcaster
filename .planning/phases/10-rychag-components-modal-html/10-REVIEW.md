---
phase: 10-rychag-components-modal-html
reviewed: 2026-09-12T09:40:00Z
depth: standard
files_reviewed: 26
files_reviewed_list:
  - alembic/versions/0022_schedules_active_requires_next_run.py
  - app/pages/identifiers.py
  - app/pages/notices.py
  - app/pages/schedules.py
  - app/routes/schedules.py
  - tests/conftest.py
  - tests/test_application/test_send_analytics.py
  - tests/test_metrics.py
  - tests/test_models/test_schedule.py
  - tests/test_models/test_send_log.py
  - tests/test_pages/test_account_groups.py
  - tests/test_pages/test_ads_status.py
  - tests/test_pages/test_confirm_delete_transport.py
  - tests/test_pages/test_editor_schedules.py
  - tests/test_pages/test_htmx_preserved.py
  - tests/test_pages/test_identifier_bounds.py
  - tests/test_pages/test_notices_registry.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_pages/test_schedule_ownership.py
  - tests/test_pages/test_schedules_list.py
  - tests/test_pages/test_schedules_poisoned_row.py
  - tests/test_planning/test_the_walkthrough_stand_is_seedable.py
  - tests/test_routes/test_schedules_api_identifier_bounds.py
  - tests/test_schedule_relationships.py
  - tests/test_schedules_out_of_domain_resume.py
  - tests/test_templates/test_components.py
findings:
  critical: 1
  warning: 6
  info: 5
  total: 12
status: issues_found
---

# Фаза 10: отчёт ревизии кода (круг седьмой, инкрементальный)

**Проверено:** 2026-09-12T09:40:00Z
**Глубина:** standard
**Файлов проверено:** 26
**Состояние:** issues_found

## Summary

Предмет круга — то, что изменилось ПОСЛЕ коммита ревизии `255b5da`: девять правок
находок прошлого отчёта (`aa516a2`, `0094e3d`, `a16fb43`, `d5c023d`, `8e85f83`,
`68244dd`, `3616321`, `0f766f2`, `ae11338`) и четыре плана десятой партии
(10-52…10-54).

**Проверка прошлых находок — все девять закрыты по предмету.**

| находка | закрыта | замер |
|---|---|---|
| CR-01 (тумблер роняет 500) | частично — см. `CR-01` ниже | оба тумблера и `update_schedule` считают момент ДО смены состояния; `tests/test_schedules_out_of_domain_resume.py` — 6 passed |
| WR-01 `_clean_times` | да | сохраняется `trimmed`, правило `test_a_time_padded_with_spaces_is_stored_trimmed` зелено |
| WR-02 величина идентификаторов | да, но гейт без зубов — см. `WR-01` ниже | `BoundedId`/`IdPath` на всех пяти входах; 19 правил нового модуля зелены |
| WR-03 `isnot(None)` | да | заведено `test_upcoming_sends_skips_the_shape_the_schema_now_forbids`, сеющее запрещённую пару в обход CHECK |
| WR-04 `exec` | да | `__builtins__` подаётся явно, контроль-зуб требует `NameError` — 6 passed |
| WR-05 характеризующее правило | да | переименовано + `pytest.mark.characterisation`, маркер зарегистрирован в `conftest` |
| WR-06 шапка `0022` | да | следствие решения названо целиком, назван и отсутствующий второй замер |
| WR-07 порядок разбора тела | да | `form()` стои́т выше `commit()`; правило на негодном `multipart` зелено |
| WR-08 жёсткая дата | да по предмету, с новой ценой — см. `WR-04` ниже | 21 вхождение заменено `a_future_run_moment()` в 13 модулях |

Прицельные прогоны (исполнением, не чтением):
`tests/test_schedules_out_of_domain_resume.py tests/test_routes/test_schedules_api_identifier_bounds.py tests/test_pages/test_notices_registry.py` — **39 passed**;
`tests/test_pages/test_editor_schedules.py tests/test_application/test_send_analytics.py` — **119 passed**;
`tests/test_metrics.py tests/test_models tests/test_schedule_relationships.py tests/test_pages/test_schedules_*.py tests/test_pages/test_schedule_ownership.py tests/test_pages/test_ads_status.py` — **124 passed**;
гейт критерия 3 (`-k "criterion_three or handler_registration or vendored_script"`) — **4 passed**;
`tests/test_planning/test_the_walkthrough_stand_is_seedable.py` — **6 passed**.

Зелень этих прогонов есть свидетельство В ПОЛЬЗУ блокера ниже, а не против него:
блокер живёт на классе входов, который ни одно правило суиты не сеет.

Главный итог круга: **правка `CR-01` закрыла ОДНУ из двух форм отказа расчёта.**
`compute_next_run_at` на испорченной СОХРАНЁННОЙ строке не только возвращает
`None` — она ещё и ПОДНИМАЕТ ИСКЛЮЧЕНИЕ на пяти замеренных формах значений, и
эта половина осталась незакрытой во всех трёх обработчиках, которые правка
трогала. Сверх того гейт полноты, заведённый правкой `WR-02`, ЗЕЛЁН ПРИ
ОБЕЗОРУЖЕННОМ РАЗБОРЩИКЕ — это измерено мутацией, а не предположено.

## Structural Findings (fallow)

Структурный пре-проход к задаче не приложен — блока `<structural_findings>` в
задании нет. Раздел оставлен пустым намеренно, чтобы отличать «структурного
субстрата не подавали» от «структурных находок нет».

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: правка закрыла `None`, но не ИСКЛЮЧЕНИЕ — те же три обработчика по-прежнему отвечают пятисоткой на испорченной сохранённой строке

**Файлы:**
`app/pages/schedules.py:1135-1148` (страничный тумблер),
`app/routes/schedules.py:494-514` (тумблер JSON-API),
`app/routes/schedules.py:392-412` (частичное обновление),
граница правила: `tests/test_schedules_out_of_domain_resume.py:26-30`

**Проблема.** Все три места правлены по одному образцу:

```python
next_run = compute_next_run_at(
    days_of_week=schedule.days_of_week,
    times_of_day=schedule.times_of_day,
    tz_name=schedule.timezone,
)
if next_run is None:        # ← закрыт РОВНО ОДИН исход
    raise HTTPException(400, ...)
```

Отказ опознаётся ТОЛЬКО по значению `None`. Но `compute_next_run_at`
(`app/services/schedule_service.py:25-28`) разбирает время
`time(int(parts[0]), int(parts[1]))` БЕЗ ЗАЩИТЫ, а зону — `ZoneInfo(tz_name)`
тоже без защиты. **Замер исполнением** (`uv run python`, дерево `ea410f4`):

```
[1] ['abc']    UTC          -> RAISES ValueError  invalid literal for int(): 'abc'
[1] ['25:00']  UTC          -> RAISES ValueError  hour must be in 0..23
[1] ['9']      UTC          -> RAISES IndexError  list index out of range
[1] [9]        UTC          -> RAISES AttributeError 'int' has no attribute 'split'
[1] ['10:00']  Mars/Phobos  -> RAISES ZoneInfoNotFoundError
['1'] ['10:00'] UTC         -> None          ← ЕДИНСТВЕННЫЙ закрытый правкой исход
```

То есть из шести замеренных форм испорченной сохранённой строки правка закрывает
ОДНУ. На остальных пяти исключение проходит мимо `if next_run is None`, уходит в
общий `@app.exception_handler(Exception)` (`app/main.py:248`) и даёт **HTTP 500
без объяснения и без пути восстановления** — дословно тот исход, который отчёт
прошлого круга назвал блокером, а шапка ревизии `0022`
(`alembic/versions/0022_schedules_active_requires_next_run.py:56-63`) теперь
объявляет ИСПРАВЛЕННЫМ: «Теперь оба тумблера и частичное обновление JSON-API
считают момент ДО смены состояния и отказывают ОБЪЯСНИМО». Утверждение шире
факта — ровно тот класс записи, который проект в других местах помечает
опровергнутым.

**Достижимость — названа честно, а не преувеличена.** Сегодняшние входы такую
строку РОДИТЬ не дают: страничный `_clean_times` отбрасывает негодное,
`_reject_malformed_times`/`validate_timezone` отвечают 422, а на создании расчёт
идёт ДО записи. Источники остаются ДВА, и оба названы самим проектом:

1. Шапка ревизии `0022:65-70` утверждает прямо, что колонка **законно содержит**
   «`null`, и элементы не-числа (строки, испорченные до фикса CR-03)», — и
   именно поэтому второй замер в накат не внесён. Если это верно для
   `days_of_week`, для `times_of_day` оно верно тем же основанием, а элемент
   не-строка в `times_of_day` даёт `AttributeError`, а не `None`.
2. Довод, которым обосновано само существование ограничения `0022:15-19`:
   «прямой psql, ручной UPDATE на бою, миграция данных и любой будущий восьмой
   писатель обходят все семь разом». Обработчик, доверяющий чистоте
   СОХРАНЁННЫХ значений, стоит на допущении, которое эта же ревизия объявляет
   несостоятельным.

Гейта на это нет: новый модуль `tests/test_schedules_out_of_domain_resume.py`
объявляет своей границей ровно `None`-исход («Предмет — ОТКАЗ ПО ОТСУТСТВИЮ
МОМЕНТА», `:26-30`), и ни одно из 3182 правил суиты не сеет строку с
испорченным ВРЕМЕНЕМ и не жмёт на ней тумблер.

**Fix.** Опознавать отказ расчёта ПО СОБЫТИЮ, а не по одному его значению, —
одним помощником на все три места:

```python
# app/services/schedule_rules.py (или рядом с compute_next_run_at)
def next_run_or_none(schedule) -> datetime | None:
    """Момент запуска сохранённой строки либо None, если ЗНАЧЕНИЯ неисполнимы.

    Исключение и пустой результат — ОДИН исход для вызывающего: строка
    неисполнима по значениям. Разделять их значило бы отдать ему разбор
    внутренностей вычислителя.
    """
    try:
        return compute_next_run_at(
            days_of_week=schedule.days_of_week or [],
            times_of_day=schedule.times_of_day or [],
            tz_name=schedule.timezone,
        )
    except (ValueError, TypeError, IndexError, AttributeError, ZoneInfoNotFoundError):
        return None
```

и во всех трёх обработчиках заменить прямой вызов на `next_run_or_none(schedule)`
(текст отказа и код ответа не меняются — исход для человека тот же).

К правке обязаны прийти правила, сеющие строку с `times_of_day=["abc"]`,
`["25:00"]` и `[9]` и требующие от ОБОИХ тумблеров и от `update_schedule`
ОТКАЗА, а не пятисотки; сегодня таких правил нет ни одного. Шапку `0022:56-63`
при этом надо привести к факту: сейчас она обещает больше, чем стои́т.

## Warnings

### WR-01: отрицательный контроль гейта границ ДУБЛИРУЕТ его логику вместо того, чтобы вызвать его, — гейт зелен при обезоруженном разборщике (ИЗМЕРЕНО)

**Файл:** `tests/test_routes/test_schedules_api_identifier_bounds.py:368-401`
(`_unbounded_identifiers`), `:420-434` (гейт), `:437-467` (контроль)

**Проблема.** Гейт полноты вызывает `_unbounded_identifiers()`. Контроль-зуб
`test_control_negative_the_catalogue_gate_reddens_on_a_bare_int` эту функцию **не
вызывает ни разу** — он собирает СВОЙ список нарушителей отдельным генератором,
повторяющим ветку (а) разборщика:

```python
offenders = [
    f"{node.name}.{statement.target.id}"
    for node in ast.walk(tree) ...          # ← копия логики, не вызов
]
assert "CreateScheduleRequest.ad_id" in offenders
```

Значит контроль доказывает зубы СВОЕЙ КОПИИ, а не гейта. **Замер мутацией**
(тело `_unbounded_identifiers` подменено на `return []`, модуль исполнен через
`ast`-подмену без правки дерева):

```
BOTH GREEN with _unbounded_identifiers disarmed
-> negative control has no teeth over the gate
```

То есть разборщик, переставший видеть что бы то ни было, оставляет **и гейт, и
его контроль зелёными**. Это ровно тот класс «зелёный по построению», против
которого контроль заведён, и он названо-обещанное свойство шапки модуля
(«Отказ ЛОВИТ НОВОЕ, а не подтверждает старое») не держит.

**Fix.** Подавать доктóренный источник САМОМУ разборщику, а не его копии:

```python
def _unbounded_identifiers(source: str | None = None) -> list[str]:
    tree = ast.parse(source if source is not None
                     else ROUTES_MODULE.read_text(encoding="utf-8"))
    ...

def test_control_negative_the_catalogue_gate_reddens_on_a_bare_int():
    doctored = ROUTES_MODULE.read_text(encoding="utf-8").replace(
        "    ad_id: BoundedId", "    ad_id: int", 1
    )
    assert doctored != ROUTES_MODULE.read_text(encoding="utf-8"), "доктóривание не сработало"
    assert "CreateScheduleRequest.ad_id" in _unbounded_identifiers(doctored)
    assert _unbounded_identifiers() == [], "боевой источник тронут контролем"
```

Тот же разбор приложúм к ветке (б) (параметры обработчиков): её сегодня не
покрывает НИ ОДИН контроль — удаление всей ветки `if isinstance(node, (ast.FunctionDef, …))`
не покраснит ничего.

### WR-02: текст отказа выписан ЛИТЕРАЛОМ дважды в одном файле, а третья его редакция живёт в закрытом реестре

**Файлы:** `app/routes/schedules.py:404-411` и `:505-512` (две дословные копии),
`app/pages/notices.py:233-240` (третья, ИНАЯ формулировка)

**Проблема.** Один исход — «полное по составу, неисполнимое по значениям» —
получил ТРИ независимых носителя слов:

```
routes:407-410  "Дни или часы расписания заданы значениями, которых система
                 исполнить не может — откройте расписание в редакторе
                 объявления и сохраните дни и время заново"
routes:508-511  ← ТОТ ЖЕ ТЕКСТ, выписанный второй раз
notices:235-239 "Дни или часы ЭТОГО расписания … Откройте расписание в редакторе
                 объявления, выберите дни и время заново и сохраните — после
                 этого включение сработает."
```

Это прямо противоречит доктрине, записанной в этих же файлах: `notices.py:1-8`
объявляет себя «единственным владельцем слов, которыми продукт сообщает
пользователю ИСХОД ЕГО ДЕЙСТВИЯ», а `routes/schedules.py:11-18` обосновывает
ввоз `ID_MAX` тем, что «вторая копия разошлась бы с первой молча при первой же
правке». Здесь копий три, две из них уже РАЗОШЛИСЬ (страничный человек и
JSON-клиент читают разные слова об одном исходе), и машинного сторожа нет:
единственная проверка — `assert "редактор" in response.json()["detail"].lower()`
(`tests/test_schedules_out_of_domain_resume.py:193`), которая переживёт любую
правку обеих копий.

**Fix.** Завести константу текста рядом с реестром и ввозить её обеими
сторонами, как уже сделано с `ID_MAX`:

```python
# app/pages/notices.py
SCHEDULE_VALUES_OUT_OF_DOMAIN_DETAIL = (
    "Дни или часы расписания заданы значениями, которых система исполнить "
    "не может — откройте расписание в редакторе объявления и сохраните дни "
    "и время заново"
)

# app/routes/schedules.py — оба места
from app.pages.notices import SCHEDULE_VALUES_OUT_OF_DOMAIN_DETAIL
raise HTTPException(400, detail=SCHEDULE_VALUES_OUT_OF_DOMAIN_DETAIL)
```

Если расхождение формулировок между слоями решено намеренно — оно обязано быть
ЗАПИСАНО решением и закреплено правилом, сверяющим обе строки посимвольно, как
это уже сделано гейтом переноса реестра.

### WR-03: отказ страничного тумблера теряет ИМЯ строки и разворот возврата — человек приходит в редактор, где неизвестно, какую карточку чинить

**Файлы:** `app/pages/schedules.py:1140-1148`, `:658-671`
(`_editor_error_redirect`), `:443-448` (`_editor_url`),
`app/templates/schedules/includes/schedule_row.html:81-86`

**Проблема.** Успешный тумблер возвращает человека через `_editor_redirect` →
`_editor_url(returns_to_editor, ad_id, schedule_id)`, то есть на
`/ads/{ad}/edit?sched={id}#sched-{id}` (карточка развёрнута, прокрутка доведена)
ЛИБО на `/schedules`, если признака возврата не было. Отказ идёт другим путём:

```python
return _editor_error_redirect(schedule.ad_id, notices.SCHEDULE_VALUES_OUT_OF_DOMAIN)
# -> "/ads/{ad_id}/edit?notice=..."   ← ни sched, ни якоря, ни признака возврата
```

Два следствия, и оба наблюдаемы:

1. **Плашка называет действие, которое адрес не поддерживает.** Текст реестра
   (`notices.py:235-239`) говорит «Откройте расписание в редакторе объявления,
   выберите дни и время заново». У объявления расписаний может быть несколько
   (`_ad_has_a_schedule`, сводка `#sched-count` считает их числом), а адрес
   отказа НЕ несёт `?sched={id}#sched-{id}` — человеку не сказано, какую из
   карточек он только что не смог включить.
2. **Разворот возврата игнорируется.** Форма тумблера на сводном списке
   (`schedule_row.html:81`) поля `return_to` не шлёт вовсе, поэтому успех
   возвращает человека на `/schedules`, а отказ уносит его на ЧУЖОЙ экран —
   редактор объявления. Смена экрана по отказу решением нигде не записана.

**Fix.** Собрать адрес отказа тем же кодом, что и адрес успеха, добавив к нему
код исхода:

```python
def _editor_error_redirect(ad_id: int, notice: str, schedule_id: int | None = None):
    url = _editor_url(returns_to_editor=True, ad_id=ad_id, schedule_id=schedule_id)
    sep = "&" if "?" in url else "?"
    return RedirectResponse(url=f"{url}{sep}notice={notice}", status_code=302)

# вызов тумблера
return _editor_error_redirect(
    schedule.ad_id, notices.SCHEDULE_VALUES_OUT_OF_DOMAIN, schedule_id
)
```

и дописать к правилу `test_page_toggle_refuses_a_row_whose_days_are_out_of_domain`
утверждение о присутствии `sched={id}` в `Location` — сегодня оно проверяет
только `notice=`.

### WR-04: `a_future_run_moment()` снял жёсткую дату, но заодно снял ВОСПРОИЗВОДИМОСТЬ, и один комментарий стал неверен на месте

**Файлы:** `tests/conftest.py:243-265`, `tests/test_metrics.py:54-69`,
`tests/test_pages/test_htmx_preserved.py:136-147`

**Проблема.** Помощник возвращает `datetime.now(timezone.utc) + timedelta(days=days)`
— значение, РАЗНОЕ при каждом вызове и при каждом прогоне. Предмет `WR-08`
(«фикстура, молча меняющая смысл») закрыт, но вместе с ним потеряны два свойства,
которых литерал не терял:

1. **Соседние строки перестали быть одинаковыми там, где это было предметом.**
   `tests/test_metrics.py:54-69` сеет три расписания в цикле, и комментарий прямо
   над полем утверждает: «разные значения у включённых и выключенной строк завели
   бы в этой фикстуре ВТОРОЕ различие сверх того одного, ради которого она и
   написана». После правки каждая из трёх строк получает СВОЙ момент (вызов на
   каждой итерации) — то есть комментарий описывает фикстуру, которой больше нет.
   Тот же вид у `test_htmx_preserved.py:136-147`, где список собирается
   генератором на `SEED_ROWS` строк.
2. **Отказ перестал воспроизводиться теми же данными.** Покрасневшее правило,
   чей посев зависит от часа и минуты прогона, разбирается уже не как дефект
   фикстуры — это дословно та цена, которую докстринг помощника назначает
   ЛИТЕРАЛУ. Открытое окно 79 журнала `.planning/WINDOWS.md` показывает, что
   недетерминированность по времени суток в этой суите — не гипотеза.

**Fix.** Развести два предмета, которые помощник сегодня смешивает:

```python
def a_future_run_moment(days: int = 1, *, shared: datetime | None = None) -> datetime:
    """…"""
    base = shared or datetime.now(timezone.utc)
    return base + timedelta(days=days)
```

и в местах, где ОДИНАКОВОСТЬ строк есть предмет фикстуры (`test_metrics.py`,
`test_htmx_preserved.py`), снять момент в имя ДО цикла и подать одно значение
всем строкам — ровно тем приёмом, который уже применён в
`test_editor_schedules.py:2856-2862` (`removed_run_at`). Комментарий
`test_metrics.py:63-67` привести к факту либо восстановить свойство, которое он
описывает.

### WR-05: `FAILURE_BANNER_HANDLERS_MEASURED` обслуживает ДВЕ РАЗНЫЕ величины — «единственный источник» связал несвязанное

**Файлы:** `tests/test_templates/test_components.py:4990-5028`
(`_declared_script_handler_registrations`), `tests/test_pages/test_shell.py:2308-2311`,
`:2596-2612`

**Проблема.** Константа объявлена и потребляется как ЧИСЛО РЕГИСТРАЦИЙ,
выполненных сценарием В РАНТАЙМЕ: `test_shell.py:2599` сверяет с ней результат
исполнения сценария в Node (`_failure_banner_registration_count(path, runs=1)`).
Новый гейт критерия 3 ввозит её же как ЧИСЛО ТЕКСТОВЫХ ВХОЖДЕНИЙ в телах
`<script>`, причём по ДВУМ формам сразу:

```python
HANDLER_REGISTRATION_FORMS = (
    re.compile(r"\.addEventListener\s*\("),
    re.compile(r"\.on[a-z]{2,}\s*=(?!=)"),   # ← этой формы понятие «замера» не знает
)
```

Сегодня обе величины равны трём, и совпадение выдано за единственность
источника. Но величины независимы по построению: регистрация в ЦИКЛЕ даёт одно
текстовое вхождение и три рантаймовых; присваивание `el.onclick = …` даёт
текстовое вхождение и НЕ участвует в замере `test_shell`. В день первого
расхождения правка константы под один модуль **покраснит другой** — и отказ
назовёт не тот предмет: `test_shell` скажет «сценарий вешает не то число
обработчиков», хотя изменилось только написание.

**Fix.** Объявить ДВА имени с разными предметами и назвать связь между ними
проверкой, а не общей константой:

```python
# tests/test_pages/test_shell.py
FAILURE_BANNER_HANDLERS_MEASURED = 3        # РАНТАЙМ: столько слушателей повисло
FAILURE_BANNER_REGISTRATION_SITES = 3       # ТЕКСТ: столько мест регистрации в файле

def test_the_two_measures_of_the_banner_agree_today():
    """Совпадение двух ЧИСЕЛ — утверждение, а не устройство двух правил."""
    assert FAILURE_BANNER_HANDLERS_MEASURED == FAILURE_BANNER_REGISTRATION_SITES
```

Гейт критерия 3 ввозит `FAILURE_BANNER_REGISTRATION_SITES`; расхождение впредь
краснит ОДНО правило, названное по предмету.

### WR-06: три изменяющих POST страничного модуля расписаний не сверяют происхождение, а гейт полноты по построению их не видит

**Файлы:** `app/pages/schedules.py:900` (`schedules_create`), `:994`
(`schedules_update`), `:1077` (`schedules_toggle`) — против `:1163`
(`schedules_delete`, сверка есть);
`tests/test_pages/test_origin_guard_on_destructive_routes.py:58-59`

**Проблема.** Разбор исходника (AST, дерево `ea410f4`) даёт:

```
schedules_create   POST /schedules/new              origin_check=False
schedules_update   POST /schedules/{id}/edit        origin_check=False
schedules_toggle   POST /schedules/{id}/toggle      origin_check=False
schedules_delete   POST /schedules/{id}/delete      origin_check=True
```

Докстринг `is_same_origin` (`app/pages/common.py:692-699`) называет требование
дословно: «ASVS L1 (V4.2.2) требует защиты ИЗМЕНЯЮЩИХ СОСТОЯНИЕ запросов от
межсайтовой подделки». Тумблер меняет состояние отправки рекламы, создание и
правка пишут строки — все три под это требование подпадают. Гейт полноты,
который должен был бы это ловить, собирает вселенную по суффиксу пути
`DESTRUCTIVE_PATH_SUFFIX = "/delete"` (`:59`), поэтому три маршрута выпадают из
неё МОЛЧА — тот же способ, которым `app/routes/` выпал из вселенной гейта
идентификаторов (`WR-02` прошлого круга).

**Достижимость названа честно и она СЕГОДНЯ НИЗКАЯ.** Cookie сессии выставляется
с `samesite=lax` (`app/pages/auth.py::_session_cookie_attrs`, замер записан
окном 53 журнала), и межсайтовая форменная отправка cookie не понесёт. Поэтому
это WARNING, а не BLOCKER. Но глубина защиты у четырёх соседних маршрутов
РАЗНАЯ без записанного решения, а единственная опора трёх из них — умолчание
cookie, о котором ни одно правило этих маршрутов не говорит; снятие или смена
`samesite` откроет их все разом и не покраснит ничего.

**Fix.** Либо поставить сверку на все изменяющие POST модуля:

```python
if not is_same_origin(request):
    return Response(status_code=403)
```

либо расширить вселенную гейта с суффикса `/delete` на «POST-маршруты
страничного слоя» и внести три изъятия ПОИМЁННО с записанным основанием — форма,
которую проект уже применяет для `DESTRUCTIVE_ROUTE_OWNERSHIP_EXEMPTIONS`.

## Info

### IN-01: восемь тестовых модулей остались с мёртвыми импортами `datetime`/`timezone`

**Файлы:** `tests/test_models/test_send_log.py:1`,
`tests/test_schedule_relationships.py:1`, `tests/test_pages/test_ads_status.py:22`,
`tests/test_pages/test_schedule_ownership.py:13`,
`tests/test_pages/test_schedules_list.py:18`,
`tests/test_pages/test_schedules_poisoned_row.py:23`,
`tests/test_pages/test_identifier_bounds.py:17`,
`tests/test_pages/test_editor_schedules.py`

Замена литерала на `a_future_run_moment()` убрала последнее употребление обоих
имён; импорт остался. Замер — разбором AST всех тринадцати тронутых модулей: в
восьми `datetime` и `timezone` не читаются ни разу. Линтера в проекте нет
(`pyproject.toml` не объявляет ни ruff, ни flake8), поэтому машинного сторожа у
этого класса тоже нет. Предложение: снять импорты; если линтер заводить не
планируется — хотя бы вместе с этой партией.

### IN-02: `a_future_run_moment` подшит под заголовок «Посев групп» и перехватил последнюю строку чужого обоснования

**Файл:** `tests/conftest.py:226-268`

Функция вставлена ВНУТРЬ секции `# --- Посев групп ---`, и абзац, объясняющий,
почему помощник посева групп живёт функцией модуля, теперь заканчивается строкой
«Импортируется как `from tests.conftest import a_future_run_moment`» — то есть
обоснование одного предмета подписано именем другого. Ниже идёт вторая строка
«Импортируется как `seed_group`», уже верная. Предложение: вынести помощник в
собственную секцию `# --- Моменты запуска ---` над секцией посева групп и
вернуть перехваченную строку её абзацу.

### IN-03: `notices.has_code()` не имеет ни одного потребителя в продукте

**Файл:** `app/pages/notices.py:305-307`

Единственные вызовы — четыре утверждения `tests/test_pages/test_notices_registry.py:201-221`.
В `app/` функция не вызывается нигде; шаблоны пользуются глобалью `notice_for`.
Это не новая правка (вход существовал до партии), но модуль в предмете круга.
Предложение: либо снять вход, либо назвать в докстринге будущего потребителя —
«отдельный вход для тех, кому запись не нужна» сегодня описывает пустое
множество.

### IN-04: снятие `PRAGMA ignore_check_constraints` стои́т после `commit()` и при отказе посева маскирует ПЕРВИЧНУЮ ошибку

**Файл:** `tests/test_application/test_send_analytics.py:1161-1171`

```python
await db_session.execute(text("PRAGMA ignore_check_constraints = ON"))
try:
    await db_session.execute(text("UPDATE schedules SET next_run_at = NULL ..."))
    await db_session.commit()
finally:
    await db_session.execute(text("PRAGMA ignore_check_constraints = OFF"))
```

Если `UPDATE` или `commit()` поднимут отказ, сессия остаётся в неоткатанном
состоянии, и `execute` в `finally` поднимет `PendingRollbackError` — она и
станет видимым отказом, а первичная причина уедет в `__context__`. Замысел
(«ВОЗВРАТ БЕЗУСЛОВЕН») при этом сохраняется: движок пересоздаётся на каждый
тест, так что снятие за границу правила не течёт. Предложение: `await
db_session.rollback()` первой строкой `finally` либо снятие через отдельное
соединение движка.

### IN-05: два названных, но ничем не стерегомых допущения разборщиков

**Файлы:** `tests/test_templates/test_components.py:4852-4900`
(`_strip_js_comments`), `tests/test_planning/test_the_walkthrough_stand_is_seedable.py:118-168`
(`ALLOWED_BUILTINS`)

1. `_strip_js_comments` не различает литерал регулярного выражения (`/…/g`) — косая
   внутри него читается началом комментария. Граница названа в докстринге честно
   («в дереве на 2026-09-12 таких литералов НОЛЬ»), но замера, который покраснеет
   в день появления первого, нет: сегодня это молчаливое занижение числа
   регистраций, то есть ложный зелёный пятого утверждения. Дешёвое закрытие —
   правило, требующее НОЛЯ вхождений `/…/[gimsuy]*` в телах блоков, с отказом,
   называющим файл.
2. `ALLOWED_BUILTINS` собирается через модульную переменную `__builtins__` с
   разбором «словарь или модуль» — деталь реализации CPython, не часть языка.
   `import builtins` и `getattr(builtins, name)` дают то же множество без ветки
   и без зависимости от того, как модуль был загружен.

---

_Reviewed: 2026-09-12T09:40:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
