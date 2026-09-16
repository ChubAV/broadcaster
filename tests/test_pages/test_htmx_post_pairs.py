"""ПАРЫ ТРАНСПОРТОВ ПЕРЕВЕДЁННЫХ POST-ОБРАБОТЧИКОВ СТРАНИЧНОГО СЛОЯ (GATE-02, D-14).

ПОЧЕМУ ОДИН МОДУЛЬ. Критерий 4 роадмапа Фазы 11 требует пар «без htmx / с htmx»
на каждом переведённом обработчике — и прямо запрещает размножать их в «320
функций» (D-14). Функция-двойник на каждое утверждение 302 молчала бы о
следующем переведённом обработчике: своей функции у него ещё нет, и уронить
нечего. Параметризованный реестр плюс ЗАМЫКАНИЕ над множеством переведённых
превращают это молчание в красное: обработчик, пошедший через `respond()`, но не
получивший ни одного случая, называется поимённо.

ПРОЧТЕНИЕ КРИТЕРИЯ 4 (D-14). Вторая половина пары утверждает «путь htmx не
получает ни полного документа, ни перенаправления»:

| Ветка | Ответ на транспорте htmx |
|---|---|
| `FRAGMENT` — действие оставляет экран | 200, фрагмент несёт свою метку, `<!DOCTYPE` нет |
| `LOCATION` — действие уводит с экрана | 204, `HX-Location` посимвольно равен адресу 302, тела нет |
| `EXTERNAL` — переход на чужой сайт | 204, `HX-Redirect`, тела нет (первый случай — план 11-15) |

Буквальное «с заголовком → 200 для всех» отвергнуто: оно противоречит
отгруженной ветке перехода Фазы 8.

⚠️ СУЩЕСТВУЮЩИЕ УТВЕРЖДЕНИЯ 302 СУИТЫ НЕ ТРОГАЮТСЯ. Они остаются в своих файлах
и продолжают стеречь путь деградации; этот модуль добавляет к ним ВТОРУЮ
половину, а не переписывает первую. Обход, сличающий каждое такое утверждение с
парой, — предмет плана 11-20.

⚠️ ОБЕ ПОЛОВИНЫ НА СВЕЖЕМ СОСТОЯНИИ. Правка меняет строку; вторая половина,
пришедшая на уже изменённое состояние, проверяла бы не тот исход, который
названа проверять. Поэтому `arrange` зовётся дважды.

⚠️ ФИКСТУРА `htmx_client` ЗДЕСЬ НЕ ЗАПРАШИВАЕТСЯ — по основанию, записанному в
шапке `test_confirm_delete_transport.py`: она метит ОБЩИЙ объект клиента, и
половина деградации молча стала бы второй половиной htmx. Признак ставится на
один запрос из двух, а `follow_redirects=True` на половине htmx — часть
предмета: 302 пришёл бы ей кодом 200 и телом чужого документа.

⚠️ ЗАМЫКАНИЕ ПОКРЫВАЕТ ДВА РЕЕСТРА. Маршруты за панелью подтверждения уже имеют
пары в `CONFIRMED_DELETE_ROUTES` (Фаза 10) — дублировать их здесь значило бы
завести второй источник одного утверждения. Покрытыми считаются ключи ЭТОГО
реестра и ключи того.
"""
import contextlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.payment import Payment
from app.models.schedule import Schedule
from app.models.subscription import Subscription
from app.pages import notices
from app.pages.identifiers import ID_MAX
from tests.test_pages.test_account_groups import (
    _seed_account as _seed_groups_account,
    _seed_group as _seed_account_group,
)
from tests.test_pages.test_confirm_delete_transport import (
    CONFIRMED_DELETE_ROUTES,
    DOCUMENT_MARK,
    HTMX_HEADERS,
    USER_EMAIL,
    _Arranged,
    _current_user,
    _foreign_user,
    _identify,
    _seed_victim,
    _user_of,
)
from tests.test_pages.test_editor_schedules import (
    _seed_account as _seed_editor_account,
    _seed_ad as _seed_editor_ad,
    _seed_group as _seed_editor_group,
    _seed_schedule,
)
from tests.test_pages.test_htmx_gates import _pages_sources, _post_handlers

# Ожидаемая форма ответа на транспорте htmx.
FRAGMENT = "ожидается 200 и фрагмент"
LOCATION = "ожидается 204 и заголовок перехода"
EXTERNAL = "ожидается 204 и заголовок внешнего перехода"


@dataclass(frozen=True)
class _PairCase:
    """ОДИН случай пары: обработчик × исход × ожидаемая форма ответа htmx.

    `landing` и `fragment_mark` — строки формата над `_Arranged.landing_args`:
    идентификаторы появляются только после посева, а посев у каждой половины
    свой.

    ⚠️ `resolve_after` СУЩЕСТВУЕТ ДЛЯ СОЗДАЮЩИХ ДЕЙСТВИЙ, И ЭТО НЕ УДОБСТВО
    (Фаза 11, план 11-05). У правки и тумблера идентификатор строки известен
    ПОСЕВОМ, то есть до запроса. У СОЗДАНИЯ его не существует до запроса вовсе:
    строку заводит сам запрос, и адрес приземления называет её идентификатор.
    Предсказывать его сложением единицы к посеянному значило бы утверждать
    поведение автоинкремента драйвера вместо поведения обработчика — правило
    краснело бы на смене драйвера и зеленело бы на неверном адресе, совпавшем с
    предсказанием. Поэтому подстановки адреса ДОБИРАЮТСЯ ИЗ БАЗЫ ПОСЛЕ запроса,
    и обе половины добирают их независимо, каждая на своём состоянии.
    """

    key: str
    name: str
    identity: str
    arrange: Callable[..., Awaitable[_Arranged]]
    landing: str
    transport: str
    fragment_mark: str | None = None
    resolve_after: Callable[[AsyncSession, _Arranged], Awaitable[dict]] | None = None

    @property
    def handler(self) -> str:
        return self.key.split("::", 1)[1]


# =============================================================================
# Посев: правка расписания в редакторе объявления
# =============================================================================

SCHEDULES_UPDATE = "app/pages/schedules.py::schedules_update"
MISSING_SCHEDULE_ID = 987654
# Первая величина вне колонки идентификатора — 2147483648 (Фаза 11, план 11-02).
OUT_OF_COLUMN_SCHEDULE_ID = ID_MAX + 1


async def _seed_editor_schedule(db: AsyncSession, user_id: int):
    ad = await _seed_editor_ad(db, user_id)
    account = await _seed_editor_account(db, user_id)
    schedule = await _seed_schedule(db, ad.id, account.id)
    return ad, account, schedule


def _edit_body(ad_id: int, account_id: int, *, to_editor: bool = True) -> dict:
    body = {
        "ad_id": str(ad_id),
        "account_id": str(account_id),
        "days_of_week": "1",
        "times_of_day": "18:30",
        "timezone": "UTC",
    }
    if to_editor:
        body["return_to"] = "editor"
    return body


async def _arrange_edit_success(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    ad, account, schedule = await _seed_editor_schedule(db, user.id)
    return _Arranged(
        url=f"/schedules/{schedule.id}/edit",
        data=_edit_body(ad.id, account.id),
        landing_args={"ad_id": ad.id, "schedule_id": schedule.id},
    )


async def _arrange_edit_missing_schedule(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    # Объявление СВОЁ, расписания с таким идентификатором нет вовсе.
    ad = await _seed_editor_ad(db, user.id)
    account = await _seed_editor_account(db, user.id)
    return _Arranged(
        url=f"/schedules/{MISSING_SCHEDULE_ID}/edit",
        data=_edit_body(ad.id, account.id),
        landing_args={"ad_id": ad.id},
    )


async def _arrange_edit_out_of_column_schedule(
    client, db, settings, identity
) -> _Arranged:
    user = await _current_user(db, identity, settings)
    # Объявление СВОЁ, идентификатор расписания лежит ВНЕ колонки (Фаза 11,
    # план 11-02, D-07): величина идёт той же веткой, что и отсутствующее
    # расписание, — посимвольно тем же адресом приземления.
    ad = await _seed_editor_ad(db, user.id)
    account = await _seed_editor_account(db, user.id)
    return _Arranged(
        url=f"/schedules/{OUT_OF_COLUMN_SCHEDULE_ID}/edit",
        data=_edit_body(ad.id, account.id),
        landing_args={"ad_id": ad.id},
    )


async def _arrange_edit_foreign_ad(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    _, account, schedule = await _seed_editor_schedule(db, user.id)
    # Расписание своё, а объявление в теле формы — чужое: вердикт владения
    # отказывает по объявлению.
    stranger = await _foreign_user(db)
    foreign_ad = await _seed_editor_ad(db, stranger.id, title="Чужое объявление")
    return _Arranged(
        url=f"/schedules/{schedule.id}/edit",
        data=_edit_body(foreign_ad.id, account.id),
    )


async def _arrange_edit_account_gone(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    ad, _, schedule = await _seed_editor_schedule(db, user.id)
    # Объявление своё, аккаунт в теле формы — чужой: вердикт владения отказывает
    # по аккаунту, и человека можно вернуть в его редактор с объяснением.
    stranger = await _foreign_user(db)
    foreign_account = await _seed_editor_account(db, stranger.id)
    return _Arranged(
        url=f"/schedules/{schedule.id}/edit",
        data=_edit_body(ad.id, foreign_account.id),
        landing_args={"ad_id": ad.id},
    )


async def _arrange_edit_without_marker(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    ad, account, schedule = await _seed_editor_schedule(db, user.id)
    return _Arranged(
        url=f"/schedules/{schedule.id}/edit",
        data=_edit_body(ad.id, account.id, to_editor=False),
    )


# =============================================================================
# Посев: тумблер расписания (Фаза 11, план 11-03)
# =============================================================================

SCHEDULES_TOGGLE = "app/pages/schedules.py::schedules_toggle"


async def _arrange_toggle_editor_success(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    ad, _, schedule = await _seed_editor_schedule(db, user.id)
    return _Arranged(
        url=f"/schedules/{schedule.id}/toggle",
        data={"return_to": "editor"},
        landing_args={"ad_id": ad.id, "schedule_id": schedule.id},
    )


async def _arrange_toggle_out_of_domain(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    ad = await _seed_editor_ad(db, user.id)
    account = await _seed_editor_account(db, user.id)
    group = await _seed_editor_group(db, user.id, account.id)
    # По составу полное, по значениям неисполнимое: день `9` не день недели
    # (CR-01). Возобновление отказывает кодом реестра.
    schedule = await _seed_schedule(
        db,
        ad.id,
        account.id,
        group_ids=[group.id],
        days=[9],
        times=["10:00"],
        is_active=False,
    )
    return _Arranged(
        url=f"/schedules/{schedule.id}/toggle",
        data={"return_to": "editor"},
        landing_args={"ad_id": ad.id},
    )


async def _arrange_toggle_missing(client, db, settings, identity) -> _Arranged:
    return _Arranged(
        url=f"/schedules/{MISSING_SCHEDULE_ID}/toggle",
        data={"return_to": "editor"},
    )


async def _arrange_toggle_from_list(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    _, _, schedule = await _seed_editor_schedule(db, user.id)
    # Строка сводного списка признака возврата не шлёт. Идентификатор уезжает в
    # `landing_args` затем, что метку фрагмента (строку своего экрана) можно
    # назвать только после посева.
    return _Arranged(
        url=f"/schedules/{schedule.id}/toggle",
        data={},
        landing_args={"schedule_id": schedule.id},
    )


# =============================================================================
# Посев: создание расписания в редакторе объявления (Фаза 11, план 11-05)
# =============================================================================

SCHEDULES_CREATE = "app/pages/schedules.py::schedules_create"


def _create_body(ad_id: int, account_id: int, *, to_editor: bool = True) -> dict:
    body = {"ad_id": str(ad_id), "account_id": str(account_id)}
    if to_editor:
        body["return_to"] = "editor"
    return body


async def _created_schedule_of_the_ad(db: AsyncSession, arranged: _Arranged) -> dict:
    """Идентификатор строки, заведённой ЭТОЙ половиной пары.

    Выборка скоуплена объявлением ИЗ ТЕЛА ФОРМЫ и берёт последнюю строку по
    возрастанию идентификатора — то есть ровно ту, которую создал запрос этой
    половины. Соседняя половина сеет СВОЁ объявление, поэтому две половины друг
    друга не видят и порядок их исполнения на результат не влияет.
    """
    ad_id = int(arranged.data["ad_id"])
    row = (
        await db.execute(
            select(Schedule)
            .where(Schedule.ad_id == ad_id)
            .order_by(Schedule.id.desc())
            .limit(1)
        )
    ).scalars().first()
    return {"schedule_id": row.id} if row is not None else {}


async def _arrange_create_into_a_list(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    # Список НЕ пуст: контейнер на экране есть, и новой карточке есть куда
    # приземлиться (D-05).
    ad, account, _ = await _seed_editor_schedule(db, user.id)
    return _Arranged(
        url="/schedules/new",
        data=_create_body(ad.id, account.id),
        landing_args={"ad_id": ad.id},
    )


async def _arrange_create_the_first_one(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    # Расписаний нет: контейнера в документе нет вовсе, и ответ уходит переходом.
    ad = await _seed_editor_ad(db, user.id)
    account = await _seed_editor_account(db, user.id)
    return _Arranged(
        url="/schedules/new",
        data=_create_body(ad.id, account.id),
        landing_args={"ad_id": ad.id},
    )


async def _arrange_create_on_a_foreign_ad(client, db, settings, identity) -> _Arranged:
    await _current_user(db, identity, settings)
    stranger = await _foreign_user(db)
    foreign_ad = await _seed_editor_ad(db, stranger.id, title="Чужое объявление")
    foreign_account = await _seed_editor_account(db, stranger.id)
    return _Arranged(
        url="/schedules/new",
        data=_create_body(foreign_ad.id, foreign_account.id),
    )


async def _arrange_create_with_account_gone(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    ad = await _seed_editor_ad(db, user.id)
    # Объявление своё, аккаунт в теле формы — чужой: вердикт владения отказывает
    # по аккаунту, и человека возвращают в ЕГО редактор с объяснением.
    stranger = await _foreign_user(db)
    foreign_account = await _seed_editor_account(db, stranger.id)
    return _Arranged(
        url="/schedules/new",
        data=_create_body(ad.id, foreign_account.id),
        landing_args={"ad_id": ad.id},
    )


# =============================================================================
# Посев: черновик объявления и его правка (Фаза 11, план 11-06)
# =============================================================================

ADS_CREATE = "app/pages/ads.py::ads_create"
ADS_UPDATE = "app/pages/ads.py::ads_update"

# Идентификатор, которого в базе нет. Величина ГОДНАЯ — она лежит в диапазоне
# колонки, и ветка, которой она уходит, есть «записи нет / запись чужая», а не
# отказ по величине: различать эти два случая ответом запрещено (T-02-21).
MISSING_AD_ID = 876543


def _editor_body(title: str = "Заголовок из пары") -> dict:
    """Тело формы редактора: только поля содержания.

    Кнопки «Сохранить» здесь нет намеренно — именованная кнопка отправки
    ПУБЛИКУЕТ объявление и уводит человека в список, то есть меняет и адрес
    приземления, и класс действия. Предмет этих случаев — автосохранение,
    оставляющее человека в редакторе.
    """
    return {"title": title, "text": "Текст объявления из пары транспортов"}


async def _newest_ad_of_the_owner(db: AsyncSession, arranged: _Arranged) -> dict:
    """Идентификатор объявления, заведённого ЭТОЙ половиной пары.

    Основание то же, что у `_created_schedule_of_the_ad` выше: строки,
    создаваемой запросом, до запроса не существует, и предсказывать её
    идентификатор сложением единицы значило бы утверждать поведение
    автоинкремента драйвера. Выборка скоуплена ВЛАДЕЛЬЦЕМ (личность пары —
    `user`) и берёт последнюю строку по возрастанию идентификатора: половины
    исполняются последовательно, и каждая добирает подстановки сразу после
    своего запроса.
    """
    owner = await _user_of(db, USER_EMAIL)
    row = (
        await db.execute(
            select(Ad)
            .where(Ad.user_id == owner.id)
            .order_by(Ad.id.desc())
            .limit(1)
        )
    ).scalars().first()
    return {"ad_id": row.id} if row is not None else {}


async def _arrange_ad_create(client, db, settings, identity) -> _Arranged:
    # Записи нет: черновик заводит САМ запрос (D-03), поэтому подстановки адреса
    # добираются после него.
    await _current_user(db, identity, settings)
    return _Arranged(url="/ads/new", data=_editor_body())


async def _arrange_ad_update_own(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    ad = await _seed_editor_ad(db, user.id)
    return _Arranged(
        url=f"/ads/{ad.id}/edit",
        data=_editor_body("Правка своего объявления"),
        landing_args={"ad_id": ad.id},
    )


async def _arrange_ad_update_missing(client, db, settings, identity) -> _Arranged:
    await _current_user(db, identity, settings)
    return _Arranged(url=f"/ads/{MISSING_AD_ID}/edit", data=_editor_body())


async def _arrange_ad_update_out_of_column(client, db, settings, identity) -> _Arranged:
    await _current_user(db, identity, settings)
    # Идентификатор объявления ВНЕ колонки (Фаза 11, план 11-06, D-07): величина
    # идёт той же веткой, что и отсутствующее объявление, — посимвольно тем же
    # адресом приземления. Неразличимость и есть предмет случая.
    return _Arranged(url=f"/ads/{ID_MAX + 1}/edit", data=_editor_body())


# =============================================================================
# Посев: тумблер группы аккаунта (Фаза 9)
# =============================================================================


async def _arrange_group_toggle(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    account = await _seed_groups_account(db, "wa", user_id=user.id)
    group = await _seed_account_group(db, account, "Группа пары", user_id=user.id)
    return _Arranged(
        url=f"/accounts/{account.id}/groups/{group.id}/toggle",
        data={"is_active": "on"},
        landing_args={"account_id": account.id, "group_id": group.id},
    )


# =============================================================================
# Посев: сохранение часового пояса в профиле (Фаза 11, план 11-09)
# =============================================================================

PROFILE_POST = "app/pages/profile.py::profile_post"


async def _arrange_profile_save(client, db, settings, identity) -> _Arranged:
    """Годный пояс СВОЕГО пользователя — сеять нечего, форма самодостаточна.

    Пользователь уже заведён входом (`_identify`); обращение к нему здесь стоит
    затем, чтобы расстановка падала вслух, если вход не состоялся, а не
    превращалась молча в запрос без сессии — то есть во ВТОРОЙ случай ниже.
    """
    await _current_user(db, identity, settings)
    return _Arranged(url="/profile", data={"timezone": "Europe/Moscow"})


async def _arrange_profile_without_session(client, db, settings, identity) -> _Arranged:
    """ТОТ ЖЕ запрос БЕЗ сессии — cookie снимается РАССТАНОВКОЙ, а не личностью.

    ⚠️ АНОНИМНОЙ ЛИЧНОСТИ СРЕДИ ЛИЧНОСТЕЙ ОБХОДА НЕТ: обе ветви `_identify`
    подписывают клиента. Ветка «нет сессии» получается снятием cookie ЗДЕСЬ, а
    не третьей личностью в общем помощнике: помощник ввозится из
    `test_confirm_delete_transport.py` и обслуживает восемь маршрутов
    подтверждения, и новая ветвь в нём меняла бы условия ЧУЖОГО обхода ради
    одного случая этого реестра.

    ⚠️ СНЯТИЕ ДЕЙСТВУЕТ НА ОБЕ ПОЛОВИНЫ ПАРЫ, И ЭТО СВОЙСТВО ОБХОДА, А НЕ
    ВЕЗЕНИЕ: расстановка зовётся ПЕРЕД КАЖДОЙ половиной (см. обход ниже),
    поэтому cookie снимается и перед запросом деградации, и перед запросом слоя
    письма.
    """
    client.cookies.clear()
    return _Arranged(url="/profile", data={"timezone": "Europe/Moscow"})


# =============================================================================
# Посев: блокировка пользователя из его карточки (Фаза 11, план 11-12)
# =============================================================================

ADMIN_TOGGLE_BLOCK = "app/pages/admin.py::admin_toggle_block"
MISSING_USER_ID = 987654
# Первая величина вне колонки идентификатора — 2147483648 (D-07).
OUT_OF_COLUMN_USER_ID = ID_MAX + 1


async def _arrange_block_toggle(client, db, settings, identity) -> _Arranged:
    """СВОЯ строка у каждой половины: вторая половина не должна снимать блокировку,
    поставленную первой, — иначе обе половины проверяли бы разные исходы."""
    target = await _seed_victim(db)
    return _Arranged(
        url=f"/admin/users/{target.id}/block", landing_args={"user_id": target.id}
    )


async def _arrange_block_missing(client, db, settings, identity) -> _Arranged:
    return _Arranged(url=f"/admin/users/{MISSING_USER_ID}/block")


async def _arrange_block_out_of_column(client, db, settings, identity) -> _Arranged:
    return _Arranged(url=f"/admin/users/{OUT_OF_COLUMN_USER_ID}/block")


async def _arrange_block_self(client, db, settings, identity) -> _Arranged:
    admin = await _current_user(db, identity, settings)
    return _Arranged(
        url=f"/admin/users/{admin.id}/block", landing_args={"user_id": admin.id}
    )


# =============================================================================
# Посев: бесплатный доступ из карточки пользователя (Фаза 11, план 11-13)
# =============================================================================

ADMIN_TOGGLE_FREE_ACCESS = "app/pages/admin.py::admin_toggle_free_access"


async def _arrange_free_access_toggle(client, db, settings, identity) -> _Arranged:
    """СВОЙ пользователь со СВОЕЙ активной строкой подписки у каждой половины.

    ⚠️ СТРОКА ПОДПИСКИ ЗАВОДИТСЯ ЗДЕСЬ ЯВНО: `_seed_victim` её не заводит, а
    без строки тумблер уходит веткой «строки подписки нет» — переходом, и успех
    фрагментом не проверялся бы вовсе.
    """
    target = await _seed_victim(db)
    db.add(
        Subscription(
            user_id=target.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_active=True,
            has_free_access=False,
        )
    )
    await db.commit()
    return _Arranged(
        url=f"/admin/users/{target.id}/unlimited", landing_args={"user_id": target.id}
    )


async def _arrange_free_access_without_subscription(
    client, db, settings, identity
) -> _Arranged:
    target = await _seed_victim(db)
    return _Arranged(
        url=f"/admin/users/{target.id}/unlimited", landing_args={"user_id": target.id}
    )


async def _arrange_free_access_missing(client, db, settings, identity) -> _Arranged:
    return _Arranged(url=f"/admin/users/{MISSING_USER_ID}/unlimited")


# =============================================================================
# Посев: оформление доступа с уходом на страницу ЮKassa (Фаза 11, план 11-15)
# =============================================================================

SUBSCRIBE_TO_PLAN = "app/pages/billing.py::subscribe_to_plan"

# Адрес подтверждения на ДОКУМЕНТИРОВАННОМ хосте (Находка C RESEARCH Фазы 11):
# все официальные примеры `confirmation_url` — на `yoomoney.ru`. Прежние фикстуры
# суиты на `yookassa.ru` путь htmx отвергнет, а путь 302 — нет; пары стоят на
# документированном хосте, чтобы обе половины утверждали ОДИН адрес.
YOOMONEY_CONFIRMATION_URL = "https://yoomoney.ru/checkout/payments/v2/contract?orderId=2c85a"


def _yookassa_network(*, failing: bool = False):
    """Фабрика подмены СЕТИ ЮKassa — единственной подменённой части пути.

    ⚠️ СЕРВИС СОЗДАНИЯ ПЛАТЕЖА НЕ ПОДМЕНЯЕТСЯ, И ЭТО ПРЕДМЕТ, А НЕ ВКУС. Потолок
    незакрытых намерений (PAY-01) живёт ВНУТРИ создания платежа; пара, подменившая
    сервис, проверяла бы транспорт мимо денежного ограничения, которое перевод
    обязан не ослабить.
    """

    @contextlib.contextmanager
    def _context():
        settings = MagicMock()
        settings.yookassa_shop_id = "shop123"
        settings.yookassa_secret_key = "secret"
        settings.yookassa_return_url = "http://test/billing"
        settings.app_name = "Broadcaster"
        payment = MagicMock()
        payment.id = "yoo_pair"
        payment.confirmation = MagicMock()
        payment.confirmation.confirmation_url = YOOMONEY_CONFIRMATION_URL
        sdk = (
            patch(
                "app.services.payment_service.YooPayment.create",
                side_effect=RuntimeError("сеть ЮKassa недоступна"),
            )
            if failing
            else patch(
                "app.services.payment_service.YooPayment.create", return_value=payment
            )
        )
        with patch(
            "app.services.payment_service.get_settings", return_value=settings
        ), sdk:
            yield

    return _context


async def _without_payments(db: AsyncSession, identity: str, settings) -> None:
    """Снять платежи СВОЕГО пользователя перед половиной пары.

    Первая половина успешного случая заводит незакрытое намерение, и вторая,
    пришедшая на это состояние, упёрлась бы в потолок — то есть проверяла бы не
    тот исход, который названа проверять (шапка модуля: обе половины на свежем
    состоянии).
    """
    user = await _current_user(db, identity, settings)
    await db.execute(delete(Payment).where(Payment.user_id == user.id))
    await db.commit()


async def _arrange_subscribe_success(client, db, settings, identity) -> _Arranged:
    await _without_payments(db, identity, settings)
    return _Arranged(url="/billing/subscribe", context=_yookassa_network())


async def _arrange_subscribe_disabled(client, db, settings, identity) -> _Arranged:
    await _without_payments(db, identity, settings)

    @contextlib.contextmanager
    def _payments_off():
        settings.yookassa_enabled = False
        try:
            yield
        finally:
            settings.yookassa_enabled = True

    return _Arranged(url="/billing/subscribe", context=_payments_off)


async def _arrange_subscribe_pending(client, db, settings, identity) -> _Arranged:
    """Незакрытое намерение заводится НАСТОЯЩИМ нажатием, а не вставкой строки.

    Вставка строки мимо сервиса утверждала бы форму схемы, а не то, что второе
    нажатие через форму упирается в потолок.
    """
    await _without_payments(db, identity, settings)
    with _yookassa_network()():
        first = await client.post("/billing/subscribe", follow_redirects=False)
    assert first.status_code == 302, "первое нажатие не завело намерения оплаты"
    return _Arranged(url="/billing/subscribe", context=_yookassa_network())


async def _arrange_subscribe_failing(client, db, settings, identity) -> _Arranged:
    await _without_payments(db, identity, settings)
    return _Arranged(url="/billing/subscribe", context=_yookassa_network(failing=True))


async def _arrange_subscribe_without_session(
    client, db, settings, identity
) -> _Arranged:
    client.cookies.clear()
    return _Arranged(url="/billing/subscribe", context=_yookassa_network())


# =============================================================================
# Посев: повторная синхронизация групп аккаунта (Фаза 11, план 11-16)
# =============================================================================

ACCOUNTS_RETRY_SYNC = "app/pages/accounts.py::accounts_retry_sync"
MISSING_ACCOUNT_ID = 987654


@contextlib.contextmanager
def _retry_sync_bridge():
    """Подмена МОСТА и очереди — внешних границ повторной синхронизации.

    Обработчик зовёт мост мессенджера и ставит фоновую задачу; ни того, ни
    другого в прогоне нет. Подмена стоит и на исходах «не найден» и «нет
    сессии»: ответ, дошедший до моста там, где не должен, прошёл бы молча без
    неё только в том случае, если бы мост был настоящим — а он в прогоне
    недоступен и уронил бы случай не по его предмету.
    """
    with patch("app.pages.accounts.WhatsAppMessenger") as messenger, patch.dict(
        "sys.modules", {"app.worker.celery_app": MagicMock()}
    ):
        messenger.return_value.retry_sync = AsyncMock(return_value={"status": "ok"})
        yield


async def _arrange_retry_sync(client, db, settings, identity) -> _Arranged:
    user = await _current_user(db, identity, settings)
    account = await _seed_groups_account(db, "wa", user_id=user.id)
    account.status = "sync_failed"
    await db.commit()
    return _Arranged(
        url=f"/accounts/{account.id}/retry-sync",
        context=_retry_sync_bridge,
        landing_args={"account_id": account.id},
    )


async def _arrange_retry_sync_missing(client, db, settings, identity) -> _Arranged:
    return _Arranged(
        url=f"/accounts/{MISSING_ACCOUNT_ID}/retry-sync", context=_retry_sync_bridge
    )


async def _arrange_retry_sync_foreign(client, db, settings, identity) -> _Arranged:
    """Чужой аккаунт идёт ТОЙ ЖЕ веткой, что несуществующий (T-11-29)."""
    stranger = await _foreign_user(db)
    account = await _seed_groups_account(db, "wa", user_id=stranger.id)
    return _Arranged(
        url=f"/accounts/{account.id}/retry-sync", context=_retry_sync_bridge
    )


async def _arrange_retry_sync_without_session(
    client, db, settings, identity
) -> _Arranged:
    user = await _current_user(db, identity, settings)
    account = await _seed_groups_account(db, "wa", user_id=user.id)
    client.cookies.clear()
    return _Arranged(
        url=f"/accounts/{account.id}/retry-sync", context=_retry_sync_bridge
    )


# =============================================================================
# РЕЕСТР
# =============================================================================

POST_PAIR_CASES: tuple[_PairCase, ...] = (
    # Фаза 11, план 11-01. Правка расписания в редакторе: карточка остаётся на
    # экране и подменяет саму себя (D-02).
    _PairCase(
        key=SCHEDULES_UPDATE,
        name="правка расписания — успех",
        identity="user",
        arrange=_arrange_edit_success,
        landing="/ads/{ad_id}/edit?sched={schedule_id}#sched-{schedule_id}",
        transport=FRAGMENT,
        fragment_mark='id="sched-{schedule_id}"',
    ),
    # Исходы, НЕ оставляющие карточку на экране (D-06): код реестра едет ровно
    # там, где он выдаётся сегодня.
    _PairCase(
        key=SCHEDULES_UPDATE,
        name="правка расписания — расписания нет при своём объявлении",
        identity="user",
        arrange=_arrange_edit_missing_schedule,
        landing="/ads/{ad_id}/edit?notice=" + notices.SCHEDULE_AD_MISSING,
        transport=LOCATION,
    ),
    # Фаза 11, план 11-02 (D-07). Идентификатор вне колонки — та же ветка, что у
    # отсутствующего расписания: неразличимость «вне диапазона» и «нет строки»
    # (T-11-05) утверждается посимвольным равенством адреса приземления.
    _PairCase(
        key=SCHEDULES_UPDATE,
        name="правка расписания — идентификатор вне колонки при своём объявлении",
        identity="user",
        arrange=_arrange_edit_out_of_column_schedule,
        landing="/ads/{ad_id}/edit?notice=" + notices.SCHEDULE_AD_MISSING,
        transport=LOCATION,
    ),
    _PairCase(
        key=SCHEDULES_UPDATE,
        name="правка расписания — объявление чужое",
        identity="user",
        arrange=_arrange_edit_foreign_ad,
        landing="/schedules",
        transport=LOCATION,
    ),
    _PairCase(
        key=SCHEDULES_UPDATE,
        name="правка расписания — аккаунт недоступен",
        identity="user",
        arrange=_arrange_edit_account_gone,
        landing="/ads/{ad_id}/edit?notice=" + notices.SCHEDULE_ACCOUNT_GONE,
        transport=LOCATION,
    ),
    # На сводном списке карточки нет — то же основание, что у ветки `WR-01`
    # удаления: фрагменту редактора там некуда приземлиться.
    _PairCase(
        key=SCHEDULES_UPDATE,
        name="правка расписания — без признака возврата",
        identity="user",
        arrange=_arrange_edit_without_marker,
        landing="/schedules",
        transport=LOCATION,
    ),
    # Фаза 11, план 11-03. Тумблер расписания: в редакторе карточка подменяет
    # саму себя с серверным состоянием (D-02, D-11).
    _PairCase(
        key=SCHEDULES_TOGGLE,
        name="тумблер расписания — успех в редакторе",
        identity="user",
        arrange=_arrange_toggle_editor_success,
        landing="/ads/{ad_id}/edit",
        transport=FRAGMENT,
        fragment_mark='id="sched-{schedule_id}"',
    ),
    # Исход уводит с экрана тем же кодом реестра, что и без htmx (D-06).
    _PairCase(
        key=SCHEDULES_TOGGLE,
        name="тумблер расписания — значения вне области",
        identity="user",
        arrange=_arrange_toggle_out_of_domain,
        landing="/ads/{ad_id}/edit?notice=" + notices.SCHEDULE_VALUES_OUT_OF_DOMAIN,
        transport=LOCATION,
    ),
    _PairCase(
        key=SCHEDULES_TOGGLE,
        name="тумблер расписания — расписания нет",
        identity="user",
        arrange=_arrange_toggle_missing,
        landing="/schedules",
        transport=LOCATION,
    ),
    # Фаза 11, план 11-04 (D-02, D-11). Строка сводного списка подменяет САМУ
    # СЕБЯ: экран остаётся, и цель у фрагмента на нём есть — сама строка.
    # ⚠️ ВЕТКА СМЕНИЛА КЛАСС, А НЕ ЗАВЕЛАСЬ ЗАНОВО: планом 11-03 этот же случай
    # стоял переходом (`LOCATION`), потому что разметки строки под фрагмент ещё
    # не было и приземляться ответу было некуда. Адрес деградации при этом не
    # сдвинулся ни на символ — половина без признака по-прежнему 302 на
    # `/schedules`, и именно её неподвижность доказывает, что сменилась ФОРМА
    # ОТВЕТА, а не поведение действия.
    _PairCase(
        key=SCHEDULES_TOGGLE,
        name="тумблер расписания — со сводного списка",
        identity="user",
        arrange=_arrange_toggle_from_list,
        landing="/schedules",
        transport=FRAGMENT,
        fragment_mark='id="schedule-row-{schedule_id}"',
    ),
    # Фаза 11, план 11-05. Создание расписания: карточка ВСТАВЛЯЕТСЯ в список
    # редактора, контейнер не перерисовывается (D-05, FORM-07).
    _PairCase(
        key=SCHEDULES_CREATE,
        name="создание расписания — в непустой список",
        identity="user",
        arrange=_arrange_create_into_a_list,
        landing="/ads/{ad_id}/edit?sched={schedule_id}#sched-{schedule_id}",
        transport=FRAGMENT,
        fragment_mark='id="sched-{schedule_id}"',
        resolve_after=_created_schedule_of_the_ad,
    ),
    # ⚠️ «БЫЛО НОЛЬ» — ПЕРЕХОД, И ЭТО НЕ ОТСТУПЛЕНИЕ ОТ ФРАГМЕНТНОГО КЛАССА, А
    # ЕГО ГРАНИЦА: при пустом списке контейнера в документе нет вовсе, и
    # приземляться фрагменту некуда (D-05). Адрес — тот же, посимвольно.
    _PairCase(
        key=SCHEDULES_CREATE,
        name="создание расписания — было ноль",
        identity="user",
        arrange=_arrange_create_the_first_one,
        landing="/ads/{ad_id}/edit?sched={schedule_id}#sched-{schedule_id}",
        transport=LOCATION,
        resolve_after=_created_schedule_of_the_ad,
    ),
    _PairCase(
        key=SCHEDULES_CREATE,
        name="создание расписания — объявление чужое",
        identity="user",
        arrange=_arrange_create_on_a_foreign_ad,
        landing="/schedules",
        transport=LOCATION,
    ),
    _PairCase(
        key=SCHEDULES_CREATE,
        name="создание расписания — аккаунт недоступен",
        identity="user",
        arrange=_arrange_create_with_account_gone,
        landing="/ads/{ad_id}/edit?notice=" + notices.SCHEDULE_ACCOUNT_GONE,
        transport=LOCATION,
    ),
    # Фаза 11, план 11-06. Черновик объявления и его правка: ответ автосохранения
    # приезжает внеполосными узлами, форма не перерисовывается (D-02, D-13).
    # ⚠️ МЕТКА ФРАГМЕНТА — РАМКА ПРЕДПРОСМОТРА, А НЕ КАРТОЧКА СПИСКА: у этого
    # ответа основного места подмены нет вовсе (`hx-swap="none"` формы), и всё
    # приезжает внеполосно. Метка выбрана из трёх внеполосных узлов ответа как
    # тот, что несёт СОДЕРЖАНИЕ записи, а не состояние индикатора.
    _PairCase(
        key=ADS_CREATE,
        name="создание черновика объявления — автосохранением",
        identity="user",
        arrange=_arrange_ad_create,
        landing="/ads/{ad_id}/edit",
        transport=FRAGMENT,
        fragment_mark='id="ad-preview"',
        resolve_after=_newest_ad_of_the_owner,
    ),
    _PairCase(
        key=ADS_UPDATE,
        name="правка объявления по адресу — своё",
        identity="user",
        arrange=_arrange_ad_update_own,
        landing="/ads/{ad_id}/edit",
        transport=FRAGMENT,
        fragment_mark='id="ad-preview"',
    ),
    # Исход уводит с экрана: редактора несуществующего объявления не бывает, и
    # приземляться фрагменту некуда. Адрес тот же, что уезжает 302 сегодня.
    _PairCase(
        key=ADS_UPDATE,
        name="правка объявления по адресу — объявления нет",
        identity="user",
        arrange=_arrange_ad_update_missing,
        landing="/ads",
        transport=LOCATION,
    ),
    # Фаза 11, план 11-06, задача 2 (D-07). Величина вне колонки — та же ветка,
    # что у несуществующего объявления: неразличимость «вне диапазона» и «нет
    # строки» утверждается посимвольным равенством адреса приземления на обоих
    # транспортах, ровно как у правки расписания (T-11-05).
    _PairCase(
        key=ADS_UPDATE,
        name="правка объявления по адресу — идентификатор вне колонки",
        identity="user",
        arrange=_arrange_ad_update_out_of_column,
        landing="/ads",
        transport=LOCATION,
    ),
    # Фаза 9, план 09-01, заведено планом 11-01. Первый фрагментный обработчик
    # вехи; в `CONFIRMED_DELETE_ROUTES` его нет (за панелью подтверждения он не
    # стоит), и без этой записи замыкание называет его непокрытым.
    _PairCase(
        key="app/pages/account_groups.py::account_groups_toggle",
        name="тумблер группы аккаунта — успех",
        identity="user",
        arrange=_arrange_group_toggle,
        landing="/accounts/{account_id}/groups",
        transport=FRAGMENT,
        fragment_mark='id="group-row-{group_id}"',
    ),
    # Фаза 11, план 11-09. Сохранение часового пояса: экран ОСТАЁТСЯ, подмена
    # приезжает в форму настроек, а код исхода — внеполосным блоком ТЕМ ЖЕ
    # ответом. Первый в вехе фрагмент, несущий код исхода: до него приклейка
    # блока была заведена и не использовалась ни одним обработчиком.
    _PairCase(
        key=PROFILE_POST,
        name="сохранение часового пояса — успех",
        identity="user",
        arrange=_arrange_profile_save,
        landing="/profile?notice=" + notices.PROFILE_SAVED,
        transport=FRAGMENT,
        fragment_mark='id="timezone"',
    ),
    # Исход уводит с экрана: без сессии подменять нечего и показывать нечего.
    _PairCase(
        key=PROFILE_POST,
        name="сохранение часового пояса — нет сессии",
        identity="user",
        arrange=_arrange_profile_without_session,
        landing="/login",
        transport=LOCATION,
    ),
    # Фаза 11, план 11-12. Блокировка пользователя из его карточки: экран
    # ОСТАЁТСЯ, подменяется содержимое блока действий, а бейдж и плитка доступа
    # приезжают внеполосно (D-02). Метка — адрес формы блокировки: она стоит в
    # ОСНОВНОМ теле, то есть доказывает, что приехал блок действий.
    _PairCase(
        key=ADMIN_TOGGLE_BLOCK,
        name="блокировка пользователя — успех",
        identity="admin",
        arrange=_arrange_block_toggle,
        landing="/admin/users/{user_id}",
        transport=FRAGMENT,
        fragment_mark='action="/admin/users/{user_id}/block"',
    ),
    # Исходы вне экрана (D-02): карточки несуществующего пользователя нет, и
    # приземляться фрагменту некуда. Адрес — тот же, что уезжает 302.
    _PairCase(
        key=ADMIN_TOGGLE_BLOCK,
        name="блокировка пользователя — пользователя нет",
        identity="admin",
        arrange=_arrange_block_missing,
        landing="/admin/users",
        transport=LOCATION,
    ),
    # D-07: величина вне колонки — та же ветка, что у несуществующей строки.
    _PairCase(
        key=ADMIN_TOGGLE_BLOCK,
        name="блокировка пользователя — идентификатор вне колонки",
        identity="admin",
        arrange=_arrange_block_out_of_column,
        landing="/admin/users",
        transport=LOCATION,
    ),
    _PairCase(
        key=ADMIN_TOGGLE_BLOCK,
        name="блокировка пользователя — нельзя заблокировать себя",
        identity="admin",
        arrange=_arrange_block_self,
        landing="/admin/users/{user_id}",
        transport=LOCATION,
    ),
    # Фаза 11, план 11-13. Бесплатный доступ из карточки пользователя: тот же
    # шаблон ответа, что у блокировки (D-02). Метка — адрес формы бесплатного
    # доступа: она стоит в ОСНОВНОМ теле, то есть доказывает, что приехал блок
    # действий.
    _PairCase(
        key=ADMIN_TOGGLE_FREE_ACCESS,
        name="бесплатный доступ — успех",
        identity="admin",
        arrange=_arrange_free_access_toggle,
        landing="/admin/users/{user_id}",
        transport=FRAGMENT,
        fragment_mark='action="/admin/users/{user_id}/unlimited"',
    ),
    # «Строки подписки нет» (FORM-04): карточка существует, но действие не
    # состоялось, и тумблер уводит на неё же — переходом, тем же адресом, что 302.
    _PairCase(
        key=ADMIN_TOGGLE_FREE_ACCESS,
        name="бесплатный доступ — строки подписки нет",
        identity="admin",
        arrange=_arrange_free_access_without_subscription,
        landing="/admin/users/{user_id}",
        transport=LOCATION,
    ),
    _PairCase(
        key=ADMIN_TOGGLE_FREE_ACCESS,
        name="бесплатный доступ — пользователя нет",
        identity="admin",
        arrange=_arrange_free_access_missing,
        landing="/admin/users",
        transport=LOCATION,
    ),
    # Фаза 11, план 11-15. Оформление доступа: ПЕРВЫЙ случай ветки EXTERNAL.
    # Успех уводит С САЙТА на страницу подтверждения ЮKassa заголовком
    # `HX-Redirect` — не `HX-Location`, который `selfRequestsOnly` заблокировал
    # бы на чужом хосте (D-09, Находка A).
    _PairCase(
        key=SUBSCRIBE_TO_PLAN,
        name="оформление доступа — успех",
        identity="user",
        arrange=_arrange_subscribe_success,
        landing=YOOMONEY_CONFIRMATION_URL,
        transport=EXTERNAL,
    ),
    # Отказы оплаты уходят переходом на /billing с прежним кодом реестра.
    _PairCase(
        key=SUBSCRIBE_TO_PLAN,
        name="оформление доступа — платежи выключены",
        identity="user",
        arrange=_arrange_subscribe_disabled,
        landing="/billing?notice=" + notices.PAYMENT_DISABLED,
        transport=LOCATION,
    ),
    _PairCase(
        key=SUBSCRIBE_TO_PLAN,
        name="оформление доступа — незакрытое намерение",
        identity="user",
        arrange=_arrange_subscribe_pending,
        landing="/billing?notice=" + notices.PAYMENT_PENDING,
        transport=LOCATION,
    ),
    _PairCase(
        key=SUBSCRIBE_TO_PLAN,
        name="оформление доступа — сбой создания",
        identity="user",
        arrange=_arrange_subscribe_failing,
        landing="/billing?notice=" + notices.PAYMENT_FAILED,
        transport=LOCATION,
    ),
    _PairCase(
        key=SUBSCRIBE_TO_PLAN,
        name="оформление доступа — нет сессии",
        identity="user",
        arrange=_arrange_subscribe_without_session,
        landing="/login",
        transport=LOCATION,
    ),
    # Фаза 11, план 11-16. Повторная синхронизация групп аккаунта: действие
    # НАВИГАЦИОННОЕ (D-02) — нажатие уводит на экран групп, и все исходы идут
    # переходом, посимвольно на адреса 302.
    _PairCase(
        key=ACCOUNTS_RETRY_SYNC,
        name="повторная синхронизация — успех",
        identity="user",
        arrange=_arrange_retry_sync,
        landing="/accounts/{account_id}/groups",
        transport=LOCATION,
    ),
    _PairCase(
        key=ACCOUNTS_RETRY_SYNC,
        name="повторная синхронизация — аккаунта нет",
        identity="user",
        arrange=_arrange_retry_sync_missing,
        landing="/accounts",
        transport=LOCATION,
    ),
    _PairCase(
        key=ACCOUNTS_RETRY_SYNC,
        name="повторная синхронизация — аккаунт чужой",
        identity="user",
        arrange=_arrange_retry_sync_foreign,
        landing="/accounts",
        transport=LOCATION,
    ),
    _PairCase(
        key=ACCOUNTS_RETRY_SYNC,
        name="повторная синхронизация — нет сессии",
        identity="user",
        arrange=_arrange_retry_sync_without_session,
        landing="/login",
        transport=LOCATION,
    ),
)

# ЛЕТОПИСЬ ЧИСЛА (каждое движение — запись, число ставится ПРОГОНОМ):
#   0 → 6, Фаза 11, план 11-01: реестр заведён — пять исходов правки расписания
#   в редакторе объявления и успех тумблера группы аккаунта.
#   6 → 7, Фаза 11, план 11-02: правка с идентификатором расписания вне колонки
#   (D-07) — та же ветка, что у отсутствующего расписания.
#   7 → 11, Фаза 11, план 11-03: четыре исхода переключения расписания — успех
#   в редакторе (фрагмент), значения вне области, расписания нет и строка
#   сводного списка (переход).
#   11 → 15, Фаза 11, план 11-05: четыре исхода СОЗДАНИЯ расписания — вставка в
#   непустой список (фрагмент), «было ноль», чужое объявление и недоступный
#   аккаунт (переход).
#   15 → 18, Фаза 11, план 11-06, задача 1: три исхода модуля ОБЪЯВЛЕНИЙ —
#   создание черновика автосохранением и правка своего (фрагмент), правка
#   несуществующего (переход).
#   18 → 19, Фаза 11, план 11-06, задача 2: правка с идентификатором объявления
#   вне колонки (D-07) — та же ветка, что у несуществующего объявления.
#   19 → 21, Фаза 11, план 11-09: два исхода СОХРАНЕНИЯ ЧАСОВОГО ПОЯСА —
#   успех (фрагмент формы настроек, несущий ВДОБАВОК внеполосный код исхода:
#   первый такой фрагмент вехи) и «нет сессии» (переход на экран входа).
#   ⚠️ ВЕТКА ОШИБКИ ПОЛЯ В ЭТОТ РЕЕСТР НЕ ВХОДИТ, И ЭТО ГРАНИЦА ОБХОДА, А НЕ
#   ПРОПУСК. Обход утверждает ЛИБО 200 с фрагментом, ЛИБО 204 с заголовком
#   перехода; ошибка заполнения отвечает 422 на ОБОИХ транспортах — третьей
#   формы ответа у обхода нет, и подогнать её под имеющиеся значило бы
#   утверждать не тот код. Обе её половины утверждены поимённо в
#   `tests/test_pages/test_profile.py`.
#   ПОСТАВЛЕНО ПРОГОНОМ: `случаев пар в реестре 21, объявлено 19`.
#   21 → 25, Фаза 11, план 11-12: четыре исхода БЛОКИРОВКИ ПОЛЬЗОВАТЕЛЯ ИЗ ЕГО
#   КАРТОЧКИ — успех (фрагмент блока действий с внеполосными бейджем и плиткой
#   доступа), пользователя нет, идентификатор вне колонки (D-07) и «нельзя
#   заблокировать себя» (переход).
#   ПОСТАВЛЕНО ПРОГОНОМ: `случаев пар в реестре 25, объявлено 21`.
#   25 → 28, Фаза 11, план 11-13: три исхода ВЫДАЧИ И СНЯТИЯ БЕСПЛАТНОГО
#   ДОСТУПА из карточки пользователя — успех (фрагмент блока действий с
#   внеполосными бейджем и плиткой доступа), «строки подписки нет» и
#   «пользователя нет» (переход).
#   ПОСТАВЛЕНО ПРОГОНОМ: `случаев пар в реестре 28, объявлено 25`.
#   28 → 33, Фаза 11, план 11-15: пять исходов ОФОРМЛЕНИЯ ДОСТУПА — успех
#   (ПЕРВЫЙ случай ветки EXTERNAL: 204 и заголовок увода на страницу ЮKassa) и
#   четыре перехода: платежи выключены, незакрытое намерение (настоящим вторым
#   нажатием через потолок PAY-01), сбой создания, нет сессии.
#   ПОСТАВЛЕНО ПРОГОНОМ: `случаев пар в реестре 33, объявлено 28`.
POST_PAIR_CASES_DECLARED = 33


def _case_id(case: _PairCase) -> str:
    return f"{case.handler}-{case.name}"


async def _landing_args(
    case: _PairCase, db: AsyncSession, arranged: _Arranged
) -> dict:
    """Подстановки адреса приземления, добранные ПОСЛЕ запроса, если случай просит.

    Случай без `resolve_after` отдаёт подстановки посева неизменными — то есть
    одиннадцать прежних записей проходят этот помощник байт-в-байт тем же
    словарём, каким пользовались до него.
    """
    if case.resolve_after is None:
        return arranged.landing_args
    return {**arranged.landing_args, **await case.resolve_after(db, arranged)}


# =============================================================================
# ОБХОД: обе половины пары
# =============================================================================


@pytest.mark.parametrize("case", POST_PAIR_CASES, ids=_case_id)
@pytest.mark.asyncio
async def test_every_pair_case_answers_both_transports(
    case: _PairCase, client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Без признака — 302 на адрес посимвольно; с признаком — форма по ветке."""
    await _identify(client, case.identity, test_settings)

    degraded = await case.arrange(client, db_session, test_settings, case.identity)
    with degraded.context():
        without = await client.post(
            degraded.url, data=degraded.data, follow_redirects=False
        )
    # Подстановки добираются ПОСЛЕ запроса: у создающего действия строки, чей
    # идентификатор называет адрес, до запроса не существует (см. `_PairCase`).
    expected = case.landing.format(**await _landing_args(case, db_session, degraded))
    assert without.status_code == 302, (
        f"{case.name}: путь деградации ответил {without.status_code} вместо 302"
    )
    assert without.headers["location"] == expected, (
        f"{case.name}: адрес деградации {without.headers['location']!r} не совпал "
        f"с ожидаемым {expected!r} ПОСИМВОЛЬНО"
    )

    arranged = await case.arrange(client, db_session, test_settings, case.identity)
    with arranged.context():
        with_layer = await client.post(
            arranged.url,
            data=arranged.data,
            headers=HTMX_HEADERS,
            follow_redirects=True,
        )
    landing_args = await _landing_args(case, db_session, arranged)
    expected = case.landing.format(**landing_args)

    assert DOCUMENT_MARK not in with_layer.text, (
        f"{case.name}: слою письма приехал ЦЕЛЫЙ ДОКУМЕНТ — обработчик ответил "
        "перенаправлением, и клиент прошёл по нему прозрачно"
    )

    if case.transport is FRAGMENT:
        assert with_layer.status_code == 200, (
            f"{case.name}: фрагментный путь ответил {with_layer.status_code} вместо 200"
        )
        mark = case.fragment_mark.format(**landing_args)
        assert mark in with_layer.text, (
            f"{case.name}: во фрагменте нет метки {mark!r}"
        )
        return

    if case.transport is LOCATION:
        assert with_layer.status_code == 204, (
            f"{case.name}: слою письма ответили {with_layer.status_code} вместо 204"
        )
        assert with_layer.headers.get("HX-Location") == expected, (
            f"{case.name}: заголовок перехода {with_layer.headers.get('HX-Location')!r} "
            f"не совпал с адресом деградации {expected!r}"
        )
        assert with_layer.content == b"", f"{case.name}: у ответа 204 появилось тело"
        return

    assert case.transport is EXTERNAL, f"{case.name}: неизвестная ветка {case.transport!r}"
    # ⚠️ ВЕТКА ПОЛУЧИЛА ПРЕДМЕТ ПЛАНОМ 11-15 И ВМЕСТЕ С НИМ — УТВЕРЖДЕНИЕ ОБ
    # ОТСУТСТВИИ `HX-Location`. Слой письма читает его ПЕРВЫМ (Находка A): ответ с
    # обоими заголовками ушёл бы межсайтовым XHR, и `selfRequestsOnly` молча
    # оставил бы человека на месте при заведённом платеже.
    assert with_layer.status_code == 204, (
        f"{case.name}: слою письма ответили {with_layer.status_code} вместо 204"
    )
    assert with_layer.headers.get("HX-Redirect") == expected, (
        f"{case.name}: заголовок внешнего перехода "
        f"{with_layer.headers.get('HX-Redirect')!r} не совпал с адресом "
        f"деградации {expected!r} ПОСИМВОЛЬНО"
    )
    assert "HX-Location" not in with_layer.headers, (
        f"{case.name}: ответ несёт ОБА заголовка перехода — слой письма уйдёт по "
        "HX-Location, и межсайтовый XHR будет заблокирован"
    )
    assert with_layer.content == b"", f"{case.name}: у ответа 204 появилось тело"


# =============================================================================
# ЧИСЛО И ЗАМЫКАНИЕ
# =============================================================================


def test_the_number_of_pair_cases_is_the_declared_one():
    """Длина реестра равна объявленному числу; пустой реестр краснит."""
    assert POST_PAIR_CASES, "реестр пар пуст — обход вакуумно зелен"
    assert len(POST_PAIR_CASES) == POST_PAIR_CASES_DECLARED, (
        f"случаев пар в реестре {len(POST_PAIR_CASES)}, объявлено "
        f"{POST_PAIR_CASES_DECLARED}. Поставьте число ПРОГОНОМ этого отказа"
    )
    ids = [_case_id(case) for case in POST_PAIR_CASES]
    assert len(set(ids)) == len(ids), "два случая названы одинаково"


def _closure_complaints(
    cases: tuple[_PairCase, ...], sources: dict[str, str] | None = None
) -> list[str]:
    """Переведённые POST-обработчики, у которых нет НИ ОДНОГО случая пары.

    Реестр приходит параметром, чтобы контроль ниже проверял ТУ ЖЕ проверку, а не
    её вторую копию.
    """
    handlers = _post_handlers(_pages_sources() if sources is None else sources)
    converted = {key for key, handler in handlers.items() if handler.calls_respond}
    covered = {case.key for case in cases} | {
        route.key for route in CONFIRMED_DELETE_ROUTES
    }
    return sorted(converted - covered)


def test_every_converted_handler_has_a_pair():
    """ЗАМЫКАНИЕ: каждый обработчик на слое ответа имеет хотя бы одну пару."""
    complaints = _closure_complaints(POST_PAIR_CASES)
    assert not complaints, (
        "обработчики идут через слой ответа, но пары транспортов у них нет ни в "
        "реестре `POST_PAIR_CASES`, ни в `CONFIRMED_DELETE_ROUTES`:\n  "
        + "\n  ".join(complaints)
    )


def test_control_a_handler_without_a_case_reddens_the_closure():
    """Отрицательный контроль: реестр без правки расписания — замыкание называет её."""
    stripped = tuple(case for case in POST_PAIR_CASES if case.key != SCHEDULES_UPDATE)
    assert len(stripped) < len(POST_PAIR_CASES), "контроль ничего не снял"
    assert SCHEDULES_UPDATE in _closure_complaints(stripped), (
        "замыкание не заметило обработчика без единого случая — правило вакуумно"
    )
