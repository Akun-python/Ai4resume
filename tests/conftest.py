from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "test.db"
    artifact_root = tmp_path / "artifacts"

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/15")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("CELERY_TASK_ALWAYS_EAGER", "true")
    monkeypatch.setenv("ARTIFACT_ROOT", str(artifact_root))

    from app.core.config import get_settings

    get_settings.cache_clear()

    from app.infra.llm.client import OpenAICompatibleLLMClient

    def fake_generate_json(self, *, schema_name: str, system_prompt: str, user_prompt: str):
        if schema_name == "candidate_profile":
            return {
                "basic_info": {
                    "name": "张三",
                    "phone": "13800000000",
                    "email": "zhangsan@example.com",
                    "city": "上海",
                    "links": ["https://github.com/zhangsan"],
                },
                "education": [
                    {
                        "school": "上海交通大学",
                        "degree": "硕士",
                        "major": "数据科学",
                        "start_date": "2022.09",
                        "end_date": "2025.03",
                        "highlights": ["研究方向聚焦数据分析与业务建模"],
                    }
                ],
                "experience": [
                    {
                        "company": "某数据公司",
                        "title": "数据分析实习生",
                        "start_date": "2024.06",
                        "end_date": "2024.12",
                        "highlights": ["搭建自动化报表体系", "支持业务指标分析"],
                    }
                ],
                "projects": [
                    {
                        "name": "用户增长分析平台",
                        "role": "项目负责人",
                        "start_date": "2024.01",
                        "end_date": "2024.05",
                        "highlights": ["完成指标体系设计", "搭建留存分析框架"],
                    }
                ],
                "skills": [
                    {"category": "编程", "items": ["Python", "SQL", "Pandas"]},
                    {"category": "分析", "items": ["A/B测试", "指标体系", "可视化"]},
                ],
                "awards": [],
            }

        if schema_name == "resume_draft_bundle":
            if "额外要求" in user_prompt:
                return {
                    "summary": (
                        "聚焦数据分析与业务问题拆解，表达更加克制专业，能够围绕岗位重点组织分析路径。"
                        "过往经历覆盖自动化报表、增长分析与指标体系搭建，强调结果表达与协作推进。"
                    ),
                    "projects": [
                        {
                            "name": "用户增长分析平台",
                            "bullets": [
                                "围绕增长目标梳理北极星指标与核心漏斗，形成更贴近岗位关注点的分析框架。",
                                "结合留存分析和分群视角组织专题研究，突出结论输出与决策支持。",
                                "沉淀指标口径与复盘表达方式，便于团队复用和后续沟通。",
                            ],
                        }
                    ],
                }

            return {
                "summary": (
                    "聚焦数据分析与业务问题拆解，能够围绕岗位关注点快速梳理需求、组织分析路径并形成结构化表达。"
                    "过往经历覆盖自动化报表、增长分析与指标体系搭建，强调方法沉淀与跨团队协作。"
                ),
                "skills": {
                    "groups": [
                        {"title": "编程", "items": ["Python", "SQL", "Pandas"]},
                        {"title": "分析", "items": ["A/B测试", "指标体系", "可视化"]},
                        {"title": "工具", "items": ["Excel", "Power BI"]},
                    ]
                },
                "projects": [
                    {
                        "name": "用户增长分析平台",
                        "role": "项目负责人",
                        "bullets": [
                            "围绕增长目标梳理北极星指标与核心漏斗，完成项目框架设计。",
                            "结合留存分析和分群视角组织分析路径，支持阶段性复盘与方案迭代。",
                            "沉淀指标口径与结论表达方式，便于团队复用和后续沟通。",
                        ],
                    }
                ],
                "experience": [
                    {
                        "company": "某数据公司",
                        "title": "数据分析实习生",
                        "bullets": [
                            "搭建自动化报表体系，优化日常数据追踪与汇总流程。",
                            "围绕业务指标变化进行专题分析，支持团队快速定位重点问题。",
                            "对阶段性分析结果进行结构化呈现，提升跨团队沟通效率。",
                        ],
                    }
                ],
                "education": [
                    {
                        "school": "上海交通大学",
                        "degree": "硕士",
                        "major": "数据科学",
                        "details": ["研究方向聚焦数据分析与业务建模"],
                    }
                ],
            }

        return {}

    monkeypatch.setattr(OpenAICompatibleLLMClient, "generate_json", fake_generate_json)

    from app.services.compiler import LatexCompilerService

    def fake_compile(self, tex_path: str) -> str:
        pdf_path = Path(tex_path).with_suffix(".pdf")
        pdf_path.write_bytes(b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF")
        return str(pdf_path)

    monkeypatch.setattr(LatexCompilerService, "compile", fake_compile)

    from app.infra.db import models  # noqa: F401
    from app.infra.db.base import Base
    from app.infra.db.session import engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    from app.main import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
