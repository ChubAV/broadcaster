"""Потолок тела запроса обратного прокси держится в step с потолком вложений.

ПРЕДМЕТ. После Фазы 12 партия вложений едет ОДНИМ составным запросом, а не
запросом на файл. Единственная рантайм-система, всё ещё настроенная на прежнее
поведение «один файл за раз», — это обратный прокси: его предел тела задаётся
шаблонами ``nginx/*.conf.template`` и к выкладке кода отношения не имеет. Его
расхождение с приложением не видит НИ ОДИН другой тест суиты, потому что ни
один не читает ``nginx/`` — и покраснеть тут больше негде.

ЦЕНА РАСХОЖДЕНИЯ НАЗВАНА ВЕЛИЧИНОЙ, А НЕ «НАСТРОЙКОЙ». Потолок ниже
произведения ``max_images_per_ad × max_image_size_mb`` означает 413 от прокси
ДО приложения. 413 есть 4xx, а на 4xx рантайм разметки подмены не делает
вовсе: человек получает общую плашку «Действие не выполнено» вместо причины и
теряет вместе с партией даже те файлы, которые прошли бы поодиночке.

ГРАНИЦА ПРАВИЛА, НАЗВАННАЯ ПРЯМО. Разбор идёт по ИСХОДНИКУ шаблона, а не по
собранному конфигу: nginx в среде разработки отсутствует (§Environment
Availability разведки Фазы 12), и собирать нечего. Отсюда то, чего правило НЕ
доказывает:

* что боевой nginx ПЕРЕЗАПУЩЕН с новым значением — правка шаблона в гите сама
  по себе боевой предел не двигает; это предмет ручного обхода фазы;
* что nginx примет этот синтаксис — синтаксической проверки конфига здесь нет;
* что значение достаточно для будущих полей формы — считается ровно то, что
  названо формулой.

ОЖИДАНИЕ БЕРЁТСЯ ИЗ ``Settings``, А НЕ ИЗ ЛИТЕРАЛА. Тест на литерале сравнивал
бы конфиг сам с собой и остался бы зелёным ровно тогда, когда значения
разъехались. Приём взят у
``tests/test_routes/test_uploads.py::test_supported_formats_and_refusal_text_stay_in_step``.

Форма модуля — ``tests/test_services/test_image_keys.py``: ни одной клиентской
фикстуры, чистые утверждения. Чтение файла дерева — как в
``tests/test_templates/test_ads_form_security.py`` (корень от собственного пути,
``read_text(encoding="utf-8")``).
"""

import re
from pathlib import Path

from app.config import Settings

REPO_ROOT = Path(__file__).resolve().parents[1]

# Оба шаблона в периметре правила. Ключ — путь, который человек прочитает в
# тексте отказа: отказ обязан называть ФАЙЛ, иначе на две копии правила одна
# формулировка, и искать придётся руками.
TEMPLATES = {
    "nginx/nginx.conf.template": REPO_ROOT / "nginx" / "nginx.conf.template",
    "nginx/nginx-http.conf.template": REPO_ROOT / "nginx" / "nginx-http.conf.template",
}

MEGABYTE = 1024 * 1024

# Суффиксы nginx: их разбор — не украшение. Значение, записанное килобайтами,
# без разбора суффикса сравнивалось бы как мегабайты и зеленело бы на пределе
# в тысячу раз меньше нужного.
_SUFFIX_BYTES = {
    "": 1,
    "k": 1024,
    "m": MEGABYTE,
    "g": 1024 * MEGABYTE,
}

_BODY_LIMIT = re.compile(r"client_max_body_size\s+(\d+)([kKmMgG]?)\s*;")


def _template_source(name: str) -> str:
    return TEMPLATES[name].read_text(encoding="utf-8")


def _without_comments(source: str) -> str:
    """Исходник без строк-комментариев.

    Закомментированная директива предела не задаёт, а совпадению регулярного
    выражения неотличима от действующей. Без этого отбрасывания правило
    зеленело бы на шаблоне, где живое значение снято, а его след остался
    строкой пояснения.
    """
    return "\n".join(
        line for line in source.splitlines() if not line.lstrip().startswith("#")
    )


def _declared_ceilings(source: str) -> list[int]:
    """Все ДЕЙСТВУЮЩИЕ потолки исходника, в байтах, в порядке объявления."""
    return [
        int(number) * _SUFFIX_BYTES[suffix.lower()]
        for number, suffix in _BODY_LIMIT.findall(_without_comments(source))
    ]


def _application_ceiling_bytes() -> int:
    """Потолок приложения — произведение тех же полей, что читает загрузка.

    ``_env_file=None`` и два обязательных поля — та же защита, что в
    ``tests/conftest.py``: боевой ``.env`` разработчика в тест протекать не
    должен, иначе правило меряло бы чужую машину. Сверяются УМОЛЧАНИЯ,
    отгруженные вместе с шаблонами, — то есть ровно та пара величин, из которой
    выведена записанная в шаблонах формула.
    """
    settings = Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test-secret-key",
    )
    return settings.max_images_per_ad * settings.max_image_size_mb * MEGABYTE


def _body_ceiling_violations(sources: dict[str, str]) -> list[str]:
    """Перечень нарушений правила. Пустой список — правило соблюдено.

    Собран отдельной функцией НАД исходниками, а не над файлами дерева, ровно
    затем, чтобы у правила был контроль зубов: подделанный В ПАМЯТИ исходник
    проходит через тот же код, что и настоящий.
    """
    expected = _application_ceiling_bytes()
    violations: list[str] = []
    ceilings: dict[str, int] = {}

    for name, source in sources.items():
        declared = _declared_ceilings(source)
        if len(declared) != 1:
            violations.append(
                f"{name}: объявлений потолка тела запроса {len(declared)}, а нужно ровно одно"
            )
            continue
        ceilings[name] = declared[0]
        if declared[0] < expected:
            violations.append(
                f"{name}: потолок прокси {declared[0] // MEGABYTE} МБ МЕНЬШЕ "
                f"потолка приложения {expected // MEGABYTE} МБ"
            )

    if len(set(ceilings.values())) > 1:
        violations.append(
            "шаблоны объявляют РАЗНЫЕ потолки: "
            + ", ".join(f"{name} = {value // MEGABYTE} МБ" for name, value in ceilings.items())
        )

    return violations


def test_both_nginx_templates_declare_a_body_ceiling():
    """Оба шаблона объявляют предел тела запроса ровно один раз.

    Ноль объявлений в любом из двух — красный: HTTP-шаблон поднимается
    контейнером, когда сертификата нет, и молчаливое умолчание nginx в этом
    дереве НЕ ИЗМЕРЕНО (запись A1 разведки). Больше одного — тоже красный:
    какое из двух действует, читается порядком вложенности блоков, а не
    файлом.
    """
    for name in TEMPLATES:
        declared = _declared_ceilings(_template_source(name))

        assert len(declared) == 1, (
            f"{name} объявляет потолок тела запроса {len(declared)} раз(а), а нужно "
            "ровно один: без директивы действует неизмеренное умолчание nginx, "
            "а при двух — неочевидная из файла"
        )


def test_the_proxy_ceiling_covers_the_application_ceiling():
    """Потолок прокси НЕ МЕНЬШЕ произведения настроек приложения.

    Утверждение идёт на произведение из ``Settings``, а не на записанное в
    шаблоне число: поднявший ``max_images_per_ad`` или ``max_image_size_mb`` и
    забывший прокси узнаёт об этом здесь, а не из журнала боевого nginx.
    """
    expected = _application_ceiling_bytes()

    for name in TEMPLATES:
        declared = _declared_ceilings(_template_source(name))
        assert declared, f"{name} не объявляет потолок тела запроса вовсе"

        assert declared[0] >= expected, (
            f"{name}: потолок прокси {declared[0] // MEGABYTE} МБ меньше потолка "
            f"приложения {expected // MEGABYTE} МБ "
            "(max_images_per_ad × max_image_size_mb). Партия вложений получит 413 "
            "ДО приложения, своп на 4xx не происходит, и человек увидит общую "
            "плашку вместо причины, потеряв даже те файлы, что прошли бы поодиночке"
        )


def test_both_templates_declare_the_same_ceiling():
    """Два шаблона объявляют ОДНО значение.

    Расхождение означало бы, что по HTTP и по HTTPS продукт ведёт себя
    по-разному — а узнаётся такое только на стенде, и только тем, кто попал на
    шаблон без сертификата.
    """
    declared = {name: _declared_ceilings(_template_source(name)) for name in TEMPLATES}
    values = {name: found[0] for name, found in declared.items() if len(found) == 1}

    assert len(values) == len(TEMPLATES), (
        f"не у всех шаблонов ровно одно объявление: { {k: len(v) for k, v in declared.items()} }"
    )
    assert len(set(values.values())) == 1, (
        "шаблоны объявляют разные потолки тела запроса — "
        + ", ".join(f"{name} = {value // MEGABYTE} МБ" for name, value in values.items())
        + "; по HTTP и по HTTPS партия вела бы себя по-разному"
    )


def test_a_lowered_ceiling_reddens_the_rule():
    """Контроль зубов: понижённое значение правило ОБЯЗАНО найти.

    Понижение делается в копии исходника В ПАМЯТИ; файл дерева не правится — и
    это проверяется здесь же, а не оставляется на честное слово.

    ⚠️ Подстановка сперва ДОКАЗЫВАЕТСЯ, а потом используется. Замена, которая
    ничего не заменила, оставила бы исходник целым, правило — зелёным, и тест
    зеленел бы ВАКУУМОМ, объявляя проверенным то, что не исполнялось ни разу.
    """
    name = "nginx/nginx.conf.template"
    original = _template_source(name)

    lowered, replacements = _BODY_LIMIT.subn("client_max_body_size 1M;", original)
    assert replacements == 1, (
        f"подстановка заменила {replacements} вхождений вместо одного: контроль "
        "зубов проверял бы нетронутый исходник и зеленел бы ни на чём"
    )
    assert lowered != original, "понижённая копия совпала с исходником"

    violations = _body_ceiling_violations({name: lowered})

    assert violations, (
        "правило не нашло нарушения на потолке в 1 МБ против потолка приложения "
        f"{_application_ceiling_bytes() // MEGABYTE} МБ — значит оно зелено не "
        "потому, что шаблоны верны, а потому, что ничего не проверяет"
    )
    assert any(name in message for message in violations), (
        f"отказ не называет файл: {violations}"
    )
    assert _template_source(name) == original, (
        "файл дерева изменился: контроль зубов обязан жить в памяти"
    )
