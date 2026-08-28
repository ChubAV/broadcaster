"""Гейты ЗАКРЫТОГО РЕЕСТРА УВЕДОМЛЕНИЙ (FOUND-05, D-10, D-11).

ПОЧЕМУ ЭТОТ ФАЙЛ ЖИВЁТ В ``tests/test_pages/``, А НЕ В ``tests/test_templates/``.
Предмет проверки — множество на Python, а не разметка. Каноническое деление уже
записано в ``tests/test_templates/test_htmx_inventory.py``: гейты РАЗМЕТКИ
читают шаблоны и живут там, гейты МНОЖЕСТВ по Python-коду живут рядом с
``test_access_gate.py`` и ``test_impersonation_gate.py``. Реестр уведомлений —
второе.

ПОЧЕМУ ФАЙЛ НЕ ИМПОРТИРУЕТ НИ ОДНОГО МОДУЛЯ ПРИЛОЖЕНИЯ, КРОМЕ ПРОВЕРЯЕМОГО.
Довод дословно наследуется у ``test_impersonation_gate.py``: тест, выводящий
ожидание из проверяемого, согласился бы с любой правкой. Тексты и перечень
кодов выписаны ЗДЕСЬ литералами, и именно поэтому расхождение видно. Взять
ожидаемый текст из модуля-источника значило бы сравнить копию с самой собой.
"""

import re

import pytest

from app.pages import notices

# Варианты, которые понимает макрос ``app/templates/components/alert.html``:
# из варианта он выводит и класс, и ``role``. Пятый вариант не отрисуется
# ничем — плашка получила бы класс, которого нет в стилях, и молча потеряла
# бы вид.
ALERT_VARIANTS = frozenset({"success", "warning", "error", "info"})

# Форма кода — плоское ``snake_case`` (D-10). Точка или заглавная буква
# означали бы новое пространство имён, а его решение фазы не заводило.
CODE_FORM = re.compile(r"^[a-z][a-z0-9_]*$")

# Сегодняшний текст исхода «повтор поставлен в очередь», выписанный копией.
# Посимвольное равенство с записью реестра — это и есть утверждение о том, что
# консолидация ПЕРЕНЕСЛА текст, а не переписала его.
RETRY_QUEUED_TEXT = (
    "Повтор поставлен в очередь. Уйдёт ТЕКУЩЕЕ содержимое объявления, "
    "а не то, что показано в записи."
)


def test_a_moved_record_carries_its_text_and_variant_unchanged() -> None:
    """Запись повтора приезжает по коду с тем же текстом и тем же вариантом."""
    record = notices.notice_for("retry_queued")

    assert record is not None, "код `retry_queued` в реестре отсутствует"
    assert record.text == RETRY_QUEUED_TEXT, (
        "текст записи `retry_queued` разошёлся с сегодняшним: консолидация "
        "переписала формулировку вместо переноса"
    )
    assert record.variant == "success", (
        "вариант записи `retry_queued` сменился — плашка сменит и цвет, и "
        "`role`, который макрос выводит из варианта"
    )


def test_an_unknown_value_draws_nothing_at_all() -> None:
    """Неизвестное значение не выбирает НИЧЕГО — ни текста, ни пустой рамки.

    ⚠️ ЭТО ГЛАВНОЕ СВОЙСТВО ЗАКРЫТОГО МНОЖЕСТВА. Значение приходит из адресной
    строки, то есть от владельца ссылки, в том числе с чужого сайта. Плашка по
    любому непустому значению позволила бы нарисовать пользователю сообщение о
    событии, которого не было, от имени приложения.
    """
    assert notices.notice_for("нет-такого-кода") is None
    assert notices.notice_for("") is None
    assert notices.notice_for(None) is None

    assert notices.has_code("нет-такого-кода") is False
    assert notices.has_code("") is False
    assert notices.has_code(None) is False


def test_the_access_redirect_flag_is_not_a_code() -> None:
    """Признак закрытого доступа кодом уведомления НЕ является (D-11).

    Состояние доступа сервер знает из строки подписки. Свернуть признак в
    реестр значило бы отдать вопрос «закрыт ли доступ» владельцу ссылки:
    достаточно было бы прислать человеку адрес, и он увидел бы плашку об
    отказе, которого не было. Признак остаётся артефактом редиректа гейта
    доступа и в реестр не входит никогда.
    """
    assert notices.notice_for("expired") is None
    assert notices.has_code("expired") is False


def test_every_code_is_distinct_and_the_index_loses_nothing() -> None:
    """Четырнадцать записей дают четырнадцать ключей — ни одна не потерялась.

    Неравенство здесь означало бы молчаливую перезапись: две записи с одним
    кодом схлопнулись бы в одну, и решение о второй не принимал бы никто.
    """
    codes = [record.code for record in notices.NOTICES]

    assert len(codes) == 14, f"записей в реестре {len(codes)}, ожидалось 14"
    assert len(set(codes)) == 14, (
        "коды записей не различны: "
        + ", ".join(sorted({code for code in codes if codes.count(code) > 1}))
    )
    assert len(notices.NOTICES) == len(notices._BY_CODE), (
        "число записей не равно числу ключей отображения — сборка потеряла "
        "запись по дороге"
    )


def test_every_code_keeps_the_flat_snake_case_form() -> None:
    """Каждый код — плоское ``snake_case`` без точек и разделов (D-10)."""
    wrong = [
        record.code for record in notices.NOTICES if not CODE_FORM.match(record.code)
    ]

    assert not wrong, f"коды нарушают форму `snake_case`: {wrong}"


def test_every_variant_is_one_the_alert_macro_understands() -> None:
    """Вариант каждой записи знаком макросу плашки.

    Незнакомый вариант не уронил бы ничего: плашка получила бы класс, которого
    нет в стилях, и ``role="status"`` вместо ``role="alert"``. То есть отказ
    выглядел бы обычным сообщением и не был бы объявлен вспомогательным
    технологиям настойчиво.
    """
    wrong = {
        record.code: record.variant
        for record in notices.NOTICES
        if record.variant not in ALERT_VARIANTS
    }

    assert not wrong, (
        f"варианты вне множества {sorted(ALERT_VARIANTS)}: {wrong} — макрос "
        "`components/alert.html` выводит из варианта и класс, и `role`"
    )


def test_the_registry_is_a_pure_function_of_the_code() -> None:
    """Второй вызов равен первому, и содержимое реестра между ними то же.

    Реестр собирается на импорте модуля и состояния не хранит. Утверждение
    закрывает форму, при которой запись выдавалась бы «один раз» или помечалась
    показанной: параллельные запросы читают одну и ту же таблицу и изменить её
    не могут.
    """
    before = dict(notices._BY_CODE)

    first = notices.notice_for("payment_pending")
    second = notices.notice_for("payment_pending")

    assert first is not None
    assert first == second, "два вызова с одним кодом дали разные записи"
    assert dict(notices._BY_CODE) == before, (
        "содержимое реестра изменилось между вызовами — чтение оказалось "
        "записью"
    )


# =============================================================================
# КОНТРОЛИ: доказательство того, что гейт КРАСНЕЕТ (`-k control`)
#
# ⚠️ ЗАЧЕМ ОНИ, ЕСЛИ ВЫШЕ УЖЕ ЕСТЬ УТВЕРЖДЕНИЯ. Утверждения выше говорят
# «сегодня всё сходится»; контроли ниже говорят «а когда перестанет — я это
# увижу». Это разные высказывания, и второе не следует из первого. Довод и
# форма наследуются у `test_impersonation_gate.py`.
# =============================================================================


def test_control_negative_a_duplicate_code_reddens_the_builder() -> None:
    """Сборщику подан кортеж с повторённым кодом — сборка обязана упасть.

    ⚠️ ИМЕННО РАДИ ЭТОГО РЕЕСТР СОБИРАЕТСЯ ИЗ ПАР, А НЕ ЛИТЕРАЛОМ СЛОВАРЯ.
    Литерал словаря Python при дубле ключа МОЛЧА перезаписывает первую запись:
    исход, о котором пользователю сообщали, исчез бы вместе со своим текстом, и
    ни один тест этого бы не заметил.
    """
    duplicated = (
        notices.Notice("same_code", "первый текст", "info"),
        notices.Notice("same_code", "второй текст", "error"),
    )

    with pytest.raises(ValueError) as failure:
        notices._index(duplicated)

    assert "same_code" in str(failure.value), (
        "сборка упала, но не назвала повторившийся код — читатель отказа не "
        "узнает, какую запись искать"
    )
