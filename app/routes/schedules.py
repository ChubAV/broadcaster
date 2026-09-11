from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import VALID_TIMEZONES
from app.dependencies import get_current_user_id, get_db
from app.models.messenger_account import MessengerAccount
from app.repositories.ad import AdRepository
from app.repositories.schedule import ScheduleRepository
from app.services.schedule_rules import (
    DAY_OF_WEEK_MAX,
    DAY_OF_WEEK_MIN,
    is_schedule_complete,
    is_valid_day_of_week,
    is_valid_time_of_day,
    owned_group_ids,
)
from app.services.schedule_service import compute_next_run_at

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


# ─── ОБЛАСТЬ ЗНАЧЕНИЙ ДНЕЙ И ВРЕМЁН НА JSON-ВХОДЕ ───────────────────────────
#
# ⚠️ ЭТОГО НЕ БЫЛО ЗДЕСЬ ВОВСЕ, И ПОСЛЕДСТВИЯ БЫЛИ РАЗНЫЕ ПО ТЯЖЕСТИ.
# Правило «какие значения система умеет исполнять» жило только на страничном
# входе (`_TIME_RE`, `_clean_ints(low=0, high=6)`), а испорченное значение
# отсюда доезжало прямо в `compute_next_run_at`:
#
#   - ВРЕМЯ ломало разбор — `int(parts[0])` / `parts[1]` идут без защиты, и
#     «abc», «25:00», «12:99» давали 500. Строка при этом не писалась.
#
#   - ДЕНЬ ВНЕ ДИАПАЗОНА разбор ПРОХОДИЛ и потому был страшнее: список `[9]`
#     НЕПУСТ, поэтому `is_schedule_complete` отвечал True, а
#     `compute_next_run_at` не встречал девятого дня недели в своём окне
#     day_offset 0..7 и возвращал None. Получалась строка `is_active=true` при
#     `next_run_at=NULL` — В ТОЧНОСТИ форма промышленной строки sched=48, ЧЕРЕЗ
#     ЭТОТ ЖЕ МАРШРУТ, уже после правки, которая его закрывала. Такая строка
#     мертва навсегда и молча: отбор фильтрует `is_active AND next_run_at <= now`,
#     а `NULL <= now` в SQL не истинно никогда, и пересчёт `next_run_at` идёт
#     только по УЖЕ ВЫБРАННЫМ строкам. Обновление тем же путём УБИВАЛО живое
#     расписание, а не только рождало мёртвое.
#
# ⚠️ ЗАЯВЛЕНИЕ ПРЕЖНЕЙ ПРАВКИ БЫЛО ШИРЕ ФАКТА. Комментарий ниже утверждал, что
# согласованность правил держится по построению, ибо `compute_next_run_at`
# возвращает None «ровно на пустых днях ИЛИ временах». Пустота — не единственное
# такое условие. Теперь утверждение ВЕРНО, но лишь потому, что вход отсекает
# значения не той области ДО расчёта; сам по себе, без этой отсечки, оно ложно.
#
# ПОЧЕМУ ОТКАЗ (422), А НА НЕПОЛНОТУ — НЕ ОТКАЗ. Это ответы на разные вопросы.
# Неполное расписание — законное промежуточное состояние черновика, его
# сохраняют выключенным и страница, и обновление этого же API. А «abc» — не
# время, `9` — не день недели: такого состояния в предметной области нет вовсе.
# Этот вход на испорченное ЗНАЧЕНИЕ ПОЛЯ отказывает с самого начала (незнакомый
# `timezone`) и отказывает на явном null (CR-03) — здесь то же поведение, а не
# третье.
#
# ПОЧЕМУ НЕ ОТБРАСЫВАНИЕ, КАК НА СТРАНИЦЕ. Форма шлёт повторяющиеся поля и не
# умеет сказать, какое из них отброшено, — потому страница и отбрасывает.
# JSON-клиент прислал ОДИН документ: сохранить его наполовину значило бы отдать
# 201 на расписание, времена которого клиент не присылал.


def _reject_out_of_range_days(values: list[int] | None) -> list[int] | None:
    if values is None:
        return values
    bad = [value for value in values if not is_valid_day_of_week(value)]
    if bad:
        raise ValueError(
            f"День недели вне диапазона {DAY_OF_WEEK_MIN}..{DAY_OF_WEEK_MAX} "
            f"(0 — понедельник): {bad}"
        )
    return values


def _reject_malformed_times(values: list[str] | None) -> list[str] | None:
    if values is None:
        return values
    bad = [value for value in values if not is_valid_time_of_day(value)]
    if bad:
        raise ValueError(
            f"Время должно быть в формате ЧЧ:ММ от 00:00 до 23:59 "
            f"(час — двумя цифрами): {bad}"
        )
    return values


class CreateScheduleRequest(BaseModel):
    ad_id: int
    account_id: int
    group_ids: list[int] = []
    days_of_week: list[int] = []
    times_of_day: list[str] = []
    timezone: str = "UTC"

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        if v not in VALID_TIMEZONES:
            raise ValueError(f"Invalid timezone: {v}")
        return v

    @field_validator("days_of_week")
    @classmethod
    def validate_days_of_week(cls, v: list[int]) -> list[int]:
        return _reject_out_of_range_days(v)

    @field_validator("times_of_day")
    @classmethod
    def validate_times_of_day(cls, v: list[str]) -> list[str]:
        return _reject_malformed_times(v)


class UpdateScheduleRequest(BaseModel):
    group_ids: list[int] | None = None
    days_of_week: list[int] | None = None
    times_of_day: list[str] | None = None
    timezone: str | None = None

    # CR-03: явный null — 422 ДО какой-либо записи в модель. `exclude_unset`
    # отличает отсутствующий ключ от присланного, но не присланный-и-пустой:
    # тело {"group_ids": null} считалось присланным, None доезжал до setattr, и
    # в JSON-колонку ложился документ `null` — запись, которую невозможно
    # прочитать обратно (ScheduleResponse требует list/str), то есть 500 на
    # каждом последующем чтении списка. Валидаторы pydantic не запускаются на
    # значениях по умолчанию, поэтому None здесь означает ровно присланный
    # null — отсутствующий ключ по-прежнему означает «не трогать» (D-15).
    @field_validator("group_ids", "days_of_week", "times_of_day", "timezone")
    @classmethod
    def reject_explicit_null(cls, v):
        if v is None:
            raise ValueError(
                "Явный null не принимается: чтобы не трогать поле, опустите ключ"
            )
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_TIMEZONES:
            raise ValueError(f"Invalid timezone: {v}")
        return v

    # Валидаторы одного поля запускаются в ПОРЯДКЕ ОБЪЯВЛЕНИЯ, поэтому явный
    # null отсекается выше и сюда доезжает либо список, либо отсутствие ключа.
    # Проверка на None всё равно стоит: она не даёт порядку объявления стать
    # несущей конструкцией, о которой знает только автор.
    @field_validator("days_of_week")
    @classmethod
    def validate_days_of_week(cls, v: list[int] | None) -> list[int] | None:
        return _reject_out_of_range_days(v)

    @field_validator("times_of_day")
    @classmethod
    def validate_times_of_day(cls, v: list[str] | None) -> list[str] | None:
        return _reject_malformed_times(v)


class ScheduleResponse(BaseModel):
    id: int
    ad_id: int
    # None, если аккаунт был удалён и расписание отвязано (issue #35).
    # CreateScheduleRequest.account_id остаётся обязательным.
    account_id: int | None
    group_ids: list
    days_of_week: list
    times_of_day: list
    timezone: str
    is_active: bool
    next_run_at: datetime | None
    created_at: datetime


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    data: CreateScheduleRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    ad_repo = AdRepository(db)
    ad = await ad_repo.get_by_id_and_user(data.ad_id, user_id)
    if ad is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ad not found",
        )

    # Владение объявлением проверялось здесь с самого начала, владение аккаунтом
    # — нет; асимметрия и была находкой CR-01/D-20: чужой `account_id`
    # принимался, и рассылка ушла бы через чужую подключённую сессию мессенджера.
    # Форма проверки — та же, что строкой выше: чужой идентификатор неотличим от
    # несуществующего и даёт 404, не подтверждая существование чужой записи.
    account = (
        await db.execute(
            select(MessengerAccount.id).where(
                MessengerAccount.id == data.account_id,
                MessengerAccount.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    # Владение ГРУППАМИ — третья сторона того же треугольника, и до этого плана
    # её здесь не было вовсе (CR-02, T-02G-06). `Schedule` не имеет своего
    # `user_id`, а `group_ids` хранятся массивом: ниже по потоку
    # `collect_due_schedules` итерирует их как есть, `send_message_once`
    # резолвит группу по первичному ключу, и владельца не перепроверяет никто.
    # Чужой идентификатор, принятый здесь, доезжает до `SendLog` со СВОИМ
    # `user_id`. Проверка стоит ДО расчёта следующего запуска и ДО записи.
    owned = await owned_group_ids(db, user_id, data.account_id, data.group_ids)
    if set(data.group_ids) - owned:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    # D-08 НА ВХОДЕ СОЗДАНИЯ — последнее место записи, которое оставалось вне
    # общего правила полноты. Обновление и тумблер этого же файла свели к
    # `is_schedule_complete` раньше (WR-05), а создание — нет, и дыра была ровно
    # в пропущенном здесь `is_active`.
    #
    # ЧТО ПРОИСХОДИЛО. Аргумент `is_active` в вызов не передавался вовсе, поэтому
    # `BaseRepository.create` строил модель с УМОЛЧАНИЕМ КОЛОНКИ — `default=True`
    # (`app/models/schedule.py`). Рядом `compute_next_run_at` возвращает None на
    # пустом списке дней или времён. Тело запроса с пустым `days_of_week` —
    # законное по схеме, `CreateScheduleRequest` объявляет его `= []` и ничем не
    # ограничивает — давало строку `is_active=true` при `next_run_at=NULL`.
    #
    # ПОЧЕМУ ЭТО НЕ «ПРОСТО НЕАККУРАТНОЕ ПОЛЕ». Такая строка МЕРТВА НАВСЕГДА и
    # молча. Отбор к отправке фильтрует `is_active = true AND next_run_at <= now`,
    # а `NULL <= now` в SQL не истинно никогда — строка не выбирается. Ветка же,
    # которая `next_run_at` ПЕРЕСЧИТЫВАЕТ, живёт ВНУТРИ цикла по уже выбранным
    # строкам (`app/application/scheduling/use_cases.py`), то есть на
    # невыбираемой строке не выполняется тоже: самовосстановления нет. Ни
    # ограничения в базе, ни чинящей задачи в проекте не существует, а сводка
    # инцидентов ищет ПРОСРОЧЕННЫЕ (`next_run_at.is_not(None)`) и такую строку
    # по построению не видит. Пользователю при этом показывается ВКЛЮЧЁННОЕ
    # расписание, которое не отправит ничего и никогда.
    #
    # ПОЧЕМУ НЕ ОТКАЗ (422). Неполнота — законное промежуточное состояние, а не
    # ошибка запроса: страничный создатель сохраняет неполное расписание
    # выключенным, и обновление этого же JSON-API — тоже. Отказ здесь стал бы
    # ТРЕТЬИМ поведением на одно правило.
    #
    # ⚠️ СОГЛАСОВАННОСТЬ ДВУХ ПРАВИЛ — С ОГОВОРКОЙ, КОТОРОЙ ЗДЕСЬ РАНЬШЕ НЕ БЫЛО.
    # Прежний текст этого абзаца утверждал, что согласованность держится по
    # построению, ибо `compute_next_run_at` возвращает None «ровно на пустых днях
    # ИЛИ временах». ЭТО БЫЛО НЕВЕРНО: функция возвращает None и на НЕПУСТОМ
    # списке дней вне 0..6 — кандидатов в её окне не находится вовсе. То есть
    # форма мёртвой строки оставалась достижима через этот самый маршрут и после
    # правки, закрывавшей его.
    #
    # Утверждение верно СЕЙЧАС и держится не на самих правилах, а на том, что
    # область значений отсечена ВЫШЕ — валидаторами `CreateScheduleRequest`
    # (`_reject_out_of_range_days`, `_reject_malformed_times`), то есть ДО того,
    # как значение доедет сюда. Расхождение впредь ловят
    # tests/test_routes/test_schedules_api_create_completeness.py (полнота) и
    # tests/test_routes/test_schedules_api_value_domain.py (область значений), а
    # последним рубежом стоит ограничение СУБД
    # `ck_schedules_active_requires_next_run` (ревизия 0022), потому что
    # прикладная проверка делает состояние недостижимым, но не невозможным.
    complete = is_schedule_complete(
        data.account_id,
        data.group_ids,
        data.days_of_week,
        data.times_of_day,
    )
    next_run = (
        compute_next_run_at(
            days_of_week=data.days_of_week,
            times_of_day=data.times_of_day,
            tz_name=data.timezone,
        )
        if complete
        else None
    )

    schedule_repo = ScheduleRepository(db)
    schedule = await schedule_repo.create(
        ad_id=data.ad_id,
        account_id=data.account_id,
        group_ids=data.group_ids,
        days_of_week=data.days_of_week,
        times_of_day=data.times_of_day,
        timezone=data.timezone,
        is_active=complete,
        next_run_at=next_run,
    )
    return schedule


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = ScheduleRepository(db)
    return await repo.list_for_user(user_id)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    data: UpdateScheduleRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = ScheduleRepository(db)
    schedule = await repo.get_for_user(schedule_id, user_id)
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    # Проверка ровно тогда, когда поле ПРИСУТСТВУЕТ в патче: отсутствующий ключ
    # означает «не трогать», и отказ на нём превратил бы частичное обновление в
    # обязательную передачу всего состава групп. Аккаунт на update не меняется
    # (`UpdateScheduleRequest` его не содержит), поэтому группы сверяются с
    # аккаунтом уже сохранённой записи. Проверка стоит до первой записи в
    # модель, иначе отказ оставил бы запись частично изменённой.
    if "group_ids" in update_data:
        requested = update_data["group_ids"] or []
        owned = await owned_group_ids(db, user_id, schedule.account_id, requested)
        if set(requested) - owned:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found",
            )

    for field, value in update_data.items():
        setattr(schedule, field, value)

    # Пересчёт зеркалит страничный слой (`app/pages/schedules.py`): неполное
    # расписание выключается всегда (D-08); полное активное — пересчитывается;
    # полное, но приостановленное, времени ближайшего запуска НЕ несёт.
    # Безусловный пересчёт, стоявший здесь раньше, рекламировал в сводке
    # редактора отправку, которой не будет (WR-06, T-02G-09).
    if not is_schedule_complete(
        schedule.account_id,
        schedule.group_ids or [],
        schedule.days_of_week or [],
        schedule.times_of_day or [],
    ):
        schedule.is_active = False
        schedule.next_run_at = None
    elif schedule.is_active:
        schedule.next_run_at = compute_next_run_at(
            days_of_week=schedule.days_of_week,
            times_of_day=schedule.times_of_day,
            tz_name=schedule.timezone,
        )
    else:
        schedule.next_run_at = None

    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = ScheduleRepository(db)
    schedule = await repo.get_for_user(schedule_id, user_id)
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )
    await repo.delete(schedule)


@router.post("/{schedule_id}/toggle", response_model=ScheduleResponse)
async def toggle_schedule(
    schedule_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    repo = ScheduleRepository(db)
    schedule = await repo.get_for_user(schedule_id, user_id)
    if schedule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found",
        )

    # D-08: НЕПОЛНОЕ расписание нельзя возобновить — отправить ему нечего и
    # некуда. Прежнее правило issue #35 («нет аккаунта — нельзя возобновить»)
    # ПОГЛОЩЕНО этим: `is_schedule_complete` требует непустой `account_id`, и
    # отвязанное расписание стало его частным случаем. Двух текстов сообщения
    # одновременно быть не может, поэтому оставлен один — общий; регрессия
    # issue #35 (`tests/test_routes/test_schedules_toggle_detached.py`)
    # проверяет коды ответа, а не формулировку, и поглощение её не задевает.
    #
    # Определение полноты — то же самое, что у страничного тумблера: до этого
    # плана здесь стояло своё, и одно и то же расписание страница включать
    # отказывалась, а JSON-API включал (WR-05, T-02G-08).
    #
    # Постановка на паузу активного расписания не блокируется: право поставить
    # на паузу не зависит от заполненности.
    if not schedule.is_active and not is_schedule_complete(
        schedule.account_id,
        schedule.group_ids or [],
        schedule.days_of_week or [],
        schedule.times_of_day or [],
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала дозаполните расписание в редакторе объявления",
        )

    schedule.is_active = not schedule.is_active

    if schedule.is_active:
        # Recompute next_run_at when activating
        schedule.next_run_at = compute_next_run_at(
            days_of_week=schedule.days_of_week,
            times_of_day=schedule.times_of_day,
            tz_name=schedule.timezone,
        )
    else:
        schedule.next_run_at = None

    await db.commit()
    await db.refresh(schedule)
    return schedule
