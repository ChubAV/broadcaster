from aiobotocore.session import AioSession


def get_image_url(key: str, s3_public_url: str) -> str:
    """Build a public URL for an S3 object key."""
    if not key:
        return ""
    base = s3_public_url.rstrip("/")
    return f"{base}/{key}"


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
        await client.put_object(
            Bucket=bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
        )

    return key
