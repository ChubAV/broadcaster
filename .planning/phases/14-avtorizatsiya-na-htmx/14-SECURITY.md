---
phase: "14"
slug: "avtorizatsiya-na-htmx"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-09-23"
---

# Phase 14 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

**Происхождение реестра.** `register_authored_at_plan_time: true` — блоки `<threat_model>` есть у
ВСЕХ семи планов (14-01…14-07), реестр не восстанавливался задним числом. Поэтому проверка шла в
режиме «подтвердить смягчения», а не «искать новые угрозы»; при `asvs_level: 1` и нуле открытых
угроз глубины L1 (грепом по дереву) достаточно по контракту `secure-phase.md` §3.

**Чем подтверждено.** Каждая строка ниже — улика, прочитанная в дереве на `65b313bc`, либо
именованное правило суиты. Полный прогон того же дерева: **3605 passed, 0 failed** (`e9f31fd0`,
вне продуктового кода с тех пор ничего не менялось). Ни одна строка не взята из заявления сводки:
разделы `## Threat Flags` всех семи сводок читаются `None`, и это ПРОВЕРЕНО, а не принято на веру.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| браузер → страничный слой | поля семи экранов авторизации (`email`, `password`, `code`, `name`), подписанный `token` шага, признак htmx | учётные данные, код подтверждения, подписанный токен шага |
| страничный слой → браузер | тело 422 с эхом введённого, фрагмент экрана, заголовки `HX-Redirect` / `HX-Location`, `Set-Cookie` сессии | эхо введённого (без пароля), заголовок перехода, cookie сессии |
| зависимость `forbid_when_impersonating` → браузер | отказ шагам восстановления под чужой личностью (403 / 204 + `HX-Location`) | признак действующего лица |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-14-01 | Tampering (open redirect) | `redirect_internal` → `HX-Redirect` | high | mitigate | `_local_path` (`app/pages/htmx.py:224`) + `_with_notice` (`:731`); адреса в обработчиках — литералы; правило `test_an_internal_full_load_never_leaves_the_site_or_carries_unencodable_text` | closed |
| T-14-02 | Tampering / DoS (инъекция заголовка, 500 на кириллице) | `redirect_internal` | medium | mitigate | `value.isascii()` (`htmx.py:260, :320`); код исхода только из реестра — `_require_registered_notice` (`:552`, вызов `:445`) | closed |
| T-14-03 | Tampering (XSS через эхо) | семь экранов, `value=` | high | mitigate | Автоэкранирование окружения `Jinja2Templates` (`app/pages/common.py:36`); фильтров `\|safe` / `Markup(` в `app/templates/auth/` и `auth_base.html` — **0**; правило с враждебным адресом на обоих транспортах | closed |
| T-14-04 | Information Disclosure (пароль в ответе) | контекст экранов | high | mitigate | `_screen_builders` ОТВЕРГАЕТ ключ `password` (`app/pages/auth.py:210-214`, `raise ValueError`, без подстановки значения — чтобы пароль не ушёл в журнал трассировкой) | closed |
| T-14-05 | Elevation of Privilege (заблокированный входит) | `login_submit` | high | mitigate | Порядок «пароль → блокировка → cookie» сохранён (`verify_password` → `elif user.is_blocked` → `set_session_cookie`); правило «cookie нет» на обоих транспортах | closed |
| T-14-06 | Spoofing / Integrity (cookie на не том объекте) | `login_submit`, `register_complete` | high | mitigate | `response = await redirect_internal(...)` → `set_session_cookie(response, …)` → `return response`; тройное утверждение: заголовок, cookie, следующий `GET /dashboard` | closed |
| T-14-07 | Information Disclosure (токен в адресе, истории, журналах) | экраны кода регистрации и восстановления | medium | mitigate | Токен только скрытым полем — **6** полей `type="hidden"` в `auth/includes/`, в адресах шаблонов токена нет (D-08) | closed |
| T-14-10 | Spoofing / CSRF (поддельная форма возврата) | `stop_impersonation` | high | mitigate | `if not is_same_origin(request)` → голый 403 (`auth.py:691`, решение владельца D-01) | closed |
| T-14-11 | Elevation of Privilege (администратор остаётся под чужой личностью) | `stop_impersonation` | high | mitigate | Возврат перезаписывает cookie свежим токеном администратора (`create_access_token(admin.id, …)`), признак действующего лица снят; тройные пары возврата | closed |
| T-14-12 | Elevation of Privilege (заблокированный администратор выходит со свежим токеном) | `stop_impersonation` | high | mitigate | `if admin is None or admin.is_blocked` — ветка третья, уход `HX-Redirect` на `/login` без cookie | closed |
| T-14-13 | Elevation of Privilege (перехват восстановления под чужой личностью) | четыре шага восстановления | high | mitigate | Зависимость `forbid_when_impersonating` на четырёх шагах (**5** вхождений в `auth.py`); кода восстановления не заводится; пары на обоих транспортах | closed |
| T-14-14 | Repudiation (окно закрыто без замера) | реестр окон | low | mitigate | Окно 63 переведено `open` → `waived` ШТАТНОЙ командой после двух совпавших замеров (14 мест голого 403; `14 0 14`), замер записан в причину | closed |
| T-14-15 | Denial of Service (выход смены экрана на потоковом ответе) | `_respond_by_transport` | low | mitigate | Отказ `ValueError` на ответе без собранного тела; правило слоя с `StreamingResponse` (`test_htmx_response_layer.py:1183-1190`) | closed |
| T-14-16 | Elevation (перебор кода) | шаги подтверждения и восстановления | medium | mitigate | `attempts < CODE_MAX_ATTEMPTS` в отборе (`auth.py:410, :918`), инкремент на неверном коде (`:429`), остаток в тексте (`:431`) | closed |
| T-14-17 | Denial of Service (двойная отправка кода и повтора) | экраны кода | low | mitigate | `hx-sync='closest #auth-step:drop'` на ОБЕИХ формах обоих экранов кода; правило `test_both_code_forms_ride_the_anchor_and_drop_a_second_request` | closed |
| T-14-18 | Repudiation (изъятие без решения) | реестр гейтов | low | mitigate | Запись `SAFE_BY_NAME` с доказательством (операнд — ASCII-литерал), изъятие названо решением владельца, а не пропуском | closed |
| T-14-19 | Repudiation (самозаверение обхода) | `14-UAT.md` | low | mitigate | `tests/test_planning/test_the_walkthrough_cannot_self_certify.py`; файл обхода — `status: testing`, девять пустых таблиц отметок, девять `result: [pending]` | closed |
| T-14-20 | Tampering (преждевременная отметка требований) | REQUIREMENTS.md | low | mitigate | `tests/test_planning/test_requirement_completion_follows_verification.py`; SIGN-01…03 остаются `[ ]` / `Pending` — `mark-complete` не вызывался ни одним планом | closed |
| T-14-08 | Spoofing (подделка входа, login CSRF) | форма входа | medium | accept | Вне объёма фазы: решение владельца, `14-CONTEXT.md` §Deferred Ideas. `SameSite=Lax`; `HX-Request` проверкой безопасности не является | closed (accepted) |
| T-14-09 | Spoofing / Info Disclosure (перебор пароля, перечисление адресов) | `login_submit`, шаги отправки кода | medium | accept | Вне объёма фазы (CONTEXT Deferred); тексты переехали ДОСЛОВНО (D-15) — фаза различимость ответов не создавала | closed (accepted) |
| T-14-21 | Elevation of Privilege (переигрывание проверенного токена восстановления) | `forgot_password_reset` | high | accept | **Заведена ПОСЛЕ планирования** — находка ревизии кода (CR-02). См. «Вне реестра планирования» ниже | closed (accepted) |
| T-14-SC | Tampering (цепочка поставки) | установки пакетов | low | accept | Фаза не устанавливает ни одного пакета (RESEARCH §Package Legitimacy Audit) — проверено: в объёме фазы нет ни одного файла манифеста зависимостей | closed (accepted) |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Вне реестра планирования: T-14-21 (CR-02)

**Изъян.** `forgot_password_reset` проверенный токен НЕ ПОГАШАЕТ: `code_record.verified_at` он не
читает вовсе (поле читается и пишется только двумя обработчиками подтверждения — `auth.py:408,
:443, :916, :950`), а ветка короткого пароля выпускает СВЕЖИЙ проверенный токен на 30 минут
(`:1097`). Держатель токена продлевает возможность бесконечно, отправляя пятисимвольный пароль.

**Кто нашёл и чем подтверждено.** Ревизия кода Фазы 14 (`14-REVIEW.md`, CR-02). Подтверждено
тремя независимыми чтениями: ревизором, оркестратором и верификатором фазы. Верификатор ДАТИРОВАЛ
изъян — `git show fd69a26a` показывает те же четыре проверки `purpose`/`verified` ДО фазы.

**Почему `accept`, а не `open`.** Решение владельца 2026-09-23. Основания, записанные при принятии:
1. изъян СТАРШЕ фазы — Фаза 14 его не создавала и поверхность не расширяла;
2. локальное решение фазы D-15 («решения обработчика не меняются: тексты, порядок проверок,
   поведение токенов») ПРЯМО запрещало чинить его здесь — починка нарушила бы собственный
   замок фазы;
3. блокировать гейтом фазу, изъяна не создавшую, значило бы наказать не тот предмет.

**Чем риск НЕ поглощён.** Он назван здесь строкой реестра, а не растворён в нуле: `threats_open: 0`
означает «нет открытых угроз выше порога», а не «изъянов нет». Кроме того у закрепляющего правила
`test_a_new_password_leaves_for_the_login_by_a_full_load_with_the_notice`
(`tests/test_pages/test_auth_transport.py`) поставлена ЛЕТОПИСЬ: правило переиспользует один токен
на оба транспорта, и это сегодняшнее свойство обработчика, а не требование; когда CR-02 будут
чинить, правило ОБЯЗАНО покраснеть на втором POST, и чинить надо правило (два транспорта — два
токена), а не возвращать переигрывание ради зелени.

**Остаток.** Починка — отдельная задача вне Фазы 14. До неё окно возможности для держателя
проверенного токена — 30 минут с самообновлением.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-14-01 | T-14-08 | Login CSRF вне объёма фазы — записанное решение владельца (`14-CONTEXT.md` §Deferred Ideas); перевод на htmx поверхность не менял | chubav | 2026-09-22 |
| R-14-02 | T-14-09 | Перебор и перечисление вне объёма; тексты переехали дословно по D-15 | chubav | 2026-09-22 |
| R-14-03 | T-14-21 | Переигрывание проверенного токена восстановления: изъян старше фазы (доказано `git show fd69a26a`), D-15 запрещал чинить его в этой фазе, починка — отдельной задачей | chubav | 2026-09-23 |
| R-14-04 | T-14-SC | Фаза не устанавливает пакетов | chubav | 2026-09-22 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-23 | 22 | 22 | 0 | `/gsd-secure-phase 14` (оркестратор, режим «подтвердить смягчения», L1) |

**Что этот аудит НЕ закрывает.** CR-01 (девять из десяти POST авторизации без сверки источника
запроса) — это T-14-08 в своей общей форме: записанное отложенное решение владельца, а не
непокрытая угроза. Он остаётся действительным и после этой фазы. 23 запрета планов 14-01…14-07
стоят в `flagged_prohibitions` вердикта без машинного принуждения — предмет Фазы 15 SC6, не этого
аудита.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer) — 18 mitigate, 4 accept
- [x] Accepted risks documented in Accepted Risks Log — четыре записи, все с именем и датой
- [x] `threats_open: 0` confirmed — ноль означает «нет открытых выше порога `high`», и это сказано прямо: T-14-21 принят решением, а не отсутствует
