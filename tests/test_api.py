from __future__ import annotations

from app.core.errors import QueueDispatchError
from app.domain.enums import ArtifactKind, ResumeSection


def test_create_job_and_fetch_status(client):
    response = client.post(
        "/v1/resume/jobs",
        json={
            "raw_experience_text": "我在某数据公司实习，做过自动化报表和用户增长分析，也负责过指标体系设计。",
            "job_description": "应聘数据分析岗位，需要 SQL、Python、指标分析与增长分析能力。",
            "target_role": "数据分析师",
            "basic_info": {
                "name": "张三",
                "email": "zhangsan@example.com",
            },
            "presentation_options": {"theme_id": "forest_slate"},
        },
    )

    assert response.status_code == 202
    job_id = response.json()["job_id"]

    status_response = client.get(f"/v1/resume/jobs/{job_id}")
    assert status_response.status_code == 200
    payload = status_response.json()
    assert payload["status"] == "succeeded"
    assert payload["presentation"]["theme_id"] == "forest_slate"
    assert payload["preview_sections"][0]["section"] == ResumeSection.SUMMARY.value
    assert ResumeSection.SUMMARY.value in payload["available_sections"]
    assert payload["artifacts"][ArtifactKind.JSON.value]
    assert payload["artifacts"][ArtifactKind.TEX.value]
    assert payload["artifacts"][ArtifactKind.PDF.value]


def test_download_artifacts(client):
    create_response = client.post(
        "/v1/resume/jobs",
        json={
            "raw_experience_text": "我做过项目分析和数据报表。",
            "job_description": "数据分析岗位，要求 SQL、Python。",
            "target_role": "数据分析师",
        },
    )
    job_id = create_response.json()["job_id"]

    for kind, expected_type in {
        "json": "application/json",
        "tex": "application/x-tex",
        "pdf": "application/pdf",
    }.items():
        response = client.get(f"/v1/resume/jobs/{job_id}/artifacts/{kind}")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith(expected_type)
        if kind == "pdf":
            assert response.headers["content-disposition"].startswith("inline;")
        else:
            assert "filename=" in response.headers["content-disposition"]


def test_regenerate_section_creates_child_job(client):
    create_response = client.post(
        "/v1/resume/jobs",
        json={
            "raw_experience_text": "我做过项目分析和数据报表。",
            "job_description": "数据分析岗位，要求 SQL、Python。",
            "target_role": "数据分析师",
        },
    )
    parent_job_id = create_response.json()["job_id"]

    regenerate_response = client.post(
        f"/v1/resume/jobs/{parent_job_id}/sections/{ResumeSection.SUMMARY.value}/regenerate"
    )
    assert regenerate_response.status_code == 202

    child_job_id = regenerate_response.json()["job_id"]
    child_status = client.get(f"/v1/resume/jobs/{child_job_id}")
    payload = child_status.json()
    assert payload["parent_job_id"] == parent_job_id
    assert payload["section_to_regenerate"] == ResumeSection.SUMMARY.value
    assert payload["status"] == "succeeded"


def test_regenerate_section_supports_refine_payload(client):
    create_response = client.post(
        "/v1/resume/jobs",
        json={
            "raw_experience_text": "我做过项目分析和数据报表。",
            "job_description": "数据分析岗位，要求 SQL、Python。",
            "target_role": "数据分析师",
        },
    )
    parent_job_id = create_response.json()["job_id"]

    regenerate_response = client.post(
        f"/v1/resume/jobs/{parent_job_id}/sections/{ResumeSection.PROJECTS.value}/regenerate",
        json={
            "preset": "more_results_focused",
            "custom_instruction": "更强调可交付成果和汇报表达。",
            "theme_id": "terracotta_ink",
        },
    )
    assert regenerate_response.status_code == 202

    child_job_id = regenerate_response.json()["job_id"]
    child_status = client.get(f"/v1/resume/jobs/{child_job_id}")
    payload = child_status.json()
    assert payload["parent_job_id"] == parent_job_id
    assert payload["section_to_regenerate"] == ResumeSection.PROJECTS.value
    assert payload["presentation"]["theme_id"] == "terracotta_ink"
    assert payload["status"] == "succeeded"


def test_cors_preflight_for_create_job(client):
    response = client.options(
        "/v1/resume/jobs",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_create_job_returns_503_when_dispatch_fails(client, monkeypatch):
    def fail_dispatch(*args, **kwargs):
        raise QueueDispatchError("dispatch failed")

    monkeypatch.setattr("app.api.routes.resume.dispatch_task", fail_dispatch)

    response = client.post(
        "/v1/resume/jobs",
        json={
            "raw_experience_text": "test",
            "job_description": "test",
            "target_role": "test",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "dispatch failed"
