---
schema_version: 1
open_count: 15
waived_count: 1
fixed_count: 4
total_count: 20
last_updated: 2026-09-02T15:03:33.140Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 06 | deviation | tests/test_pages/test_ads_editor.py |  | test_image_base_url_comes_from_app_settings краснеет только в общем прогоне; контрольный прогон без файла тестов плана 06-04 даёт тот же красный — предсуществующая порядковая зависимость суиты | open |  | 2026-08-22T07:47:15.265Z |  |
| 2 | 06 | deviation | app/application/admin/incidents.py |  | Адрес вида failure_spike ведёт в /history?status=fail — раздел истории САМОГО администратора, а не общесистемный: маршрут живой и тест его находит, но по нему видны отказы одного человека, тогда как признак считает весь сервис. D-48 предписывает «Историю с фильтром» буквально, поэтому план 06-10 адрес НЕ менял; выбор между буквой D-48 и /admin/logs?level=error — решение владельца | fixed |  | 2026-08-23T01:59:34.260Z | 2026-08-23T05:18:45.298Z |
| 3 | 06 | deviation | .planning/phases/06-admin-panel/06-11-PLAN.md |  | must_haves плана 06-11 требуют 'def monthly_revenue' и чтение has_free_access внутри app/application/admin/payments_query.py — оба невыполнимы: гейт test_the_free_access_flag_is_read_in_exactly_one_place_of_the_decision читает ТЕКСТ и допускает признак ровно в одном файле app/application/, а monthly_revenue уже отгружена планом 06-10 в overview_stats.py. План 06-11 переиспользовал обе величины и положил три условия в слой доступа к данным; гейт не ослаблен. Требуется подтверждение владельца, что править надо must_haves плана, а не код | open |  | 2026-08-23T07:04:02.702Z |  |
| 4 | 06 | unmet-truth | app/templates/admin/user_detail.html |  | НЕ СЛИВАТЬ И НЕ ДЕПЛОИТЬ ветку фазы 6 до приземления плана 06-13. План 06-12 отгрузил механику имперсонации и живую кнопку «Войти под пользователем» на карточке пользователя, но машинный гейт D-22/D-23, запрещающий необратимое и денежное под чужой личностью, строит план 06-13. В промежутке администратор под чужой личностью может НЕОБРАТИМО отправить рассылку в чужие группы. Проверено оркестратором: гейта в app/dependencies.py на этой ревизии нет; origin/master стоит на 7ef819d, из фазы 6 не выкачено ничего, поэтому опасность заперта в невыкаченной ветке. Закрывается приземлением 06-13. | fixed |  | 2026-08-23T10:17:16.138Z | 2026-08-23T11:45:32.296Z |
| 5 | 06 | unrun-verify | .planning/phases/06-admin-panel/06-14-PLAN.md |  | Человеческая приёмка задачи 2 плана 06-14 НЕ ПРОВОДИЛАСЬ: шесть пунктов (вёрстка шести подразделов на 375px; простой воркера на живом стенде; плашка недоступного источника логов; имя контейнера службы канала telegram в метках; разбираемый формат журналирования в бою; видимость очередей воркеров из веб-процесса). Исполнитель работал в изолированном рабочем дереве без живого стенда и браузера. Ни один пункт не закрыт зелёной суитой — все шесть остаются открытыми и требуют владельца | open |  | 2026-08-23T12:51:54.792Z |  |
| 6 | 06 | unmet-truth | monitoring/promtail.yml |  | Фильтр уровня подраздела «Логи» селектирует по метке потока level (app/services/loki_client.py:311, level=~"..."), которую шиппящийся monitoring/promtail.yml не создаёт ни одним правилом: relabel_configs дают container_name, stream, compose_project, compose_service, broadcaster_role, account_id; pipeline_stages — один docker:{}, разворачивающий обёртку и ничего не извлекающий из тела строки. Суита увидеть этого не могла — её потоки несут метку level, вписанную руками (tests/test_services/test_loki_client.py:103), то есть доказывает контракт клиента ПРИ наличии метки, а не появление метки в бою. Ожидаемое следствие на живом стенде: выбор любого чипа уровня даёт пустую выдачу при исправном на вид запросе. Найдено приёмкой 06-14 по репозиторию; НЕ исправлено намеренно — правка есть конфигурация сборщика плюс перевыкат мониторинга, задача приёмки кода не меняет | waived | НАХОДКА НЕ ПОДТВЕРДИЛАСЬ (проверено оркестратором): запись читает только ПЕРВУЮ стадию конвейера promtail. Дальше идут три блока match, каждый поднимает level в метку Loki — compose-сервисы (стр. 35-44), wa-worker с template Pino 10..60 в слова (стр. 46-59), max-worker (стр. 61-70). Значения сходятся с LEVEL_CHIPS клиента, обе стороны строчными. D-27 описывает конфиг верно, фильтр уровня работает. Снято, чтобы никто не чинил работающий конфиг. | 2026-08-23T12:52:09.284Z | 2026-08-23T13:18:32.360Z |
| 7 | 06 | unmet-truth | app/pages/admin.py |  | Первый выкат фазы 6 покажет инфраструктурный блок «Воркеров» как «отключён», пока три celery-контейнера (celery-beat, celery-worker-telegram, celery-worker-default) не перевыкачены: признак живости пишут САМИ процессы своими обработчиками beat_init/worker_init раз в 30 с (решение владельца D-52). Это отсутствие ещё не выкаченного источника, а не ложное показание, — но на экране будет выглядеть аварией, и принимающий обязан знать это до того, как посмотрит. Закрывается перевыкатом, не правкой кода | open |  | 2026-08-23T12:52:20.381Z |  |
| 8 | 06 | unmet-truth | docker-compose.monitoring.yml |  | ПРЕД-СУЩЕСТВУЮЩЕЕ, вне предмета фазы 6 — найдено код-ревью фазы (IN-04), проверено оркестратором. Grafana проксируется наружу по /grafana/ ОБОИМИ шаблонами nginx (nginx.conf.template:65, nginx-http.conf.template:25), пароль администратора берётся как GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:-admin} (docker-compose.monitoring.yml:37), а переменная GRAFANA_ADMIN_PASSWORD в .env.example НЕ УПОМЯНУТА ВОВСЕ. Оператор, идущий по документированной настройке, про неё не узнает, и при поднятом мониторинге Grafana доступна публично с admin/admin. Фаза 6 трогала эти шаблоны только ради HSTS; проксирование Grafana ей предшествует. Дешёвая половина починки — объявить переменную в .env.example. | open |  | 2026-08-23T16:05:35.112Z |  |
| 9 | quick-260826-6jq | deviation | tests/test_planning/test_state_progress_matches_roadmap.py |  | ПРЕД-СУЩЕСТВУЮЩЕЕ, вне предмета быстрой задачи 260826-6jq. Тест выводит счёт планов из отметок .planning/ROADMAP.md и сверяет с progress.total_plans / progress.completed_plans во frontmatter .planning/STATE.md: выводится 0, записано 110. Оба коммита задачи (a97a583, ba169b7) не тронули .planning ни одним байтом (git diff --stat HEAD~2 HEAD -- .planning пуст). ROADMAP.md обнулён коммитом 3d1e672 'chore: archive v2.0 milestone files' — строки фаз уехали в milestones/v2.0-phases/, и выводить счёт стало не из чего. НЕ починено намеренно: правка STATE.md ради зелёного занизила бы счёт закрытой вехи до нуля, потеряв запись 110/110, которую сама STATE.md объясняет как выправленную при закрытии вехи. Решает тот, кто закрывает веху (/gsd-new-milestone или /gsd-health). | open |  | 2026-08-26T05:45:08.562Z |  |
| 10 | quick-260826-jql | unrun-verify | app/messengers/telegram_user.py |  | Боевая проверка отправки не выполнена: объявление с одной картинкой в реальную Telegram-группу и русский текст потери доступа в истории отправок требуют живого сервера (D5, human_judgment) | open |  | 2026-08-26T14:50:52.666Z |  |
| 11 | 07 | unrun-verify | .planning/phases/07-obnovlenie-htmx-do-2-0-10-i-blok-konfiguratsii/07-UAT.md |  | Ручной обход 07-UAT.md создан, отметки НЕ заполнены: поведенческие половины FOUND-01 и QUAL-05 закрываются глазами на приёмке фазы. Процедура пункта 1 была НЕИСПОЛНИМА как написана (отправляла наблюдать ключ в localStorage, где отгруженный 2.0.10 его не держит) и исправлена планом 07-04: предмет записи перестал быть недостижимым, но запись остаётся ОТКРЫТОЙ — закрывает её человек, прошедший обход | open |  | 2026-08-27T10:23:15.664Z |  |
| 12 | 09 | unrun-verify | app/templates/account_groups/includes/group_row.html |  | Строка консоли 7.1 (hx-include) после правки плана 09-11 в браузере повторно НЕ наблюдалась — снятие DIV-09-01 утверждается машинным правилом, а не глазом | fixed |  | 2026-08-31T04:22:01.251Z | 2026-09-02T14:59:39.889Z |
| 13 | 09 | deviation | tests/test_pages/test_account_groups.py |  | Второе следствие DIV-09-01 остаётся открытым под записью INCLUDE_TARGET_EXCEPTIONS['group-list-sentinel'], назначенная фаза — Фаза 15 | fixed |  | 2026-08-31T04:22:01.682Z | 2026-09-02T14:59:42.909Z |
| 14 | 09 | deviation | tests/test_pages/test_admin_panel.py |  | DEF-09-01: test_the_overview_error_number_matches_the_users_own_dashboard краснеет в окно 00:00-05:00 из-за расхождения суточного и календарного окон; к правке плана 09-11 не относится | open |  | 2026-08-31T04:22:02.108Z |  |
| 15 | 09 | todo | .planning/phases/09-pilot-na-account-groups-skvoznoy-kontrakt-formy/deferred-items.md |  | DEF-09-02 — «Отмена» панели подтверждения закрывает панель, но летящий запрос удаления не отменяет; назначенная Фаза 10 | open |  | 2026-08-31T07:43:11.328Z |  |
| 16 | 09 | deviation | .planning/phases/09-pilot-na-account-groups-skvoznoy-kontrakt-formy/09-UAT.md |  | Проверка 6.3 второго круга снята в две части (Slow 3G в полёте, Offline после отказа) — отступление от порядка шагов UAT, оговорка О-1 | open |  | 2026-08-31T07:43:11.798Z |  |
| 17 | 09 | deviation | .planning/phases/09-pilot-na-account-groups-skvoznoy-kontrakt-formy/09-UAT.md |  | Стенд UAT9- не был убран владельцем: сообщено groups=0, измерено groups=32 accounts=2; уборка выполнена исполнителем, оговорка О-4 | open |  | 2026-08-31T07:43:12.216Z |  |
| 18 | 09 | unrun-verify | .planning/phases/09-pilot-na-account-groups-skvoznoy-kontrakt-formy/09-UAT.md |  | Оговорка О-6 четвёртого круга: название последней видимой строки (шаг 4.1.9) владелец дословно НЕ транскрибировал; сверка 4.1.14 проведена и расхождений не дала, но повторяемость шага ограничена — следующий обход не сможет опереться на выписанное имя | open |  | 2026-09-02T15:03:20.319Z |  |
| 19 | 09 | unrun-verify | .planning/phases/09-pilot-na-account-groups-skvoznoy-kontrakt-formy/09-UAT.md |  | Оговорка О-7 четвёртого круга: у шагов 4.1.11 и 4.1.12 нет литеральных значений (вкладка закрыта до транскрипции) — прямого ответа про прокрутку после удаления и вывода document.documentElement.className в отметке НЕТ, стоит вердикт владельца. Литералы не сочинены. Механизм компенсаторно измерен буквальными выражениями шагом 4.2.6 на более опасной ветке | open |  | 2026-09-02T15:03:26.333Z |  |
| 20 | 09 | deviation | .planning/phases/09-pilot-na-account-groups-skvoznoy-kontrakt-formy/09-UAT.md |  | Оговорка О-8 четвёртого круга: обход проведён на ПРОДЕ https://broadcaster.all-torgi.ru (аккаунт 53), а не на localhost по букве раздела «Как привести стенд»; посев и уборка шли против БОЕВОЙ базы 192.168.0.9:5432/broadcaster. Поколение дерева подтверждено тремя пробами в консоли; стенд убран и проверен машинно (UAT9- rows: groups=0 accounts=0) | open |  | 2026-09-02T15:03:33.140Z |  |

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
  },
  {
    "id": 2,
    "kind": "deviation",
    "phase": "06",
    "file": "app/application/admin/incidents.py",
    "line": null,
    "description": "Адрес вида failure_spike ведёт в /history?status=fail — раздел истории САМОГО администратора, а не общесистемный: маршрут живой и тест его находит, но по нему видны отказы одного человека, тогда как признак считает весь сервис. D-48 предписывает «Историю с фильтром» буквально, поэтому план 06-10 адрес НЕ менял; выбор между буквой D-48 и /admin/logs?level=error — решение владельца",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-08-23T01:59:34.260Z",
    "resolved_at": "2026-08-23T05:18:45.298Z"
  },
  {
    "id": 3,
    "kind": "deviation",
    "phase": "06",
    "file": ".planning/phases/06-admin-panel/06-11-PLAN.md",
    "line": null,
    "description": "must_haves плана 06-11 требуют 'def monthly_revenue' и чтение has_free_access внутри app/application/admin/payments_query.py — оба невыполнимы: гейт test_the_free_access_flag_is_read_in_exactly_one_place_of_the_decision читает ТЕКСТ и допускает признак ровно в одном файле app/application/, а monthly_revenue уже отгружена планом 06-10 в overview_stats.py. План 06-11 переиспользовал обе величины и положил три условия в слой доступа к данным; гейт не ослаблен. Требуется подтверждение владельца, что править надо must_haves плана, а не код",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-23T07:04:02.702Z",
    "resolved_at": null
  },
  {
    "id": 4,
    "kind": "unmet-truth",
    "phase": "06",
    "file": "app/templates/admin/user_detail.html",
    "line": null,
    "description": "НЕ СЛИВАТЬ И НЕ ДЕПЛОИТЬ ветку фазы 6 до приземления плана 06-13. План 06-12 отгрузил механику имперсонации и живую кнопку «Войти под пользователем» на карточке пользователя, но машинный гейт D-22/D-23, запрещающий необратимое и денежное под чужой личностью, строит план 06-13. В промежутке администратор под чужой личностью может НЕОБРАТИМО отправить рассылку в чужие группы. Проверено оркестратором: гейта в app/dependencies.py на этой ревизии нет; origin/master стоит на 7ef819d, из фазы 6 не выкачено ничего, поэтому опасность заперта в невыкаченной ветке. Закрывается приземлением 06-13.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-08-23T10:17:16.138Z",
    "resolved_at": "2026-08-23T11:45:32.296Z"
  },
  {
    "id": 5,
    "kind": "unrun-verify",
    "phase": "06",
    "file": ".planning/phases/06-admin-panel/06-14-PLAN.md",
    "line": null,
    "description": "Человеческая приёмка задачи 2 плана 06-14 НЕ ПРОВОДИЛАСЬ: шесть пунктов (вёрстка шести подразделов на 375px; простой воркера на живом стенде; плашка недоступного источника логов; имя контейнера службы канала telegram в метках; разбираемый формат журналирования в бою; видимость очередей воркеров из веб-процесса). Исполнитель работал в изолированном рабочем дереве без живого стенда и браузера. Ни один пункт не закрыт зелёной суитой — все шесть остаются открытыми и требуют владельца",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-23T12:51:54.792Z",
    "resolved_at": null
  },
  {
    "id": 6,
    "kind": "unmet-truth",
    "phase": "06",
    "file": "monitoring/promtail.yml",
    "line": null,
    "description": "Фильтр уровня подраздела «Логи» селектирует по метке потока level (app/services/loki_client.py:311, level=~\"...\"), которую шиппящийся monitoring/promtail.yml не создаёт ни одним правилом: relabel_configs дают container_name, stream, compose_project, compose_service, broadcaster_role, account_id; pipeline_stages — один docker:{}, разворачивающий обёртку и ничего не извлекающий из тела строки. Суита увидеть этого не могла — её потоки несут метку level, вписанную руками (tests/test_services/test_loki_client.py:103), то есть доказывает контракт клиента ПРИ наличии метки, а не появление метки в бою. Ожидаемое следствие на живом стенде: выбор любого чипа уровня даёт пустую выдачу при исправном на вид запросе. Найдено приёмкой 06-14 по репозиторию; НЕ исправлено намеренно — правка есть конфигурация сборщика плюс перевыкат мониторинга, задача приёмки кода не меняет",
    "status": "waived",
    "reason": "НАХОДКА НЕ ПОДТВЕРДИЛАСЬ (проверено оркестратором): запись читает только ПЕРВУЮ стадию конвейера promtail. Дальше идут три блока match, каждый поднимает level в метку Loki — compose-сервисы (стр. 35-44), wa-worker с template Pino 10..60 в слова (стр. 46-59), max-worker (стр. 61-70). Значения сходятся с LEVEL_CHIPS клиента, обе стороны строчными. D-27 описывает конфиг верно, фильтр уровня работает. Снято, чтобы никто не чинил работающий конфиг.",
    "recorded_at": "2026-08-23T12:52:09.284Z",
    "resolved_at": "2026-08-23T13:18:32.360Z"
  },
  {
    "id": 7,
    "kind": "unmet-truth",
    "phase": "06",
    "file": "app/pages/admin.py",
    "line": null,
    "description": "Первый выкат фазы 6 покажет инфраструктурный блок «Воркеров» как «отключён», пока три celery-контейнера (celery-beat, celery-worker-telegram, celery-worker-default) не перевыкачены: признак живости пишут САМИ процессы своими обработчиками beat_init/worker_init раз в 30 с (решение владельца D-52). Это отсутствие ещё не выкаченного источника, а не ложное показание, — но на экране будет выглядеть аварией, и принимающий обязан знать это до того, как посмотрит. Закрывается перевыкатом, не правкой кода",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-23T12:52:20.381Z",
    "resolved_at": null
  },
  {
    "id": 8,
    "kind": "unmet-truth",
    "phase": "06",
    "file": "docker-compose.monitoring.yml",
    "line": null,
    "description": "ПРЕД-СУЩЕСТВУЮЩЕЕ, вне предмета фазы 6 — найдено код-ревью фазы (IN-04), проверено оркестратором. Grafana проксируется наружу по /grafana/ ОБОИМИ шаблонами nginx (nginx.conf.template:65, nginx-http.conf.template:25), пароль администратора берётся как GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:-admin} (docker-compose.monitoring.yml:37), а переменная GRAFANA_ADMIN_PASSWORD в .env.example НЕ УПОМЯНУТА ВОВСЕ. Оператор, идущий по документированной настройке, про неё не узнает, и при поднятом мониторинге Grafana доступна публично с admin/admin. Фаза 6 трогала эти шаблоны только ради HSTS; проксирование Grafana ей предшествует. Дешёвая половина починки — объявить переменную в .env.example.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-23T16:05:35.112Z",
    "resolved_at": null
  },
  {
    "id": 9,
    "kind": "deviation",
    "phase": "quick-260826-6jq",
    "file": "tests/test_planning/test_state_progress_matches_roadmap.py",
    "line": null,
    "description": "ПРЕД-СУЩЕСТВУЮЩЕЕ, вне предмета быстрой задачи 260826-6jq. Тест выводит счёт планов из отметок .planning/ROADMAP.md и сверяет с progress.total_plans / progress.completed_plans во frontmatter .planning/STATE.md: выводится 0, записано 110. Оба коммита задачи (a97a583, ba169b7) не тронули .planning ни одним байтом (git diff --stat HEAD~2 HEAD -- .planning пуст). ROADMAP.md обнулён коммитом 3d1e672 'chore: archive v2.0 milestone files' — строки фаз уехали в milestones/v2.0-phases/, и выводить счёт стало не из чего. НЕ починено намеренно: правка STATE.md ради зелёного занизила бы счёт закрытой вехи до нуля, потеряв запись 110/110, которую сама STATE.md объясняет как выправленную при закрытии вехи. Решает тот, кто закрывает веху (/gsd-new-milestone или /gsd-health).",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-26T05:45:08.562Z",
    "resolved_at": null
  },
  {
    "id": 10,
    "kind": "unrun-verify",
    "phase": "quick-260826-jql",
    "file": "app/messengers/telegram_user.py",
    "line": null,
    "description": "Боевая проверка отправки не выполнена: объявление с одной картинкой в реальную Telegram-группу и русский текст потери доступа в истории отправок требуют живого сервера (D5, human_judgment)",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-26T14:50:52.666Z",
    "resolved_at": null
  },
  {
    "id": 11,
    "kind": "unrun-verify",
    "phase": "07",
    "file": ".planning/phases/07-obnovlenie-htmx-do-2-0-10-i-blok-konfiguratsii/07-UAT.md",
    "line": null,
    "description": "Ручной обход 07-UAT.md создан, отметки НЕ заполнены: поведенческие половины FOUND-01 и QUAL-05 закрываются глазами на приёмке фазы. Процедура пункта 1 была НЕИСПОЛНИМА как написана (отправляла наблюдать ключ в localStorage, где отгруженный 2.0.10 его не держит) и исправлена планом 07-04: предмет записи перестал быть недостижимым, но запись остаётся ОТКРЫТОЙ — закрывает её человек, прошедший обход",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-27T10:23:15.664Z",
    "resolved_at": null
  },
  {
    "id": 12,
    "kind": "unrun-verify",
    "phase": "09",
    "file": "app/templates/account_groups/includes/group_row.html",
    "line": null,
    "description": "Строка консоли 7.1 (hx-include) после правки плана 09-11 в браузере повторно НЕ наблюдалась — снятие DIV-09-01 утверждается машинным правилом, а не глазом",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-08-31T04:22:01.251Z",
    "resolved_at": "2026-09-02T14:59:39.889Z"
  },
  {
    "id": 13,
    "kind": "deviation",
    "phase": "09",
    "file": "tests/test_pages/test_account_groups.py",
    "line": null,
    "description": "Второе следствие DIV-09-01 остаётся открытым под записью INCLUDE_TARGET_EXCEPTIONS['group-list-sentinel'], назначенная фаза — Фаза 15",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-08-31T04:22:01.682Z",
    "resolved_at": "2026-09-02T14:59:42.909Z"
  },
  {
    "id": 14,
    "kind": "deviation",
    "phase": "09",
    "file": "tests/test_pages/test_admin_panel.py",
    "line": null,
    "description": "DEF-09-01: test_the_overview_error_number_matches_the_users_own_dashboard краснеет в окно 00:00-05:00 из-за расхождения суточного и календарного окон; к правке плана 09-11 не относится",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-31T04:22:02.108Z",
    "resolved_at": null
  },
  {
    "id": 15,
    "kind": "todo",
    "phase": "09",
    "file": ".planning/phases/09-pilot-na-account-groups-skvoznoy-kontrakt-formy/deferred-items.md",
    "line": null,
    "description": "DEF-09-02 — «Отмена» панели подтверждения закрывает панель, но летящий запрос удаления не отменяет; назначенная Фаза 10",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-31T07:43:11.328Z",
    "resolved_at": null
  },
  {
    "id": 16,
    "kind": "deviation",
    "phase": "09",
    "file": ".planning/phases/09-pilot-na-account-groups-skvoznoy-kontrakt-formy/09-UAT.md",
    "line": null,
    "description": "Проверка 6.3 второго круга снята в две части (Slow 3G в полёте, Offline после отказа) — отступление от порядка шагов UAT, оговорка О-1",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-31T07:43:11.798Z",
    "resolved_at": null
  },
  {
    "id": 17,
    "kind": "deviation",
    "phase": "09",
    "file": ".planning/phases/09-pilot-na-account-groups-skvoznoy-kontrakt-formy/09-UAT.md",
    "line": null,
    "description": "Стенд UAT9- не был убран владельцем: сообщено groups=0, измерено groups=32 accounts=2; уборка выполнена исполнителем, оговорка О-4",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-31T07:43:12.216Z",
    "resolved_at": null
  },
  {
    "id": 18,
    "kind": "unrun-verify",
    "phase": "09",
    "file": ".planning/phases/09-pilot-na-account-groups-skvoznoy-kontrakt-formy/09-UAT.md",
    "line": null,
    "description": "Оговорка О-6 четвёртого круга: название последней видимой строки (шаг 4.1.9) владелец дословно НЕ транскрибировал; сверка 4.1.14 проведена и расхождений не дала, но повторяемость шага ограничена — следующий обход не сможет опереться на выписанное имя",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-02T15:03:20.319Z",
    "resolved_at": null
  },
  {
    "id": 19,
    "kind": "unrun-verify",
    "phase": "09",
    "file": ".planning/phases/09-pilot-na-account-groups-skvoznoy-kontrakt-formy/09-UAT.md",
    "line": null,
    "description": "Оговорка О-7 четвёртого круга: у шагов 4.1.11 и 4.1.12 нет литеральных значений (вкладка закрыта до транскрипции) — прямого ответа про прокрутку после удаления и вывода document.documentElement.className в отметке НЕТ, стоит вердикт владельца. Литералы не сочинены. Механизм компенсаторно измерен буквальными выражениями шагом 4.2.6 на более опасной ветке",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-02T15:03:26.333Z",
    "resolved_at": null
  },
  {
    "id": 20,
    "kind": "deviation",
    "phase": "09",
    "file": ".planning/phases/09-pilot-na-account-groups-skvoznoy-kontrakt-formy/09-UAT.md",
    "line": null,
    "description": "Оговорка О-8 четвёртого круга: обход проведён на ПРОДЕ https://broadcaster.all-torgi.ru (аккаунт 53), а не на localhost по букве раздела «Как привести стенд»; посев и уборка шли против БОЕВОЙ базы 192.168.0.9:5432/broadcaster. Поколение дерева подтверждено тремя пробами в консоли; стенд убран и проверен машинно (UAT9- rows: groups=0 accounts=0)",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-02T15:03:33.140Z",
    "resolved_at": null
  }
]
````
