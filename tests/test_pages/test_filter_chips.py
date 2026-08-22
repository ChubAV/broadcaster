"""Компонент чипсов-фильтров: переносимость и обязательность базового адреса.

Файл заведён планом 06-03 вместе с переездом макроса из каталога включений
раздела истории в библиотеку компонентов.

ПОЧЕМУ ОТДЕЛЬНЫЙ ФАЙЛ, А НЕ ПАРА УТВЕРЖДЕНИЙ В ТЕСТАХ ИСТОРИИ. До этого плана
макрос проверялся ТОЛЬКО косвенно — через разметку раздела истории, то есть
через единственного своего потребителя. Ровно поэтому привязка к одному разделу
(умолчание базового адреса `/history`) дожила незамеченной до третьего
потребителя: тест, который рендерит историю, на «историю» в адресе чипса и
рассчитывает, и подменить его нечем. Здесь макрос рендерится напрямую и с
ЧУЖИМ базовым адресом — тем самым проверяется свойство компонента, а не
разметка одного экрана.
"""

from pathlib import Path

import pytest
from jinja2 import UndefinedError

from app.pages.common import templates

TEMPLATES_DIR = Path(templates.env.loader.searchpath[0])

COMPONENT = "components/filter_chips.html"
OLD_PATH = "history/includes/filter_chips.html"

# Набор оси в той же форме, в какой его объявляет обработчик раздела
# (app/pages/history.py): пустое значение — вариант «все».
STATUS_OPTIONS = [("", "Все"), ("ok", "Успешно"), ("failed", "Ошибка")]

# ЧУЖОЙ раздел: любой, кроме истории. Взят действующий адрес подраздела
# админ-панели — тот самый потребитель, ради которого переезд и состоялся.
FOREIGN_PATH = "/admin/logs"


def _chips(**kwargs) -> str:
    """Рендер макроса напрямую окружением Jinja приложения."""
    macro = templates.env.get_template(COMPONENT).module.filter_chips
    return str(macro(**kwargs))


def _hrefs(html: str) -> list[str]:
    """Адреса всех чипсов группы в порядке отрисовки."""
    import re

    return re.findall(r'href="([^"]*)"', html)


def test_macro_serves_a_foreign_section():
    """Базовый адрес чужого раздела — и ссылки ведут ТУДА, а не в историю.

    Несущее свойство переезда. До плана 06-03 базовый адрес имел умолчание
    `/history`, и импорт макроса в админку дал бы 200, верную разметку и чипсы,
    уводящие администратора из своего подраздела при каждом клике.
    """
    html = _chips(
        options=STATUS_OPTIONS,
        active="ok",
        base_params={},
        param_name="status",
        base_path=FOREIGN_PATH,
    )

    hrefs = _hrefs(html)
    assert len(hrefs) == len(STATUS_OPTIONS)
    assert all(href.startswith(FOREIGN_PATH) for href in hrefs), hrefs
    # Раздела истории в разметке нет НИ В КАКОМ виде: ни базой адреса, ни
    # остатком умолчания в одном из чипсов.
    assert "/history" not in html


def test_active_value_is_marked_exactly_once():
    """Активен ровно один чипс группы — тот, чьё значение совпало с текущим."""
    html = _chips(
        options=STATUS_OPTIONS,
        active="failed",
        base_params={"status": "failed"},
        param_name="status",
        base_path=FOREIGN_PATH,
    )

    assert html.count("chip--on") == 1
    assert html.count('aria-current="true"') == 1
    # И это именно «Ошибка», а не первый попавшийся чипс.
    marked = [chunk for chunk in html.split("<a ") if "chip--on" in chunk]
    assert len(marked) == 1
    assert 'data-chip="failed"' in marked[0]


def test_active_all_marks_the_empty_option():
    """Отсутствие значения оси делает активным вариант «все».

    None и пустая строка обязаны означать одно и то же: адрес без ключа и
    адрес с пустым ключом — это один и тот же экран.
    """
    for active in (None, ""):
        html = _chips(
            options=STATUS_OPTIONS,
            active=active,
            base_params={},
            param_name="status",
            base_path=FOREIGN_PATH,
        )
        marked = [chunk for chunk in html.split("<a ") if "chip--on" in chunk]
        assert len(marked) == 1, active
        assert 'data-chip=""' in marked[0], active


def test_other_filters_survive_switching_one_axis():
    """Смена ОДНОЙ оси переносит прочие фильтры и убирает пустой ключ.

    Потеря соседнего фильтра — не косметика: нажатие на статус молча вернуло бы
    в выдачу записи, отфильтрованные каналом, и экран об этом не сказал бы
    ничего. Пустое значение свой ключ УБИРАЕТ, а не пишет пустым: `?status=` и
    отсутствие ключа обязаны означать одно и то же.
    """
    html = _chips(
        options=STATUS_OPTIONS,
        active="ok",
        base_params={"status": "ok", "messenger": "telegram", "period": "7d"},
        param_name="status",
        base_path=FOREIGN_PATH,
    )

    by_value = dict(zip([value for value, _ in STATUS_OPTIONS], _hrefs(html)))

    # Смена значения оси: соседние фильтры на месте, своё значение — новое.
    assert "messenger=telegram" in by_value["failed"]
    assert "period=7d" in by_value["failed"]
    assert "status=failed" in by_value["failed"]
    assert "status=ok" not in by_value["failed"]

    # Вариант «все»: соседние фильтры на месте, свой ключ ИСЧЕЗ целиком.
    assert "messenger=telegram" in by_value[""]
    assert "period=7d" in by_value[""]
    assert "status=" not in by_value[""]


def test_missing_base_path_raises():
    """Забытый базовый адрес падает на рендере, а не строит ссылку в никуда.

    Обязательность параметра проверяется, а не декларируется докстрингом.
    Забытый аргумент в Jinja — не ошибка, а Undefined, и в атрибут href он
    печатается ПУСТОЙ строкой: чипс, ведущий на текущий адрес и молча ничего не
    фильтрующий. Ровно этот исход макрос и обязан превращать в громкую ошибку.
    """
    with pytest.raises(UndefinedError) as excinfo:
        _chips(
            options=STATUS_OPTIONS,
            active="ok",
            base_params={},
            param_name="status",
        )

    assert "base_path" in str(excinfo.value)


def test_no_template_imports_the_old_path():
    """Старого пути импорта нет ни в одном шаблоне проекта.

    Страховочная сетка против возврата, а не повтор проверки переезда: там
    утверждение сделано разово по факту, здесь оно постоянное. Обход идёт по
    ВСЕМУ дереву шаблонов — файл, воскресивший старый путь, поймается, в каком
    бы разделе он ни лежал.
    """
    offenders = [
        str(path.relative_to(TEMPLATES_DIR))
        for path in sorted(TEMPLATES_DIR.rglob("*.html"))
        if OLD_PATH in path.read_text(encoding="utf-8")
    ]

    assert not offenders, f"шаблоны со старым путём импорта чипсов: {offenders}"
    assert (TEMPLATES_DIR / COMPONENT).exists()
