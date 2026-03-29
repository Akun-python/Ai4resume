from __future__ import annotations

from typing import Dict, List

from app.domain.enums import ResumeSection, ThemeId


THEME_REGISTRY: Dict[ThemeId, Dict[str, str]] = {
    ThemeId.EXECUTIVE_BLUE: {
        "label": "Executive Blue",
        "description": "冷静商务蓝，适合数据、咨询与运营岗位。",
        "resume_ink": "1E2A37",
        "resume_accent": "1D5C8F",
        "resume_accent_soft": "EAF2F8",
        "resume_muted": "637180",
        "resume_rule": "D8E1E9",
        "resume_tag_bg": "EEF4F8",
    },
    ThemeId.FOREST_SLATE: {
        "label": "Forest Slate",
        "description": "深绿灰，偏稳重顾问风与策略表达。",
        "resume_ink": "1F2C2A",
        "resume_accent": "335C53",
        "resume_accent_soft": "EBF3F0",
        "resume_muted": "61726D",
        "resume_rule": "D7E3DE",
        "resume_tag_bg": "EEF5F2",
    },
    ThemeId.TERRACOTTA_INK: {
        "label": "Terracotta Ink",
        "description": "暖陶土棕，适合产品、品牌与运营方向。",
        "resume_ink": "322823",
        "resume_accent": "9C5E44",
        "resume_accent_soft": "FAEFE8",
        "resume_muted": "7A655A",
        "resume_rule": "E8D9D0",
        "resume_tag_bg": "FCF3EE",
    },
}

SECTION_TITLES: Dict[ResumeSection, str] = {
    ResumeSection.SUMMARY: "职业概述",
    ResumeSection.SKILLS: "核心技能",
    ResumeSection.PROJECTS: "项目经历",
    ResumeSection.EXPERIENCE: "工作经历",
    ResumeSection.EDUCATION: "教育经历",
}


def get_theme_tokens(theme_id: ThemeId) -> Dict[str, str]:
    return dict(THEME_REGISTRY[theme_id])


def get_theme_choices() -> List[Dict[str, str]]:
    return [{"id": theme_id.value, **tokens} for theme_id, tokens in THEME_REGISTRY.items()]
