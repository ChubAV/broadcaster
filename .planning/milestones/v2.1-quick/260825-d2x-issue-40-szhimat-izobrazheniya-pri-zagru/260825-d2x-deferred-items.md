# Отложенное — issue #40 (quick 260825-d2x)

## test_the_machine_readable_progress_is_derived_from_the_roadmap — красный ДО задачи

**Файл:** `tests/test_planning/test_state_progress_matches_roadmap.py`

**Что утверждает:** `progress.total_plans` и `progress.completed_plans` во
frontmatter `.planning/STATE.md` выводятся из отметок `.planning/ROADMAP.md`.

**Что наблюдается:** записано 110 и 110, выводится 0 и 0.

**Почему НЕ чинится здесь:** это расхождение учётных файлов планирования, а не
кода. Ни `.planning/STATE.md`, ни `.planning/ROADMAP.md`, ни сам тест этой
задачей не менялись (`git diff HEAD -- .planning/` пуст), а числа в отказе
совпадают с числами на базовом коммите — то есть тест был красным до первого
коммита issue #40. Правка учёта планов лежит за границей задачи, а «подгонка»
поля STATE.md попутным коммитом отключила бы проверку, которая ровно это
расхождение и ловит.

**Кому адресовано:** владельцу `.planning/` — привести `progress.*` в STATE.md
к отметкам ROADMAP.md либо починить разбор отметок, если источником счёта
объявлен ROADMAP.
