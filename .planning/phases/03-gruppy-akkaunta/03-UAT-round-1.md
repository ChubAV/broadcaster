---
status: complete
phase: 03-gruppy-akkaunta
source: [03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md, 03-04-SUMMARY.md, 03-05-SUMMARY.md, 03-06-SUMMARY.md, 03-07-SUMMARY.md, 03-08-SUMMARY.md]
started: 2026-08-13T06:29:15Z
updated: 2026-08-13T06:53:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Холодный старт с нуля
expected: |
  Остановить приложение и воркеры. Поднять всё с нуля на чистом окружении: `just upgrade` (миграции 0014 и 0015 применяются без ошибок), затем `just run` и `just celery`.
  Ожидается: приложение поднимается без исключений, обе ревизии проходят, вход на /accounts отдаёт живые данные.
  Отдельно про 0015: ревизия схлопывает дубли групп И переписывает ссылки в schedules.group_ids. Если в базе были дубли — после апгрейда расписания продолжают ссылаться на выжившую группу, ни одно расписание не потеряло адресата.
result: pass

### 2. Экран групп аккаунта — вид и адаптивность (320 / 860 / 1280)
expected: |
  Открыть /accounts/{id}/groups аккаунта с группами на трёх ширинах.
  Ожидается: строки выглядят карточками, а не таблицей; шапка переносится, не ломаясь; горизонтальной прокрутки нет ни на одной ширине; каждое значение в строке подписано.
result: pass
coverage_id: 03-01/D8, 03-05/D11

### 3. Шапка, плашка синка и блок статуса (320 / 860 / 1280)
expected: |
  На том же экране: запустить «Синхронизировать всё», дождаться сводки, посмотреть шапку и плашку на трёх ширинах.
  Ожидается: два действия в шапке переносятся на свою строку и не наезжают друг на друга; длинная строка ошибки переносится ВНУТРИ плашки, не растягивая страницу; горизонтальной прокрутки нет.
  Две страховочные проверки на 320px: имя аккаунта в 60 символов и строка ошибки воркера в 300 символов — обе должны переноситься, а не обрезаться и не распирать экран.
result: pass
coverage_id: 03-06/D9

### 4. Пометка выключенной группы в карточке расписания (320 / 400)
expected: |
  Выключить группу, которая уже выбрана в расписании объявления, и открыть карточку расписания в редакторе объявления на 320 и 400px.
  Ожидается: пометка «отключена» окрашена цветом --warn; строка не переполняется; длинное имя группы не обрезается на полуслове.
result: pass
coverage_id: 03-03/D7

### 5. Живая синхронизация на реальном аккаунте — все три пути
expected: |
  Запустить синхронизацию на реальном подключённом аккаунте: Telegram (синхронный путь), затем WhatsApp и/или MAX (фоновые пути через воркер).
  Ожидается: во ВСЕХ трёх путях после завершения на экране появляются время последнего синка и сводка результата; переименованная в мессенджере группа приезжает с новым именем; исчезнувшая группа получает пометку «не найдена»; после синка вы остаётесь на /accounts/{id}/groups того же аккаунта.
  Если синк падает (мессенджер недоступен) — на аккаунте остаётся текст ошибки и следующий шаг, а не пустота и не 500-я.
result: pass

### 6. Сообщение об ошибке не показывает внутренности
expected: |
  Вызвать сбой синхронизации (например, отключив мессенджер/мост) и посмотреть плашку ошибки на экране групп аккаунта.
  Ожидается: пользователю показан понятный текст и следующий шаг. В плашке НЕТ SQL, имён таблиц, параметров запроса и трейсбека — это правилось в этом ревью (WR-02), поэтому проверяется отдельно.
result: pass

### 7. Пять критериев успеха фазы на живом приложении
expected: |
  Пройти пять критериев успеха фазы 3 вручную на работающем приложении, включая ширину 320px:
  1. Группы управляются с экрана мессенджер-аккаунта, отдельного раздела «Группы» в меню нет.
  2. Выключенная группа не получает рассылок, включение немедленно их возобновляет.
  3. Группа удаляется с подтверждением и уходит из расписаний.
  4. Повторная синхронизация запускается с экрана и показывает результат.
  5. Старые ссылки на /groups ведут на экран аккаунтов.
result: pass
coverage_id: 03-08/D23

### 8. Пользователь открывает /accounts/{id}/groups своего аккаунта и видит только группы этого аккаунта (GRP-04, D-02)
expected: Пользователь открывает /accounts/{id}/groups своего аккаунта и видит только группы этого аккаунта (GRP-04, D-02)
result: pass
source: automated
coverage_id: 03-01/D1
verified_by: tests/test_pages/test_account_groups.py#test_page_shows_groups_of_this_account | tests/test_pages/test_account_groups.py#test_page_hides_groups_of_another_account_of_the_same_user

### 9. Чужой аккаунт и чужая группа недостижимы: страница не отдаёт данных, toggle не меняет состояния (T-03-01, T-03-02)
expected: Чужой аккаунт и чужая группа недостижимы: страница не отдаёт данных, toggle не меняет состояния (T-03-01, T-03-02)
result: pass
source: automated
coverage_id: 03-01/D2
verified_by: tests/test_pages/test_account_groups.py#test_page_of_a_foreign_account_leaks_nothing | tests/test_pages/test_account_groups.py#test_toggle_leaves_a_foreign_group_alone | tests/test_pages/test_account_groups.py#test_toggle_does_not_trust_the_account_id_from_the_url

### 10. Тумблер переключает группу одним действием без подтверждения, обратимо, ровно одну группу, не трогая состав расписаний (GRP-05, D-05, D-08)
expected: Тумблер переключает группу одним действием без подтверждения, обратимо, ровно одну группу, не трогая состав расписаний (GRP-05, D-05, D-08)
result: pass
source: automated
coverage_id: 03-01/D3
verified_by: tests/test_pages/test_account_groups.py#test_toggle_inverts_is_active_and_redirects | tests/test_pages/test_account_groups.py#test_double_toggle_returns_the_group_to_its_initial_state | tests/test_pages/test_account_groups.py#test_toggle_touches_exactly_one_group | tests/test_pages/test_account_groups.py#test_toggle_does_not_edit_the_schedules

### 11. Выключенная группа не получает задач отправки при диспетчеризации на всех трёх каналах; включение немедленно возобновляет рассылку (D-05)
expected: Выключенная группа не получает задач отправки при диспетчеризации на всех трёх каналах; включение немедленно возобновляет рассылку (D-05)
result: pass
source: automated
coverage_id: 03-01/D4
verified_by: tests/test_application/test_collect_due_inactive_group.py#test_only_the_active_group_of_a_schedule_gets_a_task | tests/test_application/test_collect_due_inactive_group.py#test_inactive_group_produces_no_task_for_any_channel | tests/test_application/test_collect_due_inactive_group.py#test_enabling_the_group_resumes_dispatch

### 12. Тихий пропуск: записи в SendLog не создаётся, расписание продолжает двигать next_run_at (D-06)
expected: Тихий пропуск: записи в SendLog не создаётся, расписание продолжает двигать next_run_at (D-06)
result: pass
source: automated
coverage_id: 03-01/D5
verified_by: tests/test_application/test_collect_due_inactive_group.py#test_skipping_writes_nothing_to_the_send_log | tests/test_application/test_collect_due_inactive_group.py#test_next_run_at_moves_forward_when_every_group_is_off

### 13. Экран достижим кликом с /accounts — вход «Настроить группы» во всех трёх копиях разметки строки и во всех ветках статуса (UI-SPEC E8)
expected: Экран достижим кликом с /accounts — вход «Настроить группы» во всех трёх копиях разметки строки и во всех ветках статуса (UI-SPEC E8)
result: pass
source: automated
coverage_id: 03-01/D6
verified_by: tests/test_pages/test_account_groups.py#test_accounts_screen_links_to_the_account_groups | grep -c 'accounts/.*groups' app/templates/accounts/list.html → 3

### 14. Базовый путь без JS: тумблер остаётся настоящей POST-формой с перехватом на самой форме (D-09)
expected: Базовый путь без JS: тумблер остаётся настоящей POST-формой с перехватом на самой форме (D-09)
result: pass
source: automated
coverage_id: 03-01/D7
verified_by: tests/test_pages/test_account_groups.py#test_toggle_is_a_real_post_form

### 15. Выключенная группа, уже выбранная в расписании объявления, остаётся видна в карточке расписания
expected: Выключенная группа, уже выбранная в расписании объявления, остаётся видна в карточке расписания
result: pass
source: automated
coverage_id: 03-03/D1
verified_by: tests/test_pages/test_editor_schedules.py#test_disabled_group_chosen_in_the_schedule_stays_visible | tests/test_pages/test_editor_schedules.py#test_active_group_is_present_regardless_of_schedules

### 16. Невыбранная выключенная группа в список выбора не попадает — список не захламляется
expected: Невыбранная выключенная группа в список выбора не попадает — список не захламляется
result: pass
source: automated
coverage_id: 03-03/D2
verified_by: tests/test_pages/test_editor_schedules.py#test_disabled_group_not_chosen_is_absent_from_the_picker | tests/test_pages/test_editor_schedules.py#test_disabled_group_chosen_in_another_ad_is_absent_here

### 17. Выборка редактора остаётся скоупнутой по владельцу: чужая группа не попадает в карточку ни в одной ветке (T-03-11)
expected: Выборка редактора остаётся скоупнутой по владельцу: чужая группа не попадает в карточку ни в одной ветке (T-03-11)
result: pass
source: automated
coverage_id: 03-03/D3
verified_by: tests/test_pages/test_editor_schedules.py#test_group_of_another_user_never_reaches_the_editor

### 18. Пометка «отключена» с пояснением стоит ровно на строке выключенной выбранной группы
expected: Пометка «отключена» с пояснением стоит ровно на строке выключенной выбранной группы
result: pass
source: automated
coverage_id: 03-03/D4
verified_by: tests/test_pages/test_editor_schedules.py#test_disabled_chosen_row_is_marked_as_off | tests/test_pages/test_editor_schedules.py#test_editor_without_disabled_selections_renders_the_same_group_set

### 19. Флажок выключенной выбранной группы работоспособен: выбор снимается и снятие доезжает до хранилища
expected: Флажок выключенной выбранной группы работоспособен: выбор снимается и снятие доезжает до хранилища
result: pass
source: automated
coverage_id: 03-03/D5
verified_by: tests/test_pages/test_editor_schedules.py#test_disabled_chosen_checkbox_stays_operable

### 20. Подпись «выбрано N из M» согласована с видимым списком в присутствии выключенных строк
expected: Подпись «выбрано N из M» согласована с видимым списком в присутствии выключенных строк
result: pass
source: automated
coverage_id: 03-03/D6
verified_by: tests/test_pages/test_editor_schedules.py#test_group_counter_agrees_with_the_rendered_rows

### 21. Экран выдерживает сотни групп: 30 строк на страницу, сентинел подтягивает следующие (D-04)
expected: Экран выдерживает сотни групп: 30 строк на страницу, сентинел подтягивает следующие (D-04)
result: pass
source: automated
coverage_id: 03-05/D1
verified_by: tests/test_pages/test_account_groups.py#test_page_shows_thirty_rows_and_a_sentinel | tests/test_pages/test_account_groups.py#test_partial_returns_the_rest_and_drops_the_sentinel

### 22. Поиск сужает список и переживает подгрузку следующей страницы (D-03)
expected: Поиск сужает список и переживает подгрузку следующей страницы (D-03)
result: pass
source: automated
coverage_id: 03-05/D2
verified_by: tests/test_pages/test_account_groups.py#test_search_narrows_the_page | tests/test_pages/test_account_groups.py#test_sentinel_carries_the_search_urlencoded | tests/test_pages/test_account_groups.py#test_partial_keeps_the_search_on_the_second_page

### 23. Числа линейки считаются по всей таблице аккаунта, а не по загруженной странице; порция прокрутки линейку не приносит (D-04)
expected: Числа линейки считаются по всей таблице аккаунта, а не по загруженной странице; порция прокрутки линейку не приносит (D-04)
result: pass
source: automated
coverage_id: 03-05/D3
verified_by: tests/test_pages/test_account_groups.py#test_counter_line_counts_the_whole_table | tests/test_pages/test_account_groups.py#test_partial_carries_no_counter_line | tests/test_pages/test_account_groups.py#test_counter_line_plurals

### 24. Чужой аккаунт недостижим через паршал; негодные параметры постраничной загрузки отвергаются (T-03-19, T-03-22)
expected: Чужой аккаунт недостижим через паршал; негодные параметры постраничной загрузки отвергаются (T-03-19, T-03-22)
result: pass
source: automated
coverage_id: 03-05/D4
verified_by: tests/test_pages/test_account_groups.py#test_partial_of_a_foreign_account_leaks_nothing | tests/test_pages/test_account_groups.py#test_partial_rejects_bad_pagination_params | tests/test_pages/test_account_groups.py#test_partial_without_session_goes_to_login

### 25. Группа удаляется с подтверждением и уходит из расписаний владельца; соседние идентификаторы остаются (GRP-06)
expected: Группа удаляется с подтверждением и уходит из расписаний владельца; соседние идентификаторы остаются (GRP-06)
result: pass
source: automated
coverage_id: 03-05/D5
verified_by: tests/test_pages/test_account_groups.py#test_delete_removes_the_group_and_redirects | tests/test_pages/test_account_groups.py#test_delete_cleans_the_group_out_of_schedules | tests/test_pages/test_account_groups.py#test_delete_keeps_the_neighbour_ids_in_the_same_schedule

### 26. Удаление недостижимо для чужой группы и для своей группы через чужой для неё аккаунт; повтор безвреден (T-03-20)
expected: Удаление недостижимо для чужой группы и для своей группы через чужой для неё аккаунт; повтор безвреден (T-03-20)
result: pass
source: automated
coverage_id: 03-05/D6
verified_by: tests/test_pages/test_account_groups.py#test_delete_leaves_a_foreign_group_alone | tests/test_pages/test_account_groups.py#test_delete_does_not_trust_the_account_id_from_the_url | tests/test_pages/test_account_groups.py#test_repeated_delete_is_harmless

### 27. Панель подтверждения одна на группу, лежит вне строки, называет оба следствия; форма-триггер работает без Alpine (D-09, D-10)
expected: Панель подтверждения одна на группу, лежит вне строки, называет оба следствия; форма-триггер работает без Alpine (D-09, D-10)
result: pass
source: automated
coverage_id: 03-05/D7
verified_by: tests/test_pages/test_account_groups.py#test_confirm_panel_names_the_group_and_both_consequences | tests/test_pages/test_account_groups.py#test_confirm_panel_lives_outside_the_row | tests/test_pages/test_account_groups.py#test_delete_trigger_is_a_real_post_form | tests/test_templates/test_components.py#test_every_row_delete_site_keeps_a_real_form (13 мест)

### 28. Шапка аккаунта честна во всех ветках: нет синка, синк идёт, синк был N назад (UI-SPEC E1)
expected: Шапка аккаунта честна во всех ветках: нет синка, синк идёт, синк был N назад (UI-SPEC E1)
result: pass
source: automated
coverage_id: 03-05/D8
verified_by: tests/test_pages/test_account_groups.py#test_header_says_the_sync_never_ran | tests/test_pages/test_account_groups.py#test_header_shows_the_relative_time_of_the_last_sync | tests/test_pages/test_account_groups.py#test_header_says_the_sync_is_in_flight | tests/test_pages/test_account_groups.py#test_header_never_renders_the_account_credentials

### 29. Три пустых состояния различимы по копирайтингу; при нуле групп линейка не рендерится (GRP-04 empty, E3 empty)
expected: Три пустых состояния различимы по копирайтингу; при нуле групп линейка не рендерится (GRP-04 empty, E3 empty)
result: pass
source: automated
coverage_id: 03-05/D9
verified_by: tests/test_pages/test_account_groups.py#test_empty_state_before_the_first_sync | tests/test_pages/test_account_groups.py#test_empty_state_after_all_groups_were_deleted | tests/test_pages/test_account_groups.py#test_empty_state_when_the_search_matched_nothing | tests/test_pages/test_account_groups.py#test_zero_groups_render_no_counter_line

### 30. Подпись «в N расписаниях» считает только расписания владельца (D-08)
expected: Подпись «в N расписаниях» считает только расписания владельца (D-08)
result: pass
source: automated
coverage_id: 03-05/D10
verified_by: tests/test_pages/test_account_groups.py#test_schedule_count_ignores_foreign_schedules | tests/test_pages/test_account_groups.py#test_row_without_schedules_says_so

### 31. Пользователь запускает повторную синхронизацию кнопкой «Синхронизировать всё», не покидая экрана (GRP-07, D-09)
expected: Пользователь запускает повторную синхронизацию кнопкой «Синхронизировать всё», не покидая экрана (GRP-07, D-09)
result: pass
source: automated
coverage_id: 03-06/D1
verified_by: tests/test_pages/test_account_groups.py#test_header_carries_the_sync_form | tests/test_pages/test_account_groups.py#test_sync_action_says_it_is_in_flight

### 32. Сводка синка показывает найдено, новых и обновлено имён; «не найдено N» появляется только при значении больше нуля (D-09, E2 populated)
expected: Сводка синка показывает найдено, новых и обновлено имён; «не найдено N» появляется только при значении больше нуля (D-09, E2 populated)
result: pass
source: automated
coverage_id: 03-06/D2
verified_by: tests/test_pages/test_account_groups.py#test_success_plashka_prints_all_three_counters | tests/test_pages/test_account_groups.py#test_success_plashka_omits_the_missing_segment_when_zero | tests/test_pages/test_account_groups.py#test_success_plashka_shows_the_missing_segment_when_nonzero | tests/test_pages/test_account_groups.py#test_plashka_renders_exactly_once

### 33. Провал синхронизации показывает текст ошибки И следующий шаг вместо сводки; текст внешней системы экранируется (D-09, T-03-27, E2 error)
expected: Провал синхронизации показывает текст ошибки И следующий шаг вместо сводки; текст внешней системы экранируется (D-09, T-03-27, E2 error)
result: pass
source: automated
coverage_id: 03-06/D3
verified_by: tests/test_pages/test_account_groups.py#test_error_plashka_names_the_error_and_the_next_step | tests/test_pages/test_account_groups.py#test_error_text_from_the_worker_is_escaped | tests/test_pages/test_account_groups.py#test_corrupt_stored_result_renders_no_plashka (5 видов мусора)

### 34. Результат последнего синка виден при перезаходе — читается из аккаунта, а не из памяти запроса (D-09)
expected: Результат последнего синка виден при перезаходе — читается из аккаунта, а не из памяти запроса (D-09)
result: pass
source: automated
coverage_id: 03-06/D4
verified_by: tests/test_pages/test_account_groups.py#test_stored_result_survives_a_revisit | tests/test_pages/test_account_groups.py#test_never_synced_account_renders_no_plashka | tests/test_pages/test_account_groups.py#test_plashka_of_a_running_sync_keeps_the_previous_summary

### 35. Фоновый синк WA и MAX добирается САМООСТАНАВЛИВАЮЩИМСЯ опросом: атрибуты присутствуют только в ветке выполнения и исчезают вместе с ней (D-09, T-03-26)
expected: Фоновый синк WA и MAX добирается САМООСТАНАВЛИВАЮЩИМСЯ опросом: атрибуты присутствуют только в ветке выполнения и исчезают вместе с ней (D-09, T-03-26)
result: pass
source: automated
coverage_id: 03-06/D5
verified_by: tests/test_pages/test_htmx_preserved.py#test_account_groups_polling_continues_while_syncing | tests/test_pages/test_htmx_preserved.py#test_account_groups_polling_stops | tests/test_pages/test_htmx_preserved.py#test_account_groups_page_polls_only_while_syncing | tests/test_pages/test_account_groups.py#test_page_polls_while_the_sync_is_running | tests/test_pages/test_account_groups.py#test_page_declares_no_poll_outside_the_running_state (2 статуса) | tests/test_pages/test_account_groups.py#test_status_endpoint_stops_the_poll_when_the_sync_ends (2 статуса) | tests/test_pages/test_account_groups.py#test_polled_block_is_declared_exactly_once (объявление в исходнике одно)

### 36. Вход статуса проверяет аутентификацию и владение В СЕБЕ: чужой аккаунт и запрос без сессии разметки не получают (T-03-25)
expected: Вход статуса проверяет аутентификацию и владение В СЕБЕ: чужой аккаунт и запрос без сессии разметки не получают (T-03-25)
result: pass
source: automated
coverage_id: 03-06/D6
verified_by: tests/test_pages/test_account_groups.py#test_status_endpoint_of_a_foreign_account_leaks_nothing | tests/test_pages/test_account_groups.py#test_status_endpoint_without_session_leaks_nothing | tests/test_pages/test_account_groups.py#test_status_endpoint_accepts_the_layout_param

### 37. Плашка результата и панели подтверждения живут ВНЕ подменяемого опросом элемента (Pitfall 8, T-11-04)
expected: Плашка результата и панели подтверждения живут ВНЕ подменяемого опросом элемента (Pitfall 8, T-11-04)
result: pass
source: automated
coverage_id: 03-06/D7
verified_by: tests/test_pages/test_account_groups.py#test_confirm_panel_never_lives_inside_the_polled_block | tests/test_pages/test_account_groups.py#test_result_plashka_never_lives_inside_the_polled_block

### 38. Кнопки повторной синхронизации ОТДЕЛЬНОЙ группы на экране нет — протокола синхронизации одной группы у воркеров не существует (D-12)
expected: Кнопки повторной синхронизации ОТДЕЛЬНОЙ группы на экране нет — протокола синхронизации одной группы у воркеров не существует (D-12)
result: pass
source: automated
coverage_id: 03-06/D8
verified_by: tests/test_pages/test_account_groups.py#test_no_per_group_sync_action_on_the_screen

### 39. GRP-08 снято во всех местах, где документы фазы его обещали; прослеживаемость сохранена (D-13)
expected: GRP-08 снято во всех местах, где документы фазы его обещали; прослеживаемость сохранена (D-13)
result: pass
source: automated
coverage_id: 03-07/D13
verified_by: grep -qE '^\\*\\*Requirements\\*\\*: GRP-04, GRP-05, GRP-06, GRP-07$' .planning/ROADMAP.md | grep -qF '| GRP-08 | Phase 3 | Out of scope v2.0 (D-13, 2026-08-11) |' .planning/REQUIREMENTS.md | ! awk '/^### Аккаунты и группы/,/^### Дашборд/' .planning/REQUIREMENTS.md | grep -q 'GRP-08'

### 40. Вход ручного создания группы не существует; дыра проверки владения аккаунтом закрыта удалением (D-14, T-03-29)
expected: Вход ручного создания группы не существует; дыра проверки владения аккаунтом закрыта удалением (D-14, T-03-29)
result: pass
source: automated
coverage_id: 03-07/D14
verified_by: test ! -f app/routes/groups.py; grep -c 'routes.groups' app/main.py → 0 | grep -rc '/api/groups' app/ tests/ | grep -v ':0' | wc -l → 0 | app.main.create_app() — среди маршрутов нет ни одного /api/groups

### 41. Тестовый посев групп не зависит от прикладных маршрутов; суита зелена и до, и после удаления входа
expected: Тестовый посев групп не зависит от прикладных маршрутов; суита зелена и до, и после удаления входа
result: pass
source: automated
coverage_id: 03-07/D15
verified_by: uv run pytest tests/ -q ДО удаления → 1055 passed, 0 failed | uv run pytest tests/ -q ПОСЛЕ удаления → 1048 passed, 0 failed

### 42. Раздел снесён целиком: страниц, паршалов, массовых операций и фильтров старого раздела в приложении не осталось (D-01)
expected: Раздел снесён целиком: страниц, паршалов, массовых операций и фильтров старого раздела в приложении не осталось (D-01)
result: pass
source: automated
coverage_id: 03-08/D16
verified_by: app/templates/groups/ — каталога нет; app/pages/groups.py — ноль обработчиков POST | tests/test_pages/test_shell.py#test_retired_groups_section_accepts_no_post

### 43. Пункт «Группы» отсутствует в боковом меню и в нижних табах на КАЖДОЙ странице (D-01, UI-SPEC E8 error)
expected: Пункт «Группы» отсутствует в боковом меню и в нижних табах на КАЖДОЙ странице (D-01, UI-SPEC E8 error)
result: pass
source: automated
coverage_id: 03-08/D17
verified_by: tests/test_pages/test_shell.py#test_nav_has_no_groups_item (11 адресов шелла)

### 44. Старый адрес и любая старая глубокая ссылка отвечают перенаправлением на экран аккаунтов (T-03-33, UI-SPEC E8 loading/error)
expected: Старый адрес и любая старая глубокая ссылка отвечают перенаправлением на экран аккаунтов (T-03-33, UI-SPEC E8 loading/error)
result: pass
source: automated
coverage_id: 03-08/D18
verified_by: tests/test_pages/test_shell.py#test_retired_groups_routes_redirect_to_accounts (4 адреса)

### 45. Общие параметризованные проверки адаптива, подгрузки и состава шелла знают новый экран вместо снесённого раздела
expected: Общие параметризованные проверки адаптива, подгрузки и состава шелла знают новый экран вместо снесённого раздела
result: pass
source: automated
coverage_id: 03-08/D19
verified_by: tests/test_pages/test_responsive_markup.py#test_list_page_no_utility_classes[account_groups], #test_account_groups_list_is_card_based, #test_account_groups_filters_block_collapsible, #test_account_groups_row_names_each_value | tests/test_pages/test_htmx_preserved.py#test_infinite_scroll_chain[account_groups], #test_infinite_scroll_keeps_filters[account_groups-search=Chat], #test_partial_without_layout_param_ok[account_groups] | tests/test_pages/test_shell.py#test_account_groups_page_gets_the_full_shell_treatment (шелл + партиал)

### 46. Поведенческие утверждения снесённого раздела — владение при переключении и чистка расписаний при удалении — живут на новом экране (T-03-34)
expected: Поведенческие утверждения снесённого раздела — владение при переключении и чистка расписаний при удалении — живут на новом экране (T-03-34)
result: pass
source: automated
coverage_id: 03-08/D20
verified_by: tests/test_pages/test_account_groups.py#test_toggle_leaves_a_foreign_group_alone, #test_toggle_does_not_trust_the_account_id_from_the_url | tests/test_pages/test_account_groups.py#test_delete_cleans_the_group_out_of_schedules, #test_delete_keeps_the_neighbour_ids_in_the_same_schedule

### 47. Стили снесённого раздела не остались сиротами в единственной таблице стилей
expected: Стили снесённого раздела не остались сиротами в единственной таблице стилей
result: pass
source: automated
coverage_id: 03-08/D21
verified_by: Разность корпусов потребителей: 0 из 234 селекторов app.css осиротело; grep -c 'groups-bulk' app.css → 0

### 48. Полная суита зелена: снос не оставил ни одного висящего утверждения
expected: Полная суита зелена: снос не оставил ни одного висящего утверждения
result: pass
source: automated
coverage_id: 03-08/D22
verified_by: uv run pytest tests/ -q → 1049 passed, 0 failed

## Summary

total: 48
passed: 48
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
