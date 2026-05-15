from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class JobRecord:
    city: str
    job_name: str
    salary: str
    company_name: str
    education: str
    experience: str
    skill_keywords: str = ""

    def dedupe_key(self) -> tuple[str, str, str, str]:
        return (
            self.city.strip(),
            self.job_name.strip(),
            self.company_name.strip(),
            self.salary.strip(),
        )

    def to_row(self) -> dict[str, str]:
        return {
            "城市": self.city,
            "岗位名称": self.job_name,
            "薪资": self.salary,
            "公司名": self.company_name,
            "学历要求": self.education,
            "工作经验": self.experience,
            "技能关键词": self.skill_keywords,
        }

