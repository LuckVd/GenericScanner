# `/commit` Command

> Git 提交流程 + Skills 集成 + 自动更新 PROJECT.md

---

## 执行流程

### 1. Pre-commit 检查

按优先级检测并执行 lint：

```
package.json → npm run lint / pnpm lint / yarn lint
Makefile     → make lint
Python       → ruff check . / flake8 / black --check .
```

- Lint 失败 → 停止流程，输出错误

### 2. 调用 workspace-governor Skill

读取 `.claude/PROJECT.md`，执行文件保护检查：

**详见**: `.claude/skills/workspace-governor.md`

| 模块 Level | 动作 |
|------------|------|
| `core` | 输出 Core Protection Warning，拒绝自动提交 |
| `stable` | 输出 Stability Modification Proposal，等待确认 |
| `active` | 允许继续 |

### 3. 调用 api-governor Skill（如涉及 API 文件）

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

### 4. Stage

```
git add <files>
```

### 5. 生成 Commit Message

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

### 6. 执行 Commit

```
git commit
```

### 7. 自动更新 PROJECT.md

提交成功后，更新 `.claude/PROJECT.md`：

1. **追加开发历史**

```markdown
| 日期 | Commit | 描述 |
|------|--------|------|
| 2026-02-15 | abc1234 | feat: add user authentication |
```

2. **检测模块状态升级**

检查每个 `dev` 状态的模块：
- 获取最近 3 次 commit 的变更文件列表
- 若模块路径无变动 → 输出升级建议

```
Module Upgrade Suggestion:
- backend-core: dev → done (3 commits without changes)
  Confirm upgrade? [y/N]
```

3. **检测 API 变更**

若变更涉及 `docs/api/**` 或 API 相关代码：
```
API Change Detected:
- Modified: docs/api/API.md
- Remember to update API documentation
```

### 8. Push

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
│ 2. workspace-    │
│    governor      │── core ────→ ⛔ Block
│    Skill         │
└────────┬─────────┘
         │ stable ──→ ⚠️ Wait Confirm
         │ active
         ▼
┌──────────────────┐
│ 3. api-governor  │
│    Skill         │── Breaking ──→ ⚠️ Wait Confirm
│ (if API files)   │
└────────┬─────────┘
         │ OK
         ▼
┌──────────────────┐
│ 4. Stage         │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 5. Generate      │
│    Commit Msg    │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 6. Commit        │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 7. Update        │
│    PROJECT.md    │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 8. Push          │
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

Updated:
- .claude/PROJECT.md (history)

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
- 跳过保护检查（workspace-governor）
- 跳过 API 变更检测（api-governor）
- 自动升级模块 Level
- 覆盖历史记录
- 忽略 Skills 输出
