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
# Единственный источник разметки полосы вложений (Фаза 12, план 12-01). Контракт
# скрытых полей ключей живёт ЗДЕСЬ с тех пор, как полоса выехала из страницы.
MEDIA_STRIP = TEMPLATES_DIR / "ads" / "includes" / "media_strip.html"


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
    """Клиентской сборки разметки в редакторе НЕТ ВОВСЕ (G-2 Фазы 12).

    ⚠️ УТВЕРЖДЕНИЕ ИНВЕРТИРОВАНО, А НЕ ОСЛАБЛЕНО, И ПРЕЖНЯЯ РЕДАКЦИЯ НАЗЫВАЕТСЯ,
    А НЕ СТИРАЕТСЯ. Здесь стояло «предпросмотр собирается узлами и заполняется
    присваиванием свойств» при ``createElement >= 3`` и ``replaceChildren >= 2``.
    Докстринг был неверен ФАКТИЧЕСКИ: предпросмотр — это Jinja-включение
    ``ads/includes/preview.html``, а мерило считало КЛИЕНТСКУЮ СБОРКУ ПЛИТОК
    вложений, то есть ровно то, что Фаза 12 удалила вместе с ``renderImages()``.

    Инверсия ``>= 3`` → ``== 0`` есть УСИЛЕНИЕ: прежнее правило разрешало
    строить разметку узлами, новое не разрешает строить её в этом файле НИКАК.
    Полоса вложений приезжает включаемым файлом с сервера
    (``ads/includes/media_strip.html``), и ни одного узла редактор больше не
    собирает. Соседнее ``test_ads_form_builds_dom_not_markup`` (ноль стоков,
    разбирающих строку) не тронуто и остаётся строгим.

    ``textContent`` при этом ОСТАЁТСЯ утверждением: счётчик символов — тот
    единственный клиентский кусок, который фаза не трогает, и заполняется он
    присваиванием свойству, а не разметкой. Снять это утверждение значило бы
    перестать проверять способ у единственного оставшегося писателя в DOM.
    """
    body = form_source()

    assert body.count("createElement") == 0, body.count("createElement")
    assert "textContent" in body
    assert body.count("replaceChildren") == 0, body.count("replaceChildren")


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
    """Обработчик на сервере читает форму по прежним именам полей.

    ⚠️ ПРЕДМЕТ ПЕРЕЕХАЛ, А НЕ ИСЧЕЗ (Фаза 12, план 12-03). Правило читало
    ``ads/form.html``: скрытые поля ключей вложений печатались там. Теперь их
    печатает ЕДИНСТВЕННЫЙ ИСТОЧНИК РАЗМЕТКИ ПОЛОСЫ —
    ``ads/includes/media_strip.html``, — и правило читает ЕГО. Оставленное на
    прежнем файле, оно зеленело бы на подстроке ``hidden`` из скрытого поля
    идентификатора объявления и на слове ``images`` из любого комментария, то
    есть перестало бы утверждать контракт, ничем этого не показав.
    """
    body = MEDIA_STRIP.read_text(encoding="utf-8")

    assert 'name="images"' in body
    assert 'type="hidden"' in body


def test_ads_form_carries_no_inline_handler_attribute():
    """Атрибута обработчика в редакторе нет — ни в разметке, ни в скрипте.

    ⚠️ ЭТО СИЛЬНАЯ ПОЛОВИНА СНЯТОГО ``test_ads_form_remove_handler_is_listener``,
    И ПРЕЖНЯЯ РЕДАКЦИЯ НАЗЫВАЕТСЯ, А НЕ СТИРАЕТСЯ. То правило утверждало ДВЕ
    вещи сразу: (а) перехват кнопки «×» — слушатель на созданном узле
    (``addEventListener``), (б) вызова обработчика в атрибуте разметки нет.
    Половина (а) потеряла предмет вместе с перехватом: по D-10 кнопка «×» стала
    обычной именованной кнопкой отправки формы объявления, и слушателя больше
    не существует — утверждать про него значило бы держать правило, которое
    зеленеет на ``addEventListener`` счётчика символов, то есть меряет не то.
    Половина (б) живёт СВОЕЙ жизнью и после снятия перехвата: запрет атрибута
    обработчика — свойство файла, а не свойство удаления вложения.
    """
    body = form_source()

    assert "onclick=" not in body
    assert "onclick=" not in script_source()
