from datetime import datetime

from sqlalchemy import and_, func, not_, or_, select

from app.models.subscription import Subscription
from app.models.user import User
from app.repositories.base import BaseRepository


def _has_active_subscription(*conditions):
    """«У пользователя есть АКТИВНАЯ строка подписки, отвечающая условиям».

    Активность спрашивается ВСЕГДА и в условия вызывающего не входит: история
    подписок пользователя лежит в тех же строках, и отбор по сроку без вопроса
    про активность выдал бы доступ по ОТМЕНЁННОМУ периоду. Частичный уникальный
    индекс `uq_subscriptions_active_user` гарантирует не более одной активной
    строки на пользователя, поэтому «есть ли такая строка» здесь тождественно
    «такова ли ЕГО строка».
    """
    return (
        select(Subscription.id)
        .where(Subscription.user_id == User.id, Subscription.is_active.is_(True), *conditions)
        .exists()
    )


def _comped():
    return _has_active_subscription(Subscription.has_free_access.is_(True))


def _live_by_term(now: datetime):
    # Сравнение СТРОГОЕ — той же строгости, что `subscription_is_live`: момент,
    # равный `now`, живым не считается, оплаченный момент уже прошёл.
    return _has_active_subscription(Subscription.expires_at > now)


def _access_open(now: datetime):
    return _has_active_subscription(
        or_(Subscription.has_free_access.is_(True), Subscription.expires_at > now)
    )


# ⚠️ ПЕРЕВОД ЕДИНСТВЕННОГО ВЕРДИКТА ДОСТУПА В ЯЗЫК ЗАПРОСА, А НЕ ВТОРОЕ ПРАВИЛО.
#
# Правило доступа объявлено ОДИН раз — `access_is_open`
# (`app/application/billing/subscription_period.py`), и объявлено на Python:
# модуль срока подписки по своей объявленной границе ничего не знает про сессию
# SQLAlchemy. При этом счётчик и страница админского списка обязаны считаться
# ОДНИМ выражением (D-34), а это требует отбора ПО ДОСТУПУ в самом запросе, до
# `OFFSET`. Отсюда перевод.
#
# ⚠️ ПОЧЕМУ ОН ЛЕЖИТ ЗДЕСЬ, А НЕ В `app/application/admin/users_query.py`, КУДА
# ПРОСИТСЯ ПО ПРЕДМЕТУ. Признак бесплатного доступа читается в `app/application/`
# РОВНО ОДНИМ файлом — предикатом доступа, — и это машинный гейт
# (`test_the_free_access_flag_is_read_in_exactly_one_place_of_the_decision`), а
# не соглашение: второе чтение признака в прикладной логике развело бы одно
# правило по двум выражениям. Слой доступа к данным под гейт не подпадает и
# подпадать не должен — SQL-выражения по нашим таблицам это его работа, а не
# работа прикладного модуля. Ослаблять гейт ради удобной раскладки файлов
# нельзя: следующий читатель добавит третье чтение уже без вопросов.
#
# Цена перевода названа вслух и оплачена тестом: расхождение с оригиналом падает
# `test_the_sql_axis_agrees_with_the_single_python_verdict`
# (`tests/test_pages/test_admin_users.py`), который прогоняет ОБА выражения по
# одной популяции. Без него разойтись было бы на чём — хватило бы забыть про
# активность строки или ослабить строгость сравнения дат, и администратор увидел
# бы «открыт» у человека, которому продукт уже отказывает.
#
# ТРИ ЗНАЧЕНИЯ РАЗБИВАЮТ ПОПУЛЯЦИЮ, А НЕ ПЕРЕСЕКАЮТ ЕЁ: «бесплатно» забирает
# льготных целиком (в том числе с мёртвой датой), «открыт» — оставшихся живых по
# сроку, «истёк» — дополнение до всех, включая тех, у кого строки подписки нет
# вовсе. Пересечение показало бы человека под двумя взаимоисключающими ярлыками,
# а недостача оставила бы кого-то ненаходимым НИ ОДНИМ фильтром.
#
# ⚠️ ПОРЯДОК ВЕТОК ТОТ ЖЕ, ЧТО В ПРЕДИКАТЕ И В РАЗМЕТКЕ: ЛЬГОТА ПЕРВОЙ. Ветка
# «открыт», оказавшись выше, забрала бы льготного себе и назвала его оплаченным —
# то есть спрятала бы от администратора его собственное действие.
_ACCESS_AXIS_CLAUSES = {
    "comped": lambda now: _comped(),
    "open": lambda now: and_(_live_by_term(now), not_(_comped())),
    "expired": lambda now: not_(_access_open(now)),
}


def access_axis_clause(value: str | None, now: datetime):
    """Условие отбора по оси доступа; `None` — «все», условия нет.

    ⚠️ САНАЦИЯ ВСТРОЕНА В ПОИСК УСЛОВИЯ, А НЕ ПРИСТАВЛЕНА К НЕМУ СБОКУ. Значение
    приезжает строкой запроса — из ссылки, закладки или чужого сообщения
    (T-06-USR3) — и служит КЛЮЧОМ в замкнутом словаре. Неизвестный ключ не
    находит условия, то есть означает «все», и в выражение не попадает вовсе: ни
    сырым, ни экранированным. Отдельный отсекатель рядом можно было бы забыть
    позвать; словарь забыть нельзя — без него нет условия.
    """
    builder = _ACCESS_AXIS_CLAUSES.get(value or "")
    return builder(now) if builder is not None else None


class UserRepository(BaseRepository[User]):
    """Доступ к пользователям.

    ⚠️ ВЫБОРОК БЕЗ ПРЕДЕЛА ЗДЕСЬ БОЛЬШЕ НЕТ, И ЭТО РЕШЕНИЕ (D-33, T-06-USR2).
    Тут жили `get_all_users()` и `search_users()` — обе `select(User)` без
    `limit`, обе с единственным потребителем: админским списком, который тянул
    ими всю таблицу пользователей на одну страницу. План 06-09 перевёл список на
    `app/application/admin/users_query.py` — страницы по 50 с точным `COUNT` по
    ТОМУ ЖЕ выражению фильтров, — и потребителей у обоих методов не осталось ни
    одного.

    Сняты они вместе со своими тестами, а не оставлены «на всякий случай»:
    оставленный метод есть приглашение вернуть страницу к полной таблице одной
    строкой правки, и вернувший её не узнает, что нарушил решение, — тест списка
    останется зелёным. Отсутствие закреплено
    `test_the_unlimited_select_left_the_repository`.

    Поиск переехал НЕ ДОСЛОВНО: `ilike` заменён явным приведением обеих сторон
    к одному регистру. Причина в модуле выборки — `ilike` в SQLite складывает
    регистр только для латиницы, и поиск по русскому имени вёл бы себя в суите
    иначе, чем в бою.
    """

    def __init__(self, session):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar() or 0
