"""Читающий JSON-API биллинга.

ПОКУПКИ ЗДЕСЬ БОЛЬШЕ НЕТ. `POST /api/billing/purchase` снесён планом 05-04
вместе со своей моделью тела запроса (D-24): после перевода покупки пакета на
форму раздела у маршрута не осталось ни одного потребителя, а отдавал он
`yookassa_payment_id` прямо в браузер — то есть ключ, которым до появления
IP-гарда подделывалось уведомление об успешной оплате.

ТРИ ЧТЕНИЯ ОСТАЮТСЯ. `balance`, `packages` и `transactions` сохранены одним
решением этого же плана: они читающие, покрыты тестами ниже, и удаление
объявленного читающего API — отдельный вопрос совместимости, а не следствие
перевода покупки на форму.
"""
import pytest


@pytest.mark.asyncio
async def test_the_json_purchase_route_no_longer_answers(client):
    """Мёртвая поверхность снесена, а не оставлена «на всякий случай».

    Запрос идёт БЕЗ учётных данных намеренно: живой маршрут ответил бы отказом
    доступа, и именно этим отличается «маршрут есть, но не пускает» от
    «маршрута нет».
    """
    response = await client.post(
        "/api/billing/purchase", json={"package_index": 0}
    )

    assert response.status_code in (404, 405), (
        "JSON-маршрут покупки пакета всё ещё отвечает"
    )


@pytest.mark.asyncio
async def test_get_balance(client, auth_headers):
    response = await client.get("/api/billing/balance", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "balance" in data


@pytest.mark.asyncio
async def test_list_packages(client, auth_headers):
    response = await client.get("/api/billing/packages", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "packages" in data
    assert len(data["packages"]) == 3


@pytest.mark.asyncio
async def test_get_transactions(client, auth_headers):
    response = await client.get("/api/billing/transactions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "transactions" in data
