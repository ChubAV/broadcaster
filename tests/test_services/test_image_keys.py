"""Ключ миниатюры выводится из проверенного ключа и хранимым НЕ становится.

Задача issue #40 добавляет второй объект на каждую загрузку. Опасность у этого
добавления одна и названа прямо: если производный ключ окажется неотличим от
ключа вложения, его можно будет подсунуть в ``Ad.images`` — а туда попадает
всё, что проходит ``own_image_keys``. Поэтому запрет проверяется РЕГРЕССИЕЙ, а
не рассуждением о выбранной приставке.
"""

import pytest
from fastapi import HTTPException

from app.services.image_keys import THUMB_KEY_PREFIX, own_image_keys, thumb_key

VALID_KEY = "7/" + "a" * 32 + "_photo.jpg"


def test_thumb_key_prefixes_the_stored_key():
    assert thumb_key(VALID_KEY) == f"{THUMB_KEY_PREFIX}{VALID_KEY}"


def test_thumb_key_is_idempotent():
    """Повторное применение ключ не удлиняет.

    Иначе двойной вызов — в шаблоне и в маршруте — молча увёл бы адрес на
    несуществующий объект, и интерфейс показал бы пустую плитку вместо
    картинки.
    """
    once = thumb_key(VALID_KEY)

    assert thumb_key(once) == once


def test_thumb_key_of_empty_value_is_empty():
    """Пустое значение остаётся пустым, а не превращается в адрес приставки."""
    assert thumb_key("") == ""


def test_a_thumbnail_key_is_not_a_storable_attachment():
    """T-Q40-04: производный ключ ``own_image_keys`` ОТВЕРГАЕТ.

    Это главный инвариант границы задачи. Образец хранимого ключа требует, чтобы
    до первого слэша стояли только цифры; приставка ``thumbs/`` этому не
    отвечает, и выбрана она именно поэтому. Утверждение снимается с
    ``own_image_keys``, а не с регулярного выражения: правило владения — одно на
    оба входа, и меряться должно то, через что проходят данные.
    """
    with pytest.raises(HTTPException) as exc_info:
        own_image_keys([thumb_key(VALID_KEY)], user_id=7, max_images=10)

    assert exc_info.value.status_code == 400


def test_the_source_key_is_still_accepted():
    """Парный тест: без него предыдущий зеленел бы при отказе ЛЮБОМУ ключу."""
    assert own_image_keys([VALID_KEY], user_id=7, max_images=10) == [VALID_KEY]
