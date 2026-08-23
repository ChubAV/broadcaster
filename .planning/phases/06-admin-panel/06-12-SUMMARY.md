---
phase: 06-admin-panel
plan: 12
subsystem: auth
tags: [jwt, rfc8693, impersonation, fastapi, jinja2, structlog, cookies, tdd]

requires:
  - phase: 06-admin-panel (план 06-02)
    provides: "`_session_cookie_attrs` / `set_session_cookie` — единственное объявление набора атрибутов cookie сессии; возврат из имперсонации ПЕРЕЗАПИСЫВАЕТ cookie через него, а не удаляет её"
  - phase: 06-admin-panel (план 06-06)
    provides: "`get_current_user_id_active` с уже написанной веткой признака действующего лица (до этого плана мёртвой) и стык `get_user_from_cookie` без такой ветки, записанный в deferred-items.md"
  - phase: 06-admin-panel (план 06-11)
    provides: "тот же страничный модуль админки и тот же файл стилей (файловая зависимость)"
provides:
  - "`actor_id` (именованный-только параметр выпуска токена) и claim `act` объектной формы RFC 8693 — ОДИН токен несёт две личности"
  - "`actor_id(payload)` — единственный читатель признака действующего лица на проект; приведение типа живёт внутри `decode_access_token`"
  - "`IMPERSONATION_EXPIRE_MINUTES` (60) и `ACCESS_EXPIRE_MINUTES` (1440) — срок имперсонации отдельной константой"
  - "Обе проверки прав администратора читают ДЕЙСТВУЮЩЕЕ ЛИЦО: `require_admin` возвращает актора, `check_is_admin` демотирует его отсутствие до «актор равен субъекту»"
  - "Закрыт стык плана 06-06: `get_user_from_cookie` получил ветку `act`, и вход администратора под ЗАБЛОКИРОВАННЫМ пользователем работает на страничном пути (D-26)"
  - "`admin_impersonate` (вход) и `stop_impersonation` (возврат) с гардом происхождения и следом в журнале"
  - "Полоса возврата в `base.html` — рисуется на всех 26 страничных маршрутах"
  - "`tests/test_services/test_auth_token.py` (13) и `tests/test_pages/test_impersonation.py` (22) — предмет имперсонации собран целиком"
affects: [06-13 (машинный гейт запретов под чужой личностью), любая будущая правка авторизации, любая правка шелла]

actuals:
  # chars/4 по РЕАЛИЗОВАННОМУ ДИФФУ (127 297 симв. по пяти коммитам плана), а не
  # по итоговому содержимому изменённых файлов: среди тронутых файлов лежат
  # app/static/css/app.css и app/pages/admin.py, у которых этим планом изменены
  # десятки строк из тысяч, и счёт по содержимому мерил бы чужой объём. Метод
  # назван здесь прямо, потому что он отличается от метода сводок 06-02 и 06-06.
  tokens: 31800
  tasks: 3
  commits: 6

tech-stack:
  added: []
  patterns:
    - "Именованный-только параметр как способ расширить общую точку выпуска, не сдвинув ни одного существующего вызова"
    - "Приведение типа второго идентификатора живёт ВНУТРИ единственной точки чтения токена; у признака ровно один читатель-функция"
    - "Второе лицо запроса едет ВМЕСТЕ с субъектом (непишущийся атрибут экземпляра), а не лишним параметром у пятнадцати вызовов проверки прав"
    - "Утверждение о журнале снимается подменой самого регистратора, когда перехват через логирование зависит от порядка файлов в прогоне"

key-files:
  created:
    - tests/test_services/test_auth_token.py
    - tests/test_pages/test_impersonation.py
  modified:
    - app/services/auth_service.py
    - app/dependencies.py
    - app/pages/common.py
    - app/pages/auth.py
    - app/pages/admin.py
    - app/templates/base.html
    - app/templates/admin/user_detail.html
    - app/static/css/app.css
    - tests/test_templates/test_components.py

key-decisions:
  - "Форма значения признака — ОБЪЕКТ `{\"sub\": \"<id>\"}` (RFC 8693), а не скаляр: вложенность записывает цепочку делегирования и оставляет место третьему лицу. Чтение при этом ТЕРПИМО к скаляру — токены такой формы уже собраны вручную планом 06-06, и строгость обесценила бы чужое утверждение молча"
  - "Действующее лицо едет к проверке прав НЕПИШУЩИМСЯ АТРИБУТОМ на объекте субъекта (`impersonated_by`), а не третьим параметром `check_is_admin`: вызовов пятнадцать в шести модулях, и забытый вызов выглядел бы исправным — администратор терял бы права ровно на одной странице"
  - "Атрибут присваивается ВСЕГДА, в том числе пустым значением: объект пользователя живёт в карте тождества сессии, и присвоение «только при имперсонации» оставило бы вчерашнего актора на объекте после возврата"
  - "`require_admin` ВОЗВРАЩАЕТ актора, а не субъекта: обработчики админки пишут `admin.id` в журнал привилегированных операций, и возврат субъекта назвал бы автором действия того, НАД КЕМ оно совершено"
  - "Обработчик возврата живёт в модуле входа, а не в админке: полоса рисуется на всех 26 страницах, и маршрут в админском роутере означал бы, что вернуться можно только оттуда, куда администратор под чужой личностью может и не дойти"
  - "Возврат НЕ спрашивает прав администратора: единственный вход — признак в собственном подписанном токене предъявителя; `require_admin` здесь запер бы в чужой учётной записи ровно того, кого обработчик должен из неё вывести"
  - "Вход администратора ПОД САМИМ СОБОЙ отвергается явно: токен, где действующее лицо совпадает с субъектом, — состояние, которого в продукте не бывает"
  - "У входа под пользователем ЕСТЬ подтверждение, хотя у обоих соседних тумблеров карточки его нет: тумблеры обратимы одним нажатием, а вход переводит ВСЕ последующие действия администратора в чужую учётную запись"
  - "Подпись полосы усекается в ОБРАБОТЧИКЕ по константе `IMPERSONATION_LABEL_CAP`, а не в разметке: величина, обрезанная в шаблоне, обрезалась бы по-разному в каждом месте показа"
  - "Утверждение о журнале снято подменой регистратора, а не `caplog`: перехват записи `app.pages.admin` краснел ТОЛЬКО в полном прогоне, и причина лежит в общей на процесс настройке журналирования — чужой предмет"

patterns-established:
  - "Терпимость чтения к чужой форме объявляется ОДНОСТОРОННЕЙ и называется в коде: выпуск пишет одну форму, чтение принимает две, и это не вторая поддерживаемая форма"
  - "Инвариант, у которого две половины, утверждается ОДНИМ телом теста: разложенные по разным тестам, половины позволяют «починить» одну, не заметив, что вторая перестала что-либо утверждать"
  - "Вспомогательная функция теста УДОСТОВЕРЯЕТСЯ, что предусловие состоялось: отсутствующий маршрут отвечает 404, и без проверки он выглядел бы как исполненное требование (две ложных зелени поймано в этом плане)"

requirements-completed: [ADMIN-06]

coverage:
  - id: D1
    description: "Токен БЕЗ признака действующего лица даёт прежний состав полезной нагрузки; с признаком — объектную форму RFC 8693; существующие позиционные вызовы выпуска не сдвинуты"
    requirement: "ADMIN-06"
    verification:
      - kind: unit
        ref: "tests/test_services/test_auth_token.py#test_a_token_without_act_keeps_the_previous_payload_key_set"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_auth_token.py#test_a_token_with_an_actor_adds_the_claim_and_keeps_the_subject_form"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_auth_token.py#test_the_actor_parameter_is_keyword_only_so_positional_calls_are_untouched"
        status: pass
    human_judgment: false
  - id: D2
    description: "Приведение типа идентификатора действующего лица живёт внутри чтения токена; отсутствие признака читается как отсутствие; испорченный признак не роняет чтение"
    requirement: "ADMIN-06"
    verification:
      - kind: unit
        ref: "tests/test_services/test_auth_token.py#test_the_actor_id_is_coerced_where_the_subject_id_is_coerced"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_auth_token.py#test_reading_a_token_without_act_yields_absence_not_an_empty_value"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_auth_token.py#test_a_corrupted_actor_claim_reads_as_absence_and_never_breaks_the_read"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_a_hand_built_token_with_a_scalar_actor_claim_still_reads"
        status: pass
    human_judgment: false
  - id: D3
    description: "Срок токена имперсонации — отдельная короткая константа (60 минут против 1440), и она доезжает до обработчика входа"
    requirement: "ADMIN-06"
    verification:
      - kind: unit
        ref: "tests/test_services/test_auth_token.py#test_the_impersonation_lifetime_is_a_named_constant_and_markedly_shorter"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_impersonation_token_carries_the_short_lifetime"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_auth_token.py#test_an_expired_impersonation_token_is_refused_like_any_expired_token"
        status: pass
    human_judgment: false
  - id: D4
    description: "Администратор входит под пользователем из его карточки и видит продукт глазами этого пользователя"
    requirement: "ADMIN-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_admin_enters_as_the_user_from_the_card"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_entering_as_a_missing_user_is_refused"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_entering_as_oneself_is_refused_and_issues_no_actor_claim"
        status: pass
    human_judgment: false
  - id: D5
    description: "Админ-доступ СОХРАНЯЕТСЯ под чужой учётной записью и определяется по действующему лицу; при его отсутствии — по субъекту (критерий 3 фазы)"
    requirement: "ADMIN-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_admin_access_survives_under_the_other_identity"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_admin_ness_is_decided_by_the_actor_and_otherwise_by_the_subject"
        status: pass
    human_judgment: false
  - id: D6
    description: "Возврат перезаписывает cookie тем же набором атрибутов, возвращает администратора без потери прав и не заводит второй cookie личности"
    requirement: "ADMIN-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_return_rewrites_the_cookie_with_the_same_attribute_set"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_no_second_identity_cookie_appears"
        status: pass
      - kind: other
        ref: "grep -Ec 'delete_cookie' app/pages/admin.py == 0"
        status: pass
    human_judgment: false
  - id: D7
    description: "Вход под ЗАБЛОКИРОВАННЫМ пользователем разрешён на страничном пути (D-26); без действующего лица блокировка действует, и страничная форма покупки заблокированному закрыта"
    requirement: "ADMIN-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_admin_may_enter_as_a_blocked_user"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_page_purchase_form_stays_closed_to_a_blocked_user"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_blocked_user.py (20 тестов плана 06-06 — зелёные)"
        status: pass
    human_judgment: false
  - id: D8
    description: "Посторонний не входит под кем-либо и не выполняет возврат; межсайтовый запрос отвергается ДО выпуска токена"
    requirement: "ADMIN-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_an_outsider_can_neither_enter_as_anyone_nor_return"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_a_cross_origin_entry_is_refused_before_any_token_is_issued"
        status: pass
    human_judgment: false
  - id: D9
    description: "Вход и возврат оставляют именованные строки журнала с идентификаторами администратора и целевого пользователя (D-24)"
    requirement: "ADMIN-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_both_the_entry_and_the_return_are_journaled_with_both_ids"
        status: pass
    human_judgment: false
  - id: D10
    description: "Полоса возврата видна на КАЖДОЙ странице продукта, называет пользователя, возвращает настоящей формой POST и не стоит шеллу ни одного запроса"
    requirement: "ADMIN-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_return_bar_is_present_in_every_section"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_without_impersonation_no_section_draws_the_bar"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_return_control_is_a_real_post_form"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_bar_costs_the_shell_no_query_of_its_own"
        status: pass
    human_judgment: false
  - id: D11
    description: "Подпись полосы никогда не пуста и не растягивает полосу: пользователь без имени называется адресом, имя произвольной длины усекается по константе"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_a_user_without_a_name_is_named_by_address_never_by_emptiness"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_an_arbitrarily_long_name_does_not_stretch_the_bar"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_bar_names_the_user_the_admin_is_acting_as"
        status: pass
    human_judgment: false
  - id: D12
    description: "Полоса не ломает раскладку шелла ни на одной из 26 страниц и выглядит янтарной предупреждающей плашкой во всю ширину над шеллом"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_bar_does_not_break_the_shell_layout"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py + tests/test_pages/test_responsive_markup.py (246 тестов — зелёные)"
        status: pass
    human_judgment: true
    rationale: "Утверждение о ВИДЕ: тон, доли фона и границы, перенос блока возврата на вторую строку на узком экране и то, что полоса не наезжает на схлопнутую панель навигации на ≤860px. Разметка и правила проверены машинно, но «полоса выглядит предупреждением, а не аварией, и читается на 375px» — суждение глазами, и автоматическим тестом в этом репозитории не выражается."

duration: 205min
completed: 2026-08-23
status: complete
---

# Phase 06 Plan 12: Вход администратора под пользователем и возврат — Summary

**Один подписанный токен несёт две личности (claim `act` формы RFC 8693): администратор входит под пользователем из его карточки, видит продукт его глазами, НЕ теряет админ-доступ, видит полосу возврата на каждой из 26 страниц и возвращается одним нажатием — cookie перезаписывается, а не заводится вторая.**

## Performance

- **Duration:** ~205 min
- **Tasks:** 3 (все — TDD, RED→GREEN)
- **Files modified:** 9 (2 создано, 7 изменено)
- **Tests added:** 35 (13 в `test_auth_token.py`, 22 в `test_impersonation.py`)

## Accomplishments

- **Критерий 3 фазы закрыт по механике.** Администратор входит под пользователем, воспроизводит его проблему и возвращается, не теряя админ-доступ. Админство поднято с СУБЪЕКТА на ДЕЙСТВУЮЩЕЕ ЛИЦО в обеих проверках прав — страничной и JSON-стороны, — и инвариантный тест утверждает обе половины правила в одном теле.
- **Закрыт унаследованный стык плана 06-06.** `get_user_from_cookie` получил ветку `act`: вход администратора под ЗАБЛОКИРОВАННЫМ пользователем работает на страничном пути (D-26) — тот самый случай, ради которого имперсонация и нужна. До этой правки такой администратор был неотличим от невошедшего: молчаливый редирект на `/login` без единого слова о причине.
- **Граница снизу той же правки закреплена впервые.** Закрытость страничной формы покупки для заблокированного была ПОБОЧНЫМ ЭФФЕКТОМ этой же функции и не была закреплена ничем; теперь у неё есть свидетель, и правка ветки `act` не сможет открыть форму молча.
- **Обычный токен не изменился ни одним ключом** — закреплено сравнением МНОЖЕСТВА ключей полезной нагрузки, а не аккуратностью правки (D-21).
- **Полоса возврата поднята из админского блока макета в шелл** и рисуется на всех 26 страничных маршрутах; отсутствие признака означает отсутствие разметки, а не полосу с пустым значением.

## Task Commits

1. **Задача 1: признак действующего лица в единственной точке токена** — `e745674` (test, RED) → `4df8b4e` (feat, GREEN)
2. **Задача 2: вход под пользователем, возврат, админство по действующему лицу** — `8cc70e8` (test, RED) → `17af29d` (feat, GREEN)
3. **Задача 3: полоса возврата в шелле** — `ec5a398` (test, RED) → `526a225` (feat, GREEN)

Рефакторинга ни в одной из трёх задач не потребовалось: реализация с первого прохода была той, которую предписывал план, и «чистить» в ней было нечего.

## Files Created/Modified

- `app/services/auth_service.py` — `ACTOR_CLAIM`, `ACCESS_EXPIRE_MINUTES`, `IMPERSONATION_EXPIRE_MINUTES`; именованный-только `actor_id` у выпуска; приведение типа второго идентификатора внутри чтения; `actor_id(payload)` — единственный читатель признака
- `app/dependencies.py` — `_actor_claim` → `_actor_id` (возвращает целое, читает заголовок наравне с cookie); `require_admin` определяет админство по действующему лицу и возвращает ЕГО
- `app/pages/common.py` — ветка `act` в `get_user_from_cookie` (D-26), `actor_of`, `check_is_admin` по действующему лицу, `impersonation_view` + ключ `impersonation` в контексте шелла, `IMPERSONATOR_ATTR`, `IMPERSONATION_LABEL_CAP`
- `app/pages/auth.py` — `stop_impersonation`: перезапись cookie единственной функцией установки, гард происхождения, `impersonation_stop` в журнале
- `app/pages/admin.py` — `admin_impersonate`: гард происхождения ДО выпуска токена, короткий срок, отказ входу под собой и под несуществующим, `impersonation_start` в журнале
- `app/templates/base.html` — полоса возврата ДО `[data-shell]`; второй импорт компонента (mono) с выписанным основанием
- `app/templates/admin/user_detail.html` — кнопка входа настоящей формой POST + панель подтверждения
- `app/static/css/app.css` — правила полосы (`flex-wrap: wrap`, прижатие возврата вправо) перед правилами шелла; порядок элементов шелла не тронут
- `tests/test_templates/test_components.py` — инвентаризация мест подтверждения: два числа из трёх подняты

## Decisions Made

Вынесены в `key-decisions` frontmatter целиком. Три самых дорогих:

1. **Действующее лицо едет к проверке прав вместе с субъектом, а не лишним параметром.** `check_is_admin(user, settings)` зовут пятнадцать обработчиков в шести модулях. Третий параметр пришлось бы дописать в каждый вызов — а забытый вызов выглядел бы совершенно исправным: администратор терял бы права ровно на одной странице. Поэтому единственная точка чтения токена вешает актора на объект субъекта непишущимся атрибутом, и правило остаётся объявленным ОДИН раз.
2. **`require_admin` возвращает актора.** Обработчики админки пишут `admin.id` в журнал привилегированных операций; верни зависимость субъекта — и журнал называл бы автором действия того, НАД КЕМ оно совершено.
3. **Возврат не спрашивает прав администратора.** Единственный вход — признак в собственном подписанном токене предъявителя. `require_admin` здесь запер бы в чужой учётной записи ровно того, кого обработчик должен из неё вывести.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Инвентаризация мест подтверждения не знала о новом месте**

- **Found during:** Задача 3 (после добавления панели подтверждения входа под пользователем)
- **Issue:** `tests/test_templates/test_components.py::test_modal_site_inventory` — машинный гейт, объявляющий числом импортёров панели подтверждения, различных имён события и мест применения. Новое место (`modal-open-user-imp-`) уронило гейт: 9 имён против объявленных 8.
- **Fix:** Подняты два числа из трёх — `MODAL_EVENT_NAMES` 8→9 и `MODAL_PLACES` 17→18. `MODAL_IMPORTERS` НЕ поднято и это содержательно: карточка пользователя уже собирала панель под подтверждение удаления, и второго импорта того же компонента в тот же файл не появляется. Основание выписано в файле рядом с числами, по форме соседних записей планов 06-05 и 06-07.
- **Verification:** `uv run pytest tests/test_templates -q` — 50 passed
- **Committed in:** `526a225`

**2. [Rule 1 — Bug] Перехват записи журнала зависел от порядка файлов в прогоне**

- **Found during:** Задача 3 (полный прогон `just test`)
- **Issue:** `test_both_the_entry_and_the_return_are_journaled_with_both_ids` в первой редакции снимал запись `caplog`-ом по образцу соседних файлов. Тест зеленел в одиночку и краснел ТОЛЬКО в полном прогоне: запись `app.pages.admin` не доезжала до перехватчика, тогда как запись `app.pages.auth` в том же теле доезжала. Минимальный воспроизводитель найден и назван: `tests/test_admin.py … tests/test_models` + этот файл (516 тестов, ~70 с). Причина лежит в общей на процесс настройке журналирования — `setup_logging` зовётся на КАЖДОЙ сборке приложения и чистит обработчики корневого регистратора, а `tests/test_messengers/conftest.py` переконфигурирует structlog на старте сессии.
- **Fix:** Утверждение снято с САМОГО ВЫЗОВА журнала — подменой регистратора модуля. От порядка файлов не зависит и утверждает ровно то, что требует D-24: имя события и оба идентификатора. Причина замены выписана в docstring теста, чтобы следующий читатель не «вернул как у соседей».
- **Files modified:** `tests/test_pages/test_impersonation.py`
- **Verification:** воспроизводящий набор — 517 passed; `just test` — 2074 passed
- **Committed in:** `526a225`

**3. [Rule 1 — Bug] Две ложных зелени в собственных тестах**

- **Found during:** Задача 2 (первый прогон RED)
- **Issue:** `test_admin_access_survives_under_the_other_identity` и инвариантный тест ЗЕЛЕНЕЛИ на красной фазе: отсутствующий маршрут входа отвечал 404, администратор оставался собой, и оба теста подтверждали обычную админскую сессию, ничего не проверяя.
- **Fix:** Введён `_enter()` — вспомогательная функция, УДОСТОВЕРЯЮЩАЯСЯ, что вход состоялся (302 на `/dashboard` и признак действующего лица в выданном токене). Все утверждения «под чужой личностью» идут через неё.
- **Files modified:** `tests/test_pages/test_impersonation.py`
- **Committed in:** `8cc70e8`

**4. [Rule 3 — Blocking] Расширение состава изменённых файлов на два**

- **Found during:** Задачи 1–3
- **Issue:** План объявлял девять файлов; тронуто одиннадцать.
- **Fix:** `tests/test_templates/test_components.py` — см. отклонение 1 (объявленный реестр, который новое место обязано пополнить). `app/pages/__init__.py` в итоге НЕ тронут: признак имперсонации удалось положить в контекст шелла тем же приёмом, что доступ и счётчики, — раскрытием словаря внутри `get_shell_context`, без правки точки сборки.
- **Impact:** Ни один из пятнадцати вызовов `check_is_admin` в шести продуктовых модулях не тронут — это и было целью выбранной формы передачи актора.

---

**Total deviations:** 4 auto-fixed (2 blocking, 2 bug). Расширений предмета нет: все четыре — либо объявленные реестры, которые правка обязана пополнить, либо собственные тесты плана, ловившие не то, что обещали.

## Issues Encountered

**Предсуществующий отказ `test_image_base_url_comes_from_app_settings` НЕ трогался.** Он краснеет в полном прогоне и зеленеет в одиночку; разбор и два минимальных воспроизводителя записаны в `deferred-items.md` планами 06-03, 06-04 и 06-06. Итог `just test` этого плана: **1 failed, 2074 passed** — единственный отказ и есть этот, унаследованный.

**Полный прогон стоит ~22 минуты.** Задачи 1 и 2 проверялись срезом `tests/test_pages tests/test_routes tests/test_services` (~21 мин каждый), задача 3 — полным `just test` дважды (второй раз после починки перехвата журнала).

## Порядок выката — записан здесь, как требовал план

⚠️ **ВХОД ПОД ПОЛЬЗОВАТЕЛЕМ НА БОЙ НЕ ВЫКАТЫВАЕТСЯ ДО ИСПОЛНЕНИЯ ПЛАНА 06-13.** Этот план поставляет МЕХАНИКУ входа, возврата и её видимость; машинный гейт запретов под чужой личностью (D-22, D-23 — оплата и весь биллинг, смена пароля и email, удаление учётной записи, отправка и повтор рассылки) закрывается планом 06-13. Угроза `T-06-IMP7` (необратимые и денежные действия под чужой личностью) остаётся ОТКРЫТОЙ до него: сегодня администратор под чужой личностью технически может отправить рассылку в чужие группы от имени пользователя, и отменить это нельзя.

Порядок не «желателен», а обязателен: кнопка входа уже стоит в карточке пользователя, и выкат этой ревизии без 06-13 делает её доступной.

## Known Stubs

Заглушек нет. Все поверхности, заведённые планом, читают живые данные: подпись полосы — из уже загруженного субъекта, действующее лицо — из подписанного токена, админство — из строки актора.

## Threat Flags

Новых поверхностей вне реестра угроз плана не заведено. Диспозиции реестра исполнены так:

| Threat ID | Disposition | Чем закрыт |
|-----------|-------------|------------|
| T-06-IMP | mitigate | Отдельный короткий срок (60 против 1440) + полоса на каждой из 26 страниц; обе меры закреплены тестами |
| T-06-IMP2 | mitigate | `is_same_origin` ДО выпуска токена + `require_admin`; отказ постороннему и межсайтовому закреплён |
| T-06-IMP3 | mitigate | `impersonation_start` / `impersonation_stop` с обоими ид. ⚠️ ПРИНЯТЫЙ РИСК ОСТАЁТСЯ: источник логов опционален (D-27, D-28), и при неподнятом мониторинге след живёт только в stdout контейнера |
| T-06-IMP4 | mitigate | Признак едет ВНУТРИ подписанного токена; второй носитель личности не заведён (закреплено сравнением множеств имён cookie) |
| T-06-IMP5 | mitigate | Обе проверки читают действующее лицо; инвариант утверждает обе половины правила одним телом |
| T-06-IMP6 | mitigate | Возврат ходит через единственную функцию установки; `grep -Ec 'delete_cookie' app/pages/admin.py == 0` |
| T-06-IMP7 | **ОТКРЫТА** | Закрывается планом 06-13. См. раздел «Порядок выката» выше |

## Next Phase Readiness

- **План 06-13 может начинаться:** признак `act` выпускается и читается, `actor_id(payload)` — готовая точка, по которой гейт запретов узнаёт «мы под чужой личностью»; форма отказа словами объявлена в UI-контракте (S9).
- **Стык из `deferred-items.md` закрыт** — ветка `act` в `get_user_from_cookie` написана, и обе стороны правила (разрешено с актором, запрещено без него) закреплены тестами.
- **Предупреждение будущим правкам авторизации:** админство теперь свойство ДЕЙСТВУЮЩЕГО ЛИЦА. Инвариантный тест краснеет в тот день, когда правка вернёт чтение прав по субъекту, — это не перестраховка, а зафиксированный урок D-20.

---
*Phase: 06-admin-panel*
*Completed: 2026-08-23*

## Self-Check: PASSED

- Созданные файлы на месте: `.planning/phases/06-admin-panel/06-12-SUMMARY.md`, `tests/test_services/test_auth_token.py`, `tests/test_pages/test_impersonation.py`
- Все шесть коммитов задач присутствуют в истории ветки: `e745674`, `4df8b4e`, `8cc70e8`, `17af29d`, `ec5a398`, `526a225`
- `just test`: 1 failed, 2074 passed — единственный отказ предсуществующий (`test_image_base_url_comes_from_app_settings`, записан в `deferred-items.md` тремя планами)
- `STATE.md` и `ROADMAP.md` НЕ трогались: их правит оркестратор после завершения волны
