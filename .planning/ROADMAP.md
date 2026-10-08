# Roadmap: Broadcaster

## Milestones

- ✅ **v1.0 Baseline** — Фазы 1-6 (ретроспективная карта отгруженной системы) — [архив](milestones/v1.0-ROADMAP.md)
- ✅ **v2.0 Redesign** — Фазы 1-6 + 05.1 (отгружено 2026-08-25) — [архив](milestones/v2.0-ROADMAP.md)
- ✅ **v2.1 HTMX-first** — Фазы 7-15 (отгружено 2026-10-08) — [архив](milestones/v2.1-ROADMAP.md)

## Phases

<details>
<summary>✅ v1.0 Baseline (Фазы 1-6) — ретроспективная карта</summary>

Шесть вертикальных пользовательских возможностей уже отгруженной системы. Это карта
текущего состояния, а не план работ: все перечисленные требования были доставлены
до введения GSD-процесса в проект.

- [x] Phase 1: Secure Access & Scheduling Profile
- [x] Phase 2: Advertisement Library
- [x] Phase 3: Messenger Accounts & Group Targeting
- [x] Phase 4: Scheduled Multi-Messenger Delivery
- [x] Phase 5: Subscription & Message Balance
- [x] Phase 6: Administration & Operations

Полные детали: [`milestones/v1.0-ROADMAP.md`](milestones/v1.0-ROADMAP.md)

</details>

<details>
<summary>✅ v2.0 Redesign (Фазы 1-6 + 05.1) — SHIPPED 2026-08-25</summary>

Нумерация начата заново с 1: фазы v1 были ретроспективной документацией уже
отгруженной системы, а не выполненными GSD-фазами.

- [x] Phase 1: Интерфейсный фундамент (13/13 планов) — completed 2026-08-10
- [x] Phase 2: Объявления и расписания (15/15 планов) — completed 2026-08-11
- [x] Phase 3: Группы аккаунта (12/12 планов) — completed 2026-08-13
- [x] Phase 4: Дашборд и история (12/12 планов) — completed 2026-08-15
- [x] Phase 5: Тарифы (30/30 планов) — completed 2026-08-25 *(модель тарификации ЗАМЕНЕНА фазой 05.1 решением владельца 2026-08-20; платёжные рельсы ЮKassa переиспользованы)*
- [x] Phase 05.1: Единая подписка (INSERTED, 14/14 планов) — completed 2026-08-21
- [x] Phase 6: Админ-панель (14/14 планов) — completed 2026-08-24

**Итого:** 7 фаз, 110 планов, 262 задачи, 41/41 требование `Complete` (+1 `VOID`).

**Десятичная фаза 05.1 (INSERTED)** вставлена после Фазы 5, а не вместо неё: владелец
остановил UAT фазы 5 на формулировке «получилась очень сложная для понимания система
тарифов». Фаза 5 не откатывалась и не переписывалась — её артефакты остаются историей
принятого и отменённого решения.

Полные детали: [`milestones/v2.0-ROADMAP.md`](milestones/v2.0-ROADMAP.md)

</details>

<details>
<summary>✅ v2.1 HTMX-first (Фазы 7-15) — SHIPPED 2026-10-08</summary>

Нумерация продолжила v2.0 (закончилась Фазой 6), а не началась заново.

- [x] Phase 7: Обновление htmx до 2.0.10 и блок конфигурации (7/7 планов) — completed 2026-08-28
- [x] Phase 8: Фундамент ответа, канал уведомлений, пакет гейтов и денежный потолок (11/11 планов) — completed 2026-08-29
- [x] Phase 9: Пилот на `account_groups` — сквозной контракт формы (20/20 планов) — completed 2026-09-02
- [x] Phase 10: Рычаг `components/modal.html` (57/57 планов) — completed 2026-09-14
- [x] Phase 11: Массовый перевод разделов письма (21/21 планов) — completed 2026-09-18
- [x] Phase 12: Загрузка изображений без `fetch()` (13/13 планов) — completed 2026-09-21
- [x] Phase 13: Мастер подключения Telegram по QR на фрагментах (6/6 планов) — completed 2026-09-21
- [x] Phase 14: Авторизация на htmx (7/7 планов) — completed 2026-09-23 *(перепроверена 2026-10-08, круг 6: SC4 — override владельца)*
- [x] Phase 15: Упрочнение и сводный обход 47 форм (33/33 планов) — completed 2026-10-06

**Итого:** 9 фаз, 175 планов, 407 задач, 41/41 требование `Complete`; EDIT-01, UPLD-01,
E2E-01 отложены в v2.2. Аудит вехи — `tech_debt` (0 блокеров):
[`milestones/v2.1-MILESTONE-AUDIT.md`](milestones/v2.1-MILESTONE-AUDIT.md).

Полные детали: [`milestones/v2.1-ROADMAP.md`](milestones/v2.1-ROADMAP.md)

</details>

## Перенесено незакрытым из v2.1

Веха v2.1 закрыта типом `override_closeout`: 44 открытых артефакта подтверждены владельцем
как осознанно отложенные, 13 подтверждений перенесены из v2.0. Главное для следующей вехи:

- 🔴 **Долг безопасности:** CR-01 Фазы 14 (девять из десяти POST авторизации без сверки
  источника), CR-02 Фазы 14 (подтверждённый токен восстановления воспроизводим — правило
  Фазы 14 закрепляет это зелёным и покраснеет на починке), WR-06 Фазы 10 (три изменяющих
  POST расписаний без сверки источника), todo «код ответа отправки кода раскрывает учётку».
- 🔴 **Выкат схемы:** очередь ревизий `0013`…`0021` не выкачена на боевую базу; у `0021`
  обязательный порядок — код с `AWAITING_STATUSES` не позже миграции (R-08-06).
- Три BLOCKER-долга безопасности из v2.0 (блокировка на страничном маршруте, коды сброса
  из `random.randint`, cookie без `secure`) — по-прежнему открыты.
- Nyquist: фазы 7, 8 без VALIDATION.md; фаза 9 — draft; фаза 10 — partial.

Полный перечень с основаниями — `.planning/STATE.md` §Deferred Items,
`.planning/MILESTONES.md` §v2.1, `.planning/milestones/v2.1-MILESTONE-AUDIT.md`.

## Backlog

### Phase 999.1: Follow-up — Phase 14 deferred UAT follow-up: Test 8 (BACKLOG)

**Goal:** Resolve the UAT checkpoint deferred during Phase 14 verification
**Source phase:** 14
**Deferred at:** 2026-10-08 during /gsd-verify-work 14 session completion (решение владельца `chubav`, Q7)
**Follow-ups:**
- (открыто) Test 8: Наблюдать фокус и объявление скринридера после подмены `#auth-step` (14-UI-REVIEW WARNING 2): куда встаёт фокус после Tab на экране кода и на входе, что объявляет скринридер и какой (deferred 2026-10-08)

### Phase 999.2: Follow-up — Phase 14 deferred UAT follow-up: Test 9 (BACKLOG)

**Goal:** Resolve the UAT checkpoint deferred during Phase 14 verification
**Source phase:** 14
**Deferred at:** 2026-10-08 during /gsd-verify-work 14 session completion (решение владельца `chubav`, Q7)
**Follow-ups:**
- (открыто) Test 9: Наблюдать вторую кнопку экрана кода, пока первый запрос в полёте (14-UI-REVIEW WARNING 3): выглядит ли «Отправить код повторно» живой, есть ли у неё индикатор (deferred 2026-10-08)

---

*Роадмап следующей вехи — `/gsd-new-milestone`. Текущее состояние проекта — `.planning/PROJECT.md`.*
