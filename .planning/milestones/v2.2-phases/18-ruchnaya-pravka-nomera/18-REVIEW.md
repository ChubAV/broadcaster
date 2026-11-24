---
phase: 18-ruchnaya-pravka-nomera
reviewed: 2026-11-22T00:00:00Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - app/application/accounts/dto.py
  - app/application/accounts/use_cases.py
  - app/pages/account_groups.py
  - app/static/css/app.css
  - app/templates/account_groups/includes/phone_form.html
  - app/templates/account_groups/partials/phone_error_response.html
  - app/templates/components/field.html
  - tests/test_pages/test_account_label_accounts.py
  - tests/test_pages/test_account_phone_form.py
  - tests/test_pages/test_account_phone_links.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_pages/test_shell.py
  - tests/test_templates/test_htmx_markup_gates.py
findings:
  critical: 0
  warning: 2
  info: 1
  total: 3
  necessity: 0
carried_forward: 0
closed_prior: 6
status: issues_found
---

# Фаза 18: отчёт о ревью кода (повторное, после раунда закрытия 18-04…18-08)

**Проверено:** 2026-11-22
**Глубина:** standard
**Файлов:** 13
**Статус:** issues_found

## Сводка

Инкрементальное ревью: `git diff 0a0aeaf9 HEAD` по тринадцати файлам, каждый прочитан целиком вокруг изменённых мест; для `app/static/css/app.css` — только блоки раунда (пометка «указан вручную», ряд действий шапки, `html { scroll-padding-top }`, сетка формы номера, `@media (max-width: 400px)`). Контекст: `18-04…18-08-SUMMARY.md`, прежний отчёт целиком.

Все шесть прежних находок закрыты (см. таблицу). Новых критических дефектов нет. Прогнаны и зелёные: `test_account_phone_form`, `test_account_label_accounts`, `test_account_phone_links`, `test_responsive_markup` (223 passed), `test_htmx_markup_gates` (125 passed), правила предков плашки в `test_shell` (40 passed).

Ответы на пять пунктов задания:

- **(a) Гейт `test_the_failure_banner_ancestor_universe_is_addressed_by_stylesheet_selectors`.** Он по-прежнему стережёт то, ради чего писан, и стал строже, а не слабее. Литерал `html` в записи `:root` означает, что блоки `html { … }` теперь попадают во вселенную предков плашки. Раньше `html { filter: blur(2px) }` не адресовался таблицей вовсе, и правило давало ноль находок. Проверено исполнением на копии таблицы стилей: `html { filter: blur(2px); }` даёт одну находку «предок :root (объявлен блоком `html`)», `html.dark { will-change: transform; }` — одну, исходный `app.css` — ноль. «Переворот» утверждений «`html` нет» в «`html` есть» честно следует из того, что `app.css` теперь адресует корень именем тега. Остаются два изъяна самого переворота, см. WR-04.
- **(b) Пустой блок `hx-swap-oob="innerHTML:#notice"`.** На пути без JS он очистить плашку не может: `respond_field_error` вызывает `_error_fragment` только при `is_htmx(request)` (`app/pages/htmx.py:1038`), иначе строит `_page`, где этого файла нет. Под имперсонацией он безвреден: плашка имперсонации `[data-impersonation]` стоит в `base.html:85` вне `#notice`, а настойчивая область `#notice-alert` блоком не названа. Область `#notice` существует в шелле всегда (`includes/notice_area.html:145`). Блок пуст (ни текста, ни потомков, ни кода исхода, ни цифр номера), и тест `test_a_422_htmx_answer_clears_the_previous_notice` это утверждает. Подмена содержимого, а не узла, соответствует правилу `notice_oob.html`. Ответ 422 на такой подмене не меняется: статус и заголовки прежние (`not [name … startswith("hx-")]`).
- **(c) `_phone_form_context`.** Все четыре пути (страница `account_groups.py:356`, страница 422 `:509`, фрагмент 422 `:530`, фрагмент успеха `:562`) получают одни и те же шесть ключей: `account_id`, `phone_value`, `phone_error`, `example_phone`, `phone_maxlength`, `phone_focus`. Умолчание обычного экрана — `focus=False`; три ответа на отправку формы — `focus=True`. Страница 422 перекрывает значение, ошибку и фокус через `context.update` теми же ключами. Единственные вызовы `_screen_context` — `:385` и `:505`, оба именованные. Тест `test_the_plain_screen_never_autofocuses_the_field` проверяет и обычный показ, и посадку `?notice=phone_saved`.
- **(d) `autofocus` в `components/field.html`.** Умолчание `false`; при ложном значении `{%- if autofocus %}` с обрезкой пробелов слева не печатает ничего, разметка прежних полей не меняется ни на символ. Других потребителей `autofocus=` в `app/templates` нет (поиск пуст). Рантайм htmx фокусирует `[autofocus]` только внутри вставленного узла (`function Ne(e)` вызывается с самим вставленным узлом, `htmx.min.js`), поэтому оставшийся в DOM атрибут не отнимает фокус при прочих подменах.
- **(e) `SyncStatusView` с `kw_only=True` без умолчаний.** Единственный конструктор в `app/` — `use_cases.py:62`; в `tests/` — один намеренный отрицательный вызов `test_account_label_accounts.py:307` (ждёт `TypeError`). Шаблоны `SyncStatusView` не создают, только читают. Поведение веток сохранено: `active`, `sync_failed`, `syncing` передаются как есть, прочее — `other`.

## Prior findings — disposition

| ID | prior title (verbatim) | state | evidence |
|----|------------------------|-------|----------|
| WR-01 | кнопка «Сохранить» выровнена по низу подсказки, а не по полю | closed | План 18-07: `app/static/css/app.css:2904-2919` — форма стала сеткой (`areas: "label label" / "input button" / "hint hint"`), подпись поля `display: contents`, кнопка `align-self: stretch`; ошибка `grid-column: 1 / -1` встаёт ниже подсказки; узкая раскладка в одном столбце `app.css:2926`. Абсолютно позиционированная точка `.form-busy` (`app.css:2343`) в сетку не входит. Тесты: `test_the_save_button_shares_the_row_of_the_phone_input`, `test_the_phone_form_takes_its_own_row_in_the_account_head`. Геометрия в браузере суитой не измеряется (оставлено обходу, `human_judgment: true` в 18-07). |
| WR-02 | якорь `#phone` не учитывает липкую шапку шелла | closed | План 18-04: `app/static/css/app.css:446` (`html { scroll-padding-top: 170px }`) и `:503` (236 px при ≤860 px); документ прокручивается самим `html` (`[data-shell]` без `overflow`, `app.css:555-563`), так что правило не инертно. Тест `test_the_document_scroll_padding_clears_the_sticky_head`. Оговорка о том, что число выведено, а не замерено, вынесена в WR-05. |
| WR-03 | умолчание `phone_is_manual = False` в `SyncStatusView` обходит собственную защиту фазы от тихой потери пометки | closed | План 18-06: `app/application/accounts/dto.py:15` (`@dataclass(slots=True, kw_only=True)`) и `:46-49` (ни одного умолчания); `app/application/accounts/use_cases.py:57-66` — один конструктор вместо четырёх. Тест `test_sync_status_view_has_no_defaults` (проверяет `dataclasses.fields` и `TypeError`). |
| IN-01 | фокус теряется только при нажатии на кнопку, а не при отправке Enter (уточнение к `18-UI-REVIEW.md`) | closed | План 18-05: `app/templates/components/field.html:12,30` (параметр `autofocus`), `app/templates/account_groups/includes/phone_form.html:88` (`autofocus=phone_focus`), `app/pages/account_groups.py:509,530,562` (`focus=True` в трёх ответах на отправку). Тест `test_the_answer_to_a_submission_puts_focus_back_into_the_field`. Фокус, поставленный рантаймом на `[autofocus]`, проверен чтением `htmx.min.js`; поведение в живом браузере суитой не исполняется. |
| IN-02 | `_screen_context` — семь позиционных параметров и словарь, достраиваемый после литерала | closed | План 18-07: `app/pages/account_groups.py:265-273` (параметры только именованные, `account_id = account.id` на `:296`), `:237-262` (`_phone_form_context`, единственное место шести ключей), `:356-358` (блок формы внутри литерала через `**`), вызовы `:385`, `:505` именованные. |
| IN-03 | тест закрепляет литерал `maxlength == "64"` вместо выведения из константы | closed | План 18-07: `tests/test_pages/test_account_phone_form.py:275-281` — `int(field["maxlength"]) == 2 * MANUAL_INPUT_MAX_CHARS` и `> MANUAL_INPUT_MAX_CHARS`, константа из `app.services.phone`. |

## Предупреждения

### WR-04: переворот утверждений в гейте предков плашки привязывает охранное правило к стилевому решению и не получил контроля

**Файл:** `tests/test_pages/test_shell.py:7943-7947` (утверждение `"html" in simple_parts`), `:7929-7934`, `:6057`
**Проблема:** смысл правки верный (см. пункт (a) сводки), но у переворота два изъяна.
1. Утверждение `assert "html" in simple_parts` требует, чтобы в `app.css` СТОЯЛ селектор `html`. Это условие не нужно ни антивакуумной половине (запись `:root` адресуется блоками `:root` и `.is-modal-open` независимо от `html`), ни охранной функции. Оно делает охранное правило о плашке красным при любой законной правке, снимающей `html { scroll-padding-top }` (например, переход на другое решение WR-02: отклеенная шапка при ≤860 px, вариант из `18-UAT.md:240`). Сообщение отказа при этом говорит о повисшем литерале, а не о предмете гейта. Прежняя форма («если `html` появился, внеси литерал») была однонаправленной и имела смысл; новая двунаправленная привязывает гейт к стилю.
2. Единственная причина, по которой литерал `html` внесён, — чтобы `html { filter|transform|… }` попадал под правило ловушек. Контроля, который это показывает, в наборе нет: комментарий `test_shell.py:6053-6056` заявляет «внесён, как и требовал отказ правила», а утверждение «блок `html { filter: … }` краснит гейт» не доказано ни одним тестом (в `tests/test_pages/test_shell.py` блоков `html {` с запрещённым свойством нет). Я воспроизвёл это исполнением (`html { filter: blur(2px); }` → одна находка), но в репозитории этого нет, и следующий читатель, снявший литерал как «лишний», не получит красного.
**Исправление:** сделать утверждение однонаправленным и добавить контроль в семейство `test_control_*`:

```python
if "html" in simple_parts:
    assert "html" in FAILURE_BANNER_ANCESTORS[":root"], "app.css адресует корень именем тега, а таблица этого литерала не знает"

def test_control_a_filter_on_the_html_tag_reddens(tmp_path):
    poisoned = _stylesheet_source(_app_css_path()) + "\nhtml { filter: blur(2px); }\n"
    findings = _ancestor_trap_findings(_scratch_stylesheet(tmp_path, poisoned))
    assert len(findings) == 1 and ":root" in findings[0] and "filter" in findings[0]
```

### WR-05: литералы отступа прокрутки (170 / 236 px) не привязаны к высоте шапки, а границы теста живут в самом тесте

**Файл:** `app/static/css/app.css:446`, `:503`; `tests/test_pages/test_responsive_markup.py` (`SCROLL_PADDING_DESKTOP_HEAD = 135`, `SCROLL_PADDING_MOBILE_HEAD = 201`, `SCROLL_PADDING_FIELD_LABEL = 20`, `test_the_document_scroll_padding_clears_the_sticky_head`)
**Проблема:** закрытие WR-02 держится на двух числах, которые комментарий к ним сам называет «вывод из CSS, а не замер»; обход, который их измеряет, ещё впереди. Тест сравнивает литерал `app.css` с тремя константами, лежащими в том же тесте (135, 201, 20): они не читают ни правила `[data-head]`, ни его содержимое, поэтому тест краснеет только при правке самого литерала вниз, но не при росте шапки (длиннее подпись аккаунта в `<h1>`, новая строка в подзаголовке, ещё одна плашка в ряду). Рост шапки молча возвращает WR-02: поле `#phone` снова оказывается под липкой шапкой, а зелёная суита это не заметит. Правило глобальное (`html`), то есть действует и на экраны без шапки: при ≤860 px 236 px «охранной зоны» сверху на ландшафтном телефоне или при открытой клавиатуре съедают почти всю видимую область для прокрутки фокуса.
**Исправление:** до закрытия фазы внести замер обхода (высота `[data-head]` на 320, 375, 860 и 900 px при самой длинной подписи аккаунта) в `18-UAT.md` и поднять константы теста до «замер + 20 + запас» одним коммитом; в комментарии у констант указать, что они обязаны совпадать с последним замером, а не с выводом. Если высота шапки продолжает расти от содержимого, рассмотреть отклеивание шапки при ≤860 px (вариант, уже названный в `18-UAT.md:240`), тогда отступ не нужен вовсе.

## Информация

### IN-04: устаревшие имена и перечни ключей после рефакторинга

**Файл:** `tests/test_pages/test_account_label_accounts.py:280` и `:283`; `app/templates/account_groups/partials/phone_response.html:24`; `app/templates/account_groups/partials/phone_error_response.html:27`
**Проблема:** (1) тест `test_sync_status_view_carries_the_manual_flag_in_all_four_constructors` и его докстринг говорят о четырёх конструкторах, которых после плана 18-06 нет (остался один, ветки `connecting`→`other` проверяются значением статуса); имя вводит в заблуждение следующего читателя. (2) Перечни «Читаемые ключи» обоих фрагментов не называют `phone_focus`, а включаемая форма его читает: пропуск ключа в будущем четвёртом рендере молча снимет фокус (в Jinja отсутствующий ключ ложен), и перечень, на который читатель опирается, этого не подскажет.
**Исправление:** переименовать тест в `…_in_every_status` и поправить докстринг; добавить `phone_focus` в оба перечня (в `phone_response.html` и `phone_error_response.html`) с пометкой «истинен в ответах на отправку формы».

---

_Проверено: 2026-11-22_
_Ревьюер: Claude (gsd-code-reviewer)_
_Глубина: standard_
