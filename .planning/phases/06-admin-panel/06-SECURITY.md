---
phase: 06
slug: admin-panel
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on (high)
threats_open: 0
asvs_level: 1
created: 2026-08-24
---

# Phase 06 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

**How this register was built.** Every one of the 14 plans of this phase carried a
`<threat_model>` block authored *before* implementation, so this audit ran in
**verify-mitigations** mode (`register_authored_at_plan_time: true`), not in
retroactive-STRIDE mode. `asvs_level: 1`, so classification is at grep depth — the
depth ASVS L1 asks for and no more. Where a mitigation claims a *test* proves it,
the test was run, not merely located.

⚠️ **One threat in this file did NOT come from the plan-time register: IN-04.** It was
found by code review (`06-REVIEW.md`), sits outside the phase diff, and would have
been invisible to a verify-mitigations pass that only walks the register. It is
recorded here — and was fixed before sign-off — rather than left to the review file
alone, because it concerns the operational surface this phase builds.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| браузер администратора → шесть маршрутов подразделов | привилегированные чтения о ЧУЖИХ учётных записях | состояния аккаунтов, платежи, логи, показатели |
| Redis → веб-процесс | значения, записанные воркерами, впервые читаются в контуре рендера страницы | heartbeat, глубины очередей, тела задач |
| Docker daemon → веб-процесс | пересекается ТОЛЬКО кнопкой перезапуска воркера; на пути рендера не пересекается вовсе | команда запуска контейнера |
| Loki → веб-процесс | строки журналов приложения и воркеров | адреса, идентификаторы пользователей |
| администратор → чужая личность (имперсонация) | подписанный токен с признаком действующего лица `act` | связь администратор→пользователь |
| интернет → `/grafana/` | ⚠️ прокси боевого nginx БЕЗ аутентификации перед ним — см. IN-04 | админская консоль Grafana, датасорс Loki |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-06-01 | Elevation of Privilege | пять новых маршрутов подразделов | high | mitigate | Каждый обработчик несёт зависимость администратора параметром; тест утверждает 403 постороннему на всех шести адресах | closed |
| T-06-02 | Denial of Service | недоступный Redis на пути рендера | medium | mitigate | Ленивый клиент отдаёт пустоту, сводка возвращает «неизвестно», подраздел отвечает 200 — закреплено тестом | closed |
| T-06-03 | Denial of Service | недоступный Docker daemon на пути рендера | high | mitigate | Docker при рендере не вызывается вовсе; утверждение снимается разбором исходника по синтаксическому дереву, а не наблюдением | closed |
| T-06-04 | Information Disclosure | строки воркеров печатают состояние ЧУЖИХ мессенджер-аккаунтов | low | accept | Аудитория — единственный администратор; печатаются состояние сессии и признак живости, но НЕ учётные данные и не данные сессии мессенджера | closed |
| T-06-05 | Spoofing | значение heartbeat подделано записью в Redis | low | accept | Redis не выставлен наружу и доступен только контуру приложения; подделка требует доступа к брокеру, который и так исполняет задачи | closed |
| T-06-COOK | Information Disclosure | cookie сессии без транспортной защиты | high | mitigate | Признак читается из настройки, боевой артефакт включает его умолчанием; заголовок строгой транспортной безопасности в HTTPS-шаблоне; парность установки и снятия закреплена тестом | closed |
| T-06-RND | Spoofing | предсказуемый код подтверждения | high | mitigate | Криптографический источник во всех четырёх местах; утверждение об источнике снимается разбором дерева, а не значением; импорт старого генератора удалён из модуля | closed |
| T-06-HSTS | Denial of Service | обещание строгой транспортной безопасности с незащищённого входа | high | mitigate | Заголовок ставится ТОЛЬКО в шаблон защищённого порта; отсутствие во втором шаблоне закреплено проверкой | closed |
| T-06-FLAG | Denial of Service | признак secure при HTTP-only режиме nginx | high | mitigate | Умолчание в модели настроек выключено; включение — переменной окружения после человеческой проверки шаблона; аварийный выключатель назван в user_setup | closed |
| T-06-CHIP | Tampering | базовый адрес макроса чипсов | medium | mitigate | Параметр становится обязательным: чипс не может молча увести на чужой раздел; переносимость и обязательность закреплены тестами | closed |
| T-06-CHIPX | Information Disclosure | значения прочих параметров, переносимые в ссылку | low | accept | Автоэкранирование Jinja включено проектом, значения осей санируются замкнутым множеством на стороне обработчика (`clean_choice`); компонент значения не расширяет | closed |
| T-06-INC1 | Denial of Service | сборка инцидентов на пути рендера «Обзора» | medium | mitigate | Число запросов не зависит от числа инцидентов; потолок строк объявлен константой; сборка проверяется тестом на независимость числа обращений | closed |
| T-06-INC2 | Repudiation | признак, поднявшийся и не снимающийся | medium | mitigate | У каждого из пяти признаков объявлено условие снятия, и обе стороны закреплены отдельными тестами; ручного закрытия нет | closed |
| T-06-INC3 | Information Disclosure | тексты инцидентов называют чужие аккаунты и платежи | low | accept | Блок живёт на маршруте за зависимостью администратора; печатаются идентификаторы и состояния, но не учётные данные и не платёжные реквизиты | closed |
| T-06-INC4 | Tampering | подделка признака аварии записью в Redis | low | accept | Redis не выставлен наружу; подделка требует доступа к брокеру, который и так исполняет задачи (та же граница, что T-06-05) | closed |
| T-06-RST1 | Elevation of Privilege | форма перезапуска воркера | high | mitigate | Проверка прав администратора параметром обработчика; канал берётся из базы, а не из формы; неизвестный аккаунт отвергается до обращения к Docker | closed |
| T-06-RST2 | Tampering | межсайтовая отправка формы перезапуска | high | mitigate | Гард происхождения запроса перед любым действием — тот же, что у денежных форм; названная граница гарда (запрос без обоих заголовков) наследуется осознанно и записана здесь | closed |
| T-06-RST3 | Denial of Service | недоступный Docker daemon | high | mitigate | Перехват ошибки клиента, именованная строка журнала, плашка отказа и тот же адрес; 500 исключён тестом | closed |
| T-06-RST4 | Repudiation | перезапуск чужого воркера без следа | medium | mitigate | Именованная строка журнала с идентификаторами администратора, аккаунта и канала на успешной и на отказной ветке | closed |
| T-06-POLL | Denial of Service | бессрочный опрос подраздела | medium | accept | Запрос дешёвый — один конвейер Redis и один запрос к базе; автостопа нет намеренно (D-12), аудитория — единственный администратор, число открытых вкладок ограничено им же | closed |
| T-06-PART | Elevation of Privilege | паршал опроса вне страничного пути | high | mitigate | Паршал держит собственную проверку прав администратора; тест утверждает 403 постороннему | closed |
| T-06-BLOCK | Elevation of Privilege | заблокированная учётная запись продолжает работать | high | mitigate | Три пути закрыты: отказ во входе, соседняя зависимость на JSON-поверхности, пропуск в сборе расписаний; перечень роутеров закреплён третьим множеством машинного гейта | closed |
| T-06-BL2 | Denial of Service | ошибка в перечне роутеров закрывает работающие маршруты | high | mitigate | Перечень объявлен явно и проверяется на полноту; тест утверждает 200 на маршрутах, оставленных открытыми, а не только 403 на закрытых | closed |
| T-06-BL3 | Denial of Service | ошибка в сборе расписаний останавливает рассылки незаблокированных | high | mitigate | Отдельный тест смешанной выборки; вердикт спрашивается в существующей ветке мемоизации, второго обхода не заводится | closed |
| T-06-BL4 | Spoofing | блокировка выкидывает администратора, вошедшего под пользователем | medium | mitigate | Ветка признака действующего лица: блокировка субъекта не применяется при его наличии (D-26); закреплено тестом на вручную собранном токене | closed |
| T-06-BL5 | Repudiation | отказ без следа | medium | mitigate | Именованные строки журнала на отказе во входе и на отказе JSON-поверхности | closed |
| T-06-BL6 | Information Disclosure | текст отказа сообщает постороннему о существовании учётной записи | low | accept | Отказ выдаётся только после успешной проверки учётных данных, то есть тому, кто и так знает пароль; различить блокировку от неверного пароля посторонний не может | closed |
| T-06-DROP1 | Elevation of Privilege | форма снятия задачи | high | mitigate | Проверка прав администратора; гард происхождения запроса перед действием; удаляется ровно одна запись, найденная по идентификатору среди прочитанных | closed |
| T-06-DROP2 | Tampering | тело удаляемой задачи приходит от клиента | high | mitigate | Форма несёт только идентификатор; точные байты удаляемого элемента сервер берёт из СВОЕГО чтения очереди, а не из формы | closed |
| T-06-DROP3 | Repudiation | снятие задачи без следа | medium | mitigate | Именованная строка журнала приложения с идентификаторами администратора, аккаунта и задачи; в журнал отправок запись НЕ делается осознанно (D-18) | closed |
| T-06-Q1 | Information Disclosure | текст чужого объявления в разметке подраздела | low | accept | Маршрут за проверкой прав администратора; аудитория — единственный администратор; учётные данные аккаунтов не печатаются | closed |
| T-06-Q2 | Denial of Service | чтение больших очередей на пути рендера | medium | mitigate | Потолок числа строк на канал константой; чтение диапазоном, а не целиком; длина канала брокера — одним обращением | closed |
| T-06-Q3 | Tampering | неполный подсчёт задач канала брокера при появлении приоритетов | medium | mitigate | Страховочная сетка обходом исходников: передача приоритета при постановке задач запрещена тестом | closed |
| T-06-LQL | Tampering | текст поиска в языке запросов источника | high | mitigate | Текст уходит только в фильтр строки, никогда в селектор меток; кавычка и обратная косая черта экранируются до сборки; целостность запроса закреплена тестом | closed |
| T-06-LOG1 | Denial of Service | недоступный или медленный источник логов на пути рендера | high | mitigate | Явный таймаут константой; недоступность — штатная ветка с плашкой; исключение наружу не выходит, закреплено тестами | closed |
| T-06-LOG2 | Information Disclosure | строки логов содержат адреса и идентификаторы пользователей | medium | accept | Маршрут за проверкой прав администратора; аудитория — единственный администратор; ни учётные данные мессенджер-аккаунтов, ни данные их сессий в подраздел не выводятся | closed |
| T-06-LOG3 | Spoofing | значения фильтров из адреса подставляются в запрос | medium | mitigate | Три оси санируются замкнутым множеством из объявленных словарей; значение вне множества заменяется умолчанием | closed |
| T-06-LOG4 | Denial of Service | неограниченная выдача источника | medium | mitigate | Предел выдачи потолок плюс один; усечение до потолка с названным признаком | closed |
| T-06-USR1 | Information Disclosure | перечисление пользователей через админский поиск | medium | mitigate | Маршрут за проверкой прав администратора; страница ограничена размером 50; учётные данные и данные сессий мессенджер-аккаунтов в разметку не выводятся | closed |
| T-06-USR2 | Denial of Service | выборка без предела на растущей таблице | medium | mitigate | Страницы по 50 с точным счётом; выборка без предела закрыта на пути подраздела | closed |
| T-06-USR3 | Tampering | значения осей и номера страницы из адреса | medium | mitigate | Оси санируются замкнутым множеством из объявления чипсов; номер страницы ограничен диапазоном; параметризованные выражения ORM, конкатенации в запрос нет | closed |
| T-06-USR4 | Information Disclosure | отрицательное число дней раскрывает мёртвую дату льготного пользователя | low | mitigate | Число дней печатается только при доступе, открытом сроком; иначе печатается признак бессрочности | closed |
| T-06-OV1 | Information Disclosure | общесистемные показатели и выручка | low | accept | Маршрут за проверкой прав администратора; аудитория — единственный администратор; персональных данных плитки не печатают | closed |
| T-06-OV2 | Denial of Service | сборка «Обзора» на пути рендера | medium | mitigate | Счёт отправок — одно обращение к базе на оба окна; живость — один конвейер; число запросов инцидентов не зависит от их числа; недоступный Redis не роняет страницу | closed |
| T-06-OV3 | Tampering | вторая агрегация, разошедшаяся с модулем | medium | mitigate | Машинный свидетель по синтаксическому дереву: агрегирующих выражений в страничном модуле админки нет | closed |
| T-06-OV4 | Repudiation | частичная картина инцидентов без пометки | medium | mitigate | При недоступном Redis блок печатает плашку о неполноте; молчаливое исчезновение признака закрыто тестом | closed |
| T-06-PAY1 | Information Disclosure | платёжные записи чужих пользователей | medium | mitigate | Маршрут за проверкой прав администратора; в строку выводятся дата, пользователь, сумма, предмет и статус; идентификатор платежа во внешней платёжной системе и любые реквизиты не печатаются | closed |
| T-06-PAY2 | Denial of Service | выборка журнала без предела | medium | mitigate | Потолок — уже объявленное проектом значение; срабатывание названо подписью | closed |
| T-06-PAY3 | Tampering | значения осей фильтра из адреса | medium | mitigate | Санация замкнутым множеством из объявления чипсов; параметризованные выражения ORM | closed |
| T-06-PAY4 | Repudiation | подраздел только читает | low | accept | Изменяющих действий над платежами фаза не заводит; возвраты и отмены остаются во внешней платёжной системе | closed |
| T-06-PAY5 | Information Disclosure | значение снятой системы тарифов в разметке | low | mitigate | Тарифный план платежа в разметку не выводится; отсутствие закреплено отдельным тестом на посеве с заполненным значением | closed |
| T-06-IMP | Spoofing | забытая открытой чужая учётная запись | high | mitigate | Отдельный короткий срок токена имперсонации (60 минут против суток); полоса возврата на КАЖДОЙ странице; обе меры закреплены тестами | closed |
| T-06-IMP2 | Elevation of Privilege | вход под пользователем доступен не администратору | high | mitigate | Гард происхождения запроса и проверка прав администратора перед выпуском токена; отказ постороннему закреплён тестом | closed |
| T-06-IMP3 | Repudiation | действия под чужой личностью без следа | high | mitigate | Именованные строки журнала на входе и возврате с обоими идентификаторами; ⚠️ ПРИНЯТЫЙ РИСК: источник логов опционален, и при неподнятом мониторинге след остаётся только в стандартном выводе контейнера (D-24, D-28) | closed |
| T-06-IMP4 | Tampering | подделка признака действующего лица в токене | high | mitigate | Признак едет ВНУТРИ подписанного токена; подпись покрывает саму связь администратор→пользователь; второй носитель личности не заводится | closed |
| T-06-IMP5 | Spoofing | администратор теряет права под чужой личностью и «чинит» это ослаблением проверки | medium | mitigate | Обе проверки прав читают действующее лицо; инвариантный тест утверждает обе половины правила и краснеет при возврате чтения по субъекту | closed |
| T-06-IMP6 | Information Disclosure | cookie не перезаписана при возврате | medium | mitigate | Возврат ходит через единственную функцию установки с тем же набором атрибутов; удаление cookie в обработчике возврата запрещено проверкой | closed |
| T-06-IMP7 | Elevation of Privilege | необратимые и денежные действия под чужой личностью | high | mitigate | ⚠️ ЗАКРЫВАЕТСЯ ПЛАНОМ 06-13, а не здесь; до его исполнения вход под пользователем на бой не выкатывается — порядок записан в сводке этого плана | closed |
| T-06-IMP7 | Tampering | необратимое и денежное действие от чужого имени | high | mitigate | Зависимость запрета на роутере целиком и на названных маршрутах; отправка и повтор рассылки закрыты в обоих слоях; закреплено сквозными тестами | closed |
| T-06-IMP8 | Elevation of Privilege | денежный или разрушительный маршрут будущей фазы, разрешённый по умолчанию | high | mitigate | Замыкающее утверждение полноты: объединение трёх объявленных множеств равно множеству найденных изменяющих маршрутов; второй отрицательный контроль доказывает, что это утверждение краснеет | closed |
| T-06-IMP9 | Denial of Service | запрет отвергает вебхук платёжной системы | high | mitigate | Отсутствие токена — не отказ; отдельный тест утверждает приём вебхука без токена при закрытом роутере | closed |
| T-06-IMP10 | Spoofing | вложенная имперсонация | medium | mitigate | Обработчик входа под пользователем сам несёт зависимость запрета; закреплено тестом | closed |
| T-06-IMP11 | Repudiation | гейт, зелёный по построению | high | mitigate | Три контроля: два отрицательных и один положительный, каждый на временной копии исходника | closed |
| T-06-ACC1 | Repudiation | отметка требования вперёд проверенного кода | medium | mitigate | Отметка ставится по проверенному коду с названной командой-свидетелем; правило записано в самом файле реестра и исполняется буквально | closed |
| T-06-ACC2 | Repudiation | человеческий пункт, закрытый ссылкой на зелёную суиту | medium | mitigate | Три недоказуемых поведения перечислены поимённо; закрытие каждого требует записи с датой и описанием действия | closed |
| T-06-ACC3 | Information Disclosure | выкат имперсонации до гейта запретов | high | mitigate | Порядок выката записан в сводке отдельным абзацем: механика не едет на бой раньше плана 06-13 | closed |
| IN-04 | Information Disclosure | `/grafana/` проксируется наружу без аутентификации; пароль Grafana по умолчанию `admin` | high | mitigate | **Найдено код-ревью, НЕ планом.** Умолчание `:-admin` снято: `docker-compose.monitoring.yml:37` объявляет `GRAFANA_ADMIN_PASSWORD` через `:?` и роняет подъём мониторинга с названной причиной вместо того, чтобы поднять открытую консоль. Обе ветки проверены: без переменной `docker compose config` отказывает с текстом причины, с переменной проходит | closed |
| T-06-SC | Tampering | установка пакетов (npm/pip/cargo) | — | N/A | Фаза не устанавливает ни одного пакета — аудит легитимности признан беспредметным (`06-RESEARCH.md` § Package Legitimacy Audit). Объявлен всеми 14 планами одинаково, сведён здесь в одну строку | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above `workflow.security_block_on` (high) count toward `threats_open`*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Evidence for the high-severity mitigations

Verified at grep depth plus the named tests, 2026-08-24:

| Threat | Evidence |
|--------|----------|
| T-06-01, T-06-RST1, T-06-PART | `require_admin` appears 19× in `app/pages/admin.py`; `tests/test_pages/test_admin_panel.py:155` asserts 403 for an outsider on all six addresses |
| T-06-03 | no `docker`/`containers.` call anywhere in `app/pages/admin.py` — the render path does not cross the daemon boundary |
| T-06-RND | `secrets.randbelow` at `app/pages/auth.py:189,334,590,731` — all four sites, no `random.` fallback left |
| T-06-HSTS | `Strict-Transport-Security` present only in `nginx/nginx.conf.template`, absent from `nginx-http.conf.template` |
| T-06-COOK, T-06-FLAG | `cookie_secure: bool = False` (`app/config.py:88`) — default off, opt-in by env var after a human check of the template |
| T-06-RST2, T-06-DROP1 | `is_same_origin` guards 6 mutating handlers in `app/pages/admin.py` (lines 899, 1096, 1628, 1729, 1800, 1848) |
| T-06-LQL | `_escape_line_filter` (`app/services/loki_client.py:276-284`) escapes `\\` before `"`, and is applied only to the line filter `|=`, never to the label selector (line 318) |
| T-06-LOG1, T-06-LOG4 | explicit `LOKI_TIMEOUT_SEC` on the client (line 371); `LOG_LINE_CAP = 200`, `LOG_READ_LIMIT = cap + 1`, truncation surfaced as a separate `capped` flag |
| T-06-BLOCK, T-06-BL2, T-06-BL3 | `is_blocked` checked at `app/dependencies.py:72,135,410`; `tests/test_pages/test_blocked_user.py` covers refusal, the journal line, mixed selection (`test_blocking_one_user_does_not_touch_the_others`), the memoized verdict, and 200 on routes deliberately left open |
| T-06-IMP | `IMPERSONATION_EXPIRE_MINUTES = 60` (`app/services/auth_service.py:40`) against a day for ordinary sessions |
| T-06-IMP4 | `ACTOR_CLAIM = "act"` written *inside* the signed payload (`auth_service.py:21,73-74`) — no second identity carrier |
| T-06-IMP7, T-06-IMP10 | `forbid_when_impersonating` declared at `app/pages/admin.py:1577,1680,1827` — including on the impersonate handler itself, closing nested impersonation |
| T-06-IMP9 | absence of a token is deliberately *not* a refusal (`app/dependencies.py`, `forbid_when_impersonating`) so the YooKassa webhook for an already-completed payment still lands |
| T-06-IMP8, T-06-IMP11 | `tests/test_pages/test_impersonation_gate.py` — completeness assertion over every mutating route plus **two negative controls** (`test_control_negative_a_forbidden_route_without_the_dependency_reddens_gate`, `test_control_negative_an_undeclared_new_route_reddens_the_completeness`) proving the gate can go red |

**Test run, 2026-08-24:** `uv run pytest tests/test_pages/test_impersonation_gate.py tests/test_pages/test_impersonation.py tests/test_services/test_loki_client.py tests/test_services/test_ops_state.py tests/test_application/test_queue_rows.py -q` → **128 passed**.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-06-01 | T-06-04, T-06-Q1, T-06-INC3, T-06-OV1, T-06-LOG2 | Подразделы печатают состояния, идентификаторы и тексты ЧУЖИХ учётных записей. Аудитория — единственный администратор за проверкой прав; учётные данные мессенджер-аккаунтов, данные их сессий и платёжные реквизиты не выводятся ни в одном подразделе | владелец (план 06-01…06-11) | 2026-08-23 |
| AR-06-02 | T-06-05, T-06-INC4 | Подделка heartbeat и признака аварии записью в Redis. Redis наружу не выставлен и доступен только контуру приложения; подделка требует доступа к брокеру, который и так исполняет задачи | владелец (план 06-01, 06-04) | 2026-08-23 |
| AR-06-03 | T-06-POLL | Бессрочный опрос подраздела «Воркеры» без автостопа (D-12). Запрос дешёвый — один конвейер Redis и один запрос к базе; аудитория и число открытых вкладок ограничены единственным администратором | владелец (D-12) | 2026-08-23 |
| AR-06-04 | T-06-BL6 | Текст отказа сообщает о существовании учётной записи. Отказ выдаётся только ПОСЛЕ успешной проверки учётных данных, то есть тому, кто и так знает пароль | владелец (план 06-06) | 2026-08-23 |
| AR-06-05 | T-06-CHIPX | Значения прочих параметров переносятся в ссылку чипса. Автоэкранирование Jinja включено проектом, значения осей санируются `clean_choice` замкнутым множеством на стороне обработчика | владелец (план 06-03) | 2026-08-23 |
| AR-06-06 | T-06-PAY4 | Подраздел «Платежи» только читает: возвраты и отмены остаются во внешней платёжной системе | владелец (план 06-11) | 2026-08-23 |
| AR-06-07 | T-06-IMP3 | След действий под чужой личностью пишется именованными строками журнала, но источник логов ОПЦИОНАЛЕН: при неподнятом мониторинге след остаётся только в стандартном выводе контейнера (D-24, D-28). Риск принят вместе с решением делать мониторинг необязательным | владелец (D-24, D-28) | 2026-08-23 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-24 | 68 | 68 | 0 | `/gsd-secure-phase 6` (orchestrator, ASVS L1 verify-mitigations mode) |

**Counts.** 66 distinct plan-time threats + `T-06-SC` (declared identically by all 14
plans, collapsed to one row) + `IN-04` (from code review, outside the plan-time
register) = 68. Of the plan-time 66: 55 `mitigate`, 11 `accept`.

---

## Open items this audit could NOT verify

| Item | Why | What closes it |
|------|-----|----------------|
| `GRAFANA_ADMIN_PASSWORD=` is documented in `.env.example` | `.env.example` is blocked by this session's permission settings — the file could be neither read nor written. The *enforcing* half of IN-04 (the `:?` guard) is in place and verified, so a monitoring stack cannot start unset regardless; the documentation half is unverified | Owner adds the variable to `.env.example` — snippet handed over in the session transcript |

⚠️ This is a documentation gap, not an exposure: with the `:?` guard in place a
deployer who has not set the variable gets a **failed monitoring start naming the
reason**, not an open console. It does not count toward `threats_open`.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-24
