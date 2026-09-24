---
phase: "15"
slug: "uprochnenie-i-svodnyy-obhod-47-form"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
validated: "2026-09-24"
created: "2026-09-23"
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
>
> Засеяно шагом 5.5 `/gsd-plan-phase 15` из раздела `## Validation Architecture`
> файла `15-RESEARCH.md` — команды и времена там ЗАМЕРЕНЫ исполнением 2026-09-23,
> а не оценены. Карта «Per-Task Verification Map» заполняется планировщиком,
> когда планы существуют.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest` 9.0.2+ с `pytest-asyncio` 1.3.0+ (`[dependency-groups].dev`, `pyproject.toml:39-41`) |
| **Config file** | **none** — ни `pytest.ini`, ни `setup.cfg`, ни `[tool.pytest.*]`. Маркеры регистрируются хуком `pytest_configure` в `tests/conftest.py:485`. Новых настроек фаза не заводит |
| **Quick run command** | `uv run pytest tests/test_planning/ tests/test_templates/ -q` |
| **Full suite command** | `just test` (== `uv run pytest tests/ -v`) |
| **Estimated runtime** | ~15.7 s быстрый прогон (замерено: 0.71 s + 14.96 s) |
| **Build command** | `uv run python -m compileall -q app main.py tests` (объявлен `workflow.build_command`) |
| **Разделение диагноза** | `-m "not planning"` — продуктовая половина; `-m planning` — половина записи. ⚠️ Отбор есть инструмент РАЗБОРА, а не разрешение не прогонять: выключение каталога `tests/test_planning/` запрещено прохибицией плана 10-26 |

---

## Sampling Rate

- **After every task commit:** `uv run pytest tests/test_planning/ tests/test_templates/ -q` — 15.7 s, покрывает приборы переписи и разметки, то есть предмет большинства задач фазы
- **After every plan wave:** `uv run pytest tests/test_planning/ tests/test_templates/ tests/test_pages/ -q` плюс `uv run python -m compileall -q app main.py tests`
- **Before `/gsd-verify-work`:** `just test` — полная суита зелена
- **Max feedback latency:** ~16 s

⚠️ **Названное входное условие фазы.** Полная суита КРАСНА без всякого вклада Фазы 15:
`test_no_walkthrough_declares_itself_passed_with_empty_marks` падает на `14-UAT.md`
(9 таблиц отметок, 0 заполненных). Решение владельца `chubav` 2026-09-23 (RESEARCH.md,
Open Questions #4): **шапка `14-UAT.md` возвращается в нетерминальное состояние отдельной
задачей фазы**; отметки НЕ заполняются — правило самозаверения это прямо запрещает.
Пока задача не исполнена, гейт фазы обещать зелёную полную суиту не может.

---

## Per-Task Verification Map

*Заполнено `/gsd-validate-phase 15` 2026-09-24 после исполнения всех 14 планов. Прежняя пометка «заполняется планировщиком — на момент засева планов нет» устарела с исполнением; четыре селектора засева (`no_manual_fetch`, `push_url_decision`, `not_renamed`, `phase_10_resolved`) не отбирали ни одного теста — исполнители назвали правила иначе; селекторы ниже заменены по замеру, прежние названы здесь, а не стёрты.*

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 15-02 T1–T3 | 15-02 | 1 | FORM-01 | — | инвентарь мест письма сходится объявленным числом (49 мест / 27 файлов), ни одно место не выпало молча | unit | `uv run pytest tests/test_templates/test_form_inventory.py -x -q` | ✅ | ✅ green (24) |
| 15-10 T1–T2 | 15-10 | 2 | FORM-01 | — | связка «форма-триггер → модалка с `hx-post`» доказана для всех 18 триггеров (D-07) четырьмя счетами | unit | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -k modal_linkage -q` | ✅ | ✅ green (12) |
| — | до фазы (Ф-14) | — | FORM-01 | — | обработчиковая половина закрыта: отставание 0 и обход не слеп | unit | `uv run pytest tests/test_pages/test_htmx_gates.py -k "backlog or named_zero" -q` | ✅ | ✅ green (3) |
| 15-04 T1 | 15-04 | 1 | FETCH-03 | — | **ЗАПРЕТ** ручной сборки запроса в `app/templates/` — контракт, а не счётчик | unit | `uv run pytest tests/test_templates/test_htmx_inventory.py -k fetch_prohibition -q` | ✅ | ✅ green (6) |
| 15-04 T1 | 15-04 | 1 | FETCH-03 | — | ноль не есть слепота сети: на синтетическом дереве та же сеть находит и называет | unit | `uv run pytest tests/test_templates/test_htmx_inventory.py -k control_negative -q` | ✅ | ✅ green (7) |
| 15-11 T1 | 15-11 | 2 | QUAL-04 | — | по каждому месту письма записано решение трёх случаев; реестр ↔ инвентарь — биекция (реестр живёт в `test_htmx_gates.py`, а не в `test_form_inventory.py`) | unit | `uv run pytest tests/test_pages/test_htmx_gates.py -k push_url_decisions -q` | ✅ | ✅ green |
| 15-11 T2 | 15-11 | 2 | QUAL-04 | — | `hx-push-url` запрещён на маршрутах «изменяет данные» (D-13) | unit | `uv run pytest tests/test_pages/test_htmx_gates.py -k push_url -q` | ✅ | ✅ green (24) |
| 15-11 T1–T3 | 15-11 | 2 | QUAL-04 | — | «атрибута нет» есть РЕШЕНИЕ, а не пробел: ноль атрибута доказан от вакуума | unit | `uv run pytest tests/test_pages/test_htmx_gates.py -k "push_url and control" -q` | ✅ | ✅ green (12) |
| 15-05 T1 | 15-05 | 1 | GATE-09 | — | условный `hx-post` в шаблонах == 0, перечень объявлен ПУСТЫМ явно + контроль от вакуума | unit | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -k conditional_hx_post -q` | ✅ | ✅ green (7) |
| 15-05 T2 | 15-05 | 1 | GATE-09 | — | 12 мест условной сборки прочих `hx-*` объявлены числом и составом (улика для человека) | unit | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -k conditional_hx_attributes -q` | ✅ | ✅ green (3) |
| 15-05 T3 | 15-05 | 1 | GATE-09 | — | обвод фокуса органа снятия объявлен в CSS (машинная половина пункта 2) | unit | `uv run pytest tests/test_templates/ -k focus_ring -q` | ✅ | ✅ green (3) |
| 15-06 T1, 15-14 T1 | 15-06, 15-14 | 1, 4 | GATE-09 | — | `14-UAT.md` и `15-UAT.md` не объявляют себя закрытыми шире своих отметок | unit | `uv run pytest tests/test_planning/test_the_walkthrough_cannot_self_certify.py -q` | ✅ | ✅ green (5) |
| 15-03 T1–T3 | 15-03 | 1 | GATE-10 | — | число пар `*_degrades_without_htmx` ↔ `*_degrades_without_alpine` сходится ОБЪЯВЛЕННЫМ предикатом | unit | `uv run pytest tests/test_templates/test_degradation_pairs.py -q` | ✅ | ✅ green (15) |
| 15-03 T2 | 15-03 | 1 | GATE-10 | — | ни один существующий `*_degrades_without_alpine` не переименован (критерий 4) — объявленные имена живут в суите | unit | `uv run pytest tests/test_templates/test_degradation_pairs.py -k "declared_alpine or alpine_list" -q` | ✅ | ✅ green |
| 15-01 T1–T3, 15-12 T1–T3 | 15-01, 15-12 | 1, 2 | критерий 6 | — | перепись воспроизводима (697 на 156 планах; 650 на 142 — сохранено); биекция перепись ↔ реестр; класс и диспозиция из объявленных перечней | unit | `uv run pytest tests/test_planning/test_plan_prohibitions_census.py -q` | ✅ | ✅ green (64) |
| 15-13 T2 | 15-13 | 3 | критерий 6 | — | каждый из 321 запрета Фазы 10 РЕШЁН или несёт названную причину из объявленного перечня (ослаблено против «ни один не `unresolved`» решением владельца: 70 `product-invariant` → require-enforcement остаются открытыми по числу) | unit | `uv run pytest tests/test_planning/test_plan_prohibitions_census.py -k closing_rule -q` | ✅ | ✅ green |
| 15-01 T3, 15-13 T1 | 15-01, 15-13 | 1, 3 | критерий 6 (D-05) | — | у каждого из 61 запрета с `verification: test` предъявлено существование теста либо записано его отсутствие | unit | `uv run pytest tests/test_planning/test_plan_prohibitions_census.py -k "declared_test_exists or declared_rule" -q` | ✅ | ✅ green |
| 15-08 T1–T2 | 15-08 | 1 | D-18.1 (CR-01) | — | правка расписания на невалидной сохранённой зоне не даёт пятисотки И записывает валидную зону | integration | `uv run pytest tests/test_pages/test_editor_schedules.py -k malformed_stored -q` | ✅ | ✅ green (32) |
| 15-08 T3 | 15-08 | 1 | D-18.2 | — | запрет огульного `except` в `schedule_rules.py` принуждён разбором `ast` тела, не грепом | unit | `uv run pytest tests/test_services/ -k schedule_rules_gate -q` | ✅ | ✅ green (9) |
| 15-07 T1–T3 | 15-07 | 1 | D-18.3 | — | орган снятия плашки: два `aria-label` различимы; компенсация перекрытия объявлена | unit | `uv run pytest tests/test_templates/ -k banner_dismiss -q` | ✅ | ✅ green (21) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_planning/test_plan_prohibitions_census.py` — прибор переписи, покрывает критерий 6. **Обязателен `pytestmark = pytest.mark.planning`.** Не утверждает вердикт своей фазы и не несёт литерала незакрытого состояния (`unresolved == 329` запрещено)
- [x] `15-PROHIBITIONS-SUBJECT.md` — реестр решений по форме `10-PROHIBITIONS-SUBJECT.md` (`status: subject`, поля `permit_*` заводит ОТВЕТ ВЛАДЕЛЬЦА): строка на каждый из 650, класс полем, диспозиция из объявленного перечня
- [x] `tests/test_templates/test_form_inventory.py` — инвентарь 49/27 + реестр решений `hx-push-url`; покрывает FORM-01 и QUAL-04. Объявленные литералы, летопись 47 → 49
- [x] `tests/test_templates/test_degradation_pairs.py` — счёт пар по ОБЪЯВЛЕННОМУ предикату + перечень пяти основ alpine литералом; покрывает GATE-10
- [x] новая группа в `tests/test_templates/test_htmx_inventory.py` — ЗАПРЕТ `fetch(` == 0 (FETCH-03), рядом со счётчиком G-22, с летописью имени `test_no_manual_fetch_remains`
- [x] новые группы в `tests/test_templates/test_htmx_markup_gates.py` — связка D-07; условный `hx-post` == 0 с явно пустым перечнем; 12 мест условной сборки прочих `hx-*`
- [x] новая группа в `tests/test_pages/test_htmx_gates.py` — запрет `hx-push-url` на маршрутах «изменяет данные» (дом определён Ф-13: слой ответа, не пакет разметки)
- [x] контроли от вакуума на `tmp_path` — по ОДНОМУ на каждый объявленный ноль (три ноля: `fetch(`, условный `hx-post`, `hx-push-url`). Форма — `tests/test_templates/test_htmx_inventory.py:1312-1400`
- [x] абзац «ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ» в докстринге КАЖДОГО нового файла (D-16, образец `tests/test_pages/test_impersonation_gate.py:373,456,631,696`)
- [x] `15-UAT.md` — девять пунктов, **9 таблиц «Отметка о закрытии» с поимённым заполнением** (дата, браузер, ОС, наблюдатель), раздел улики ОТДЕЛЬНО от `result`
- [x] задача, возвращающая шапку `14-UAT.md` в нетерминальное состояние (решение владельца, Open Questions #4) — без неё `tests/test_planning/` красен
- [x] Framework install: **не требуется** — pytest, pytest-asyncio, PyYAML на месте

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Девять именованных пунктов ручного обхода, включая пункт 9 (слепая зона условной сборки атрибутов) и дословно вписанное в один из девяти приземление фокуса на location-пути | GATE-09 | Суита идёт на in-memory SQLite через `ASGITransport` и **не исполняет ни строчки JS**; браузерного привода нет, `E2E-01` отклонён и отложен на веху v2.2 | Пункты 1–8 принимаются записью своих фаз (7–11) по D-15 и не переподтверждаются. Глазами смотрится пункт 9. Машинный замер пишется РАЗДЕЛОМ УЛИКИ; `result` и отметки о закрытии заполняет человек поимённо (D-17) — иначе `test_the_walkthrough_cannot_self_certify.py` краснит прогон |
| Виден ли обвод фокуса органа снятия плашки глазом; срабатывает ли пробел; нарисованное перекрытие | D-18.3 | `app/static/css/app.css:1255-1258` дословно запрещает объявлять отрисовку пройденной по зелени правил | Окно 1280 px. Замер 2026-09-14: видимого столкновения текста с крестиком НЕТ — подтвердить или опровергнуть заново. Проверить, что при двойной аварии два `aria-label` различимы на слух скринридера |
| Отметки `14-UAT.md` | вход фазы | Правило самозаверения прямо запрещает заполнить отметки ради зелени | Решение владельца 2026-09-23: шапка возвращается в нетерминальное состояние, отметки НЕ заполняются |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 20s
- [x] Каждый объявленный ноль несёт контроль от вакуума (три ноля)
- [x] Каждый новый файл несёт абзац «ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ» (D-16)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-09-24 (`/gsd-validate-phase 15`, in `/gsd-execute-phase 15`)

---

## Validation Audit 2026-09-24

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Замер: 20 строк карты прогнаны командами на дереве после плана 15-14 (полная суита на нём же — `3867 passed, 0 failed`). Все требования COVERED. Четыре селектора засева не отбирали тестов (см. карту) — это расхождение ИМЁН, а не пробел покрытия: поведение под ними принуждено правилами с иными именами, отобранными заново. Одна строка сужена решением владельца, а не аудитом: критерий 6 закрыт правилом «решён или названа причина», а 70 запретов класса `product-invariant` остаются открытыми по его выбору `require-enforcement` (запись — `15-12-SUMMARY.md`, `15-13-SUMMARY.md`). Пункты «Wave 0» отмечены по факту существования артефактов; таблицы отметок `15-UAT.md` существуют и ПУСТЫ — их заполняет человек (D-17), и отметка «Wave 0» этого не утверждает.
