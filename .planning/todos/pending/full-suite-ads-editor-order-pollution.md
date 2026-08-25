---
id: full-suite-ads-editor-order-pollution
created: 2026-08-21
source: 05.1 wave-9 post-merge gate; baseline confirmed on 54a121a
area: tests / порядок исполнения сюиты
severity: medium
status: pending
audit_acknowledged:
  milestone: v2.0
  at: 2026-08-25
---

# `test_image_base_url_comes_from_app_settings` красный только в полном прогоне

## Что осталось

`tests/test_pages/test_ads_editor.py::test_image_base_url_comes_from_app_settings`
падает **исключительно** при прогоне всей сюиты и зелёный при любом сужении.
Отказ **доэтотный** — не привнесён фазой 05.1.

| Прогон | Коммит | Итог |
|---|---|---|
| Полная сюита, домердж | `54a121a` | `1 failed, 1751 passed` (19:20) |
| Полная сюита, после волны 9 | `590766e` | `1 failed, 1759 passed` (28:36) |
| Один тест | `590766e` | `1 passed` |
| Весь файл `test_ads_editor.py` | `590766e` | `36 passed` |
| Файлы волны 9 + `test_ads_editor.py` | `590766e` | `149 passed` |

Тот же тест, то же утверждение, тот же результат до и после — волна 9 добавила
восемь зелёных тестов и ни одного красного. Файлы, которые волна трогала
(`test_0020_flat_subscription.py`, `test_payment_service.py`,
`test_billing_section.py`), отравителями **не являются** — проверено прямым
прогоном в порядке сюиты.

## Симптом

```
assert 'https://cdn.bound-to-app-settings.test/bucket/u1/photo.jpg' in <listing.text>
tests/test_pages/test_ads_editor.py:264
```

Страница `/ads` отдаёт `200`, но ссылки на изображение в разметке нет. Соседний
тест того же контракта (`test_editor_s3_public_url_global_comes_from_app_settings`)
при этом зелёный — значит привязка `create_app(settings=...)` работает, а не
находится сам посев. Рабочая гипотеза: утечка состояния между файлами (владелец
посеянного объявления не совпадает с зарегистрированным `cdn_client`
пользователем), а не дефект `get_image_url`.

## Как найти

Бисекция по файлам сюиты: половина файлов до `test_pages/test_ads_editor.py`
плюс сам файл, затем сужение. Каждый полный прогон ~20–30 минут, поэтому
бисекция дешевле лобового перебора.

## Почему это заведено, а не починено

Работа лежит вне предмета фазы 05.1 (единая подписка). Решение владельца
2026-08-21: завести и идти дальше.
