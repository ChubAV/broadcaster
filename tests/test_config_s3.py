from app.config import Settings


def test_s3_settings_defaults():
    s = Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test",
    )
    assert s.s3_endpoint_url == ""
    assert s.s3_access_key == ""
    assert s.s3_secret_key == ""
    assert s.s3_bucket_name == "broadcaster"
    assert s.s3_region == ""
    assert s.s3_public_url == ""


def test_s3_settings_custom():
    s = Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test",
        s3_endpoint_url="https://s3.example.com",
        s3_access_key="AKID",
        s3_secret_key="SECRET",
        s3_bucket_name="my-bucket",
        s3_region="us-east-1",
        s3_public_url="https://cdn.example.com/my-bucket",
    )
    assert s.s3_endpoint_url == "https://s3.example.com"
    assert s.s3_bucket_name == "my-bucket"
    assert s.s3_public_url == "https://cdn.example.com/my-bucket"
