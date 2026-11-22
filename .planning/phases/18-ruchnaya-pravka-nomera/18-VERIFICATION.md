---
phase: 18-ruchnaya-pravka-nomera
verified: 2026-11-22T13:00:00Z
status: passed
score: 9/15 must-haves verified
covered_files:
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-01-PLAN.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-01-SUMMARY.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-02-PLAN.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-02-SUMMARY.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-03-PLAN.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-03-SUMMARY.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-04-PLAN.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-04-SUMMARY.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-05-PLAN.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-05-SUMMARY.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-06-PLAN.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-06-SUMMARY.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-07-PLAN.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-07-SUMMARY.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-08-PLAN.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-08-SUMMARY.md"
  - "app/application/accounts/dto.py"
  - "app/application/accounts/labels.py"
  - "app/application/accounts/use_cases.py"
  - "app/pages/account_groups.py"
  - "app/pages/accounts.py"
  - "app/pages/htmx.py"
  - "app/pages/notices.py"
  - "app/services/account_label.py"
  - "app/static/css/app.css"
  - "app/templates/account_groups/includes/phone_form.html"
  - "app/templates/account_groups/list.html"
  - "app/templates/account_groups/partials/phone_error_response.html"
  - "app/templates/account_groups/partials/phone_response.html"
  - "app/templates/accounts/list.html"
  - "app/templates/accounts/partial_cards.html"
  - "app/templates/accounts/partials/sync_status_card.html"
  - "app/templates/base.html"
  - "app/templates/components/account_label.html"
  - "tests/account_label_support.py"
  - "tests/test_application/test_account_label_rows.py"
  - "tests/test_pages/test_account_groups.py"
  - "tests/test_pages/test_account_label_accounts.py"
  - "tests/test_pages/test_account_label_groups.py"
  - "tests/test_pages/test_account_label_sweep.py"
  - "tests/test_pages/test_account_phone_form.py"
  - "tests/test_pages/test_account_phone_links.py"
  - "tests/test_pages/test_htmx_gates.py"
  - "tests/test_pages/test_htmx_post_pairs.py"
  - "tests/test_pages/test_htmx_validation_sink.py"
  - "tests/test_pages/test_hx_location_destinations.py"
  - "tests/test_pages/test_identifier_bounds.py"
  - "tests/test_pages/test_impersonation.py"
  - "tests/test_pages/test_impersonation_gate.py"
  - "tests/test_pages/test_notices_registry.py"
  - "tests/test_pages/test_origin_guard_on_destructive_routes.py"
  - "tests/test_pages/test_responsive_markup.py"
  - "tests/test_pages/test_shell.py"
  - "tests/test_services/test_account_label.py"
  - "tests/test_templates/test_form_inventory.py"
  - "tests/test_templates/test_htmx_markup_gates.py"
covered_digest: "v4:sha256:37fff9a2f81cb97ac2521f3a1219287c7c8f0d79f83dc3c5fdaa5e9ed47fccc1"
behavior_unverified: 6
overrides_applied: 0
prohibitions_flagged: 12
re_verification:
  previous_status: human_needed
  previous_score: 5/5
  previous_round_record: "Раунд 2026-11-21 (первичная верификация, d197f956): human_needed, 5/5 истин критериев ROADMAP верифицировано, 0 присутствует-без-проверки, 0 блокеров. Подтверждено: маршрут account_phone_save, форма, пометка «указан вручную» (17 мест макроса), 9 ссылок /groups#phone, 422 с эхом, очистка (KEPT -> WRITTEN), имперсонация с причиной в ALLOWED_ROUTES, числа гейтов 50/50/26/38/193; выборки 98 и 1248 passed, полный прогон 6035 passed, 2 skipped. Шесть пунктов human_verification (htmx-подмена, очистка с JS, 422 без плашки, якорь #phone, автозаполнение, раскладка 320/375), 12 запретов judgment-уровня flagged-unverified. Открытые находки ревью WR-01, WR-02, WR-03, IN-01..IN-03. Затем обход владельца (18-UAT.md): 5 pass, 2 issue (G-18-4 якорь под шапкой, G-18-6 усечение номера в h2 и перелив К аккаунтам на 320), status diagnosed; решения владельца для gap-раунда записаны в 18-UAT.md."
  gaps_closed:
    - "G-18-4 (код): `html { scroll-padding-top: 170px }` и 236px при <=860px, app.css:446, :503 — браузерная приёмка остаётся в human_verification"
    - "G-18-6 (код): приоритет усечения пометки `flex: 1 1 0; max-width: max-content`, `.acct-head__actions { flex: 0 1 auto; min-width: 0 }` — браузерная приёмка остаётся в human_verification"
    - "WR-01, WR-02, WR-03, IN-01, IN-02, IN-03 (ревью 2026-11-22 закрыло их по коду)"
    - "OBS-422 (код): пустой блок `innerHTML:#notice` в phone_error_response.html; пример под полем на ошибке один"
  gaps_remaining: []
  regressions: []
overrides: []
human_verification:
  - test: "Якорь `#phone` под липкой шапкой (G-18-4, WR-02, UI-R-11/UI-R-15), переформулирован под код с `html { scroll-padding-top }`: с `/accounts` нажать «Указать номер» / «Изменить» на аккаунте с длинным списком групп на 1280, 375 и 320 px; затем открыть `/accounts/{id}/groups#phone` напрямую; затем перейти по якорю `#sched-{id}` на экране расписаний"
    expected: "в видимой области остаются и поле «Номер телефона», и его подпись: `document.elementFromPoint` в центре поля возвращает не `[data-head]`, верх подписи ниже низа шапки; `getComputedStyle(document.documentElement).scrollPaddingTop` равен 170px на десктопе и 236px при <=860px; якоря `#sched-{id}` не ушли под шапку"
    why_human: "прокрутка и перекрытие липкой шапкой — поведение браузера; владелец в UAT (тест 4) видел поле целиком под шапкой, исправление в коде проверено только чтением CSS и тестом `test_the_document_scroll_padding_clears_the_sticky_head`, который сравнивает литерал с константами в самом тесте"
  - test: "Раскладка на 320 и 375 px (G-18-6, UI-R-14, UI-R-05), после правок 18-04: шапка экрана групп с ручным номером; чип расписания с ручным номером и двойником; карточка `/accounts`; карточка в `sync_failed` (четыре действия)"
    expected: "в `<h2>` номер виден целиком (`scrollWidth == clientWidth` у части номера), усекается пометка «указан вручную», `#id` двойника виден; в чипе на 320 px допустим усечённый номер с полным текстом в `title=` (решение владельца), канал не уступает раньше номера, `#id` на месте; «К аккаунтам» не выходит за карточку (`innerWidth` равен `visualViewport` на 320); ряд действий `sync_failed` переносится без обрезки; пометка набрана кеглем номера"
    why_human: "рендер суита не проверяет: тесты читают текст CSS. До правок замер владельца давал номер 105/116 px (320) и 115/116 px (375) с многоточием на «67», после правок замера нет"
  - test: "Кнопка «Сохранить» у поля (WR-01, UI-R-09/UI-R-19): на 1280, 900, 375 и 320 px в обычном состоянии и после 422 снять `getBoundingClientRect` поля `#phone` и кнопки; в дереве доступности DevTools посмотреть имя поля"
    expected: "на >400 px верх и низ кнопки совпадают с полем (±1 px), после 422 кнопка не сдвигается, подсказка и ошибка под рядом; на <=400 px кнопка стоит сразу под полем; имя поля — «Номер телефона…» с текстом ошибки на 422; щелчок по подписи ставит фокус в поле"
    why_human: "геометрия сетки (`grid-template-areas`, `align-self: stretch`, `display: contents` у подписи) суитой не измеряется; `display: contents` на `label` исторически бывает хрупок для дерева доступности — проверка ручная"
  - test: "Фокус после «Сохранить» и после 422 (план 18-05: UI-P1, IN-01, UI-R-16) в настоящем браузере: сохранить номер кнопкой и клавишей Enter; затем ввести `abc` и отправить; затем просто открыть экран и перейти по якорю с карточки"
    expected: "после успеха и после 422 `document.activeElement` — поле `#phone`; читалка на 422 озвучивает ошибку вместе с именем поля; при обычном открытии экрана и при переходе по якорю без JS фокус полю не навязывается (нет `autofocus` в разметке показа)"
    why_human: "рантайм htmx 2.0.10 фокусирует `[autofocus]` в подменённом содержимом — это поведение браузера и JS, суита проверяет только атрибут в ответе; вывод о рантайме сделан чтением `htmx.min.js`"
  - test: "Старая плашка при ошибке (план 18-08: OBS-422, UI-R-24) в браузере с JS: сохранить корректный номер (появится «Номер сохранён.»), затем ввести `abc` и отправить"
    expected: "зелёная плашка «Номер сохранён.» исчезает, под полем одна ошибка «Не похоже на номер телефона. Пример: +7 999 123-45-67», пример под полем один раз (подсказка о примере не повторяется, остаётся фраза о стирании); красная плашка аварии не появилась; `#notice` остался в DOM (повторное сохранение снова показывает плашку)"
    why_human: "применение внеполосного блока `hx-swap-oob=innerHTML:#notice` — поведение рантайма htmx; суита проверяет, что пустой блок есть в ответе 422 и что ответ без `HX-*` заголовков, но не то, что плашка исчезла"
  - test: "Высота `[data-head]` против литералов 170 / 236 px (WR-05, UI-R-23): на 320, 375, 860 и 900 px при самой длинной подписи аккаунта (пометка, `#id`, длинный канал) замерить высоту шапки; затем открыть экраны, где `[data-head]` нет, и перейти по их якорям"
    expected: "замер + 20 px подписи поля + запас не превышают 170 px на десктопе и 236 px при <=860 px (иначе литералы и константы `SCROLL_PADDING_*` в `test_responsive_markup.py` поднимаются одним коммитом по замеру); на экранах без шапки глобальный отступ не даёт заметной пустоты над якорем и не съедает область прокрутки на ландшафтном телефоне"
    why_human: "литералы выведены, а не замерены (комментарий в `app.css:436-446` говорит это прямо); замеры владельца в UAT дают шапку 86 px (1280) и 172 px (320/375), что укладывается, но без самой длинной подписи; рост шапки молча вернёт G-18-4 при зелёной суите"
  - test: "Контраст и размер пометки на рендере (UI-R-18): инструментом DevTools в `<h2>`, `<h1>` шелла, карточке `/accounts` и в чипе расписания (выключенном и включённом)"
    expected: "контраст `--text-secondary` на фоне не ниже 4,5:1 (расчёт по токенам дал 5,47-5,88:1); кегль пометки равен кеглю номера (11 px)"
    why_human: "тест `test_the_manual_mark_contrast_meets_aa_on_every_background` считает по значениям токенов, а не по рендеру; на полупрозрачной шапке и смеси акцента в чипе значение может отличаться"
human_verification_discharged:
  - test: "htmx-обмен без перезагрузки при сохранении номера (прежний пункт 1)"
    discharged_by: "18-UAT.md, тест 1, result: pass (владелец: «тесты 1-3 прийми», 2026-11-21); машинная улика CDP на бою: POST /accounts/75/phone -> 200, подписи, вкладка и плашка сменились без перезагрузки"
  - test: "Очистка номера с JS (прежний пункт 2)"
    discharged_by: "18-UAT.md, тест 2, result: pass (то же принятие владельца); улика: «Номер неизвестен», пометки нет, плашка «Номер удалён.»"
  - test: "422 без плашки аварии (прежний пункт 3)"
    discharged_by: "18-UAT.md, тест 3, result: pass (то же принятие владельца); улика: текст ошибки по-русски, эхо `abc`, обе плашки аварии невидимы. Побочное наблюдение (старая зелёная плашка над ошибкой, пример дважды) выделено в OBS-422 и ушло в новые пункты human_verification"
  - test: "Автозаполнение (прежний пункт 5)"
    discharged_by: "18-UAT.md, тест 5, result: pass: владелец в Chrome, при установке курсора в поле браузер ничего не предлагает; `autocomplete=off` на месте (phone_form.html:87)"
human_verification_carried_forward:
  - test: "Якорь `#phone` (прежний пункт 4)"
    state: "still required: 18-UAT.md тест 4 result: issue (G-18-4); переформулирован выше под `scroll-padding-top`"
  - test: "Раскладка на 320 и 375 px (прежний пункт 6)"
    state: "still required: 18-UAT.md тест 6 result: issue (G-18-6); переформулирован выше под приоритет усечения, сжимаемый ряд действий; кнопка WR-01 вынесена отдельным пунктом"
behavior_unverified_items:
  - truth: "G-18-4: после перехода по `#phone` поле и его подпись не под липкой шапкой"
    test: "перейти по якорю с карточки на 1280/375/320 px"
    expected: "`elementFromPoint` в центре поля не `[data-head]`"
    why_human: "перекрытие шапкой видно только в рендере; литералы 170/236 выведены, а не замерены (WR-05)"
  - truth: "G-18-6: при нехватке ширины усекается пометка, номер в `<h2>` и чипе остаётся целым пока пометка не ушла, `#id` виден, «К аккаунтам» внутри карточки"
    test: "открыть экран групп и карточки на 320/375 px"
    expected: "номер целиком в `<h2>`, пометка усечена первой, нет горизонтальной прокрутки"
    why_human: "приоритет задан текстом CSS (`flex: 1 1 0; max-width: max-content`), тест читает правило, а не раскладку; владелец видел обратное до правки"
  - truth: "UI-P1/IN-01: после ответа на отправку формы фокус стоит в поле"
    test: "сохранить и отправить неверный ввод в браузере с JS"
    expected: "`document.activeElement` равен `#phone`"
    why_human: "фокусировку `[autofocus]` выполняет рантайм htmx; суита проверяет атрибут в ответе"
  - truth: "OBS-422: ответ 422 снимает прежнюю плашку «Номер сохранён.»"
    test: "сохранить корректный номер, затем `abc`"
    expected: "`#notice` пуст, ошибка под полем одна"
    why_human: "применение внеполосного блока — рантайм htmx; суита проверяет пустой блок в ответе"
  - truth: "WR-01: кнопка «Сохранить» стоит в одном ряду с полем и выровнена по нему, не по подсказке"
    test: "замер `getBoundingClientRect` на 1280/900/375/320 px"
    expected: "верх и низ кнопки и поля совпадают, после 422 кнопка не прыгает"
    why_human: "геометрия сетки не измеряется суитой"
  - truth: "G-18-6 (решение владельца «Да, заодно»): ряд действий шапки на 320 px переносится внутри карточки"
    test: "экран групп на 320 px"
    expected: "`innerWidth` равен `visualViewport`, «К аккаунтам» внутри карточки"
    why_human: "перелив по CSS предсуществует с `bef29322`; правка `flex: 0 1 auto; min-width: 0` проверена чтением, замера нет"
advisory:
  - finding: "WR-04 (код-ревью 2026-11-22, warning): утверждение `assert 'html' in simple_parts` в `tests/test_pages/test_shell.py:7943` привязывает охранное правило о плашке аварии к стилевому решению (красно при любой законной правке, снимающей `html { scroll-padding-top }`, например при отклеивании шапки <=860 px), и контроля `html { filter }` в наборе нет. Подтверждено чтением: `test_control_a_filter_on_the_html_tag_reddens` в репозитории отсутствует"
    category: other
    reason: "тест-долг, цель фазы не затрагивает; ревьюер предложил однонаправленное условие `if 'html' in simple_parts` и контроль в семействе `test_control_*`"
    evidence_status: "подтверждено чтением test_shell.py:7943 и поиском по имени контроля"
    owner: "владелец фазы; чинится вместе с решением по WR-05 (если шапку отклеят, утверждение станет красным)"
  - finding: "WR-05 (код-ревью, warning): литералы 170/236 px не привязаны к высоте шапки; границы теста (135/201/20) живут в самом тесте и не краснеют при росте шапки; правило глобальное. Также вынесено пунктом human_verification (высота шапки против литералов)"
    category: other
    reason: "закрытие G-18-4 держится на двух числах, выведенных из CSS; до замера обходом гарантии нет"
    evidence_status: "подтверждено чтением app.css:436-446, :503 и test_responsive_markup.py:5454-5458"
    owner: "владелец при `/gsd-verify-work 18`: замер шапки, затем поднять литералы и константы одним коммитом"
  - finding: "IN-04 (код-ревью, info): имя и докстринг теста `test_sync_status_view_carries_the_manual_flag_in_all_four_constructors` говорят о четырёх конструкторах, которых после 18-06 нет; перечни «Читаемые ключи» в `phone_response.html` и `phone_error_response.html` не называют `phone_focus`"
    category: other
    reason: "устаревшие имена вводят читателя в заблуждение; ключ в перечне подсказал бы будущему четвёртому рендеру. Для `phone_error_response.html` проверено: перечень заканчивается на `phone_maxlength`"
    evidence_status: "подтверждено чтением"
    owner: "владелец; чистка без влияния на цель"
  - finding: "UI-R-04 (UI-ревью, WARNING, цель затронута): при узкой ширине пометка «указан вручную» уходит первой, а `title=` чипа берётся из плоской подписи без пометки (`ads/includes/sched_card.html:226`), у `<h2>` `title=` нет (`account_groups/list.html:59`): ручной номер неотличим от автоматического. Конфликт D-10 («в плоских формах пометки нет») с контрактом усечения; не входит в цель «видит, что номер указан им» на широких экранах, но ослабляет её на узких"
    category: other
    reason: "нужно решение владельца об исключении из D-10 (отдельный помощник для `title=`, не `plain`); владельцу не предлагалось, в раунд не входило"
    evidence_status: "по коду (UI-REVIEW), не замерено"
    owner: "владелец; кандидат на gap-раунд или перенос с названным решением"
  - finding: "UI-R-13 (UI-ревью, WARNING): `components/field.html` не печатает `aria-describedby`, параметра нет; имя поля собирается из подписи, подсказки и ошибки внутри `<label>`"
    category: other
    reason: "общий макрос всех форм авторизации и профиля, вне фазы; владелец в раунд не включал; отдельное решение"
    evidence_status: "подтверждено чтением field.html:14-33"
    owner: "владелец"
  - finding: "UI-R-21 (UI-ревью, WARNING): `.mono--muted` (`app.css:858`, `--text-muted` 3,61:1 на `--surface`) на «Номер неизвестен» и `#id` двойника; дефект пришёл из Фазы 17, гап-раунд оставил его нарочно"
    category: other
    reason: "одна строка, но меняет все экраны с `.mono--muted`: нужно решение владельца"
    evidence_status: "по токенам (расчёт UI-ревью), не замерено на рендере"
    owner: "владелец"
  - finding: "UI-R-02 (INFO) «Изменить» не называет объект (9 мест) и UI-R-03 (INFO) «Сохранить» общий глагол (`phone_form.html:89`)"
    category: other
    reason: "формулировки, решения владельца; правка UI-R-02 затрагивает счёт ссылок в `test_account_phone_links.py`"
    evidence_status: "подтверждено чтением (accounts/list.html:119,145,185 и др.)"
    owner: "владелец"
  - finding: "UI-R-05 (INFO): `.acct-card__actions > .btn:first-child { flex: 1 1 auto }` растягивает только первую кнопку; в `sync_failed` четыре элемента; перенос на 320 px не измерен (вошло в human_verification про раскладку 320/375)"
    category: other
    reason: "косметика, без влияния на цель"
    evidence_status: "по коду (app.css:3330), не замерено"
    owner: "владелец"
  - finding: "UI-R-20 (INFO): повтор `MESSENGER_LABELS` в `account_groups/list.html:15` (IN-02 Фазы 17)"
    category: other
    reason: "предсуществующий долг Фазы 17, фазу 18 не трогает"
    evidence_status: "перенесён из UI-ревью без перепроверки"
    owner: "владелец"
  - finding: "UI-R-22 (INFO): подсказка «Чтобы стереть номер…» видна и у аккаунта без номера, где стирать нечего (`phone_form.html:78-81`)"
    category: other
    reason: "появилась вместе с UI-P3; лечится условием по пустому `phone_value`"
    evidence_status: "подтверждено чтением phone_form.html: ветка меняет подсказку только при ошибке"
    owner: "владелец"
  - finding: "UI-R-23 (INFO): глобальный `html { scroll-padding-top }` действует на экраны без `[data-head]`; также вынесено пунктом human_verification"
    category: other
    reason: "не проверено, какие экраны без шапки имеют якоря"
    evidence_status: "по коду"
    owner: "владелец при замере шапки"
---

# Фаза 18: ручная правка номера — отчёт верификации (повторная, после gap-раунда 18-04…18-08)

**Цель фазы:** пользователь сам указывает, исправляет или стирает номер своего аккаунта в любой момент и видит, что номер указан им, — а автоматика его не перебивает
**Проверено:** 2026-11-22
**Статус:** human_needed
**Повторная верификация:** да — после gap-раунда (`/gsd-execute-phase 18 --gaps-only`), предыдущий раунд 2026-11-21 (human_needed, 5/5)

Исходная гипотеза: «задачи gap-раунда выполнены, цель не достигнута». Опровергнуть по коду не удалось: исправления G-18-4, G-18-6, OBS-422, WR-01, WR-03, IN-01…IN-03 существуют в коде, связаны и закреплены тестами, регрессий в критериях ROADMAP нет. Но ровно те дефекты, ради которых раунд запущен (якорь под шапкой, усечение номера, кнопка у поля, фокус, старая плашка), браузерные: суита их не исполняет, а владелец видел их провал в UAT. Поэтому шесть истин остаются «присутствует, поведение не проверено», а статус — `human_needed`. Блокеров и разрывов кода нет.

## Достижение цели

### Наблюдаемые истины

Контракт — пять критериев ROADMAP (регрессионная проверка) плюс истины gap-раунда из планов 18-04…18-08 и решений владельца в `18-UAT.md`.

| # | Истина | Статус | Улика |
|---|--------|--------|-------|
| 1 | Ссылка с карточки, свободный ввод, оба транспорта, пометка «указан вручную» везде, где подпись рисуется разметкой | ✓ VERIFIED (регрессия) | Файлы `account_label.py`, `account_label.html`, `labels.py`, `accounts/*.html` с прошлого раунда не менялись (`git diff d197f956..HEAD -- app tests` не содержит их). Мой прогон четырёх файлов (`test_responsive_markup`, `test_account_phone_form`, `test_account_label_accounts`, `test_account_phone_links`): 223 passed (151 + 24 + 24 + 24). Браузерная половина принята владельцем (UAT тест 1, pass) |
| 2 | 422 с русским текстом и примером, эхо, плашки аварии нет | ✓ VERIFIED (регрессия) | `phone_error_response.html` несёт форму и пустой блок; текст ошибки несёт пример; UAT тест 3 pass |
| 3 | Очистка: «Номер неизвестен», пометка исчезает, автоисточник снова вправе писать | ✓ VERIFIED (регрессия) | `app/application/accounts/phone.py` в gap-раунде не менялся; `test_after_the_clearing_an_automatic_source_may_fill_the_number_again` (`test_account_phone_form.py:664`) прошёл в моём прогоне; UAT тест 2 pass |
| 4 | Имперсонация, чужой аккаунт как несуществующий, `is_same_origin`, `ID_MAX` | ✓ VERIFIED (регрессия) | Порядок проверок в `account_phone_save` (`account_groups.py:373-543`: сессия, источник, `set_manual_phone`, журнал только `account_id` и `phone_set`) не менялся; `ALLOWED_ROUTES` и `test_impersonation*` не в диффе. Полный прогон оркестратора на 6e3cea19: 6046 passed, 2 skipped, `TEST_EXIT=0` |
| 5 | Сквозные гейты пересчитаны и зелены | ✓ VERIFIED (регрессия) | Числа в коде: `WRITE_FORM_PLACES = 50`, `MUTATING_ROUTE_COUNT = 50`, `FRAGMENT_RESPONSE_HANDLERS_DECLARED = 26`; `OOB_BLOCKS = 25` (сдвиг 24 -> 25 плана 18-08, `test_htmx_markup_gates.py:2677`). Выборка `test_htmx_markup_gates` + `test_shell` по ключам oob/notice/ancestor/banner: 75 passed. Полная суита оркестратора зелёная |
| 6 | G-18-4 (18-04): поле `#phone` и его подпись после перехода по якорю не под липкой шапкой; шапка остаётся липкой на всех ширинах | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | `app.css:446` `html { scroll-padding-top: 170px }` и `:503` 236px внутри `@media (max-width: 860px)`; базовое правило выше медиаблока; `scroll-margin` на `[data-acct-phone]` нет. Замеры владельца в UAT (шапка 86 px на 1280, 172 px на 320/375) покрываются литералами, но число выведено, а не замерено (WR-05). Эффект на странице суита не видит |
| 7 | G-18-6 (18-04): усекается пометка, номер в `<h2>` и чипе остаётся пока пометка не ушла; `#id` не сжимается; канал и номер не несжимаемые | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | `app.css:2590-2600` (`flex: 1 1 0; max-width: max-content` у пометки в `.chip__label` и `.acct-head__name`; `.acct-label__id { flex: none }`); тест `test_account_label_keeps_the_twin_id_visible_in_a_one_line_container` (`:5164`) переписан на механизм, `flex-shrink` у пометки запрещён регулярным выражением. Раскладка 320/375 не измерена после правки |
| 8 | G-18-6 (решение владельца): ряд действий шапки на 320 px переносится внутри карточки | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | `app.css:2868-2871` `flex: 0 1 auto; min-width: 0`; тест `test_the_account_head_actions_can_wrap_inside_the_card`. Перелив был предсуществующим (`bef29322`), замера после правки нет |
| 9 | UI-P2: пометка кеглем номера (`--fs-xs`) и цветом с контрастом не ниже 4,5:1 на четырёх фонах | ✓ VERIFIED (по токенам; рендер — human) | `app.css:2594` `.acct-label__manual { color: var(--text-secondary); font-size: var(--fs-xs) }`; `test_the_manual_mark_contrast_meets_aa_on_every_background` считает формулу WCAG по значениям токенов `:root`; проходит в моём прогоне |
| 10 | UI-P1, IN-01: после ответа на отправку (успех с JS, 422 с JS, страница 422) фокус в поле; при обычном показе `autofocus` нет | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED (серверная часть VERIFIED) | `field.html:12,30` (параметр, по умолчанию ложный), `phone_form.html:88` `autofocus=phone_focus`; `_phone_form_context(..., focus=...)`: `False` в `_screen_context` (`account_groups.py:356-358`), `True` в трёх ответах на отправку (`:509-511`, `:530-532`, `:562-566`). Тесты `test_the_answer_to_a_submission_puts_focus_back_into_the_field` (`:693`), `test_the_plain_screen_never_autofocuses_the_field` (`:735`) зелёные. Фокусировку `[autofocus]` исполняет рантайм htmx в браузере |
| 11 | UI-P3 + OBS-422 (часть): подсказка называет стирание; на ответе с ошибкой пример под полем один | ✓ VERIFIED | `phone_form.html` (`erase_sentence`, ветка `example_phone in phone_error`); тесты `test_the_hint_tells_that_a_cleared_field_erases_the_number` (`:761`), `test_an_error_answer_names_the_example_once` (`:778`) зелёные |
| 12 | OBS-422: ответ 422 снимает прежнюю плашку «Номер сохранён.», не трогая настойчивую область и без `HX-*` | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED (серверная часть VERIFIED) | `phone_error_response.html`: пустой `<div hx-swap-oob="innerHTML:#notice"></div>` после включения формы; `_error_fragment` рисует этот файл (`account_groups.py:528`); `test_a_422_htmx_answer_clears_the_previous_notice` (`:357`) зелёный; `#notice` есть в шелле. Что рантайм htmx подменил содержимое и плашка исчезла, суита не исполняет |
| 13 | WR-01: кнопка «Сохранить» в одном ряду с полем, выровнена по нему; на <=400 px сразу под полем | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | `app.css:2904-2935` (сетка `"label label" / "input button" / "hint hint"`, `align-self: stretch`; на <=400 px одна колонка с кнопкой под полем); тесты `test_the_save_button_shares_the_row_of_the_phone_input` (`:5284`) и собственной строки формы зелёные. Геометрия не измерена |
| 14 | WR-03: у `SyncStatusView` нет ни одного умолчания, один конструктор | ✓ VERIFIED | `dto.py:15` `@dataclass(slots=True, kw_only=True)`, четыре поля без умолчаний (`:46-49`); `use_cases.py:57-66` один конструктор `SyncStatusView(status=..., messenger_type=..., phone=..., phone_is_manual=account.phone_is_manual)`; `test_sync_status_view_has_no_defaults` (`:294`) зелёный; единственный конструктор в `app/` |
| 15 | IN-02, IN-03: один помощник контекста формы с шестью ключами; `maxlength` выведен из константы | ✓ VERIFIED | `account_groups.py:237-262` `_phone_form_context`; `_screen_context` с параметрами только по имени; вызовы `:356`, `:509`, `:530`, `:562`; тест `maxlength` через `MANUAL_INPUT_MAX_CHARS` в `test_account_phone_form.py` |

**Счёт:** 9/15 истин верифицировано (5 критериев ROADMAP + истины 9, 11, 14, 15); 6 присутствуют и подключены, но поведение в браузере не исполнено тестами (6, 7, 8, 10, 12, 13).

Каждая из шести — behavior-dependent (перекрытие шапкой, усечение при нехватке ширины, фокус и подмена, геометрия сетки): в проверке нашлось только присутствие правила и текст-тест, поэтому они не считаются верифицированными и не провалены. Все шесть вынесены в `behavior_unverified_items` и `human_verification`.

### Отложенные пункты

Не заявлены. Просмотрены фазы 19 и 20 вехи (захват номера при подключении; дозаполнение номеров): они не покрывают находки UI- и код-ревью этого раунда.

### Дисциплина закрытия находок ревью (контракт переноса)

Каждая находка попала в вердикт: ни одна не потеряна.

**Код-ревью 2026-11-22, открытые три:**

| ID | Куда попало |
|----|-------------|
| WR-04 | `advisory` (подтверждено чтением, `test_shell.py:7943`) |
| WR-05 | `advisory` и `human_verification` (высота шапки против литералов) |
| IN-04 | `advisory` |

Закрыты ревью и подтверждены мной по коду: WR-01 (18-07), WR-02 (18-04), WR-03 (18-06), IN-01 (18-05), IN-02 и IN-03 (18-07). Примечание к записи ревью: в сводке код-ревью «`test_responsive_markup` (223 passed)» цифра относится к прогону четырёх файлов вместе (151 + 24 + 24 + 24 = 223), а не к одному `test_responsive_markup`. На выводы это не влияет.

**UI-ревью 2026-11-22, открытые 14:**

| ID | Серьёзность | Куда попало |
|----|-------------|-------------|
| UI-R-02 | INFO | `advisory` (решение владельца) |
| UI-R-03 | INFO | `advisory` (решение владельца) |
| UI-R-04 | WARNING | `advisory`, цель затронута на узких экранах; нужно решение владельца по D-10 |
| UI-R-05 | INFO | `advisory` и в human-пункт про раскладку 320/375 |
| UI-R-13 | WARNING | `advisory` (общий макрос вне фазы, решение владельца) |
| UI-R-14 | человек | `human_verification` «Раскладка на 320 и 375 px» |
| UI-R-15 | человек | `human_verification` «Якорь `#phone`» |
| UI-R-16 | человек | `human_verification` «Фокус после «Сохранить» и после 422» |
| UI-R-18 | человек | `human_verification` «Контраст и размер пометки на рендере» |
| UI-R-19 | человек | `human_verification` «Кнопка «Сохранить» у поля» |
| UI-R-20 | INFO | `advisory` (предсуществующий долг Фазы 17) |
| UI-R-21 | WARNING | `advisory` (решение владельца) |
| UI-R-22 | INFO | `advisory` |
| UI-R-23 | INFO | `advisory` и `human_verification` «Высота `[data-head]` против литералов» |

Итог по UI-ревью: 14 открытых = 5 в `human_verification` напрямую (UI-R-14, 15, 16, 18, 19) + 9 в `advisory` (UI-R-02, 03, 04, 05, 13, 20, 21, 22, 23). Закрытые ревью по коду UI-P1, UI-P2, UI-P3, UI-R-01, 06…12, 17 и UI-R-24 (OBS-422) учтены истинами 9, 10, 11, 12, 13 выше. Отдельно, из «Владельцу не предлагалось» в `18-UAT.md`: опора 2 UI-ревью (UI-R-04, `title=` без пометки) и последний пункт опоры 6 (UI-R-13) вынесены в `advisory`, а не потеряны.

### Обязательные артефакты (gap-раунд)

| Артефакт | Ожидание | Статус | Детали |
|----------|----------|--------|--------|
| `app/static/css/app.css` | приоритет усечения, сжимаемый ряд действий, кегль и цвет пометки, `scroll-padding-top` (170 / 236), сетка формы, правило <=400 px | ✓ VERIFIED (уровни 1-3) | `:446`, `:503`, `:2590-2600`, `:2868-2871`, `:2904-2935`; не заглушка, подключён (шелл и экран групп) |
| `app/templates/account_groups/partials/phone_error_response.html` | форма и пустой блок подмены содержимого `#notice` | ✓ VERIFIED | включён обработчиком `_error_fragment`; пустой блок без номера, текста и кода (D-16) |
| `app/templates/components/field.html` | булев параметр `autofocus=false` | ✓ VERIFIED | при умолчании разметка прежних полей не меняется; потребитель один (`phone_form.html`) |
| `app/templates/account_groups/includes/phone_form.html` | подсказка о стирании, пример один на ошибке, `autofocus=phone_focus` | ✓ VERIFIED | поле без `required`, `autocomplete=off` |
| `app/pages/account_groups.py` | `_phone_form_context`, ключ `phone_focus`, `_screen_context` по именам | ✓ VERIFIED | четыре вызова; нет ни `rollback`, ни собственного редиректа в обработчике правки |
| `app/application/accounts/dto.py`, `use_cases.py` | `SyncStatusView` без умолчаний, один конструктор | ✓ VERIFIED | `kw_only=True`; единственный вызов `use_cases.py:62` |
| `tests/test_pages/test_responsive_markup.py`, `test_account_phone_form.py`, `test_account_label_accounts.py`, `test_shell.py`, `test_htmx_markup_gates.py` | тесты раунда | ✓ VERIFIED | функции существуют и проходят; ограничения — WR-04, WR-05 в `advisory` |
| `.planning/phases/18-ruchnaya-pravka-nomera/18-01-SUMMARY.md` | пометка «ОПРОВЕРГНУТО» у ложного порядка усечения | ✓ VERIFIED | два вхождения |

### Проверка ключевых связей

| Откуда | Куда | Через | Статус |
|--------|------|-------|--------|
| `account_groups.py:_error_fragment` | `phone_error_response.html` | `respond_field_error(request, page=..., fragment=...)` -> шаблон (`:528`) | ✓ WIRED |
| `phone_error_response.html` | `includes/notice_area.html` (`#notice`) | `hx-swap-oob="innerHTML:#notice"` (область есть в шелле) | ✓ WIRED (применение — human) |
| `phone_form.html` | `field.html` | `field(..., autofocus=phone_focus)` | ✓ WIRED |
| `account_groups.py` | `phone_form.html` | `_phone_form_context` во всех четырёх рендерах | ✓ WIRED |
| `use_cases.py:get_sync_status_view` | `dto.SyncStatusView` -> `accounts.py` | все четыре поля по имени -> `view.phone_is_manual` | ✓ WIRED |
| `app.css` (`html { scroll-padding-top }`) | `base.html` `<header data-head>` (`position: sticky`) | отступ на прокручиваемом документе | ✓ WIRED (эффект — human) |
| `app.css` (правила `.acct-label__*`) | `components/account_label.html` | классы частей подписи в `.chip__label` и `.acct-head__name` | ✓ WIRED (раскладка — human) |

### Трассировка потока данных (уровень 4)

| Артефакт | Данные | Источник | Реальные данные | Статус |
|----------|--------|----------|-----------------|--------|
| форма номера | `phone_value`, `phone_error`, `phone_focus` | `acct_label.phone_text` из `load_account_rows` / эхо присланного / флаг вызывающего | да | ✓ FLOWING |
| фрагмент опроса | `phone_is_manual` | колонка `MessengerAccount.phone_is_manual` у уже загруженного аккаунта | да | ✓ FLOWING |

### Поведенческие проверки

| Поведение | Команда | Результат | Статус |
|-----------|---------|-----------|--------|
| Регрессия критериев 1-4, истины 9-15 (тесты раунда) | `flock … uv run pytest tests/test_pages/test_responsive_markup.py tests/test_pages/test_account_phone_form.py tests/test_pages/test_account_label_accounts.py tests/test_pages/test_account_phone_links.py -q -p no:randomly -x` | 223 passed (193 с) | ✓ PASS |
| Гейты OOB и охранное правило плашки | `… pytest tests/test_templates/test_htmx_markup_gates.py tests/test_pages/test_shell.py -k "oob or notice or ancestor or banner"` | 75 passed | ✓ PASS |
| Полная суита | не запускалась мной; лог оркестратора на 6e3cea19 | 6046 passed, 2 skipped, `TEST_EXIT=0`; с тех пор менялся только `.planning/` | ✓ PASS (по логу) |
| `tests/test_planning` на HEAD | данные оркестратора | 218 passed, 2 skipped | ✓ PASS (по данным оркестратора) |
| Проверка TDD-гейта | данные оркестратора | 8 планов `type: tdd`, 0 нарушений | ✓ PASS (по данным оркестратора) |
| Коммиты сводок | `git cat-file -e` по 20 хешам из сводок 18-04…18-08 | все 20 существуют | ✓ PASS |

### Выполнение проб

Фаза не объявляет проб (`probe-*.sh`): шаг пропущен.

### Покрытие требований

| Требование | Планы | Статус | Улика |
|------------|-------|--------|-------|
| PHONE-08 | 18-01, 18-04, 18-06 | ✓ SATISFIED в коде; раскладка пометки на узких экранах — human | макрос и поле `phone_is_manual`, `SyncStatusView` без умолчаний, приоритет усечения, контраст по токенам; UI-R-04 в `advisory` |
| PHONE-09 | 18-02, 18-03, 18-04, 18-05, 18-07, 18-08 | ✓ SATISFIED в коде; браузерные половины — human | маршрут, форма, 9 ссылок, 422, фокус, плашка, сетка формы; UAT 1-3, 5 pass; 4 и 6 issue, исправления ждут замера |
| PHONE-10 | 18-02, 18-05 | ✓ SATISFIED | очистка и `KEPT -> WRITTEN`; подсказка о стирании |
| PHONE-11 | 18-02 | ✓ SATISFIED | имперсонация с причиной, чужой как несуществующий |

Все четыре ID заявлены в `requirements:` планов 18-01…18-08 и присутствуют в `REQUIREMENTS.md` (строки 28, 32-34; трассировка Phase 18, «Pending»). Осиротевших требований нет. Чекбоксы и колонка «Pending» — запись оркестратора при закрытии фазы; верификатор их не правит.

### Запреты планов (`must_haves.prohibitions`), перенесено с прошлого раунда

12 запретов планов 18-01…18-03 объявлены `status: flagged-unverified` (judgment). Планы 18-04…18-08 новых запретов не вводят. Вердикт ниже НЕАВТОРИТЕТЕН; `unverified-prohibition — human review recommended`. После gap-раунда перепроверено: `account_label.py` (флаг в ключ двойника, умолчание у `AccountRow`) в диффе нет; в `account_groups.py` обработчика нет `rollback`, собственного редиректа и `PHONE_ERROR_BLANK`; у поля нет `required`; `SyncStatusView` лишился умолчания (запрет 18-01 только усилен). Владелец в UAT (тест 7, `pass`, «согласен со всеми 12») сверил строки по пересказу сводной таблицей агента; читал ли он код, в записи не сказано.

| Запрет | Вердикт по коду | Флаг |
|--------|-----------------|------|
| 18-01: флаг в `_twin_key` | не нарушен (`_twin_key(type_, shown)`) | human review recommended |
| 18-01: пометка в плоских формах | не нарушена (`<title>`/модалка/`title=` используют `plain`; но см. UI-R-04 о цене этого решения) | human review recommended |
| 18-01: умолчание у `AccountRow.phone_is_manual` | не нарушен (без умолчания; и у `SyncStatusView` теперь тоже) | human review recommended |
| 18-01: запись в колонки из продуктового кода плана | не нарушен; гейт единого писателя зелёный | human review recommended |
| 18-02: запись мимо `set_manual_phone` | не нарушен (`account_groups.py:492`) | human review recommended |
| 18-02: номер в журнал/адрес/уведомление | не нарушен (`account_id`, `phone_set`; блок снятия плашки пуст) | human review recommended |
| 18-02: зависимость запрета имперсонации; различение чужого и несуществующего | не нарушен | human review recommended |
| 18-02: `PHONE_ERROR_BLANK` из формы, `required` у поля | не нарушен (подтверждено и обходом) | human review recommended |
| 18-02: откат сессии на ветках отказа; собственный редирект | не нарушен | human review recommended |
| 18-02: удаление/вставка аккаунта, сравнение с сохранённым, UNIQUE/отказ по дубликату | не нарушен | human review recommended |
| 18-03: новый маршрут показа или ключ контекста ради ссылки | не нарушен | human review recommended |
| 18-03: прятать ссылку в `syncing`/`sync_failed`, оформлять её формой | не нарушен | human review recommended |

### Антипаттерны

| Файл | Строка | Шаблон | Серьёзность | Влияние |
|------|--------|--------|-------------|---------|
| файлы `app/` и `tests/` диффа `d197f956..HEAD` | — | `TBD` / `FIXME` / `XXX` в добавленных строках | — | совпадений нет |
| те же | — | `TODO`/`HACK`/`PLACEHOLDER`/«coming soon» в `app/` | — | совпадений нет (единственный отклик — сигнатура макроса `field`, ложное срабатывание на `placeholder=`) |

Находка ревью, подтверждённая мной: `tests/test_pages/test_shell.py:7943` — `assert "html" in simple_parts` (WR-04, предупреждение, цель не затрагивает; в `advisory`).

### Человеческая проверка

Семь пунктов перечислены в frontmatter (`human_verification`). Прежние шесть учтены так: 4 сняты UAT владельца (htmx-обмен, очистка с JS, 422 без плашки — тесты 1-3; автозаполнение — тест 5), 2 остаются (якорь `#phone`, раскладка 320/375), добавлены пять новых от gap-раунда (кнопка у поля, фокус после ответа, старая плашка, высота шапки против литералов, контраст на рендере). Отметки и `result` за владельца не записаны; это работа `/gsd-verify-work 18`.

Замечание о весе снятых пунктов: владелец принял тесты 1-3 по машинной улике агента (CDP) словами «тесты 1-3 прийми», не по собственному наблюдению; для верификатора это владельческий `pass` в UAT, как предписывает контракт, но запись об этом в `18-UAT.md` честно названа.

### Резюме

Цель достигнута в части, проверяемой кодом: человек указывает, исправляет и стирает номер, пометка «указан вручную» видна, автоматика его не перебивает (`KEPT`), после очистки снова вправе писать, имперсонация разрешена с причиной; критерии ROADMAP 1-5 без регрессий, числа гейтов совпадают (`OOB_BLOCKS` 25), полная суита зелёная. Gap-раунд закрыл в коде оба провала владельческого обхода (G-18-4, G-18-6) и семь находок ревью, но ни одно из этих исправлений ещё не наблюдалось в браузере: отступ прокрутки 170/236 px выведен, а не замерен (WR-05), приоритет усечения закреплён текстом CSS, фокус и снятие плашки зависят от рантайма htmx. Поэтому `human_needed`: шесть истин присутствуют без доказанного поведения, семь пунктов ждут человека. Из решений владельца остаются не принятыми UI-R-04 (пометка неотличима от автоматического номера при усечении; ослабляет «видит, что номер указан им» на узких экранах), UI-R-13 и UI-R-21. Все три открытые находки код-ревью и все 14 открытых пунктов UI-ревью названы в вердикте. Блокеров нет.

---

_Проверено: 2026-11-22_
_Верификатор: Claude (gsd-verifier)_
