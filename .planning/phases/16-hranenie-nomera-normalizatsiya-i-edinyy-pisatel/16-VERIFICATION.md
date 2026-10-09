---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
verified: 2026-10-09T17:03:15Z
status: gaps_found
score: 16/20 must-haves verified
covered_files:
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-01-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-01-SUMMARY.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-02-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-02-SUMMARY.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-03-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-03-SUMMARY.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-04-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-04-SUMMARY.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-05-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-05-SUMMARY.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-06-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-06-SUMMARY.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-07-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-07-SUMMARY.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-08-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-08-SUMMARY.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-09-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-09-SUMMARY.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-10-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-10-SUMMARY.md"
  - "alembic/versions/0023_messenger_account_phone.py"
  - "app/application/accounts/phone.py"
  - "app/models/messenger_account.py"
  - "app/services/phone.py"
  - "pyproject.toml"
  - "scripts/prohibitions_census.py"
  - "tests/test_application/test_account_phone_race.py"
  - "tests/test_application/test_account_phone_writer.py"
  - "tests/test_application/test_phone_single_writer_gate.py"
  - "tests/test_migrations/test_0023_messenger_account_phone.py"
  - "tests/test_migrations/test_model_matches_head.py"
  - "tests/test_models/test_messenger_account_phone_check.py"
  - "tests/test_phone_privacy_gate.py"
  - "tests/test_planning/test_deferred_items_are_idempotent.py"
  - "tests/test_planning/test_plan_prohibitions_census.py"
  - "tests/test_planning/test_requirement_completion_follows_verification.py"
  - "tests/test_planning/test_state_progress_matches_roadmap.py"
  - "tests/test_services/test_phone.py"
  - "uv.lock"
covered_digest: "v3:sha256:b9992c0cb015c213134cfb6aa18b54efa50d0888aa56a95f893116830882eacf"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 9/10
  previous_round:
    verified: 2026-10-08T20:54:43Z
    status: gaps_found
    score: 9/10 must-haves verified
    covered_digest: "v3:sha256:1649a7e64fbdc378e82ed3c7a63f8d590d6744ed618f0a76021d847282cecdc4"
    gaps:
      - truth: "Критерий 3 (вторая половина): мусор отвергается, а не становится «номером» (D-06) — ручной путь не сочиняет российский номер, которого не бывает, а автопуть не хранит обрывок цифр как номер"
        status: failed
        reason: >-
          CR-01: normalize_manual('00 44 7911 123456') = '+700447911123456', '00 380 50 123 4567' =
          '+700380501234567', '050 123 4567' = '+70501234567', '8 029 123 45 67' = '+70291234567'.
          WR-04: автопуть принимал '12345' → '+12345', '4412345' → '+4412345', '88812' → '+88812'
          (REPORTED_MIN_DIGITS = 5), и строка теста five_digits_lower_bound закрепляла это как норму.
        artifacts:
          - path: "app/services/phone.py"
            issue: "normalize_manual (строки 130–140): нет отказа для кода страны 7 с национальной частью на 0 (number.italian_leading_zero); REPORTED_MIN_DIGITS = 5 (строка 44) пропускает обрывки из 5–6 цифр"
          - path: "tests/test_services/test_phone.py"
            issue: "в MANUAL_REJECTED нет строк '00…' и местного номера с ведущим 0; строка REPORTED_ACCEPTED id=five_digits_lower_bound (строка 81) утверждает '12345' → '+12345' как верное — правило фазы закрепляет дефект"
        missing:
          - "В normalize_manual отказ PHONE_ERROR_NOT_A_NUMBER, когда number.country_code == 7 и number.italian_leading_zero (без is_valid_number — D-05 соблюдён)"
          - "Строки MANUAL_REJECTED: '00 44 7911 123456', '00 380 50 123 4567', '050 123 4567', '8 029 123 45 67'"
          - "Поднять REPORTED_MIN_DIGITS до 7; строку five_digits_lower_bound перенести в REPORTED_REFUSED; летописью назвать прежнее значение 5"
          - "WR-03 (по пути): в mask_phone для разбираемого номера с не более чем двумя цифрами национальной части отдавать head + ' ***'; строка '+88812' в таблицу маски"
    human_verification_disposition:
      - item: "1. Решение владельца по CR-01, вариант ввода с префиксом 00"
        disposition: discharged
        evidence: >-
          Решение владельца О-3 (а) «отказ», 2026-10-09, прогон /gsd-plan-phase 16 --gaps (записано в
          16-RESEARCH.md §«Вопросы владельцу прогона закрытия гэпа» и в 16-07-PLAN.md). Мой прогон
          `uv run python -c "from app.services.phone import normalize_manual; print(normalize_manual('00 44 7911 123456'))"`:
          код выхода 1, stdout пуст, последняя строка stderr — ровно
          `app.services.phone.PhoneError: Не похоже на номер телефона. Пример: +7 999 123-45-67`.
          Исход (а) совпал с заранее названным; '+700447911123456' больше не сохраняется. Вариант (б) не реализован
          (нет кода, переписывающего '00' в '+').
      - item: "2. Сверка вердиктов запретов (judgment-tier)"
        disposition: still_required
        evidence: >-
          Акт владельца. Перенесён в human_verification 1 этого отчёта и расширен: 13 запретов первой партии плюс
          10 запретов партии 16-07…16-10 (перепись: фаза 16 — 23 строки), у каждого вердикт верификатора с уликой.
  gaps_closed:
    - "Пункт missing 1 (CR-01): app/services/phone.py:172-173 — отказ при country_code == RU_KZ_COUNTRY_CODE and italian_leading_zero; GREEN 97e62918; тест test_a_number_typed_with_the_00_prefix_is_refused_not_saved_as_plus_seven_zero (tests/test_services/test_phone.py:248) зелен; мой зонд — все 4 входа гэпа и '+7 012 345 67 89', '0079991234567' дают отказ; Италия '+39 06 1234 5678' → '+390612345678'"
    - "Пункт missing 2: семь строк cr01_* в MANUAL_REJECTED (tests/test_services/test_phone.py:275-283) и положительный контроль italian_leading_zero_is_not_plus_seven (:228)"
    - "Пункт missing 3 (WR-04): app/services/phone.py:63 REPORTED_MIN_DIGITS = 7 с летописью (:60-62), отказ IS_POSSIBLE_LOCAL_ONLY (:213-215); GREEN ae44c1d0; строка five_digits_fragment_was_the_lower_bound в REPORTED_REFUSED (tests/test_services/test_phone.py:115) с летописью (:85); мой зонд: '12345', '123456', '88812', '4412345', '71234567' → None; Ниуэ, Токелау, Fragment строкой и целым — приняты"
    - "Пункт missing 4 (WR-03): app/services/phone.py:266-268 порог маски; GREEN fdb12dd5; тест test_a_short_national_part_is_masked_entirely (:379); мой зонд: '+88812' → '+888 ***', '+712' → '+7 ***', D-10 '+79991234567' → '+7 *** ***-**-67'"
    - "Предупреждение WR-01 прошлого раунда (executemany и ещё четыре формы): закрыто a97179ab, 78495634 — все пять форм дают находку; остаток — новая WR-08 (гэп ниже)"
    - "Предупреждение WR-02 прошлого раунда (bind_contextvars): закрыто 6ed63a95 — мой зонд: structlog.contextvars.bind_contextvars(phone=…) и голое bind_contextvars(phone=…) дают находку; остаток — IN-06 (advisory ниже)"
    - "Предупреждение WR-05 прошлого раунда (KEPT на отсутствующей строке): закрыто 67a25113, bee23ee2 — PhoneWrite.MISSING (app/application/accounts/phone.py:88, :117-120); три правила 16-08 зелены в моём прогоне (3 passed); остаток — IN-07 (гэп ниже)"
  gaps_remaining:
    - "Критерий 3 (вторая половина, D-06) по-прежнему не выполнен полностью — четыре пункта missing прошлого гэпа закрыты, но правило «мусор отвергается» пробито в двух новых местах: WR-06 (ручной путь, номер +7 с четырьмя лишними цифрами сохраняется как «ручной») и WR-07 (автопуть хранит TOO_LONG / INVALID_LENGTH / '+7 0…'). Прошлый раунд верификации WR-06 не заметил: я проверял только префикс 00 и ведущий ноль"
  regressions: []
gaps:
  - truth: "Критерий 3, вторая половина (D-06): мусор и слишком длинный ввод отвергаются, а не становятся «номером» — ручной путь (WR-06)"
    status: failed
    reason: >-
      WR-06 воспроизведён моим зондом: normalize_manual('+7 999 123-45-67 1234') = '+799912345671234',
      '8 999 123 45 67 8901' = '+799912345678901', '89991234567 8901' = '+799912345678901',
      '8 800 123 45 67 890' = '+788001234567890'. format_phone показывает '+7 99912345671234' — номера,
      которого не бывает. Он сохраняется под phone_is_manual=true, и ни один автоисточник его уже не исправит (D-07).
      Это тот же класс вреда, что CR-01, только с другой стороны. RU-метаданные допускают национальную часть из 14 цифр,
      в 9.0.41 законную лишь для бесплатного шаблона 8108…, который аккаунтом мессенджера быть не может.
      Правило немонотонно: '+7 999 123-45-678' (+1 цифра), '+7 999 123-45-67 12' (+2) и '… 123' (+3) получают отказ,
      а +4 цифры принимаются. Добавочный без маркера ('доб', 'ext') — ровно «номер с добавочным» из запрета 16-02 №2.
      Таблица теста не видит дефекта: строк с +4 цифрами нет. Решения владельца, разрешающего 14-значную национальную
      часть +7, нет ни в CONTEXT, ни в RESEARCH (О-1, О-3, О-4).
    artifacts:
      - path: "app/services/phone.py"
        issue: "normalize_manual (:172-173) отвергает у кода 7 только ведущий ноль; длина национальной части не проверяется. Пункт 5 докстринга (:137-148) сам называет «10 и 14 цифр», но закрыт только поднабор с нулём"
      - path: "tests/test_services/test_phone.py"
        issue: "в MANUAL_REJECTED нет ни одной строки +7 с 14-значной национальной частью; соседние one_digit_long / twelve_digits есть, поэтому дыра невидима суите"
    missing:
      - "В normalize_manual отказ PHONE_ERROR_NOT_A_NUMBER, когда number.country_code == RU_KZ_COUNTRY_CODE и длина str(number.national_number) не равна 10 (признак разбора, без is_valid_number — D-05 соблюдён; так же, как CR-01). Константу длины назвать, например RU_KZ_NATIONAL_DIGITS = 10, с комментарием про шаблон 8108… в метаданных 9.0.41"
      - "Строки MANUAL_REJECTED: '+7 999 123-45-67 1234', '8 999 123 45 67 8901', '89991234567 8901', '8 800 123 45 67 890'; положительные строки MANUAL_ACCEPTED (Россия, Казахстан, 8-800) не меняются"
      - "Пункт 5 докстринга normalize_manual дополнить: какая часть «10 и 14 цифр» закрыта и чем, с летописью (ревью WR-06, верификация 2026-10-09)"
  - truth: "Критерий 3, вторая половина (D-06) на автопути, и правдивость границы П-1 в шапке модуля (истина 6 плана 16-07: «граница названа, а не выдана за покрытие») — WR-07"
    status: partial
    reason: >-
      WR-07 воспроизведён: normalize_reported('70123456789') = '+70123456789' (у кода 7 ведущий ноль — константа
      RU_KZ_COUNTRY_CODE в app/services/phone.py:70-73 сама говорит, что такого не бывает); '799912345678' →
      '+799912345678' и '79991234567890' → '+79991234567890' (INVALID_LENGTH; ручная таблица отвергает те же цифры
      как twelve_digits); '1234567890123' → '+1234567890123' и '441234567890123' → '+441234567890123' (TOO_LONG — это
      и есть «слишком длинный ввод» критерия 3); '123456789' → '+123456789' (TOO_SHORT, 9 цифр);
      '700447911123456' → '+700447911123456' (выдуманный номер CR-01 автопутём). Шапка модуля (:33-37) называет
      единственной оставшейся границей «семизначный обрывок TOO_SHORT». Истина 16-07 «граница названа, а не выдана
      за покрытие» поэтому выполнена по букве и нарушена по смыслу: принимаемое множество шире названного. Тяжесть
      ниже, чем у WR-06: автономер не закрыт признаком «ручной», пользователь перепишет его ручной правкой (Фаза 18).
      Но автоисточник сам его уже не исправит (условие phone IS NULL), а Фазы 17–20 покажут его как подпись аккаунта.
      Довод П-1 (Fragment) эти вердикты не покрывает: Fragment '+888…' даёт TOO_SHORT, а не TOO_LONG или INVALID_LENGTH.
    artifacts:
      - path: "app/services/phone.py"
        issue: "normalize_reported (:213-216) отвергает только IS_POSSIBLE_LOCAL_ONLY; шапка (:33-37) и докстринг (:190-196) называют границу уже, чем она есть"
      - path: "tests/test_services/test_phone.py"
        issue: "в REPORTED_REFUSED нет строк TOO_LONG, INVALID_LENGTH и '+7 0…'; таблицы принятых по границе П-1 строк нет"
    missing:
      - "По умолчанию (а): в normalize_reported отвергать то же, что ручной путь отвергает признаками разбора, — код 7 с ведущим нулём и с национальной частью не из 10 цифр (общее правило с починкой WR-06), а также вердикты TOO_LONG и INVALID_LENGTH (Fragment их не даёт). Строки замера выше — в REPORTED_REFUSED; Fragment, Ниуэ, Токелау, Узбекистан, Казахстан остаются в REPORTED_ACCEPTED"
      - "Если владелец выберет (б) (human_verification 2): переписать абзац П-1 шапки на настоящее принимаемое множество («любое разбираемое значение из 7…15 цифр, кроме IS_POSSIBLE_LOCAL_ONLY») и завести поимённую таблицу строк, принятых по этой границе, без утверждения их как нормы; принять отступление записью overrides"
  - truth: "Шапка гейта единственного писателя называет настоящую границу: литеральные формы записи, видимые в исходнике, ловятся, а вне охвата только значения, собранные во время исполнения (истина 5 плана 16-09; запрет 16-09 №2; D-13) — WR-08"
    status: failed
    reason: >-
      WR-08 воспроизведён: я подал девять литеральных форм в phone_write_offences (path 'scripts/x.py'), и каждая
      вернула []:
      `conn.execute(update(MessengerAccount), parameters=[{"id": 1, "phone": p}])` (у Connection/AsyncConnection
      аргумент называется parameters, а в ROW_MAPPING_KEYWORDS только params/mappings);
      `s.execute(update(MessengerAccount), [{"id": a.id, "phone": n} for a, n in rows])`;
      `insert(MessengerAccount).values([{… "phone": n} for …])`; генераторное выражение с тем же словарём;
      `'UPDATE messenger_accounts SET "phone" = :p …'`; `'INSERT INTO "messenger_accounts" …'`;
      `"INSERT INTO public.messenger_accounts …"`; `update(MessengerAccount).ordered_values((MessengerAccount.phone, x))`;
      `object.__setattr__(account, "phone", x)`. Контроли в том же прогоне ловятся: params=, позиционный список,
      SET phone без кавычек. При этом шапка (tests/test_application/test_phone_single_writer_gate.py:68) утверждает:
      «Всё, что видно литералом в исходнике, ловится». Это повтор WR-01 прошлого раунда: граница названа шире,
      чем видит предикат. Список словарей-литералов в comprehension и parameters= — естественная форма скрипта
      дозаполнения Фазы 20, ради которого гейт существует. Живое дерево сейчас чисто (мой греп app/ и scripts/:
      записей вне модуля-писателя нет), поэтому цель «записать номер можно только через один модуль» сегодня
      выполняется. Не выполнено обещание гейта, на которое опираются Фазы 18–20.
    artifacts:
      - path: "tests/test_application/test_phone_single_writer_gate.py"
        issue: "ROW_MAPPING_KEYWORDS (:122) без 'parameters'; _literal_mappings (:299-313) не раскрывает ListComp/GeneratorExp/SetComp; RAW_SQL_PHONE_WRITE (:129-133) не допускает кавычек у phone и у messenger_accounts и префикса схемы; ordered_values нет в WRITE_CALL_NAMES (:108); __setattr__ нет в NAMED_ATTRIBUTE_WRITERS (:111); шапка :63-68 утверждает полный охват литералов"
    missing:
      - "'parameters' в ROW_MAPPING_KEYWORDS"
      - "_literal_mappings: для ast.ListComp / ast.GeneratorExp / ast.SetComp отдавать node.elt, когда элемент — литерал словаря или вызов dict(...)"
      - "RAW_SQL_PHONE_WRITE: необязательные кавычки вокруг phone(_is_manual)? и messenger_accounts, необязательный префикс схемы \"?\\w+\"?\\."
      - "ordered_values в судимые вызовы (позиционные кортежи, первый элемент которых — ключ phone*); __setattr__ в NAMED_ATTRIBUTE_WRITERS"
      - "Каждую из девяти форм — строкой LITERAL_FORM_CASES с ожидаемым видом; живое дерево — по-прежнему ноль, реестр — ровно модуль-писатель"
      - "Сужение заявления шапки вместо починки не годится: запрет 16-09 №2 прямо запрещает выдавать слепоту предиката за границу средства, а границей объявлены только значения, собранные во время исполнения"
  - truth: "record_reported_phone с аккаунтом, ни разу не добавленным в сессию, поднимает ValueError(ACCOUNT_NOT_IN_SESSION) — мастер Фазы 19 с забытым session.add падает громко (истина 3 плана 16-08) — IN-07"
    status: partial
    reason: >-
      IN-07 воспроизведён: объект MessengerAccount() не добавлен в сессию. record_reported_phone(s, acc, None),
      (s, acc, '') и (s, acc, 'garbage') возвращают PhoneWrite.UNPARSEABLE, id остаётся None, ValueError нет.
      ValueError поднимается только на разбираемом номере ('79991234567'). Причина — порядок в
      app/application/accounts/phone.py:150-156: normalize_reported идёт раньше проверки id. Две части истины
      выполнены: UPDATE … WHERE id IS NULL не исполняется, KEPT молча не возвращается. Безусловная часть
      «поднимает ValueError» неверна на пути, который PHONE-15 называет самым частым (старый воркер без номера).
      Докстринг (:144-148) обещает Фазе 19 «узнаёт об ошибке сразу». Тест
      test_recording_an_account_never_added_to_the_session_raises (tests/test_application/test_account_phone_writer.py:338)
      подаёт только разбираемый номер. Вред мал: в колонку ничего не пишется. Но это договор писателя с Фазой 19.
    artifacts:
      - path: "app/application/accounts/phone.py"
        issue: "record_reported_phone (:150-156): проверка членства в сессии стоит после нормализации; докстринг шире поведения"
      - path: "tests/test_application/test_account_phone_writer.py"
        issue: "правило отказа не параметризовано неразбираемым входом (None / мусор)"
    missing:
      - "Перенести «if account.id is None: flush; if account.id is None: raise ValueError(ACCOUNT_NOT_IN_SESSION)» до normalize_reported, либо проверять членство без оператора (sqlalchemy.inspect(account).session is not session.sync_session) до нормализации"
      - "Параметризовать test_recording_an_account_never_added_to_the_session_raises входами None, '' и 'garbage' в дополнение к разбираемому номеру"
      - "Если владелец предпочтёт сузить договор: докстринг «когда источник прислал разбираемый номер» и запись overrides на истину 3 плана 16-08"
advisory:
  - finding: "IN-06: гейт приватности не узнаёт привязку контекста под другим именем — `from structlog.contextvars import bind_contextvars as bind_ctx; bind_ctx(phone=account.phone)`, `structlog.threadlocal.bind_threadlocal(phone=…)`, `tmp_bind(logger, phone=…)`; того же семейства — получатель журнала с нестандартным именем (`lg = logging.getLogger(); lg.info('x %s', account.phone)`)"
    category: security
    reason: >-
      Воспроизведено: python_log_offences на всех четырёх формах вернул [], а контроли (bind_contextvars(phone=…)
      через атрибут и голым именем) — находку. Это не блокер, по трём причинам. (1) Истина 6 плана 16-09 сформулирована
      по имени («любой вызов, чьё имя — bind_contextvars или bound_contextvars») и выполнена. (2) Шапка гейта приватности,
      в отличие от гейта писателя, не заявляет полного охвата литералов: раздел «ЧТО СЧИТАЕТСЯ ВЫЗОВОМ ЖУРНАЛА» перечисляет
      распознаваемые имена явно, а D-17 сам задаёт гейт списком получателей (`logger.*`/`log.*`/`logging.*`/`print(`).
      (3) В живом дереве этих форм нет (0 находок). Касается вердикта запрета 16-09 №2 «или его привязки к журналу»,
      который уже «нарушен» через WR-08. Рекомендация: закрыть в том же проходе, что и WR-08, — добавить
      bind_threadlocal / tmp_bind в CONTEXT_BINDERS и разрешать псевдонимы ImportFrom, либо назвать случай псевдонима
      в «ГРАНИЦЕ СРЕДСТВА».
    evidence_status: "reproduced by verifier (predicate returned [] on 4 forms; controls caught)"
human_verification:
  - test: "Сверка вердиктов запретов (перенос пункта 2 прошлого раунда, расширенный): открыть раздел «Запреты (judgment-tier)» этого отчёта — 23 строки, планы 16-01…16-10"
    expected: >-
      Владелец согласен с каждым вердиктом: 19 строк «соблюдён» с названной уликой, 16-02 №2 «нарушен» (WR-06 —
      гэп 1), 16-09 №2 «нарушен» (WR-08 — гэп 3, с частью IN-06), 16-06 №1 «соблюдён в живом дереве, средство
      принуждения неполно (WR-08)», 16-10 №2 «соблюдён после восстановления 36b668d0»
    why_human: "Все запреты фазы judgment-tier со статусом flagged-unverified; вердикт LLM-судьи не авторитетен и молча в passed не засчитывается (ADR-550 D4)"
  - test: "Решение владельца по автопути (гэп 2, WR-07): принимать ли автоисточником значения с вердиктами TOO_LONG / INVALID_LENGTH и '+7 0…'"
    expected: >-
      Владелец называет исход заранее, исполнитель гэпа его воспроизводит: (а) — умолчание — отказ, normalize_reported('70123456789'),
      ('799912345678'), ('1234567890123') дают None, Fragment '88801234567' по-прежнему '+88801234567'; (б) принять, переписать
      абзац П-1 шапки на настоящее множество и записать overrides
    why_human: "Автопуть сознательно сделан мягче ручного (D-05, О-1: Fragment); где проходит граница «номер из мессенджера заведомо настоящий» — политика владельца, а не факт кода. Правдивость шапки нужна при любом исходе"
---

# Фаза 16: Хранение номера, нормализация и единый писатель — отчёт верификации (раунд 2)

**Цель фазы:** у аккаунта есть место для номера в каноническом виде E.164, записать туда номер можно только через один модуль, который не даёт автоматическому источнику затереть ручное значение — даже в гонке, — и номер не утекает в журналы
**Проверено:** 2026-10-09T17:03:15Z (HEAD `36b668d0`; код совпадает с `49347f53` — `git diff --name-only 49347f53..HEAD` даёт только файлы `.planning/`)
**Статус:** gaps_found
**Повторная верификация:** да, после партии закрытия гэпа 16-07…16-10. Прошлый раунд — 2026-10-08T20:54:43Z, `gaps_found`, 9/10

## Что изменилось с прошлого раунда

Все четыре пункта `missing` прошлого гэпа закрыты, и я проверил каждый сам: CR-01, WR-04, WR-03, а попутно и предупреждения WR-01, WR-02, WR-05. Пункт `human_verification` 1 закрыт решением владельца О-3 (а), и исход я воспроизвёл. Но правило критерия 3 «мусор отвергается» пробито в двух новых местах (WR-06, WR-07). Шапка гейта писателя снова обещает больше, чем видит предикат (WR-08). Договор `record_reported_phone` с Фазой 19 шире поведения (IN-07). Каждую находку ревью я воспроизвёл своим зондом, а не принял на слово.

## Достижение цели

### Наблюдаемые истины

| # | Истина | Статус | Улика |
|---|--------|--------|-------|
| 1 | Критерий 1: после `upgrade head` всё «неизвестно», `downgrade` до `0022` снимает обе колонки, `0023` за `0022`, `test_model_matches_head.py` расширен | ✓ VERIFIED (регрессия) | `alembic/` и `app/models/` не менялись с `225fd3c7` (`git diff --stat` пуст); `tests/test_migrations` в моём прогоне зелёные (в составе 421 passed). Ветка PostgreSQL вне объёма — деплой-гейт D-26 |
| 2 | Критерий 2: два аккаунта с одним номером сосуществуют; «ручной без номера» отвергает CHECK | ✓ VERIFIED (регрессия) | Те же файлы не менялись; `test_messenger_account_phone_check.py` и тест ревизии зелёные |
| 3 | Критерий 3, первая половина: названные написания сводятся к E.164 и показываются по-русски | ✓ VERIFIED | Мой зонд: `8 999 123-45-67`, `+7 (999) 123-45-67`, `79991234567` → `+79991234567`; `+7 701 123 4567` → `+77011234567`; автопуть `88801234567` → `+88801234567`, целое `79991234567` → `+79991234567`; `format_phone`: `+7 999 123-45-67`, `+7 701 123 4567`, `+888 01234567` |
| 4 | Критерий 3, вторая половина: мусор и слишком длинный ввод отвергаются, а не становятся «номером» (D-06) | ✗ FAILED | CR-01 и WR-04 закрыты: 6 входов CR-01 → отказ, 5 обрывков WR-04 → `None`. **WR-06** (ручной путь): `+7 999 123-45-67 1234` → `+799912345671234` под признаком «ручной». **WR-07** (автопуть): `70123456789` → `+70123456789`, `1234567890123` → `+1234567890123`. См. гэпы 1 и 2 |
| 5 | Критерий 3, третья часть: неразбираемый сохранённый номер показывается как есть | ✓ VERIFIED | `format_phone('+999123456')` → `+999123456`, `format_phone('garbage')` → `garbage` |
| 6 | Критерий 4: ручной номер переживает автозапись последовательно и в гонке; условный UPDATE; очистка `(NULL, false)`; отрицание реально краснеет | ✓ VERIFIED | `_fill_if_unknown` изменён планом 16-08, поэтому мутацию я повторил на нынешнем коде: плагин `-p mutate_rcw16` подменил `_fill_if_unknown` чтением-проверкой-записью, и `test_the_production_writer_keeps_the_manual_number_in_every_position` покраснел: «позиция 2: итог ('+79990000002', True), ручной номер затёрт». Без мутации — `4 passed`. Файл теста гонки не менялся с `225fd3c7` |
| 7 | Критерий 5: номер в строке журнала четырёх деревьев краснит гейт приватности; подложенная строка; только `phone_set` | ✓ VERIFIED (advisory IN-06) | Гейт зелёный (72 правила в составе 421 passed). Мой зонд: `structlog.contextvars.bind_contextvars(phone=…)` и голое `bind_contextvars(phone=…)` дают находку (прошлое WR-02 закрыто). Псевдоним ввоза, `bind_threadlocal`, `tmp_bind` и получатель с именем `lg` находку не дают — это IN-06, advisory |
| 8 | Цель: записать номер в колонку можно только через один модуль (D-12, D-13) — в живом дереве | ✓ VERIFIED | Мой греп `app/` и `scripts/`: вне `app/application/accounts/phone.py` записей `phone` / `phone_is_manual` нет. `app/pages/accounts.py:896` — `"phone": submitted` в контексте шаблона, `:837/:903/:938` — разметка и `start_session`. Гейт на живом дереве даёт 0, реестр — ровно модуль-писатель. Слепота средства принуждения — истина 18 |
| 9 | Маска D-10, чистота модуля, закрытые тексты отказа | ✓ VERIFIED | `mask_phone('+79991234567')` → `+7 *** ***-**-67`, `'+88812'` → `+888 ***`, `'+712'` → `+7 ***`. В `app/services/phone.py` нет ни `is_valid_number`, ни голого `is_possible_number(`. `PHONE_ERROR_MESSAGES` — 4 константы |
| 10 | План 16-01: суита записей зелёная без ослабления | ✓ VERIFIED (регрессия) | Мой прогон `uv run pytest tests/test_planning -q -p no:randomly` → `218 passed, 2 skipped` |
| 11 | 16-07: ручной `00…`, местный номер с ведущим 0 и `+7 0…` → `PHONE_ERROR_NOT_A_NUMBER`; вариант (б) не реализован; Италия и все прежние принятые строки и строки О-1 не тронуты; 4 текста, без валидатора | ✓ VERIFIED | `app/services/phone.py:172-173`. Мой зонд: 7 входов → отказ, `+39 06 1234 5678` → `+390612345678`, `+888 0123 4567` → отказ, `88801234567` → `+78801234567`, `8-800-555-35-35` → `+78005553535`. Проверка владельца дала исход (а), см. `re_verification` |
| 12 | 16-07: автопуть — граница 7, отказ `IS_POSSIBLE_LOCAL_ONLY`; Fragment, Ниуэ, Токелау приняты; строка `five_digits_lower_bound` перенесена с летописью | ✓ VERIFIED | `:63`, `:213-215`; `tests/test_services/test_phone.py:85, :115`. Зонд: 5 обрывков → `None`; `6831234`, `6901234`, `88801234567`, `888012345678` приняты |
| 13 | 16-07, истина 6: граница правила автопути названа в шапке, а не выдана за покрытие | ✗ FAILED (partial) | Шапка `:33-37` называет только «семизначный обрывок TOO_SHORT», а принимаются ещё TOO_LONG, INVALID_LENGTH, TOO_SHORT длиннее 7 цифр и `+7 0…` (замер — гэп 2, WR-07) |
| 14 | 16-08: `PhoneWrite.MISSING` на отсутствующей строке; проба `select(exists())` только после UPDATE с 0 строк — `[Update]` / `[Update, Select]`; `set_manual_phone` прежний с `LookupError`; писатель не коммитит и не присваивает | ✓ VERIFIED | `app/application/accounts/phone.py:105-120`. Мой прогон: `-k "missing_account_is_named_missing or existence_probe_runs_only or never_added_to_the_session"` → `3 passed`; правило порядка операторов утверждает поведение, а не наличие. Оба гейта зелёные с изменённым модулем |
| 15 | 16-08, истина 3: объект вне сессии → `ValueError(ACCOUNT_NOT_IN_SESSION)`, ноль операторов, `KEPT` не возвращается | ✗ FAILED (partial) | На разбираемом номере выполняется. На `None` / `''` / `'garbage'` мой зонд даёт `PhoneWrite.UNPARSEABLE` без исключения (IN-07, гэп 4) |
| 16 | 16-08: тест гонки и его отрицание не ослаблены | ✓ VERIFIED | `git diff --stat 225fd3c7 -- tests/test_application/test_account_phone_race.py` пуст; мутант убит (истина 6) |
| 17 | 16-09: пять форм WR-01 ловятся подложенными случаями; executemany по PK в синтетическом `scripts/` находится обходом; живое дерево — 0; законные места не краснят; реестры прежние | ✓ VERIFIED | Мой зонд: `execute(update(…), [{"id": 1, "phone": p}])` и `params=[…]` дают находку вида «ключ словаря строк». `PHONE_WRITER_EXCEPTIONS` — ровно модуль-писатель (`:144-148`). 48 правил гейта зелёные |
| 18 | 16-09, истина 5: шапка гейта писателя называет настоящую границу — литеральные формы ловятся, вне охвата только значения времени исполнения | ✗ FAILED | Девять литеральных форм дают `[]` (WR-08, гэп 3), при том что `:68` утверждает «Всё, что видно литералом в исходнике, ловится» |
| 19 | 16-09: гейт приватности судит `bind_contextvars` / `bound_contextvars` при любом получателе; живые привязки распознаны и чисты; реестр пуст, потолок 0 | ✓ VERIFIED (advisory IN-06) | `CONTEXT_BINDERS`, `_is_context_binding`; зонд выше; `PHONE_LOG_EXCEPTIONS = {}`, `PHONE_LOG_EXCEPTIONS_CEILING = 0` (`:117`, `:120`) |
| 20 | 16-10: 11 находок первого ревью разобраны (`fixed` — с существующим коммитом, `deferred` — с причиной и адресатом); IN-01 в STATE.md; реестр запретов согласован | ✓ VERIFIED | На `14e60e75` в диспозиции `open: 0`, `total: 11`. Все 8 исправляющих хешей — предки HEAD с темой `feat(16-0N)`. `.planning/STATE.md:739` — строка «Phase 16 → Phase 18» об IN-01. `prohibitions_census.py --check` → rc 0, «764 строк, биекция — согласие» (фаза 16 — 23 строки). Нынешняя диспозиция (`open: 5`, `total: 16`) — уже итог повторного ревью `7ad78670`, а не отступление 16-10. Строки IN-01…IN-05, потерянные проходом записи ревью, восстановлены `36b668d0` |

**Счёт:** 16/20 истин подтверждены (0 — присутствуют, но поведение не проверено). Провалены: 4, 13, 15, 18.

### Отложенное

Нет. Ни один гэп не покрывает поздняя фаза. Фаза 18 (критерий 2) лишь показывает текст отказа, который ей отдаёт нормализатор Фазы 16. Фаза 20 (критерий 2) тестирует условную запись собственного скрипта, но не чинит обещание сквозного гейта писателя. Гейт — артефакт Фазы 16.

### Advisory (новый объём, не блокирует)

| # | Находка | Категория | Почему advisory |
|---|---------|-----------|-----------------|
| 1 | IN-06: гейт приватности слеп к псевдониму ввоза привязки, к `bind_threadlocal` / `tmp_bind` и к получателю журнала с нестандартным именем (`lg.info(…, account.phone)`) | security | Воспроизведено. Блокером не считаю: шапка гейта приватности перечисляет распознаваемые имена явно и полного охвата не заявляет, D-17 сам задаёт гейт списком имён, в живом дереве таких форм нет. Рекомендую закрыть вместе с гэпом 3 |

### Требуемые артефакты

| Артефакт | Ожидается | Статус | Подробности |
|----------|-----------|--------|-------------|
| `alembic/versions/0023_messenger_account_phone.py` | ревизия `0023` | ✓ VERIFIED | не менялась с прошлого раунда |
| `app/models/messenger_account.py` | колонки и CHECK | ✓ VERIFIED | не менялась |
| `app/services/phone.py` | `RU_KZ_COUNTRY_CODE`, отказ CR-01, `REPORTED_MIN_DIGITS = 7`, отказ `LOCAL_ONLY`, порог маски, шапка с летописями | ⚠️ ЕСТЬ, С ГЭПОМ | Всё перечисленное есть и подключено (писатель его ввозит). Но правило отказа ручного пути неполно (WR-06), а шапка называет границу автопути уже настоящей (WR-07) |
| `app/application/accounts/phone.py` | `PhoneWrite.MISSING`, проба после UPDATE, `ACCOUNT_NOT_IN_SESSION` | ⚠️ ЕСТЬ, С ГЭПОМ | Проба и `MISSING` верны и закреплены. Проверка членства стоит после нормализации (IN-07). Продуктовых потребителей по замыслу нет: их заведут Фазы 18–20 |
| `tests/test_services/test_phone.py` | правила и строки 16-07 | ✓ VERIFIED | 133 правила; строк WR-06 / WR-07 нет — это гэпы 1–2 |
| `tests/test_application/test_account_phone_writer.py` | три правила 16-08 | ✓ VERIFIED | 17 правил; правило отказа не параметризовано мусором (гэп 4) |
| `tests/test_application/test_phone_single_writer_gate.py` | виды 6–7, `LITERAL_FORM_CASES`, шапка с границей | ✗ ПРЕДИКАТ УЖЕ ЗАЯВЛЕНИЯ | WR-08, гэп 3 |
| `tests/test_phone_privacy_gate.py` | `CONTEXT_BINDERS`, `_is_context_binding` | ✓ VERIFIED (IN-06) | — |
| `16-REVIEW-DISPOSITION.md` / `.planning/STATE.md` | диспозиция и строка IN-01 | ✓ VERIFIED | см. истину 20 |

### Проверка ключевых связей

| Откуда | Куда | Через что | Статус | Подробности |
|--------|------|-----------|--------|-------------|
| `set_manual_phone` | `normalize_manual` → `PhoneError` | прямой вызов до `session.execute` | WIRED | `app/application/accounts/phone.py:176` |
| `fill_reported_phone` / `record_reported_phone` | `normalize_reported` → `_fill_if_unknown` | прямой вызов | WIRED | `:129-132`, `:150-157`; у `record_reported_phone` порядок нормализации и проверки членства — гэп 4 |
| `_fill_if_unknown` | проба `select(exists())` | `session.execute` после UPDATE с `rowcount != 1` | WIRED | `:115-120`; порядок `[Update]` / `[Update, Select]` закреплён правилом |
| `run_interleaved` | боевой писатель и отрицание | один помощник | WIRED | Мутант нынешнего кода убит |
| `writer_sources(root)` | живое дерево и `tmp_path/scripts` | один обход | WIRED | `test_a_planted_bulk_update_by_primary_key_reddens_the_gate` зелёный |
| `python_log_calls` | `_is_context_binding` | отбор вызовов | WIRED | Привязки `app/middleware.py`, `app/worker/tasks.py` распознаны (app: 215 вызовов по SUMMARY 16-09) |

### Трассировка данных (уровень 4)

Неприменима: фаза ничего не отрисовывает. Сквозной путь «источник → нормализация → условный UPDATE → колонка → `format_phone`» прогнан тестами писателя.

### Поведенческие пробы

| Поведение | Команда | Результат | Статус |
|-----------|---------|-----------|--------|
| Модули фазы | `uv run pytest` по 7 модулям фазы и `tests/test_migrations` (quick run из VALIDATION) | `421 passed` за 9,9 с | ✓ PASS |
| Суита записей | `uv run pytest tests/test_planning -q -p no:randomly` | `218 passed, 2 skipped` | ✓ PASS |
| Перепись запретов | `uv run python scripts/prohibitions_census.py --check` | rc 0, 764 строки, биекция | ✓ PASS |
| Проверка владельца CR-01 | `uv run python -c "…normalize_manual('00 44 7911 123456')"` | exit 1, stdout пуст, stderr `…PhoneError: Не похоже на номер телефона. Пример: +7 999 123-45-67` | ✓ PASS (исход (а)) |
| Мутант гонки (критерий 4) | `-p mutate_rcw16` + один названный тест | `1 failed`: «позиция 2 … ручной номер затёрт» | ✓ PASS (мутант убит) |
| Правила 16-08 | `-k "missing_account_is_named_missing or existence_probe_runs_only or never_added_to_the_session"` | `3 passed` | ✓ PASS |
| WR-06 | `normalize_manual('+7 999 123-45-67 1234')` и ещё 3 входа | `+799912345671234`, `+799912345678901` ×2, `+788001234567890` | ✗ FAIL |
| WR-07 | `normalize_reported` на 10 входах | `+70123456789`, `+799912345678`, `+79991234567890`, `+1234567890123`, `+441234567890123`, `+123456789`, `+700447911123456`, `+799912345671234` | ✗ FAIL |
| WR-08 | `phone_write_offences` на 9 литеральных формах и 3 контролях | 9 × `[]`; контроли пойманы | ✗ FAIL |
| IN-06 | `python_log_offences` на 4 формах и 2 контролях | 4 × `[]`; контроли пойманы | ⚠️ WARN |
| IN-07 | `record_reported_phone` на объекте вне сессии | `None` / `''` / `'garbage'` → `UNPARSEABLE`; `'79991234567'` → `ValueError` | ✗ FAIL (partial) |

Полный прогон я не повторял, по указанию оркестратора: на `49347f53` он дал `4406 passed, 2 skipped, 0 failed`, а код с тех пор не менялся. Зонды лежат в scratchpad сессии (`probe16.py`, `gateprobe.py`, `in07.py`, `mutate_rcw16.py`) и в репозиторий не попали.

### Пробы

Неприменимо: планы и SUMMARY не объявляют `scripts/*/tests/probe-*.sh`.

### Покрытие требований

| Требование | План-источник | Описание | Статус | Улика |
|------------|---------------|----------|--------|-------|
| PHONE-01 | 16-02, 16-03, 16-05, 16-07 | номер в каноническом E.164 в отдельном поле, «неизвестен» — отдельное состояние, уникальности нет | ✗ ЧАСТИЧНО | Поле, состояние и отсутствие уникальности подтверждены (истины 1, 2). Каноничность по-прежнему нарушена: ручной путь кладёт в поле выдуманный 15-значный `+7…` (WR-06), автопуть — `+7 0…` и номера TOO_LONG (WR-07) |
| PHONE-02 | 16-05, 16-06, 16-08, 16-09 | ручной номер не затирается автоисточником, в том числе в гонке | ✓ SATISFIED (с гэпами средства) | Сама гарантия держится: истины 6, 8, 14, 16, мутант убит на нынешнем коде. Обещание гейта писателя шире предиката (гэп 3), договор `record_reported_phone` шире поведения (гэп 4). Это гэпы средств и договора, а не нарушение гарантии в коде сегодня |
| PHONE-21 | 16-02, 16-04, 16-07, 16-09 | номера не попадают в журналы, только маска или признак | ✓ SATISFIED (advisory IN-06) | Истины 7, 9, 19; порог маски WR-03 закрыт |
| `записи-старт-вехи` | 16-01 | псевдо-ID решения владельца 2026-10-08 | ✓ SATISFIED | Истина 10 |
| `диспозиция-ревью-16` | 16-10 | псевдо-ID решения владельца О-4 | ✓ SATISFIED | Истина 20 |

Осиротевших требований нет: REQUIREMENTS.md (`:84-85`, `:104`) отдаёт Фазе 16 ровно PHONE-01, PHONE-02 и PHONE-21, и каждое заявлено планами. Все три по-прежнему `Pending`, что верно при `gaps_found`.

### Найденные антипаттерны

| Файл | Строка | Шаблон | Серьёзность | Последствие |
|------|--------|--------|-------------|-------------|
| `app/services/phone.py` | 172-173 | у кода 7 отказ только при ведущем нуле, длина не проверяется (WR-06) | 🛑 Blocker | выдуманный 15-значный номер навсегда закрыт под «ручным» |
| `app/services/phone.py` | 33-37, 213-216 | шапка называет границу уже настоящей; автопуть хранит TOO_LONG / INVALID_LENGTH / `+7 0…` (WR-07) | 🛑 (гэп 2, partial) | ложная подпись аккаунта в Фазах 17–20, которую автоисточник уже не исправит |
| `tests/test_application/test_phone_single_writer_gate.py` | 63-68, 108-133, 299-313 | заявлен полный охват литералов, девять форм проходят (WR-08) | 🛑 Blocker (истина 16-09) | второй писатель Фазы 20 в форме comprehension / `parameters=` пройдёт гейт |
| `app/application/accounts/phone.py` | 144-156 | договор «узнаёт об ошибке сразу» шире поведения (IN-07) | 🛑 (гэп 4, partial) | забытый `session.add` молчит при старом воркере без номера |
| `tests/test_phone_privacy_gate.py` | 149, 237-239 | распознавание по последнему имени (IN-06) | ⚠️ Warning (advisory) | псевдоним привязки уводит номер в журнал незамеченным |
| `pyproject.toml` | 21 | точный пин (IN-02) | ℹ️ Info | отложено владельцем (О-4) |
| `scripts/prohibitions_census.py` | 398-402, 1334-1338 | падение на дробных фазах (IN-04) | ℹ️ Info | отложено владельцем (О-4) |

Маркеров `TBD` / `FIXME` / `XXX` / `TODO` / `HACK` / `PLACEHOLDER` в шести файлах, которые партия изменила, нет. IN-01, IN-03 и IN-05 отложены владельцем (О-4) с адресатами. Диспозиция переносит их с причинами, а этот отчёт заново их не судит.

### Запреты (judgment-tier, вердикт верификатора не авторитетен)

У всех 23 запретов фазы `status: flagged-unverified`. Ниже вердикт LLM-судьи с уликой. Флаг каждой строки: `unverified-prohibition — human review recommended` (human_verification 1).

| План | Запрет (кратко) | Вердикт | Улика |
|------|-----------------|---------|-------|
| 16-01 №1 | не ослаблять правила записей | соблюдён | `tests/test_planning`: 218 passed, 2 skipped |
| 16-01 №2 | не стирать числа без летописи | соблюдён | летописи `REQUIREMENT_ROWS_DECLARED`, `REGISTRY_HEADER` (прошлый раунд; файлы не менялись) |
| 16-01 №3 | не трогать продуктовый код | соблюдён | коммиты 16-01 не касаются `app/`, `alembic/`, воркеров |
| 16-02 №1 | не подставлять ввод в текст `PhoneError` | соблюдён | только константы `PHONE_ERROR_*`; новых текстов 16-07 не завёл |
| 16-02 №2 | не превращать мусор в «номер» (в т. ч. номер с добавочным) | **нарушен** | CR-01 закрыт, но WR-06: добавочный без маркера сохраняется как `+799912345671234` — гэп 1 |
| 16-03 №1 | нет уникального индекса | соблюдён | файлы не менялись, тест зелёный |
| 16-03 №2 | ревизия не заполняет номер | соблюдён | то же |
| 16-04 №1 | номер не попадает в журнал даже маской | соблюдён (с пропуском IN-06) | живое дерево: 0 нарушений |
| 16-04 №2 | реестр исключений не расширяется | соблюдён | `PHONE_LOG_EXCEPTIONS = {}`, потолок 0 |
| 16-05 №1 | автоисточник не затирает ручной номер | соблюдён | мутант нынешнего кода убит |
| 16-05 №2 | автономер не помечается ручным | соблюдён | `_fill_if_unknown` пишет только `phone` (`:112`) |
| 16-06 №1 | нет записи в обход писателя | соблюдён в живом дереве; средство неполно | греп и гейт: 0; пропуски гейта — WR-08 (гэп 3) |
| 16-06 №2 | реестр писателя — ровно модуль-писатель | соблюдён | `:144-148`, правило реестра зелёное |
| 16-07 №1 | не реализовывать вариант (б) «`00` как `+`» | соблюдён | `00 44 7911 123456` → отказ; кода переписывания нет |
| 16-07 №2 | без валидатора, без нового текста, 4 константы | соблюдён | греп `is_valid_number` пуст; `PHONE_ERROR_MESSAGES` — 4 |
| 16-07 №3 | не терять Fragment, Ниуэ, Токелау | соблюдён | зонд: `+88801234567`, `+888012345678`, `+6831234`, `+6901234` |
| 16-08 №1 | проба существования не перед записью | соблюдён | `:105-120`; правило порядка `[Update]` / `[Update, Select]` зелёное |
| 16-08 №2 | не ослаблять тест гонки | соблюдён | файл не менялся с `225fd3c7`; мутант убит |
| 16-09 №1 | не расширять реестры ради зелени | соблюдён | оба реестра прежние |
| 16-09 №2 | не выдавать слепоту предиката за границу средства | **нарушен** | WR-08: 9 литеральных форм проходят при заявлении полного охвата — гэп 3; часть «привязки к журналу» — IN-06 |
| 16-10 №1 | `fixed` только с существующим коммитом | соблюдён | 8 хешей — предки HEAD, темы `feat(16-0N)` |
| 16-10 №2 | не отбрасывать находку молча | соблюдён после восстановления | на `14e60e75` все 11 строк на месте. Проход записи повторного ревью потерял диспозиции IN-01…IN-05, `36b668d0` их вернул. Пять новых находок разобраны в этом отчёте |
| 16-10 №3 | не править формулировки после засева | соблюдён | `--check` rc 0; правило отпечатка в `tests/test_planning` зелёное |

### Новые находки повторного ревью: куда легла каждая

| Находка | Воспроизведена | Куда легла | Почему |
|---------|----------------|------------|--------|
| WR-06 | да, 4 входа | **гэп 1** (blocker) | бьёт по критерию 3 / D-06 и запрету 16-02 №2; тот же класс вреда, что CR-01 (закрыто под «ручным» навсегда); чинится признаком разбора без пересмотра D-05 |
| WR-07 | да, 10 входов | **гэп 2** (partial) + human_verification 2 | бьёт по критерию 3 («слишком длинный ввод отвергается») и по истине 6 плана 16-07 (граница названа неверно); где проходит мягкость автопути — решение владельца, умолчание — отказ |
| WR-08 | да, 9 форм | **гэп 3** (blocker) | бьёт по истине 5 плана 16-09 и запрету 16-09 №2; сужать заявление шапки этот запрет не даёт |
| IN-06 | да, 4 формы | **advisory** | истина 16-09 выполнена по букве, шапка гейта приватности полного охвата не заявляет, в живом дереве форм нет; рекомендовано закрыть вместе с гэпом 3 |
| IN-07 | да | **гэп 4** (partial) | безусловная истина 3 плана 16-08 неверна на достижимом пути; мелкая правка порядка либо запись overrides на суженный договор |
| IN-01…IN-05 | — | отложены владельцем (О-4) | диспозиция с причинами и адресатами, восстановлена `36b668d0` |

### Нужна проверка человеком

#### 1. Сверка вердиктов запретов (перенос пункта 2 прошлого раунда)

**Проверка:** таблица «Запреты» выше, 23 строки.
**Ожидается:** владелец согласен с каждым вердиктом. Две строки «нарушен» (16-02 №2, 16-09 №2) совпадают с гэпами 1 и 3.
**Почему человек:** запреты judgment-tier, вердикт LLM не авторитетен.

#### 2. Решение владельца по мягкости автопути (гэп 2, WR-07)

**Проверка:** назвать исход до исполнения гэпа, затем сверить: `normalize_reported('70123456789')`, `('799912345678')`, `('1234567890123')`, а для контроля `('88801234567')`.
**Ожидается:** (а), по умолчанию: `None`, `None`, `None`, `'+88801234567'`. Либо (б): значения принимаются, абзац П-1 шапки переписан на настоящее множество, отступление записано в `overrides`.
**Почему человек:** автопуть сознательно мягче ручного (D-05, О-1), и где проходит граница доверия источнику — политика владельца.

Пункт 1 прошлого раунда (префикс `00`, CR-01) закрыт решением владельца О-3 (а) и моим воспроизведением исхода — см. `re_verification.previous_round.human_verification_disposition`.

### Сводка гэпов

**Две причины, четыре гэпа.**

**Причина А — правило «мусор отвергается» (критерий 3, D-06) закрыто не до конца.** Партия закрыла ровно те входы, которые назвал прошлый гэп, но не весь класс.
1. **Гэп 1, WR-06 (блокер).** RU-метаданные допускают 14-значную национальную часть, поэтому номер `+7` с четырьмя лишними цифрами (добавочный без маркера) сохраняется как «ручной» `+799912345671234`. Докстринг 16-07 называет причину («10 и 14 цифр»), но закрыт только поднабор с ведущим нулём. Я сам пропустил этот случай в прошлом раунде: проверял только `00` и ведущий ноль. Починка — признак разбора (длина национальной части у кода 7), D-05 не задевает.
2. **Гэп 2, WR-07 (partial).** Автопуть хранит TOO_LONG, INVALID_LENGTH и `+7 0…`, а шапка модуля называет единственной границей семизначный TOO_SHORT. Общее правило «код 7 → ровно 10 национальных цифр, без ведущего нуля» закрывает часть гэпа 2 вместе с гэпом 1. TOO_LONG и INVALID_LENGTH у прочих кодов требуют решения владельца (human_verification 2).

**Причина Б — средства и договоры фазы обещают больше, чем делают.**
3. **Гэп 3, WR-08 (блокер по истине 16-09).** Шапка гейта писателя второй раз заявляет «всё литеральное ловится», и второй раз это неверно: девять форм, включая самые вероятные для скрипта Фазы 20 (`parameters=`, список словарей в comprehension), проходят. Живое дерево сегодня чисто, поэтому сама гарантия PHONE-02 держится, но её страж для Фаз 18–20 дыряв. IN-06 (advisory) — родственная слепота гейта приватности, её разумно закрыть тем же проходом.
4. **Гэп 4, IN-07 (partial).** `record_reported_phone` громко падает на объекте вне сессии только при разбираемом номере. Правка — перенос проверки до нормализации и параметризация теста.

**Планировщику гэпов:** REVIEW.md он не читает, поэтому всё нужное для четырёх гэпов уже лежит в `gaps[].missing`. Строки таблиц, которые нужно добавить, названы поимённо. Урок «тесты фазы закрепляют дефекты» здесь работает в обратную сторону: строк WR-06 / WR-07 в таблицах нет вовсе, поэтому починка ничего не переписывает, а только добавляет.

**Вне объёма (не гэп):** ветка PostgreSQL ревизии `0023`, READ COMMITTED и `rowcount` на asyncpg (деплой-гейт D-26). `/gsd-secure-phase 16` не запускался, `16-SECURITY.md` нет.

---

_Проверено: 2026-10-09T17:03:15Z_
_Верификатор: Claude (gsd-verifier)_
