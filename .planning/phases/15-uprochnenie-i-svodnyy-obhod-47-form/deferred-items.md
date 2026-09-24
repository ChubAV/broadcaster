# Deferred Items — Phase 15

## Deferred Items

- Правило пар 302 жалуется на `tests/test_pages/test_billing_section.py:706` (найдено исполнителем плана 15-08, 2026-09-24)
  status: open
  **What:** `test_every_302_assertion_on_a_converted_handler_is_paired` (`tests/test_pages/test_htmx_post_pairs.py`) красен дословно так: «утверждения 302 без пары: tests/test_pages/test_billing_section.py:706 (test_the_payment_form_keeps_its_route_and_degrades_without_htmx): обработчик не назван — адрес POST собран выражением».
  **Measured origin:** красно и на дереве `83c34ab5` — ДО первого коммита плана 15-08 (прогон правила над снимком `git archive 83c34ab5`); файл правки — коммит `0203202f` плана 15-03. План 15-08 этого файла не трогал.
  **Why deferred:** вне области плана 15-08 (правило границы области исполнителя: чинится только то, что сломала собственная правка). Второе красное правило того же модуля — число утверждений 302 (189 против 188) — ВЫЗВАНО планом 15-08 и им же починено (`5e9b4d49`).
  **Addressee:** оркестратор фазы / план, владеющий парами 302 (исполнитель 15-03 или ревизия фазы).
