from __future__ import annotations

import logging
import random
import re
import time
from typing import Iterable

from .config import LOG_DIR, LOG_FILE_PATH
from .models import JobRecord


def ensure_runtime_dirs() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def configure_logging() -> logging.Logger:
    ensure_runtime_dirs()
    logger = logging.getLogger("boss_scraper")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.propagate = False
    return logger


def normalize_whitespace(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def split_requirements_text(value: str) -> tuple[str, str]:
    normalized = normalize_whitespace(value)
    if not normalized:
        return "", ""

    parts = [part.strip() for part in re.split(r"[·/|丨]", normalized) if part.strip()]
    experience = ""
    education = ""

    for part in parts:
        lower = part.lower()
        if not experience and (
            "经验" in part
            or "应届" in part
            or "在校" in part
            or "1-" in part
            or "年" in part
            or part == "不限"
        ):
            experience = part
            continue

        if not education and (
            "本科" in part
            or "大专" in part
            or "硕士" in part
            or "博士" in part
            or "学历" in part
            or "中专" in part
            or "高中" in part
            or "初中" in part
            or part == "不限"
            or "college" in lower
        ):
            education = part

    if not experience and parts:
        experience = parts[0]
    if not education and len(parts) > 1:
        education = parts[1]
    return experience, education


def normalize_skill_keywords(raw: Iterable[str] | str | None) -> str:
    if raw is None:
        return ""
    if isinstance(raw, str):
        return normalize_whitespace(raw)
    cleaned = [normalize_whitespace(item) for item in raw if normalize_whitespace(item)]
    return " / ".join(cleaned)


def sleep_with_jitter(delay_range: tuple[float, float]) -> None:
    low, high = delay_range
    time.sleep(random.uniform(low, high))


def unique_records(records: Iterable[JobRecord]) -> list[JobRecord]:
    seen: set[tuple[str, str, str, str]] = set()
    deduped: list[JobRecord] = []
    for record in records:
        key = record.dedupe_key()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)
    return deduped

