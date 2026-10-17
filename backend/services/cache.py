"""Tiny on-disk JSON cache so a flaky venue Wi-Fi can't break a live demo.

Every successful open-data response is stored here. If a later live call
fails (no internet, rate limit, API outage) the provider can fall back to the
last good copy and the response is labelled as cached - never silently.
"""
from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("heatwise.cache")

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
_lock = threading.Lock()


def _path(namespace: str, key: str) -> Path:
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:20]
    return CACHE_DIR / f"{namespace}_{digest}.json"


def get(namespace: str, key: str, max_age_s: Optional[float] = None) -> Optional[Any]:
    """Return a cached value, or None. max_age_s=None means 'any age'."""
    p = _path(namespace, key)
    try:
        with _lock:
            if not p.exists():
                return None
            payload = json.loads(p.read_text(encoding="utf-8"))
        if max_age_s is not None and (time.time() - payload.get("stored_at", 0)) > max_age_s:
            return None
        return payload.get("value")
    except Exception:  # noqa: BLE001 - a corrupt cache file must never break an analysis
        logger.warning("Cache read failed for %s", p.name, exc_info=True)
        return None


def put(namespace: str, key: str, value: Any) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with _lock:
            _path(namespace, key).write_text(
                json.dumps({"stored_at": time.time(), "key": key, "value": value}),
                encoding="utf-8",
            )
    except Exception:  # noqa: BLE001
        logger.warning("Cache write failed", exc_info=True)
