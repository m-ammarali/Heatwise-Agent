"""Optional Alibaba Cloud Model Studio (Qwen) narrative layer.

Uses the OpenAI-compatible endpoint, so no extra SDK is needed. Entirely
optional: with no DASHSCOPE_API_KEY (or on any error) every function returns
None and HeatWise keeps working with its deterministic, rule-based text.

The model is only asked to *explain* numbers HeatWise already computed - it
never produces the risk score, so the score stays auditable.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import requests

logger = logging.getLogger("heatwise.qwen")

DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"      # override with QWEN_MODEL (see Model Studio console for current IDs)

SYSTEM_PROMPT = (
    "You are the reporting module of HeatWise Agent, an operational heat-risk tool for "
    "outdoor work teams. Write for a site supervisor: plain, concrete, no medical claims. "
    "Use ONLY the numbers given. Never invent measurements. Do not change the risk score. "
    "Treat the microclimate adjustment as a modelled estimate, not a measurement."
)


def is_configured() -> bool:
    return bool(os.getenv("DASHSCOPE_API_KEY"))


def ask(prompt: str, max_tokens: int = 450) -> Optional[str]:
    key = os.getenv("DASHSCOPE_API_KEY")
    if not key:
        return None
    base = (os.getenv("QWEN_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
    model = os.getenv("QWEN_MODEL") or DEFAULT_MODEL
    try:
        resp = requests.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "max_tokens": max_tokens, "temperature": 0.3,
                  "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                               {"role": "user", "content": prompt}]},
            timeout=25,
        )
        if not resp.ok:
            logger.warning("Qwen call failed: HTTP %s", resp.status_code)   # never log the key/body
            return None
        text = resp.json()["choices"][0]["message"]["content"]
        return text.strip() or None
    except Exception:  # noqa: BLE001
        logger.warning("Qwen call failed (network/format).")
        return None
