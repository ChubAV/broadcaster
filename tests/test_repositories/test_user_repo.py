import pytest
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.auth_service import hash_password


# ДВА ТЕСТА СНЯТЫ ВМЕСТЕ СО СВОИМ ПРЕДМЕТОМ ПЛАНОМ 06-09, А НЕ ПЕРЕНАЦЕЛЕНЫ.
# Они проверяли `get_all_users()` и `search_users()` — выборки БЕЗ предела, чьим
# единственным потребителем был админский список. Список переведён на
# `app/application/admin/users_query.py` со страницами по 50 и точным `COUNT`
# (D-33), методов больше нет, и проверять стало нечего.
#
# Перенацелить их на новый модуль было бы хуже, чем снять: свойства там другие
# (счёт совпадает с содержимым, поиск складывает кириллицу, страница не
# пересекается с соседней), и они уже проверены на своём месте —
# `tests/test_pages/test_admin_users.py`. Тест, сохранивший имя и сменивший
# предмет, читается как непрерывность покрытия там, где её не было.
#
# Что выборка без предела не вернулась, стережёт
# `test_the_unlimited_select_left_the_repository` в том же файле.


@pytest.mark.asyncio
async def test_count_all(db_session):
    repo = UserRepository(db_session)
    u1 = User(email="a@test.com", password_hash=hash_password("p"), name="A")
    db_session.add(u1)
    await db_session.commit()

    count = await repo.count_all()
    assert count == 1
