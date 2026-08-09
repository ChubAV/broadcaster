"""Wave 0: UI-04 — прямой рендер макросов библиотеки компонентов без HTTP.

В проекте до этого не было ни одного теста, рендерящего шаблон напрямую.
Паттерн вводится здесь: берём окружение Jinja из ``app.pages.common`` и
вызываем ``get_template(...).module.<macro>(...)``.

Почему именно так, а не через страницу: макрос, случайно взявший данные из
контекста вызывающего шаблона, отрендерится ПУСТОЙ строкой, а страница всё
равно вернёт 200. Прямой рендер с пустым контекстом ловит это сразу.
"""

from pathlib import Path

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
# Массовое удаление групп — единственное подтверждение в проекте, где удаляется
# не одна сущность по идентификатору в маршруте, а НАБОР, приходящий полями
# формы (app/pages/groups.py: form.get("action") + form.getlist("group_ids")).
# Без слота такое подтверждение пришлось бы собирать отдельной разметкой в обход
# библиотеки.

HIDDEN_FIELD = '<input type="hidden" name="action" value="delete">'


def _modal_block(fields: str = HIDDEN_FIELD, body: str | None = None) -> str:
    """Отрендерить модалку блочным вызовом с произвольными полями формы."""
    body_arg = f", body={body!r}" if body is not None else ""
    return ENV.from_string(
        "{% from 'components/modal.html' import modal %}"
        "{% call modal(id='del-bulk', title='Удалить выбранные группы?',"
        " action='/groups/bulk', confirm_label='Удалить'" + body_arg + ") %}"
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
    assert 'action="/groups/bulk"' in form


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
