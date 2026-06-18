import os

from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV", "production")
DEV_MODE = ENV == "dev"

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
