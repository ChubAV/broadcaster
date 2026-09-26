---
phase: "15"
slug: "uprochnenie-i-svodnyy-obhod-47-form"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
validated: "2026-09-26"
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
| 15-15 T1 | 15-15 | 5 | критерий 6 | T-15-69, T-15-70, T-15-71 | числа Фазы 15 меряются над фиксированным набором 156 файлов; новые планы держит растущая биекция с реестром без литерала | unit | `uv run pytest tests/test_planning/ -q -p no:randomly` | ✅ | ✅ green (208) |
| 15-15 T2 | 15-15 | 5 | критерий 6 (IN-06) | T-15-72 | прямые импортёры PyYAML объявлены перечнем; новый импортёр называется | unit | `uv run pytest tests/test_planning/test_plan_prohibitions_census.py -q -p no:randomly -k yaml` | ✅ | ✅ green (2) |
| 15-16 T1 | 15-16 | 5 | долг D-18 (WR-01) | T-15-73, T-15-75 | правка из редактора на неисполнимых значениях отказывает с `SCHEDULE_VALUES_OUT_OF_DOMAIN`, строка не тронута | integration | `uv run pytest tests/test_pages/test_editor_schedules.py -q -p no:randomly -k "malformed_stored or second_line"` | ✅ | ✅ green (40) |
| 15-16 T2 | 15-16 | 5 | долг D-18 (WR-02) | T-15-74 | создание спрашивает вторую линию; прямых вызовов вычислителя в страничном модуле ноль | integration | `uv run pytest tests/test_pages/test_editor_schedules.py -q -p no:randomly -k "second_line or asked_through_the_helper or create"` | ✅ | ✅ green (26) |
| 15-17 T1 | 15-17 | 5 | GATE-10 (WR-03) | T-15-76 | четыре пары удаления утверждают точный `Location` и исчезновение сущности | integration | `uv run pytest tests/test_pages/test_responsive_markup.py tests/test_pages/test_ads_editor.py -q -p no:randomly -k delete_confirm_degrades_without_htmx` | ✅ | ✅ green (4) |
| 15-17 T2 | 15-17 | 5 | GATE-10 | T-15-77 | пара с перенаправлением без точного адреса краснит гейт пар | unit | `uv run pytest tests/test_templates/test_degradation_pairs.py -q -p no:randomly` | ✅ | ✅ green (17) |
| 15-18 T1 | 15-18 | 5 | QUAL-04, GATE-09 (IN-03) | T-15-78 | единый разборщик: многосимвольный разделитель, три вида скобок, кавычки | unit | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -q -p no:randomly -k split_top_level` | ✅ | ✅ green (3) |
| 15-18 T2 | 15-18 | 5 | QUAL-04, GATE-09 (IN-03) | T-15-78 | гейт страниц ввозит разборщик, второе определение снято | unit | `uv run pytest tests/test_pages/test_htmx_gates.py -q -p no:randomly` | ✅ | ✅ green (84) |
| 15-19 T1 | 15-19 | 5 | GATE-09 (Г-3, IN-04) | T-15-79 | потеря фокуса и роль флажка записаны принятыми следствиями и стережены | unit | `uv run pytest tests/test_templates/test_banner_dismiss.py -q -p no:randomly` | ✅ | ✅ green (26) |
| 15-19 T2 | 15-19 | 5 | GATE-09 (UI 6, 7) | T-15-80 | имена органов с различающим словом первым; тексты плашек не тронуты | unit | `uv run pytest tests/test_templates/test_banner_dismiss.py tests/test_pages/test_shell.py -q -p no:randomly -k "banner or dismiss or accessible or stack"` | ✅ | ✅ green (64) |
| 15-19 T3 | 15-19 | 5 | GATE-09 (UI 5) | — | токен обвода фокуса непрозрачен не ниже 0.7 | unit | `uv run pytest tests/test_templates/test_banner_dismiss.py tests/test_templates/test_htmx_markup_gates.py -q -p no:randomly -k focus` | ✅ | ✅ green (6) |
| 15-20 T1 | 15-20 | 6 | критерий 6 (IN-01) | T-15-81 | пустой ключ `verification` — отказ по имени | unit | `uv run pytest tests/test_planning/test_plan_prohibitions_census.py -q -p no:randomly -k verification` | ✅ | ✅ green (10) |
| 15-20 T2 | 15-20 | 6 | критерий 6 (IN-02) | T-15-82 | испорченный реестр — строка `ОТКАЗ:` и код 1 | unit | `uv run pytest tests/test_planning/test_plan_prohibitions_census.py -q -p no:randomly -k "refused or malformed or registry"` | ✅ | ✅ green (23) |
| 15-21 T1 | 15-21 | 6 | GATE-09, GATE-10 (UI 3, 8) | T-15-83 | шесть сентинелов без размера; умолчание сервера — `PAGE_SIZE` | integration | `uv run pytest tests/test_templates/test_markup_literal_inventory.py tests/test_pages/test_htmx_preserved.py -q -p no:randomly` | ✅ | ✅ green (36) |
| 15-21 T2 | 15-21 | 6 | GATE-09, GATE-10 (IN-05) | T-15-84 | сеть литерала размера — пять форм с контролями | unit | `uv run pytest tests/test_templates/test_markup_literal_inventory.py -q -p no:randomly` | ✅ | ✅ green (11) |
| 15-22 T1 | 15-22 | 7 | критерий 6 | T-15-85 | несколько правил в строке; запись меры покрытия только по правилу, найденному `ast` | unit | `uv run pytest tests/test_planning/test_plan_prohibitions_census.py -q -p no:randomly -k "coverage or rule_site or record"` | ✅ | ✅ green (14) |
| 15-22 T2 | 15-22 | 7 | критерий 6 | T-15-86, T-15-04 | разрешение остатка частичной строки — только у разрешённого класса, построчно | unit | `uv run pytest tests/test_planning/ -q -p no:randomly` | ✅ | ✅ green (208) |
| 15-23 T1 | 15-23 | 7 | долг D-18 | T-15-88 | один помощник зоны профиля на создание, правку и карточку | unit | `uv run pytest tests/test_pages/test_editor_schedules.py tests/test_services/ -q -p no:randomly -k "malformed_stored or profile_timezone or schedule_rules"` | ✅ | ✅ green (47) |
| 15-23 T2 | 15-23 | 7 | долг D-18 (UI 4) | T-15-87 | подсказка о нераспознанной зоне на обоих путях отрисовки; плашки успеха нет | integration | `uv run pytest tests/test_pages/test_editor_schedules.py -q -p no:randomly -k "hint or unrecognised or malformed_stored"` | ✅ | ✅ green (42) |
| 15-24 T1 | 15-24 | 8 | критерий 6 (Г-1) | T-15-89, T-15-90 | строки поведения панели записаны только с доказанным направлением | unit | `uv run pytest tests/test_planning/ -q -p no:randomly` | ✅ | ✅ green (208) |
| 15-24 T2 | 15-24 | 8 | критерий 6 (Г-1) | T-15-89 | новые правила поведения панели с контролями | unit | `uv run pytest tests/test_templates/test_confirmation_panel_invariants.py -q -p no:randomly` | ✅ | ✅ green (26) |
| 15-25 T1 | 15-25 | 9 | критерий 6 (Г-1) | T-15-91 | строки устройства рычага записаны с доказанным направлением | unit | `uv run pytest tests/test_planning/ -q -p no:randomly` | ✅ | ✅ green (208) |
| 15-25 T2 | 15-25 | 9 | критерий 6 (Г-1) | T-15-92 | `hx-confirm` запрещён машинно; место панели по всем местам | unit | `uv run pytest tests/test_templates/test_confirmation_panel_invariants.py -q -p no:randomly` | ✅ | ✅ green (26) |
| 15-26 T1 | 15-26 | 10 | критерий 6 (Г-1) | T-15-93, T-15-94 | строки серверной стороны записаны с доказанным направлением | integration | `uv run pytest tests/test_pages/test_origin_guard_on_destructive_routes.py tests/test_pages/test_identifier_bounds.py -q -p no:randomly` | ✅ | ✅ green (33) |
| 15-26 T2 | 15-26 | 10 | критерий 6 (Г-1) | T-15-93, T-15-94 | правила остатков серверной стороны с контролями | unit | `uv run pytest tests/test_pages/test_write_path_invariants.py -q -p no:randomly` | ✅ | ✅ green (13) |
| 15-27 T1 | 15-27 | 11 | критерий 6 (Г-1) | T-15-96 | строки сценария плашки записаны с доказанным направлением | unit | `uv run pytest tests/test_pages/test_shell.py -q -p no:randomly -k "banner or failure"` | ✅ | ✅ green (38) |
| 15-27 T2 | 15-27 | 11 | критерий 6 (Г-1) | T-15-95, T-15-96 | тексты плашек, тело третьего обработчика, закрытый перечень чтений ответа | unit | `uv run pytest tests/test_pages/test_failure_banner_invariants.py -q -p no:randomly` | ✅ | ✅ green (20) |
| 15-28 T1 | 15-28 | 12 | критерий 6 (Г-1) | T-15-96 | строки подъёма и стопки записаны с доказанным направлением | unit | `uv run pytest tests/test_pages/test_shell.py -q -p no:randomly -k "lift or stack"` | ✅ | ✅ green (7) |
| 15-28 T2 | 15-28 | 12 | критерий 6 (Г-1) | T-15-97 | второй блок подъёма любым селектором; объявление блокировки прокрутки | unit | `uv run pytest tests/test_pages/test_failure_banner_invariants.py -q -p no:randomly` | ✅ | ✅ green (20) |
| 15-29 T1 | 15-29 | 13 | критерий 6 (Г-1) | T-15-99 | строки правил расписания записаны с доказанным направлением | unit | `uv run pytest tests/test_services/ tests/test_routes/test_schedules_api_value_domain.py -q -p no:randomly` | ✅ | ✅ green (395) |
| 15-29 T2 | 15-29 | 13 | критерий 6 (Г-1, D-05) | T-15-98, T-15-99 | отпечаток вычислителя; скоуп владельца чтений ответа удаления; форма ответа | integration | `uv run pytest tests/test_pages/test_schedule_invariants.py -q -p no:randomly` | ✅ | ✅ green (15) |
| 15-30 T1 | 15-30 | 14 | критерий 6 (Г-1, D-05) | T-15-100, T-15-101 | отбор коммитов плана по теме; пустота и мелкий клон — отказ | unit | `uv run pytest tests/test_planning/test_executed_plans_kept_their_scope.py -q -p no:randomly` | ✅ | ✅ green (53) |
| 15-30 T2 | 15-30 | 14 | критерий 6 (Г-1, D-05) | T-15-100 | 14 исторических фактов держатся над коммитами своих планов | unit | `uv run pytest tests/test_planning/ -q -p no:randomly` | ✅ | ✅ green (208) |
| 15-31 T1 | 15-31 | 15 | критерий 6 (Г-1, D-05) | T-15-102 | 5 исторических фактов содержания, у каждого вида контроль | unit | `uv run pytest tests/test_planning/test_executed_plans_kept_their_scope.py -q -p no:randomly` | ✅ | ✅ green (53) |
| 15-31 T2 | 15-31 | 15 | критерий 6 (Г-1, D-05) | T-15-102, T-15-103 | 4 правила предметов D-05 в суите; `10-48#3` частичная с разрешением остатка | unit | `uv run pytest tests/test_templates/test_walkthrough_anchors.py tests/test_planning/test_the_walkthrough_stand_is_seedable.py -q -p no:randomly` | ✅ | ✅ green (27) |
| 15-32 T1 | 15-32 | 16 | критерий 6 | T-15-104 | предмет решения собран: строки, замеры, варианты | unit | `uv run pytest tests/test_planning/ -q -p no:randomly` | ✅ | ✅ green (208) |
| 15-32 T2 | 15-32 | 16 | критерий 6 | T-15-104 | решение владельца по каждой строке (чекпойнт) | manual | — (ответ владельца; записывается задачей 3) | — | ✅ ответ владельца 2026-09-26 (записан задачей 3) |
| 15-32 T3 | 15-32 | 16 | критерий 6 | T-15-105, T-15-106 | ответ владельца записан полями; формы невыбранных ветвей не заведены | unit | `uv run pytest tests/test_planning/ -q -p no:randomly` | ✅ | ✅ green (208) |
| 15-33 T1 | 15-33 | 17 | критерий 6 (Г-1) | T-15-107 | закрывающее правило в сильной форме краснит в правильную сторону | unit | `uv run pytest tests/test_planning/test_plan_prohibitions_census.py -q -p no:randomly -k "closing or strong or reason"` | ✅ | ✅ green (6) |
| 15-33 T2 | 15-33 | 17 | критерий 6 | T-15-108 | человеческий реестр и адресат класса приведены к машинному | unit | `uv run pytest tests/test_planning/ -q -p no:randomly` | ✅ | ✅ green (208) |

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

**Approval (партия закрытия 15-15…15-33):** validated 2026-09-26 (`/gsd-validate-phase 15`, in `/gsd-execute-phase 15 --gaps-only`) — 40 строк карты переизмерены, все зелены; прежняя строка одобрения 2026-09-24 относится к планам 15-01…15-14 и не вычёркивается (D-30/D-32).

2026-09-25 — партия закрытия гэпа верификации 15-15…15-33 (19 планов, 40 задач) спланирована прогоном `/gsd-plan-phase 15 --gaps`; строки карты выше добавлены ПЛАНИРОВАНИЕМ и стоят `⬜ pending` — ЗАПЛАНИРОВАНО, АУДИТОМ НЕ ПРОВЕРЕНО. Поля шапки `status`, `nyquist_compliant`, `validated` этой записью не тронуты: их ставит `/gsd-validate-phase` после исполнения партии. Строка карты «15-13 T2» (закрывающее правило в ослабленной форме) остаётся записью своего дня; сильную форму вводит план 15-33, и строку переписывает аудит, а не планирование.

---

## Validation Audit 2026-09-24

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Замер: 20 строк карты прогнаны командами на дереве после плана 15-14 (полная суита на нём же — `3867 passed, 0 failed`). Все требования COVERED. Четыре селектора засева не отбирали тестов (см. карту) — это расхождение ИМЁН, а не пробел покрытия: поведение под ними принуждено правилами с иными именами, отобранными заново. Одна строка сужена решением владельца, а не аудитом: критерий 6 закрыт правилом «решён или названа причина», а 70 запретов класса `product-invariant` остаются открытыми по его выбору `require-enforcement` (запись — `15-12-SUMMARY.md`, `15-13-SUMMARY.md`). Пункты «Wave 0» отмечены по факту существования артефактов; таблицы отметок `15-UAT.md` существуют и ПУСТЫ — их заполняет человек (D-17), и отметка «Wave 0» этого не утверждает.

## Validation Audit 2026-09-26

Прогон `/gsd-validate-phase 15` внутри `/gsd-execute-phase 15 --gaps-only` (шаг `aggregate_results`) после исполнения партии закрытия 15-15…15-33. Каждая автоматическая команда строк 15-15 T1…15-33 T2 карты прогнана по отдельности на дереве `b277ff2e`; ни одна не вернула пустой отбор (`-k`), все зелены — числа проставлены в колонке Status. Строка 15-32 T2 — ответ владельца (чекпойнт), команды у неё нет по построению. Полная суита на том же дереве (гейт оркестратора): `4082 passed, 0 failed`.

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
| Rows re-measured | 40 |

