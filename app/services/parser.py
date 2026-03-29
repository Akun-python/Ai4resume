from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from app.core.errors import LLMResponseError
from app.domain.schemas import BasicInfo, CandidateProfile
from app.infra.llm.client import get_llm_client


class ResumeParsingService:
    def __init__(self) -> None:
        self.llm = get_llm_client()

    def parse(
        self,
        *,
        raw_experience_text: str,
        job_description: str,
        target_role: str,
        basic_info: Optional[BasicInfo],
    ) -> CandidateProfile:
        system_prompt = (
            "你是一名中文简历信息抽取助手。"
            "请从候选人的自由文本经历中抽取结构化履历，只输出严格 JSON。"
            "不要虚构公司、项目、学校、时间、数字指标、奖项或证书；"
            "缺失字段请使用 null 或空数组。"
        )
        user_prompt = (
            f"目标岗位：{target_role}\n"
            f"岗位描述：\n{job_description}\n\n"
            f"用户原始经历：\n{raw_experience_text}\n\n"
            "请返回 CandidateProfile 对象，字段必须包含："
            "basic_info、education、experience、projects、skills、awards。\n"
            "其中 skills 优先输出为数组，每项包含 category 和 items。"
        )

        last_error: Optional[Exception] = None
        for _ in range(3):
            try:
                payload = self.llm.generate_json(
                    schema_name="candidate_profile",
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
                normalized = self._normalize_profile_payload(payload)
                if basic_info:
                    normalized["basic_info"] = {
                        **normalized.get("basic_info", {}),
                        **basic_info.model_dump(exclude_none=True),
                    }
                return CandidateProfile.model_validate(normalized)
            except (LLMResponseError, ValidationError) as exc:
                last_error = exc

        raise LLMResponseError(f"Failed to parse candidate profile: {last_error}")

    def _normalize_profile_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(payload)
        normalized["skills"] = self._normalize_skills(normalized.get("skills"))
        return normalized

    @staticmethod
    def _normalize_skills(skills: Any) -> List[Dict[str, Any]]:
        if skills is None:
            return []

        if isinstance(skills, list):
            if all(isinstance(item, dict) for item in skills):
                return skills
            if all(isinstance(item, str) for item in skills):
                items = [item.strip() for item in skills if item.strip()]
                return [{"category": "综合技能", "items": items}] if items else []

            normalized_groups: List[Dict[str, Any]] = []
            loose_items: List[str] = []
            for item in skills:
                if isinstance(item, dict):
                    normalized_groups.append(item)
                elif isinstance(item, str) and item.strip():
                    loose_items.append(item.strip())
            if loose_items:
                normalized_groups.append({"category": "综合技能", "items": loose_items})
            return normalized_groups

        if isinstance(skills, dict):
            normalized_groups: List[Dict[str, Any]] = []
            for category, items in skills.items():
                if isinstance(items, list):
                    normalized_items = [str(item).strip() for item in items if str(item).strip()]
                else:
                    normalized_items = [str(items).strip()] if str(items).strip() else []
                if normalized_items:
                    normalized_groups.append({"category": str(category).strip(), "items": normalized_items})
            return normalized_groups

        if isinstance(skills, str) and skills.strip():
            return [{"category": "综合技能", "items": [skills.strip()]}]

        return []
