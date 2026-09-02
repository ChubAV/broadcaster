"""Wave 0: UI-04 — прямой рендер макросов библиотеки компонентов без HTTP.

В проекте до этого не было ни одного теста, рендерящего шаблон напрямую.
Паттерн вводится здесь: берём окружение Jinja из ``app.pages.common`` и
вызываем ``get_template(...).module.<macro>(...)``.

Почему именно так, а не через страницу: макрос, случайно взявший данные из
контекста вызывающего шаблона, отрендерится ПУСТОЙ строкой, а страница всё
равно вернёт 200. Прямой рендер с пустым контекстом ловит это сразу.
"""

import json
import re
import shutil
import subprocess
from html import unescape
from pathlib import Path
from typing import NamedTuple

import pytest

from app.pages.common import templates

ENV = templates.env
TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "app" / "templates"


def macro(path: str, macro_name: str, /):
    """Вернуть макрос ``macro_name`` из шаблона ``path`` с пустым контекстом."""
    return getattr(ENV.get_template(path).module, macro_name)


def render(path: str, macro_name: str, /, *args, **kwargs) -> str:
    """Отрендерить макрос.

    Параметры помечены positional-only: у макросов библиотеки есть собственный
    параметр ``name``, и без этого он бы конфликтовал с параметром хелпера.
    """
    return str(macro(path, macro_name)(*args, **kwargs))


# --- badge -------------------------------------------------------------------

def test_badge_variants():
    success = render("components/badge.html", "badge", "Активно", "success")
    neutral = render("components/badge.html", "badge", "Пауза", "neutral")

    assert "Активно" in success
    assert "Пауза" in neutral
    assert "badge--success" in success
    assert "badge--neutral" in neutral
    assert success != neutral


def test_badge_escapes_input():
    out = render("components/badge.html", "badge", "<script>x</script>")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


# --- field -------------------------------------------------------------------

def test_field_renders_all_attrs():
    out = render(
        "components/field.html",
        "field",
        name="email",
        label="Email",
        type="email",
        required=True,
        autocomplete="email",
        placeholder="you@example.com",
    )
    assert "<label" in out
    assert "Email" in out
    for token in (
        'name="email"',
        'id="email"',
        'type="email"',
        "required",
        'autocomplete="email"',
        'placeholder="you@example.com"',
    ):
        assert token in out, token

    # name и id обязаны стоять на одном и том же элементе input
    tag = out[out.index("<input") : out.index(">", out.index("<input"))]
    assert 'name="email"' in tag
    assert 'id="email"' in tag


def test_field_value_roundtrip():
    out = render(
        "components/field.html",
        "field",
        name="email",
        value="user@example.com",
    )
    assert 'value="user@example.com"' in out


def test_field_extra_attrs():
    """Атрибуты, без которых не собираются экраны подтверждения кода и пароля."""
    out = render(
        "components/field.html",
        "field",
        name="code",
        type="text",
        maxlength=6,
        pattern="[0-9]{6}",
        inputmode="numeric",
        minlength=6,
    )
    for token in ('maxlength="6"', 'pattern="[0-9]{6}"', 'inputmode="numeric"', 'minlength="6"'):
        assert token in out, token


def test_textarea_and_select_fields():
    textarea = render(
        "components/field.html",
        "textarea_field",
        name="body",
        label="Текст",
        value="Привет",
    )
    assert "<textarea" in textarea
    assert 'name="body"' in textarea
    assert "Привет" in textarea

    select = render(
        "components/field.html",
        "select_field",
        name="timezone",
        label="Часовой пояс",
        options=[("Europe/Moscow", "Europe/Moscow"), ("UTC", "UTC")],
        selected="Europe/Moscow",
    )
    # Порядок атрибутов зафиксирован: существующие тесты проекта проверяют
    # подстроку '<option value="X" selected'.
    assert '<option value="Europe/Moscow" selected' in select
    assert '<option value="UTC"' in select
    assert '<option value="UTC" selected' not in select


# --- button ------------------------------------------------------------------

def test_button_variants():
    primary = render("components/button.html", "button", "Создать", variant="primary")
    danger = render("components/button.html", "button", "Удалить", variant="danger")

    assert "btn--primary" in primary
    assert "btn--danger" in danger
    assert primary != danger
    assert "Создать" in primary

    link = render("components/button.html", "link_button", "Создать", href="/ads/new")
    assert '<a href="/ads/new"' in link or '<a class="btn btn--primary" href="/ads/new"' in link
    assert 'href="/ads/new"' in link


def test_button_type_and_name():
    out = render(
        "components/button.html",
        "button",
        "Сохранить",
        type="submit",
        name="action",
        value="save",
    )
    assert 'type="submit"' in out
    assert 'name="action"' in out
    assert 'value="save"' in out


# --- empty_state -------------------------------------------------------------

def test_empty_state_renders():
    out = render(
        "components/empty_state.html",
        "empty_state",
        "Объявления не найдены",
        hint="Создайте первое объявление",
    )
    assert "Объявления не найдены" in out
    assert "Создайте первое объявление" in out


# --- toggle ------------------------------------------------------------------

def test_toggle_reflects_state():
    on = render("components/toggle.html", "toggle", name="active", checked=True)
    off = render("components/toggle.html", "toggle", name="active", checked=False)

    assert "checked" in on
    assert "checked" not in off
    assert 'name="active"' in on


# --- progress ----------------------------------------------------------------

def test_progress_clamps():
    over = render("components/progress.html", "progress", percent=140)
    assert "140" not in over
    assert "100%" in over

    under = render("components/progress.html", "progress", percent=-20)
    assert "-20" not in under
    assert "0%" in under

    normal = render("components/progress.html", "progress", percent=42)
    assert "42%" in normal


# --- mono --------------------------------------------------------------------

def test_mono_renders():
    out = render("components/mono.html", "mono", "12 / 500")
    assert "12 / 500" in out
    assert "mono" in out


# --- avatar ------------------------------------------------------------------

def test_avatar_initial():
    assert "И" in render("components/avatar.html", "avatar", "Иван")
    assert "?" in render("components/avatar.html", "avatar", None)
    assert "?" in render("components/avatar.html", "avatar", "")


# --- card --------------------------------------------------------------------

def test_card_wrappers():
    opened = render("components/card.html", "card_open", title="Тариф")
    closed = render("components/card.html", "card_close")
    assert "card" in opened
    assert "Тариф" in opened
    assert "</div>" in closed


# --- alert -------------------------------------------------------------------

def test_alert_variants():
    error = render("components/alert.html", "alert", "Неверный email или пароль")
    success = render("components/alert.html", "alert", "Пароль изменён", "success")
    assert "Неверный email или пароль" in error
    assert "alert--error" in error
    assert "alert--success" in success


# --- table (UI-06) -----------------------------------------------------------

def test_table_macros_emit_responsive_primitives():
    """Единственное место фазы, где адаптивные примитивы проверяются на уровне
    макроса, а не отрендеренной страницы: планы 03-08 их только вызывают."""
    head = render("components/table.html", "rowhead", columns=["ГРУППА", "УЧАСТНИКИ"])
    assert "data-rowhead" in head
    assert "ГРУППА" in head

    row = render("components/table.html", "row_open")
    assert "data-row" in row
    assert "data-rowhead" not in row

    grow = render("components/table.html", "cell", "Название", grow=True)
    assert "data-grow" in grow
    assert "Название" in grow

    plain = render("components/table.html", "cell", "42")
    assert "data-grow" not in plain

    assert "</div>" in render("components/table.html", "row_close")


# --- подпись колонки внутри ячейки (UI-06, План 09) --------------------------
#
# Правило [data-cell-label] в app.css существует с Плана 07, но эмитить атрибут
# было нечем: у макроса cell не было параметра подписи. На 860px шапка колонок
# скрывается ([data-rowhead] { display: none }), и число в ячейке остаётся без
# смысла — подпись возвращает его.


def test_cell_label_emitted():
    """Подпись выводится ПЕРЕД значением и внутри того же элемента ячейки.

    Порядок обязателен: на узкой ширине ячейка читается слева направо, и
    обратный порядок дал бы «42 Групп» вместо «Групп 42».
    """
    out = render("components/table.html", "cell", "42", label="Групп")

    assert "data-cell-label" in out
    assert out.index("Групп") < out.index("42")

    # оба внутри одного элемента ячейки: подпись стоит после открывающего тега
    # ячейки, значение — до её закрывающего тега
    cell_open_end = out.index(">")
    assert out.index("data-cell-label") > cell_open_end
    assert out.rstrip().endswith("</span>")
    assert out.index("42") < out.rindex("</span>")


def test_cell_without_label_emits_no_span():
    """Без подписи вывод макроса не меняется ни одним символом."""
    out = render("components/table.html", "cell", "42")

    assert "data-cell-label" not in out
    assert out == '<span class="cell">42</span>'


def test_cell_label_is_escaped():
    """Подпись — обычный экранированный вывод: макрос не место для готового HTML."""
    out = render("components/table.html", "cell", "42", label="<b>x</b>")

    assert "<b>x</b>" not in out
    assert "&lt;b&gt;" in out


def test_cell_label_composes_with_all_flags():
    out = render(
        "components/table.html",
        "cell",
        "42",
        label="Групп",
        mono=True,
        muted=True,
        area="meta",
        title="Групп",
    )

    for token in ("cell--mono", "cell--muted", 'data-area="meta"', 'title="Групп"', "data-cell-label"):
        assert token in out, token


def test_cell_label_in_block_call():
    """Блочный вызов: подпись стоит перед содержимым caller()."""
    out = ENV.from_string(
        "{% from 'components/table.html' import cell %}"
        "{% call cell(label='Успех') %}<em>готово</em>{% endcall %}"
    ).render()

    assert "data-cell-label" in out
    assert "<em>готово</em>" in out
    assert out.index("Успех") < out.index("готово")


# --- modal (D-18) ------------------------------------------------------------

MODAL_ARGS = dict(
    id="del-1",
    title="Удалить объявление?",
    action="/ads/1/delete",
    confirm_label="Удалить",
)


def test_modal_renders_form_action():
    """Модалка заменяет браузерный диалог, но НЕ форму: маршрут и метод прежние."""
    out = render("components/modal.html", "modal", **MODAL_ARGS)
    assert "<form" in out
    form = out[out.index("<form") : out.index(">", out.index("<form"))]
    assert 'method="post"' in form
    assert 'action="/ads/1/delete"' in form
    assert "Удалить" in out


def test_modal_has_dialog_semantics():
    out = render("components/modal.html", "modal", **MODAL_ARGS)
    assert 'role="dialog"' in out
    assert 'aria-modal="true"' in out
    assert "aria-labelledby" in out


def test_modal_cancel_present():
    """Отмена не должна быть труднее подтверждения и не должна быть submit."""
    out = render("components/modal.html", "modal", **MODAL_ARGS)
    assert "Отмена" in out
    cancel_at = out.index("Отмена")
    cancel_tag_start = out.rindex("<button", 0, cancel_at)
    cancel_tag = out[cancel_tag_start : out.index(">", cancel_tag_start)]
    assert 'type="button"' in cancel_tag
    assert 'type="submit"' not in cancel_tag


def test_modal_escapes_title():
    out = render(
        "components/modal.html",
        "modal",
        id="x",
        title="<b>Удалить</b>",
        action="/x/delete",
        confirm_label="Удалить",
    )
    assert "<b>Удалить</b>" not in out
    assert "&lt;b&gt;" in out


def test_modal_does_not_reuse_browser_dialog():
    body = (TEMPLATES_DIR / "components" / "modal.html").read_text(encoding="utf-8")
    assert "confirm(" not in body


# --- слот полей формы внутри модалки (UI-04, План 09) ------------------------
#
# Слот заводился под массовое удаление групп — единственное подтверждение, где
# удаляется не одна сущность по идентификатору в маршруте, а НАБОР, приходящий
# полями формы. План 03-08 снёс раздел вместе с массовыми операциями (D-01,
# D-03), и ПОТРЕБИТЕЛЯ у слота в проекте больше нет.
#
# Тесты слота при этом остаются, а сам слот из макроса не удаляется: это
# свойство компонента, доказанное синтетическим вызовом, а не след снесённого
# раздела. Удаление возможности из библиотеки — отдельное решение, и принимать
# его заодно со сносом раздела нельзя.
#
# Адрес в вызове СИНТЕТИЧЕСКИЙ и намеренно не совпадает ни с одним живым
# маршрутом: адрес снесённого раздела, оставленный здесь, вечно давал бы ложное
# срабатывание греп-проверке «обращений к снесённому разделу не осталось».

HIDDEN_FIELD = '<input type="hidden" name="action" value="delete">'
SLOT_TEST_ACTION = "/synthetic/bulk"


def _modal_block(fields: str = HIDDEN_FIELD, body: str | None = None) -> str:
    """Отрендерить модалку блочным вызовом с произвольными полями формы."""
    body_arg = f", body={body!r}" if body is not None else ""
    return ENV.from_string(
        "{% from 'components/modal.html' import modal %}"
        "{% call modal(id='del-bulk', title='Удалить выбранные элементы?',"
        f" action='{SLOT_TEST_ACTION}', confirm_label='Удалить'" + body_arg + ") %}"
        + fields
        + "{% endcall %}"
    ).render()


def test_modal_accepts_block_fields():
    """Поля слота попадают ВНУТРЬ формы, а не рядом с ней."""
    out = _modal_block()

    assert 'name="action"' in out
    assert out.index("<form") < out.index('name="action"') < out.index("</form>")


def test_modal_block_fields_do_not_replace_actions():
    """Слот аддитивен: кнопки на месте, отмена по-прежнему не submit."""
    out = _modal_block()

    assert "modal__actions" in out
    assert 'x-ref="cancel"' in out
    assert "Отмена" in out
    assert "Удалить" in out

    # отмена остаётся ПЕРВОЙ в порядке обхода: подтверждение не должно
    # срабатывать по Enter раньше, чем пользователь увидит вопрос
    assert out.index('x-ref="cancel"') < out.index('type="submit"')

    cancel_at = out.index("Отмена")
    cancel_tag_start = out.rindex("<button", 0, cancel_at)
    cancel_tag = out[cancel_tag_start : out.index(">", cancel_tag_start)]
    assert 'type="button"' in cancel_tag
    assert 'type="submit"' not in cancel_tag


def test_modal_body_and_block_coexist():
    """Параметр body и блочное содержимое не конфликтуют — выводятся оба."""
    out = _modal_block(body="Выбрано групп: 3")

    assert "Выбрано групп: 3" in out
    assert 'name="action"' in out
    assert out.index("Выбрано групп: 3") < out.index('name="action"')


def test_modal_block_call_keeps_method_and_action():
    """Маршрут и метод при блочном вызове те же: незаметный съезд на GET сделал
    бы удаление доступным по ссылке."""
    out = _modal_block()

    form = out[out.index("<form") : out.index(">", out.index("<form"))]
    assert 'method="post"' in form
    assert f'action="{SLOT_TEST_ACTION}"' in form


# --- гард повторной отправки (E6 loading, план 03-10) ------------------------
#
# Провалившаяся must-have истина фазы 3 (03-VERIFICATION.md): кнопка
# подтверждения обязана отражать выполняющийся запрос и не допускать повторной
# отправки. Гард живёт в МАКРОСЕ, а не в местах применения: одна правка доходит
# до всех двенадцати мест подтверждения, и ни один потребитель ради неё не
# правится (см. test_modal_guard_is_inherited_by_every_consumer ниже).
#
# Приём — Alpine-атрибут на САМОЙ форме, а не встроенный обработчик отправки:
# встроенные обработчики закреплены двусторонней инвентаризацией
# test_only_known_non_dialog_submit_handlers_remain, и второй такой обработчик,
# где бы он ни появился, её покрасил бы.

GUARD_ATTR_RE = re.compile(r'x-on:submit\s*=\s*"([^"]*)"')


def _form_tag(out: str) -> str:
    """Открывающий тег формы панели целиком — от «<form» до «>»."""
    start = out.index("<form")
    return out[start : out.index(">", start) + 1]


def _button_tag(out: str, marker: str) -> str:
    """Тег кнопки, несущей ``marker``, целиком — от «<button» до «>»."""
    at = out.index(marker)
    start = out.rindex("<button", 0, at)
    return out[start : out.index(">", start) + 1]


def _assert_guarded(out: str) -> None:
    """Гард на форме и признак запроса на кнопке подтверждения."""
    form = _form_tag(out)
    guard = GUARD_ATTR_RE.search(form)
    assert guard, (
        "на форме панели нет перехвата отправки — повторная отправка "
        f"разрушительного действия ничем не отменяется: {form!r}"
    )
    expression = guard.group(1)
    assert "preventDefault" in expression, (
        f"перехват не отменяет повторную отправку: {expression!r}"
    )
    assert "sending" in expression and "= true" in expression, (
        f"перехват не устанавливает признак выполняющегося запроса: {expression!r}"
    )
    # Модификатор .prevent отменял бы отправку ВСЕГДА, а форма панели —
    # единственный настоящий путь выполнения разрушительного действия.
    assert "x-on:submit.prevent" not in form, (
        "перехват отменяет отправку всегда — подтверждённое удаление перестало "
        f"уходить на сервер: {form!r}"
    )

    confirm = _button_tag(out, 'type="submit"')
    assert 'x-bind:disabled="sending"' in confirm, (
        f"кнопка подтверждения не отключается на время запроса: {confirm!r}"
    )
    assert 'x-bind:aria-busy="sending"' in confirm, (
        f"кнопка подтверждения не сообщает о запросе вспомогательным технологиям: {confirm!r}"
    )


def test_modal_confirm_guards_double_submit():
    """Первая отправка переводит панель в состояние запроса, вторая отменяется."""
    out = render("components/modal.html", "modal", **MODAL_ARGS)

    _assert_guarded(out)

    assert "sending: false" in out, "состояние отправки не объявлено в x-data"
    # Сброс именно в show(), а не в hide(): возврат по истории браузера
    # восстанавливает страницу из кеша уже с закрытой панелью, и сброс на
    # закрытии до неё не доедет — кнопка осталась бы мёртвой.
    assert "this.sending = false" in out, (
        "состояние не сбрасывается при открытии панели — после возврата по "
        "истории кнопка подтверждения осталась бы отключённой навсегда"
    )


def test_modal_guard_leaves_cancel_operable():
    """Отмена во время отправки остаётся доступной.

    Правило компонента (План 09 Фазы 1): отмена разрушительного действия не
    имеет права быть труднее его подтверждения — в том числе во время запроса.
    """
    out = render("components/modal.html", "modal", **MODAL_ARGS)
    cancel = _button_tag(out, 'x-ref="cancel"')

    assert "disabled" not in cancel, (
        "кнопка отказа блокируется во время отправки — отмена стала труднее "
        f"подтверждения: {cancel!r}"
    )


# Возврат клиентского состояния отправки в исходное по завершении htmx-запроса.
# Признак записан АТРИБУТОМ клиентского фреймворка на теге формы — по образцу
# уже стоящего там перехвата отправки, а не встроенным обработчиком событий:
# встроенные закреплены двусторонней инвентаризацией
# test_only_known_non_dialog_submit_handlers_remain, и третий такой обработчик
# её покрасил бы.
HTMX_RESET_ATTR_RE = re.compile(r'x-on:htmx:after-request\s*=\s*"([^"]*)"')


def test_modal_hands_the_sending_state_back_on_the_htmx_path():
    """У блокировки кнопки подтверждения ОДИН владелец (WARN-2 / WR-02).

    На htmx-пути атрибут блокировки кнопки ведут ДВОЕ: клиентское состояние
    (`x-bind:disabled="sending"`) и рантайм (`hx-disabled-elt`). Проверено по
    вендоренному htmx 2.0.10: рантайм выставляет блокировку только когда
    атрибута нет, помечает её своей меткой и снимает по этой метке; привязки
    клиентского фреймворка применяются микрозадачей, поэтому синхронный
    слушатель отправки рантайма выигрывает гонку и владеет атрибутом.

    ⚠️ ЦЕНА ГОНКИ ВИДНА ТОЛЬКО ПОСЛЕ ОТКАЗА ЗАПРОСА, И ИМЕННО ЭТОТ СЛУЧАЙ
    НАПИСАН БЫЛ ДЛЯ ЧЕЛОВЕКА. Рантайм снимает блокировку, а `sending` остаётся
    true — на экране включённая праздная кнопка с признаком занятости, и
    сбрасывается он только в `show()`, то есть при СЛЕДУЮЩЕМ открытии панели.
    Человек, у которого зависла сеть, оказывается перед кнопкой, которая
    выглядит занятой и не делает ничего.

    ⚠️ ВТОРОЕ УТВЕРЖДЕНИЕ — НЕСУЩЕЕ, А НЕ ГИГИЕНА. Без него первое было бы
    зелено и при признаке, просочившемся в УМОЛЧАНИЕ: пятнадцать мест
    подтверждения без htmx-признака обязаны рендериться байт-в-байт как до
    правки (D-01), и признак, выехавший из своей ветки, нарушил бы это молча.
    """
    over_htmx = render("components/modal.html", "modal", hx_post=True, **MODAL_ARGS)
    form = _form_tag(over_htmx)

    reset = HTMX_RESET_ATTR_RE.search(form)
    assert reset, (
        "на htmx-пути форма панели не возвращает клиентское состояние отправки "
        "в исходное по завершении запроса — после отказа на экране осталась бы "
        f"включённая праздная кнопка с признаком занятости: {form!r}"
    )
    expression = reset.group(1)
    assert "sending" in expression and "false" in expression, (
        f"признак завершения запроса не сбрасывает состояние отправки: {expression!r}"
    )

    default = render("components/modal.html", "modal", **MODAL_ARGS)
    assert not HTMX_RESET_ATTR_RE.search(default), (
        "признак просочился в УМОЛЧАНИЕ: пятнадцать мест подтверждения без "
        "htmx-признака обязаны рендериться байт-в-байт как до правки, а "
        f"рендерятся иначе: {_form_tag(default)!r}"
    )


def test_modal_guard_survives_the_block_call():
    """Гард не теряется на пути блочного вызова.

    Единственный продуктовый потребитель слота — карточка расписания в
    редакторе объявления (ads/includes/sched_card.html); её удаление обязано
    получить тот же гард, что и вызовы без слота.
    """
    _assert_guarded(_modal_block())


# --- инварианты библиотеки ---------------------------------------------------

COMPONENT_CALLS = [
    ("components/badge.html", "badge", ("Метка",), {}),
    ("components/field.html", "field", (), {"name": "x"}),
    ("components/field.html", "textarea_field", (), {"name": "x"}),
    ("components/field.html", "select_field", (), {"name": "x", "options": [("a", "A")]}),
    ("components/button.html", "button", ("Кнопка",), {}),
    ("components/button.html", "link_button", ("Ссылка",), {"href": "/"}),
    ("components/card.html", "card_open", (), {}),
    ("components/card.html", "card_close", (), {}),
    ("components/table.html", "rowhead", (), {}),
    ("components/table.html", "row_open", (), {}),
    ("components/table.html", "row_close", (), {}),
    ("components/table.html", "cell", ("Ячейка",), {}),
    ("components/empty_state.html", "empty_state", ("Пусто",), {}),
    ("components/toggle.html", "toggle", (), {"name": "x"}),
    ("components/progress.html", "progress", (), {"percent": 10}),
    ("components/mono.html", "mono", ("TEXT",), {}),
    ("components/avatar.html", "avatar", ("Имя",), {}),
    ("components/alert.html", "alert", ("Сообщение",), {}),
    ("components/modal.html", "modal", (), MODAL_ARGS),
    # ⚠️ Обёртка htmx-формы попадает под рамку каталога компонентов
    # (test_components_are_documented_macros) САМА, а под ЭТОТ перечень — НЕТ:
    # он выписан руками, и новый макрос в него сам не приходит.
    # Вызов прямой (без блока) намеренно: он проверяет ветку
    # `caller is defined`, без которой макрос упал бы вне `{% call %}`.
    ("components/form_wrapper.html", "form_wrapper", (), {"action": "/x"}),
]


def test_macros_take_no_context():
    """Ни один макрос не читает переменные вызывающего шаблона.

    Рендер с пустым контекстом обязан вернуть непустую разметку: если макрос
    полагается на контекст, здесь он выдаст пустую строку.
    """
    for path, name, args, kwargs in COMPONENT_CALLS:
        out = render(path, name, *args, **kwargs)
        assert out.strip(), f"{path}:{name} отрендерился пустым"
        assert "<" in out, f"{path}:{name} не выдал разметку"


def test_components_have_no_with_context_import():
    for path in sorted((TEMPLATES_DIR / "components").glob("*.html")):
        body = path.read_text(encoding="utf-8")
        assert "with context" not in body, path.name


def test_components_are_documented_macros():
    files = sorted((TEMPLATES_DIR / "components").glob("*.html"))
    assert len(files) >= 11
    for path in files:
        body = path.read_text(encoding="utf-8")
        assert body.lstrip().startswith("{#"), path.name
        assert "{% macro " in body, path.name


UNSAFE_MARKERS = ("|safe", "| safe", "autoescape false", "autoescape False", "Markup(")


def test_no_unsafe_escaping():
    """Инвариант экранирования: ни один шаблон проекта не отключает автоэкранирование."""
    offenders = []
    for path in sorted(TEMPLATES_DIR.rglob("*.html")):
        body = path.read_text(encoding="utf-8")
        for marker in UNSAFE_MARKERS:
            if marker in body:
                offenders.append(f"{path.relative_to(TEMPLATES_DIR)}: {marker}")
    assert not offenders, offenders


# =============================================================================
# План 13, Задача 2: страховочная сетка подтверждений (UI-04, SC-3)
# =============================================================================
#
# Gap 1 из 01-VERIFICATION.md: подтверждения удаления были сделаны системным
# диалогом браузера. Планы 09-12 перевели все четырнадцать мест на панель
# дизайн-системы. Обратный ход прост и незаметен: следующая фаза добавит раздел
# с удалением и подтвердит его диалогом, всё отдаст 200, и увидит это только
# пользователь. Эта сетка ловит и возврат диалога, и потерю места подтверждения.

MODAL_COMPONENT = "components/modal.html"

# Вызов системного диалога ПОДТВЕРЖДЕНИЯ. Точка перед именем допускается
# (window.confirm), символ слова — нет: confirm_label= и confirm_variant= —
# параметры макроса панели, а не диалог.
BROWSER_DIALOG_RE = re.compile(r"(?<!\w)confirm\s*\(")

# Единственный оставшийся в проекте ВСТРОЕННЫЙ обработчик отправки формы. Это
# НЕ диалог подтверждения: он отключает кнопку и меняет её подпись, то есть
# защищает от двойной отправки. В границу Gap 1 не входит, и файл не принадлежит
# ни одному плану набора 09-13 — правка нарушила бы контракт распараллеливания.
#
# Двусторонняя инвентаризация ниже — то, что делает сужение запрета до диалогов
# ПОДТВЕРЖДЕНИЯ усилением, а не поблажкой: новый встроенный обработчик где
# угодно краснеет, даже если диалога в нём нет (T-13-07).
INLINE_SUBMIT_HANDLER = "onsubmit"
KNOWN_SUBMIT_HANDLER_FILES = frozenset({"accounts/connect_max.html"})
INLINE_SUBMIT_HANDLER_RE = re.compile(rf'{INLINE_SUBMIT_HANDLER}\s*=\s*"([^"]*)"')

# Массовые действия списка групп были ЕДИНСТВЕННЫМ местом, где кнопка действия
# не обёрнута формой. План 03-08 снёс раздел вместе с ними (D-01, D-03), и
# названного исключения у запрета больше нет: перечень ПУСТ, а значит запрет
# действует без изъятий.
#
# Пустой перечень не делает тест бессмысленным — наоборот, он делает его
# строже: предикат «кнопка вне формы, вызывающая функцию массового действия»
# по-прежнему обходит ВСЕ шаблоны, и первая же такая кнопка, где бы она ни
# появилась, теперь краснеет как незаявленная. Имя функции сохранено именно для
# этого: у экрана групп аккаунта массовых операций нет, и возвращаться они
# должны через явное решение, а не тихо.
BULK_ACTION_FUNCTION = "submitBulkGroups"
BULK_ACTION_FILES: frozenset[str] = frozenset()
BULK_ACTION_BUTTONS = 2

FORM_RE = re.compile(r"<form\b[^>]*>.*?</form>", re.S)
FORM_METHOD_RE = re.compile(r'method\s*=\s*"([^"]*)"')
BUTTON_TAG_RE = re.compile(r"<button\b[^>]*>")
MODAL_EVENT_PREFIX = "modal-open-"
MODAL_EVENT_RE = re.compile(rf"{MODAL_EVENT_PREFIX}([a-z-]*)")

# Кнопка отправки внутри формы. Второй носитель — вызов макроса button: у него
# type='submit' ПО УМОЛЧАНИЮ, и это доказывается один раз отдельным
# утверждением в test_every_row_delete_site_keeps_a_real_form, а не
# принимается на веру.
SUBMIT_BUTTON_MARKERS = ('type="submit"', "button(")


class RowDeleteSite(NamedTuple):
    """Шаблон со строчным удалением ОДНОЙ сущности и образец адреса удаления.

    forms — ОЖИДАЕМОЕ число форм удаления, а не порог «хотя бы одна»: у трёх
    файлов раздела «Аккаунты» их по три (по одной на ветку статуса), и порог
    растворил бы потерю одной ветки.
    """

    template: str
    action_pattern: str
    forms: int


# ШЕСТЬ шаблонов, ДВЕНАДЦАТЬ мест. Шесть, а не четыре: два файла раздела
# «Аккаунты» помимо списочной страницы — порция бесконечной прокрутки и блок
# подмены по опросу статуса — несут по три места каждый. План 11 присутствие
# формы утверждает ТОЛЬКО для accounts/list.html, поэтому для шести мест из
# двенадцати этот перечень — единственное покрытие (T-13-06).
#
# Самая опасная поверхность из шести — accounts/partials/sync_status_card.html:
# это цель подмены по hx-swap="outerHTML", и на первичной отрисовке страницы её
# разметки нет вовсе. Потеря формы там проявится только после первого опроса
# статуса, то есть ни один дымовой проход её не увидит (WR-04).
#
# План 02-07 УБРАЛ шестое место: карточка сводного списка расписаний больше не
# предлагает удаление (D-18). Это не потеря пути удаления, а его единственность:
# расписание удаляется в редакторе объявления, где видно, что именно исчезнет, и
# то место закреплено отдельно — tests/test_pages/test_editor_schedules.py
# ::test_schedule_delete_is_a_real_form. Перечень СТРОЧНЫХ удалений уменьшился
# на один вход, ни одно утверждение не ослаблено.
#
# План 03-05 добавил СЕДЬМОЙ шаблон и ТРИНАДЦАТОЕ место: строка группы на экране
# аккаунта получила удаление (GRP-06). Место строчное, поэтому входит именно
# сюда; образец адреса включает сегмент `/groups/`, иначе он совпал бы и с
# формой удаления самого АККАУНТА (`/accounts/{id}/delete`) — общий префикс у
# двух разных разрушительных действий.
#
# План 03-08 СНЯЛ седьмой шаблон и тринадцатое место: строка снесённого
# глобального раздела «Группы» удалена вместе с ним (D-01). Путь удаления группы
# при этом не потерян и даже не изменился по форме — он ЕДИНСТВЕННЫЙ и живёт
# строкой выше, на экране аккаунта, где владение проверяется тройным WHERE.
# Уменьшение объявленных чисел — признание СОЗНАТЕЛЬНОГО снятия: молчаливое
# исчезновение места по-прежнему краснеет.
ROW_DELETE_SITES = (
    RowDeleteSite("accounts/list.html", r"/accounts/[^\"]+/delete", 3),
    RowDeleteSite("accounts/partial_cards.html", r"/accounts/[^\"]+/delete", 3),
    RowDeleteSite(
        "accounts/partials/sync_status_card.html", r"/accounts/[^\"]+/delete", 3
    ),
    RowDeleteSite(
        "account_groups/includes/group_row.html",
        r"/accounts/[^\"]+/groups/[^\"]+/delete",
        1,
    ),
    RowDeleteSite("ads/includes/ad_card.html", r"/ads/[^\"]+/delete", 1),
    RowDeleteSite("admin/user_detail.html", r"/admin/users/[^\"]+/delete", 1),
)

ROW_DELETE_PLACES = 12

# Три счёта инвентаризации. Третий обязателен: файл подмены статуса панель
# сознательно НЕ импортирует (асимметрия Плана 11), поэтому счёт по импортёрам
# физически не может дойти до числа мест.
#
# План 02-04 добавил ДЕВЯТОГО импортёра и ПЯТНАДЦАТОЕ место: редактор
# объявления получил собственное подтверждение удаления («УДАЛИТЬ ОБЪЯВЛЕНИЕ» в
# правой колонке). Место не строчное — оно страничное, поэтому в перечень
# ROW_DELETE_SITES не входит; имя события у него то же, что у карточки списка
# (`ad-del-`), и число РАЗЛИЧНЫХ имён не менялось.
#
# План 02-05 добавил ДЕСЯТОГО импортёра, СЕДЬМОЕ имя события и ШЕСТНАДЦАТОЕ
# место: карточка расписания в редакторе получила «УДАЛИТЬ РАСПИСАНИЕ»
# (ads/includes/sched_card.html). Имя события СВОЁ (`sched-del-`), а не общее со
# строкой сводного списка (`schedule-del-`): обе разметки могут оказаться на
# одной странице, и общее имя открывало бы две панели одним событием.
# Место карточное, а не строчное — перечень ROW_DELETE_SITES фиксирует строки
# списков, и карточка редактора в него не входит.
#
# План 02-07 СНЯЛ десятого импортёра, СЕДЬМОЕ имя события и ШЕСТНАДЦАТОЕ место:
# карточка сводного списка расписаний перестала предлагать удаление (D-18).
# Имя `schedule-del-` исчезло из проекта целиком — оно принадлежало ровно этому
# месту; имя карточки редактора (`sched-del-`) не затронуто, и удаление
# расписания по-прежнему подтверждается панелью, но ровно в одном месте.
# Уменьшение объявленных чисел — признание СОЗНАТЕЛЬНОГО снятия: молчаливое
# исчезновение места по-прежнему краснеет.
# План 03-05 добавил ДЕСЯТОГО импортёра и ШЕСТНАДЦАТОЕ место: строка группы на
# экране аккаунта (`account_groups/includes/group_row.html`). Имя события —
# ТО ЖЕ, что у строки старого раздела (`group-del-`), и число РАЗЛИЧНЫХ имён не
# менялось: подтверждается одна и та же сущность по одному и тому же
# идентификатору, а обе разметки на одной странице не встречаются — экран
# аккаунта и глобальный раздел «Группы» это разные страницы.
#
# План 03-08 снёс глобальный раздел (D-01) и вместе с ним ДВУХ импортёров
# (`groups/list.html` и `groups/includes/group_row.html`), ДВА места
# подтверждения и ОДНО имя события:
#   * `groups-bulk-del` исчезло из проекта целиком — оно принадлежало ровно
#     панели массового удаления, а массовых операций у нового экрана нет (D-03);
#   * `group-del-` ОСТАЛОСЬ: имя было общим у обеих строк, и та из них, что
#     живёт на экране аккаунта, никуда не делась — поэтому имён 5, а не 4.
# Ожидание плана 03-05 «16 → 15» не сбылось: оно учитывало только строку и
# упускало панель массового удаления в списочной странице. Число проверено
# счётом по файлам, а не перенесено из прогноза.
#
# План 04-09 добавил ДЕВЯТОГО импортёра, ШЕСТОЕ имя события и ПЯТНАДЦАТОЕ место:
# карточка записи истории получила ПОВТОР ОТПРАВКИ (HIST-04). Это первое место
# подтверждения в проекте, подтверждающее НЕ удаление: действие необратимо по
# другой причине — отправка в стороннюю группу не отзывается и тратит баланс, —
# поэтому в перечень строчных УДАЛЕНИЙ (ROW_DELETE_SITES) оно не входит и числа
# ROW_DELETE_PLACES не двигает.
#
# Мест ПЯТНАДЦАТЬ, а не шестнадцать, хотя повтор появился на ДВУХ экранах.
# Запуск и панель объявлены ОДИН раз макросами в history/includes/
# history_card.html, а страница записи (history/detail.html) их импортирует —
# тем же приёмом, каким план 04-07 сделал одну кнопку копирования на оба
# экрана. Вторая копия разошлась бы с первой ровно там, где расхождение
# опаснее всего: в тексте, обещающем пользователю, ЧТО именно будет отправлено
# (D-17). Поэтому страница записи в счёт импортёров и мест НЕ входит: она не
# содержит ни строки `components/modal.html`, ни собственного имени события.
#
# Числа получены СЧЁТОМ ПО ФАЙЛАМ уже после правки шаблонов, а не прогнозом:
# предыдущий комментарий выше — след ровно того случая, когда прогноз не сбылся.
#
# ⚠️ ТРИ ЧИСЛА ПОДНЯТЫ ПЛАНОМ 06-05 НА ЕДИНИЦУ КАЖДОЕ, И ЭТО ОДНО МЕСТО, А НЕ
# три разных. Перезапуск воркера (D-11) добавил ОДНОГО потребителя панели
# (`admin/workers.html` — он её собирает), ОДНО новое имя события
# (`modal-open-worker-restart-`) и ОДНО место применения (диспетчер события в
# `admin/includes/worker_row.html`). Числа снова получены СЧЁТОМ по файлам после
# правки, а не прогнозом.
#
# ⚠️ ТЕ ЖЕ ТРИ ЧИСЛА ПОДНЯТЫ ПЛАНОМ 06-07 ЕЩЁ НА ЕДИНИЦУ КАЖДОЕ, И ЭТО СНОВА
# ОДНО МЕСТО. Снятие задачи из очереди (D-17) добавило ОДНОГО потребителя
# панели (`admin/queue.html` — он её собирает), ОДНО новое имя события
# (`modal-open-queue-drop-`) и ОДНО место применения (диспетчер события в
# `admin/includes/queue_row.html`). Числа получены СЧЁТОМ по файлам после
# правки, а не прогнозом.
#
# ⚠️ ПЛАН 06-12 ПОДНЯЛ ДВА ЧИСЛА ИЗ ТРЁХ, А НЕ ВСЕ ТРИ, И РАЗНИЦА ЗДЕСЬ
# СОДЕРЖАТЕЛЬНАЯ. Вход администратора ПОД ПОЛЬЗОВАТЕЛЕМ (ADMIN-06) добавил ОДНО
# новое имя события (`modal-open-user-imp-`) и ОДНО место применения (диспетчер
# в `admin/user_detail.html`), но НЕ добавил импортёра: карточка пользователя
# уже собирала панель — под подтверждение удаления, — и второй импорт того же
# компонента в тот же файл не появляется.
#
# ЗАЧЕМ У ЭТОГО ДЕЙСТВИЯ ПОДТВЕРЖДЕНИЕ, КОГДА У ОБОИХ СОСЕДНИХ ТУМБЛЕРОВ ЕГО
# НЕТ. Тумблеры обратимы одним нажатием и данных не меняют; вход под
# пользователем переводит ВСЕ последующие действия администратора в чужую
# учётную запись — от синхронизации групп до всего, что он нажмёт по дороге.
# Начальный фокус панели стоит на «Отмене», поэтому по Enter вход не
# срабатывает.
#
# Числа снова получены СЧЁТОМ по файлам после правки, а не прогнозом.
MODAL_IMPORTERS = 11
MODAL_EVENT_NAMES = 9
MODAL_PLACES = 18


# --- разборщики исходников ---------------------------------------------------


def _all_templates() -> list[tuple[str, str]]:
    """Все шаблоны проекта парами «путь относительно app/templates — исходник»."""
    return [
        (path.relative_to(TEMPLATES_DIR).as_posix(), path.read_text(encoding="utf-8"))
        for path in sorted(TEMPLATES_DIR.rglob("*.html"))
    ]


def _template_source(rel: str) -> str:
    return (TEMPLATES_DIR / rel).read_text(encoding="utf-8")


def _macro_calls(source: str, macro_name: str) -> int:
    """Число ВЫЗОВОВ макроса. Объявление вызовом не считается.

    Наивный поиск по имени нашёл бы объявление в самом компоненте и объявил бы
    библиотеку своим же потребителем.
    """
    calls = 0
    for match in re.finditer(rf"(?<![\w.]){re.escape(macro_name)}\s*\(", source):
        if source[: match.start()].rstrip().endswith("macro"):
            continue
        calls += 1
    return calls


def _form_spans(source: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in FORM_RE.finditer(source)]


def _delete_forms_in(source: str, action_pattern: str) -> list[str]:
    """Формы удаления ЦЕЛИКОМ: открывающий тег с методом POST и адресом.

    Регистр метода НЕ учитывается: в трёх файлах раздела «Аккаунты» он написан
    заглавными, в строках групп, расписаний и объявлений — строчными. Сравнение
    с учётом регистра покраснело бы на разнице регистра, а не на потере формы.
    """
    forms = []
    for form in FORM_RE.findall(source):
        opening = form[: form.index(">") + 1]
        method = FORM_METHOD_RE.search(opening)
        if not method or method.group(1).lower() != "post":
            continue
        if not re.search(rf'action="{action_pattern}"', opening):
            continue
        forms.append(form)
    return forms


def _formless_bulk_buttons(source: str) -> list[str]:
    """Кнопки, вызывающие функцию массового действия и НЕ обёрнутые формой."""
    spans = _form_spans(source)
    return [
        match.group(0)
        for match in BUTTON_TAG_RE.finditer(source)
        if BULK_ACTION_FUNCTION in match.group(0)
        and not any(start <= match.start() < end for start, end in spans)
    ]


def test_no_template_calls_browser_dialog():
    """Ни один шаблон проекта не вызывает системный диалог ПОДТВЕРЖДЕНИЯ.

    Исключений нет ни одного, включая саму панель: components/modal.html
    дополнительно закрыт test_modal_does_not_reuse_browser_dialog.
    """
    offenders = {
        rel: len(BROWSER_DIALOG_RE.findall(source))
        for rel, source in _all_templates()
        if BROWSER_DIALOG_RE.search(source)
    }
    assert not offenders, (
        "системный диалог браузера вернулся в шаблоны — подтверждение обязано "
        f"открывать панель дизайн-системы: {offenders}"
    )


def test_only_known_non_dialog_submit_handlers_remain():
    """Двусторонняя инвентаризация единственного встроенного обработчика.

    Это компенсация за сужение запрета выше до диалогов ПОДТВЕРЖДЕНИЯ. Новый
    встроенный обработчик отправки в любом файле краснеет здесь, даже если
    диалога в нём нет.
    """
    found = {
        rel for rel, source in _all_templates() if INLINE_SUBMIT_HANDLER in source
    }
    assert found == set(KNOWN_SUBMIT_HANDLER_FILES), (
        "множество шаблонов со встроенным обработчиком отправки разошлось с "
        f"названным перечнем: новые {sorted(found - KNOWN_SUBMIT_HANDLER_FILES)}; "
        f"исчезнувшие {sorted(KNOWN_SUBMIT_HANDLER_FILES - found)}"
    )

    for rel in sorted(KNOWN_SUBMIT_HANDLER_FILES):
        source = _template_source(rel)
        handlers = INLINE_SUBMIT_HANDLER_RE.findall(source)
        assert handlers, f"{rel}: обработчик отправки не разобран"
        for handler in handlers:
            assert not BROWSER_DIALOG_RE.search(handler), (
                f"{rel}: встроенный обработчик стал диалогом подтверждения — "
                f"это уже не защита от двойной отправки: {handler!r}"
            )
            # Положительное утверждение о том, ЧЕМ этот обработчик является.
            assert "disabled" in handler, (
                f"{rel}: обработчик перестал быть защитой от двойной отправки — "
                f"кнопка больше не отключается: {handler!r}"
            )


def test_every_modal_site_has_cancel_and_escape():
    """Свойства панели доказываются ОДИН раз и наследуются всеми местами.

    Отказ с начальным фокусом, закрытие по Esc и перехват обхода по Tab живут в
    макросе. Сетка утверждает их по разметке макроса и отдельно — что каждое
    место применения вызывает именно этот макрос, а не собирает свою панель.
    Копия панели в обход библиотеки краснеет.
    """
    out = render("components/modal.html", "modal", **MODAL_ARGS)
    assert 'x-ref="cancel"' in out, "начальный фокус на отказе потерян"
    assert MODAL_ARGS["confirm_label"] in out
    assert "Отмена" in out, "кнопка отказа исчезла"
    assert "keydown.escape" in out, "закрытие по Esc потеряно"
    assert "keydown.tab" in out, "перехват обхода по Tab потерян"

    consumers = {
        rel
        for rel, source in _all_templates()
        if MODAL_COMPONENT in source and rel != MODAL_COMPONENT
    }
    assert consumers, "потребителей панели не найдено — проверь разрешитель"

    silent = {rel for rel in consumers if not _macro_calls(_template_source(rel), "modal")}
    assert not silent, (
        "шаблоны импортируют панель, но макрос не вызывают — панель собрана в "
        f"обход библиотеки и проверенных свойств не наследует: {sorted(silent)}"
    )


def test_every_row_delete_site_keeps_a_real_form():
    """В каждом из ДВЕНАДЦАТИ мест удаления стоит настоящая форма (WR-04).

    Панель — УСИЛЕНИЕ поверх формы, а не замена ей: без Alpine перехват не
    навешивается, и форма уходит на прежний маршрут прежним методом. Кнопка
    вместо формы оставила бы раздел без единственного пути удалить сущность.
    """
    # Второй носитель кнопки отправки доказывается здесь же: у макроса button
    # type='submit' по умолчанию, и это не принимается на веру.
    assert 'type="submit"' in render("components/button.html", "button", "Удалить")

    assert sum(site.forms for site in ROW_DELETE_SITES) == ROW_DELETE_PLACES, (
        "перечень строчных удалений разошёлся с числом мест"
    )

    offenders = {}
    for site in ROW_DELETE_SITES:
        source = _template_source(site.template)
        forms = _delete_forms_in(source, site.action_pattern)
        if len(forms) != site.forms:
            offenders[site.template] = (
                f"форм удаления {len(forms)}, ожидалось {site.forms} "
                f"(образец адреса {site.action_pattern})"
            )
            continue
        formless = [
            index
            for index, form in enumerate(forms)
            if not any(marker in form for marker in SUBMIT_BUTTON_MARKERS)
        ]
        if formless:
            offenders[site.template] = (
                f"формы без кнопки отправки внутри: {formless}"
            )

    assert not offenders, (
        "место подтверждения удаления потеряло настоящую форму — без Alpine "
        "удалить сущность станет нечем: "
        + "; ".join(f"{rel} -> {why}" for rel, why in sorted(offenders.items()))
    )


def test_bulk_actions_are_the_only_formless_delete_triggers():
    """Кнопок действия вне формы в проекте не осталось НИ ОДНОЙ (план 03-08).

    Предикат — «кнопка, не обёрнутая формой, вызывающая функцию массового
    действия», а НЕ «намерение удаления»: из двух кнопок снесённого раздела
    намерение удаления несло одну, и счёт по намерению дал бы единицу вместо
    двух.

    Тест работает в обе стороны и с пустым перечнем: кнопка массового действия
    без формы в любом файле краснеет как незаявленная, а появление имени в
    перечне без самой кнопки — как исчезнувшая.
    """
    counts = {
        rel: len(_formless_bulk_buttons(source))
        for rel, source in _all_templates()
        if _formless_bulk_buttons(source)
    }
    assert set(counts) == set(BULK_ACTION_FILES), (
        "кнопки массового действия вне формы разошлись с названным перечнем: "
        f"новые {sorted(set(counts) - BULK_ACTION_FILES)}; "
        f"исчезнувшие {sorted(BULK_ACTION_FILES - set(counts))}"
    )
    for rel in sorted(BULK_ACTION_FILES):
        assert counts[rel] == BULK_ACTION_BUTTONS, (
            f"{rel}: кнопок массового действия без формы {counts[rel]}, "
            f"ожидалось {BULK_ACTION_BUTTONS}"
        )


def test_modal_cancel_is_not_a_delete_trigger():
    """Кнопка отказа панели — второе названное исключение.

    По контракту Плана 09 она НЕ кнопка отправки, иначе отмена стала бы труднее
    подтверждения. Утверждение существует, чтобы предыдущий тест не пришлось
    однажды «слегка ослабить» из-за неё.
    """
    out = render("components/modal.html", "modal", **MODAL_ARGS)
    cancel_at = out.index("Отмена")
    cancel_tag = out[out.rindex("<button", 0, cancel_at) : cancel_at]

    assert 'type="button"' in cancel_tag
    assert 'type="submit"' not in cancel_tag
    assert "delete" not in cancel_tag, (
        "кнопка отказа понесла адрес удаления — отмена перестала быть отменой: "
        f"{cancel_tag!r}"
    )
    assert "formaction" not in cancel_tag


# Явный перечень ПОТРЕБИТЕЛЕЙ панели — восемь файлов. В отличие от
# MODAL_IMPORTERS (это ЦЕЛОЕ ЧИСЛО файлов со строкой "components/modal.html",
# включая сам компонент) здесь МНОЖЕСТВО ИМЁН, поэтому напрямую сравнивать их
# нельзя — отношение между двумя счётами утверждается ниже.
#
# Восьмой вход добавлен планом 04-09: карточка записи истории подтверждает
# повтор отправки. Страница записи (history/detail.html) потребителем НЕ
# является — она импортирует готовые макросы запуска и панели из карточки, а
# саму панель не собирает.
MODAL_CONSUMERS = frozenset(
    {
        "account_groups/includes/group_row.html",
        "accounts/list.html",
        "accounts/partial_cards.html",
        "admin/user_detail.html",
        "ads/form.html",
        "ads/includes/ad_card.html",
        "ads/includes/sched_card.html",
        "history/includes/history_card.html",
        # Девятый вход добавлен планом 06-05: перезапуск воркера в админке
        # (D-11). Панель собирает СТРАНИЦА подраздела, а не строка воркера, и
        # это размещение несущее — панель обязана стоять ВНЕ контейнера
        # HTMX-опроса, иначе тик через двадцать секунд закрывал бы её сам, ровно
        # когда администратор читает, что именно будет потеряно. Строка воркера
        # (`admin/includes/worker_row.html`) панель не собирает: она только
        # диспетчеризует событие открытия и потребителем не является.
        "admin/workers.html",
        # Десятый вход добавлен планом 06-07: снятие задачи из очереди (D-17).
        # Размещение то же и по той же причине, что у соседа выше: панель
        # собирает СТРАНИЦА подраздела, а строка очереди
        # (`admin/includes/queue_row.html`) только диспетчеризует событие
        # открытия и потребителем не является. Действие необратимо — снятая
        # задача не восстанавливается ничем, — и гард повторной отправки ему
        # нужен ровно так же, как удалению сущности.
        "admin/queue.html",
    }
)

# Разметка панели, собранная в обход библиотеки. Гард живёт в макросе, поэтому
# самодельная копия панели его не унаследует — и обязана краснеть.
PANEL_MARKUP_MARKERS = ("modal__form", "modal__actions", "modal__panel")


def test_modal_guard_is_inherited_by_every_consumer():
    """Гард повторной отправки приходит к каждому потребителю ИЗ МАКРОСА.

    Тест работает в обе стороны: и новый импортёр, и исчезнувший его красят.
    Иначе восьмой потребитель, добавленный будущей фазой в обход библиотеки,
    остался бы без гарда молча — и заметил бы это только пользователь,
    удаливший сущность дважды.
    """
    consumers = {
        rel
        for rel, source in _all_templates()
        if MODAL_COMPONENT in source and rel != MODAL_COMPONENT
    }
    assert consumers == set(MODAL_CONSUMERS), (
        "множество потребителей панели разошлось с названным перечнем: "
        f"новые {sorted(consumers - MODAL_CONSUMERS)}; "
        f"исчезнувшие {sorted(MODAL_CONSUMERS - consumers)}"
    )

    # Слагаемое «+ 1» — САМ компонент components/modal.html: он попадает в счёт
    # MODAL_IMPORTERS, потому что строка импорта показана в его собственной
    # шапке-документации, но потребителем при этом не является. Расхождение
    # «семь против восьми» тут не ошибка счёта, и приводить числа к согласию
    # правкой одного из них нельзя — они считают РАЗНЫЕ множества.
    assert len(MODAL_CONSUMERS) + 1 == MODAL_IMPORTERS, (
        f"потребителей {len(MODAL_CONSUMERS)}, импортёров ожидается "
        f"{MODAL_IMPORTERS} — два счёта одного множества разошлись"
    )

    # Гард обязан быть в макросе: иначе наследовать потребителям нечего.
    assert GUARD_ATTR_RE.search(_template_source(MODAL_COMPONENT)), (
        "гард исчез из макроса — ни один потребитель его больше не наследует"
    )

    homemade = {}
    for rel in sorted(consumers):
        source = _template_source(rel)
        if not _macro_calls(source, "modal"):
            homemade[rel] = "импортирует панель, но макрос не вызывает"
            continue
        own = [marker for marker in PANEL_MARKUP_MARKERS if marker in source]
        if own:
            homemade[rel] = f"собирает разметку панели сам: {own}"

    assert not homemade, (
        "потребитель собирает панель в обход библиотеки — гарда повторной "
        "отправки он не унаследует: "
        + "; ".join(f"{rel} -> {why}" for rel, why in sorted(homemade.items()))
    )


def test_modal_site_inventory():
    """Инвентаризация мест подтверждения сходится ТРЕМЯ счётами.

    Счёт по импортёрам до числа мест дойти не может в принципе: файл подмены
    статуса панель сознательно не импортирует. Поэтому третий счёт — ПРЯМОЙ:
    сумма вхождений имени события открытия по всем шаблонам, КРОМЕ самого
    компонента. Компонент исключён потому, что имя стоит у него в слушателе
    макроса и в примере из шапки файла — два вхождения, которые местами
    применения не являются.
    """
    templates_ = _all_templates()

    importers = {rel for rel, source in templates_ if MODAL_COMPONENT in source}
    assert len(importers) == MODAL_IMPORTERS, (
        f"импортёров панели {len(importers)}, ожидалось {MODAL_IMPORTERS} "
        f"(семь потребителей плюс сам компонент — план 03-08 снял двух вместе "
        f"с глобальным разделом «Группы»): {sorted(importers)}"
    )

    names = set()
    places = 0
    for rel, source in templates_:
        if rel == MODAL_COMPONENT:
            continue
        found = MODAL_EVENT_RE.findall(source)
        names.update(found)
        places += len(found)

    assert len(names) == MODAL_EVENT_NAMES, (
        f"различных имён события открытия {len(names)}, ожидалось "
        f"{MODAL_EVENT_NAMES}: {sorted(names)}"
    )
    assert places == MODAL_PLACES, (
        f"мест подтверждения {places}, ожидалось {MODAL_PLACES} — место молча "
        "исчезло или появилось незаявленное"
    )


# --- issue #40: показ вложения идёт через ОДИН макрос -------------------------
#
# Мест показа вложения пять, и правило у них общее: спросить миниатюру, оставить
# полноразмерный адрес запасным. Собранное на месте пятое место унаследовало бы
# из этого правила ровно ничего и отличалось бы от четырёх остальных молча —
# заметил бы это пользователь, у которого одна картинка грузится быстро, а
# соседняя нет.

THUMB_COMPONENT = "components/thumb.html"

# Пять файлов-потребителей: полоса вложений и предпросмотр редактора, аватарка
# карточки списка, блоки миниатюр в истории и в админском экране истории.
THUMB_CONSUMERS = {
    "ads/form.html",
    "ads/includes/preview.html",
    "ads/includes/ad_card.html",
    "history/detail.html",
    "admin/user_history_detail.html",
}

# Элемент `img`, чей адрес строится ПРЕЖНИМИ выражениями напрямую. Именно это
# задача issue #40 и убирает из пяти файлов.
DIRECT_IMG_RE = re.compile(r"<img[^>]*src=\"\{\{\s*(?:get_image_url|resolve_image_url)")

# Ссылка на ПОЛНОРАЗМЕРНЫЙ объект в истории и админке. Миниатюра — способ
# ПОКАЗАТЬ, а не то, что открывается по клику.
FULL_SIZE_LINK_RE = re.compile(r"<a[^>]*href=\"\{\{\s*resolve_image_url")


def test_thumbnail_macro_is_the_only_way_an_attachment_is_shown():
    """Ни один потребитель не строит адрес картинки сам.

    Тест работает в обе стороны: и файл, вернувшийся к прямому выражению, и
    потребитель, потерявший импорт макроса, краснеют здесь. Проверяется ИСХОДНИК,
    потому что проверяемое — способ сборки, а не значение конкретного адреса.
    """
    direct = {
        rel: DIRECT_IMG_RE.findall(source)
        for rel, source in _all_templates()
        if DIRECT_IMG_RE.search(source)
    }
    assert not direct, (
        "элемент img строит адрес прежним выражением напрямую — миниатюры он не "
        f"запрашивает и запасного адреса не несёт: {sorted(direct)}"
    )

    silent = {
        rel
        for rel in sorted(THUMB_CONSUMERS)
        if THUMB_COMPONENT not in _template_source(rel)
    }
    assert not silent, (
        "место показа вложения не импортирует макрос миниатюры — правило показа "
        f"собрано в обход библиотеки: {sorted(silent)}"
    )


def test_thumbnail_macro_carries_both_addresses_and_a_one_shot_switch():
    """Свойства отката доказываются ОДИН раз — в макросе (P-8, D-6).

    Потребители наследуют их вызовом, поэтому утверждения на разметку макроса
    достаточно; что каждое из пяти мест зовёт именно его, держит тест выше.
    """
    source = _template_source(THUMB_COMPONENT)

    assert "thumb_image_url" in source, "макрос не запрашивает миниатюру"
    assert "data-full" in source, "запасной полноразмерный адрес потерян"
    assert "onerror" in source, "переключателя на запасной адрес нет"
    # Снятие обработчика с самого себя — защита от ЦИКЛА: без него отказ
    # запасного адреса запускал бы бесконечное переключение.
    assert "this.onerror=null" in source


def test_history_thumbnails_still_link_to_the_full_size_object():
    """Клик по миниатюре открывает полноразмерную картинку, а не миниатюру.

    Парный к структурному тесту выше: тот требует, чтобы `img` перестал строить
    адрес прежним выражением, и без этого утверждения его можно было бы
    «удовлетворить», переведя на миниатюру заодно и ссылку — то есть отняв у
    пользователя единственный способ разглядеть отправленное.
    """
    for rel in ("history/detail.html", "admin/user_history_detail.html"):
        assert FULL_SIZE_LINK_RE.search(_template_source(rel)), rel


# --- блокировка прокрутки: ПОВЕДЕНЧЕСКОЕ правило сноса панели (план 09-17) ---
#
# ⚠️ ПОЧЕМУ ПРАВИЛО ИСПОЛНЯЕТ ОБЪЕКТ, А НЕ ЧИТАЕТ РАЗМЕТКУ. Добавка
# `scroll-lock` (план 09-13) поднимает признак `is-modal-open` на элементе
# документа в `show()` и снимает его в `hide()`. Разметочное правило зеленело бы
# на ВХОЖДЕНИИ строки `classList.remove`, которая в `hide()` и так есть, — и
# ровно этот исход назван поимённо списком `missing:` отчёта верификации
# (09-VERIFICATION.md, гейп 1). Утверждать нужно не наличие строки, а СОСТОЯНИЕ
# документа после того, как узел панели СНЕСЁН, — а снос `hide()` не вызывает
# вовсе: ответ удаления уносит КОРЕНЬ панели внеполосным узлом
# (`delete_response.html:100` по `#group-del-N`).
#
# Путей ухода узла из документа ДВА (человек закрыл; ответ удаления снёс), а
# путь снятия признака сегодня ОДИН. Правила ниже утверждают равенство этих
# двух чисел ПОВЕДЕНИЕМ.
#
# ⚠️ ЛИНИЯ, КОТОРУЮ СУИТА НЕ ПЕРЕСЕКАЛА НИ РАЗУ: тесты идут транспортом ASGI и
# не исполняют ни строчки JS. Здесь она пересекается — объект `x-data`
# вырезается из ОТРИСОВАННОЙ разметки и исполняется в интерпретаторе JS со
# стаб-документом.
#
# ⚠️ СТАБЫ НЕЙМИТИРУЮЩИЕ РОВНО ТАМ, ГДЕ ПРЕДМЕТ. Список классов — настоящее
# множество с настоящими `add`/`remove`/`contains`; заглушка, всегда отвечающая
# «нет», построила бы зелёное правило. Всё остальное (`focus`,
# `querySelectorAll`, `$nextTick`) предметом не является и стабится.

APP_CSS = TEMPLATES_DIR.parent / "static" / "css" / "app.css"

# ⚠️ ИМЯ ПРИЗНАКА ИЗМЕРЕНО ПО ПРАВИЛУ ТАБЛИЦЫ СТИЛЕЙ, А НЕ ВЗЯТО ИЗ ПАМЯТИ
# (идиома SP-1, 09-PATTERNS.md). Значение выписано из селектора
# `app/static/css/app.css` (`.is-modal-open, .is-modal-open body { overflow:
# hidden }`); разъехавшись с ним, правила ниже начали бы проверять
# НЕСУЩЕСТВУЮЩИЙ признак и зеленели бы вакуумом. Сверка исполняется правилом
# положительного контроля, а не оставлена читателю.
SCROLL_LOCK_CLASS = "is-modal-open"

# Интерпретатор JS НОВОЙ ЗАВИСИМОСТЬЮ НЕ ЯВЛЯЕТСЯ: на нём собран `wa_worker/`,
# и `justfile` несёт его рецепты (`wa-worker-build`, `wa-workers`).
NODE_BIN = "node"

MODAL_XDATA_RE = re.compile(r'x-data="(\{.*?\})"', re.DOTALL)

MODAL_LIFECYCLE_HARNESS = """
'use strict';
const payload = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const LOCK = payload.lock;
const EXPRESSION = payload.expression;

function makeClassList() {
  const own = new Set();
  return {
    add(...names) { for (const n of names) { own.add(n); } },
    remove(...names) { for (const n of names) { own.delete(n); } },
    contains(name) { return own.has(name); }
  };
}

const documentElement = { classList: makeClassList() };
globalThis.document = {
  documentElement: documentElement,
  activeElement: { focus() {} }
};

function reset() { documentElement.classList = makeClassList(); }
function locked() { return documentElement.classList.contains(LOCK); }

function build() {
  const panel = (new Function('return (' + EXPRESSION + ');'))();
  panel.$nextTick = function (fn) { fn(); };
  panel.$refs = {
    cancel: { focus() {} },
    panel: { querySelectorAll() { return []; } }
  };
  return panel;
}

// СНОС УЗЛА выражается вызовом того метода объекта, который рантайм Alpine
// 3.13.3 зовёт при удалении поддерева. Нет метода — сносить нечем, и признак
// переживает уход панели.
function hasTeardown(panel) { return typeof panel.destroy === 'function'; }
function teardown(panel) { if (hasTeardown(panel)) { panel.destroy(); } }

function scenarioRaise() {
  reset();
  const panel = build();
  panel.show();
  return {
    raised: locked(),
    has_destroy: hasTeardown(panel),
    still_locked_after_teardown: null,
    repeat_matches: null
  };
}

function scenarioTeardown() {
  const runs = [];
  for (let i = 0; i < 2; i++) {
    reset();
    const panel = build();
    panel.show();
    const raised = locked();
    const has = hasTeardown(panel);
    teardown(panel);
    runs.push({ raised: raised, has_destroy: has, still_locked_after_teardown: locked() });
  }
  const same = JSON.stringify(runs[0]) === JSON.stringify(runs[1]);
  return Object.assign({}, runs[1], { repeat_matches: same });
}

function scenarioSibling() {
  reset();
  const open_panel = build();
  const closed_panel = build();
  open_panel.show();
  const raised = locked();
  const has = hasTeardown(closed_panel);
  teardown(closed_panel);
  return {
    raised: raised,
    has_destroy: has,
    still_locked_after_teardown: locked(),
    repeat_matches: null
  };
}

const SCENARIOS = { raise: scenarioRaise, teardown: scenarioTeardown, sibling: scenarioSibling };
const run = SCENARIOS[payload.scenario];
if (!run) {
  console.error('неизвестный сценарий: ' + payload.scenario);
  process.exit(2);
}
process.stdout.write(JSON.stringify(run()));
"""

# Подставленный путь снятия, ЗАВЕДОМО мёртвый: панель закрывает СЕБЯ и не
# трогает документ. Ключ объектного литерала, объявленный ПОСЛЕДНИМ, побеждает
# одноимённый объявленный раньше, — поэтому подстановка остаётся действенной и
# после того, как настоящий путь снятия в выражении появится.
DEAD_TEARDOWN = "destroy() { this.open = false; }"


def _modal_xdata_expression(html_source: str) -> str:
    """Исходник объекта ``x-data`` из ОТРИСОВАННОЙ разметки панели.

    Разбор идёт по отрисованному выводу, а не по исходнику шаблона: браузер
    получает именно его, и подстановка ``{{ id }}`` в имя атрибута
    ``x-on:modal-open-…`` к этому времени уже произошла.

    ⚠️ ГРАНИЦА РАЗБОРЩИКА НАЗЫВАЕТСЯ ЗДЕСЬ, А НЕ ОСТАВЛЯЕТСЯ НА ДОГАДКУ: он
    рассчитан на ОДНО выражение ``x-data`` в поданной разметке и утверждает это
    числом найденных вхождений. Разметка с двумя панелями сделала бы выбор
    вхождения молчаливым — и правило проверяло бы не ту панель.
    """
    found = MODAL_XDATA_RE.findall(html_source)
    assert len(found) == 1, (
        f"в поданной разметке {len(found)} выражений x-data, а не одно: "
        "разборщик рассчитан на одну панель, и выбор вхождения стал бы "
        "молчаливым"
    )
    return unescape(found[0])


def _xdata_with_dead_teardown(expression: str) -> str:
    """Подставленное выражение БЕЗ пути снятия на ветви сноса.

    ⚠️ ДВОЙНОЙ ПРЕДОХРАНИТЕЛЬ ПОДСТАНОВКИ — по образцу ``_tree_with``
    (tests/test_templates/test_htmx_markup_gates.py) и по той же причине:
    подстановка обязана доказать, что она что-то изменила, и что изменила
    ИМЕННО ТО. Образец — закрывающая скобка объектного литерала, и он
    встречается ровно один раз по построению: это последний символ выражения.
    Результат отдельно проверяется на отличие от исходника и на единственность
    вставленного пути.
    """
    source = expression.strip()
    assert source.endswith("}"), (
        "выражение x-data не кончается закрывающей скобкой объектного литерала: "
        "контроль подставляет не туда и потому не доказывает ничего"
    )
    assert DEAD_TEARDOWN not in source, (
        "мёртвый путь снятия уже стоит в выражении — подстановка ничего не "
        "добавляет, и контроль зелен по построению"
    )
    poisoned = source[:-1] + ", " + DEAD_TEARDOWN + " }"
    assert poisoned != source, "подстановка ничего не изменила"
    assert poisoned.count(DEAD_TEARDOWN) == 1, (
        "мёртвый путь снятия встречается в подставленном выражении не один раз"
    )
    return poisoned


def _run_modal_lifecycle(expression: str, scenario: str) -> dict:
    """Исполнить сценарий жизненного цикла панели в интерпретаторе JS.

    ⚠️ ОТСУТСТВИЕ ИНТЕРПРЕТАТОРА РОНЯЕТ ПРАВИЛО ГРОМКО, А НЕ ПРОПУСКАЕТ ЕГО.
    ``pytest.skip`` здесь не применяется НИ ПРИ КАКОЙ причине: пропущенное
    правило неотличимо от зелёного, и фаза оплатила этот класс однажды (WARN-4
    первого круга). Интерпретатор новой зависимостью не является — на нём
    собран ``wa_worker/``, и ``justfile`` несёт его рецепты.
    """
    if shutil.which(NODE_BIN) is None:
        pytest.fail(
            f"интерпретатор JS `{NODE_BIN}` не найден в PATH, и правило сноса "
            "панели исполнить нечем. Пропуск здесь запрещён: пропущенное "
            "правило неотличимо от зелёного. Интерпретатор в проекте уже "
            "есть — на нём собран wa_worker/, рецепты justfile: "
            "wa-worker-build, wa-workers"
        )
    payload = json.dumps(
        {"expression": expression, "scenario": scenario, "lock": SCROLL_LOCK_CLASS}
    )
    proc = subprocess.run(
        [NODE_BIN, "-e", MODAL_LIFECYCLE_HARNESS],
        input=payload,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        pytest.fail(
            f"гарнир жизненного цикла панели вернул код {proc.returncode} на "
            f"сценарии {scenario!r}; вывод ошибки:\n{proc.stderr.strip()}"
        )
    try:
        return json.loads(proc.stdout.strip())
    except json.JSONDecodeError:  # pragma: no cover — диагностический путь
        pytest.fail(
            "гарнир не вернул вердикт разбираемой строкой; получено: "
            f"{proc.stdout.strip()!r}"
        )


def test_the_panel_raises_the_scroll_lock_when_it_opens():
    """ПОЛОЖИТЕЛЬНЫЙ КОНТРОЛЬ (антивакуум): признак вообще поднимается.

    Без этого утверждения несущее правило ниже зелено ВАКУУМОМ на панели,
    которая признака не поднимала никогда. Заодно сверяется само имя признака:
    правило читает таблицу стилей и роняет прогон, если селектора с этим именем
    там нет, — измеренная константа, разъехавшаяся с источником, проверяла бы
    несуществующее свойство.
    """
    css = APP_CSS.read_text(encoding="utf-8")
    assert f".{SCROLL_LOCK_CLASS}" in css, (
        f"селектора .{SCROLL_LOCK_CLASS} в {APP_CSS.name} нет: измеренная "
        "константа разъехалась с правилом таблицы стилей, и правила ниже "
        "проверяли бы признак, который ничего не блокирует"
    )

    verdict = _run_modal_lifecycle(_modal_xdata_expression(_modal_block()), "raise")

    assert verdict["raised"] is True, (
        f"после show() признака {SCROLL_LOCK_CLASS} на документе нет — панель "
        "блокировку прокрутки не поднимает вовсе, и утверждения о её снятии "
        f"доказывали бы ровно ничего; вердикт: {verdict}"
    )


def test_the_scroll_lock_never_survives_the_teardown_of_the_panel():
    """НЕСУЩЕЕ: снос узла панели оставляет документ БЕЗ признака блокировки.

    Путей ухода узла из документа два — человек закрыл (``hide()``) и ответ
    удаления унёс КОРЕНЬ панели внеполосным узлом (``hide()`` не вызывается
    вовсе). Путей снятия признака обязано быть столько же.

    Цена отказа: ``<html>`` остаётся с классом, ``overflow: hidden`` держится, и
    экран, весь смысл которого — бесконечная прокрутка, перестаёт достигать
    своего сентинела. Признак отказа МОЛЧАЛИВЫЙ: 200, чистая консоль, честная
    линейка счётчика.

    Сценарий исполняется ДВАЖДЫ подряд и обязан дать тот же исход — ребро
    ``idempotency`` (QUAL-01).
    """
    verdict = _run_modal_lifecycle(_modal_xdata_expression(_modal_block()), "teardown")

    assert verdict["raised"] is True, (
        f"признак не поднялся — сценарий сноса проверял бы пустое место: {verdict}"
    )
    assert verdict["has_destroy"] is True, (
        "у объекта x-data панели НЕТ пути снятия на ветви сноса узла: рантайм "
        "Alpine зовёт при удалении поддерева метод, которого у объекта нет, и "
        f"снимать признак {SCROLL_LOCK_CLASS} на htmx-пути удаления нечем; "
        f"вердикт: {verdict}"
    )
    assert verdict["still_locked_after_teardown"] is False, (
        f"после сноса узла панели признак {SCROLL_LOCK_CLASS} остался на "
        'документе: правило overflow: hidden держится, hx-trigger="revealed" '
        "сентинела не срабатывает больше никогда, и остаток списка становится "
        f"недостижимым; вердикт: {verdict}"
    )
    assert verdict["repeat_matches"] is True, (
        "повторное исполнение сценария сноса дало ДРУГОЙ исход: снятие признака "
        f"при сносе не идемпотентно; вердикт: {verdict}"
    )


def test_the_teardown_of_a_closed_panel_keeps_an_open_sibling_locked():
    """Снос ЗАКРЫТОЙ соседней панели НЕ отпирает документ у открытой.

    Путь снятия на ветви сноса обязан быть защищён проверкой СОБСТВЕННОГО
    состояния панели. Без неё снос любой закрытой соседки — а он происходит при
    каждой подмене строки тумблером — снимал бы блокировку у открытой, и
    шестнадцать мест подтверждения Фазы 10 начали бы отпирать документ друг за
    другом.

    Ребро ``concurrency`` (QUAL-01) снимается ЭТИМ сценарием: две панели,
    живущие в документе одновременно. Параллельного исполнения в живом браузере
    суита не поднимает, и шире измеренного здесь не утверждается.
    """
    verdict = _run_modal_lifecycle(_modal_xdata_expression(_modal_block()), "sibling")

    assert verdict["raised"] is True, (
        f"открытая панель признака не подняла — сценарий беспредметен: {verdict}"
    )
    assert verdict["has_destroy"] is True, (
        "у объекта x-data панели нет пути снятия на ветви сноса, поэтому "
        "утверждение о защите открытой соседки проверяло бы отсутствующий "
        f"механизм; вердикт: {verdict}"
    )
    assert verdict["still_locked_after_teardown"] is True, (
        "снос ЗАКРЫТОЙ соседней панели снял блокировку у ОТКРЫТОЙ: путь снятия "
        "на ветви сноса не защищён проверкой собственного состояния панели; "
        f"вердикт: {verdict}"
    )


def test_control_negative_a_panel_without_a_teardown_path_stays_locked():
    """ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ: гарнир обязан уметь сказать «заперто».

    Тот же гарнир, поданный ПОДСТАВЛЕННОМУ выражению, чей путь снятия на ветви
    сноса заведомо мёртв, обязан сообщить, что признак пережил снос. Без этого
    контроля гарнир доказывает работоспособность гарнира, а не свойство
    компонента.
    """
    poisoned = _xdata_with_dead_teardown(_modal_xdata_expression(_modal_block()))

    verdict = _run_modal_lifecycle(poisoned, "teardown")

    assert verdict["raised"] is True, (
        f"подставленное выражение признака не поднимает: {verdict}"
    )
    assert verdict["still_locked_after_teardown"] is True, (
        "гарнир сообщил «отперто» о выражении, у которого пути снятия на ветви "
        "сноса нет: он доказывает не свойство компонента, а собственную "
        f"работоспособность; вердикт: {verdict}"
    )


# Идентификаторы, которые ответ удаления уносит внеполосным снятием, и
# идентификатор КОРНЯ панели подтверждения.
OOB_DELETE_ID_RE = re.compile(r'<div id="([^"]+)"[^>]*hx-swap-oob="delete"')
MODAL_ROOT_ID_RE = re.compile(r'<div class="modal" id="([^"]+)"')


def test_the_delete_response_removes_the_very_node_that_owns_the_scroll_lock():
    """Узел, который уносит ответ, и узел, который владеет признаком, — ОДИН.

    Разъехавшись, эти два места сделали бы починку беспредметной МОЛЧА: ответ
    снимал бы один узел, а признак блокировки жил бы на другом. Совпадение
    утверждается, а не предполагается.

    Правило верно независимо от механизма блокировки — и именно оно остаётся
    записанной причиной, по которой любое документное состояние этого
    компонента обязано иметь путь снятия на ветви сноса.
    """
    response = ENV.get_template(
        "account_groups/partials/delete_response.html"
    ).render(group_id=7, active_groups=1, total_groups=2)
    removed = set(OOB_DELETE_ID_RE.findall(response))
    assert removed, (
        "ответ удаления не уносит ни одного узла внеполосным снятием — "
        "утверждение о тождестве проверяло бы пустое множество"
    )

    panel = ENV.from_string(
        "{% from 'components/modal.html' import modal %}"
        "{{ modal(id='group-del-' ~ group_id, title='Удалить группу?',"
        " action='/accounts/1/groups/7/delete', confirm_label='Удалить') }}"
    ).render(group_id=7)
    root = MODAL_ROOT_ID_RE.search(panel)
    assert root is not None, (
        "у корня панели подтверждения нет идентификатора — уносить ответу нечего"
    )

    assert root.group(1) in removed, (
        f"ответ удаления уносит {sorted(removed)}, а корень панели — "
        f"{root.group(1)!r}: узел, который уходит, и узел, который владеет "
        "признаком блокировки, РАЗЪЕХАЛИСЬ, и починка ветви сноса стала бы "
        "беспредметной молча"
    )
