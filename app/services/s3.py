"""Адрес объекта, запись объекта и три чтения над одним открытым клиентом.

До задачи 260825-hnf модуль умел ровно две вещи — построить публичный адрес и
положить объект, — потому что единственным его вызывающим был маршрут загрузки,
а маршруту хватает одной записи на запрос. Обслуживающему прогону этого мало: он
идёт по сотням ключей, и ему нужны чтение, проверка существования производного
объекта и ОДИН клиент на весь проход вместо клиента на объект.

ПОЧЕМУ ЗАПИСЬ РАЗДЕЛЕНА НА ДВА УРОВНЯ. ``upload_file_to_s3`` открывает клиента
сам и потому годится только там, где вызов одиночный. ``put_object_bytes``
принимает уже открытого клиента и потому годится в цикле. Второй не КОПИЯ
первого, а его тело: ``upload_file_to_s3`` теперь делегирует, и это не
аккуратность ради аккуратности — две копии одного вызова разъехались бы по
``ContentType``, а именно он на этом пути защищает от подмены типа отдаваемых
браузеру байтов.

ПОЧЕМУ ПРИМИТИВ ЗОВЁТСЯ ``put_object_bytes``, А НЕ ``put_object``. Второе имя
затенило бы внутри этого же модуля одноимённый метод клиента ``aiobotocore``, и
делегирующее тело читалось бы как рекурсия. Метод клиента при этом зовётся
прежним именем, и существующая регрессия утверждает аргументы именно его.

ПОЧЕМУ ОТСУТСТВИЕ ОБЪЕКТА — ЭТО ``None``, А ОСТАЛЬНЫЕ ОТКАЗЫ — ИСКЛЮЧЕНИЯ.
«Объекта нет» — обычный и ожидаемый ответ для вызывающего, который как раз и
спрашивает, есть ли миниатюра. «Отказано в доступе» и «хранилище недоступно» —
не ответы, а поломки, и решение о том, что с ними делать, принадлежит
вызывающему. Молчаливое ``None`` на ЛЮБОЙ ошибке превратило бы отчёт
обслуживающего прогона в ложь: недоступный бакет отчитался бы строкой «работы
нет».
"""

from contextlib import asynccontextmanager
from dataclasses import dataclass

from aiobotocore.session import AioSession
from botocore.exceptions import ClientError

# Сколько первых байтов объекта выкачивается ради заявленных размеров.
#
# ЧИСЛО ВЫБРАНО ПО ФОРМЕ ЗАГОЛОВКОВ, А НЕ НА ГЛАЗ. У PNG размеры лежат в первых
# 33 байтах — блок IHDR стоит сразу за сигнатурой. У JPEG маркер размеров SOF
# стоит ЗА секциями метаданных, а одна секция APP1/EXIF по формату может занять
# до 64 КиБ сама по себе, и превью внутри неё регулярно занимает десятки
# килобайт. 64 КиБ покрывают обычный снимок с телефона; редкий случай, когда не
# покрывают, закрывается ОТКАТОМ на полное чтение у вызывающего, а не
# расширением этой константы наугад — расширять её значило бы платить трафиком
# за каждый объект ради нескольких.
HEAD_READ_BYTES = 65_536

# Коды, которыми хранилище сообщает «такого объекта нет». Три, а не один:
# `get_object` отвечает `NoSuchKey`, `head_object` — голым `404`, а часть
# S3-совместимых реализаций подставляет `NotFound`.
_MISSING_OBJECT_CODES = frozenset({"NoSuchKey", "NotFound", "404"})

# Код отказа «запрошенный диапазон за концом объекта». Приходит на пустой
# объект: диапазон `bytes=0-65535` для нулевой длины неудовлетворим.
_INVALID_RANGE_CODE = "InvalidRange"


@dataclass(frozen=True)
class ObjectHead:
    """Первые байты объекта и ПОЛНЫЙ его размер.

    Поле ``size`` лежит здесь, а не добывается отдельным запросом, потому что
    хранилище называет полный размер в заголовке ``Content-Range`` ТОГО ЖЕ
    ответа: `bytes 0-65535/4194304`. Спрашивать вес вторым запросом значило бы
    удвоить число обращений ради числа, которое уже пришло.

    Когда хранилище диапазон проигнорировало и отдало объект целиком, заголовка
    ``Content-Range`` в ответе нет — тогда размер берётся из ``ContentLength``,
    и это не приближение: тело в этом случае и так полное.
    """

    body: bytes
    size: int


def get_image_url(key: str, s3_public_url: str) -> str:
    """Build a public URL for an S3 object key."""
    if not key:
        return ""
    base = s3_public_url.rstrip("/")
    return f"{base}/{key}"


@asynccontextmanager
async def open_s3_client(
    endpoint_url: str,
    access_key: str,
    secret_key: str,
    region: str = "",
):
    """Открыть клиента хранилища на время блока.

    Вынесено из ``upload_file_to_s3`` без изменения смысла: ``region_name``
    подставляется только при непустом значении, потому что пустая строка — не
    «регион по умолчанию», а регион с пустым именем.
    """
    session = AioSession()
    client_kwargs = {
        "service_name": "s3",
        "endpoint_url": endpoint_url,
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
    }
    if region:
        client_kwargs["region_name"] = region

    async with session.create_client(**client_kwargs) as client:
        yield client


def _error_code(exc: ClientError) -> str:
    return str(exc.response.get("Error", {}).get("Code", ""))


async def put_object_bytes(
    client,
    bucket: str,
    key: str,
    content: bytes,
    content_type: str,
) -> str:
    """Положить байты в хранилище через УЖЕ ОТКРЫТОГО клиента."""
    await client.put_object(
        Bucket=bucket,
        Key=key,
        Body=content,
        ContentType=content_type,
    )
    return key


async def read_object_head(
    client,
    bucket: str,
    key: str,
    size: int = HEAD_READ_BYTES,
) -> ObjectHead | None:
    """Прочитать первые ``size`` байтов объекта и узнать его полный размер.

    Отсутствующий объект даёт ``None``. Пустой объект даёт ``ObjectHead(b"", 0)``:
    диапазон для нулевой длины неудовлетворим, и хранилище отвечает отказом, но
    «объект есть и он пуст» — не то же самое, что «объекта нет».
    """
    try:
        response = await client.get_object(
            Bucket=bucket, Key=key, Range=f"bytes=0-{size - 1}"
        )
    except ClientError as exc:
        code = _error_code(exc)
        if code in _MISSING_OBJECT_CODES:
            return None
        if code == _INVALID_RANGE_CODE:
            return ObjectHead(body=b"", size=0)
        raise

    body = await response["Body"].read()

    content_range = response.get("ContentRange")
    if content_range and "/" in content_range:
        total = content_range.rsplit("/", 1)[1]
        if total.isdigit():
            return ObjectHead(body=body, size=int(total))

    return ObjectHead(body=body, size=int(response.get("ContentLength", len(body))))


async def read_object(client, bucket: str, key: str) -> bytes | None:
    """Прочитать объект целиком. Отсутствующий объект даёт ``None``."""
    try:
        response = await client.get_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        if _error_code(exc) in _MISSING_OBJECT_CODES:
            return None
        raise

    return await response["Body"].read()


async def object_exists(client, bucket: str, key: str) -> bool:
    """Есть ли объект под этим ключом.

    Запрашиваются только заголовки: вызывающему нужен факт существования
    миниатюры, а не её байты, и выкачивать их ради ответа «да» значило бы
    платить трафиком за каждое вложение, у которого миниатюра уже есть.
    """
    try:
        await client.head_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        if _error_code(exc) in _MISSING_OBJECT_CODES:
            return False
        raise

    return True


async def upload_file_to_s3(
    content: bytes,
    key: str,
    content_type: str,
    endpoint_url: str,
    access_key: str,
    secret_key: str,
    bucket: str,
    region: str = "",
) -> str:
    """Upload file to S3 and return the object key."""
    async with open_s3_client(endpoint_url, access_key, secret_key, region) as client:
        return await put_object_bytes(client, bucket, key, content, content_type)
