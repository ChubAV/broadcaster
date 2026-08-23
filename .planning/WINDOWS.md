---
schema_version: 1
open_count: 2
waived_count: 0
fixed_count: 0
total_count: 2
last_updated: 2026-08-23T01:59:34.260Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 06 | deviation | tests/test_pages/test_ads_editor.py |  | test_image_base_url_comes_from_app_settings краснеет только в общем прогоне; контрольный прогон без файла тестов плана 06-04 даёт тот же красный — предсуществующая порядковая зависимость суиты | open |  | 2026-08-22T07:47:15.265Z |  |
| 2 | 06 | deviation | app/application/admin/incidents.py |  | Адрес вида failure_spike ведёт в /history?status=fail — раздел истории САМОГО администратора, а не общесистемный: маршрут живой и тест его находит, но по нему видны отказы одного человека, тогда как признак считает весь сервис. D-48 предписывает «Историю с фильтром» буквально, поэтому план 06-10 адрес НЕ менял; выбор между буквой D-48 и /admin/logs?level=error — решение владельца | open |  | 2026-08-23T01:59:34.260Z |  |

````json
[
  {
    "id": 1,
    "kind": "deviation",
    "phase": "06",
    "file": "tests/test_pages/test_ads_editor.py",
    "line": null,
    "description": "test_image_base_url_comes_from_app_settings краснеет только в общем прогоне; контрольный прогон без файла тестов плана 06-04 даёт тот же красный — предсуществующая порядковая зависимость суиты",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-22T07:47:15.265Z",
    "resolved_at": null
  },
  {
    "id": 2,
    "kind": "deviation",
    "phase": "06",
    "file": "app/application/admin/incidents.py",
    "line": null,
    "description": "Адрес вида failure_spike ведёт в /history?status=fail — раздел истории САМОГО администратора, а не общесистемный: маршрут живой и тест его находит, но по нему видны отказы одного человека, тогда как признак считает весь сервис. D-48 предписывает «Историю с фильтром» буквально, поэтому план 06-10 адрес НЕ менял; выбор между буквой D-48 и /admin/logs?level=error — решение владельца",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-23T01:59:34.260Z",
    "resolved_at": null
  }
]
````
