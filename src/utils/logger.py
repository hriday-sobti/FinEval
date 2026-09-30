"""FinEval Structured Logging Module.

Ensures traceable, clean logging without leaking API keys or secrets.
"""

import logging
import sys
from typing import Any, Dict, Optional

from src.utils.config import settings


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger


def log_benchmark_event(
    logger: logging.Logger,
    run_id: str,
    scenario_id: str,
    prompt_version: str,
    model: str,
    status: str,
    latency_ms: float,
    evaluation_status: str,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Standardized benchmark execution event log."""
    msg = (
        f"run_id={run_id} scenario_id={scenario_id} prompt_version={prompt_version} "
        f"model={model} status={status} latency_ms={latency_ms:.1f} "
        f"evaluation_status={evaluation_status}"
    )
    if extra:
        extra_str = " ".join(f"{k}={v}" for k, v in extra.items())
        msg += f" {extra_str}"
    logger.info(msg)
