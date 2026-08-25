import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from botocore.exceptions import ClientError

from app.services.s3 import (
    ObjectHead,
    get_image_url,
    object_exists,
    put_object_bytes,
    read_object,
    read_object_head,
    upload_file_to_s3,
)


def test_get_image_url():
    """get_image_url builds URL from s3_public_url + key."""
    url = get_image_url("1/abc123_photo.jpg", "https://cdn.example.com/bucket")
    assert url == "https://cdn.example.com/bucket/1/abc123_photo.jpg"


def test_get_image_url_strips_trailing_slash():
    url = get_image_url("1/photo.jpg", "https://cdn.example.com/bucket/")
    assert url == "https://cdn.example.com/bucket/1/photo.jpg"


def test_get_image_url_empty_key():
    url = get_image_url("", "https://cdn.example.com/bucket")
    assert url == ""


@pytest.mark.asyncio
async def test_upload_file_to_s3():
    """upload_file_to_s3 calls S3 put_object with correct params."""
    mock_client = AsyncMock()
    mock_client.put_object = AsyncMock()

    mock_session = MagicMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session.create_client.return_value = mock_ctx

    with patch("app.services.s3.AioSession", return_value=mock_session):
        key = await upload_file_to_s3(
            content=b"image-bytes",
            key="1/photo.jpg",
            content_type="image/png",
            endpoint_url="https://s3.example.com",
            access_key="AKID",
            secret_key="SECRET",
            bucket="my-bucket",
            region="us-east-1",
        )

    assert key == "1/photo.jpg"
    mock_client.put_object.assert_called_once_with(
        Bucket="my-bucket",
        Key="1/photo.jpg",
        Body=b"image-bytes",
        ContentType="image/png",
    )


# --- Чтения над уже открытым клиентом (quick 260825-hnf) ----------------------
#
# Функции ниже принимают клиента аргументом, поэтому подменять `AioSession` им
# незачем: двойник передаётся напрямую. Тест записи выше остался НЕТРОНУТЫМ — он
# и есть доказательство, что единственный писатель в S3 поведения не изменил,
# хотя его тело теперь делегирует новому примитиву.


class _Body:
    """Тело ответа хранилища: настоящий клиент отдаёт поток, а не байты."""

    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    async def read(self) -> bytes:
        return self._payload


def _client_error(code: str, operation: str = "GetObject") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, operation)


@pytest.mark.asyncio
async def test_read_object_head_asks_for_a_range_and_returns_the_full_size():
    """Полный размер снят с `Content-Range`, а не с длины полученного тела."""
    client = AsyncMock()
    client.get_object = AsyncMock(
        return_value={
            "Body": _Body(b"first-bytes"),
            "ContentRange": "bytes 0-65535/4194304",
            "ContentLength": 65536,
        }
    )

    head = await read_object_head(client, "my-bucket", "1/photo.jpg", size=65536)

    assert head == ObjectHead(body=b"first-bytes", size=4194304)
    client.get_object.assert_called_once_with(
        Bucket="my-bucket", Key="1/photo.jpg", Range="bytes=0-65535"
    )


@pytest.mark.asyncio
async def test_read_object_head_falls_back_to_content_length():
    """Хранилище диапазон проигнорировало: тело полное, размер — из длины."""
    client = AsyncMock()
    client.get_object = AsyncMock(
        return_value={"Body": _Body(b"whole-object"), "ContentLength": 12}
    )

    head = await read_object_head(client, "my-bucket", "1/photo.jpg")

    assert head == ObjectHead(body=b"whole-object", size=12)


@pytest.mark.asyncio
async def test_read_object_head_treats_an_unsatisfiable_range_as_an_empty_object():
    """«Объект есть и он пуст» — не то же самое, что «объекта нет»."""
    client = AsyncMock()
    client.get_object = AsyncMock(side_effect=_client_error("InvalidRange"))

    head = await read_object_head(client, "my-bucket", "1/empty.jpg")

    assert head == ObjectHead(body=b"", size=0)


@pytest.mark.asyncio
async def test_read_object_head_returns_none_for_a_missing_key():
    client = AsyncMock()
    client.get_object = AsyncMock(side_effect=_client_error("NoSuchKey"))

    assert await read_object_head(client, "my-bucket", "1/gone.jpg") is None


@pytest.mark.asyncio
async def test_read_object_returns_the_whole_body():
    client = AsyncMock()
    client.get_object = AsyncMock(return_value={"Body": _Body(b"image-bytes")})

    assert await read_object(client, "my-bucket", "1/photo.jpg") == b"image-bytes"
    client.get_object.assert_called_once_with(Bucket="my-bucket", Key="1/photo.jpg")


@pytest.mark.asyncio
async def test_read_object_returns_none_for_a_missing_key():
    client = AsyncMock()
    client.get_object = AsyncMock(side_effect=_client_error("NoSuchKey"))

    assert await read_object(client, "my-bucket", "1/gone.jpg") is None


@pytest.mark.asyncio
async def test_object_exists_asks_for_headers_only():
    """Нужен факт существования миниатюры, а не её байты."""
    client = AsyncMock()
    client.head_object = AsyncMock(return_value={"ContentLength": 10})

    assert await object_exists(client, "my-bucket", "thumbs/1/photo.jpg") is True
    client.head_object.assert_called_once_with(
        Bucket="my-bucket", Key="thumbs/1/photo.jpg"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("code", ["NoSuchKey", "NotFound", "404"])
async def test_object_exists_is_false_for_a_missing_key(code):
    client = AsyncMock()
    client.head_object = AsyncMock(side_effect=_client_error(code, "HeadObject"))

    assert await object_exists(client, "my-bucket", "thumbs/1/gone.jpg") is False


@pytest.mark.asyncio
async def test_a_storage_failure_is_not_swallowed():
    """Отказ, не означающий отсутствия, проходит наружу как исключение.

    Молчаливое ``None`` на ЛЮБОЙ ошибке сделало бы отчёт обслуживающего прогона
    лжецом: недоступный бакет отчитался бы строкой «работы нет».
    """
    client = AsyncMock()
    client.get_object = AsyncMock(side_effect=_client_error("AccessDenied"))
    client.head_object = AsyncMock(
        side_effect=_client_error("AccessDenied", "HeadObject")
    )

    with pytest.raises(ClientError):
        await read_object_head(client, "my-bucket", "1/photo.jpg")
    with pytest.raises(ClientError):
        await read_object(client, "my-bucket", "1/photo.jpg")
    with pytest.raises(ClientError):
        await object_exists(client, "my-bucket", "1/photo.jpg")


@pytest.mark.asyncio
async def test_put_object_bytes_writes_through_an_open_client():
    """Примитив записи, которым пользуется прогон по сотням объектов."""
    client = AsyncMock()
    client.put_object = AsyncMock()

    key = await put_object_bytes(
        client, "my-bucket", "1/photo.jpg", b"payload", "image/jpeg"
    )

    assert key == "1/photo.jpg"
    client.put_object.assert_called_once_with(
        Bucket="my-bucket",
        Key="1/photo.jpg",
        Body=b"payload",
        ContentType="image/jpeg",
    )
