# Profile Timezone Settings Design

**Goal:** Добавить страницу настроек профиля, где пользователь может выбрать свой часовой пояс по умолчанию. Этот часовой пояс будет использоваться как дефолт в формах создания расписаний и может отображаться в интерфейсе.

## Текущий контекст

- В `app/models/user.py` уже есть поле `timezone: Mapped[str] = mapped_column(String(50), default="UTC")`.
- В `app/constants.py` определены:
  - `TIMEZONE_CHOICES: list[tuple[str, str]]` — список таймзон для select.
  - `VALID_TIMEZONES: set[str]` — множество валидных значений.
- В `app/pages/schedules.py` и `app/routes/schedules.py` эти константы уже используются для валидации и отрисовки формы.
- В шаблоне `app/templates/admin/user_detail.html` таймзона пользователя уже отображается, но сам пользователь сейчас не может её менять через UI.
- В навигации (например, `base.html` / `dashboard.html`) нет отдельного пункта "Профиль" / "Настройки".

## Требования

1. **Страница настроек профиля**
   - Новый маршрут, условно `/profile` (GET/POST).
   - Доступен только авторизованному пользователю.
   - Показывает форму с выбором часового пояса:
     - Список значений берётся из `TIMEZONE_CHOICES`.
     - Текущий `user.timezone` выбран по умолчанию.
   - При сабмите:
     - Значение берётся из `form_data["timezone"]`.
     - Проверяется, что оно входит в `VALID_TIMEZONES`.
     - В случае невалидного значения — либо игнорируем изменение и показываем ошибку, либо возвращаем форму с сообщением (минимум: не сохраняем).
     - В случае успеха сохраняем в `user.timezone` и делаем редирект (например, обратно на `/profile`) с флеш‑сообщением "Настройки сохранены".

2. **Интеграция с расписаниями**
   - При создании нового расписания (страница `GET /schedules/new` / аналогичная):
     - Значение по умолчанию для `timezone` в форме:
       - Если `user.timezone` присутствует в `VALID_TIMEZONES` — использовать его.
       - Иначе использовать текущий дефолт (сейчас это либо `Europe/Moscow` в шаблоне, либо `"UTC"` в коде; нужно аккуратно сохранить существующее поведение как fallback).
   - При редактировании расписания:
     - Логика остаётся прежней: по умолчанию берём `schedule.timezone`.

3. **UX / UI**
   - Новый шаблон (например, `profile.html`), наследующийся от `base.html`.
   - Навигация:
     - Добавить пункт меню "Профиль" или "Настройки" (в зависимости от текущего языка навигации; проект русифицирован, поэтому "Профиль" или "Настройки профиля").
     - Подсвечивать его через существующий механизм `active_page`, аналогично `ads`, `groups`, `schedules`, `accounts`.
   - Форма:
     - Один блок формы "Часовой пояс" с `<select>`, как в `schedules/form.html`, но с привязкой к `user.timezone`.
     - Кнопка "Сохранить".

4. **Безопасность и доступ**
   - Страница `/profile` использует уже существующий механизм аутентификации:
     - `get_user_from_cookie(request, db, settings)` для получения пользователя.
     - Если пользователь не найден — редирект на `/login`.
   - Работает только с текущим пользователем, без возможности менять чужие настройки.

## Архитектура решения

1. **Pages-уровень**
   - Новый модуль `app/pages/profile.py` с `APIRouter(tags=["pages"])`.
   - Два обработчика:
     - `@router.get("/profile", response_class=HTMLResponse)` — вывод формы.
     - `@router.post("/profile", response_class=HTMLResponse | RedirectResponse)` — обработка сабмита.
   - Использование:
     - `get_db`, `get_settings`.
     - `get_user_from_cookie`, `check_is_admin`, `templates` из `app/pages/common.py`.
     - `TIMEZONE_CHOICES`, `VALID_TIMEZONES` из `app/constants.py`.

2. **Template-уровень**

- Новый шаблон `app/templates/profile.html`:
  - Наследуется от `base.html`.
  - Принимает контекст:
    - `request`
    - `user`
    - `is_admin`
    - `active_page="profile"`
    - `timezone_choices=TIMEZONE_CHOICES`
    - `current_timezone=user.timezone`
    - Опционально сообщение об успехе / об ошибке.
  - Верстка и стили сохраняют текущий "Tailwind-like" стиль из других шаблонов.

3. **Навигация**

- В `base.html` (или другом шаблоне, где определено меню) добавляется пункт:
  - Ссылка на `/profile`.
  - Подсветка по `active_page == "profile"`.

4. **Дефолт для расписаний**

- В `app/pages/schedules.py`:
  - В обработчике, который отдаёт форму создания нового расписания, вычислить:
    - `default_timezone = user.timezone if user and user.timezone in VALID_TIMEZONES else "<старый дефолт>"`
  - Передать `default_timezone` в контекст шаблона.
- В `app/templates/schedules/form.html`:
  - В логике выбора `selected` для `<option>` учесть новый `default_timezone`, если `schedule` отсутствует (создание нового):
    - Если `schedule` есть — всё как сейчас.
    - Если `schedule` нет:
      - Если `default_timezone` есть и совпадает с `tz_value` — `selected`.
      - Иначе сохраняем текущее поведение (например, `Europe/Moscow` как финальный fallback).

## Тестирование

1. **Маршруты профиля**
   - Новый тестовый модуль, например `tests/test_pages/test_profile.py`.
   - Тесты:
     - `test_profile_requires_auth`: неавторизованный запрос на `/profile` редиректит на `/login`.
     - `test_profile_get_renders_form`: авторизованный пользователь видит select с текущей таймзоной по умолчанию.
     - `test_profile_post_updates_timezone`: отправка валидной таймзоны обновляет `user.timezone` в БД.
     - `test_profile_post_invalid_timezone_does_not_update`: невалидное значение не меняет таймзону (и, опционально, возвращает ошибку).

2. **Дефолт в расписаниях**
   - Расширить существующие тесты страниц/роутов расписаний или добавить новые:
     - `test_new_schedule_uses_user_timezone_as_default`: при `user.timezone = "Europe/Moscow"` в HTML формы `new schedule` опция `Europe/Moscow` помечена как selected.
     - `test_new_schedule_falls_back_when_user_timezone_invalid`: при `user.timezone = "Bad/Zone"` дефолт остаётся прежним (`Europe/Moscow` или `"UTC"`).

## Открытые вопросы / допущения

- Предполагается, что `User.timezone` и "дефолт для расписаний" — одно и то же. Если позже потребуется разделить эти концепции, можно будет добавить отдельное поле.
- Пока не добавляем другие настройки профиля (имя, язык и т.п.), чтобы не раздувать объём задачи.
- UX сообщений (ошибка / успех) реализуем в минимальном виде, без сложной системы флеш‑сообщений.

