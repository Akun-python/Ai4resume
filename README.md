# 中文 LaTeX 简历智能体

这是一个后端优先、现已补齐前端工作台的简历生成项目。用户输入个人经历和岗位描述后，系统会调用 LLM 抽取结构化信息，生成 LaTeX，编译 PDF，并支持按模块重生成。

## 功能概览

### 后端
- `POST /v1/resume/jobs` 创建简历生成任务
- `GET /v1/resume/jobs/{job_id}` 查询任务状态、可用区块和结果摘要
- `GET /v1/resume/jobs/{job_id}/artifacts/{kind}` 下载 `json | tex | pdf`
- `POST /v1/resume/jobs/{job_id}/sections/{section}/regenerate` 按模块重生成

### 前端
- 单页输入工作台，支持岗位描述和经历原文提交
- 任务状态自动轮询
- PDF 内嵌预览与 `pdf / tex / json` 下载
- `summary / skills / projects / experience / education` 区块重生成

## 目录结构

- `app/` FastAPI 后端、领域模型、服务层与模板
- `worker/` Celery 任务
- `tests/` 后端测试
- `frontend/` Vite + React + TypeScript 前端工作台

## 后端本地运行

1. 复制 `.env.example` 为 `.env` 并填写配置。
2. 安装依赖：

```bash
pip install --user -e .[dev]
```

3. 启动 API：

```bash
uvicorn app.main:app --reload
```

4. 启动 worker：

```bash
celery -A app.infra.queue.celery_app.celery_app worker --loglevel=info -Q resume
```

## 前端本地运行

```bash
cd frontend
npm install
npm run dev
```

开发模式下，Vite 会把 `/v1/*` 请求代理到 `http://127.0.0.1:8000`。

如果你本地暂时没有启动 Redis 和 Celery，但想先把接口跑通，可以在 `.env` 中设置：

```bash
JOB_DISPATCH_MODE=inline
```

这样创建任务和区块重生成会在 API 进程内直接执行，不依赖消息队列。

## 测试与构建

### 后端测试

```bash
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest -q
```

### 前端测试

```bash
cd frontend
npm run test
```

### 前端构建

```bash
cd frontend
npm run build
```

## Docker

```bash
docker compose up --build
```

当前 Docker 编排覆盖 API、worker、Redis 和 PostgreSQL。前端暂时独立运行，不在本轮挂入 FastAPI 或 Compose。
