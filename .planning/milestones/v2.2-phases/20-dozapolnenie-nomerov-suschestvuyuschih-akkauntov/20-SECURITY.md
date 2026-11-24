---
phase: "20"
slug: "dozapolnenie-nomerov-suschestvuyuschih-akkauntov"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-11-24"
---

# Phase 20 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Реестр собран из блоков `<threat_model>` планов 20-01…20-07 (составлен на этапе плана) и разделов `## Threat Flags` семи сводок; все семь сводок заявили «None» — новых сетевых точек, путей авторизации и схем нет. Уровень ASVS 1, порог блокировки `high`: сверка мер — по коду и тестам на уровне grep, аудитор не порождался (короткий путь `/gsd-secure-phase`: `threats_open: 0`, реестр плановый, ASVS 1). `T-20-SC` повторяется во всех семи планах как одна и та же угроза и записан один раз. `T-20-05` живёт в плане 20-07 (перенесён из 20-01 ревизией 1, ID прежний); пропусков нет — 25 номерных угроз плюс `T-20-SC`.

Область кода — `scripts/backfill_account_phones.py` (840 строк), рецепты `backfill-phones` / `prod-backfill-phones` в `justfile:177-183`, тесты `tests/test_scripts/test_backfill_account_phones.py` (коммиты `3b306e77…b456d8cc`). Все 29 тестов-улик, названных в реестрах планов, существуют; файл прогнан на `8fd9ab7d`: 155 passed. Скрипт ввозит из `app.messengers` только чистые помощники (`reported_phone_from_status`, `reported_phone_of`), адаптеры WA/MAX не ввозятся; команды изменения брокера (`lpop|rpop|brpop|.delete(|.revoke(|.purge(`) — 0 вхождений; `pyproject.toml` / `uv.lock` фазой не менялись.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| источник номера → ядро | `reported` — недоверенные данные мессенджера; нормализует только писатель Фазы 16 | номер собственного аккаунта |
| ядро → база (`messenger_accounts`) | запись только условным оператором `fill_reported_phone`; просмотр — только чтение `exists` | `account_id`, номер |
| ядро → вывод (`print`) | у процессов `scripts/` маски на исполнении нет; рубежи — `mask_phone` в `print`, `repr=False`, имя класса исключения | маскированный номер, заметки |
| скрипт → Docker daemon (`docker.sock` в `web`) | чтение списка контейнеров с меткой роли; подъём и остановка — только по `--wake` | имена контейнеров |
| воркер WA/MAX → скрипт (`/status`) | тело ответа — недоверенный JSON | поле `phone`, `connected` |
| скрипт → Redis (`wa:queue:*` / `max:queue:*`, `telegram`, pidbox) | только `LLEN`, `LRANGE`, `inspect` | длина очереди, снимок задач |
| `messenger_accounts.credentials` → Telethon | строка сессии — сам ключ авторизации; разбирается до сети, назад не пишется | строка сессии (секрет) |
| процесс скрипта → сеть Telegram | короткое подключение ключом, который параллельно использует Celery | ключ авторизации |
| администратор → `just` → `docker compose exec -T web` | права — доступ к хосту и `docker.sock`, вне приложения; аргументы ограничены `argparse` | флаги CLI |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-20-01 | Tampering (второй писатель затирает ручной номер) | `run`, `_write` | high | mitigate | запись только `fill_reported_phone` (`scripts/backfill_account_phones.py:78,236`), иных `UPDATE`/`session.add` нет; `test_manual_entered_during_the_run_is_kept` | closed |
| T-20-02 | Information Disclosure (номер, строка сессии, текст исключения в выводе) | печать строк и итога | high | mitigate | `mask_phone(e164)` внутри `print` (`:687-688`); `credentials`/`reported` с `repr=False` (`:155,161`); заметки — `type(exc).__name__` (`:221,242,831` и др.); `test_output_masks_numbers_and_has_a_filled_line`; гейт `tests/test_phone_privacy_gate.py` | closed |
| T-20-03 | Tampering (скрипт меняет статус или строку сессии) | `select_candidates`, `run` | medium | mitigate | выборка колонками в `AccountRow` (`:182-189`), сущности в сессию не грузятся; `test_status_unchanged_by_any_outcome` | closed |
| T-20-04 | Denial of Service (сбой одного аккаунта обрывает или откатывает прогон) | цикл `run` | medium | mitigate | сессия и `commit` на аккаунт, `rollback` при исключении (`:236-242`); `test_one_failing_account_does_not_stop_or_undo_the_run` | closed |
| T-20-05 | Tampering (просмотр пишет под откатом) | ветка просмотра `run`, `_preview` | medium | mitigate | в просмотре писатель не вызывается, предсказание — `select(exists())` (`:246-269,677-678`); `test_dry_run_writes_nothing_and_predicts`, `test_dry_run_predicts_kept_and_gone_by_reading` | closed |
| T-20-06 | Tampering / DoS (скрипт будит спящий воркер) | `WorkerStatusSource.poll` | high | mitigate | адрес только из карты Docker `running` (`:283-322,344-346`); адаптеры WA/MAX не ввозятся (`:78-85`); без `--wake` — «воркер не запущен» (`:347-349`); `test_never_wakes_through_adapters`, `test_dry_run_starts_no_container` | closed |
| T-20-07 | Spoofing (недоверенное тело `/status`) | `classify_status` | medium | mitigate | `reported_phone_from_status` + `normalize_reported` (`:652,687`); `test_classify_status_table`, `test_classify_status_precision_of_the_phone_field` | closed |
| T-20-08 | Information Disclosure (тело ответа / текст исключения в выводе) | `_ask` | medium | mitigate | заметка — имя класса, код или фраза таблицы A6 (`:448`); `test_classify_status_transport_failures_are_unreachable` | closed |
| T-20-09 | Denial of Service (отказ Docker роняет прогон) | ленивая карта | low | mitigate | отказ кэшируется и становится исходом аккаунта (`:333,342-343`); `test_docker_unavailable_is_a_per_account_outcome` | closed |
| T-20-10 | Tampering / DoS (подъём = вход связанного устройства; удаление сессии на 401/403/405) | `_wake` | high | mitigate | только по флагу, без `dry_run` (`:347`), только `active` (`:359`), только при прочитанной и пустой очереди (`:361-368`), по одному (цикл ядра); остаточный 405 принят владельцем — AR-20-03; `test_wake_conditions_matrix` | closed |
| T-20-11 | Denial of Service (гасит чужой контейнер или посреди отправки) | `_wake`, `_stop_if_idle` | high | mitigate | повторная проверка `_running_now` → `get_container_endpoint` перед подъёмом (`:318,371-373`); гасится только `started` (`:378-396`); очередь перед остановкой (`:418-430`); `test_wake_never_stops_a_container_it_did_not_start`, `test_wake_leaves_the_container_when_the_queue_filled`. Остаточные окна — см. «Наблюдения аудита» (WR-02, WR-03) | closed |
| T-20-12 | Denial of Service (осиротевший поднятый контейнер) | `finally` подъёма | medium | mitigate | остановка в `finally` (`:394-396`), в том числе на `CancelledError`; заметка «проверьте just wa-workers / just max-workers» при отказе (`:424-438`); `test_wake_stops_the_container_on_failure_and_cancellation`. Остаток — WR-01 | closed |
| T-20-13 | Tampering (подъём под просмотром) | `poll` | high | mitigate | `if not options.wake or options.dry_run` — без подъёма (`:347-349`); `test_wake_with_dry_run_in_the_core_starts_nothing`; отказ CLI — T-20-24 | closed |
| T-20-14 | Denial of Service (`AUTH_KEY_DUPLICATED`) | `TelegramSource.poll` | high | mitigate | последовательный цикл ядра (`:675`); признак «занят» до построения клиента (`:499-508`); `receive_updates=False` (`:509`); `disconnect` в `finally` (`:532-534`); запуск только из контейнера — T-20-23; `test_telegram_sequential_one_client_at_a_time`, `test_telegram_busy_*` (2) | closed |
| T-20-15 | Tampering (пустая строка сессии → новый ключ) | `parse_session` | medium | mitigate | пустая и неразбираемая строка отсеиваются до сети (`:458-469`); `test_telegram_bad_session_string_never_connects` | closed |
| T-20-16 | Information Disclosure (строка сессии, `User`, текст исключения Telethon) | `poll`, ядро | high | mitigate | `credentials` с `repr=False` (`:155`); заметки — имя класса (`:526-531`); `test_telegram_output_carries_no_session_or_exception_text`; гейт приватности | closed |
| T-20-17 | Repudiation (неверная классификация исключений Telethon) | карта исключений | low | mitigate | перехват по классам `telethon_errors`, `is_user_authorized` / `get_me` (`:509-531`); `test_telegram_outcomes_map` | closed |
| T-20-18 | Denial of Service (рассылка не распознана → второе подключение) | `TelegramBusyProbe._check` | high | mitigate | `active` ∪ `reserved` ∪ список `telegram` (`:556,604-610`); `test_busy_probe_reads_a_real_kombu_message_from_the_telegram_list` | closed |
| T-20-19 | Denial of Service (ответил не каждый воркер очереди) | `_check` | high | mitigate | состав из `active_queues` (`:581`); каждый воркер обязан быть в `active`/`reserved`, иначе `None` → «занят» (`:605-607,505-506`); `test_busy_probe_fails_closed` | closed |
| T-20-20 | Tampering (скрипт меняет брокер) | `_check` | medium | mitigate | только `lrange` / `inspect`; команды изменения брокера — 0 вхождений; `app/worker/` фазой не правился | closed |
| T-20-21 | Denial of Service (окно проверка→`connect`; подключения TG из `web`, невидимые `inspect`) | признак в целом | medium | accept | AR-20-01 | closed |
| T-20-22 | Tampering (запуск без флагов пишет, не желая того) | справка, рецепты, баннер | medium | mitigate | `WRITES by default` в рецептах (`justfile:177,181`); `ПИШЕТ` в шапке и справке (`:9,702`); первая строка `РЕЖИМ ЗАПИСИ` (`:670`); `test_recipes_say_they_write_by_default`, `test_script_help_runs_and_says_it_writes` | closed |
| T-20-23 | Denial of Service (TG опрошен с хоста при боевом `.env`) | `build_sources` | high | mitigate | TG только при `--telegram-from-container` (`:775,791`), иначе `TelegramOutsideContainerSource` (`:760`); флаг передаёт лишь `prod-backfill-phones` (`justfile:183`); `test_build_sources_guards_telegram_outside_the_container`, `test_recipes_prod_uses_exec_t_web_and_local_has_no_docker` | closed |
| T-20-24 | Tampering (`--wake` под `--dry-run`) | `amain` | medium | mitigate | `parser.error` до любой работы (`:813`); `test_wake_with_dry_run_is_rejected_before_any_source_call` | closed |
| T-20-25 | Information Disclosure (копия боевой базы со строками сессий) | процедура проверки | low | accept | AR-20-02 | closed |
| T-20-SC | Tampering (цепочка поставки) | npm/pip/cargo installs | high | mitigate | установок нет: `pyproject.toml`, `uv.lock`, `package.json` фазой не менялись (`httpx`, `docker`, Telethon 1.42.0, Celery 5.6.2, redis 6.4.0 уже закреплены) | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-20-01 | T-20-21 | окно между снимком «занят» и `connect`, а также подключения TG из `web` (например, `TelegramUserMessenger` на странице аккаунтов), невидимые `inspect`, остаются; снимок берётся на каждый аккаунт непосредственно перед подключением; боевой прогон — шаг владельца, начинать с `--dry-run --account-id`, в окне без рассылок (то же — IN-03 обзора кода) | план 20-05 (RESEARCH A1, диспозиция `accept` реестра плана) | 2026-11-23 |
| AR-20-02 | T-20-25 | копия боевой базы не делается; корректность доказана тестами на синтетических данных, настоящие исходы — первым боевым `--dry-run --account-id` | владелец, O-4 (а) в прогоне `/gsd-plan-phase 20` | 2026-11-23 |
| AR-20-03 | T-20-10 (остаток) | 405 на живой сессии при подъёме по `--wake` может привести к удалению файлов сессии самим воркером; путь тот же, что у плановой отправки; офлайн-чтение `creds.json` (вариант (в)) отвергнуто | владелец, O-1 (а) в прогоне `/gsd-plan-phase 20` | 2026-11-23 |

*Accepted risks do not resurface in future audit runs.*

---

## Наблюдения аудита (вне блокировки)

Меры реестра реализованы так, как их описали планы, поэтому все угрозы закрыты на глубине L1. Обзор кода фазы (`20-REVIEW.md`, все 8 находок в `20-REVIEW-DISPOSITION.md` — `open`) нашёл остаточные окна в тех же мерах. Аудит их не закрывает и не принимает от имени владельца — разбор остаётся за владельцем:

- **WR-03 → T-20-11.** Между `_running_now` и `_start` контейнер может поднять кто-то другой. `start_container` (а у MAX — и Docker 409) возвращает адрес чужого контейнера, скрипт ставит `started = True` и гасит его в `finally`. Окно узкое, и его сужает проверка пустой очереди.
- **WR-02 → T-20-11.** `LLEN == 0` не доказывает простоя: задачу, которую воркер уже взял из очереди в окне подъёма (до 90 с у WA, около 120 с у MAX), `stop(timeout=10)` оборвёт посреди отправки.
- **WR-01 → T-20-12.** Настоящие `stop_container` при `APIError` возвращают `False`, а не бросают исключение. `_stop_if_idle` отбрасывает результат, поэтому заметки «контейнер оставлен» нет. Тест моделирует отказ через `raise RuntimeError`. Контейнер гаснет сам через `IDLE_SHUTDOWN_SEC=300`.
- **IN-02 → T-20-10 / T-20-23.** У `--wake` нет стража от запуска вне боевого контейнера. При локальном `.env` на боевую базу локальный Docker подымет воркеры с боевым `REDIS_URL` и пустым томом сессий.

Все четыре касаются только пути `--wake`, который включается флагом. Путь по умолчанию и `--dry-run` их не затрагивают.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-24 | 26 | 26 | 0 | `/gsd-secure-phase 20` (L1 grep по `scripts/backfill_account_phones.py`, `justfile`; 29 тестов-улик на месте, `tests/test_scripts/test_backfill_account_phones.py` 155 passed на `8fd9ab7d`; аудитор не порождался — короткий путь ASVS 1) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-24
