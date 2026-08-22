---
schema_version: 1
open_count: 1
waived_count: 0
fixed_count: 0
total_count: 1
last_updated: 2026-08-22T07:47:15.265Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 06 | deviation | tests/test_pages/test_ads_editor.py |  | test_image_base_url_comes_from_app_settings краснеет только в общем прогоне; контрольный прогон без файла тестов плана 06-04 даёт тот же красный — предсуществующая порядковая зависимость суиты | open |  | 2026-08-22T07:47:15.265Z |  |

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
  }
]
````
