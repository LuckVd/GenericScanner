# `/commit` Command

> Git 提交流程 + Skills 集成 + 自动更新状态文件

---

## 执行流程

### 1. Pre-commit 检查

按优先级检测并执行 lint：

```
package.json → npm run lint / pnpm lint / yarn lint
Makefile     → make lint
Python + uv  → uv run ruff check . / uv run flake8 / uv run black --check .
Python       → ruff check . / flake8 / black --check .
```

**Python 环境优先级**：
- 存在 `uv.lock` 或 `.venv/` 时，优先使用 `uv run` 执行命令
- 示例：`uv run ruff check .` 而非 `ruff check .`

- Lint 失败 → 停止流程，输出错误

### 2. 清理临时文件

在提交前，检测并删除与项目本身无关的临时文件：

**需要删除的临时文件类型**：

| 类型 | 模式 | 示例 |
|------|------|------|
| 缓存文件 | `**/__pycache__/`, `**/*.pyc`, `.pytest_cache/` | Python 缓存 |
| 构建产物 | `**/dist/`, `**/build/`, `**/*.egg-info/` | 构建输出 |
| 临时报告 | `**/coverage-report/`, `**/.coverage`, `**/htmlcov/` | 测试报告 |
| 日志文件 | `**/*.log`, `**/logs/*.log` | 运行日志 |
| 临时文件 | `**/*.tmp`, `**/*.temp`, `**/*.swp` | 编辑器临时文件 |
| IDE 文件 | `**/.idea/`, `**/.vscode/` (可选保留) | IDE 配置 |

**执行步骤**：
1. 扫描项目目录，识别上述临时文件
2. 输出待删除列表供确认
3. 用户确认后删除
4. 从 Git 跟踪中移除（如已跟踪）

**输出格式**：
```
🧹 Temporary Files Cleanup

Found temporary files:
- __pycache__/ (15 files)
- .pytest_cache/ (3 files)
- coverage-report/ (8 files)

Delete these files before commit? [Y/n]
```

**注意**：
- 不要删除 `.gitignore` 中未忽略但项目需要的文件
- 保留 `.env.example` 等示例文件
- 保留测试数据文件（如 `tests/fixtures/`）

### 3. 调用 workspace-governor Skill

读取 `.claude/PROJECT.md`，执行文件保护检查：

**详见**: `.claude/skills/workspace-governor.md`

| 模块 Level | 动作 |
|------------|------|
| `core` | 输出 Core Protection Warning，拒绝自动提交 |
| `stable` | 输出 Stability Modification Proposal，等待确认 |
| `active` | 允许继续 |

### 4. 调用 api-governor Skill（如涉及 API 文件）

若变更涉及 API 相关文件，执行 Breaking Change 检测：

**详见**: `.claude/skills/api-governor.md`

**API 相关路径**:
- `docs/api/**`
- `**/routes/**`
- `**/api/**`
- `**/controllers/**`
- `**/endpoints/**`

| 检测结果 | 动作 |
|----------|------|
| Breaking Change | 输出 API Change Proposal，等待确认 |
| Non-Breaking | 允许继续，提示更新文档 |

### 5. 调用 goal-tracker Skill

检查当前目标进度，询问用户目标是否完成：

**详见**: `.claude/skills/goal-tracker.md`

| 目标状态 | 动作 |
|----------|------|
| `in_progress` | 输出目标完成询问 |
| `completed` | 提示设置新目标 |
| `blocked` | 输出阻塞原因 |

**目标完成询问格式**:

```
📌 Goal Progress Check

Current Goal: <任务描述>
Status: in_progress
Created: <创建日期>
Progress: <提交次数> commits

Changes to commit:
- <变更文件列表>

Is this goal completed?
[ ] Yes - Mark as completed
[ ] No - Continue tracking
```

**用户确认后**:
- 完成 → 更新 `docs/CURRENT_GOAL.md` 状态为 `completed` → 询问下一个目标
- 未完成 → 追加进度记录到 PROJECT.md → 继续提交流程

### 6. Stage

```
git add <files>
```

### 7. 生成 Commit Message

分析 `git diff --cached`，按 Conventional Commits 生成：

```
<type>[scope][!]: <description>

<body>

<footer>
```

**Type 列表：**
- `feat` - 新功能
- `fix` - Bug 修复
- `refactor` - 重构
- `perf` - 性能优化
- `docs` - 文档
- `style` - 代码风格
- `test` - 测试
- `build` - 构建
- `ci` - CI/CD
- `chore` - 杂项
- `deps` - 依赖
- `config` - 配置

**Breaking Change：** 使用 `!` 或 footer `BREAKING CHANGE:`

**Commit Message 内容要求**：

commit message 的 body 部分必须包含从上次 commit 到本次的所有变更内容：

```markdown
## 变更内容

### 新增
- <新增的功能/文件>

### 修改
- <修改的内容>

### 删除
- <删除的内容>

### 修复
- <修复的问题>
```

**生成步骤**：
1. 执行 `git log -1 --pretty=%B HEAD` 获取上次 commit message
2. 执行 `git diff HEAD~1..HEAD --stat` 获取变更统计
3. 执行 `git diff HEAD~1..HEAD` 分析具体变更内容
4. 汇总所有变更，生成完整的 commit message body

**示例**：

```
feat(auth): 实现用户认证模块

## 变更内容

### 新增
- src/auth/login.py: 用户登录逻辑
- src/auth/token.py: JWT token 生成与验证
- tests/test_auth.py: 认证模块单元测试

### 修改
- src/config.py: 添加 JWT 配置项
- requirements.txt: 添加 pyjwt 依赖

### 删除
- src/deprecated/auth_old.py: 移除旧认证实现

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 8. 执行 Commit

```
git commit
```

### 9. 自动更新状态文件

提交成功后，更新以下文件：

**1. PROJECT.md — 追加开发历史**

```markdown
| 日期 | Commit | 描述 |
|------|--------|------|
| 2026-02-15 | abc1234 | feat: add user authentication |
```

**2. CURRENT_GOAL.md — 更新进度记录**

```markdown
## 进度记录

| 时间 | 进展 |
|------|------|
| 2026-02-15 | 开始实现登录逻辑 |
| 2026-02-15 14:30 | feat: add user authentication |
```

**3. ROADMAP.md — 同步当前焦点（如目标/阶段变化）**

```markdown
## 当前焦点

| 字段 | 值 |
|------|-----|
| **阶段** | Phase 1 |
| **目标** | 实现用户登录 API |
| **重点模块** | backend-features |
```

**4. 检测模块状态升级**

检查每个 `dev` 状态的模块：
- 获取最近 3 次 commit 的变更文件列表
- 若模块路径无变动 → 输出升级建议

```
Module Upgrade Suggestion:
- backend-core: dev → done (3 commits without changes)
  Confirm upgrade? [y/N]
```

**5. 检测 API 变更**

若变更涉及 `docs/api/**` 或 API 相关代码：
```
API Change Detected:
- Modified: docs/api/API.md
- Remember to update API documentation
```

### 10. 更新 Git 历史记录

提交成功后，更新 Git 历史文档系统：

#### 9.1 更新 history.md（简洁摘要）

追加一行到 `docs/git/history.md`：

```markdown
| 2026-02-15 14:30 | a1b2c3d | feat(auth): 实现用户登录 API，支持 JWT 认证 |
```

**格式要求**：
- 时间：`YYYY-MM-DD HH:MM`
- Commit：短 ID（7 位）
- 简介：不超过 50 字，来源于 commit message 的精简

**操作步骤**：
1. 读取 `docs/git/history.md`
2. 移除 `| - | - | （暂无记录） |` 占位行（如存在）
3. 追加新行到表格末尾

#### 9.2 创建详细日志文件

**路径**: `docs/git/logs/YYYY-MM-DD-HHMM-commitid.md`

**示例**: `docs/git/logs/2026-02-15-1430-a1b2c3d.md`

**内容模板**：

```markdown
# <commit-id>

## 基本信息

| 字段 | 值 |
|------|-----|
| **时间** | <YYYY-MM-DD HH:MM> |
| **Commit** | <完整 commit hash> |
| **Message** | <完整 commit message> |

## 简介

<commit message 的中文精简描述>

## 变更文件

| 文件 | 操作 |
|------|------|
| `src/auth/login.ts` | 新增 |
| `src/auth/token.ts` | 修改 |
| `tests/auth.test.ts` | 删除 |

## API 变更

> 如涉及 API 变更

| 端点 | 操作 | 说明 |
|------|------|------|
| `POST /api/login` | 新增 | 用户登录，返回 JWT token |

## 功能变更

| 功能 | 操作 | 说明 |
|------|------|------|
| JWT 认证 | 新增 | 支持 token 生成和验证 |
| 密码验证 | 新增 | bcrypt 密码比对 |

## 关联目标

- 目标：<当前目标描述>
- 状态：<目标状态>
```

**信息收集来源**：

| 信息 | 来源 | 用途 |
|------|------|------|
| Commit ID | `git rev-parse HEAD` | 日志文件名 + 内容 |
| Commit Message | `git log -1 --pretty=%B` | 简介 + Message 字段 |
| 变更文件列表 | `git diff --name-status HEAD~1` | 变更文件表 |
| API 变更 | api-governor 检测结果 | API 变更表 |
| 目标信息 | `docs/CURRENT_GOAL.md` | 关联目标 |
| 时间戳 | 系统时间 | 记录时间 |

### 11. Push

```
git push
```

---

## Skills 集成详情

### workspace-governor 调用

**触发**: 所有文件变更

**执行**:
1. 读取 PROJECT.md 获取模块定义
2. 匹配变更文件到模块
3. 检查模块 Level
4. 执行保护逻辑

**输出**:
- `core` → Core Protection Warning → 阻止
- `stable` → Stability Modification Proposal → 等待确认
- `active` → 静默通过

### api-governor 调用

**触发**: API 相关文件变更

**执行**:
1. 分析变更内容
2. 判断是否 Breaking Change
3. 输出提案或允许执行

**输出**:
- Breaking Change → API Change Proposal → 等待确认
- Non-Breaking → 允许执行，提示更新文档

### goal-tracker 调用

**触发**: 所有提交

**执行**:
1. 读取 `docs/CURRENT_GOAL.md`
2. 检查目标状态
3. 输出目标完成询问
4. 根据用户回答更新状态

**输出**:
- in_progress → 目标完成询问 → 等待确认
- completed → 提示设置新目标
- blocked → 输出阻塞原因

---

## 流程图

```
/commit
   │
   ▼
┌──────────────────┐
│ 1. Lint Check    │── Fail ──→ Stop
└────────┬─────────┘
         │ Pass
         ▼
┌──────────────────┐
│ 2. 清理临时文件   │── 用户取消 ──→ Stop
│    (Cleanup)     │
└────────┬─────────┘
         │ 确认
         ▼
┌──────────────────┐
│ 3. workspace-    │
│    governor      │── core ────→ ⛔ Block
│    Skill         │
└────────┬─────────┘
         │ stable ──→ ⚠️ Wait Confirm
         │ active
         ▼
┌──────────────────┐
│ 4. api-governor  │
│    Skill         │── Breaking ──→ ⚠️ Wait Confirm
│ (if API files)   │
└────────┬─────────┘
         │ OK
         ▼
┌──────────────────┐
│ 5. goal-tracker  │
│    Skill         │── completed ──→ 💡 Prompt new goal
│                  │
└────────┬─────────┘
         │ in_progress
         ▼
┌──────────────────┐
│ 6. Stage         │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 7. Generate      │
│    Commit Msg    │
│  (含完整变更)    │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 8. Commit        │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 9. Update        │
│ - PROJECT.md     │
│ - CURRENT_GOAL   │
│ - ROADMAP.md     │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 10. Git History  │
│ - history.md     │
│ - logs/详细日志  │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 11. Push         │
└──────────────────┘
```

---

## 输出格式

```
✅ Commit Successful

Commit: abc1234
Message: feat(auth): add user authentication

Skills Executed:
- workspace-governor: passed (active modules)
- api-governor: skipped (no API changes)
- goal-tracker: progress recorded (goal in progress)

Updated:
- .claude/PROJECT.md (history)
- docs/CURRENT_GOAL.md (progress)
- docs/ROADMAP.md (focus)
- docs/git/history.md (summary)
- docs/git/logs/2026-02-15-1430-abc1234.md (detail)

Suggestions:
- backend-core: consider upgrading to done/stable

Push: Success
```

---

## Stability Modification Proposal

修改 `stable` 模块时输出：

```
⚠️ Stability Modification Proposal

Module: <module-name>
Level: stable
Files: <changed-files>

Changes:
<change-summary>

Impact:
<impact-analysis>

Confirm modification? [y/N]
```

---

## Core Protection Warning

修改 `core` 模块时输出：

```
⛔ Core Protection Warning

Module: <module-name>
Level: core
Files: <changed-files>

This module is protected from automatic modification.

To modify:
1. Manually edit .claude/PROJECT.md
2. Change module level: core → stable
3. Re-run /commit

Operation blocked.
```

---

## API Change Proposal

检测到 Breaking Change 时输出：

```
⚠️ API Change Proposal

Breaking Change Detected!

Affected Endpoint: <method> <path>
Files: <changed-files>

Changes:
<change-details>

Impact:
<impact-analysis>

Required Actions:
[ ] Update docs/api/API.md
[ ] Notify API consumers

Confirm this Breaking Change? [y/N]
```

---

## 禁止行为

- Lint 失败仍提交
- 跳过清理临时文件步骤
- 跳过保护检查（workspace-governor）
- 跳过 API 变更检测（api-governor）
- 跳过目标进度检查（goal-tracker）
- 自动升级模块 Level
- 覆盖历史记录
- 忽略 Skills 输出
- 未经确认修改目标状态
- 提交不完整的 commit message（必须包含所有变更内容）
- 提交临时文件（缓存、日志、报告等）
