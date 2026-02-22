import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.s3 import upload_file_to_s3, get_image_url


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
