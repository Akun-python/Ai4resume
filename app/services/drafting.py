from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Dict, Iterable, List, Sequence
from urllib.parse import urlparse

from app.core.errors import LLMResponseError
from app.domain.enums import RefinePreset, ResumeSection
from app.domain.schemas import (
    CandidateProfile,
    EducationEntry,
    ExperienceEntry,
    PreviewSection,
    PresentationOptions,
    ProjectEntry,
    ResumeDraft,
    SectionRefineRequest,
    SkillEntry,
)
from app.infra.llm.client import get_llm_client
from app.services.presentation import SECTION_TITLES, get_theme_tokens


DEFAULT_TEMPLATE_VERSION = "resume_cn_v1"

SECTION_ORDER = [
    ResumeSection.SUMMARY,
    ResumeSection.SKILLS,
    ResumeSection.PROJECTS,
    ResumeSection.EXPERIENCE,
    ResumeSection.EDUCATION,
]

SECTION_META = {
    ResumeSection.SUMMARY.value: {"title": SECTION_TITLES[ResumeSection.SUMMARY], "icon_latex": r"\faUserTie"},
    ResumeSection.SKILLS.value: {"title": SECTION_TITLES[ResumeSection.SKILLS], "icon_latex": r"\faCode"},
    ResumeSection.PROJECTS.value: {"title": SECTION_TITLES[ResumeSection.PROJECTS], "icon_latex": r"\faProjectDiagram"},
    ResumeSection.EXPERIENCE.value: {"title": SECTION_TITLES[ResumeSection.EXPERIENCE], "icon_latex": r"\faBriefcase"},
    ResumeSection.EDUCATION.value: {"title": SECTION_TITLES[ResumeSection.EDUCATION], "icon_latex": r"\faGraduationCap"},
}

SKILL_GROUP_META = {
    "编程": {"title": "编程", "icon_latex": r"\faCode"},
    "分析": {"title": "分析", "icon_latex": r"\faChartLine"},
    "工具": {"title": "工具", "icon_latex": r"\faTools"},
    "方法": {"title": "方法", "icon_latex": r"\faLayerGroup"},
    "综合技能": {"title": "综合技能", "icon_latex": r"\faStar"},
}

SKILL_GROUP_ORDER = ["编程", "分析", "工具", "方法", "综合技能"]
ROLE_KEYWORDS = (

    "python",
    "sql",
    "pandas",
    "numpy",
    "spark",
    "airflow",
    "excel",
    "tableau",
    "power bi",
    "bi",
    "数据分析",
    "数据挖掘",
    "数据治理",
    "数据建模",
    "机器学习",
    "用户增长",
    "商业分析",
    "产品分析",
    "指标体系",
    "ab测试",
    "实验",
    "可视化",
    "自动化",
)

REFINE_PRESET_GUIDANCE = {
    RefinePreset.MORE_PROFESSIONAL: "语言更职业、更适合正式求职场景，减少口语感。",
    RefinePreset.MORE_CONCISE: "压缩句子长度，保留高信息密度，减少重复表达。",
    RefinePreset.MORE_RESULTS_FOCUSED: "突出结果、产出、影响和可交付物，但不能编造数字。",
    RefinePreset.MORE_ROLE_ALIGNED: "更贴近岗位描述关键词，强调岗位匹配度和相关方法能力。",
    RefinePreset.MORE_EXECUTIVE: "表达更成熟克制，突出判断、推进、协作和业务理解。",
}


class ResumeDraftingService:
    def __init__(self) -> None:
        self.llm = get_llm_client()

    def draft(
        self,
        *,
        profile: CandidateProfile,
        job_description: str,
        target_role: str,
        presentation: PresentationOptions,
    ) -> ResumeDraft:
        selected_sections = self._pick_sections(profile)
        payload = self._generate_section_bundle(
            profile=profile,
            job_description=job_description,
            target_role=target_role,
            sections=selected_sections,
        )
        base_context = self._build_base_latex_context(profile, selected_sections, presentation)
        normalized = self._normalize_generated_bundle(
            profile=profile,
            payload=payload,
            sections=selected_sections,
            job_description=job_description,
            target_role=target_role,
        )
        latex_context = self._merge_latex_context(
            base_context=base_context,
            generated_context=normalized,
            selected_sections=selected_sections,
        )
        return ResumeDraft(
            selected_sections=selected_sections,
            section_content=latex_context["section_content"],
            latex_context=latex_context,
            template_version=DEFAULT_TEMPLATE_VERSION,
        )

    def regenerate_section(
        self,
        *,
        profile: CandidateProfile,
        current_draft: ResumeDraft,
        job_description: str,
        target_role: str,
        section: ResumeSection,
        presentation: PresentationOptions,
        refine_request: SectionRefineRequest | None = None,
    ) -> ResumeDraft:
        selected_sections = list(current_draft.selected_sections or self._pick_sections(profile))
        if section not in selected_sections:
            selected_sections.append(section)
            selected_sections = [item for item in SECTION_ORDER if item in selected_sections]

        payload = self._generate_section_bundle(
            profile=profile,
            job_description=job_description,
            target_role=target_role,
            sections=[section],
            refine_request=refine_request,
            current_draft=current_draft,
        )
        base_context = self._build_base_latex_context(profile, selected_sections, presentation)
        generated_context = self._normalize_generated_bundle(
            profile=profile,
            payload=payload,
            sections=[section],
            job_description=job_description,
            target_role=target_role,
        )
        latex_context = self._merge_latex_context(
            base_context=base_context,
            generated_context=generated_context,
            selected_sections=selected_sections,
            existing_context=current_draft.latex_context,
            existing_section_content=current_draft.section_content,
            regenerate_only=section,
        )
        return ResumeDraft(
            selected_sections=selected_sections,
            section_content=latex_context["section_content"],
            latex_context=latex_context,
            template_version=current_draft.template_version or DEFAULT_TEMPLATE_VERSION,
        )

    def _pick_sections(self, profile: CandidateProfile) -> List[ResumeSection]:
        selected: List[ResumeSection] = [ResumeSection.SUMMARY]
        if any(group.items for group in profile.skills):
            selected.append(ResumeSection.SKILLS)
        if profile.projects:
            selected.append(ResumeSection.PROJECTS)
        if profile.experience:
            selected.append(ResumeSection.EXPERIENCE)
        if profile.education:
            selected.append(ResumeSection.EDUCATION)
        return [section for section in SECTION_ORDER if section in selected]

    def _generate_section_bundle(
        self,
        *,
        profile: CandidateProfile,
        job_description: str,
        target_role: str,
        sections: Iterable[ResumeSection],
        refine_request: SectionRefineRequest | None = None,
        current_draft: ResumeDraft | None = None,
    ) -> Dict[str, Any]:
        section_names = ", ".join(section.value for section in sections)
        refine_instruction = self._build_refine_instruction(refine_request)
        current_section_snapshot = {}
        if current_draft and refine_request:
            current_section_snapshot = {
                section.value: current_draft.section_content.get(section.value, "")
                for section in sections
            }

        system_prompt = (
            "你是一名资深中文简历顾问。"
            "请基于候选人的结构化履历、岗位描述和必要的润色指令，输出适合 ATS 的中文简历内容。"
            "你可以润色、压缩、重组表达，但绝不能新增候选人未提供的公司、项目、学校、奖项、时间、证书或数字。"
            "如果原始信息没有量化数据，就不要补数字。"
            "项目和工作经历默认写成 3 到 4 条高密度 bullet，覆盖职责、方法、产出和影响。"
            "只输出严格 JSON，不要输出 Markdown 或代码块。"
        )
        user_prompt = (
            f"目标岗位：{target_role}\n"
            f"岗位描述：\n{job_description}\n\n"
            f"候选人结构化资料：\n{profile.model_dump_json(indent=2)}\n\n"
            f"请只生成这些模块：{section_names}\n"
            "返回 JSON 规则：\n"
            "1. summary：2 到 3 句，聚焦岗位匹配、方法能力和业务场景。\n"
            "2. skills：优先返回 { groups: [{ title, items }] }。\n"
            "3. projects / experience：返回数组，每项包含 name 或 company，以及 bullets。\n"
            "4. education：返回数组，每项包含 school，可带 details。\n"
            f"润色要求：{refine_instruction}\n"
        )
        if current_section_snapshot:
            user_prompt += f"\n当前目标区块草稿：\n{current_section_snapshot}\n"

        try:
            payload = self.llm.generate_json(
                schema_name="resume_draft_bundle",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        except LLMResponseError:
            return {}
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _build_refine_instruction(refine_request: SectionRefineRequest | None) -> str:
        if not refine_request:
            return "保持专业、真实、适合正式投递。"

        parts: List[str] = []
        if refine_request.preset:
            parts.append(REFINE_PRESET_GUIDANCE[refine_request.preset])
        if refine_request.custom_instruction:
            custom_instruction = refine_request.custom_instruction.strip()
            if custom_instruction:
                parts.append(f"额外要求：{custom_instruction}")
        return " ".join(parts) if parts else "保持专业、真实、适合正式投递。"

    def _build_base_latex_context(
        self,
        profile: CandidateProfile,
        selected_sections: Sequence[ResumeSection],
        presentation: PresentationOptions,
    ) -> Dict[str, object]:
        skill_groups = self._normalize_skill_groups(None, profile.skills)
        projects = [self._project_entry_from_profile(item) for item in profile.projects]
        experience = [self._experience_entry_from_profile(item) for item in profile.experience]
        education = [self._education_entry_from_profile(item) for item in profile.education]
        preview_sections = self._build_preview_sections(selected_sections)
        return {
            "basic_info": profile.basic_info.model_dump(),
            "contact_items": self._build_contact_items(profile),
            "section_meta": deepcopy(SECTION_META),
            "skill_groups": skill_groups,
            "skills": skill_groups,
            "projects": projects,
            "project_entries": projects,
            "experience": experience,
            "experience_entries": experience,
            "education": education,
            "education_entries": education,
            "awards": [item.model_dump() for item in profile.awards],
            "section_content": {},
            "selected_sections": [section.value for section in selected_sections],
            "layout_options": {
                "allow_two_pages": True,
                "single_column": True,
                "dense_bullets": True,
                "style": "ats_refined_single_column",
            },
            "presentation": presentation.model_dump(mode="json"),
            "preview_sections": [item.model_dump(mode="json") for item in preview_sections],
            "theme_tokens": get_theme_tokens(presentation.theme_id),
        }

    def _merge_latex_context(
        self,
        *,
        base_context: Dict[str, object],
        generated_context: Dict[str, object],
        selected_sections: Sequence[ResumeSection],
        existing_context: Dict[str, object] | None = None,
        existing_section_content: Dict[str, str] | None = None,
        regenerate_only: ResumeSection | None = None,
    ) -> Dict[str, object]:
        merged = deepcopy(base_context)
        if existing_context:
            for section in selected_sections:
                if regenerate_only is not None and section == regenerate_only:
                    continue
                for key in self._section_context_keys(section):
                    if key in existing_context:
                        merged[key] = deepcopy(existing_context[key])

            current_section_content = existing_context.get("section_content", {})
            if isinstance(current_section_content, dict):
                merged["section_content"] = dict(current_section_content)
        if existing_section_content:
            merged["section_content"] = {
                **dict(merged.get("section_content", {})),
                **dict(existing_section_content),
            }

        for section in selected_sections:
            if regenerate_only is not None and section != regenerate_only:
                continue
            for key in self._section_context_keys(section):
                if key == "section_content":
                    continue
                if key in generated_context:
                    merged[key] = deepcopy(generated_context[key])

        updated_section_content = dict(merged.get("section_content", {}))
        new_section_content = generated_context.get("section_content", {})
        if isinstance(new_section_content, dict):
            updated_section_content.update(new_section_content)
        merged["section_content"] = updated_section_content
        merged["selected_sections"] = [section.value for section in selected_sections]
        merged["section_meta"] = deepcopy(SECTION_META)
        merged["layout_options"] = deepcopy(base_context["layout_options"])
        merged["basic_info"] = deepcopy(base_context["basic_info"])
        merged["contact_items"] = deepcopy(base_context["contact_items"])
        merged["presentation"] = deepcopy(base_context["presentation"])
        merged["preview_sections"] = deepcopy(base_context["preview_sections"])
        merged["theme_tokens"] = deepcopy(base_context["theme_tokens"])
        return merged

    @staticmethod
    def _section_context_keys(section: ResumeSection) -> Sequence[str]:
        return {
            ResumeSection.SUMMARY: ("section_content",),
            ResumeSection.SKILLS: ("skills", "skill_groups", "section_content"),
            ResumeSection.PROJECTS: ("projects", "project_entries", "section_content"),
            ResumeSection.EXPERIENCE: ("experience", "experience_entries", "section_content"),
            ResumeSection.EDUCATION: ("education", "education_entries", "section_content"),
        }[section]

    def _normalize_generated_bundle(
        self,
        *,
        profile: CandidateProfile,
        payload: Dict[str, Any],
        sections: Sequence[ResumeSection],
        job_description: str,
        target_role: str,
    ) -> Dict[str, object]:
        context: Dict[str, object] = {"section_content": {}}

        if ResumeSection.SUMMARY in sections:
            summary = self._normalize_summary(
                value=payload.get("summary"),
                profile=profile,
                job_description=job_description,
                target_role=target_role,
            )
            context["section_content"] = {**context["section_content"], "summary": summary}

        if ResumeSection.SKILLS in sections:
            skill_groups = self._normalize_skill_groups(payload.get("skills"), profile.skills)
            context["skill_groups"] = skill_groups
            context["skills"] = skill_groups
            context["section_content"] = {
                **context["section_content"],
                "skills": self._skill_groups_to_text(skill_groups),
            }

        if ResumeSection.PROJECTS in sections:
            projects = self._normalize_project_entries(
                raw_projects=payload.get("projects"),
                profile=profile,
                job_description=job_description,
                target_role=target_role,
            )
            context["projects"] = projects
            context["project_entries"] = projects
            context["section_content"] = {
                **context["section_content"],
                "projects": self._entries_to_text(projects, "name"),
            }

        if ResumeSection.EXPERIENCE in sections:
            experience = self._normalize_experience_entries(
                raw_experience=payload.get("experience"),
                profile=profile,
                job_description=job_description,
                target_role=target_role,
            )
            context["experience"] = experience
            context["experience_entries"] = experience
            context["section_content"] = {
                **context["section_content"],
                "experience": self._entries_to_text(experience, "company"),
            }

        if ResumeSection.EDUCATION in sections:
            education = self._normalize_education_entries(payload.get("education"), profile.education)
            context["education"] = education
            context["education_entries"] = education
            context["section_content"] = {
                **context["section_content"],
                "education": self._entries_to_text(education, "school"),
            }

        return context

    def _normalize_summary(
        self,
        *,
        value: Any,
        profile: CandidateProfile,
        job_description: str,
        target_role: str,
    ) -> str:
        summary = self._clean_text(value) if isinstance(value, str) else ""
        if summary:
            sentences = [self._ensure_sentence(item) for item in self._split_sentences(summary) if item]
            if len(sentences) >= 2:
                return "".join(sentences[:3])
        return self._fallback_summary(profile=profile, job_description=job_description, target_role=target_role)

    def _fallback_summary(
        self,
        *,
        profile: CandidateProfile,
        job_description: str,
        target_role: str,
    ) -> str:
        focus_terms = self._extract_focus_terms(job_description, target_role)
        skill_terms = self._collect_skill_terms(profile.skills)
        scene_terms = self._collect_scene_terms(profile)

        focus_phrase = "、".join(focus_terms[:3]) if focus_terms else target_role
        skill_phrase = "、".join(skill_terms[:4]) if skill_terms else "结构化分析、协作推进、结果表达"
        scene_phrase = "、".join(scene_terms[:3]) if scene_terms else "项目推进与业务问题拆解"

        return "".join(
            [
                self._ensure_sentence(
                    f"{target_role}方向候选人，具备{scene_phrase}相关经历，能够围绕{focus_phrase}快速理解需求并组织交付"
                ),
                self._ensure_sentence(
                    f"熟悉{skill_phrase}等能力组合，能将岗位关注点转化为清晰的分析路径、执行动作与结果表达"
                ),
                self._ensure_sentence("过往经历强调方法沉淀、跨角色协作与稳定输出，适合承担需要判断力和落地能力的岗位"),
            ]
        )

    def _normalize_skill_groups(self, value: Any, fallback_skills: Sequence[SkillEntry]) -> List[Dict[str, object]]:
        grouped_items: Dict[str, List[str]] = {}
        raw_groups = self._extract_skill_groups(value)
        for group in raw_groups:
            title = self._canonical_skill_group_title(group.get("title"))
            items = self._extract_items(group.get("items"))
            if title and items:
                grouped_items.setdefault(title, [])
                grouped_items[title].extend(items)

        if not grouped_items:
            for skill in fallback_skills:
                title = self._canonical_skill_group_title(skill.category)
                grouped_items.setdefault(title, [])
                grouped_items[title].extend(self._extract_items(skill.items))

        ordered_titles = self._dedupe_preserve_order(SKILL_GROUP_ORDER + sorted(grouped_items.keys()))
        ordered_groups: List[Dict[str, object]] = []
        for title in ordered_titles:
            if title not in grouped_items:
                continue
            items = self._dedupe_preserve_order(grouped_items[title])
            if not items:
                continue
            meta = SKILL_GROUP_META.get(title, SKILL_GROUP_META["综合技能"])
            ordered_groups.append(
                {
                    "title": meta["title"] if title in SKILL_GROUP_META else title,
                    "icon_latex": meta["icon_latex"],
                    "items": items,
                }
            )
        return ordered_groups

    def _extract_skill_groups(self, value: Any) -> List[Dict[str, Any]]:
        if value is None:
            return []
        if isinstance(value, dict):
            if isinstance(value.get("groups"), list):
                return [item for item in value["groups"] if isinstance(item, dict)]
            groups: List[Dict[str, Any]] = []
            for key, items in value.items():
                if key == "text":
                    continue
                extracted_items = self._extract_items(items)
                if extracted_items:
                    groups.append({"title": key, "items": extracted_items})
            return groups
        if isinstance(value, list):
            groups: List[Dict[str, Any]] = []
            loose_items: List[str] = []
            for item in value:
                if isinstance(item, dict):
                    groups.append(item)
                elif isinstance(item, str):
                    loose_items.extend(self._split_inline_items(item))
            if loose_items:
                groups.append({"title": "综合技能", "items": loose_items})
            return groups
        if isinstance(value, str):
            return [{"title": "综合技能", "items": self._split_inline_items(value)}]
        return []

    def _normalize_project_entries(
        self,
        *,
        raw_projects: Any,
        profile: CandidateProfile,
        job_description: str,
        target_role: str,
    ) -> List[Dict[str, object]]:
        generated_entries = self._extract_object_entries(raw_projects, ("projects", "items", "entries"))
        source_entries = self._sort_entries_by_relevance(
            list(profile.projects),
            job_description=job_description,
            target_role=target_role,
            text_getter=lambda item: " ".join([item.name, item.role or "", *item.highlights]),
        )
        normalized: List[Dict[str, object]] = []
        for source in source_entries:
            matched = self._match_generated_entry(generated_entries, source.name, source.role)
            bullets = self._normalize_bullets(
                raw_bullets=matched.get("bullets") or matched.get("highlights"),
                raw_summary=matched.get("summary"),
                source_highlights=source.highlights,
                label=source.name,
                role_text=source.role,
                kind="project",
            )
            normalized.append(
                {
                    "name": source.name,
                    "role": source.role,
                    "start_date": source.start_date,
                    "end_date": source.end_date,
                    "summary": self._clean_text(matched.get("summary")),
                    "highlights": bullets,
                    "bullets": bullets,
                }
            )
        return normalized

    def _normalize_experience_entries(
        self,
        *,
        raw_experience: Any,
        profile: CandidateProfile,
        job_description: str,
        target_role: str,
    ) -> List[Dict[str, object]]:
        generated_entries = self._extract_object_entries(raw_experience, ("experience", "items", "entries"))
        source_entries = self._sort_entries_by_relevance(
            list(profile.experience),
            job_description=job_description,
            target_role=target_role,
            text_getter=lambda item: " ".join([item.company, item.title or "", *item.highlights]),
        )
        normalized: List[Dict[str, object]] = []
        for source in source_entries:
            matched = self._match_generated_entry(generated_entries, source.company, source.title)
            bullets = self._normalize_bullets(
                raw_bullets=matched.get("bullets") or matched.get("highlights"),
                raw_summary=matched.get("summary"),
                source_highlights=source.highlights,
                label=source.company,
                role_text=source.title,
                kind="experience",
            )
            normalized.append(
                {
                    "company": source.company,
                    "title": source.title,
                    "start_date": source.start_date,
                    "end_date": source.end_date,
                    "summary": self._clean_text(matched.get("summary")),
                    "highlights": bullets,
                    "bullets": bullets,
                }
            )
        return normalized

    def _normalize_education_entries(
        self,
        value: Any,
        fallback_education: Sequence[EducationEntry],
    ) -> List[Dict[str, object]]:
        generated_entries = self._extract_object_entries(value, ("education", "items", "entries"))
        normalized: List[Dict[str, object]] = []
        for source in fallback_education:
            matched = self._match_generated_entry(generated_entries, source.school, source.degree or source.major)
            details = self._extract_items(matched.get("details") or matched.get("highlights") or source.highlights)
            normalized.append(
                {
                    "school": source.school,
                    "degree": source.degree,
                    "major": source.major,
                    "start_date": source.start_date,
                    "end_date": source.end_date,
                    "highlights": details,
                    "details": details,
                }
            )
        return normalized

    def _normalize_bullets(
        self,
        *,
        raw_bullets: Any,
        raw_summary: Any,
        source_highlights: Sequence[str],
        label: str,
        role_text: str | None,
        kind: str,
    ) -> List[str]:
        bullets = [self._polish_bullet(text) for text in self._extract_items(raw_bullets)]
        if raw_summary:
            bullets.extend(self._expand_summary_to_bullets(str(raw_summary), label=label, role_text=role_text, kind=kind))
        for index, highlight in enumerate(source_highlights):
            bullets.append(self._expand_source_highlight(highlight, role_text, kind, index))

        bullets = self._dedupe_preserve_order([item for item in bullets if item])
        defaults = self._default_bullets(label=label, role_text=role_text, kind=kind)
        for default_bullet in defaults:
            if len(bullets) >= 4:
                break
            if default_bullet not in bullets:
                bullets.append(default_bullet)
        return bullets[:4] if bullets else defaults[:3]

    def _expand_summary_to_bullets(self, summary: str, *, label: str, role_text: str | None, kind: str) -> List[str]:
        sentences = self._split_sentences(summary)
        if not sentences:
            return []
        bullets = [self._ensure_sentence(sentences[0])]
        if len(sentences) >= 2:
            bullets.append(
                self._ensure_sentence(
                    f"围绕{label}{'相关工作' if kind == 'experience' else '目标'}持续推进{self._clean_text(sentences[1])}"
                )
            )
        else:
            bullets.append(
                self._ensure_sentence(
                    f"在{label}阶段承担{role_text or ('项目推进' if kind == 'project' else '关键工作')}职责，保证任务衔接和结果表达清晰"
                )
            )
        return bullets

    def _expand_source_highlight(self, highlight: str, role_text: str | None, kind: str, position: int) -> str:
        normalized = self._clean_text(highlight)
        if not normalized:
            return ""
        if position == 0:
            return self._ensure_sentence(
                f"围绕{normalized}承担{role_text or ('项目推进' if kind == 'project' else '执行')}职责，结合目标拆解关键任务并推进落地"
            )
        if position == 1:
            return self._ensure_sentence(f"将{normalized}进一步组织为可执行方案，与相关方持续对齐范围、节奏和交付标准")
        return self._ensure_sentence(f"基于{normalized}形成结构化结论与复盘内容，支持后续协作、沟通与持续优化")
        return self._ensure_sentence(f"基于{normalized}形成结构化结论与复盘内容，支持后续协作、沟通与持续优化")

    def _default_bullets(self, *, label: str, role_text: str | None, kind: str) -> List[str]:
        noun = "项目" if kind == "project" else "岗位工作"
        return [
            self._ensure_sentence(
                f"围绕{label}承担{role_text or noun}中的关键职责，从需求理解、任务拆解到结果呈现保持完整闭环"
            ),
            self._ensure_sentence("在推进过程中注重方法梳理与过程协同，保证信息表达清晰、执行节奏稳定"),
            self._ensure_sentence("对阶段性产出进行整理与复盘，便于后续复用、沟通汇报和持续迭代"),
        ]

    def _sort_entries_by_relevance(
        self,
        entries: List[ProjectEntry] | List[ExperienceEntry],
        *,
        job_description: str,
        target_role: str,
        text_getter,
    ):
        focus_terms = self._extract_focus_terms(job_description, target_role)

        def score(item: ProjectEntry | ExperienceEntry) -> int:
            haystack = self._clean_text(text_getter(item)).lower()
            relevance = sum(2 if term in haystack else 0 for term in focus_terms)
            date_weight = 1 if getattr(item, "end_date", None) else 0
            return relevance + date_weight

        return sorted(entries, key=score, reverse=True)

    def _extract_focus_terms(self, job_description: str, target_role: str) -> List[str]:
        source_text = f"{job_description} {target_role}".lower()
        found = [keyword for keyword in ROLE_KEYWORDS if keyword in source_text]
        if found:
            return self._dedupe_preserve_order(found)
        english_terms = re.findall(r"[a-zA-Z][a-zA-Z0-9+.#/-]{1,20}", source_text)
        chinese_terms = re.findall(r"[\u4e00-\u9fff]{2,6}", source_text)
        return self._dedupe_preserve_order(english_terms + chinese_terms)[:8]

    def _collect_skill_terms(self, skills: Sequence[SkillEntry]) -> List[str]:
        items: List[str] = []
        for group in skills:
            items.extend(group.items)
        return self._dedupe_preserve_order([self._clean_text(item) for item in items if self._clean_text(item)])

    def _collect_scene_terms(self, profile: CandidateProfile) -> List[str]:
        seeds: List[str] = []
        for project in profile.projects:
            seeds.extend([project.name, project.role or "", *project.highlights[:2]])
        for experience in profile.experience:
            seeds.extend([experience.company, experience.title or "", *experience.highlights[:2]])
        cleaned = [item for item in (self._clean_text(seed) for seed in seeds) if 2 <= len(item) <= 24]
        return self._dedupe_preserve_order(cleaned)

    def _build_contact_items(self, profile: CandidateProfile) -> List[Dict[str, str]]:
        basic_info = profile.basic_info
        items: List[Dict[str, str]] = []
        if basic_info.phone:
            items.append({"icon_latex": r"\faPhone*", "text": basic_info.phone, "href": f"tel:{basic_info.phone}"})
        if basic_info.email:
            items.append({"icon_latex": r"\faEnvelope", "text": basic_info.email, "href": f"mailto:{basic_info.email}"})
        if basic_info.city:
            items.append({"icon_latex": r"\faMapMarker*", "text": basic_info.city, "href": ""})
        for link in basic_info.links:
            normalized = self._clean_text(link)
            if not normalized:
                continue
            url = normalized if "://" in normalized else f"https://{normalized}"
            parsed = urlparse(url)
            host = parsed.netloc.lower()
            icon = r"\faGlobe"
            if "github.com" in host:
                icon = r"\faGithub"
            elif "linkedin.com" in host:
                icon = r"\faLinkedin"
            items.append({"icon_latex": icon, "text": self._format_link_label(parsed, normalized), "href": url})
        return items

    @staticmethod
    def _format_link_label(parsed, fallback: str) -> str:
        host = parsed.netloc or ""
        path = parsed.path.strip("/")
        if host and path:
            return f"{host}/{path}"
        return host or fallback

    def _build_preview_sections(self, selected_sections: Sequence[ResumeSection]) -> List[PreviewSection]:
        preview_sections: List[PreviewSection] = []
        for index, section in enumerate(selected_sections):
            preview_sections.append(
                PreviewSection(
                    section=section,
                    title=SECTION_META[section.value]["title"],
                    order=index,
                )
            )
        return preview_sections

    def _match_generated_entry(
        self,
        generated_entries: Sequence[Dict[str, Any]],
        primary_name: str,
        secondary_name: str | None,
    ) -> Dict[str, Any]:
        if not generated_entries:
            return {}
        primary = self._normalize_lookup(primary_name)
        secondary = self._normalize_lookup(secondary_name or "")
        for entry in generated_entries:
            values = [
                self._normalize_lookup(str(entry.get(key, "")))
                for key in ("name", "project_name", "company", "school", "title", "role")
            ]
            joined = " ".join(value for value in values if value)
            if primary and primary in joined:
                return entry
            if secondary and secondary in joined:
                return entry
        return {}

    @staticmethod
    def _extract_object_entries(value: Any, preferred_keys: Sequence[str]) -> List[Dict[str, Any]]:
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            for key in preferred_keys:
                if isinstance(value.get(key), list):
                    return [item for item in value[key] if isinstance(item, dict)]
        return []

    def _project_entry_from_profile(self, item: ProjectEntry) -> Dict[str, object]:
        bullets = [self._ensure_sentence(point) for point in self._extract_items(item.highlights)]
        return {
            "name": item.name,
            "role": item.role,
            "start_date": item.start_date,
            "end_date": item.end_date,
            "summary": "",
            "highlights": bullets,
            "bullets": bullets,
        }

    def _experience_entry_from_profile(self, item: ExperienceEntry) -> Dict[str, object]:
        bullets = [self._ensure_sentence(point) for point in self._extract_items(item.highlights)]
        return {
            "company": item.company,
            "title": item.title,
            "start_date": item.start_date,
            "end_date": item.end_date,
            "summary": "",
            "highlights": bullets,
            "bullets": bullets,
        }

    def _education_entry_from_profile(self, item: EducationEntry) -> Dict[str, object]:
        details = [self._ensure_sentence(point) for point in self._extract_items(item.highlights)]
        return {
            "school": item.school,
            "degree": item.degree,
            "major": item.major,
            "start_date": item.start_date,
            "end_date": item.end_date,
            "highlights": details,
            "details": details,
        }

    @staticmethod
    def _entries_to_text(entries: Sequence[Dict[str, object]], key: str) -> str:
        values = [str(entry.get(key, "")).strip() for entry in entries if str(entry.get(key, "")).strip()]
        return "；".join(values)

    @staticmethod
    def _skill_groups_to_text(groups: Sequence[Dict[str, object]]) -> str:
        fragments: List[str] = []
        for group in groups:
            title = str(group.get("title", "")).strip()
            items = [str(item).strip() for item in group.get("items", []) if str(item).strip()]
            if title and items:
                fragments.append(f"{title}：{' / '.join(items)}")
        return "；".join(fragments)

    @staticmethod
    def _entries_to_text(entries: Sequence[Dict[str, object]], key: str) -> str:
        values = [str(entry.get(key, "")).strip() for entry in entries if str(entry.get(key, "")).strip()]
        return "；".join(values)

    @staticmethod
    def _skill_groups_to_text(groups: Sequence[Dict[str, object]]) -> str:
        fragments: List[str] = []
        for group in groups:
            title = str(group.get("title", "")).strip()
            items = [str(item).strip() for item in group.get("items", []) if str(item).strip()]
            if title and items:
                fragments.append(f"{title}：{' / '.join(items)}")
        return "；".join(fragments)

    @staticmethod
    def _extract_items(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return ResumeDraftingService._split_inline_items(value)
        return []

    @staticmethod
    def _split_inline_items(value: str) -> List[str]:
        text = str(value).replace("\r", "\n")
        parts = re.split(r"[\n;；、|]+", text)
        return [part.strip(" -\t") for part in parts if part.strip(" -\t")]

    @staticmethod
    def _clean_text(value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip()

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        return [item.strip() for item in re.split(r"[。！？!?]+", text) if item.strip()]

    @staticmethod
    def _ensure_sentence(text: str) -> str:
        cleaned = ResumeDraftingService._clean_text(text).rstrip("，；。!?！？")
        if not cleaned:
            return ""
        return cleaned if cleaned[-1] in "。！？!?" else f"{cleaned}。"

    @staticmethod
    def _polish_bullet(text: str) -> str:
        cleaned = ResumeDraftingService._clean_text(text).lstrip("-•·")
        if not cleaned:
            return ""
        return ResumeDraftingService._ensure_sentence(cleaned)

    @staticmethod
    def _normalize_lookup(value: str) -> str:
        return re.sub(r"\s+", "", value).lower()

    @staticmethod
    def _dedupe_preserve_order(items: Sequence[str]) -> List[str]:
        seen = set()
        ordered: List[str] = []
        for item in items:
            normalized = ResumeDraftingService._normalize_lookup(item)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(item)
        return ordered

    @staticmethod
    def _canonical_skill_group_title(value: Any) -> str:
        normalized = ResumeDraftingService._clean_text(value).lower()
        if not normalized:
            return "综合技能"
        if normalized in {"编程", "开发", "programming", "language", "languages", "coding"}:
            return "编程"
        if normalized in {"分析", "analytics", "analysis", "数据分析", "data analysis", "建模"}:
            return "分析"
        if normalized in {"工具", "tools", "tool", "平台", "software", "devops"}:
            return "工具"
        if normalized in {"方法", "method", "methodology", "业务方法", "框架"}:
            return "方法"
        return ResumeDraftingService._clean_text(value) or "综合技能"
