from __future__ import annotations

from app.domain.enums import ResumeSection, ThemeId
from app.domain.schemas import (
    BasicInfo,
    CandidateProfile,
    EducationEntry,
    ExperienceEntry,
    PresentationOptions,
    ProjectEntry,
    ResumeDraft,
    SectionRefineRequest,
    SkillEntry,
)
from app.services.drafting import ResumeDraftingService
from app.services.parser import ResumeParsingService
from app.services.rendering import LatexRenderingService, latex_escape


def build_profile() -> CandidateProfile:
    return CandidateProfile(
        basic_info=BasicInfo(
            name="张三",
            phone="13800000000",
            email="zhangsan@example.com",
            city="上海",
            links=["https://github.com/zhangsan"],
        ),
        education=[
            EducationEntry(
                school="上海交通大学",
                degree="硕士",
                major="数据科学",
                start_date="2022.09",
                end_date="2025.03",
                highlights=["研究方向聚焦数据分析与业务建模"],
            )
        ],
        experience=[
            ExperienceEntry(
                company="某数据公司",
                title="数据分析实习生",
                start_date="2024.06",
                end_date="2024.12",
                highlights=["搭建自动化报表体系", "支持业务指标分析"],
            )
        ],
        projects=[
            ProjectEntry(
                name="用户增长分析平台",
                role="项目负责人",
                start_date="2024.01",
                end_date="2024.05",
                highlights=["完成指标体系设计", "搭建留存分析框架"],
            )
        ],
        skills=[
            SkillEntry(category="编程", items=["Python", "SQL", "Pandas"]),
            SkillEntry(category="分析", items=["A/B测试", "指标体系", "可视化"]),
        ],
    )


def test_latex_escape_handles_special_characters():
    escaped = latex_escape(r"50% growth_1 & value")
    assert r"\%" in escaped
    assert r"\_" in escaped
    assert r"\&" in escaped


def test_template_renders_enhanced_sections():
    draft = ResumeDraft(
        selected_sections=[ResumeSection.SUMMARY, ResumeSection.SKILLS],
        section_content={
            "summary": "聚焦数据分析与业务问题拆解，能够形成结构化结论。",
            "skills": "编程：Python / SQL；分析：A/B测试 / 指标体系",
        },
        latex_context={
            "basic_info": BasicInfo(name="张三", email="zhangsan@example.com").model_dump(),
            "contact_items": [{"icon_latex": r"\faEnvelope", "text": "zhangsan@example.com", "href": "mailto:zhangsan@example.com"}],
            "section_meta": {
                "summary": {"title": "职业概述", "icon_latex": r"\faUserTie"},
                "skills": {"title": "核心技能", "icon_latex": r"\faCode"},
            },
            "skill_groups": [
                {"title": "编程", "icon_latex": r"\faCode", "items": ["Python", "SQL"]},
                {"title": "分析", "icon_latex": r"\faChartLine", "items": ["A/B测试", "指标体系"]},
            ],
            "projects": [],
            "experience": [],
            "education": [],
            "awards": [],
            "section_content": {
                "summary": "聚焦数据分析与业务问题拆解，能够形成结构化结论。",
                "skills": "编程：Python / SQL；分析：A/B测试 / 指标体系",
            },
            "selected_sections": [ResumeSection.SUMMARY.value, ResumeSection.SKILLS.value],
            "layout_options": {"allow_two_pages": True},
            "theme_tokens": {
                "resume_ink": "1E2A37",
                "resume_accent": "1D5C8F",
                "resume_muted": "637180",
                "resume_rule": "D8E1E9",
                "resume_tag_bg": "EEF4F8",
                "resume_accent_soft": "EAF2F8",
            },
        },
    )
    rendered = LatexRenderingService().render(draft)
    assert "职业概述" in rendered
    assert r"\faUserTie" in rendered
    assert r"\faCode" in rendered
    assert "张三" in rendered


def test_parser_normalizes_string_skill_list():
    service = ResumeParsingService()
    normalized = service._normalize_profile_payload(
        {
            "basic_info": {},
            "education": [],
            "experience": [],
            "projects": [],
            "skills": ["Python", "SQL", "Pandas"],
            "awards": [],
        }
    )
    assert normalized["skills"] == [{"category": "综合技能", "items": ["Python", "SQL", "Pandas"]}]


def test_drafting_service_builds_richer_bullets_without_fake_metrics(monkeypatch):
    class FakeLLM:
        def generate_json(self, *, schema_name: str, system_prompt: str, user_prompt: str):
            assert schema_name == "resume_draft_bundle"
            return {
                "summary": (
                    "聚焦数据分析与业务问题拆解，能够围绕增长场景组织分析路径并形成结构化表达。"
                    "过往经历覆盖自动化报表与指标体系设计。"
                ),
                "skills": {"groups": [{"title": "编程", "items": ["Python", "SQL"]}]},
                "projects": [
                    {
                        "name": "用户增长分析平台",
                        "bullets": [
                            "围绕增长目标梳理核心指标与分析问题。",
                            "沉淀结论表达方式并支持后续复盘。",
                        ],
                    }
                ],
                "experience": [
                    {
                        "company": "某数据公司",
                        "bullets": [
                            "搭建自动化报表体系，优化日常追踪流程。",
                        ],
                    }
                ],
            }

    profile = build_profile()
    service = ResumeDraftingService()
    monkeypatch.setattr(service, "llm", FakeLLM())

    draft = service.draft(
        profile=profile,
        job_description="应聘数据分析岗位，需要 SQL、Python、指标体系和增长分析能力。",
        target_role="数据分析师",
        presentation=PresentationOptions(theme_id=ThemeId.EXECUTIVE_BLUE),
    )

    project_bullets = draft.latex_context["projects"][0]["bullets"]
    experience_bullets = draft.latex_context["experience"][0]["bullets"]
    skill_groups = draft.latex_context["skill_groups"]

    assert len(project_bullets) >= 3
    assert len(experience_bullets) >= 3
    assert all(not any(char.isdigit() for char in bullet) for bullet in project_bullets + experience_bullets)
    assert skill_groups[0]["title"] == "编程"
    assert draft.latex_context["presentation"]["theme_id"] == ThemeId.EXECUTIVE_BLUE.value
    assert draft.latex_context["preview_sections"][0]["section"] == ResumeSection.SUMMARY.value


def test_regenerate_section_applies_refine_request(monkeypatch):
    class FakeLLM:
        def generate_json(self, *, schema_name: str, system_prompt: str, user_prompt: str):
            assert "额外要求：更强调可交付成果" in user_prompt
            return {
                "projects": [
                    {
                        "name": "用户增长分析平台",
                        "bullets": [
                            "围绕增长目标整理分析框架，突出可交付成果和汇报表达。",
                            "将留存分析结果结构化沉淀，便于团队复用。",
                            "支持阶段性复盘与业务沟通。",
                        ],
                    }
                ]
            }

    profile = build_profile()
    service = ResumeDraftingService()
    monkeypatch.setattr(service, "llm", FakeLLM())
    current_draft = ResumeDraft(
        selected_sections=[ResumeSection.SUMMARY, ResumeSection.PROJECTS],
        section_content={"summary": "原概述", "projects": "原项目"},
        latex_context={
            "section_content": {"summary": "原概述", "projects": "原项目"},
            "projects": [{"name": "用户增长分析平台", "bullets": ["原始 bullet"]}],
            "basic_info": profile.basic_info.model_dump(),
            "contact_items": [],
            "section_meta": {},
            "skill_groups": [],
            "experience": [],
            "education": [],
            "awards": [],
            "selected_sections": [ResumeSection.SUMMARY.value, ResumeSection.PROJECTS.value],
            "layout_options": {"allow_two_pages": True},
            "presentation": {"theme_id": ThemeId.EXECUTIVE_BLUE.value},
            "preview_sections": [],
            "theme_tokens": {
                "resume_ink": "1E2A37",
                "resume_accent": "1D5C8F",
                "resume_muted": "637180",
                "resume_rule": "D8E1E9",
                "resume_tag_bg": "EEF4F8",
                "resume_accent_soft": "EAF2F8",
            },
        },
    )

    draft = service.regenerate_section(
        profile=profile,
        current_draft=current_draft,
        job_description="应聘数据分析岗位，需要 SQL、Python、指标体系和增长分析能力。",
        target_role="数据分析师",
        section=ResumeSection.PROJECTS,
        presentation=PresentationOptions(theme_id=ThemeId.TERRACOTTA_INK),
        refine_request=SectionRefineRequest(
            preset="more_results_focused",
            custom_instruction="更强调可交付成果",
        ),
    )

    assert draft.latex_context["presentation"]["theme_id"] == ThemeId.TERRACOTTA_INK.value
    assert "可交付成果" in draft.latex_context["projects"][0]["bullets"][0]
    assert draft.section_content["summary"] == "原概述"


def test_template_avoids_empty_nested_itemize():
    draft = ResumeDraft(
        selected_sections=[ResumeSection.PROJECTS],
        section_content={"projects": "示例项目"},
        latex_context={
            "basic_info": BasicInfo(name="张三").model_dump(),
            "contact_items": [],
            "section_meta": {
                "projects": {"title": "项目经历", "icon_latex": r"\faProjectDiagram"},
            },
            "skill_groups": [],
            "projects": [
                {
                    "name": "示例项目",
                    "role": "负责人",
                    "start_date": "2024.01",
                    "end_date": "2024.03",
                    "bullets": [],
                    "highlights": [],
                }
            ],
            "experience": [],
            "education": [],
            "awards": [],
            "section_content": {"projects": "示例项目"},
            "selected_sections": [ResumeSection.PROJECTS.value],
            "layout_options": {"allow_two_pages": True},
            "theme_tokens": {
                "resume_ink": "1E2A37",
                "resume_accent": "1D5C8F",
                "resume_muted": "637180",
                "resume_rule": "D8E1E9",
                "resume_tag_bg": "EEF4F8",
                "resume_accent_soft": "EAF2F8",
            },
        },
    )
    rendered = LatexRenderingService().render(draft)
    assert rendered.count(r"\begin{itemize}") == 0
