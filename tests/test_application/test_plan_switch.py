"""Правило перехода между тарифами — чистая функция, без БД и без Jinja.

ПРЕДМЕТ ФАЙЛА — ТАБЛИЦА РЕШЕНИЙ И ГРАНИЦЫ. Само правило («вверх можно, вниз
нельзя, незнакомому плану ранг не угадывается») проверяется здесь построчно, без
поднятия БД и без HTTP: это ровно тот класс логики, ошибка в которой стоит денег
в обе стороны, и проверять её через страницу значило бы смешивать две причины
падения — правило и маршрут.

ЧЕГО ЗДЕСЬ НЕТ. Обе стадии применения правила живут своими файлами: гард формы —
`tests/test_pages/test_billing_payment_errors.py` (302 с названной причиной),
стадия подтверждённого платежа — там же, раздел «СТАДИЯ ПРИМЕНЕНИЯ».

ЗАЧЕМ ТЕСТ ЕДИНСТВЕННОСТИ ОБЪЯВЛЕНИЯ. План 05-11 существует потому, что копий
правила стало две: гард формы отвергал понижение, а `_apply_extension`
перезаписывал план подтверждённого платежа безусловно. Копии разъехались молча и
стоили пользователю оплаченного месяца старшего тарифа. Тест ниже держит инвариант
«объявление одно» так, чтобы вторая копия не смогла появиться незамеченной.
"""
import ast
from pathlib import Path

import pytest

from app.application.billing.plan_switch import switch_is_refused

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "application"
    / "billing"
    / "plan_switch.py"
)


# --- Таблица решений ----------------------------------------------------------


def test_renewing_the_own_plan_is_not_refused():
    """Продление СВОЕГО тарифа правилом не задевается вовсе.

    Самый вероятный способ сломать правило — отвергнуть вместе с понижением и
    продление, у которого план «уже есть». Тогда подписчик Pro не смог бы даже
    продлиться.
    """
    assert switch_is_refused("pro", "pro") is False


def test_an_upgrade_is_not_refused():
    assert switch_is_refused("basic", "pro") is False


@pytest.mark.parametrize(
    "current,target",
    [("pro", "basic"), ("basic", "free"), ("pro", "free")],
)
def test_every_downgrade_is_refused(current: str, target: str):
    """Понижение отвергается на КАЖДОЙ паре, а не только на самой заметной.

    Пары выписаны все три, потому что «вниз» бывает не только с вершины: переход
    Basic → Free сжёг бы оплаченный остаток ровно так же, как Pro → Basic.
    """
    assert switch_is_refused(current, target) is True


@pytest.mark.parametrize(
    "current,target",
    [("platinum", "basic"), ("basic", "platinum")],
)
def test_an_unranked_plan_is_refused_from_either_side(current: str, target: str):
    """ОТКАЗ ПО УМОЛЧАНИЮ: незнакомому плану ранг не угадывается.

    Перечень тарифов правится переменной окружения `PLAN_LIMITS`, а `PLAN_ORDER` —
    кодом; разойтись они могут в любую сторону. Обе догадки стоят денег: угаданное
    повышение подарило бы месяц старшего тарифа, угаданное понижение сожгло бы
    оплаченный остаток. Поэтому проверяются ОБЕ стороны — незнакомым может
    оказаться и действующий план, и покупаемый.
    """
    assert switch_is_refused(current, target) is True


# --- Границы модуля -----------------------------------------------------------


def test_the_module_carries_no_database_or_web_machinery():
    """Модуль принимает значения и возвращает значение — больше ничего.

    Проверяется по атрибутам МОДУЛЯ, а не по тексту: имя, упомянутое в
    комментарии, атрибутом не становится, а протащенная зависимость становится.
    """
    import app.application.billing.plan_switch as module

    for leaked in ("select", "AsyncSession", "Request", "templates", "db"):
        assert not hasattr(module, leaked), f"в правило протекло {leaked}"


def test_the_only_import_of_the_rule_is_the_declared_plan_order():
    """Единственная внешняя зависимость правила — `app.constants`.

    Разбор идёт по СИНТАКСИЧЕСКОМУ ДЕРЕВУ, а не поиском подстроки: предмет
    проверки — что модуль ИМПОРТИРУЕТ, а упоминание имени в докстринге импортом
    не является и ломать тест не должно.

    Инвариант держит топологию, ради которой модуль и заведён: `app/pages` уже
    импортирует `app/services`, поэтому правило обязано лежать в слое, который не
    видит ни того, ни другого — иначе обратный импорт замкнул бы цикл.
    """
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }

    assert imported == {"app.constants"}, imported


# --- Единственность объявления ------------------------------------------------


def test_both_stages_read_the_same_declaration_of_the_rule():
    """Обе стадии ссылаются на ОДИН объект функции, а не на две копии.

    Проверка по объектам модулей, а не по тексту исходника, и это существенно:
    текстовая проверка зеленела бы на второй реализации под другим именем и
    краснела бы от упоминания имени в комментарии — то есть ловила бы не то.

    Стадии две: НАМЕРЕНИЕ (`app.pages.billing` решает, продавать ли) и
    ПРИМЕНЕНИЕ (`app.services.payment_service` решает, что делать с уже
    уплаченным). Расхождение между ними и есть гэп 1 отчёта 05-VERIFICATION.md.
    """
    import app.pages.billing as intent_stage
    import app.services.payment_service as apply_stage

    assert intent_stage.switch_is_refused is switch_is_refused
    assert apply_stage.switch_is_refused is switch_is_refused

    # Ранг берётся ТОЛЬКО из объявления правила: собственного `PLAN_ORDER` у
    # потребителей нет, поэтому и сравнить ранги в обход правила им нечем.
    assert not hasattr(intent_stage, "PLAN_ORDER")
    assert not hasattr(apply_stage, "PLAN_ORDER")
