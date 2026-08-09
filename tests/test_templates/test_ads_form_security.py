"""CR-01: сток разметки в редакторе объявления закрыт.

Проверяется ИСХОДНИК ``app/templates/ads/form.html``, а не отрендеренная
страница. Причина — WR-06: страница отдаёт 500 в тестовой среде, потому что
шаблонные глобалы адреса хранилища собирают настройки в обход подмены
зависимостей; дефект отложен в Фазу 2 (ADS-07). Ждать HTTP-покрытия, чтобы
закрепить уязвимость severity high, значит оставить её незакреплённой.

Почему проверка исходника здесь осмысленна, а не суррогат: уязвимость —
свойство СПОСОБА СБОРКИ, а не конкретного значения. Значение из ненадёжного
источника, присвоенное свойству узла, парсером разметки не разбирается никогда;
то же значение, попавшее в строку разметки, разбирается всегда. Отсутствие
строковой сборки в файле — и есть проверяемое утверждение.

Стиль проверок исходника шаблона взят из ``test_components.py``
(``TEMPLATES_DIR``, чтение файла, ``test_no_unsafe_escaping``).
"""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "app" / "templates"
ADS_FORM = TEMPLATES_DIR / "ads" / "form.html"


def form_source() -> str:
    return ADS_FORM.read_text(encoding="utf-8")


def script_source() -> str:
    """Содержимое блоков ``<script>`` шаблона формы объявления."""
    body = form_source()
    blocks = []
    cursor = 0
    while True:
        start = body.find("<script", cursor)
        if start == -1:
            break
        open_end = body.find(">", start)
        end = body.find("</script>", open_end)
        assert end != -1, "незакрытый блок скрипта в ads/form.html"
        blocks.append(body[open_end + 1 : end])
        cursor = end
    assert blocks, "в ads/form.html не найдено ни одного блока скрипта"
    return "\n".join(blocks)


# --- сток разметки -----------------------------------------------------------

MARKUP_SINKS = ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write")


def test_ads_form_builds_dom_not_markup():
    """Ни одного стока, разбирающего строку парсером разметки."""
    body = form_source()
    offenders = [sink for sink in MARKUP_SINKS if sink in body]

    assert not offenders, offenders


def test_ads_form_uses_property_assignment():
    """Предпросмотр собирается узлами и заполняется присваиванием свойств."""
    body = form_source()

    assert body.count("createElement") >= 3, body.count("createElement")
    assert "textContent" in body
    assert body.count("replaceChildren") >= 2, body.count("replaceChildren")


def test_ads_form_has_no_template_literal_markup():
    """В блоке скрипта нет шаблонных строк, собирающих разметку."""
    offenders = [
        line.strip()
        for line in script_source().splitlines()
        if "`" in line and "<" in line
    ]

    assert not offenders, offenders


# --- контракт формы, который правка не имеет права сломать --------------------


def test_ads_form_hidden_input_contract_kept():
    """Обработчик на сервере читает форму по прежним именам полей."""
    body = form_source()

    assert "images" in body
    assert "hidden" in body


def test_ads_form_remove_handler_is_listener():
    """Обработчик удаления — слушатель на созданном узле, а не строка атрибута."""
    body = form_source()

    assert "addEventListener" in body
    assert 'onclick="removeImage' not in body
    assert "onclick='removeImage" not in body
    assert "onclick=" not in script_source()
