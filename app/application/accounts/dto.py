from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class AccountInfo:
    id: int
    type: str
    status: str
    created_at: datetime


@dataclass(slots=True)
class SyncStatusView:
    """Состояние синхронизации аккаунта для ответа опроса статуса.

    Числа групп здесь НЕТ намеренно. Оно уже приходит в блок статуса вместе с
    остальной статистикой строки (`_get_account_stats` кладёт `groups_count`
    для КАЖДОГО запрошенного аккаунта), поэтому второе поле было недостижимым
    запасным вариантом — и ради него на каждый ответ опроса, то есть раз в пять
    секунд на вкладку, выполнялся отдельный `SELECT` по группам с подсчётом
    длины в Python.

    Номер (`phone`) здесь, наоборот, ЕСТЬ: фрагмент опроса приходит голым
    идентификатором и типом, объекта аккаунта у него нет, а подпись «Номер» на
    карточке нужна и после подмены (Фаза 17, D-18). Он берётся у уже загруженного
    объекта аккаунта и запроса не прибавляет; признак двойника считает
    обработчик по строкам пользователя, а не это поле.
    """

    status: str
    messenger_type: str | None = None
    phone: str | None = None


@dataclass(slots=True)
class GroupResyncResult:
    """Счётчики одной переинвентаризации состава групп аккаунта (D-09).

    По ним строится сводка синка «найдено N, новых M, обновлено имён K».

    Поле называется `created`, а не `new`: `new` в Python занято иным смыслом.
    В JSON-строке `last_sync_result` тот же счётчик называется `new` — так его
    читает сводка UI-SPEC; расхождение имён намеренное и локализовано в
    `group_resync.apply_group_resync`.
    """

    found: int
    created: int
    renamed: int
    missing: int
    error: str | None = None

