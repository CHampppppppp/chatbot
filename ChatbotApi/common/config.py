import os

from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV", "production")
DEV_MODE = ENV == "dev"

DEFAULT_CORS_ALLOWED_ORIGINS = [
    "http://nginx",
    "http://127.0.0.1:3005",
    "http://localhost:3005",
    "https://chatbot.mgsai.cn",
    "https://szyx.zjer.cn",
]


def get_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized_value = value.strip().lower()
    if normalized_value in {"1", "true", "yes", "on"}:
        return True
    if normalized_value in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be a boolean value")


def get_csv_env(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if value is None:
        return default

    values = [item.strip() for item in value.split(",") if item.strip()]
    if not values:
        raise RuntimeError(f"{name} must contain at least one origin")
    return values


CORS_ALLOWED_ORIGINS = get_csv_env(
    "CORS_ALLOWED_ORIGINS", DEFAULT_CORS_ALLOWED_ORIGINS
)
COOKIE_SECURE = get_bool_env("COOKIE_SECURE", default=False)
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE")
if COOKIE_SAMESITE:
    COOKIE_SAMESITE = COOKIE_SAMESITE.lower()
if COOKIE_SAMESITE and COOKIE_SAMESITE not in {"lax", "strict", "none"}:
    raise RuntimeError("COOKIE_SAMESITE must be lax, strict, or none")
if COOKIE_SAMESITE == "none" and not COOKIE_SECURE:
    raise RuntimeError("COOKIE_SAMESITE=none requires COOKIE_SECURE=true")


def get_cookie_samesite() -> str:
    return COOKIE_SAMESITE or "lax"

ID_TOKEN_EXPIRE_MINUTES = int(os.getenv("ID_TOKEN_EXPIRE_MINUTES", "86400"))


def required_env(name: str, dev_default: str | None = None) -> str:
    value = os.getenv(name)
    if value:
        return value
    if DEV_MODE and dev_default is not None:
        return dev_default
    raise RuntimeError(f"Missing required environment variable: {name}")


SECRET_KEY = required_env("SECRET_KEY", "dev-secret-key-change-me")

# SSO认证配置
SSO_APP_KEY = required_env("SSO_APP_KEY", "dev-sso-app-key")
SSO_SECRET_KEY = required_env("SSO_SECRET_KEY", "dev-sso-secret-key")
