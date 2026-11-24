---
phase: 17-pokaz-nomera-na-vseh-ekranah
reviewed: 2026-11-20T00:00:00Z
depth: standard
files_reviewed: 38
files_reviewed_list:
  - app/application/accounts/dto.py
  - app/application/accounts/labels.py
  - app/application/accounts/use_cases.py
  - app/pages/account_groups.py
  - app/pages/accounts.py
  - app/pages/admin.py
  - app/pages/common.py
  - app/pages/history.py
  - app/services/account_label.py
  - app/static/css/app.css
  - app/templates/account_groups/list.html
  - app/templates/accounts/list.html
  - app/templates/accounts/partial_cards.html
  - app/templates/accounts/partials/sync_status_card.html
  - app/templates/admin/history_partial_cards.html
  - app/templates/admin/includes/queue_row.html
  - app/templates/admin/includes/worker_row.html
  - app/templates/admin/queue.html
  - app/templates/admin/user_detail.html
  - app/templates/admin/user_history.html
  - app/templates/ads/includes/sched_card.html
  - app/templates/components/account_label.html
  - app/templates/history/includes/history_card.html
  - app/templates/history/list.html
  - tests/account_label_support.py
  - tests/test_application/test_account_label_rows.py
  - tests/test_pages/test_account_label_accounts.py
  - tests/test_pages/test_account_label_admin.py
  - tests/test_pages/test_account_label_admin_history.py
  - tests/test_pages/test_account_label_groups.py
  - tests/test_pages/test_account_label_history.py
  - tests/test_pages/test_account_label_sweep.py
  - tests/test_pages/test_admin_panel.py
  - tests/test_pages/test_editor_schedules.py
  - tests/test_pages/test_history_export.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_services/test_account_label.py
  - tests/test_templates/test_account_label_gate.py
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
  necessity: 1
status: issues_found
---

# Phase 17: Code Review Report

**Reviewed:** 2026-11-20
**Depth:** standard
**Files Reviewed:** 38
**Status:** issues_found

## Summary

Разобрано изменение фазы (`git diff 0516c113..HEAD`) в больших уже существовавших модулях (`admin.py`, `history.py`, `accounts.py`, `app.css`, три больших тестовых файла) и целиком — новые файлы. Прогнаны под `flock`: девять файлов `test_account_label*` / гейт (151 passed), `test_phone_privacy_gate`, `test_phone_gates_parity`, `test_phone_single_writer_gate`, `test_history_export`, `test_editor_schedules` (1378 passed). Полную суиту не гнал.

Проверка по пунктам безопасности из задания, все — без находок:

- **Граница владельца.** `load_account_rows` фильтрует по `MessengerAccount.user_id`; админские порции берут `user_id` из адреса просматриваемого пользователя (маршрут за `require_admin`), а не администратора. `accounts_sync_status` строит подпись только после `view is not None` (владение проверил `get_sync_status_view`). CSV читает карту `phones` по `user.id` до потока; чужой номер в файл не попадает (тест `test_export_never_carries_another_users_number` зелёный).
- **Экранирование HTML.** `|safe` и `Markup` в `account_label.html`, `services/account_label.py` и `modal.html` отсутствуют. Подпись печатается автоэкранированием; в `x-*` / `hx-*` не кладётся (`queue_row.html` ключи панелей подписи не получают). Плоская форма в `title=`, `<option>`, теле модалки и сводке расписания проходит `join` / `{{ }}` с автоэкранированием один раз — двойного экранирования нет.
- **CSV.** `export_phone_cell` снимает ровно один «+» (`removeprefix`) ДО `export_cell`; формулы (`+=1`, `-5`, `@x`, `\t=`) обезврежены. Неразбираемый номер идёт как есть, но через `export_cell`.
- **Журналы.** В изменённом коде нет вызовов журнала с номером или подписью; гейты приватности зелёные.
- **Админ-экраны.** Номер администратору показывают только маршруты админки; пользовательские экраны получают `audience='user'` по умолчанию, `#id` у недвойника там не печатается.
- **Единый источник подписи.** Признак двойника во всех путях считается одним правилом по ВСЕМ аккаунтам пользователя (`build_labels` / `label_of` / `labels_for`); расхождения между страницей, порцией, опросом и фильтром не нашёл.

Критических дефектов нет. Найдено два предупреждения (ненадёжная тестовая вспомогательная функция; недостижимая ветка с неверным утверждением в докстринге) и три замечания уровня Info. Решения владельца D-01…D-21 (в том числе «удалённый между запросами аккаунт даёт исключение», «двойники по пользователю и по мессенджеру», «CSV без «+»») не оспариваются.

## Warnings

### WR-01: `_ChipTitles` в `test_editor_schedules.py` не знает пустых элементов и приписывает всем чипам `title=` первого

**File:** `tests/test_pages/test_editor_schedules.py:1426-1445` (класс `_ChipTitles`), используется в `test_the_chip_title_and_the_panel_text_carry_the_plain_label` (`:1468`)
**Issue:** Разборщик считает вложенность увеличением `_depth` на каждом `handle_starttag` и уменьшением на каждом `handle_endtag`. Внутри `<label class="chip">` стоит `<input class="chip__input" type="radio" ...>` — пустой элемент без закрывающего тега. Счётчик на нём растёт и не возвращается, поэтому после `</label>` глубина остаётся 1, `_chip_title` не сбрасывается, и ВСЕ следующие чипы читаются как вложенные в первый. Воспроизведено на урезанной разметке двух чипов:

```
{'1': 'A', '2': 'A'}   # у второго чипа title был 'B'
```

Тест зелёный только потому, что читает единственный ключ — первого, по порядку `id`, аккаунта (`twin`). Если порядок аккаунтов или состав чипов изменится (двойник окажется вторым), проверка начнёт сравнивать `title=` чужого чипа и пройдёт или упадёт по случайной причине. То же свойство у `_SummaryTitles` (`:1400`): любой пустой элемент внутри `.sched-card__sum` (сейчас там `messenger_icon`) сделает «внутри сводки» весь остаток документа. Общий разборщик `tests/account_label_support.py::_Tracker` пустые элементы учитывает (`_VOID`) — здесь они забыты.
**Fix:** Не заводить вторую копию разборщика с вложенностью, а либо ввозить набор пустых элементов и не считать их (`if tag in _VOID: return` после записи атрибутов, и не увеличивать `_depth`), либо расширить `account_label_support` функцией «`title=` предка-чипа → `data-account-label` потомка» на базе `_Tracker`:

```python
_VOID = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"})

def handle_starttag(self, tag, attrs):
    a = dict(attrs)
    if self._chip_title is not None:
        if "data-account-label" in a:
            self.by_account[a["data-account-label"] or ""] = self._chip_title
        if tag not in _VOID:
            self._depth += 1
    elif tag == "label" and "chip" in (a.get("class") or "").split():
        self._chip_title, self._depth = a.get("title") or "", 1
```

И добавить в тест второй чип с иной подписью и утверждение по нему (сейчас оно отсутствует, поэтому дефект не виден).

### WR-02: Недостижимая ветка `group.account_id is None` в `history_account_label`, а докстринг называет её случаем D-15

**File:** `app/pages/history.py:172-195` (условие на строке 194)
**Category:** necessity
**Issue:** Состояние «у группы нет аккаунта» не существует: `Group.account_id` объявлен `Mapped[int]` с `ForeignKey("messenger_accounts.id", ondelete="CASCADE")` без `nullable=True` (`app/models/group.py:49-51`), то есть колонка `NOT NULL`. Строка группы без аккаунта удаляется каскадом вместе с ним, поэтому единственный реальный случай D-15 — `group is None` (внешнее соединение `SendLog` → `Group` вернуло пустую группу). Докстринг же утверждает: «`None` возвращается в двух случаях: группы нет … или у группы нет аккаунта (D-15)». Второй случай — вымышленное состояние, и запись о нём вводит читателя в заблуждение о модели данных (следующий читатель решит, что аккаунт у группы бывает пустым, и начнёт защищаться от этого в других местах). Не доверенная граница: значение берётся из собственной базы по `NOT NULL` колонке, а не из ввода.
**Fix:** Оставить только реальное условие и поправить докстринг:

```python
if group is None:
    return None
return labels.get(group.account_id)
```

В докстринге вместо «двух случаев» назвать два реальных: группы нет (запись пережила её удаление) и аккаунта нет в карте (чужой либо исчезнувший между запросами — по T-17-12 остаётся без подписи). Если гард нужен как защита от будущей миграции `nullable=True`, записать это причиной в комментарии, а не в описании данных.

## Info

### IN-01: `export_row(..., phone=None)` молча отдаёт пустую «Номер» при забытом аргументе

**File:** `app/pages/history.py:317-322`, `:365`, `:859-866`
**Issue:** Именованный параметр `phone` имеет умолчание `None`, а ячейка строится как `export_phone_cell(phone) if group else ""`. Вызывающий, который передаст группу с аккаунтом, но забудет `phone=`, получит строку с заполненным «Аккаунтом» и пустым «Номером» — неотличимо от аккаунта без номера (D-16) и без единого исключения. Сегодня вызывающий один (`history_export`), и тест `test_export_carries_the_number_without_the_plus` его сторожит, но функция заявлена чистой и самодостаточной, а правила «ячейка = карта» нет (докстринг сам это признаёт: «Правила, сравнивающего ячейку с экраном, нет»).
**Fix:** Сделать `phone` обязательным именованным параметром (без умолчания) — тогда второй вызывающий падает на `TypeError` при первом же запуске, а не выгружает файл с тихо пустой колонкой. Тесты `export_row(...)` без `phone=` получат его явно (`phone=None`).

### IN-02: Шесть локальных словарей «тип → имя канала» остались рядом с единым `MESSENGER_LABELS`

**File:** `app/templates/accounts/list.html:52`, `app/templates/accounts/partial_cards.html:21`, `app/templates/accounts/partials/sync_status_card.html:52`, `app/templates/account_groups/list.html:15` (используется только в `:51` как `account.type in MESSENGER_LABELS`), `app/templates/admin/includes/worker_row.html:53`, `app/templates/admin/includes/queue_row.html:36`
**Issue:** D-11 формулирует «помощник один — источник слов тоже один» и перечисляет места, откуда локальный словарь уходит (`sched_card.html`, `history/list.html`, `admin/user_history.html`, `admin/user_detail.html`). Названные места убраны, но в соседних шаблонах тех же экранов тот же литерал `{'tg_user': 'Telegram', 'wa': 'WhatsApp', 'max': 'MAX'}` остаётся: карточки аккаунта печатают канал (`acct-card__chan`) из локальной копии, а номер рядом — из подписи, берущей канал из `MESSENGER_LABELS`. Добавление четвёртого мессенджера в `app/constants.py` обновит подпись, но не эти шесть копий (значок канала и слово канала разойдутся молча). Это не нарушение решения (места в D-11 не названы) — пробел в полноте замены; гейт 17-08 ловит только `#`, а не словарь.
**Fix:** Заменить копии глобалом `messenger_labels` (он уже есть в `app/pages/common.py:328`) либо читать `acct_label.channel`; для проверки «тип известен» — `account.type in messenger_labels`. Если замена выходит за рамки вехи, записать остаток отдельной строкой в `deferred-items`.

### IN-03: Тест прохода импортирует приватные помощники из чужих тестовых модулей

**File:** `tests/test_pages/test_account_label_sweep.py:54-57`
**Issue:** `_seed_viewed_user` (из `test_account_label_admin_history.py`), `_seed_log` (из `test_account_label_history.py`), `_fake_redis`, `_FakeQueuePageRedis`, `_queue_task` (из `test_admin_panel.py`), `_seed_ad`, `_seed_schedule` (из `test_editor_schedules.py`) — приватные имена тестовых файлов других планов. Переименование или перенос любого из них оставляет `test_account_label_sweep.py` не собирающимся (`ImportError` при сборе роняет файл целиком, а не один тест), причём авторы этих файлов о зависимости не знают. Файл `account_label_support.py` создавался именно как общий модуль, но эти помощники в него не вынесены.
**Fix:** Перенести общие посевы в `tests/account_label_support.py` (или в `tests/conftest.py`, как `seed_group`) и ввозить оттуда; либо объявить зависимость комментарием в тех модулях, откуда берутся имена.

---

_Reviewed: 2026-11-20_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
