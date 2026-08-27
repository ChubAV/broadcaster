"""План 07-02: версия статики считается по СОДЕРЖИМОМУ охвата (FOUND-03, D-06…D-09).

Поведенческие тесты работают на ВРЕМЕННОМ каталоге и передают корень охвата
параметром: настоящий `app/static` они не читают и модульных имён не подменяют.

Утверждения формулируются сравнением ДВУХ вызовов — «до правки» и «после
правки», — а не сравнением с выписанным хешем: требование говорит о свойстве
«изменилось / не изменилось», а выписанное значение привязало бы тест к
алгоритму и краснело бы на смене алгоритма, ничего не сообщая о свойстве.

Модуль импортируется целиком (`from app.pages import common`), а не по именам:
имя, которого ещё нет, обязано ронять СВОЙ тест обращением к атрибуту, а не
сбор всего файла — иначе красная фаза неотличима от опечатки в импорте.
"""

import os
import re
from pathlib import Path

from app.pages import common

# ФОРМА ЗНАЧЕНИЯ выписана ЗДЕСЬ числом, а не собрана из
# `common.ASSET_VERSION_LEN`: тест, выводящий ожидание из проверяемого,
# согласился бы с молчаливым изменением длины дайджеста. Длина есть часть
# контракта — значение видно в каждом отрендеренном документе на шести тегах, —
# поэтому её изменение обязано быть решением, записанным в двух местах сразу.
ASSET_VERSION_RE = re.compile(r"[0-9a-f]{12}")
ASSET_VERSION_LEN_EXPECTED = 12

# Единственная деградация расчёта: и пустой охват, и ошибка чтения дают ЕЁ, а не
# хеш, посчитанный по нулю или по части файлов.
DEGRADED_VERSION = "dev"

# Подставная статика по образу настоящей: таблица стилей в одном подкаталоге,
# два вендоренных рантайма в другом.
_SEED = (
    ("css/app.css", b":root{--accent:#7c5cff}\n"),
    ("js/htmx.min.js", b"/*! htmx 2.0.10 */window.htmx={};\n"),
    ("js/alpine.min.js", b"/*! alpine 3.x */window.Alpine={};\n"),
)


def _seed_static(root: Path, order: tuple[int, ...] | None = None) -> Path:
    """Создать временный каталог статики; `order` задаёт ПОРЯДОК создания файлов."""
    items = list(_SEED)
    if order is not None:
        items = [items[index] for index in order]
    for rel, body in items:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    return root


# --- Детерминированность ------------------------------------------------------


def test_version_is_deterministic_across_calls(tmp_path):
    root = _seed_static(tmp_path / "static")

    assert common._compute_asset_version(root) == common._compute_asset_version(root)


def test_filesystem_creation_order_does_not_affect_version(tmp_path):
    # Порядок обхода файловой системы не воспроизводим между машинами, а версия
    # обязана совпадать у всех контейнеров.
    first = _seed_static(tmp_path / "first", order=(0, 1, 2))
    second = _seed_static(tmp_path / "second", order=(2, 0, 1))

    assert common._compute_asset_version(first) == common._compute_asset_version(second)


def test_scope_is_sorted_by_relative_path(tmp_path):
    root = _seed_static(tmp_path / "static", order=(2, 1, 0))

    scope = common._asset_scope(root)

    assert scope == sorted(scope)
    assert scope == ["css/app.css", "js/alpine.min.js", "js/htmx.min.js"]


# --- Содержимое охвата --------------------------------------------------------


def test_stylesheet_byte_change_changes_version(tmp_path):
    root = _seed_static(tmp_path / "static")
    before = common._compute_asset_version(root)

    path = root / "css" / "app.css"
    path.write_bytes(path.read_bytes().replace(b"7c5cff", b"7c5cfe"))

    assert common._compute_asset_version(root) != before


def test_script_byte_change_changes_version(tmp_path):
    # FOUND-03 целиком: сегодня подмена вендоренного рантайма версию не трогает,
    # и вернувшийся пользователь исполняет старый файл против нового контракта.
    root = _seed_static(tmp_path / "static")
    before = common._compute_asset_version(root)

    path = root / "js" / "htmx.min.js"
    path.write_bytes(path.read_bytes().replace(b"htmx 2.0.10", b"htmx 2.0.11"))

    assert common._compute_asset_version(root) != before


def test_rename_without_byte_change_changes_version(tmp_path):
    # Относительный путь входит в хеш: переименование меняет то, ЧТО отдаётся по
    # адресу, даже когда байты файла не тронуты.
    root = _seed_static(tmp_path / "static")
    before = common._compute_asset_version(root)

    (root / "js" / "alpine.min.js").rename(root / "js" / "alpine.bundle.js")

    assert common._compute_asset_version(root) != before


def test_fourth_script_file_changes_version(tmp_path):
    # Охват — glob, а не белый список: четвёртый вендоренный файл, привезённый
    # будущей фазой, обязан попасть в расчёт сам (D-06).
    root = _seed_static(tmp_path / "static")
    before = common._compute_asset_version(root)

    (root / "js" / "vendor.min.js").write_bytes(b"window.vendor={};\n")

    assert common._compute_asset_version(root) != before


def test_utime_only_change_keeps_version(tmp_path):
    # Два контейнера, собранные из одного дерева в разное время, обязаны отдавать
    # одинаковый `?v=`, а деплой без правок статики — не сбрасывать кеш никому (D-07).
    root = _seed_static(tmp_path / "static")
    before = common._compute_asset_version(root)
    stamp_before = (root / "css" / "app.css").stat().st_mtime

    stamp = 1_000_000_000
    for rel, _body in _SEED:
        os.utime(root / rel, (stamp, stamp))

    assert (root / "css" / "app.css").stat().st_mtime != stamp_before
    assert common._compute_asset_version(root) == before


def test_woff2_font_is_outside_scope(tmp_path):
    # У шрифтов нет тега с `?v=` — они подключаются из таблицы стилей (D-06).
    root = _seed_static(tmp_path / "static")
    before = common._compute_asset_version(root)

    fonts = root / "fonts"
    fonts.mkdir(parents=True, exist_ok=True)
    (fonts / "ibm-plex-sans-400.woff2").write_bytes(b"wOF2" + b"\x00" * 64)

    assert common._compute_asset_version(root) == before
    assert "fonts/ibm-plex-sans-400.woff2" not in common._asset_scope(root)


# --- Деградация ---------------------------------------------------------------


def test_empty_scope_degrades_to_dev(tmp_path):
    # Хеш пустого охвата стабилен и потому неотличим от исправного расчёта, а
    # означает он, что каталог статики не найден. Ветка отдельная и явная.
    empty = tmp_path / "empty"
    empty.mkdir(parents=True, exist_ok=True)
    assert common._compute_asset_version(empty) == DEGRADED_VERSION

    fonts_only = tmp_path / "fonts-only"
    (fonts_only / "fonts").mkdir(parents=True, exist_ok=True)
    (fonts_only / "fonts" / "x.woff2").write_bytes(b"wOF2")
    assert common._compute_asset_version(fonts_only) == DEGRADED_VERSION


def test_missing_root_degrades_to_dev(tmp_path):
    assert common._compute_asset_version(tmp_path / "no-such-dir") == DEGRADED_VERSION


def test_version_form_is_twelve_lowercase_hex_or_dev(tmp_path):
    root = _seed_static(tmp_path / "static")

    version = common._compute_asset_version(root)
    assert ASSET_VERSION_RE.fullmatch(version), version
    assert common.ASSET_VERSION_LEN == ASSET_VERSION_LEN_EXPECTED

    degraded = common._compute_asset_version(tmp_path / "no-such-dir")
    assert degraded == DEGRADED_VERSION
    # Деградация отличима от исправного расчёта именно тем, что форме не отвечает.
    assert not ASSET_VERSION_RE.fullmatch(degraded)


# --- D-09: инвентарный гейт состава охвата ------------------------------------
#
# Гейт работает по НАСТОЯЩЕМУ каталогу статики — в дополнение к поведенческим
# тестам выше, а не вместо них. Он закрывает два тихих отказа, которых
# поведенческий тест не видит в принципе, потому что работает на подставном
# каталоге: пустой glob (расчёт исправен, но охватывает ноль файлов, и версия
# стабильна и бессмысленна) и четвёртый вендоренный файл, появившийся мимо
# расчёта и мимо шести мест доставки версии.

STATIC_DIR = Path(__file__).resolve().parents[2] / "app" / "static"

# СОСТАВ ОХВАТА расчёта версии. Перечень выписан ЗДЕСЬ, а не собран тем же
# globом, который проверяется: тест, выводящий ожидание из проверяемого,
# согласился бы с любой правкой — и четвёртый вендоренный рантайм, привезённый
# будущей фазой мимо расчёта, был бы молча узаконен собственным гейтом.
# Изменение этого множества обязано быть решением, записанным в двух местах сразу.
#
# Летопись состава:
#   Фаза 7, планирование (2026-08-27): состав снят ПО КОДУ — ровно три файла.
#   Замена вендоренного рантайма планом 07-01 (htmx 1.9.10 → 2.0.10) этот
#   перечень НЕ меняет: меняются байты файла, а не его имя. Меняется при этом
#   ЗНАЧЕНИЕ версии — ровно то, чего требует FOUND-03, — и именно поэтому гейт
#   утверждает состав охвата, а не значение хеша.
ASSET_GLOB_FILES = {
    "css/app.css",
    "js/htmx.min.js",
    "js/alpine.min.js",
}


def test_inventory_scope_matches_declared_files():
    # Гейт зовёт ТОТ ЖЕ помощник охвата, что и расчёт: второй, независимый обход
    # разъехался бы с расчётом молча и продолжал бы утверждать состав того
    # охвата, который перестал применяться.
    scope = set(common._asset_scope(STATIC_DIR))

    unexpected = sorted(scope - ASSET_GLOB_FILES)
    missing = sorted(ASSET_GLOB_FILES - scope)
    assert scope == ASSET_GLOB_FILES, (
        f"охват расчёта версии нашёл {len(scope)}, ожидалось "
        f"{len(ASSET_GLOB_FILES)} — вендоренный файл появился мимо расчёта либо "
        f"охват опустел; незаявленные: {unexpected}, пропавшие: {missing}"
    )


def test_inventory_real_asset_version_is_not_degraded():
    # Второе, независимое от множества, доказательство непустоты охвата: пустой
    # glob на настоящем каталоге дал бы РОВНО строку деградации, и шесть тегов
    # получили бы стабильный `?v=dev`, не меняющийся ни от одной подмены.
    version = common.templates.env.globals["asset_version"]

    assert version != DEGRADED_VERSION, (
        "глобал версии равен строке деградации — охват на настоящем каталоге "
        f"пуст либо нечитаем: {sorted(common._asset_scope(STATIC_DIR))}"
    )
    assert ASSET_VERSION_RE.fullmatch(version), version
