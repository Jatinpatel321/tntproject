from app.core.redis import redis_client

EMERGENCY_SHUTDOWN_KEY = "tnt:emergency_shutdown"
_fallback_shutdown_enabled = False


def set_emergency_shutdown(enabled: bool) -> bool:
    global _fallback_shutdown_enabled
    _fallback_shutdown_enabled = enabled

    try:
        redis_client.set(EMERGENCY_SHUTDOWN_KEY, "1" if enabled else "0")
    except Exception:
        pass

    return enabled


def is_emergency_shutdown_enabled() -> bool:
    try:
        value = redis_client.get(EMERGENCY_SHUTDOWN_KEY)
        if value is not None:
            return str(value).strip() in {"1", "true", "True", "yes", "on"}
    except Exception:
        pass

    return _fallback_shutdown_enabled
