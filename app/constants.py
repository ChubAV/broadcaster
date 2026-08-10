TIMEZONE_CHOICES: list[tuple[str, str]] = [
    ("Europe/Kaliningrad", "Калининград (UTC+2)"),
    ("Europe/Moscow", "Москва (UTC+3)"),
    ("Europe/Samara", "Самара (UTC+4)"),
    ("Asia/Yekaterinburg", "Екатеринбург (UTC+5)"),
    ("Asia/Novosibirsk", "Новосибирск (UTC+6)"),
    ("Asia/Krasnoyarsk", "Красноярск (UTC+7)"),
    ("Asia/Irkutsk", "Иркутск (UTC+8)"),
    ("Asia/Yakutsk", "Якутск (UTC+9)"),
    ("Asia/Vladivostok", "Владивосток (UTC+10)"),
    ("Asia/Magadan", "Магадан (UTC+11)"),
    ("Asia/Kamchatka", "Камчатка (UTC+12)"),
    ("UTC", "UTC"),
]

VALID_TIMEZONES: set[str] = {tz[0] for tz in TIMEZONE_CHOICES}

# Состояние объявления (D-02). Единственный источник этих значений на весь
# проект: их читают модель, доменный подбор расписаний к отправке, схемы
# JSON-API и шаблон карточки списка. Литерал, выписанный в каждом из этих мест
# по отдельности, разъехался бы молча — объявление не отфильтровалось бы ни как
# черновик, ни как опубликованное.
#
# Значения строковые, а не sa.Enum: в проекте все статусы строковые
# (MessengerAccount.status сравнивается со строкой "active" прямо в доменном
# коде), а sa.Enum на PostgreSQL завёл бы именованный тип БД, который downgrade
# обязан удалять отдельным шагом — прецедента в проекте нет.
AD_STATUS_DRAFT: str = "draft"
AD_STATUS_PUBLISHED: str = "published"

AD_STATUSES: set[str] = {AD_STATUS_DRAFT, AD_STATUS_PUBLISHED}
