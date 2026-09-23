---
phase: "15"
slug: "uprochnenie-i-svodnyy-obhod-47-form"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
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

*Заполняется планировщиком — на момент засева планов нет. Ниже — карта требований фазы на
средства проверки, снятая разведкой; планировщик разносит её по задачам.*

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | FORM-01 | — | инвентарь мест письма сходится объявленным числом (49 мест / 27 файлов), ни одно место не выпало молча | unit | `uv run pytest tests/test_templates/test_form_inventory.py -x -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | FORM-01 | — | связка «форма-триггер → модалка с `hx-post`» доказана для всех 18 триггеров (D-07) | unit | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -k modal_linkage -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | FORM-01 | — | обработчиковая половина закрыта: отставание 0 и обход не слеп | unit | `uv run pytest tests/test_pages/test_htmx_gates.py -k "backlog or named_zero" -q` | ✅ | ⬜ pending |
| TBD | TBD | TBD | FETCH-03 | — | **ЗАПРЕТ** «`fetch(` в `app/templates/` == 0» — контракт, а не счётчик | unit | `uv run pytest tests/test_templates/test_htmx_inventory.py -k no_manual_fetch -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | FETCH-03 | — | ноль не есть слепота сети: на синтетическом дереве та же сеть находит и называет | unit | `uv run pytest tests/test_templates/test_htmx_inventory.py -k control_negative -q` | ✅ форма | ⬜ pending |
| TBD | TBD | TBD | QUAL-04 | — | по каждому из 49 мест записано решение трёх случаев; реестр ↔ инвентарь — биекция | unit | `uv run pytest tests/test_templates/test_form_inventory.py -k push_url_decision -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | QUAL-04 | — | `hx-push-url` запрещён на маршрутах «изменяет данные» (D-13) | unit | `uv run pytest tests/test_pages/test_htmx_gates.py -k push_url -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | QUAL-04 | — | «атрибута нет» есть РЕШЕНИЕ, а не пробел: ноль атрибута доказан от вакуума | unit | `uv run pytest tests/test_pages/test_htmx_gates.py -k "push_url and control" -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | GATE-09 | — | условный `hx-post` в шаблонах == 0, перечень объявлен ПУСТЫМ явно + контроль от вакуума | unit | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -k conditional_hx_post -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | GATE-09 | — | 12 мест условной сборки прочих `hx-*` объявлены числом и составом (улика для человека) | unit | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -k conditional_hx_attributes -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | GATE-09 | — | обвод фокуса органа снятия объявлен в CSS (машинная половина пункта 2) | unit | `uv run pytest tests/test_templates/ -k focus_ring -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | GATE-09 | — | `15-UAT.md` не объявляет себя закрытым шире своих отметок | unit | `uv run pytest tests/test_planning/test_the_walkthrough_cannot_self_certify.py -q` | ✅ (красно сегодня) | ⬜ pending |
| TBD | TBD | TBD | GATE-10 | — | число пар `*_degrades_without_htmx` ↔ `*_degrades_without_alpine` сходится ОБЪЯВЛЕННЫМ предикатом | unit | `uv run pytest tests/test_templates/test_degradation_pairs.py -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | GATE-10 | — | ни один существующий `*_degrades_without_alpine` не переименован (критерий 4) | unit | `uv run pytest tests/test_templates/test_degradation_pairs.py -k not_renamed -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | критерий 6 | — | перепись 650 воспроизводима; биекция перепись ↔ реестр; диспозиция из объявленного перечня | unit | `uv run pytest tests/test_planning/test_plan_prohibitions_census.py -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | критерий 6 | — | ни один запрет Фазы 10 не остаётся `unresolved` | unit | `uv run pytest tests/test_planning/test_plan_prohibitions_census.py -k phase_10_resolved -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | критерий 6 (D-05) | — | у каждого из 61 запрета с `verification: test` предъявлено существование теста | unit | `uv run pytest tests/test_planning/test_plan_prohibitions_census.py -k declared_test_exists -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | D-18.1 (CR-01) | — | правка расписания на невалидной сохранённой зоне не даёт пятисотки И записывает валидную зону | integration | `uv run pytest tests/test_pages/test_editor_schedules.py -k malformed_stored -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | D-18.2 | — | запрет огульного `except` в `schedule_rules.py` принуждён разбором `ast` тела, не грепом | unit | `uv run pytest tests/test_services/ -k schedule_rules_gate -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | D-18.3 | — | орган снятия плашки: два `aria-label` различимы; компенсация перекрытия объявлена | unit | `uv run pytest tests/test_templates/ -k banner_dismiss -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_planning/test_plan_prohibitions_census.py` — прибор переписи, покрывает критерий 6. **Обязателен `pytestmark = pytest.mark.planning`.** Не утверждает вердикт своей фазы и не несёт литерала незакрытого состояния (`unresolved == 329` запрещено)
- [ ] `15-PROHIBITIONS-SUBJECT.md` — реестр решений по форме `10-PROHIBITIONS-SUBJECT.md` (`status: subject`, поля `permit_*` заводит ОТВЕТ ВЛАДЕЛЬЦА): строка на каждый из 650, класс полем, диспозиция из объявленного перечня
- [ ] `tests/test_templates/test_form_inventory.py` — инвентарь 49/27 + реестр решений `hx-push-url`; покрывает FORM-01 и QUAL-04. Объявленные литералы, летопись 47 → 49
- [ ] `tests/test_templates/test_degradation_pairs.py` — счёт пар по ОБЪЯВЛЕННОМУ предикату + перечень пяти основ alpine литералом; покрывает GATE-10
- [ ] новая группа в `tests/test_templates/test_htmx_inventory.py` — ЗАПРЕТ `fetch(` == 0 (FETCH-03), рядом со счётчиком G-22, с летописью имени `test_no_manual_fetch_remains`
- [ ] новые группы в `tests/test_templates/test_htmx_markup_gates.py` — связка D-07; условный `hx-post` == 0 с явно пустым перечнем; 12 мест условной сборки прочих `hx-*`
- [ ] новая группа в `tests/test_pages/test_htmx_gates.py` — запрет `hx-push-url` на маршрутах «изменяет данные» (дом определён Ф-13: слой ответа, не пакет разметки)
- [ ] контроли от вакуума на `tmp_path` — по ОДНОМУ на каждый объявленный ноль (три ноля: `fetch(`, условный `hx-post`, `hx-push-url`). Форма — `tests/test_templates/test_htmx_inventory.py:1312-1400`
- [ ] абзац «ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ» в докстринге КАЖДОГО нового файла (D-16, образец `tests/test_pages/test_impersonation_gate.py:373,456,631,696`)
- [ ] `15-UAT.md` — девять пунктов, **9 таблиц «Отметка о закрытии» с поимённым заполнением** (дата, браузер, ОС, наблюдатель), раздел улики ОТДЕЛЬНО от `result`
- [ ] задача, возвращающая шапку `14-UAT.md` в нетерминальное состояние (решение владельца, Open Questions #4) — без неё `tests/test_planning/` красен
- [ ] Framework install: **не требуется** — pytest, pytest-asyncio, PyYAML на месте

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Девять именованных пунктов ручного обхода, включая пункт 9 (слепая зона условной сборки атрибутов) и дословно вписанное в один из девяти приземление фокуса на location-пути | GATE-09 | Суита идёт на in-memory SQLite через `ASGITransport` и **не исполняет ни строчки JS**; браузерного привода нет, `E2E-01` отклонён и отложен на веху v2.2 | Пункты 1–8 принимаются записью своих фаз (7–11) по D-15 и не переподтверждаются. Глазами смотрится пункт 9. Машинный замер пишется РАЗДЕЛОМ УЛИКИ; `result` и отметки о закрытии заполняет человек поимённо (D-17) — иначе `test_the_walkthrough_cannot_self_certify.py` краснит прогон |
| Виден ли обвод фокуса органа снятия плашки глазом; срабатывает ли пробел; нарисованное перекрытие | D-18.3 | `app/static/css/app.css:1255-1258` дословно запрещает объявлять отрисовку пройденной по зелени правил | Окно 1280 px. Замер 2026-09-14: видимого столкновения текста с крестиком НЕТ — подтвердить или опровергнуть заново. Проверить, что при двойной аварии два `aria-label` различимы на слух скринридера |
| Отметки `14-UAT.md` | вход фазы | Правило самозаверения прямо запрещает заполнить отметки ради зелени | Решение владельца 2026-09-23: шапка возвращается в нетерминальное состояние, отметки НЕ заполняются |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] Каждый объявленный ноль несёт контроль от вакуума (три ноля)
- [ ] Каждый новый файл несёт абзац «ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ» (D-16)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
