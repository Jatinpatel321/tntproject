import json

from app.core.redis import redis_client

UNIVERSITY_POLICY_KEY = "tnt:policy:university"

_fallback_policy = {
    "enabled": False,
    "break_start_hour": 12,
    "break_end_hour": 14,
    "max_orders_per_user": 3,
    "min_slot_duration_minutes": 15,
}


def get_university_policy() -> dict:
    try:
        raw = redis_client.get(UNIVERSITY_POLICY_KEY)
        if raw:
            data = json.loads(raw)
            return {
                "enabled": bool(data.get("enabled", False)),
                "break_start_hour": int(data.get("break_start_hour", 12)),
                "break_end_hour": int(data.get("break_end_hour", 14)),
                "max_orders_per_user": int(data.get("max_orders_per_user", 3)),
                "min_slot_duration_minutes": int(data.get("min_slot_duration_minutes", 15)),
            }
    except Exception:
        pass

    return dict(_fallback_policy)


def set_university_policy(
    enabled: bool,
    break_start_hour: int,
    break_end_hour: int,
    max_orders_per_user: int,
    min_slot_duration_minutes: int,
) -> dict:
    global _fallback_policy

    policy = {
        "enabled": bool(enabled),
        "break_start_hour": int(break_start_hour),
        "break_end_hour": int(break_end_hour),
        "max_orders_per_user": int(max_orders_per_user),
        "min_slot_duration_minutes": int(min_slot_duration_minutes),
    }
    _fallback_policy = policy

    try:
        redis_client.set(UNIVERSITY_POLICY_KEY, json.dumps(policy))
    except Exception:
        pass

    return policy


def is_hour_in_break_window(hour: int, start_hour: int, end_hour: int) -> bool:
    return start_hour <= hour < end_hour
