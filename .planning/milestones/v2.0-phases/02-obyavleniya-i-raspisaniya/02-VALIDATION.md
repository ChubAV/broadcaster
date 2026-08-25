---
phase: 2
slug: obyavleniya-i-raspisaniya
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-10
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=9.0.2 + pytest-asyncio >=1.3.0 + aiosqlite >=0.22.1 |
| **Config file** | none — конфигурация только в `tests/conftest.py` (нет `pytest.ini`, нет секции в `pyproject.toml`) |
| **Quick run command** | `uv run pytest tests/test_pages tests/test_routes/test_ads.py tests/test_routes/test_schedules.py tests/test_templates tests/test_application -q` |
| **Full suite command** | `just test` → `uv run pytest tests/ -v` |
| **Estimated runtime** | quick ~10 s · full ~740 s (12 мин 21 с, замерено исследованием 2026-08-10) |

**Базовая линия до плана 02-01:** 624 passed / 25 failed / 3 errors из 652 собранных. Единственная причина всех 28 — утечка `.env` разработчика в тестовые `Settings` (`app/config.py:78`).
**Базовая линия после плана 02-01:** 0 failed, 0 errors. Всё, что краснеет после этого, внесено фазой.

---

## Sampling Rate

- **After every task commit:** `uv run pytest tests/test_pages tests/test_routes/test_ads.py tests/test_routes/test_schedules.py tests/test_templates tests/test_application -q`
- **After every plan wave:** `just test` — полный прогон, сравнение с зафиксированной базовой линией
- **Before `/gsd-verify-work`:** полная суита зелёная
- **Max feedback latency:** 10 s на задачу, 740 s на волну

> Полный прогон на каждый коммит задачи не гонять — 12 минут съедают цикл обратной связи.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 1 | BASE | T-02-01 | Тесты не запускаются с боевыми SMTP-параметрами и боевым `s3_public_url` разработчика | integration | `uv run pytest tests/test_config.py tests/test_config_s3.py tests/test_e2e.py tests/test_main.py tests/test_routes/test_groups_bulk.py tests/test_routes/test_sync_groups.py tests/test_routes/test_tg_user_auth.py tests/test_routes/test_uploads.py tests/test_routes/test_wa_sync_status.py tests/test_services/test_messenger_factory.py -q` | ✅ существуют, красные | ⬜ pending |
| 2-01-02 | 01 | 1 | ADS-04, ADS-06 | T-02-02 / T-02-03 / T-02-04 | Импорт модуля не конструирует `Settings`; чужое объявление недоступно на редактирование | integration | `uv run pytest tests/test_pages/test_ads_editor.py tests/test_pages/test_schedule_creation_path_exists.py tests/test_pages/test_shell.py tests/test_pages/test_responsive_markup.py tests/test_templates -q` | ❌ W0 | ⬜ pending |
| 2-02-01 | 02 | 2 | ADS-05 | T-02-07 | Тип файла определяется по содержимому; SVG отклоняется | integration | `uv run pytest tests/test_routes/test_uploads.py -q` | ✅ расширяется | ⬜ pending |
| 2-02-02 | 02 | 2 | ADS-05 | T-02-08 / T-02-09 / T-02-10 | Чужой ключ и превышение лимита отклоняются на всех четырёх входах | integration | `uv run pytest tests/test_pages/test_ads_image_ownership.py tests/test_routes/test_ads.py tests/test_pages/test_ads_editor.py -q` | ❌ W0 | ⬜ pending |
| 2-02-03 | 02 | 2 | ADS-07 | T-02-05 / T-02-06 | Чужие `ad_id` и `account_id` отклоняются на страничном и JSON-входе | integration | `uv run pytest tests/test_pages/test_schedule_ownership.py tests/test_routes/test_schedules.py tests/test_pages/test_schedules_detached_account.py tests/test_routes/test_schedules_toggle_detached.py tests/test_pages/test_schedule_creation_path_exists.py -q` | ❌ W0 | ⬜ pending |
| 2-03-01 | 03 | 3 | ADS-04 | T-02-16 | Чекпойнт решения: подтверждение необратимого шага и резервной копии | — | не автоматизируется (checkpoint:decision) | — | ⬜ pending |
| 2-03-02 | 03 | 3 | ADS-04 | T-02-11 / T-02-12 / T-02-13 / T-02-14 / T-02-15 | Черновик не выбирается к отправке и его `next_run_at` сдвигается; произвольная строка состояния не пишется через API | unit + integration | `uv run pytest tests/test_application tests/test_pages/test_ads_status.py tests/test_models/test_ad.py tests/test_constants.py tests/test_routes/test_ads.py tests/test_pages/test_schedule_creation_path_exists.py tests/test_worker_tasks.py -q` | ❌ W0 | ⬜ pending |
| 2-03-03 | 03 | 3 | ADS-04 | T-02-16 | Ревизия `0013` применяется и откатывается; существующие строки становятся опубликованными | integration | `uv run pytest tests/test_migrations/test_0013_ad_status.py -q` | ❌ W0 | ⬜ pending |
| 2-04-01 | 04 | 4 | ADS-04, ADS-06 | T-02-19 | Предпросмотр рендерится сервером; пользовательский текст экранируется | integration | `uv run pytest tests/test_templates tests/test_pages/test_https_asset_scheme.py -q` | ✅ существуют | ⬜ pending |
| 2-04-02 | 04 | 4 | ADS-04, ADS-05, ADS-06 | T-02-20 / T-02-21 / T-02-22 | Автосохранение чужого объявления невозможно; предпросмотр из базы, не из тела запроса | integration | `uv run pytest tests/test_pages/test_ads_editor.py tests/test_pages/test_ads_image_ownership.py tests/test_pages/test_ads_status.py tests/test_routes/test_ads.py -q` | ✅ расширяется | ⬜ pending |
| 2-04-03 | 04 | 4 | ADS-04, ADS-05 | T-02-17 / T-02-18 | Разметка строится узлами DOM; значение настроек безопасно для JS-контекста | integration | `uv run pytest tests/test_templates/test_ads_form_security.py tests/test_pages/test_ads_editor.py tests/test_pages/test_responsive_markup.py tests/test_pages/test_htmx_preserved.py tests/test_pages/test_schedule_creation_path_exists.py -q` | ✅ существуют | ⬜ pending |
| 2-05-01 | 05 | 5 | ADS-07, ADS-08 | T-02-28 | Тело окна подтверждения экранируется | integration | `uv run pytest tests/test_templates tests/test_pages/test_responsive_markup.py -q` | ✅ существуют | ⬜ pending |
| 2-05-02 | 05 | 5 | ADS-07 | T-02-23 / T-02-24 / T-02-25 / T-02-26 / T-02-27 | Адрес возврата строится сервером; некорректные значения отбрасываются до разбора; проверки владения сохранены | integration | `uv run pytest tests/test_pages/test_editor_schedules.py tests/test_pages/test_schedule_ownership.py tests/test_routes/test_schedules.py tests/test_pages/test_schedules_detached_account.py tests/test_routes/test_schedules_toggle_detached.py tests/test_routes/test_schedules_profile_timezone.py tests/test_pages/test_schedule_creation_path_exists.py -q` | ❌ W0 | ⬜ pending |
| 2-05-03 | 05 | 5 | ADS-07, ADS-08 | — | Вложенных форм нет; удаление работает без Alpine | integration | `uv run pytest tests/test_pages/test_editor_schedules.py tests/test_pages/test_ads_editor.py tests/test_pages/test_responsive_markup.py tests/test_pages/test_schedule_creation_path_exists.py tests/test_templates -q` | ❌ W0 | ⬜ pending |
| 2-06-01 | 06 | 6 | ADS-07, SCH-05 | T-02-29 / T-02-30 / T-02-31 / T-02-32 | Путь создания расписания жив; оставшиеся обработчики и их проверки владения на месте | integration | `uv run pytest tests/test_pages/test_schedule_creation_path_exists.py tests/test_pages/test_editor_schedules.py tests/test_routes/test_schedules.py -q` | ✅ существуют | ⬜ pending |
| 2-06-02 | 06 | 6 | ADS-07, SCH-05 | T-02-33 | Ни один тест не удалён вместе с маршрутом | integration | `uv run pytest tests/test_pages/test_shell.py tests/test_pages/test_responsive_markup.py tests/test_pages/test_schedules_detached_account.py tests/test_routes/test_schedules_toggle_detached.py tests/test_routes/test_schedules_profile_timezone.py tests/test_pages/test_schedule_creation_path_exists.py -q` | ✅ существуют | ⬜ pending |
| 2-07-01 | 07 | 7 | SCH-04 | T-02-34 / T-02-38 | Имена групп разрешаются с ограничением по владельцу, одним запросом на страницу | integration | `uv run pytest tests/test_pages/test_responsive_markup.py tests/test_routes/test_schedules.py tests/test_pages/test_schedules_detached_account.py -q` | ✅ существуют | ⬜ pending |
| 2-07-02 | 07 | 7 | SCH-04 | T-02-35 / T-02-36 | Неизвестный фильтр не роняет страницу; поисковый термин экранируется | integration | `uv run pytest tests/test_pages/test_htmx_preserved.py tests/test_pages/test_responsive_markup.py tests/test_templates -q` | ✅ существуют | ⬜ pending |
| 2-07-03 | 07 | 7 | SCH-04, SCH-05 | T-02-37 | Переключение чужого расписания невозможно | integration | `uv run pytest tests/ -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` + 11 модульных фикстур — `_env_file=None` (закрывает 25 failed + 3 errors) → план 02-01
- [ ] `tests/test_pages/test_ads_editor.py` — первый рендер-тест редактора (D-21), покрывает ADS-04 и ADS-06 → план 02-01
- [ ] `tests/test_pages/test_schedule_creation_path_exists.py` — страховочная сетка SC-3 на всю фазу → план 02-01
- [ ] `tests/test_pages/test_ads_image_ownership.py` — WR-01 и D-13 → план 02-02
- [ ] `tests/test_pages/test_schedule_ownership.py` — CR-01/D-20, оба входа → план 02-02
- [ ] `tests/test_routes/test_uploads.py` — тест подделанного заголовка типа (CR-02) → план 02-02
- [ ] `tests/test_routes/test_ads.py` — переписать тест, закрепляющий приём чужого ключа изображения → план 02-02
- [ ] `tests/test_application/test_collect_due_draft.py` — D-01, самая чувствительная правка фазы → план 02-03
- [ ] `tests/test_pages/test_ads_status.py` — бейдж состояния, живость `/dashboard`, `/api/ads`, старых страниц расписаний → план 02-03
- [ ] `tests/test_migrations/__init__.py` + `test_0013_ad_status.py` — единственная проверка ревизии: суита миграции не применяет → план 02-03
- [ ] `tests/test_models/test_ad.py` — переписать утверждения о старом флаге активности → план 02-03
- [ ] `tests/test_pages/test_editor_schedules.py` — ADS-07 и ADS-08 → план 02-05
- [ ] Переписать тесты, ссылающиеся на удаляемые маршруты: `test_shell.py`, `test_responsive_markup.py`, `test_schedules_detached_account.py`, `test_schedules_toggle_detached.py`, `test_schedules_profile_timezone.py` → план 02-06
- [ ] `tests/test_pages/test_schedules_list.py` — SCH-04 и SCH-05 → план 02-07

Framework install: не требуется. Новых зависимостей фаза не вводит.

---

## Manual-Only Verifications

Держатся в `<verify><human-check>` соответствующих задач, потому что `workflow.human_verify_mode = end-of-phase`: отдельных задач-чекпойнтов проверки не создаётся.

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Каретка и выделение не сбрасываются при автосохранении | ADS-04 | Позиция каретки не наблюдаема из HTTP-теста | `/ads/new`, набрать текст, дождаться паузы 2 с, продолжить набор с середины строки |
| 5 held-out визуальных состояний редактора (индикатор на 320px, предпросмотр 4000 символов и ссылка 300 символов, значение сводки, заголовок 200 символов, соотношение колонок >900px) | ADS-04, ADS-06 | Backstop-проверки UI-SPEC: переносы и обрезка не выражаются утверждением на разметке | Задача 2-04-03, блок `<human-check>` |
| 6 held-out визуальных состояний расписаний (имя аккаунта 60 символов, имя группы 120 символов, шапка 7 дней × 6 времён, сводка шапки, заголовок 200 символов в окне подтверждения, экранирование тела окна) | ADS-07, ADS-08 | Backstop-проверки UI-SPEC | Задача 2-05-03, блок `<human-check>` |
| 1 held-out визуальное состояние сводного списка (заголовок 200 символов на 320px) | SCH-04 | Backstop-проверка UI-SPEC | Задача 2-07-03, блок `<human-check>` |
| Применение ревизии `0013` к настоящей базе | ADS-04 | Тесты строят схему `Base.metadata.create_all` и миграции не применяют; PostgreSQL в суите отсутствует | `just upgrade`, затем `uv run alembic current` и `uv run alembic heads` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10 s (задача) / 740 s (волна)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
