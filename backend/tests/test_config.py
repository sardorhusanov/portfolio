import pytest
from fastapi import Response
from pydantic import ValidationError

from app.api.routes.admin_auth import set_cookie
from app.core.config import Settings, get_settings


def test_production_requires_explicit_secure_configuration(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    options = dict(
        _env_file=None,
        app_env="production",
        debug=False,
        frontend_url="https://portfolio.example",
        public_site_url="https://portfolio.example",
    )
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(**options)
    settings = Settings(**options, secret_key="a-random-production-secret-" * 3)
    assert settings.site_url == "https://portfolio.example"
    with pytest.raises(ValidationError, match="HTTPS"):
        Settings(
            **{**options, "frontend_url": "http://localhost:5173"}, secret_key=settings.secret_key
        )


def test_production_refresh_cookie_is_secure(monkeypatch):
    monkeypatch.setattr(get_settings(), "app_env", "production")
    response = Response()
    set_cookie(response, "opaque-refresh-token")
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "Secure" in cookie and "SameSite=lax" in cookie
    assert "Path=/api/v1/admin/auth" in cookie
