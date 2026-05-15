from __future__ import annotations

from typing import Any

from .models import JobRecord
from .utils import normalize_skill_keywords, normalize_whitespace, split_requirements_text


def parse_job_card(card_or_payload: dict[str, Any], city: str) -> JobRecord:
    job_name = first_non_empty(
        card_or_payload,
        ["job_name", "jobName", "title", "positionName", "name"],
    )
    salary = first_non_empty(
        card_or_payload,
        ["salary", "salaryDesc", "salaryText", "pay"],
    )
    company_name = first_non_empty(
        card_or_payload,
        ["company_name", "brandName", "companyName", "bossName", "brand"],
    )

    experience = normalize_whitespace(
        first_non_empty(
            card_or_payload,
            ["experience", "jobExperience", "experienceName", "expDesc"],
        )
    )
    education = normalize_whitespace(
        first_non_empty(
            card_or_payload,
            ["education", "jobDegree", "degreeName", "degree", "eduLevel"],
        )
    )

    if not experience or not education:
        derived_experience, derived_education = split_requirements_text(
            first_non_empty(
                card_or_payload,
                ["requirements", "jobLabelsText", "jobInfoDesc", "desc", "tag_text"],
            )
        )
        experience = experience or derived_experience
        education = education or derived_education

    skill_keywords = normalize_skill_keywords(
        first_non_empty(
            card_or_payload,
            ["skill_keywords", "skills", "skillList", "labels", "jobLabels", "tags"],
            default=[],
        )
    )

    return JobRecord(
        city=city,
        job_name=normalize_whitespace(job_name),
        salary=normalize_whitespace(salary),
        company_name=normalize_whitespace(company_name),
        education=education,
        experience=experience,
        skill_keywords=skill_keywords,
    )


def extract_payload_job_rows(payload: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    walk_payload(payload, rows)
    return rows


def walk_payload(node: Any, rows: list[dict[str, Any]]) -> None:
    if isinstance(node, dict):
        if looks_like_job_record(node):
            rows.append(node)
        for value in node.values():
            walk_payload(value, rows)
    elif isinstance(node, list):
        for item in node:
            walk_payload(item, rows)


def looks_like_job_record(item: dict[str, Any]) -> bool:
    key_space = set(item.keys())
    if {"jobName", "salaryDesc"} <= key_space:
        return True
    if {"job_name", "salary", "company_name"} <= key_space:
        return True
    return bool(
        {"jobName", "salaryDesc", "brandName"} & key_space
        and {"jobExperience", "jobDegree", "skills"} & key_space
    )


def first_non_empty(
    payload: dict[str, Any],
    keys: list[str],
    default: str | list[Any] | None = "",
) -> Any:
    for key in keys:
        value = payload.get(key)
        if value in (None, "", [], ()):
            continue
        return value
    return default

