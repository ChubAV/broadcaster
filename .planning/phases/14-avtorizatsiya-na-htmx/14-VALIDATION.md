---
phase: "14"
slug: "avtorizatsiya-na-htmx"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-09-22"
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

Источник — `14-RESEARCH.md` §Validation Architecture (строки 670-703), §Environment Availability и
§Security Domain; карта задач — планы `14-01`…`14-07`. Базовый прогон трёх гейтовых модулей
(`130 passed` за 86 с) измерен разведкой на дереве 2026-09-22; время полного прогона (~39 мин) —
замер Фазы 13 (`13-VALIDATION.md`, 39:02–39:43 на пяти прогонах), здесь не перемерялось.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio, httpx `AsyncClient` поверх ASGI, SQLite `:memory:` |
| **Config file** | конфигурации pytest в `pyproject.toml` нет (только зависимости); фикстуры — `tests/conftest.py` (`client`, `htmx_client`, `authed_client`, `admin_client`, `db_session`, `test_settings` с пустым `smtp_host`) |
| **Quick run command** | `uv run pytest tests/test_pages/test_auth_transport.py tests/test_pages/test_registration.py tests/test_pages/test_password_reset.py tests/test_pages/test_blocked_user.py tests/test_pages/test_impersonation.py tests/test_pages/test_cookie_flags.py -q -p no:randomly` |
| **Gate run command** | `uv run pytest tests/test_pages/test_htmx_gates.py tests/test_templates/test_htmx_inventory.py tests/test_templates/test_htmx_markup_gates.py tests/test_templates/test_htmx_markup_security.py tests/test_pages/test_hx_location_destinations.py tests/test_pages/test_impersonation_gate.py tests/test_pages/test_identifier_bounds.py tests/test_pages/test_htmx_preserved.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_htmx_response_layer.py tests/test_pages/test_auth_transport.py -q -p no:randomly` |
| **Records command** | `uv run pytest tests/test_planning -q` (записи правит только план 14-07) |
| **Full suite command** | `uv run pytest tests/ -q` (рецепт `just test`) |
| **Estimated runtime** | быстрый прогон — десятки секунд; прогон гейтов — ~3 мин; полный — ~39 мин |

---

## Sampling Rate

**Обратная связь и гейт завершения — разные инструменты.**

- **After every task commit (обратная связь):** первая команда `<automated>` задачи — модуль пути
  авторизации и/или файл гейта, который задача двигает (секунды — десятки секунд).
- **After every plan (последняя задача плана):** прогон гейтов (Gate run command) плюс модули
  прежних тестов авторизации, которые план правит.
- **After plans 14-01 and 14-06:** полный прогон ОДИН раз — перевод входа меняет статусы, на которые
  опираются помощники входа всей суиты; 14-06 ставит последние перечни вехи (именованный ноль,
  гейт критерия 3).
- **After every plan wave:** полный прогон — пост-слияночный гейт оркестратора (`just test`).
- **Before `/gsd-verify-work`:** полный прогон зелёный + `uv run pytest tests/test_planning -q`.
- **Max feedback latency:** ~180 с (прогон гейтов в конце плана); на задачу — меньше минуты.

⚠️ Полный прогон единицей обратной связи НЕ является: ~39 мин против десятков секунд у быстрого.
⚠️ Известный шум, а не отказ фазы: ночное окно админ-обзора (00:00–05:00 UTC, CONTEXT Landmines).

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 1 | SIGN-01, SIGN-02, SIGN-03 | T-14-01, T-14-03, T-14-04, T-14-05, T-14-06 | неверный пароль — 422 без пароля в теле и без cookie; эхо email экранировано; верный — cookie на ответе 204 с `HX-Redirect`; заблокированный cookie не получает | tracer (e2e пути входа на настоящем приложении) | `uv run pytest tests/test_pages/test_auth_transport.py -q -p no:randomly` | ✅ (создан RED задачи 14-01-01) | ✅ green |
| 14-01-02 | 01 | 1 | SIGN-01, SIGN-03 | T-14-01, T-14-02 | `redirect_internal` отвергает внешний адрес, `//`, обратную косую черту, управляющие символы и не-ASCII на обоих транспортах; узнавание переведённого — закрытое семейство, контроли зубов | unit (слой ответа) + gate (перечни слоя) | `uv run pytest tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_impersonation_gate.py tests/test_pages/test_identifier_bounds.py tests/test_pages/test_hx_location_destinations.py -q -p no:randomly` | ✅ | ✅ green |
| 14-01-03 | 01 | 1 | SIGN-01 | T-14-03 | `POST /login` остаётся маршрутом с путём деградации; экран входа за макросом; ноль фильтров безопасной разметки | gate (перечни разметки) | `uv run pytest tests/test_templates/test_htmx_markup_gates.py tests/test_templates/test_htmx_inventory.py tests/test_templates/test_htmx_markup_security.py -q -p no:randomly` | ✅ | ✅ green |
| 14-02-01 | 02 | 2 | SIGN-01, SIGN-02 | T-14-03, T-14-07, T-14-15 | токен шага только скрытым полем, заголовков перехода у смены экрана нет; эхо адреса экранировано; выход смены экрана отвергает потоковый ответ | unit (выход смены экрана) + integration | `uv run pytest tests/test_pages/test_auth_transport.py tests/test_pages/test_htmx_response_layer.py tests/test_pages/test_reset_code_source.py tests/test_pages/test_htmx_response_contract.py -q -p no:randomly` | ✅ | ✅ green |
| 14-02-02 | 02 | 2 | SIGN-01, SIGN-02 | — | N/A | gate (семейство выходов, ветка пар `SCREEN`, вызывающие макроса) | `uv run pytest tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_registration.py -q -p no:randomly` | ✅ | ✅ green |
| 14-03-01 | 03 | 3 | SIGN-01, SIGN-02, SIGN-03 | T-14-03, T-14-04, T-14-06, T-14-16, T-14-17 | неверный код — 422 с эхом кода, счёт попыток прежний; пароль не возвращается; завершение — cookie на ответе 204 после пробного срока; двойная отправка экрана кода отбрасывается | integration | `uv run pytest tests/test_pages/test_auth_transport.py tests/test_pages/test_trial.py tests/test_pages/test_cookie_flags.py -q -p no:randomly` | ✅ | ✅ green |
| 14-03-02 | 03 | 3 | SIGN-01, SIGN-03 | — | N/A | gate | `uv run pytest tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_registration.py -q -p no:randomly` | ✅ | ✅ green |
| 14-04-01 | 04 | 4 | SIGN-01, SIGN-02 | T-14-03, T-14-07, T-14-13 | под чужой личностью шаги восстановления закрыты на обоих транспортах, кода не заводится; эхо адреса экранировано | integration | `uv run pytest tests/test_pages/test_auth_transport.py tests/test_pages/test_impersonation.py tests/test_pages/test_reset_code_source.py -q -p no:randomly` | ✅ | ✅ green |
| 14-04-02 | 04 | 4 | SIGN-01, SIGN-02 | — | N/A | gate | `uv run pytest tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_password_reset.py -q -p no:randomly` | ✅ | ✅ green |
| 14-05-01 | 05 | 5 | SIGN-01, SIGN-02, SIGN-03 | T-14-01, T-14-04, T-14-13, T-14-16 | новый пароль не возвращается; смена пароля под чужой личностью закрыта; код исхода из реестра, адрес — литерал; шелл без переходного блока | integration | `uv run pytest tests/test_pages/test_auth_transport.py tests/test_pages/test_impersonation.py tests/test_pages/test_shell.py -q -p no:randomly` | ✅ | ✅ green |
| 14-05-02 | 05 | 5 | SIGN-01, SIGN-02 | — | N/A | gate | `uv run pytest tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_password_reset.py -q -p no:randomly` | ✅ | ✅ green |
| 14-06-01 | 06 | 6 | SIGN-01, SIGN-03 | T-14-10, T-14-11, T-14-12 | чужой источник — голый 403 на обоих транспортах; возврат перезаписывает cookie на ответе 204 без признака действующего лица; закрытое действующее лицо выходит со снятой cookie | integration (тройные пары возврата) | `uv run pytest tests/test_pages/test_impersonation.py tests/test_pages/test_origin_guard_on_destructive_routes.py tests/test_pages/test_cookie_flags.py -q -p no:randomly` | ✅ | ✅ green |
| 14-06-02 | 06 | 6 | SIGN-03 | T-14-01, T-14-18 | `HX-Location` в модуле авторизации только у возврата; адреса полной перезагрузки — литералы; изъятие 403 называет решение владельца | gate + отрицательные контроли | `uv run pytest tests/test_pages/test_htmx_gates.py -q -p no:randomly` | ✅ | ✅ green |
| 14-06-03 | 06 | 6 | SIGN-01, SIGN-03 | — | N/A | gate (пары, назначения перехода, вызывающие макроса) | `uv run pytest tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_hx_location_destinations.py tests/test_templates/test_htmx_markup_gates.py -q -p no:randomly` | ✅ | ✅ green |
| 14-07-01 | 07 | 7 | SIGN-03 | T-14-20 | критерии не переписаны, летописи стоят, требования не отмечены до верификации | records | `uv run pytest tests/test_planning -q` | ✅ | ✅ green |
| 14-07-02 | 07 | 7 | SIGN-01, SIGN-02, SIGN-03 | T-14-14, T-14-19 | окно 63 решено замером и командой реестра; обход не заверяет сам себя | records | `uv run pytest tests/test_planning/test_the_walkthrough_cannot_self_certify.py -q` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### Требование → тест (RESEARCH §Phase Requirements → Test Map)

| Критерий / решение | Поведение | Где доказывается |
|--------------------|-----------|------------------|
| кр. 1, SIGN-02 | неверный пароль и неверный код — 422, эхо в `value=`, пароль не возвращается, враждебное экранировано, cookie нет | 14-01-01, 14-03-01, 14-05-01 (`tests/test_pages/test_auth_transport.py`) |
| кр. 2, SIGN-01 | девять форм + возврат через `form_wrapper`, `hx-post == action`, `method="post"`, цель `#auth-step` существует; пары на обоих транспортах; отставание — именованный ноль | 14-01-03 … 14-06-03 (перечни разметки, `test_htmx_post_pairs.py`), 14-06-02 (ноль) |
| кр. 3, SIGN-03 | успех — `HX-Redirect` + cookie на том же ответе; `HX-Location` в модуле авторизации только у возврата | 14-01-01, 14-03-01, 14-05-01 (выходы полной перезагрузки), 14-06-02 (гейт критерия 3) |
| кр. 4 | браузер: четыре пути с настоящими письмами, cookie и `<title>`, возврат, менеджер паролей, вёрстка | ручной обход (ниже), `14-UAT.md` (план 14-07) |
| D-01 | голый 403 возврата — объявленное изъятие; окно 63 | 14-06-01, 14-06-02, 14-07-02 |
| D-05 | заблокированный — 422, текст, email, cookie нет | 14-01-01 |
| D-07 | `<title>` — первый узел фрагмента и равен заголовку страницы | 14-01-01 (`test_every_converted_screen_title_matches_its_page`) и правила каждого экрана |
| D-13 | отказ под чужой личностью на шагах восстановления — 204 + `HX-Location` с htmx, 403 без | 14-04-01, 14-05-01 |

---

## Wave 0 Requirements

Отдельной волны 0 нет: фреймворк, фикстуры и модули гейтов существуют, а каждая задача фазы
начинается с RED своего поведения (TDD-режим). Заготовки, которых сегодня нет и которые заводит
план, их создающий:

- [x] `tests/test_pages/test_auth_transport.py` — модуль пути авторизации: трасер входа и правила 422/эха/экранирования/cookie/`<title>` (14-01); экраны регистрации (14-02, 14-03), восстановления и отказ под чужой личностью (14-04, 14-05)
- [x] `tests/test_pages/test_htmx_post_pairs.py` — ветки `FULL_LOAD` (14-01) и `SCREEN` (14-02), личность `ANONYMOUS`, поле `sets_session_cookie`; контроль обхода 302 переписан на синтетическое отставание (14-01)
- [x] `tests/test_pages/test_htmx_gates.py` — узнавание переведённого по семейству выходов с контролями зубов (14-01, 14-02); гейт критерия 3 с контролями (14-06)

*Existing infrastructure covers the framework; the rows above are created by their plans' RED steps.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Вход: неверный пароль оставляет email, вкладка «Вход — Broadcaster»; верный уводит в кабинет полной загрузкой, cookie `access_token` сменилась | SIGN-02, SIGN-03, кр. 4 | суита не исполняет JS и не видит вкладки и хранилища cookie браузера | `/login` → неверный пароль → верный; DevTools → Application → Cookies до и после |
| Регистрация и подтверждение почты НАСТОЯЩИМ письмом: экран кода без перезагрузки, адрес `/register`, неверный код остаётся в поле, повтор присылает новое письмо, завершение открывает кабинет | SIGN-01, SIGN-02, кр. 4, D-02 | доставка письма и живой рантайм подмены — вне суиты | Новый ящик; код брать ТОЛЬКО из письма; F5 на шаге возвращает к началу пути (D-08) |
| Восстановление пароля настоящим письмом до `/login` с плашкой «Пароль успешно изменён. Войдите с новым паролем.» и вход новым паролем | SIGN-01, SIGN-03, кр. 4, D-02 | то же | Ящик существующей учётной записи |
| Возврат из-под чужой личности: адрес `/admin`, вкладка админки, полосы нет, cookie без признака действующего лица | SIGN-03, D-12 | подмена `body` рантаймом и смена вкладки — вне суиты | Админ → карточка пользователя → «Войти как» → «ВЕРНУТЬСЯ В АДМИНА» |
| Менеджер паролей: пять наблюдений RESEARCH Находки 7 в Chrome и Firefox, база сравнения — путь без JS | SIGN-03, кр. 4 | эвристики браузеров сервером не измеряются (A1–A3) | Чистый профиль; регрессия относительно пути без JS выносится владельцу |
| Вёрстка карточки авторизации: подзаголовок под брендом, промежутки как до фазы, индикатор у кнопки; 375px и десктоп | SIGN-01, A4 | визуальное суждение | Сравнить с `master` на тех же экранах |

**Предусловия обхода (D-02, выписаны также в `14-UAT.md` планом 14-07):** рабочий SMTP на стенде;
доступный ящик для регистрации нового адреса; ящик существующей учётной записи для
восстановления; учётная запись администратора и пользователь для входа под ним; Chrome и Firefox.
Если письма не доходят, обход ОСТАНАВЛИВАЕТСЯ и вопрос уходит владельцу — код из базы молча не
подставляется. Машинная улика обхода — не приёмка: `result` и отметки заполняет человек.
`human_verify_mode: end-of-phase` — чекпоинтов внутри планов нет, обход — на приёмке фазы.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references — все три заготовки созданы RED-шагами своих планов и существуют на дереве `e9f31fd0` (40, 14 и 60 правил соответственно)
- [x] No watch-mode flags
- [ ] Feedback latency < 180s — НЕ ПОДТВЕРЖДЕНО ЗАМЕРОМ, и это записано, а не отмечено: прогон гейтов уложился (127.77 с), но строка карты 14-05-01 заняла **740 с** (12:20). Оценка «~3 мин» верна для гейтов и неверна для строк, включающих `test_impersonation.py` вместе с `test_shell.py`. Предмет строки не ошибка — она устарела замером (D-30/D-32)
- [x] `nyquist_compliant: true` set in frontmatter — выставлен `/gsd-validate-phase 14` по замеру 2026-09-22 (раздел аудита ниже)

**Approval:** validated 2026-09-22 (`/gsd-validate-phase 14`, прогон из `/gsd-execute-phase 14`)

---

## Validation Audit 2026-09-22

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

**Замер, а не перенос статусов из сводок.** Все 16 строк карты (14 различных команд) прогнаны на
дереве `e9f31fd0` — после всех семи планов, рабочее дерево чистое. Каждый прогон с `-p no:randomly`;
число отобранных везде ненулевое, то есть зелень не вакуумная. Полный прогон того же дерева —
`3605 passed, 0 failed` (38:48, пост-слияночный гейт волны 7).

| Строки карты | Итог |
|--------------|------|
| 14-01-01 | 40 passed (17.98 с) |
| 14-01-02 | 196 passed (2:07) |
| 14-01-03 | 114 passed (4.72 с) |
| 14-02-01 | 102 passed (27.62 с) |
| 14-02-02, 14-03-02 | 151 passed (1:32) |
| 14-03-01 | 51 passed (26.24 с) |
| 14-04-01 | 90 passed (1:11) |
| 14-04-02, 14-05-02 | 152 passed (1:32) |
| 14-05-01 | 329 passed (12:20) |
| 14-06-01 | 64 passed (57.38 с) |
| 14-06-02 | 60 passed (25.02 с) |
| 14-06-03 | 183 passed (1:11) |
| 14-07-01 | 44 passed (0.52 с) |
| 14-07-02 | 5 passed (0.12 с) |

**Заготовки волны 0 существуют** (`tests/test_pages/test_auth_transport.py` — 40 правил,
`test_htmx_post_pairs.py` — 14 с ветками `FULL_LOAD`/`SCREEN`/`ANONYMOUS` и полем
`sets_session_cookie`, `test_htmx_gates.py` — 60, включая гейт критерия 3 и правило именованного
нуля `test_the_named_zero_of_the_backlog_is_not_a_broken_scanner`).

**Что этот аудит НЕ закрывает.** Шесть поведений раздела Manual-Only остаются ручными по существу
(браузер, настоящие письма, менеджер паролей, вёрстка) — они не «пропущенные тесты», а предмет
обхода `14-UAT.md`, чьи отметки заполняет человек. `nyquist_compliant: true` означает: у каждой
задачи карты есть автоматическая команда и она зелена; критерий 4 роадмапа этим НЕ доказан.
