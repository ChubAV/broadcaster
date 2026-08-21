from app.models.user import User
from app.models.subscription import Subscription
from app.models.messenger_account import MessengerAccount
from app.models.ad import Ad
from app.models.group import Group
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.models.telegram_auth_session import TelegramAuthSession
from app.models.email_verification import EmailVerificationCode
from app.models.payment import Payment
from app.models.group_info import GroupInfo

__all__ = [
    "User",
    "Subscription",
    "MessengerAccount",
    "Ad",
    "Group",
    "Schedule",
    "SendLog",
    "TelegramAuthSession",
    "EmailVerificationCode",
    "Payment",
    "GroupInfo",
]

# ДВУХ МОДЕЛЕЙ ВАЛЮТЫ СООБЩЕНИЙ ЗДЕСЬ БОЛЬШЕ НЕТ, И ЭТО СНЯТИЕ ПРЕДМЕТА.
# Ревизия `0020` уронила таблицы `message_balances` и `balance_transactions`
# вместе с колонкой тарифа подписки: сообщения бесплатны у всех (D-D), учитывать
# нечего. Сборник моделей строит схему тестовой суиты через
# `Base.metadata.create_all`, поэтому оставленный здесь импорт вернул бы таблицы
# в тестовую базу и развёл её с боевой схемой молча.

