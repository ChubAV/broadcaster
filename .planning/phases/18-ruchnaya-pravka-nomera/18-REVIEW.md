---
phase: 18-ruchnaya-pravka-nomera
reviewed: 2026-11-21T00:00:00Z
depth: standard
files_reviewed: 38
files_reviewed_list:
  - app/application/accounts/dto.py
  - app/application/accounts/labels.py
  - app/application/accounts/use_cases.py
  - app/pages/account_groups.py
  - app/pages/accounts.py
  - app/pages/htmx.py
  - app/pages/notices.py
  - app/services/account_label.py
  - app/static/css/app.css
  - app/templates/account_groups/includes/phone_form.html
  - app/templates/account_groups/list.html
  - app/templates/account_groups/partials/phone_response.html
  - app/templates/accounts/list.html
  - app/templates/accounts/partial_cards.html
  - app/templates/accounts/partials/sync_status_card.html
  - app/templates/base.html
  - app/templates/components/account_label.html
  - tests/account_label_support.py
  - tests/test_application/test_account_label_rows.py
  - tests/test_pages/test_account_groups.py
  - tests/test_pages/test_account_label_accounts.py
  - tests/test_pages/test_account_label_groups.py
  - tests/test_pages/test_account_label_sweep.py
  - tests/test_pages/test_account_phone_form.py
  - tests/test_pages/test_account_phone_links.py
  - tests/test_pages/test_htmx_gates.py
  - tests/test_pages/test_htmx_post_pairs.py
  - tests/test_pages/test_htmx_validation_sink.py
  - tests/test_pages/test_hx_location_destinations.py
  - tests/test_pages/test_identifier_bounds.py
  - tests/test_pages/test_impersonation.py
  - tests/test_pages/test_impersonation_gate.py
  - tests/test_pages/test_notices_registry.py
  - tests/test_pages/test_origin_guard_on_destructive_routes.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_services/test_account_label.py
  - tests/test_templates/test_form_inventory.py
  - tests/test_templates/test_htmx_markup_gates.py
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
  necessity: 0
status: issues_found
---

# Фаза 18: отчёт о ревью кода

**Проверено:** 2026-11-21
**Глубина:** standard
**Файлов:** 38
**Статус:** issues_found

## Сводка

Просмотрены изменения фазы 18 (`git diff 103fa6d0..HEAD`): пометка «указан вручную» (18-01), форма ручной правки номера и маршрут `POST /accounts/{id}/phone` (18-02), ссылка с карточки на `/accounts/{id}/groups#phone` (18-03). Остальной код файлов читался только там, где фаза с ним взаимодействует.

Критических дефектов не найдено. Проверено и подтверждено как верное:

- Порядок проверок маршрута: сессия, сверка источника (403 без тела), отсутствие поля, граница идентификатора (`id_in_column`), владение (`_load_owned_account`), писатель. Чужой, несуществующий, вне колонки и `LookupError` писателя отвечают одним и тем же переходом на `/accounts`.
- Отсутствие поля `phone` отличается от пустого (`"phone" not in submitted`), поэтому запрос без поля номер не стирает. Очистка пустой строкой работает (D-09, реализация корректна).
- Эхо введённого значения идёт только автоэкранированием макроса `field`; приёмов отключения экранирования на пути нет. Номер не попадает ни в адрес, ни в текст уведомления, ни в журнал (`account_id` и `phone_set`).
- `_with_notice` вставляет код исхода до якоря: адрес `/groups?notice=phone_saved#phone` собирается верно.
- Подпись в ответе успеха берётся из перечитанных данных (`db.refresh` и `load_account_rows`), `expire_on_commit=False` это не ломает.
- Все места, строящие `AccountRow`, `AccountLabel` и `SyncStatusView`, обновлены; остальные потребители `phone_label` и `labels_for` получают ORM-объекты с `phone_is_manual`, так что `AttributeError` из `row_of` на проде не достижим.
- Замер из докстринга `respond` повторён на дереве: `uv run python -c ...` печатает `25 2`, как записано.
- Новые тесты утверждают поведение (состояние базы после запроса, а не только код ответа), контроли против вакуумности стоят (`test_plain_forms_never_carry_the_manual_mark`).

Оставшиеся находки касаются вёрстки и устойчивости к будущим правкам. Две из них (WR-01, WR-02) уже названы в `18-UI-REVIEW.md` как выводы «по коду»; здесь они подтверждены чтением CSS и разметки.

## Предупреждения

### WR-01: кнопка «Сохранить» выровнена по низу подсказки, а не по полю

**Файл:** `app/static/css/app.css:2839-2842` (правило `[data-acct-phone] .form-wrapper`), разметка `app/templates/account_groups/includes/phone_form.html:51-53`
**Проблема:** контейнер формы — `display: flex; flex-wrap: wrap; align-items: flex-end`. Первый ребёнок — `label.field` (`.field` — колонка: подпись, `<input>`, подсказка `field__hint`, при ошибке ещё `field__error`; `app.css:735`). `flex-end` выравнивает кнопку по нижнему краю всего `label`, то есть по подсказке «Пример: …» (она выводится всегда), а при 422 — по тексту ошибки. Кнопка сидит ниже поля на высоту строки подсказки плюс `gap: 7px`, а на ветке ошибки смещение растёт. Это не отказ потока, но кнопка визуально отрывается от поля, к которому относится, и «прыгает» между состояниями.
**Исправление:** выравнивать кнопку не по низу `label`, а по самому полю. Минимальный вариант без правки общего компонента:

```css
[data-acct-phone] .form-wrapper { align-items: flex-start; }
/* кнопка опускается на высоту подписи поля: */
[data-acct-phone] .btn { margin-block-start: calc(var(--fs-2xs) * 1.4 + 7px); }
```

либо вынести подсказку и ошибку из `label.field` в общем компоненте. Проверить замером на 1440 и 375 px (машинной проверки у вёрстки нет, см. `test_the_phone_form_takes_its_own_row_in_the_account_head`: он читает только текст CSS).

### WR-02: якорь `#phone` не учитывает липкую шапку шелла

**Файл:** `app/static/css/app.css:656-657` (`[data-head] { position: sticky; top: 0; z-index: 5 }`); якорь — `app/templates/accounts/list.html:119` и ещё восемь мест (`href="/accounts/{id}/groups#phone"`), цель — `<input id="phone">` из `phone_form.html`
**Проблема:** вся фаза строится на переходе по ссылке с якорем (D-01, D-12, и тот же адрес возвращает редирект после сохранения). Браузер прокручивает страницу так, чтобы элемент с `id="phone"` оказался у верхнего края окна. У `[data-head]` `position: sticky; top: 0`, а `scroll-margin-top` / `scroll-padding-top` в `app.css` нет вовсе (поиск по файлу пуст). Поэтому, когда экран групп достаточно длинный, чтобы прокрутка состоялась, поле (и его подпись «Номер телефона» выше) оказывается под шапкой. Ровно тот случай, ради которого якорь и введён. Замера в браузере нет; вывод по CSS и разметке.
**Исправление:** дать цели отступ прокрутки:

```css
[data-acct-phone] { scroll-margin-top: calc(var(--head-h, 72px) + 16px); }
```

(или `scroll-padding-top` на прокручиваемом контейнере; взять реальную высоту шапки из существующего токена, а не литерал). Добавить в `test_responsive_markup.py` проверку наличия правила и вынести замер на 375 px в ручную часть приёмки.

### WR-03: умолчание `phone_is_manual = False` в `SyncStatusView` обходит собственную защиту фазы от тихой потери пометки

**Файл:** `app/application/accounts/dto.py:42`, `app/application/accounts/use_cases.py:57-87`
**Проблема:** `AccountRow.phone_is_manual` сделано обязательным без умолчания, и докстринг прямо объясняет зачем: забытый конструктор должен падать `TypeError` громко, а не терять пометку молча. `SyncStatusView.phone_is_manual: bool = False` устроен наоборот: пятый конструктор (новая ветка статуса, новое поле) молча даст «ручной номер не помечен», и это проявится только после первого опроса карточки (пометка исчезнет с подменой). Громкость держит лишь тест `test_sync_status_view_carries_the_manual_flag_in_all_four_constructors`, который знает про четыре перечисленных статуса; ветка, добавленная в `get_sync_status_view`, ему не видна. Умолчание объяснено порядком полей dataclass («стоит после полей с умолчанием»), то есть это следствие порядка, а не решение. Причина названа в докстринге, но решения нет.
Кроме того, функция четырежды повторяет один и тот же вызов с четырьмя аргументами, отличающимися только `status` (4 × 6 строк вместо одного). Каждый новый признак карточки придётся добавлять в четырёх местах, а забытое место, при умолчании в DTO, не заметит никто.
**Исправление:** убрать умолчание (поля без умолчания поставить перед ним или сделать dataclass `kw_only=True`), и собрать ответ один раз:

```python
status = account.status if account.status in {"active", "sync_failed", "syncing"} else "other"
return SyncStatusView(
    status=status,
    messenger_type=account.type,
    phone=account.phone,
    phone_is_manual=account.phone_is_manual,
)
```

(форму сверить с ветками, которые функция отдаёт до этого места: `connecting` и прочие остаются `other`). Тест «все четыре конструктора» при этом остаётся полезным как проверка значений.

## Информация

### IN-01: фокус теряется только при нажатии на кнопку, а не при отправке Enter (уточнение к `18-UI-REVIEW.md`)

**Файл:** `app/templates/account_groups/includes/phone_form.html:50-54`, `app/templates/components/button.html`
**Проблема:** `18-UI-REVIEW.md` называет потерю фокуса после каждой отправки первым приоритетом. По вендоренному `htmx.min.js` (2.0.10) подмена `outerHTML` возвращает фокус элементу с тем же `id`, который был активен до подмены (используется `activeElement` и `setSelectionRange`). У поля `id="phone"` есть, значит отправка Enter из поля (и ветка 422 после неё) фокус сохраняет вместе с положением курсора. Теряется он, когда человек нажал саму кнопку «Сохранить»: у кнопки `id` нет. Масштаб проблемы уже, чем записано, но проблема остаётся для пользователей клавиатуры и читалок.
**Исправление:** если цель — стабильный фокус, достаточно после подмены ставить фокус на `#phone` (одно место, `htmx:afterSwap` на контейнере) либо дать кнопке стабильный `id`. Решать вместе с WR-01, поскольку оба касаются того же блока.

### IN-02: `_screen_context` — семь позиционных параметров и словарь, достраиваемый после литерала

**Файл:** `app/pages/account_groups.py:233-277`
**Проблема:** `account` и `account_id` передаются вместе, хотя `account_id == account.id` (расхождение возможно только по ошибке вызывающего). Четыре ключа формы номера (`phone_value`, `phone_error`, `example_phone`, `phone_maxlength`) и `screen_title` добавлены присваиваниями после литерала `context`, а не в нём, и это единственные ключи, оформленные иначе. Вызовы со всеми семью позиционными аргументами (`account_groups.py:341, 457-459`) легко перепутать местами (`user`/`account`, `db`/`settings`).
**Исправление:** брать `account_id` из `account.id`, вынести блок формы в литерал (или в `context.update({...})` с одним комментарием про умолчания и Pitfall 2), а вызовы перевести на именованные аргументы.

### IN-03: тест закрепляет литерал `maxlength == "64"` вместо выведения из константы

**Файл:** `tests/test_pages/test_account_phone_form.py:229`
**Проблема:** `assert field["maxlength"] == "64"` дублирует `PHONE_FIELD_MAXLENGTH = 2 * MANUAL_INPUT_MAX_CHARS`. Законное изменение предела (`MANUAL_INPUT_MAX_CHARS`) покраснит тест, хотя контракт «двойной запас» сохранён, а ошибочная правка, оставившая `2 * ...` без смысла (например, предел равен пределу сервера), заметит только он, и только если число совпало. То есть утверждение проверяет число, а не инвариант, который описан в комментарии к константе.
**Исправление:** сравнивать `int(field["maxlength"]) == 2 * MANUAL_INPUT_MAX_CHARS` (константа уже импортируется из `app.services.phone`) и отдельно проверять `> MANUAL_INPUT_MAX_CHARS`.

---

_Проверено: 2026-11-21_
_Ревьюер: Claude (gsd-code-reviewer)_
_Глубина: standard_
