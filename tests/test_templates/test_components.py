"""Wave 0: UI-04 — прямой рендер макросов библиотеки компонентов без HTTP.

В проекте до этого не было ни одного теста, рендерящего шаблон напрямую.
Паттерн вводится здесь: берём окружение Jinja из ``app.pages.common`` и
вызываем ``get_template(...).module.<macro>(...)``.

Почему именно так, а не через страницу: макрос, случайно взявший данные из
контекста вызывающего шаблона, отрендерится ПУСТОЙ строкой, а страница всё
равно вернёт 200. Прямой рендер с пустым контекстом ловит это сразу.
"""

import ast
import json
import re
import shutil
from html import unescape
from pathlib import Path
from typing import NamedTuple

import pytest

from app.pages import notices as app_notices
from app.pages.common import templates

# ⚠️ ИМЯ ЗАГОЛОВКА ПЕРЕХОДА БЕРЁТСЯ ИМПОРТОМ ИЗ ОБЪЯВЛЯЮЩЕГО ЕГО МОДУЛЯ, А НЕ
# НАБИРАЕТСЯ СТРОКОЙ. Литерал, набранный здесь руками, пережил бы переименование
# константы МОЛЧА: разбор перестал бы находить место сборки, антивакуум покраснел
# бы не тем текстом, а до его правки правило было бы вакуумно-зелёным. Модуль
# берётся ЦЕЛИКОМ вдобавок к константе — им разрешаются имена, приехавшие в
# чужой исходник импортом (см. `_resolvable_string_names`).
from app.pages import htmx as app_htmx
from app.pages.htmx import HX_LOCATION_HEADER
from tests.conftest import run_node_script

# ⚠️ ТРИ ЧИСЛА КРИТЕРИЯ 3 ВЕХИ БЕРУТСЯ ИМПОРТОМ ИЗ ОБЪЯВЛЯЮЩИХ ИХ МОДУЛЕЙ, А НЕ
# ВТОРЫМИ ЭКЗЕМПЛЯРАМИ. Вторая копия числа или выражения разошлась бы с первой
# МОЛЧА: правило проверяло бы устаревшее значение при зелёном соседе. Та же
# доктрина единственного источника, по которой `test_htmx_response_layer.py`
# импортирует помощников входа под чужой личностью, а модуль правил
# безопасности разметки — разборщик комментариев. См. раздел критерия 3 ниже.
from tests.test_templates.test_htmx_inventory import _strip_comments
from tests.test_templates.test_htmx_markup_gates import (
    CLIENT_STATE_NODES,
    _all_templates as _all_templates_under,
    _client_state_sites,
)
from tests.test_templates.test_htmx_markup_security import INLINE_HANDLER_ATTR

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


def _modal_block_source(fields: str = HIDDEN_FIELD, body: str | None = None) -> str:
    """ИСХОДНИК шаблона, собирающего панель блочным вызовом.

    ⚠️ ВЫНЕСЕН ИЗ `_modal_block` ФАЗОЙ 10 (план 10-09), А НЕ ЗАВЕДЁН ВТОРЫМ
    СБОРЩИКОМ. Отрицательному контролю инвентаря слотов нужен ИСХОДНИК с
    блочным вызовом, а не отрисованная разметка; второй сборщик той же формы
    разошёлся бы с этим молча — и контроль стерёг бы вызов, которого в проекте
    нет. Сборщик ОДИН, а рендер стал его потребителем.
    """
    body_arg = f", body={body!r}" if body is not None else ""
    return (
        "{% from 'components/modal.html' import modal %}"
        "{% call modal(id='del-bulk', title='Удалить выбранные элементы?',"
        f" action='{SLOT_TEST_ACTION}', confirm_label='Удалить'" + body_arg + ") %}"
        + fields
        + "{% endcall %}"
    )


def _modal_block(fields: str = HIDDEN_FIELD, body: str | None = None) -> str:
    """Отрендерить модалку блочным вызовом с произвольными полями формы."""
    return ENV.from_string(_modal_block_source(fields, body)).render()


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
    over_htmx = render("components/modal.html", "modal", **MODAL_ARGS)
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


# ⚠️ РЕНДЕРНАЯ ПОЛОВИНА КРИТЕРИЯ 1 ФАЗЫ 10 (D-14). Два правила ниже по файлу —
# `test_modal_guard_is_inherited_by_every_consumer` и `test_modal_site_inventory`
# — читают ИСХОДНИКИ шаблонов. Это правило ИСПОЛНЯЕТ рендер макроса без единого
# дополнительного аргумента и смотрит на ОТРЕНДЕРЕННУЮ разметку. Предметы
# разные, поэтому правило заведено НОВЫМ, а не влито в них: слитое дало бы
# одному правилу два предмета и потеряло бы различимость отказа.
#
# ⚠️ ЭТО МАШИННАЯ ПРОВЕРКА ТОГО, ЧТО «ОДНА ПРАВКА» РАСХОДИТСЯ НА ВСЕХ. До Фазы 10
# набор свойств качества приезжал только тому вызывающему, который ПЕРЕДАЛ
# признак отправки; правило, рендерящее макрос без аргументов, на том состоянии
# КРАСНОЕ. Зелёное оно означает ровно одно: htmx приходит ко всем 18 местам
# подтверждения из макроса, а не из дисциплины вызывающих.
PANEL_SENDING_STATE_ATTRS = (
    'hx-post="/ads/1/delete"',
    'hx-swap="none"',
    'hx-disabled-elt="find button[type=submit]"',
    'hx-indicator="find .form-busy"',
)


def test_the_panel_hands_the_sending_state_to_every_call_site():
    """Набор свойств качества приходит вызывающему БЕЗ ЕДИНОГО АРГУМЕНТА.

    ⚠️ АДРЕС ОТПРАВКИ ПЕЧАТАЕТ ТУ ЖЕ ПЕРЕМЕННУЮ, ЧТО И `action` ФОРМЫ, и
    посимвольное их равенство утверждается здесь, а не проверяется глазами:
    два разных выражения с одинаковым результатом считаются нарушением
    осознанно — иначе маршрут htmx-пути и маршрут пути деградации разъехались
    бы молча.
    """
    out = render("components/modal.html", "modal", **MODAL_ARGS)
    form = _form_tag(out)

    missing = [attr for attr in PANEL_SENDING_STATE_ATTRS if attr not in form]
    assert not missing, (
        "макрос панели раздаёт свойства качества не всем вызывающим — без "
        f"аргументов не приехало: {missing}; тег формы: {form!r}"
    )

    assert f'action="{MODAL_ARGS["action"]}"' in form, (
        "форма панели перестала быть настоящей формой POST: путь деградации "
        "лишился адреса"
    )

    assert '<span class="form-busy" aria-hidden="true"></span>' in out, (
        "узел индикатора приходит не всем панелям — часть мест подтверждения "
        "осталась бы без порога видимости, а высоты панелей разъехались бы"
    )

    assert "{%" not in form and "{{" not in form, (
        f"в отрендеренном теге формы осталась конструкция шаблонизатора: {form!r}"
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
    # План 11-11 ПЕРЕНЁС это место, а не снял и не добавил: форма-триггер
    # удаления переехала со страницы карточки во включаемый шаблон блока
    # «Действия» дословно (D-02 Фазы 11), панель осталась на странице. Число
    # мест прежнее; сменился только файл, где форма написана.
    RowDeleteSite(
        "admin/includes/user_actions.html", r"/admin/users/[^\"]+/delete", 1
    ),
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

# Набор свойств качества, который потребитель обязан унаследовать БЕЗУСЛОВНО
# (Фаза 10, план 10-01, D-14). Предмет здесь — ИСХОДНИК макроса, поэтому адрес
# отправки записан ПЕРЕМЕННОЙ, а не значением: правило G-4 сравнивает СЫРЫЕ
# строки шаблона, и совпадение `hx-post` с `action` держится тем, что оба
# печатают одно и то же выражение.
# ⚠️ ЗАПИСЬ ВОЗВРАТА СОСТОЯНИЯ ДОПОЛНЕНА ФАЗОЙ 10 (план 10-02, D-12), И ЭТО НЕ
# ПОДГОНКА ПОД ПРАВКУ. Прежняя запись — `x-on:htmx:after-request="sending =
# false"` — после появления ветви по успешности обмена перестала встречаться в
# теге ДОСЛОВНО, и правило покраснело бы на СВОЁМ ЖЕ выигрыше. Сужать её до
# имени атрибута нельзя: набор здесь стережёт БЕЗУСЛОВНОСТЬ печати вместе со
# ЗНАЧЕНИЕМ, а имя атрибута без значения зеленело бы на пустом выражении.
# Значение поэтому выписано ЦЕЛИКОМ, и ветвь входит в охраняемое: потеряв её,
# панель начнёт закрываться на любом завершении запроса, и краснеть это обязано
# ЗДЕСЬ ТОЖЕ, а не только у поведенческого правила.
# ⚠️ ЗНАЧЕНИЕ СДВИНУЛОСЬ ВТОРИЧНО (план 10-05), И ОСНОВАНИЕ АБЗАЦА ВЫШЕ ОТ ЭТОГО
# НЕ ИЗМЕНИЛОСЬ. Ветвь, заведённая планом 10-02, была МЕРТВА на транспорте
# перехода — признак успешности события на нём не присваивается вовсе (гейп 1
# отчёта верификации фазы), — и к ней прибавлен ЯВНЫЙ дизъюнкт транспорта. Он
# входит в охраняемое ровно по той же причине, что и первый: панель, потерявшая
# его, снова перестанет закрываться на 16 из 18 мест, и покраснеть это обязано
# ЗДЕСЬ ТОЖЕ. Форма записана ЭКРАНИРОВАННОЙ, потому что набор сличается с СЫРОЙ
# строкой шаблона, а не с отрисованной разметкой.
# ⚠️ ГЛАГОЛ ФОРМЫ ВНЕСЁН В НАБОР ФАЗОЙ 10 (план 10-09, WR-03), И ЭТО НЕ
# ДУБЛИРОВАНИЕ СОСЕДНЕГО ГЕЙТА. Сосед сличает глагол двух КОПИЙ (панель и
# макрос-обёртка) и сводит параметрическое значение к умолчанию — то есть глагол,
# вернувшийся ПАРАМЕТРОМ с тем же умолчанием, для него неотличим от литерала.
# Здесь же набор сличается с СЫРОЙ строкой шаблона и стережёт БЕЗУСЛОВНОСТЬ
# ПЕЧАТИ: через этот набор глагол наследуют все 18 мест подтверждения, и
# параметрическая форма записи краснеет ЗДЕСЬ ЖЕ, а не у соседа.
PANEL_QUALITY_SOURCE_PROPERTIES = (
    'method="post"',
    'hx-post="{{ action }}"',
    'hx-swap="none"',
    'hx-disabled-elt="find button[type=submit]"',
    'hx-indicator="find .form-busy"',
    (
        'x-on:htmx:after-request="sending = false; '
        "if ($event.detail.successful || ($event.detail.xhr &amp;&amp; "
        "$event.detail.xhr.getResponseHeader('HX-Location'))) hide()\""
    ),
)


MODAL_SIGNATURE_RE = re.compile(r"\{%-?\s*macro\s+modal\((.*?)\)\s*-?%\}", re.S)
MODAL_CALL_RE = re.compile(r"(?<![\w.])modal\s*\(", re.S)
KWARG_NAME_RE = re.compile(r"(?<![\w.])([A-Za-z_]\w*)\s*=(?!=)")


def _modal_signature_names(source: str) -> set[str]:
    """Имена параметров сигнатуры макроса панели."""
    match = MODAL_SIGNATURE_RE.search(source)
    if not match:
        return set()
    return {
        part.split("=", 1)[0].strip()
        for part in _split_top_level(match.group(1))
        if part.strip()
    }


def _split_top_level(argument_text: str) -> list[str]:
    """Разбить список аргументов по запятым ВЕРХНЕГО УРОВНЯ.

    Наивный `split(',')` разорвал бы вложенный вызов и литерал со списком, и
    разборщик выдал бы имена, которых в исходнике нет.
    """
    parts, depth, current = [], 0, []
    for char in argument_text:
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    parts.append("".join(current))
    return parts


def _modal_call_kwargs(source: str) -> set[str]:
    """Имена ИМЕНОВАННЫХ АРГУМЕНТОВ всех вызовов панели в одном шаблоне.

    Объявление макроса вызовом не считается — по той же форме, что и в
    `_macro_calls`: иначе компонент объявил бы сам себя своим вызывающим.
    """
    names: set[str] = set()
    for match in MODAL_CALL_RE.finditer(source):
        if source[: match.start()].rstrip().endswith("macro"):
            continue
        depth, end = 1, match.end()
        while end < len(source) and depth:
            if source[end] in "([{":
                depth += 1
            elif source[end] in ")]}":
                depth -= 1
            end += 1
        for part in _split_top_level(source[match.end() : end - 1]):
            found = KWARG_NAME_RE.match(part.strip())
            if found:
                names.add(found.group(1))
    return names


MODAL_BLOCK_CALL_RE = re.compile(r"\{%-?\s*call\s+modal\s*\(", re.S)
ENDCALL_RE = re.compile(r"\{%-?\s*endcall\s*-?%\}")

# ⚠️ НАРУШИТЕЛЬ РАСПОЗНАЁТСЯ ПО ПРЕФИКСУ АТРИБУТА СЛОЯ ПИСЬМА, А НЕ ПО ПЕРЕЧНЮ
# ИМЁН. Перечень устарел бы на первом же атрибуте, которого в нём нет, а предмет
# запрета — ЛЮБОЙ запрос, поднятый изнутри слота, а не четыре знакомых глагола.
WRITE_LAYER_ATTR_PREFIX = "hx-"
WRITE_LAYER_ATTR_RE = re.compile(
    rf"(?<![-\w]){re.escape(WRITE_LAYER_ATTR_PREFIX)}[a-z-]+\s*="
)


def _modal_call_slots(templates: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Тела БЛОЧНЫХ вызовов панели: пары «путь шаблона → текст слота».

    Границы аргументов считаются вложенностью скобок — той же формой, что и у
    `_modal_call_kwargs`: наивный поиск закрывающей скобки разорвал бы вызов с
    вложенным вызовом в аргументе (`queue_drop_modal_id(...)` в админской
    очереди — ровно такой случай), и разборщик выдал бы слот, которого нет.

    ⚠️ САМ КОМПОНЕНТ ИСКЛЮЧЁН ТЕМ ЖЕ ПРИЁМОМ, ЧТО И В ИНВЕНТАРЕ МЕСТ: в его
    шапке стоит ДОКУМЕНТНАЯ ВЫДЕРЖКА блочного вызова, которую эти же регулярные
    выражения разбирают неотличимо от настоящего вызова. Не исключив её,
    инвентарь объявил бы компонент своим же четвёртым вызывающим.
    """
    slots: list[tuple[str, str]] = []
    for rel, source in templates:
        if rel == MODAL_COMPONENT:
            continue
        for match in MODAL_BLOCK_CALL_RE.finditer(source):
            depth, end = 1, match.end()
            while end < len(source) and depth:
                if source[end] in "([{":
                    depth += 1
                elif source[end] in ")]}":
                    depth -= 1
                end += 1
            opened = source.index("%}", end - 1) + 2
            closing = ENDCALL_RE.search(source, opened)
            assert closing, (
                f"{rel}: блочный вызов панели не закрыт — разбор слота пошёл бы "
                "до конца файла и утверждал бы не про слот"
            )
            slots.append((rel, source[opened : closing.start()]))
    return slots


def _slot_offenders(slots: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Слоты, несущие СВОЙ запрос атрибутом слоя письма."""
    return [(rel, text) for rel, text in slots if WRITE_LAYER_ATTR_RE.search(text)]


def _macro_form_tag(source: str) -> str:
    """Открывающий тег формы панели В ИСХОДНИКЕ — от «<form» до первого «>».

    ⚠️ ГРАНИЦА ОБРЫВАЕТСЯ НА ПЕРВОМ «>» НАМЕРЕННО, той же формой, что и у
    разборщиков гейтов разметки: символ конца тега внутри значения атрибута
    сделал бы разбор неотличимым от разбора соседнего узла.
    """
    start = source.index('<form class="modal__form"')
    return source[start : source.index(">", start) + 1]


def test_modal_guard_is_inherited_by_every_consumer():
    """Гард повторной отправки приходит к каждому потребителю ИЗ МАКРОСА.

    Тест работает в обе стороны: и новый импортёр, и исчезнувший его красят.
    Иначе восьмой потребитель, добавленный будущей фазой в обход библиотеки,
    остался бы без гарда молча — и заметил бы это только пользователь,
    удаливший сущность дважды.

    ⚠️ ПРАВИЛО РАСШИРЕНО ФАЗОЙ 10 (план 10-01, D-14): прибавлено утверждение
    БЕЗУСЛОВНОСТИ унаследованного — набор свойств качества стои́т в исходнике
    макроса ВНЕ какого-либо условия шаблонизатора. До правки фазы атрибуты
    печатались под условием, и это утверждение было КРАСНЫМ; четыре прежних
    утверждения правила при этом не тронуты ни на символ и своих вердиктов не
    меняют. ЧИСЛА НЕ ДВИНУЛИСЬ — потребителей по-прежнему 10, импортёров 11, — и
    ИМЕННО ЭТО доказывает, что рычаг фазы инвентаря не тронул: расширение
    добавляет утверждение о свойстве, которого до фазы не существовало, а не
    новое место.

    ⚠️ НЕ ПУТАТЬ С `test_the_panel_hands_the_sending_state_to_every_call_site`:
    у того ДРУГОЙ ПРЕДМЕТ — он ИСПОЛНЯЕТ рендер макроса без аргументов и смотрит
    на отрендеренную разметку, а это правило и его сосед по инвентарю читают
    ИСХОДНИКИ. Строка нужна затем, чтобы следующий читатель не «починил»
    расширение обратно, приняв его за дублирование.
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

    # РАСШИРЕНИЕ ФАЗЫ 10: УНАСЛЕДОВАННОЕ ПРИХОДИТ БЕЗУСЛОВНО.
    #
    # Потребитель наследует из макроса не только гард повторной отправки, но и
    # весь набор свойств качества htmx. Пока они стояли под условием
    # шаблонизатора, «унаследовано» означало «унаследовано ТЕМ, КТО ПОПРОСИЛ», и
    # различить это утверждениями выше было нельзя: они смотрят на потребителя,
    # а условие живёт в макросе.
    form_tag = _macro_form_tag(_template_source(MODAL_COMPONENT))
    conditional = [
        prop for prop in PANEL_QUALITY_SOURCE_PROPERTIES if prop not in form_tag
    ]
    assert not conditional, (
        "свойство качества пропало из открывающего тега формы панели — "
        f"потребители его не унаследуют: {conditional}"
    )
    assert "{%" not in form_tag, (
        "в открывающем теге формы панели снова появилась конструкция "
        "шаблонизатора: унаследованное перестало быть БЕЗУСЛОВНЫМ, и место "
        "подтверждения может молча остаться без htmx — "
        f"{form_tag!r}"
    )


def test_modal_site_inventory():
    """Инвентаризация мест подтверждения сходится ЧЕТЫРЬМЯ счётами.

    Счёт по импортёрам до числа мест дойти не может в принципе: файл подмены
    статуса панель сознательно не импортирует. Поэтому третий счёт — ПРЯМОЙ:
    сумма вхождений имени события открытия по всем шаблонам, КРОМЕ самого
    компонента. Компонент исключён потому, что имя стоит у него в слушателе
    макроса и в примере из шапки файла — два вхождения, которые местами
    применения не являются.

    ⚠️ ЧЕТВЁРТЫЙ СЧЁТ ПРИБАВЛЕН ФАЗОЙ 10 (план 10-01, D-14): множество ИМЁН
    ИМЕНОВАННЫХ АРГУМЕНТОВ, передаваемых вызывающими по всем шаблонам, есть
    ПОДМНОЖЕСТВО имён сигнатуры макроса. Он стережёт свойство, которого до фазы
    не существовало: пока признак отправки был параметром, «одна правка»
    держалась дисциплиной вызывающих, а не устройством макроса. Снятый параметр,
    возвращённый вызывающим по невнимательности, теперь называется ПОИМЁННО и с
    файлом, а не роняет шаблон в бою.

    ⚠️ ТРИ ДЕЙСТВУЮЩИХ СЧЁТА И ИХ ЧИСЛА (11 / 9 / 18) НЕ ТРОНУТЫ НИ НА СИМВОЛ, и
    их НЕПОДВИЖНОСТЬ есть доказательство того, что рычаг фазы инвентаря не
    тронул: мест не прибавилось и не убыло, изменилось лишь то, ОТКУДА они
    получают htmx.
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

    # --- ЧЕТВЁРТЫЙ СЧЁТ: аргументы вызывающих ⊆ сигнатура макроса ------------
    signature = _modal_signature_names(_template_source(MODAL_COMPONENT))
    assert signature, "сигнатура макроса панели не разобралась — счёт вакуумен"

    passed: dict[str, set[str]] = {}
    for rel, source in templates_:
        if rel == MODAL_COMPONENT:
            continue
        for name in _modal_call_kwargs(source):
            passed.setdefault(name, set()).add(rel)

    # АНТИВАКУУМ: разборщик, вернувший пустое множество, зеленел бы на любом
    # дереве — и зелёный цвет сломанного разборщика посимвольно совпадал бы с
    # зелёным цветом соблюдённого правила. Вызывающие панели передают именованные
    # аргументы всегда: без `title` и `action` панель не собирается вовсе.
    assert passed, (
        "разборщик вызовов панели не нашёл НИ ОДНОГО именованного аргумента — "
        "счёт вакуумен, и правило перестало отличать соблюдение от поломки"
    )

    unknown = {name: sorted(files) for name, files in passed.items() if name not in signature}
    assert not unknown, (
        "вызывающий передаёт панели имя, которого в её сигнатуре нет — снятый "
        "параметр вернулся или имя разошлось с макросом: "
        + "; ".join(f"{name} <- {files}" for name, files in sorted(unknown.items()))
    )


# --- ГЛАГОЛ ФОРМЫ ПАНЕЛИ — ЛИТЕРАЛ, А НЕ ПАРАМЕТР (WR-03) -------------------
#
# ⚠️ ПРЕДМЕТ ПРАВИЛА — ЕДИНСТВЕННОЕ ДОСТИЖИМОЕ СЛЕДСТВИЕ ПАРАМЕТРА, А НЕ
# САМ ПАРАМЕТР. Пока глагол формы приходил параметром, вызывающий мог
# собрать панель, у которой БЕЗ JavaScript форма уходит ОДНИМ глаголом, а
# через слой письма — ДРУГИМ: адрес htmx-запроса печатается макросом БЕЗУСЛОВНО
# и глаголом формы не управляется вовсе. Разъезд двух путей был бы виден
# только тому, у кого JavaScript отключён, — то есть ровно тому, кого гейты
# деградации и защищают, — и случился бы на РАЗРУШИТЕЛЬНОМ действии.
#
# ⚠️ ИМЯ ИЩЕТСЯ РАЗБОРЩИКОМ СИГНАТУРЫ, А НЕ ПОДСТРОКОЙ: подстрока `method`
# стоит в шапке компонента законно (комментарий о литерале) и в самом
# открывающем теге формы — поиск подстрокой давал бы вердикт по чужому поводу.

MODAL_VERB_LITERAL = 'method="post"'

# СИНТЕТИЧЕСКИЙ ИСХОДНИК ОТРИЦАТЕЛЬНОГО КОНТРОЛЯ: панель с
# ПАРАМЕТРИЧЕСКИМ глаголом — то состояние рычага, которое правило обязано
# краснить. После правки такого исходника в дереве нет и читать его неоткуда:
# он собирается СТРОКОЙ здесь. Без контроля правило зеленело бы на СЛОМАННОМ
# разборщике посимвольно так же, как на соблюдённом свойстве (D-13 Фазы 8).
MODAL_PARAMETRIC_VERB_FIXTURE = (
    '{% macro modal(id, title, action, confirm_label, method="post") -%}\n'
    '<form class="modal__form" method="{{ method }}" action="{{ action }}">\n'
    "</form>\n"
    "{%- endmacro %}"
)


def test_the_panel_verb_is_a_literal_and_not_a_parameter():
    """НЕСУЩЕЕ: глагол формы панели — ЛИТЕРАЛ, и вызывающий им не управляет.

    Два утверждения и отрицательный контроль в ТОМ ЖЕ правиле: имени глагола
    в сигнатуре НЕТ, а в открывающем теге формы он СТОИТ литералом. Одно без
    другого не годится: снятый параметр без литерала оставил бы форму без
    глагола вовсе (браузер ушёл бы GET-ом на разрушительное действие), а литерал
    при живом параметре был бы мёртвым украшением.

    ⚠️ НЕ ПУТАТЬ С ГЕЙТОМ СЛИЧЕНИЯ ДВУХ КОПИЙ (D-16): тот сличает глагол
    панели с глаголом макроса-обёртки и сводит параметрическое значение к умолчанию,
    то есть параметр, вернувшийся с тем же умолчанием, ему неотличим от литерала.
    Отличить их умеет только это правило.
    """
    source = _template_source(MODAL_COMPONENT)

    signature = _modal_signature_names(source)
    assert signature, "сигнатура макроса панели не разобралась — правило вакуумно"
    assert "method" not in signature, (
        "глагол формы панели стоит ПАРАМЕТРОМ сигнатуры: вызывающий "
        "может собрать панель, которая без JavaScript уходит одним глаголом, а "
        "через слой письма — другим, и сделает это на разрушительном действии: "
        f"{sorted(signature)}"
    )

    form_tag = _macro_form_tag(source)
    assert MODAL_VERB_LITERAL in form_tag, (
        "в открывающем теге формы панели глагол печатается НЕ ЛИТЕРАЛОМ: "
        f"{MODAL_VERB_LITERAL!r} в теге не найден — {form_tag!r}"
    )

    # --- ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ: те же два разборщика на синтетике ---
    assert MODAL_PARAMETRIC_VERB_FIXTURE != source, (
        "синтетический исходник контроля совпал с прочитанным из шаблона — "
        "контроль перестал проверять ПРОТИВОПОЛОЖНОЕ состояние"
    )
    control_signature = _modal_signature_names(MODAL_PARAMETRIC_VERB_FIXTURE)
    control_tag = _macro_form_tag(MODAL_PARAMETRIC_VERB_FIXTURE)
    assert "method" in control_signature, (
        "разборщик сигнатуры НЕ НАШЁЛ имени глагола там, где оно заведомо "
        f"есть: вердикт первого утверждения ничего не значит — {sorted(control_signature)}"
    )
    assert MODAL_VERB_LITERAL not in control_tag, (
        "разборщик тега НАШЁЛ литерал там, где глагол параметрический: "
        f"вердикт второго утверждения ничего не значит — {control_tag!r}"
    )


# --- СЛОТ БЛОЧНОГО ВЫЗОВА НЕ НЕСЁТ СВОЕГО ЗАПРОСА (WR-04) --------------------
#
# ⚠️ МЕХАНИЗМ ДЕФЕКТА, А НЕ ОПРЯТНОСТЬ: обработчик завершения запроса висит на
# ФОРМЕ панели, слот рисуется ВНУТРИ этой формы, а событие завершения запроса
# ВСПЛЫВАЕТ. Запрос, поднятый изнутри слота, дошёл бы событием до формы и закрыл
# бы панель ЧУЖИМ обменом — посреди решения человека и на любом из 18 мест
# подтверждения. Сегодня дефект ЛАТЕНТНЫЙ: все три слота несут только скрытые
# поля. Инвентарь краснит введение такого запроса В МОМЕНТ ВВЕДЕНИЯ, а не
# выясняется ручным обходом через фазу.
#
# ⚠️ ГРАНИЦА ПРЕДИКАТА, БЕЗ КОТОРОЙ ЗАПИСЬ БЫЛА БЫ ШИРЕ ПОВЕДЕНИЯ: правило
# читает ТЕКСТ слота и распознаёт нарушителя по ПРЕФИКСУ АТРИБУТА слоя письма,
# то есть видит только РАЗМЕТОЧНУЮ форму введения запроса. Запрос, поднятый
# изнутри слота ПРОГРАММНО — вызовом слоя письма из скрипта или обработчиком
# объекта клиентского состояния, — предикат НЕ РАЗЛИЧАЕТ и этой половины не
# закрывает вовсе. Она остаётся предметом отложенного сужения обработчика
# (.planning/WINDOWS.md), и сужение это здесь НЕ делается намеренно: правка
# попала бы в выражение, которым держится критерий 3 фазы и зубы которого
# измерены тремя мутациями верификатора.

# ЛЕТОПИСЬ ЧИСЛА: 0 → 3, Фаза 10, план 10-09. ОТКУДА: счёт `_modal_call_slots`
# по всему дереву шаблонов, снятый ПРОГОНОМ покрасневшего правила с заведомо
# неверным объявленным числом, а не сложением в уме. ЧТО ОЗНАЧАЕТ: столько
# блочных вызовов панели живёт в дереве — строка расписания в редакторе
# объявления (return_to и ad_id), строка группы аккаунта (search) и админская
# очередь (task_id). Документная выдержка из шапки самого компонента в счёт НЕ
# входит: разборщик исключает компонент целиком. Выросшее беззвучно означает,
# что четвёртый слот завели, не пересмотрев запрет.
MODAL_BLOCK_CALLS_DECLARED = 3

# Синтетический слот НАРУШИТЕЛЯ: скрытое поле плюс узел, поднимающий СВОЙ
# запрос атрибутом слоя письма. Собирается ЕДИНСТВЕННЫМ сборщиком блочного
# вызова — вторая его копия разошлась бы с настоящим вызовом молча.
SLOT_WITH_OWN_REQUEST = (
    HIDDEN_FIELD + '<button type="button" hx-get="/synthetic/preview">Показать</button>'
)


def test_no_confirm_panel_slot_carries_a_request_of_its_own():
    """НЕСУЩЕЕ: ни один слот блочного вызова панели не несёт СВОЕГО запроса.

    Отказ называет ФАЙЛ и ТЕКСТ слота: инвентарь, сообщающий только «есть
    нарушитель», отправляет читателя искать его руками — ровно ту работу, ради
    снятия которой инвентарь и заводится.
    """
    slots = _modal_call_slots(_all_templates())

    # АНТИВАКУУМ: разборщик, вернувший пустой перечень, зеленел бы на ЛЮБОМ
    # дереве, и зелёный цвет сломанного разборщика посимвольно совпадал бы с
    # зелёным цветом соблюдённого свойства (D-13 Фазы 8).
    assert slots, (
        "разборщик не нашёл НИ ОДНОГО блочного вызова панели — инвентарь "
        "вакуумен и перестал отличать соблюдение от поломки"
    )
    assert len(slots) == MODAL_BLOCK_CALLS_DECLARED, (
        f"блочных вызовов панели {len(slots)}, объявлено "
        f"{MODAL_BLOCK_CALLS_DECLARED} — слот завели или сняли, не пересмотрев "
        f"запрет: {[rel for rel, _ in slots]}"
    )

    offenders = _slot_offenders(slots)
    assert not offenders, (
        "слот блочного вызова панели несёт СВОЙ запрос: событие завершения "
        "чужого обмена всплывёт до формы панели и закроет её посреди решения "
        "человека — "
        + "; ".join(f"{rel} -> {text.strip()!r}" for rel, text in offenders)
    )


def test_control_negative_a_slot_with_a_request_reddens_the_slot_inventory():
    """ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ: предикат УМЕЕТ находить нарушителя.

    Контроль, вернувший пустой перечень, стерёг бы не то: несущее правило выше
    зеленело бы одинаково и на соблюдённом дереве, и на сломанном разборщике.
    """
    fixture = [("synthetic/slot_with_own_request.html", _modal_block_source(SLOT_WITH_OWN_REQUEST))]

    slots = _modal_call_slots(fixture)
    assert len(slots) == 1, (
        f"разборщик нашёл в синтетике {len(slots)} слотов вместо одного: "
        f"контроль утверждает не про тот текст — {slots!r}"
    )
    assert "hx-get" in slots[0][1], (
        f"разбор потерял атрибут слоя письма из слота: {slots[0][1]!r}"
    )

    offenders = _slot_offenders(slots)
    assert offenders, (
        "предикат НЕ НАШЁЛ нарушителя там, где запрос заведомо есть — вердикт "
        f"несущего правила ничего не значит: {slots!r}"
    )

    # И тот же предикат на НАСТОЯЩЕМ дереве обязан молчать: контроль,
    # краснящий всё подряд, стерёг бы не введение запроса, а само существование
    # слотов.
    assert not _slot_offenders(_modal_call_slots(_all_templates())), (
        "предикат краснит настоящее дерево — он различает не то, что объявлено"
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

# --- ПЛОЩАДКА ПРИЗЕМЛЕНИЯ ФОКУСА (Фаза 10, план 10-02, D-11) -----------------
#
# ⚠️ ПЛОЩАДКА ВЫБРАНА ОДИН РАЗ НА ВСЕ 18 МЕСТ ПОДТВЕРЖДЕНИЯ, И ПАРАМЕТРОМ
# МАКРОСА ОНА НЕ СТАНОВИТСЯ: 18 вызовов получили бы по решению — ровно та форма,
# которую D-11 Фазы 9 уже отверг для цели свопа. Величина живёт в объекте
# клиентского состояния ОДИН раз и утверждается правилом
# `test_the_focus_landing_is_declared_once_and_called_twice`.
#
# ⚠️ ИМЯ ИЗМЕРЕНО ПО ШЕЛЛУ, А НЕ ВЗЯТО ИЗ ПАМЯТИ (идиома SP-1, 09-PATTERNS.md).
# Разъехавшись с включаемым файлом области уведомлений, эта константа заставила
# бы правила ниже проверять НЕСУЩЕСТВУЮЩУЮ площадку и зеленеть вакуумом; сверка
# исполняется правилом `test_the_landing_region_exists_in_the_shell_of_both_apps`,
# а не оставлена читателю.
FOCUS_LANDING_ID = "notice"

# Включаемый файл областей уведомления и оба шелла, которые его подключают.
NOTICE_AREA = "includes/notice_area.html"
APP_SHELLS = ("base.html", "auth_base.html")

# ⚠️ ИМЯ ИНТЕРПРЕТАТОРА (`NODE_BIN`) ПЕРЕЕХАЛО В `tests/conftest.py` ПЛАНОМ
# 09-19 — вместе с самим запуском. Имя интерпретатора есть свойство ЗАПУСКА, а
# не свойство панели подтверждения, и второй его экземпляр разошёлся бы с
# первым молча. Здесь он больше не объявляется; собственного вызова подпроцесса
# в файле не остаётся.

MODAL_XDATA_RE = re.compile(r'x-data="(\{.*?\})"', re.DOTALL)

# ⚠️ ГАРНИР ПОЛУЧАЕТ ПАВЛОАД ПОДСТАНОВКОЙ, А НЕ СТАНДАРТНЫМ ВВОДОМ (план
# 09-19). Общий запуск `run_node_script` принимает ровно исходник и потоков в
# подпроцесс не открывает: стандартный ввод был бы вторым каналом, о котором
# знал бы один вызывающий из двух. Образец подстановки — `__PAYLOAD__`,
# встречается ровно один раз, и единственность утверждается в `_run_modal_lifecycle`.
MODAL_LIFECYCLE_HARNESS = """
'use strict';
const payload = __PAYLOAD__;
const LOCK = payload.lock;
const EXPRESSION = payload.expression;
const AFTER_REQUEST = payload.after_request;
const LANDING_ID = payload.landing_id;
const LANDING_PRESENT = payload.landing_present;
const DISMISSAL = payload.dismissal;
const BANNER_IDS = payload.banner_ids;
const HIDDEN_ATTR = payload.hidden_attr;

function makeClassList() {
  const own = new Set();
  return {
    add(...names) { for (const n of names) { own.add(n); } },
    remove(...names) { for (const n of names) { own.delete(n); } },
    contains(name) { return own.has(name); }
  };
}

// ⚠️ ГАРНИР ВЕДЁТ ЗАПИСЬ ПОСЛЕДНЕГО СФОКУСИРОВАННОГО ИМЕНИ, А НЕ БУЛЕВО
// «фокус двигался». Правило обязано отличать «фокус ПРИЕХАЛ НА ПЛОЩАДКУ» от
// «фокус не двигался вовсе»: у отсоединённого открывателя метод фокусировки
// ЕСТЬ, вызов не падает и не делает НИЧЕГО, — и булево «метод вызван» зеленело
// бы ровно на том дефекте, ради которого правило заводится (Landmine 2).
let focused = null;
// Отдельная запись ПОПЫТОК фокусировки — только для внятного текста отказа:
// «вызов был, а фокус не сдвинулся» и «вызова не было вовсе» есть два разных
// дефекта, и вердикт обязан их различать.
let attempted = [];

// ⚠️ ПОДСТАВНОЙ УЗЕЛ НЕСЁТ ТРИ ВЕЩИ, И ВСЕ ТРИ — ПРЕДМЕТ. Опознаваемое имя
// (иначе вердикт не различает узлы), НАСТОЯЩИЙ признак присутствия в документе
// (ветвление возврата фокуса спрашивает именно его) и метод фокусировки,
// ведущий себя КАК В БРАУЗЕРЕ.
//
// ⚠️ ФОКУСИРОВКА ОТСОЕДИНЁННОГО УЗЛА НЕ ДЕЛАЕТ НИЧЕГО, И ЭТО НЕ УПРОЩЕНИЕ, А
// САМ ПРЕДМЕТ (Landmine 2). Метод у такого узла ЕСТЬ, вызов не падает — и фокус
// молча остаётся там, где был. Стаб, записывающий имя независимо от присутствия,
// имитировал бы успех там, где в браузере не происходит ничего, и правила ниже
// зеленели бы на сегодняшнем дефекте.
//
// ⚠️ СУМКА АТРИБУТОВ ПРИБАВЛЕНА ПЛАНОМ 10-41, И ВЕДЁТ ОНА СЕБЯ КАК В БРАУЗЕРЕ,
// А НЕ КАК УДОБНО. Три вещи названы фактом, потому что каждая из них, сделанная
// иначе, дала бы ЗЕЛЁНОЕ правило на дефектном рычаге:
//   [1] постановка есть ПРИСВОЕНИЕ, а не переключение: второй вызов на том же
//       узле обязан оставить признак стоя́щим, иначе снятие двух заготовок
//       одним перебором «снимало» бы и обратно ставило;
//   [2] вопрос о наличии спрашивает КЛЮЧ, а не истинность значения: признак
//       скрытости несёт ПУСТОЕ значение (`setAttribute('hidden', '')`), и
//       проверка на истинность зеленела бы НАОБОРОТ — на снятой заготовке
//       отвечала бы «не снята»;
//   [3] сумка — объектный литерал БЕЗ ПРОТОТИПА: имя атрибута, совпавшее с
//       именем метода прототипа объекта, иначе отвечало бы «есть» всегда.
//
// ⚠️ ВСЕ ЗАВЕДЁННЫЕ УЗЛЫ СКЛАДЫВАЮТСЯ В РЕЕСТР, И ЭТО НУЖНО `reset()`. Сценарий,
// прочитавший признак, оставшийся от предыдущего прогона, зеленел бы ПРОШЛЫМ.
const allNodes = [];
function makeNode(name, connected) {
  const node = {
    name: name,
    isConnected: connected,
    attrs: Object.create(null),
    setAttribute(attr, value) { this.attrs[attr] = value; },
    removeAttribute(attr) { delete this.attrs[attr]; },
    hasAttribute(attr) {
      return Object.prototype.hasOwnProperty.call(this.attrs, attr);
    },
    focus() {
      attempted.push(name);
      if (!this.isConnected) { return; }
      focused = name;
    }
  };
  allNodes.push(node);
  return node;
}

const documentElement = { classList: makeClassList() };
// Площадка приземления и тело документа — два разных узла с разными именами:
// вердикт «фокус на теле документа» и вердикт «фокус на площадке» обязаны быть
// различимы, потому что первый и есть сегодняшний дефект.
const landing = makeNode('landing', true);
const body = makeNode('body', true);

// Узлы заготовок плашки отказа — по одному на объявленный идентификатор.
// ⚠️ ПУСТОЙ ПЕРЕЧЕНЬ ОСТАВЛЯЕТ РАЗРЕШЕНИЕ ИДЕНТИФИКАТОРОВ ПОБАЙТОВО ПРЕЖНИМ, и
// это ОБЯЗАТЕЛЬСТВО, а не следствие: восемь действующих сценариев подают
// умолчание и обязаны дать те же вердикты, что до прибавки.
const banners = Object.create(null);
for (const bannerId of BANNER_IDS) {
  banners[bannerId] = makeNode('banner:' + bannerId, true);
}

globalThis.document = {
  documentElement: documentElement,
  activeElement: body,
  // ⚠️ РАЗРЕШЕНИЕ УЗЛА ПО ИДЕНТИФИКАТОРУ ОТВЕЧАЕТ ТОЛЬКО НА ЗАЯВЛЕННЫЙ
  // ИДЕНТИФИКАТОР. Стаб, отдающий узел на ЛЮБОЙ идентификатор, зеленел бы и на
  // панели, приземляющейся куда попало; отсутствие площадки выражается
  // признаком LANDING_PRESENT и служит отрицательным контролем.
  //
  // ⚠️ ПОРЯДОК ВЕТВЕЙ НЕСУЩИЙ (план 10-41): площадка приземления разрешается
  // ПЕРВОЙ и дословно прежней ветвью, заготовки — второй. Обратный порядок
  // сделал бы прибавку заметной для восьми действующих сценариев, чей перечень
  // заготовок пуст, — то есть нарушил бы обязательство умолчания.
  getElementById(id) {
    if (LANDING_PRESENT && id === LANDING_ID) { return landing; }
    if (Object.prototype.hasOwnProperty.call(banners, id)) { return banners[id]; }
    return null;
  }
};

function reset() {
  documentElement.classList = makeClassList();
  focused = null;
  attempted = [];
  document.activeElement = body;
  // Сумки атрибутов ВСЕХ заведённых узлов обнуляются вместе с остальным
  // состоянием: признак, переживший прогон, зеленил бы следующий прошлым.
  for (const node of allNodes) { node.attrs = Object.create(null); }
}
function locked() { return documentElement.classList.contains(LOCK); }

function build() {
  const panel = (new Function('return (' + EXPRESSION + ');'))();
  panel.$nextTick = function (fn) { fn(); };
  panel.$refs = {
    cancel: makeNode('cancel', true),
    panel: { querySelectorAll() { return []; } }
  };
  return panel;
}

// ⚠️ ВЫРАЖЕНИЕ АТРИБУТА ИСПОЛНЯЕТСЯ ТЕМ ЖЕ СПОСОБОМ, ЧТО И У РАНТАЙМА ALPINE:
// телом функции с областью видимости объекта клиентского состояния. Вызов
// метода объекта напрямую проверял бы НЕ ТО — предмет здесь ветвь, записанная
// в АТРИБУТЕ, а не тело `hide()`.
//
// ⚠️ ИСТОЧНИК ОБЪЕКТА СОБЫТИЯ СМЕНЁН ФАЗОЙ 10 (план 10-05), СПОСОБ ИСПОЛНЕНИЯ —
// НЕТ. Прежде функция принимала БУЛЕВО и собирала объект события сама
// (`{ detail: { successful: successful } }`) — форму, которой рантайм на
// транспорте перехода НЕ ПРОИЗВОДИТ: правило, кормимое ею, зеленело в вакууме и
// отличить исправную панель от мёртвой ветви не могло (гейп 1 отчёта
// верификации фазы). Теперь функция принимает ГОТОВЫЙ `detail` целиком, а формы
// его объявлены `EVENT_SHAPES` ниже и сняты с вендоренного бандла. Обоснование
// абзаца выше остаётся верным ЦЕЛИКОМ и не переписывается.
function afterRequest(panel, detail) {
  const handler = new Function('$event', 'with (this) { ' + AFTER_REQUEST + ' }');
  handler.call(panel, { detail: detail });
}

// --- ЧЕТЫРЕ РЕАЛЬНЫЕ ФОРМЫ СОБЫТИЯ ЗАВЕРШЕНИЯ ЗАПРОСА (план 10-05) ----------
//
// ⚠️ СОСТАВ СНЯТ С ВЕНДОРЕННОГО БАНДЛА `app/static/js/htmx.min.js` (htmx
// 2.0.10) КОМАНДАМИ ВЫДЕРЖЕК, А НЕ ВЫВЕДЕН ИЗ ДОКУМЕНТАЦИИ. Измерено:
//
//   [1] объект события собирается ДО отправки запроса —
//       `const T={xhr:g,target:u,requestConfig:C,etc:i,boosted:$,select:F,
//       pathInfo:{…}}` — значит `xhr` в нём есть ВСЕГДА, а ключа признака
//       успешности нет ВОВСЕ до присваивания;
//   [2] присваивание в бандле ЕДИНСТВЕННОЕ (`s.count('e.successful=') == 1`),
//       стои́т на смещении 48145 — `e.target=r;e.failed=a;e.successful=!a` — и
//       стои́т ПОСЛЕ раннего возврата ветки перехода в обработчике ответа `Vn`
//       (`if(T(n,/HX-Location:/i)){…Nn("get",e,s);return}`);
//   [3] на несостоявшемся обмене событие летит из `g.onerror`, `g.onabort` и
//       `g.ontimeout` с ТЕМ ЖЕ объектом, а `Vn` не вызывается вовсе.
//
// ⚠️ ОТСУТСТВИЕ КЛЮЧА ВОСПРОИЗВОДИТСЯ ОТСУТСТВИЕМ, А НЕ ЛОЖЬЮ, И ЭТО НЕСУЩЕЕ.
// Булево `false` прошло бы через ветвь по коду ответа идентично, а через ветвь
// с признаком события — НЕТ; гарнир, подменяющий одно другим, снова стерёг бы
// не то. Единственность ключа утверждается полем вердикта
// `successful_key_present`, а не оставляется читателю.
const EVENT_SHAPES = {
  // ТРАНСПОРТ ПЕРЕХОДА: ответ `location_response()` (app/pages/htmx.py:133-150)
  // — 204 + заголовок перехода. Сработал ранний возврат [2]: ключа признака
  // успешности НЕТ.
  location: function () {
    return {
      xhr: {
        status: 204,
        getResponseHeader: function (name) {
          return name === 'HX-Location' ? '/ads' : null;
        }
      }
    };
  },
  // ФРАГМЕНТНЫЙ ТРАНСПОРТ: своп состоялся, признаки присвоены ветвью [2].
  fragment: function () {
    return {
      successful: true,
      failed: false,
      xhr: {
        status: 200,
        getResponseHeader: function () { return null; }
      }
    };
  },
  // ОТКАЗ СЕРВЕРА: заголовка перехода нет, ранний возврат не сработал, признаки
  // присвоены ветвью [2] штатно — ложью.
  refused: function () {
    return {
      successful: false,
      failed: true,
      xhr: {
        status: 500,
        getResponseHeader: function () { return null; }
      }
    };
  },
  // НЕСОСТОЯВШИЙСЯ ОБМЕН: обрыв сети, отмена, таймаут — событие из обработчиков
  // отказа транспорта [3]. Обработчик ответа не вызывался, ключа признака
  // успешности НЕТ; код ответа равен нулю, чтение заголовка даёт пустоту.
  never_completed: function () {
    return {
      xhr: {
        status: 0,
        getResponseHeader: function () { return null; }
      }
    };
  }
};

// ⚠️ ОСНАСТКА ЗАПИСЫВАЕТ ИМЯ ОТРАБОТАВШЕЙ ВЕТВИ, А НЕ ИТОГОВУЮ ПОЗИЦИЮ ФОКУСА
// (WR-07 ревизии фазы). Две ветви ухода узла, неразличимые для теста, оставляют
// запись шапки непроверяемой и взаимозаменяемой: правило обязано утверждать,
// КАКАЯ ИЗ ДВУХ отработала. Подмена происходит ДО исполнения выражения, потому
// что выражение разрешает имя метода на объекте в момент вызова.
//
// ⚠️ ПЕРЕЧЕНЬ ИМЁН НА ВОПРОС «ОТРАБОТАЛА ЛИ ВЕТВЬ СНОСА ИЛИ ОКАЗАЛАСЬ ПУСТОЙ
// ОПЕРАЦИЕЙ» НЕ ОТВЕЧАЕТ, а правило атрибуции обязано отвечать: страж
// собственного состояния (`if (this.open)`) делает снос закрытой панели пустым.
// Поэтому оснастка ведёт ВТОРУЮ запись — состояние панели ПЕРЕД каждым вызовом.
function spyBranches(panel) {
  const names = [];
  const openBefore = {};
  const realHide = panel.hide;
  const realDestroy = panel.destroy;
  panel.hide = function () {
    names.push('hide');
    openBefore.hide = this.open;
    return realHide.call(this);
  };
  panel.destroy = function () {
    names.push('destroy');
    openBefore.destroy = this.open;
    return realDestroy.call(this);
  };
  return { names: names, openBefore: openBefore };
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

// --- СЦЕНАРИИ ФАЗЫ 10: ФОКУС И ВЕТВЬ ПО УСПЕШНОСТИ ОБМЕНА -------------------
//
// ⚠️ ОТКРЫВАТЕЛЬ ЗДЕСЬ ОТСОЕДИНЁН ОТ ДОКУМЕНТА НАМЕРЕННО, И ЭТО НЕ КРАЙНИЙ
// СЛУЧАЙ, А ФРАГМЕНТНЫЙ ПУТЬ ФАЗЫ ДОСЛОВНО: кнопка, открывшая панель, уезжает
// внеполосным узлом ВМЕСТЕ со своей строкой. Метод фокусировки у такого узла
// остаётся, и панель, спрашивающая наличие метода, «возвращает» на него фокус
// вызовом, который не делает ничего.

function scenarioFocusAfterHide() {
  const runs = [];
  for (let i = 0; i < 2; i++) {
    reset();
    const panel = build();
    document.activeElement = makeNode('opener', false);
    panel.show();
    const opener_has_focus_method = typeof panel.opener.focus === 'function';
    const opener_connected = panel.opener.isConnected;
    panel.hide();
    runs.push({
      focused: focused,
      attempted: attempted.slice(),
      opener_has_focus_method: opener_has_focus_method,
      opener_connected: opener_connected,
      open_after: panel.open
    });
  }
  const same = JSON.stringify(runs[0]) === JSON.stringify(runs[1]);
  return Object.assign({}, runs[1], { repeat_matches: same });
}

function scenarioFocusAfterTeardown() {
  const runs = [];
  for (let i = 0; i < 2; i++) {
    reset();
    const panel = build();
    document.activeElement = makeNode('opener', false);
    panel.show();
    // ⚠️ `hide()` НЕ ЗОВЁТСЯ ВОВСЕ — И В ЭТОМ ВЕСЬ СЦЕНАРИЙ. На фрагментном
    // пути событие после запроса приходит ПОСЛЕ свопа, то есть после того, как
    // внеполосный узел уже снял панель вместе с её формой.
    //
    // ⚠️⚠️ ФОРМУЛИРОВКА ДВУХ СТРОК ВЫШЕ — ОПРОВЕРГНУТО РАНТАЙМОМ. Действующая
    // версия — шапка app/templates/components/modal.html (абзац «ВЕРНО (по
    // рантайму, четырьмя утверждениями)»), и пометка указывает НА НЕЁ, а не
    // пересказывает её: пересказ через круг разошёлся бы с оригиналом, и вышло
    // бы третье поколение формулировки. Источник опровержения: ревизия Фазы 10
    // (10-REVIEW.md, WR-07) и верификация Фазы 10, исправлено планом 10-05.
    // Верно по рантайму: событие завершения запроса летит В ТОЙ ЖЕ ЗАДАЧЕ, а
    // снос компонента приходит МИКРОЗАДАЧЕЙ ПОЗЖЕ, — значит `hide()` на
    // фрагментном пути ОТРАБАТЫВАЕТ, а ветвь приземления в сносе остаётся
    // ЗАЩИТНОЙ, а не нормальной.
    // ПРЕЖНИЙ ТЕКСТ НЕ СТИРАЕТСЯ (идиома D-30/D-32 .planning/STATE.md): стёртая
    // формулировка лишает следующего читателя знания о том, что прочтение
    // вообще понадобилось, и он «починит» верную ветвь.
    //
    // ИМЯ ПРЕДМЕТА, НАЗВАННОЕ ТЕМ, ЧЕМ ОН ЯВЛЯЕТСЯ: это ЗАЩИТНАЯ ветвь сноса
    // ОТКРЫТОЙ панели (снос узла у панели, которую никто не закрывал), а не
    // «фокус после сноса на фрагментном пути». ⚠️ ИМЯ `scenarioFocusAfterTeardown`
    // И КЛЮЧ `focus_after_teardown` ОСТАВЛЕНЫ ПО ЗАМЕРУ, А НЕ ПО ВКУСУ:
    // переименование задело бы ЧЕТЫРЕ места (:2214 и :2408 — имя функции и ключ
    // отображения; :3790 и :3874 — потребители ключа в правилах модуля), то есть
    // больше трёх, а ключ отображения есть КОНТРАКТ модуля. Правка записи не
    // имеет права превратиться в правку контракта, поэтому новое имя предмета
    // вписано здесь строкой, а идентификаторы не тронуты.
    const has = hasTeardown(panel);
    teardown(panel);
    runs.push({
      focused: focused,
      attempted: attempted.slice(),
      has_destroy: has,
      still_locked_after_teardown: locked(),
      open_after: panel.open
    });
  }
  const same = JSON.stringify(runs[0]) === JSON.stringify(runs[1]);
  return Object.assign({}, runs[1], { repeat_matches: same });
}

function scenarioFocusSibling() {
  reset();
  const open_panel = build();
  const closed_panel = build();
  document.activeElement = makeNode('opener', true);
  open_panel.show();
  const focused_before = focused;
  const has = hasTeardown(closed_panel);
  teardown(closed_panel);
  return {
    focused_before: focused_before,
    focused_after: focused,
    attempted: attempted.slice(),
    has_destroy: has,
    still_locked_after_teardown: locked(),
    repeat_matches: null
  };
}

// ⚠️ СЦЕНАРИЙ `exchange` СНЯТ ПЛАНОМ 10-05, И ЭТО НЕ ПОТЕРЯ ПОКРЫТИЯ, А ПЕРЕЕЗД.
// Он синтезировал объект события из БУЛЕВА (`{ successful: true }` /
// `{ successful: false }`) — то есть подавал форму, которой рантайм на
// транспорте перехода НЕ ПРОИЗВОДИТ ВООБЩЕ. Всё, что он утверждал, утверждается
// теперь сценарием `transports` на ЧЕТЫРЁХ РЕАЛЬНЫХ формах: успех — правилами
// `test_the_panel_closes_on_the_fragment_transport` и
// `test_the_panel_closes_on_the_location_transport`, отказ — правилами
// `test_the_panel_stays_open_when_the_server_refused_on_either_transport` и
// `test_the_panel_stays_open_when_the_exchange_never_completed_on_either_transport`.

// --- СЦЕНАРИЙ ТРАНСПОРТОВ (план 10-05) --------------------------------------
//
// Прогоняет ОДНУ названную форму события из `EVENT_SHAPES` через выражение
// атрибута и возвращает вердикт, снятый ДО сноса узла, плюс отдельную запись о
// самом сносе. Порядок несущий: снос ЗАКРЫВАЕТ ещё открытую панель, и вердикт,
// снятый после него, показывал бы закрытой панель, которая на отказе обязана
// остаться открытой.
function scenarioTransports() {
  const shapeName = payload.event_shape;
  const make = EVENT_SHAPES[shapeName];
  if (!make) {
    console.error('неизвестная форма события: ' + shapeName);
    process.exit(2);
  }
  const runs = [];
  for (let i = 0; i < 2; i++) {
    reset();
    const panel = build();
    panel.show();
    // Признак отправки встаёт так же, как его ставит перехват отправки формы:
    // сброс его — предмет утверждения на ВСЕХ четырёх формах.
    panel.sending = true;
    const spy = spyBranches(panel);
    const detail = make();
    const key_present = Object.prototype.hasOwnProperty.call(detail, 'successful');
    // ⚠️ ЧТО ОТДАЁТ ЧТЕНИЕ ЗАГОЛОВКА ПЕРЕХОДА — ОТДЕЛЬНОЕ ПОЛЕ ВЕРДИКТА, А НЕ
    // ВЫВОД ИЗ ИМЕНИ ФОРМЫ. Правила отказа утверждают «ни на одном транспорте»,
    // и утверждение это держится ровно на том, что дизъюнкту транспорта на
    // этих формах сработать НЕ НА ЧЕМ: заголовка в ответе нет.
    const location_header = detail.xhr
      ? detail.xhr.getResponseHeader('HX-Location')
      : null;

    // ⚠️ ИСКЛЮЧЕНИЕ ЛОВИТСЯ И ЕДЕТ В ВЕРДИКТ ПОЛЕМ, А НЕ ПРОГЛАТЫВАЕТСЯ:
    // выражение, упавшее внутри слушателя, оставило бы панель открытой — то
    // есть выглядело бы РОВНО как исправное поведение на путях отказа.
    let threw = null;
    try {
      afterRequest(panel, detail);
    } catch (e) {
      threw = String((e && e.message) || e);
    }

    const verdict = {
      open: panel.open,
      sending: panel.sending,
      locked: locked(),
      branches: spy.names.slice(),
      successful_key_present: key_present,
      location_header: location_header,
      threw: threw
    };

    // Снос узла ПОСЛЕ события — тем же вызовом, каким его делает рантайм
    // клиентского состояния из колбэка наблюдателя мутаций.
    const open_at_teardown = panel.open;
    teardown(panel);
    verdict.teardown = {
      branches: spy.names.slice(),
      open_at_call: open_at_teardown,
      // Пустая операция — это НЕ «ветвь не звалась»: она звалась и вышла на
      // собственном страже состояния. Различие утверждается полем, а не
      // выводится из перечня имён.
      was_a_noop: open_at_teardown === false,
      open: panel.open,
      locked: locked()
    };
    runs.push(verdict);
  }
  const same = JSON.stringify(runs[0]) === JSON.stringify(runs[1]);
  return Object.assign({}, runs[1], { repeat_matches: same });
}

// --- СЦЕНАРИЙ УХОДА ПАНЕЛИ ПО ВОЛЕ ЧЕЛОВЕКА (план 10-07, DEF-09-02) ---------
//
// Исполняет ВЫРАЖЕНИЕ пути ухода телом функции с областью видимости объекта
// клиентского состояния — тем же способом, каким рантайм клиентского состояния
// исполняет атрибуты, и тем же, каким это делает сценарий транспортов. Вызов
// `panel.hide()` напрямую проверял бы НЕ ТО: предмет здесь ветвь, записанная в
// АТРИБУТЕ, а не тело `hide()` — панель, потерявшая гейт в атрибуте, уходила бы
// во время летящего запроса, а метод при этом оставался бы прежним.
//
// ⚠️ ПРИЗНАК ОТПРАВКИ ВЫСТАВЛЯЕТСЯ ТАК ЖЕ, КАК ЕГО СТАВИТ ПЕРЕХВАТ ОТПРАВКИ
// ФОРМЫ, — присваиванием тому же полю того же объекта.
//
// ⚠️ НЕОБЯЗАТЕЛЬНАЯ ФОРМА СОБЫТИЯ ПРОГОНЯЕТСЯ ДО ИСПОЛНЕНИЯ ВЫРАЖЕНИЯ и служит
// ровно одному — доказать, что гейт НЕ ЛОВУШКА: панель, пережившая ОТКАЗ
// СЕРВЕРА, обязана снова уходить по каждому из трёх путей. Состояние панели
// сразу после обмена едет в вердикт отдельным полем `exchange`, а не выводится
// из имени формы: без него утверждение «после отказа панель осталась открытой,
// и признак отправки сброшен» держалось бы на вере.
function scenarioDismissal() {
  const runs = [];
  for (let i = 0; i < 2; i++) {
    reset();
    const panel = build();
    panel.show();
    panel.sending = payload.sending;
    let exchange = null;
    if (payload.event_shape) {
      const make = EVENT_SHAPES[payload.event_shape];
      if (!make) {
        console.error('неизвестная форма события: ' + payload.event_shape);
        process.exit(2);
      }
      afterRequest(panel, make());
      exchange = { open: panel.open, sending: panel.sending, locked: locked() };
    }
    const focused_before = focused;
    const spy = spyBranches(panel);
    // ⚠️ ИСКЛЮЧЕНИЕ ЛОВИТСЯ И ЕДЕТ В ВЕРДИКТ ПОЛЕМ, А НЕ ПРОГЛАТЫВАЕТСЯ:
    // выражение, упавшее внутри слушателя, оставило бы панель открытой — то
    // есть выглядело бы РОВНО как исправно сработавший гейт.
    let threw = null;
    try {
      const handler = new Function('with (this) { ' + DISMISSAL + ' }');
      handler.call(panel);
    } catch (e) {
      threw = String((e && e.message) || e);
    }
    runs.push({
      open: panel.open,
      locked: locked(),
      focused: focused,
      focused_before: focused_before,
      attempted: attempted.slice(),
      sending: panel.sending,
      branches: spy.names.slice(),
      exchange: exchange,
      threw: threw
    });
  }
  const same = JSON.stringify(runs[0]) === JSON.stringify(runs[1]);
  return Object.assign({}, runs[1], { repeat_matches: same });
}

// --- СНЯТИЕ ЗАГОТОВОК ПЛАШКИ ОТКАЗА ПРИ ОТКРЫТИИ ПАНЕЛИ (план 10-41) --------
//
// ⚠️ ЗАЧЕМ ЭТО СЦЕНАРИЙ ИСПОЛНЕНИЯ, А НЕ ДВА ПОДСТРОЧНЫХ ПОИСКА. Конъюнкция
// «глагол применён К ЭТОЙ заготовке» подстрокой НЕВЫРАЗИМА ПО ПОСТРОЕНИЮ: в
// рычаге связь «идентификатор → цель глагола» проходит через перебор массива
// (`forEach`), то есть она есть связь ИСПОЛНЕНИЯ, а не соседства литералов.
// Подстрочная форма правила (`_lever_clearing_findings` в модуле шелла) на теле,
// где обе заготовки НАЗВАНЫ, а признак поставлен площадке приземления, даёт НОЛЬ
// находок и проходит зелёной — замер восьмого круга ревизии (`CR-01`).
//
// ⚠️ ВЕРДИКТ НАЗЫВАЕТ ПО КАЖДОЙ ЗАГОТОВКЕ ОТДЕЛЬНО, А НЕ ОБЩИМ БУЛЕВЫМ. Общее
// «снято» не отличило бы «снялась одна из двух» от «снялись обе», а именно это
// различие и есть форма (C) матрицы мутаций.
//
// ⚠️ ПОЛЕ `registered` ОТДАЁТ ТО, ЧТО ГАРНИР ЗАВЁЛ НА САМОМ ДЕЛЕ, А НЕ ЭХО
// ПАВЛОАДА. Без него «заготовка не снята» неотличимо от «узла заготовки не
// существует, и снимать было нечего»: разрешение идентификатора отдало бы
// пустоту, рычаг честно ничего не сделал бы, и правило краснело бы ВСЕГДА.
function scenarioBannerClearing() {
  reset();
  const panel = build();
  panel.show();
  const cleared = Object.create(null);
  for (const bannerId of Object.keys(banners)) {
    cleared[bannerId] = banners[bannerId].hasAttribute(HIDDEN_ATTR);
  }
  return {
    raised: locked(),
    cleared: cleared,
    landing_hidden: landing.hasAttribute(HIDDEN_ATTR),
    registered: Object.keys(banners),
    has_destroy: null,
    still_locked_after_teardown: null,
    repeat_matches: null
  };
}

const SCENARIOS = {
  raise: scenarioRaise,
  teardown: scenarioTeardown,
  sibling: scenarioSibling,
  banner_clearing: scenarioBannerClearing,
  focus_after_hide: scenarioFocusAfterHide,
  focus_after_teardown: scenarioFocusAfterTeardown,
  focus_untouched_by_closed_sibling: scenarioFocusSibling,
  transports: scenarioTransports,
  dismissal: scenarioDismissal
};
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

# Подставленный путь снятия БЕЗ СТРАЖА СОБСТВЕННОГО СОСТОЯНИЯ, приземляющий
# фокус безусловно (Фаза 10, план 10-02). Он выражает ровно тот дефект, от
# которого стои́т `if (this.open)` в ветви сноса: снос ЗАКРЫТОЙ соседки уводит
# фокус у ОТКРЫТОЙ панели.
#
# ⚠️ ПОДСТАНОВКА НЕ НАЗЫВАЕТ ВНУТРЕННЕГО ИМЕНИ МЕТОДА ПРИЗЕМЛЕНИЯ НАМЕРЕННО:
# она приземляет фокус САМА, по идентификатору площадки. Названный здесь метод
# привязал бы контроль к устройству объекта, и переименование внутри макроса
# ломало бы контроль, а выглядело бы это отказом правила.
UNGUARDED_TEARDOWN = (
    "destroy() { this.open = false; "
    "document.documentElement.classList.remove('is-modal-open'); "
    "const home = document.getElementById('__LANDING__'); "
    "if (home) home.focus(); }"
)


def _xdata_with_unguarded_teardown(expression: str) -> str:
    """Подставленное выражение, чей путь сноса СТРАЖА НЕ ИМЕЕТ.

    Тот же двойной предохранитель и тот же приём последнего ключа объектного
    литерала, что и у ``_xdata_with_dead_teardown``: ключ, объявленный ПОСЛЕДНИМ,
    побеждает одноимённый объявленный раньше, поэтому подстановка остаётся
    действенной и после того, как настоящий страж в выражении появится.
    """
    poisoned_body = UNGUARDED_TEARDOWN.replace("__LANDING__", FOCUS_LANDING_ID)
    source = expression.strip()
    assert source.endswith("}"), (
        "выражение x-data не кончается закрывающей скобкой объектного литерала: "
        "контроль подставляет не туда и потому не доказывает ничего"
    )
    assert poisoned_body not in source, (
        "путь снятия без стража уже стоит в выражении — подстановка ничего не "
        "добавляет, и контроль зелен по построению"
    )
    poisoned = source[:-1] + ", " + poisoned_body + " }"
    assert poisoned != source, "подстановка ничего не изменила"
    assert poisoned.count(poisoned_body) == 1, (
        "путь снятия без стража встречается в подставленном выражении не один раз"
    )
    return poisoned


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


def _modal_after_request_expression(html_source: str) -> str:
    """Выражение атрибута события завершения запроса из ОТРИСОВАННОЙ разметки.

    ⚠️ ПРЕДМЕТ — ИМЕННО АТРИБУТ, А НЕ ТЕЛО `hide()`. Ветвь по успешности обмена
    живёт в выражении атрибута формы, и правило, зовущее метод объекта напрямую,
    проверяло бы не то место: панель, потерявшая ветвь в атрибуте, закрывалась бы
    на ЛЮБОМ завершении запроса, а метод при этом оставался бы прежним.

    Граница разборщика та же, что у `_modal_xdata_expression`: ОДНО выражение на
    поданную разметку, и это утверждается числом найденных вхождений.
    """
    found = HTMX_RESET_ATTR_RE.findall(html_source)
    assert len(found) == 1, (
        f"в поданной разметке {len(found)} выражений завершения запроса, а не "
        "одно: разборщик рассчитан на одну панель, и выбор вхождения стал бы "
        "молчаливым"
    )
    return unescape(found[0])


# --- ПУТИ УХОДА ПАНЕЛИ ПО ВОЛЕ ЧЕЛОВЕКА (Фаза 10, план 10-07, DEF-09-02) -----
#
# ⚠️ МНОЖЕСТВО ЗДЕСЬ ДРУГОЕ, ЧЕМ У БУХГАЛТЕРИИ ПРИЗЕМЛЕНИЯ ФОКУСА, И СПУТАТЬ ИХ
# ЛЕГКО. Там считаются ПУТИ УХОДА УЗЛА ИЗ ДОКУМЕНТА, и их ДВА (человек закрыл
# и внеполосный узел унёс корень). Здесь считаются ПУТИ УХОДА ПАНЕЛИ ПО ВОЛЕ
# ЧЕЛОВЕКА, и их ТРИ: клавиша выхода на окне, щелчок по оверлею и кнопка отказа.
# Привести два числа к согласию НЕЛЬЗЯ, и это не небрежность: множества разные,
# и второе не подмножество первого — все три пути человека ведут в ОДНУ ветвь
# ухода узла (`hide()`), а второй путь ухода узла воли человека не спрашивает
# вовсе.
#
# ⚠️ ЧИСЛО ПОСТАВЛЕНО ПРОГОНОМ ПОКРАСНЕВШЕГО ПРАВИЛА, А НЕ СЛОЖЕНИЕМ В УМЕ
# (план 10-07, задача 2). Оно существует затем, чтобы ЧЕТВЁРТЫЙ путь ухода,
# заведённый будущей фазой, не мог появиться БЕЗ ГЕЙТА молча: инвентарь
# `test_every_dismissal_path_of_the_panel_is_gated_on_the_in_flight_state`
# сличает найденное разборщиком с объявленным здесь и краснеет при расхождении,
# называя оба числа и пути поимённо.
DISMISSAL_PATHS_DECLARED = 3
DISMISSAL_ESCAPE_RE = re.compile(r'x-on:keydown\.escape\.window\s*=\s*"([^"]*)"')
DISMISSAL_CLICK_RE = re.compile(r'x-on:click\s*=\s*"([^"]*)"')

OVERLAY_MARKER = 'class="modal__overlay"'
CANCEL_MARKER = 'x-ref="cancel"'
CONFIRM_MARKER = 'type="submit"'


def _modal_overlay_tag(html_source: str) -> str:
    """Тег узла оверлея панели целиком — от «<div» до «>»."""
    at = html_source.index(OVERLAY_MARKER)
    start = html_source.rindex("<div", 0, at)
    return html_source[start : html_source.index(">", start) + 1]


def _modal_cancel_button_tag(html_source: str) -> str:
    """Тег кнопки ОТКАЗА целиком — ДЕЙСТВУЮЩИМ разборщиком тега по маркеру.

    ⚠️ ОБЁРТКА ТОНКАЯ НАМЕРЕННО: своего разборщика тегов здесь не заводится и
    второй копии логики извлечения не появляется. Имя нужно затем, чтобы предмет
    правила доступности был назван ИМЕНЕМ, а не выражением с маркером внутри
    тела правила: записанный контракт («отмена разрушительного действия не имеет
    права быть труднее его подтверждения», шапка `components/modal.html`) и
    угроза T-10-41 говорят про ИМЕННО ЭТУ кнопку, и в коде это обязано быть
    видно так же ясно, как в записи.
    """
    return _button_tag(html_source, CANCEL_MARKER)


def _modal_confirm_button_tag(html_source: str) -> str:
    """Тег кнопки ПОДТВЕРЖДЕНИЯ целиком — тем же разборщиком по маркеру.

    Нужен ровно для одного — доказать АСИММЕТРИЮ: привязка отключённости в
    файле присутствует ЗАКОННО (у этой кнопки, в селекторе отключения на форме
    и в перечислителе фокусируемых узлов), и счёт вхождений по файлу её от
    привязки на кнопке отказа не отличает.
    """
    return _button_tag(html_source, CONFIRM_MARKER)


def _one_attribute(pattern: "re.Pattern[str]", tag: str, what: str) -> str:
    """Единственное вхождение атрибута в поданном теге — иначе отказ.

    Граница та же, что у `_modal_xdata_expression`: ОДНА панель на поданную
    разметку. Разборщик, молча выбравший одно вхождение из двух, проверял бы не
    ту панель.
    """
    found = pattern.findall(tag)
    assert len(found) == 1, (
        f"в теге {what} найдено {len(found)} выражений вместо одного: выбор "
        f"вхождения стал бы молчаливым; тег: {tag!r}"
    )
    return unescape(found[0])


def _modal_dismissal_expressions(html_source: str) -> dict[str, str]:
    """Выражения ТРЁХ путей ухода панели по воле человека, по имени пути.

    Разбор идёт по ОТРИСОВАННОЙ разметке, а не по исходнику шаблона: браузер
    получает именно её.

    ⚠️ ЧИСЛО НАЙДЕННОГО УТВЕРЖДАЕТСЯ ЗДЕСЬ, А НЕ ОСТАВЛЯЕТСЯ ЧИТАТЕЛЮ.
    Разборщик, молча вернувший два пути вместо трёх, сделал бы инвентарь
    (`test_every_dismissal_path_of_the_panel_is_gated_on_the_in_flight_state`)
    ВАКУУМНО ЗЕЛЁНЫМ: обход по двум найденным сошёлся бы сам с собой, а третий
    путь остался бы негейтированным и невидимым.
    """
    root_escape = DISMISSAL_ESCAPE_RE.findall(html_source)
    assert len(root_escape) == 1, (
        f"в поданной разметке {len(root_escape)} выражений пути клавиши выхода, "
        "а не одно: разборщик рассчитан на одну панель, и выбор вхождения стал "
        "бы молчаливым"
    )

    pairs = [
        ("escape", unescape(root_escape[0])),
        (
            "overlay",
            _one_attribute(
                DISMISSAL_CLICK_RE, _modal_overlay_tag(html_source), "оверлея"
            ),
        ),
        (
            "cancel",
            _one_attribute(
                DISMISSAL_CLICK_RE, _modal_cancel_button_tag(html_source),
                "кнопки отказа",
            ),
        ),
    ]
    names = [name for name, _ in pairs]
    assert (
        len(names) == DISMISSAL_PATHS_DECLARED
        and len(set(names)) == DISMISSAL_PATHS_DECLARED
    ), (
        f"разборщик вернул {len(names)} путей ухода с именами {names}, а "
        f"объявлено {DISMISSAL_PATHS_DECLARED}: утверждения ниже обходили бы не "
        "то множество"
    )
    return dict(pairs)


def _run_modal_lifecycle(
    expression: str,
    scenario: str,
    *,
    after_request: str = "",
    landing_present: bool = True,
    event_shape: str = "",
    dismissal: str = "",
    sending: bool = False,
    banner_ids: tuple[str, ...] = (),
) -> dict:
    """Исполнить сценарий жизненного цикла панели в интерпретаторе JS.

    ⚠️ ЗАПУСК ОБЩИЙ, А НЕ СОБСТВЕННЫЙ (план 09-19). Подпроцесс поднимает
    ``tests.conftest.run_node_script`` — единственный на проект. Там же живёт и
    причина, по которой отсутствие интерпретатора РОНЯЕТ правило, а не
    пропускает его: ``pytest.skip`` не применяется ни при какой причине, потому
    что пропущенное правило неотличимо от зелёного (WARN-4 первого круга).
    Здесь остаётся ровно то, что принадлежит ПАНЕЛИ: сборка павлоада и выбор
    сценария.

    ⚠️ ДВА ВХОДА ПРИБАВЛЕНЫ ФАЗОЙ 10 (план 10-02) И ОБА НЕОБЯЗАТЕЛЬНЫ С
    УМОЛЧАНИЕМ, ОСТАВЛЯЮЩИМ ТРИ ДЕЙСТВУЮЩИХ СЦЕНАРИЯ БАЙТ-В-БАЙТ ПРЕЖНИМИ:
    ``after_request`` нужен только сценарию ветви обмена, ``landing_present`` —
    только отрицательному контролю площадки. Вердикты правил блокировки
    прокрутки расширением не двигаются, и это утверждается прогоном ДО и ПОСЛЕ,
    а не обещается здесь.

    ⚠️ ТРЕТИЙ ВХОД ПРИБАВЛЕН ПЛАНОМ 10-05 ТОЙ ЖЕ ФОРМОЙ И С ТЕМ ЖЕ
    ОБЯЗАТЕЛЬСТВОМ: ``event_shape`` называет форму события из ``EVENT_SHAPES`` и
    нужен ТОЛЬКО сценарию транспортов; умолчание оставляет все действующие
    сценарии байт-в-байт прежними. Неизменность их вердиктов утверждена
    прогоном ДО правки (``10 passed, 54 deselected`` по фильтру правил фокуса и
    блокировки прокрутки) и тем же прогоном ПОСЛЕ.

    ⚠️ ЧЕТВЁРТЫЙ И ПЯТЫЙ ВХОДЫ ПРИБАВЛЕНЫ ПЛАНОМ 10-07 ТОЙ ЖЕ ФОРМОЙ И С ТЕМ ЖЕ
    ОБЯЗАТЕЛЬСТВОМ: ``dismissal`` подаёт ВЫРАЖЕНИЕ пути ухода панели по воле
    человека, ``sending`` — значение признака отправки, и нужны они ТОЛЬКО
    сценарию ухода; умолчания оставляют все действующие сценарии байт-в-байт
    прежними. Неизменность их вердиктов утверждена прогоном ДО правки
    (``18 passed, 53 deselected`` по фильтру правил блокировки прокрутки,
    приземления фокуса и транспортов) и тем же прогоном ПОСЛЕ.
    ``event_shape`` сценарий ухода ПЕРЕИСПОЛЬЗУЕТ, а не дублирует: формы события
    у него общие с транспортами, своих он не заводит.

    ⚠️ ГРАНИЦА, НАЗВАННАЯ ПЛАНОМ 10-19 (находка ревизии `WR-06`): УТВЕРЖДЕНИЙ О
    ПОРЯДКЕ ЗАДАЧ РАНТАЙМА ГАРНИР НЕ ВОСПРОИЗВОДИТ И НЕ ПРОВЕРЯЕТ. Гарнир
    подменяет отложенный вызов немедленным (``panel.$nextTick = function (fn) {
    fn(); };``) и зовёт ``hide()`` и ``destroy()`` РУКАМИ, в порядке, заданном
    телом самого сценария. Поэтому ТРИ утверждения о порядке из шапки
    ``app/templates/components/modal.html``, на которых держится исправление
    плана 10-05, остаются ВНЕ его охвата, и названы они здесь поимённо, а не
    общей фразой:
    1. внеполосное снятие происходит СИНХРОННО внутри свопа (задержка свопа по
       умолчанию равна нулю);
    2. событие завершения запроса летит В ТОЙ ЖЕ ЗАДАЧЕ (из ``xhr.onload``);
    3. рантайм клиентского состояния сносит компонент из колбэка наблюдателя
       мутаций, то есть МИКРОЗАДАЧЕЙ ПОЗЖЕ.

    СЛЕДСТВИЕ ДЛЯ ЧИТАТЕЛЯ ЗЕЛЁНОГО ПРАВИЛА, И ОНО ЕСТЬ ВЕСЬ СМЫСЛ ЭТОГО
    АБЗАЦА: зелень правил гарнира утверждает СВОЙСТВА ВЕТВЕЙ ухода — какая
    отработала, что она сделала с фокусом, блокировкой прокрутки и признаком
    открытости, — а НЕ их порядок. Правило
    ``test_the_rule_names_which_branch_closed_the_panel_on_both_transports``
    утверждает ИМЯ отработавшей ветви, но стои́т на порядке, заданном сценарием,
    а не на порядке рантайма. Прочитанная шире, эта зелень означала бы, что три
    утверждения выше проверены машиной; они не проверены ничем машинным, и их
    человеческая половина закрывается обходом ``10-UAT.md``, а не этим файлом.

    ⚠️ ПЕРЕПИСЫВАТЬ ГАРНИР НА АСИНХРОННЫЙ РАНТАЙМ РАДИ ЭТИХ ТРЁХ УТВЕРЖДЕНИЙ —
    НЕ ЧИНИТЬ, А ЛОМАТЬ. Гарнир существует ради свойств, наблюдаемых БЕЗ
    рантайма, и переписанный он перестал бы отвечать за то, за что отвечает
    сегодня. Названа ГРАНИЦА, а не снята.

    ⚠️ ШЕСТОЙ ВХОД ПРИБАВЛЕН ПЛАНОМ 10-41 ТОЙ ЖЕ ФОРМОЙ И С ТЕМ ЖЕ
    ОБЯЗАТЕЛЬСТВОМ: ``banner_ids`` называет идентификаторы заготовок плашки
    отказа и нужен ТОЛЬКО сценарию снятия заготовок; умолчание оставляет все
    восемь действующих сценариев байт-в-байт прежними. Неизменность их вердиктов
    утверждена ЗАМЕРОМ, а не обещанием: прогон всего модуля ДО правки дал
    ``84 passed``, ПОСЛЕ — ``88 passed`` (те же 84 плюс четыре новых правила
    плана 10-41).

    ⚠️ ИМЯ ПРИЗНАКА СКРЫТОСТИ ЕДЕТ В ПАВЛОАДЕ КЛЮЧОМ, А НЕ ВХОДОМ ФУНКЦИИ, И
    ВВОЗИТСЯ ОНО ЛЕНИВО. Гарниру нужно ЧЕМ спрашивать сумку атрибутов, но
    величина эта — свойство заготовок, а не решение вызывающего, и вторым входом
    она дала бы каждому вызову повод её переопределить. Ввоз идёт ВНУТРИ функции
    и ТОЛЬКО при непустом перечне: в ``tests/test_pages/test_shell.py`` на уровне
    модуля стои́т утверждение, срабатывание которого роняет СБОР файла целиком
    (`REVIEW-8/IN-01`, владелец — план 10-45), и безусловный ввоз перенёс бы этот
    отказ на восемь сценариев, к заготовкам отношения не имеющих.
    """
    hidden_attr = ""
    if banner_ids:
        from tests.test_pages.test_shell import FAILURE_BANNER_HIDDEN_ATTR

        hidden_attr = FAILURE_BANNER_HIDDEN_ATTR

    payload = json.dumps(
        {
            "expression": expression,
            "scenario": scenario,
            "lock": SCROLL_LOCK_CLASS,
            "after_request": after_request,
            "landing_id": FOCUS_LANDING_ID,
            "landing_present": landing_present,
            "event_shape": event_shape,
            "dismissal": dismissal,
            "sending": sending,
            "banner_ids": list(banner_ids),
            "hidden_attr": hidden_attr,
        }
    )
    assert MODAL_LIFECYCLE_HARNESS.count("__PAYLOAD__") == 1, (
        "образец подстановки павлоада встречается в гарнире не один раз — "
        "подстановка стала бы молчаливой"
    )
    return run_node_script(MODAL_LIFECYCLE_HARNESS.replace("__PAYLOAD__", payload))


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


# --- ВЕТВЬ ПО УСПЕШНОСТИ ОБМЕНА И ПРИЗЕМЛЕНИЕ ФОКУСА (план 10-02) ------------
#
# ⚠️ ПРАВИЛА НИЖЕ ИСПОЛНЯЮТ ВЫРАЖЕНИЯ, А НЕ ИЩУТ В НИХ ПОДСТРОКУ. Разметочная
# половина допустима только как ДОПОЛНЕНИЕ к поведенческой: правило на вхождении
# строки в этом дереве уже признано недостаточным (план 09-17, WR-03 четвёртого
# круга) — и признано на ЭТОМ ЖЕ объекте. Панель, у которой ветвь стои́т в
# атрибуте текстуально, но фокус никуда не едет, зеленела бы у разметочного
# правила посимвольно так же, как исправная.


def test_the_panel_closes_only_on_a_successful_exchange():
    """РАЗМЕТОЧНОЕ: первичный предикат — признак СОБЫТИЯ, сброс отправки ВНЕ ветви.

    ⚠️ ИМЯ ПРАВИЛА СОХРАНЕНО НАМЕРЕННО, А ТЕЛО ПЕРЕСТРОЕНО (план 10-05). Имя
    называют три записи — шапка `app/templates/components/modal.html`,
    `10-CONTEXT.md` (D-12) и `10-02-SUMMARY.md`; переименование осиротило бы их
    все разом.

    ⚠️ ЧТО ИМЕННО УЕХАЛО ИЗ ЭТОГО ПРАВИЛА И КУДА — НАЗВАНО ЗДЕСЬ, ЧТОБЫ
    СЛЕДУЮЩИЙ ЧИТАТЕЛЬ НЕ СЧЁЛ ПОЛОВИНУ ПОТЕРЯННОЙ. Уехала ПОВЕДЕНЧЕСКАЯ
    половина (сценарий `exchange`): она исполняла форму события, синтезированную
    из БУЛЕВА — `{ detail: { successful: … } }`, — которой рантайм на транспорте
    перехода не производит ВОВСЕ, и потому была зелена независимо от
    исправности предмета (гейп 1 верификации фазы). Ровно то же самое
    утверждается теперь на ЧЕТЫРЁХ РЕАЛЬНЫХ формах события:
    `test_the_panel_closes_on_the_location_transport` и
    `test_the_panel_closes_on_the_fragment_transport` — успех,
    `test_the_panel_stays_open_when_the_server_refused_on_either_transport` и
    `test_the_panel_stays_open_when_the_exchange_never_completed_on_either_transport`
    — отказ, с отрицательным контролем
    `test_control_negative_an_unconditional_close_reddens_both_failure_transports`
    поверх обоих.

    Здесь остаётся половина РАЗМЕТОЧНАЯ и механизмо-независимая: первичным
    предикатом остаётся признак успешности СОБЫТИЯ (второго определения успеха
    по коду ответа проект не заводит — отвергающая формулировка D-12 в силе), а
    сброс признака отправки стои́т ВНЕ ветви закрытия. Второе утверждение
    несущее: сброс, уехавший ВНУТРЬ ветви, оставил бы человеку после отказа
    включённую праздную кнопку с признаком занятости — рантайм свою блокировку
    снимает, а признак остался бы поднятым до СЛЕДУЮЩЕГО открытия панели.
    """
    expression = _modal_after_request_expression(_modal_block())

    assert "detail.successful" in expression, (
        "выражение завершения запроса не читает признак успешности события — "
        "либо ветви нет вовсе, либо первичным предикатом стало ВТОРОЕ "
        "определение успеха по коду ответа, молча расходящееся с блоком "
        f"конфигурации `responseHandling`: {expression!r}"
    )
    assert "hide()" in expression, (
        f"выражение завершения запроса панель не закрывает вовсе: {expression!r}"
    )

    # Сброс признака отправки — ВНЕ ветви закрытия. Граница ветви — ключевое
    # слово условия; всё, что стои́т до него, исполняется БЕЗУСЛОВНО.
    head, keyword, tail = expression.partition("if ")
    assert keyword, (
        "в выражении завершения запроса нет условия вовсе — панель закрывается "
        f"на ЛЮБОМ завершении запроса: {expression!r}"
    )
    assert SENDING_RESET in head, (
        "сброс признака отправки не стои́т ПЕРЕД условием закрытия: "
        f"выражение: {expression!r}"
    )
    assert SENDING_RESET not in tail, (
        "сброс признака отправки уехал ВНУТРЬ ветви закрытия: после отказа "
        "рантайм снимет свою блокировку с кнопки подтверждения, а признак "
        "занятости останется поднятым до следующего открытия панели — на "
        f"экране включённая праздная кнопка; выражение: {expression!r}"
    )


# --- ТРАНСПОРТЫ ЗАВЕРШЕНИЯ ЗАПРОСА (план 10-05, закрытие гейпа 1) ------------
#
# ⚠️ ЧЕМ ЭТИ ПРАВИЛА ОТЛИЧАЮТСЯ ОТ ПРЕЖНИХ: они кормят гарнир формами события,
# СНЯТЫМИ С ВЕНДОРЕННОГО БАНДЛА, а не синтезированными из булева. Прежняя
# поведенческая половина исполняла `{ detail: { successful: … } }` — форму,
# которой рантайм на транспорте перехода не производит ВОВСЕ, — и потому была
# зелена независимо от исправности предмета. Это и есть предмет гейпа 1 отчёта
# верификации фазы.

# ⚠️ ДОСЛОВНО СЕГОДНЯШНЕЕ (до правки плана 10-05) ВЫРАЖЕНИЕ — ЛИТЕРАЛОМ, А НЕ
# ЧТЕНИЕМ ИЗ ШАБЛОНА: после правки его в шаблоне не будет, и контроль,
# читающий шаблон, стал бы контролировать сам себя. Литерал сличается с
# прочитанным из шаблона на НЕРАВЕНСТВО — подстановка обязана доказать, что
# изменила что-то, и что изменила ИМЕННО ТО (идиома двойного предохранителя
# `_xdata_with_dead_teardown`).
SUCCESSFUL_ONLY_BRANCH = "sending = false; if ($event.detail.successful) hide()"

# Сброс признака отправки — ДОСЛОВНО, потому что его положение ОТНОСИТЕЛЬНО
# ветви закрытия и есть предмет утверждения, а не его наличие.
SENDING_RESET = "sending = false"

# --- ПОДСТАНОВКИ ОТРИЦАТЕЛЬНЫХ КОНТРОЛЕЙ (план 10-05) -----------------------
#
# ⚠️ ПРАВИЛО, ЗЕЛЁНОЕ ПЕРВЫМ ЖЕ ПРОГОНОМ, ОБЯЗАНО НЕСТИ КОНТРОЛЬ, ДОКАЗЫВАЮЩИЙ,
# ЧТО ОНО УМЕЕТ КРАСНЕТЬ. Формы события заведены задачей 2 плана раньше правил
# задачи 3, поэтому наблюдённого перехода цвета у пяти правил ниже быть не может
# по построению — их зубы держатся ИСКЛЮЧИТЕЛЬНО на этих подстановках, и
# подстановка каждый раз сличается с прочитанным из шаблона на неравенство.

# Панель, не закрывающаяся НИКОГДА: краснит оба правила успешных транспортов.
NEVER_CLOSING_BRANCH = "sending = false;"

# Панель, закрывающаяся БЕЗУСЛОВНО: ровно тот «оптимистичный UI», который веха
# запретила поимённо, — обязана покраснить оба правила отказа.
UNCONDITIONAL_CLOSE_BRANCH = "sending = false; hide()"

# Панель, уходящая ВЕТВЬЮ СНОСА вместо ветви закрытия: краснит правило
# атрибуции. Без неё правило атрибуции зелено и у панели, которая закрывается
# не тем путём, — а различить эти два пути правило и заведено (WR-07).
CLOSE_VIA_TEARDOWN_BRANCH = "sending = false; destroy()"

# Дизъюнкт транспорта БЕЗ проверки присутствия объекта запроса — ровно та форма,
# которую разметочная половина правила несостоявшегося обмена обязана отвергать.
UNGUARDED_LOCATION_BRANCH = (
    "sending = false; if ($event.detail.successful || "
    "$event.detail.xhr.getResponseHeader('HX-Location')) hide()"
)

# Присутствие объекта запроса, проверенное ДО обращения к его методу чтения
# заголовка. Две допустимые идиомы: короткое замыкание и необязательная цепочка.
XHR_PRESENCE_GUARD_RE = re.compile(r"\$event\.detail\.xhr\s*(?:&&|\?\.)")


def _guards_the_request_object(expression: str) -> bool:
    """Защищено ли обращение к методу чтения заголовка проверкой присутствия.

    ⚠️ ПРОВЕРКА РАЗМЕТОЧНАЯ, И ПРИЧИНА НАЗВАНА ЗДЕСЬ, А НЕ ОСТАВЛЕНА НА ДОГАДКУ.
    Поведенческого различителя у этой защиты НЕТ и быть не может: объект запроса
    присутствует на ВСЕХ четырёх реальных формах события — он собирается ДО
    отправки запроса (`const T={xhr:g,…}`) и летит тем же объектом из
    `onerror`/`onabort`/`ontimeout`, — измерено по вендоренному бандлу. Поэтому
    снятие защиты ни одной из четырёх форм не покраснит, и единственное, чем
    защита стережётся, — это утверждение о ТЕКСТЕ выражения.
    Что защита стои́т не зря: обращение к методу отсутствующего объекта упало бы
    исключением ВНУТРИ слушателя, а упавший слушатель оставляет панель открытой,
    то есть выглядит РОВНО как исправное поведение на путях отказа — отказ был
    бы неотличим от успеха защиты.
    """
    if "getResponseHeader" not in expression:
        # Заголовка не читает — защищать нечего.
        return True
    return XHR_PRESENCE_GUARD_RE.search(expression) is not None


def test_the_panel_closes_on_the_location_transport():
    """НЕСУЩЕЕ: панель закрывается на транспорте `HX-Location` (16 из 18 мест).

    Критерий 3 роадмапа называет механизм закрытия ПОИМЁННО
    (`x-on:htmx:after-request`), а на транспорте, которым `respond()` отвечает на
    ВСЕХ нефрагментных ветках, он не работал: обработчик ответа htmx рано
    возвращается из ветки заголовка перехода, единственное присваивание признака
    успешности стои́т ПОСЛЕ этого возврата, и `$event.detail.successful` есть
    `undefined`. Уборка целиком зависела от свопа тела документа по follow-up
    GET — не доехал своп, и панель осталась висеть поверх устаревшего экрана с
    блокировкой прокрутки на корневом элементе.

    ⚠️ ФОРМА СОБЫТИЯ ЗДЕСЬ РЕАЛЬНАЯ, А НЕ СИНТЕЗИРОВАННАЯ, и ключа признака
    успешности в ней НЕТ ВОВСЕ — не `false`, а отсутствует. Это утверждается
    полем вердикта, а не оставляется на веру: гарнир, подменяющий отсутствие
    ложью, стерёг бы не то.

    ⚠️ РАЗМЕТОЧНАЯ ПОЛОВИНА ЗДЕСЬ МЕХАНИЗМО-НЕЗАВИСИМА: она утверждает, что
    выражение читает величину, выставляемую рантаймом на ОБОИХ транспортах, то
    есть обращается к объекту запроса события. Утверждение верно при любой из
    двух ветвей, рассмотренных на останове владельца.
    """
    rendered = _modal_block()
    expression = _modal_after_request_expression(rendered)

    assert "detail.xhr" in expression, (
        "выражение завершения запроса не обращается к объекту запроса события: "
        "оно читает только признак успешности, которого на транспорте перехода "
        "не существует, и ветвь закрытия мертва на 16 из 18 мест подтверждения; "
        f"выражение: {expression!r}"
    )

    verdict = _run_modal_lifecycle(
        _modal_xdata_expression(rendered),
        "transports",
        after_request=expression,
        event_shape="location",
    )

    assert verdict["successful_key_present"] is False, (
        "форма события транспорта перехода несёт ключ признака успешности — "
        "гарнир подаёт форму, которой рантайм на этом пути НЕ ПРОИЗВОДИТ, и "
        f"правило снова зелено в вакууме; вердикт: {verdict}"
    )
    assert verdict["threw"] is None, (
        "выражение завершения запроса упало исключением внутри слушателя: "
        "панель осталась бы открытой, и выглядело бы это как исправное "
        f"поведение; вердикт: {verdict}"
    )
    assert verdict["open"] is False, (
        "на транспорте `HX-Location` панель ОСТАЛАСЬ ОТКРЫТОЙ: механизм, "
        "названный критерием 3 поимённо, на 16 из 18 мест подтверждения не "
        f"работает, и уборка целиком зависит от свопа тела документа; {verdict}"
    )
    assert verdict["locked"] is False, (
        "панель закрылась, а признак блокировки прокрутки остался на корневом "
        f"элементе: экран остался неспособным прокручиваться; вердикт: {verdict}"
    )
    assert verdict["sending"] is False, (
        "сброс признака отправки на транспорте перехода не произошёл: кнопка "
        f"подтверждения осталась бы занятой; вердикт: {verdict}"
    )
    assert verdict["repeat_matches"] is True, (
        f"повторное исполнение сценария транспорта дало ДРУГОЙ исход: {verdict}"
    )


def test_control_negative_the_successful_only_branch_is_dead_on_the_location_transport():
    """ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ: правило выше УМЕЕТ КРАСНЕТЬ на прежнем выражении.

    Гейт, зелёный на сегодняшнем дереве, гейтом не является — именно этим
    критерий 3 и был провален в первый раз: правило
    `test_the_panel_closes_only_on_a_successful_exchange` зеленело на форме
    события, которой рантайм на доминирующем транспорте не производит.

    Контроль подставляет выражение, ДОСЛОВНО равное прежнему, и обязан получить
    панель, ОСТАВШУЮСЯ открытой: ветвь по одному лишь признаку успешности на
    этом транспорте МЕРТВА. Подстановка сличается с прочитанным из шаблона на
    неравенство — иначе контроль контролировал бы сам себя.
    """
    rendered = _modal_block()
    live = _modal_after_request_expression(rendered)

    assert live != SUCCESSFUL_ONLY_BRANCH, (
        "выражение шаблона ДОСЛОВНО равно прежнему: правка ветви не "
        "приземлилась, и контроль ниже подставляет то же самое, что уже стои́т "
        f"в шаблоне — доказывать ему нечего; выражение: {live!r}"
    )

    verdict = _run_modal_lifecycle(
        _modal_xdata_expression(rendered),
        "transports",
        after_request=SUCCESSFUL_ONLY_BRANCH,
        event_shape="location",
    )

    assert verdict["open"] is True, (
        "прежняя ветвь ЗАКРЫЛА панель на форме события транспорта перехода — "
        "значит гарнир подаёт не ту форму, и несущее правило выше зелено в "
        f"вакууме; вердикт: {verdict}"
    )
    assert verdict["locked"] is True, (
        "прежняя ветвь панель не закрыла, а признак блокировки прокрутки с "
        f"корневого элемента всё же снялся — состояние разъехалось: {verdict}"
    )
    assert verdict["branches"] == [], (
        "прежняя ветвь отработала ветвью ухода узла на транспорте перехода — "
        f"мёртвой она не была, и предмет гейпа 1 назван неверно: {verdict}"
    )
    assert verdict["sending"] is False, (
        "сброс признака отправки у прежнего выражения не произошёл — контроль "
        f"подставил не то выражение: {verdict}"
    )


def _transport_verdict(shape: str, *, expression: str | None = None) -> dict:
    """Вердикт сценария транспортов на названной форме события.

    Умолчание выражения — ПРОЧТЁННОЕ ИЗ ШАБЛОНА: предмет правил ниже — панель,
    которая отгружается, а не литерал в файле правил. Подстановка называется
    явно и только там, где она есть отрицательный контроль.
    """
    rendered = _modal_block()
    return _run_modal_lifecycle(
        _modal_xdata_expression(rendered),
        "transports",
        after_request=(
            expression
            if expression is not None
            else _modal_after_request_expression(rendered)
        ),
        event_shape=shape,
    )


def test_the_panel_closes_on_the_fragment_transport():
    """НЕСУЩЕЕ: панель закрывается и на фрагментном транспорте (2 места из 18).

    Форма события снята с ветви свопа вендоренного бандла: своп состоялся,
    признаки присвоены (`e.target=r;e.failed=a;e.successful=!a`, смещение
    48145), заголовка перехода в ответе нет. Дизъюнкту транспорта сработать не
    на чем — закрывает ПЕРВИЧНЫЙ предикат, признак успешности самого рантайма.

    ⚠️ КОНТРОЛЬ ВСТРОЕН, ПОТОМУ ЧТО ПРАВИЛО ЗЕЛЕНО ПЕРВЫМ ЖЕ ПРОГОНОМ: формы
    события заведены задачей 2 плана, наблюдённого перехода цвета у него быть не
    может, и без подстановки «панель не закрывается никогда» оно зеленело бы у
    панели, у которой ветви закрытия нет вовсе.
    """
    verdict = _transport_verdict("fragment")

    assert verdict["successful_key_present"] is True, (
        "форма события фрагментного транспорта НЕ несёт ключа признака "
        "успешности — она снята не с ветви свопа, и правило проверяет не тот "
        f"путь; вердикт: {verdict}"
    )
    assert verdict["location_header"] is None, (
        "форма события фрагментного транспорта отдаёт заголовок перехода: "
        "закрыть панель мог дизъюнкт транспорта, и первичный предикат остался "
        f"непроверенным; вердикт: {verdict}"
    )
    assert verdict["threw"] is None, (
        f"выражение упало исключением внутри слушателя: {verdict}"
    )
    assert verdict["open"] is False, (
        "на фрагментном транспорте панель ОСТАЛАСЬ ОТКРЫТОЙ: подтверждённое "
        f"удаление выполнено, а окно висит поверх результата; {verdict}"
    )
    assert verdict["locked"] is False, (
        "панель закрылась, а признак блокировки прокрутки остался на корневом "
        f"элементе: {verdict}"
    )
    assert verdict["sending"] is False, (
        f"сброс признака отправки не произошёл: {verdict}"
    )
    assert verdict["repeat_matches"] is True, (
        f"повторное исполнение сценария дало ДРУГОЙ исход: {verdict}"
    )

    control = _transport_verdict("fragment", expression=NEVER_CLOSING_BRANCH)
    assert control["open"] is True, (
        "подстановка, которая панель не закрывает ВООБЩЕ, дала закрытую панель: "
        "правило выше зелено независимо от предмета и краснеть не умеет; "
        f"вердикт контроля: {control}"
    )


def test_the_panel_stays_open_when_the_server_refused_on_either_transport():
    """НЕСУЩЕЕ (защитная половина D-12): отказ сервера панель не закрывает.

    Форма события отказа: заголовка перехода в ответе НЕТ ни на каком
    транспорте — сервер отказал, и ранний возврат ветки перехода не сработал, —
    поэтому признаки присвоены штатно: успешность ложна, отказ истинен, код 500.
    Дизъюнкту транспорта сработать не на чем, и это утверждается полем
    `location_header`, а не выводится из имени формы: отсюда «ни на одном
    транспорте» в имени правила.

    Цена закрытия названа вехой поимённо и запрещена ею же под именем
    «оптимистичный UI»: панель ушла бы, действие выполнено НЕ было, а экран
    выглядел бы так, будто всё получилось. Оставшаяся открытой панель —
    ЖЕЛАЕМОЕ поведение: поверх неё встаёт плашка аварии QUAL-03, и повторить
    можно, не открывая панель заново.

    Умеет ли правило краснеть — доказывает
    `test_control_negative_an_unconditional_close_reddens_both_failure_transports`.
    """
    verdict = _transport_verdict("refused")

    assert verdict["successful_key_present"] is True, (
        "на отказе сервера ключ признака успешности ОТСУТСТВУЕТ — форма снята "
        "не с ветви свопа: при 5xx ранний возврат ветки перехода не срабатывает "
        f"и признак присваивается штатно ложью; вердикт: {verdict}"
    )
    assert verdict["location_header"] is None, (
        "форма события отказа отдаёт заголовок перехода — такого ответа сервер "
        f"на отказе не даёт, и правило проверяет не тот путь: {verdict}"
    )
    assert verdict["threw"] is None, (
        f"выражение упало исключением внутри слушателя: {verdict}"
    )
    assert verdict["open"] is True, (
        "при ОТКАЗЕ СЕРВЕРА панель закрылась: действие выполнено не было, а "
        "экран выглядит так, будто всё получилось — оптимистичный UI, "
        f"запрещённый вехой поимённо; вердикт: {verdict}"
    )
    assert verdict["locked"] is True, (
        "панель осталась открытой, а признак блокировки прокрутки с корневого "
        f"элемента снялся — состояние разъехалось: {verdict}"
    )
    assert verdict["branches"] == [], (
        "на отказе сервера отработала ветвь ухода узла — панель ушла с экрана "
        f"путём, которого на этом пути быть не должно: {verdict}"
    )
    assert verdict["sending"] is False, (
        "сброс признака отправки не произошёл на ОТКАЗЕ, а это единственный "
        "путь, на котором он виден человеку: рантайм снимает свою блокировку, и "
        "на экране остаётся включённая праздная кнопка с признаком занятости; "
        f"вердикт: {verdict}"
    )
    assert verdict["repeat_matches"] is True, (
        f"повторное исполнение сценария дало ДРУГОЙ исход: {verdict}"
    )


def test_the_panel_stays_open_when_the_exchange_never_completed_on_either_transport():
    """НЕСУЩЕЕ: обрыв, отмена и таймаут панель не закрывают, и выражение не падает.

    Форма события снята с обработчиков отказа ТРАНСПОРТА, а не ответа:
    `g.onerror`, `g.onabort` и `g.ontimeout` диспетчеризуют событие завершения
    запроса с ТЕМ ЖЕ объектом, а обработчик ответа `Vn` на этих путях не
    вызывается ВОВСЕ — значит ключа признака успешности НЕТ (не ложь, а
    отсутствие), код ответа равен нулю, чтение заголовка даёт пустоту.
    Клиентского тайм-аута у проекта нет (ключа в блоке `responseHandling` нет,
    умолчание рантайма равно нулю) — путь таймаута приходит от сервера или от
    сети, но форма события у него та же.

    ⚠️ ЭТО ПРАВИЛО — ЕДИНСТВЕННОЕ, СТЕРЕГУЩЕЕ ЗАЩИТУ ОБРАЩЕНИЯ К ОБЪЕКТУ
    ЗАПРОСА, и стережёт оно её РАЗМЕТОЧНО. Поведенческого различителя у защиты
    нет: объект запроса присутствует на всех четырёх формах — основание
    выписано целиком у `_guards_the_request_object`. Что подстановка без защиты
    утверждение действительно краснит, доказывается тут же, а не обещается.
    """
    expression = _modal_after_request_expression(_modal_block())

    assert _guards_the_request_object(expression), (
        "обращение к методу чтения заголовка перехода НЕ защищено проверкой "
        "присутствия объекта запроса: у отсутствующего объекта выражение упало "
        "бы исключением ВНУТРИ слушателя, а упавший слушатель оставляет панель "
        "открытой — то есть выглядит ровно как исправное поведение на путях "
        f"отказа; выражение: {expression!r}"
    )
    assert not _guards_the_request_object(UNGUARDED_LOCATION_BRANCH), (
        "утверждение выше зелено и на выражении БЕЗ защиты — проверять ему "
        "нечего, и снятие защиты оно не покраснит"
    )

    verdict = _transport_verdict("never_completed")

    assert verdict["successful_key_present"] is False, (
        "на несостоявшемся обмене ключ признака успешности ПРИСУТСТВУЕТ — "
        "форма снята не с обработчиков отказа транспорта: обработчик ответа на "
        f"этих путях не вызывается вовсе; вердикт: {verdict}"
    )
    assert verdict["location_header"] is None, (
        f"у несостоявшегося обмена чтение заголовка дало значение: {verdict}"
    )
    assert verdict["threw"] is None, (
        "выражение УПАЛО ИСКЛЮЧЕНИЕМ на несостоявшемся обмене: панель осталась "
        "бы открытой по причине отказа, а не по ветви, и отличить одно от "
        f"другого стало бы нечем; вердикт: {verdict}"
    )
    assert verdict["open"] is True, (
        "при НЕСОСТОЯВШЕМСЯ ОБМЕНЕ (обрыв сети, отмена, таймаут) панель "
        "закрылась: запрос до сервера не доехал, ничего выполнено не было, а "
        f"экран выглядит так, будто получилось; вердикт: {verdict}"
    )
    assert verdict["locked"] is True, (
        "панель осталась открытой, а признак блокировки прокрутки с корневого "
        f"элемента снялся — состояние разъехалось: {verdict}"
    )
    assert verdict["branches"] == [], (
        f"на несостоявшемся обмене отработала ветвь ухода узла: {verdict}"
    )
    assert verdict["sending"] is False, (
        f"сброс признака отправки не произошёл: {verdict}"
    )
    assert verdict["repeat_matches"] is True, (
        f"повторное исполнение сценария дало ДРУГОЙ исход: {verdict}"
    )


def test_the_rule_names_which_branch_closed_the_panel_on_both_transports():
    """НЕСУЩЕЕ (закрытие WR-07): утверждается ИМЯ ветви, а не позиция фокуса.

    Две ветви ухода узла — закрытие и снос — обе зовут единственное объявленное
    выражение приземления, и по ИТОГОВОЙ ПОЗИЦИИ ФОКУСА они неразличимы. Пока
    правило утверждало позицию, запись шапки об атрибуции оставалась
    непроверяемой, и обе ветви были взаимозаменяемы: ровно поэтому запись
    и разошлась с рантаймом (WR-07 ревизии фазы, третья запись `artifacts`
    гейпа 1 верификации).

    На ОБОИХ успешных транспортах отрабатывает ЗАКРЫТИЕ. Снос, приходящий
    ПОСЛЕ него (рантайм клиентского состояния сносит компонент из колбэка
    наблюдателя мутаций — микрозадачей позже), в перечень ДОБАВЛЯЕТСЯ, но
    застаёт панель уже закрытой, и его собственный страж состояния делает его
    ПУСТОЙ ОПЕРАЦИЕЙ. «Пустая операция» и «ветвь не звалась» — два разных факта,
    и вердикт различает их отдельным полем, а не перечнем имён.
    """
    for shape in ("location", "fragment"):
        verdict = _transport_verdict(shape)

        assert verdict["branches"] == ["hide"], (
            f"на транспорте {shape} панель ушла НЕ ветвью закрытия: запись "
            "шапки об атрибуции двух ветвей снова разошлась с рантаймом; "
            f"вердикт: {verdict}"
        )
        assert verdict["teardown"]["branches"] == ["hide", "destroy"], (
            f"на транспорте {shape} снос узла не позвал ветви сноса вовсе — "
            f"сносить панель стало нечем; вердикт: {verdict}"
        )
        assert verdict["teardown"]["was_a_noop"] is True, (
            f"на транспорте {shape} ветвь сноса застала панель ОТКРЫТОЙ: "
            "значит закрытие не отработало, и уборка снова зависит от свопа "
            f"тела документа; вердикт: {verdict}"
        )
        assert verdict["teardown"]["locked"] is False, (
            f"после сноса на транспорте {shape} признак блокировки прокрутки "
            f"остался на корневом элементе: {verdict}"
        )

        control = _transport_verdict(shape, expression=CLOSE_VIA_TEARDOWN_BRANCH)
        assert control["branches"] == ["destroy"], (
            f"на транспорте {shape} подстановка, уходящая ВЕТВЬЮ СНОСА, дала "
            "тот же перечень имён, что и ветвь закрытия: правило атрибуции две "
            f"ветви не различает и стережёт запись шапки вхолостую; {control}"
        )


def test_control_negative_an_unconditional_close_reddens_both_failure_transports():
    """ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ: два правила отказа умеют краснеть.

    Без него правила отказа зелены и у панели, которая не закрывается НИКОГДА —
    в том числе у той, чьё выражение упало исключением на первой же строке.
    Подстановка закрывает панель БЕЗУСЛОВНО, то есть выражает ровно тот
    «оптимистичный UI», который веха запретила поимённо, и обязана дать закрытую
    панель на ОБЕИХ формах отказа.
    """
    live = _modal_after_request_expression(_modal_block())
    assert live != UNCONDITIONAL_CLOSE_BRANCH, (
        "выражение шаблона закрывает панель БЕЗУСЛОВНО — подстановке нечего "
        f"доказывать, а панель ушла бы с экрана после отказа: {live!r}"
    )

    for shape in ("refused", "never_completed"):
        control = _transport_verdict(shape, expression=UNCONDITIONAL_CLOSE_BRANCH)

        assert control["open"] is False, (
            f"на форме отказа {shape} безусловное закрытие панель НЕ закрыло: "
            "значит правило отказа зелено независимо от предмета — оно не "
            f"отличает исправную панель от не закрывающейся вовсе; {control}"
        )
        assert control["branches"] == ["hide"], (
            f"на форме отказа {shape} безусловное закрытие не позвало ветви "
            f"закрытия: подстановка не сработала, и контроль вхолостую; {control}"
        )
        assert control["locked"] is False, (
            f"на форме отказа {shape} безусловное закрытие оставило признак "
            f"блокировки прокрутки: подстановка сработала наполовину; {control}"
        )


# --- УХОД ПАНЕЛИ ПО ВОЛЕ ЧЕЛОВЕКА ВО ВРЕМЯ ЛЕТЯЩЕГО ЗАПРОСА (план 10-07) ----
#
# Предмет — `DEF-09-02`, находка ручного обхода Фазы 9 с назначенной Фазой 10.
# Человек, нажавший уход на медленной сети, считает, что отменил удаление, — а
# удаление происходит: уход панели летящего запроса НЕ ОТМЕНЯЕТ. Фаза 10
# РАСШИРИЛА предмет с одного места до 18, раздав признак отправки всем панелям
# подтверждения и не спросив его ни на одном пути ухода.

# ⚠️ ДОСЛОВНО СЕГОДНЯШНЕЕ (до правки плана 10-07) ВЫРАЖЕНИЕ ПУТИ УХОДА —
# ЛИТЕРАЛОМ, А НЕ ЧТЕНИЕМ ИЗ ШАБЛОНА: после правки его там не будет, и контроль,
# читающий шаблон, стал бы контролировать сам себя. Литерал сличается с
# прочитанным из шаблона на НЕРАВЕНСТВО — подстановка обязана доказать, что
# изменила что-то, и что изменила ИМЕННО ТО (идиома двойного предохранителя
# `_xdata_with_dead_teardown`).
UNGATED_DISMISSAL = "hide()"


def _dismissal_verdict(
    expression: str,
    *,
    sending: bool,
    after_request: str = "",
    event_shape: str = "",
) -> dict:
    """Вердикт сценария ухода на поданном выражении и признаке отправки."""
    rendered = _modal_block()
    return _run_modal_lifecycle(
        _modal_xdata_expression(rendered),
        "dismissal",
        dismissal=expression,
        sending=sending,
        after_request=after_request,
        event_shape=event_shape,
    )


def test_the_panel_refuses_dismissal_while_the_request_is_in_flight():
    """НЕСУЩЕЕ (DEF-09-02): панель не уходит, пока необратимый запрос летит.

    Цена отказа названа поимённо в отчёте верификации фазы и в независимом
    разборе ревизии (§WR-09): запрос продолжается против компонента, чьё
    собственное состояние уже ложно, доходит до сервера и выполняет необратимое
    действие, — а на маршрутах, не выдающих плашки на успех (D-03), человек не
    получает НИКАКОГО сигнала о том, что оно произошло.

    ⚠️ ТРИ УТВЕРЖДЕНИЯ О СОСТОЯНИИ, А НЕ ОДНО. Панель, «оставшаяся открытой» с
    уже снятым признаком блокировки прокрутки, есть ТРЕТЬЕ состояние — и оно
    молчаливое: на экране всё выглядит исправно, а страница за панелью снова
    прокручивается. Фокус, уехавший с кнопки отказа при оставшейся панели, есть
    четвёртое.

    ⚠️ ИСПОЛНЯЕТСЯ ВЫРАЖЕНИЕ АТРИБУТА, А НЕ МЕТОД ОБЪЕКТА: предмет здесь ветвь,
    записанная в АТРИБУТЕ. Правило, зовущее `hide()` напрямую, зеленело бы на
    панели, у которой гейта в атрибуте нет вовсе.
    """
    for path, expression in _modal_dismissal_expressions(_modal_block()).items():
        verdict = _dismissal_verdict(expression, sending=True)

        assert verdict["threw"] is None, (
            f"выражение пути «{path}» упало исключением внутри слушателя: панель "
            "осталась бы открытой, и выглядело бы это РОВНО как исправно "
            f"сработавший гейт; вердикт: {verdict}"
        )
        assert verdict["open"] is True, (
            f"путь «{path}» УНЁС ПАНЕЛЬ С ЭКРАНА во время летящего необратимого "
            "запроса: человек считает действие отменённым, а оно происходит — и "
            f"это верно на всех 18 местах подтверждения сразу; вердикт: {verdict}"
        )
        assert verdict["locked"] is True, (
            f"на пути «{path}» панель осталась открытой, а признак блокировки "
            "прокрутки с корневого элемента снялся — состояние разъехалось, и за "
            f"открытой панелью снова прокручивается страница; вердикт: {verdict}"
        )
        assert verdict["focused"] == verdict["focused_before"], (
            f"на пути «{path}» панель осталась открытой, а фокус уехал с кнопки "
            "отказа: ветвь приземления отработала при неушедшей панели, и обход "
            f"по клавише табуляции начинается вне панели; вердикт: {verdict}"
        )
        assert verdict["sending"] is True, (
            f"путь «{path}» сбросил признак отправки САМ: следующий уход прошёл "
            f"бы гейт, хотя запрос всё ещё летит; вердикт: {verdict}"
        )
        assert verdict["repeat_matches"] is True, (
            f"повторное исполнение пути «{path}» дало ДРУГОЙ исход: {verdict}"
        )


def test_control_negative_an_ungated_dismissal_reddens_the_gate():
    """ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ: правило выше УМЕЕТ КРАСНЕТЬ.

    Гейт, зелёный на сегодняшнем дереве, гейтом не является. Контроль
    подставляет выражение, ДОСЛОВНО равное сегодняшнему, и обязан получить
    панель, УШЕДШУЮ С ЭКРАНА при истинном признаке отправки. Подстановка
    сличается с прочитанным из шаблона на неравенство — иначе контроль
    контролировал бы сам себя.
    """
    live = _modal_dismissal_expressions(_modal_block())

    for path, expression in live.items():
        assert expression != UNGATED_DISMISSAL, (
            f"выражение пути «{path}» ДОСЛОВНО равно сегодняшнему: гейт на этом "
            "пути не приземлился, и контроль ниже подставляет то же самое, что "
            f"уже стои́т в шаблоне — доказывать ему нечего; {expression!r}"
        )

        control = _dismissal_verdict(UNGATED_DISMISSAL, sending=True)

        assert control["open"] is False, (
            f"негейтированное выражение пути «{path}» НЕ закрыло панель при "
            "истинном признаке отправки: значит гарнир не исполняет выражение "
            f"вовсе, и несущее правило выше зелено в вакууме; вердикт: {control}"
        )
        assert control["branches"] == ["hide"], (
            f"негейтированное выражение пути «{path}» ушло НЕ ветвью закрытия: "
            f"подстановка сработала не так, как сегодняшнее выражение; {control}"
        )
        assert control["locked"] is False, (
            f"негейтированное выражение пути «{path}» панель закрыло, а признак "
            f"блокировки прокрутки не снялся: сработала наполовину; {control}"
        )


# Форма гейта — ОДНА на все три пути и повторяется ДОСЛОВНО: три разные формы
# одного условия разошлись бы молча. Имя поля и форма условия сняты с перехвата
# отправки на форме панели (`if (sending) { … return; }`) — у панели уже есть
# ОДИН способ спросить «запрос летит», и второй разошёлся бы с первым.
DISMISSAL_GATE_RE = re.compile(r"\bif\s*\(\s*sending\s*\)\s*return\s*;")

# Привязки отключённости и занятости, которых у кнопки ОТКАЗА быть не должно ни
# одной. Перечень закрытый и назван поимённо: «нет ни одной привязки» на
# открытом множестве было бы непроверяемым обещанием.
CANCEL_FORBIDDEN_BINDINGS = (
    "x-bind:disabled",
    ":disabled",
    "disabled=",
    "x-bind:aria-busy",
    ":aria-busy",
    "aria-busy=",
    "tabindex",
)

HX_DISABLED_ELT_RE = re.compile(r'hx-disabled-elt\s*=\s*"([^"]*)"')

CANCEL_LABEL_PROBE = "Не надо"


def _cancel_button_label(html_source: str) -> str:
    """Подпись кнопки отказа — текст между её тегом и закрывающим тегом."""
    tag = _modal_cancel_button_tag(html_source)
    start = html_source.index(tag) + len(tag)
    end = html_source.index("</button>", start)
    inner = html_source[start:end]
    return re.sub(r"<[^>]*>", "", inner).strip()


def test_the_panel_accepts_dismissal_once_the_request_has_ended():
    """ПОЛОЖИТЕЛЬНЫЙ КОНТРОЛЬ И ЗАЩИТА ОТ ЛОВУШКИ, а не гигиена.

    Без ПЕРВОЙ половины несущее правило зелено и у панели, которая не
    закрывается НИКОГДА, — то есть гейт неотличим от сломанного ухода.

    ВТОРАЯ половина НЕСУЩАЯ и есть то, чем гейт отличается от ЛОВУШКИ. Панель,
    пережившая ОТКАЗ СЕРВЕРА, обязана снова уходить по каждому из трёх путей:
    выражение завершения запроса сбрасывает признак отправки БЕЗУСЛОВНО, панель
    при этом остаётся открытой (D-12), и обещание D-12 — «повторить можно, не
    открывая её заново» — превращается в свою противоположность ровно тогда,
    когда после отказа панель не закрывается ничем.

    Форма события отказа взята из `EVENT_SHAPES` (план 10-05), а не выдумана:
    гарнир, синтезирующий её из булева, подавал бы форму, которой рантайм не
    производит.
    """
    rendered = _modal_block()
    after_request = _modal_after_request_expression(rendered)
    paths = _modal_dismissal_expressions(rendered)

    # ПОЛОВИНА 1: обмен не начинался — панель уходит по каждому из трёх путей.
    for path, expression in paths.items():
        verdict = _dismissal_verdict(expression, sending=False)

        assert verdict["threw"] is None, (
            f"выражение пути «{path}» упало исключением при ложном признаке "
            f"отправки; вердикт: {verdict}"
        )
        assert verdict["open"] is False, (
            f"путь «{path}» НЕ ЗАКРЫЛ панель при ложном признаке отправки: гейт "
            "стал ЛОВУШКОЙ — панель нельзя убрать с экрана вовсе, и несущее "
            f"правило выше зелено у неработающего ухода; вердикт: {verdict}"
        )
        assert verdict["locked"] is False, (
            f"путь «{path}» закрыл панель, а признак блокировки прокрутки "
            f"остался на корневом элементе; вердикт: {verdict}"
        )
        assert verdict["focused"] != verdict["focused_before"], (
            f"путь «{path}» закрыл панель, а фокус остался на кнопке отказа "
            f"снесённой панели — приземление не отработало; вердикт: {verdict}"
        )
        assert verdict["branches"] == ["hide"], (
            f"путь «{path}» ушёл НЕ ветвью закрытия; вердикт: {verdict}"
        )

    # ПОЛОВИНА 2: сервер ОТКАЗАЛ — признак сброшен, панель осталась, уход снова
    # работает по каждому из трёх путей.
    for path, expression in paths.items():
        verdict = _dismissal_verdict(
            expression,
            sending=True,
            after_request=after_request,
            event_shape="refused",
        )

        assert verdict["exchange"] is not None, (
            f"форма события отказа не прогонялась на пути «{path}»: вторая "
            f"половина контроля не исполнилась вовсе; вердикт: {verdict}"
        )
        assert verdict["exchange"]["open"] is True, (
            f"после ОТКАЗА СЕРВЕРА панель ушла с экрана сама (путь «{path}»): "
            "D-12 нарушен ещё до того, как человек чего-либо коснулся; вердикт: "
            f"{verdict}"
        )
        assert verdict["exchange"]["sending"] is False, (
            f"после ОТКАЗА СЕРВЕРА признак отправки НЕ СБРОШЕН (путь «{path}»): "
            "гейт стал ЛОВУШКОЙ — панель после отказа не закрывается ничем, и "
            "обещание D-12 «повторить можно, не открывая её заново» "
            f"превратилось в свою противоположность; вердикт: {verdict}"
        )
        assert verdict["open"] is False, (
            f"после ОТКАЗА СЕРВЕРА путь «{path}» панель НЕ ЗАКРЫЛ: гейт стал "
            f"ловушкой на живом маршруте отказа; вердикт: {verdict}"
        )
        assert verdict["locked"] is False, (
            f"после отказа путь «{path}» закрыл панель, а признак блокировки "
            f"прокрутки остался на корневом элементе; вердикт: {verdict}"
        )
        assert verdict["repeat_matches"] is True, (
            f"повторное исполнение пути «{path}» после отказа дало ДРУГОЙ исход: "
            f"{verdict}"
        )


def test_every_dismissal_path_of_the_panel_is_gated_on_the_in_flight_state():
    """ИНВЕНТАРЬ: число путей ухода объявлено, и КАЖДЫЙ несёт гейт.

    Правило существует затем, чтобы ЧЕТВЁРТЫЙ путь ухода, заведённый будущей
    фазой, не мог появиться без гейта МОЛЧА. Поведенческие правила выше обходят
    то, что вернул разборщик, и на новом негейтированном пути они молчали бы —
    разборщик о нём не знает. Здесь краснеет само расхождение чисел.

    ⚠️ СЧИТАЮТСЯ ПУТИ УХОДА ПО ВОЛЕ ЧЕЛОВЕКА, А НЕ ПУТИ УХОДА УЗЛА ИЗ ДОКУМЕНТА:
    это разные множества, и приводить их числа к согласию нельзя (запись над
    `DISMISSAL_PATHS_DECLARED`).
    """
    paths = _modal_dismissal_expressions(_modal_block())

    assert len(paths) == DISMISSAL_PATHS_DECLARED, (
        f"найдено {len(paths)} путей ухода ({sorted(paths)}), объявлено "
        f"{DISMISSAL_PATHS_DECLARED}: либо путь заведён без объявления, либо "
        "объявление разъехалось с разметкой"
    )

    ungated = {
        name: expression
        for name, expression in paths.items()
        if not DISMISSAL_GATE_RE.search(expression)
    }
    assert not ungated, (
        f"найдено {len(paths)} путей ухода, объявлено {DISMISSAL_PATHS_DECLARED}, "
        f"и гейта по признаку отправки НЕ НЕСУТ: {sorted(ungated)} — "
        f"их выражения: {ungated}. Панель уходит с экрана этими путями во время "
        "летящего необратимого запроса на всех 18 местах подтверждения"
    )

    forms = {DISMISSAL_GATE_RE.search(expression).group(0) for expression in paths.values()}
    assert len(forms) == 1, (
        f"формы гейта на путях ухода РАЗНЫЕ: {sorted(forms)}. Три разные формы "
        "одного условия расходятся молча — форма выбирается ОДНА и повторяется "
        "дословно"
    )


def test_the_cancel_button_stays_available_while_the_dismissal_is_gated():
    """СТРАЖА ЗАПИСАННОГО КОНТРАКТА О КНОПКЕ ОТКАЗА (угроза T-10-41).

    Записанный контракт шапки — «Кнопка ОТКАЗА не блокируется ничем: отмена
    разрушительного действия не имеет права быть труднее его подтверждения» —
    гейтом ПРОЧИТЫВАЕТСЯ, а не отменяется: недействующей на время полёта
    становится ВЕТВЬ УХОДА, потому что уход, не отменяющий запроса, есть не
    более лёгкая отмена, а ЛОЖНАЯ. Разница между «не действует, пока панель
    занята» и «недоступна» и есть предмет этого правила.

    ⚠️ ЗУБЫ ПРАВИЛА — АСИММЕТРИЯ, А НЕ ОТСУТСТВИЕ. Грепом по файлу это
    неразличимо: привязка отключённости присутствует в файле ЗАКОННО — у кнопки
    подтверждения, в селекторе отключения на форме и в перечислителе
    фокусируемых узлов объекта клиентского состояния, — и счёт вхождений их не
    различает. Пара утверждений «у отказа нет / у подтверждения есть» —
    единственное, чего греп дать не может, и она же служит антивакуумом: правило,
    зелёное при разборщике, вернувшем ОДИН И ТОТ ЖЕ тег на оба маркера, этой
    асимметрии дать не может.
    """
    rendered = _modal_block()
    cancel = _modal_cancel_button_tag(rendered)
    confirm = _modal_confirm_button_tag(rendered)

    # АНТИВАКУУМ — ДО остальных проверок: сличаемые теги обязаны быть РАЗНЫМИ.
    assert cancel != confirm, (
        "разборщик вернул ОДИН И ТОТ ЖЕ тег на оба маркера — асимметрия ниже "
        f"недоказуема, и правило зелено в вакууме; тег: {cancel!r}"
    )

    # 1. У кнопки отказа нет НИ ОДНОЙ привязки отключённости или занятости.
    present = [name for name in CANCEL_FORBIDDEN_BINDINGS if name in cancel]
    assert not present, (
        f"кнопка ОТКАЗА получила {present}: записанный контракт «отмена "
        "разрушительного действия не имеет права быть труднее его "
        "подтверждения» ОТМЕНЁН, а не прочитан — гейт ухода подменён "
        f"недоступностью элемента; тег: {cancel!r}"
    )

    # 2. АСИММЕТРИЯ: у кнопки ПОДТВЕРЖДЕНИЯ привязка отключённости ЕСТЬ.
    assert "x-bind:disabled" in confirm, (
        "у кнопки ПОДТВЕРЖДЕНИЯ привязки отключённости НЕТ: утверждение 1 выше "
        "перестало что-либо значить — оно зелено и у панели, где не отключается "
        f"ничего вовсе, и защита от повторной отправки снята; тег: {confirm!r}"
    )

    # 3. Селектор отключения рантайма кнопку отказа НЕ АДРЕСУЕТ.
    disabled_elt = HX_DISABLED_ELT_RE.search(_form_tag(rendered))
    assert disabled_elt, (
        "на форме панели нет селектора отключения рантайма: защита от повторной "
        "отправки на htmx-пути снята целиком"
    )
    selector = disabled_elt.group(1)
    assert "submit" in selector and "cancel" not in selector, (
        f"селектор отключения рантайма адресует кнопку отказа: {selector!r} — "
        "рантайм отключил бы её на время полёта, и контракт был бы отменён в "
        "обход разметки самой кнопки"
    )

    # 4. Ссылка начального фокуса на месте, а атрибута порядка обхода нет вовсе.
    assert CANCEL_MARKER in cancel, (
        f"кнопка отказа потеряла ссылку начального фокуса; тег: {cancel!r}"
    )

    # 5. Подпись НЕПУСТА и печатается ПАРАМЕТРОМ макроса: «стала недействующей
    #    ветвь ухода» не имеет права превратиться в «сменилась подпись».
    label = _cancel_button_label(rendered)
    assert label, f"подпись кнопки отказа пуста; разметка кнопки: {cancel!r}"

    probed = render(
        "components/modal.html",
        "modal",
        id="del-probe",
        title="Удалить?",
        action="/synthetic/probe",
        confirm_label="Удалить",
        cancel_label=CANCEL_LABEL_PROBE,
    )
    assert _cancel_button_label(probed) == CANCEL_LABEL_PROBE, (
        "подпись кнопки отказа НЕ приходит параметром макроса: "
        f"{_cancel_button_label(probed)!r} вместо {CANCEL_LABEL_PROBE!r} — "
        "правка гейта подменила подпись литералом"
    )


def test_the_panel_lands_the_focus_when_its_opener_left_the_document():
    """НЕСУЩЕЕ: ветвление спрашивает ПРИСУТСТВИЕ узла, а не наличие метода.

    Сегодняшняя форма (`if (back && back.focus)`) на фрагментном пути ЛОЖНА и
    ложна молча: открыватель — кнопка удаления той самой строки — уезжает
    внеполосным узлом ответа, метод фокусировки у отсоединённого узла остаётся,
    вызов не падает и НЕ ДЕЛАЕТ НИЧЕГО. Фокус остаётся на теле документа, и
    обход по Tab начинается сначала на каждом подтверждённом действии.

    ⚠️ ПРАВИЛО ОТЛИЧАЕТ «ФОКУС УШЁЛ НА ПЛОЩАДКУ» ОТ «ФОКУС НЕ ДВИГАЛСЯ», и
    отличает вердиктом с ИМЕНЕМ узла, а не булевым «метод вызван». Булево
    зеленело бы ровно на том дефекте, ради которого правило заведено.
    """
    verdict = _run_modal_lifecycle(
        _modal_xdata_expression(_modal_block()),
        "focus_after_hide",
        landing_present=True,
    )

    assert verdict["opener_has_focus_method"] is True, (
        "у подставного открывателя нет метода фокусировки — сценарий проверял "
        "бы не тот случай: весь предмет правила в том, что метод ЕСТЬ, а узла в "
        f"документе НЕТ; вердикт: {verdict}"
    )
    assert verdict["opener_connected"] is False, (
        "подставной открыватель присутствует в документе — сценарий беспредметен: "
        f"проверяется ветвь ОТСУТСТВИЯ открывателя; вердикт: {verdict}"
    )
    assert verdict["focused"] == "landing", (
        "после закрытия панели фокус НЕ приземлился на область уведомлений: "
        "ветвление возврата спрашивает наличие метода вместо присутствия узла в "
        "документе, вызов фокусировки отсоединённого узла не делает ничего, и "
        f"фокус молча остался на теле документа; вердикт: {verdict}"
    )
    assert verdict["repeat_matches"] is True, (
        f"повторное исполнение сценария дало ДРУГОЙ исход: {verdict}"
    )


def test_the_teardown_lands_the_focus_too():
    """НЕСУЩЕЕ: приземление живёт и на ВТОРОМ пути ухода узла (Landmine 1).

    Обязательство, повешенное только на `hide()`, на фрагментном пути не
    работает ВОВСЕ: событие после запроса приходит ПОСЛЕ свопа, то есть после
    того, как внеполосный узел уже снял панель вместе с её формой. Ровно на этом
    абзаце споткнулся план 09-13 — он повесил обязательство на `hide()`, не
    прочитав, что второго пути ухода узла тот не покрывает.

    Сценарий `hide()` не зовёт НИ РАЗУ: панель открывается и СНОСИТСЯ.
    """
    verdict = _run_modal_lifecycle(
        _modal_xdata_expression(_modal_block()),
        "focus_after_teardown",
        landing_present=True,
    )

    assert verdict["has_destroy"] is True, (
        "у объекта x-data панели нет пути снятия на ветви сноса узла — "
        f"приземлять фокус на фрагментном пути нечем; вердикт: {verdict}"
    )
    assert verdict["still_locked_after_teardown"] is False, (
        "снос узла оставил признак блокировки прокрутки — расширение гарнира "
        f"задело действующее свойство: {verdict}"
    )
    assert verdict["focused"] == "landing", (
        "снос узла панели фокус НЕ приземлил: обязательство висит только на "
        "`hide()`, который на фрагментном пути не вызывается вовсе, — и после "
        "подтверждённого удаления фокус остаётся на теле документа; вердикт: "
        f"{verdict}"
    )
    assert verdict["repeat_matches"] is True, (
        f"повторное исполнение сценария сноса дало ДРУГОЙ исход: {verdict}"
    )


def test_the_teardown_of_a_closed_panel_never_moves_the_focus():
    """ПРОВЕРКА СОБСТВЕННОГО СОСТОЯНИЯ: снос ЗАКРЫТОЙ соседки фокуса не трогает.

    Страж собственного состояния в ветви сноса — РАЗЛИЧИТЕЛЬ, а не украшение:
    подмена строки сносит закрытые панели ПОСТОЯННО, и без стража каждая из них
    уводила бы фокус у ОТКРЫТОЙ — включая административные подтверждения.
    Зеркало правила блокировки прокрутки
    (`test_the_teardown_of_a_closed_panel_keeps_an_open_sibling_locked`) на
    втором обязательстве той же ветви.
    """
    verdict = _run_modal_lifecycle(
        _modal_xdata_expression(_modal_block()),
        "focus_untouched_by_closed_sibling",
        landing_present=True,
    )

    assert verdict["has_destroy"] is True, (
        "у объекта x-data панели нет пути снятия на ветви сноса, поэтому "
        "утверждение о защите фокуса открытой соседки проверяло бы "
        f"отсутствующий механизм; вердикт: {verdict}"
    )
    assert verdict["still_locked_after_teardown"] is True, (
        "снос ЗАКРЫТОЙ соседки снял блокировку у ОТКРЫТОЙ — страж собственного "
        f"состояния потерян; вердикт: {verdict}"
    )
    assert verdict["focused_after"] == verdict["focused_before"], (
        "снос ЗАКРЫТОЙ соседней панели УВЁЛ фокус у открытой: приземление "
        "поставлено мимо стража собственного состояния, и каждая подмена строки "
        f"выдёргивает человека из открытого им окна; вердикт: {verdict}"
    )

    # ⚠️ ЗУБЫ ДОКАЗЫВАЮТСЯ ЗДЕСЬ ЖЕ, А НЕ ЗАЯВЛЯЮТСЯ. Утверждение выше зелено и
    # на дереве, где приземления нет ВОВСЕ, — и таким оно было ДО правки этого
    # плана. Подстановка снимает страж и обязана его покрасить: без неё правило
    # неотличимо от собственного отсутствия.
    poisoned = _run_modal_lifecycle(
        _xdata_with_unguarded_teardown(_modal_xdata_expression(_modal_block())),
        "focus_untouched_by_closed_sibling",
        landing_present=True,
    )
    assert poisoned["focused_after"] != poisoned["focused_before"], (
        "выражение, чей путь сноса стража СОБСТВЕННОГО СОСТОЯНИЯ не имеет, "
        "фокуса у открытой панели не увело — правило выше не отличает "
        f"защищённый путь снятия от незащищённого; вердикт: {poisoned}"
    )


def test_control_negative_a_panel_landing_on_a_missing_region_reddens_the_gate():
    """ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ: гарнир обязан уметь сказать «не приземлился».

    Тот же гарнир на стаб-документе БЕЗ площадки обязан сообщить, что фокус на
    площадку не приехал, — иначе оба несущих правила выше доказывают
    работоспособность гарнира, а не свойство компонента.

    ⚠️ ДВОЙНОЙ ПРЕДОХРАНИТЕЛЬ, ПО ОБРАЗЦУ `_xdata_with_dead_teardown`: контроль
    отдельно утверждает, что на документе С площадкой тот же сценарий даёт
    ДРУГОЙ вердикт. Без этого утверждения контроль был бы зелен по построению —
    например, на панели, которая фокуса не двигает никогда.
    """
    expression = _modal_xdata_expression(_modal_block())

    for scenario in ("focus_after_hide", "focus_after_teardown"):
        with_region = _run_modal_lifecycle(
            expression, scenario, landing_present=True
        )
        without_region = _run_modal_lifecycle(
            expression, scenario, landing_present=False
        )

        assert with_region["focused"] == "landing", (
            f"сценарий {scenario} не приземляет фокус и на документе С "
            f"площадкой — контроль ничего не различает: {with_region}"
        )
        assert without_region["focused"] != "landing", (
            f"гарнир сообщил «приземлился» о документе, в котором площадки НЕТ "
            f"({scenario}): он доказывает собственную работоспособность, а не "
            f"свойство компонента; вердикт: {without_region}"
        )
        assert without_region["focused"] != with_region["focused"], (
            f"вердикт сценария {scenario} не зависит от наличия площадки — "
            "правила выше зелены вакуумом"
        )


def test_the_landing_region_exists_in_the_shell_of_both_apps():
    """Площадка существует в шелле и ПРОГРАММНО ФОКУСИРУЕМА.

    Без этого правила приземление ехало бы в пустоту ровно там, где панель как
    раз и открыта: область, исчезнувшая или переехавшая, оставила бы фокус на
    теле документа МОЛЧА — вызов фокусировки не состоялся бы вовсе, а в консоли
    не появилось бы ни слова.

    ⚠️ ПРИЗНАК ФОКУСИРУЕМОСТИ ОБЯЗАН СТОЯТЬ ИМЕННО НА ВЕЖЛИВОЙ ОБЛАСТИ, А НЕ НА
    ЕЁ СОСЕДКЕ. Площадка выбирается ОДНА: вторая фокусируемая область немедленно
    поставила бы вопрос, какая из них площадка, и ответ разошёлся бы с объектом
    клиентского состояния молча.
    """
    source = _template_source(NOTICE_AREA)

    region = re.search(
        rf'<div id="{re.escape(FOCUS_LANDING_ID)}"[^>]*>', source
    )
    assert region, (
        f"области с идентификатором {FOCUS_LANDING_ID!r} в шелле нет: панель "
        "приземляет фокус в пустоту, и молча"
    )
    assert 'role="status"' in region.group(0), (
        "площадка приземления перестала быть ВЕЖЛИВОЙ областью: "
        f"{region.group(0)!r}"
    )
    assert 'tabindex="-1"' in region.group(0), (
        "область уведомлений не несёт признака программной фокусируемости: "
        "вызов фокусировки на ней не делает ничего, и фокус после "
        f"подтверждённого удаления остаётся на теле документа; {region.group(0)!r}"
    )

    alert_region = re.search(r'<div id="notice-alert"[^>]*>', source)
    assert alert_region, "настойчивая область уведомления пропала из шелла"
    assert "tabindex" not in alert_region.group(0), (
        "признак фокусируемости появился и на НАСТОЙЧИВОЙ области — площадок "
        "стало две, и какая из них площадка, не говорит ничто: "
        f"{alert_region.group(0)!r}"
    )

    for shell in APP_SHELLS:
        assert NOTICE_AREA in _template_source(shell), (
            f"шелл {shell} перестал подключать область уведомлений — площадки "
            "приземления на его страницах нет вовсе"
        )


# --- ПЛОЩАДКА ПРИЗЕМЛЕНИЯ НИКОГДА НЕ ПОЛУЧАЕТ ТЕКСТА ОТКАЗА (WR-02) ----------
#
# ⚠️ ПРАВИЛО СТЕРЕЖЁТ ЗАПИСЬ, А НЕ ЧИНИТ ПОВЕДЕНИЕ. Прежняя запись шапки
# `includes/notice_area.html` обещала, что «на отказном пути фокус приземляется
# точно на текст отказа, и там выбор окупается целиком». Обещание опровергнуто
# ТРЕМЯ измерениями, и запись сужена до измеренной; правило держит сужение,
# чтобы следующий читатель не «починил» верную сторону — тот же класс, за
# который фаза уже платила кругом верификации.
#
# ⚠️ ВАРИАНТЫ КОДОВ ЧИТАЮТСЯ ИЗ РЕЕСТРА ПРИЛОЖЕНИЯ, А НЕ ИЗ ЛИТЕРАЛА. Литерал
# «error», выписанный здесь, зеленел бы и тогда, когда вариант в реестре
# сменили: правило утверждало бы про свою же копию.

# Два кода, которые панель подтверждения СПОСОБНА выдать на пути перехода:
# отказ перезапуска воркера в админке — единственное подтверждение фазы, чей
# обработчик уводит человека с кодом исхода.
PANEL_REFUSAL_CODES = (
    app_notices.WORKER_NO_CONTAINER,
    app_notices.WORKER_RESTART_FAILED,
)

# Оба фрагментных ответа фазы. На фрагментном пути плашки на успех нет вовсе
# (D-03), поэтому площадка приземления пуста ВСЕГДА — и это ровно тот путь,
# ДЛЯ КОТОРОГО площадка и выбиралась.
FRAGMENT_RESPONSE_TEMPLATES = (
    "ads/partials/sched_delete_response.html",
    "account_groups/partials/delete_response.html",
)

ALERT_REGION_ID = "notice-alert"


def test_the_landing_region_never_receives_the_text_of_a_refusal():
    """НЕСУЩЕЕ: текст отказа физически не может оказаться в площадке.

    Три утверждения — по одному на каждое измерение суженной записи:
    вариант обоих кодов читается ИЗ РЕЕСТРА; разметка вежливой области варианта
    ошибки НЕ ПРИНИМАЕТ, а соседняя принимает ТОЛЬКО его; на фрагментном пути
    кода уведомления не несёт ни один из двух ответов фазы.

    Отказ называет КОД, его ВАРИАНТ и ОБЛАСТЬ, в которую он едет: «не совпало»
    отправило бы читателя перечитывать три файла.
    """
    # --- 1. ВАРИАНТ ОБОИХ КОДОВ — ИЗ РЕЕСТРА ---
    # АНТИВАКУУМ: перечень не пуст, и каждый код в реестре НАЙДЕН. Неизвестный
    # код реестр не выбирает вовсе (`notice_for` возвращает None), и правило
    # зеленело бы на опечатке в имени константы.
    assert PANEL_REFUSAL_CODES, (
        "перечень кодов отказа панели ПУСТ — правило зелено вакуумом и "
        "перестало отличать соблюдение от поломки"
    )
    for code in PANEL_REFUSAL_CODES:
        record = app_notices.notice_for(code)
        assert record is not None, (
            f"код {code!r} реестру НЕИЗВЕСТЕН: правило утверждает про исход, "
            "которого приложение выдать не может"
        )
        assert record.variant == "error", (
            f"код {code!r} несёт вариант {record.variant!r}, а не 'error' — он "
            f"поедет в вежливую область {FOCUS_LANDING_ID!r}, то есть В САМУ "
            "ПЛОЩАДКУ ПРИЗЕМЛЕНИЯ, и запись шапки о цене выбора снова стала "
            "шире поведения"
        )

    # --- 2. РАЗМЕТКА: ВЕЖЛИВАЯ ОБЛАСТЬ ВАРИАНТА ОШИБКИ НЕ ПРИНИМАЕТ ---
    source = _template_source(NOTICE_AREA)
    polite = re.search(
        rf'<div id="{re.escape(FOCUS_LANDING_ID)}"[^>]*>(.*?)</div>', source, re.S
    )
    assert polite, (
        f"вежливая область {FOCUS_LANDING_ID!r} не разобралась — утверждать "
        "про её содержимое нечем"
    )
    assert "notice.variant != 'error'" in polite.group(1), (
        f"площадка приземления {FOCUS_LANDING_ID!r} перестала ОТСЕИВАТЬ вариант "
        f"ошибки: текст отказа поедет прямо в неё — {polite.group(1)!r}"
    )

    alert_region = re.search(
        rf'<div id="{re.escape(ALERT_REGION_ID)}"[^>]*>(.*?)</div>', source, re.S
    )
    assert alert_region, (
        f"настойчивая область {ALERT_REGION_ID!r} не разобралась — второй "
        "половине утверждения не на чём стоять"
    )
    assert "notice.variant == 'error'" in alert_region.group(1), (
        f"настойчивая область {ALERT_REGION_ID!r} перестала принимать ТОЛЬКО "
        f"вариант ошибки: {alert_region.group(1)!r}"
    )

    # --- 3. ФРАГМЕНТНЫЙ ПУТЬ: ПЛОЩАДКА ПУСТА ВСЕГДА (D-03) ---
    assert FRAGMENT_RESPONSE_TEMPLATES, (
        "перечень фрагментных ответов ПУСТ — третье измерение записи вакуумно"
    )
    with_notice = [
        rel for rel in FRAGMENT_RESPONSE_TEMPLATES if "notice" in _template_source(rel)
    ]
    assert not with_notice, (
        "фрагментный ответ понёс код уведомления: площадка приземления "
        f"перестала быть пустой ВСЕГДА, и запись о цене выбора устарела — "
        f"{with_notice}"
    )


def test_the_focus_landing_is_declared_once_and_called_twice():
    """Площадка объявлена в объекте ОДИН раз и зовётся из ОБЕИХ ветвей.

    Два независимо выписанных приземления разошлись бы молча, и половина из 18
    мест приземлялась бы в одно место, половина — в другое. Правило читает
    ОТРЕНДЕРЕННОЕ выражение, а не шаблон: предмет — то, что доезжает до
    браузера.
    """
    expression = _modal_xdata_expression(_modal_block())

    literal = f"'{FOCUS_LANDING_ID}'"
    assert expression.count(literal) == 1, (
        f"идентификатор площадки {literal} встречается в выражении клиентского "
        f"состояния {expression.count(literal)} раз(а), а не один: приземление "
        "выписано независимо в двух ветвях, и разойтись они могут молча — "
        f"выражение: {expression!r}"
    )
    assert "isConnected" in expression, (
        "ветвление возврата фокуса не спрашивает присутствия открывателя в "
        f"документе: {expression!r}"
    )


# --- СНЯТИЕ ЗАГОТОВОК ПЛАШКИ ОТКАЗА ПРИ ОТКРЫТИИ ПАНЕЛИ (план 10-41, CR-01) --
#
# ⚠️ ЗАЧЕМ ЭТА ГРУППА ЗАВЕДЕНА ЗДЕСЬ, А НЕ ДОПИСАНА К ПОДСТРОЧНОЙ В МОДУЛЕ
# ШЕЛЛА. Предмет группы — КОНЪЮНКЦИЯ «признак скрытости поставлен ИМЕННО ЭТОЙ
# заготовке». Подстрокой она невыразима ПО ПОСТРОЕНИЮ: связь «идентификатор →
# цель глагола» проходит в рычаге через перебор массива, то есть она есть связь
# ИСПОЛНЕНИЯ, а не соседства литералов. Разборщика JS в дереве нет и заводить
# его нельзя, зато живой канал исполнения (`MODAL_LIFECYCLE_HARNESS`) в этом
# модуле уже стои́т — и группа встаёт к нему, а не к подстроке.
#
# ⚠️ ПОДСТРОЧНОЕ ПРАВИЛО В МОДУЛЕ ШЕЛЛА НЕ УДАЛЕНО И УДАЛЯТЬСЯ НЕ ДОЛЖНО. Оно
# осталось АНТИВАКУУМНЫМ слоем: объявление метода есть, тело непусто, глагол в
# теле присутствует, проза не считается. Конъюнкции оно НЕ утверждает — и прямо
# называет это правило своим адресом.


def _failure_banner_names() -> tuple[tuple[str, ...], str]:
    """Перечень заготовок и имя признака скрытости — ВВОЗОМ, а не второй копией.

    ⚠️ ВЫПИСАННАЯ КОПИЯ РАЗОШЛАСЬ БЫ С ПЕРЕЧНЕМ МОЛЧА при первой же третьей
    заготовке: правила ниже проверяли бы две из трёх и остались бы зелёными.
    Владелец обеих величин — `tests/test_pages/test_shell.py`, там они замерены
    по включаемому файлу заготовок, и второго их экземпляра здесь не заводится.

    ⚠️ ВВОЗ ВНУТРИ ФУНКЦИИ, А НЕ НА УРОВНЕ МОДУЛЯ, И ПРИЧИНА ЗАМЕРЕНА. В
    `test_shell.py` на уровне модуля стои́т утверждение, срабатывание которого
    роняет СБОР файла целиком; модульный ввоз перенёс бы этот отказ и на
    настоящий файл — то есть расхождение в ЧУЖОМ модуле гасило бы 88 правил
    здесь. Находка `REVIEW-8/IN-01` предметом плана 10-41 не является, её
    владелец — план 10-45. Форма ввоза — живая идиома проекта
    (`_auth_shell_template_source` в том же `test_shell.py` ввозит
    `_template_source` ровно так).
    """
    from tests.test_pages.test_shell import (
        FAILURE_BANNER_HIDDEN_ATTR,
        FAILURE_BANNER_IDS,
    )

    return FAILURE_BANNER_IDS, FAILURE_BANNER_HIDDEN_ATTR


def _banner_clearing_verdict(expression: str) -> dict:
    """Вердикт ИСПОЛНЕНИЯ метода открытия по каждой заготовке и по площадке.

    Поля вердикта: ``cleared`` — карта «идентификатор заготовки → несёт ли ОНА
    признак скрытости ПОСЛЕ вызова метода открытия»; ``landing_hidden`` — то же
    у площадки приземления фокуса; ``registered`` — какие узлы заготовок гарнир
    завёл на самом деле; ``raised`` — поднялся ли признак блокировки прокрутки,
    то есть отработал ли метод открытия вообще.
    """
    banner_ids, _hidden_attr = _failure_banner_names()
    return _run_modal_lifecycle(expression, "banner_clearing", banner_ids=banner_ids)


# Разрешение узла по ПЕРЕМЕННОЙ, а не по строковому литералу. Ровно это и есть
# связь исполнения: аргумент разрешения — имя перебираемой величины, и подстрока
# о ней ничего сказать не может.
_CLEARING_LOOKUP_RE = re.compile(r"getElementById\(\s*([A-Za-z_$][\w$]*)\s*\)")


def _clearing_chunk(expression: str) -> str:
    """ДОСЛОВНАЯ строка выражения, снимающая заготовки. Якорь всех доктóриваний.

    Выводится ИЗ выражения, а не выписывается литералом, — по той же причине и
    той же формой, что `_lever_clearing_chunk` (tests/test_pages/test_shell.py):
    выписанный кусок разошёлся бы с рычагом при первой же его правке молча и с
    зелёным контролем, что хуже красного.
    """
    banner_ids, hidden_attr = _failure_banner_names()
    verb = f"setAttribute('{hidden_attr}'"
    hits = [
        line for line in expression.splitlines(keepends=True)
        if verb in line and all(banner_id in line for banner_id in banner_ids)
    ]
    assert len(hits) == 1, (
        f"строк выражения, снимающих ОБЕ заготовки, {len(hits)}, а не одна — "
        "доктóрить нечего либо подмена задела бы не то место"
    )
    return hits[0]


def _banner_id_array(banner_ids: tuple[str, ...]) -> str:
    """Перечень идентификаторов ровно той формой, какой его несёт рычаг."""
    return "[" + ", ".join(f"'{banner_id}'" for banner_id in banner_ids) + "]"


def _xdata_with_clearing_dropped(expression: str) -> str:
    """ФОРМА (A): снятие ВЫРЕЗАНО целиком — дословный возврат к дереву до правки.

    ⚠️ ДВОЙНОЙ ПРЕДОХРАНИТЕЛЬ ПОДСТАНОВКИ НАСЛЕДУЕТСЯ У `_xdata_with_dead_teardown`
    и по той же причине: подстановка обязана доказать, что она что-то изменила, и
    что изменила ИМЕННО ТО.
    """
    chunk = _clearing_chunk(expression)
    assert expression.count(chunk) == 1, (
        "строка снятия встречается в выражении не один раз — вырезание задело "
        "бы не то место"
    )
    dropped = expression.replace(chunk, "")
    assert dropped != expression, "вырезание не сработало — якорь замены не найден"
    assert chunk not in dropped, (
        "строка снятия осталась в доктóренном выражении — форма (A) не "
        "воспроизведена"
    )
    return dropped


def _xdata_with_clearing_retargeted(expression: str) -> str:
    """ФОРМА (B): обе заготовки НАЗВАНЫ, а глагол применён к площадке приземления.

    ⚠️ ЭТО РАЗЛИЧАЮЩАЯ МУТАЦИЯ ПАРТИИ. Перечень идентификаторов остаётся в теле
    метода дословно, глагол постановки признака остаётся в теле дословно — и
    ровно поэтому подстрочная форма правила даёт на ней НОЛЬ находок. Меняется
    ОДНО: аргумент разрешения узла перестаёт быть перебираемой величиной и
    становится идентификатором площадки приземления.
    """
    banner_ids, _hidden_attr = _failure_banner_names()
    chunk = _clearing_chunk(expression)
    lookups = _CLEARING_LOOKUP_RE.findall(chunk)
    assert len(lookups) == 1, (
        f"разрешений узла ПО ПЕРЕМЕННОЙ в строке снятия {len(lookups)}, а не "
        "одно — перенацеливание задело бы не то место либо рычаг перестал "
        "разрешать узел через перебор, и вся эта группа стережёт не то"
    )
    retargeted_chunk = _CLEARING_LOOKUP_RE.sub(
        f"getElementById('{FOCUS_LANDING_ID}')", chunk, count=1
    )
    assert retargeted_chunk != chunk, "перенацеливание не сработало"
    assert expression.count(chunk) == 1, (
        "строка снятия встречается в выражении не один раз — подмена задела бы "
        "не то место"
    )
    retargeted = expression.replace(chunk, retargeted_chunk)
    for banner_id in banner_ids:
        assert banner_id in retargeted, (
            f"после перенацеливания заготовки #{banner_id} в выражении нет — "
            "контроль доказывал бы удаление, а не форму (B)"
        )
    return retargeted


def _xdata_with_one_banner_cleared(expression: str) -> str:
    """ФОРМА (C): снимается ОДНА заготовка, вторая лишь названа литералом.

    Второй идентификатор переносится в строковый литерал, в переборе НЕ
    участвующий: в теле метода он присутствует, снятия не получает. Подстрочная
    форма правила даёт на ней ОДНУ находку и потому её видит; здесь она нужна
    ради ДРУГОГО — арифметика расхождений обязана считаться НА ЗАГОТОВКУ и
    называть ИМЕННО оставшуюся.
    """
    banner_ids, _hidden_attr = _failure_banner_names()
    assert len(banner_ids) >= 2, (
        f"заготовок объявлено {len(banner_ids)} — форма (C) «снята одна из "
        "двух» на таком перечне невыразима, и контроль доказывал бы не то"
    )
    kept, *left_behind = banner_ids
    chunk = _clearing_chunk(expression)
    full_array = _banner_id_array(banner_ids)
    assert chunk.count(full_array) == 1, (
        f"перечня идентификаторов `{full_array}` в строке снятия "
        f"{chunk.count(full_array)} вхождений, а не одно — подмена задела бы "
        "не то место"
    )
    indent = chunk[: len(chunk) - len(chunk.lstrip())]
    stale = (
        indent
        + "var staleBannerIds = "
        + _banner_id_array(tuple(left_behind))
        + ";\n"
    )
    partial_chunk = chunk.replace(full_array, _banner_id_array((kept,))) + stale
    partial = expression.replace(chunk, partial_chunk)
    assert partial != expression, "подстановка ничего не изменила"
    for banner_id in banner_ids:
        assert banner_id in partial, (
            f"после подстановки заготовки #{banner_id} в выражении нет — "
            "контроль доказывал бы удаление, а не форму (C)"
        )
    return partial


def _xdata_with_clearing_in_a_line_comment(expression: str) -> str:
    """ФОРМА (D): снятие спрятано в СТРОЧНЫЙ комментарий JS внутри выражения.

    ⚠️ ЭТУ ФОРМУ ПОДСТРОЧНАЯ АНТИПРОЗАИЧЕСКАЯ ПОЛОВИНА ПРОПУСКАЛА (`REVIEW-8/WR-03`):
    вырезались блочный комментарий JS и комментарий Jinja, а строчный — нет.
    Здесь она непроходима ПО ПОСТРОЕНИЮ: комментарий не исполняется, и зазеленеть
    правилу на нём нечем — вырезать его не требуется вовсе.
    """
    banner_ids, hidden_attr = _failure_banner_names()
    chunk = _clearing_chunk(expression)
    indent = chunk[: len(chunk) - len(chunk.lstrip())]
    commented_chunk = indent + "// " + chunk.strip() + "\n"
    assert "\n" not in chunk.strip(), (
        "строка снятия многострочна — предваривший её строчный комментарий "
        "погасил бы только первую строку, и форма (D) не воспроизвелась бы"
    )
    commented = expression.replace(chunk, commented_chunk)
    assert commented != expression, "закомментирование не сработало"
    verb = f"setAttribute('{hidden_attr}'"
    assert verb in commented, (
        "глагол снятия пропал из доктóренного выражения — контроль доказывал бы "
        "его удаление, а не безвредность комментария"
    )
    for banner_id in banner_ids:
        assert banner_id in commented, (
            f"заготовки #{banner_id} нет в доктóренном выражении — контроль "
            "доказывал бы удаление, а не форму (D)"
        )
    return commented


def test_the_lever_clears_both_failure_banners_by_execution():
    """Рычаг ставит признак скрытости КАЖДОЙ заготовке — утверждено ИСПОЛНЕНИЕМ.

    ⚠️ ЧЕМ ЭТО ПРАВИЛО ОТЛИЧАЕТСЯ ОТ ПОДСТРОЧНОГО, И ОТЛИЧИЕ ЕСТЬ ВЕСЬ СМЫСЛ ЕГО
    СУЩЕСТВОВАНИЯ. Подстрочное (`_lever_clearing_findings`,
    tests/test_pages/test_shell.py) ведёт по телу метода ДВА НЕЗАВИСИМЫХ поиска:
    «заготовка названа» и «глагол присутствует». Конъюнкцию «глагол применён К
    ЭТОЙ заготовке» такая форма не выражает, и тело, где обе заготовки лишь
    названы, а признак поставлен площадке приземления, проходит её ЗЕЛЁНЫМ (ноль
    находок — замер восьмого круга ревизии, `CR-01`). Здесь метод открытия
    ИСПОЛНЯЕТСЯ, и вердикт спрашивается У КАЖДОГО УЗЛА отдельно.

    ⚠️ АНТИВАКУУМНАЯ ПОЛОВИНА ИДЁТ ПЕРВОЙ и утверждает ЧЕТЫРЕ вещи, потому что
    вакуум здесь возможен четырьмя способами: пустой перечень заготовок, пустое
    выражение, незаведённые узлы (разрешение отдало бы пустоту, и «не снято»
    стало бы неотличимо от «нечего снимать») и неотработавший метод открытия.

    ⚠️ ЧТО ИМЕННО СТЕРЕЖЁТСЯ. Не отрисовка браузером — ИСПОЛНЕНИЕ метода
    открытия в интерпретаторе JS. Отрисовка остаётся шагу 4.4 ручного обхода
    `10-UAT.md`, и объявлять его пройденным по зелени этого правила НЕЛЬЗЯ.
    """
    banner_ids, hidden_attr = _failure_banner_names()
    assert banner_ids, (
        "перечень заготовок плашки пуст — правило ниже прошло бы по нулю "
        "элементов и объявило зелёным отсутствие проверки"
    )

    expression = _modal_xdata_expression(_modal_block())
    assert expression.strip(), (
        "выражение x-data рычага пусто — исполнять нечего, и правило зеленело "
        "бы вакуумом"
    )

    verdict = _banner_clearing_verdict(expression)

    assert set(verdict["registered"]) == set(banner_ids), (
        "ГАРНИР ЗАВЁЛ НЕ ТЕ УЗЛЫ ЗАГОТОВОК: объявлено "
        f"{sorted(banner_ids)}, заведено {sorted(verdict['registered'])} — "
        "разрешение идентификатора отдало бы пустоту, и «заготовка не снята» "
        "было бы неотличимо от «снимать было нечего»"
    )
    assert verdict["raised"] is True, (
        "после вызова метода открытия признака блокировки прокрутки на "
        "документе нет — метод не отработал вовсе, и утверждения о снятии "
        f"заготовок доказывали бы ровно ничего; вердикт: {verdict}"
    )

    findings: list[str] = []
    for banner_id in banner_ids:
        if verdict["cleared"].get(banner_id) is not True:
            findings.append(
                f"#{banner_id}: ПОСЛЕ вызова метода открытия признака "
                f"`{hidden_attr}` у этой заготовки НЕТ — отказ, случившийся ДО "
                "открытия панели, поднимается над кнопкой необратимого удаления "
                "и утверждает о ТЕКУЩЕМ действии неправду (CR-01)"
            )
    if verdict["landing_hidden"] is not False:
        findings.append(
            f"#{FOCUS_LANDING_ID}: признак `{hidden_attr}` получила ПЛОЩАДКА "
            "ПРИЗЕМЛЕНИЯ ФОКУСА — глагол применён НЕ ТОЙ ЦЕЛИ. Это форма (B) "
            "матрицы мутаций девятого круга: перечень заготовок в теле метода "
            "назван, глагол в теле присутствует, и подстрочная форма правила "
            "даёт на таком теле НОЛЬ находок. Заодно площадка приземления "
            "получает скрытость и перестаёт принимать фокус"
        )

    assert not findings, (
        "components/modal.html: ИСПОЛНЕНИЕ метода открытия НЕ снимает заготовки "
        "плашки отказа так, как объявлено:\n"
        + "\n".join(f"  — {line}" for line in findings)
        + f"\nвердикт: {verdict}"
    )


def test_control_a_lever_that_targets_the_wrong_node_reddens():
    """ЧТО ДОКАЗЫВАЕТ: форма (B) матрицы мутаций КРАСНИТ правило исполнением.

    ⚠️ ЭТО РАЗЛИЧАЮЩИЙ СЛУЧАЙ ПАРТИИ, И РАЗНИЦА НАЗЫВАЕТСЯ ЧИСЛОМ, А НЕ
    ОПИСАНИЕМ. Доктóренное выражение НАЗЫВАЕТ обе заготовки в перечне
    идентификаторов, а признак скрытости ставит площадке приземления фокуса.
    Подстрочная форма правила (`_lever_clearing_findings`,
    tests/test_pages/test_shell.py) на этой самой мутации даёт НОЛЬ находок и
    ПРОХОДИТ ЗЕЛЁНОЙ — замер восьмого круга ревизии, находка `CR-01`, и гэп
    `V9-01` девятого круга верификации. Правило, исполняющее метод открытия,
    краснеет на ней ОТДЕЛЬНЫМ отказом о площадке приземления.

    ⚠️ ПОЛОЖИТЕЛЬНАЯ ПОЛОВИНА ИДЁТ ПЕРВОЙ: непрáвленое выражение даёт исправный
    вердикт. Без неё контроль был бы совместим с правилом, находящим
    расхождение всегда.
    """
    expression = _modal_xdata_expression(_modal_block())
    banner_ids, _hidden_attr = _failure_banner_names()

    healthy = _banner_clearing_verdict(expression)
    assert all(healthy["cleared"][banner_id] for banner_id in banner_ids), (
        "на НЕПРÁВЛЕНОМ выражении снятие уже не сходится — доктóривание ниже "
        f"доказывало бы красноту того, что и так красно; вердикт: {healthy}"
    )
    assert healthy["landing_hidden"] is False, (
        "непрáвленый рычаг ставит признак скрытости площадке приземления — "
        f"контроль ниже не отличил бы мутацию от боевого дерева: {healthy}"
    )

    verdict = _banner_clearing_verdict(_xdata_with_clearing_retargeted(expression))

    for banner_id in banner_ids:
        assert verdict["cleared"][banner_id] is False, (
            f"ПРАВИЛО ЗАЗЕЛЕНЕЛО НА ФОРМЕ (B): заготовка #{banner_id} объявлена "
            "снятой, хотя глагол применён к площадке приземления, а не к ней — "
            f"конъюнкция снова не выражена; вердикт: {verdict}"
        )
    assert verdict["landing_hidden"] is True, (
        "доктóривание НЕ ПЕРЕНАЦЕЛИЛО глагол: площадка приземления признака "
        "скрытости не получила, и форма (B) не воспроизведена — контроль "
        f"доказывал бы форму (A); вердикт: {verdict}"
    )


def test_control_a_lever_whose_clearing_is_dropped_or_partial_reddens():
    """ЧТО ДОКАЗЫВАЕТ: формы (A) и (C) матрицы мутаций КРАСНЯТ правило.

    ⚠️ ДВЕ ФОРМЫ ЖИВУТ В ОДНОМ КОНТРОЛЕ ДВУМЯ ПОЛОВИНАМИ, И ВТОРАЯ НЕ ИЗБЫТОЧНА.
    Первая (A) доказывает, что ВЫРЕЗАННОЕ снятие видно вовсе. Вторая (C)
    доказывает ДРУГОЕ: расхождение считается НА ЗАГОТОВКУ, и отказ называет
    ИМЕННО ту, что осталась, — правило, объявляющее «не снято» разом для обеих,
    прошло бы первую половину и провалило бы вторую.

    ⚠️ ПОЛОЖИТЕЛЬНАЯ ПОЛОВИНА ИДЁТ ПЕРВОЙ: непрáвленое выражение даёт исправный
    вердикт. Без неё контроль был бы совместим с правилом, находящим
    расхождение всегда.
    """
    expression = _modal_xdata_expression(_modal_block())
    banner_ids, _hidden_attr = _failure_banner_names()

    healthy = _banner_clearing_verdict(expression)
    assert all(healthy["cleared"][banner_id] for banner_id in banner_ids), (
        "на НЕПРÁВЛЕНОМ выражении снятие уже не сходится — доктóривания ниже "
        f"доказывали бы красноту того, что и так красно; вердикт: {healthy}"
    )

    # (A) СНЯТИЕ ВЫРЕЗАНО — дословный возврат к дереву до правки рычага.
    dropped = _banner_clearing_verdict(_xdata_with_clearing_dropped(expression))
    for banner_id in banner_ids:
        assert dropped["cleared"][banner_id] is False, (
            "ПРАВИЛО НЕ ЗАМЕТИЛО ВЫРЕЗАННОЕ СНЯТИЕ: заготовка "
            f"#{banner_id} объявлена снятой на выражении, где снятия нет "
            f"вовсе; вердикт: {dropped}"
        )
    assert dropped["landing_hidden"] is False, (
        "на выражении с ВЫРЕЗАННЫМ снятием площадка приземления получила "
        "признак скрытости — вырезание задело не то место, и форма (A) не "
        f"воспроизведена; вердикт: {dropped}"
    )

    # (C) СНИМАЕТСЯ ОДНА ЗАГОТОВКА, ВТОРАЯ ТОЛЬКО НАЗВАНА ЛИТЕРАЛОМ.
    kept, *left_behind = banner_ids
    partial = _banner_clearing_verdict(_xdata_with_one_banner_cleared(expression))
    assert partial["cleared"][kept] is True, (
        f"заготовка #{kept} осталась в переборе, но снятой не объявлена — "
        "доктóривание формы (C) задело не то место, и контроль сличал бы не "
        f"ту мутацию; вердикт: {partial}"
    )
    for banner_id in left_behind:
        assert partial["cleared"][banner_id] is False, (
            "ПРАВИЛО ЗАЗЕЛЕНЕЛО НА ЗАГОТОВКЕ, ВЫНЕСЕННОЙ ИЗ ПЕРЕБОРА: "
            f"#{banner_id} названа в теле метода строковым литералом и признака "
            "скрытости не получает, а вердикт объявляет её снятой — расхождение "
            f"считается не НА ЗАГОТОВКУ; вердикт: {partial}"
        )
    assert sum(1 for v in partial["cleared"].values() if v is True) == 1, (
        "снятой оказалась не РОВНО одна заготовка — форма (C) не "
        f"воспроизведена; вердикт: {partial}"
    )


def test_control_a_lever_that_clears_only_in_a_line_comment_reddens():
    """ЧТО ДОКАЗЫВАЕТ: форма (D) — снятие в СТРОЧНОМ комментарии JS — краснит.

    ⚠️ ИМЕННО ЭТА ФОРМА ПРОХОДИТ ЗЕЛЁНОЙ У АНТИПРОЗАИЧЕСКОЙ ПОЛОВИНЫ
    ПОДСТРОЧНОГО ПРАВИЛА, И ЭТО ЗАМЕР, А НЕ ОПАСЕНИЕ. Разбор тела метода в
    модуле шелла вырезал блочный комментарий JS и комментарий Jinja, а СТРОЧНЫЙ
    (`// …`) — нет; тело же метода живёт в МНОГОСТРОЧНОМ значении атрибута
    `x-data`, где `//` есть законный комментарий. Копия рычага, где снятие
    вырезано, а вместо него дописана одна строка комментария, называющая обе
    заготовки и глагол, давала подстрочному правилу НОЛЬ находок
    (`REVIEW-8/WR-03`). Половину эту чинит план 10-41 задачей 2; здесь форма (D)
    непроходима ПО ПОСТРОЕНИЮ — комментарий не исполняется, и зазеленеть на нём
    нечем, вырезать его не требуется вовсе.

    ⚠️ ПОЛОЖИТЕЛЬНАЯ ПОЛОВИНА ИДЁТ ПЕРВОЙ.
    """
    expression = _modal_xdata_expression(_modal_block())
    banner_ids, hidden_attr = _failure_banner_names()

    healthy = _banner_clearing_verdict(expression)
    assert all(healthy["cleared"][banner_id] for banner_id in banner_ids), (
        "на НЕПРÁВЛЕНОМ выражении снятие уже не сходится — доктóривание ниже "
        f"доказывало бы красноту того, что и так красно; вердикт: {healthy}"
    )

    commented_expression = _xdata_with_clearing_in_a_line_comment(expression)
    verdict = _banner_clearing_verdict(commented_expression)

    for banner_id in banner_ids:
        assert verdict["cleared"][banner_id] is False, (
            "ПРАВИЛО ЗАЗЕЛЕНЕЛО НА СНЯТИИ, СПРЯТАННОМ В СТРОЧНЫЙ КОММЕНТАРИЙ: "
            f"заготовка #{banner_id} объявлена снятой, хотя строка снятия не "
            f"исполняется вовсе; вердикт: {verdict}"
        )
    assert verdict["landing_hidden"] is False, (
        "на закомментированном снятии площадка приземления получила признак "
        f"скрытости — закомментировано не то место; вердикт: {verdict}"
    )
    assert f"setAttribute('{hidden_attr}'" in commented_expression, (
        "ГЛАГОЛ ПРОПАЛ ИЗ ДОКТÓРЕННОГО ВЫРАЖЕНИЯ — контроль доказывал бы его "
        "удаление, а не безвредность строчного комментария, и разница между "
        "двумя формами правила больше не показана"
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


# =============================================================================
# КРИТЕРИЙ 3 ВЕХИ — ЧЕТЫРЬМЯ ЧИСЛАМИ, А НЕ ЗАЯВЛЕНИЕМ (D-13)
#
# Критерий 3 Фазы 10 гласит: «новых строк JS фаза не добавляет (машинно: диффом
# по `app/static/js/` и шаблонам)». Прочтение владельца (D-13) — критерий
# запрещает НОВЫЕ СУЩНОСТИ, а не правку существующих, — записано в шапке
# `app/templates/components/modal.html` рядом с правкой, которую оно объясняет,
# и повторяется в докстринге правила ниже. Здесь оно ПЕРЕВЕДЕНО В ЧИСЛА:
# заявление «мы ничего не добавили» проверяется чтением диффа глазами, а четыре
# числа проверяются прогоном.
#
# ⚠️ ТРИ ИЗ ЧЕТЫРЁХ ЧИСЕЛ ЧИТАЮТСЯ ИМПОРТОМ ИЗ ОБЪЯВЛЯЮЩИХ ИХ МОДУЛЕЙ, И
# ВТОРОГО ЭКЗЕМПЛЯРА НИ ОДНОГО ИЗ НИХ ЗДЕСЬ НЕ ЗАВОДИТСЯ. Вторая копия числа
# разошлась бы с первой МОЛЧА: правило проверяло бы устаревшее значение при
# зелёном соседе, и обнаружилось бы это в тот единственный день, когда число
# действительно двинулось. Доктрина единственного источника в этом дереве уже
# записана (образец импорта помощника между тестовыми модулями —
# `tests/test_pages/test_htmx_response_layer.py`), и здесь она применяется к
# ЧИСЛАМ, а не к помощникам.
#
# Четвёртое число — набор файлов каталога сценариев — не объявлено нигде, и
# только оно заводится ЗДЕСЬ ВПЕРВЫЕ.
# =============================================================================

# Каталог вендоренных сценариев. Выведен из УЖЕ ОБЪЯВЛЕННОГО корня шаблонов, а
# не из второго вычисления корня проекта: два вычисления одного корня — та же
# вторая копия, только адресом вместо числа.
STATIC_JS_DIR = TEMPLATES_DIR.parent / "static" / "js"

# Набор вендоренных файлов сценариев — ИМЕНАМИ, а не числом, и выбор этот
# несущий. Файл, ПЕРЕИМЕНОВАННЫЙ НА МЕСТЕ (подмена рантайма другой сборкой под
# новым именем), при счёте числом прошёл бы молча: число осталось бы двойкой.
# Именами такая подмена краснеет.
#
# Оба файла названы по НАЗНАЧЕНИЮ, а не только по имени:
#   * `htmx.min.js` — рантайм РАЗМЕТКИ: он читает атрибуты `hx-*`, шлёт запрос и
#     применяет внеполосные узлы ответа. Это тот самый слой письма, ради
#     которого веха и затеяна.
#   * `alpine.min.js` — рантайм КЛИЕНТСКОГО СОСТОЯНИЯ: он исполняет `x-data`,
#     `x-init` и выражения атрибутов панели подтверждения (открытие, закрытие,
#     блокировка прокрутки, приземление фокуса).
#
# Оба вендорены, то есть лежат в дереве файлами, а не приезжают сборщиком: у
# проекта нет ни build-шага, ни менеджера пакетов на стороне разметки, и
# «новая строка JS» здесь означает буквально новый файл в этом каталоге.
VENDORED_JS_FILES = frozenset({"alpine.min.js", "htmx.min.js"})


def _vendored_js_files(directory: Path | None = None) -> set[str]:
    """Имена файлов сценариев каталога — ОБХОДОМ, а не перечнем.

    Каталог принимается параметром по той же причине, по которой его принимает
    обход шаблонов в гейтах разметки: группа контроля обязана подать ИЗМЕНЁННУЮ
    копию каталога, и разборщик, зашитый на единственный путь, сделал бы
    отрицательный контроль невыразимым.

    Обход РЕКУРСИВНЫЙ: файл, положенный будущей фазой в подкаталог, обязан
    попасть в охват сам, а не ждать, пока кто-то вспомнит про его каталог.
    """
    root = STATIC_JS_DIR if directory is None else directory
    if not root.exists():
        return set()
    return {path.name for path in root.rglob("*.js")}


# --- ПЯТОЕ ЧИСЛО КРИТЕРИЯ 3: РЕГИСТРАЦИИ В ТЕЛАХ БЛОКОВ `<script>` -----------
#
# ⚠️ ЗАЧЕМ ЗАВЕДЕНО, И ЭТО НЕ РАСШИРЕНИЕ ВПРОК. Четыре утверждения гейта ниже
# меряют имена файлов каталога вендоренных сценариев, встроенные обработчики
# отправки, атрибуты событий рантайма разметки и число узлов клиентского
# состояния. ТЕЛО блока `<script>` внутри шаблона не измеряется НИ ОДНИМ из
# четырёх — и ровно туда коммит `4e24d61` (план 10-49) внёс семь исполняемых
# строк JS, целиком новую регистрацию ТРЕТЬЕГО обработчика в
# `app/templates/includes/htmx_error_banner.html:227-233`. Гейт остался зелён,
# и ОДИННАДЦАТЫЙ круг верификации назвал это блокером дословно: «следующая
# такая правка снова пройдёт молча, и заметит её опять не прогон, а круг
# верификации».
#
# ⚠️ ЧЕГО ЭТО ЧИСЛО НЕ РЕШАЕТ. Оно объявляет ЧИСЛО СЕГОДНЯШНЕГО ДЕРЕВА и ловит
# НЕЗАЯВЛЕННОЕ. Какое ОСНОВАНИЕ стои́т за числом три у заготовок, здесь НЕ
# выводится и не предполагается — оно ВНЕСЕНО решением владельца и живёт
# ПОЛЕМ: ветвь `extend-override`, принял `chubav`, 2026-09-12, запись
# `overrides[1]` шапки
# `.planning/phases/10-rychag-components-modal-html/10-VERIFICATION.md` (план
# 10-53, останов `gate="blocking-human"`). Полный абзац основания — в
# докстринге правила ниже.

SCRIPT_OPEN_TAG = re.compile(r"<script\b[^>]*>", re.IGNORECASE)
SCRIPT_CLOSE_TAG = re.compile(r"</script\s*>", re.IGNORECASE)


def _script_bodies(source: str) -> list[str]:
    """Содержимое КАЖДОГО блока ``<script>`` шаблона и ничего кроме него.

    ⚠️ РАЗБИРАЕТСЯ ТЕЛО, А НЕ ФАЙЛ, И ЭТО НЕСУЩЕЕ РЕШЕНИЕ. Вызов регистрации,
    набранный в прозе вокруг блока — в комментарии-обосновании, в тексте
    документации, в примере подключения, — рантаймом не исполняется и предметом
    критерия 3 не является. Правило, считающее вхождения по ФАЙЛУ, краснело бы
    на правку документации и, что хуже, позволяло бы комментарию ЗАМЕНИТЬ собой
    ушедшую регистрацию, оставив число верным. Тем же основанием заведён
    `_strip_comments` модуля инвентаря разметки, и цена там уже уплачена
    (`REVEALED_LITERAL_OCCURRENCES` знала наизусть текст одного комментария).

    ОТКРЫВАЮЩИЙ ТЕГ С АТРИБУТАМИ ПРИНИМАЕТСЯ. Шелл подключает вендоренный
    рантайм тегом с адресом (`<script defer src="…">`), и разборщик, знающий
    только пустой тег, потерял бы будущий блок МОЛЧА: тело такого тега сегодня
    пусто, но завтра там может встать код.

    НЕЗАКРЫТЫЙ БЛОК ЕСТЬ ОТКАЗ РАЗБОРЩИКА, А НЕ ПУСТОЙ РЕЗУЛЬТАТ. Молчаливый
    пропуск здесь и есть предмет гэпа, ради которого правило заводится: разбор,
    вернувший на сломанном входе пустоту, сошёлся бы с объявлением ровно в тот
    день, когда объявление тоже опустошат.
    """
    bodies: list[str] = []
    position = 0
    while True:
        opened = SCRIPT_OPEN_TAG.search(source, position)
        if opened is None:
            return bodies
        closed = SCRIPT_CLOSE_TAG.search(source, opened.end())
        if closed is None:
            raise ValueError(
                "НЕЗАКРЫТЫЙ БЛОК `<script>`: открывающий тег найден на смещении "
                f"{opened.start()}, закрывающего нет. Разбор оборван ОТКАЗОМ, а "
                "не пустым результатом — пустой результат сошёлся бы с "
                "объявлением и спрятал бы поломку разборщика"
            )
        bodies.append(source[opened.end() : closed.start()])
        position = closed.end()


def _strip_js_comments(source: str) -> str:
    """Текст сценария без комментариев — строчных и блочных.

    ⚠️ ЭТО НЕ ГИГИЕНА РАЗБОРА, А ВТОРАЯ ПОЛОВИНА ТОГО ЖЕ РЕШЕНИЯ. Ввозимый
    `_strip_comments` вырезает Jinja- и HTML-комментарии, но ВНУТРИ блока
    `<script>` шаблона `ads/form.html` лежат три десятка строк строчных
    комментариев-обоснований — то есть ровно тот класс, на котором проект уже
    заплатил дважды. Гейт, считающий прозу, краснеет на правку документации и
    позволяет комментарию ЗАМЕНИТЬ собой пропавшее место, оставив число верным.

    ПОРЯДОК ВЫРЕЗАНИЯ НАЗВАН И ЗНАЧИМ: сначала Jinja и HTML — ввозимым
    помощником, ПОТОМ сценарные — здесь. HTML-комментарий, лежащий внутри блока
    сценария, до рантайма не доходит, а Jinja исполняется раньше обоих.

    РАЗБОР СТРОКОЗНАЮЩИЙ, И ЭТО ИЗМЕРЕНО ПРЕДМЕТОМ: в телах блоков дерева лежат
    адреса (`fetch('/accounts/connect/tg_user/start-qr', …)`), и вырезание по
    наивному `//.*$` снесло бы хвост такой строки вместе с тем, что стоит за
    ней. Кавычки всех трёх видов и экранирование обратной косой учитываются.

    ⚠️ ГРАНИЦА РАЗБОРЩИКА НАЗВАНА ПРЯМО, А НЕ ОСТАВЛЕНА ЧИТАТЕЛЮ: литерал
    регулярного выражения (`/…/g`) распознаётся НЕ КАК ЛИТЕРАЛ — косая внутри
    него читается началом комментария. В дереве на 2026-09-12 таких литералов в
    телах блоков НОЛЬ (замер прогоном), и день, когда первый появится, обязан
    начаться с правки этой функции, а не с правки числа.
    """
    out: list[str] = []
    index = 0
    length = len(source)
    while index < length:
        char = source[index]
        if char in "\"'`":
            quote = char
            out.append(char)
            index += 1
            while index < length:
                current = source[index]
                out.append(current)
                index += 1
                if current == "\\" and index < length:
                    out.append(source[index])
                    index += 1
                    continue
                if current == quote:
                    break
            continue
        if char == "/" and index + 1 < length:
            following = source[index + 1]
            if following == "/":
                while index < length and source[index] != "\n":
                    index += 1
                continue
            if following == "*":
                end = source.find("*/", index + 2)
                index = length if end == -1 else end + 2
                continue
        out.append(char)
        index += 1
    return "".join(out)


# РАСПОЗНАВАЕМЫЕ ФОРМЫ РЕГИСТРАЦИИ — ДВЕ, и вторая включена не впрок.
#
#   * вызов метода регистрации слушателя на приёмнике (`…addEventListener(`) —
#     единственная форма, которой пользуется дерево сегодня;
#   * присваивание свойства-обработчика (`…onclick =`) — вхождений внутри тел
#     блоков в дереве НОЛЬ (замер планировщика 2026-09-12; единственное
#     вхождение такой формы в проекте — атрибут РАЗМЕТКИ `components/thumb.html:34`,
#     то есть предмет утверждения 3, а не пятого).
#
# Форма включена потому, что правило, знающее ОДНУ форму, пропустит регистрацию,
# вернувшуюся в другой, — и пропустит её МОЛЧА, ровно как четыре утверждения
# пропустили третий обработчик.
#
# ⚠️ ГРАНИЦА ДОКАЗАННОГО, И ПЕРЕЧЕНЬ ЭТОТ ЕСТЬ ЧАСТЬ ПРАВИЛА, А НЕ ПРИЗНАНИЕ
# СЛАБОСТИ. Пятое утверждение НЕ ВИДИТ: регистраций, сделанных кодом из каталога
# вендоренных сценариев (предмет утверждения 1); атрибутов событий разметки
# (предмет утверждения 3); узлов клиентского состояния (предмет утверждения 4);
# регистрации, собранной склейкой строк (`el['add' + 'EventListener']`).
HANDLER_REGISTRATION_FORMS = (
    re.compile(r"\.addEventListener\s*\("),
    re.compile(r"\.on[a-z]{2,}\s*=(?!=)"),
)


def _script_handler_registrations(
    templates: list[tuple[str, str]],
) -> dict[str, int]:
    """Измеренный перечень «путь шаблона → число регистраций в телах `<script>`».

    В перечень попадают ТОЛЬКО файлы с НЕНУЛЕВЫМ числом. Пять шаблонов дерева
    несут блок сценария без единой регистрации, и нули в перечне были бы
    величинами, которые надо сверять, — сторож завёл бы себе сторожа. Новый
    файл, принёсший регистрацию, приходит в перечень НОВЫМ КЛЮЧОМ, и разница
    множеств его называет поимённо.

    Вход — пары «путь — исходник», а не каталог: группа контроля обязана подать
    ИЗМЕНЁННУЮ копию дерева, и обход, зашитый на боевой каталог, сделал бы
    отрицательные контроли невыразимыми.
    """
    measured: dict[str, int] = {}
    for rel, source in templates:
        total = 0
        for body in _script_bodies(_strip_comments(source)):
            text = _strip_js_comments(body)
            total += sum(len(form.findall(text)) for form in HANDLER_REGISTRATION_FORMS)
        if total:
            measured[rel] = total
    return measured


# ОБЪЯВЛЕНИЕ — ДВА СЛАГАЕМЫХ, И ВТОРОЕ ЗДЕСЬ НЕ ОБЪЯВЛЯЕТСЯ ВОВСЕ.
#
# Ниже перечислены ТОЛЬКО те файлы, у которых единственного источника числа ещё
# нет. Значение `includes/htmx_error_banner.html` живёт в
# `tests/test_pages/test_shell.py` (`FAILURE_BANNER_HANDLERS_MEASURED`) и
# приезжает сюда ВВОЗОМ: вторая копия числа разошлась бы с первой МОЛЧА, и
# правило проверяло бы устаревшее значение при зелёном соседе. Та же доктрина
# единственного источника, по которой утверждения 3 и 4 ввозят
# `INLINE_HANDLER_ATTR` и `CLIENT_STATE_NODES`.
#
# ЛЕТОПИСЬ ЧИСЛА `ads/form.html`: измерено разбором дерева 2026-09-12 планом
# 10-52 — восемь вызовов регистрации в единственном блоке сценария файла
# (`:411`, `:423`, `:514`, `:517`, `:532`-`:535`). На базе фазы (`7c1041d`)
# число было тем же: фаза этого файла сценарием не трогала.
#
# ЧТО ОЗНАЧАЕТ ДВИЖЕНИЕ ЧИСЛА В КАЖДУЮ СТОРОНУ:
#   вверх — в тело блока внесена НОВАЯ регистрация; это новая СУЩНОСТЬ в смысле
#           D-13, то есть предмет решения о критерии 3, а не правка тела
#           существующего метода;
#   вниз  — регистрация ушла из дерева ЛИБО её потерял разборщик; второе
#           опаснее первого и краснеет тем же отказом.
SCRIPT_HANDLER_REGISTRATIONS_DECLARED_HERE = {
    "ads/form.html": 8,
}

FAILURE_BANNER_TEMPLATE = "includes/htmx_error_banner.html"


def _declared_script_handler_registrations() -> dict[str, int]:
    """Полное объявление: перечень выше ПЛЮС значение заготовок ВВОЗОМ.

    ⚠️ ВВОЗ ВНУТРИ ФУНКЦИИ, А НЕ НА УРОВНЕ МОДУЛЯ, И ПРИЧИНА ТА ЖЕ, ЧТО У ДВУХ
    УЖЕ СТОЯЩИХ В ЭТОМ ФАЙЛЕ ВВОЗОВ ИЗ `test_shell.py` (см. `:2869` и `:4276`):
    в том модуле на уровне модуля стои́т утверждение, срабатывание которого
    роняет СБОР файла целиком (`REVIEW-8/IN-01`), и модульный ввоз перенёс бы
    расхождение в ЧУЖОМ модуле на все правила настоящего файла.

    ЛЕТОПИСЬ ЧИСЛА ЗАГОТОВОК ЖИВЁТ ПРИ ЕГО ЕДИНСТВЕННОМ ИСТОЧНИКЕ, а не здесь:
    `tests/test_pages/test_shell.py:2295-2311` записывает и замер, и пересъёмку
    2 → 3 планом 10-49. Второй копии летописи здесь не заводится по тому же
    основанию, по которому не заводится второй копии числа.
    """
    # ⚠️ ЛЕТОПИСЬ ПЕРЕХОДА ЦВЕТА — НЕ ВЫЧЁРКИВАЕТСЯ, А ЕСТЬ ЗАМЕР (идиома
    # D-30/D-32). Красная фаза этого правила снята ОБЪЯВЛЕНИЕМ, равным ЗАМЕРУ
    # БАЗЫ ФАЗЫ (`7c1041d`): значение заготовок стояло здесь ЛИТЕРАЛОМ 2 — два
    # обработчика, заведённых Фазой 8 (коммит `6d2eaf2`). Отказ на том
    # объявлении назвал `includes/htmx_error_banner.html: найдено 3, объявлено 2`
    # (`1 failed, 87 deselected`, rc=1, коммит `9042c55`).
    #
    # ЗАЧЕМ RED СНИМАЛСЯ ИМЕННО ТАК, А НЕ НА НЕТРОНУТОМ ДЕРЕВЕ: обычная форма
    # этой фазы здесь НЕДОСТИЖИМА ЧЕСТНО — покраснеть на настоящем дереве
    # правило могло бы только ОТКАТОМ третьего обработчика, а откат запрещён
    # (правка закрывает настоящий дефект `G-10-5` и стережётся двумя
    # контролями плана 10-49). Замер базы фазы есть ровно то объявление, при
    # котором правило, существуй оно тогда, увидело бы правку девятой партии, —
    # то есть ИЗМЕРЕНО, что правило различает дерево ДО коммита `4e24d61` и
    # дерево ПОСЛЕ него.
    #
    # ЧЕМ ЗНАЧЕНИЕ БЕРЁТСЯ ТЕПЕРЬ: ВВОЗОМ единственного источника. Литерала в
    # этом модуле НЕТ, и второй копии числа завести нечем.
    from tests.test_pages.test_shell import FAILURE_BANNER_HANDLERS_MEASURED

    return {
        **SCRIPT_HANDLER_REGISTRATIONS_DECLARED_HERE,
        FAILURE_BANNER_TEMPLATE: FAILURE_BANNER_HANDLERS_MEASURED,
    }


def test_criterion_three_holds_by_the_numbers():
    """Критерий 3 вехи — ЧЕТЫРЬМЯ ЧИСЛАМИ, и каждое названо отдельно.

    ⚠️ ПРОЧТЕНИЕ КРИТЕРИЯ 3 (D-13) — РЕШЕНИЕ ВЛАДЕЛЬЦА, А НЕ ВОЛЬНОСТЬ
    ИСПОЛНИТЕЛЯ, И ЗАПИСАНО ОНО ЗДЕСЬ ЦЕЛИКОМ. Критерий гласит «новых строк JS
    фаза не добавляет (машинно: диффом по `app/static/js/` и шаблонам)», а фаза
    правит тела `hide()`, `destroy()` и выражение `x-on:htmx:after-request`
    внутри шаблона панели. Противоречие снимается прочтением: критерий
    запрещает НОВЫЕ СУЩНОСТИ, а не правку существующих. Правка тела метода
    объекта клиентского состояния и правка выражения СУЩЕСТВУЮЩЕГО атрибута
    новой сущностью не является — новый ключ того же объекта остаётся тем же
    объектом.

    БУКВАЛЬНОЕ ПРОЧТЕНИЕ ОТВЕРГНУТО, и причина не в удобстве: оно запретило бы
    ПОЧИНКУ теми же критериями, которые эту починку просят. Критерий 2 той же
    фазы требует, чтобы панель не закрывалась на отказе, а критерий про фокус —
    чтобы фокус приземлялся; исполнить оба, не тронув ни одного выражения, нельзя.

    ФОРМУЛИРОВКА КРИТЕРИЯ В РОАДМАПЕ НЕ АМЕНДИРОВАНА, и это тоже решение:
    документ вехи держится ФИКСИРОВАННЫМ, а прочтение есть предмет записи
    решений (`10-CONTEXT.md`, D-13) и вот этого правила. Амендмент чужого
    документа задним числом лишил бы читателя возможности увидеть, что
    прочтение вообще понадобилось.

    ЧТО ИМЕННО ФАЗА НЕ ПРИБАВИЛА — четыре вещи, по одной на утверждение:
      1. ни одного файла в каталоге вендоренных сценариев;
      2. ни одного шаблона со ВСТРОЕННЫМ обработчиком отправки (`onsubmit`);
      3. ни одного атрибута события РАНТАЙМА РАЗМЕТКИ (`hx-on`) — их в проекте
         ноль, и ноль этот утверждается здесь вместе с остальными тремя;
      4. ни одного узла клиентского состояния (`x-data`).

    ⚠️ ОТКАЗ НАЗЫВАЕТ, КАКОЕ ИМЕННО ИЗ ЧЕТЫРЁХ УТВЕРЖДЕНИЙ НЕ СОШЛОСЬ, и
    приводит найденное рядом с объявленным. Общий отказ «критерий 3 нарушен» не
    сказал бы, где искать, — а четыре утверждения ведут в четыре разных файла.

    ⚠️ ЗАПИСЬ D-30/D-32: ТО, ЧТО ПЕРЕРОСЛО ЧЕТЫРЕ ЧИСЛА, ВСТАЁТ РЯДОМ С НИМИ, А
    НЕ НА ИХ МЕСТО. Всё, что записано выше, было ВЕРНО для своего дерева, и
    вычёркиванию не подлежит. Но 2026-09-11 коммит `4e24d61` (план 10-49) внёс
    в ТЕЛО блока `<script>` шаблона `includes/htmx_error_banner.html:227-233`
    семь исполняемых строк JS — целиком новую регистрацию ТРЕТЬЕГО обработчика
    на узле тела документа. Ни одно из четырёх утверждений выше этого класса
    правок не измеряет: тело блока сценария не есть ни файл каталога
    `app/static/js/`, ни атрибут `onsubmit`, ни атрибут `hx-on`, ни узел
    `x-data`. ОДИННАДЦАТЫЙ круг верификации назвал это блокером: зелень
    настоящего правила об этой правке не говорила НИЧЕГО.

    Поэтому утверждений здесь ПЯТЬ, и пятое меряет то, чего не мерял никто:
      5. регистрации обработчиков в телах блоков `<script>` всех шаблонов —
         ПЕРЕЧНЕМ ФАЙЛОВ С ЧИСЛАМИ, а не одним итогом (пять шаблонов дерева
         несут блок сценария без единой регистрации, и один итог не сказал бы,
         в каком из семи искать).

    ⚠️ ОСНОВАНИЕ ЧИСЛА ТРЁХ РЕГИСТРАЦИЙ У ЗАГОТОВОК ЕСТЬ РЕШЕНИЕ
    ВЛАДЕЛЬЦА, И ОНО ВНЕСЕНО, А НЕ ОЖИДАЕТСЯ. Тремя величинами: ветвь
    `extend-override`, принял `chubav`, дата 2026-09-12. Живёт решение ПОЛЕМ,
    а не прозой, — записью `overrides[1]` шапки
    `.planning/phases/10-rychag-components-modal-html/10-VERIFICATION.md` (останов
    задачи 1 плана 10-53, `gate="blocking-human"`): область действующего
    отступления РАСШИРЕНА записью, называющей ТРЕТИЙ ФАЙЛ
    (`app/templates/includes/htmx_error_banner.html`) и ТРЕТЬЮ СУЩНОСТЬ
    (регистрацию `htmx:afterRequest` на узле тела документа, `:227-233`,
    коммит `4e24d61`) ПОИМЁННО. Цена расширения названа там же и
    ссылается на запись 74 журнала `.planning/WINDOWS.md`.

    ⚠️ ОБЛАСТЬ ТОГО РЕШЕНИЯ УЗКА, И УЗОСТЬ ЕСТЬ ЕГО ПРЕДМЕТ: поле
    `covers` покрывает ТОЛЬКО ЭТУ регистрацию и на БУДУЩИЕ регистрации
    в том же файле НЕ распространяется. Следующая такая регистрация
    обязана покраснить настоящее утверждение и требует НОВОГО решения
    владельца.

    ⚠️ ЧЕГО ЭТО ОСНОВАНИЕ НЕ МЕНЯЕТ — ПРЕДМЕТ ПРАВИЛА. Утверждение
    объявляет ЧИСЛО СЕГОДНЯШНЕГО ДЕРЕВА и ловит НЕЗАЯВЛЕННОЕ, а не
    заявленное. Объявленное число вправе сдвинуть только НОВОЕ решение
    владельца, а не замер исполнителя: правка одного лишь числа под
    найденное есть ровно то молчание, против которого утверждение
    заведено, — и машина не вправе выбрать за владельца, ровно как
    верификатор не вправе толковать отступление шире, чем оно себя
    объявляет.
    """
    templates = _all_templates()

    # 1. Каталог вендоренных сценариев — ИМЕНАМИ.
    vendored = _vendored_js_files()
    assert vendored == set(VENDORED_JS_FILES), (
        "УТВЕРЖДЕНИЕ 1 ИЗ 5 (каталог вендоренных сценариев) НЕ СОШЛОСЬ.\n"
        f"  найдено, но не объявлено: {sorted(vendored - set(VENDORED_JS_FILES))}\n"
        f"  объявлено, но не найдено: {sorted(set(VENDORED_JS_FILES) - vendored)}\n"
        "Новый файл здесь есть буквально «новая строка JS» в смысле критерия 3; "
        "исчезнувший означает, что рантайм подменили другой сборкой"
    )

    # 2. Встроенные обработчики отправки — число НЕ ВЫРОСЛО. Перечень живёт в
    # этом же файле и объявлен ОДИН раз (`KNOWN_SUBMIT_HANDLER_FILES`); второго
    # экземпляра здесь не заводится.
    with_inline_handler = {
        rel for rel, source in templates if INLINE_SUBMIT_HANDLER in source
    }
    assert with_inline_handler == set(KNOWN_SUBMIT_HANDLER_FILES), (
        "УТВЕРЖДЕНИЕ 2 ИЗ 5 (встроенные обработчики отправки) НЕ СОШЛОСЬ.\n"
        f"  найдено {len(with_inline_handler)}, объявлено "
        f"{len(KNOWN_SUBMIT_HANDLER_FILES)}\n"
        f"  новые: {sorted(with_inline_handler - set(KNOWN_SUBMIT_HANDLER_FILES))}\n"
        f"  исчезнувшие: {sorted(set(KNOWN_SUBMIT_HANDLER_FILES) - with_inline_handler)}"
    )

    # 3. Атрибуты событий рантайма разметки — вхождений НОЛЬ. Выражение берётся
    # ИМПОРТОМ из модуля правил безопасности разметки: второго экземпляра
    # регулярки не заводится, поэтому расхождение двух копий невозможно ПО
    # ПОСТРОЕНИЮ, а не по договорённости.
    runtime_event_attrs = {
        rel: INLINE_HANDLER_ATTR.findall(_strip_comments(source))
        for rel, source in templates
        if INLINE_HANDLER_ATTR.search(_strip_comments(source))
    }
    assert not runtime_event_attrs, (
        "УТВЕРЖДЕНИЕ 3 ИЗ 5 (атрибуты событий рантайма разметки) НЕ СОШЛОСЬ.\n"
        f"  найдено вхождений в {len(runtime_event_attrs)} файлах: "
        f"{sorted(runtime_event_attrs)}, объявлен НОЛЬ.\n"
        "Содержимое такого атрибута разбирается рантаймом как выражение — это "
        "второй слой экранирования поверх слоя разметки, и автоматическое "
        "экранирование шаблонизатора его не касается"
    )

    # 4. Узлы клиентского состояния — число НЕ ДВИНУЛОСЬ. И число, и обход
    # берутся ИМПОРТОМ из объявляющего их модуля разметочных гейтов.
    client_state_nodes = len(_client_state_sites(templates))
    assert client_state_nodes == CLIENT_STATE_NODES, (
        "УТВЕРЖДЕНИЕ 4 ИЗ 5 (узлы клиентского состояния) НЕ СОШЛОСЬ.\n"
        f"  найдено {client_state_nodes}, объявлено {CLIENT_STATE_NODES}.\n"
        "Новый узел `x-data` есть новая СУЩНОСТЬ в смысле D-13 — в отличие от "
        "правки тела метода уже существующего объекта, которую критерий 3 не "
        "запрещает"
    )

    # 5. Регистрации обработчиков в ТЕЛАХ блоков `<script>` — ПЕРЕЧНЕМ ФАЙЛОВ С
    # ЧИСЛАМИ. Значение заготовок в объявлении приходит ВВОЗОМ единственного
    # источника, поэтому расхождение двух копий невозможно ПО ПОСТРОЕНИЮ.
    registrations = _script_handler_registrations(templates)
    declared = _declared_script_handler_registrations()
    diverged = {
        rel: (registrations.get(rel), declared.get(rel))
        for rel in sorted(set(registrations) | set(declared))
        if registrations.get(rel) != declared.get(rel)
    }
    appeared = sorted(set(registrations) - set(declared))
    vanished = sorted(set(declared) - set(registrations))
    assert not diverged, (
        "УТВЕРЖДЕНИЕ 5 ИЗ 5 (регистрации обработчиков в телах блоков "
        "`<script>`) НЕ СОШЛОСЬ.\n"
        + "".join(
            f"  {rel}: найдено {found}, объявлено {decl}\n"
            for rel, (found, decl) in diverged.items()
        )
        + f"  появившиеся файлы: {appeared}\n"
        + f"  исчезнувшие файлы: {vanished}\n"
        + "Отказ печатает ФАЙЛ и ОБА ЧИСЛА при нём, а появившиеся и исчезнувшие "
        "файлы — РАЗНИЦЕЙ МНОЖЕСТВ, а не парой итогов: два итога сказали бы, "
        "что число разошлось, и не сказали бы, где искать (класс находки "
        "ревизии IN-03, и повторять его в правиле, заводимом ПРОТИВ молчаливых "
        "движений, было бы платой за собственный урок).\n"
        "Новая регистрация в теле блока сценария есть новая СУЩНОСТЬ в смысле "
        "D-13 — в отличие от правки тела существующего метода, которую критерий "
        "3 не запрещает. Если число выросло ОСОЗНАННО, объявление правится "
        "вместе с записью ОСНОВАНИЯ; правка одного лишь числа есть ровно то "
        "молчание, против которого утверждение заведено"
    )


def test_control_negative_a_new_vendored_script_reddens_the_gate(tmp_path):
    """ЧТО ДОКАЗЫВАЕТ: утверждение 1 краснеет на ЛИШНЕМ файле сценариев.

    ⚠️ БЕЗ ЭТОГО КОНТРОЛЯ ПЕРВОЕ УТВЕРЖДЕНИЕ БЫЛО БЫ ЗЕЛЁНЫМ ПО ПОСТРОЕНИЮ.
    Сломанный обход (не тот каталог, не то расширение, нерекурсивный поиск) даёт
    ПУСТОЕ множество, а пустое множество перестаёт сходиться с объявленным
    только в тот день, когда перечень тоже опустошат. Подмена ниже кладёт в
    копию каталога третий файл и утверждает, что правило его ВИДИТ.

    Каталог проекта контроль не трогает: подмена пишется во временный каталог
    (`tmp_path`), боевое дерево читается только на чтение.
    """
    scratch = tmp_path / "js"
    scratch.mkdir()
    for name in sorted(VENDORED_JS_FILES):
        (scratch / name).write_text("/* копия для контроля */\n", encoding="utf-8")
    intruder = "some-future-phase-vendored-this.min.js"
    (scratch / intruder).write_text("/* лишний файл */\n", encoding="utf-8")

    found = _vendored_js_files(scratch)

    assert intruder in found, (
        "ПОДМЕНА НЕ ПРИЗЕМЛИЛАСЬ: обход не увидел лишнего файла, и утверждение "
        "ниже доказывало бы не зубы правила, а промах контроля"
    )
    assert found != set(VENDORED_JS_FILES), (
        "УТВЕРЖДЕНИЕ О НАБОРЕ ВЕНДОРЕННЫХ ФАЙЛОВ НЕ ЗАМЕТИЛО НОВЫЙ ФАЙЛ — "
        "критерий 3 закрывался бы заявлением, а не измерением, и новая строка "
        "JS приехала бы в проект молча"
    )

    # Граница контроля: боевой каталог подменой не тронут.
    assert _vendored_js_files() == set(VENDORED_JS_FILES), (
        "ПОДМЕНА ПРОТЕКЛА ЗА ГРАНИЦУ КОНТРОЛЯ: боевой каталог сценариев изменён"
    )


# --- ЗУБЫ ПЯТОГО УТВЕРЖДЕНИЯ: ДВА ОТРИЦАТЕЛЬНЫХ КОНТРОЛЯ --------------------
#
# ⚠️ БЕЗ НИХ ПЯТОЕ УТВЕРЖДЕНИЕ БЫЛО БЫ ЗЕЛЁНЫМ ПО ПОСТРОЕНИЮ. Сломанный обход
# тел блоков (не тот тег, не тот каталог, потерянный закрывающий тег) даёт
# ПУСТОЙ перечень, а пустой перестаёт сходиться с объявленным только в тот день,
# когда объявление тоже опустошат. Ровно этот класс уже назван у контроля
# каталога вендоренных сценариев выше, и форма здесь наследуется дословно: три
# утверждения — подмена приземлилась, правило её видит, БОЕВОЕ дерево не тронуто.
#
# ⚠️ ДВА КОНТРОЛЯ, А НЕ ОДИН, И ВТОРОЙ НЕ ИЗБЫТОЧЕН ПРИ ПЕРВОМ. Первый
# доказывает, что правило видит движение ЧИСЛА у ИЗВЕСТНОГО файла; второй — что
# оно видит ПОЯВЛЕНИЕ файла. Правило, отбирающее только объявленные ключи,
# прошло бы первый и провалило бы предмет: следующая фаза положит сценарий в
# НОВЫЙ шаблон, а не в старый.

CONTROL_PLANTED_REGISTRATIONS = 1

CONTROL_INVENTED_TEMPLATE = "controls/a-template-the-control-invented.html"


def _templates_copy(tmp_path: Path) -> Path:
    """Копия боевого каталога шаблонов во временном каталоге.

    Граница контроля начинается ЗДЕСЬ: подмена пишется в копию, боевое дерево
    читается только на чтение. Третье утверждение каждого контроля ниже эту
    границу ПРОВЕРЯЕТ, а не декларирует, — контроль, протёкший за неё, правил бы
    предмет, который меряет, и оба контроля стали бы зелёными по построению.
    """
    scratch = tmp_path / "templates"
    shutil.copytree(TEMPLATES_DIR, scratch)
    return scratch


def test_control_negative_a_new_handler_registration_reddens_the_gate(tmp_path):
    """ЧТО ДОКАЗЫВАЕТ: пятое утверждение краснеет на ЛИШНЕЙ регистрации.

    ⚠️ ПОДСАЖИВАЕТСЯ РЕГИСТРАЦИЯ НА ПРОИЗВОЛЬНОЕ ИМЯ СОБЫТИЯ, А НЕ КОПИЯ
    ТРЕТЬЕГО ОБРАБОТЧИКА. Правило обязано краснеть на РЕГИСТРАЦИЮ КАК ТАКОВУЮ, а
    не на одно знакомое имя события: иначе следующая правка заведёт слушателя
    другого события, и правило промолчит ровно так же, как промолчали четыре
    утверждения на `htmx:afterRequest`.

    ⚠️ ОЖИДАНИЕ ВЫПИСАНО ЛИТЕРАЛОМ (`CONTROL_PLANTED_REGISTRATIONS` — ровно одна
    подсаженная регистрация), а не вычислено из измерения: вычисленное ожидание
    сходится с измеренным ВСЕГДА, включая день, когда оба неверны.
    """
    scratch = _templates_copy(tmp_path)
    declared = _declared_script_handler_registrations()

    # Копия БЕЗ подмены: правило её ОТПУСКАЕТ. Без этого замера утверждения ниже
    # доказывали бы не зубы правила, а то, что копия отличается от дерева.
    pristine = _script_handler_registrations(_all_templates_under(scratch))
    assert pristine == declared, (
        "КОПИЯ КАТАЛОГА РАЗОШЛАСЬ С ОБЪЯВЛЕНИЕМ ДО ВСЯКОЙ ПОДМЕНЫ: "
        f"{pristine} против {declared}. Контроль ниже мерял бы изъян копирования"
    )

    banner = scratch / FAILURE_BANNER_TEMPLATE
    source = banner.read_text(encoding="utf-8")
    assert source.count("</script>") == 1, (
        "ФОРМА ПОДМЕНЫ РАЗОШЛАСЬ С ФАЙЛОМ: в заготовках ожидался ОДИН "
        f"закрывающий тег, найдено {source.count('</script>')}"
    )
    banner.write_text(
        source.replace(
            "</script>",
            "  document.body.addEventListener("
            "'a-control-invented-this-event-name', function () { return; });\n"
            "</script>",
            1,
        ),
        encoding="utf-8",
    )

    measured = _script_handler_registrations(_all_templates_under(scratch))

    # 1. Подмена ПРИЗЕМЛИЛАСЬ: ровно одна регистрация сверх прежнего.
    assert (
        measured.get(FAILURE_BANNER_TEMPLATE)
        == declared[FAILURE_BANNER_TEMPLATE] + CONTROL_PLANTED_REGISTRATIONS
    ), (
        "ПОДМЕНА НЕ ПРИЗЕМЛИЛАСЬ: разборщик не увидел подсаженной регистрации "
        f"({measured.get(FAILURE_BANNER_TEMPLATE)} против объявленных "
        f"{declared[FAILURE_BANNER_TEMPLATE]} плюс {CONTROL_PLANTED_REGISTRATIONS}), "
        "и утверждение ниже доказывало бы промах контроля, а не зубы правила"
    )

    # 2. Правило ВИДИТ расхождение и называет ФАЙЛ — ровно тем сличением,
    # которым сличает пятое утверждение гейта.
    diverged = sorted(
        rel
        for rel in set(measured) | set(declared)
        if measured.get(rel) != declared.get(rel)
    )
    assert diverged == [FAILURE_BANNER_TEMPLATE], (
        "ПЯТОЕ УТВЕРЖДЕНИЕ НЕ ЗАМЕТИЛО ЛИШНЕЙ РЕГИСТРАЦИИ В ТЕЛЕ БЛОКА "
        f"СЦЕНАРИЯ: разошлись {diverged}. Критерий 3 закрывался бы заявлением, "
        "а не измерением, и новая строка JS приехала бы в проект молча — ровно "
        "как приехала 2026-09-11 коммитом `4e24d61`"
    )

    # 3. ГРАНИЦА КОНТРОЛЯ: боевое дерево подменой не тронуто.
    assert _script_handler_registrations(_all_templates()) == declared, (
        "ПОДМЕНА ПРОТЕКЛА ЗА ГРАНИЦУ КОНТРОЛЯ: боевой каталог шаблонов изменён"
    )


def test_control_negative_a_new_template_with_a_handler_registration_reddens_the_gate(
    tmp_path,
):
    """ЧТО ДОКАЗЫВАЕТ: пятое утверждение краснеет на НОВОМ файле с регистрацией.

    Файл приходит в измеренный перечень НОВЫМ КЛЮЧОМ, и разница множеств
    называет его поимённо — а не растворяет в итоговом числе. Ровно этого не
    делает находка ревизии `IN-03` (инвентарь поднят числом, отказ печатает два
    итога), и повторять её класс в правиле, заводимом ПРОТИВ молчаливых
    движений, было бы платой за собственный урок.

    ⚠️ ОЖИДАНИЯ ВЫПИСАНЫ ЛИТЕРАЛАМИ: имя подсаженного файла и число регистраций
    в нём (`CONTROL_PLANTED_REGISTRATIONS`).

    ⚠️ В ИМЕНИ СТОИ́Т `handler_registration`, И ЭТО НЕ УКРАШЕНИЕ. Отбор гейта
    партии — `-k "criterion_three or handler_registration or vendored_script"` —
    требует собрать ЧЕТЫРЕ правила; имя без этой подстроки в отбор не попало бы,
    и цвет настоящего контроля не мерялся бы НИЧЕМ. Правило, чья краснота
    никем не читается, есть то же вакуумное принуждение, против которого
    заводится пятое утверждение.
    """
    scratch = _templates_copy(tmp_path)
    declared = _declared_script_handler_registrations()

    invented = scratch / CONTROL_INVENTED_TEMPLATE
    invented.parent.mkdir(parents=True, exist_ok=True)
    invented.write_text(
        "<div id=\"a-node-the-control-invented\"></div>\n"
        "<script>\n"
        "  document.body.addEventListener("
        "'a-control-invented-this-event-name', function () { return; });\n"
        "</script>\n",
        encoding="utf-8",
    )

    measured = _script_handler_registrations(_all_templates_under(scratch))

    # 1. Подмена ПРИЗЕМЛИЛАСЬ: новый файл попал в перечень НОВЫМ ключом.
    assert measured.get(CONTROL_INVENTED_TEMPLATE) == CONTROL_PLANTED_REGISTRATIONS, (
        "ПОДМЕНА НЕ ПРИЗЕМЛИЛАСЬ: обход не увидел НОВОГО шаблона с блоком "
        f"сценария ({measured.get(CONTROL_INVENTED_TEMPLATE)} против "
        f"{CONTROL_PLANTED_REGISTRATIONS}), и утверждение ниже доказывало бы "
        "промах контроля"
    )

    # 2. Правило ВИДИТ появление файла и называет ЕГО, а не итог.
    appeared = sorted(set(measured) - set(declared))
    assert appeared == [CONTROL_INVENTED_TEMPLATE], (
        "ПЯТОЕ УТВЕРЖДЕНИЕ НЕ ЗАМЕТИЛО НОВОГО ШАБЛОНА С РЕГИСТРАЦИЕЙ: "
        f"появившиеся {appeared}. Правило, отбирающее только ОБЪЯВЛЕННЫЕ ключи, "
        "прошло бы контроль лишней регистрации и провалило бы предмет: сценарий "
        "следующей фазы ляжет в НОВЫЙ шаблон, а не в старый"
    )

    # 3. ГРАНИЦА КОНТРОЛЯ: боевое дерево подменой не тронуто.
    assert _script_handler_registrations(_all_templates()) == declared, (
        "ПОДМЕНА ПРОТЕКЛА ЗА ГРАНИЦУ КОНТРОЛЯ: боевой каталог шаблонов изменён"
    )
    assert not (TEMPLATES_DIR / CONTROL_INVENTED_TEMPLATE).exists(), (
        "ПОДМЕНА ПРОТЕКЛА ЗА ГРАНИЦУ КОНТРОЛЯ: выдуманный контролем шаблон "
        "приземлился в БОЕВОЕ дерево"
    )


# =============================================================================
# СТЕРЕГУЩЕЕ ПРАВИЛО ПОМЕТКИ ВТОРОЙ ВЕТВИ УСЛОВИЯ ЗАКРЫТИЯ ПАНЕЛИ
# (Фаза 10, план 10-27, IN-02 ПЯТОГО круга ревизии)
# =============================================================================
#
# ⚠️ ЧТО ЭТО ПРАВИЛО СТЕРЕЖЁТ, И ЧЕГО ОНО НЕ СТЕРЕЖЁТ. Оно стережёт СОГЛАСИЕ
# ПОМЕТКИ С ДЕРЕВОМ, а не продуктовое решение. Пометка стои́т в
# `app/templates/components/modal.html` над открывающим тегом формы панели и
# цитирует ЗАМЕР: мест сборки ответа с заголовком перехода — одно, статус — 204.
# Пометка без стерегущего правила есть в точности тот класс записи, за который
# фаза получила круги 3, 4 и 5: утверждение, верное в день записи, переживающее
# своё дерево и читаемое следующим как исполненный инвариант.
#
# ⚠️ ПОЧЕМУ ПРАВИЛО НЕ УТВЕРЖДАЕТ «СТАТУС ЛЕЖИТ В УСПЕШНОМ ДИАПАЗОНЕ», ХОТЯ 204
# В НЁМ ЛЕЖИТ. Такое утверждение стерегло бы НЕ ТО. Замер вендоренного рантайма
# (`app/static/js/htmx.min.js`, htmx 2.0.10): ветка заголовка перехода в
# обработчике ответа `Vn` стои́т на смещении 47067 и кончается ранним возвратом,
# а ЕДИНСТВЕННОЕ в бандле присваивание признака успешности — на смещении 48145,
# то есть ПОСЛЕ него. До диапазона исполнение на этом пути НЕ ДОХОДИТ ВОВСЕ, и
# признак есть `undefined`, а не `false`. Диапазон здесь ни на что не влияет;
# влияет ЦИТАТА статуса в пометке — её правило и сличает с деревом.
#
# ⚠️ ПРАВИЛО НЕ СУДИТ О ТОМ, ДОЛЖЕН ЛИ ПРОЕКТ ЗАВОДИТЬ ОТКАЗ С ПЕРЕХОДОМ. Оно
# краснеет ровно тогда, когда пометка разошлась с деревом, и отправляет читателя
# править ПОМЕТКУ.

# --- ОБЪЯВЛЕННЫЕ ЧИСЛА -------------------------------------------------------
#
# ЛЕТОПИСЬ: измерено разбором дерева `app/**/*.py` по AST 2026-09-08 планом
# 10-27 (`transition_response_assemblies` ниже — тот же разборщик, которым
# меряет правило). Найдено ОДНО место — `Response(status_code=204,
# headers={HX_LOCATION_HEADER: …})` внутри `location_response()`
# (`app/pages/htmx.py`). Мест ВЫЗОВА этой сборки два (`respond()` там же и
# `htmx_refusal_handler` в `app/main.py`), но собирают ответ они не сами —
# число ниже считает СБОРКУ, а не вызов.
#
# ЧТО ОЗНАЧАЕТ ДВИЖЕНИЕ ЧИСЛА В КАЖДУЮ СТОРОНУ:
#   вверх — в дереве появилась ВТОРАЯ сборка ответа с заголовком перехода;
#           замер пометки снят с другого дерева, и решение о втором дизъюнкте
#           обязано быть принято заново;
#   вниз  — сборка ушла или разборщик её потерял; пометка цитирует место,
#           которого нет.
TRANSITION_ASSEMBLY_PLACES = 1

# ЛЕТОПИСЬ: тот же замер того же дня тем же планом. 204 ставится ОДНИМ местом,
# поэтому у всех ответов перехода проекта статус один. Обоснование самого
# статуса записано докстрингом `location_response()` (204 не имеет тела ПО
# ОПРЕДЕЛЕНИЮ) и этим правилом не пересматривается — правило лишь сличает
# цитату пометки с деревом.
TRANSITION_RESPONSE_STATUS = 204

APP_DIR = Path(__file__).resolve().parents[2] / "app"


class TransitionAssembly(NamedTuple):
    """Одно место сборки ответа, несущего заголовок перехода."""

    module: str
    line: int
    status: int | None
    form: str


def _resolvable_string_names(tree: ast.Module) -> dict[str, str]:
    """Имена исходника, разрешимые в СТРОКУ: модульные константы плюс импорты.

    ⚠️ БЕЗ РАЗРЕШЕНИЯ ИМЁН РАЗБОР ЛОВИЛ БЫ ТОЛЬКО ЛИТЕРАЛ. Боевое место сборки
    пишет `headers={HX_LOCATION_HEADER: …}` — имя, а не строку; разборщик,
    умеющий только строки, нашёл бы НОЛЬ мест и покраснел бы антивакуумом на
    исправном дереве.
    """
    names: dict[str, str] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names[target.id] = node.value.value
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("pages.htmx"):
            for alias in node.names:
                value = getattr(app_htmx, alias.name, None)
                if isinstance(value, str):
                    names[alias.asname or alias.name] = value
    return names


def _is_transition_header_key(node: ast.expr, names: dict[str, str]) -> bool:
    """Ключ словаря заголовков есть заголовок перехода — в любой из трёх форм.

    Сличение регистронезависимое: имена заголовков регистром не различаются, и
    правило, различающее их регистром, краснело бы на написании, а не на сути.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.lower() == HX_LOCATION_HEADER.lower()
    if isinstance(node, ast.Name):
        return names.get(node.id, "").lower() == HX_LOCATION_HEADER.lower()
    if isinstance(node, ast.Attribute):
        resolved = getattr(app_htmx, node.attr, None)
        return isinstance(resolved, str) and resolved.lower() == HX_LOCATION_HEADER.lower()
    return False


def transition_response_assemblies(sources: dict[str, str]) -> list[TransitionAssembly]:
    """Места сборки ответа с заголовком перехода — ПО ДЕРЕВУ, а не по строкам.

    ⚠️ ИСХОДНИКИ ПРИХОДЯТ ПАРАМЕТРОМ, И ЭТО НЕСУЩЕЕ. Без параметра зубы правила
    пришлось бы ЗАЯВЛЯТЬ вместо того, чтобы их ПОКАЗЫВАТЬ, а боевой файл
    пришлось бы править ради доказательства. Приём взят у действующих контролей
    фазы (`tests/test_pages/test_origin_guard_on_destructive_routes.py`).

    ⚠️ РАЗБОР ПО ДЕРЕВУ, А НЕ ПОСТРОЧНЫЙ. Построчный поиск имени заголовка
    считал бы его вхождения в докстрингах и комментариях слоя ответа — их там
    несколько, — то есть ОБЪЯСНЕНИЕ роняло бы УТВЕРЖДЕНИЕ.

    Узнаются ДВЕ формы сборки: именованный аргумент заголовков в вызове и
    присваивание в заголовки уже готового ответа. Вторая от первой не отличается
    ничем, кроме видимости для наивного разборщика, — то есть место, написанное
    ею, выпало бы из обхода МОЛЧА.
    """
    found: list[TransitionAssembly] = []
    for module, source in sorted(sources.items()):
        tree = ast.parse(source)
        names = _resolvable_string_names(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                header_dicts = [
                    kw.value
                    for kw in node.keywords
                    if kw.arg == "headers" and isinstance(kw.value, ast.Dict)
                ]
                carries = any(
                    key is not None and _is_transition_header_key(key, names)
                    for header_dict in header_dicts
                    for key in header_dict.keys
                )
                if not carries:
                    continue
                status: int | None = None
                for kw in node.keywords:
                    if (
                        kw.arg in ("status_code", "status")
                        and isinstance(kw.value, ast.Constant)
                        and isinstance(kw.value.value, int)
                    ):
                        status = kw.value.value
                if (
                    status is None
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, int)
                ):
                    status = node.args[0].value
                found.append(
                    TransitionAssembly(
                        module, node.lineno, status, "именованный аргумент заголовков"
                    )
                )
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Subscript) and _is_transition_header_key(
                        target.slice, names
                    ):
                        found.append(
                            TransitionAssembly(
                                module,
                                node.lineno,
                                None,
                                "присваивание в заголовки готового ответа",
                            )
                        )
    return found


def _app_python_sources() -> dict[str, str]:
    """Пары «путь относительно корня проекта → ТЕКСТ исходника», весь `app/`."""
    root = APP_DIR.parent
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(APP_DIR.rglob("*.py"))
    }


def check_transition_assemblies(sources: dict[str, str]) -> list[TransitionAssembly]:
    """Три утверждения о поданном дереве. Вынесены сюда РАДИ КОНТРОЛЕЙ.

    Правило ниже зовёт эту функцию боевым деревом, отрицательные контроли —
    подменёнными копиями. Второго экземпляра текстов отказа не заводится,
    поэтому контроль доказывает зубы ТОГО ЖЕ текста, который увидит читатель.
    """
    found = transition_response_assemblies(sources)

    # АНТИВАКУУМ: сломавшийся разборщик возвращает пустое множество, и зелёный
    # цвет сломанного разборщика посимвольно совпадает с зелёным цветом
    # соблюдённого правила. Без этого утверждения правило зеленело бы навсегда,
    # ничего не стерегя.
    assert found, (
        "АНТИВАКУУМ: разбор дерева `app/` не нашёл НИ ОДНОГО места сборки "
        "ответа с заголовком перехода. Такого дерева у проекта нет — значит "
        "сломался сам разборщик, и правило перестало отличать соблюдение от "
        "поломки"
    )

    listing = "; ".join(
        f"{a.module}:{a.line} ({a.form}, статус {a.status})" for a in found
    )
    assert len(found) == TRANSITION_ASSEMBLY_PLACES, (
        "СОБЫТИЕ (А): ЧИСЛО МЕСТ СБОРКИ ОТВЕТА С ЗАГОЛОВКОМ ПЕРЕХОДА РАЗОШЛОСЬ "
        f"С ОБЪЯВЛЕННЫМ — найдено {len(found)}, объявлено "
        f"{TRANSITION_ASSEMBLY_PLACES}: {listing}.\n"
        "Замер, на который опирается пометка второй ветви условия закрытия "
        "панели, СНЯТ С ДРУГОГО ДЕРЕВА. РЕШЕНИЕ О ВТОРОМ ДИЗЪЮНКТЕ ОБЯЗАНО БЫТЬ "
        "ПРИНЯТО ЗАНОВО: новое место могло завести форму ответа, которой у "
        "проекта не было"
    )

    wrong = [a for a in found if a.status != TRANSITION_RESPONSE_STATUS]
    assert not wrong, (
        "СОБЫТИЕ (Б): СТАТУС МЕСТА СБОРКИ РАЗОШЁЛСЯ С ОБЪЯВЛЕННЫМ — объявлено "
        f"{TRANSITION_RESPONSE_STATUS}, найдено: "
        + "; ".join(f"{a.module}:{a.line} → {a.status}" for a in wrong)
        + ".\nПОМЕТКА РЫЧАГА СТАЛА НЕВЕРНОЙ. Комментарий над открывающим тегом "
        "формы панели в app/templates/components/modal.html цитирует статус "
        f"{TRANSITION_RESPONSE_STATUS} как замер дерева, и цитата разошлась с "
        "деревом. ПРАВИТЬ ПОМЕТКУ, а не это правило"
    )
    return found


def test_the_transition_response_is_assembled_in_one_declared_place():
    """НЕСУЩЕЕ: замер, который цитирует пометка рычага, СХОДИТСЯ С ДЕРЕВОМ.

    Пометка второй ветви условия закрытия панели
    (`app/templates/components/modal.html`, над открывающим тегом формы)
    цитирует два числа: мест сборки ответа с заголовком перехода — одно, статус
    — 204. Оба сличаются здесь с деревом разбором по AST, а не принимаются на
    веру.

    ⚠️ ДВА СОБЫТИЯ РАЗОШЛИСЬ ДВУМЯ ТЕКСТАМИ СОЗНАТЕЛЬНО. Один текст на два
    разных события лгал бы в одном из них: (а) появилось новое место сборки —
    решение о втором дизъюнкте принимается заново; (б) статус существующего
    места уехал — цитата пометки стала неверной, и править надо пометку.
    """
    found = check_transition_assemblies(_app_python_sources())

    assert [a.status for a in found] == [TRANSITION_RESPONSE_STATUS], (
        f"замер дерева разошёлся с объявленным составом статусов: {found}"
    )


def test_control_negative_a_changed_transition_status_reddens_the_rule():
    """ЧТО ДОКАЗЫВАЕТ: правило выше КРАСНЕЕТ событием (Б) на подменённом статусе.

    ⚠️ ПОДМЕНА ЖИВЁТ В КОПИИ ИСХОДНИКА В ПАМЯТИ. Боевой файл контроль не
    трогает: правило принимает исходники параметром именно ради этого.
    """
    sources = _app_python_sources()
    mutated = dict(sources)
    mutated["app/pages/htmx.py"] = sources["app/pages/htmx.py"].replace(
        f"status_code={TRANSITION_RESPONSE_STATUS}, headers={{HX_LOCATION_HEADER",
        "status_code=400, headers={HX_LOCATION_HEADER",
    )
    assert mutated["app/pages/htmx.py"] != sources["app/pages/htmx.py"], (
        "ПОДМЕНА НЕ ПРИЗЕМЛИЛАСЬ: форма сборки в слое ответа изменилась, и "
        "контроль ниже доказывал бы не зубы правила, а промах контроля"
    )

    with pytest.raises(AssertionError) as raised:
        check_transition_assemblies(mutated)

    message = str(raised.value)
    assert "СОБЫТИЕ (Б)" in message, (
        "правило покраснело НЕ ТЕМ событием: подменён статус, а текст отказа "
        f"говорит о другом; текст: {message!r}"
    )
    assert "app/templates/components/modal.html" in message, (
        "текст события (Б) не называет файла рычага — поймавший красное пойдёт "
        f"ИСКАТЬ пометку вместо того, чтобы её править; текст: {message!r}"
    )

    # Граница контроля: боевое дерево подменой не тронуто.
    check_transition_assemblies(_app_python_sources())


def test_control_negative_a_second_transition_assembly_reddens_the_rule():
    """ЧТО ДОКАЗЫВАЕТ: правило КРАСНЕЕТ событием (А) на втором месте сборки.

    ⚠️ БЕЗ ЭТОГО КОНТРОЛЯ СЧЁТ МЕСТ БЫЛ БЫ ЗЕЛЁНЫМ ПО ПОСТРОЕНИЮ: разборщик,
    видящий ровно одну форму записи, пропустил бы вторую МОЛЧА. Подмена кладёт
    в копию дерева второе место, написанное тем же именем константы.
    """
    sources = _app_python_sources()
    intruder = "app/pages/some_future_phase.py"
    sources[intruder] = (
        "from fastapi import Response\n"
        "from app.pages.htmx import HX_LOCATION_HEADER\n"
        "\n"
        "def refuse_with_a_transition():\n"
        "    return Response(status_code=409, headers={HX_LOCATION_HEADER: '/ads'})\n"
    )

    with pytest.raises(AssertionError) as raised:
        check_transition_assemblies(sources)

    message = str(raised.value)
    assert "СОБЫТИЕ (А)" in message, (
        "правило покраснело НЕ ТЕМ событием: добавлено место сборки, а текст "
        f"отказа говорит о другом; текст: {message!r}"
    )
    assert intruder in message, (
        f"текст события (А) не называет найденных мест ПОИМЁННО: {message!r}"
    )
    assert "СОБЫТИЕ (Б)" not in message, (
        "два события слиплись в один текст — один из них он описывает ложно: "
        f"{message!r}"
    )


def test_control_negative_an_empty_transition_scan_cannot_go_green():
    """ЧТО ДОКАЗЫВАЕТ: правило ПАДАЕТ на пустом множестве найденных мест.

    Сломавшийся разбор не имеет права зеленеть: он зеленел бы навсегда, ничего
    не стерегя, и пометка рычага пережила бы своё дерево незамеченной.
    """
    with pytest.raises(AssertionError) as raised:
        check_transition_assemblies({})

    message = str(raised.value)
    assert "АНТИВАКУУМ" in message, (
        f"пустое множество покраснело не антивакуумом, а чем-то ещё: {message!r}"
    )
    assert "СОБЫТИЕ" not in message, (
        "пустое множество покраснело текстом события расхождения — читатель "
        f"пойдёт править дерево вместо разборщика: {message!r}"
    )
