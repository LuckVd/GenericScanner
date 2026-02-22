# PROJECT.md

> VulnScan Engine 唯一配置文档 — 项目信息、模块定义、保护规则、开发历史

---

## 项目信息

| 字段 | 值 |
|------|-----|
| **名称** | VulnScan Engine |
| **类型** | backend |
| **描述** | 企业级分布式漏洞扫描引擎，支持高并发、插件化、智能指纹识别、资产管理与统计追踪 |

### 运行环境约束

| 项目类型 | 约束 |
|----------|------|
| **Python + uv** | 优先使用 uv 创建的虚拟环境运行项目 |
| **检测方式** | 存在 `pyproject.toml` + `.venv/` 或 `uv.lock` 时启用 |

**Python 环境优先级**：
```
1. uv 虚拟环境 (.venv/bin/python 或 .venv/Scripts/python.exe)
2. 系统 Python
```

**常用命令**：
```bash
# 使用 uv 运行
uv run python <script>
uv run pytest
uv run ruff check .
```

---

## 模块定义

### 模块状态说明

| Status | 说明 |
|--------|------|
| `todo` | 未开始 |
| `dev` | 开发中 |
| `done` | 已完成 |

### 模块等级说明

| Level | 含义 | 修改规则 |
|-------|------|----------|
| `active` | 活跃开发 | 自由修改 |
| `stable` | 已稳定 | 需确认 |
| `core` | 核心保护 | 禁止自动修改 |

### 模块列表

| 模块 | 路径 | Status | Level |
|------|------|--------|-------|
| claude-control | `.claude/**` | done | core |
| governance-specs | `docs/api/**`, `docs/CURRENT_GOAL.md`, `docs/ROADMAP.md` | done | core |
| git-history | `docs/git/**` | done | stable |
| api-gateway | `scheduler/api_gateway/**` | todo | active |
| task-manager | `scheduler/task_manager/**` | todo | active |
| dispatcher | `scheduler/dispatcher/**` | todo | active |
| asset-center | `scheduler/asset_center/**` | todo | active |
| stats-center | `scheduler/stats_center/**` | todo | active |
| plugin-repo | `scheduler/plugin_repo/**` | todo | active |
| config-center | `scheduler/config_center/**` | todo | active |
| node-manager | `scanner/node_manager/**` | todo | active |
| auth-manager | `scanner/core_engine/auth_manager/**` | todo | active |
| fingerprint | `scanner/core_engine/fingerprint/**` | todo | active |
| vuln-detector | `scanner/core_engine/vuln_detector/**` | todo | active |
| plugin-loader | `scanner/plugin_loader/**` | todo | active |
| security | `scanner/security/**` | todo | active |
| common-models | `common/models/**` | todo | active |
| common-utils | `common/utils/**` | todo | active |
| plugins | `plugins/**` | todo | active |
| tests | `tests/**` | todo | active |

---

## 保护规则

### 文件保护

```
Level: core  → 禁止自动修改，需人工降级
Level: stable → 修改前输出 Stability Modification Proposal，等待确认
Level: active → 允许自由修改
```

### API 保护

API 文件变更时：
- 检测 Breaking Change（参数删除/类型变更/响应结构变化）
- 稳定 API 变更需确认
- 自动提示更新 `docs/api/API.md`

### 默认原则

- 未定义的模块默认为 `active`
- 不确定时默认视为 `stable`
- AI 不得自动升级 Level（active → stable → core）

---

## 开发历史

> 每次提交后自动追加

| 日期 | Commit | 描述 |
|------|--------|------|
| 2026-02-22 | 63416ee | docs: 初始化 VulnScan Engine 项目配置 |
| 2026-02-22 | 53f7aea | feat(scheduler): 实现 Phase 1 任务调度中心基础框架 |

---

## 自动升级规则

提交后自动检测：

1. **模块状态升级建议**
   - 条件：模块 `dev` + 最近 3 次提交无该模块变动
   - 动作：建议升级为 `done` + `stable`

2. **API 变更检测**
   - 条件：检测到 API 文件变更
   - 动作：提示更新 `docs/api/API.md`

3. **保护文件警告**
   - 条件：修改 `stable` 或 `core` 文件
   - 动作：输出提示，等待确认

---

## 当前目标

> 当前开发目标独立维护，详见 `docs/CURRENT_GOAL.md`

**快速操作：**
- 查看目标：`/goal`
- 设置目标：`/goal set <任务描述>`
- 标记完成：`/goal done`

---

## 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.11+ |
| 异步框架 | asyncio |
| 消息队列 | RabbitMQ |
| 数据库 | MySQL |
| 缓存 | Redis |
| ORM | SQLAlchemy |
| API 框架 | FastAPI |
| 任务调度 | Celery (可选) |
