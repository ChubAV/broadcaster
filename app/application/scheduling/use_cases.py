from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.constants import AD_STATUS_DRAFT, AD_STATUS_PUBLISHED
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.services.schedule_service import compute_next_run_at

logger = structlog.get_logger(__name__)


def effective_ad_status(ad: Ad) -> str:
    """Состояние объявления с безопасным дефолтом.

    Всё, кроме опубликованного, считается черновиком — тот же безопасный
    дефолт, что и в карточке списка (UI-SPEC E15). Сторона отказа выбрана не
    симметрично: показать пользователю лишний бейдж «Черновик» — мелкая
    неточность, а отправить объявление с нераспознанным состоянием — рассылка
    в чужие группы, которую нельзя отозвать.
    """
    return AD_STATUS_PUBLISHED if ad.status == AD_STATUS_PUBLISHED else AD_STATUS_DRAFT


@dataclass(slots=True)
class DispatchTask:
    type: str
    ad_id: int
    group_id: int
    account_id: int
    # `None` — повтор записи журнала, у которой расписания нет (план 04-03).
    # Колонка `send_logs.schedule_id` nullable и внешним ключом не является
    # (ревизия 0005_sendlog_remove_fk_add_snapshots), поэтому осмысленного
    # числа для подстановки у такой отправки не существует. Ноль создал бы в
    # журнале ссылку на несуществующее расписание — значение проходит как есть.
    schedule_id: int | None
    # WA-specific fields (populated for type="wa")
    user_id: int | None = None
    ad_text: str | None = None
    ad_title: str | None = None
    ad_images: list[str] | None = None
    group_external_id: str | None = None
    group_name: str | None = None


def build_dispatch_task(
    *,
    ad: Ad,
    group: Group,
    account: MessengerAccount,
    schedule_id: int | None,
) -> DispatchTask:
    """Собирает задачу отправки — ОДНО определение на планировщик и повтор.

    ПОЧЕМУ ХЕЛПЕР ОДИН. Задачу отправки собирают два пути: планировщик
    (`collect_due_schedules` ниже) и повтор из истории (`retry_send` в
    `app/worker/tasks.py`). Состав задачи не сводится к четырём
    идентификаторам: для `wa` и `max` в неё кладётся вся полезная нагрузка
    очереди — текст, заголовок, развёрнутые в полные URL изображения, внешний
    идентификатор и имя группы, — потому что воркер аккаунта читает её из Redis
    и в базу не ходит. Две копии этого блока означают, что однажды поправят
    одну из двух, и повтор начнёт уезжать в очередь с составом полей, отличным
    от боевой рассылки, — молча, без падения тестов. Поэтому сборка живёт
    здесь, а оба пути её ВЫЗЫВАЮТ.

    Разворачивание ключей изображений в полные URL — часть сборки, а не
    вызывающего: в очередь обязан уехать адрес, доступный воркеру аккаунта, а
    не ключ хранилища. Пустое значение проходит как есть — разворачивать нечего.

    `schedule_id=None` — валидный вход: см. комментарий у поля `DispatchTask`.

    ЧЕГО ХЕЛПЕР НЕ ДЕЛАЕТ:
    - не ходит в БД и не принимает сессии: все три сущности передаются уже
      загруженными, и решение «что грузить» остаётся за вызывающим;
    - не диспетчеризует и не знает про Celery и Redis: маршрутизация по типу
      аккаунта живёт в `dispatch_send_tasks`, и второго её определения здесь
      не заводится;
    - не проверяет пригодность сущностей — ни статус аккаунта, ни черновик, ни
      включённость группы. Эти ветки различны у планировщика и у повтора и
      стоят у вызывающих.
    """
    task = DispatchTask(
        type=account.type,
        ad_id=ad.id,
        group_id=group.id,
        account_id=account.id,
        schedule_id=schedule_id,
    )
    # Populate WA-specific fields for Redis per-account queues.
    if account.type in ("wa", "max"):
        task.user_id = ad.user_id
        task.ad_text = ad.text
        task.ad_title = ad.title
        if ad.images:
            from app.services.s3 import get_image_url
            from app.config import get_settings
            s3_public_url = get_settings().s3_public_url
            task.ad_images = [get_image_url(img, s3_public_url) for img in ad.images]
        else:
            task.ad_images = ad.images
        task.group_external_id = group.group_external_id
        task.group_name = group.name
    return task


async def collect_due_schedules(
    session: AsyncSession,
    *,
    now: datetime | None = None,
    check_limit,
) -> list[DispatchTask]:
    """Логика выбора due-расписаний и подготовки задач отправки.

    Поведение повторяет текущее check_schedules_async, но без побочных эффектов вне БД.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    result = await session.execute(
        select(Schedule)
        .options(joinedload(Schedule.ad), joinedload(Schedule.account))
        .where(
            Schedule.is_active == True,  # noqa: E712
            Schedule.next_run_at <= now,
        )
    )
    schedules = result.unique().scalars().all()

    if not schedules:
        return []

    tasks_to_dispatch: list[DispatchTask] = []
    checked_users: dict[int, tuple[bool, str]] = {}

    for schedule in schedules:
        ad = schedule.ad
        account = schedule.account

        # D-01: расписание объявления-черновика к отправке не выбирается.
        #
        # Условие стоит В ЭТОЙ ВЕТКЕ, а не в WHERE запроса выше, и это не
        # стилистический выбор. Фильтр в WHERE тоже не создал бы задачи, но
        # оставил бы next_run_at в прошлом — и в момент публикации черновика
        # расписание выстрелило бы всеми накопленными пропущенными слотами
        # сразу, тихой рассылкой задним числом в чужие группы (T-02-12).
        # Ветка же пересчитывает next_run_at и продолжает цикл.
        #
        # schedule.ad уже загружен joinedload выше — дополнительного запроса
        # проверка не стоит.
        if (
            not ad
            or not account
            or account.status != "active"
            or effective_ad_status(ad) == AD_STATUS_DRAFT
        ):
            schedule.next_run_at = compute_next_run_at(
                days_of_week=schedule.days_of_week,
                times_of_day=schedule.times_of_day,
                tz_name=schedule.timezone,
                now=now,
            )
            continue

        user_id = ad.user_id
        if user_id not in checked_users:
            checked_users[user_id] = await check_limit(session, user_id, "send")

        allowed, _reason = checked_users[user_id]
        if not allowed:
            schedule.next_run_at = compute_next_run_at(
                days_of_week=schedule.days_of_week,
                times_of_day=schedule.times_of_day,
                tz_name=schedule.timezone,
                now=now,
            )
            continue

        for group_id in schedule.group_ids or []:
            group = await session.get(Group, group_id)

            # D-05: выключенная группа задач отправки не получает.
            #
            # Условие стоит В ЭТОМ ЦИКЛЕ, а не в WHERE выборки расписаний выше,
            # и это не стилистический выбор. Состав групп расписания хранится
            # JSON-списком в самом расписании (`Schedule.group_ids`), поэтому
            # фильтра по составу групп в том WHERE не построить вовсе. Но даже
            # будь он возможен, он был бы неверен: выключение группы НЕ меняет
            # состав расписания — тумблер обратим (D-08), и включение группы
            # обязано немедленно возобновить рассылку. Пропускается ГРУППА, а не
            # расписание: расчёт next_run_at ниже не трогается, иначе включение
            # группы выстрелило бы всеми накопленными пропущенными слотами.
            #
            # Пропуск ТИХИЙ: записи в SendLog здесь не создаётся и нового
            # статуса журнала не вводится (D-06) — история отражает реальные
            # попытки отправки, а не намерения. Единственный след — событие
            # structlog ниже.
            #
            # Объект группы поднят ВЫШЕ ветвления по account.type: до правки он
            # запрашивался только в ветке WA/MAX, и условие, оставленное внутри
            # неё, пропустило бы Telegram. Ветка ниже переиспользует уже
            # полученный объект.
            #
            # Парный тестовый файл tests/test_application/
            # test_collect_due_inactive_group.py — спецификация этого места.

            # СТРОКИ НЕТ — ЗАДАЧИ НЕТ. Висячий идентификатор в group_ids
            # (расписание пережило удаление группы) раньше проходил насквозь:
            # ветка выше не срабатывала (`if group and ...`), задача создавалась,
            # и дефект становился ТИХИМ. Для wa/max в очередь Redis уезжал
            # адресат `group_external_id=None`, для tg_user задача доезжала до
            # send_message_once и превращалась в запись журнала «Missing ad,
            # group, or account» — отказ отправки без единого намёка на причину.
            #
            # Проверка стоит ПЕРЕД проверкой включённости и отдельно от неё:
            # «группы нет» и «группа выключена» — разные события, и в логе они
            # обязаны быть различимы. Уровень WARNING, а не INFO: выключение —
            # решение пользователя, а висячая ссылка — расхождение данных.
            if group is None:
                logger.warning(
                    "group_skipped_missing",
                    group_id=group_id,
                    schedule_id=schedule.id,
                )
                continue

            if not group.is_active:
                logger.info(
                    "group_skipped_inactive",
                    group_id=group_id,
                    schedule_id=schedule.id,
                )
                continue

            # Сборка задачи — общий хелпер, а не блок на месте: тот же состав
            # полей уезжает в очередь при повторе из истории (план 04-03).
            # Второй проверки «группа есть» здесь нет намеренно: она была бы
            # вторым определением того же условия и разъехалась бы с первым.
            task = build_dispatch_task(
                ad=ad,
                group=group,
                account=account,
                schedule_id=schedule.id,
            )
            tasks_to_dispatch.append(task)

        schedule.next_run_at = compute_next_run_at(
            days_of_week=schedule.days_of_week,
            times_of_day=schedule.times_of_day,
            tz_name=schedule.timezone,
            now=now,
        )

    await session.commit()
    return tasks_to_dispatch


async def send_message_once(
    session: AsyncSession,
    *,
    ad_id: int,
    group_id: int,
    account_id: int,
    # `None` по тому же основанию, что у `DispatchTask.schedule_id`: отправка
    # без расписания — валидный случай, а колонка журнала nullable.
    schedule_id: int | None,
    messenger_factory: Any,
    settings: Any,
    task_id: str | None = None,
) -> None:
    """Общая доменная логика отправки одного сообщения.

    Функция не знает о Celery, только о БД и messenger-интерфейсе.
    """
    ad = await session.get(Ad, ad_id)
    group = await session.get(Group, group_id)
    account = await session.get(MessengerAccount, account_id)

    if not ad or not group or not account:
        log_entry = SendLog(
            user_id=ad.user_id if ad else 0,
            schedule_id=schedule_id,
            ad_id=ad_id,
            group_id=group_id,
            ad_title=ad.title if ad else None,
            ad_text=ad.text if ad else None,
            ad_images=ad.images if ad else None,
            group_name=group.name if group else None,
            messenger_type=account.type if account else None,
            task_id=task_id,
            status="fail",
            error_message="Missing ad, group, or account",
        )
        session.add(log_entry)
        await session.commit()
        return

    # Защита в глубину, а не замена ветке в collect_due_schedules (T-02-13):
    # задача может долететь до воркера уже после того, как объявление вернули
    # в черновик, — между подбором расписаний и отправкой проходит очередь.
    #
    # Статус записи "fail", а не новое слово: журнал отправок читают четыре
    # шаблона, и незнакомое значение отрисовалось бы там сырой латиницей.
    # Отправки не было, поэтому "fail" здесь честен, а причина названа в тексте
    # ошибки.
    if effective_ad_status(ad) == AD_STATUS_DRAFT:
        log_entry = SendLog(
            user_id=ad.user_id,
            schedule_id=schedule_id,
            ad_id=ad_id,
            group_id=group_id,
            ad_title=ad.title,
            ad_text=ad.text,
            ad_images=ad.images,
            group_name=group.name,
            messenger_type=account.type,
            task_id=task_id,
            status="fail",
            error_message=f"Ad {ad_id} is a draft",
        )
        session.add(log_entry)
        await session.commit()
        return

    if account.status != "active":
        log_entry = SendLog(
            user_id=ad.user_id,
            schedule_id=schedule_id,
            ad_id=ad_id,
            group_id=group_id,
            ad_title=ad.title,
            ad_text=ad.text,
            ad_images=ad.images,
            group_name=group.name,
            messenger_type=account.type,
            task_id=task_id,
            status="account_disconnected",
            error_message=f"Account {account.id} is {account.status}",
        )
        session.add(log_entry)
        await session.commit()
        return

    images: list[str] | None = None
    if ad.images:
        from app.services.s3 import get_image_url  # локальный импорт чтобы избежать циклов

        s3_public_url = settings.s3_public_url
        images = [get_image_url(img, s3_public_url) for img in ad.images]

    try:
        messenger = messenger_factory(account, settings)
    except ValueError as e:
        # Некорректная конфигурация мессенджера — считаем невосстанавливаемой ошибкой.
        log_entry = SendLog(
            user_id=ad.user_id,
            schedule_id=schedule_id,
            ad_id=ad_id,
            group_id=group_id,
            ad_title=ad.title,
            ad_text=ad.text,
            ad_images=ad.images,
            group_name=group.name,
            messenger_type=account.type,
            task_id=task_id,
            status="fail",
            error_message=str(e),
        )
        session.add(log_entry)
        await session.commit()
        return

    result = await messenger.send_message(
        group_id=group.group_external_id,
        text=ad.text,
        images=images,
    )

    status = "ok" if result.get("ok") else "fail"
    log_entry = SendLog(
        user_id=ad.user_id,
        schedule_id=schedule_id,
        ad_id=ad_id,
        group_id=group_id,
        ad_title=ad.title,
        ad_text=ad.text,
        ad_images=ad.images,
        group_name=group.name,
        messenger_type=account.type,
        task_id=task_id,
        status=status,
        error_message=result.get("error"),
    )
    session.add(log_entry)

    if status == "ok":
        from app.services.billing_service import deduct_message
        from app.services.billing_cache import invalidate_balance_cache
        await deduct_message(session, ad.user_id)
        await invalidate_balance_cache(ad.user_id)

    await session.commit()

    # Ошибка с флагом no_retry помечает группу, но не выбрасывает исключение.
    if not result.get("ok"):
        error = result.get("error")
        if result.get("no_retry"):
            group.last_error = error
            group.error_at = datetime.now(timezone.utc)
            await session.commit()
        else:
            raise Exception(f"Send failed: {error}")
    else:
        if group.last_error:
            group.last_error = None
            group.error_at = None
            await session.commit()

