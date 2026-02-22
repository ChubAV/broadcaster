# S3 Image Storage Migration

## Context

Broadcaster currently stores uploaded images on local filesystem (`uploads/` directory), shared between Docker containers via a named volume. This design doc describes migration to S3-compatible object storage.

## Decisions

- **S3 provider:** Any S3-compatible (configurable endpoint_url)
- **Migration:** Clean switch, no migration of existing local files
- **URL delivery:** Public bucket, direct S3 URLs to clients
- **DB storage:** Keep relative keys (`user_id/filename`), build URLs dynamically via helper

## Architecture

### Configuration (`app/config.py`)

New settings:
- `s3_endpoint_url` — S3 API endpoint
- `s3_access_key`, `s3_secret_key` — credentials
- `s3_bucket_name` — bucket name (default: `broadcaster`)
- `s3_region` — optional region
- `s3_public_url` — public base URL for serving images (may differ from API endpoint)

`upload_dir` becomes unused. `max_image_size_mb` stays.

### S3 Service (`app/services/s3.py`)

New module using `aiobotocore`:
- `upload_file(content, key, content_type) -> str` — upload to S3, return key
- `delete_file(key)` — delete from S3
- `get_public_url(key) -> str` — build public URL from `s3_public_url` + key

### Upload Route (`app/routes/uploads.py`)

Replace local file write with `s3.upload_file()`. Response format unchanged: `{"path": "user_id/filename"}`.

### Image Serving

- Remove `StaticFiles("/uploads")` mount from `main.py`
- Add `get_image_url()` as Jinja2 global function
- Templates use `{{ get_image_url(path) }}` instead of `/uploads/{{ path }}`

### Messenger Adapters

- **Telegram:** Pass S3 URLs directly to `send_file()` (supports URLs)
- **WhatsApp bridge:** Modify to download from URL before sending, since `MessageMedia.fromFilePath()` requires local files. Use `MessageMedia.fromUrl()` or download via `axios`.

### Docker

Remove `uploads` volume from `docker-compose.yml` and `docker-compose.dev.yml`.

### Tests

Mock S3 client in tests. Update upload and worker tests.
