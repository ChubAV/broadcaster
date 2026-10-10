---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
verified: 2026-10-10T07:08:40Z
status: gaps_found
score: 27/30 must-haves verified
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
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-11-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-11-SUMMARY.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-12-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-12-SUMMARY.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-13-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-13-SUMMARY.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-14-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-14-SUMMARY.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-15-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-15-SUMMARY.md"
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
covered_digest: "v3:sha256:78f0cbcfb38e09766d843c81cc73cc9f69349dfb8aef0e663da2f087ba45a64f"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 16/20
  previous_round:
    verified: 2026-10-09T17:03:15Z
    status: gaps_found
    score: 16/20 must-haves verified
    covered_digest: "v3:sha256:b9992c0cb015c213134cfb6aa18b54efa50d0888aa56a95f893116830882eacf"
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
    advisory_disposition:
      - finding: "IN-06"
        disposition: discharged
        evidence: >-
          Решение владельца О-6 «закрыть в этом проходе», 2026-10-09 (16-RESEARCH.md). Закрыто планом 16-13, GREEN 3bd2e6a0,
          58550bb3 (оба — предки HEAD 9ecf63bf). Мой зонд 2026-10-10: python_log_offences на всех четырёх формах прошлого
          раунда (псевдоним bind_ctx, structlog.threadlocal.bind_threadlocal, with tmp_bind(logger, phone=…),
          lg = logging.getLogger(); lg.info(…, account.phone)) даёт находку. Остаток того же семейства — новая IN-09 (гэп 3 этого отчёта)
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
    human_verification_disposition:
      - item: "1. Сверка вердиктов запретов (judgment-tier)"
        disposition: still_required
        evidence: >-
          Акт владельца, машиной не решается. Перенесён в human_verification 1 этого отчёта и расширен: 23 запрета планов
          16-01…16-10 плюс 12 запретов партии 16-11…16-15 (перепись: фаза 16 — 35 строк; `prohibitions_census.py --check`
          rc 0, «776 строк, биекция с переписью — согласие»), у каждого вердикт верификатора с уликой.
      - item: "2. Решение владельца по автопути (гэп 2, WR-07)"
        disposition: discharged
        evidence: >-
          Решение владельца О-5 (а) «отказ», 2026-10-09, второй прогон /gsd-plan-phase 16 --gaps (16-RESEARCH.md §«Вопросы
          владельцу второго прогона закрытия гэпа»). Исход назван до исполнения, и код даёт ровно его. Мой зонд 2026-10-10:
          normalize_reported('70123456789') → None, ('799912345678') → None, ('1234567890123') → None, контроль
          ('88801234567') → '+88801234567'. Правило test_the_auto_path_refuses_what_the_owner_named_before_execution
          (tests/test_services/test_phone.py:187) утверждает тот же список [None, None, None, '+88801234567'] и зелено
          (в составе 559 passed). Вариант (б) не реализован: записи overrides нет, а TOO_LONG / INVALID_LENGTH отвергаются
          (REPORTED_REFUSED_VERDICTS, app/services/phone.py:86-92, :287-288).
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
  gaps_closed:
    - "Гэп 1 раунда 2 (WR-06): app/services/phone.py:110 RU_KZ_NATIONAL_DIGITS = 10, общий предикат _is_impossible_zone_seven (:159-176), отказ ручного пути (:237-238); GREEN 02d73c93. Мой зонд: '+7 999 123-45-67 1234', '8 999 123 45 67 8901', '89991234567 8901', '8 800 123 45 67 890', а также найденные планированием '8 999 123-45-67 123', '8 800 555-35-35 123' и '+7 999 123-45-678' — отказ PHONE_ERROR_NOT_A_NUMBER. Перебор 4 основы × 1…5 лишних цифр — 20 зелёных случаев test_a_number_with_extra_digits_typed_by_hand_is_refused_whatever_their_count. Принятые написания прежние: '8 999 123-45-67', '+7 (999) 123-45-67', '79991234567', '+7 701 123 4567', '8 701 123 4567', '8-800-555-35-35', '+39 06 1234 5678', '88801234567' → '+78801234567'. Тот же класс у других кодов стран — новая WR-09 (гэп 1 этого отчёта)"
    - "Гэп 2 раунда 2 (WR-07): REPORTED_REFUSED_VERDICTS (:86-92) и общий предикат у автопути (:285-288); GREEN 2565d515; исход владельца О-5 (а) воспроизведён (см. previous_round.human_verification_disposition 2). Мой зонд: '79991234567890', '441234567890123', '700447911123456', '799912345671234', '7999123' → None. Fragment строкой и целым, Ниуэ, Токелау, Узбекистан, Казахстан приняты. Мой повтор перебора: 1935 входов, принято 583 TOO_SHORT и 558 IS_POSSIBLE, ни одного отвергнутого вердикта. Число 583 совпадает с шапкой (:37-45). Неточность формулировки абзаца — advisory IN-08"
    - "Гэп 3 раунда 2 (WR-08): GREEN f10abdd7, 2ccdb4d2, 6c862686, e168d3dd. Мой зонд: все девять литеральных форм прошлого раунда (parameters=, comprehension, генератор, values([… for …]), кавычки у колонки и у таблицы, префикс схемы, ordered_values, object.__setattr__) дают ровно одну находку. Заявление «Всё, что видно литералом…» осталось только летописью (test_phone_single_writer_gate.py:120-129). Новое заявление «через механизм» снова шире предиката — WR-10 (гэп 2 этого отчёта)"
    - "Гэп 4 раунда 2 (IN-07): app/application/accounts/phone.py:164-165 — проверка членства до normalize_reported; GREEN 164a0276, страж 1fad15e3. Мой зонд: None / '' / 'garbage' / '79991234567' на объекте вне сессии → ValueError(ACCOUNT_NOT_IN_SESSION), 0 операторов, id None. Объект чужой AsyncSession() → тот же отказ, 0 операторов. Правило параметризовано четырьмя входами (4 passed). Мелкие неточности теста и текста — advisory IN-10"
    - "Advisory IN-06 раунда 2: закрыто 3bd2e6a0, 58550bb3 (О-6) — см. previous_round.advisory_disposition; остаток — IN-09 (гэп 3 этого отчёта)"
  gaps_remaining:
    - "Критерий 3, вторая половина (D-06): у кода 7 класс «номер плюс лишние цифры» закрыт, у других кодов — нет (WR-09, ручной путь). Нужно решение владельца (human_verification 2)"
    - "Правдивость шапок гейтов: заявление гейта писателя «через механизм» шире предиката в третий раз (WR-01 → WR-08 → WR-10), граница гейта приватности не называет две опознаваемые формы (IN-09)"
  regressions: []
gaps:
  - truth: "Критерий 3, вторая половина (D-06): мусор и слишком длинный ввод отвергаются, а не становятся «номером» — ручной путь вне кода 7 (WR-09)"
    status: partial
    reason: >-
      WR-09 воспроизведён моим зондом (normalize_manual, phonenumberslite 9.0.41). Настоящий мобильный номер с лишними
      цифрами, дописанными без маркера добавочного, сохраняется как выдуманный «ручной» номер: Беларусь
      '+375 29 123 45 67 1' → '+3752912345671' и '… 12' → '+37529123456712'; Украина '+380 50 123 4567 1' →
      '+3805012345671'; Киргизия '+996 700 123 456 1' → '+9967001234561'; Турция '+90 532 123 45 67 12' →
      '+90532123456712' и '… 123' → '+905321234567123' (при этом +1 цифра получает отказ, правило немонотонно, как
      WR-06 раунда 2); Израиль +1…+3 приняты; Китай '+86 138 0013 8000 1' → '+86138001380001'; Германия +1, +2 приняты.
      Это тот же класс вреда, за который раунд 2 открыл гэп 1: номер, которого не бывает, сохраняется под
      phone_is_manual=true и закрыт для автоисправления (D-07); запрет 16-02 №2 прямо называет «номер с добавочным».
      План 16-11 закрыл класс только у кода 7 (_is_impossible_zone_seven, app/services/phone.py:172-173 возвращает False
      для любого другого кода). Истины плана 16-11 сформулированы для России, Казахстана и 8-800 и выполнены. Но ни код,
      ни докстринг эту границу не называют: пункт 5 (:193-213) объясняет ограничение кодом 7 только для половины про
      ведущий ноль («у Италии +39 06 … ведущий ноль законен»). А строка WR-06 в 16-REVIEW-DISPOSITION.md говорит
      «класс «номер плюс лишние цифры» закреплён перебором» — шире кода. Беларусь и Украина — самые вероятные не-RU
      номера у пользователей продукта. Буква D-05 («parse → is_possible_number → E.164») такой ввод пропускает. Значит,
      как далеко ручной путь вправе отходить от буквы D-05 у чужих кодов, решает владелец (human_verification 2).
      При любом его выборе нужна правка: либо отказ, либо названная граница.
    artifacts:
      - path: "app/services/phone.py"
        issue: "normalize_manual (:237-240): кроме кода 7 судится только общая «возможность» (IS_POSSIBLE), которая берёт объединение длин всех типов номеров и поэтому допускает лишние цифры там, где какой-либо тип (бесплатный, платный) длиннее мобильного; пункт 5 докстринга (:193-213) границу «только код 7» для лишних цифр не называет"
      - path: "tests/test_services/test_phone.py"
        issue: "EXTRA_DIGIT_BASES (:512-517) — только основы +7 (Россия, 8-800, Казахстан); строк BY / UA / TR в MANUAL_REJECTED нет, поэтому суита дефекта не видит"
    missing:
      - "По умолчанию (а), если владелец его подтвердит: в normalize_manual после проверки кода 7 требовать, чтобы номер был возможен хотя бы для одного типа, каким бывает аккаунт мессенджера: MOBILE, FIXED_LINE, FIXED_LINE_OR_MOBILE, VOIP — через phonenumbers.is_possible_number_for_type_with_reason == IS_POSSIBLE. Это проверка длин, без is_valid_number, D-05 соблюдён. TOLL_FREE не включать по тому же доводу, что RU_KZ_NATIONAL_DIGITS: бесплатный номер аккаунтом не бывает. Мой замер правила: отказ для BY +1/+2, UA +1, TR +2/+3, IL +1, CN +1; приняты '8 999 123-45-67', '8-800-555-35-35', '+39 06 1234 5678', '+7 701 123 4567'"
      - "Германия '+49 151 23456789 1' и '… 12' остаются принятыми и при правиле (а): у DE переменная длина FIXED_LINE. Утверждение ревью «This refuses every +1/+2 row in the table above» для DE неверно. Остаток назвать в пункте 5 докстринга как границу, строкой таблицы нормой не утверждать"
      - "Строки EXTRA_DIGIT_BASES (или MANUAL_REJECTED) для BY, UA, TR (и IL, CN); правило-сторож: каждый номер-образец метаданных 9.0.41 типов MOBILE / FIXED_LINE / FIXED_LINE_OR_MOBILE / VOIP по всем регионам ручной путь принимает в международной записи; все прежние строки MANUAL_ACCEPTED не перевёрнуты"
      - "Если владелец выберет (б) «принимать как сейчас»: назвать в пункте 5 докстринга normalize_manual границу «правило лишних цифр — только у кода 7; у прочих кодов номер с лишними цифрами сохраняется, если его длина возможна для какого-либо типа», с примером BY; сузить формулировку строки WR-06 в 16-REVIEW-DISPOSITION.md до «код 7»; записать overrides на эту истину"
  - truth: "Шапка гейта единственного писателя называет настоящую границу и не выдаёт слепоту предиката за неё (истина 6 плана 16-12; истина 5 плана 16-09; запреты 16-09 №2 и 16-12 №2; D-13) — WR-10"
    status: failed
    reason: >-
      WR-10 воспроизведён: phone_write_offences(…, 'scripts/x.py') вернул [] на пяти формах, каждая из которых
      называет колонку номера литералом в аргументе самого пишущего вызова:
      `session.query(MessengerAccount).filter_by(id=i).update(values={"phone": x})` (сигнатура Query.update в
      SQLAlchemy 2.0.46 — (self, values, synchronize_session, update_args));
      `set_attribute(account, key="phone", value=x)`; `set_committed_value(account, key="phone", value=x)`;
      `await session.run_sync(Session.bulk_update_mappings, MessengerAccount, [{"id": 1, "phone": p}])`;
      `update(MessengerAccount).values(**{"phone": n for n in [x]})` (ключ литеральный, а не вычисленный).
      На SQLite в памяти я проверил, что первые три формы и bulk_update_mappings действительно пишут колонку:
      '+71', '+72', '+73' сохранились. Шапка (tests/test_application/test_phone_single_writer_gate.py:96-118)
      заявляет: «Ловится всякая запись, в которой колонка номера … названа литералом в самом пишущем вызове, в его
      аргументе-контейнере». Ни одна из пяти форм не подпадает под пять названных недостижимых форм: (1) — значение
      именем или вычисленный ключ; (4) — API без имени или под чужим псевдонимом, а Session.bulk_update_mappings
      назван литерально. Значит, по собственному правилу шапки (:116-118) это слепота предиката, а не граница средства.
      Это третий повтор: WR-01 (2026-10-08) → WR-08 (2026-10-09) → WR-10. Каждый раз набор уже, но заявление шапки
      всякий раз шире предиката. run_sync — естественный путь к синхронному bulk-API из асинхронного кода, а проект
      асинхронный целиком; для скрипта Фазы 20 эта форма правдоподобна. Живое дерево чисто (гейт: 0 находок; мой греп
      app/ и scripts/ записей вне модуля-писателя не находит), поэтому цель «записать номер можно только через один
      модуль» сегодня выполняется. Не выполнено обещание средства, на которое опираются Фазы 18–20.
    artifacts:
      - path: "tests/test_application/test_phone_single_writer_gate.py"
        issue: "ветка update/values судит только позиционный аргумент, именованный values= не судится; NAMED_ATTRIBUTE_WRITERS (:175, :413-431) судятся только по позиции, key= не судится; строки ROW_MAPPING судятся, лишь когда имя самого вызова — execute / bulk_* (run_sync(Session.bulk_update_mappings, …) проходит); _literal_mappings (:520) не отдаёт ast.DictComp с литеральным ключом; шапка :96-118 заявляет охват через механизм"
    missing:
      - "values= именованным аргументом у update(...) / Query.update(...) судить через _literal_mappings"
      - "у NAMED_ATTRIBUTE_WRITERS судить и именованный key= (и name= у setattr-подобных), если его значение — константа из PHONE_COLUMNS"
      - "вызов, позиционный аргумент которого — Name / Attribute с последним именем из ROW_MAPPING_CALL_NAMES (форма run_sync(Session.bulk_update_mappings, …)), судить по остальным позиционным аргументам как по строкам"
      - "_literal_mappings / _mapping_phone_keys: ast.DictComp, у которого key — константа из PHONE_COLUMNS"
      - "Каждую из пяти форм — строкой LITERAL_FORM_CASES с ожидаемым видом; живое дерево — по-прежнему 0, реестр — ровно модуль-писатель"
      - "Чтобы не открыть четвёртый круг: планировщику перебрать сигнатуры каждого судимого API (inspect.signature в SQLAlchemy 2.0.46: Query.update, Update.values, set_attribute, set_committed_value, Session/Connection.execute, bulk_*_mappings, run_sync) и для каждого позиционного параметра, который судится, судить и его именованную форму; найденные формы — строками LITERAL_FORM_CASES. Список ревью — не перечень всего"
      - "Сузить заявление шапки шестой «недостижимой» формой нельзя без решения владельца: эти формы синтаксически достижимы, а запрет 16-09 №2 запрещает выдавать слепоту предиката за границу средства"
  - truth: "Граница гейта приватности названа: что вне охвата, перечислено в «ГРАНИЦЕ СРЕДСТВА», а журнал, опознаваемый по фабрике, имени журнала или ввозу, распознаётся (истины 3 и 5 плана 16-13; D-17; О-6) — IN-09"
    status: partial
    reason: >-
      IN-09 воспроизведён: python_log_offences(…, 'app/x.py') вернул [] на формах
      `from logging import info; info("n=%s", account.phone)`, `from logging import warning as warn_; warn_(…, account.phone)`,
      `class S: lg = structlog.get_logger()` с вызовом `self.lg.info("x", phone=account.phone)` и с `cls.lg.warning(…)`,
      а также `if (lg := logging.getLogger()): lg.info(account.phone)`. Контроли в том же прогоне ловятся: `self.lg = structlog.get_logger()`
      в __init__, `lg = logging.getLogger()` на уровне модуля, псевдоним bind_ctx, bind_threadlocal, tmp_bind.
      Шапка (tests/test_phone_privacy_gate.py:100-128) обосновывает каждый пункт границы одним доводом: журнал
      «нельзя опознать ни по фабрике, ни по имени журнала, ни по ввозу». А обе формы как раз опознаются: первая — ввозом
      функции модуля logging (шапка сама относит к охвату «тот же logging.* … под другим именем»), вторая — связыванием
      с фабрикой в теле класса. Ни одна не поймана и ни одна не названа в границе. Это тот же изъян, что WR-10, только
      в другом гейте: заявление шапки шире предиката. Ревью дало находке уровень info. Вред мал: в живом дереве этих
      форм нет (0 находок, прежние 215/68/89 вызовов). Но истина 5 плана 16-13 («что осталось вне охвата, названо»)
      буквально неверна.
    artifacts:
      - path: "tests/test_phone_privacy_gate.py"
        issue: "module_log_names (:295-338): ввоз ImportFrom считается получателем, только если имя похоже на журнал (:307-313), функции logging из LOG_METHODS не распознаются; Assign в теле класса кладёт имя в receiver_names, а вызов self.lg / cls.lg сверяется только с receiver_attributes (:335-345); NamedExpr не собирается; «ГРАНИЦА СРЕДСТВА» (:100-128) этих форм не называет"
    missing:
      - "Имена, ввезённые ImportFrom из модуля logging и входящие в LOG_METHODS (и их псевдонимы), — голые вызовы журнала"
      - "Связывание получателя в теле класса (Assign / AnnAssign) добавлять и в receiver_attributes — вызов self.lg / cls.lg"
      - "NamedExpr с фабрикой — поймать или назвать в «ГРАНИЦЕ СРЕДСТВА» с причиной"
      - "Строки POSITIVE_CONTROLS для каждой формы; живые деревья — прежние 215/68/89 вызовов и 0 находок; PHONE_LOG_EXCEPTIONS = {}, потолок 0"
      - "Назвать формы в границе вместо поимки можно только с правдивой причиной: довод «нельзя опознать ни по фабрике, ни по имени, ни по ввозу» к ним не подходит"
advisory:
  - finding: "IN-08: абзац границы автопути (app/services/phone.py:37-45) начинается словами «Кроме настоящих номеров автопуть принимает ЛЮБОЕ … TOO_SHORT», и читатель решит, что каждое принятое IS_POSSIBLE-значение — настоящий номер. В том же переборе 400 из 558 принятых IS_POSSIBLE-значений метаданные считают недействительными ('+72345678901', '+2023456789', '+2723456'); вне перебора '10000000000' → '+10000000000', '440000000000' → '+44000000000'"
    category: other
    reason: >-
      Воспроизведено моим повтором перебора: 1935 входов, принято 583 TOO_SHORT и 558 IS_POSSIBLE, из них 400 не проходят
      is_valid_number. Блокером не считаю. Исход владельца О-5 (а) код даёт ровно: отвергнуты код 7 и вердикты TOO_LONG /
      INVALID_LENGTH. Отказ от валидатора «действительности» — запертое решение D-05, и шапка того же модуля его прямо
      называет (абзац «ПОЧЕМУ ВАЛИДАТОР «ДЕЙСТВИТЕЛЬНОСТИ» НОМЕРА НЕ ПРИМЕНЯЕТСЯ ВОВСЕ»). Скрытой границы нет, есть
      неточное слово. Асимметрия «'+7 0…' отвергается, '+1 0…' хранится» — следствие О-5 (а), которое владелец сформулировал
      именно для кода 7. Рекомендация: переписать как «кроме номеров, которые метаданные считают возможными (в том числе
      недействительных — D-05) …» и привести рядом замер 400/558. Закрыть заодно с гэпом 1, в том же файле
    evidence_status: "reproduced by verifier (enumeration re-run: 583 TOO_SHORT, 558 IS_POSSIBLE, 400 invalid)"
  - finding: "IN-10: случай «объект другой сессии» в record_reported_phone не закреплён тестом, и причина в докстринге теста ложна; текст ACCOUNT_NOT_IN_SESSION даёт для этого случая неверный совет"
    category: other
    reason: >-
      Воспроизведено. Докстринг test_recording_an_account_outside_this_session_raises
      (tests/test_application/test_account_phone_writer.py:369-394) говорит: «вторая сессия к базе :memory: в фикстуре
      не гарантирована». Но проверке членства база не нужна. Мой зонд: other = AsyncSession() без привязки,
      other.add(account), затем record_reported_phone(db_session, account, '79991234567') → ValueError(ACCOUNT_NOT_IN_SESSION),
      0 операторов. Параметризация ["detached"] — один случай под видом матрицы. Совет текста «добавьте его через
      session.add» для объекта чужой сессии не работает: мой зонд даёт InvalidRequestError. Тот же текст поднимается и
      второй линией после flush (app/application/accounts/phone.py:171-172), где объект уже в сессии. Само поведение
      истины 3 плана 16-14 верно, и я наблюдал его прямым прогоном, поэтому это не гэп. Рекомендация: строка "foreign"
      в параметризации; нейтральный текст, например «аккаунт не принадлежит сессии писателя»; второй линии — свою
      закрытую константу, например «после flush у аккаунта нет id». Закрыть в любом проходе, где правится писатель
    evidence_status: "reproduced by verifier (foreign-session probe raised with 0 statements; session.add on foreign object raised InvalidRequestError)"
human_verification:
  - test: "Сверка вердиктов запретов (перенос пункта 1 раунда 2, расширенный): открыть раздел «Запреты (judgment-tier)» этого отчёта — 35 строк, планы 16-01…16-15"
    expected: >-
      Владелец согласен с каждым вердиктом. 31 строка «соблюдён» с названной уликой. 16-02 №2 «нарушен» (WR-09, гэп 1;
      часть WR-06 закрыта). 16-09 №2 «нарушен» (WR-10, гэп 2; часть про привязку к журналу — IN-09, гэп 3). 16-06 №1 и
      16-04 №1 «соблюдён в живом дереве, средство неполно». 16-15 №2 «соблюдён на коммите плана; позднее инструмент
      ревью дописал метку (not in the current review)»
    why_human: "Все запреты фазы judgment-tier со статусом flagged-unverified; вердикт LLM-судьи не авторитетен и молча в passed не засчитывается (ADR-550 D4)"
  - test: "Решение владельца по ручному вводу номера чужой зоны с лишними цифрами (гэп 1, WR-09): отвергать ли ручным путём номер, длина которого возможна лишь для типа, каким аккаунт мессенджера не бывает"
    expected: >-
      Владелец называет исход до исполнения, исполнитель гэпа его воспроизводит. (а) Отказ по типам аккаунта
      (MOBILE, FIXED_LINE, FIXED_LINE_OR_MOBILE, VOIP): normalize_manual('+375 29 123 45 67 1') и ('+380 50 123 4567 1')
      поднимают PhoneError с PHONE_ERROR_NOT_A_NUMBER; контроли '+375 29 123 45 67' → '+375291234567',
      '+380 50 123 4567' → '+380501234567', '8-800-555-35-35' → '+78005553535'; Германия с лишними цифрами названа
      границей. (б) Принимать как сейчас: граница «только код 7» названа в пункте 5 докстринга, строка WR-06 диспозиции
      сужена, отступление записано в overrides
    why_human: "D-05 — запертое решение («parse → is_possible_number → E.164»), и правило (а) отходит от его буквы сильнее, чем правило кода 7. Это новая политика: какие типы номеров считать аккаунтом, и риск ложного отказа настоящему номеру при отставании метаданных. Выбор между ложным отказом и выдуманным «ручным» номером — решение владельца, а не факт кода"
---

# Фаза 16: Хранение номера, нормализация и единый писатель — отчёт верификации (раунд 3)

**Цель фазы:** у аккаунта есть место для номера в каноническом виде E.164, записать туда номер можно только через один модуль, который не даёт автоматическому источнику затереть ручное значение — даже в гонке, — и номер не утекает в журналы
**Проверено:** 2026-10-10T07:08:40Z (HEAD `9ecf63bf`; код совпадает с `719555b7`: `git diff --name-only 719555b7..HEAD` вне `.planning/` пуст)
**Статус:** gaps_found
**Повторная верификация:** да, после партии закрытия гэпа раунда 2 (16-11…16-15). Прошлый раунд — 2026-10-09T17:03:15Z, `gaps_found`, 16/20

## Что изменилось с прошлого раунда

Все четыре гэпа раунда 2 закрыты, и каждый я проверил сам, своим зондом, а не по SUMMARY:
- WR-06: `+7` с лишними цифрами получает отказ, класс закреплён перебором 4×5;
- WR-07: исход владельца О-5 (а) воспроизведён буква в букву;
- WR-08: девять литеральных форм ловятся;
- IN-07: забытый `session.add` падает громко на любом входе.

Advisory IN-06 тоже закрыт (О-6). Пункт `human_verification` 2 раунда 2 закрыт решением владельца О-5 (а), и исход я воспроизвёл.

Повторное ревью нашло пять новых находок. Каждую я воспроизвёл. Три из них оставляют фазу в `gaps_found`:
- **WR-09.** Класс вреда WR-06 жив у кодов стран, отличных от 7. Нужно решение владельца.
- **WR-10.** Заявление шапки гейта писателя шире предиката в третий раз.
- **IN-09.** Граница гейта приватности не называет две формы, которые сама же считает опознаваемыми.

IN-08 и IN-10 легли в advisory.

## Достижение цели

### Наблюдаемые истины

| # | Истина | Статус | Улика |
|---|--------|--------|-------|
| 1 | Критерий 1: после `upgrade head` всё «неизвестно», `downgrade` до `0022` снимает обе колонки, `0023` за `0022`, `test_model_matches_head.py` расширен | ✓ VERIFIED (регрессия) | `alembic/`, `app/models/`, `tests/test_migrations/` не менялись с `36b668d0` (`git diff --stat` пуст). В моём прогоне `tests/test_migrations` зелёные (в составе 559 passed). Ветка PostgreSQL вне объёма — деплой-гейт D-26 |
| 2 | Критерий 2: два аккаунта с одним номером сосуществуют; «ручной без номера» отвергает CHECK | ✓ VERIFIED (регрессия) | Те же файлы не менялись; `test_messenger_account_phone_check.py` зелёный |
| 3 | Критерий 3, первая половина: названные написания сводятся к E.164 и показываются по-русски | ✓ VERIFIED | Мой зонд: `8 999 123-45-67`, `+7 (999) 123-45-67`, `79991234567` → `+79991234567`; `+7 701 123 4567` и `8 701 123 4567` → `+77011234567`; автопуть `79991234567` (целое) → `+79991234567`, `88801234567` → `+88801234567`; `format_phone`: `+7 999 123-45-67`, `+7 701 123 4567`, `+888 01234567` |
| 4 | Критерий 3, вторая половина: мусор и слишком длинный ввод отвергаются, а не становятся «номером» (D-06) | ✗ FAILED (partial) | Код 7 и автопуть закрыты (истины 21–24). Но у других кодов ручной путь хранит номер с лишними цифрами под признаком «ручной»: `+375 29 123 45 67 1` → `+3752912345671`, `+380 50 123 4567 1` → `+3805012345671`, `+90 532 123 45 67 12` → `+90532123456712` (**WR-09**, гэп 1) |
| 5 | Критерий 3, третья часть: неразбираемый сохранённый номер показывается как есть | ✓ VERIFIED | `format_phone('+999123456')` → `+999123456`, `format_phone('garbage')` → `garbage` |
| 6 | Критерий 4: ручной номер переживает автозапись последовательно и в гонке; условный UPDATE; очистка `(NULL, false)`; отрицание реально краснеет | ✓ VERIFIED | `_fill_if_unknown` не менялся. Мутант я повторил на нынешнем коде: плагин `-p mutate_rcw16r3` подменил `_fill_if_unknown` чтением-проверкой-записью, и `test_the_production_writer_keeps_the_manual_number_in_every_position` покраснел: «позиция 2: итог ('+79990000002', True), ручной номер затёрт». Без мутации — `4 passed`. `git diff --quiet 225fd3c7 -- tests/test_application/test_account_phone_race.py` — без изменений |
| 7 | Критерий 5: номер в строке журнала четырёх деревьев краснит гейт приватности; подложенная строка; только `phone_set` | ✓ VERIFIED | Гейт зелёный (в составе 559 passed); правила подложенной строки и живых деревьев зелёные. Неполнота границы — истина 28 |
| 8 | Цель: записать номер в колонку можно только через один модуль (D-12, D-13) — в живом дереве | ✓ VERIFIED | Мой греп `app/` и `scripts/` записей `phone` / `phone_is_manual` вне модуля-писателя не находит. `app/pages/accounts.py:837/896/903/938` — контекст шаблона, разметка, `start_session`; `app/messengers/max.py:167` — тело HTTP-запроса к воркеру. Гейт на живом дереве даёт 0, реестр — ровно модуль-писатель. Слепота средства — истина 18 |
| 9 | Маска D-10, чистота модуля, закрытые тексты отказа | ✓ VERIFIED | `mask_phone('+79991234567')` → `+7 *** ***-**-67`, `'+88812'` → `+888 ***`, `'+712'` → `+7 ***`. В `app/services/phone.py` нет ни `is_valid_number`, ни голого `is_possible_number(`; `PHONE_ERROR_MESSAGES` — 4 константы |
| 10 | План 16-01: суита записей зелёная без ослабления | ✓ VERIFIED (регрессия) | Мой прогон `tests/test_planning` → `218 passed, 2 skipped` |
| 11 | 16-07: ручной `00…`, местный номер с ведущим 0 и `+7 0…` → `PHONE_ERROR_NOT_A_NUMBER`; вариант (б) не реализован | ✓ VERIFIED (регрессия) | Зонд: `00 44 7911 123456`, `050 123 4567`, `8 029 123 45 67` → отказ; `+39 06 1234 5678` → `+390612345678`; `88801234567` → `+78801234567`; ручной `+888 0123 4567` → отказ |
| 12 | 16-07: автопуть — граница 7, отказ `IS_POSSIBLE_LOCAL_ONLY` | ✓ VERIFIED (регрессия) | Зонд: `12345`, `4412345`, `71234567` → `None`; `6831234`, `6901234` приняты |
| 13 | 16-07, истина 6 / 16-11, истина 7: граница автопути названа по настоящему принимаемому множеству | ✓ VERIFIED (advisory IN-08) | В раунде 2 провалена. Шапка `:37-45` называет `TOO_SHORT` у кода не 7 с замером «583 из 1935». Мой повтор перебора: 583 `TOO_SHORT`, 558 `IS_POSSIBLE`, отвергнутых вердиктов 0. Формулировка «Кроме настоящих номеров» неточна: 400 из 558 недействительны. Отказ от валидатора назван в той же шапке (D-05), поэтому это advisory, а не гэп |
| 14 | 16-08: `PhoneWrite.MISSING`; проба после UPDATE — `[Update]` / `[Update, Select]`; `set_manual_phone` с `LookupError`; писатель не коммитит и не присваивает | ✓ VERIFIED (регрессия) | `_fill_if_unknown` и `set_manual_phone` не менялись; правила 16-08 зелёные в составе 559 |
| 15 | 16-08, истина 3 / 16-14, истина 1: объект вне сессии → `ValueError(ACCOUNT_NOT_IN_SESSION)` при любом входе, ноль операторов | ✓ VERIFIED | В раунде 2 провалена. Мой зонд: `None` / `''` / `'garbage'` / `'79991234567'` → `ValueError`, текст равен константе, операторов 0, `id` остаётся `None`. Правило `test_recording_an_account_never_added_to_the_session_raises` — 4 случая, зелёные |
| 16 | 16-08 / 16-14: тест гонки и его отрицание не ослаблены | ✓ VERIFIED | Файл не менялся с `225fd3c7`; мутант убит (истина 6) |
| 17 | 16-09: пять форм WR-01 ловятся; executemany в синтетическом `scripts/`; живое дерево — 0 | ✓ VERIFIED (регрессия) | Контроли моего зонда: `params=[…]`, присваивание атрибуту — находка; правила 16-09 зелёные |
| 18 | 16-09, истина 5 / 16-12, истина 6: шапка гейта писателя называет настоящую границу и не выдаёт слепоту за неё | ✗ FAILED | Пять форм дают `[]` (**WR-10**, гэп 2), хотя шапка `:96-118` заявляет охват «всякой записи, где колонка названа литералом в самом пишущем вызове». Девять форм WR-08 теперь ловятся |
| 19 | 16-09: гейт приватности судит `bind_contextvars` / `bound_contextvars` при любом получателе; реестр пуст, потолок 0 | ✓ VERIFIED (регрессия) | `PHONE_LOG_EXCEPTIONS = {}` (`:155`), `PHONE_LOG_EXCEPTIONS_CEILING = 0` (`:158`) |
| 20 | 16-10: 11 находок первого ревью разобраны; IN-01 в STATE.md; реестр запретов согласован | ✓ VERIFIED (регрессия) | Строки CR-01 и WR-01…WR-05 байт в байт те же, что на `ed800e77`. В IN-01…IN-05 диспозиция `deferred` и причины прежние (о метке инструмента — истина 30) |
| 21 | 16-11, истины 1–2: ручной `+7` с лишними цифрами отвергается текстом `PHONE_ERROR_NOT_A_NUMBER`, класс закрыт перебором | ✓ VERIFIED | `app/services/phone.py:110`, `:159-176`, `:237-238`. Зонд — см. `re_verification.gaps_closed` 1. Правила `test_a_russian_number_with_four_extra_digits_typed_by_hand_is_refused` (1) и `…_whatever_their_count` (20) зелёные |
| 22 | 16-11, истина 3: принятые написания не меняются | ✓ VERIFIED | Зонд истины 3 и 11; `MANUAL_ACCEPTED` зелёная |
| 23 | 16-11, истина 4: автопуть даёт исход владельца О-5 (а) | ✓ VERIFIED | `normalize_reported`: `70123456789` → `None`, `799912345678` → `None`, `1234567890123` → `None`, `88801234567` → `+88801234567`; замеренные в раунде 2 `79991234567890`, `441234567890123`, `700447911123456`, `799912345671234`, `7999123` → `None`. Правило `test_the_auto_path_refuses_what_the_owner_named_before_execution` зелёное |
| 24 | 16-11, истины 5–6: Fragment, Ниуэ, Токелау, Узбекистан, Казахстан и номера-образцы метаданных приняты; перебор 1935 входов без отвергнутых вердиктов | ✓ VERIFIED | Зонд: `88801234567`, `888012345678`, `6831234`, `6901234`, `998901234567`, `77011234567` приняты. Правила `test_every_example_number_of_the_metadata_is_still_accepted_from_a_source` и `test_the_auto_path_never_stores_a_verdict_the_owner_refused` зелёные; перебор я повторил сам |
| 25 | 16-12, истины 1–2: девять форм WR-08 и формы тех же семейств — строки `LITERAL_FORM_CASES`, находка ровно одна | ✓ VERIFIED | Зонд — см. `gaps_closed` 3; правило `test_a_literal_write_form_is_a_write` зелёное |
| 26 | 16-12, истины 3–5: подложенный бэкфилл Фазы 20 с `parameters=` и comprehension краснит; живое дерево — 0; реестр — ровно писатель; законные места не краснят | ✓ VERIFIED | `test_a_planted_backfill_with_parameters_and_a_comprehension_reddens_the_gate`, `test_no_phone_write_outside_the_writer_in_the_live_tree`, `test_the_exception_registry_names_only_the_writer_module`, `test_a_legitimate_phone_mention_is_not_a_write` зелёные; `render(…, phone=submitted)` в моём зонде — `[]` |
| 27 | 16-13, истины 1–4: псевдоним привязки, `structlog.threadlocal`, получатель из фабрики под любым именем; живые деревья без новых находок | ✓ VERIFIED | Зонд: `bind_ctx(phone=…)`, `structlog.threadlocal.bind_threadlocal(phone=…)`, `with tmp_bind(logger, phone=…)`, `lg = logging.getLogger(); lg.info(…, account.phone)`, `self.lg = structlog.get_logger()` в `__init__` — все дают находку. `test_a_planted_aliased_binding_in_app_reddens_the_gate` и `test_no_number_reaches_a_python_log_call_in_the_live_trees` зелёные |
| 28 | 16-13, истина 5 (и истина 3 в части «под любым именем»): что вне охвата, названо в «ГРАНИЦЕ СРЕДСТВА» | ✗ FAILED (partial) | `from logging import info` / `warning as warn_` и `lg = structlog.get_logger()` в теле класса с вызовом `self.lg` / `cls.lg` дают `[]` и в границе не названы (**IN-09**, гэп 3) |
| 29 | 16-14, истины 2–5: проверка членства до нормализации, без операторов и flush; отсоединённый и чужой объект — отказ; член сессии с мусором — `UNPARSEABLE` без flush; писатель не коммитит | ✓ VERIFIED (advisory IN-10) | `app/application/accounts/phone.py:164-165`. Отсоединённый объект закреплён `test_recording_an_account_outside_this_session_raises`. Объект чужой сессии я проверил прямым прогоном: `AsyncSession()` без привязки → `ValueError`, 0 операторов. Тестом этот случай не закреплён — IN-10. `test_recording_garbage_for_a_pending_member_issues_nothing` зелёный |
| 30 | 16-15: пять находок раунда 2 — `fixed` с существующими коммитами; одиннадцать прежних строк перенесены; реестр запретов пересеян | ✓ VERIFIED | Десять хешей из клеток Source — предки HEAD (`git merge-base --is-ancestor`); темы — `feat(16-11)` … `feat(16-14)` и страж `test(16-14)` (`1fad15e3`). На коммите плана `d06307a4`: `open: 0`, `total: 16`, строки IN-01…IN-05 байт в байт как на `ed800e77`. Позднее штатный проход записи ревью (`9ecf63bf`) дописал к ним метку `(not in the current review)` — документированное поведение инструмента, а не правка 16-15. Реестр: 12 строк планов 16-11…16-15, `--check` rc 0, `tests/test_planning` 218 passed |

**Счёт:** 27/30 истин подтверждены (0 — присутствуют, но поведение не проверено). Провалены: 4, 18, 28.

### Отложенное

Нет. Фаза 18 (критерий 2) лишь показывает текст отказа нормализатора и не решает, что считать мусором у чужих кодов. Фазы 19–20 потребляют гейты, но не чинят их шапки. Гейты и нормализатор — артефакты Фазы 16.

### Advisory (новый объём, не блокирует)

| # | Находка | Категория | Почему advisory |
|---|---------|-----------|-----------------|
| 1 | IN-08: абзац границы автопути называет принятое сверх `TOO_SHORT` «настоящими номерами»; 400 из 558 принятых `IS_POSSIBLE` недействительны | other | Воспроизведено. Исход О-5 (а) код даёт ровно. Отказ от валидатора — запертое D-05, и он назван в той же шапке. Неточно слово, граница не скрыта. Закрыть вместе с гэпом 1 |
| 2 | IN-10: случай «чужая сессия» не закреплён тестом по ложной причине; текст `ACCOUNT_NOT_IN_SESSION` советует `session.add`, а для чужого объекта он падает | other | Воспроизведено. Поведение истины 16-14 верно, и я наблюдал его прямым прогоном. Изъян в тесте и в тексте для разработчика, а не в гарантии |

Advisory раунда 2 (IN-06) закрыт и перенесён в `re_verification.previous_round.advisory_disposition`.

### Требуемые артефакты

| Артефакт | Ожидается | Статус | Подробности |
|----------|-----------|--------|-------------|
| `alembic/versions/0023_messenger_account_phone.py` | ревизия `0023` | ✓ VERIFIED | не менялась |
| `app/models/messenger_account.py` | колонки и CHECK | ✓ VERIFIED | не менялась |
| `app/services/phone.py` | `RU_KZ_NATIONAL_DIGITS`, `REPORTED_REFUSED_VERDICTS`, `_is_impossible_zone_seven`, оба отказа, шапка с границей и летописями | ⚠️ ЕСТЬ, С ГЭПОМ | всё перечисленное есть и подключено; у других кодов класс лишних цифр не закрыт и не назван (WR-09); формулировка IN-08 |
| `app/application/accounts/phone.py` | проверка членства первой строкой `record_reported_phone`, текст, летопись | ✓ VERIFIED (IN-10) | `:164-165`; продуктовых потребителей по замыслу нет, их заведут Фазы 18–20 |
| `tests/test_services/test_phone.py` | `EXTRA_DIGIT_BASES`, строки `wr06_*` / `wr07_*`, пять правил | ✓ VERIFIED | основ BY / UA / TR нет — это гэп 1 |
| `tests/test_application/test_account_phone_writer.py` | параметризация из 4 входов, два новых правила | ✓ VERIFIED (IN-10) | — |
| `tests/test_application/test_phone_single_writer_gate.py` | расширенный предикат, 51 новая строка `LITERAL_FORM_CASES`, шапка «через механизм» | ✗ ПРЕДИКАТ УЖЕ ЗАЯВЛЕНИЯ | WR-10, гэп 2 |
| `tests/test_phone_privacy_gate.py` | `module_log_names`, расширенные `CONTEXT_BINDERS` / `LOGGER_FACTORIES`, граница | ⚠️ ГРАНИЦА НЕПОЛНА | IN-09, гэп 3 |
| `16-REVIEW-DISPOSITION.md` / реестр запретов | диспозиция раунда 2, засев | ✓ VERIFIED | истина 30 |

### Проверка ключевых связей

| Откуда | Куда | Через что | Статус | Подробности |
|--------|------|-----------|--------|-------------|
| `normalize_manual` | `_is_impossible_zone_seven` → `PhoneError(PHONE_ERROR_NOT_A_NUMBER)` | прямой вызов `:237-238` | WIRED | `set_manual_phone` зовёт `normalize_manual` до `session.execute` (`:192`) |
| `normalize_reported` | `_is_impossible_zone_seven` и `REPORTED_REFUSED_VERDICTS` | прямой вызов `:285-288` | WIRED | писатель зовёт его в `fill_reported_phone` (`:129`) и `record_reported_phone` (`:166`) |
| `record_reported_phone` | проверка членства → `ValueError` | `inspect(account).session is not session.sync_session` | WIRED | стоит до нормализации; 0 операторов |
| `_fill_if_unknown` | условный UPDATE и проба | `session.execute` | WIRED | мутант убит |
| `writer_sources(root)` | живое дерево и `tmp_path/scripts` | один обход | WIRED | подложенный бэкфилл Фазы 20 найден |
| `python_log_calls` | `module_log_names` → `_is_log_method_call` / `_is_context_binding` | отбор вызовов | WIRED (с пробелом IN-09) | псевдонимы и фабрики распознаны; ввоз функций `logging` и связывание в теле класса — нет |

### Трассировка данных (уровень 4)

Неприменима: фаза ничего не отрисовывает. Сквозной путь «источник → нормализация → условный UPDATE → колонка → `format_phone`» прогнан тестами писателя.

### Поведенческие пробы

| Поведение | Команда | Результат | Статус |
|-----------|---------|-----------|--------|
| Модули фазы | `flock … uv run pytest` по 7 модулям фазы и `tests/test_migrations` | `559 passed` за 12,6 с | ✓ PASS |
| Суита записей | `flock … uv run pytest tests/test_planning -q -p no:randomly` | `218 passed, 2 skipped` | ✓ PASS |
| Перепись запретов | `uv run python scripts/prohibitions_census.py --check` | rc 0, «реестр: 776 строк, биекция с переписью — согласие» | ✓ PASS |
| Мутант гонки | `-p mutate_rcw16r3` + один названный тест | `1 failed`: «позиция 2 … ручной номер затёрт» | ✓ PASS (мутант убит) |
| Исход О-5 (а) | `normalize_reported` на 4 входах владельца | `None`, `None`, `None`, `'+88801234567'` | ✓ PASS |
| WR-06 закрыт | `normalize_manual` на 7 входах `+7` с лишними цифрами | 7 × отказ `NOT_A_NUMBER` | ✓ PASS |
| IN-07 закрыт | `record_reported_phone` вне сессии, 4 входа + чужая сессия | 5 × `ValueError`, 0 операторов | ✓ PASS |
| WR-08 / IN-06 закрыты | гейты на 9 + 4 формах прошлого раунда | 13 × находка | ✓ PASS |
| WR-09 | `normalize_manual` на 7 основах × +1…+4 цифры | BY +1/+2, UA +1, KG +1, TR +2/+3, IL +1…+3, CN +1, DE +1/+2 сохранены | ✗ FAIL |
| WR-10 | `phone_write_offences` на 5 формах; запись на SQLite в памяти | 5 × `[]`; колонка записана (`+71`, `+72`, `+73`) | ✗ FAIL |
| IN-09 | `python_log_offences` на 5 формах и 6 контролях | 5 × `[]`; контроли пойманы | ✗ FAIL (partial) |
| IN-08 | повтор перебора 1935 входов | 583 TOO_SHORT, 558 IS_POSSIBLE, из них 400 недействительны | ⚠️ WARN |
| IN-10 | чужая `AsyncSession()`; `session.add` чужого объекта | `ValueError`; `InvalidRequestError` | ⚠️ WARN |

Полный прогон я не повторял, по указанию оркестратора: на `719555b7` он дал `4544 passed, 2 skipped, 0 failed`, а код с тех пор не менялся. Зонды лежат в scratchpad сессии (`r3/probe_norm.py`, `r3/probe_gates.py`, `r3/in07.py`, `r3/mutate_rcw16r3.py`) и в репозиторий не попали.

### Пробы

Неприменимо: планы и SUMMARY не объявляют `scripts/*/tests/probe-*.sh`.

### Покрытие требований

| Требование | План-источник | Описание | Статус | Улика |
|------------|---------------|----------|--------|-------|
| PHONE-01 | 16-02, 16-03, 16-05, 16-07, 16-11 | номер в каноническом E.164 в отдельном поле, «неизвестен» — отдельное состояние, уникальности нет | ✗ ЧАСТИЧНО | Поле, состояние и отсутствие уникальности подтверждены (истины 1, 2). У кода 7 и на автопути номера, которых не бывает, больше не сохраняются (истины 21–24). Ручной путь всё ещё кладёт в поле выдуманный номер чужой зоны (WR-09, гэп 1, ждёт решения владельца) |
| PHONE-02 | 16-05, 16-06, 16-08, 16-09, 16-12, 16-14 | ручной номер не затирается автоисточником, в том числе в гонке | ✓ SATISFIED (с гэпом средства) | Гарантия держится: истины 6, 8, 14–16, мутант убит на нынешнем коде, живое дерево чисто. Обещание гейта писателя шире предиката (гэп 2) — гэп средства, а не нарушение гарантии в коде сегодня |
| PHONE-21 | 16-02, 16-04, 16-07, 16-09, 16-13 | номера не попадают в журналы, только маска или признак | ✓ SATISFIED (с гэпом средства) | Истины 7, 9, 19, 27. Граница гейта приватности неполна (гэп 3); в живых деревьях находок 0 |
| `записи-старт-вехи` | 16-01 | псевдо-ID решения владельца 2026-10-08 | ✓ SATISFIED | Истина 10 |
| `диспозиция-ревью-16` | 16-10, 16-15 | псевдо-ID решений владельца О-4 / партии раунда 2 | ✓ SATISFIED | Истины 20, 30 |

Осиротевших требований нет: REQUIREMENTS.md (`:84-85`, `:104`) отдаёт Фазе 16 ровно PHONE-01, PHONE-02 и PHONE-21, и каждое заявлено планами. Все три по-прежнему `Pending`, и при `gaps_found` это верно.

### Найденные антипаттерны

| Файл | Строка | Шаблон | Серьёзность | Последствие |
|------|--------|--------|-------------|-------------|
| `app/services/phone.py` | 172-173, 193-213, 237-240 | класс лишних цифр закрыт только у кода 7, граница не названа (WR-09) | 🛑 (гэп 1, partial) | номер чужой зоны с лишними цифрами навсегда закрыт под «ручным» |
| `tests/test_application/test_phone_single_writer_gate.py` | 96-118, 175, 413-431, 520 | охват «через механизм» заявлен, пять форм проходят (WR-10) | 🛑 Blocker (истина 16-12) | второй писатель Фазы 20 через `run_sync(Session.bulk_update_mappings, …)` или `Query.update(values=…)` проходит гейт |
| `tests/test_phone_privacy_gate.py` | 100-128, 295-345 | граница не называет опознаваемые формы (IN-09) | 🛑 (гэп 3, partial) | номер через `from logging import info` или журнал из тела класса уходит в Loki незамеченным |
| `app/services/phone.py` | 37-45 | «Кроме настоящих номеров» (IN-08) | ⚠️ Warning (advisory) | читатель переоценит принимаемое множество |
| `app/application/accounts/phone.py` / `tests/test_application/test_account_phone_writer.py` | 70, 171-172 / 369-394 | неверный совет в тексте, ложная причина в тесте (IN-10) | ⚠️ Warning (advisory) | разработчик Фазы 19 последует совету и получит `InvalidRequestError` |
| `pyproject.toml` | 21 | точный пин (IN-02) | ℹ️ Info | отложено владельцем (О-4) |
| `scripts/prohibitions_census.py` | — | падение на дробных фазах (IN-04) | ℹ️ Info | отложено владельцем (О-4) |

В шести файлах, которые партия изменила, нет маркеров `TBD` / `FIXME` / `XXX` / `TODO` / `HACK` / `PLACEHOLDER`. IN-01, IN-03 и IN-05 отложены владельцем (О-4) с адресатами. Диспозиция переносит их с причинами, а этот отчёт заново их не судит.

Ворота улик повторной верификации (#3304) все три гэпа проходят. Гэп 1 продолжает гэп 1 раунда 2: та же истина, критерий 3. Файлы гэпов 1–3 изменены после 2026-10-09T17:03:15Z. У каждой находки есть воспроизводимая улика — мой зонд.

### Запреты (judgment-tier, вердикт верификатора не авторитетен)

У всех 35 запретов фазы `status: flagged-unverified`. Ниже вердикт LLM-судьи с уликой. Флаг каждой строки: `unverified-prohibition — human review recommended` (human_verification 1).

| План | Запрет (кратко) | Вердикт | Улика |
|------|-----------------|---------|-------|
| 16-01 №1 | не ослаблять правила записей | соблюдён | `tests/test_planning`: 218 passed, 2 skipped |
| 16-01 №2 | не стирать числа без летописи | соблюдён | файлы записей не менялись партией |
| 16-01 №3 | не трогать продуктовый код | соблюдён | коммиты 16-01 не касаются `app/`, `alembic/`, воркеров |
| 16-02 №1 | не подставлять ввод в текст `PhoneError` | соблюдён | только константы `PHONE_ERROR_*`; 16-11 новых текстов не завёл |
| 16-02 №2 | не превращать мусор в «номер» (в т. ч. номер с добавочным) | **нарушен** | WR-06 закрыт у кода 7, но WR-09: `+375 29 123 45 67 1` сохраняется как `+3752912345671` — гэп 1 |
| 16-03 №1 | нет уникального индекса | соблюдён | файлы не менялись, тест зелёный |
| 16-03 №2 | ревизия не заполняет номер | соблюдён | то же |
| 16-04 №1 | номер не попадает в журнал даже маской | соблюдён в живом дереве; средство неполно | живые деревья: 0 находок; пропуски гейта — IN-09 (гэп 3) |
| 16-04 №2 | реестр исключений не расширяется | соблюдён | `PHONE_LOG_EXCEPTIONS = {}`, потолок 0 |
| 16-05 №1 | автоисточник не затирает ручной номер | соблюдён | мутант нынешнего кода убит |
| 16-05 №2 | автономер не помечается ручным | соблюдён | `_fill_if_unknown` пишет только `phone` (`:112`) |
| 16-06 №1 | нет записи в обход писателя | соблюдён в живом дереве; средство неполно | греп и гейт: 0; пропуски гейта — WR-10 (гэп 2) |
| 16-06 №2 | реестр писателя — ровно модуль-писатель | соблюдён | `:268-272`, правило реестра зелёное |
| 16-07 №1 | не реализовывать вариант (б) «`00` как `+`» | соблюдён | `00 44 7911 123456` → отказ |
| 16-07 №2 | без валидатора, без нового текста, 4 константы | соблюдён | греп `is_valid_number` в модуле пуст; 4 константы |
| 16-07 №3 | не терять Fragment, Ниуэ, Токелау | соблюдён | зонд: `+88801234567`, `+888012345678`, `+6831234`, `+6901234` |
| 16-08 №1 | проба существования не перед записью | соблюдён | `:105-120` не менялись |
| 16-08 №2 | не ослаблять тест гонки | соблюдён | файл не менялся с `225fd3c7`; мутант убит |
| 16-09 №1 | не расширять реестры ради зелени | соблюдён | оба реестра прежние |
| 16-09 №2 | не выдавать слепоту предиката за границу средства | **нарушен** | WR-10: пять форм проходят при заявлении охвата «через механизм» — гэп 2; часть «привязки к журналу» — IN-09, гэп 3. Девять форм WR-08 закрыты |
| 16-10 №1 | `fixed` только с существующим коммитом | соблюдён | 8 хешей первой партии — предки HEAD |
| 16-10 №2 | не отбрасывать находку молча | соблюдён | пять находок раунда 3 разобраны в этом отчёте (раздел ниже) |
| 16-10 №3 | не править формулировки после засева | соблюдён | `--check` rc 0; правило отпечатка в `tests/test_planning` зелёное |
| 16-11 №1 | без валидатора, без голой «возможности», без нового текста; 4 константы | соблюдён | греп пуст; `PHONE_ERROR_MESSAGES` — 4 |
| 16-11 №2 | не терять настоящий номер; ручной `+888…` отвергается; «`00` как `+`» не реализуется | соблюдён | зонд истины 24; `+888 0123 4567` → отказ |
| 16-11 №3 | не реализовывать О-5 (б) и не утверждать границу `TOO_SHORT` нормой | соблюдён | в `REPORTED_ACCEPTED` нет строк `TOO_SHORT` вне Fragment; граница — в шапке |
| 16-12 №1 | не расширять `PHONE_WRITER_EXCEPTIONS` | соблюдён | ровно модуль-писатель |
| 16-12 №2 | не сужать заявление шапки вместо починки | соблюдён по букве | все формы WR-08 и перебора планирования ловятся; новая слепота (WR-10) — по 16-09 №2 и истине 18 |
| 16-13 №1 | не расширять `PHONE_LOG_EXCEPTIONS` и потолок | соблюдён | `{}`, 0 |
| 16-13 №2 | не расширять список получателей угадыванием | соблюдён | опознание по фабрике, ввозу, имени; `a = lg` названо в границе |
| 16-14 №1 | не ослаблять тест гонки | соблюдён | `git diff --quiet 225fd3c7`; мутант убит |
| 16-14 №2 | проверка членства без оператора и flush; договор не сужен | соблюдён | зонд: 0 операторов на 5 случаях; правило ожидающего члена зелёное |
| 16-15 №1 | `fixed` только с существующим коммитом `feat(16-1N)` | соблюдён | 10 хешей — предки HEAD, темы `feat(16-11…14)` и страж `test(16-14)` |
| 16-15 №2 | строки IN-01…IN-05, CR-01, WR-01…WR-05 — байт в байт | соблюдён на коммите плана | на `d06307a4` все 11 строк равны `ed800e77`; метку `(not in the current review)` к IN-01…IN-05 позднее дописал проход записи ревью `9ecf63bf`, диспозиции и причины целы |
| 16-15 №3 | не править формулировки запретов после засева | соблюдён | `--check` rc 0, правило отпечатка зелёное |

### Новые находки повторного ревью: куда легла каждая

| Находка | Воспроизведена | Куда легла | Почему |
|---------|----------------|------------|--------|
| WR-09 | да, 7 основ × 4 | **гэп 1** (partial) + human_verification 2 | Тот же класс вреда, что WR-06 (выдуманный номер закрыт под «ручным», D-07; запрет 16-02 №2), у кодов не 7. Граница нигде не названа, а запись диспозиции говорит о классе шире кода. Отход от буквы D-05 — решение владельца, умолчание (а) — отказ по типам аккаунта. В ревью утверждение про DE неточно: правило (а) Германию не закрывает |
| WR-10 | да, 5 форм, запись подтверждена на SQLite | **гэп 2** (blocker по истине 16-12 / 16-09) | Заявление шапки «через механизм» покрывает формы, а предикат их не видит. По правилу самой шапки это слепота, а не граница; запрет 16-09 №2 нарушен в третий раз |
| IN-08 | да, перебор повторён | **advisory** | Исход О-5 (а) дан ровно; отказ от валидатора назван в той же шапке (D-05); неточно слово, граница не скрыта |
| IN-09 | да, 5 форм | **гэп 3** (partial) | Истина 5 плана 16-13 буквально неверна: две опознаваемые формы не пойманы и не названы. Ревью дало уровень info, вред мал, но довод границы к этим формам не подходит |
| IN-10 | да | **advisory** | Поведение истины 16-14 верно, я наблюдал его прямым прогоном; изъян в тесте и в тексте для разработчика |
| IN-01…IN-05 | — | отложены владельцем (О-4) | диспозиция с причинами и адресатами |

### Нужна проверка человеком

#### 1. Сверка вердиктов запретов (перенос пункта 1 раунда 2)

**Проверка:** таблица «Запреты» выше, 35 строк.
**Ожидается:** владелец согласен с каждым вердиктом. Две строки «нарушен» (16-02 №2, 16-09 №2) совпадают с гэпами 1 и 2–3.
**Почему человек:** запреты judgment-tier, вердикт LLM не авторитетен.

#### 2. Решение владельца по номерам чужих зон с лишними цифрами (гэп 1, WR-09)

**Проверка:** назвать исход до исполнения гэпа, затем сверить `normalize_manual('+375 29 123 45 67 1')` и `('+380 50 123 4567 1')`, а для контроля `('+375 29 123 45 67')` и `('8-800-555-35-35')`.
**Ожидается:** (а) по умолчанию — `PhoneError(PHONE_ERROR_NOT_A_NUMBER)` дважды, затем `'+375291234567'` и `'+78005553535'`, а Германия названа границей. Либо (б): поведение прежнее, граница «только код 7» названа в докстринге, отступление записано в `overrides`.
**Почему человек:** правило (а) отходит от буквы запертого D-05 и вводит политику «каким типом бывает аккаунт». Цена — риск ложного отказа настоящему номеру, если метаданные отстанут.

Пункт 2 раунда 2 (WR-07) закрыт решением владельца О-5 (а) и моим воспроизведением исхода — см. `re_verification.previous_round.human_verification_disposition`.

### Сводка гэпов

**Две причины, три гэпа.**

**Причина А — правило «мусор отвергается» (критерий 3, D-06) закрыто для кода 7, но не для класса.**
1. **Гэп 1, WR-09 (partial, нужно решение владельца).** Беларусь, Украина, Турция и другие: настоящий номер с 1–3 лишними цифрами сохраняется как «ручной». Код 7 закрыт признаком разбора. Для прочих кодов нужно правило по типам номеров, а это шаг от буквы D-05. Поэтому сначала решение владельца (human_verification 2), потом правка. Правка нужна при любом исходе: граница сегодня нигде не названа. IN-08 правится в том же файле.

**Причина Б — шапки гейтов снова обещают больше, чем видят предикаты.**
2. **Гэп 2, WR-10 (блокер по истине 16-12).** Это третий круг: WR-01 → WR-08 → WR-10. Каждый раз набор пропусков уже, но схема прежняя: ревьюер подаёт формы, исполнитель чинит ровно их. Чтобы не открыть четвёртый круг, рекомендую планировщику перебрать сигнатуры судимых API (`inspect.signature`) и для каждого судимого позиционного параметра судить и его именованную форму. Пять форм ревью — пример, а не перечень.
3. **Гэп 3, IN-09 (partial).** Тот же изъян в гейте приватности: две формы, опознаваемые по правилу самой шапки, не пойманы и не названы. Правка мала, её разумно сделать тем же проходом, что гэп 2.

**Планировщику гэпов:** REVIEW.md он не читает, поэтому всё нужное уже лежит в `gaps[].missing`, вместе с замерами. Advisory IN-08 и IN-10 стоят в `advisory`. Их можно закрыть попутно, в тех же файлах: `app/services/phone.py` и писатель с его тестом.

**Вне объёма (не гэп):** ветка PostgreSQL ревизии `0023`, READ COMMITTED и `rowcount` на asyncpg (деплой-гейт D-26). `/gsd-secure-phase 16` не запускался, `16-SECURITY.md` нет.

### Перенос прежних блоков (договор переноса)

Я сверил результат с копией `VERIFICATION.before-r3.md` и перенёс прежние блоки так:
- **Цепочка `re_verification`.** Вердикт раунда 2 лежит в `re_verification.previous_round`: `verified`, `status`, `score`, `covered_digest`, все четыре `gaps` дословно, `advisory` (IN-06) дословно, `human_verification` дословно. К ним добавлены `human_verification_disposition` и `advisory_disposition`. Прежний блок `re_verification` раунда 2 перенесён целиком в `re_verification.previous_round.re_verification`, со сдвигом отступа на 4 пробела и без единой правки: `previous_status`/`previous_score` раунда 1, `previous_round` раунда 1 (его `gaps` и `human_verification_disposition`), а также `gaps_closed`, `gaps_remaining`, `regressions` раунда 2.
- **`human_verification`.** Пункт 1 раунда 2 (запреты) перенесён как пункт 1 и расширен до 35 строк. Пункт 2 (WR-07) снят с уликой. Новый пункт 2 (WR-09) машиной не решается.
- **`advisory`.** IN-06 снят с причиной и уликой (`advisory_disposition`). Новые записи — IN-08 и IN-10.
- **`overrides`.** Ни в одном прошлом раунде их не было, и сейчас нет (`overrides_applied: 0`).

---

_Проверено: 2026-10-10T07:08:40Z_
_Верификатор: Claude (gsd-verifier)_
