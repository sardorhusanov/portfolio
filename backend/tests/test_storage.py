import io
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import UploadFile
from PIL import Image
from pydantic import SecretStr, ValidationError
from starlette.datastructures import Headers
from vercel.blob import AsyncBlobClient
from vercel.blob.errors import BlobError

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.services.blob_storage import VercelBlobStorage
from app.services.storage import LocalStorage, Storage, StorageService


@pytest.fixture
def blob_client(monkeypatch):
    client = MagicMock(spec=AsyncBlobClient)
    client.__aenter__.return_value = client
    client.__aexit__.return_value = False
    client.put.side_effect = lambda key, *args, **kwargs: SimpleNamespace(
        url="https://portfolio.public.blob.vercel-storage.com/" + key
    )
    factory = MagicMock(return_value=client)
    monkeypatch.setattr("app.services.blob_storage.AsyncBlobClient", factory)
    monkeypatch.setattr(get_settings(), "blob_read_write_token", SecretStr("secret-blob-token"))
    return client, factory


def image_file():
    image = io.BytesIO()
    Image.new("RGB", (20, 10), "green").save(image, "PNG")
    image.seek(0)
    return UploadFile(
        file=image, filename="picture.png", headers=Headers({"content-type": "image/png"})
    )


def mock_session():
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


async def test_blob_upload_uses_public_sdk_url_and_keeps_jpeg_pair(blob_client):
    client, factory = blob_client
    storage = VercelBlobStorage()
    session = mock_session()
    upload = await StorageService(session, storage).upload(image_file(), "posts")

    webp, jpeg = client.put.await_args_list
    webp_key, webp_bytes = webp.args
    jpeg_key, jpeg_bytes = jpeg.args
    assert jpeg_key == webp_key[:-5] + ".jpg"
    assert webp.kwargs["content_type"] == "image/webp"
    assert jpeg.kwargs["content_type"] == "image/jpeg"
    for call in (webp, jpeg):
        assert call.kwargs["access"] == "public"
        assert call.kwargs["add_random_suffix"] is False
        assert call.kwargs["overwrite"] is False
    assert Image.open(io.BytesIO(webp_bytes)).format == "WEBP"
    assert Image.open(io.BytesIO(jpeg_bytes)).format == "JPEG"
    assert upload.url == "https://portfolio.public.blob.vercel-storage.com/" + webp_key
    assert storage.url(jpeg_key) == upload.url[:-5] + ".jpg"
    assert upload.storage_key == webp_key
    assert (upload.width, upload.height) == (20, 10)
    session.commit.assert_awaited_once()
    factory.assert_called_with(token="secret-blob-token")
    assert client.__aexit__.await_count == 2


async def test_blob_delete_works_in_a_new_request_without_url_cache(blob_client):
    client, _ = blob_client
    await VercelBlobStorage().delete("posts/image.webp")
    client.delete.assert_awaited_once_with("posts/image.webp")
    client.__aexit__.assert_awaited_once()


@pytest.mark.parametrize("operation", ["write", "delete"])
async def test_blob_failures_are_sanitized_and_close_client(blob_client, caplog, operation):
    client, _ = blob_client
    getattr(client, "put" if operation == "write" else "delete").side_effect = BlobError(
        "request failed with secret-blob-token"
    )
    storage = VercelBlobStorage()
    with pytest.raises(AppError, match="temporarily unavailable") as error:
        if operation == "write":
            await storage.write("posts/image.webp", b"image")
        else:
            await storage.delete("posts/image.webp")
    assert error.value.status == 503
    assert "secret-blob-token" not in str(error.value)
    assert "secret-blob-token" not in caplog.text
    assert error.value.__suppress_context__
    client.__aexit__.assert_awaited_once()


@pytest.mark.parametrize("key", ["../outside.webp", "/absolute.webp", "posts//x.webp", "a\\b"])
async def test_blob_rejects_invalid_keys_without_network(blob_client, key):
    _, factory = blob_client
    storage = VercelBlobStorage()
    for operation in (storage.write(key, b"image"), storage.delete(key)):
        with pytest.raises(AppError, match="Invalid storage path"):
            await operation
    factory.assert_not_called()


@pytest.mark.parametrize("failure", ["first_write", "jpeg_write", "commit"])
async def test_failed_upload_cleans_both_variants_and_keeps_original_error(failure, caplog):
    storage = MagicMock(spec=Storage)
    session = mock_session()
    original = RuntimeError("Original upload failure")
    if failure == "first_write":
        storage.write.side_effect = original
    elif failure == "jpeg_write":
        storage.write.side_effect = [None, original]
    else:
        session.commit.side_effect = original
        storage.url.return_value = "https://portfolio.example/image.webp"
    storage.delete.side_effect = [RuntimeError("secret-cleanup-error"), None]

    with pytest.raises(RuntimeError, match="Original upload failure") as error:
        await StorageService(session, storage).upload(image_file(), "posts")
    assert error.value is original
    session.rollback.assert_awaited_once()
    cleaned = [call.args[0] for call in storage.delete.await_args_list]
    assert len(cleaned) == 2
    assert cleaned[1] == cleaned[0][:-5] + ".jpg"
    assert "secret-cleanup-error" not in caplog.text


async def test_local_storage_remains_available_and_rejects_traversal(tmp_path):
    storage = LocalStorage(tmp_path)
    await storage.write("posts/image.webp", b"image")
    assert (tmp_path / "posts/image.webp").read_bytes() == b"image"
    assert storage.url("posts/image.webp") == "/uploads/posts/image.webp"
    await storage.delete("posts/image.webp")
    assert not (tmp_path / "posts/image.webp").exists()
    with pytest.raises(AppError, match="Invalid storage path"):
        await storage.write("../outside.webp", b"image")


def test_storage_selection_and_blob_configuration(monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "upload_dir", tmp_path)
    monkeypatch.setattr(get_settings(), "storage_backend", "local")
    assert isinstance(StorageService(mock_session()).storage, LocalStorage)
    monkeypatch.setattr(get_settings(), "storage_backend", "vercel_blob")
    assert isinstance(StorageService(mock_session()).storage, VercelBlobStorage)
    with pytest.raises(ValidationError, match="BLOB_READ_WRITE_TOKEN"):
        Settings(_env_file=None, storage_backend="vercel_blob", blob_read_write_token="")
    settings = Settings(
        _env_file=None, storage_backend="vercel_blob", blob_read_write_token="secret-blob-token"
    )
    assert "secret-blob-token" not in repr(settings)
