from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MessengerAccount(Base):
    __tablename__ = "messenger_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    type: Mapped[str] = mapped_column(String(20))  # tg_user, wa
    credentials: Mapped[str] = mapped_column(Text)
    session_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="disconnected")
    # D-12: результат последней синхронизации живёт на аккаунте, а не в памяти
    # процесса — шапка «последняя синхронизация N назад» и сводка «найдено N,
    # новых M, обновлено имён K» обязаны переживать перезаход пользователя.
    #
    # NULL здесь означает «синхронизация ещё НЕ выполнялась» и обязан
    # отличаться от «синк дал ноль групп»: сразу после выката ревизии 0014 в
    # этом состоянии находятся ВСЕ существующие строки.
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Форма хранения (разрешение дискреции D-12, допущение A1 из RESEARCH):
    # JSON-строка вида {"found": N, "new": M, "renamed": K, "missing": J,
    # "error": null}, где error — текст ошибки синка либо null.
    #
    # Text, а не sa.JSON: тесты идут на SQLite in-memory, прод — на PostgreSQL,
    # и Text ведёт себя в обеих СУБД одинаково. Разбор — на стороне читателя
    # (`parse_sync_result`) с защитой от мусора: плашка результата обязана
    # деградировать в отсутствие плашки, а не в стек-трейс.
    last_sync_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    # D-01, D-02, D-14: номер аккаунта в E.164 — `+` и до 15 цифр, отсюда
    # String(16). NULL означает «номер неизвестен» и обязан отличаться от
    # пустой строки: сразу после выката ревизии 0023 в этом состоянии находятся
    # ВСЕ существующие строки, включая MAX, чей введённый номер лежит в
    # `credentials` (переносит его дозаполнение Фазы 20, а не ревизия).
    #
    # Уникальности НЕТ и не должно быть (D-02): один SIM законно даёт TG + WA +
    # MAX, а TG при пересканировании создаёт новую строку.
    #
    # Пишет колонку ТОЛЬКО `app/application/accounts/phone.py` (D-13) — правило
    # «ручное не затирается» держится лишь при одном писателе.
    phone: Mapped[str | None] = mapped_column(String(16), nullable=True)
    # Номер указан пользователем вручную: автоисточник его не затирает (D-07) —
    # условная запись автоисточника требует `NOT phone_is_manual`. Умолчание
    # `false` стоит и на стороне базы (`server_default`), чтобы строки, вставленные
    # мимо ORM, получали то же «не ручной», что и созданные приложением.
    phone_is_manual: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
