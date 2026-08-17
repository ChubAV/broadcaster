from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    yookassa_payment_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="pending")
    amount_value: Mapped[str] = mapped_column(String(50))
    amount_currency: Mapped[str] = mapped_column(String(10), default="RUB")
    # ПРЕДМЕТ ПОКУПКИ ХРАНИТСЯ СВОЕЙ КОЛОНКОЙ, а не выводится из заполненности
    # соседних полей. Обработчик вебхука решает по ней, что выдать, и решение
    # обязано опираться на строку СВОЕЙ базы, а не на `metadata` уведомления:
    # уведомление приезжает извне (T-05-02).
    #
    # String, а не sa.Enum: причина выписана в app/constants.py:24-27 —
    # именованный тип PostgreSQL потребовал бы отдельного шага в downgrade
    # каждой ревизии, и прецедента в проекте нет.
    kind: Mapped[str] = mapped_column(String(50), default="package")
    plan: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # УСЛОВИЯ СДЕЛКИ ХРАНЯТСЯ СВОЕЙ КОЛОНКОЙ — ОТВЕТ ГАРДА, СНЯТЫЙ В МОМЕНТ
    # ПРОДАЖИ (D-28). Третья колонка тройки «предмет и условия сделки» рядом с
    # `kind` и `plan`. Между продажей и подтверждением лежит вся сессия оплаты у
    # ЮKassa, и состояние подписки за это время меняется — самим пользователем,
    # соседним платежом или временем. Пока ответ нигде не записан, стадия
    # применения принимает решение ЗАНОВО по изменившейся строке подписки и
    # выдаёт не то, что было продано (гэп 1 раунда 4).
    #
    # ЗНАЧЕНИЙ ТРИ, А НЕ ДВА:
    #   True  — правило спросили в момент продажи, и оно переход РАЗРЕШИЛО;
    #   False — спросили, и оно ОТВЕРГЛО. Через форму сегодня недостижимо (отказ
    #           возвращает 302 ДО создания платежа), но колонка обязана уметь это
    #           выразить: иначе следующий писатель выразит отказ через NULL;
    #   NULL  — правило НЕ СПРАШИВАЛИ. Пакетный платёж (тарифа он не касается)
    #           либо строка старше ревизии 0019.
    #
    # ⚠️ NULL НЕ ОЗНАЧАЕТ «НЕТ», И ИМЕННО ПОЭТОМУ У КОЛОНКИ НЕТ `server_default`.
    # Умолчание проставило бы КАЖДОЙ существующей строке ответ, которого у неё
    # никогда не было: `False` записал бы отказ, которого не случалось, `True` —
    # разрешение, которого никто не давал. У строки, заведённой до колонки,
    # записанному ответу взяться неоткуда, и выдумать его хуже, чем пересчитать
    # правилом — что стадия применения для NULL и делает.
    #
    # Новые строки без ответа не заводятся: `switch_authorized` — обязательный
    # keyword-only параметр `create_payment`, и вызов без него падает TypeError.
    switch_authorized: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # NULL с появлением подписок: у платежа за тариф сообщений не покупается
    # вовсе, и ноль здесь читался бы как «куплено ноль сообщений».
    messages_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    package_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
